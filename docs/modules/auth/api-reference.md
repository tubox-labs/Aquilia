# Auth API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

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

## Public Exports

`ABACEngine`, `AUTHZ_INSUFFICIENT_ROLE`, `AUTHZ_INSUFFICIENT_SCOPE`, `AUTHZ_POLICY_DENIED`, `AUTHZ_RESOURCE_FORBIDDEN`, `AUTHZ_TENANT_MISMATCH`, `AUTH_ACCOUNT_LOCKED`, `AUTH_ACCOUNT_SUSPENDED`, `AUTH_BACKUP_CODE_EXHAUSTED`, `AUTH_BACKUP_CODE_INVALID`, `AUTH_CLIENT_INVALID`, `AUTH_CONSENT_REQUIRED`, `AUTH_DEVICE_CODE_EXPIRED`, `AUTH_DEVICE_CODE_PENDING`, `AUTH_GRANT_INVALID`, `AUTH_INVALID_CREDENTIALS`, `AUTH_KEY_EXPIRED`, `AUTH_KEY_REVOKED`, `AUTH_MFA_ALREADY_ENROLLED`, `AUTH_MFA_INVALID`, `AUTH_MFA_NOT_ENROLLED`, `AUTH_MFA_REQUIRED`, `AUTH_PASSWORD_BREACHED`, `AUTH_PASSWORD_REUSED`, `AUTH_PASSWORD_WEAK`, `AUTH_PKCE_INVALID`, `AUTH_RATE_LIMITED`, `AUTH_REDIRECT_URI_MISMATCH`, `AUTH_REQUIRED`, `AUTH_SCOPE_INVALID`, `AUTH_SESSION_HIJACK_DETECTED`, `AUTH_SESSION_INVALID`, `AUTH_SESSION_REQUIRED`, `AUTH_SLOW_DOWN`, `AUTH_TOKEN_EXPIRED`, `AUTH_TOKEN_INVALID`, `AUTH_TOKEN_REVOKED`, `AUTH_WEBAUTHN_INVALID`, `Abstain`, `AccessLevel`, `AdminGuard`, `Allow`, `ApiKeyCredential`, `AquilAuthMiddleware`, `AuditEvent`, `AuditEventType`, `AuditSeverity`, `AuditStore`, `AuditTrail`, `AuthConfig`, `AuthGuard`, `AuthManager`, `AuthManagerProvider`, `AuthPrincipal`, `AuthResult`, `AuthRuntimeContext`, `AuthorizationCodeStoreProvider`, `AuthorizationRequiredFault`, `AuthzEngine`, `AuthzEngineProvider`, `CSRFProtection`, `Clearance`, `ClearanceCondition`, `ClearanceEngine`, `ClearanceGuard`, `ClearanceVerdict`, `ControllerGuardAdapter`, `Credential`, `CredentialStatus`, `CredentialStore`, `CredentialStoreProvider`, `Deny`, `DeviceCodeStoreProvider`, `EnhancedRequestScopeMiddleware`, `FaultHandlerMiddleware`, `FlowGuard`, `HasherConfig`, `Identity`, `IdentityStatus`, `IdentityStore`, `IdentityStoreProvider`, `IdentityType`, `KeyAlgorithm`, `KeyDescriptor`, `KeyRing`, `KeyRingProvider`, `KeyStatus`, `LoggingAuditStore`, `MFACredential`, `MFAManager`, `MFAManagerProvider`, `MemoryAuditStore`, `MemoryCredentialStore`, `MemoryIdentityStore`, `MemoryTokenStore`, `OAuth2Manager`, `OAuth2ManagerProvider`, `OAuthClient`, `OAuthClientStore`, `OAuthClientStoreProvider`, `OptionalAuthMiddleware`, `PasswordCredential`, `PasswordHasher`, `PasswordHasherProvider`, `PasswordPolicy`, `PasswordPolicyProvider`, `Policy`, `PolicyDecision`, `PolicyRegistry`, `PolicyResult`, `RBACEngine`, `RateLimiter`, `RateLimiterProvider`, `RequestFingerprint`, `RequireApiKeyGuard`, `RequireAuthGuard`, `RequirePermissionGuard`, `RequirePolicyGuard`, `RequireRolesGuard`, `RequireScopesGuard`, `RequireSessionAuthGuard`, `RequireTokenAuthGuard`, `RoleGuard`, `ScopeGuard`, `SecurityHeaders`, `SessionAuthBridge`, `SessionAuthBridgeProvider`, `SessionEngineProvider`, `SessionMiddleware`, `SignInProvisionPolicy`, `TokenBinder`, `TokenClaims`, `TokenConfig`, `TokenManager`, `TokenManagerProvider`, `TokenStore`, `TokenStoreProvider`, `VerifiedEmailGuard`, `_extract_identity`, `_extract_session`, `api_session_policy`, `authenticated`, `bind_identity`, `bind_token_claims`, `build_merged_clearance`, `constant_time_compare`, `controller_require_auth`, `controller_require_permission`, `controller_require_roles`, `controller_require_scopes`, `create_auth_container`, `create_auth_middleware_stack`, `device_session_policy`, `during_hours`, `exempt`, `extract_controller_clearance`, `generate_opaque_id`, `generate_secure_token`, `get_auth_runtime_context`, `get_identity`, `get_identity_id`, `get_method_clearance`, `get_roles`, `get_scopes`, `get_session`, `get_tenant_id`, `grant`, `hash_password`, `hash_sensitive`, `hash_token`, `ip_allowlist`, `is_mfa_verified`, `is_owner_or_admin`, `is_same_tenant`, `is_verified`, `register_auth_providers`, `require_attribute`, `require_auth`, `require_identity`, `require_permission`, `require_roles`, `require_scopes`, `requires`, `reset_auth_runtime_context`, `rule`, `set_auth_runtime_context`, `set_identity`, `set_mfa_verified`, `user_session_policy`, `validate_password`, `verify_password`, `within_quota`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `AuditEventType` | `aquilia/auth/audit.py` | str, enum.Enum | Categories of security events. |
| `AuditSeverity` | `aquilia/auth/audit.py` | str, enum.Enum | Severity levels for audit events. |
| `AuditEvent` | `aquilia/auth/audit.py` | object | Structured security audit event. |
| `AuditStore` | `aquilia/auth/audit.py` | object | Base class for audit event storage. |
| `MemoryAuditStore` | `aquilia/auth/audit.py` | AuditStore | In-memory audit store for development/testing. |
| `LoggingAuditStore` | `aquilia/auth/audit.py` | AuditStore | Audit store that logs to Python logging framework. |
| `AuditTrail` | `aquilia/auth/audit.py` | object | Central audit trail for security events. |
| `Decision` | `aquilia/auth/authz.py` | str, Enum | Authorization decision. |
| `AuthzContext` | `aquilia/auth/authz.py` | object | Authorization context for policy evaluation. |
| `AuthzResult` | `aquilia/auth/authz.py` | object | Authorization result. |
| `RBACEngine` | `aquilia/auth/authz.py` | object | Role-Based Access Control engine. |
| `ABACEngine` | `aquilia/auth/authz.py` | object | Attribute-Based Access Control engine. |
| `ScopeChecker` | `aquilia/auth/authz.py` | object | OAuth2-style scope checking. |
| `AuthzEngine` | `aquilia/auth/authz.py` | object | Unified authorization engine. |
| `PolicyBuilder` | `aquilia/auth/authz.py` | object | Helper for building common authorization policies. |
| `AccessLevel` | `aquilia/auth/clearance.py` | enum.IntEnum | Hierarchical access tiers -- higher ordinal = stricter. |
| `ClearanceCondition` | `aquilia/auth/clearance.py` | Protocol | A callable predicate evaluated at request time. |
| `Clearance` | `aquilia/auth/clearance.py` | object | Immutable clearance requirement descriptor. |
| `ClearanceVerdict` | `aquilia/auth/clearance.py` | object | Result of a clearance evaluation. |
| `ClearanceEngine` | `aquilia/auth/clearance.py` | object | Evaluates clearance requirements against request context. |
| `ClearanceGuard` | `aquilia/auth/clearance.py` | object | Pipeline guard that enforces Clearance requirements. |
| `IdentityType` | `aquilia/auth/core.py` | str, Enum | Type of authenticated principal. |
| `IdentityStatus` | `aquilia/auth/core.py` | str, Enum | Identity status. |
| `Identity` | `aquilia/auth/core.py` | object | Authenticated principal (user or service). |
| `CredentialStatus` | `aquilia/auth/core.py` | str, Enum | Credential status. |
| `Credential` | `aquilia/auth/core.py` | Protocol | Base protocol for credentials. |
| `PasswordCredential` | `aquilia/auth/core.py` | object | Password-based credential. |
| `ApiKeyCredential` | `aquilia/auth/core.py` | object | API key credential (long-lived). |
| `OAuthClient` | `aquilia/auth/core.py` | object | OAuth2/OIDC client. |
| `MFACredential` | `aquilia/auth/core.py` | object | Multi-factor authentication credential. |
| `TokenClaims` | `aquilia/auth/core.py` | object | Access token claims (JWT payload). |
| `AuthResult` | `aquilia/auth/core.py` | object | Result of authentication operation. |
| `IdentityStore` | `aquilia/auth/core.py` | Protocol | Protocol for identity storage. |
| `CredentialStore` | `aquilia/auth/core.py` | Protocol | Protocol for credential storage. |
| `OAuthClientStore` | `aquilia/auth/core.py` | Protocol | Protocol for OAuth client storage. |
| `SurpArtifact` | `aquilia/auth/surp.py` | object | Base surp artifact. |
| `KeyArtifact` | `aquilia/auth/surp.py` | SurpArtifact | Cryptographic key artifact. |
| `PolicyArtifact` | `aquilia/auth/surp.py` | SurpArtifact | Authorization policy artifact. |
| `AuditEventArtifact` | `aquilia/auth/surp.py` | SurpArtifact | Audit event artifact. |
| `ArtifactSigner` | `aquilia/auth/surp.py` | object | Signs and verifies surp artifacts. |
| `MemoryArtifactStore` | `aquilia/auth/surp.py` | object | In-memory artifact store for development/testing. |
| `AuditLogger` | `aquilia/auth/surp.py` | object | Audit event logger with surp artifact integration. |
| `AuthorizationRequiredFault` | `aquilia/auth/decorators.py` | Fault | Raised when authorization check fails. |
| `AuthGuard` | `aquilia/auth/decorators.py` | object | Base class for authentication/authorization guards. |
| `AdminGuard` | `aquilia/auth/decorators.py` | AuthGuard | Guard that requires admin role. |
| `VerifiedEmailGuard` | `aquilia/auth/decorators.py` | AuthGuard | Guard that requires verified email. |
| `RoleGuard` | `aquilia/auth/decorators.py` | AuthGuard | Guard that requires specific role(s). |
| `ScopeGuard` | `aquilia/auth/decorators.py` | AuthGuard | Guard that requires specific scope(s). |
| `AUTH_INVALID_CREDENTIALS` | `aquilia/auth/faults.py` | Fault | Invalid username or password. |
| `AUTH_TOKEN_INVALID` | `aquilia/auth/faults.py` | Fault | Invalid or malformed token. |
| `AUTH_TOKEN_EXPIRED` | `aquilia/auth/faults.py` | Fault | Access token has expired. |
| `AUTH_TOKEN_REVOKED` | `aquilia/auth/faults.py` | Fault | Token has been revoked. |
| `AUTH_MFA_REQUIRED` | `aquilia/auth/faults.py` | Fault | Multi-factor authentication required. |
| `AUTH_MFA_INVALID` | `aquilia/auth/faults.py` | Fault | Invalid MFA code. |
| `AUTH_ACCOUNT_SUSPENDED` | `aquilia/auth/faults.py` | Fault | Account is suspended. |
| `AUTH_ACCOUNT_LOCKED` | `aquilia/auth/faults.py` | Fault | Account is locked due to failed login attempts. |
| `AUTH_RATE_LIMITED` | `aquilia/auth/faults.py` | Fault | Too many authentication attempts. |
| `AUTH_REQUIRED` | `aquilia/auth/faults.py` | Fault | Authentication required but not provided. |
| `AUTH_CLIENT_INVALID` | `aquilia/auth/faults.py` | Fault | Invalid OAuth client credentials. |
| `AUTH_GRANT_INVALID` | `aquilia/auth/faults.py` | Fault | Invalid OAuth grant (code, refresh token, etc.). |
| `AUTH_REDIRECT_URI_MISMATCH` | `aquilia/auth/faults.py` | Fault | OAuth redirect URI doesn't match registered URI. |
| `AUTH_SCOPE_INVALID` | `aquilia/auth/faults.py` | Fault | Requested scope is invalid or not allowed. |
| `AUTH_PKCE_INVALID` | `aquilia/auth/faults.py` | Fault | PKCE code verifier doesn't match challenge. |
| `AUTHZ_POLICY_DENIED` | `aquilia/auth/faults.py` | Fault | Authorization policy denied access. |
| `AUTHZ_INSUFFICIENT_SCOPE` | `aquilia/auth/faults.py` | Fault | Token missing required scopes. |
| `AUTHZ_INSUFFICIENT_ROLE` | `aquilia/auth/faults.py` | Fault | Identity missing required role. |
| `AUTHZ_RESOURCE_FORBIDDEN` | `aquilia/auth/faults.py` | Fault | Access to resource is forbidden. |
| `AUTHZ_TENANT_MISMATCH` | `aquilia/auth/faults.py` | Fault | Identity tenant doesn't match resource tenant. |
| `AUTH_PASSWORD_WEAK` | `aquilia/auth/faults.py` | Fault | Password doesn't meet policy requirements. |
| `AUTH_PASSWORD_BREACHED` | `aquilia/auth/faults.py` | Fault | Password found in breach database. |
| `AUTH_PASSWORD_REUSED` | `aquilia/auth/faults.py` | Fault | Password was recently used. |
| `AUTH_KEY_EXPIRED` | `aquilia/auth/faults.py` | Fault | API key has expired. |
| `AUTH_KEY_REVOKED` | `aquilia/auth/faults.py` | Fault | API key has been revoked. |
| `AUTH_SESSION_REQUIRED` | `aquilia/auth/faults.py` | Fault | Session required but not found. |
| `AUTH_SESSION_INVALID` | `aquilia/auth/faults.py` | Fault | Session is invalid or corrupted. |
| `AUTH_SESSION_HIJACK_DETECTED` | `aquilia/auth/faults.py` | Fault | Potential session hijacking detected. |
| `AUTH_CONSENT_REQUIRED` | `aquilia/auth/faults.py` | Fault | User consent required for OAuth flow. |
| `AUTH_DEVICE_CODE_PENDING` | `aquilia/auth/faults.py` | Fault | Device code authorization pending. |
| `AUTH_DEVICE_CODE_EXPIRED` | `aquilia/auth/faults.py` | Fault | Device code has expired. |
| `AUTH_SLOW_DOWN` | `aquilia/auth/faults.py` | Fault | Device flow polling too fast. |
| `AUTH_MFA_NOT_ENROLLED` | `aquilia/auth/faults.py` | Fault | MFA not enrolled for user. |
| `AUTH_MFA_ALREADY_ENROLLED` | `aquilia/auth/faults.py` | Fault | MFA already enrolled. |
| `AUTH_WEBAUTHN_INVALID` | `aquilia/auth/faults.py` | Fault | WebAuthn credential invalid. |
| `AUTH_BACKUP_CODE_INVALID` | `aquilia/auth/faults.py` | Fault | Invalid backup code. |
| `AUTH_BACKUP_CODE_EXHAUSTED` | `aquilia/auth/faults.py` | Fault | All backup codes used. |
| `Guard` | `aquilia/auth/guards.py` | object | Base guard for authentication/authorization. |
| `AuthGuard` | `aquilia/auth/guards.py` | Guard | Authentication guard - requires valid authentication. |
| `ApiKeyGuard` | `aquilia/auth/guards.py` | Guard | API key authentication guard. |
| `AuthzGuard` | `aquilia/auth/guards.py` | Guard | Authorization guard - enforces access control. |
| `ScopeGuard` | `aquilia/auth/guards.py` | Guard | Scope-only guard - quick scope check. |
| `RoleGuard` | `aquilia/auth/guards.py` | Guard | Role-only guard - quick role check. |
| `CSRFProtection` | `aquilia/auth/hardening.py` | object | CSRF token generation and validation. |
| `RequestFingerprint` | `aquilia/auth/hardening.py` | object | Fingerprint a request for session binding. |
| `SecurityHeaders` | `aquilia/auth/hardening.py` | object | Configurable security headers for HTTP responses. |
| `TokenBinder` | `aquilia/auth/hardening.py` | object | Binds tokens to client characteristics for proof-of-possession. |
| `HasherConfig` | `aquilia/auth/hashing.py` | object | Algorithm-agnostic configuration for :class:`PasswordHasher`. |
| `PasswordHasher` | `aquilia/auth/hashing.py` | object | Multi-algorithm password hasher with automatic algorithm detection. |
| `PasswordPolicy` | `aquilia/auth/hashing.py` | object | Password policy validator. |
| `AuthPrincipal` | `aquilia/auth/integration/aquila_sessions.py` | SessionPrincipal | Authentication principal for Aquilia Sessions. |
| `SessionAuthBridge` | `aquilia/auth/integration/aquila_sessions.py` | object | Bridge between AuthManager and SessionEngine. |
| `PasswordHasherProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for PasswordHasher. |
| `PasswordPolicyProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for PasswordPolicy. |
| `KeyRingProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for KeyRing. |
| `TokenManagerProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for TokenManager. |
| `RateLimiterProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for RateLimiter. |
| `IdentityStoreProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for IdentityStore. |
| `CredentialStoreProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for CredentialStore. |
| `TokenStoreProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for TokenStore. |
| `OAuthClientStoreProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for OAuthClientStore. |
| `AuthorizationCodeStoreProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for AuthorizationCodeStore. |
| `DeviceCodeStoreProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for DeviceCodeStore. |
| `AuthManagerProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for AuthManager. |
| `MFAManagerProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for MFAManager. |
| `OAuth2ManagerProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for OAuth2Manager. |
| `AuthzEngineProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for AuthzEngine. |
| `SessionEngineProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for SessionEngine. |
| `SessionAuthBridgeProvider` | `aquilia/auth/integration/di_providers.py` | object | Provider for SessionAuthBridge. |
| `AuthConfig` | `aquilia/auth/integration/di_providers.py` | object | Authentication configuration builder. |
| `FlowGuard` | `aquilia/auth/integration/flow_guards.py` | object | Base class for Flow guards. |
| `RequireAuthGuard` | `aquilia/auth/integration/flow_guards.py` | FlowGuard | Require valid authentication. |
| `RequireSessionAuthGuard` | `aquilia/auth/integration/flow_guards.py` | FlowGuard | Require authentication via session. |
| `RequireTokenAuthGuard` | `aquilia/auth/integration/flow_guards.py` | FlowGuard | Require authentication via Bearer token. |
| `RequireApiKeyGuard` | `aquilia/auth/integration/flow_guards.py` | FlowGuard | Require authentication via API key. |
| `RequireScopesGuard` | `aquilia/auth/integration/flow_guards.py` | FlowGuard | Require specific OAuth scopes. |
| `RequireRolesGuard` | `aquilia/auth/integration/flow_guards.py` | FlowGuard | Require specific roles. |
| `RequirePermissionGuard` | `aquilia/auth/integration/flow_guards.py` | FlowGuard | Require specific permission. |
| `RequirePolicyGuard` | `aquilia/auth/integration/flow_guards.py` | FlowGuard | Require custom authorization policy. |
| `ControllerGuardAdapter` | `aquilia/auth/integration/flow_guards.py` | object | Adapts a FlowGuard to work in the Controller pipeline. |
| `AquilAuthMiddleware` | `aquilia/auth/integration/middleware.py` | object | Unified middleware for Auth + Sessions + DI integration. |
| `OptionalAuthMiddleware` | `aquilia/auth/integration/middleware.py` | AquilAuthMiddleware | Auth middleware that doesn't require authentication. |
| `SessionMiddleware` | `aquilia/auth/integration/middleware.py` | object | Session-only middleware without authentication. |
| `FaultHandlerMiddleware` | `aquilia/auth/integration/middleware.py` | object | Middleware for handling faults with FaultEngine. |
| `EnhancedRequestScopeMiddleware` | `aquilia/auth/integration/middleware.py` | object | Enhanced request scope middleware with better integration. |
| `AuthRuntimeContext` | `aquilia/auth/integration/runtime_context.py` | object | Request-scoped auth runtime state. |
| `AuthSession` | `aquilia/auth/integration/sessions.py` | object | Authentication session. |
| `MemorySessionStore` | `aquilia/auth/integration/sessions.py` | object | In-memory session store for development/testing. |
| `SessionManager` | `aquilia/auth/integration/sessions.py` | object | Session manager for authentication. |
| `AuthSessionMiddleware` | `aquilia/auth/integration/sessions.py` | object | Middleware for session-based authentication. |
| `RateLimiter` | `aquilia/auth/manager.py` | object | Simple in-memory rate limiter for authentication attempts. |
| `SignInProvisionPolicy` | `aquilia/auth/manager.py` | object | Provisioning policy for sign_in bootstrap behavior. |
| `AuthManager` | `aquilia/auth/manager.py` | object | Central authentication manager. |
| `TOTPProvider` | `aquilia/auth/mfa.py` | object | TOTP (Time-based One-Time Password) provider. |
| `WebAuthnProvider` | `aquilia/auth/mfa.py` | object | WebAuthn provider for passwordless authentication. |
| `MFAManager` | `aquilia/auth/mfa.py` | object | Central MFA manager coordinating all MFA providers. |
| `PKCEVerifier` | `aquilia/auth/oauth.py` | object | PKCE (Proof Key for Code Exchange) utilities. |
| `OAuth2Manager` | `aquilia/auth/oauth.py` | object | OAuth 2.0 / OIDC authorization server. |
| `PolicyDecision` | `aquilia/auth/policy/__init__.py` | Enum | Result of a policy evaluation. |
| `PolicyResult` | `aquilia/auth/policy/__init__.py` | object | Result of evaluating a policy rule. |
| `Policy` | `aquilia/auth/policy/__init__.py` | object | Base class for resource-based authorization policies. |
| `PolicyRegistry` | `aquilia/auth/policy/__init__.py` | object | Registry for authorization policies. |
| `MemoryIdentityStore` | `aquilia/auth/stores.py` | object | In-memory identity storage for development/testing. |
| `MemoryCredentialStore` | `aquilia/auth/stores.py` | object | In-memory credential storage for development/testing. |
| `MemoryOAuthClientStore` | `aquilia/auth/stores.py` | object | In-memory OAuth client storage for development/testing. |
| `MemoryTokenStore` | `aquilia/auth/stores.py` | object | In-memory token storage for development/testing. |
| `RedisTokenStore` | `aquilia/auth/stores.py` | object | Redis-backed token store with bloom filter for fast revocation checks. |
| `MemoryAuthorizationCodeStore` | `aquilia/auth/stores.py` | object | In-memory authorization code storage for OAuth2 flows. |
| `MemoryDeviceCodeStore` | `aquilia/auth/stores.py` | object | In-memory device code storage for device authorization flow. |
| `KeyAlgorithm` | `aquilia/auth/tokens.py` | str, Enum | Supported signing algorithms (Enum prevents arbitrary values). |
| `KeyStatus` | `aquilia/auth/tokens.py` | str, Enum | Key status in lifecycle (Enum prevents invalid state transitions). |
| `KeyDescriptor` | `aquilia/auth/tokens.py` | object | Cryptographic key metadata. |
| `KeyRing` | `aquilia/auth/tokens.py` | object | Key ring for JWT signing and verification. |
| `TokenConfig` | `aquilia/auth/tokens.py` | object | Token manager configuration. |
| `TokenStore` | `aquilia/auth/tokens.py` | Protocol | Protocol for token storage (opaque tokens, revocation). |
| `TokenManager` | `aquilia/auth/tokens.py` | object | Token lifecycle manager. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `is_verified` | `aquilia/auth/clearance.py` | `def is_verified(identity: Any, request: Any, ctx: Any)` | Condition: identity must have 'verified' attribute or status ACTIVE. |
| `is_owner_or_admin` | `aquilia/auth/clearance.py` | `def is_owner_or_admin(identity: Any, request: Any, ctx: Any)` | Condition: identity is resource owner or has admin role. |
| `within_quota` | `aquilia/auth/clearance.py` | `def within_quota(identity: Any, request: Any, ctx: Any)` | Condition: identity hasn't exceeded rate/resource quota. |
| `is_same_tenant` | `aquilia/auth/clearance.py` | `def is_same_tenant(identity: Any, request: Any, ctx: Any)` | Condition: identity's tenant matches resource tenant. |
| `during_hours` | `aquilia/auth/clearance.py` | `def during_hours(start: int=9, end: int=17)` | Factory: condition that restricts access to business hours (UTC). |
| `require_attribute` | `aquilia/auth/clearance.py` | `def require_attribute(key: str, value: Any=None)` | Factory: condition that requires a specific identity attribute. |
| `ip_allowlist` | `aquilia/auth/clearance.py` | `def ip_allowlist(*cidrs: str)` | Factory: condition restricting access to specific IP ranges. |
| `grant` | `aquilia/auth/clearance.py` | `def grant(level: AccessLevel=AccessLevel.AUTHENTICATED, entitlements: Sequence[str]=(), conditions: Sequence[Callable]=(), compartment: str \| None=None, deny_message: str='Insufficient clearance', audit: bool=True)` | Decorator to attach clearance requirements to a route method. |
| `exempt` | `aquilia/auth/clearance.py` | `def exempt(fn: Callable)` | Decorator to exempt a route from class-level clearance. |
| `get_method_clearance` | `aquilia/auth/clearance.py` | `def get_method_clearance(method: Any)` | Extract clearance from a decorated method. |
| `extract_controller_clearance` | `aquilia/auth/clearance.py` | `def extract_controller_clearance(controller_class: type)` | Extract clearance from controller class. |
| `build_merged_clearance` | `aquilia/auth/clearance.py` | `def build_merged_clearance(controller_class: type, handler_method: Any)` | Build merged clearance from class + method. |
| `authenticated` | `aquilia/auth/decorators.py` | `def authenticated(func: F \| None=None, *, login_url: str \| None=None, redirect_if_html: bool=False, include_next: bool=True, next_param: str='next', redirect_status: int=303)` | Decorator requiring authenticated identity. |
| `require_identity` | `aquilia/auth/decorators.py` | `def require_identity(*, roles: list[str] \| None=None, scopes: list[str] \| None=None, attributes: dict[str, Any] \| None=None, require_all_roles: bool=False, require_all_scopes: bool=True, login_url: str \| None=None, redirect_if_html: bool=False, include_next: bool=True, next_param: str='next', redirect_status: int=303)` | Decorator requiring identity with specific attributes. |
| `requires` | `aquilia/auth/decorators.py` | `def requires(*guards: AuthGuard)` | Decorator to require multiple guards. |
| `raise_auth_fault` | `aquilia/auth/faults.py` | `def raise_auth_fault(fault_class: type[Fault], **kwargs)` | Raise an auth fault with context. |
| `is_auth_fault` | `aquilia/auth/faults.py` | `def is_auth_fault(exception: Exception)` | Check if exception is an auth fault. |
| `require_auth` | `aquilia/auth/guards.py` | `def require_auth(auth_manager: AuthManager, optional: bool=False)` | Decorator: Require authentication. |
| `require_scopes` | `aquilia/auth/guards.py` | `def require_scopes(*scopes: str)` | Decorator: Require OAuth scopes. |
| `require_roles` | `aquilia/auth/guards.py` | `def require_roles(*roles: str, require_all: bool=False)` | Decorator: Require roles. |
| `constant_time_compare` | `aquilia/auth/hardening.py` | `def constant_time_compare(a: str \| bytes, b: str \| bytes)` | Compare two strings/bytes in constant time to prevent timing attacks. |
| `generate_secure_token` | `aquilia/auth/hardening.py` | `def generate_secure_token(length: int=32)` | Generate a cryptographically secure random token. |
| `generate_opaque_id` | `aquilia/auth/hardening.py` | `def generate_opaque_id(prefix: str='aq')` | Generate an opaque identifier with prefix. |
| `hash_token` | `aquilia/auth/hardening.py` | `def hash_token(token: str)` | Hash a token for storage (one-way). |
| `hash_sensitive` | `aquilia/auth/hardening.py` | `def hash_sensitive(value: str, salt: str='')` | Hash sensitive data with optional salt. |
| `get_password_hasher` | `aquilia/auth/hashing.py` | `def get_password_hasher()` | Get default password hasher instance. |
| `hash_password` | `aquilia/auth/hashing.py` | `def hash_password(password: str)` | Hash password with default hasher. |
| `verify_password` | `aquilia/auth/hashing.py` | `def verify_password(password_hash: str, password: str)` | Verify password with default hasher. |
| `validate_password` | `aquilia/auth/hashing.py` | `def validate_password(password: str, policy: PasswordPolicy \| None=None)` | Validate password against policy. |
| `bind_identity` | `aquilia/auth/integration/aquila_sessions.py` | `def bind_identity(session: Session, identity: Identity)` | Bind identity to session. |
| `bind_token_claims` | `aquilia/auth/integration/aquila_sessions.py` | `def bind_token_claims(session: Session, claims: TokenClaims)` | Bind token claims to session. |
| `get_identity_id` | `aquilia/auth/integration/aquila_sessions.py` | `def get_identity_id(session: Session)` | Get identity ID from session. |
| `get_tenant_id` | `aquilia/auth/integration/aquila_sessions.py` | `def get_tenant_id(session: Session)` | Get tenant ID from session. |
| `get_roles` | `aquilia/auth/integration/aquila_sessions.py` | `def get_roles(session: Session)` | Get roles from session. |
| `get_scopes` | `aquilia/auth/integration/aquila_sessions.py` | `def get_scopes(session: Session)` | Get scopes from session. |
| `is_mfa_verified` | `aquilia/auth/integration/aquila_sessions.py` | `def is_mfa_verified(session: Session)` | Check if MFA was verified for this session. |
| `set_mfa_verified` | `aquilia/auth/integration/aquila_sessions.py` | `def set_mfa_verified(session: Session)` | Mark session as MFA verified. |
| `user_session_policy` | `aquilia/auth/integration/aquila_sessions.py` | `def user_session_policy(ttl: timedelta=timedelta(days=7), idle_timeout: timedelta=timedelta(hours=1), max_sessions: int \| None=5, store_name: str='redis')` | Create policy for user web sessions. |
| `api_session_policy` | `aquilia/auth/integration/aquila_sessions.py` | `def api_session_policy(ttl: timedelta=timedelta(hours=1), max_sessions: int \| None=None)` | Create policy for API token sessions. |
| `device_session_policy` | `aquilia/auth/integration/aquila_sessions.py` | `def device_session_policy(ttl: timedelta=timedelta(days=90), idle_timeout: timedelta=timedelta(days=30))` | Create policy for device (mobile app) sessions. |
| `register_auth_providers` | `aquilia/auth/integration/di_providers.py` | `def register_auth_providers(container: Container, config: dict[str, Any] \| None=None)` | Register all auth providers in DI container. |
| `create_auth_container` | `aquilia/auth/integration/di_providers.py` | `def create_auth_container(config: dict[str, Any] \| None=None, parent: Container \| None=None)` | Create DI container with all auth providers registered. |
| `get_session` | `aquilia/auth/integration/flow_guards.py` | `def get_session(context: Any)` | Extract session from flow context. |
| `get_identity` | `aquilia/auth/integration/flow_guards.py` | `def get_identity(context: Any)` | Extract identity from flow context. |
| `set_identity` | `aquilia/auth/integration/flow_guards.py` | `def set_identity(context: Any, identity: Identity \| None)` | Set identity in flow context. |
| `controller_require_auth` | `aquilia/auth/integration/flow_guards.py` | `def controller_require_auth(optional: bool=False)` | Create auth guard for Controller pipeline. |
| `controller_require_scopes` | `aquilia/auth/integration/flow_guards.py` | `def controller_require_scopes(*scopes: str, require_all: bool=True)` | Create scope guard for Controller pipeline. |
| `controller_require_roles` | `aquilia/auth/integration/flow_guards.py` | `def controller_require_roles(*roles: str, require_all: bool=True)` | Create role guard for Controller pipeline. |
| `controller_require_permission` | `aquilia/auth/integration/flow_guards.py` | `def controller_require_permission(authz_engine: AuthzEngine, permission: str, resource: str \| None=None)` | Create permission guard for Controller pipeline. |
| `require_auth` | `aquilia/auth/integration/flow_guards.py` | `def require_auth(optional: bool=False)` | Create authentication guard node. |
| `require_scopes` | `aquilia/auth/integration/flow_guards.py` | `def require_scopes(*scopes: str, require_all: bool=True)` | Create scope guard node. |
| `require_roles` | `aquilia/auth/integration/flow_guards.py` | `def require_roles(*roles: str, require_all: bool=True)` | Create role guard node. |
| `require_permission` | `aquilia/auth/integration/flow_guards.py` | `def require_permission(authz_engine: AuthzEngine, permission: str, resource: str \| None=None)` | Create permission guard node. |
| `create_auth_middleware_stack` | `aquilia/auth/integration/middleware.py` | `def create_auth_middleware_stack(session_engine: SessionEngine, auth_manager: AuthManager, app_container: Container, fault_engine: FaultEngine \| None=None, require_auth: bool=False)` | Create complete middleware stack for authenticated app. |
| `set_auth_runtime_context` | `aquilia/auth/integration/runtime_context.py` | `def set_auth_runtime_context(context: AuthRuntimeContext)` | Set auth runtime context for current async task execution. |
| `reset_auth_runtime_context` | `aquilia/auth/integration/runtime_context.py` | `def reset_auth_runtime_context(token: Token)` | Reset auth runtime context to previous value. |
| `get_auth_runtime_context` | `aquilia/auth/integration/runtime_context.py` | `def get_auth_runtime_context()` | Get current auth runtime context, if any. |
| `Allow` | `aquilia/auth/policy/__init__.py` | `def Allow(reason: str \| None=None, **metadata)` | Create an Allow decision. |
| `Deny` | `aquilia/auth/policy/__init__.py` | `def Deny(reason: str \| None=None, **metadata)` | Create a Deny decision. |
| `Abstain` | `aquilia/auth/policy/__init__.py` | `def Abstain(reason: str \| None=None)` | Create an Abstain decision (defer to next rule/policy). |
| `rule` | `aquilia/auth/policy/__init__.py` | `def rule(func: Callable)` | Decorator to mark a method as a policy rule. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `_CLEARANCE_ATTR` | `aquilia/auth/clearance.py` | `'__aquilia_clearance__'` |
| `F` | `aquilia/auth/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |
| `SUPPORTED_ALGORITHMS` | `aquilia/auth/hashing.py` | `('argon2id', 'scrypt', 'bcrypt', 'pbkdf2_sha512', 'pbkdf2_sha256')` |
| `_AUTH_RUNTIME_CONTEXT` | `aquilia/auth/integration/runtime_context.py` | `ContextVar[AuthRuntimeContext \| None]` |
| `_HMAC_ALGORITHMS` | `aquilia/auth/tokens.py` | `frozenset[str]` |
| `_ASYMMETRIC_ALGORITHMS` | `aquilia/auth/tokens.py` | `frozenset[str]` |
| `_SUPPORTED_ALGORITHMS` | `aquilia/auth/tokens.py` | `frozenset[str]` |
| `_HMAC_DIGEST` | `aquilia/auth/tokens.py` | `dict[str, str]` |

## Detailed Classes And Methods

### `AuditEventType`

- Source: `aquilia/auth/audit.py`
- Bases: `str, enum.Enum`
- Summary: Categories of security events.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `AUTH_LOGIN_SUCCESS` | `` | `'auth.login.success'` |
| `AUTH_LOGIN_FAILURE` | `` | `'auth.login.failure'` |
| `AUTH_LOGOUT` | `` | `'auth.logout'` |
| `AUTH_TOKEN_ISSUED` | `` | `'auth.token.issued'` |
| `AUTH_TOKEN_REFRESHED` | `` | `'auth.token.refreshed'` |
| `AUTH_TOKEN_REVOKED` | `` | `'auth.token.revoked'` |
| `AUTH_TOKEN_EXPIRED` | `` | `'auth.token.expired'` |
| `AUTH_TOKEN_INVALID` | `` | `'auth.token.invalid'` |
| `AUTH_API_KEY_USED` | `` | `'auth.apikey.used'` |
| `AUTH_API_KEY_REJECTED` | `` | `'auth.apikey.rejected'` |
| `AUTH_MFA_CHALLENGE` | `` | `'auth.mfa.challenge'` |
| `AUTH_MFA_SUCCESS` | `` | `'auth.mfa.success'` |
| `AUTH_MFA_FAILURE` | `` | `'auth.mfa.failure'` |
| `AUTHZ_ACCESS_GRANTED` | `` | `'authz.access.granted'` |
| `AUTHZ_ACCESS_DENIED` | `` | `'authz.access.denied'` |
| `AUTHZ_CLEARANCE_GRANTED` | `` | `'authz.clearance.granted'` |
| `AUTHZ_CLEARANCE_DENIED` | `` | `'authz.clearance.denied'` |
| `AUTHZ_POLICY_EVALUATED` | `` | `'authz.policy.evaluated'` |
| `SESSION_CREATED` | `` | `'session.created'` |
| `SESSION_DESTROYED` | `` | `'session.destroyed'` |
| `SESSION_EXPIRED` | `` | `'session.expired'` |
| `SESSION_HIJACK_ATTEMPT` | `` | `'session.hijack_attempt'` |
| `ACCOUNT_LOCKED` | `` | `'account.locked'` |
| `ACCOUNT_UNLOCKED` | `` | `'account.unlocked'` |
| `ACCOUNT_SUSPENDED` | `` | `'account.suspended'` |
| `ACCOUNT_RATE_LIMITED` | `` | `'account.rate_limited'` |
| `ACCOUNT_PASSWORD_CHANGED` | `` | `'account.password_changed'` |
| `ACCOUNT_CREATED` | `` | `'account.created'` |
| `OAUTH_AUTH_CODE_ISSUED` | `` | `'oauth.authcode.issued'` |
| `OAUTH_CLIENT_AUTH` | `` | `'oauth.client.auth'` |
| `OAUTH_DEVICE_AUTH` | `` | `'oauth.device.auth'` |
| `SECURITY_KEY_ROTATED` | `` | `'security.key.rotated'` |
| `SECURITY_KEY_REVOKED` | `` | `'security.key.revoked'` |
| `SECURITY_CONFIG_CHANGED` | `` | `'security.config.changed'` |

### `AuditSeverity`

- Source: `aquilia/auth/audit.py`
- Bases: `str, enum.Enum`
- Summary: Severity levels for audit events.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `INFO` | `` | `'info'` |
| `WARNING` | `` | `'warning'` |
| `CRITICAL` | `` | `'critical'` |
| `ALERT` | `` | `'alert'` |

### `AuditEvent`

- Source: `aquilia/auth/audit.py`
- Bases: `object`
- Summary: Structured security audit event.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `event_type` | `AuditEventType` | `` |
| `severity` | `AuditSeverity` | `` |
| `timestamp` | `float` | `field(default_factory=time.time)` |
| `identity_id` | `str \| None` | `None` |
| `ip_address` | `str \| None` | `None` |
| `user_agent` | `str \| None` | `None` |
| `resource` | `str \| None` | `None` |
| `action` | `str \| None` | `None` |
| `outcome` | `str` | `'success'` |
| `details` | `dict[str, Any]` | `field(default_factory=dict)` |
| `request_id` | `str \| None` | `None` |
| `session_id` | `str \| None` | `None` |
| `tenant_id` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `timestamp_iso` | `def timestamp_iso(self)` | ISO 8601 timestamp. |
| `to_dict` | `def to_dict(self)` | Serialize to dict for logging/storage. |
| `to_json` | `def to_json(self)` | Serialize to JSON string. |

### `AuditStore`

- Source: `aquilia/auth/audit.py`
- Bases: `object`
- Summary: Base class for audit event storage.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `emit` | `async def emit(self, event: AuditEvent)` | Store/emit an audit event. |
| `query` | `async def query(self, event_type: AuditEventType \| None=None, identity_id: str \| None=None, since: float \| None=None, until: float \| None=None, limit: int=100)` | Query stored events. Optional -- not all stores support this. |

### `MemoryAuditStore`

- Source: `aquilia/auth/audit.py`
- Bases: `AuditStore`
- Summary: In-memory audit store for development/testing.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `emit` | `async def emit(self, event: AuditEvent)` | Store event in memory. |
| `query` | `async def query(self, event_type: AuditEventType \| None=None, identity_id: str \| None=None, since: float \| None=None, until: float \| None=None, limit: int=100)` | Query events from memory store. |
| `clear` | `def clear(self)` | Clear all stored events. |
| `events` | `def events(self)` | Access stored events. |

### `LoggingAuditStore`

- Source: `aquilia/auth/audit.py`
- Bases: `AuditStore`
- Summary: Audit store that logs to Python logging framework.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `emit` | `async def emit(self, event: AuditEvent)` | Emit event to logger. |

### `AuditTrail`

- Source: `aquilia/auth/audit.py`
- Bases: `object`
- Summary: Central audit trail for security events.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add_store` | `def add_store(self, store: AuditStore)` | Add an audit store. |
| `emit` | `async def emit(self, event: AuditEvent)` | Emit an event to all stores. |
| `login_success` | `async def login_success(self, identity_id: str, request: Any=None, method: str='password', **extra)` | Record successful login. |
| `login_failure` | `async def login_failure(self, identity_id: str \| None, request: Any=None, reason: str='invalid_credentials', **extra)` | Record failed login attempt. |
| `access_denied` | `async def access_denied(self, identity_id: str \| None, resource: str, request: Any=None, reason: str='insufficient_permissions', **extra)` | Record access denied event. |
| `clearance_evaluated` | `async def clearance_evaluated(self, identity_id: str \| None, resource: str, granted: bool, request: Any=None, **extra)` | Record clearance evaluation result. |
| `token_event` | `async def token_event(self, event_type: AuditEventType, identity_id: str, request: Any=None, **extra)` | Record token lifecycle event. |
| `account_locked` | `async def account_locked(self, identity_id: str, request: Any=None, reason: str='max_attempts_exceeded', **extra)` | Record account lockout. |
| `session_event` | `async def session_event(self, event_type: AuditEventType, identity_id: str \| None=None, request: Any=None, **extra)` | Record session lifecycle event. |
| `query` | `async def query(self, event_type: AuditEventType \| None=None, identity_id: str \| None=None, since: float \| None=None, until: float \| None=None, limit: int=100)` | Query events from first store that supports it. |

