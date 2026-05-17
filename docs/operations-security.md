# Operations And Security

## Health And Metrics

`ASGIAdapter` serves `GET /_health` and `HEAD /_health` before normal route dispatch. The response includes engine metrics and subsystem health when `HealthRegistry` is available. Non-GET/HEAD methods receive 405.

The health route is intentionally handled before controller routing and middleware dispatch. Use it for process and load-balancer readiness checks, but do not treat it as a substitute for subsystem-specific checks such as database migrations, mail delivery, provider credentials, or registry reachability.

## Secrets

Set `AQ_SECRET_KEY` or `SECRET_KEY`, or configure `AquilaConfig.Signing.secret`. Non-dev auth token secrets must not be insecure defaults.

Relevant source-backed secret surfaces:

| Surface | Source-backed behavior |
| --- | --- |
| Signing | `AquiliaServer._bootstrap_signing()` reads configured signing secret plus `AQ_SECRET_KEY` and `SECRET_KEY` fallbacks. |
| Auth tokens | Auth configuration validates token secrets and rejects insecure non-dev defaults. |
| Provider credentials | Provider commands and credential stores live under `aquilia.providers`; Render credential storage uses the encrypted credential helpers documented in that module. |
| Dotenv | `DotEnvLoader.ensure_loaded()` participates in config loading before `AQ_` overlays and explicit overrides. |

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
