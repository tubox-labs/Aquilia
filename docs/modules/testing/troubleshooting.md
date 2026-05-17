# Testing Troubleshooting

Test client/server, test cases, fixtures, auth/cache/mail/fault/effect/DI test helpers, config overrides, and request factory utilities.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Module-Relevant Commands

- `aq test`

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
| `aquilia/testing/__init__.py` | 117 | 0 | 0 | Aquilia Testing Framework. |
| `aquilia/testing/assertions.py` | 442 | 1 | 0 | Aquilia Testing - Custom Assertion Helpers. |
| `aquilia/testing/auth.py` | 290 | 3 | 0 | Aquilia Testing - Auth & Identity Helpers. |
| `aquilia/testing/cache.py` | 221 | 2 | 0 | Aquilia Testing - Cache Testing Utilities. |
| `aquilia/testing/cases.py` | 274 | 4 | 0 | Aquilia Testing - Test Case Base Classes. |
| `aquilia/testing/client.py` | 606 | 3 | 0 | Aquilia Testing - HTTP & WebSocket Test Client. |
| `aquilia/testing/config.py` | 299 | 2 | 2 | Aquilia Testing - Config Override Utilities. |
| `aquilia/testing/di.py` | 290 | 1 | 4 | Aquilia Testing - DI Container Testing Utilities. |
| `aquilia/testing/effects.py` | 258 | 4 | 0 | Aquilia Testing - Effect System Testing Utilities. |
| `aquilia/testing/faults.py` | 167 | 2 | 0 | Aquilia Testing - Fault Testing Utilities. |
| `aquilia/testing/fixtures.py` | 212 | 0 | 14 | Aquilia Testing - Pytest Fixtures. |
| `aquilia/testing/mail.py` | 168 | 2 | 3 | Aquilia Testing - Mail Testing Utilities. |
| `aquilia/testing/server.py` | 267 | 1 | 1 | Aquilia Testing - TestServer Factory. |
| `aquilia/testing/utils.py` | 263 | 0 | 6 | Aquilia Testing - Request/Response Utility Factories. |
