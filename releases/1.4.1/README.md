# Aquilia v1.4.1 Release Notes — "Safe Harbor"

Aquilia v1.4.1 is a **hardening and repair release** that follows v1.4.0 "Grand Armada".
It resolves two admin-subsystem defects reported from production use, lands the
framework's response to a full 27-finding migration audit performed while porting a
real NestJS backend (AniWave) to native Aquilia, and **rebuilds the authentication &
authorization architecture** end-to-end following a second, auth-focused gap analysis.

```bash
pip install --upgrade aquilia==1.4.1
```

---

## Headline Fixes

```
┌──────────────────────────────┐  ┌──────────────────────────────────────────┐
│  Admin login redirect loop   │  │  Migration audit response (F-01 … F-27) │
│  sessions mounted only when  │  │  two Critical migration defects, eight   │
│  auth was enabled → no       │  │  Major correctness fixes, verified on    │
│  session cookie → /admin     │  │  live PostgreSQL, live HTTP, and 10–100  │
│  login ⇄ /admin/ forever     │  │  writer concurrency stress               │
└──────────────────────────────┘  └──────────────────────────────────────────┘
```

1. **Authentication & authorization architecture rebuild** — every finding
   of the auth gap analysis is resolved: one unified configuration model
   (`AuthSettings` — the loader no longer injects a secret default that
   outranked operator configuration), an authenticate-then-enforce request
   pipeline with a canonical `AuthState` (invalid tokens on public routes
   degrade to anonymous; protected routes keep precise 401s), a route-level
   **async guard pipeline** with `Auth.global_guards` (the `APP_GUARD`
   equivalent), `@UseGuards`, and `@Public()`, a **Passport-style strategy
   registry** with a **stateless JWT mode**, **`@CurrentUser()` principal
   injection** for application-defined types, **refresh-token rotation with
   reuse detection** (replaying a rotated-away token revokes the whole
   session family; concurrent refreshes yield exactly one winner),
   **durable database stores**, a real **Redis session store**, exact 401
   error contracts rendered through the app's `error_renderer`, and a
   fail-closed auth bootstrap outside dev/test. Full report:
   [`auth_architecture.md`](auth_architecture.md); architecture reference:
   [`docs/AUTH_ARCHITECTURE.md`](../../docs/AUTH_ARCHITECTURE.md).

2. **Admin login redirect loop (silent, credentials valid)** — with sessions
   enabled and framework auth disabled (the standard shape for apps that
   manage their own Bearer tokens), `SessionMiddleware` was never mounted
   and the `SessionEngine` was never registered in DI: both were nested
   inside `if use_auth:`. Login authenticated correctly, issued **no**
   session cookie, and the browser bounced between `/admin/login` and
   `/admin/` forever. Middleware mounting and DI registration are now
   gated on the session engine existing; `AquilAuthMiddleware` still owns
   sessions whenever auth initializes. See [`admin.md`](admin.md).

3. **Admin security DI provider registration (`ValueProvider … missing
   argument: 'token'`)** — the 1.4.0 registration sites passed
   `ValueProvider(value)` without the required `token`, and inverted the
   `(provider, tag)` argument order of `Container.register`. All admin
   security and subsystem providers now register and resolve cleanly.
   See [`admin.md`](admin.md).

4. **Migration-system audit response** — `ArrayField` cannot serialize into
   migrations (F-01, Critical) and generated FK migrations typed UUID-keyed
   columns as `INTEGER`, producing un-appliable DDL (F-02, Critical), are
   fixed along with 25 further findings: composite primary keys wired
   end-to-end, atomic `get_or_create`/`update_or_create`, multi-value
   response headers preserved, response bodies readable after client close,
   route `status_code=` honored, bare `Annotated` facet classes validated,
   a stable `SealFault.errors` surface, CLI workspace-config preservation,
   honest `makemigrations --dry-run`, drift-free `aq db diff`, late task
   registration, TestClient inline query URLs, and more. The complete
   per-finding report — root cause, fix, files, tests, and verification
   commands for all 27 findings plus the user-reported CLI database-URL
   defect — lives in
   [`docs/AQUILIA_MIGRATION_AUDIT.md`](../../docs/AQUILIA_MIGRATION_AUDIT.md) §7.
   Summary: [`migration_audit.md`](migration_audit.md).

---

## Verification

- **Complete test suite: 9646 passed, 0 failed** (238 new tests added by
  this release: 87 audit regressions across 12 files + 151 auth-rebuild
  adversarial tests across 7 files, including live-Redis CAS-rotation
  races and a 120-request mixed-traffic auth soak).
- The migration fixes were verified against **live PostgreSQL 16** (UUID FK
  applies, zero false schema drift, 10/50/100-writer concurrency stress:
  exactly one row, one creator, zero exceptions) and the HTTP-client fixes
  against a **live loopback server** (multi `Set-Cookie` with comma-bearing
  `Expires` dates, read-after-close, connection reuse, concurrent requests).
- The admin session fix is verified end-to-end: superuser login issues the
  `aquilia_session` cookie and the dashboard renders; without the cookie the
  login guard still redirects.

## Upgrading

v1.4.1 is a **drop-in upgrade** for v1.4.0 with two deliberate behavior
changes to review:

1. **HTTP auth enforcement is now opt-in** (`AquilaConfig.Auth.enabled`
   defaults to `False`). Apps that relied on merely *defining* the auth
   config section to mount the framework's auth middleware must set
   `enabled = True` or use `.integrate(Integration.auth(...))` (which still
   enables by default). This only affects apps that never asked for
   framework auth — the previous default silently intercepted
   application-managed Bearer tokens with the framework's own keyring.
2. **Contract validation faults now return HTTP 400** instead of 500 (a
   client payload rejection is a client error). Consumers keying on the
   status code should note the change; the response body shape is unchanged.

3. **Authentication changes to review** (full list in
   [`docs/AUTH_ARCHITECTURE.md`](../../docs/AUTH_ARCHITECTURE.md) §11):
   auth faults now return **401** (was 403) with their real message in
   production; the token **audience default is unified to `["api"]`**
   (framework-issued tokens with the old `"aquilia-app"` default stop
   validating — re-issue them or pin the audience explicitly for one TTL
   window); TTL minute/day aliases you set now actually apply (typed
   layers no longer mask them with defaults); `require_auth` raises a
   fault (rendered through the configured `error_renderer`) instead of
   returning a hand-built 401 body; auth bootstrap fails closed outside
   dev/test; `workspace.AuthConfig` is deprecated.

Everything else — including the multi-header and body-lifecycle changes in
the HTTP client — is backward compatible. The `NativeTransport`
`_read_response_head` extension point now returns raw `(name, value)` lists
(see the audit report, F-07) — custom transports overriding it should
return the list form; the previous dict form is no longer produced.
