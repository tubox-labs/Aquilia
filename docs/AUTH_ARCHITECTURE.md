# Aquilia Authentication & Authorization — Architecture

**Status:** v1.5 architecture (2026-09). This document describes the auth
subsystem after the gap-analysis rebuild
(`docs/AQUILIA_AUTH_VS_NESTJS_GAPS.md` → §11 fix report). It is the
authoritative developer-facing reference for the design.

---

## 1. Design principles

1. **One configuration model.** Every supported spelling (pyconfig env
   classes, typed integrations, raw dicts, `AQ_` environment variables,
   minute/day aliases) normalizes onto one canonical shape consumed through
   one frozen type (`AuthSettings`). No layer injects value defaults that
   can outrank operator configuration.
2. **Authenticate, then enforce — as separate phases.** Credential
   resolution never raises; enforcement (global flag, guards) decides what a
   failure means *for that route*. This is what makes `@Public()` tolerance
   and precise 401s coexist.
3. **One canonical request state.** `AuthState` is the single truth; every
   legacy mirror (`ctx.identity`, `request.state["identity"]`, …) is a
   derived view written by one function.
4. **Route-level authorization.** Guards run in the controller engine with
   route metadata (global → module → route), NestJS-`CanActivate`-style,
   async-capable. Enforcement composes at the route, not by blanket
   middleware rejection.
5. **Fail closed in production.** Auth bootstrap errors crash the boot
   outside dev/test; guard references that cannot resolve crash the boot in
   every mode.
6. **Framework primitives over app workarounds.** Stateless verification,
   principal injection, rotation with reuse detection, durable stores, and
   exact error contracts are framework features — apps should never need to
   bypass the pipeline.

---

## 2. Layer map

