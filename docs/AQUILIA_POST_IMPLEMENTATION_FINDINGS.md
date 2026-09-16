# Aquilia Migration — Post-Implementation Findings, Bugs & Gap Report

Date: 2026-09-16 (expanded same-day after full session review)
Scope: forensic record of **everything encountered** during the AniWave Aquilia migration — the deep framework study, four implementation passes (provider/httpx, auth+config, deep contracts, controller features), every bug hit, every wrong behavior traced, every framework gap verified, every debugging dead end, and everything left open.

**Verification discipline:** each finding carries an evidence label:

- **[LIVE]** — reproduced at runtime during this work (error output, failing test, HTTP response).
- **[SRC]** — verified line-by-line in the installed `aquilia 1.4.1` (`.venv/lib/python3.13/site-packages/aquilia/`) while writing or during implementation.
- **[GIT]** — demonstrated by `git show HEAD:...` evidence (pre-fix code).
- **[STUDY]** — found by source study of `tmp/Aquilia/` during the audit phase; **not** re-verified against the installed wheel (noted where this matters).
- **[ONCE]** — observed exactly once, not reproducible afterwards; hypotheses recorded.

Test status at time of writing: **108/108 backend tests pass**; working-tree diff vs `HEAD`: 43 files, +851/−1437. Companion documents: `docs/AQUILIA_NATIVE_MIGRATION.md` (what changed and why), `tmp/Aquilia/docs/AQUILIA_AUTH_VS_NESTJS_GAPS.md` (pre-migration 1.4.0 auth audit + 1.4.1 fix report).

---

## 1. Executive Findings

### Critical

| ID | Finding | Severity | Category | Status |
|---|---|---|---|---|
| A-01 | Migrated provider HTTP layer was **100% non-functional** (fatal transport override); app silently survived on the third-party Miruro pipe | CRITICAL | BUG | FIXED [LIVE][GIT] |
| F-EN-01 | Engine mangles nested-contract validation errors (`list()` over a dict) → `{path: "device", message: "deviceId"}` | HIGH | BUG | OPEN [LIVE] |
| F-CORE-02 | `Request.path_params` is a **method** → contract path-param merge (`isinstance(dict)`) silently never fires | HIGH | BUG | OPEN [LIVE] |
| F-CORE-05 | `ConfigLoader.load(paths=["workspace.py"])` is **cwd-relative** and fails silently — app boots unconfigured from the wrong directory | HIGH | BUG / RELIABILITY | OPEN [LIVE] |
| F-OR-01 | ORM `find_or_create`/`get_or_create` reject FK-column keys (`user_id`) that `filter`/`create` accept — shipped 6 failing tests at baseline | HIGH | BUG | OPEN (app workaround) [LIVE] |
| A-07 | `backend/requirements.txt` stale — **missing httpx**, pins `aquilia>=1.4.0` not `>=1.4.1` → txt-driven deploys break | HIGH | DX / BUILD | OPEN [SRC] |
| A-13/A-15 | No e2e rate-limit coverage; **no HTTP-layer test for the provider package** (the exact gap that shipped A-01) | HIGH | TESTING GAP | OPEN |
| F-MAN-01 | `aq run`'s workspace validation resolves manifest `module:Class` refs as **file paths relative to the module's own directory** — framework refs (`aquilia.auth.guards:AuthGuard`) and cross-module refs falsely error, `aq run` refuses to start an app the server itself boots fine | HIGH | BUG | OPEN (framework); app worked around [LIVE] |

### High-value headline items

- **`aquilia.http` unsuitable for provider workloads** [SRC, all points]: pseudo-streaming, pool poisoning on abandoned streams, unconsumed retry/proxy config, Set-Cookie handling contradicting its own docstring, constructor timeouts that never reach custom transports. httpx adopted deliberately (§4–§5).
- **Session cookie on every API response** [LIVE, new]: the session middleware commits an anonymous `aquilia_admin_session` cookie (7-day Max-Age) on API routes — a Node-contract deviation (Node set no cookies) with a bounded in-memory store (§10.6).
- **Cache**: `get_or_set` can't cache `None`; `l1_ttl` structurally inapplicable; bulk paths lose tags (§6).
- **Tasks**: memory backend loses jobs on restart; `fail_orphaned_dependents` referenced in a docstring but doesn't exist (§7).
- **DI/Auth**: auth components registered under string tokens only; singleton controllers resolve from the *base* container; engine throttle runs before guards (§9–§10).
- **Contracts**: two distinct attribute-access traps that silently return `None` or raise; model binding auto-requires every column; `__all__` projections leak model columns including secrets (§8, §D3.10).

---

## 2. Do Not Re-Audit — Extraction Method

### Confirmed

Everything marked [LIVE], [SRC], or [GIT] in §3–§19: reproduced at runtime, verified in the installed wheel source, or shown in git history. The chronological session log (§D) contains the reproduction narratives.

### Suspected

- **F-CA-06r** `CompositeBackend.increment` race (L2 incr then separate L1 read+write) — [STUDY]; AniWave uses the plain Redis backend, no reproduction possible in our usage.
- **F-TA-05** `TaskManager.stop()` abandons tasks that swallow `CancelledError` — [STUDY].
- **F-HTTP-09** HTTP/1.1-only + latin-1 header encoding limits — [STUDY]; all AniWave headers are ASCII.

### Unverified

- **A-19** One-time anomaly: an early live script observed `GET /api/auth/me` (no Authorization header) return **200** after a prior authenticated call on the same client; isolated reruns and the e2e unauthorized-matrix consistently return 401. Hypotheses tested and ruled out: session-cookie authentication (explicitly verified: cookie present, still 401 — §10.6), stale route state. Not reproducible; recorded because it was observed.
- Whether the per-process task scheduler duplicates periodic jobs under multi-worker deployment (single-instance today).

---

## 3. Aquilia Core Findings

### F-CORE-01 — Engine nested-contract error aggregation destroys nested error dicts

```text
Location:    aquilia/controller/engine.py:1011–1018 (installed 1.4.1)
Severity:    HIGH | Category: BUG | Evidence: [LIVE] (reproduced twice)
Observed:    for field, field_errors in bp_instance.errors.items():
                 ... all_contract_errors[field] = list(field_errors)
             — when field_errors is a nested dict (nested Contract failure),
             list() yields the dict's KEYS.
Expected:    Nested errors flatten to dotted paths (device.deviceId) with messages.
Live repro:  POST /api/auth/register {"device": {"deviceId": "short"}} →
             details [{"path": "device", "message": "deviceId"}] — field name as message.
Impact:      Every nested-contract failure produces a meaningless message.
Root cause:  Aggregation assumes list values.
Workaround:  None possible app-side (mangled before app code sees it).
Recommended: Recurse dict values into dotted-path entries (working reference implementation
             exists in app/error_renderer.py:_flatten_errors for intact nested dicts).
Status:      OPEN
```

### F-CORE-02 — `Request.path_params` is a method, silently breaking contract path binding

```text
Location:    aquilia/request.py:1881 (`def path_params(self)`); aquilia/contracts/integration.py:476–480
Severity:    HIGH | Category: BUG | Evidence: [LIVE] + [SRC]
Observed:    integration.py: `path_params = request.path_params; if isinstance(path_params, dict): ...`
             — a bound method is not a dict; the merge is silently skipped. The module docstring
             claims "Parses body, query, path, header, and cookie values".
Live repro:  DELETE /api/auth/sessions/<uuid> with a SessionIdContract param →
             400 {"path": "sessionId", "message": "This field is required"} despite a valid UUID in the path.
Impact:      Path params can never feed contracts; the Path→Body→Query order is unreachable.
Recommended: Property (or call-when-callable in integration.py).
Status:      OPEN
```

### F-CORE-03 — Engine passes path params through un-cast

```text
Location:    aquilia/controller/engine.py:1104–1107
Severity:    MEDIUM | Category: DESIGN GAP | Evidence: [SRC]
Observed:    kwargs[param_name] = path_params[param_name] — no type cast; query params ARE cast
             (with a RoutingFault) — inconsistent treatment of equivalent inputs.
Impact:      Every app re-implements casting + error shape (AniWave: app/validation.int_path_param
             preserving the Nest ParseIntPipe HTTP_ERROR contract).
Status:      OPEN
```

### F-CORE-04 — Route-level throttle runs BEFORE auth guards

```text
Location:    aquilia/controller/engine.py:243 (throttle) vs :321 (guards); interceptors after guards
Severity:    MEDIUM | Category: DESIGN GAP | Evidence: [SRC]
Observed:    Engine throttle cannot be used when 401s must not consume buckets (the Node guard order).
Workaround:  AniWave enforces rate limits in an Interceptor — the engine correctly orders
             interceptors AFTER guards (verified live: 30 unauthenticated 401s left the bucket untouched).
Status:      OPEN (worked around)
```

### F-CORE-05 — ConfigLoader workspace path is cwd-relative and fails silently

```text
Location:    aquilia/runtime.py:356 (ConfigLoader.load(paths=["workspace.py"]))
Severity:    HIGH | Category: BUG / RELIABILITY | Evidence: [LIVE]
Observed:    Booting from any directory other than the workspace root silently skips the workspace
             file. Module discovery uses an ABSOLUTE path, so modules still load and the server
             boots — with no auth config, no sessions config, no integrations.
Live repro:  From repo root: server config "auth" section = None, framework auth providers never
             registered (downstream: every DI resolution of TokenManager failed with
             PROVIDER_NOT_FOUND). From backend/: full auth section present.
Debug path:  This cost the longest debugging session of the migration (§D2.2): in-process boots
             worked (cwd=backend) while pytest failed (rootdir=repo root); a private-runtime
             test inside pytest reproduced it; bisecting env vars eliminated them; printing the
             server's resolved config exposed AUTH-CFG: None.
Impact:      A wrong-cwd deployment serves an unconfigured app — a self-masking outage class.
Workaround:  AniWave documents "run from backend/" for tests and dev; production entrypoint sets
             AQUILIA_WORKSPACE.
Recommended: from_workspace() already holds the absolute workspace_file — pass it through.
Status:      OPEN (documented app-side)
```

### F-CORE-06 — Aquilia auth components registered under string tokens only

```text
Location:    aquilia/server.py:494 (AuthManager — class token), :514 (TokenManager — string token
             "aquilia.auth.tokens.TokenManager"), PasswordHasher string-tokened
Severity:    MEDIUM | Category: DESIGN GAP / DX | Evidence: [LIVE] (twice)
Observed:    AuthService.__init__(token_manager: TokenManager) → request-time
             PROVIDER_NOT_FOUND ... token=aquilia.auth.tokens.TokenManager (the error even spells
             the token the caller wanted).
Workaround:  Annotated[TokenManager, Inject("aquilia.auth.tokens.TokenManager")].
Recommended: Class-token registration or aliases.
Status:      OPEN (worked around)
```

### F-CORE-07 — Singleton controllers resolve constructor deps from the base container

```text
Location:    aquilia/controller/factory.py:40–41,118 (app_container = base container)
Severity:    MEDIUM | Category: DESIGN GAP | Evidence: [LIVE]
Observed:    instantiation_mode="singleton" on controllers whose services are module-scoped fails:
             PROVIDER_NOT_FOUND for modules.auth.services.AuthService (present in the auth module
             container, absent from the base container).
Live repro:  Enabling singleton mode broke 38 tests; reverting restored 108/108.
Recommended: Resolve singletons from the owning module's container (route.app_name is known).
Status:      OPEN (reverted)
```

### F-CORE-08 — Contract attribute-access traps (two distinct, both hit)

