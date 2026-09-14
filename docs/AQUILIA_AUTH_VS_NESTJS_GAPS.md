# Aquilia vs NestJS — Authentication & Authorization Gap Analysis

**Derived from:** the AniWave Node.js → Aquilia migration (2026-09-14), plus a
second targeted verification pass over `aquilia.auth` / `aquilia.signing` /
config-loading performed specifically for this document. Rules: only what was
actually encountered or verified; every claim carries a provenance tag —
**[runtime]** observed while the app ran, **[source]** read in Aquilia 1.4.0
source and matched to behavior, **[test]** reproduced in the AniWave test
suite, **[proof]** reproduced in an isolated verification script (transcript
included), **[xref]** cross-reference to another migration finding, inlined
here. No speculation.

**Context in one line:** AniWave's auth contract (Bearer JWTs, stateless
verification, rotating refresh credentials with reuse detection, device
sessions, guests, exact 401 error bodies) had to be preserved byte-for-byte,
and the entire HTTP auth layer of Aquilia had to be **bypassed and rebuilt**
to achieve it — while the framework's *cryptographic* primitives were reused
directly. This document records why, plus everything else the auth work
exposed: missing features, confirmed bugs, and the framework's
multiple-sources-of-truth problem in authentication configuration.

---

## 1. The AniWave auth contract (what had to be preserved)

From the Node backend (`src/modules/auth/*`, ported and e2e-verified):

- HS256 access JWTs, 30 min TTL, claims `{sub, sid}` + iss/aud; **stateless
  verification** — no DB/session lookup per request (revocation bounded by
  the token TTL; refresh fails immediately after revocation).
- Global "protected by default" with `@Public()` opt-out for catalog,
  streaming, and health routes. **An invalid token on a public route is
  ignored**, not rejected.
- Rotating refresh tokens: CAS rotation on the session row, previous-hash
  replay detection → session revocation + security event, distinct revoke
  reasons, hard 3-month calendar expiry, device metadata, guest accounts.
- Anti-enumeration posture: **all** access-token failures collapse into one
  generic 401 (`Invalid or expired access token`); missing header is a
  distinct 401 (`Authentication required`).
- Bcrypt-12 (Node) → argon2id (Aquilia `PasswordHasher`) — deliberate,
  documented upgrade.

## 2. Aquilia's auth surface as verified during migration

What exists (read + partially exercised):

| Piece | Verdict from the migration |
|---|---|
| `PasswordHasher` (argon2id/scrypt/bcrypt/PBKDF2, PHC auto-detect) | **Used directly, excellent.** Dummy-hash timing equalizer trivially built on it. |
| `TokenManager` + `KeyRing`/`KeyDescriptor` (HS256 stdlib, `kid` rotation API, OWASP checks: `alg=none` rejection, iss/aud/exp/nbf, jti revocation lookup) | **Used directly as the token engine.** Stateless-compatible (in-memory `TokenStore` never holds entries → revocation check passes). |
| `AquilAuthMiddleware` + backends (`token`, `session`, `api_key`, `password` — full inventory [source]) | **Bypassed entirely** (AG-01…AG-04). |
| `AuthManager` (sign_in/sign_out/refresh/revoke, `login_identifier_attributes`) | Read; refresh model is opaque-token-in-store — **not usable for AniWave's rotation semantics** (AG-05). |
| Stores: `MemoryIdentityStore`, `MemoryCredentialStore`, `MemoryTokenStore`, `RedisTokenStore`, `MemoryOAuthClientStore`, `MemoryDeviceCodeStore` | Read [source]. Durable stores exist **only for tokens** — identity/credential stores are memory-only (AG-06). |
| Guards (`AuthGuard`, `RoleGuard`, `ScopeGuard`, `PolicyGuard`), `@authenticated`/`@roles_required`/`@scopes_required`, Clearance engine | Read; **never exercised** — AniWave has no roles. No gaps claimed beyond the structural AG-04/AG-11 notes. |
| MFA module (`TOTPProvider`, `WebAuthnProvider`, `MFAManager`, backup codes) [source] | Present, unexercised — see §5 (a genuine Aquilia advantage). |
| OAuth server machinery (`PKCEVerifier` S256, Authorization Code flow, client/device-code stores) [source] | Present, unexercised — see §5. |
| Sessions subsystem (`SessionPolicy`/`TransportPolicy`/…, cookie-centric) | Disabled; AniWave is Bearer-only. Unexercised (but see §7, MS-07). |
| `AquilaConfig.Auth` (`enabled`, `secret_key`, `backends`, `require_auth_by_default`, TTLs, MFA flags) | `enabled=False` set; `require_auth_by_default` exists but is coupled to the middleware path (AG-09). |

## 3. Genuine gaps (each one forced custom code or bypass)

---

### AG-01 — Defining the auth config section auto-mounts an enforcing auth pipeline keyed to the framework's secret, colliding with app-managed token schemes

