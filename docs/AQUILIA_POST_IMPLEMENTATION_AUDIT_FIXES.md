# Aquilia Post-Implementation Audit — Forensic Verification & Fix Report

Date: 2026-09-16
Scope: full forensic audit of the `aquilia/` framework against the findings recorded in [`AQUILIA_POST_IMPLEMENTATION_FINDINGS.md`](AQUILIA_POST_IMPLEMENTATION_FINDINGS.md) (the AniWave migration report), plus an independent hunt for additional defects across every subsystem. All fixes ship in the **v1.4.2 "Depths Unknown"** release.

**Method.** Nine specialized auditors worked in parallel over the whole framework (HTTP client, controller engine + request/response, contracts, config/DI/runtime, ORM/DB, cache, tasks, CLI/manifest/discovery, auth/sessions/admin, plus a cross-cutting hygiene sweep). Every report claim was re-verified against the current source and — wherever feasible — reproduced at runtime with standalone scripts before being accepted; two independent cross-review validators then stress-tested the fix designs for the two highest-risk subsystems (contracts, HTTP) before implementation. Every fix ships with permanent regression tests.

---

## 1. Verdict on the reported findings

Of the report's framework findings: **every one verified true against the current source except one** (F-CORE-06, auth string-token DI — refuted: class tokens and string tokens normalize to identical dotted keys in this codebase, so constructor injection of `TokenManager`/`PasswordHasher` already works; the report's failure mode predates the 1.4.1 auth rebuild). The audit also surfaced a large set of previously-unreported defects, several more severe than anything in the report.

### Table of confirmed report findings and their resolution

| Finding | Verdict | Resolution in this pass |
|---|---|---|
| F-CORE-01 / F-EN-01 nested contract errors mangled (`list()` over dict) | CONFIRMED [LIVE] | Fixed: engine `_merge_contract_errors` recurses to dotted paths; `SealFault` details flatten the same way |
| F-CORE-02 `Request.path_params` is a method | CONFIRMED [LIVE] | Fixed: converted to `@property`; also repairs contract path binding, clearance compartments, GuardContext, debug pages, DI `Path` resolution (six silently-broken call sites) |
| F-CORE-03 path params un-cast | PARTIALLY (router pre-casts typed params; failure mode is 404-not-400 and non-int/float/bool/str annotations degrade to str) | Documented; residual gap noted |
| F-CORE-04 throttle before guards | CONFIRMED | Documented (interceptors-after-guards is the correct seam; semantic reorder deferred — genuine trade-off) |
| F-CORE-05 workspace config cwd-relative, silent | CONFIRMED [LIVE] | Fixed: runtime passes the absolute workspace file; loader warns on missing paths |
| F-CORE-06 auth string-token DI | **REFUTED** (stale post-rebuild — tokens unify) | No change needed |
| F-CORE-07 singleton controllers resolve from base container | CONFIRMED [LIVE] | Fixed: singletons resolve from the owning module's container with base fallback |
| F-CORE-08 contract attribute-access traps | CONFIRMED [LIVE] (×3 variants) | Fixed: metaclass pops shadowing class attributes; `__getattr__` returns `None` for known absent optionals; class-level facet access preserved via metaclass `__getattr__` |
| F-CORE-09 model-bound contracts auto-require columns | CONFIRMED [LIVE] | Fixed: implicit derivation (`Spec.fields=None`) no longer auto-requires; explicit `Spec.fields` unchanged |
| F-CORE-10 stacked "Cast failed for" prefixes | CONFIRMED [LIVE] | Fixed: `fault_message` strips nested prefixes; list/tuple children get `item {i}:` labels |
| F-CORE-11 framework triggers its own seal_* deprecation | CONFIRMED [LIVE] | Fixed: the four Render validators migrated to `@ward`; validators verified still firing with zero warnings |
| F-CORE-12 dotenv configure-after-load | CONFIRMED (mechanism; pytest-plugin claim false in this repo) | Fixed: ConfigLoader passes config-adjacent `.env` candidates so a foreign-cwd load can't freeze the policy |
| F-CORE-13 docs drift (ORM API, otel, imports, footer) | CONFIRMED | Fixed: GUIDE §11/§22/§23 rewritten against real APIs; 1,063 doc links repaired; every import statement runtime-verified |
| F-MAN-01..13 `aq run` validator / manifest system | ALL CONFIRMED (several [LIVE]) | Fixed: import-based validation shared with doctor/validate; validate-before-mutate; non-zero exit codes; differ never-removes by default (`prune` opt-in); `auto_discover=False` honored; `aq manifest update` no longer destroys lists on import failure; fingerprint covers all fields; honest no-op messages |
| F-HTTP-01..11 HTTP client defects | ALL CONFIRMED [SRC/LIVE] | Fixed: see §2 |
| F-CA-01..09 cache defects | ALL CONFIRMED | Fixed: see §2 |
| F-TA-03..09 task defects | ALL CONFIRMED (F-TA-05 worse than reported) | Fixed: see §2 |
| F-OR-01 FK-column keys rejected by upserts | CONFIRMED [LIVE] | Fixed: `_col_to_attr` normalization across the upsert family, unique-constraint detection, conflict columns, bulk_update |
| F-OR-02..04 ORM design notes | CONFIRMED as documented | get_or_create race documented; RelatedNotLoaded semantics verified sound |
| F-AU-01 protect-by-default locks admin | CONFIRMED (post-rebuild) | Fixed: pre-auth admin routes marked public |
| F-AU-06 anonymous session cookie on every API response | CONFIRMED [LIVE] | Fixed: path-prefix scoping + `persist_anonymous` policy (backwards-compatible defaults) |
| A-19 one-time unauthenticated 200 | EXPLAINED (not a framework leak) | Two mechanisms identified: TestClient default-header persistence, and token→session identity binding (documented on the binding code) |
| F-CO-LEAK `__all__` projections leak model secrets | CONFIRMED [LIVE] [SECURITY] | Fixed: default projection excludes silently-derived model columns (RuntimeWarning fires); explicit `__all__` opt-in preserved |