### `Decision`

- Source: `aquilia/auth/authz.py`
- Bases: `str, Enum`
- Summary: Authorization decision.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `ALLOW` | `` | `'allow'` |
| `DENY` | `` | `'deny'` |
| `ABSTAIN` | `` | `'abstain'` |

### `AuthzContext`

- Source: `aquilia/auth/authz.py`
- Bases: `object`
- Summary: Authorization context for policy evaluation.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `identity` | `Identity` | `` |
| `resource` | `str` | `` |
| `action` | `str` | `` |
| `scopes` | `list[str]` | `field(default_factory=list)` |
| `roles` | `list[str]` | `field(default_factory=list)` |
| `attributes` | `dict[str, Any]` | `field(default_factory=dict)` |
| `tenant_id` | `str \| None` | `None` |
| `session_id` | `str \| None` | `None` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

### `AuthzResult`

- Source: `aquilia/auth/authz.py`
- Bases: `object`
- Summary: Authorization result.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `decision` | `Decision` | `` |
| `reason` | `str \| None` | `None` |
| `policy_id` | `str \| None` | `None` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

### `RBACEngine`

- Source: `aquilia/auth/authz.py`
- Bases: `object`
- Summary: Role-Based Access Control engine.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `define_role` | `def define_role(self, role: str, permissions: list[str], inherits: list[str] \| None=None)` | Define role with permissions and inheritance. |
| `get_permissions` | `def get_permissions(self, role: str, _visited: set[str] \| None=None)` | Get all permissions for role (including inherited). |
| `check_permission` | `def check_permission(self, roles: list[str], permission: str)` | Check if any role has permission. |
| `check` | `def check(self, context: AuthzContext, permission: str)` | Check authorization using RBAC. |

