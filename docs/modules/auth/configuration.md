# Auth Configuration

Authentication, authorization, identity stores, token management, guards, clearance rules, MFA, OAuth, and session integration.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

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

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `PolicyBuilder` | `aquilia/auth/authz.py` | `owner_only`, `admin_or_owner`, `time_based` | Helper for building common authorization policies. |
| `PolicyArtifact` | `aquilia/auth/surp.py` | `to_dict` | Authorization policy artifact. |
| `HasherConfig` | `aquilia/auth/hashing.py` | `from_dict`, `to_dict` | Algorithm-agnostic configuration for :class:`PasswordHasher`. |
| `PasswordPolicy` | `aquilia/auth/hashing.py` | `from_dict`, `to_dict`, `validate`, `validate_async` | Password policy validator. |
| `PasswordHasherProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for PasswordHasher. |
| `PasswordPolicyProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for PasswordPolicy. |
| `KeyRingProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for KeyRing. |
| `TokenManagerProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for TokenManager. |
| `RateLimiterProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for RateLimiter. |
| `IdentityStoreProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for IdentityStore. |
| `CredentialStoreProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for CredentialStore. |
| `TokenStoreProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for TokenStore. |
| `OAuthClientStoreProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for OAuthClientStore. |
| `AuthorizationCodeStoreProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for AuthorizationCodeStore. |
| `DeviceCodeStoreProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for DeviceCodeStore. |
| `AuthManagerProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for AuthManager. |
| `MFAManagerProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for MFAManager. |
| `OAuth2ManagerProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for OAuth2Manager. |
| `AuthzEngineProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for AuthzEngine. |
| `SessionEngineProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for SessionEngine. |
| `SessionAuthBridgeProvider` | `aquilia/auth/integration/di_providers.py` | `provide` | Provider for SessionAuthBridge. |
| `AuthConfig` | `aquilia/auth/integration/di_providers.py` | `rate_limit`, `sessions`, `tokens`, `mfa`, `oauth`, `build` | Authentication configuration builder. |
| `RequirePolicyGuard` | `aquilia/auth/integration/flow_guards.py` |  | Require custom authorization policy. |
| `AquilAuthMiddleware` | `aquilia/auth/integration/middleware.py` |  | Unified middleware for Auth + Sessions + DI integration. |
| `OptionalAuthMiddleware` | `aquilia/auth/integration/middleware.py` |  | Auth middleware that doesn't require authentication. |
| `SessionMiddleware` | `aquilia/auth/integration/middleware.py` |  | Session-only middleware without authentication. |
| `FaultHandlerMiddleware` | `aquilia/auth/integration/middleware.py` |  | Middleware for handling faults with FaultEngine. |
| `EnhancedRequestScopeMiddleware` | `aquilia/auth/integration/middleware.py` |  | Enhanced request scope middleware with better integration. |
| `AuthSessionMiddleware` | `aquilia/auth/integration/sessions.py` |  | Middleware for session-based authentication. |
| `SignInProvisionPolicy` | `aquilia/auth/manager.py` | `secure_defaults` | Provisioning policy for sign_in bootstrap behavior. |
| `TOTPProvider` | `aquilia/auth/mfa.py` | `generate_secret`, `generate_code`, `verify_code`, `generate_provisioning_uri`, `generate_backup_codes`, `hash_backup_code`, `verify_backup_code` | TOTP (Time-based One-Time Password) provider. |
| `WebAuthnProvider` | `aquilia/auth/mfa.py` | `generate_challenge`, `generate_registration_options`, `generate_authentication_options`, `verify_registration_response`, `verify_authentication_response` | WebAuthn provider for passwordless authentication. |
| `PolicyDecision` | `aquilia/auth/policy/__init__.py` |  | Result of a policy evaluation. |
| `PolicyResult` | `aquilia/auth/policy/__init__.py` |  | Result of evaluating a policy rule. |
| `Policy` | `aquilia/auth/policy/__init__.py` | `evaluate`, `get_rules` | Base class for resource-based authorization policies. |
| `PolicyRegistry` | `aquilia/auth/policy/__init__.py` | `register`, `get`, `evaluate`, `resources` | Registry for authorization policies. |
| `TokenConfig` | `aquilia/auth/tokens.py` |  | Token manager configuration. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.