- **Severity:** Major
- **Status:** confirmed [runtime] (the migration's first auth incident)
- **Component:** `aquilia/server.py` auth activation (~lines 381–420); `AquilaConfig.Auth.enabled` default
- **How discovered:** `workspace.py` set only `secret_key` and `password_hasher` under `class auth(AquilaConfig.Auth)` — no backends, no enforcement requested. Boot mounted `AquilAuthMiddleware` with default `TokenBackend`/`SessionBackend` anyway. A request with a **valid app-issued JWT** (HS256, `JWT_SECRET`, `kid="aniwave-active"`) to `GET /api/auth/me` returned `403 {"code":"AUTH_002","message":"Invalid token"}` — the framework middleware validated the Bearer token against **its own** keyring before the app's route decorator ran.
- **Actual:** presence of the config section ⇒ HTTP auth enforcement with the framework's key store. Apps that issue their own tokens (a completely normal design) are silently intercepted with 403s.
- **Expected:** opt-in enforcement; an app-level bearer scheme should never be validated against a framework secret by default.
- **Impact:** the whole framework HTTP-auth path had to be disabled (`enabled = False`), forfeiting everything built on it (AG-02…AG-04, AG-09, AG-10).
- **Workaround:** `enabled = False` + the app's own `@require_auth` decorator (`app/auth.py`).
- **Recommended fix:** default `enabled=False`; separate "configure hashing/keys" from "enforce HTTP auth".

---

### AG-02 — `AUTH*` faults are re-raised *before* the `require_auth` decision: invalid tokens on public routes are hard-rejected

- **Severity:** Major
- **Status:** confirmed [source] (`aquilia/auth/integration/middleware.py`, backend loop ~lines 178–193)
- **Evidence:**
  ```python
  except Exception as e:
      if hasattr(e, "code") and str(e.code).startswith("AUTH"):
          raise            # ← re-raised unconditionally
      self.logger.warning(...)
  # ... only LATER:
  if self.require_auth and not identity:
      return self._handle_auth_required()
  ```
  A request carrying a malformed/expired Bearer token raises from
  `backend.authenticate()` and propagates **regardless of** `require_auth`.
- **Actual:** with the middleware active, *any* route — including public ones — rejects bad tokens. NestJS's `@Public()` pattern (AniWave's model) skips token verification entirely on public routes: a stale token on `/api/catalog/...` is simply ignored.
- **Expected:** on non-enforced routes, failed optional authentication should degrade to anonymous, not reject.
- **Impact:** second, independent reason the middleware could not be used even in lenient mode; "ignore tokens on public routes" is part of AniWave's client-observable behavior.
- **Workaround:** bypass (AG-01); the app decorator only runs on routes that declare it. [test] e2e exercises public routes with garbage tokens.
- **Recommended fix:** swallow AUTH faults when `require_auth` is False (log at debug); or let per-route enforcement metadata drive the decision.

---

### AG-03 — `TokenBackend` performs a per-request `IdentityStore` lookup; there is no stateless verification mode