### `ABACEngine`

- Source: `aquilia/auth/authz.py`
- Bases: `object`
- Summary: Attribute-Based Access Control engine.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register_policy` | `def register_policy(self, policy_id: str, policy_func: Callable[[AuthzContext], AuthzResult])` | Register attribute-based policy. |
| `evaluate` | `def evaluate(self, context: AuthzContext, policy_id: str)` | Evaluate specific policy. |

### `ScopeChecker`

- Source: `aquilia/auth/authz.py`
- Bases: `object`
- Summary: OAuth2-style scope checking.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `check_scopes` | `def check_scopes(available_scopes: list[str], required_scopes: list[str])` | Check if available scopes satisfy requirements. |
| `check` | `def check(context: AuthzContext, required_scopes: list[str])` | Check scope-based authorization. |

### `AuthzEngine`

- Source: `aquilia/auth/authz.py`
- Bases: `object`
- Summary: Unified authorization engine.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `set_policy_order` | `def set_policy_order(self, policy_ids: list[str])` | Set evaluation order for policies. |
| `check_scope` | `def check_scope(self, context: AuthzContext, required_scopes: list[str])` | Check scope requirements (raises if failed). |
| `check_role` | `def check_role(self, context: AuthzContext, required_roles: list[str])` | Check role requirements (raises if failed). |
| `check_permission` | `def check_permission(self, context: AuthzContext, permission: str)` | Check RBAC permission (raises if failed). |
| `check_tenant` | `def check_tenant(self, context: AuthzContext, resource_tenant_id: str)` | Check tenant isolation (multi-tenancy). |
| `check` | `def check(self, context: AuthzContext)` | Comprehensive authorization check. |
| `authorize` | `def authorize(self, context: AuthzContext, raise_on_deny: bool=True)` | Authorize action (with optional exception raising). |
| `list_permitted_actions` | `def list_permitted_actions(self, identity: Identity, resource: str, actions: list[str])` | List permitted actions for resource. |

### `PolicyBuilder`

- Source: `aquilia/auth/authz.py`
- Bases: `object`
- Summary: Helper for building common authorization policies.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `owner_only` | `def owner_only(attribute: str='owner_id')` | Policy: Only resource owner can access. |
| `admin_or_owner` | `def admin_or_owner(admin_role: str='admin', attribute: str='owner_id')` | Policy: Admin or resource owner can access. |
| `time_based` | `def time_based(allowed_hours: tuple[int, int]=(9, 17))` | Policy: Allow access only during specific hours (UTC). |

### `AccessLevel`

- Source: `aquilia/auth/clearance.py`
- Bases: `enum.IntEnum`
- Summary: Hierarchical access tiers -- higher ordinal = stricter.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `PUBLIC` | `` | `0` |
| `AUTHENTICATED` | `` | `10` |
| `INTERNAL` | `` | `20` |
| `CONFIDENTIAL` | `` | `30` |
| `RESTRICTED` | `` | `40` |

### `ClearanceCondition`

- Source: `aquilia/auth/clearance.py`
- Bases: `Protocol`
- Summary: A callable predicate evaluated at request time.
- Decorators: `runtime_checkable`

### `Clearance`

- Source: `aquilia/auth/clearance.py`
- Bases: `object`
- Summary: Immutable clearance requirement descriptor.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `level` | `AccessLevel` | `AccessLevel.AUTHENTICATED` |
| `entitlements` | `tuple[str, ...]` | `()` |
| `conditions` | `tuple[Callable, ...]` | `()` |
| `compartment` | `str \| None` | `None` |
| `deny_message` | `str` | `'Insufficient clearance'` |
| `audit` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `merge` | `def merge(self, override: Clearance)` | Merge this (class-level) clearance with an override (method-level). |

### `ClearanceVerdict`

- Source: `aquilia/auth/clearance.py`
- Bases: `object`
- Summary: Result of a clearance evaluation.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `granted` | `bool` | `` |
| `level_ok` | `bool` | `` |
| `entitlements_ok` | `bool` | `` |
| `conditions_ok` | `bool` | `` |
| `compartment_ok` | `bool` | `` |
| `missing_entitlements` | `tuple[str, ...]` | `()` |
| `failed_conditions` | `tuple[str, ...]` | `()` |
| `message` | `str` | `''` |
| `evaluated_at` | `float` | `0.0` |
| `identity_id` | `str \| None` | `None` |

### `ClearanceEngine`

- Source: `aquilia/auth/clearance.py`
- Bases: `object`
- Summary: Evaluates clearance requirements against request context.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve_identity_level` | `def resolve_identity_level(self, identity: Any)` | Determine the highest AccessLevel an identity holds. |
| `resolve_entitlements` | `def resolve_entitlements(self, identity: Any)` | Resolve the set of entitlements an identity holds. |
| `resolve_compartment` | `def resolve_compartment(self, compartment_template: str \| None, identity: Any, request: Any, ctx: Any)` | Resolve a compartment template to a concrete value. |
| `evaluate` | `async def evaluate(self, clearance: Clearance, identity: Any, request: Any, ctx: Any)` | Evaluate a clearance requirement against the current context. |
| `clear_cache` | `def clear_cache(self)` | Clear identity level cache. |

