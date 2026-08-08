# Operations And Security

## Health And Metrics

`ASGIAdapter` serves `GET /_health` and `HEAD /_health` before normal route dispatch. The response includes engine metrics and subsystem health when `HealthRegistry` is available. Non-GET/HEAD methods receive 405.

The health route is intentionally handled before controller routing and middleware dispatch. Use it for process and load-balancer readiness checks, but do not treat it as a substitute for subsystem-specific checks such as database migrations, mail delivery, provider credentials, or registry reachability.

### The health endpoint bypasses the middleware chain entirely

`/_health` and `/health` are answered inside `ASGIAdapter.handle_http()` before a `Request` object is even constructed. **No middleware runs for them** — not CORS, not rate limiting, not auth, not CSP, not the fault middleware. `_serve_health()` compensates with a small hardcoded header set (`cache-control: no-store`, `x-content-type-options: nosniff`, `x-frame-options: DENY`) and by rejecting non-GET/HEAD methods with 405.

There is no configuration flag to put the health endpoint behind authentication. The payload it returns is not secret in the credential sense, but it does describe internal topology: in-flight request counts, mean latency, per-subsystem health, and the aliases of any storage backend that is currently down. Treat that as information you are publishing to anyone who can reach the port.

If your threat model requires the metrics payload to be non-public, restrict it at the layer in front of the app rather than in the app:

- block or allow-list `/_health` and `/health` at the ingress, load balancer, or reverse proxy, and expose them only on an internal listener; or
- serve the app on an internal port and let only the health checker reach it directly.

An authenticated health check is not offered because the endpoint exists to answer liveness probes that run before, and independently of, the auth subsystem being healthy — a probe that fails when the session store is down cannot distinguish "process is dead" from "database is slow", which is the one distinction a liveness probe exists to make.

Cache, storage, and filesystem health are really probed rather than assumed (1.3.4+). The cache performs a write/read/delete round trip against its backend; storage pings every registered backend and publishes one `storage.<alias>` entry per disk plus an aggregate that reports `degraded` — naming the failing aliases — when only some backends are down; the filesystem reports pool state. A probe that raises is reported unhealthy rather than aborting startup, since these subsystems are non-required.

```json
{
  "storage":         { "status": "degraded",  "message": "unhealthy: cdn" },
  "storage.default": { "status": "healthy",   "message": "Backend 'default' healthy" },
  "storage.cdn":     { "status": "unhealthy", "message": "Backend 'cdn' unhealthy" },
  "cache":           { "status": "healthy",   "message": "backend=redis" },
  "filesystem":      { "status": "healthy",   "message": "pool_max_threads=8" }
}
```

A failing **default** storage backend is fatal at boot, because the application cannot serve without it. A failing optional backend is logged, reported unhealthy, and does not prevent startup.

## Secrets

Set `AQ_SECRET_KEY` or `SECRET_KEY`, or configure `AquilaConfig.Signing.secret`. Non-dev auth token secrets must not be insecure defaults.

Relevant source-backed secret surfaces:

| Surface | Source-backed behavior |
| --- | --- |
| Signing | `AquiliaServer._bootstrap_signing()` reads configured signing secret plus `AQ_SECRET_KEY` and `SECRET_KEY` fallbacks. |
| Auth tokens | Auth configuration validates token secrets and rejects insecure non-dev defaults. |
| Provider credentials | Provider commands and credential stores live under `aquilia.providers`; Render credential storage uses the encrypted credential helpers documented in that module. |
| Dotenv | `DotEnvLoader.ensure_loaded()` participates in config loading before `AQ_` overlays and explicit overrides. |

## Path Containment (Filesystem And Storage)

Path containment has exactly one implementation, `aquilia.filesystem.validate_path()`. It resolves symlinks with `os.path.realpath` and compares path *components*, so a sibling directory such as `/var/data-private` cannot satisfy a root of `/var/data` the way a string-prefix check would. `aquilia.storage.backends.local.LocalStorage` delegates to it rather than maintaining a parallel check.

