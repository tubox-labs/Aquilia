# Admin Subsystem Fixes in v1.4.1

Two defects reported from production use of the admin dashboard, both
reproduced end-to-end before fixing and locked in with regression tests
(`tests/test_admin_session_middleware.py`).

---

## 1. The silent admin login redirect loop

### Symptom

Logging in to `/admin` with valid superuser credentials appears to succeed
and then… shows the login page again. No error, no message. An HTTP trace
shows the loop:

```
POST /admin/login   → 302 Location: /admin/     (no Set-Cookie!)
GET  /admin/        → 302 Location: /admin/login  (no identity)
GET  /admin/login   → 200 (clean form — looks like a refresh)
```

Credentials verified correct: the `AdminUser` record exists, is a
superadmin, is active, and `check_password()` succeeds. Authentication was
never the problem — the session cookie was never issued.

### Root cause

In `AquiliaServer._setup_middleware`, the block that mounts
`SessionMiddleware` and registers the `SessionEngine` into every DI
container was **indented inside `if use_auth:`**. An application with
sessions enabled and framework auth disabled — the standard shape for apps
that verify their own Bearer tokens — therefore:

1. created the session engine correctly (that block is gated on
   `use_sessions`), but then
2. never mounted `SessionMiddleware` (so `ctx.session` is always `None`;
   the login handler's `ctx.session.data["_admin_identity"] = …` writes
   nothing), and
3. never registered the engine in DI.

With no middleware to serialize the session, the login response carried no
`Set-Cookie`; the dashboard's identity guard then redirected back to the
login page — each hop individually legitimate, the combination an infinite
silent loop.

### Fix

Session middleware mounting and the engine's DI registration are now gated
on **the session engine existing**, not on auth being enabled
(`aquilia/server.py`). `AquilAuthMiddleware` continues to own session
handling whenever auth initializes, so the session-only middleware is
skipped in that case (no double-run). A latent `UnboundLocalError` — a
function-local `ValueProvider` import shadowing the module-level one,
which crashed the session-DI block whenever auth was disabled — was
removed at the same time.

### Verification

- Reproduced the exact trace (302 → `/admin/` with no `Set-Cookie`,
  dashboard bouncing to login) before the fix; after the fix the login
  response sets `aquilia_session=…` and `GET /admin/` renders **200**.
- The guard is not weakened: without a session cookie the dashboard still
  redirects to the login page.
- With auth enabled, `AquilAuthMiddleware` mounts and no duplicate session
  middleware runs.
- The `SessionEngine` resolves from every DI container to the live engine
  instance.

---

## 2. Admin security DI provider registration

### Symptom (v1.4.0)

```
LOG WARNING  admin.security  Failed to register admin security DI providers:
ValueProvider.__init__() missing 1 required positional argument: 'token'
```

### Root cause (v1.4.0)

The registration sites in `aquilia/admin/security.py` constructed
`ValueProvider(policy)` — the `token` argument is required — and passed
`container.register(AdminSecurityPolicy, ValueProvider(policy))`, inverting
`Container.register(provider, tag=None)`'s argument order.
`aquilia/admin/di_providers.py` had the same shape and referenced
`Scope.APP`/`Scope.SINGLETON` constants that do not exist on the scopes
module. Because `register_security_providers` catches its own exceptions,
the failure was a single boot-time warning and silently missing providers.

### Fix

All registration sites construct `ValueProvider(value=…, token=…, name=…)`
with the correct `Container.register(provider)` call shape
(`aquilia/admin/security.py`, `aquilia/admin/di_providers.py`). A
repository-wide AST sweep confirms no remaining `ValueProvider` call
without `token` and no `Scope`-enum arguments.

### Verification

All six security providers (`AdminSecurityPolicy`, `AdminCSRFProtection`,
`AdminRateLimiter`, `AdminSecurityHeaders`, `PasswordValidator`,
`SecurityEventTracker`) plus `AdminSite`/`AdminAuditLog` register into a
real container and resolve back to their values — covered by regression
tests in `tests/test_admin_session_middleware.py` and
`tests/test_admin_security.py`.