- **Severity:** Major
- **Status:** confirmed [source] (`aquilia/auth/backends/token.py` ~lines 40–61: `claims = await token_manager.validate_access_token(token)` then `return await self._identity_store.get(identity_id)`)
- **Actual:** every authenticated request resolves `sub` through an `IdentityStore`. With the auto-provisioned `MemoryIdentityStore` that is a dict lookup returning nothing app-meaningful; with a real (app-built, per AG-06) DB-backed store it is **a database query per request** and changes revocation semantics (revoke identity ⇒ immediate 401, vs AniWave's deliberate "revocation lands within ≤30 min, ordinary requests stay stateless" contract).
- **Expected:** a stateless bearer mode (verify signature/claims only) — the dominant `jsonwebtoken`/Passport-JWT pattern, including AniWave's Node guard.
- **Impact:** TokenBackend unusable for the contract.
- **Workaround:** `app/auth.py:verify_access_token()` wraps `TokenManager.validate_access_token` directly (stateless — the in-memory token store never revokes anything).
- **Recommended fix:** a `stateless=True` token backend (or IdentityStore-optional mode) that trusts verified claims.

---

### AG-04 — The `Guard` protocol is synchronous; token verification is async — guards cannot verify anything

- **Severity:** Major
- **Status:** confirmed [source] (`aquilia/auth/guards.py`: `def check(self, ctx) -> None` protocol)
- **Actual:** guards may only *assert on pre-resolved identity* (`ctx.identity`, set by middleware). Any async work — JWT verification via the async `TokenManager`, a cache/DB check — cannot live in a guard. Verification therefore must happen in middleware, which is exactly the path AG-01/AG-02 forced off.
- **Expected:** async-capable guards. NestJS `CanActivate` returns `Promise<boolean> | boolean` — AniWave's own Node guard was `async canActivate(context)` [source: `jwt-auth.guard.ts`], doing exactly the async verification Aquilia's guard layer cannot express. **This also constrains authorization**: any authz decision requiring async I/O (permission table lookup, policy service) cannot be a guard either (see AG-11).
- **Workaround:** `app/auth.py:require_auth` — an async decorator that verifies, attaches `ctx.identity` + the app principal in `ctx.state`.
- **Recommended fix:** allow `async def check(...)` in the Guard protocol.

---

### AG-05 — No refresh-token rotation or reuse-detection primitive; `AuthManager`'s refresh model is opaque-token-in-store

- **Severity:** Major (for AniWave's class of app)
- **Status:** confirmed [source] (`aquilia/auth/manager.py`: `issue_refresh_token` → `rt_<random>` in `TokenStore` with TTL; `refresh_access_token`/`revoke_token` operate on that store)
- **Actual:** the framework's refresh credential is an opaque token tracked in a token store. There is no concept of: atomic credential rotation on a session row, remembering the *previous* hash to detect replay of a rotated-away token, revoking a session family on reuse, per-session device metadata, or hard calendar-month expiry. None of `user_sessions` (refresh/previous hash, rotated_at, revoked_at + reason, device fields) has a framework analogue.
- **Expected (honestly scoped):** NestJS does **not** provide this either — AniWave's Node `AuthService` implemented all of it by hand on Drizzle. Not a gap *relative to NestJS*; recorded because the migration demonstrates the absence relative to "batteries-included auth" expectations.
- **Impact:** the entire session lifecycle (≈300 lines: CAS rotation, replay classification, revocation reasons, logout/logout-all, password-change revocation of other devices, guest accounts, opportunistic cleanup) is app code in both stacks. [test] e2e: rotation, 3-way concurrent refresh with exactly one winner, replay→revocation, logout-all counts.
- **Recommended fix (if Aquilia wants an opinionated session story):** a rotating-refresh-credential primitive with reuse detection is the centerpiece.

---

### AG-06 — No durable `IdentityStore` / `CredentialStore` ships (memory-only); only `TokenStore` has a Redis implementation

- **Severity:** Minor–Major (deployment-dependent)
- **Status:** confirmed [source] (`aquilia/auth/stores.py` class inventory)
- **Actual:** an app wanting the framework's HTTP path with real users must implement `IdentityStore`/`CredentialStore` against its own DB; nothing is provided. Running the defaults means **every restart loses all identities and credentials** in the enforced path.
- **Expected:** at least one durable reference implementation (ORM or Redis), as exists for tokens.
- **Workaround:** bypassed; app users live in the ORM, verified via `PasswordHasher`.
- **Recommended fix:** ship an ORM-backed identity/credential store pair.

---

### AG-07 — `TokenManager` payload schema is fixed; custom claims are limited to the predefined set

- **Severity:** Minor
- **Status:** confirmed [source] (`issue_access_token(identity_id, scopes, roles, session_id, tenant_id, ttl)` — payload keys `iss/sub/aud/exp/iat/nbf/jti/scopes[/roles/sid/tenant_id]`)
- **Actual:** no API to add arbitrary claims. AniWave's `{sub, sid}` maps onto `sub` + `session_id` — workable — but the token also carries `nbf`, `jti`, `scopes: []` whether wanted or not, and `scopes` is a **required** argument.
- **Workaround:** none needed; documented deviation (client treats tokens as opaque).
- **Recommended fix:** an `extra_claims: dict` parameter.

---

### AG-08 — Distinct auth faults (`AUTH_TOKEN_INVALID` / `AUTH_TOKEN_EXPIRED` / `AUTH_TOKEN_REVOKED` / `AUTH_002`) leak the failure reason; no generic-failure mode

- **Severity:** Minor (security posture)
- **Status:** confirmed [source] (`aquilia/auth/tokens.py` — three distinct raise sites) + [runtime] (the `AUTH_002` response in AG-01)
- **Actual:** the framework tells the caller *why* a token failed. AniWave deliberately collapses every failure into one generic 401 so an attacker learns nothing about which check fired.
- **Workaround:** `verify_access_token()` catches **all** framework auth faults and re-raises a single `UnauthorizedFault("Invalid or expired access token")`. [test] e2e 401-matrix.
- **Recommended fix:** a "collapse token errors" option; app-level error-body hooks. [xref] The migration separately established that the framework's exception middleware hardcodes its error envelope with no rendering hook, so any custom auth error shape requires replacing the middleware outright.

---

### AG-09 — "Protect-by-default" exists but is unusable for app token schemes (coupled to the middleware path)

- **Severity:** Minor
- **Status:** confirmed [source] (`AquilaConfig.Auth.require_auth_by_default`) + [runtime] (the coupling)
- **Actual/Expected:** the NestJS global-guard + `@Public()` pattern has a config analogue, but enabling the section re-triggers AG-01/AG-02. The pattern must be rebuilt by hand: every protected handler carries `@require_auth`. **Inverted-defaults safety is lost** — Node *could not* forget protection (global guard); the Aquilia backend *can* (a missed decorator silently opens a route).
- **Workaround:** per-handler decorators; e2e asserts 401 on every protected family.
- **Recommended fix:** fix AG-01/02/04; then this flag becomes the real protect-by-default story.

---

### AG-10 — The principal type is framework-owned; app principals need side-channel state

- **Severity:** Minor
- **Status:** confirmed [runtime] + one source-verified partial mitigation
- **Actual:** the framework principal is the frozen `Identity` dataclass. AniWave's principal is `{id, sessionId}` with exact accessor semantics — carried in `ctx.state["aniwave_user"]` via the custom decorator, with a framework `Identity` (sid in `attributes`) attached best-effort.
- **Partial mitigation [source, not exercised]:** the middleware registers the resolved `Identity` into the request DI container (`container.register_instance(Identity, identity, scope="request")`) — so handler parameters typed `Identity` can be injected: a `@CurrentUser()`-adjacent mechanism **exists**, but only for the framework principal type and only on the middleware path. A custom principal type cannot ride it.
- **Recommended fix:** allow the auth pipeline to yield an app-defined principal type for request-scoped injection.

---

### AG-11 — Authorization primitives: read but never exercised (structural note only)

- **Status:** not exercised — no defects claimed. One structural note [source]: `RoleGuard`/`ScopeGuard`/`PolicyGuard` and Clearance all assert on pre-resolved `ctx.identity`, so they inherit AG-04's sync/async split — an authorization decision requiring async I/O (permission table, policy service) cannot be a guard either.

### AG-12 — No rate limiter matching a custom fixed-window contract (auth endpoints)

- **Status:** confirmed [xref]. The framework's `Throttle`/`RateLimitIntegration` produce a different error body and semantics (`{"error": "Too many requests", "retry_after": N}` + `Retry-After` header) than AniWave's contract (fixed-window `rl:{scope}:{ip}`, 429 envelope with `details.retryAfterSeconds`, no headers, fail-open) — so the limiter was hand-rolled on Redis. Same amount of work NestJS's `ThrottlerModule` would have needed to match the exact Node contract: equivalent effort, no Aquilia advantage.

---

### AG-13 — **The signing-secret resolution order is broken by the config loader's own defaults: a well-known key silently wins over the operator's secret** *(new — proven for this document)*

- **Severity:** **Critical** (framework security defect)
- **Status:** confirmed [proof] + [source]
- **Component:** `aquilia/config/_loader.py:get_auth_config()` defaults vs `aquilia/server.py:_bootstrap_signing()` (~lines 2355–2400)
- **The mechanism [source]:** `_bootstrap_signing` documents and implements this order: (1) `Signing.secret` → (2) `Auth.secret_key` (called "legacy path") → (3) env `AQ_SECRET_KEY` → (4) env `SECRET_KEY` → (5) insecure fallback. **Step 2 is** `token_cfg.get("secret_key") or auth_cfg.get("secret_key")` — it checks the `auth.tokens.secret_key` **sub-key first**. But `get_auth_config()`'s defaults unconditionally inject `tokens: {"secret_key": "aquilia_insecure_dev_secret"}` (27 bytes) into every merged auth config. That always-truthy default sub-key outranks both the user's `auth.secret_key` **and both environment variables** — the documented order is dead unless the operator sets `Signing.secret` specifically.
- **Proof transcript [proof]** (verification script against this workspace; note the warning firing *during* the very run that had the proper secret configured):
  ```
  AQ_SECRET_KEY env len: 43
  auth.secret_key (user-set): 'dev-only-aquilia-signing-key-change-me-32ch'
  auth.tokens.secret_key (loader default): 'aquilia_insecure_dev_secret'
  => _bootstrap_signing picks: 'aquilia_insecure_dev_secret' len: 27
  WARNING | aquilia.signing — Aquilia signing: signing secret is only 27 bytes; …
  ```
  This also retroactively explains a boot warning observed throughout the migration and left "cause unverified" at the time — `Aquilia signing: signing secret is only 27 bytes; recommend ≥32 bytes` — despite `AQ_SECRET_KEY` being 43–44 chars: the warning was measuring the loader's default, not the configured key.
- **Actual:** every Aquilia app that follows the scaffold's own template (`AquilaConfig.Auth.secret_key = Secret(env="AQ_SECRET_KEY", …)`) signs with the **same publicly-known key** `"aquilia_insecure_dev_secret"`.
- **Expected:** the operator's secret is used; defaults never outrank explicit configuration.
- **Security impact (scoped honestly):** whatever `aquilia.signing` protects becomes forgeable across **all default-configured Aquilia deployments** (anyone knowing the source knows the key). Which subsystems consume the signing engine was not traced end-to-end in this analysis; the module docstring positions it for session/CSRF-style signed artifacts. AniWave itself is functionally unaffected (its tokens use `JWT_SECRET` via its own `TokenManager`; it consumes no signing-engine artifacts) — but the defect is real and framework-wide.
- **Workaround used (AniWave):** none needed for function; noted here because it was live in our boots.
- **Recommended fix:** in `_bootstrap_signing`, only consult `tokens.secret_key` when the user actually set it (distinguish injected defaults from user values in `get_subsystem_config`), or drop the default from the loader and warn loudly when nothing is configured. Add a test: configured `Auth.secret_key` + env ⇒ signing engine uses it.

---

### AG-14 — The auth `enabled` switch has **opposite defaults** in the two configuration layers

- **Severity:** Major (configuration correctness)
- **Status:** confirmed [proof] + [source]
- **Component:** `aquilia/pyconfig.py` (`AquilaConfig.Auth.enabled` class default) vs `aquilia/config/_loader.py:get_auth_config()` (default `"enabled": False`)
- **Proof transcript [proof]** (same verification run):
  ```
  auth.enabled (merged config, from my section): False
  pyconfig AquilaConfig.Auth.enabled default: True
  ```
- **Actual:** the Python env-class layer defaults auth to **enabled** (this is exactly why AG-01 fired — my section set only `secret_key`/`password_hasher` and the middleware mounted); the config-loader layer defaults the same switch to **disabled**. Which default an app gets depends on *which configuration system it used* — same framework, same switch, opposite meanings.
- **Expected:** one default, or at minimum identical defaults across layers.
- **Impact:** the scaffold's own recommended path (pyconfig env classes) is the one that silently enables enforcement; an app configured through the loader/integration path gets the opposite.
- **Recommended fix:** align to `False` in both layers; document that defining the section does not enable enforcement.

---

### AG-15 — Access-token TTL is configured in **minutes** in one layer and **seconds** in another, with no linkage

- **Severity:** Minor (footgun)
- **Status:** confirmed [source]: `get_auth_config()` defaults `tokens.access_token_ttl_minutes: 60`; `AquilaConfig.Auth.access_token_ttl_minutes: int = 60` (pyconfig ~line 1143); `TokenConfig.access_token_ttl: int = 3600` **seconds** (tokens.py ~line 412).
- **Actual:** two knobs for the same concept, different units, no conversion or precedence documented. An app setting minutes on the config class has no effect on a `TokenManager` constructed with its own `TokenConfig` (AniWave's case — 1800 s set directly, correctly), and an app reading "60" from one layer can easily pass it to the other as seconds/minutes.
- **Recommended fix:** one canonical TTL (seconds) with a single documented location.

---

### AG-16 — Issuer/audience defaults differ between layers

- **Severity:** Minor
- **Status:** confirmed [source]: `get_auth_config()` defaults `issuer: "aquilia"`, `audience: "aquilia-app"`; `TokenConfig` defaults `issuer: "aquilia"`, `audience: ["api"]`.
- **Actual:** tokens issued through the AuthManager path and tokens verified by a directly-constructed `TokenManager` disagree on audience unless explicitly aligned. AniWave set `aniwave_client` on `TokenConfig` only — correct for its single-engine design, but a two-layer app would silently mismatch.
- **Recommended fix:** single source for issuer/audience; loader defaults must match `TokenConfig`.

---

### AG-17 — A bcrypt-era `hash_rounds: 12` knob lives in the auth config defaults alongside the argon2 `HasherConfig`

- **Severity:** Minor (confusing/dead config)
- **Status:** confirmed [source] (`get_auth_config()` → `security: {"hash_rounds": 12, ...}`) and [proof-adjacent]: `PasswordHasher` ctor defaults and `HasherConfig` defaults are consistent (time_cost=2, memory_cost=65536, parallelism=4 — verified equal), but neither reads `hash_rounds`.
- **Actual:** three ways to "configure hashing" (`AquilaConfig.Auth.password_hasher`, `security.hash_rounds`, ctor args); one of them (`hash_rounds`) appears to be consumed by nothing in the verified hashing path. An operator tuning it changes nothing.
- **Recommended fix:** remove or wire `hash_rounds`; document the canonical hasher configuration.

---

### AG-18 — No global (app-wide) guard registration; guards stop at module scope

- **Severity:** Minor–Major (pattern parity)
- **Status:** confirmed [source]: manifests support per-module `guards=[...]` (`aquilia/manifest.py` documents module-level guard declaration); no app-wide guard registration point was found in workspace/manifest. NestJS's `APP_GUARD` registers a guard for **every** route in one line — the mechanism AniWave's "protected by default" depends on.
- **Actual:** to protect an app you must (a) repeat guards per module manifest, or (b) hand-roll per-handler decorators (what AniWave did), or (c) enable the middleware path (AG-01/02).
- **Recommended fix:** a workspace-level guard registration (equivalent of `APP_GUARD`).

---

## 4. Missing features: present in NestJS auth, absent in Aquilia

Everything below was actually looked for during the migration. Verification
status per item.

| # | NestJS capability | Aquilia 1.4 status | Verified |
|---|---|---|---|
| M-1 | **Passport strategy pattern** — named, swappable strategies (`PassportStrategy('jwt')`, `'google'`, 500+ ecosystem packages), uniform `validate()` contract | Fixed set of 4 backends (`token`, `session`, `api_key`, `password`) behind an `AuthBackend` protocol; no named-strategy registry, no ecosystem | [source] backends inventory |
| M-2 | **Global guard registration** (`APP_GUARD`) — one line protects the app | Absent; module-manifest guards only | [source] (AG-18) |
| M-3 | **`@Public()` route opt-out metadata** against a global guard | No equivalent usable with app token schemes (`require_auth_by_default` coupled to the broken middleware path — AG-09) | [runtime] |
| M-4 | **`@CurrentUser()` parameter decorator** for app principal types | Framework-principal-only DI injection on the (disabled) middleware path; app principals need `ctx.state` side-channel (AG-10) | [runtime]+[source] |
| M-5 | **Async guards** (`CanActivate → Promise`) | Sync-only guard protocol (AG-04) | [source] |
| M-6 | **Stateless JWT verification mode** (passport-jwt's default posture) | `TokenBackend` always resolves identity per request (AG-03) | [source] |
| M-7 | **Public-route token tolerance** (guards skip verification where not required) | AUTH faults re-raised before the enforcement check (AG-02) | [source] |
| M-8 | **Exception-filter control of auth error bodies** | Fixed fault codes; the exception middleware's envelope is hardcoded with no hook (AG-08) — the migration had to replace the middleware to render its own error contract | [runtime] |
| M-9 | **Session serialization hooks** (`serializeUser`/`deserializeUser`) | Session engine persists its own structures; no app-object serialization hook found | [source, shallow] — sessions unexercised; flagged low-confidence |
| M-10 | Refresh-token rotation/reuse detection | Absent (AG-05) — **equally absent in NestJS**; listed for completeness since it was looked for | [source] |

Not claimed as missing: RBAC decorators/roles (`RoleGuard`/`ScopeGuard`/
Clearance exist [source], unexercised — AG-11), throttling (exists, wrong
contract for AniWave — AG-12), MFA/OAuth (Aquilia is *ahead* — §5).

## 5. The reverse: present in Aquilia, absent from NestJS (source-verified, unexercised)

Honesty cuts both ways; these exist in `aquilia.auth` with no NestJS core
equivalent (Nest requires third-party packages):

- **In-framework MFA**: `TOTPProvider`, `WebAuthnProvider` (passkeys),
  backup codes, `MFAManager` [source: `aquilia/auth/mfa.py`].
- **In-framework OAuth *server* machinery**: Authorization Code flow with
  PKCE (`PKCEVerifier`, S256), OAuth client store, **device-code flow**
  store [source: `aquilia/auth/oauth.py`, `stores.py`].
- **JWT key rotation API**: `KeyRing`/`KeyDescriptor` with `kid`-based
  promotion for zero-downtime signing-key rotation [source] — passport-jwt
  has no native equivalent.
- **PHC self-describing multi-algorithm `PasswordHasher`** (argon2id default)
  — used and verified by AniWave.

None of these were exercised by AniWave (no MFA/OAuth in scope), so quality
is unverified — presence only.

## 6. Bugs, errors, and broken behavior (auth-specific, consolidated)

1. **[proof] AG-13** — signing engine silently uses the well-known default
   `"aquilia_insecure_dev_secret"` even when `AQ_SECRET_KEY` /
   `Auth.secret_key` are set; the documented resolution order is dead.
   Security-relevant, framework-wide.
2. **[proof] AG-14** — `enabled` defaults to `True` in the pyconfig layer
   and `False` in the loader layer: the same switch flips meaning depending
   on which config system the app used. This is the root of the AG-01
   surprise.
3. **[runtime] AG-01** — valid app JWTs → `403 AUTH_002 "Invalid token"`
   from the auto-mounted middleware (the migration's first auth incident).
4. **[source] AG-02** — invalid tokens on public/non-enforced routes are
   hard-rejected (fault re-raised before the `require_auth` check).
5. **[runtime, migration log] AG-12-adjacent** — enabling the auth section
   also **force-enables the session subsystem**: the server's activation
   code (`use_sessions = True` when a session backend is active,
   server.py ~388–395) — a Bearer-only app that enables auth gets cookie
   machinery mounted whether it wanted it or not. Observed as the
   "ADMIN: Sessions are NOT configured!" banner pressure during boots.
6. **[runtime] AG-17** — `security.hash_rounds: 12` is dead configuration in
   the auth defaults (nothing in the verified hashing path reads it).
7. **[runtime]** — the config-primitive naming split (`Secret.reveal()` vs
   `Env.resolve()` for the same concept) bit the settings code:
   `AttributeError: 'Secret' object has no attribute 'resolve'`.
8. **[source] AG-06** — memory-only identity/credential stores: default
   deployments lose all users/credentials on restart.

## 7. Multiple sources of truth in authentication (the full inventory)

Every item below was verified in source or by proof script. This is the
deepest structural problem found: **authentication configuration is spread
across three config systems (pyconfig env classes, the ConfigLoader
subsystem dicts, and constructor defaults) plus the environment, with
different defaults, different units, and no documented precedence.**

- **MS-1 — The token/signing secret exists in 5 ranked locations with a
  broken order** [proof, AG-13]: `Signing.secret` → `Auth.secret_key` →
  `tokens.secret_key` (loader default, secretly wins) → env `AQ_SECRET_KEY`
  → env `SECRET_KEY` → hardcoded fallback. Two of these are *defaults*, not
  user input — and one default outranks user configuration.
- **MS-2 — The `enabled` switch defaults differently per layer** [proof,
  AG-14]: pyconfig `True` vs loader `False`.
- **MS-3 — Access-token TTL: minutes here, seconds there, no link**
  [source, AG-15]: `access_token_ttl_minutes` (pyconfig + loader defaults)
  vs `TokenConfig.access_token_ttl` seconds.
- **MS-4 — Issuer/audience defaults disagree between layers** [source,
  AG-16]: audience `"aquilia-app"` vs `["api"]`.
- **MS-5 — Backends list declared in 3 places** [source]: the
  `AquilAuthMiddleware` constructor default, `get_auth_config()`
  `security.backends`, and `AquilaConfig.Auth.backends` (the scaffold
  workspace template sets the third). All currently agree only by
  coincidence of copy-paste.
- **MS-6 — Hashing configured 3 ways** [source/proof, AG-17]:
  `AquilaConfig.Auth.password_hasher` (HasherConfig), `security.hash_rounds`
  (dead), and `PasswordHasher` ctor args (what AniWave uses).
- **MS-7 — Two session middlewares coexist** [source]:
  `aquilia/middleware/builtin/session.py:SessionMiddleware` (the middleware
  chain's AUTH-priority slot) *and* the session-engine integration inside
  `AquilAuthMiddleware` (resolve/commit + `SessionAuthBridge`). Their
  division of labor is not documented; both were disabled in AniWave, so
  interaction is unverified — the coexistence itself is the finding.
- **MS-8 — Identity is mirrored into 5+ locations per request** [source]:
  `request.state["identity"]`, `request.state["authenticated"]`,
  `ctx.identity`, the request-scoped DI registration, and
  `runtime_context.identity` (via `set_auth_runtime_context`), plus the
  session bridge. All kept in sync by hand inside the middleware — any
  consumer reading a different mirror can see different truths during
  partial failures.
- **MS-9 — "Authenticated?" has multiple answers** [source]: `identity is
  not None` (middleware) vs `session.is_authenticated` (session engine) vs
  `request.state["authenticated"]` — three booleans for one question,
  reconciled only implicitly.
- **MS-10 — App-level keys are a second universe by design-pressure**
  [runtime]: AniWave needs `JWT_SECRET` (app tokens) *and* `AQ_SECRET_KEY`
  (framework signing) — the collision (AG-01) pushes every app with its own
  token scheme into exactly this two-secret split, and nothing documents
  which framework features consume which secret.

**Consequence:** the only safe posture the migration found was to disable
the framework auth subsystem entirely and re-derive everything (secret,
TTL, issuer/audience, principal, verification) from one app-owned source of
truth (`app/settings.py` + `app/auth.py`) — which forfeits every framework
auth feature, exercised or not.

## 8. NestJS vs Aquilia — authentication mechanism, as actually encountered

| Area | NestJS (as AniWave used it) | Aquilia 1.4 (as AniWave used it) | Verdict |
|---|---|---|---|
| Token issuance/verification | `jsonwebtoken` lib called from the app service | `TokenManager` + `KeyRing` primitives called from the app service | **Equivalent** — Aquilia's primitives are richer (kid rotation, OWASP checks, revocation hook) |
| Password hashing | bcrypt-12 via `bcryptjs` | `PasswordHasher` argon2id, PHC auto-detect | **Aquilia better** |
| Guard/plumbing model | async `CanActivate`, `APP_GUARD` global registration, Reflector `@Public()`, `@CurrentUser()` — the whole pattern was ~30 lines | Sync-only guards; auto-mounting middleware keyed to its own secret; no global guard; hand-written decorators (~120 lines) | **NestJS clearly better** |
| Stateless bearer auth | Trivial (verify in guard) | Not expressible in the backend path (AG-03) | **NestJS better** |
| Public-route token tolerance | `@Public()` skips verification | AUTH faults re-raised pre-check (AG-02) | **NestJS better** |
| Error-contract control | Exception filter maps any shape | Fixed codes; no hook (AG-08) | **NestJS better** |
| Configuration coherence | One module (`ConfigModule` + env) | Three config systems, conflicting defaults/units, broken secret precedence (§7) | **NestJS clearly better** |
| Refresh/session intelligence | None — custom on Drizzle | None — opaque tokens in store; custom on the Aquilia ORM | **Equivalent: both app-authored** |
| Durable auth stores | App owns DB | Memory-only identity/credential stores; Redis only for tokens | **Own-DB (Nest-style) better** than Aquilia defaults |
| MFA | Third-party packages | In-framework (TOTP/WebAuthn/backup codes) [source, unexercised] | **Aquilia ahead on paper** |
| OAuth server | Third-party packages | In-framework (PKCE, device-code) [source, unexercised] | **Aquilia ahead on paper** |
| Strategy ecosystem | Passport, 500+ strategies | 4 fixed backends + protocol | **NestJS better** |
| Cookie sessions | (unused) | Full policy subsystem (unused; MS-07 coexistence) | Not comparable |

**The honest framing:** AniWave's Node auth was *also* mostly hand-rolled —
NestJS contributed the plumbing, not the session intelligence. Aquilia
contributed good cryptographic primitives and then **got in the way** at
exactly the plumbing layer where NestJS helps — and, per §7, at the
configuration layer where NestJS is boring in the good sense.

## 9. What Aquilia did well (verified in use)

- **`PasswordHasher`** — argon2id default, PHC self-describing hashes,
  automatic algorithm detection on verify, multi-backend fallbacks. Used
  directly for register/login/password-change and the timing equalizer.
- **`TokenManager`/`KeyRing`** — stdlib HS256, `sid` claim support,
  `kid`-based rotation API, OWASP-oriented validation, revocation hook that
  degrades gracefully to stateless with the in-memory store. Adopted
  wholesale as AniWave's token engine.
- **Request-scoped `Identity` DI registration** [source] — the right
  instinct for principal injection; needs to escape the middleware coupling
  (AG-10).
- **In-framework MFA and OAuth-server machinery** [source] — ahead of
  NestJS core; quality unverified (unexercised).
- **Auth fault taxonomy maps cleanly through the fault system** — where an
  app's error contract matches the framework's, no custom mapping is needed.

## 10. Verdict

For **Bearer-token applications that own their token scheme** — the most
common SPA/mobile API shape, and exactly AniWave's shape — Aquilia 1.4's
authentication layer is a **trap-laden partial**: strong cryptographic
primitives bolted to an HTTP pipeline that (a) activates itself, (b) keys to
its own secret, (c) hard-fails tokens on public routes, (d) requires a
per-request identity lookup, and (e) cannot express verification in its
guard layer — sitting on top of a **configuration layer with three systems,
conflicting defaults, mismatched units, and a proven security-relevant
precedence bug** (AG-13). The only safe posture found was total bypass and
a parallel app-owned auth stack, which is precisely the work NestJS's
plumbing saves you from. The authorization (RBAC/scope) side looks
reasonable on paper but was not exercised; MFA/OAuth-server look like
genuine advantages, also unexercised.

**Recommended Aquilia fixes, in priority order:**

1. **[Security] Fix the signing-secret precedence** — injected loader
   defaults must never outrank explicit operator configuration (AG-13).
2. **Unify auth configuration into one source of truth** — one secret, one
   TTL (seconds), one issuer/audience, one `enabled` default (§7/MS-1…6).
3. `enabled=False` default + decouple key configuration from enforcement
   (AG-01/AG-14).
4. Swallow AUTH faults on non-enforced routes (AG-02).
5. Async guard protocol (AG-04) — unlocks authz use cases too.
6. Stateless token backend (AG-03).
7. Global guard registration, `@Public()` equivalent (AG-18/AG-09).
8. Generic-failure mode + a configurable error-body hook (AG-08).
9. Durable identity/credential stores (AG-06); extra-claims issuance
   (AG-07); app-principal request injection (AG-10).
10. Remove or wire dead config (`hash_rounds`, AG-17); document or merge
    the two session middlewares (MS-7); document the identity mirrors
    (MS-8/9).

With 1–7 in place, an app like AniWave could use the framework path instead
of routing around it.

---

# 11. Fix Report (2026-09-15, auth architecture rebuild)

Every finding in §3/§4/§7 was re-verified against master, redesigned, and
implemented; a second independent hostile audit then reviewed the result and
its findings were fixed and regression-tested in turn. Full architecture
reference: `docs/AUTH_ARCHITECTURE.md`.

## Findings resolved

| Finding | Resolution |
|---|---|
| AG-01 (auto-activation) | Stays fixed (v1.4.1) **plus** the residual: a raw `auth:` section without `enabled` no longer enables either (the generic `get_subsystem_config` default-on no longer applies), and sessions are force-enabled only when the `session` strategy is explicitly configured. |
| AG-02 (faults re-raised pre-check) | **Fixed.** Resolution never raises; faults are recorded on `AuthState.error`; enforcement (global flag honoring `@Public()`, or guards) re-raises them for protected routes. Public routes degrade to anonymous — verified e2e with garbage and forged tokens. |
| AG-03 (mandatory identity lookup) | **Fixed.** `jwt-stateless` strategy (`StatelessTokenBackend`): verified claims → principal, zero store lookups. `stateless: true` swaps it in automatically. |
| AG-04 / AG-11 (sync guards) | **Fixed.** `async def can_activate(ctx) -> bool` (NestJS `CanActivate`); `GuardContext` with `await resolve_identity()`; all built-in guards have async forms; legacy `check()` still works. |
| AG-05 / M-10 (rotation) | **Fixed.** `RotatingTokenStore` protocol: hash-keyed session *families* with current+previous credentials; replay of a rotated-away token **revokes the family**; atomic CAS per store (lock / Lua / SQL `UPDATE…WHERE`); concurrent refresh races produce exactly one winner (stress-tested 8-way, repeated). `device_metadata` rides the family; `AuthManager.refresh_access_token` forwards it. |
| AG-06 (memory-only stores) | **Fixed.** `DatabaseIdentityStore` / `DatabaseCredentialStore` / `DatabaseTokenStore` on any Aquilia-supported DB (shares the app database by default); Redis token store wired via `token_store={"type": "redis"}`; ready-made store objects accepted. |
| AG-07 (fixed claim set) | **Fixed.** `extra_claims={...}` on issuance (reserved claims protected at issue time); `scopes` optional; `TokenClaims.extra` carries arbitrary claims through `verify_token`. |
| AG-08 (distinct faults, no hook) | **Fixed.** `collapse_token_errors` (one generic 401 for every token failure; missing header stays AUTH_010); auth denials flow through the F-20 `error_renderer`. |
| AG-09 / AG-18 / M-2 / M-3 (protect-by-default, APP_GUARD, @Public) | **Fixed.** Guard pipeline in the controller engine: `Auth.global_guards` (APP_GUARD equivalent) → manifest `guards` (now actually consumed for HTTP routes) → `@UseGuards`; `@Public()` exempts routes (auth guards skipped, authz guards kept); implicit `AuthGuard` enforces `require_auth_by_default` even without the auth middleware. |
| AG-10 / M-4 (principal) | **Fixed.** `principal_factory` config; app principals on `AuthState.principal` + request DI; `Annotated[AppUser, CurrentUser]` injection (type-aware, `optional=True` for anonymous-allowed). |
| AG-13 / MS-1 (secret precedence — Critical) | **Fixed.** Loader injects no values; `resolve_signing_secret` implements the documented order, never injects; retired insecure secrets are treated as unset. The scaffold's prod template no longer crashes; the documented `Auth.secret_key` path now actually keys both the token engine and signing. |
| AG-14 / MS-2 (enabled defaults) | Stays fixed; both layers plus the raw-dict path now agree on False. |
| AG-15 / MS-3 (TTL units) | **Fixed.** Seconds canonical; aliases converted; typed layers no longer emit masking defaults (the second audit caught that `refresh_token_ttl_days = 7` was silently becoming 30 days — fixed and regression-tested). |
| AG-16 / MS-4 (issuer/audience) | **Fixed.** Audience always `list[str]`, default `["api"]` in every layer (breaking: see migration note 3). |
| AG-17 (hash_rounds) | **Fixed.** Removed from defaults (was consumed by nothing); hasher now actually wired from config (dict / `HasherConfig` / instance / legacy builder). |
| MS-5 (backends in 3 places) | **Fixed.** Defaults live only on `AuthSettings`; the middleware's constructor fallback is documented as a manual-use default the server never relies on. |
| MS-6 (hashing 3 ways) | **Fixed** (see AG-17). |
| MS-7 (session middleware dupes) | **Fixed.** One canonical session middleware; the auth-integration duplicate is a deprecated alias; exactly one lifecycle runs per app (verified incl. admin login e2e). |
| MS-8 / MS-9 (identity mirrors) | **Fixed.** `AuthState` canonical; `apply_auth_state_views` is the single write point; `authenticated` has one answer. |
| MS-10 (two-secret universe) | **Documented + unified**: `Auth.secret_key` keys both engines unless `Signing.secret` is set; apps managing their own tokens can now register their verifier as a framework global guard instead of bypassing. |
| M-1 (strategy pattern) | **Fixed.** `AuthStrategyRegistry` + `register_strategy`; names first-class in config. |
| M-5 (async guards) / M-6 (stateless) / M-7 (public tolerance) / M-8 (error contract) | **Fixed** (above). |
| M-9 (serializeUser) | **Consciously substituted** by `principal_factory` + `CurrentUser` + claims binding (see AUTH_ARCHITECTURE §10). |
| N-1 (redis auth store unimplemented) | **Fixed.** `token_store={"type": "redis"}` constructs a real `RedisTokenStore`; `store_type` is memory/database for identity/credential stores. |
| N-2 (AUTH_002→403) | **Fixed.** Full code→status table: authentication → 401, rate-limit-style → 429, password-policy → 400, `AUTHZ_*` → 403. |
| N-3 (flat pyconfig never flowed) | **Fixed.** `normalize_auth_config` lifts flat attributes onto the canonical shape; scaffold path verified end-to-end. |
| N-4 (MemoryTokenStore hardcoded) / N-5 (hasher ignored) | **Fixed.** Store specs + hasher wiring in `_create_auth_manager`. |
| N-6 (sessions redis unimplemented) | **Fixed.** `RedisStore` (JSON sessions, Redis TTLs, principal index); `"redis"` store name now real. |
| N-7 (auth bypassed error_renderer) | **Fixed.** Enforcement raises faults; the exception middleware renders them through the configured `error_renderer`; denial responses carry the session `Set-Cookie` via fault metadata headers. |
| N-11 (auth faults masked in prod) | **Fixed.** All auth faults `public = True`. |
| AG-12 (rate-limiter contract) | **By design** — unchanged posture, documented. |

## Second-audit findings (found *after* the rebuild, all fixed + regression-tested)

`tests/test_auth_second_audit.py` pins each: **F1** (critical — the default
`[token, session]` deployment crashed on valid Bearer requests via dict-claims
`bind_token_claims`; the first e2e suite ran stateless-only and missed it),
**R1** (Set-Cookie lost on 401 denials), **C1** (`auth` vs `integrations.auth`
first-wins shadowing; env var could disable a configured integration),
**C2** (TTL aliases masked by typed-layer defaults), **C3** (fail-open
bootstrap — now fail-closed outside dev/test), **F2–F6** (guard-contract
hardening: falsy/False semantics, `authentication_guard` opt-out, Mock-proof
`route_is_public`, dict route metadata, legacy `@requires` async-guard
dispatch), **H1–H3** (malformed config sections tolerated; tuple guard lists;
bare-name guard refs fail the boot with a clear message), **M1/M2/M3/M4**
(retired-secret ordering, explicit zero values, negative/non-integer TTLs,
string booleans), **M5** (test-config precedence aligned), **M6/M7**
(`store_type="redis"` doc fixed; `workspace.AuthConfig` deprecated with
canonical defaults).

## Verification

* New adversarial suites: `test_auth_config_precedence.py` (36),
  `test_auth_guard_pipeline.py` (17), `test_auth_strategies_stateless.py`
  (33), `test_auth_durable_stores.py` (22), `test_auth_principal_e2e.py`
  (13), `test_auth_redis_integration.py` (8, live Redis incl. the Lua CAS),
  `test_auth_second_audit.py` (22) — **151 tests** covering precedence
  across every config mechanism, forged/algorithm-confusion/malformed/
  expired/boundary JWTs, public-route tolerance, nested/global/per-route
  guard combinations, async authorization, concurrent refresh races,
  reuse→family-revocation, restart persistence, fail-closed boot, and
  AniWave-shaped end-to-end flows (120-request mixed-traffic soak).
* Full pre-existing suite: 9,614+ passed / 0 failed at each checkpoint.