---

## 2. New defects found by the audit (not in the report)

### Critical / high severity (all fixed)

| ID | Subsystem | Defect | Fix |
|---|---|---|---|
| N-HTTP-HEAD | http | HEAD/204/304/1xx responses misframed (body reader trusts Content-Length with no method/status awareness) — HEAD on keep-alive blocks, misreads, poisons the pool | Framing-aware `_BodyReader` with a NONE mode |
| N-HTTP-HDRS | http | `AsyncHTTPClient(headers=...)` constructor headers **never sent** — the SendGrid provider's Authorization header was dead, every SendGrid send unauthenticated | `config.default_headers/default_params` wired into the send path |
| N-DB-BLEED | db | Cross-task transaction bleed: SQLiteAdapter pinned the writer on the shared instance; request A's rollback silently destroyed request B's committed writes (B received a normal pk, no error) | Per-task transaction connection via ContextVar routing |
| N-DB-CANCEL | db | `db.transaction()` leaked on `CancelledError` (`except Exception` only) — engine wedged permanently after one cancellation | `except BaseException` with rollback |
| N-DB-RACE | migrations | No cross-process migration lock — concurrent boots raced (3 processes → 2 failures) | `cross_process_migration_lock` (flock / advisory lock, best-effort) |
| N-DB-RUNPYTHON | migrations | RunPython ran after history commit — a failing data migration was recorded as applied and skipped forever | RunPython inside the final transactional group |
| N-TA-CANCEL | tasks | A task body raising `CancelledError` killed its worker loop permanently; job frozen RUNNING | Child-task isolation with worker-vs-job cancellation classification |
| N-TA-TIMEOUT | tasks | Task timeout defeatable: a body swallowing cancellation ran to completion, recorded as success (0.2s budget → 1.2s, COMPLETED) | Shielded runner + explicit cancel + elapsed-time enforcement |
| N-TA-STOP | tasks | `stop()` hung FOREVER on Python 3.12+ with a CancelledError-swallowing task (the documented timeout branch unreachable) | `asyncio.wait` bounded loop with re-cancel and detach |
| N-CA-POOL | cache | Redis pool exhaustion silently dropped writes (30/40 concurrent ops failed silently at the default 10-connection non-blocking pool) | `BlockingConnectionPool` |
| N-CA-CLEAR | cache | `clear()` prefix-scan deleted FOREIGN keys sharing the prefix (verified deleting another app's session key) | Registry-driven clear scoped to the service's own keys |
| N-CA-HANG | cache | `MemoryBackend(max_size=0)` froze the entire event loop (infinite eviction loop, no await point) | `<= 0` treated as unlimited + config validation |
| N-CA-MW | cache | CacheMiddleware bodies corrupted through redis/JSON backends (bytes → repr string on every HIT) | Base64 body encoding with legacy-miss fallback |
| N-CLI-DESTROY | cli | `aq manifest update` silently EMPTIED controllers/services lists when the workspace package failed to import | Refuse-to-write on failed scan; AST-aware edits; real controller detection |
| N-CO-EMPTY | contracts | Empty projection list `[]` fell through to `__all__` (every field, contradicting the docstring) — compounds the secrets leak | Empty list → empty output |

### Medium severity (all fixed unless noted)

- **HTTP**: pool poisoning on abandoned/cancelled streams (release gate on clean body completion); trailer sections neither parsed nor drained (next-request corruption); negative chunk size → raw ValueError + poisoned pool; Content-Length truncation silently returned partial bodies; read-until-close timeout swallowed as EOF; redirect chains leaked connections surviving `client.close()`; redirect hops bypassed the cookie jar in both directions; Max-Age cookies never expired; no response-size cap (gzip bombs); corrupt gzip silently returned as raw bytes; `read()` after `iter_bytes()` returned `b""`; per-request `follow_redirects` ignored; proxy config (incl. `trust_env`) silently ignored; retry config dead; unknown session kwargs silently dropped; `MiddlewareStack.build()` crashed in a running loop; IPv6 Host header malformed; URL userinfo silently discarded; non-ASCII headers/paths crashed at the transport (late, untyped).
- **ORM**: `order()`/`values()`/`only()` accepted unknown fields as silent no-ops or string literals; mixed naive/aware datetime comparison wrong on sqlite; legacy `like`/`ilike` skipped LIKE-escaping (`%` matched everything); `iterator()` clobbered a user-set `limit()`; `bulk_create`'s `ignore_conflicts` was sqlite-only syntax + inserts never actually batched.
- **Cache**: `get_or_set` re-computed on every call for `None` loaders; fault emission was dead code (wrong import path, nonexistent API); `l1_ttl` never reached the L1 backend; `set_many` dropped tags on every backend; composite lacked distributed-lock delegation; `touch` lost tags (escaping invalidation); composite `increment` race wrote stale values to L1 (11/15 rounds stale); redis `get_many` lost tags/TTL (promoted into L1 as never-expiring); `redis_decode_responses` config no-op; namespace sets grew without bound; `stats().size` always read db0; `@cached` sentinel collided with a legitimate `"__aquilia_cache_none__"` value; stampede join performed network I/O under the global inflight lock; delete raised where get/set swallowed.
- **Tasks**: dependency-failure propagation implemented (`fail_orphaned_dependents` was docstring-only — dependents stayed WAITING forever on all three backends, including missing-dependency typos); per-process scheduler duplicated periodic jobs across workers (verified 2×; now schedule-slot dedup); unsatisfiable cron expressions fired hourly forever (now a construction fault); non-retryable faults burned the full retry budget; `attempt_epoch` anti-zombie plumbing had no reader (zombie writes clobbered reclaiming workers).
- **CLI/manifest**: differ add-path silently rewrote hand-written refs to same-named classes elsewhere; `--freeze` was a no-op on keyword-form manifests; injection into commented-out lists; module-name quoting inconsistency let single-quoted workspaces bypass validation entirely; `aq add --depends-on` validated against comment lines.
- **Engine/middleware**: `Response(headers=...)` bypassed CRLF validation; `RequestIdMiddleware` echoed unsanitized inbound IDs verbatim; malformed JSON bodies reported per-field "required" instead of invalid-JSON; filter/pagination failures fail-open (returned unfiltered data — ACL-bypass class; now fail closed); legacy route compiler mangled `module:Class` refs into a fabricated `apps.*` path and print-swallowed the failure.
- **Config/DI**: subsystem config `or`-shadowing discarded typed integrations when a single env var created a root section (typed Redis URL silently vanished); `ControllerFactory.shutdown()` never called (singleton `on_shutdown` leaked); malformed workspace.py raised opaque AttributeErrors from deep in the loader.
- **Auth/sessions/admin**: admin session fixation (rotation code was dead — `Session.regenerate` didn't exist; pre-login session ID survived authentication); full identity incl. superuser roles serialized into admin sessions (privilege revocation lagged up to 30 days); env-superuser fallback active in production with no mode gate and non-constant-time compare; `aq admin` generator hardcoded `cookie_secure=False`; anonymous-session store churn (1 stored session per cookie-less request); password-backend username-enumeration timing; TOTP code replay within window.

### Not fixed (deliberate decisions — recorded for maintainers)

- **Token→session identity binding** (a Bearer-authenticated request binds the identity into the session, after which the cookie alone authenticates — the A-19 anomaly's framework-side mechanism): kept, now documented on the binding code with its CSRF implications; an opt-out flag is the right next step but changes authentication semantics and needs a maintainer decision.
- **Engine throttle-before-guards ordering**: reorder is a genuine semantic trade-off (DoS protection vs auth-order correctness); interceptors remain the correct seam. Documented.
- **otel subsystem**: orphaned (not wired into integrations); GUIDE §22 now documents it as manual/experimental. Wiring or removing it is a roadmap decision.
- **`aquilia/http/pool.py`**: deprecated (import-time warning), removal planned for 2.0.0. The live pool absorbed its useful ideas (waiting acquire, stats, keepalive cap).
- **In-flight connection bounding defaults, response-size cap (64MB), total-deadline coverage of the full body**: behavior changes documented in the changelog; escape hatches provided (`TimeoutConfig.slow()/no_timeout()`, `max_response_size=None`).

---

## 3. Test coverage added

New regression test files (all green):

- `tests/test_core_audit_fixes.py` — engine/config/request/response core fixes (35 tests)
- `tests/test_orm_audit_fixes.py` + `tests/test_db_transaction_fixes.py` — ORM/DB (59 tests)
- `tests/test_cache_audit_fixes.py` — cache (54 tests)
- `tests/test_tasks_audit_fixes.py` — tasks (41 tests)
- `tests/test_contract_attr_and_projection_fixes.py` — contracts attribute/projection fixes (53 tests)
- `tests/test_http_client_overhaul.py` — HTTP client overhaul (36+ tests, real-socket loopback servers)
- `tests/test_cli_manifest_audit_fixes.py` — CLI/manifest
- `tests/test_auth_sessions_audit_fixes.py` — auth/sessions/admin

Full suite at the end of the pass: **see §5**.

## 4. Fixed-then-broken-again guardrails worth knowing

- The contracts metaclass fix (popping shadowing class attributes) required careful ordering: popping before annotation introspection silently drops defaults (fields flip required); underscore-prefixed names must be excluded (would delete `Contract._active_groups`); read-only fields must be included in the synthetic-`None` set (they never enter validated data).
- The HTTP streaming decompressor's first implementation looped forever on multi-member gzip (`unused_data` prepended to `pending` replayed members); caught by its own regression test and fixed before commit.
- The tasks `stop()` rewrite required per-pass small timeouts with re-cancel delivery — a single full-deadline wait starved the re-cancel and hung.

## 5. Final verification

- Full suite: 9,646 baseline → **10,053 passed, 0 failed, 9 skipped** with all fixes (+407 new regression tests across 9 new test files).
- `ruff check` clean on the entire `aquilia/` package.
- Docs: every import statement in GUIDE.md/README.md runtime-verified; 1,063 broken doc links repaired.

---

*The engineering truth of this pass: the migration report's sharpest findings were all real, but the independent hunt found the worst defects somewhere else entirely — in the corners no application touches: HEAD requests, multi-member gzip, concurrent boots, cancellation inside transactions, one-worker death per CancelledError, and a dev CLI that could delete its users' manifest declarations.*