### `ClearanceGuard`

- Source: `aquilia/auth/clearance.py`
- Bases: `object`
- Summary: Pipeline guard that enforces Clearance requirements.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `for_controller` | `def for_controller(self)` | Return self -- already works as controller pipeline guard. |

### `IdentityType`

- Source: `aquilia/auth/core.py`
- Bases: `str, Enum`
- Summary: Type of authenticated principal.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `USER` | `` | `'user'` |
| `SERVICE` | `` | `'service'` |
| `DEVICE` | `` | `'device'` |
| `ANONYMOUS` | `` | `'anonymous'` |

### `IdentityStatus`

- Source: `aquilia/auth/core.py`
- Bases: `str, Enum`
- Summary: Identity status.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `ACTIVE` | `` | `'active'` |
| `SUSPENDED` | `` | `'suspended'` |
| `DELETED` | `` | `'deleted'` |
| `PENDING` | `` | `'pending'` |

### `Identity`

- Source: `aquilia/auth/core.py`
- Bases: `object`
- Summary: Authenticated principal (user or service).
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `id` | `str` | `` |
| `type` | `IdentityType` | `` |
| `attributes` | `dict[str, Any]` | `` |
| `status` | `IdentityStatus` | `IdentityStatus.ACTIVE` |
| `tenant_id` | `str \| None` | `None` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `updated_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_attribute` | `def get_attribute(self, key: str, default: Any=None)` | Get attribute value with default. |
| `has_role` | `def has_role(self, role: str)` | Check if identity has role. |
| `has_scope` | `def has_scope(self, scope: str)` | Check if identity has scope. |
| `is_active` | `def is_active(self)` | Check if identity is active. |
| `to_dict` | `def to_dict(self)` | Serialize to dict. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any])` | Deserialize from dict. |

### `CredentialStatus`

- Source: `aquilia/auth/core.py`
- Bases: `str, Enum`
- Summary: Credential status.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `ACTIVE` | `` | `'active'` |
| `SUSPENDED` | `` | `'suspended'` |
| `REVOKED` | `` | `'revoked'` |
| `EXPIRED` | `` | `'expired'` |

### `Credential`

- Source: `aquilia/auth/core.py`
- Bases: `Protocol`
- Summary: Base protocol for credentials.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `identity_id` | `str` | `` |
| `status` | `CredentialStatus` | `` |
| `created_at` | `datetime` | `` |
| `last_used_at` | `datetime \| None` | `` |

### `PasswordCredential`

- Source: `aquilia/auth/core.py`
- Bases: `object`
- Summary: Password-based credential.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `identity_id` | `str` | `` |
| `password_hash` | `str` | `` |
| `algorithm` | `str` | `'argon2id'` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `last_changed_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `last_used_at` | `datetime \| None` | `None` |
| `must_change` | `bool` | `False` |
| `status` | `CredentialStatus` | `CredentialStatus.ACTIVE` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `should_rotate` | `def should_rotate(self, max_age_days: int=90)` | Check if password should be rotated. |
| `touch` | `def touch(self)` | Update last_used_at timestamp. |
| `to_dict` | `def to_dict(self)` | Serialize to dict. |

### `ApiKeyCredential`

- Source: `aquilia/auth/core.py`
- Bases: `object`
- Summary: API key credential (long-lived).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `identity_id` | `str` | `` |
| `key_id` | `str` | `` |
| `key_hash` | `str` | `` |
| `prefix` | `str` | `` |
| `scopes` | `list[str]` | `` |
| `rate_limit` | `int \| None` | `None` |
| `expires_at` | `datetime \| None` | `None` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `last_used_at` | `datetime \| None` | `None` |
| `status` | `CredentialStatus` | `CredentialStatus.ACTIVE` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_expired` | `def is_expired(self)` | Check if key has expired. |
| `touch` | `def touch(self)` | Update last_used_at timestamp. |
| `generate_key` | `def generate_key(env: Literal['test', 'live']='live')` | Generate new API key. |
| `hash_key` | `def hash_key(key: str)` | Hash API key with HMAC-SHA256 (OWASP recommended). |
| `verify_key` | `def verify_key(key: str, stored_hash: str)` | Verify API key against stored hash using constant-time comparison. |
| `to_dict` | `def to_dict(self)` | Serialize to dict. |

### `OAuthClient`

- Source: `aquilia/auth/core.py`
- Bases: `object`
- Summary: OAuth2/OIDC client.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `client_id` | `str` | `` |
| `client_secret_hash` | `str \| None` | `` |
| `name` | `str` | `` |
| `grant_types` | `list[Literal['authorization_code', 'client_credentials', 'refresh_token', 'device_code']]` | `` |
| `redirect_uris` | `list[str]` | `` |
| `scopes` | `list[str]` | `` |
| `require_pkce` | `bool` | `True` |
| `require_consent` | `bool` | `True` |
| `token_endpoint_auth_method` | `Literal['client_secret_basic', 'client_secret_post', 'none']` | `'client_secret_post'` |
| `access_token_ttl` | `int` | `3600` |
| `refresh_token_ttl` | `int` | `2592000` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `status` | `CredentialStatus` | `CredentialStatus.ACTIVE` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_public_client` | `def is_public_client(self)` | Check if client is public (no secret). |
| `supports_grant_type` | `def supports_grant_type(self, grant_type: str)` | Check if client supports grant type. |
| `is_redirect_uri_valid` | `def is_redirect_uri_valid(self, redirect_uri: str)` | Check if redirect URI is allowed. |
| `generate_client_id` | `def generate_client_id(prefix: str='app')` | Generate client ID. |
| `generate_client_secret` | `def generate_client_secret()` | Generate client secret. |
| `hash_client_secret` | `def hash_client_secret(secret: str)` | Hash client secret with HMAC-SHA256 (OWASP recommended). |
| `verify_client_secret` | `def verify_client_secret(secret: str, stored_hash: str)` | Verify client secret against stored hash using constant-time comparison. |
| `to_dict` | `def to_dict(self)` | Serialize to dict. |

