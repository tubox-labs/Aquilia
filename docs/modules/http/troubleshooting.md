# Http Troubleshooting

Native async HTTP client, request/response builders, sessions, retry policies, auth interceptors, cookies, middleware, streaming, and transport.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Symptoms And Actions

| Symptom | Likely Source | Action |
| --- | --- | --- |
| Import error during startup | Bad manifest class path or optional provider dependency | Check `modules/<name>/manifest.py`, install the relevant extra, and rerun `aq validate`. |
| Route not found | Controller omitted from manifest, wrong route prefix, or startup conflict | Run `aq inspect routes`; inspect controller decorators and `Module.route_prefix()`. |
| Dependency not found | Service not registered or constructor annotation cannot be resolved | Check `AppManifest.services`, DI provider registrations, and `aq inspect di`. |
| Config value missing | Dotenv/env overlay not loaded or wrong nested key | Check `ConfigLoader` precedence and `AQ_` double-underscore key names. |
| Production security failure | Insecure secret or required key not configured | Set `AQ_SECRET_KEY`, `SECRET_KEY`, or Python-native secret config. |
| Optional subsystem unavailable | Provider/backend dependency or startup connection failed | Check startup logs; optional subsystems often log non-fatal failures. |

## Source Files To Inspect

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/http/__init__.py` | 380 | 0 | 0 | AquilaHTTP — Async HTTP Client for Aquilia. |
| `aquilia/http/_transport.py` | 805 | 6 | 1 | HTTP Transport Layer |
| `aquilia/http/auth.py` | 533 | 8 | 0 | AquilaHTTP — Authentication Interceptors. |
| `aquilia/http/client.py` | 556 | 1 | 6 | AquilaHTTP — Async HTTP Client. |
| `aquilia/http/config.py` | 434 | 8 | 0 | AquilaHTTP — Configuration. |
| `aquilia/http/cookies.py` | 480 | 3 | 0 | AquilaHTTP — Cookie Jar. |
| `aquilia/http/faults.py` | 769 | 25 | 0 | AquilaHTTP — Fault Classes. |
| `aquilia/http/integration.py` | 340 | 2 | 2 | AquilaHTTP — Framework Integration. |
| `aquilia/http/interceptors.py` | 516 | 11 | 0 | AquilaHTTP — Interceptors. |
| `aquilia/http/middleware.py` | 485 | 11 | 1 | AquilaHTTP — Middleware. |
| `aquilia/http/multipart.py` | 484 | 3 | 0 | AquilaHTTP — Multipart Form Data. |
| `aquilia/http/pool.py` | 445 | 4 | 0 | AquilaHTTP — Connection Pool. |
| `aquilia/http/request.py` | 552 | 3 | 7 | AquilaHTTP — HTTP Client Request. |
| `aquilia/http/response.py` | 502 | 1 | 1 | AquilaHTTP — HTTP Client Response. |
| `aquilia/http/retry.py` | 390 | 8 | 1 | AquilaHTTP — Retry Strategies. |
| `aquilia/http/session.py` | 490 | 1 | 0 | AquilaHTTP — HTTP Session. |
| `aquilia/http/streaming.py` | 388 | 5 | 4 | AquilaHTTP — Streaming Support. |