```text
Location:    aquilia/contracts/core.py:1104–1110 (__getattr__ raises for missing validated keys)
Severity:    MEDIUM | Category: BUG / API footgun | Evidence: [LIVE] (both)
(a) A field assigned `= None` in the class body creates a class attribute that SHADOWS __getattr__:
    body.device returned None even when a valid device was provided and sealed (register
    succeeded with deviceName=None in the created session).
(b) A raw Facet in Annotated becomes a class-attribute descriptor; attribute access on an ABSENT
    optional field raises AttributeError instead of returning None ('CommentsQuery' object has no
    attribute 'before').
Expected:    body.<field> returns validated data when present, None when absent — regardless of
             declaration style. The three declaration styles (assignment, Annotated+Field,
             Annotated+Facet) look equivalent in examples but behave differently.
Workaround:  AniWave convention: annotation-only optional fields (Field(required=False), no `= None`,
             no raw Facet for optionals); ListFacet in declared position only for required fields.
Recommended: Metaclass should not bind shadowing class attributes, or __getattr__ should return
             None for known optional-absent fields.
Status:      OPEN (convention documented)
```

### F-CORE-09 — Model-bound contracts auto-require every model column

```text
Location:    aquilia/contracts/core.py:638+ (_derive_model_facets)
Severity:    LOW | Category: API footgun | Evidence: [LIVE]
Observed:    Spec.model = User marks all model-derived facets required; a PUT contract (no
             auto-partial) 400s with "email/password_hash: This field is required" even though the
             contract declares only preferredGenres.
Workaround:  Spec.fields = [] for input contracts; PATCH routes get partial=True automatically.
Status:      OPEN (worked around)
```

### F-CORE-10 — Stacked "Cast failed for 'x':" prefixes in list-child messages

```text
Severity:    LOW | Category: DX | Evidence: [LIVE]
Observed:    A blank genre item yields "Cast failed for 'preferredGenres[1]': Cast failed for
             '<unbound>': This field may not be blank" — double prefix plus '<unbound>' for the
             anonymous child facet.
Workaround:  AniWave's error renderer strips prefixes iteratively.
Status:      OPEN (cosmetic)
```

### F-CORE-11 — Framework's own code triggers its deprecation warnings

```text
Severity:    LOW | Category: BUG (hygiene) | Evidence: [LIVE] (60 warnings in every pytest run)
Observed:    aquilia/providers/render/types.py:1046 registers RenderDeployConfig.seal_auto_deploy
             (and seal_num_instances, seal_port, seal_health_check_path…) via the deprecated
             seal_*/async_seal_* prefix convention that the framework itself deprecates
             ("deprecated in 1.3.0, removed in 2.0.0 … will silently stop validating").
Impact:      The fleet-wide warning noise hides real deprecations; after 2.0.0 the framework's own
             validators silently stop running.
Status:      OPEN
```

### F-CORE-12 — Dotenv ordering under pytest

```text
Severity:    LOW | Category: DX | Evidence: [LIVE]
Observed:    "DotEnvLoader.configure() called after loading — no effect" warning in every pytest run
             — the aquilia testing plugin (auto-loaded via entry point, before conftest) triggers
             dotenv loading before the app's dotenv policy configures it.
Impact:      Cosmetic; env pinning in conftest still works because os.environ wins.
Status:      OPEN (cosmetic)
```

### F-CORE-13 — Documentation / naming gaps discovered while navigating the framework

```text
Severity:    LOW | Category: DOCUMENTATION GAP | Evidence: [SRC/STUDY]
(a) There is NO aquilia/orm/ package — the ORM lives in aquilia/models/ (+ aquilia/db/). Anything
    guiding users to "aquilia/orm" (including the migration brief's own reference) dead-ends.
(b) GUIDE.md §11 documents an OLDER ORM API that does not match the source: `Q.eq("role","admin")`
    builder style (actual: field__lookup kwargs), `MigrationRunner`/`op.create_table` (actual:
    MigrationEngine), `nullable=`/`indexed=` options (actual: null=/db_index=). The ORM module's
    own docstrings are correct; the guide misleads.
(c) The framework's contracts example material shows `bp.imprint(db=db)` — that signature does not
    exist; the real API is imprint(instance=None, *, partial=None) and requires pre-sealed data
    ("Cannot imprint -- data has not been sealed", core.py:1820).
Status:      OPEN
```

---

## 3b. Manifest & `aq` CLI Subsystem Findings

*Added 2026-09-16 after `aq run` failed on AniWave's manifests. All [LIVE] items were reproduced with crafted workspaces in `/tmp` by calling the framework functions directly; [SRC] items were verified line-by-line in the installed 1.4.1.*

### F-MAN-01 — `aq run` validation resolves manifest refs as module-relative file paths (the reported bug)

```text
Location:    aquilia/cli/commands/run.py:278–330 (_validate_workspace_config)
Severity:    HIGH | Category: BUG | Evidence: [LIVE]
Observed:    The validator regex-scrapes every quoted colon-string from the manifest TEXT
             (re.findall(r'"([^"]*:[\w]+)"', line)), then resolves each as a file path RELATIVE
             TO THE MODULE'S OWN DIRECTORY: it strips a leading "modules." prefix and the
             module's own name, then walks module_dir/parts….
             For guards=["aquilia.auth.guards:AuthGuard"] in the auth manifest this produces
             modules/auth/aquilia/auth/guards.py — not found → "Import error in auth:
             aquilia.auth.guards:AuthGuard (file not found: modules/auth/aquilia/auth/guards.py)"
             → aq run refuses to start.
             Cross-module refs fail the same way: "modules.other.services:OtherService" listed
             in the demo manifest → modules/demo/other/services.py → false error, even though
             cross-module service imports are a supported Aquilia pattern (imports/depends_on
             + exports).
Expected:    The server itself resolves both forms correctly (server.py _resolve_guard_reference
             handles colon AND dotted paths via importlib). Only the CLI validator is broken.
             Notably aq doctor implements the SAME check correctly (resolves from
             workspace_root/modules, skips refs not starting with "modules") — two CLI
             commands, same check, one right one wrong.
Impact:      Any app using framework-internal guards/middleware/pipes in manifests, or
             cross-module component imports, cannot start via `aq run` at all.
Root cause:  Text-scraping + filesystem heuristics instead of importing the manifest and
             resolving refs with importlib.
Workaround:  Use the dotted (colon-less) reference form in manifest guards —
             "aquilia.auth.guards.AuthGuard" — which the server resolves identically
             (_resolve_guard_reference rsplit(".", 1)) and the broken regex ignores.
             Applied to AniWave's auth/library manifests; aq run boots; 108/108 tests pass
             (guard enforcement covered by the 401 matrix).
Recommended: Import the manifest module and use importlib.util.find_spec for each ref
             (as doctor almost does), or drop the pre-validation entirely — the server's own
             registry validation (aquilary) already fails loudly and precisely at boot.
Status:      OPEN (framework); app FIXED via dotted refs
```

### F-MAN-02 — A quoted URL-style string crashes the whole validation

```text
Location:    aquilia/cli/commands/run.py:~295 (module_path, class_name = import_path.split(":"))
Severity:    MEDIUM | Category: BUG | Evidence: [LIVE]
Observed:    A manifest containing any quoted string that ends in ":<word>" but contains an
             earlier colon — e.g. {"url": "redis://localhost:6379"} (no /db suffix) — matches
             the scrape regex; split(":") returns 3 parts; the unpack raises ValueError; only
             the outer handler catches it → "Unexpected error during validation: too many
             values to unpack (expected 2)" and aq run refuses to start with NO indication of
             the offending string or file.
Reproduced:  _validate_workspace_config on a manifest containing _CACHE = {"url":
             "redis://localhost:6379"} → ['Unexpected error during validation: too many
             values to unpack (expected 2)'].
Impact:      A config value in any manifest bricks the dev workflow with an opaque error.
Root cause:  Unpack outside the per-ref try; regex matches non-import strings.
Status:      OPEN
```

### F-MAN-03 — Text-scrape validation has false positives AND false negatives

```text
Severity:    LOW | Category: DESIGN GAP | Evidence: [SRC + LIVE context]
Observed:    Only whole-line comments are skipped: inline trailing comments ("…],  # note"),
             docstrings, and any config string with a colon are all "validated" as imports
             (F-MAN-02 is the crash case). Conversely, manifests whose component lists are
             built programmatically (loops, conditionals, constants) are invisible to the
             regex — validation passes while giving zero real coverage.
Status:      OPEN (moot if F-MAN-01 is fixed by importing the manifest)
```

### F-MAN-04 — `aq run` mutates files BEFORE validation, and leaves mutations behind on failure

```text
Location:    aquilia/cli/commands/run.py:693–696 (cmd_run: _discover_and_update_manifests
             THEN _validate_workspace_config)
Severity:    MEDIUM | Category: BUG / DX | Evidence: [LIVE]
Observed:    The run that reported the guard bug printed "✅ Updated workspace.py with 6
             module configurations" and then "Workspace validation failed!" — the auto-sync
             (manifest rewrites via AutoDiscoveryEngine.sync_all + workspace.py rewrite via
             WorkspaceGenerator.update_workspace_config) executes BEFORE validation, and its
             file writes are NOT rolled back when validation fails.
Impact:      An aborted run can leave rewritten manifests/workspace behind. (In AniWave's
             case the rewrites were byte-identical — verified by hashing before/after — but
             that is luck: our components matched discovery exactly.)
Status:      OPEN
```

### F-MAN-05 — workspace.py rewriter mutates formatting file-wide and reports no-op writes as updates