### `MFACredential`

- Source: `aquilia/auth/core.py`
- Bases: `object`
- Summary: Multi-factor authentication credential.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `identity_id` | `str` | `` |
| `mfa_type` | `Literal['totp', 'webauthn', 'sms', 'email']` | `` |
| `mfa_secret` | `str \| None` | `None` |
| `backup_codes` | `list[str]` | `field(default_factory=list)` |
| `webauthn_credentials` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `phone_number` | `str \| None` | `None` |
| `email` | `str \| None` | `None` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `verified_at` | `datetime \| None` | `None` |
| `last_used_at` | `datetime \| None` | `None` |
| `status` | `CredentialStatus` | `CredentialStatus.ACTIVE` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_verified` | `def is_verified(self)` | Check if MFA is verified. |
| `touch` | `def touch(self)` | Update last_used_at timestamp. |
| `generate_totp_secret` | `def generate_totp_secret()` | Generate TOTP secret (base32). |
| `generate_backup_codes` | `def generate_backup_codes(count: int=10)` | Generate backup codes (8-character alphanumeric). |
| `to_dict` | `def to_dict(self)` | Serialize to dict. |

### `TokenClaims`

- Source: `aquilia/auth/core.py`
- Bases: `object`
- Summary: Access token claims (JWT payload).
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `iss` | `str` | `` |
| `sub` | `str` | `` |
| `aud` | `list[str]` | `` |
| `exp` | `int` | `` |
| `iat` | `int` | `` |
| `nbf` | `int` | `` |
| `jti` | `str` | `` |
| `scopes` | `list[str]` | `` |
| `sid` | `str \| None` | `None` |
| `roles` | `list[str]` | `field(default_factory=list)` |
| `tenant_id` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_expired` | `def is_expired(self)` | Check if token has expired. |
| `has_scope` | `def has_scope(self, scope: str)` | Check if token has scope. |
| `to_dict` | `def to_dict(self)` | Serialize to dict (JWT payload). |
| `from_dict` | `def from_dict(cls, data: dict[str, Any])` | Deserialize from dict (JWT payload). |

### `AuthResult`

- Source: `aquilia/auth/core.py`
- Bases: `object`
- Summary: Result of authentication operation.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `identity` | `Identity` | `` |
| `access_token` | `str \| None` | `None` |
| `refresh_token` | `str \| None` | `None` |
| `session_id` | `str \| None` | `None` |
| `expires_in` | `int \| None` | `None` |
| `token_type` | `str` | `'Bearer'` |
| `scopes` | `list[str]` | `field(default_factory=list)` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize to dict (token response). |

### `IdentityStore`

- Source: `aquilia/auth/core.py`
- Bases: `Protocol`
- Summary: Protocol for identity storage.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `create` | `async def create(self, identity: Identity)` | Create new identity. |
| `get` | `async def get(self, identity_id: str)` | Get identity by ID. |
| `get_by_attribute` | `async def get_by_attribute(self, key: str, value: Any)` | Get identity by attribute (e.g., email). |
| `update` | `async def update(self, identity: Identity)` | Update identity. |
| `delete` | `async def delete(self, identity_id: str)` | Delete identity (soft delete). |
| `list_by_tenant` | `async def list_by_tenant(self, tenant_id: str)` | List identities by tenant. |

### `CredentialStore`

- Source: `aquilia/auth/core.py`
- Bases: `Protocol`
- Summary: Protocol for credential storage.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `create_password` | `async def create_password(self, credential: PasswordCredential)` | Create password credential. |
| `get_password` | `async def get_password(self, identity_id: str)` | Get password credential. |
| `update_password` | `async def update_password(self, credential: PasswordCredential)` | Update password credential. |
| `create_api_key` | `async def create_api_key(self, credential: ApiKeyCredential)` | Create API key credential. |
| `get_api_key` | `async def get_api_key(self, key_id: str)` | Get API key by ID. |
| `get_api_key_by_hash` | `async def get_api_key_by_hash(self, key_hash: str)` | Get API key by hash. |
| `list_api_keys` | `async def list_api_keys(self, identity_id: str)` | List API keys for identity. |
| `revoke_api_key` | `async def revoke_api_key(self, key_id: str)` | Revoke API key. |
| `create_mfa` | `async def create_mfa(self, credential: MFACredential)` | Create MFA credential. |
| `get_mfa` | `async def get_mfa(self, identity_id: str)` | Get MFA credentials for identity. |
| `update_mfa` | `async def update_mfa(self, credential: MFACredential)` | Update MFA credential. |

### `OAuthClientStore`

- Source: `aquilia/auth/core.py`
- Bases: `Protocol`
- Summary: Protocol for OAuth client storage.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `create` | `async def create(self, client: OAuthClient)` | Create OAuth client. |
| `get` | `async def get(self, client_id: str)` | Get client by ID. |
| `update` | `async def update(self, client: OAuthClient)` | Update client. |
| `delete` | `async def delete(self, client_id: str)` | Delete client. |
| `list_all` | `async def list_all(self)` | List all clients. |

### `SurpArtifact`

- Source: `aquilia/auth/surp.py`
- Bases: `object`
- Summary: Base surp artifact.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `artifact_type` | `str` | `` |
| `artifact_id` | `str` | `` |
| `version` | `int` | `` |
| `created_at` | `datetime` | `` |
| `created_by` | `str` | `` |
| `signature` | `str \| None` | `None` |
| `metadata` | `dict[str, Any] \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary. |
| `compute_hash` | `def compute_hash(self)` | Compute SHA256 hash of artifact (for signing). |

### `KeyArtifact`

- Source: `aquilia/auth/surp.py`
- Bases: `SurpArtifact`
- Summary: Cryptographic key artifact.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `key_descriptor` | `KeyDescriptor` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `PolicyArtifact`

- Source: `aquilia/auth/surp.py`
- Bases: `SurpArtifact`
- Summary: Authorization policy artifact.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `policy_id` | `str` | `` |
| `policy_data` | `dict[str, Any]` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `AuditEventArtifact`

- Source: `aquilia/auth/surp.py`
- Bases: `SurpArtifact`
- Summary: Audit event artifact.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `event_type` | `str` | `` |
| `identity_id` | `str \| None` | `` |
| `resource` | `str \| None` | `` |
| `action` | `str \| None` | `` |
| `result` | `str` | `` |
| `details` | `dict[str, Any]` | `` |

### `ArtifactSigner`

- Source: `aquilia/auth/surp.py`
- Bases: `object`
- Summary: Signs and verifies surp artifacts.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sign_artifact` | `def sign_artifact(self, artifact: SurpArtifact)` | Sign artifact. |
| `verify_artifact` | `def verify_artifact(self, artifact: SurpArtifact, signature: str)` | Verify artifact signature. |

### `MemoryArtifactStore`

- Source: `aquilia/auth/surp.py`
- Bases: `object`
- Summary: In-memory artifact store for development/testing.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `save_artifact` | `async def save_artifact(self, artifact: SurpArtifact)` | Save artifact. |
| `get_artifact` | `async def get_artifact(self, artifact_id: str)` | Get artifact by ID. |
| `list_artifacts` | `async def list_artifacts(self, artifact_type: str \| None=None)` | List artifacts by type. |

### `AuditLogger`

- Source: `aquilia/auth/surp.py`
- Bases: `object`
- Summary: Audit event logger with surp artifact integration.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `log_event` | `async def log_event(self, event_type: str, result: str, identity_id: str \| None=None, resource: str \| None=None, action: str \| None=None, details: dict[str, Any] \| None=None)` | Log audit event. |
| `query_events` | `async def query_events(self, event_type: str \| None=None, identity_id: str \| None=None, start_time: datetime \| None=None, end_time: datetime \| None=None)` | Query audit events. |

### `AuthorizationRequiredFault`

- Source: `aquilia/auth/decorators.py`
- Bases: `Fault`
- Summary: Raised when authorization check fails.

### `AuthGuard`

- Source: `aquilia/auth/decorators.py`
- Bases: `object`
- Summary: Base class for authentication/authorization guards.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `check` | `async def check(self, identity: Identity \| None, session: Session \| None)` | Check if access should be granted. |

### `AdminGuard`

- Source: `aquilia/auth/decorators.py`
- Bases: `AuthGuard`
- Summary: Guard that requires admin role.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `check` | `async def check(self, identity: Identity \| Session \| None=None, session: Session \| None=None)` |  |

### `VerifiedEmailGuard`

- Source: `aquilia/auth/decorators.py`
- Bases: `AuthGuard`
- Summary: Guard that requires verified email.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `check` | `async def check(self, identity: Identity \| Session \| None=None, session: Session \| None=None)` |  |

### `RoleGuard`

- Source: `aquilia/auth/decorators.py`
- Bases: `AuthGuard`
- Summary: Guard that requires specific role(s).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `check` | `async def check(self, identity: Identity \| None, session: Session \| None)` |  |

### `ScopeGuard`

- Source: `aquilia/auth/decorators.py`
- Bases: `AuthGuard`
- Summary: Guard that requires specific scope(s).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `check` | `async def check(self, identity: Identity \| None, session: Session \| None)` |  |

### `AUTH_INVALID_CREDENTIALS`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Invalid username or password.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_001'` |
| `message` | `` | `'Invalid credentials'` |
| `public_message` | `` | `'Invalid username or password'` |
| `retryable` | `` | `False` |

### `AUTH_TOKEN_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Invalid or malformed token.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_002'` |
| `message` | `` | `'Invalid token'` |
| `public_message` | `` | `'Invalid authentication token'` |
| `retryable` | `` | `False` |

### `AUTH_TOKEN_EXPIRED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Access token has expired.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_003'` |
| `message` | `` | `'Token expired'` |
| `public_message` | `` | `'Your session has expired. Please log in again.'` |
| `retryable` | `` | `False` |

### `AUTH_TOKEN_REVOKED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Token has been revoked.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_004'` |
| `message` | `` | `'Token revoked'` |
| `public_message` | `` | `'This token has been revoked'` |
| `retryable` | `` | `False` |

### `AUTH_MFA_REQUIRED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Multi-factor authentication required.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_005'` |
| `message` | `` | `'MFA required'` |
| `public_message` | `` | `'Please enter your MFA code'` |
| `retryable` | `` | `True` |

### `AUTH_MFA_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Invalid MFA code.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_006'` |
| `message` | `` | `'Invalid MFA code'` |
| `public_message` | `` | `'Invalid MFA code'` |
| `retryable` | `` | `True` |

### `AUTH_ACCOUNT_SUSPENDED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Account is suspended.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_007'` |
| `message` | `` | `'Account suspended'` |
| `public_message` | `` | `'Your account has been suspended. Please contact support.'` |
| `retryable` | `` | `False` |

### `AUTH_ACCOUNT_LOCKED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Account is locked due to failed login attempts.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_008'` |
| `message` | `` | `'Account locked'` |
| `public_message` | `` | `'Account locked due to multiple failed login attempts'` |
| `retryable` | `` | `True` |
| `retry_after` | `` | `900` |

### `AUTH_RATE_LIMITED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Too many authentication attempts.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_009'` |
| `message` | `` | `'Rate limit exceeded'` |
| `public_message` | `` | `'Too many attempts. Please try again later.'` |
| `retryable` | `` | `True` |
| `retry_after` | `` | `900` |

### `AUTH_REQUIRED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Authentication required but not provided.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_010'` |
| `message` | `` | `'Authentication required'` |
| `public_message` | `` | `'Please log in to access this resource'` |
| `retryable` | `` | `False` |

### `AUTH_CLIENT_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Invalid OAuth client credentials.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_011'` |
| `message` | `` | `'Invalid client'` |
| `public_message` | `` | `'Invalid client credentials'` |
| `retryable` | `` | `False` |

### `AUTH_GRANT_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Invalid OAuth grant (code, refresh token, etc.).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_012'` |
| `message` | `` | `'Invalid grant'` |
| `public_message` | `` | `'Invalid or expired authorization code'` |
| `retryable` | `` | `False` |

### `AUTH_REDIRECT_URI_MISMATCH`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: OAuth redirect URI doesn't match registered URI.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_013'` |
| `message` | `` | `'Redirect URI mismatch'` |
| `public_message` | `` | `'Invalid redirect URI'` |
| `retryable` | `` | `False` |

### `AUTH_SCOPE_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Requested scope is invalid or not allowed.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_014'` |
| `message` | `` | `'Invalid scope'` |
| `public_message` | `` | `'Requested scope is not available'` |
| `retryable` | `` | `False` |

### `AUTH_PKCE_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: PKCE code verifier doesn't match challenge.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_015'` |
| `message` | `` | `'PKCE verification failed'` |
| `public_message` | `` | `'Authorization failed'` |
| `retryable` | `` | `False` |

### `AUTHZ_POLICY_DENIED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Authorization policy denied access.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTHZ_001'` |
| `message` | `` | `'Access denied by policy'` |
| `public_message` | `` | `'You do not have permission to perform this action'` |
| `retryable` | `` | `False` |

### `AUTHZ_INSUFFICIENT_SCOPE`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Token missing required scopes.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTHZ_002'` |
| `message` | `` | `'Insufficient scope'` |
| `public_message` | `` | `'Insufficient permissions'` |
| `retryable` | `` | `False` |

### `AUTHZ_INSUFFICIENT_ROLE`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Identity missing required role.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTHZ_003'` |
| `message` | `` | `'Insufficient role'` |
| `public_message` | `` | `'Insufficient permissions'` |
| `retryable` | `` | `False` |