| Surface | Source-backed behavior |
| --- | --- |
| Whole-file operations | Every path-accepting helper in `filesystem/_ops.py` validates before touching the OS. |
| Streaming | `stream_read`, `stream_copy`, `AsyncFileStream`, and `AsyncWriteStream` validate at construction, before any descriptor is opened (1.3.4+; previously the `sandbox` argument was accepted and ignored). |
| Directory operations | `list_dir`, `scan_dir`, `make_dir`, `remove_dir`, `remove_tree`, `copy_tree`, and `walk` validate their arguments (1.3.4+). |
| Local storage | `LocalStorage._full_path()` delegates to `validate_path`, translating traversal into `STORAGE_PERMISSION_DENIED`. |

Symlinks are always resolved before the containment check regardless of `follow_symlinks`, which governs `stat` and directory-scan metadata semantics only.

Set a sandbox root for any application that resolves user-supplied paths, and make the requirement enforceable:

```python
Integration.filesystem(
    enabled=True,
    sandbox_root="/srv/uploads",
    allow_unsandboxed=False,   # an unset sandbox_root becomes a boot-time error
)
```

`allow_unsandboxed` defaults to `True` so tooling and CLI use are unaffected; set it to `False` in production configuration so a missing root fails loudly instead of silently disabling containment.

Storage backend configuration is a trust boundary. `StorageRegistry.create_backend()` imports any dotted `backend` value verbatim, which is effectively an arbitrary-module-load primitive. Storage configuration must be deployment-controlled and must never be derived from request-supplied data.

## HTTP Response Caching

`CacheMiddleware` writes to a **shared** cache, so any response varying per identity must not be stored under an identity-independent key. Two safeguards apply and neither can be disabled implicitly:

1. A request carrying `Cookie` or `Authorization` bypasses the cache unless that header appears in `vary_headers` **and** `cache_authenticated=True` is passed.
2. A response setting `Set-Cookie` is never stored.

Both paths mark the response `X-Cache: PRIVATE`. Before enabling the response cache at `scope="global"`, confirm which routes return per-user content and decide explicitly whether they should be cached at all.

When cached values must carry arbitrary Python objects, the pickle serializer requires an HMAC signing key and refuses to deserialize unsigned or tampered payloads:

```python
Integration.cache(
    backend="redis",
    serializer="pickle",
    serializer_secret_key=env("AQUILIA_CACHE_SIGNING_KEY"),
)
```

Prefer `json` or `msgpack` unless pickle's capabilities are specifically required.

## Admin

Admin requires sessions or auth. `aq admin check` validates prerequisites. Admin route registration is controlled by `Integration.admin(...)` and per-module enable flags.

Operational admin commands are mounted under `aq admin`: `check`, `setup`, `status`, `createsuperuser`, `createstaff`, `listusers`, `changepassword`, and `audit`. See [Admin CLI Reference](modules/admin/cli-reference.md) for arguments, options, and defaults extracted from Click.

## Middleware Priorities

Middleware is sorted by `(scope, priority)` ascending, where scope ranks `global < app < controller < route`. **Ascending priority means outermost — a lower number runs first on the way in and last on the way out.** `AquiliaServer` registers the built-in stack at these priorities:

| Priority | Middleware | Registered when |
| --- | --- | --- |
| 1 | `ExceptionMiddleware` | only when no `middleware_chain` is configured |
| 2 | `FaultMiddleware` | always |
| 3 | `ProxyFixMiddleware` | `security.proxy_fix` |
| 4 | `HTTPSRedirectMiddleware` | `security.https_redirect` |
| 5 | `ServerRequestScopeMiddleware` | always |
| 6 | `StaticMiddleware` | `integrations.static_files.enabled` |
| 7 | `SecurityHeadersMiddleware` | `security.helmet_enabled` |
| 8 | `HSTSMiddleware` | `security.hsts` |
| 9 | `CSPMiddleware` | `security.csp.enabled` |
| 10 | `RequestIdMiddleware` | only when no `middleware_chain` is configured |
| 11 | `EnhancedCORSMiddleware` | `security.cors_enabled` |
| 12 | `RateLimitMiddleware` (IP/anonymous rules) | `security.rate_limiting` |
| 15 | `AquilAuthMiddleware` / `SessionMiddleware` | `auth.enabled` / sessions enabled |
| 16 | `RateLimitMiddleware` (identity rules) | any rule keyed on user identity |
| 20 | `CSRFMiddleware` | `security.csrf_protection` |
| 25 | `TemplateMiddleware` | templates configured |

Several of these orderings are load-bearing rather than cosmetic. Proxy fix precedes everything IP-dependent so CORS and IP rate limiting see the corrected client address. CSRF runs after auth/session because it needs a session to store and validate its token against. Rate-limit rules are split across two priority slots for the same reason: a rule keyed on user identity cannot run before the middleware that establishes identity, or its key extractor returns `None` and the rule is skipped for every request — so identity rules register at 16, while IP rules stay at 12 where they can reject anonymous abuse before paying for auth.

Priority is a flat integer namespace shared by framework internals, security config, the template engine, inspector tooling, and third-party app manifests. Two middlewares registered at the same scope and priority resolve by registration order, which is an implementation detail and not part of the public API. `MiddlewareStack.add()` logs a warning when it detects such a collision; construct the stack with `strict_priorities=True` to turn that warning into a fatal `ConfigInvalidFault` at startup instead.

Check resolved ordering with `aq inspect config` and the runtime startup logs whenever behavior depends on it.

### A custom `middleware_chain` drops `ExceptionMiddleware`

Fault handling is two-tier. `FaultMiddleware` (priority 2, always registered) resolves anything the `FaultEngine` recognizes; whatever it cannot resolve it re-raises, expecting `ExceptionMiddleware` (priority 1) outside it to apply the richer treatment — `HTTPFault`-to-status-code mapping (401, 403, 404, 409, …) and the HTML debug pages in development.

`ExceptionMiddleware` is only registered on the **legacy fallback path**, taken when the workspace defines no `middleware_chain`. If you supply your own `middleware_chain`, you replace that fallback and `ExceptionMiddleware` is never added. Unresolved exceptions then fall through to `ASGIAdapter.handle_http()`'s own catch-all, which returns a correct but generic 500 — you lose fault-to-status translation and the debug pages.

If you configure a custom `middleware_chain`, include `ExceptionMiddleware` in it yourself:

```python
from aquilia import MiddlewareChain

chain = (
    MiddlewareChain.chain()
    .use("aquilia.middleware.ExceptionMiddleware", priority=1, debug=False)
    # ... your own middleware ...
)
```

The `MiddlewareChain.defaults()` and `MiddlewareChain.production()` presets already include it; only hand-rolled chains are exposed to this gap.

`FaultMiddleware` and `ServerRequestScopeMiddleware` are framework plumbing and are always registered regardless of this setting; you never need to list them.

### HTTP middleware does not cover WebSocket

`aquilia.sockets.middleware` is a **separate middleware system**. Nothing you configure through `Workspace.security(...)` reaches it.

Enabling `security.rate_limiting`, `security.cors_enabled`, `security.csrf_protection`, or auth middleware protects your **HTTP surface only**. A WebSocket endpoint is protected only by the socket middleware explicitly registered for it, plus socket guards. A deployment with HTTP rate limiting enabled and no socket rate limiting has an unlimited message-rate surface on every open connection.

Register socket middleware in `workspace.py`, the same way as the HTTP chain:

```python
from aquilia.sockets.middleware import SocketMiddlewareChain

workspace = (
    Workspace("chatapp")
    .middleware(MiddlewareChain.production())              # HTTP
    .socket_middleware(SocketMiddlewareChain.production()) # WebSocket
)
```

