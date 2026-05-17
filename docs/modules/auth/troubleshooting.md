# Auth Troubleshooting

Authentication, authorization, identity stores, token management, guards, clearance rules, MFA, OAuth, and session integration.

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
| `aquilia/auth/__init__.py` | 314 | 0 | 0 | AquilAuth - Authentication & Authorization System |
| `aquilia/auth/audit.py` | 510 | 7 | 0 | AquilAuth - Security Audit Trail |
| `aquilia/auth/authz.py` | 542 | 8 | 0 | AquilAuth - Authorization Engine |
| `aquilia/auth/clearance.py` | 864 | 6 | 12 | Aquilia Clearance System -- Unique declarative access control. |
| `aquilia/auth/core.py` | 652 | 14 | 0 | AquilAuth - Core Types |
| `aquilia/auth/surp.py` | 395 | 7 | 0 | AquilAuth - Surp Artifacts |
| `aquilia/auth/decorators.py` | 864 | 6 | 3 | AquilAuth - Authentication Decorators and Guards. |
| `aquilia/auth/faults.py` | 493 | 37 | 2 | AquilAuth - Authentication/Authorization Faults |
| `aquilia/auth/guards.py` | 522 | 6 | 3 | AquilAuth - Guards and Flow Integration |
| `aquilia/auth/hardening.py` | 348 | 4 | 5 | AquilAuth - Security Hardening Utilities |
| `aquilia/auth/hashing.py` | 621 | 3 | 4 | AquilAuth - Password Hashing |
| `aquilia/auth/integration/__init__.py` | 1 | 0 | 0 | AquilAuth - Integration package. |
| `aquilia/auth/integration/aquila_sessions.py` | 464 | 2 | 11 | AquilAuth - Aquilia Sessions Integration |
| `aquilia/auth/integration/di_providers.py` | 557 | 18 | 2 | AquilAuth - DI Providers |
| `aquilia/auth/integration/flow_guards.py` | 817 | 10 | 11 | AquilAuth - Flow & Controller Guards (Deep Integration) |
| `aquilia/auth/integration/middleware.py` | 622 | 5 | 1 | AquilAuth - Unified Middleware |
| `aquilia/auth/integration/runtime_context.py` | 51 | 1 | 3 | AquilAuth runtime context bridge. |
| `aquilia/auth/integration/sessions.py` | 351 | 4 | 0 | AquilAuth - Session Integration |
| `aquilia/auth/manager.py` | 1239 | 3 | 0 | AquilAuth - Authentication Manager |
| `aquilia/auth/mfa.py` | 461 | 3 | 0 | AquilAuth - MFA Providers |
| `aquilia/auth/oauth.py` | 528 | 2 | 0 | AquilAuth - OAuth2/OIDC Flows |
| `aquilia/auth/policy/__init__.py` | 191 | 4 | 4 | AquilAuth - Policy DSL Module |
| `aquilia/auth/stores.py` | 580 | 7 | 0 | AquilAuth - Credential and Token Stores |
| `aquilia/auth/tokens.py` | 787 | 7 | 0 | AquilAuth - Token Management |