### `AUTHZ_RESOURCE_FORBIDDEN`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Access to resource is forbidden.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTHZ_004'` |
| `message` | `` | `'Resource forbidden'` |
| `public_message` | `` | `'Access to this resource is forbidden'` |
| `retryable` | `` | `False` |

### `AUTHZ_TENANT_MISMATCH`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Identity tenant doesn't match resource tenant.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTHZ_005'` |
| `message` | `` | `'Tenant mismatch'` |
| `public_message` | `` | `'Access denied'` |
| `retryable` | `` | `False` |

### `AUTH_PASSWORD_WEAK`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Password doesn't meet policy requirements.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_101'` |
| `message` | `` | `'Weak password'` |
| `public_message` | `` | `"Password doesn't meet security requirements"` |
| `retryable` | `` | `True` |

### `AUTH_PASSWORD_BREACHED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Password found in breach database.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_102'` |
| `message` | `` | `'Breached password'` |
| `public_message` | `` | `'This password has been found in data breaches. Please choose a different password.'` |
| `retryable` | `` | `True` |

### `AUTH_PASSWORD_REUSED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Password was recently used.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_103'` |
| `message` | `` | `'Password reused'` |
| `public_message` | `` | `'This password was recently used. Please choose a different password.'` |
| `retryable` | `` | `True` |

### `AUTH_KEY_EXPIRED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: API key has expired.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_104'` |
| `message` | `` | `'API key expired'` |
| `public_message` | `` | `'API key has expired'` |
| `retryable` | `` | `False` |

### `AUTH_KEY_REVOKED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: API key has been revoked.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_105'` |
| `message` | `` | `'API key revoked'` |
| `public_message` | `` | `'API key has been revoked'` |
| `retryable` | `` | `False` |

### `AUTH_SESSION_REQUIRED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Session required but not found.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_201'` |
| `message` | `` | `'Session required'` |
| `public_message` | `` | `'Please log in'` |
| `retryable` | `` | `False` |

### `AUTH_SESSION_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Session is invalid or corrupted.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_202'` |
| `message` | `` | `'Invalid session'` |
| `public_message` | `` | `'Your session is invalid. Please log in again.'` |
| `retryable` | `` | `False` |

### `AUTH_SESSION_HIJACK_DETECTED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Potential session hijacking detected.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_203'` |
| `message` | `` | `'Session hijack detected'` |
| `public_message` | `` | `'Security issue detected. Please log in again.'` |
| `retryable` | `` | `False` |

### `AUTH_CONSENT_REQUIRED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: User consent required for OAuth flow.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_301'` |
| `message` | `` | `'Consent required'` |
| `public_message` | `` | `'Please authorize this application'` |
| `retryable` | `` | `True` |

### `AUTH_DEVICE_CODE_PENDING`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Device code authorization pending.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_302'` |
| `message` | `` | `'Authorization pending'` |
| `public_message` | `` | `'Waiting for user authorization'` |
| `retryable` | `` | `True` |

### `AUTH_DEVICE_CODE_EXPIRED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Device code has expired.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_303'` |
| `message` | `` | `'Device code expired'` |
| `public_message` | `` | `'Authorization code expired. Please try again.'` |
| `retryable` | `` | `False` |

### `AUTH_SLOW_DOWN`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Device flow polling too fast.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_304'` |
| `message` | `` | `'Slow down'` |
| `public_message` | `` | `'Polling too frequently'` |
| `retryable` | `` | `True` |
| `retry_after` | `` | `5` |

### `AUTH_MFA_NOT_ENROLLED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: MFA not enrolled for user.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_401'` |
| `message` | `` | `'MFA not enrolled'` |
| `public_message` | `` | `'Multi-factor authentication is not set up'` |
| `retryable` | `` | `True` |

### `AUTH_MFA_ALREADY_ENROLLED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: MFA already enrolled.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_402'` |
| `message` | `` | `'MFA already enrolled'` |
| `public_message` | `` | `'Multi-factor authentication is already set up'` |
| `retryable` | `` | `False` |

### `AUTH_WEBAUTHN_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: WebAuthn credential invalid.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_403'` |
| `message` | `` | `'WebAuthn invalid'` |
| `public_message` | `` | `'Security key verification failed'` |
| `retryable` | `` | `True` |

### `AUTH_BACKUP_CODE_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Invalid backup code.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_404'` |
| `message` | `` | `'Invalid backup code'` |
| `public_message` | `` | `'Invalid backup code'` |
| `retryable` | `` | `True` |

### `AUTH_BACKUP_CODE_EXHAUSTED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: All backup codes used.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'AUTH_405'` |
| `message` | `` | `'Backup codes exhausted'` |
| `public_message` | `` | `'All backup codes have been used. Please generate new codes.'` |
| `retryable` | `` | `False` |

### `Guard`

- Source: `aquilia/auth/guards.py`
- Bases: `object`
- Summary: Base guard for authentication/authorization.

### `AuthGuard`

- Source: `aquilia/auth/guards.py`
- Bases: `Guard`
- Summary: Authentication guard - requires valid authentication.

### `ApiKeyGuard`

- Source: `aquilia/auth/guards.py`
- Bases: `Guard`
- Summary: API key authentication guard.

### `AuthzGuard`

- Source: `aquilia/auth/guards.py`
- Bases: `Guard`
- Summary: Authorization guard - enforces access control.

### `ScopeGuard`

- Source: `aquilia/auth/guards.py`
- Bases: `Guard`
- Summary: Scope-only guard - quick scope check.

### `RoleGuard`

- Source: `aquilia/auth/guards.py`
- Bases: `Guard`
- Summary: Role-only guard - quick role check.

### `CSRFProtection`

- Source: `aquilia/auth/hardening.py`
- Bases: `object`
- Summary: CSRF token generation and validation.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `generate_token` | `def generate_token(self)` | Generate a new CSRF token. |
| `validate_token` | `def validate_token(self, token: str)` | Validate a CSRF token. |
| `requires_validation` | `def requires_validation(self, method: str)` | Check if the HTTP method requires CSRF validation. |

### `RequestFingerprint`

- Source: `aquilia/auth/hardening.py`
- Bases: `object`
- Summary: Fingerprint a request for session binding.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `ip_hash` | `str` | `` |
| `ua_hash` | `str` | `` |
| `accept_hash` | `str` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_request` | `def from_request(cls, request: Any)` | Create fingerprint from a request object. |
| `matches` | `def matches(self, other: RequestFingerprint, strict: bool=False)` | Check if another fingerprint matches this one. |
| `to_string` | `def to_string(self)` | Serialize to storable string. |
| `from_string` | `def from_string(cls, s: str)` | Deserialize from string. |

### `SecurityHeaders`

- Source: `aquilia/auth/hardening.py`
- Bases: `object`
- Summary: Configurable security headers for HTTP responses.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `content_security_policy` | `str` | `"default-src 'self'"` |
| `strict_transport_security` | `str` | `'max-age=31536000; includeSubDomains'` |
| `x_content_type_options` | `str` | `'nosniff'` |
| `x_frame_options` | `str` | `'DENY'` |
| `referrer_policy` | `str` | `'strict-origin-when-cross-origin'` |
| `permissions_policy` | `str` | `'geolocation=(), camera=(), microphone=()'` |
| `cross_origin_opener_policy` | `str` | `'same-origin'` |
| `cross_origin_embedder_policy` | `str` | `'require-corp'` |
| `cross_origin_resource_policy` | `str` | `'same-origin'` |
| `cache_control` | `str` | `'no-store, no-cache, must-revalidate'` |
| `pragma` | `str` | `'no-cache'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `apply` | `def apply(self, response: Any)` | Apply security headers to a response object. |
| `to_dict` | `def to_dict(self)` | Return headers as a dictionary. |

### `TokenBinder`

- Source: `aquilia/auth/hardening.py`
- Bases: `object`
- Summary: Binds tokens to client characteristics for proof-of-possession.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `create_binding` | `def create_binding(self, token: str, fingerprint: RequestFingerprint)` | Create a binding hash for a token + fingerprint combination. |
| `verify_binding` | `def verify_binding(self, token: str, fingerprint: RequestFingerprint, expected_binding: str)` | Verify that a token is being used from the expected client. |

### `HasherConfig`

- Source: `aquilia/auth/hashing.py`
- Bases: `object`
- Summary: Algorithm-agnostic configuration for :class:`PasswordHasher`.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `algorithm` | `str` | `'argon2id'` |
| `time_cost` | `int` | `2` |
| `memory_cost` | `int` | `65536` |
| `parallelism` | `int` | `4` |
| `hash_len` | `int` | `32` |
| `salt_len` | `int` | `16` |
| `scrypt_n` | `int` | `32768` |
| `scrypt_r` | `int` | `8` |
| `scrypt_p` | `int` | `1` |
| `scrypt_dklen` | `int` | `32` |
| `bcrypt_rounds` | `int` | `12` |
| `pbkdf2_iterations` | `int` | `600000` |
| `pbkdf2_sha512_iterations` | `int` | `210000` |
| `pbkdf2_dklen` | `int` | `32` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_dict` | `def from_dict(cls, data: dict[str, Any])` | Build from a plain dict (e.g. serialised from ``pyconfig``). |
| `to_dict` | `def to_dict(self)` |  |

### `PasswordHasher`

- Source: `aquilia/auth/hashing.py`
- Bases: `object`
- Summary: Multi-algorithm password hasher with automatic algorithm detection.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_config` | `def from_config(cls, config: HasherConfig)` | Build a PasswordHasher from a :class:`HasherConfig`. |
| `hash` | `def hash(self, password: str)` | Hash *password* with the configured algorithm (PHC format output). |
| `verify` | `def verify(self, password_hash: str, password: str)` | Verify *password* against *password_hash* (auto-detects algorithm). |
| `hash_async` | `async def hash_async(self, password: str)` | Hash password without blocking the event loop. |
| `verify_async` | `async def verify_async(self, password_hash: str, password: str)` | Verify password without blocking the event loop. |
| `check_needs_rehash` | `def check_needs_rehash(self, password_hash: str)` | Check if *password_hash* should be regenerated with current params. |

### `PasswordPolicy`

- Source: `aquilia/auth/hashing.py`
- Bases: `object`
- Summary: Password policy validator.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_dict` | `def from_dict(cls, data: dict[str, Any])` | Build a PasswordPolicy from a plain configuration dictionary. |
| `to_dict` | `def to_dict(self)` | Serialize policy settings (excluding blacklist internals). |
| `validate` | `def validate(self, password: str)` | Validate password against policy. Returns (is_valid, errors). |
| `validate_async` | `async def validate_async(self, password: str)` | Async password validation (non-blocking breach check). |

### `AuthPrincipal`

- Source: `aquilia/auth/integration/aquila_sessions.py`
- Bases: `SessionPrincipal`
- Summary: Authentication principal for Aquilia Sessions.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_identity` | `def from_identity(cls, identity: Identity)` | Create AuthPrincipal from Identity. |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any])` | Deserialize from dictionary. |

### `SessionAuthBridge`

- Source: `aquilia/auth/integration/aquila_sessions.py`
- Bases: `object`
- Summary: Bridge between AuthManager and SessionEngine.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `create_auth_session` | `async def create_auth_session(self, identity: Identity, request: Any, token_claims: TokenClaims \| None=None)` | Create authenticated session. |
| `rotate_on_privilege_escalation` | `async def rotate_on_privilege_escalation(self, session: Session, response: Any)` | Rotate session ID after privilege escalation (e.g., MFA). |
| `verify_and_extend` | `async def verify_and_extend(self, session: Session)` | Verify session is valid and extend if needed. |
| `logout` | `async def logout(self, session: Session, response: Any)` | Logout - destroy session. |
| `logout_all_devices` | `async def logout_all_devices(self, identity_id: str)` | Logout from all devices - destroy all sessions for identity. |

### `PasswordHasherProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for PasswordHasher.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide PasswordHasher instance. |

### `PasswordPolicyProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for PasswordPolicy.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide PasswordPolicy instance. |

### `KeyRingProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for KeyRing.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide KeyRing with default keys. |

### `TokenManagerProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for TokenManager.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide TokenManager instance. |

### `RateLimiterProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for RateLimiter.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self, max_attempts: int=5, window_seconds: int=900, lockout_duration: int=3600)` | Provide RateLimiter instance. |

### `IdentityStoreProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for IdentityStore.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide memory-based identity store. |

### `CredentialStoreProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for CredentialStore.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide memory-based credential store. |

### `TokenStoreProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for TokenStore.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide memory-based token store. |

### `OAuthClientStoreProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for OAuthClientStore.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide memory-based OAuth client store. |

### `AuthorizationCodeStoreProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for AuthorizationCodeStore.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide memory-based authorization code store. |

### `DeviceCodeStoreProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for DeviceCodeStore.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide memory-based device code store. |

### `AuthManagerProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for AuthManager.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide AuthManager instance. |

### `MFAManagerProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for MFAManager.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide MFAManager instance. |

### `OAuth2ManagerProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for OAuth2Manager.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide OAuth2Manager instance. |

### `AuthzEngineProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for AuthzEngine.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide AuthzEngine instance. |

### `SessionEngineProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for SessionEngine.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self, policy: SessionPolicy \| None=None, logger: logging.Logger \| None=None)` | Provide SessionEngine instance. |

### `SessionAuthBridgeProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Provider for SessionAuthBridge.
- Decorators: `service(scope='app')`

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `provide` | `def provide(self)` | Provide SessionAuthBridge instance. |

### `AuthConfig`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Authentication configuration builder.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `rate_limit` | `def rate_limit(self, max_attempts: int=5, window_seconds: int=900, lockout_duration: int=3600)` | Configure rate limiting. |
| `sessions` | `def sessions(self, policy: str='user', ttl_days: int=7, idle_timeout_hours: int=1, max_sessions: int=5)` | Configure session management. |
| `tokens` | `def tokens(self, access_ttl_minutes: int=15, refresh_ttl_days: int=30)` | Configure token lifetimes. |
| `mfa` | `def mfa(self, enabled: bool=True, required: bool=False)` | Configure MFA. |
| `oauth` | `def oauth(self, enabled: bool=True)` | Enable OAuth2/OIDC. |
| `build` | `def build(self)` | Build configuration dict. |