```text
Location:    aquilia/cli/generators/workspace.py:280–347 (update_workspace_config)
Severity:    LOW | Category: DX | Evidence: [SRC] + [LIVE]
Observed:    (a) Phase 4 applies re.sub(r"\n{3,}", "\n\n") to the WHOLE file — collapsing
             every triple+ blank line anywhere in workspace.py, a formatting mutation beyond
             the module blocks. (b) "✅ Updated workspace.py with N module configurations"
             prints even when the content is byte-identical (observed twice; hashes before/
             after unchanged). (c) Module-block preservation works by pattern-matching the
             exact `.module(Module(` opening (the quirk AniWave's workspace.py comments
             already document — hand-edits inside a block that break the pattern are lost).
             Mitigations present: syntax check before write; skip-on-no-insertion-point.
Status:      OPEN
```

### F-MAN-06 — The CLI manifest sync ignores `auto_discover=False`

```text
Location:    aquilia/discovery/engine.py (AutoDiscoveryEngine); no reference to
             auto_discover anywhere in the discovery package
Severity:    MEDIUM | Category: BUG | Evidence: [SRC]
Observed:    AniWave's manifests set auto_discover=False (explicit component lists), yet
             `aq run` still runs AutoDiscoveryEngine.sync_all(dry_run=False) over every
             module and will rewrite manifests according to discovery results. The manifest
             flag only gates the RUNTIME's convention scan, not the CLI's rewrite pass.
Impact:      Users who explicitly opted out of discovery still get their manifests rewritten
             by the dev command.
Status:      OPEN (no damage in AniWave — components matched)
```

### F-MAN-07 — The differ auto-REMOVES manifest refs that pattern-based discovery cannot see

```text
Location:    aquilia/discovery/engine.py:691–720 (diff, removal branch)
Severity:    MEDIUM | Category: BUG / DATA-LOSS RISK | Evidence: [SRC]
Observed:    For own-module refs (ref.startswith(module_prefix)), any ref not present in
             discovered paths becomes a "remove" action — with only a same-class-name-
             found-elsewhere ("is_moved") check as protection. A hand-written service ref
             whose class lives outside the discovery patterns (a helpers.py, a non-*Service
             name without @service) is invisible to discovery → `aq run` silently deletes
             the manifest entry → the next boot fails to resolve the service.
Impact:      The dev CLI can destroy valid manifest configuration. AniWave unaffected
             (all refs live in convention files with matching names).
Status:      OPEN
```

### F-MAN-08 — `to_dict()`/fingerprint omit several manifest fields

```text
Location:    aquilia/manifest.py:1293–1331 (AppManifest.to_dict / fingerprint)
Severity:    LOW | Category: BUG | Evidence: [SRC]
Observed:    The fingerprint input omits base_path, session, versioning, features, and
             template — the "stable hash of manifest for reproducible deploys" does not
             change when those fields change.
Status:      OPEN
```

### F-MAN-09 — `imports`/`depends_on` "bidirectional sync" only fires when one side is empty

```text
Location:    aquilia/manifest.py:1226–1238 (__post_init__)
Severity:    LOW | Category: BUG | Evidence: [SRC]
Observed:    The comment claims "whichever one a manifest sets, the other mirrors it", but
             the sync is `if depends_on and not imports: …` / `if imports and not
             depends_on: …` — setting BOTH with different contents silently diverges them
             (the runtime wires DI links from depends_on; the aqilary validator checks
             depends_on; imports becomes a decorative list).
Status:      OPEN
```

### F-MAN-10 — `Module.register_*` builders silently discard their arguments

```text
Location:    aquilia/workspace.py:356–425
Severity:    MEDIUM | Category: DESIGN GAP | Evidence: [SRC]
Observed:    register_controllers/services/providers/routes/sockets/middlewares (and model/
             serializer variants) emit a DeprecationWarning and `return self` — the arguments
             are discarded. With warnings filtered (common in prod), controllers "registered"
             this way silently never load.
Status:      OPEN (documented in the migration report)
```

### F-MAN-11 — Two reference grammars; only one passes the broken validator

```text
Location:    aquilia/manifest.py:191–197 (ComponentRef requires colon form) vs
             aquilia/server.py:_resolve_guard_reference (accepts colon AND dotted)
Severity:    LOW | Category: DX / CONSISTENCY | Evidence: [SRC]
Observed:    Plain string refs in guards/controllers/etc. accept both "pkg.mod:Class" and
             "pkg.mod.Class"; ComponentRef accepts only the colon form. The aq-run validator
             (F-MAN-01) rejects the colon form for non-own-module refs — so the ONLY form
             that works everywhere is the dotted one, which ComponentRef cannot express.
Status:      OPEN (AniWave convention: dotted refs in guards)
```

### F-MAN-12/13 — Minor manifest validation gaps

```text
Severity:    LOW | Evidence: [SRC]
(a) Name validation name.replace("_","").isalnum() accepts any unicode alphanumeric
    (e.g. CJK module names) but rejects hyphens; no length cap.
(b) AppManifest.database is accepted, warned about, then silently set to None in
    __post_init__ — config silently discarded instead of rejected (same family as the
    ignored route_prefix).
Status:      OPEN
```

---

## 4. Aquilia HTTP vs httpx — Deep Comparison

All Aquilia-side claims verified against installed 1.4.1 source (`aquilia/http/`); httpx side verified against 0.28.1 behavior exercised during the migration (per-call clients, MockTransport e2e tests, live scraping).

### API / request model

- **Methods/headers/query/JSON**: parity for the basics; Aquilia adds a fluent `RequestBuilder`, httpx uses kwargs. Both adequate.
- **Cookies**: httpx — case-insensitive `Headers.get_list("set-cookie")` returns individual lines; `Response.cookies` correct. Aquilia — `get_headers()`/`cookies` are correct, but the collapsed `headers` dict joins duplicate Set-Cookie with `", "`, and `HTTPSession.send` feeds **that dict** to the cookie jar (`session.py:197` → `set_from_response`), so two Set-Cookie lines parse as one malformed value. `create_response`'s own docstring says Set-Cookie "must not be combined — use get_headers()" while the dict path combines it anyway: **the implementation contradicts its own documentation** [SRC].
- **Redirects**: both follow; Aquilia ignores the per-request `follow_redirects` that `RequestBuilder.follow_redirects()` lets you set (`session.py:200` reads only client config) [SRC].
- **Multipart/forms**: Aquilia has `MultipartFormData`; not exercised by AniWave — no finding.

### Async behavior

- Both async-native. **Cancellation** is decisive: httpx's pool handles task cancellation safely. Aquilia's `body_stream()` `finally` returns the connection to the pool whenever `keep_connection and conn.is_alive()` — **even with an unread body** [SRC]. AniWave's racing engine cancels provider tasks on first success — exactly the pattern that poisons pooled connections with leftover bytes; the next request on that connection parses garbage as its status line.

### Connection management

- Aquilia: per-host dict pool under one `asyncio.Lock`; `max_per_host` bounds only *idle* pooled connections — in-flight connections are unbounded; no pool-acquisition wait (excess connections closed on release); `TimeoutConfig.pool` never enforced anywhere [SRC].
- httpx/httpcore: real pool with limits, waiting queue, cancellation-safe release.
- **Dead code**: `aquilia/http/pool.py` (ConnectionPoolManager, ConnectionStats, PooledConnection) is re-exported in `__init__.py` and used by nothing — the elaborate pool is not the pool that runs [SRC].

### Timeouts

- Aquilia: connect + per-read + write timeouts exist; **no end-to-end total deadline** (total only acts as a read fallback); pool timeout unused; and **constructor timeouts never reach user-supplied transports** — the exact seam that silently disabled every per-call provider timeout in the migrated backend (A-02) [LIVE].
- httpx: connect/read/write/pool, per request, enforced.

### Streaming (critical for AniWave)

- Aquilia `_create_body_stream` reads the **entire body into memory before the first yield** for every framing mode (chunked: read all chunks → single `yield body`; content-length: `readexactly` all) [SRC]. `iter_bytes(chunk_size)` re-slices that buffer — `chunk_size` is cosmetic. A slow trickle never trips the read timeout because each individual read succeeds.
- httpx: true incremental `aiter_bytes`; cancellation mid-stream cleans up.
- AniWave impact: the media proxy fetches HLS segments/subtitles; under Aquilia HTTP a large segment would be fully buffered and un-timeout-able while trickling. (Our httpx proxy also buffers today — Node parity — but the capability and failure modes differ categorically.)

### Reliability

- Aquilia `RetryConfig` (backoff, Retry-After, status/method filters — a rich `retry.py` library) is **never consumed** by `AsyncHTTPClient`/`HTTPSession`/`NativeTransport` [SRC, grep]. Configuring retries is a silent no-op unless you hand-wire `RetryMiddleware`.
- `ProxyConfig` with `from_env()` (reads HTTP_PROXY by default) is **never referenced** by transport or session [SRC, grep] — proxy config silently ignored.
- `MiddlewareStack.build()` calls `run_until_complete` inside a potentially running loop (`middleware.py:110`) — would crash if used; currently dead code [SRC].

### Provider-specific requirements (AniWave workloads, all exercised live)

| Requirement | Aquilia HTTP | httpx | Evidence |
|---|---|---|---|
| Scraping with custom headers/Referer | OK | OK | live |
| Multiple Set-Cookie (Livewire CSRF, ao.session) | correct only via `get_headers()`; session-jar path broken | correct natively | [SRC]; migration bug A-03 |
| Concurrent 10-way race with cancellation | pool poisoning risk | safe | [SRC] |
| Per-call timeouts | silently dropped on the constructor+custom-transport path | enforced | [LIVE] (A-02) |
| HLS segment/subtitle fetch | whole-body buffering | incremental | [SRC] |
| Redirects per request | ignored | honored | [SRC] |
| Retries | dead config | n/a | [SRC] |
| Proxy | ignored | supported | [SRC] |

### Performance

- No benchmarks were produced (the decision was correctness-driven; pre-fix native paths failed 100%, so no A/B exists). Post-switch live smoke: 10/10 providers loaded; fast-tier episode merge 7.2 s; watch race resolved real HLS in 1.5 s (Frieren/154587) [LIVE].

### Developer experience

- httpx: sync attribute access, `MockTransport` for tests (AniWave's streaming e2e uses it), ubiquitous knowledge.
- Aquilia: async-only accessors; the migration needed a `TextResponse` eager-wrapper shim + `split_set_cookie`/`set_cookie_values` helpers to bridge the ported scrapers — all deleted after the httpx switch.

### Capability matrix

| Capability | Aquilia HTTP | httpx | Gap | AniWave impact | Recommendation |
|---|---|---|---|---|---|
| Incremental response streaming | No (whole-body buffer) | Yes | [SRC] | Media memory/latency | Keep httpx |
| Cancellation-safe pooling | No (partial-read conns pooled) | Yes | [SRC] | Race engine cancels | Keep httpx |
| Multi Set-Cookie (session path) | Broken vs own docs | Yes | [SRC] | Scrapers need cookies | Keep httpx |
| Per-request timeout | Partial (constructor path drops it) | Yes | [LIVE] | All provider budgets | Keep httpx |
| Retry config | Dead code | n/a | [SRC] | unused | — |
| Proxy | Ignored | Yes | [SRC] | none today | — |
| Per-request follow_redirects | Ignored | Yes | [SRC] | none | — |
| Total deadline | No | Yes | [SRC] | slow trickles | Keep httpx |
| Zero-dependency stdlib client | **Yes** | No | — | — | — |
| Typed fault hierarchy | **Yes** | Basic | — | — | — |
| HTTP/2 | No | Optional | [STUDY] | none | — |

**Aquilia-HTTP-only capabilities:** dependency-free stdlib implementation; rich typed faults (`ConnectTimeoutFault`, `TLSFault`, …) carrying retryable metadata; built-in DI provider (`HTTPClientProvider`).

---

## 5. Aquilia HTTP — Bugs, Missing Features, Integration Gaps

### Bugs

1. **Pseudo-streaming** — `_create_body_stream` buffers entire bodies (`_transport.py:624+`; chunked branch reads all chunks then one `yield body`). [SRC]
2. **Pool poisoning on abandoned streams** — `body_stream` finally returns partially-read connections to the pool. [SRC]
3. **Set-Cookie doc/behavior contradiction** — dict path joins all duplicates; session jar consumes the dict. [SRC]
4. **Per-request `follow_redirects` ignored** (`session.py:200`). [SRC]
5. **`MiddlewareStack.build()` would crash in a running loop** (`middleware.py:110`). [SRC; dead code]

### Missing features

6. **Retry execution** — RetryConfig has no consumer. [SRC]
7. **Proxy support** — env-loaded config ignored by the transport. [SRC]
8. **Total deadline / pool timeout** — unenforced. [SRC]
9. **Streaming request bodies** — `_build_request_bytes` handles `bytes` only; an `AsyncIterator[bytes]` body silently produces no body and no Content-Length. [SRC]

### Integration gaps

10. **Constructor `timeout=` does not propagate to a user-supplied `transport=`** — the seam AniWave's migrated `_http.py` hit (A-02). [LIVE]
11. **`pool.py` exported but unused** — two pool implementations, one dead. [SRC]
12. Per-call fresh clients (cookie isolation — the reference pattern) get no pool benefit at all; the framework's DI singleton client is the only pooled path, and it shares one cookie jar across all requests (compounding finding 3 for multi-site scrapers). [SRC]

---

## 6. Aquilia Cache — Post-Implementation Findings

AniWave usage: `CacheIntegration(backend="redis", key_prefix="backend:")` backing catalog read-through (`get_or_set`), streaming resolve (delete-then-`get_or_set` for `refresh=`), and the 60 s playlist cache. Verified live during the migration: key layout `backend:backend:v1:default:<key>` (note the doubled `backend:` — CacheService prefix + RedisBackend prefix), namespaced clear semantics, cross-test leakage behavior, `get_default_cache_service()` process-global identity.

### Findings

1. **`get_or_set` cannot cache `None`** — fast path `if value is not None: return value`; a None loader result is stored but every subsequent call misses and recomputes (only `@cached` uses a None sentinel). [SRC] AniWave impact: none (producers raise on failure).
2. **`get`/`set` never raise** ("Never raises — returns default on error") — callers cannot distinguish cached-None from backend-down; no error surfaced to the app's fault system beyond internal fault emission. [SRC] Impact: Redis outage degrades silently to full-miss (matches Node availability posture; acceptable, but invisible).
3. **`l1_ttl` is dead config** — parsed into `CacheConfig` (core.py:248), passed to `create_cache_backend` (di_providers.py:181), but `MemoryBackend.__init__` **has no TTL parameter at all**; composite L1 built with `max_size/eviction_policy/threshold` only. [SRC]
4. **`MemoryBackend.set_many` drops tags** — entries constructed without tags. [SRC]
5. **`CompositeBackend` lacks `try_acquire_lock`/`supports_distributed_lock`** — distributed stampede locking exists only on RedisBackend; composite silently loses it even with Redis L2. [SRC]
6. **`touch` is get+set** — non-atomic, loses tags. [SRC]
7. **Redis `get_many` builds `CacheEntry(key, value)` without tags/namespace** — bulk reads lose tag association. [SRC]
8. **`redis_decode_responses` config field ignored** (hardcoded `decode_responses=False`). [STUDY]
9. **Double key prefixing** — CacheService prefix + RedisBackend prefix compose to `aq:aq:v1:…`-style duplication (harmless; surprised us during key debugging). [LIVE]

### Capability matrix

| Capability | Aquilia Cache | AniWave requirement | Status | Gap |
|---|---|---|---|---|
| Redis backend, JSON values | Yes | catalog/resolve/playlist caching | WORKING | — |
| Read-through + stampede prevention | `get_or_set` (process single-flight + optional distributed lock) | episode/home caches | WORKING | None-caching caveat (1) |
| Namespaced clear | Yes | test isolation | WORKING | — |
| Short-TTL entries | Yes | 60 s playlist cache | WORKING | — |
| Failure behavior | Silent fail-open | availability-first | WORKING (by design) | no app-visible error hook |
| Composite L1 TTL | Config exists | unused | **BROKEN** (l1_ttl inapplicable) | (3) |
| Tag invalidation on bulk paths | Partial | unused | PARTIALLY WORKING | (4)(6)(7) |

---

## 7. Aquilia Task — Post-Implementation Findings

AniWave usage: one task (`aniwave:warm_episodes`, memory backend, 2 workers, `max_retries=0`, 300 s timeout), dispatched fire-and-forget from the catalog home producer via `loop.create_task(warm_episodes.delay(...))` with a done-callback logger; the service instance reaches the task body through a module-level `_active` reference registered in the DI `async_init` hook (documented bridge — the task subsystem has no DI integration).

### Findings

1. **Memory backend loses jobs on restart** — `is_persistent = False` (documented in source). [SRC] Impact: pending warm-ups dropped; next viewer triggers a normal merge (self-healing). Acceptable for warm-up; NOT acceptable for durable workloads.
2. **No per-queue rate limiting** — explicitly documented as deliberately absent (`tasks/__init__.py:24–26`). [SRC]
3. **`fail_orphaned_dependents` does not exist** — referenced in an engine docstring (engine.py:254) as the mechanism for failed dependencies; grep finds no implementation; dependents of failed/dead jobs stay WAITING forever. [SRC: docstring vs grep]
4. **Scheduler is per-process** — every process running a TaskManager evaluates periodic schedules; default `dedup="allow"` means N processes enqueue N copies. [SRC/STUDY; not reproduced — single instance]
5. **`stop()` abandons tasks that swallow `CancelledError`** (bounded wait, stuck tasks detached with warning). [STUDY]
6. **At-least-once delivery only** (documented) — idempotent task functions required; warm-up is. [SRC]
7. **Task arguments are not versioned** — moving/renaming a task function breaks `func_ref` resolution on durable backends (`TaskResolutionFault`). [STUDY]
8. **Redis backend pop/list/stats do O(n) loads of all indexed jobs**; SQL claim scans up to 32 candidates. [STUDY]
9. **CronSchedule has no timezone support** (UTC only) and scans minute-by-minute. [STUDY]
10. **No DI integration for task bodies** — module functions with JSON args only; AniWave's `_active` bridge is the documented pattern. [SRC]

### Capability matrix

| Capability | Aquilia Task | Previous AniWave mechanism (Node/BullMQ) | Gap | Impact |
|---|---|---|---|---|
| Fire-and-forget background job | Yes (memory) | BullMQ (Redis-persistent) | persistence | warm-up loss on restart (accepted) |
| Retries with backoff | Yes | BullMQ | — | — |
| Timeout | Yes | BullMQ | — | — |
| Scheduling | Yes (per-process) | — | multi-process duplication | none today |
| DI access from task body | No | — | manual bridge | documented `_active` pattern |
| Durable queues | Redis/SQL backends exist | Redis | — | available if needed |

**Verdict:** safely replaces the Node warm-up workload; unproven (and partially broken, see 3/4/7) for durable/workflow workloads AniWave doesn't have.

---

## 8. Contracts + ORM Findings

### Contract findings (beyond F-CORE-08/09/10)

1. **F-CORE-02** (path-param binding broken) — see §3; discovered when `SessionIdContract` received nothing from the path [LIVE].
2. **`imprint` requires pre-sealed data** and the documented `bp.imprint(db=db)` form doesn't exist (F-CORE-13c). [SRC]
3. **`Spec` + `imprint` work well once understood** — source-mapped camelCase→snake_case writes, PATCH auto-partial, projection molding with `@computed` context all verified live (profile/preferences updates, session views). Gap is documentation/discoverability, not capability. [LIVE]
4. **`__all__` projections leak every model column** — molding a `Spec.model = UserSession` contract with `projections = {"session": "__all__"}` emitted `refresh_token_hash`, `previous_refresh_token_hash`, `last_ip`, `user_agent`, and the FK value in the output dict. Caught during bring-up (printed the molded dict); AniWave uses explicit projection lists everywhere. A secrets-leak footgun for anyone reaching for `__all__`. [LIVE]
5. **`ReadOnly` mold auto-formats UUID/datetime but not in JS `toISOString()` form** (`+00:00` vs `Z`, microseconds vs milliseconds) — AniWave keeps exact wire parity via `@computed` + `time_utils.iso_ms`. [LIVE]
6. **`ReadOnly` skips None values unless `allow_null=True`** — a nullable field silently disappears from output when null (observed: `platform` missing from session views until `ReadOnly(allow_null=True)`). [LIVE]
7. **Declared-facet fields return the facet itself on attribute access** — `body.keys` returned the ListFacet object (whose `__getitem__` expects a slice → `TypeError: Expected a slice` when iterated by the service). [LIVE]
8. **Nested validated data arrives as DataObject** (attribute + .get access both work) — good; but the nested *error* path is mangled by the engine (F-CORE-01). [LIVE]
9. **Unused-but-present capabilities** (INFO, no defect): `Contract["projection"]` lens references, `ContractUnion` discriminated unions, `seal_many`/`seal_stream`/`seal_columnar`, `from_env`/`from_cli`, `example()`/`strategy()`, `Contract.Pipeline`, `Lens` (sync mold raises `LensUnresolvedFault` for un-awaited async related managers — deliberate, security-noted in source), `MAX_NESTING_DEPTH = 32` cap. [STUDY/SRC]

### ORM findings

1. **F-OR-01 — lookup-key inconsistency** (`aquilia/models/base.py:908–914`): `find_or_create`/`get_or_create` validate keys against `_fields` (FK attribute `user`), while `filter(user_id=...)` and `create(user_id=...)` accept the raw column — the metaclass itself documents `user_id` as the write/filter spelling. **Confirmed by the 6 baseline test failures** (`Unknown field: 'user_id'. Valid fields: [... 'user' ...]`). App workaround: filter-then-write inside `_upsert_retry` (DB unique constraint preserves race-freedom). [LIVE]
2. **`find_or_create` requires a unique constraint over the lookup fields**; `get_or_create` without one warns and falls back to racy SELECT-then-INSERT. [SRC]
3. **`bulk_create`/`bulk_update` skip signals by design** (documented at the call sites). [SRC]
4. **Unhydrated FK reads return a `RelatedNotLoaded` sentinel** — `.pk`/bool/== work; anything else raises. Deliberate (async ORM, no lazy loading) but a sharp edge for code ported from sync ORMs. [STUDY]
5. **No `aquilia/orm/` package** — the ORM is `aquilia/models` + `aquilia/db` (F-CORE-13a). [SRC]
6. **GUIDE.md documents a stale ORM API** (F-CORE-13b). [STUDY]
7. Migration tooling itself worked correctly for AniWave: one generated migration (7 tables), applied by `auto_migrate` at boot, no hand edits. [LIVE]

---

## 9. DI Findings

1. **String-token-only auth registrations** (F-CORE-06). [LIVE ×2]
2. **Singleton → base container** (F-CORE-07). [LIVE, 38 failures]
3. Request scopes share provider dicts by reference (copy-on-write on first register); auth ValueProviders registered at server init are correctly visible to request scopes. [LIVE — verified working]
4. **`Annotated[T, Inject("…")]` string tokens work well** once known; the failure mode for the wrong spelling is a request-time 404-shaped `PROVIDER_NOT_FOUND` fault, not a boot error — late, confusing, but with an excellent error message (it names the exact token and candidates). [LIVE]
5. **Remaining manual dependency management in backend/** (deliberate, documented): the `metrics` module singleton (consumed by middleware + metrics endpoint outside DI), the catalog `_active` task bridge (registered via the DI `async_init` lifecycle hook — the correct available seam), the rate limiter's module-global Redis client (raw INCR/EXPIRE semantics), and the provider package's framework-free module state.
6. `DISettings.scope_enforcement` exists ("warn"/"raise") — AniWave runs "warn" in dev, "raise" in prod config; no scope violation ever fired during testing. [LIVE]

---

## 10. Auth Findings

*(Aquilia limitation vs AniWave integration bug called out per finding.)*

1. **`require_auth_by_default=True` is unusable alongside the framework admin** — admin routes carry no `@Public()` markers; `route_is_public` uses strict `is True` comparisons, so protect-by-default locks the admin login page before any session exists. **Aquilia limitation.** [SRC] AniWave keeps `require_auth_by_default=False` + per-module `AuthGuard`s (auth, library manifests) — same fail-closed posture for API routes, admin unaffected.
2. **Principal injection works end-to-end** — `principal_factory` → `Annotated[AuthUser, CurrentUser]`. The bring-up failure (`'Identity' object has no attribute 'session_id'` → 500 on `/api/auth/sessions`) was an **AniWave integration bug**: the factory was omitted from the workspace auth config; the engine's Identity fallback has no `session_id`. Fixed by wiring `principal_factory = "app.principals:build_principal"`. [LIVE]
3. **401 semantics preserved** — framework `AUTH_0xx` codes map to the Node envelope with the "Authentication required" (AUTH_010) vs "Invalid or expired access token" (AUTH_002/003/004) distinction; covered by the unauthorized-matrix e2e. The initial implementation collapsed both to the generic message and failed the matrix — fixed by splitting the renderer mapping. [LIVE]
4. **Stateless Bearer posture verified** — no per-request store lookups; `collapse_token_errors` anti-enumeration. [LIVE]
5. **Auth-component DI token mismatch** (F-CORE-06). **Aquilia limitation.** [LIVE]
6. **Session middleware sets a cookie on every API response** [LIVE, new]: register (and any API request) returns `Set-Cookie: aquilia_admin_session=sess_…; Max-Age=604799; Path=/; HttpOnly; SameSite=lax`. Root cause: the workspace `.sessions(...)` config (added for the admin dashboard) mounts the session engine globally, and the auth middleware resolves/commits a session per request — anonymous API sessions are created, marked dirty, and persisted (memory store, LRU-bounded ~10k). Node set no cookies on API routes. Verified that the cookie does **not** authenticate API routes (Bearer still required — `/api/auth/me` with cookie, no header → 401). Impact: response bloat (one Set-Cookie per response), cookie churn on API clients, session-store growth bounded by eviction; a CSRF-relevant surface exists in principle for any future cookie-authenticated route (none today). Workaround options: scope sessions to the admin prefix (framework route scoping for session middleware not found) or accept. **Status: OPEN (behavior deviation, documented).**
7. **Retained app-owned pieces (AniWave-specific, not framework gaps)**: refresh-token CAS rotation on `user_sessions` (device registry + AuthEvent audit — beyond `RotatingTokenStore`'s storage model), the metrics bearer gate, the Redis rate limiter (Node envelope + fail-open + F-CORE-04 ordering).
8. **Unused framework auth surface** (INFO): MFA (TOTP/WebAuthn), OAuth2 server (PKCE/device flow), API-key backend, clearance matrix, audit trail. None needed by AniWave; no defects found in study beyond those already listed.

---

## 11. Provider System Findings

Reconciling `tmp/provider/` (working FastAPI+httpx reference) with `backend/provider/` (migrated library) and `modules/providers/` (service adapter).

### What the migration originally broke (all fixed in this work)

1. **A-01 — Fatal transport override (CRITICAL)**: `_MultiHeaderTransport._read_response_head` returned `headers: dict[str,str]` (git HEAD: `return m.group(1), int(m.group(2)), m.group(3), headers` after comma-joining) while the stock caller unpacks tuples (`_transport.py:697`: `{name.lower(): value for name, value in raw_headers}`). **Every provider HTTP call raised `TransportFault: too many values to unpack (expected 2)`** — reproduced live (localhost double-cookie server AND real requests: `anineko.search("frieren")` failed while `anilist_query` on the stock client succeeded in the same run). All 10 scrapers, ARM/AniZip mapping, and the racing engine were dead; the app survived on the Miruro pipe. The irony: the override was also unnecessary — 1.4.1 preserves repeated Set-Cookie natively via `_raw_headers`/`get_headers()`. [LIVE][GIT]
2. **A-02 — Timeouts silently ignored (HIGH)**: helpers passed `timeout=` to the `AsyncHTTPClient` constructor with a custom transport; the session never propagates config to user transports. Verified: `AsyncHTTPClient(timeout=20.0, transport=NativeTransport())` leaves the transport at 30.0. Every request ran at the default. [LIVE]
3. **A-03 — mkissa case-sensitive cookie lookups (HIGH)**: `headers.get("set-cookie")` against Aquilia's case-preserving dict missed `Set-Cookie` — breaking the Livewire CSRF/session flow (store_cookies stored nothing) and streamsb `sid` extraction. httpx is case-insensitive; fixed by the switch. [SRC][LIVE]
4. **A-04 — Racing regressions (MEDIUM)**: migrated WATCH_TIMEOUT 75 s / EPISODES_TIMEOUT 60 s / WATCH_CACHE_TTL 45 s vs reference 15/6/600; an 8-second post-winner drain awaiting losers (every successful race paid up to +8 s); single-phase 10-provider episode gather instead of the reference's fast-tier strategy (`anizone/anikoto/reanime/aniwaves` first, rest only if empty). All restored; the test that had codified the regressed constants was updated. [GIT diff vs reference]
5. **A-04b — 422 mapping (LOW)**: `extract_simple` raised `ApiError(422)` for bad `type`/provider → mapped to `PROVIDER_UNAVAILABLE` instead of `VALIDATION_ERROR` (the `ValidationError` class existed, never raised). Fixed to raise `ValidationError`. [SRC]

### Reference-vs-backend deltas deliberately kept

- Relative-import fix in `_race._load` (the tmp snapshot's `src.providers.*` import was broken in its own layout — silently disabling native providers there).
- Per-call fresh clients (cookie isolation) — reference pattern, preserved on httpx.
- The tokenized media proxy (`/api/stream/media`) is a deliberate superset of the reference's plain `/proxy_*` endpoints.
- The reference's lenient extract semantics (coerce bad audio, ignore unknown provider) vs the backend's 422 — kept the backend's stricter behavior (tests codify it).

### Still open / by design

6. **Provider package remains framework-free library code with module state**: `_race._latency/_ep_latency/_failures` (bounded: 10 providers) and `_watch_cache` / `provider/providers/_cache._store` (**unbounded by key count** — entries only overwritten, never evicted; one entry per (provider, anime[, episode, audio]) ever seen). MEDIUM memory-growth risk in long-lived processes. [SRC]
7. **Miruro-pipe fallback retained** (reference behavior, foreign provider ranking and all) — untested by the suite. [testing gap]
8. **No HTTP-layer test for the provider helpers** — the exact gap that shipped A-01 ("cookie flows import + load" was the extent of the original verification). Streaming proxy HTTP is covered via MockTransport; `provider/providers/_http.py` has nothing. [testing gap]
9. **Scrapers rot silently** — ten regex-HTML scrapers; the race hides individual failures by design; `ProviderService.providers_status()` exists but has **no route** (dead code, no ops visibility). [SRC]
10. **`api.py` legacy `Optional[...]` typing and the dead `get_anime_characters`/`get_sources`/`get_bridge_status` ports** — kept as 1:1 library surface, documented. [SRC]

---

## 12. Pipeline and System-Level Findings

1. **Request → DI → controller → service → provider → HTTP → DB/cache → response**: verified end-to-end live (health, live AniList search, register, me, 401 matrix, watchlist write, live stream resolve with tokenized servers). The system-level traps found were only *visible* when subsystems interacted: F-CORE-05 (config feeds auth feeds DI), F-CORE-07 (factory × module containers), A-02 (client × transport config).
2. **Auth → identity → authorization → controller**: framework middleware + module guards + CurrentUser injection verified live, including engine-guaranteed 401-before-throttle (30×401 leave the bucket untouched; valid request passes).
3. **Task → dispatch → execution**: warm-up dispatch verified in e2e (home rebuild triggers it); task-body success exercised indirectly by catalog episode tests. Task failure/retry paths untested (warm-up has `max_retries=0`).
4. **Media proxy chain (resolve → tokenize → playlist rewrite → variant → segment → AES key)**: covered by the LocalHlsServer e2e including XOR-manifest decryption and segment deobfuscation. **Cancellation mid-segment untested**; the proxy buffers whole segments (Node parity; memory consideration under concurrency).
5. **Test-isolation interactions**: the resolve cache and playlist cache live in the shared test Redis DB — a stale resolve key from an earlier test once served a cached token whose playlist was also cached, defeating a deliberate upstream-failure test (diagnosed by flushing Redis; fixed with per-test namespace clears). Cross-test cache coupling is now handled by the autouse fixture, but the lesson stands: framework-level cache + session-scoped app fixture = implicit state sharing. [LIVE]

---

## 13. Missing Features Needed for AniWave

| Feature | Class | Why needed | Current workaround | Why insufficient | Suggested fix (framework/app) | Priority |
|---|---|---|---|---|---|---|
| Typed path-param casting | Framework missing | `/<anilistId>` routes | `int_path_param` + inline UUID check | every controller re-implements; error shape app-defined | engine casts by annotation (framework) | MEDIUM |
| Contract path-param binding | Framework broken (F-CORE-02) | query-contract pattern for path ids | plain params + inline validation | two validation styles coexist | fix `request.path_params` (framework) | MEDIUM |
| Nested contract error fidelity | Framework broken (F-CORE-01) | device validation messages | none | client sees `"message": "deviceId"` | engine-side flatten (framework) | MEDIUM |
| Auth-component class tokens | Framework incomplete | clean constructor injection | `Inject("<string>")` | tribal knowledge | class tokens/aliases (framework) | LOW |
| Singleton controllers with module DI | Framework incomplete | per-request instantiation cost | per_request mode | minor overhead | owning-module resolution (framework) | LOW |
| Production HTTP client | Framework incomplete | provider + media workloads | httpx | second HTTP stack in the app | fix aquilia/http or bless httpx at the `HTTPTransport` seam (framework) | HIGH if unification desired |
| Session middleware scoped to admin prefix | Framework missing | API responses carry admin cookies (§10.6) | accept | response bloat, store growth | route-scope the session engine (framework) | LOW |
| Rate limiter with Node contract | AniWave-specific | RATE_LIMITED envelope, fail-open, auth ordering | custom Redis interceptor | — | correct layer; keep | — |
| Provider status route | AniWave-specific | scraper-health observability | dead service method | no visibility | expose `GET /api/providers/status` (app) | LOW |
| Durable task backend | Framework exists (Redis/SQL) | warm-up loss on restart | memory backend | self-healing | config change if durable workloads appear | LOW |

---

## 14. What Should Be Fixed in Aquilia Itself

1. **`request.path_params` → property** (F-CORE-02) — one line; unblocks documented contract binding.
2. **Engine nested-error aggregation** (F-CORE-01) — recurse dict values into dotted paths.
3. **`ConfigLoader.load` absolute workspace path** (F-CORE-05) — `from_workspace()` already holds it.
4. **HTTP: real streaming, cancellation-safe pooling, Set-Cookie dict exception, consumed Retry/Proxy config, config-to-user-transport propagation** (§5) — until then httpx stays the provider client.
5. **Class-token auth registrations** (F-CORE-06); **module-container singleton resolution** (F-CORE-07).
6. **ORM lookup-key consistency** (F-OR-01) — accept FK `_id` column keys in find_or_create.
7. **Contract attribute-access traps** (F-CORE-08) and the **`__all__` projection secret leak** (§8.4) — metaclass/projection defaults.
8. **Fix the framework's own seal_* deprecation usage** (F-CORE-11) before 2.0.0 silently disables its validators.
9. **Replace the `aq run` manifest validator's text-scrape with import-based resolution** (F-MAN-01/02/03) — import the manifest and use importlib (the aqilary registry and `aq doctor` already show both halves of the correct approach); stop the auto-sync from removing entries and from running against `auto_discover=False` modules (F-MAN-06/07); validate before mutating (F-MAN-04).
10. **Docs**: correct GUIDE.md §11 (ORM API), add the real `imprint` signature, point ORM references at `aquilia.models`.

---

## 15. What Should Remain in AniWave

- The Node wire contract: error envelope, page envelopes, `toISOString()` timestamps, route shapes.
- The Redis fixed-window rate limiter (fail-open, auth-ordered, `details.retryAfterSeconds`).
- Stream capability tokens (AES-GCM SSRF binding) and the m3u8 toolkit.
- Refresh rotation / device sessions / AuthEvent audit on `user_sessions`.
- pino-shaped logging; in-process metrics.
- The provider package (port of the verified reference), including its module state — scraper crypto belongs in the app, not the framework.
- The error-envelope outer middleware (covers `_handle_unexpected`/`PermissionError` paths the `error_renderer` hook does not).

---

## 16. Technical Debt Left After Migration

Ranked by impact:

1. **`backend/requirements.txt` stale** — missing `httpx`, pins `aquilia[postgres]>=1.4.0` (needs `>=1.4.1`). Found during this report's verification pass; txt-driven deploys break. **OPEN (A-07).**
2. **Unbounded provider caches** (`_cache._store`, `_race._watch_cache`). **OPEN.**
3. **`providers_status` dead code** (service method, no route). **OPEN.**
4. **API responses set admin session cookies** (§10.6) — behavior deviation, bounded impact. **OPEN.**
5. **Repo hygiene** — `db.sqlite3` at repo root; the entire `aniwave/` Node tree + `node_modules/` still present. **OPEN.**
6. **Per-request controller instantiation** — forced by F-CORE-07; minor overhead. **OPEN.**
7. **Media proxy segment buffering** — Node parity; a streaming passthrough would reduce memory. **OPEN (low).**
8. **Nested device error message lost** — blocked on F-CORE-01. **OPEN.**
9. Removed during the migration (for the record): NODE_ENV dual config, `AppCache` single-flight re-implementation, `_playlist_cache` dict LRU, `app/auth.py` decorator stack, `_validated`/`_device`/`_require_uuid`/`_validate_genres`/`_int_or_400`/`_int_or_none`/`_parse_anilist_id`/`_parse_list_query`/`_parse_search_query`/`_query` helpers, duplicated `_iso`, `AuthResult`/`SessionView`/`AuthUserRecord` DTO classes, 14 `print()` calls, stale `endpoints/main` `.pyc`, duplicated workspace imports, the kwargs-scanning rate-limit wrapper.

---

## 17. Testing Gaps

Specific scenarios (not "more tests"):

1. **Provider HTTP layer** (A-15): local HTTP server asserting `_http.fetch_text/get/post/head`, per-call timeout enforcement, multi-Set-Cookie retrieval — the test that would have caught A-01.
2. **Rate limiting e2e** (A-13): suite runs `RATE_LIMIT_DISABLED=true`; the interceptor path (marker resolution via route metadata, 429 envelope, 401-ordering, fail-open with Redis stopped) was verified only by manual live runs.
3. **Admin dashboard + session-cookie login**: zero tests reference `/admin` or the cookie flow.
4. **Specula/OpenAPI generation**: untested.
5. **Nested contract error shape**: assert dotted-path details once F-CORE-01 is fixed.
6. **Cache stampede**: concurrent-miss single-flight of `get_or_set` (N coroutines, one loader execution).
7. **Redis outage at HTTP level**: catalog fail-open; playlist miss-through (only the rate limiter's fail-open is unit-tested).
8. **Task failure paths**: no test exercises task retry/dead-letter at all.
9. **Media proxy cancellation**: client disconnect mid-segment (upstream cleanup, no leaks).
10. **Miruro pipe fallback flow** (codec is unit-tested; the fallback path isn't).
11. **DB failure paths**: health "degraded" shape; queries failing mid-request.
12. **Live scraper canary**: network-marked per-provider smoke (the 10/10 load + episode merge + watch race was run manually).
13. **Session-cookie behavior** (§10.6): assert API responses' cookie shape and that cookies never authenticate API routes (regression guard for the deviation).

Covered well (contrast): auth e2e matrix (rotation, reuse detection, single-winner concurrency), streaming proxy chain with local HLS server, catalog shapes, 100-concurrent stress, m3u8/mappers/token/error-renderer units.

---

## 18. Production Risks

| Risk | Rank | Evidence |
|---|---|---|
| App started from wrong cwd serves unconfigured (auth off, default DB) | HIGH | F-CORE-05 reproduced; masked by successful boot |
| requirements.txt-driven deploys broken (no httpx) | HIGH until fixed | A-07 |
| Scraper rot: providers break silently; no status route/canary | HIGH | §11.9; live CDN variance observed (flixcloud 403 blips — environmental, memory note) |
| Rate limiter fails open on Redis outage → abuse window | MEDIUM | by design; no HTTP-level test |
| Provider cache memory growth in long-lived process | MEDIUM | §16.2 |
| Media proxy memory under concurrent segment fetches | MEDIUM | §12.4 |
| Session store growth / cookie churn on API traffic | LOW-MEDIUM | §10.6 (LRU-bounded store) |
| Warm-up jobs lost on restart | LOW | self-healing |
| Multi-worker changes: per-process scheduler duplication; playlist cache becomes shared via Redis (improvement) | LOW | §7.4 |

---

## 19. Final Gap Matrix

| ID | Subsystem | Finding | Category | Severity | Confirmed? | Affected files | Impact | Root cause | Workaround | Recommended fix | Owner | Status |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| A-01 | provider/http | Fatal transport override killed all provider HTTP | BUG | CRITICAL | [LIVE][GIT] | provider/providers/_http.py (HEAD) | 100% provider outage hidden by pipe | dict vs tuple contract | — (httpx) | none needed | AniWave | FIXED |
| A-02 | provider/http | Per-call timeouts silently ignored | BUG | HIGH | [LIVE] | _http.py (HEAD) | 30 s floors | config not propagated to user transports | — (httpx) | propagate config | Aquilia | FIXED (app) |
| A-03 | provider/mkissa | Case-sensitive Set-Cookie lookups | BUG | HIGH | [SRC] | mkissa.py | cookie flows broken | case-preserving dict | — (httpx) | — | AniWave | FIXED |
| A-04 | provider/race | Regressed budgets/cache/drain/tiering | REGRESSION | MEDIUM | [GIT] | _race.py | latency 5–10× | tuning without reference check | — (restored) | — | AniWave | FIXED |
| A-04b | provider/api | 422s mapped as PROVIDER_UNAVAILABLE | BUG | LOW | [SRC] | api.py | wrong error class | ValidationError never raised | — (fixed) | — | AniWave | FIXED |
| A-05 | library/ORM | `user_id` lookup keys rejected | BUG | HIGH | [LIVE] | library/services.py | 6 endpoints 500 (baseline) | ORM key inconsistency | filter-then-write + retry | accept FK column keys | Aquilia | PARTIALLY FIXED (app workaround) |
| A-07 | build | requirements.txt stale | DX | HIGH | [SRC] | backend/requirements.txt | broken txt deploys | not updated with httpx | use pyproject/uv | regenerate | AniWave | OPEN |
| A-09/10 | provider | Unbounded caches | RELIABILITY | MEDIUM | [SRC] | _cache.py, _race.py | memory growth | no eviction | restart | LRU/TTL bound | AniWave | OPEN |
| A-11 | repo | stray db.sqlite3, aniwave/ tree | DX | LOW | [SRC] | repo root | confusion | migration leftovers | — | clean up | AniWave | OPEN |
| A-13 | tests | no rate-limit e2e | TESTING | HIGH | [SRC] | tests/ | enforcement manually verified only | disabled in suite | — | scenario tests | AniWave | OPEN |
| A-15 | tests | no provider HTTP-layer test | TESTING | HIGH | [SRC] | tests/ | A-01 class ships again | coverage gap | — | local-server test | AniWave | OPEN |
| A-16 | tests | Miruro fallback untested | TESTING | MEDIUM | [SRC] | tests/ | fallback rot | coverage gap | — | fallback-flow test | AniWave | OPEN |
| A-17 | provider | providers_status unwired | MISSING | LOW | [SRC] | services.py | no scraper observability | never routed | manual DI call | expose route | AniWave | OPEN |
| A-18 | errors | nested device message lost | BUG | MEDIUM | [LIVE] | engine | client UX | F-CORE-01 | none | framework fix | Aquilia | BLOCKED |
| A-19 | auth | one-time NO-AUTH 200 anomaly | UNKNOWN | LOW | [ONCE] | — | none reproduced | unresolved | — | monitor | — | NEEDS INVESTIGATION |
| F-MAN-01 | aq CLI/manifest | run.py validator resolves refs as module-relative paths; framework/cross-module refs falsely error | BUG | HIGH | [LIVE] | cli/commands/run.py:278–330 | aq run cannot start valid apps | text-scrape + fs heuristics | dotted refs in guards | import manifest + importlib | Aquilia | OPEN (app FIXED) |
| F-MAN-02 | aq CLI/manifest | URL-style string crashes validation with generic unpack error | BUG | MEDIUM | [LIVE] | cli/commands/run.py:~295 | opaque startup failure | unpack outside try | avoid such strings | rsplit(":",1) + per-ref try | Aquilia | OPEN |
| F-MAN-03 | aq CLI/manifest | scrape validation false +/- | DESIGN | LOW | [SRC] | run.py | coverage illusion | regex over text | — | import the manifest | Aquilia | OPEN |
| F-MAN-04 | aq CLI | mutate-before-validate; writes not rolled back | BUG | MEDIUM | [LIVE] | run.py:693–696 | aborted runs leave rewrites | ordering | verify hashes | validate first | Aquilia | OPEN |
| F-MAN-05 | aq CLI | workspace rewriter mutates formatting file-wide; no-op writes reported as updates | DX | LOW | [SRC][LIVE] | generators/workspace.py | formatting churn | global regex | pattern quirk documented | diff-before-write | Aquilia | OPEN |
| F-MAN-06 | aq CLI/discovery | sync ignores auto_discover=False | BUG | MEDIUM | [SRC] | discovery/engine.py | opted-out manifests rewritten | flag not consulted | components matched | respect the flag | Aquilia | OPEN |
| F-MAN-07 | aq CLI/discovery | differ auto-removes refs invisible to pattern discovery | BUG / DATA LOSS | MEDIUM | [SRC] | discovery/engine.py:691 | valid entries deleted | pattern-only discovery | none needed | never remove, only warn | Aquilia | OPEN |
| F-MAN-08 | manifest | to_dict/fingerprint omit base_path/session/versioning/features/template | BUG | LOW | [SRC] | manifest.py:1293 | fingerprints miss config dims | serialization gaps | — | include all fields | Aquilia | OPEN |
| F-MAN-09 | manifest | imports/depends_on sync only when one side empty | BUG | LOW | [SRC] | manifest.py:1226 | silent divergence | conditional sync | set one only | warn on divergence | Aquilia | OPEN |
| F-MAN-10 | workspace | Module.register_* discard arguments | DESIGN | MEDIUM | [SRC] | workspace.py:356 | silent no-load with filtered warnings | deprecated no-ops | manifest lists | raise in 2.0 | Aquilia | OPEN |
| F-MAN-11 | manifest/CLI | two ref grammars; only dotted passes validator; ComponentRef can't express it | CONSISTENCY | LOW | [SRC] | manifest.py:191, server.py | confusion | grammar drift | dotted convention | unify grammar | Aquilia | OPEN |
| F-MAN-12/13 | manifest | unicode name acceptance; database silently nulled | DESIGN | LOW | [SRC] | manifest.py | minor | validation gaps | — | tighten | Aquilia | OPEN |
| F-HTTP-01 | http | pseudo-streaming | BUG | HIGH | [SRC] | _transport.py | media memory/latency | single-yield design | httpx | incremental reads | Aquilia | OPEN |
| F-HTTP-02 | http | pool poisoning on abandoned streams | BUG | HIGH | [SRC] | _transport.py | corrupted follow-ups | finally returns partial conn | httpx; per-call clients | drain-or-close | Aquilia | OPEN |
| F-HTTP-03 | http | RetryConfig never consumed | MISSING | MEDIUM | [SRC] | config.py | silent no-op | unwired | unused | wire or remove | Aquilia | OPEN |
| F-HTTP-04 | http | ProxyConfig ignored | MISSING | MEDIUM | [SRC] | config.py | silent no-op | unwired | unused | implement or remove | Aquilia | OPEN |
| F-HTTP-05 | http | per-request follow_redirects ignored | BUG | LOW | [SRC] | session.py:200 | API promise unfulfilled | config-only check | — | honor flag | Aquilia | OPEN |
| F-HTTP-06 | http | Set-Cookie dict join contradicts docs; session jar broken | BUG | MEDIUM | [SRC] | response.py, session.py | cookie loss | dict collapse + single parse | get_headers()/httpx | exclude from join | Aquilia | OPEN |
| F-HTTP-07 | http | no total deadline; pool timeout unused | MISSING | MEDIUM | [SRC] | _transport.py | slow-trickle bodies | unenforced | httpx | enforce | Aquilia | OPEN |
| F-HTTP-08 | http | streaming request bodies silently dropped | BUG | MEDIUM | [SRC] | _transport.py | no-body requests | bytes-only builder | unused | support iterators | Aquilia | OPEN |
| F-HTTP-11 | http | pool.py dead code; singleton client shares one cookie jar | DESIGN | LOW | [SRC] | pool.py, session.py | confusion; multi-site scrapers unusable via DI client | unused implementation | per-call clients | remove or wire | Aquilia | OPEN |
| F-CA-01 | cache | get_or_set can't cache None | DESIGN | LOW | [SRC] | service.py | recompute loops | fast-path check | producers raise | None sentinel | Aquilia | OPEN |
| F-CA-02 | cache | get/set never raise | DESIGN | LOW | [SRC] | service.py | silent degradation | by design | accepted | error hook | Aquilia | OPEN |
| F-CA-03 | cache | l1_ttl dead config | BUG | LOW | [SRC] | core/di_providers/memory | config pretends | MemoryBackend lacks TTL param | avoid composite | add TTL param | Aquilia | OPEN |
| F-CA-04/06/07 | cache | set_many/touch/get_many tag+atomicity gaps | BUG | LOW | [SRC] | backends | tag invalidation gaps | partial impls | unused | complete or document | Aquilia | OPEN |
| F-CA-08 | cache | redis_decode_responses ignored | BUG | LOW | [STUDY] | redis.py | config no-op | hardcoded | unused | honor config | Aquilia | OPEN |
| F-CA-09 | cache | doubled key prefix | DX | LOW | [LIVE] | service/redis backends | surprising keys | two prefixes | known | document | Aquilia | OPEN |
| F-TA-01 | tasks | memory backend loses jobs | DESIGN | LOW | [SRC] | engine.py | warm-up loss | in-process store | accepted | Redis backend if needed | AniWave | NOT APPLICABLE |
| F-TA-02 | tasks | no per-queue rate limiting | MISSING | LOW | [SRC] | __init__.py | — | deliberate | — | — | Aquilia | NOT APPLICABLE |
| F-TA-03 | tasks | fail_orphaned_dependents missing | BUG | MEDIUM | [SRC] | engine.py | WAITING-forever dependents | docstring references nonexistent API | no deps used | implement or fix docs | Aquilia | OPEN |
| F-TA-04 | tasks | per-process scheduler duplication | DESIGN | MEDIUM | [SRC/STUDY] | engine.py | duplicate periodic jobs (multi-worker) | no leader election | single instance | leader election | Aquilia | OPEN |
| F-TA-05/07/08/09 | tasks | stop() abandonment; args not versioned; O(n) redis ops; cron no tz | DESIGN | LOW | [STUDY] | engine/backends | edge cases | documented trade-offs | unused | — | Aquilia | OPEN |
| F-EN-01 | engine | nested contract errors mangled | BUG | HIGH | [LIVE]×2 | engine.py:1011 | useless nested messages | list() over dict | none app-side | recursive flatten | Aquilia | OPEN |
| F-EN-02 | engine | throttle before guards | DESIGN | MEDIUM | [SRC] | engine.py:243/321 | auth-order violations | execution order | interceptor | reorder/document | Aquilia | OPEN (worked around) |
| F-EN-03 | engine | path params un-cast | DESIGN | MEDIUM | [SRC] | engine.py:1104 | per-app casting | no cast step | int_path_param | annotation casting | Aquilia | OPEN (worked around) |
| F-CORE-02 | request/contracts | path_params method breaks merge | BUG | HIGH | [LIVE] | request.py:1881, integration.py:476 | path params can't feed contracts | type mismatch | plain params | property | Aquilia | OPEN |
| F-CORE-05 | runtime/config | cwd-relative workspace load, silent | BUG | HIGH | [LIVE] | runtime.py:356 | unconfigured boot | relative path | run from backend/ | absolute path | Aquilia | OPEN (documented) |
| F-CORE-06 | DI/auth | string-token-only auth components | DESIGN | MEDIUM | [LIVE]×2 | server.py:514 | type injection fails | registration choice | Inject("…") | class tokens | Aquilia | OPEN (worked around) |
| F-CORE-07 | DI/factory | singleton → base container | DESIGN | MEDIUM | [LIVE] | factory.py | singleton unusable | container choice | per_request | owning-module container | Aquilia | OPEN (reverted) |
| F-CORE-08 | contracts | attribute-access traps | BUG | MEDIUM | [LIVE]×2 | core.py | silent None / spurious 500 | class-attr shadowing | annotation-only convention | metaclass fix | Aquilia | OPEN (convention) |
| F-CORE-09 | contracts | model binding auto-requires columns | DESIGN | LOW | [LIVE] | core.py | PUT contracts 400 | derivation defaults | Spec.fields=[] | non-required default | Aquilia | OPEN (worked around) |
| F-CORE-10 | contracts | stacked Cast-failed prefixes | DX | LOW | [LIVE] | facets.py | noisy messages | child wrap | renderer strips | single prefix | Aquilia | OPEN (app cleanup) |
| F-CORE-11 | framework | own code uses deprecated seal_* | BUG | LOW | [LIVE] | providers/render/types.py | warning noise; 2.0.0 validators silently off | hygiene | none | migrate to @ward | Aquilia | OPEN |
| F-CORE-12 | framework | dotenv ordering warning under pytest | DX | LOW | [LIVE] | dotenv/testing | cosmetic | plugin load order | none | defer load | Aquilia | OPEN |
| F-CORE-13 | docs | orm path/GUIDE §11/imprint signature | DOCS | LOW | [SRC/STUDY] | GUIDE.md, examples | misleads users | doc drift | source docstrings | fix docs | Aquilia | OPEN |
| F-CO-04 | contracts | imprint(db=) form doesn't exist | DOCS | LOW | [SRC] | core.py | example misleads | API drift | imprint(instance=) | fix examples | Aquilia | OPEN |
| F-CO-LEAK | contracts | __all__ projections leak model secrets | SECURITY | MEDIUM | [LIVE] | projections | refresh_token_hash in output | default includes all columns | explicit projections | exclude sensitive by default | Aquilia | OPEN (app uses explicit lists) |
| F-OR-01 | ORM | find_or_create key validation vs filter/create | BUG | HIGH | [LIVE] | models/base.py:908 | baseline 6 failures | inconsistency | filter-then-write | accept FK column keys | Aquilia | OPEN (app workaround) |
| F-OR-03/04 | ORM | bulk skips signals; RelatedNotLoaded sentinel | DESIGN | LOW | [SRC/STUDY] | models | porting sharp edges | deliberate | known | document | Aquilia | OPEN |
| F-AU-01 | auth | protect-by-default locks admin | DESIGN | MEDIUM | [SRC] | admin, auth/state.py | unusable posture | no @Public on admin | module guards | mark admin public | Aquilia | OPEN (worked around) |
| F-AU-06 | auth/sessions | session cookie on every API response | COMPAT | LOW-MEDIUM | [LIVE] | workspace sessions config | Node deviation, store growth | global session engine | accept | scope sessions to admin | Aquilia/AniWave | OPEN |
| A-SESS | tests | QueryAwareClient shim needed | DX | LOW | [LIVE] | tests/conftest.py | test friction | TestClient can't take inline path?query | shim | accept query strings | Aquilia | OPEN (worked around) |

---

## 20. Most Important Final Summary

## Critical Bugs

- **A-01 (FIXED)**: migrated provider layer entirely dead — transport override returning `dict` where the framework unpacks tuples; only the third-party fallback pipe kept the app superficially alive.
- **F-MAN-01 (OPEN; app worked around)**: `aq run`'s validator resolves manifest refs as module-relative file paths — framework and cross-module refs falsely error, so the dev CLI cannot start an app the server runs fine (the bug that triggered this audit; AniWave fixed by dotted-form guards, verified: `aq run` boots, 108/108 tests).
- **F-EN-01 (OPEN)**: engine destroys nested-contract validation messages.
- **F-CORE-02 (OPEN)**: `request.path_params` is a method — documented contract path binding silently dead.
- **F-CORE-05 (OPEN)**: workspace config loads relative to cwd and fails silently; the app boots unconfigured from the wrong directory.

## Critical Missing Features

- A production-grade HTTP client in `aquilia.http` (streaming, cancellation-safe pooling, wired retry/proxy config, config-to-transport propagation).
- Typed path-parameter casting in the engine.
- Class-token DI registration for auth components; module-container-aware singleton controllers.
- Session middleware scoping (admin-only) so API responses don't carry session cookies.

## Critical Framework Gaps

- Engine throttle ordering (before guards) makes the built-in throttle unusable for auth-aware limiting.
- ORM lookup-key inconsistency (`user_id` accepted by filter/create, rejected by find_or_create).
- Cache: dead `l1_ttl` config, None-unfriendly `get_or_set`, tag loss on bulk paths.
- Tasks: docstring-referenced `fail_orphaned_dependents` doesn't exist; per-process scheduler duplication risk.
- Contracts: attribute-access traps; `__all__` projections leaking model secrets by default.

## Critical AniWave Gaps

- `backend/requirements.txt` missing httpx (deploy breakage; one-line fix, unfixed).
- No provider HTTP-layer test, no rate-limit e2e, no admin/session/Specula coverage.
- Unbounded provider caches; `providers_status` unwired; repo still carries the Node tree and a stray sqlite file; API responses set admin session cookies (deviation).

## aquilia/http vs httpx Final Verdict

**httpx, decisively — on source-verified evidence, not preference.** Whole-body buffering before the first yield; partially-read connections returned to the pool on abandonment (the racing engine's core pattern); a Set-Cookie dict path contradicting its own docstring; retry and proxy config silently ignored; no total deadline; per-request redirect flags that do nothing; and the constructor-timeout seam that silently disabled every provider budget. Aquilia HTTP's genuine advantages — zero dependencies, typed faults — don't offset these for scraping and media workloads. Revisit only after the framework fixes streaming, pooling, and config wiring; the `HTTPTransport` seam is the natural httpx-wrapping point.

## Aquilia Cache Final Verdict

**Working and adopted.** Redis backend, namespaced keys, TTLs, and `get_or_set` single-flight all behaved correctly under real integration. Defects live in corners AniWave doesn't use (composite L1 TTL, bulk tag fidelity, None caching, touch atomicity). Keep; no app-side concerns.

## Aquilia Task Final Verdict

**Sufficient for AniWave's actual workload, unproven beyond it.** Fire-and-forget warm-up with timeout and workers works; memory-backend restart loss is acceptable because warm-up self-heals. Durable/workflow needs would require the Redis/SQL backend and fixes (or avoidance) of dependency orphaning and multi-process scheduling. AniWave has no such workloads.

## Provider System Final Verdict

**Restored to reference behavior and verified live** (10/10 providers, fast-tier merge 7.2 s, watch race 1.5 s to real HLS). The original migration's losses — fatal transport bug, ignored timeouts, cookie case-sensitivity, regressed race budgets, mis-mapped 422s — are all fixed. Remaining weaknesses are operational: scraper rot with no canary or status route, unbounded caches, untested fallback.

## Production Blockers

1. `backend/requirements.txt` missing httpx (one-line fix).
2. Deployment must start from the workspace root (F-CORE-05) — enforced only by documentation.
3. No automated verification of the provider HTTP layer or rate limiting — the failure classes that already shipped once.

## Recommended Next Engineering Phase

Prioritized by demonstrated ship-cost:

1. **Fix `backend/requirements.txt`** (minutes).
2. **Add the provider HTTP-layer test and rate-limit e2e scenarios** (§17.1–17.2).
3. **Bound the provider caches** and **expose `GET /api/providers/status`** as a scraper-health canary.
4. **Push the framework one-liners upstream** (path_params property, nested-error flatten, absolute workspace path, FK lookup keys, auth class tokens) — each verified, each currently worked around app-side.
5. **Add a scheduled live scraper smoke suite** so provider rot pages someone instead of silently degrading to the fallback pipe.
6. Decide the session-cookie deviation (accept or scope sessions to /admin).

---

# Appendix D — Session Debugging Log (everything encountered, chronologically)

The narrative record behind the findings above. Every error below was actually hit; resolutions in brackets.

## D1. Provider / HTTP phase

1. **`ModuleNotFoundError: No module named 'httpx'`** when smoke-testing with system `python3` instead of the project venv — environment discipline issue, resolved by always using `uv run`/`.venv/bin/python`. [env]
2. **`uv add httpx` downgraded aquilia 1.4.1 → 1.4.0** (the lock still said 1.4.0 while 1.4.1 was installed — pre-existing drift). Re-pinned `aquilia[postgres]>=1.4.1`; lock now says 1.4.1. [A-08, fixed]
3. **The fatal transport bug** (A-01): reproduced by the audit agent with a local double-Set-Cookie server and live requests — `TransportFault: too many values to unpack (expected 2)` on every `_http` call while `anilist_query` (stock client) succeeded in the same run. The smoking gun: the override returned a dict; the caller unpacks 2-tuples. [fixed by httpx switch]
4. **Ignored timeouts** (A-02): verified `AsyncHTTPClient(timeout=20.0, transport=NativeTransport())` leaves the transport at 30.0 — the session doesn't propagate config to user transports. [fixed by httpx]
5. **mkissa cookie case-sensitivity** (A-03): `headers.get("set-cookie")` vs `Set-Cookie`. [fixed by httpx case-insensitivity]
6. **Print→logging conversion script inserted `import logging` inside a module docstring** (`api.py` opened mid-docstring) — my tooling bug; repaired by hand. [fixed]
7. **Racing regressions** (A-04) discovered by diffing backend `_race.py` against the reference: budgets 75/60/45 vs 15/6/600, 8 s drain, single-phase episodes. Restored reference semantics; updated the test that had codified the regressions. [fixed]
8. **Bash cwd flip-flopping** between project root and `backend/` repeatedly broke relative-path scripts mid-session — switched to absolute paths. [env]

## D2. Auth / config phase

1. **`PROVIDER_NOT_FOUND: aquilia.auth.tokens.TokenManager`** on the first auth e2e run — TokenManager is registered under a *string* token; type injection fails. Fixed with `Annotated[TokenManager, Inject("aquilia.auth.tokens.TokenManager")]`. [F-CORE-06]
2. **The same error persisted under pytest while in-process boots worked** — the longest debug of the session:
   - reproduced with a private runtime inside pytest → still failed;
   - ran the identical script as plain Python with the same env → worked (201);
   - printed the server's resolved config: **`AUTH-CFG: None` under pytest, full section in plain Python**;
   - bisected env vars → not env;
   - root cause: `ConfigLoader.load(paths=["workspace.py"])` is cwd-relative; pytest's rootdir was the repo root, plain runs were in `backend/`. Module discovery uses an absolute path, so the app still booted — masked. [F-CORE-05]
3. **`'Identity' object has no attribute 'session_id'`** (500 on `/api/auth/sessions`) — the engine fell back to the framework `Identity` because `principal_factory` had been omitted from the workspace auth config during the rewrite. Fixed by wiring `app.principals:build_principal`. [integration bug, fixed]
4. **Unauthorized-matrix failure**: framework AUTH codes all rendered as "Authentication required"; the Node contract distinguishes missing-header vs invalid-token messages. Fixed by splitting the renderer mapping (AUTH_010 generic; AUTH_002/003/004 invalid-token). [fixed]
5. **`_playlist_cache` AttributeErrors in stress/streaming tests** — tests referenced the removed module global after the CacheService migration. Rewired fixtures to `get_default_cache_service().clear(namespace="default")`. [fixed]
6. **Streaming stub rewrite on httpx**: first attempt used a sync `MockTransport` handler calling `run_until_complete` inside a live loop (`coroutine ... never awaited`); fixed with async handlers. [fixed]
7. **`test_playlist_upstream_failure` returned 200 instead of 502**: two-layer cause — (a) a stale resolve-cache key in the shared test Redis served an old token whose playlist was also cached (flushing Redis fixed the isolation), and (b) a genuine double-patch bug in the test: it captured `real_client = httpx.AsyncClient` *after* `hls_stub` had already patched it, so the "failing" client delegated back to the healthy stub. Fixed with an import-time pristine reference. [fixed]
8. **`NameError: name 'user' is not defined`** (500 on notifications/read) — my regex-based controller conversion missed `notifications_read` (its signature includes `body`, so the single-ctx pattern didn't match). Fixed the signature. [fixed]
9. **Pre-existing library ORM bug** (A-05): watchlist/progress/notifications 500 with `Unknown field: 'user_id'` — verified at baseline via a pristine git worktree (6 failing tests). Fixed with filter-then-write upserts. [fixed]
10. **Health `version` assertion** failed after correcting the hardcoded `"0.0.0"` to the workspace `1.0.0` — test updated. [fixed]
11. **`uv run pytest` from the repo root vs `backend/`** — the F-CORE-05 trap codified: tests must run from `backend/`. [documented]

## D3. Deep-contracts phase

1. **`body.device` returned `None` despite a valid payload** — the `= None` class-assignment shadows `__getattr__` (F-CORE-08a). Diagnosed by dumping `validated_data` (device present) vs attribute access (None). Fixed by removing all `= None` assignments. [fixed]
2. **`'CommentsQuery' object has no attribute 'before'`** on absent optional field — raw `DateTimeFacet` in `Annotated` becomes a descriptor that raises when missing (F-CORE-08b). Fixed by the annotation-derived form (`Annotated[datetime | None, Field(required=False)]`). [fixed]
3. **`TypeError: Expected a slice`** when the service iterated `body.keys` — declared-facet fields return the *facet object* on attribute access. Fixed by moving `ListFacet` into `Annotated` for that field. [§8.7]
4. **Preferences PUT 400 "email/password_hash required"** — model binding auto-requires all columns (F-CORE-09). Fixed with `Spec.fields = []`. [fixed]
5. **`__all__` projection leaked `refresh_token_hash`** into a molded session view during bring-up — caught by printing the dict; switched to explicit projection lists. [F-CO-LEAK]
6. **`platform` key missing from session output** when null — `ReadOnly()` skips None without `allow_null=True`. Fixed. [§8.6]
7. **Nested device error still mangled** (`message: "deviceId"`) after my renderer flattening — traced to the *engine* mangling nested dicts before app code (F-CORE-01). Not app-fixable. [OPEN]
8. **`SessionIdContract` path binding failed** ("This field is required" with a valid UUID in the path) — led to discovering `request.path_params` is a method and the integration's `isinstance(dict)` check (F-CORE-02). Reverted to inline UUID validation. [OPEN framework; worked around]
9. **Double "Cast failed for …" prefixes** in list-child messages — renderer now strips iteratively. [F-CORE-10]
10. **`imprint` "data has not been sealed"** when constructing contracts manually in a debug script — imprint requires sealed data; PATCH auto-partial is what makes the endpoint path work. [F-CO-04, documented]
11. **preferences PUT failing before `Spec.fields=[]`** — see 4; also confirmed PATCH auto-partial behavior for UpdateProfileContract. [fixed]

## D4. Controller-features phase

1. **Singleton experiment broke 38 tests** with `PROVIDER_NOT_FOUND: modules.auth.services.AuthService` — singleton controllers resolve from the base container (F-CORE-07). Reverted to per_request. [OPEN framework]
2. **Rate-limit interceptor verification**: with limiting enabled, 10×201 then 429 with the exact Node envelope; 30 unauthenticated 401s left the bucket untouched; a valid request passed. One script bug on the way: the "valid" token was `None` because the enabling register had itself been rate-limited (429) — diagnosed from `Bearer None` → AUTH_002. [verified]
3. **Throttle-vs-guards ordering confirmed in source** (engine.py:243 vs :321) — engine throttle unusable for auth-ordered limiting; interceptor is the correct seam. [F-EN-02]

## D6. Manifest / `aq run` phase (2026-09-16, post-report)

1. **`aq run` refused to start AniWave**: "Import error in auth: aquilia.auth.guards:AuthGuard (file not found: modules/auth/aquilia/auth/guards.py)" — despite the server booting and all 108 tests passing with those guards. Located the validator (`cli/commands/run.py:278–330`): it regex-scrapes quoted colon-strings from manifest TEXT and resolves them as file paths relative to the module's own directory — `aquilia.auth.guards:AuthGuard` became `modules/auth/aquilia/auth/guards.py`. [F-MAN-01]
2. **Reproduced with crafted workspaces** by calling `_validate_workspace_config` directly: framework-guard refs AND cross-module service refs both false-positive; own-module refs with real files pass. Also confirmed `aq doctor` implements the same check correctly (resolves from workspace root, skips non-`modules.*` refs) — one CLI right, one wrong. [F-MAN-01]
3. **Found the crash variant**: a manifest containing `"redis://localhost:6379"` (string ending in `:word`) kills the whole validation with "Unexpected error during validation: too many values to unpack" — reproduced. [F-MAN-02]
4. **Mutation audit**: hashed workspace.py + all manifests before/after `aq run` — byte-identical in our case (components matched discovery), but the "✅ Updated workspace.py" message prints even for no-op writes, the rewriter collapses 3+ blank lines file-wide, and mutation happens BEFORE validation with no rollback on failure. [F-MAN-04/05]
5. **Discovery audit**: the CLI's manifest sync ignores `auto_discover=False`, and its differ auto-REMOVES own-module refs that pattern-based discovery can't see — a data-loss path for valid hand-written entries. [F-MAN-06/07]
6. **manifest.py audit**: fingerprint omits base_path/session/versioning/features/template; imports/depends_on "sync" only when one side is empty; `Module.register_*` discard arguments; ComponentRef can't express the dotted form that the (broken) validator requires. [F-MAN-08..13]
7. **App-side fix applied and verified**: manifest guards switched to the dotted form `aquilia.auth.guards.AuthGuard` — the server resolves it identically (`_resolve_guard_reference` rsplit), the broken regex ignores it. `aq run` now boots past validation to the dev-server banner; workspace.py hash unchanged by the run; **108/108 tests pass** (guard enforcement covered by the 401 matrix).

## D5. Verification-phase anomalies

1. **`NO-AUTH: 200`** in one early live script (unauthenticated `/api/auth/me` returning 200 after a prior authenticated call on the same client). Isolated reruns: 401. Session-cookie authentication explicitly tested and ruled out (cookie present, still 401). **Unreproducible; recorded as [ONCE] (A-19).**
2. **Register sets `aquilia_admin_session` on every response** — discovered while chasing A-19; verified the cookie never authenticates API routes; documented as a behavior deviation (F-AU-06).
3. **`redis-cli` not installed** on the host — Redis flushed via the python client instead. [env]
4. **60 `RenderDeployConfig.seal_*` deprecation warnings** in every pytest run — the framework deprecating its own code (F-CORE-11).
5. **`DotEnvLoader.configure() called after loading — no effect`** warning under pytest (F-CORE-12).
6. **Live provider verification** after all fixes: 10/10 providers load; Frieren episodes merged from 3 fast-tier providers in 7.2 s; watch race resolved real HLS in 1.5 s; full API e2e green (health → live search → register → me → 401 matrix → watchlist → live resolve). [LIVE]

---

*End of report. The engineering truth of this migration: the framework's core request/response/DI/ORM/contracts machinery held up under real integration; the provider-critical HTTP stack did not; and the sharpest framework edges (cwd-relative config, path-param binding, nested error fidelity, DI token spellings) were all found the hard way — by things breaking in ways that initially looked like app bugs.*
