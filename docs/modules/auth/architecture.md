# Auth Architecture

Authentication, authorization, identity stores, token management, guards, clearance rules, MFA, OAuth, and session integration.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
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

## Internal Shape

`auth` has 24 Python files, 164 public classes, 61 public module-level functions, and 19 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.faults` | 7 |
| `aquilia.faults.domains` | 6 |
| `.core` | 5 |
| `aquilia.sessions` | 5 |
| `.tokens` | 4 |
| `..core` | 3 |
| `..manager` | 3 |
| `.aquila_sessions` | 3 |
| `.stores` | 3 |
| `aquilia.faults` | 3 |
| `..authz` | 2 |
| `..faults` | 2 |
| `.authz` | 2 |
| `.hashing` | 2 |
| `.manager` | 2 |
| `aquilia.di` | 2 |
| `aquilia.request` | 2 |
| `...faults.domains` | 1 |
| `..faults.domains` | 1 |
| `..hashing` | 1 |
| `..mfa` | 1 |
| `..oauth` | 1 |
| `..stores` | 1 |
| `..tokens` | 1 |
| `.audit` | 1 |
| `.clearance` | 1 |
| `.decorators` | 1 |
| `.hardening` | 1 |
| `.mfa` | 1 |
| `.oauth` | 1 |
| `.policy` | 1 |
| `.runtime_context` | 1 |
| `aquilia._version` | 1 |
| `aquilia.di.decorators` | 1 |
| `aquilia.flow` | 1 |
| `aquilia.middleware` | 1 |
| `aquilia.response` | 1 |
| `aquilia.typing` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `typing` | 21 |
| `__future__` | 20 |
| `dataclasses` | 11 |
| `datetime` | 9 |
| `collections` | 8 |
| `secrets` | 8 |
| `hashlib` | 7 |
| `enum` | 6 |
| `logging` | 5 |
| `time` | 5 |
| `base64` | 4 |
| `hmac` | 4 |
| `json` | 4 |
| `functools` | 2 |
| `inspect` | 2 |
| `os` | 2 |
| `asyncio` | 1 |
| `contextlib` | 1 |
| `contextvars` | 1 |
| `pathlib` | 1 |
| `struct` | 1 |
| `unittest` | 1 |
| `urllib` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `AuditStore` | `aquilia/auth/audit.py` | Base class for audit event storage. |
| `MemoryAuditStore` | `aquilia/auth/audit.py` | In-memory audit store for development/testing. |
| `LoggingAuditStore` | `aquilia/auth/audit.py` | Audit store that logs to Python logging framework. |
| `RBACEngine` | `aquilia/auth/authz.py` | Role-Based Access Control engine. |
| `ABACEngine` | `aquilia/auth/authz.py` | Attribute-Based Access Control engine. |
| `AuthzEngine` | `aquilia/auth/authz.py` | Unified authorization engine. |
| `PolicyBuilder` | `aquilia/auth/authz.py` | Helper for building common authorization policies. |
| `ClearanceEngine` | `aquilia/auth/clearance.py` | Evaluates clearance requirements against request context. |
| `ClearanceGuard` | `aquilia/auth/clearance.py` | Pipeline guard that enforces Clearance requirements. |
| `IdentityStore` | `aquilia/auth/core.py` | Protocol for identity storage. |
| `CredentialStore` | `aquilia/auth/core.py` | Protocol for credential storage. |
| `OAuthClientStore` | `aquilia/auth/core.py` | Protocol for OAuth client storage. |
| `PolicyArtifact` | `aquilia/auth/surp.py` | Authorization policy artifact. |
| `MemoryArtifactStore` | `aquilia/auth/surp.py` | In-memory artifact store for development/testing. |
| `AuthGuard` | `aquilia/auth/decorators.py` | Base class for authentication/authorization guards. |
| `AdminGuard` | `aquilia/auth/decorators.py` | Guard that requires admin role. |
| `VerifiedEmailGuard` | `aquilia/auth/decorators.py` | Guard that requires verified email. |
| `RoleGuard` | `aquilia/auth/decorators.py` | Guard that requires specific role(s). |
| `ScopeGuard` | `aquilia/auth/decorators.py` | Guard that requires specific scope(s). |
| `Guard` | `aquilia/auth/guards.py` | Base guard for authentication/authorization. |
| `AuthGuard` | `aquilia/auth/guards.py` | Authentication guard - requires valid authentication. |
| `ApiKeyGuard` | `aquilia/auth/guards.py` | API key authentication guard. |
| `AuthzGuard` | `aquilia/auth/guards.py` | Authorization guard - enforces access control. |
| `ScopeGuard` | `aquilia/auth/guards.py` | Scope-only guard - quick scope check. |
| `RoleGuard` | `aquilia/auth/guards.py` | Role-only guard - quick role check. |
| `HasherConfig` | `aquilia/auth/hashing.py` | Algorithm-agnostic configuration for :class:`PasswordHasher`. |
| `PasswordPolicy` | `aquilia/auth/hashing.py` | Password policy validator. |
| `PasswordHasherProvider` | `aquilia/auth/integration/di_providers.py` | Provider for PasswordHasher. |
| `PasswordPolicyProvider` | `aquilia/auth/integration/di_providers.py` | Provider for PasswordPolicy. |
| `KeyRingProvider` | `aquilia/auth/integration/di_providers.py` | Provider for KeyRing. |
| `TokenManagerProvider` | `aquilia/auth/integration/di_providers.py` | Provider for TokenManager. |
| `RateLimiterProvider` | `aquilia/auth/integration/di_providers.py` | Provider for RateLimiter. |
| `IdentityStoreProvider` | `aquilia/auth/integration/di_providers.py` | Provider for IdentityStore. |
| `CredentialStoreProvider` | `aquilia/auth/integration/di_providers.py` | Provider for CredentialStore. |
| `TokenStoreProvider` | `aquilia/auth/integration/di_providers.py` | Provider for TokenStore. |
| `OAuthClientStoreProvider` | `aquilia/auth/integration/di_providers.py` | Provider for OAuthClientStore. |
| `AuthorizationCodeStoreProvider` | `aquilia/auth/integration/di_providers.py` | Provider for AuthorizationCodeStore. |
| `DeviceCodeStoreProvider` | `aquilia/auth/integration/di_providers.py` | Provider for DeviceCodeStore. |
| `AuthManagerProvider` | `aquilia/auth/integration/di_providers.py` | Provider for AuthManager. |
| `MFAManagerProvider` | `aquilia/auth/integration/di_providers.py` | Provider for MFAManager. |
| `OAuth2ManagerProvider` | `aquilia/auth/integration/di_providers.py` | Provider for OAuth2Manager. |
| `AuthzEngineProvider` | `aquilia/auth/integration/di_providers.py` | Provider for AuthzEngine. |
| `SessionEngineProvider` | `aquilia/auth/integration/di_providers.py` | Provider for SessionEngine. |
| `SessionAuthBridgeProvider` | `aquilia/auth/integration/di_providers.py` | Provider for SessionAuthBridge. |
| `AuthConfig` | `aquilia/auth/integration/di_providers.py` | Authentication configuration builder. |
| `FlowGuard` | `aquilia/auth/integration/flow_guards.py` | Base class for Flow guards. |
| `RequireAuthGuard` | `aquilia/auth/integration/flow_guards.py` | Require valid authentication. |
| `RequireSessionAuthGuard` | `aquilia/auth/integration/flow_guards.py` | Require authentication via session. |
| `RequireTokenAuthGuard` | `aquilia/auth/integration/flow_guards.py` | Require authentication via Bearer token. |
| `RequireApiKeyGuard` | `aquilia/auth/integration/flow_guards.py` | Require authentication via API key. |
| `RequireScopesGuard` | `aquilia/auth/integration/flow_guards.py` | Require specific OAuth scopes. |
| `RequireRolesGuard` | `aquilia/auth/integration/flow_guards.py` | Require specific roles. |
| `RequirePermissionGuard` | `aquilia/auth/integration/flow_guards.py` | Require specific permission. |
| `RequirePolicyGuard` | `aquilia/auth/integration/flow_guards.py` | Require custom authorization policy. |
| `ControllerGuardAdapter` | `aquilia/auth/integration/flow_guards.py` | Adapts a FlowGuard to work in the Controller pipeline. |
| `AquilAuthMiddleware` | `aquilia/auth/integration/middleware.py` | Unified middleware for Auth + Sessions + DI integration. |
| `OptionalAuthMiddleware` | `aquilia/auth/integration/middleware.py` | Auth middleware that doesn't require authentication. |
| `SessionMiddleware` | `aquilia/auth/integration/middleware.py` | Session-only middleware without authentication. |
| `FaultHandlerMiddleware` | `aquilia/auth/integration/middleware.py` | Middleware for handling faults with FaultEngine. |
| `EnhancedRequestScopeMiddleware` | `aquilia/auth/integration/middleware.py` | Enhanced request scope middleware with better integration. |
| `MemorySessionStore` | `aquilia/auth/integration/sessions.py` | In-memory session store for development/testing. |
| `SessionManager` | `aquilia/auth/integration/sessions.py` | Session manager for authentication. |
| `AuthSessionMiddleware` | `aquilia/auth/integration/sessions.py` | Middleware for session-based authentication. |
| `SignInProvisionPolicy` | `aquilia/auth/manager.py` | Provisioning policy for sign_in bootstrap behavior. |
| `AuthManager` | `aquilia/auth/manager.py` | Central authentication manager. |
| `TOTPProvider` | `aquilia/auth/mfa.py` | TOTP (Time-based One-Time Password) provider. |
| `WebAuthnProvider` | `aquilia/auth/mfa.py` | WebAuthn provider for passwordless authentication. |
| `MFAManager` | `aquilia/auth/mfa.py` | Central MFA manager coordinating all MFA providers. |
| `OAuth2Manager` | `aquilia/auth/oauth.py` | OAuth 2.0 / OIDC authorization server. |
| `PolicyDecision` | `aquilia/auth/policy/__init__.py` | Result of a policy evaluation. |
| `PolicyResult` | `aquilia/auth/policy/__init__.py` | Result of evaluating a policy rule. |
| `Policy` | `aquilia/auth/policy/__init__.py` | Base class for resource-based authorization policies. |
| `PolicyRegistry` | `aquilia/auth/policy/__init__.py` | Registry for authorization policies. |
| `MemoryIdentityStore` | `aquilia/auth/stores.py` | In-memory identity storage for development/testing. |
| `MemoryCredentialStore` | `aquilia/auth/stores.py` | In-memory credential storage for development/testing. |
| `MemoryOAuthClientStore` | `aquilia/auth/stores.py` | In-memory OAuth client storage for development/testing. |
| `MemoryTokenStore` | `aquilia/auth/stores.py` | In-memory token storage for development/testing. |
| `RedisTokenStore` | `aquilia/auth/stores.py` | Redis-backed token store with bloom filter for fast revocation checks. |
| `MemoryAuthorizationCodeStore` | `aquilia/auth/stores.py` | In-memory authorization code storage for OAuth2 flows. |
| `MemoryDeviceCodeStore` | `aquilia/auth/stores.py` | In-memory device code storage for device authorization flow. |

## Error Handling

Fault/error classes defined here:

`AuthorizationRequiredFault`, `FaultHandlerMiddleware`