`SocketMiddlewareChain.production()` gives you fault handling (2), metrics (6), message validation (10), and rate limiting (12). Auth and permissions are not in the preset because they need application-specific configuration — add them with `.use()`:

```python
_B = "aquilia.sockets.middleware.builtin"

chain = (
    SocketMiddlewareChain.production()
    .use(f"{_B}.SocketAuthMiddleware", priority=15, require_identity=True)
    .use(f"{_B}.SocketPermissionMiddleware", priority=18,
         require_roles={"room.moderate": ["moderator"]})
)
```

`SocketFaultMiddleware` is registered by the server whether or not it is in your chain, mirroring `FaultMiddleware` on the HTTP side — without it a fault raised in an event handler is logged and the client is told nothing.

Middleware can also be scoped to one namespace via the decorator, which is the socket analogue of controller-scoped HTTP middleware:

```python
@Socket("/chat/:room", message_rate_limit=5, middleware=[PresenceMiddleware()])
class ChatSocket(SocketController):
    ...
```

Three invariants worth knowing:

- **Ordering matches HTTP.** Ascending priority is outermost and runs first inbound; scope bands (`global` < `namespace:*` < `event:*`) outrank priority. Same-scope priority collisions are logged at startup, or raise `ConfigInvalidFault` under `strict_priorities`.
- **The enforcement math is shared.** The socket rate limiter uses the same token bucket as HTTP rate limiting (`aquilia._ratelimit`) and the same expiry-aware store, so the two transports cannot drift in algorithm. The plumbing stays separate — WebSocket message semantics genuinely differ from HTTP request/response — the algorithm does not.
- **Only inbound messages are covered.** `conn.send_event`, `publish_room`, and adapter fan-out do not traverse any chain. "Rate limiting a socket" means limiting what the client sends.

`SocketRateLimitMiddleware` defaults to `key_by="client"`: authenticated users are keyed by identity id, anonymous connections by connection id. That default means a logged-in user cannot multiply their message budget by opening more connections. Use `key_by="connection"` when you specifically want a per-connection budget, or `key_by="identity"` to leave anonymous traffic unlimited by this rule.

Per-process caveat: buckets are not shared across workers. A socket connection pins to one worker for its lifetime, so per-connection limits are exact, while a per-identity limit is effectively multiplied by the number of workers that user has connections on.

## Production Entrypoint

Use `aquilia.entrypoint:app` with `AQUILIA_WORKSPACE` and `AQUILIA_ENV=prod`. If the workspace is missing, the entrypoint provides a 503 stub response instead of silently failing.

Production startup paths:

```bash
AQUILIA_WORKSPACE=/srv/app AQUILIA_ENV=prod uvicorn aquilia.entrypoint:app --host 0.0.0.0 --port 8000
```

`aq serve` is the mounted production CLI command. It accepts worker, bind, gunicorn, timeout, and graceful-timeout options; see [CLI Reference](cli-reference.md).

## Deployment Checks

1. Run `aq validate` before packaging or deployment.
2. Run `aq doctor` in the target environment where provider credentials and workspace files are present.
3. Run `aq inspect config` and verify resolved values do not contain development defaults.
4. Run database migration commands for configured model stores before serving traffic.
5. Verify `GET /_health` after startup.

## Error Handling In Production

Structured faults from `aquilia.faults` are converted by fault middleware. Unexpected exceptions are handled by the ASGI/server exception paths and, depending on mode, can render development pages or production-safe responses. Keep `AQUILIA_ENV=prod` for production entrypoints so development behavior is not enabled accidentally.

Fault-to-status-code translation depends on `ExceptionMiddleware` being present, which a custom `middleware_chain` silently removes — see [A custom `middleware_chain` drops `ExceptionMiddleware`](#a-custom-middleware_chain-drops-exceptionmiddleware).
