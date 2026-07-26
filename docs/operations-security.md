# Operations And Security

## Health And Metrics

`ASGIAdapter` serves `GET /_health` and `HEAD /_health` before normal route dispatch. The response includes engine metrics and subsystem health when `HealthRegistry` is available. Non-GET/HEAD methods receive 405.

The health route is intentionally handled before controller routing and middleware dispatch. Use it for process and load-balancer readiness checks, but do not treat it as a substitute for subsystem-specific checks such as database migrations, mail delivery, provider credentials, or registry reachability.

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

Source comments in `AquiliaServer._setup_security_middleware()` assign security/static middleware priorities: proxy fix 3, HTTPS redirect 4, static files 6, security headers 7, HSTS 8, CSP 9, CORS 11, rate limit 12, CSRF 20. Fault middleware is priority 2 and request-scope middleware priority 5.

Middleware ordering matters because fault handling and request-scope cleanup are framework safety rails. Security-related middleware is added by server setup when configured by `Workspace.security(...)` and integration objects. Manifest and workspace custom middleware should be checked with `aq inspect config` and runtime startup logs when behavior depends on order.

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