### `FlowGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `object`
- Summary: Base class for Flow guards.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `as_flow_node` | `def as_flow_node(self, name: str \| None=None, priority: int=50)` | Convert guard to FlowNode. |

### `RequireAuthGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require valid authentication.

### `RequireSessionAuthGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require authentication via session.

### `RequireTokenAuthGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require authentication via Bearer token.

### `RequireApiKeyGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require authentication via API key.

### `RequireScopesGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require specific OAuth scopes.

### `RequireRolesGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require specific roles.

### `RequirePermissionGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require specific permission.

### `RequirePolicyGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require custom authorization policy.

### `ControllerGuardAdapter`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `object`
- Summary: Adapts a FlowGuard to work in the Controller pipeline.

### `AquilAuthMiddleware`

- Source: `aquilia/auth/integration/middleware.py`
- Bases: `object`
- Summary: Unified middleware for Auth + Sessions + DI integration.

### `OptionalAuthMiddleware`

- Source: `aquilia/auth/integration/middleware.py`
- Bases: `AquilAuthMiddleware`
- Summary: Auth middleware that doesn't require authentication.

### `SessionMiddleware`

- Source: `aquilia/auth/integration/middleware.py`
- Bases: `object`
- Summary: Session-only middleware without authentication.

### `FaultHandlerMiddleware`

- Source: `aquilia/auth/integration/middleware.py`
- Bases: `object`
- Summary: Middleware for handling faults with FaultEngine.

### `EnhancedRequestScopeMiddleware`

- Source: `aquilia/auth/integration/middleware.py`
- Bases: `object`
- Summary: Enhanced request scope middleware with better integration.

### `AuthRuntimeContext`

- Source: `aquilia/auth/integration/runtime_context.py`
- Bases: `object`
- Summary: Request-scoped auth runtime state.
- Decorators: `dataclass(slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `request` | `Any` | `` |
| `session` | `Any \| None` | `None` |
| `identity` | `Any \| None` | `None` |
| `auth` | `Any \| None` | `None` |
| `response` | `Any \| None` | `None` |
| `container` | `Any \| None` | `None` |

### `AuthSession`

- Source: `aquilia/auth/integration/sessions.py`
- Bases: `object`
- Summary: Authentication session.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_expired` | `def is_expired(self)` | Check if session is expired. |
| `update_activity` | `def update_activity(self)` | Update last activity timestamp. |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any])` | Deserialize from dictionary. |

### `MemorySessionStore`

- Source: `aquilia/auth/integration/sessions.py`
- Bases: `object`
- Summary: In-memory session store for development/testing.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `create_session` | `async def create_session(self, identity_id: str, ttl_seconds: int=3600, metadata: dict[str, Any] \| None=None)` | Create new session. |
| `get_session` | `async def get_session(self, session_id: str)` | Get session by ID. |
| `update_session` | `async def update_session(self, session: AuthSession)` | Update session. |
| `delete_session` | `async def delete_session(self, session_id: str)` | Delete session. |
| `list_sessions` | `async def list_sessions(self, identity_id: str)` | List all active sessions for identity. |
| `delete_all_sessions` | `async def delete_all_sessions(self, identity_id: str)` | Delete all sessions for identity. |

### `SessionManager`

- Source: `aquilia/auth/integration/sessions.py`
- Bases: `object`
- Summary: Session manager for authentication.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `create_session` | `async def create_session(self, identity: Identity, metadata: dict[str, Any] \| None=None)` | Create new session for identity. |
| `get_session` | `async def get_session(self, session_id: str)` | Get session and update activity. |
| `extend_session` | `async def extend_session(self, session_id: str, additional_seconds: int=3600)` | Extend session expiration. |
| `rotate_session` | `async def rotate_session(self, old_session_id: str)` | Rotate session ID (privilege escalation). |
| `delete_session` | `async def delete_session(self, session_id: str)` | Delete session (logout). |
| `delete_all_sessions` | `async def delete_all_sessions(self, identity_id: str)` | Delete all sessions for identity (logout all devices). |

### `AuthSessionMiddleware`

- Source: `aquilia/auth/integration/sessions.py`
- Bases: `object`
- Summary: Middleware for session-based authentication.

### `RateLimiter`

- Source: `aquilia/auth/manager.py`
- Bases: `object`
- Summary: Simple in-memory rate limiter for authentication attempts.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `record_attempt` | `def record_attempt(self, key: str)` | Record failed authentication attempt. |
| `is_locked_out` | `def is_locked_out(self, key: str)` | Check if key is currently locked out. |
| `get_remaining_attempts` | `def get_remaining_attempts(self, key: str)` | Get remaining attempts before lockout. |
| `reset` | `def reset(self, key: str)` | Reset attempts for key (successful auth). |

### `SignInProvisionPolicy`

- Source: `aquilia/auth/manager.py`
- Bases: `object`
- Summary: Provisioning policy for sign_in bootstrap behavior.
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enable_identity_seed` | `bool` | `True` |
| `create_identity_if_missing` | `bool` | `True` |
| `backfill_password_credential` | `bool` | `True` |
| `overwrite_password_credential` | `bool` | `False` |
| `allow_username_bootstrap` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `secure_defaults` | `def secure_defaults(cls, env: str \| None=None)` | Environment-aware secure defaults. |

### `AuthManager`

- Source: `aquilia/auth/manager.py`
- Bases: `object`
- Summary: Central authentication manager.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `current_session` | `def current_session(self)` | Return current runtime session if auth/session middleware is active. |
| `has_active_session` | `def has_active_session(self)` | Check whether a runtime session is currently available. |
| `current_identity_id` | `def current_identity_id(self)` | Return identity_id bound to the current runtime session, if available. |
| `authenticate_password` | `async def authenticate_password(self, username: str, password: str, scopes: SessionScope \| str \| list[SessionScope \| str] \| tuple[SessionScope \| str, ...] \| set[SessionScope \| str] \| None=None, session_id: str \| None=None, client_metadata: dict[str, Any] \| None=None)` | Authenticate using username/password. |
| `sign_in` | `async def sign_in(self, *, username: str, password: str, scopes: SessionScope \| str \| list[SessionScope \| str] \| tuple[SessionScope \| str, ...] \| set[SessionScope \| str] \| None=None, session: Literal['auto', 'new'] \| str='auto', client_metadata: dict[str, Any] \| None=None, identity: Identity \| None=None, password_hash: str \| None=None, provision: SignInProvisionPolicy \| None=None)` | Aquilia-native high-level sign-in API. |
| `authenticate_api_key` | `async def authenticate_api_key(self, api_key: str, required_scopes: SessionScope \| str \| list[SessionScope \| str] \| tuple[SessionScope \| str, ...] \| set[SessionScope \| str] \| None=None)` | Authenticate using API key. |
| `refresh_access_token` | `async def refresh_access_token(self, refresh_token: str)` | Refresh access token using refresh token. |
| `revoke_token` | `async def revoke_token(self, token: str, token_type: str='refresh')` | Revoke a token. |
| `logout` | `async def logout(self, identity_id: str \| None=None, session_id: str \| None=None, access_token: str \| None=None, refresh_token: str \| None=None)` | Logout user by revoking all tokens. |
| `sign_out` | `async def sign_out(self, *, scope: Literal['session', 'identity', 'all']='session', identity_id: str \| None=None, session_id: str \| None=None, access_token: str \| None=None, refresh_token: str \| None=None)` | Aquilia-native sign-out API with explicit scope semantics. |
| `resume_identity` | `async def resume_identity(self, access_token: str \| None=None)` | Resolve the current identity from token or runtime session context. |
| `verify_token` | `async def verify_token(self, access_token: str)` | Verify and decode access token. |
| `get_identity_from_token` | `async def get_identity_from_token(self, access_token: str)` | Extract identity from access token. |

### `TOTPProvider`

- Source: `aquilia/auth/mfa.py`
- Bases: `object`
- Summary: TOTP (Time-based One-Time Password) provider.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `generate_secret` | `def generate_secret(self)` | Generate random TOTP secret. |
| `generate_code` | `def generate_code(self, secret: str, timestamp: int \| None=None)` | Generate TOTP code for given secret and time. |
| `verify_code` | `def verify_code(self, secret: str, code: str, window: int=1, timestamp: int \| None=None)` | Verify TOTP code. |
| `generate_provisioning_uri` | `def generate_provisioning_uri(self, secret: str, account_name: str)` | Generate provisioning URI for QR code. |
| `generate_backup_codes` | `def generate_backup_codes(self, count: int=10)` | Generate backup recovery codes. |
| `hash_backup_code` | `def hash_backup_code(code: str)` | Hash backup code for storage using HMAC-SHA256. |
| `verify_backup_code` | `def verify_backup_code(code: str, code_hash: str)` | Verify backup code against hash. |

### `WebAuthnProvider`

- Source: `aquilia/auth/mfa.py`
- Bases: `object`
- Summary: WebAuthn provider for passwordless authentication.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `generate_challenge` | `def generate_challenge(self)` | Generate cryptographic challenge. |
| `generate_registration_options` | `def generate_registration_options(self, user_id: str, user_name: str, user_display_name: str)` | Generate WebAuthn registration options. |
| `generate_authentication_options` | `def generate_authentication_options(self, credential_ids: list[str] \| None=None)` | Generate WebAuthn authentication options. |
| `verify_registration_response` | `def verify_registration_response(self, response: dict[str, Any], expected_challenge: str)` | Verify WebAuthn registration response. |
| `verify_authentication_response` | `def verify_authentication_response(self, response: dict[str, Any], expected_challenge: str, stored_credential: dict[str, Any])` | Verify WebAuthn authentication response. |

### `MFAManager`

- Source: `aquilia/auth/mfa.py`
- Bases: `object`
- Summary: Central MFA manager coordinating all MFA providers.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `enroll_totp` | `async def enroll_totp(self, user_id: str, account_name: str)` | Enroll user in TOTP MFA. |
| `verify_totp` | `async def verify_totp(self, secret: str, code: str)` | Verify TOTP code. |
| `verify_backup_code` | `async def verify_backup_code(self, code: str, backup_code_hashes: list[str])` | Verify backup code and remove it. |

### `PKCEVerifier`

- Source: `aquilia/auth/oauth.py`
- Bases: `object`
- Summary: PKCE (Proof Key for Code Exchange) utilities.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `generate_code_verifier` | `def generate_code_verifier(length: int=128)` | Generate code verifier for PKCE. |
| `generate_code_challenge` | `def generate_code_challenge(verifier: str, method: str='S256')` | Generate code challenge from verifier. |
| `verify_code_challenge` | `def verify_code_challenge(verifier: str, challenge: str, method: str='S256')` | Verify code verifier against challenge. |

### `OAuth2Manager`

- Source: `aquilia/auth/oauth.py`
- Bases: `object`
- Summary: OAuth 2.0 / OIDC authorization server.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `validate_client` | `async def validate_client(self, client_id: str, client_secret: str \| None=None)` | Validate OAuth client credentials. |
| `authorize` | `async def authorize(self, client_id: str, redirect_uri: str, scope: str, state: str \| None=None, response_type: str='code', code_challenge: str \| None=None, code_challenge_method: str='S256')` | Authorization endpoint - initiate authorization flow. |
| `grant_authorization_code` | `async def grant_authorization_code(self, client_id: str, identity_id: str, redirect_uri: str, scopes: list[str], code_challenge: str \| None=None, code_challenge_method: str='S256')` | Grant authorization code after user consent. |
| `exchange_authorization_code` | `async def exchange_authorization_code(self, code: str, client_id: str, client_secret: str \| None, redirect_uri: str, code_verifier: str \| None=None)` | Token endpoint - exchange authorization code for tokens. |
| `client_credentials_grant` | `async def client_credentials_grant(self, client_id: str, client_secret: str, scope: str \| None=None)` | Client Credentials grant - machine-to-machine auth. |
| `device_authorization` | `async def device_authorization(self, client_id: str, scope: str \| None=None)` | Device Authorization - initiate device flow. |
| `device_token` | `async def device_token(self, device_code: str, client_id: str)` | Device Token - poll for authorization. |

### `PolicyDecision`

- Source: `aquilia/auth/policy/__init__.py`
- Bases: `Enum`
- Summary: Result of a policy evaluation.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `ALLOW` | `` | `'allow'` |
| `DENY` | `` | `'deny'` |
| `ABSTAIN` | `` | `'abstain'` |

### `PolicyResult`

- Source: `aquilia/auth/policy/__init__.py`
- Bases: `object`
- Summary: Result of evaluating a policy rule.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `decision` | `PolicyDecision` | `` |
| `reason` | `str \| None` | `None` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

### `Policy`

- Source: `aquilia/auth/policy/__init__.py`
- Bases: `object`
- Summary: Base class for resource-based authorization policies.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `resource` | `str` | `''` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `evaluate` | `def evaluate(self, action: str, identity: Any, resource: Any=None)` | Evaluate policy for a given action. |
| `get_rules` | `def get_rules(self)` | Get list of defined rule names. |

### `PolicyRegistry`