```
┌──────────────────────────────────────────────────────────────────────────┐
│ CONFIGURATION                                                            │
│  AquilaConfig.Auth (env classes)  ─┐                                     │
│  Integration.auth(...)  ──────────┼─► get_auth_config()                  │
│  raw dicts / AQ_AUTH__* env vars ─┘   (merge + normalize_auth_config)   │
│                                            │                            │
│                            AuthSettings (frozen, typed)                 │
│              one TTL unit (seconds) · one audience (list[str])          │
│              no injected secrets · one `enabled` default (False)        │
└──────────────────────────────────────────┼───────────────────────────────┘
                                           │
┌──────────────────────────────────────────▼───────────────────────────────┐
│ BOOTSTRAP (server.py)                                                    │
│  _create_auth_manager: stores (memory/database/redis/objects) ·          │
│      TokenManager from AuthSettings · PasswordHasher · RateLimiter ·     │
│      principal_factory                                                   │
│  _bootstrap_signing: resolve_signing_secret (Signing.secret →           │
│      Auth.secret_key → AQ_SECRET_KEY → SECRET_KEY — never a default)     │
│  _build_guard_pipeline: global_guards (+ implicit AuthGuard when         │
│      require_auth_by_default without middleware)                         │
│  middleware mount: AquilAuthMiddleware (owns sessions when auth is on)   │
└──────────────────────────────────────────┬───────────────────────────────┘
                                           │
┌──────────────────────────────────────────▼───────────────────────────────┐
│ REQUEST PIPELINE (per request)                                           │
│                                                                          │
│  ASGI adapter (route match → route_metadata on request.state)            │
│    └─ ExceptionMiddleware (outermost — renders faults via error_renderer)│
│        └─ AquilAuthMiddleware                                            │
│            1. resolve session (SessionEngine)                            │
│            2. optional authenticate: strategies → Authentication/Identity│
│               (AUTH faults RECORDED on AuthState.error, never raised)    │
│            3. principal_factory(identity, claims) → app principal        │
│            4. apply_auth_state_views — the single mirror write point     │
│            5. enforce: require_auth honoring @Public; session cookie     │
│               rides the denial fault's metadata headers                  │
│        └─ ControllerEngine                                                │
│            ├─ clearance evaluation                                       │
│            ├─ GUARD PIPELINE: global → module → route (@UseGuards)       │
│            │    async can_activate(ctx) · @Public skips auth guards      │
│            └─ parameter binding: Annotated[T, CurrentUser] → principal   │
│               (type-aware: Identity-annotated params get the Identity)   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Configuration

### 3.1 Canonical shape and precedence

`AuthSettings.from_config(any_spelling)` is the constructor everything uses.
Normalization rules (`aquilia/auth/config.py`):

* Explicit nested values (`tokens.*` / `security.*` — typed integrations,
  `AQ_AUTH__TOKENS__*` env) win over flat pyconfig attributes.
* `*_seconds` TTL spellings win over minute/day aliases; aliases convert.
* Audience always becomes `list[str]` (default `["api"]` everywhere).
* Retired insecure secrets (`aquilia_insecure_dev_secret`, `dev_secret`,
  `change-me-in-prod`, …) are indistinguishable from *unset* — a default can
  never beat an operator's secret.
* `enabled` defaults to **False** in every layer; presence of a section is
  not consent to enforce; an explicit `True` in either merged source wins.
* The `auth` section and `integrations.auth` are **merged** (integration
  keys win on conflict) — an env var creating one source never discards the
  other.

### 3.2 Signing secret resolution

`resolve_signing_secret()` (shared by the signing engine and the token
engine, tested, default-free):

1. `AquilaConfig.Signing.secret`
2. user-set `Auth.secret_key` / `auth.tokens.secret_key`
3. `AQ_SECRET_KEY` environment variable
4. `SECRET_KEY` environment variable
5. *(caller policy)* — the signing engine falls back to an insecure dev key
   with a warning; the token engine generates an ephemeral secret in dev and
   raises `ConfigInvalidFault` in non-dev.

`Signing.fallback_secrets` (key rotation) remain honored for verification.

### 3.3 Failure policy

* Non-dev/test boot: any auth bootstrap error (insecure secret, unknown
  store type, bad `principal_factory`) **crashes the server** — never
  degrades to open.
* Guard references that cannot be resolved crash the boot in every mode
  (`module.Class` / `module:Class` form required for strings).

---

## 4. Strategies (backends)

The Passport-style registry (`aquilia/auth/strategies.py`):

| Name | Behavior |
|---|---|
| `token` / `jwt` | Verify Bearer JWT, resolve identity from the identity store (stateful). |
| `jwt-stateless` / `stateless` | Verify Bearer JWT, build principal **from claims** — no per-request store lookup (passport-jwt default posture). `stateless: true` swaps `token` → `jwt-stateless` automatically. |
| `session` | Restore identity from the framework session cookie. |
| `api_key` | `X-Api-Key` / `ApiKey` header. |
| `password` | Programmatic credential login. |

Custom strategies: `register_strategy("google", factory_or_class_or_instance)`
then reference by name in `backends`. Strategies may return a bare
`Identity` (legacy) or an `Authentication` (identity + claims + principal).

Backends **never raise** out of the resolution loop — faults are recorded on
`AuthState.error`:

* public / optional route → request proceeds anonymously;
* protected route → the recorded fault is re-raised at enforcement
  (precise 401 reason), or the generic `AUTH_REQUIRED` when no credential
  was presented.

## 5. Guards

* **Protocol:** `async def can_activate(ctx: GuardContext) -> bool` —
  `True`/`None` allow, `False` denies with the guard's `denial_fault`,
  raising denies with the specific fault. Legacy sync `check(ctx)` guards
  run through the same pipeline.
* **`GuardContext`** exposes the canonical state (`identity`, `principal`,
  `claims`, `user`) plus `request`/`ctx`/`container`/`route_metadata`, and
  `await resolve_identity()` for proactive Bearer verification.
* **Sources, in order:** `Auth.global_guards` (APP_GUARD equivalent) →
  `AppManifest.guards` (stamped on compiled routes) → `@UseGuards(...)` on
  controller class or method.
* **`@Public()`:** exempts the route from the global authentication
  requirement and skips *authentication* guards (`AuthGuard` and anything
  with `authentication_guard = True`). Authorization guards (roles, scopes,
  policies) still run. `AuthGuard` subclasses can opt back in with
  `authentication_guard = False`.
* **Protect-by-default:** `require_auth_by_default = True` protects every
  route except `@Public()` ones — enforced by the middleware when it is
  mounted, and by an implicit `AuthGuard` in the pipeline when it is not
  (own-token apps register their verifier as a global guard instead).

## 6. Principals

* **Framework principal:** `Identity` (frozen dataclass) — canonical
  internal representation.
* **App principals:** `principal_factory = "app.auth.build_principal"`
  (`(identity, claims) -> Any`); the middleware produces it per request,
  registers it in request DI, and `AuthState.principal` carries it.
* **Injection:** `user: Annotated[AppUser, CurrentUser]` (or the
  `current_user` parameter name). `CurrentUser(optional=True)` injects
  `None` for anonymous. Resolution is type-aware: `Annotated[Identity,
  CurrentUser]` returns the framework identity even when a principal factory
  is configured.

## 7. Tokens

* **Issuance:** `issue_access_token(identity_id, scopes=None, roles=None,
  session_id=None, tenant_id=None, ttl=None, extra_claims=None)` —
  `extra_claims` may not override engine-owned claims (raises at issue
  time).
* **Validation:** OWASP checks; the algorithm comes from the key descriptor
  (never the token header — algorithm-confusion guard); malformed base64/JSON
  is a 401 `AUTH_TOKEN_INVALID`, never a 500.
* **`collapse_errors = True`:** every token failure becomes one generic
  401 (`AUTH_002`, "Invalid or expired access token") — anti-enumeration.
  A *missing* header stays distinct (`AUTH_010`).
* **Refresh rotation with reuse detection** (default when the store supports
  it): credentials are SHA-256-hashed; each session *family* tracks
  current+previous hashes; presenting the rotated-away hash revokes the
  whole family (stolen-token tripwire). Rotation is atomic per store —
  lock (memory), Lua CAS (Redis), `UPDATE … WHERE current_hash = ?` (SQL) —
  so concurrent refreshes produce exactly one winner.
* **Status codes:** authentication faults map to 401 (not the 403 the
  SECURITY domain would produce); rate-limit-style auth faults → 429;
  password-policy faults → 400; `AUTHZ_*` stays 403. Auth faults are
  `public = True`, so production renders their real message.
* **Error rendering:** auth denials flow through the exception middleware —
  the F-20 `error_renderer` hook shapes auth 401/403 bodies exactly like
  every other fault. Denial responses carry the session's `Set-Cookie` via
  fault metadata headers.

## 8. Stores

| Store | Identity | Credentials | Tokens | Durable |
|---|---|---|---|---|
| `MemoryIdentityStore` / `MemoryCredentialStore` / `MemoryTokenStore` | ✓ | ✓ | ✓ (rotation) | ✗ (dev/test) |
| `DatabaseIdentityStore` / `DatabaseCredentialStore` / `DatabaseTokenStore` | ✓ | ✓ | ✓ (SQL CAS rotation) | ✓ — any Aquilia DB; shares the app database by default |
| `RedisTokenStore` | — | — | ✓ (Lua CAS rotation) | ✓ |
| `RedisStore` (sessions) | — | — | — | ✓ |

Configuration: `store_type: "memory" | "database"` (identity+credential
shorthand) plus per-store overrides (`identity_store`, `credential_store`,
`token_store` — dict specs or ready-made objects; token store accepts
`redis` with `url`).

## 9. Sessions

Exactly one session lifecycle runs per app: `AquilAuthMiddleware` owns
resolve/commit when auth is mounted (same priority slot), the builtin
`SessionMiddleware` otherwise. The old duplicate in
`aquilia.auth.integration.middleware` is a deprecated alias. Session stores:
`memory`, `file`, `redis`. Privilege changes (login/logout) rotate the
session; rejected (401) requests still receive/rotate their cookie.

## 10. What was deliberately *not* changed

* **MFA / WebAuthn / OAuth-server machinery** — untouched Aquilia
  advantages over NestJS core.
* **RBAC / scopes / policies / Clearance** — kept; `RoleGuard`,
  `ScopeGuard`, `PolicyGuard` gained async `can_activate` without losing
  their sync contract.
* **`AuthManager` semantics** (`sign_in`/`sign_out`/`resume_identity`) —
  preserved; `refresh_access_token` now forwards `device_metadata`.
* **Rate limiting contract (AG-12)** — the framework limiter exists with
  its own contract; exact-contract limiters remain app-level by design.
* **Session serialization hooks (M-9)** — consciously substituted by
  `principal_factory` + `CurrentUser` + claims binding rather than a
  `serializeUser` equivalent.
* **WebSocket handshake auth** — independent one-time-per-connection
  resolution (note: it always does an identity lookup even when
  `stateless=True`; documented residual).

---

## 11. Migration notes (v1.4 → v1.5)

Breaking changes, each with its mitigation:

1. **`AquilaConfig.Auth.enabled`** remains `False`-defaulted (v1.4.1), but a
   raw `auth:` section without `enabled` no longer enables either, and
   `auth` + `integrations.auth` now **merge** (previously first-wins).
   Apps relying on section-presence→enabled must set `enabled = True`.
2. **TTL units:** minute/day aliases still work, but the canonical fields
   are `*_seconds`; typed layers no longer emit masking defaults — an alias
   you set now actually applies. If you set both, seconds wins.
3. **Audience default** unified to `["api"]` (was `"aquilia-app"` in config
   layers). Framework-issued tokens with the old default audience will stop
   validating after upgrade — re-issue tokens or set
   `audience = "aquilia-app"` explicitly for one TTL window.
4. **Auth faults render 401** (were 403) and are public (real message in
   production, was "Internal server error"). Clients keying on 403 must
   accept 401.
5. **`AuthMiddleware`/`AquilAuthMiddleware` `require_auth`** now *raises* a
   fault (rendered by the exception middleware, honoring `error_renderer`)
   instead of returning a hand-built 401 body. Custom middleware stacks must
   include a fault-handling middleware (server stacks always do).
6. **`hash_rounds`** is gone from auth defaults (it was consumed by nothing).
7. **`workspace.AuthConfig`** is deprecated (aligned defaults + warning);
   migrate to `AquilaConfig.Auth` or `Integration.auth(...)`.
8. **Session store `"redis"`** now actually uses Redis (requires
   `pip install redis`); previously it silently fell back to memory.
9. **Auth bootstrap fails closed** outside dev/test — an insecure secret or
   unknown store type now crashes the boot instead of serving without auth.
10. **`TokenBackend.authenticate`** may return an `Authentication` object
    (identity + claims) instead of a bare `Identity`. `isinstance(result,
    Authentication)` before reading `.identity`.
