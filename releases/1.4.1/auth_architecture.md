# Aquilia v1.4.1 — Authentication & Authorization Architecture Rebuild

**Date:** 2026-09-15 · **Scope:** every finding of
[`docs/AQUILIA_AUTH_VS_NESTJS_GAPS.md`](../../docs/AQUILIA_AUTH_VS_NESTJS_GAPS.md)
(AG-01…AG-18, M-1…M-10, MS-1…MS-10) plus eleven newly discovered defects
(N-1…N-11), plus the findings of a second independent hostile audit of the
rebuilt code. **Architecture reference:**
[`docs/AUTH_ARCHITECTURE.md`](../../docs/AUTH_ARCHITECTURE.md).

The rebuild's premise: for Bearer-token applications that own their token
scheme — the most common SPA/mobile API shape — Aquilia 1.4.0's
authentication layer was a trap-laden partial whose only safe posture was
total bypass. v1.4.1 makes the framework path the natural one.

---

## 1. What changed, by subsystem

### Configuration — one source of truth

| Before | After |
|---|---|
| Three config systems with different key shapes; flat pyconfig attributes never reached the nested keys the machinery read | `AuthSettings` — every spelling (env classes, `Integration.auth()`, raw dicts, `AQ_AUTH__*` env vars, minute/day aliases) normalizes onto one canonical model |
| The loader injected `tokens.secret_key = "aquilia_insecure_dev_secret"`, which **outranked operator configuration** (AG-13, Critical, still live in 1.4.1's first cut) | The loader injects no values; `resolve_signing_secret` implements the documented order and never injects; retired insecure secrets are treated as unset |
| The scaffold's `Auth.secret_key` path never reached the token engine (and crashed the prod boot with auth enabled) | The documented path keys both the token engine and the signing engine |
| `auth` and `integrations.auth` shadowed each other (first-wins); an env var could silently disable a configured integration | The sections merge (integration keys win; explicit `enabled: true` anywhere wins) |
| TTLs in minutes here, seconds there; typed-layer defaults masked user aliases (`refresh_token_ttl_days = 7` silently became 30 days) | Seconds canonical; aliases convert; `*_seconds` wins; typed layers emit no masking defaults |
| Audience `"aquilia-app"` vs `["api"]`; `hash_rounds` dead; hasher and rate limiter configured but dropped | Audience unified (`["api"]`); dead knob removed; hasher and rate limiter actually wired |

### Request pipeline — authenticate, then enforce

- Credential resolution **never raises**: faults are recorded on the
  canonical `AuthState`; enforcement (global flag honoring `@Public()`, or
  guards) decides what a failure means *for that route*. Invalid tokens on
  public routes degrade to anonymous; protected routes keep precise 401
  reason codes (AG-02, M-7).
- `AuthState` is the single per-request truth; every legacy mirror
  (`ctx.identity`, `request.state[...]`, DI registrations) is a derived view
  written by one function (MS-8/9).
- Auth denials flow through the exception middleware and the pluggable
  `error_renderer`; the session's `Set-Cookie` rides the denial fault so
  rejected requests still establish/rotate their session cookie (AG-08,
  N-7).
- Authentication faults render **401** (were 403 — N-2); rate-limit-style
  auth faults → 429; password-policy → 400; `AUTHZ_*` → 403; auth faults are
  `public = True` so production shows the real message (N-11).
- Exactly one session lifecycle per app; sessions force-enabled only when
  the `session` strategy is explicitly configured (MS-7).

### Guards — route-level, async, composable

- `async def can_activate(ctx: GuardContext) -> bool` — the NestJS
  `CanActivate` contract; guards can finally perform JWT verification,
  permission-table lookups, and policy-service calls (AG-04/AG-11, M-5).
  Legacy sync `check()` guards run unchanged.
- Guard sources compose: `Auth.global_guards` (the `APP_GUARD` equivalent)
  → module manifest `guards` (previously validated but dead for HTTP —
  AG-18) → `@UseGuards(...)` on class or method.
- `@Public()` exempts a route from protect-by-default and skips
  *authentication* guards; authorization guards still run. Protect-by-default
  works with or without the auth middleware (AG-09, M-2/M-3).

### Strategies, principals, tokens

- Passport-style registry: `register_strategy("google", ...)`; built-ins
  `token`, `jwt-stateless`, `session`, `api_key`, `password` (M-1).
- **Stateless mode**: `stateless: true` verifies claims and builds the
  principal with zero per-request identity lookups (AG-03, M-6).
- `Annotated[AppUser, CurrentUser]` injection with the
  `Auth.principal_factory` hook; type-aware; `optional=True` for maybe-user
  routes (AG-10, M-4).
- `extra_claims` with reserved-claim protection; `scopes` optional;
  `TokenClaims.extra` round-trips arbitrary claims (AG-07).
- `collapse_token_errors`: one generic 401 for every token failure, missing
  header stays distinct (AG-08).
- **Rotation with reuse detection** (AG-05, M-10): hash-keyed session
  *families*; presenting a rotated-away token revokes the whole family;
  atomic CAS per store (lock / Redis Lua / SQL `UPDATE…WHERE`); concurrent
  refreshes yield exactly one winner; `device_metadata` per family.
- Malformed base64/JSON tokens are 401s, never uncaught 500s; the
  verification algorithm always comes from the key descriptor (algorithm
  confusion guard), both tested adversarially.

### Stores — durable by configuration

`DatabaseIdentityStore` / `DatabaseCredentialStore` / `DatabaseTokenStore`
on any Aquilia-supported database (sharing the app database by default);
`token_store={"type": "redis"}`; the previously-missing Redis **session**
store; ready-made store objects accepted (AG-06, N-1/N-4/N-6).

### Production posture

Auth bootstrap **fails closed** outside dev/test (an insecure secret or
unknown store type crashes the boot instead of serving unprotected — C3 of
the second audit); unresolvable guard references fail the boot in every
mode with an actionable message.

---

## 2. The second audit

A hostile re-review of the rebuilt code found a **critical** defect the
first test pass had missed: the *default* `[token, session]` deployment
crashed on every valid Bearer request (dict claims reached an
attribute-reading session binder; the first e2e suite had only exercised
stateless mode). It also found config source-shadowing, TTL-alias masking,
fail-open bootstrap, session-cookie loss on 401 denials, and several
guard-contract holes. Every finding is fixed and pinned by
`tests/test_auth_second_audit.py` (22 tests).

## 3. Verification

- **151 new adversarial tests** across 7 files — configuration precedence
  from every supported mechanism (including env-created sections, malformed
  values, retired secrets), forged/algorithm-confusion/malformed/expired/
  boundary JWTs, public-route token tolerance, global/module/per-route
  guard combinations, async authorization, repeated 8-way concurrent
  refresh races (exactly one winner), reuse→family revocation, restart
  persistence, fail-closed boot, collapse-mode 401 matrices, a 120-request
  mixed-traffic soak, and live-Redis verification of the Lua CAS rotation
  and the Redis session store.
- **Full suite: 9,646 passed, 0 failed** (was 9,488 before this release's
  additions); `ruff check aquilia/` clean.

## 4. Upgrading

See `docs/AUTH_ARCHITECTURE.md` §11 for the complete migration list. The
headline items: re-issue framework tokens or pin the audience for one TTL
window (default unified to `["api"]`); clients keying on 403 for auth
failures must accept 401; `require_auth` now raises faults; TTL aliases
you set now actually apply; auth bootstrap fails closed outside dev/test.