- Source: `aquilia/auth/policy/__init__.py`
- Bases: `object`
- Summary: Registry for authorization policies.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register` | `def register(self, policy: Policy)` | Register a policy by its resource name. |
| `get` | `def get(self, resource: str)` | Get policy for a resource. |
| `evaluate` | `def evaluate(self, resource: str, action: str, identity: Any, resource_obj: Any=None)` | Evaluate policy for a resource action. |
| `resources` | `def resources(self)` | List all registered resource types. |

### `MemoryIdentityStore`

- Source: `aquilia/auth/stores.py`
- Bases: `object`
- Summary: In-memory identity storage for development/testing.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `create` | `async def create(self, identity: Identity)` | Create new identity. |
| `get` | `async def get(self, identity_id: str)` | Get identity by ID. |
| `get_by_attribute` | `async def get_by_attribute(self, attribute: str, value: Any)` | Get identity by attribute value. |
| `update` | `async def update(self, identity: Identity)` | Update existing identity. |
| `delete` | `async def delete(self, identity_id: str)` | Delete identity (soft delete by setting status). |
| `list_by_tenant` | `async def list_by_tenant(self, tenant_id: str, limit: int=100, offset: int=0)` | List identities by tenant. |

### `MemoryCredentialStore`

- Source: `aquilia/auth/stores.py`
- Bases: `object`
- Summary: In-memory credential storage for development/testing.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `save_password` | `async def save_password(self, credential: PasswordCredential)` | Save password credential (upsert). |
| `create_password` | `async def create_password(self, credential: PasswordCredential)` | Create password credential (`CredentialStore` protocol; delegates to `save_password`). |
| `update_password` | `async def update_password(self, credential: PasswordCredential)` | Update password credential (`CredentialStore` protocol; delegates to `save_password`). |
| `get_password` | `async def get_password(self, identity_id: str)` | Get password credential. |
| `delete_password` | `async def delete_password(self, identity_id: str)` | Delete password credential. |
| `save_api_key` | `async def save_api_key(self, credential: ApiKeyCredential)` | Save API key credential (indexes by both `key_id` and `key_hash`). |
| `create_api_key` | `async def create_api_key(self, credential: ApiKeyCredential)` | Create API key credential (`CredentialStore` protocol; raises `ConflictFault` if `key_id` exists). |
| `get_api_key` | `async def get_api_key(self, key_id: str)` | Get API key credential. |
| `get_api_key_by_hash` | `async def get_api_key_by_hash(self, key_hash: str)` | Get API key by its HMAC hash — O(1) lookup (`CredentialStore` protocol). |
| `get_api_key_by_prefix` | `async def get_api_key_by_prefix(self, prefix: str)` | Get API key by prefix (first 8 chars). Deprecated: prefer `get_api_key_by_hash`. |
| `list_api_keys` | `async def list_api_keys(self, identity_id: str)` | List all API keys for identity. |
| `revoke_api_key` | `async def revoke_api_key(self, key_id: str)` | Soft-revoke API key — sets `status = CredentialStatus.REVOKED` (`CredentialStore` protocol). |
| `delete_api_key` | `async def delete_api_key(self, key_id: str)` | Hard-delete API key credential. |
| `save_mfa` | `async def save_mfa(self, credential: MFACredential)` | Save MFA credential. |
| `create_mfa` | `async def create_mfa(self, credential: MFACredential)` | Create MFA credential (`CredentialStore` protocol; delegates to `save_mfa`). |
| `update_mfa` | `async def update_mfa(self, credential: MFACredential)` | Update MFA credential (`CredentialStore` protocol; delegates to `save_mfa`). |
| `get_mfa` | `async def get_mfa(self, identity_id: str, mfa_type: str \| None=None)` | Get MFA credentials for identity. |
| `delete_mfa` | `async def delete_mfa(self, identity_id: str, mfa_type: str \| None=None)` | Delete MFA credentials. |

`MemoryCredentialStore` now fully satisfies the `CredentialStore` protocol under the
protocol's own method names (`create_password`/`update_password`/`create_api_key`/
`get_api_key_by_hash`/`revoke_api_key`/`create_mfa`/`update_mfa`) — previously only
the ad hoc `save_*`/`get_api_key_by_prefix` names existed, and `AuthManager` was
written against those, not the protocol. Custom `CredentialStore` implementations
should implement the protocol names; the `save_*`/`get_api_key_by_prefix` names
remain for backward compatibility but are not part of the protocol.

### `MemoryOAuthClientStore`

- Source: `aquilia/auth/stores.py`
- Bases: `object`
- Summary: In-memory OAuth client storage for development/testing.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `create` | `async def create(self, client: OAuthClient)` | Create OAuth client. |
| `get` | `async def get(self, client_id: str)` | Get OAuth client by ID. |
| `update` | `async def update(self, client: OAuthClient)` | Update OAuth client. |
| `delete` | `async def delete(self, client_id: str)` | Delete OAuth client. |
| `list` | `async def list(self, owner_id: str \| None=None, limit: int=100, offset: int=0)` | List OAuth clients, optionally filtered by owner (from metadata). |
| `list_all` | `async def list_all(self)` | List all OAuth clients (`OAuthClientStore` protocol; delegates to `list()`). |

### `MemoryTokenStore`

- Source: `aquilia/auth/stores.py`
- Bases: `object`
- Summary: In-memory token storage for development/testing.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `save_refresh_token` | `async def save_refresh_token(self, token_id: str, identity_id: str, scopes: list[str], expires_at: datetime, session_id: str \| None=None, metadata: dict[str, Any] \| None=None)` | Save refresh token. |
| `get_refresh_token` | `async def get_refresh_token(self, token_id: str)` | Get refresh token data. |
| `revoke_refresh_token` | `async def revoke_refresh_token(self, token_id: str)` | Revoke single refresh token. |
| `revoke_tokens_by_identity` | `async def revoke_tokens_by_identity(self, identity_id: str)` | Revoke all tokens for identity. |
| `revoke_tokens_by_session` | `async def revoke_tokens_by_session(self, session_id: str)` | Revoke all tokens for session. |
| `is_token_revoked` | `async def is_token_revoked(self, token_id: str)` | Check if token is revoked. |
| `cleanup_expired` | `async def cleanup_expired(self)` | Remove expired tokens (returns count removed). |

### `RedisTokenStore`

- Source: `aquilia/auth/stores.py`
- Bases: `object`
- Summary: Redis-backed token store with bloom filter for fast revocation checks.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `save_refresh_token` | `async def save_refresh_token(self, token_id: str, identity_id: str, scopes: list[str], expires_at: datetime, session_id: str \| None=None, metadata: dict[str, Any] \| None=None)` | Save refresh token to Redis. |
| `get_refresh_token` | `async def get_refresh_token(self, token_id: str)` | Get refresh token data from Redis. |
| `revoke_refresh_token` | `async def revoke_refresh_token(self, token_id: str)` | Revoke single refresh token. |
| `revoke_tokens_by_identity` | `async def revoke_tokens_by_identity(self, identity_id: str)` | Revoke all tokens for identity. |
| `revoke_tokens_by_session` | `async def revoke_tokens_by_session(self, session_id: str)` | Revoke all tokens for session. |
| `is_token_revoked` | `async def is_token_revoked(self, token_id: str)` | Check if token is revoked (fast check using Redis set). |
| `cleanup_expired` | `async def cleanup_expired(self)` | Redis handles expiration automatically, return 0. |

### `MemoryAuthorizationCodeStore`

- Source: `aquilia/auth/stores.py`
- Bases: `object`
- Summary: In-memory authorization code storage for OAuth2 flows.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `save_code` | `async def save_code(self, code: str, client_id: str, identity_id: str, redirect_uri: str, scopes: list[str], expires_at: datetime, code_challenge: str \| None=None, code_challenge_method: str \| None=None)` | Save authorization code. |
| `get_code` | `async def get_code(self, code: str)` | Get authorization code data. |
| `consume_code` | `async def consume_code(self, code: str)` | Mark code as used (one-time use). |
| `cleanup_expired` | `async def cleanup_expired(self)` | Remove expired codes. |

### `MemoryDeviceCodeStore`

- Source: `aquilia/auth/stores.py`
- Bases: `object`
- Summary: In-memory device code storage for device authorization flow.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `save_device_code` | `async def save_device_code(self, device_code: str, user_code: str, client_id: str, scopes: list[str], expires_at: datetime)` | Save device code. |
| `get_by_device_code` | `async def get_by_device_code(self, device_code: str)` | Get device code data. |
| `get_by_user_code` | `async def get_by_user_code(self, user_code: str)` | Get device code data by user code. |
| `authorize_device_code` | `async def authorize_device_code(self, user_code: str, identity_id: str)` | Authorize device code (user approved). |
| `deny_device_code` | `async def deny_device_code(self, user_code: str)` | Deny device code (user rejected). |

### `KeyAlgorithm`

- Source: `aquilia/auth/tokens.py`
- Bases: `str, Enum`
- Summary: Supported signing algorithms (Enum prevents arbitrary values).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `HS256` | `` | `'HS256'` |
| `HS384` | `` | `'HS384'` |
| `HS512` | `` | `'HS512'` |
| `RS256` | `` | `'RS256'` |
| `ES256` | `` | `'ES256'` |
| `EdDSA` | `` | `'EdDSA'` |

### `KeyStatus`

- Source: `aquilia/auth/tokens.py`
- Bases: `str, Enum`
- Summary: Key status in lifecycle (Enum prevents invalid state transitions).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `ACTIVE` | `` | `'active'` |
| `ROTATING` | `` | `'rotating'` |
| `RETIRED` | `` | `'retired'` |
| `REVOKED` | `` | `'revoked'` |

### `KeyDescriptor`

- Source: `aquilia/auth/tokens.py`
- Bases: `object`
- Summary: Cryptographic key metadata.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `kid` | `str` | `` |
| `algorithm` | `str` | `` |
| `public_key_pem` | `str` | `` |
| `private_key_pem` | `str \| None` | `None` |
| `status` | `str` | `KeyStatus.ACTIVE` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `retire_after` | `datetime \| None` | `None` |
| `revoked_at` | `datetime \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_active` | `def is_active(self)` | Check if key can be used for signing. |
| `can_verify` | `def can_verify(self)` | Check if key can be used for verification. |
| `to_dict` | `def to_dict(self, include_private_key: bool=False)` | Serialize to dict. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any])` | Deserialize from dict. |
| `generate` | `def generate(cls, kid: str, algorithm: str=KeyAlgorithm.HS256, secret: str \| None=None)` | Generate a new key (or wrap an existing secret) for *algorithm*. |

### `KeyRing`

- Source: `aquilia/auth/tokens.py`
- Bases: `object`
- Summary: Key ring for JWT signing and verification.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_signing_key` | `def get_signing_key(self)` | Get current signing key. |
| `get_verification_key` | `def get_verification_key(self, kid: str)` | Get verification key by kid. |
| `add_key` | `def add_key(self, key: KeyDescriptor)` | Add key to ring. |
| `promote_key` | `def promote_key(self, kid: str)` | Promote key to active (retire current). |
| `revoke_key` | `def revoke_key(self, kid: str)` | Revoke key (invalid for all operations). |
| `to_dict` | `def to_dict(self, include_private_keys: bool=True)` | Serialize to dict. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any])` | Deserialize from dict. |
| `from_file` | `def from_file(cls, path: Path)` | Load from JSON file. |
| `to_file` | `def to_file(self, path: Path)` | Save to JSON file. |

### `TokenConfig`

- Source: `aquilia/auth/tokens.py`
- Bases: `object`
- Summary: Token manager configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `issuer` | `str` | `'aquilia'` |
| `audience` | `list[str]` | `field(default_factory=lambda: ['api'])` |
| `access_token_ttl` | `int` | `3600` |
| `refresh_token_ttl` | `int` | `2592000` |

`TokenConfig` does **not** configure the signing algorithm (the previous
`algorithm: str = KeyAlgorithm.RS256` field was dead — never read by
`TokenManager`, and misleadingly implied an RS256 default). The algorithm is a
property of the active `KeyDescriptor` inside the `KeyRing` passed to
`TokenManager(key_ring=..., token_store=...)`. Build it with
`KeyDescriptor.generate(kid=..., algorithm=...)`; it defaults to `HS256`
(stdlib-only, zero extra dependencies) unless an asymmetric algorithm
(`RS256`/`ES256`/`EdDSA`, which require `pip install cryptography`) is
explicitly requested.

### `TokenStore`

- Source: `aquilia/auth/tokens.py`
- Bases: `Protocol`
- Summary: Protocol for token storage (opaque tokens, revocation).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `save_refresh_token` | `async def save_refresh_token(self, token_id: str, identity_id: str, scopes: list[str], expires_at: datetime, session_id: str \| None=None)` | Save refresh token. |
| `get_refresh_token` | `async def get_refresh_token(self, token_id: str)` | Get refresh token data. |
| `revoke_refresh_token` | `async def revoke_refresh_token(self, token_id: str)` | Revoke refresh token. |
| `revoke_tokens_by_identity` | `async def revoke_tokens_by_identity(self, identity_id: str)` | Revoke all tokens for identity. |
| `revoke_tokens_by_session` | `async def revoke_tokens_by_session(self, session_id: str)` | Revoke all tokens for session. |
| `is_token_revoked` | `async def is_token_revoked(self, token_id: str)` | Check if token is revoked. |

### `TokenManager`

- Source: `aquilia/auth/tokens.py`
- Bases: `object`
- Summary: Token lifecycle manager.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `issue_access_token` | `async def issue_access_token(self, identity_id: str, scopes: list[str], roles: list[str] \| None=None, session_id: str \| None=None, tenant_id: str \| None=None, ttl: int \| None=None)` | Issue signed access token. |
| `issue_refresh_token` | `async def issue_refresh_token(self, identity_id: str, scopes: list[str], session_id: str \| None=None)` | Issue opaque refresh token. |
| `validate_access_token` | `async def validate_access_token(self, token: str)` | Validate and decode access token. |
| `validate_refresh_token` | `async def validate_refresh_token(self, token: str)` | Validate refresh token. |
| `refresh_access_token` | `async def refresh_access_token(self, refresh_token: str)` | Exchange refresh token for new access + refresh tokens. |
| `revoke_token` | `async def revoke_token(self, token_id: str)` | Revoke token by ID. |
| `revoke_tokens_by_identity` | `async def revoke_tokens_by_identity(self, identity_id: str)` | Revoke all tokens for identity. |
| `revoke_tokens_by_session` | `async def revoke_tokens_by_session(self, session_id: str)` | Revoke all tokens for session. |
