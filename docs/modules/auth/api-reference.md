# Authentication And Authorization API Reference

This page is extracted from the current Python source. It includes public classes, methods, functions, constants, dataclass-like fields, decorators, and notable attributes.

## Public Class Summary

| Name | Source | Bases | Purpose |
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
| `CrousArtifact` | `aquilia/auth/crous.py` | object | Base crous artifact. |
| `KeyArtifact` | `aquilia/auth/crous.py` | CrousArtifact | Cryptographic key artifact. |
| `PolicyArtifact` | `aquilia/auth/crous.py` | CrousArtifact | Authorization policy artifact. |
| `AuditEventArtifact` | `aquilia/auth/crous.py` | CrousArtifact | Audit event artifact. |
| `ArtifactSigner` | `aquilia/auth/crous.py` | object | Signs and verifies crous artifacts. |
| `MemoryArtifactStore` | `aquilia/auth/crous.py` | object | In-memory artifact store for development/testing. |
| `AuditLogger` | `aquilia/auth/crous.py` | object | Audit event logger with crous artifact integration. |
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

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `is_verified` | `aquilia/auth/clearance.py` | `def is_verified(identity: Any, request: Any, ctx: Any) -> bool` | Condition: identity must have 'verified' attribute or status ACTIVE. |
| `is_owner_or_admin` | `aquilia/auth/clearance.py` | `def is_owner_or_admin(identity: Any, request: Any, ctx: Any) -> bool` | Condition: identity is resource owner or has admin role. |
| `within_quota` | `aquilia/auth/clearance.py` | `def within_quota(identity: Any, request: Any, ctx: Any) -> bool` | Condition: identity hasn't exceeded rate/resource quota. |
| `is_same_tenant` | `aquilia/auth/clearance.py` | `def is_same_tenant(identity: Any, request: Any, ctx: Any) -> bool` | Condition: identity's tenant matches resource tenant. |
| `during_hours` | `aquilia/auth/clearance.py` | `def during_hours(start: int = 9, end: int = 17) -> Callable` | Factory: condition that restricts access to business hours (UTC). |
| `require_attribute` | `aquilia/auth/clearance.py` | `def require_attribute(key: str, value: Any = None) -> Callable` | Factory: condition that requires a specific identity attribute. |
| `ip_allowlist` | `aquilia/auth/clearance.py` | `def ip_allowlist(*cidrs: str) -> Callable` | Factory: condition restricting access to specific IP ranges. |
| `grant` | `aquilia/auth/clearance.py` | `def grant(level: AccessLevel = AccessLevel.AUTHENTICATED, entitlements: Sequence[str] = (), conditions: Sequence[Callable] = (), compartment: str &#124; None = None, deny_message: str = 'Insufficient clearance', audit: bool = True) -> Callable` | Decorator to attach clearance requirements to a route method. |
| `exempt` | `aquilia/auth/clearance.py` | `def exempt(fn: Callable) -> Callable` | Decorator to exempt a route from class-level clearance. |
| `get_method_clearance` | `aquilia/auth/clearance.py` | `def get_method_clearance(method: Any) -> Clearance &#124; None` | Extract clearance from a decorated method. |
| `extract_controller_clearance` | `aquilia/auth/clearance.py` | `def extract_controller_clearance(controller_class: type) -> Clearance &#124; None` | Extract clearance from controller class. |
| `build_merged_clearance` | `aquilia/auth/clearance.py` | `def build_merged_clearance(controller_class: type, handler_method: Any) -> Clearance &#124; None` | Build merged clearance from class + method. |
| `authenticated` | `aquilia/auth/decorators.py` | `def authenticated(func: F &#124; None = None, *, login_url: str &#124; None = None, redirect_if_html: bool = False, include_next: bool = True, next_param: str = 'next', redirect_status: int = 303) -> F &#124; Callable[[F], F]` | Decorator requiring authenticated identity. |
| `require_identity` | `aquilia/auth/decorators.py` | `def require_identity(*, roles: list[str] &#124; None = None, scopes: list[str] &#124; None = None, attributes: dict[str, Any] &#124; None = None, require_all_roles: bool = False, require_all_scopes: bool = True, login_url: str &#124; None = None, redirect_if_html: bool = False, include_next: bool = True, next_param: str = 'next', redirect_status: int = 303) -> Callable[[F], F]` | Decorator requiring identity with specific attributes. |
| `requires` | `aquilia/auth/decorators.py` | `def requires(*guards: AuthGuard) -> Callable[[F], F]` | Decorator to require multiple guards. |
| `raise_auth_fault` | `aquilia/auth/faults.py` | `def raise_auth_fault(fault_class: type[Fault], **kwargs)` | Raise an auth fault with context. |
| `is_auth_fault` | `aquilia/auth/faults.py` | `def is_auth_fault(exception: Exception) -> bool` | Check if exception is an auth fault. |
| `require_auth` | `aquilia/auth/guards.py` | `def require_auth(auth_manager: AuthManager, optional: bool = False) -> Callable` | Decorator: Require authentication. |
| `require_scopes` | `aquilia/auth/guards.py` | `def require_scopes(*scopes: str) -> Callable` | Decorator: Require OAuth scopes. |
| `require_roles` | `aquilia/auth/guards.py` | `def require_roles(*roles: str, require_all: bool = False) -> Callable` | Decorator: Require roles. |
| `constant_time_compare` | `aquilia/auth/hardening.py` | `def constant_time_compare(a: str &#124; bytes, b: str &#124; bytes) -> bool` | Compare two strings/bytes in constant time to prevent timing attacks. |
| `generate_secure_token` | `aquilia/auth/hardening.py` | `def generate_secure_token(length: int = 32) -> str` | Generate a cryptographically secure random token. |
| `generate_opaque_id` | `aquilia/auth/hardening.py` | `def generate_opaque_id(prefix: str = 'aq') -> str` | Generate an opaque identifier with prefix. |
| `hash_token` | `aquilia/auth/hardening.py` | `def hash_token(token: str) -> str` | Hash a token for storage (one-way). |
| `hash_sensitive` | `aquilia/auth/hardening.py` | `def hash_sensitive(value: str, salt: str = '') -> str` | Hash sensitive data with optional salt. |
| `get_password_hasher` | `aquilia/auth/hashing.py` | `def get_password_hasher() -> PasswordHasher` | Get default password hasher instance. |
| `hash_password` | `aquilia/auth/hashing.py` | `def hash_password(password: str) -> str` | Hash password with default hasher. |
| `verify_password` | `aquilia/auth/hashing.py` | `def verify_password(password_hash: str, password: str) -> bool` | Verify password with default hasher. |
| `validate_password` | `aquilia/auth/hashing.py` | `def validate_password(password: str, policy: PasswordPolicy &#124; None = None) -> tuple[bool, list[str]]` | Validate password against policy. |
| `bind_identity` | `aquilia/auth/integration/aquila_sessions.py` | `def bind_identity(session: Session, identity: Identity) -> None` | Bind identity to session. |
| `bind_token_claims` | `aquilia/auth/integration/aquila_sessions.py` | `def bind_token_claims(session: Session, claims: TokenClaims) -> None` | Bind token claims to session. |
| `get_identity_id` | `aquilia/auth/integration/aquila_sessions.py` | `def get_identity_id(session: Session) -> str &#124; None` | Get identity ID from session. |
| `get_tenant_id` | `aquilia/auth/integration/aquila_sessions.py` | `def get_tenant_id(session: Session) -> str &#124; None` | Get tenant ID from session. |
| `get_roles` | `aquilia/auth/integration/aquila_sessions.py` | `def get_roles(session: Session) -> list[str]` | Get roles from session. |
| `get_scopes` | `aquilia/auth/integration/aquila_sessions.py` | `def get_scopes(session: Session) -> list[str]` | Get scopes from session. |
| `is_mfa_verified` | `aquilia/auth/integration/aquila_sessions.py` | `def is_mfa_verified(session: Session) -> bool` | Check if MFA was verified for this session. |
| `set_mfa_verified` | `aquilia/auth/integration/aquila_sessions.py` | `def set_mfa_verified(session: Session) -> None` | Mark session as MFA verified. |
| `user_session_policy` | `aquilia/auth/integration/aquila_sessions.py` | `def user_session_policy(ttl: timedelta = timedelta(days=7), idle_timeout: timedelta = timedelta(hours=1), max_sessions: int &#124; None = 5, store_name: str = 'redis') -> SessionPolicy` | Create policy for user web sessions. |
| `api_session_policy` | `aquilia/auth/integration/aquila_sessions.py` | `def api_session_policy(ttl: timedelta = timedelta(hours=1), max_sessions: int &#124; None = None) -> SessionPolicy` | Create policy for API token sessions. |
| `device_session_policy` | `aquilia/auth/integration/aquila_sessions.py` | `def device_session_policy(ttl: timedelta = timedelta(days=90), idle_timeout: timedelta = timedelta(days=30)) -> SessionPolicy` | Create policy for device (mobile app) sessions. |
| `register_auth_providers` | `aquilia/auth/integration/di_providers.py` | `def register_auth_providers(container: Container, config: dict[str, Any] &#124; None = None) -> None` | Register all auth providers in DI container. |
| `create_auth_container` | `aquilia/auth/integration/di_providers.py` | `def create_auth_container(config: dict[str, Any] &#124; None = None, parent: Container &#124; None = None) -> Container` | Create DI container with all auth providers registered. |
| `get_session` | `aquilia/auth/integration/flow_guards.py` | `def get_session(context: Any) -> Session &#124; None` | Extract session from flow context. |
| `get_identity` | `aquilia/auth/integration/flow_guards.py` | `def get_identity(context: Any) -> Identity &#124; None` | Extract identity from flow context. |
| `set_identity` | `aquilia/auth/integration/flow_guards.py` | `def set_identity(context: Any, identity: Identity &#124; None) -> None` | Set identity in flow context. |
| `controller_require_auth` | `aquilia/auth/integration/flow_guards.py` | `def controller_require_auth(optional: bool = False) -> ControllerGuardAdapter` | Create auth guard for Controller pipeline. |
| `controller_require_scopes` | `aquilia/auth/integration/flow_guards.py` | `def controller_require_scopes(*scopes: str, require_all: bool = True) -> ControllerGuardAdapter` | Create scope guard for Controller pipeline. |
| `controller_require_roles` | `aquilia/auth/integration/flow_guards.py` | `def controller_require_roles(*roles: str, require_all: bool = True) -> ControllerGuardAdapter` | Create role guard for Controller pipeline. |
| `controller_require_permission` | `aquilia/auth/integration/flow_guards.py` | `def controller_require_permission(authz_engine: AuthzEngine, permission: str, resource: str &#124; None = None) -> ControllerGuardAdapter` | Create permission guard for Controller pipeline. |
| `require_auth` | `aquilia/auth/integration/flow_guards.py` | `def require_auth(optional: bool = False) -> FlowNode` | Create authentication guard node. |
| `require_scopes` | `aquilia/auth/integration/flow_guards.py` | `def require_scopes(*scopes: str, require_all: bool = True) -> FlowNode` | Create scope guard node. |
| `require_roles` | `aquilia/auth/integration/flow_guards.py` | `def require_roles(*roles: str, require_all: bool = True) -> FlowNode` | Create role guard node. |
| `require_permission` | `aquilia/auth/integration/flow_guards.py` | `def require_permission(authz_engine: AuthzEngine, permission: str, resource: str &#124; None = None) -> FlowNode` | Create permission guard node. |
| `create_auth_middleware_stack` | `aquilia/auth/integration/middleware.py` | `def create_auth_middleware_stack(session_engine: SessionEngine, auth_manager: AuthManager, app_container: Container, fault_engine: FaultEngine &#124; None = None, require_auth: bool = False) -> list[Middleware]` | Create complete middleware stack for authenticated app. |
| `set_auth_runtime_context` | `aquilia/auth/integration/runtime_context.py` | `def set_auth_runtime_context(context: AuthRuntimeContext) -> Token` | Set auth runtime context for current async task execution. |
| `reset_auth_runtime_context` | `aquilia/auth/integration/runtime_context.py` | `def reset_auth_runtime_context(token: Token) -> None` | Reset auth runtime context to previous value. |
| `get_auth_runtime_context` | `aquilia/auth/integration/runtime_context.py` | `def get_auth_runtime_context() -> AuthRuntimeContext &#124; None` | Get current auth runtime context, if any. |
| `Allow` | `aquilia/auth/policy/__init__.py` | `def Allow(reason: str &#124; None = None, **metadata) -> PolicyResult` | Create an Allow decision. |
| `Deny` | `aquilia/auth/policy/__init__.py` | `def Deny(reason: str &#124; None = None, **metadata) -> PolicyResult` | Create a Deny decision. |
| `Abstain` | `aquilia/auth/policy/__init__.py` | `def Abstain(reason: str &#124; None = None) -> PolicyResult` | Create an Abstain decision (defer to next rule/policy). |
| `rule` | `aquilia/auth/policy/__init__.py` | `def rule(func: Callable) -> Callable` | Decorator to mark a method as a policy rule. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_CLEARANCE_ATTR` | `aquilia/auth/clearance.py` | `'__aquilia_clearance__'` |
| `F` | `aquilia/auth/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |
| `SUPPORTED_ALGORITHMS` | `aquilia/auth/hashing.py` | `('argon2id', 'scrypt', 'bcrypt', 'pbkdf2_sha512', 'pbkdf2_sha256')` |
| `_AUTH_RUNTIME_CONTEXT` | `aquilia/auth/integration/runtime_context.py` | `ContextVar[AuthRuntimeContext &#124; None]` |
| `_HMAC_ALGORITHMS` | `aquilia/auth/tokens.py` | `frozenset[str]` |
| `_ASYMMETRIC_ALGORITHMS` | `aquilia/auth/tokens.py` | `frozenset[str]` |
| `_SUPPORTED_ALGORITHMS` | `aquilia/auth/tokens.py` | `frozenset[str]` |
| `_HMAC_DIGEST` | `aquilia/auth/tokens.py` | `dict[str, str]` |

## Detailed Classes And Methods

### Class: `AuditEventType`

- Source: `aquilia/auth/audit.py`
- Bases: `str, enum.Enum`
- Summary: Categories of security events.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `AUTH_LOGIN_SUCCESS` |  | `'auth.login.success'` |
| `AUTH_LOGIN_FAILURE` |  | `'auth.login.failure'` |
| `AUTH_LOGOUT` |  | `'auth.logout'` |
| `AUTH_TOKEN_ISSUED` |  | `'auth.token.issued'` |
| `AUTH_TOKEN_REFRESHED` |  | `'auth.token.refreshed'` |
| `AUTH_TOKEN_REVOKED` |  | `'auth.token.revoked'` |
| `AUTH_TOKEN_EXPIRED` |  | `'auth.token.expired'` |
| `AUTH_TOKEN_INVALID` |  | `'auth.token.invalid'` |
| `AUTH_API_KEY_USED` |  | `'auth.apikey.used'` |
| `AUTH_API_KEY_REJECTED` |  | `'auth.apikey.rejected'` |
| `AUTH_MFA_CHALLENGE` |  | `'auth.mfa.challenge'` |
| `AUTH_MFA_SUCCESS` |  | `'auth.mfa.success'` |
| `AUTH_MFA_FAILURE` |  | `'auth.mfa.failure'` |
| `AUTHZ_ACCESS_GRANTED` |  | `'authz.access.granted'` |
| `AUTHZ_ACCESS_DENIED` |  | `'authz.access.denied'` |
| `AUTHZ_CLEARANCE_GRANTED` |  | `'authz.clearance.granted'` |
| `AUTHZ_CLEARANCE_DENIED` |  | `'authz.clearance.denied'` |
| `AUTHZ_POLICY_EVALUATED` |  | `'authz.policy.evaluated'` |
| `SESSION_CREATED` |  | `'session.created'` |
| `SESSION_DESTROYED` |  | `'session.destroyed'` |
| `SESSION_EXPIRED` |  | `'session.expired'` |
| `SESSION_HIJACK_ATTEMPT` |  | `'session.hijack_attempt'` |
| `ACCOUNT_LOCKED` |  | `'account.locked'` |
| `ACCOUNT_UNLOCKED` |  | `'account.unlocked'` |
| `ACCOUNT_SUSPENDED` |  | `'account.suspended'` |
| `ACCOUNT_RATE_LIMITED` |  | `'account.rate_limited'` |
| `ACCOUNT_PASSWORD_CHANGED` |  | `'account.password_changed'` |
| `ACCOUNT_CREATED` |  | `'account.created'` |
| `OAUTH_AUTH_CODE_ISSUED` |  | `'oauth.authcode.issued'` |
| `OAUTH_CLIENT_AUTH` |  | `'oauth.client.auth'` |
| `OAUTH_DEVICE_AUTH` |  | `'oauth.device.auth'` |
| `SECURITY_KEY_ROTATED` |  | `'security.key.rotated'` |
| `SECURITY_KEY_REVOKED` |  | `'security.key.revoked'` |
| `SECURITY_CONFIG_CHANGED` |  | `'security.config.changed'` |

### Class: `AuditSeverity`

- Source: `aquilia/auth/audit.py`
- Bases: `str, enum.Enum`
- Summary: Severity levels for audit events.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `INFO` |  | `'info'` |
| `WARNING` |  | `'warning'` |
| `CRITICAL` |  | `'critical'` |
| `ALERT` |  | `'alert'` |

### Class: `AuditEvent`

- Source: `aquilia/auth/audit.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Structured security audit event.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `event_type` | `AuditEventType` |  |
| `severity` | `AuditSeverity` |  |
| `timestamp` | `float` | `field(default_factory=time.time)` |
| `identity_id` | `str &#124; None` | `None` |
| `ip_address` | `str &#124; None` | `None` |
| `user_agent` | `str &#124; None` | `None` |
| `resource` | `str &#124; None` | `None` |
| `action` | `str &#124; None` | `None` |
| `outcome` | `str` | `'success'` |
| `details` | `dict[str, Any]` | `field(default_factory=dict)` |
| `request_id` | `str &#124; None` | `None` |
| `session_id` | `str &#124; None` | `None` |
| `tenant_id` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `timestamp_iso` | `def timestamp_iso(self) -> str` | property | ISO 8601 timestamp. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dict for logging/storage. |
| `to_json` | `def to_json(self) -> str` |  | Serialize to JSON string. |

### Class: `AuditStore`

- Source: `aquilia/auth/audit.py`
- Bases: `object`
- Summary: Base class for audit event storage.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `emit` | `async def emit(self, event: AuditEvent) -> None` |  | Store/emit an audit event. |
| `query` | `async def query(self, event_type: AuditEventType &#124; None = None, identity_id: str &#124; None = None, since: float &#124; None = None, until: float &#124; None = None, limit: int = 100) -> list[AuditEvent]` |  | Query stored events. Optional -- not all stores support this. |

### Class: `MemoryAuditStore`

- Source: `aquilia/auth/audit.py`
- Bases: `AuditStore`
- Summary: In-memory audit store for development/testing.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `emit` | `async def emit(self, event: AuditEvent) -> None` |  | Store event in memory. |
| `query` | `async def query(self, event_type: AuditEventType &#124; None = None, identity_id: str &#124; None = None, since: float &#124; None = None, until: float &#124; None = None, limit: int = 100) -> list[AuditEvent]` |  | Query events from memory store. |
| `clear` | `def clear(self) -> None` |  | Clear all stored events. |
| `events` | `def events(self) -> list[AuditEvent]` | property | Access stored events. |

### Class: `LoggingAuditStore`

- Source: `aquilia/auth/audit.py`
- Bases: `AuditStore`
- Summary: Audit store that logs to Python logging framework.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `emit` | `async def emit(self, event: AuditEvent) -> None` |  | Emit event to logger. |

### Class: `AuditTrail`

- Source: `aquilia/auth/audit.py`
- Bases: `object`
- Summary: Central audit trail for security events.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `add_store` | `def add_store(self, store: AuditStore) -> None` |  | Add an audit store. |
| `emit` | `async def emit(self, event: AuditEvent) -> None` |  | Emit an event to all stores. |
| `login_success` | `async def login_success(self, identity_id: str, request: Any = None, method: str = 'password', **extra) -> None` |  | Record successful login. |
| `login_failure` | `async def login_failure(self, identity_id: str &#124; None, request: Any = None, reason: str = 'invalid_credentials', **extra) -> None` |  | Record failed login attempt. |
| `access_denied` | `async def access_denied(self, identity_id: str &#124; None, resource: str, request: Any = None, reason: str = 'insufficient_permissions', **extra) -> None` |  | Record access denied event. |
| `clearance_evaluated` | `async def clearance_evaluated(self, identity_id: str &#124; None, resource: str, granted: bool, request: Any = None, **extra) -> None` |  | Record clearance evaluation result. |
| `token_event` | `async def token_event(self, event_type: AuditEventType, identity_id: str, request: Any = None, **extra) -> None` |  | Record token lifecycle event. |
| `account_locked` | `async def account_locked(self, identity_id: str, request: Any = None, reason: str = 'max_attempts_exceeded', **extra) -> None` |  | Record account lockout. |
| `session_event` | `async def session_event(self, event_type: AuditEventType, identity_id: str &#124; None = None, request: Any = None, **extra) -> None` |  | Record session lifecycle event. |
| `query` | `async def query(self, event_type: AuditEventType &#124; None = None, identity_id: str &#124; None = None, since: float &#124; None = None, until: float &#124; None = None, limit: int = 100) -> list[AuditEvent]` |  | Query events from first store that supports it. |

### Class: `Decision`

- Source: `aquilia/auth/authz.py`
- Bases: `str, Enum`
- Summary: Authorization decision.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `ALLOW` |  | `'allow'` |
| `DENY` |  | `'deny'` |
| `ABSTAIN` |  | `'abstain'` |

### Class: `AuthzContext`

- Source: `aquilia/auth/authz.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Authorization context for policy evaluation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `identity` | `Identity` |  |
| `resource` | `str` |  |
| `action` | `str` |  |
| `scopes` | `list[str]` | `field(default_factory=list)` |
| `roles` | `list[str]` | `field(default_factory=list)` |
| `attributes` | `dict[str, Any]` | `field(default_factory=dict)` |
| `tenant_id` | `str &#124; None` | `None` |
| `session_id` | `str &#124; None` | `None` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

### Class: `AuthzResult`

- Source: `aquilia/auth/authz.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Authorization result.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `decision` | `Decision` |  |
| `reason` | `str &#124; None` | `None` |
| `policy_id` | `str &#124; None` | `None` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

### Class: `RBACEngine`

- Source: `aquilia/auth/authz.py`
- Bases: `object`
- Summary: Role-Based Access Control engine.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `define_role` | `def define_role(self, role: str, permissions: list[str], inherits: list[str] &#124; None = None) -> None` |  | Define role with permissions and inheritance. |
| `get_permissions` | `def get_permissions(self, role: str, _visited: set[str] &#124; None = None) -> set[str]` |  | Get all permissions for role (including inherited). |
| `check_permission` | `def check_permission(self, roles: list[str], permission: str) -> bool` |  | Check if any role has permission. |
| `check` | `def check(self, context: AuthzContext, permission: str) -> AuthzResult` |  | Check authorization using RBAC. |

### Class: `ABACEngine`

- Source: `aquilia/auth/authz.py`
- Bases: `object`
- Summary: Attribute-Based Access Control engine.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register_policy` | `def register_policy(self, policy_id: str, policy_func: Callable[[AuthzContext], AuthzResult]) -> None` |  | Register attribute-based policy. |
| `evaluate` | `def evaluate(self, context: AuthzContext, policy_id: str) -> AuthzResult` |  | Evaluate specific policy. |

### Class: `ScopeChecker`

- Source: `aquilia/auth/authz.py`
- Bases: `object`
- Summary: OAuth2-style scope checking.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `check_scopes` | `def check_scopes(available_scopes: list[str], required_scopes: list[str]) -> bool` | staticmethod | Check if available scopes satisfy requirements. |
| `check` | `def check(context: AuthzContext, required_scopes: list[str]) -> AuthzResult` | staticmethod | Check scope-based authorization. |

### Class: `AuthzEngine`

- Source: `aquilia/auth/authz.py`
- Bases: `object`
- Summary: Unified authorization engine.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `set_policy_order` | `def set_policy_order(self, policy_ids: list[str]) -> None` |  | Set evaluation order for policies. |
| `check_scope` | `def check_scope(self, context: AuthzContext, required_scopes: list[str]) -> None` |  | Check scope requirements (raises if failed). |
| `check_role` | `def check_role(self, context: AuthzContext, required_roles: list[str]) -> None` |  | Check role requirements (raises if failed). |
| `check_permission` | `def check_permission(self, context: AuthzContext, permission: str) -> None` |  | Check RBAC permission (raises if failed). |
| `check_tenant` | `def check_tenant(self, context: AuthzContext, resource_tenant_id: str) -> None` |  | Check tenant isolation (multi-tenancy). |
| `check` | `def check(self, context: AuthzContext) -> AuthzResult` |  | Comprehensive authorization check. |
| `authorize` | `def authorize(self, context: AuthzContext, raise_on_deny: bool = True) -> AuthzResult` |  | Authorize action (with optional exception raising). |
| `list_permitted_actions` | `def list_permitted_actions(self, identity: Identity, resource: str, actions: list[str]) -> list[str]` |  | List permitted actions for resource. |

### Class: `PolicyBuilder`

- Source: `aquilia/auth/authz.py`
- Bases: `object`
- Summary: Helper for building common authorization policies.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `owner_only` | `def owner_only(attribute: str = 'owner_id') -> Callable[[AuthzContext], AuthzResult]` | staticmethod | Policy: Only resource owner can access. |
| `admin_or_owner` | `def admin_or_owner(admin_role: str = 'admin', attribute: str = 'owner_id') -> Callable[[AuthzContext], AuthzResult]` | staticmethod | Policy: Admin or resource owner can access. |
| `time_based` | `def time_based(allowed_hours: tuple[int, int] = (9, 17)) -> Callable[[AuthzContext], AuthzResult]` | staticmethod | Policy: Allow access only during specific hours (UTC). |

### Class: `AccessLevel`

- Source: `aquilia/auth/clearance.py`
- Bases: `enum.IntEnum`
- Summary: Hierarchical access tiers -- higher ordinal = stricter.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `PUBLIC` |  | `0` |
| `AUTHENTICATED` |  | `10` |
| `INTERNAL` |  | `20` |
| `CONFIDENTIAL` |  | `30` |
| `RESTRICTED` |  | `40` |

### Class: `ClearanceCondition`

- Source: `aquilia/auth/clearance.py`
- Bases: `Protocol`
- Decorators: `runtime_checkable`
- Summary: A callable predicate evaluated at request time.

### Class: `Clearance`

- Source: `aquilia/auth/clearance.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Immutable clearance requirement descriptor.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `level` | `AccessLevel` | `AccessLevel.AUTHENTICATED` |
| `entitlements` | `tuple[str, ...]` | `()` |
| `conditions` | `tuple[Callable, ...]` | `()` |
| `compartment` | `str &#124; None` | `None` |
| `deny_message` | `str` | `'Insufficient clearance'` |
| `audit` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `merge` | `def merge(self, override: Clearance) -> Clearance` |  | Merge this (class-level) clearance with an override (method-level). |

### Class: `ClearanceVerdict`

- Source: `aquilia/auth/clearance.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of a clearance evaluation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `granted` | `bool` |  |
| `level_ok` | `bool` |  |
| `entitlements_ok` | `bool` |  |
| `conditions_ok` | `bool` |  |
| `compartment_ok` | `bool` |  |
| `missing_entitlements` | `tuple[str, ...]` | `()` |
| `failed_conditions` | `tuple[str, ...]` | `()` |
| `message` | `str` | `''` |
| `evaluated_at` | `float` | `0.0` |
| `identity_id` | `str &#124; None` | `None` |

### Class: `ClearanceEngine`

- Source: `aquilia/auth/clearance.py`
- Bases: `object`
- Summary: Evaluates clearance requirements against request context.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `resolve_identity_level` | `def resolve_identity_level(self, identity: Any) -> AccessLevel` |  | Determine the highest AccessLevel an identity holds. |
| `resolve_entitlements` | `def resolve_entitlements(self, identity: Any) -> set[str]` |  | Resolve the set of entitlements an identity holds. |
| `resolve_compartment` | `def resolve_compartment(self, compartment_template: str &#124; None, identity: Any, request: Any, ctx: Any) -> str &#124; None` |  | Resolve a compartment template to a concrete value. |
| `evaluate` | `async def evaluate(self, clearance: Clearance, identity: Any, request: Any, ctx: Any) -> ClearanceVerdict` |  | Evaluate a clearance requirement against the current context. |
| `clear_cache` | `def clear_cache(self) -> None` |  | Clear identity level cache. |

### Class: `ClearanceGuard`

- Source: `aquilia/auth/clearance.py`
- Bases: `object`
- Summary: Pipeline guard that enforces Clearance requirements.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `for_controller` | `def for_controller(self) -> ClearanceGuard` |  | Return self -- already works as controller pipeline guard. |

### Class: `IdentityType`

- Source: `aquilia/auth/core.py`
- Bases: `str, Enum`
- Summary: Type of authenticated principal.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `USER` |  | `'user'` |
| `SERVICE` |  | `'service'` |
| `DEVICE` |  | `'device'` |
| `ANONYMOUS` |  | `'anonymous'` |

### Class: `IdentityStatus`

- Source: `aquilia/auth/core.py`
- Bases: `str, Enum`
- Summary: Identity status.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `ACTIVE` |  | `'active'` |
| `SUSPENDED` |  | `'suspended'` |
| `DELETED` |  | `'deleted'` |
| `PENDING` |  | `'pending'` |

### Class: `Identity`

- Source: `aquilia/auth/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Authenticated principal (user or service).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `id` | `str` |  |
| `type` | `IdentityType` |  |
| `attributes` | `dict[str, Any]` |  |
| `status` | `IdentityStatus` | `IdentityStatus.ACTIVE` |
| `tenant_id` | `str &#124; None` | `None` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `updated_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_attribute` | `def get_attribute(self, key: str, default: Any = None) -> Any` |  | Get attribute value with default. |
| `has_role` | `def has_role(self, role: str) -> bool` |  | Check if identity has role. |
| `has_scope` | `def has_scope(self, scope: str) -> bool` |  | Check if identity has scope. |
| `is_active` | `def is_active(self) -> bool` |  | Check if identity is active. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dict. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any]) -> Identity` | classmethod | Deserialize from dict. |

### Class: `CredentialStatus`

- Source: `aquilia/auth/core.py`
- Bases: `str, Enum`
- Summary: Credential status.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `ACTIVE` |  | `'active'` |
| `SUSPENDED` |  | `'suspended'` |
| `REVOKED` |  | `'revoked'` |
| `EXPIRED` |  | `'expired'` |

### Class: `Credential`

- Source: `aquilia/auth/core.py`
- Bases: `Protocol`
- Decorators: `dataclass`
- Summary: Base protocol for credentials.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `identity_id` | `str` |  |
| `status` | `CredentialStatus` |  |
| `created_at` | `datetime` |  |
| `last_used_at` | `datetime &#124; None` |  |

### Class: `PasswordCredential`

- Source: `aquilia/auth/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Password-based credential.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `identity_id` | `str` |  |
| `password_hash` | `str` |  |
| `algorithm` | `str` | `'argon2id'` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `last_changed_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `last_used_at` | `datetime &#124; None` | `None` |
| `must_change` | `bool` | `False` |
| `status` | `CredentialStatus` | `CredentialStatus.ACTIVE` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `should_rotate` | `def should_rotate(self, max_age_days: int = 90) -> bool` |  | Check if password should be rotated. |
| `touch` | `def touch(self) -> None` |  | Update last_used_at timestamp. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dict. |

### Class: `ApiKeyCredential`

- Source: `aquilia/auth/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: API key credential (long-lived).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `identity_id` | `str` |  |
| `key_id` | `str` |  |
| `key_hash` | `str` |  |
| `prefix` | `str` |  |
| `scopes` | `list[str]` |  |
| `rate_limit` | `int &#124; None` | `None` |
| `expires_at` | `datetime &#124; None` | `None` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `last_used_at` | `datetime &#124; None` | `None` |
| `status` | `CredentialStatus` | `CredentialStatus.ACTIVE` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_expired` | `def is_expired(self) -> bool` |  | Check if key has expired. |
| `touch` | `def touch(self) -> None` |  | Update last_used_at timestamp. |
| `generate_key` | `def generate_key(env: Literal['test', 'live'] = 'live') -> str` | staticmethod | Generate new API key. |
| `hash_key` | `def hash_key(key: str) -> str` | staticmethod | Hash API key with HMAC-SHA256 (OWASP recommended). |
| `verify_key` | `def verify_key(key: str, stored_hash: str) -> bool` | staticmethod | Verify API key against stored hash using constant-time comparison. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dict. |

### Class: `OAuthClient`

- Source: `aquilia/auth/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: OAuth2/OIDC client.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `client_id` | `str` |  |
| `client_secret_hash` | `str &#124; None` |  |
| `name` | `str` |  |
| `grant_types` | `list[Literal['authorization_code', 'client_credentials', 'refresh_token', 'device_code']]` |  |
| `redirect_uris` | `list[str]` |  |
| `scopes` | `list[str]` |  |
| `require_pkce` | `bool` | `True` |
| `require_consent` | `bool` | `True` |
| `token_endpoint_auth_method` | `Literal['client_secret_basic', 'client_secret_post', 'none']` | `'client_secret_post'` |
| `access_token_ttl` | `int` | `3600` |
| `refresh_token_ttl` | `int` | `2592000` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `status` | `CredentialStatus` | `CredentialStatus.ACTIVE` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_public_client` | `def is_public_client(self) -> bool` |  | Check if client is public (no secret). |
| `supports_grant_type` | `def supports_grant_type(self, grant_type: str) -> bool` |  | Check if client supports grant type. |
| `is_redirect_uri_valid` | `def is_redirect_uri_valid(self, redirect_uri: str) -> bool` |  | Check if redirect URI is allowed. |
| `generate_client_id` | `def generate_client_id(prefix: str = 'app') -> str` | staticmethod | Generate client ID. |
| `generate_client_secret` | `def generate_client_secret() -> str` | staticmethod | Generate client secret. |
| `hash_client_secret` | `def hash_client_secret(secret: str) -> str` | staticmethod | Hash client secret with HMAC-SHA256 (OWASP recommended). |
| `verify_client_secret` | `def verify_client_secret(secret: str, stored_hash: str) -> bool` | staticmethod | Verify client secret against stored hash using constant-time comparison. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dict. |

### Class: `MFACredential`

- Source: `aquilia/auth/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Multi-factor authentication credential.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `identity_id` | `str` |  |
| `mfa_type` | `Literal['totp', 'webauthn', 'sms', 'email']` |  |
| `mfa_secret` | `str &#124; None` | `None` |
| `backup_codes` | `list[str]` | `field(default_factory=list)` |
| `webauthn_credentials` | `list[dict[str, Any]]` | `field(default_factory=list)` |
| `phone_number` | `str &#124; None` | `None` |
| `email` | `str &#124; None` | `None` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `verified_at` | `datetime &#124; None` | `None` |
| `last_used_at` | `datetime &#124; None` | `None` |
| `status` | `CredentialStatus` | `CredentialStatus.ACTIVE` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_verified` | `def is_verified(self) -> bool` |  | Check if MFA is verified. |
| `touch` | `def touch(self) -> None` |  | Update last_used_at timestamp. |
| `generate_totp_secret` | `def generate_totp_secret() -> str` | staticmethod | Generate TOTP secret (base32). |
| `generate_backup_codes` | `def generate_backup_codes(count: int = 10) -> list[str]` | staticmethod | Generate backup codes (8-character alphanumeric). |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dict. |

### Class: `TokenClaims`

- Source: `aquilia/auth/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Access token claims (JWT payload).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `iss` | `str` |  |
| `sub` | `str` |  |
| `aud` | `list[str]` |  |
| `exp` | `int` |  |
| `iat` | `int` |  |
| `nbf` | `int` |  |
| `jti` | `str` |  |
| `scopes` | `list[str]` |  |
| `sid` | `str &#124; None` | `None` |
| `roles` | `list[str]` | `field(default_factory=list)` |
| `tenant_id` | `str &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_expired` | `def is_expired(self) -> bool` |  | Check if token has expired. |
| `has_scope` | `def has_scope(self, scope: str) -> bool` |  | Check if token has scope. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dict (JWT payload). |
| `from_dict` | `def from_dict(cls, data: dict[str, Any]) -> TokenClaims` | classmethod | Deserialize from dict (JWT payload). |

### Class: `AuthResult`

- Source: `aquilia/auth/core.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of authentication operation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `identity` | `Identity` |  |
| `access_token` | `str &#124; None` | `None` |
| `refresh_token` | `str &#124; None` | `None` |
| `session_id` | `str &#124; None` | `None` |
| `expires_in` | `int &#124; None` | `None` |
| `token_type` | `str` | `'Bearer'` |
| `scopes` | `list[str]` | `field(default_factory=list)` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dict (token response). |

### Class: `IdentityStore`

- Source: `aquilia/auth/core.py`
- Bases: `Protocol`
- Summary: Protocol for identity storage.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `create` | `async def create(self, identity: Identity) -> None` |  | Create new identity. |
| `get` | `async def get(self, identity_id: str) -> Identity &#124; None` |  | Get identity by ID. |
| `get_by_attribute` | `async def get_by_attribute(self, key: str, value: Any) -> Identity &#124; None` |  | Get identity by attribute (e.g., email). |
| `update` | `async def update(self, identity: Identity) -> None` |  | Update identity. |
| `delete` | `async def delete(self, identity_id: str) -> None` |  | Delete identity (soft delete). |
| `list_by_tenant` | `async def list_by_tenant(self, tenant_id: str) -> list[Identity]` |  | List identities by tenant. |

### Class: `CredentialStore`

- Source: `aquilia/auth/core.py`
- Bases: `Protocol`
- Summary: Protocol for credential storage.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `create_password` | `async def create_password(self, credential: PasswordCredential) -> None` |  | Create password credential. |
| `get_password` | `async def get_password(self, identity_id: str) -> PasswordCredential &#124; None` |  | Get password credential. |
| `update_password` | `async def update_password(self, credential: PasswordCredential) -> None` |  | Update password credential. |
| `create_api_key` | `async def create_api_key(self, credential: ApiKeyCredential) -> None` |  | Create API key credential. |
| `get_api_key` | `async def get_api_key(self, key_id: str) -> ApiKeyCredential &#124; None` |  | Get API key by ID. |
| `get_api_key_by_hash` | `async def get_api_key_by_hash(self, key_hash: str) -> ApiKeyCredential &#124; None` |  | Get API key by hash. |
| `list_api_keys` | `async def list_api_keys(self, identity_id: str) -> list[ApiKeyCredential]` |  | List API keys for identity. |
| `revoke_api_key` | `async def revoke_api_key(self, key_id: str) -> None` |  | Revoke API key. |
| `create_mfa` | `async def create_mfa(self, credential: MFACredential) -> None` |  | Create MFA credential. |
| `get_mfa` | `async def get_mfa(self, identity_id: str) -> list[MFACredential]` |  | Get MFA credentials for identity. |
| `update_mfa` | `async def update_mfa(self, credential: MFACredential) -> None` |  | Update MFA credential. |

### Class: `OAuthClientStore`

- Source: `aquilia/auth/core.py`
- Bases: `Protocol`
- Summary: Protocol for OAuth client storage.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `create` | `async def create(self, client: OAuthClient) -> None` |  | Create OAuth client. |
| `get` | `async def get(self, client_id: str) -> OAuthClient &#124; None` |  | Get client by ID. |
| `update` | `async def update(self, client: OAuthClient) -> None` |  | Update client. |
| `delete` | `async def delete(self, client_id: str) -> None` |  | Delete client. |
| `list_all` | `async def list_all(self) -> list[OAuthClient]` |  | List all clients. |

### Class: `CrousArtifact`

- Source: `aquilia/auth/crous.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Base crous artifact.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `artifact_type` | `str` |  |
| `artifact_id` | `str` |  |
| `version` | `int` |  |
| `created_at` | `datetime` |  |
| `created_by` | `str` |  |
| `signature` | `str &#124; None` | `None` |
| `metadata` | `dict[str, Any] &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dictionary. |
| `compute_hash` | `def compute_hash(self) -> str` |  | Compute SHA256 hash of artifact (for signing). |

### Class: `KeyArtifact`

- Source: `aquilia/auth/crous.py`
- Bases: `CrousArtifact`
- Decorators: `dataclass`
- Summary: Cryptographic key artifact.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `key_descriptor` | `KeyDescriptor` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `PolicyArtifact`

- Source: `aquilia/auth/crous.py`
- Bases: `CrousArtifact`
- Decorators: `dataclass`
- Summary: Authorization policy artifact.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `policy_id` | `str` |  |
| `policy_data` | `dict[str, Any]` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `AuditEventArtifact`

- Source: `aquilia/auth/crous.py`
- Bases: `CrousArtifact`
- Decorators: `dataclass`
- Summary: Audit event artifact.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `event_type` | `str` |  |
| `identity_id` | `str &#124; None` |  |
| `resource` | `str &#124; None` |  |
| `action` | `str &#124; None` |  |
| `result` | `str` |  |
| `details` | `dict[str, Any]` |  |

### Class: `ArtifactSigner`

- Source: `aquilia/auth/crous.py`
- Bases: `object`
- Summary: Signs and verifies crous artifacts.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `sign_artifact` | `def sign_artifact(self, artifact: CrousArtifact) -> str` |  | Sign artifact. |
| `verify_artifact` | `def verify_artifact(self, artifact: CrousArtifact, signature: str) -> bool` |  | Verify artifact signature. |

### Class: `MemoryArtifactStore`

- Source: `aquilia/auth/crous.py`
- Bases: `object`
- Summary: In-memory artifact store for development/testing.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `save_artifact` | `async def save_artifact(self, artifact: CrousArtifact) -> None` |  | Save artifact. |
| `get_artifact` | `async def get_artifact(self, artifact_id: str) -> CrousArtifact &#124; None` |  | Get artifact by ID. |
| `list_artifacts` | `async def list_artifacts(self, artifact_type: str &#124; None = None) -> list[CrousArtifact]` |  | List artifacts by type. |

### Class: `AuditLogger`

- Source: `aquilia/auth/crous.py`
- Bases: `object`
- Summary: Audit event logger with crous artifact integration.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `log_event` | `async def log_event(self, event_type: str, result: str, identity_id: str &#124; None = None, resource: str &#124; None = None, action: str &#124; None = None, details: dict[str, Any] &#124; None = None) -> AuditEventArtifact` |  | Log audit event. |
| `query_events` | `async def query_events(self, event_type: str &#124; None = None, identity_id: str &#124; None = None, start_time: datetime &#124; None = None, end_time: datetime &#124; None = None) -> list[AuditEventArtifact]` |  | Query audit events. |

### Class: `AuthorizationRequiredFault`

- Source: `aquilia/auth/decorators.py`
- Bases: `Fault`
- Summary: Raised when authorization check fails.

### Class: `AuthGuard`

- Source: `aquilia/auth/decorators.py`
- Bases: `object`
- Summary: Base class for authentication/authorization guards.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `check` | `async def check(self, identity: Identity &#124; None, session: Session &#124; None) -> bool` |  | Check if access should be granted. |

### Class: `AdminGuard`

- Source: `aquilia/auth/decorators.py`
- Bases: `AuthGuard`
- Summary: Guard that requires admin role.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `check` | `async def check(self, identity: Identity &#124; Session &#124; None = None, session: Session &#124; None = None) -> bool` |  | Method. |

### Class: `VerifiedEmailGuard`

- Source: `aquilia/auth/decorators.py`
- Bases: `AuthGuard`
- Summary: Guard that requires verified email.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `check` | `async def check(self, identity: Identity &#124; Session &#124; None = None, session: Session &#124; None = None) -> bool` |  | Method. |

### Class: `RoleGuard`

- Source: `aquilia/auth/decorators.py`
- Bases: `AuthGuard`
- Summary: Guard that requires specific role(s).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `check` | `async def check(self, identity: Identity &#124; None, session: Session &#124; None) -> bool` |  | Method. |

### Class: `ScopeGuard`

- Source: `aquilia/auth/decorators.py`
- Bases: `AuthGuard`
- Summary: Guard that requires specific scope(s).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `check` | `async def check(self, identity: Identity &#124; None, session: Session &#124; None) -> bool` |  | Method. |

### Class: `AUTH_INVALID_CREDENTIALS`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Invalid username or password.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_001'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Invalid credentials'` |
| `public_message` |  | `'Invalid username or password'` |
| `retryable` |  | `False` |

### Class: `AUTH_TOKEN_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Invalid or malformed token.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_002'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Invalid token'` |
| `public_message` |  | `'Invalid authentication token'` |
| `retryable` |  | `False` |

### Class: `AUTH_TOKEN_EXPIRED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Access token has expired.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_003'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Token expired'` |
| `public_message` |  | `'Your session has expired. Please log in again.'` |
| `retryable` |  | `False` |

### Class: `AUTH_TOKEN_REVOKED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Token has been revoked.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_004'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Token revoked'` |
| `public_message` |  | `'This token has been revoked'` |
| `retryable` |  | `False` |

### Class: `AUTH_MFA_REQUIRED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Multi-factor authentication required.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_005'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'MFA required'` |
| `public_message` |  | `'Please enter your MFA code'` |
| `retryable` |  | `True` |

### Class: `AUTH_MFA_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Invalid MFA code.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_006'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Invalid MFA code'` |
| `public_message` |  | `'Invalid MFA code'` |
| `retryable` |  | `True` |

### Class: `AUTH_ACCOUNT_SUSPENDED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Account is suspended.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_007'` |
| `severity` |  | `Severity.ERROR` |
| `message` |  | `'Account suspended'` |
| `public_message` |  | `'Your account has been suspended. Please contact support.'` |
| `retryable` |  | `False` |

### Class: `AUTH_ACCOUNT_LOCKED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Account is locked due to failed login attempts.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_008'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Account locked'` |
| `public_message` |  | `'Account locked due to multiple failed login attempts'` |
| `retryable` |  | `True` |
| `retry_after` |  | `900` |

### Class: `AUTH_RATE_LIMITED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Too many authentication attempts.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_009'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Rate limit exceeded'` |
| `public_message` |  | `'Too many attempts. Please try again later.'` |
| `retryable` |  | `True` |
| `retry_after` |  | `900` |

### Class: `AUTH_REQUIRED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Authentication required but not provided.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_010'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Authentication required'` |
| `public_message` |  | `'Please log in to access this resource'` |
| `retryable` |  | `False` |

### Class: `AUTH_CLIENT_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Invalid OAuth client credentials.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_011'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Invalid client'` |
| `public_message` |  | `'Invalid client credentials'` |
| `retryable` |  | `False` |

### Class: `AUTH_GRANT_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Invalid OAuth grant (code, refresh token, etc.).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_012'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Invalid grant'` |
| `public_message` |  | `'Invalid or expired authorization code'` |
| `retryable` |  | `False` |

### Class: `AUTH_REDIRECT_URI_MISMATCH`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: OAuth redirect URI doesn't match registered URI.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_013'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Redirect URI mismatch'` |
| `public_message` |  | `'Invalid redirect URI'` |
| `retryable` |  | `False` |

### Class: `AUTH_SCOPE_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Requested scope is invalid or not allowed.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_014'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Invalid scope'` |
| `public_message` |  | `'Requested scope is not available'` |
| `retryable` |  | `False` |

### Class: `AUTH_PKCE_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: PKCE code verifier doesn't match challenge.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_015'` |
| `severity` |  | `Severity.ERROR` |
| `message` |  | `'PKCE verification failed'` |
| `public_message` |  | `'Authorization failed'` |
| `retryable` |  | `False` |

### Class: `AUTHZ_POLICY_DENIED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Authorization policy denied access.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTHZ_001'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Access denied by policy'` |
| `public_message` |  | `'You do not have permission to perform this action'` |
| `retryable` |  | `False` |

### Class: `AUTHZ_INSUFFICIENT_SCOPE`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Token missing required scopes.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTHZ_002'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Insufficient scope'` |
| `public_message` |  | `'Insufficient permissions'` |
| `retryable` |  | `False` |

### Class: `AUTHZ_INSUFFICIENT_ROLE`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Identity missing required role.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTHZ_003'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Insufficient role'` |
| `public_message` |  | `'Insufficient permissions'` |
| `retryable` |  | `False` |

### Class: `AUTHZ_RESOURCE_FORBIDDEN`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Access to resource is forbidden.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTHZ_004'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Resource forbidden'` |
| `public_message` |  | `'Access to this resource is forbidden'` |
| `retryable` |  | `False` |

### Class: `AUTHZ_TENANT_MISMATCH`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Identity tenant doesn't match resource tenant.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTHZ_005'` |
| `severity` |  | `Severity.ERROR` |
| `message` |  | `'Tenant mismatch'` |
| `public_message` |  | `'Access denied'` |
| `retryable` |  | `False` |

### Class: `AUTH_PASSWORD_WEAK`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Password doesn't meet policy requirements.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_101'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Weak password'` |
| `public_message` |  | `"Password doesn't meet security requirements"` |
| `retryable` |  | `True` |

### Class: `AUTH_PASSWORD_BREACHED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Password found in breach database.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_102'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Breached password'` |
| `public_message` |  | `'This password has been found in data breaches. Please choose a different password.'` |
| `retryable` |  | `True` |

### Class: `AUTH_PASSWORD_REUSED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Password was recently used.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_103'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Password reused'` |
| `public_message` |  | `'This password was recently used. Please choose a different password.'` |
| `retryable` |  | `True` |

### Class: `AUTH_KEY_EXPIRED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: API key has expired.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_104'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'API key expired'` |
| `public_message` |  | `'API key has expired'` |
| `retryable` |  | `False` |

### Class: `AUTH_KEY_REVOKED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: API key has been revoked.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_105'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'API key revoked'` |
| `public_message` |  | `'API key has been revoked'` |
| `retryable` |  | `False` |

### Class: `AUTH_SESSION_REQUIRED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Session required but not found.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_201'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Session required'` |
| `public_message` |  | `'Please log in'` |
| `retryable` |  | `False` |

### Class: `AUTH_SESSION_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Session is invalid or corrupted.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_202'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Invalid session'` |
| `public_message` |  | `'Your session is invalid. Please log in again.'` |
| `retryable` |  | `False` |

### Class: `AUTH_SESSION_HIJACK_DETECTED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Potential session hijacking detected.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_203'` |
| `severity` |  | `Severity.ERROR` |
| `message` |  | `'Session hijack detected'` |
| `public_message` |  | `'Security issue detected. Please log in again.'` |
| `retryable` |  | `False` |

### Class: `AUTH_CONSENT_REQUIRED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: User consent required for OAuth flow.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_301'` |
| `severity` |  | `Severity.INFO` |
| `message` |  | `'Consent required'` |
| `public_message` |  | `'Please authorize this application'` |
| `retryable` |  | `True` |

### Class: `AUTH_DEVICE_CODE_PENDING`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Device code authorization pending.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_302'` |
| `severity` |  | `Severity.INFO` |
| `message` |  | `'Authorization pending'` |
| `public_message` |  | `'Waiting for user authorization'` |
| `retryable` |  | `True` |

### Class: `AUTH_DEVICE_CODE_EXPIRED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Device code has expired.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_303'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Device code expired'` |
| `public_message` |  | `'Authorization code expired. Please try again.'` |
| `retryable` |  | `False` |

### Class: `AUTH_SLOW_DOWN`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Device flow polling too fast.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_304'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Slow down'` |
| `public_message` |  | `'Polling too frequently'` |
| `retryable` |  | `True` |
| `retry_after` |  | `5` |

### Class: `AUTH_MFA_NOT_ENROLLED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: MFA not enrolled for user.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_401'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'MFA not enrolled'` |
| `public_message` |  | `'Multi-factor authentication is not set up'` |
| `retryable` |  | `True` |

### Class: `AUTH_MFA_ALREADY_ENROLLED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: MFA already enrolled.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_402'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'MFA already enrolled'` |
| `public_message` |  | `'Multi-factor authentication is already set up'` |
| `retryable` |  | `False` |

### Class: `AUTH_WEBAUTHN_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: WebAuthn credential invalid.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_403'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'WebAuthn invalid'` |
| `public_message` |  | `'Security key verification failed'` |
| `retryable` |  | `True` |

### Class: `AUTH_BACKUP_CODE_INVALID`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: Invalid backup code.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_404'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Invalid backup code'` |
| `public_message` |  | `'Invalid backup code'` |
| `retryable` |  | `True` |

### Class: `AUTH_BACKUP_CODE_EXHAUSTED`

- Source: `aquilia/auth/faults.py`
- Bases: `Fault`
- Summary: All backup codes used.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `domain` |  | `FaultDomain.SECURITY` |
| `code` |  | `'AUTH_405'` |
| `severity` |  | `Severity.WARN` |
| `message` |  | `'Backup codes exhausted'` |
| `public_message` |  | `'All backup codes have been used. Please generate new codes.'` |
| `retryable` |  | `False` |

### Class: `Guard`

- Source: `aquilia/auth/guards.py`
- Bases: `object`
- Summary: Base guard for authentication/authorization.

### Class: `AuthGuard`

- Source: `aquilia/auth/guards.py`
- Bases: `Guard`
- Summary: Authentication guard - requires valid authentication.

### Class: `ApiKeyGuard`

- Source: `aquilia/auth/guards.py`
- Bases: `Guard`
- Summary: API key authentication guard.

### Class: `AuthzGuard`

- Source: `aquilia/auth/guards.py`
- Bases: `Guard`
- Summary: Authorization guard - enforces access control.

### Class: `ScopeGuard`

- Source: `aquilia/auth/guards.py`
- Bases: `Guard`
- Summary: Scope-only guard - quick scope check.

### Class: `RoleGuard`

- Source: `aquilia/auth/guards.py`
- Bases: `Guard`
- Summary: Role-only guard - quick role check.

### Class: `CSRFProtection`

- Source: `aquilia/auth/hardening.py`
- Bases: `object`
- Summary: CSRF token generation and validation.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_token` | `def generate_token(self) -> str` |  | Generate a new CSRF token. |
| `validate_token` | `def validate_token(self, token: str) -> bool` |  | Validate a CSRF token. |
| `requires_validation` | `def requires_validation(self, method: str) -> bool` |  | Check if the HTTP method requires CSRF validation. |

### Class: `RequestFingerprint`

- Source: `aquilia/auth/hardening.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Fingerprint a request for session binding.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `ip_hash` | `str` |  |
| `ua_hash` | `str` |  |
| `accept_hash` | `str` |  |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_request` | `def from_request(cls, request: Any) -> RequestFingerprint` | classmethod | Create fingerprint from a request object. |
| `matches` | `def matches(self, other: RequestFingerprint, strict: bool = False) -> bool` |  | Check if another fingerprint matches this one. |
| `to_string` | `def to_string(self) -> str` |  | Serialize to storable string. |
| `from_string` | `def from_string(cls, s: str) -> RequestFingerprint &#124; None` | classmethod | Deserialize from string. |

### Class: `SecurityHeaders`

- Source: `aquilia/auth/hardening.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Configurable security headers for HTTP responses.

Attributes and fields:

| Name | Type | Default |
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

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `apply` | `def apply(self, response: Any) -> Any` |  | Apply security headers to a response object. |
| `to_dict` | `def to_dict(self) -> dict[str, str]` |  | Return headers as a dictionary. |

### Class: `TokenBinder`

- Source: `aquilia/auth/hardening.py`
- Bases: `object`
- Summary: Binds tokens to client characteristics for proof-of-possession.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `create_binding` | `def create_binding(self, token: str, fingerprint: RequestFingerprint) -> str` |  | Create a binding hash for a token + fingerprint combination. |
| `verify_binding` | `def verify_binding(self, token: str, fingerprint: RequestFingerprint, expected_binding: str) -> bool` |  | Verify that a token is being used from the expected client. |

### Class: `HasherConfig`

- Source: `aquilia/auth/hashing.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Algorithm-agnostic configuration for :class:`PasswordHasher`.

Attributes and fields:

| Name | Type | Default |
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

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_dict` | `def from_dict(cls, data: dict[str, Any]) -> HasherConfig` | classmethod | Build from a plain dict (e.g. serialised from ``pyconfig``). |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Method. |

### Class: `PasswordHasher`

- Source: `aquilia/auth/hashing.py`
- Bases: `object`
- Summary: Multi-algorithm password hasher with automatic algorithm detection.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_config` | `def from_config(cls, config: HasherConfig) -> PasswordHasher` | classmethod | Build a PasswordHasher from a :class:`HasherConfig`. |
| `hash` | `def hash(self, password: str) -> str` |  | Hash *password* with the configured algorithm (PHC format output). |
| `verify` | `def verify(self, password_hash: str, password: str) -> bool` |  | Verify *password* against *password_hash* (auto-detects algorithm). |
| `hash_async` | `async def hash_async(self, password: str) -> str` |  | Hash password without blocking the event loop. |
| `verify_async` | `async def verify_async(self, password_hash: str, password: str) -> bool` |  | Verify password without blocking the event loop. |
| `check_needs_rehash` | `def check_needs_rehash(self, password_hash: str) -> bool` |  | Check if *password_hash* should be regenerated with current params. |

### Class: `PasswordPolicy`

- Source: `aquilia/auth/hashing.py`
- Bases: `object`
- Summary: Password policy validator.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_dict` | `def from_dict(cls, data: dict[str, Any]) -> PasswordPolicy` | classmethod | Build a PasswordPolicy from a plain configuration dictionary. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize policy settings (excluding blacklist internals). |
| `validate` | `def validate(self, password: str) -> tuple[bool, list[str]]` |  | Validate password against policy. Returns (is_valid, errors). |
| `validate_async` | `async def validate_async(self, password: str) -> tuple[bool, list[str]]` |  | Async password validation (non-blocking breach check). |

### Class: `AuthPrincipal`

- Source: `aquilia/auth/integration/aquila_sessions.py`
- Bases: `SessionPrincipal`
- Summary: Authentication principal for Aquilia Sessions.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `from_identity` | `def from_identity(cls, identity: Identity) -> AuthPrincipal` | classmethod | Create AuthPrincipal from Identity. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dictionary. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any]) -> AuthPrincipal` | classmethod | Deserialize from dictionary. |

### Class: `SessionAuthBridge`

- Source: `aquilia/auth/integration/aquila_sessions.py`
- Bases: `object`
- Summary: Bridge between AuthManager and SessionEngine.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `create_auth_session` | `async def create_auth_session(self, identity: Identity, request: Any, token_claims: TokenClaims &#124; None = None) -> Session` |  | Create authenticated session. |
| `rotate_on_privilege_escalation` | `async def rotate_on_privilege_escalation(self, session: Session, response: Any) -> Session` |  | Rotate session ID after privilege escalation (e.g., MFA). |
| `verify_and_extend` | `async def verify_and_extend(self, session: Session) -> bool` |  | Verify session is valid and extend if needed. |
| `logout` | `async def logout(self, session: Session, response: Any) -> None` |  | Logout - destroy session. |
| `logout_all_devices` | `async def logout_all_devices(self, identity_id: str) -> None` |  | Logout from all devices - destroy all sessions for identity. |

### Class: `PasswordHasherProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for PasswordHasher.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> PasswordHasher` |  | Provide PasswordHasher instance. |

### Class: `PasswordPolicyProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for PasswordPolicy.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> PasswordPolicy` |  | Provide PasswordPolicy instance. |

### Class: `KeyRingProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for KeyRing.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> KeyRing` |  | Provide KeyRing with default keys. |

### Class: `TokenManagerProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for TokenManager.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> TokenManager` |  | Provide TokenManager instance. |

### Class: `RateLimiterProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for RateLimiter.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self, max_attempts: int = 5, window_seconds: int = 900, lockout_duration: int = 3600) -> RateLimiter` |  | Provide RateLimiter instance. |

### Class: `IdentityStoreProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for IdentityStore.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> MemoryIdentityStore` |  | Provide memory-based identity store. |

### Class: `CredentialStoreProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for CredentialStore.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> MemoryCredentialStore` |  | Provide memory-based credential store. |

### Class: `TokenStoreProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for TokenStore.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> MemoryTokenStore` |  | Provide memory-based token store. |

### Class: `OAuthClientStoreProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for OAuthClientStore.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> MemoryOAuthClientStore` |  | Provide memory-based OAuth client store. |

### Class: `AuthorizationCodeStoreProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for AuthorizationCodeStore.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> MemoryAuthorizationCodeStore` |  | Provide memory-based authorization code store. |

### Class: `DeviceCodeStoreProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for DeviceCodeStore.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> MemoryDeviceCodeStore` |  | Provide memory-based device code store. |

### Class: `AuthManagerProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for AuthManager.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> AuthManager` |  | Provide AuthManager instance. |

### Class: `MFAManagerProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for MFAManager.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> MFAManager` |  | Provide MFAManager instance. |

### Class: `OAuth2ManagerProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for OAuth2Manager.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> OAuth2Manager` |  | Provide OAuth2Manager instance. |

### Class: `AuthzEngineProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for AuthzEngine.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> AuthzEngine` |  | Provide AuthzEngine instance. |

### Class: `SessionEngineProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for SessionEngine.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self, policy: SessionPolicy &#124; None = None, logger: logging.Logger &#124; None = None) -> SessionEngine` |  | Provide SessionEngine instance. |

### Class: `SessionAuthBridgeProvider`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Decorators: `service`
- Summary: Provider for SessionAuthBridge.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `provide` | `def provide(self) -> SessionAuthBridge` |  | Provide SessionAuthBridge instance. |

### Class: `AuthConfig`

- Source: `aquilia/auth/integration/di_providers.py`
- Bases: `object`
- Summary: Authentication configuration builder.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `rate_limit` | `def rate_limit(self, max_attempts: int = 5, window_seconds: int = 900, lockout_duration: int = 3600) -> AuthConfig` |  | Configure rate limiting. |
| `sessions` | `def sessions(self, policy: str = 'user', ttl_days: int = 7, idle_timeout_hours: int = 1, max_sessions: int = 5) -> AuthConfig` |  | Configure session management. |
| `tokens` | `def tokens(self, access_ttl_minutes: int = 15, refresh_ttl_days: int = 30) -> AuthConfig` |  | Configure token lifetimes. |
| `mfa` | `def mfa(self, enabled: bool = True, required: bool = False) -> AuthConfig` |  | Configure MFA. |
| `oauth` | `def oauth(self, enabled: bool = True) -> AuthConfig` |  | Enable OAuth2/OIDC. |
| `build` | `def build(self) -> dict[str, Any]` |  | Build configuration dict. |

### Class: `FlowGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `object`
- Summary: Base class for Flow guards.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `as_flow_node` | `def as_flow_node(self, name: str &#124; None = None, priority: int = 50) -> FlowNode` |  | Convert guard to FlowNode. |

### Class: `RequireAuthGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require valid authentication.

### Class: `RequireSessionAuthGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require authentication via session.

### Class: `RequireTokenAuthGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require authentication via Bearer token.

### Class: `RequireApiKeyGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require authentication via API key.

### Class: `RequireScopesGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require specific OAuth scopes.

### Class: `RequireRolesGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require specific roles.

### Class: `RequirePermissionGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require specific permission.

### Class: `RequirePolicyGuard`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `FlowGuard`
- Summary: Require custom authorization policy.

### Class: `ControllerGuardAdapter`

- Source: `aquilia/auth/integration/flow_guards.py`
- Bases: `object`
- Summary: Adapts a FlowGuard to work in the Controller pipeline.

### Class: `AquilAuthMiddleware`

- Source: `aquilia/auth/integration/middleware.py`
- Bases: `object`
- Summary: Unified middleware for Auth + Sessions + DI integration.

### Class: `OptionalAuthMiddleware`

- Source: `aquilia/auth/integration/middleware.py`
- Bases: `AquilAuthMiddleware`
- Summary: Auth middleware that doesn't require authentication.

### Class: `SessionMiddleware`

- Source: `aquilia/auth/integration/middleware.py`
- Bases: `object`
- Summary: Session-only middleware without authentication.

### Class: `FaultHandlerMiddleware`

- Source: `aquilia/auth/integration/middleware.py`
- Bases: `object`
- Summary: Middleware for handling faults with FaultEngine.

### Class: `EnhancedRequestScopeMiddleware`

- Source: `aquilia/auth/integration/middleware.py`
- Bases: `object`
- Summary: Enhanced request scope middleware with better integration.

### Class: `AuthRuntimeContext`

- Source: `aquilia/auth/integration/runtime_context.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Request-scoped auth runtime state.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `request` | `Any` |  |
| `session` | `Any &#124; None` | `None` |
| `identity` | `Any &#124; None` | `None` |
| `auth` | `Any &#124; None` | `None` |
| `response` | `Any &#124; None` | `None` |
| `container` | `Any &#124; None` | `None` |

### Class: `AuthSession`

- Source: `aquilia/auth/integration/sessions.py`
- Bases: `object`
- Summary: Authentication session.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_expired` | `def is_expired(self) -> bool` |  | Check if session is expired. |
| `update_activity` | `def update_activity(self) -> None` |  | Update last activity timestamp. |
| `to_dict` | `def to_dict(self) -> dict[str, Any]` |  | Serialize to dictionary. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any]) -> AuthSession` | classmethod | Deserialize from dictionary. |

### Class: `MemorySessionStore`

- Source: `aquilia/auth/integration/sessions.py`
- Bases: `object`
- Summary: In-memory session store for development/testing.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `create_session` | `async def create_session(self, identity_id: str, ttl_seconds: int = 3600, metadata: dict[str, Any] &#124; None = None) -> AuthSession` |  | Create new session. |
| `get_session` | `async def get_session(self, session_id: str) -> AuthSession &#124; None` |  | Get session by ID. |
| `update_session` | `async def update_session(self, session: AuthSession) -> None` |  | Update session. |
| `delete_session` | `async def delete_session(self, session_id: str) -> bool` |  | Delete session. |
| `list_sessions` | `async def list_sessions(self, identity_id: str) -> list[AuthSession]` |  | List all active sessions for identity. |
| `delete_all_sessions` | `async def delete_all_sessions(self, identity_id: str) -> int` |  | Delete all sessions for identity. |

### Class: `SessionManager`

- Source: `aquilia/auth/integration/sessions.py`
- Bases: `object`
- Summary: Session manager for authentication.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `create_session` | `async def create_session(self, identity: Identity, metadata: dict[str, Any] &#124; None = None) -> AuthSession` |  | Create new session for identity. |
| `get_session` | `async def get_session(self, session_id: str) -> AuthSession &#124; None` |  | Get session and update activity. |
| `extend_session` | `async def extend_session(self, session_id: str, additional_seconds: int = 3600) -> bool` |  | Extend session expiration. |
| `rotate_session` | `async def rotate_session(self, old_session_id: str) -> AuthSession &#124; None` |  | Rotate session ID (privilege escalation). |
| `delete_session` | `async def delete_session(self, session_id: str) -> bool` |  | Delete session (logout). |
| `delete_all_sessions` | `async def delete_all_sessions(self, identity_id: str) -> int` |  | Delete all sessions for identity (logout all devices). |

### Class: `AuthSessionMiddleware`

- Source: `aquilia/auth/integration/sessions.py`
- Bases: `object`
- Summary: Middleware for session-based authentication.

### Class: `RateLimiter`

- Source: `aquilia/auth/manager.py`
- Bases: `object`
- Summary: Simple in-memory rate limiter for authentication attempts.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `record_attempt` | `def record_attempt(self, key: str) -> None` |  | Record failed authentication attempt. |
| `is_locked_out` | `def is_locked_out(self, key: str) -> bool` |  | Check if key is currently locked out. |
| `get_remaining_attempts` | `def get_remaining_attempts(self, key: str) -> int` |  | Get remaining attempts before lockout. |
| `reset` | `def reset(self, key: str) -> None` |  | Reset attempts for key (successful auth). |

### Class: `SignInProvisionPolicy`

- Source: `aquilia/auth/manager.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Provisioning policy for sign_in bootstrap behavior.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `enable_identity_seed` | `bool` | `True` |
| `create_identity_if_missing` | `bool` | `True` |
| `backfill_password_credential` | `bool` | `True` |
| `overwrite_password_credential` | `bool` | `False` |
| `allow_username_bootstrap` | `bool` | `True` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `secure_defaults` | `def secure_defaults(cls, env: str &#124; None = None) -> SignInProvisionPolicy` | classmethod | Environment-aware secure defaults. |

### Class: `AuthManager`

- Source: `aquilia/auth/manager.py`
- Bases: `object`
- Summary: Central authentication manager.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `current_session` | `def current_session(self) -> Any &#124; None` |  | Return current runtime session if auth/session middleware is active. |
| `has_active_session` | `def has_active_session(self) -> bool` |  | Check whether a runtime session is currently available. |
| `current_identity_id` | `def current_identity_id(self) -> str &#124; None` |  | Return identity_id bound to the current runtime session, if available. |
| `authenticate_password` | `async def authenticate_password(self, username: str, password: str, scopes: SessionScope &#124; str &#124; list[SessionScope &#124; str] &#124; tuple[SessionScope &#124; str, ...] &#124; set[SessionScope &#124; str] &#124; None = None, session_id: str &#124; None = None, client_metadata: dict[str, Any] &#124; None = None) -> AuthResult` |  | Authenticate using username/password. |
| `sign_in` | `async def sign_in(self, *, username: str, password: str, scopes: SessionScope &#124; str &#124; list[SessionScope &#124; str] &#124; tuple[SessionScope &#124; str, ...] &#124; set[SessionScope &#124; str] &#124; None = None, session: Literal['auto', 'new'] &#124; str = 'auto', client_metadata: dict[str, Any] &#124; None = None, identity: Identity &#124; None = None, password_hash: str &#124; None = None, provision: SignInProvisionPolicy &#124; None = None) -> AuthResult` |  | Aquilia-native high-level sign-in API. |
| `authenticate_api_key` | `async def authenticate_api_key(self, api_key: str, required_scopes: SessionScope &#124; str &#124; list[SessionScope &#124; str] &#124; tuple[SessionScope &#124; str, ...] &#124; set[SessionScope &#124; str] &#124; None = None) -> AuthResult` |  | Authenticate using API key. |
| `refresh_access_token` | `async def refresh_access_token(self, refresh_token: str) -> tuple[str, str]` |  | Refresh access token using refresh token. |
| `revoke_token` | `async def revoke_token(self, token: str, token_type: str = 'refresh') -> None` |  | Revoke a token. |
| `logout` | `async def logout(self, identity_id: str &#124; None = None, session_id: str &#124; None = None, access_token: str &#124; None = None, refresh_token: str &#124; None = None) -> None` |  | Logout user by revoking all tokens. |
| `sign_out` | `async def sign_out(self, *, scope: Literal['session', 'identity', 'all'] = 'session', identity_id: str &#124; None = None, session_id: str &#124; None = None, access_token: str &#124; None = None, refresh_token: str &#124; None = None) -> JSONObject` |  | Aquilia-native sign-out API with explicit scope semantics. |
| `resume_identity` | `async def resume_identity(self, access_token: str &#124; None = None) -> Identity &#124; None` |  | Resolve the current identity from token or runtime session context. |
| `verify_token` | `async def verify_token(self, access_token: str) -> TokenClaims` |  | Verify and decode access token. |
| `get_identity_from_token` | `async def get_identity_from_token(self, access_token: str) -> Identity &#124; None` |  | Extract identity from access token. |

### Class: `TOTPProvider`

- Source: `aquilia/auth/mfa.py`
- Bases: `object`
- Summary: TOTP (Time-based One-Time Password) provider.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_secret` | `def generate_secret(self) -> str` |  | Generate random TOTP secret. |
| `generate_code` | `def generate_code(self, secret: str, timestamp: int &#124; None = None) -> str` |  | Generate TOTP code for given secret and time. |
| `verify_code` | `def verify_code(self, secret: str, code: str, window: int = 1, timestamp: int &#124; None = None) -> bool` |  | Verify TOTP code. |
| `generate_provisioning_uri` | `def generate_provisioning_uri(self, secret: str, account_name: str) -> str` |  | Generate provisioning URI for QR code. |
| `generate_backup_codes` | `def generate_backup_codes(self, count: int = 10) -> list[str]` |  | Generate backup recovery codes. |
| `hash_backup_code` | `def hash_backup_code(code: str) -> str` | staticmethod | Hash backup code for storage using HMAC-SHA256. |
| `verify_backup_code` | `def verify_backup_code(code: str, code_hash: str) -> bool` | staticmethod | Verify backup code against hash. |

### Class: `WebAuthnProvider`

- Source: `aquilia/auth/mfa.py`
- Bases: `object`
- Summary: WebAuthn provider for passwordless authentication.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_challenge` | `def generate_challenge(self) -> str` |  | Generate cryptographic challenge. |
| `generate_registration_options` | `def generate_registration_options(self, user_id: str, user_name: str, user_display_name: str) -> dict[str, Any]` |  | Generate WebAuthn registration options. |
| `generate_authentication_options` | `def generate_authentication_options(self, credential_ids: list[str] &#124; None = None) -> dict[str, Any]` |  | Generate WebAuthn authentication options. |
| `verify_registration_response` | `def verify_registration_response(self, response: dict[str, Any], expected_challenge: str) -> dict[str, Any]` |  | Verify WebAuthn registration response. |
| `verify_authentication_response` | `def verify_authentication_response(self, response: dict[str, Any], expected_challenge: str, stored_credential: dict[str, Any]) -> bool` |  | Verify WebAuthn authentication response. |

### Class: `MFAManager`

- Source: `aquilia/auth/mfa.py`
- Bases: `object`
- Summary: Central MFA manager coordinating all MFA providers.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `enroll_totp` | `async def enroll_totp(self, user_id: str, account_name: str) -> dict[str, Any]` |  | Enroll user in TOTP MFA. |
| `verify_totp` | `async def verify_totp(self, secret: str, code: str) -> bool` |  | Verify TOTP code. |
| `verify_backup_code` | `async def verify_backup_code(self, code: str, backup_code_hashes: list[str]) -> tuple[bool, list[str]]` |  | Verify backup code and remove it. |

### Class: `PKCEVerifier`

- Source: `aquilia/auth/oauth.py`
- Bases: `object`
- Summary: PKCE (Proof Key for Code Exchange) utilities.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `generate_code_verifier` | `def generate_code_verifier(length: int = 128) -> str` | staticmethod | Generate code verifier for PKCE. |
| `generate_code_challenge` | `def generate_code_challenge(verifier: str, method: str = 'S256') -> str` | staticmethod | Generate code challenge from verifier. |
| `verify_code_challenge` | `def verify_code_challenge(verifier: str, challenge: str, method: str = 'S256') -> bool` | staticmethod | Verify code verifier against challenge. |

### Class: `OAuth2Manager`

- Source: `aquilia/auth/oauth.py`
- Bases: `object`
- Summary: OAuth 2.0 / OIDC authorization server.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `validate_client` | `async def validate_client(self, client_id: str, client_secret: str &#124; None = None) -> OAuthClient` |  | Validate OAuth client credentials. |
| `authorize` | `async def authorize(self, client_id: str, redirect_uri: str, scope: str, state: str &#124; None = None, response_type: str = 'code', code_challenge: str &#124; None = None, code_challenge_method: str = 'S256') -> dict[str, Any]` |  | Authorization endpoint - initiate authorization flow. |
| `grant_authorization_code` | `async def grant_authorization_code(self, client_id: str, identity_id: str, redirect_uri: str, scopes: list[str], code_challenge: str &#124; None = None, code_challenge_method: str = 'S256') -> str` |  | Grant authorization code after user consent. |
| `exchange_authorization_code` | `async def exchange_authorization_code(self, code: str, client_id: str, client_secret: str &#124; None, redirect_uri: str, code_verifier: str &#124; None = None) -> dict[str, Any]` |  | Token endpoint - exchange authorization code for tokens. |
| `client_credentials_grant` | `async def client_credentials_grant(self, client_id: str, client_secret: str, scope: str &#124; None = None) -> dict[str, Any]` |  | Client Credentials grant - machine-to-machine auth. |
| `device_authorization` | `async def device_authorization(self, client_id: str, scope: str &#124; None = None) -> dict[str, Any]` |  | Device Authorization - initiate device flow. |
| `device_token` | `async def device_token(self, device_code: str, client_id: str) -> dict[str, Any]` |  | Device Token - poll for authorization. |

### Class: `PolicyDecision`

- Source: `aquilia/auth/policy/__init__.py`
- Bases: `Enum`
- Summary: Result of a policy evaluation.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `ALLOW` |  | `'allow'` |
| `DENY` |  | `'deny'` |
| `ABSTAIN` |  | `'abstain'` |

### Class: `PolicyResult`

- Source: `aquilia/auth/policy/__init__.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Result of evaluating a policy rule.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `decision` | `PolicyDecision` |  |
| `reason` | `str &#124; None` | `None` |
| `metadata` | `dict[str, Any]` | `field(default_factory=dict)` |

### Class: `Policy`

- Source: `aquilia/auth/policy/__init__.py`
- Bases: `object`
- Summary: Base class for resource-based authorization policies.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `resource` | `str` | `''` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `evaluate` | `def evaluate(self, action: str, identity: Any, resource: Any = None) -> PolicyResult` |  | Evaluate policy for a given action. |
| `get_rules` | `def get_rules(self) -> list[str]` |  | Get list of defined rule names. |

### Class: `PolicyRegistry`

- Source: `aquilia/auth/policy/__init__.py`
- Bases: `object`
- Summary: Registry for authorization policies.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `register` | `def register(self, policy: Policy)` |  | Register a policy by its resource name. |
| `get` | `def get(self, resource: str) -> Policy &#124; None` |  | Get policy for a resource. |
| `evaluate` | `def evaluate(self, resource: str, action: str, identity: Any, resource_obj: Any = None) -> PolicyResult` |  | Evaluate policy for a resource action. |
| `resources` | `def resources(self) -> list[str]` | property | List all registered resource types. |

### Class: `MemoryIdentityStore`

- Source: `aquilia/auth/stores.py`
- Bases: `object`
- Summary: In-memory identity storage for development/testing.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `create` | `async def create(self, identity: Identity) -> Identity` |  | Create new identity. |
| `get` | `async def get(self, identity_id: str) -> Identity &#124; None` |  | Get identity by ID. |
| `get_by_attribute` | `async def get_by_attribute(self, attribute: str, value: Any) -> Identity &#124; None` |  | Get identity by attribute value. |
| `update` | `async def update(self, identity: Identity) -> Identity` |  | Update existing identity. |
| `delete` | `async def delete(self, identity_id: str) -> bool` |  | Delete identity (soft delete by setting status). |
| `list_by_tenant` | `async def list_by_tenant(self, tenant_id: str, limit: int = 100, offset: int = 0) -> list[Identity]` |  | List identities by tenant. |

### Class: `MemoryCredentialStore`

- Source: `aquilia/auth/stores.py`
- Bases: `object`
- Summary: In-memory credential storage for development/testing.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `save_password` | `async def save_password(self, credential: PasswordCredential) -> None` |  | Save password credential. |
| `get_password` | `async def get_password(self, identity_id: str) -> PasswordCredential &#124; None` |  | Get password credential. |
| `delete_password` | `async def delete_password(self, identity_id: str) -> bool` |  | Delete password credential. |
| `save_api_key` | `async def save_api_key(self, credential: ApiKeyCredential) -> None` |  | Save API key credential. |
| `get_api_key` | `async def get_api_key(self, key_id: str) -> ApiKeyCredential &#124; None` |  | Get API key credential. |
| `get_api_key_by_prefix` | `async def get_api_key_by_prefix(self, prefix: str) -> ApiKeyCredential &#124; None` |  | Get API key by prefix (first 8 chars). |
| `list_api_keys` | `async def list_api_keys(self, identity_id: str) -> list[ApiKeyCredential]` |  | List all API keys for identity. |
| `delete_api_key` | `async def delete_api_key(self, key_id: str) -> bool` |  | Delete API key credential. |
| `save_mfa` | `async def save_mfa(self, credential: MFACredential) -> None` |  | Save MFA credential. |
| `get_mfa` | `async def get_mfa(self, identity_id: str, mfa_type: str &#124; None = None) -> list[MFACredential]` |  | Get MFA credentials for identity. |
| `delete_mfa` | `async def delete_mfa(self, identity_id: str, mfa_type: str &#124; None = None) -> bool` |  | Delete MFA credentials. |

### Class: `MemoryOAuthClientStore`

- Source: `aquilia/auth/stores.py`
- Bases: `object`
- Summary: In-memory OAuth client storage for development/testing.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `create` | `async def create(self, client: OAuthClient) -> OAuthClient` |  | Create OAuth client. |
| `get` | `async def get(self, client_id: str) -> OAuthClient &#124; None` |  | Get OAuth client by ID. |
| `update` | `async def update(self, client: OAuthClient) -> OAuthClient` |  | Update OAuth client. |
| `delete` | `async def delete(self, client_id: str) -> bool` |  | Delete OAuth client. |
| `list` | `async def list(self, owner_id: str &#124; None = None, limit: int = 100, offset: int = 0) -> list[OAuthClient]` |  | List OAuth clients, optionally filtered by owner (from metadata). |

### Class: `MemoryTokenStore`

- Source: `aquilia/auth/stores.py`
- Bases: `object`
- Summary: In-memory token storage for development/testing.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `save_refresh_token` | `async def save_refresh_token(self, token_id: str, identity_id: str, scopes: list[str], expires_at: datetime, session_id: str &#124; None = None, metadata: dict[str, Any] &#124; None = None) -> None` |  | Save refresh token. |
| `get_refresh_token` | `async def get_refresh_token(self, token_id: str) -> dict[str, Any] &#124; None` |  | Get refresh token data. |
| `revoke_refresh_token` | `async def revoke_refresh_token(self, token_id: str) -> None` |  | Revoke single refresh token. |
| `revoke_tokens_by_identity` | `async def revoke_tokens_by_identity(self, identity_id: str) -> None` |  | Revoke all tokens for identity. |
| `revoke_tokens_by_session` | `async def revoke_tokens_by_session(self, session_id: str) -> None` |  | Revoke all tokens for session. |
| `is_token_revoked` | `async def is_token_revoked(self, token_id: str) -> bool` |  | Check if token is revoked. |
| `cleanup_expired` | `async def cleanup_expired(self) -> int` |  | Remove expired tokens (returns count removed). |

### Class: `RedisTokenStore`

- Source: `aquilia/auth/stores.py`
- Bases: `object`
- Summary: Redis-backed token store with bloom filter for fast revocation checks.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `save_refresh_token` | `async def save_refresh_token(self, token_id: str, identity_id: str, scopes: list[str], expires_at: datetime, session_id: str &#124; None = None, metadata: dict[str, Any] &#124; None = None) -> None` |  | Save refresh token to Redis. |
| `get_refresh_token` | `async def get_refresh_token(self, token_id: str) -> dict[str, Any] &#124; None` |  | Get refresh token data from Redis. |
| `revoke_refresh_token` | `async def revoke_refresh_token(self, token_id: str) -> None` |  | Revoke single refresh token. |
| `revoke_tokens_by_identity` | `async def revoke_tokens_by_identity(self, identity_id: str) -> None` |  | Revoke all tokens for identity. |
| `revoke_tokens_by_session` | `async def revoke_tokens_by_session(self, session_id: str) -> None` |  | Revoke all tokens for session. |
| `is_token_revoked` | `async def is_token_revoked(self, token_id: str) -> bool` |  | Check if token is revoked (fast check using Redis set). |
| `cleanup_expired` | `async def cleanup_expired(self) -> int` |  | Redis handles expiration automatically, return 0. |

### Class: `MemoryAuthorizationCodeStore`

- Source: `aquilia/auth/stores.py`
- Bases: `object`
- Summary: In-memory authorization code storage for OAuth2 flows.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `save_code` | `async def save_code(self, code: str, client_id: str, identity_id: str, redirect_uri: str, scopes: list[str], expires_at: datetime, code_challenge: str &#124; None = None, code_challenge_method: str &#124; None = None) -> None` |  | Save authorization code. |
| `get_code` | `async def get_code(self, code: str) -> dict[str, Any] &#124; None` |  | Get authorization code data. |
| `consume_code` | `async def consume_code(self, code: str) -> bool` |  | Mark code as used (one-time use). |
| `cleanup_expired` | `async def cleanup_expired(self) -> int` |  | Remove expired codes. |

### Class: `MemoryDeviceCodeStore`

- Source: `aquilia/auth/stores.py`
- Bases: `object`
- Summary: In-memory device code storage for device authorization flow.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `save_device_code` | `async def save_device_code(self, device_code: str, user_code: str, client_id: str, scopes: list[str], expires_at: datetime) -> None` |  | Save device code. |
| `get_by_device_code` | `async def get_by_device_code(self, device_code: str) -> dict[str, Any] &#124; None` |  | Get device code data. |
| `get_by_user_code` | `async def get_by_user_code(self, user_code: str) -> dict[str, Any] &#124; None` |  | Get device code data by user code. |
| `authorize_device_code` | `async def authorize_device_code(self, user_code: str, identity_id: str) -> bool` |  | Authorize device code (user approved). |
| `deny_device_code` | `async def deny_device_code(self, user_code: str) -> bool` |  | Deny device code (user rejected). |

### Class: `KeyAlgorithm`

- Source: `aquilia/auth/tokens.py`
- Bases: `str, Enum`
- Summary: Supported signing algorithms (Enum prevents arbitrary values).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `HS256` |  | `'HS256'` |
| `HS384` |  | `'HS384'` |
| `HS512` |  | `'HS512'` |
| `RS256` |  | `'RS256'` |
| `ES256` |  | `'ES256'` |
| `EdDSA` |  | `'EdDSA'` |

### Class: `KeyStatus`

- Source: `aquilia/auth/tokens.py`
- Bases: `str, Enum`
- Summary: Key status in lifecycle (Enum prevents invalid state transitions).

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `ACTIVE` |  | `'active'` |
| `ROTATING` |  | `'rotating'` |
| `RETIRED` |  | `'retired'` |
| `REVOKED` |  | `'revoked'` |

### Class: `KeyDescriptor`

- Source: `aquilia/auth/tokens.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Cryptographic key metadata.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `kid` | `str` |  |
| `algorithm` | `str` |  |
| `public_key_pem` | `str` |  |
| `private_key_pem` | `str &#124; None` | `None` |
| `status` | `str` | `KeyStatus.ACTIVE` |
| `created_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |
| `retire_after` | `datetime &#124; None` | `None` |
| `revoked_at` | `datetime &#124; None` | `None` |

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `is_active` | `def is_active(self) -> bool` |  | Check if key can be used for signing. |
| `can_verify` | `def can_verify(self) -> bool` |  | Check if key can be used for verification. |
| `to_dict` | `def to_dict(self, include_private_key: bool = False) -> dict[str, Any]` |  | Serialize to dict. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any]) -> KeyDescriptor` | classmethod | Deserialize from dict. |
| `generate` | `def generate(cls, kid: str, algorithm: str = KeyAlgorithm.HS256, secret: str &#124; None = None) -> KeyDescriptor` | classmethod | Generate a new key (or wrap an existing secret) for *algorithm*. |

### Class: `KeyRing`

- Source: `aquilia/auth/tokens.py`
- Bases: `object`
- Summary: Key ring for JWT signing and verification.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `get_signing_key` | `def get_signing_key(self) -> KeyDescriptor` |  | Get current signing key. |
| `get_verification_key` | `def get_verification_key(self, kid: str) -> KeyDescriptor &#124; None` |  | Get verification key by kid. |
| `add_key` | `def add_key(self, key: KeyDescriptor) -> None` |  | Add key to ring. |
| `promote_key` | `def promote_key(self, kid: str) -> None` |  | Promote key to active (retire current). |
| `revoke_key` | `def revoke_key(self, kid: str) -> None` |  | Revoke key (invalid for all operations). |
| `to_dict` | `def to_dict(self, include_private_keys: bool = True) -> dict[str, Any]` |  | Serialize to dict. |
| `from_dict` | `def from_dict(cls, data: dict[str, Any]) -> KeyRing` | classmethod | Deserialize from dict. |
| `from_file` | `def from_file(cls, path: Path) -> KeyRing` | classmethod | Load from JSON file. |
| `to_file` | `def to_file(self, path: Path) -> None` |  | Save to JSON file. |

### Class: `TokenConfig`

- Source: `aquilia/auth/tokens.py`
- Bases: `object`
- Decorators: `dataclass`
- Summary: Token manager configuration.

Attributes and fields:

| Name | Type | Default |
| --- | --- | --- |
| `issuer` | `str` | `'aquilia'` |
| `audience` | `list[str]` | `field(default_factory=lambda: ['api'])` |
| `access_token_ttl` | `int` | `3600` |
| `refresh_token_ttl` | `int` | `2592000` |
| `algorithm` | `str` | `KeyAlgorithm.RS256` |

### Class: `TokenStore`

- Source: `aquilia/auth/tokens.py`
- Bases: `Protocol`
- Summary: Protocol for token storage (opaque tokens, revocation).

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `save_refresh_token` | `async def save_refresh_token(self, token_id: str, identity_id: str, scopes: list[str], expires_at: datetime, session_id: str &#124; None = None) -> None` |  | Save refresh token. |
| `get_refresh_token` | `async def get_refresh_token(self, token_id: str) -> dict[str, Any] &#124; None` |  | Get refresh token data. |
| `revoke_refresh_token` | `async def revoke_refresh_token(self, token_id: str) -> None` |  | Revoke refresh token. |
| `revoke_tokens_by_identity` | `async def revoke_tokens_by_identity(self, identity_id: str) -> None` |  | Revoke all tokens for identity. |
| `revoke_tokens_by_session` | `async def revoke_tokens_by_session(self, session_id: str) -> None` |  | Revoke all tokens for session. |
| `is_token_revoked` | `async def is_token_revoked(self, token_id: str) -> bool` |  | Check if token is revoked. |

### Class: `TokenManager`

- Source: `aquilia/auth/tokens.py`
- Bases: `object`
- Summary: Token lifecycle manager.

Methods:

| Name | Signature | Decorators | Purpose |
| --- | --- | --- | --- |
| `issue_access_token` | `async def issue_access_token(self, identity_id: str, scopes: list[str], roles: list[str] &#124; None = None, session_id: str &#124; None = None, tenant_id: str &#124; None = None, ttl: int &#124; None = None) -> str` |  | Issue signed access token. |
| `issue_refresh_token` | `async def issue_refresh_token(self, identity_id: str, scopes: list[str], session_id: str &#124; None = None) -> str` |  | Issue opaque refresh token. |
| `validate_access_token` | `async def validate_access_token(self, token: str) -> dict[str, Any]` |  | Validate and decode access token. |
| `validate_refresh_token` | `async def validate_refresh_token(self, token: str) -> dict[str, Any]` |  | Validate refresh token. |
| `refresh_access_token` | `async def refresh_access_token(self, refresh_token: str) -> tuple[str, str]` |  | Exchange refresh token for new access + refresh tokens. |
| `revoke_token` | `async def revoke_token(self, token_id: str) -> None` |  | Revoke token by ID. |
| `revoke_tokens_by_identity` | `async def revoke_tokens_by_identity(self, identity_id: str) -> None` |  | Revoke all tokens for identity. |
| `revoke_tokens_by_session` | `async def revoke_tokens_by_session(self, session_id: str) -> None` |  | Revoke all tokens for session. |

## Functions

| Name | Source | Signature | Purpose |
| --- | --- | --- | --- |
| `is_verified` | `aquilia/auth/clearance.py` | `def is_verified(identity: Any, request: Any, ctx: Any) -> bool` | Condition: identity must have 'verified' attribute or status ACTIVE. |
| `is_owner_or_admin` | `aquilia/auth/clearance.py` | `def is_owner_or_admin(identity: Any, request: Any, ctx: Any) -> bool` | Condition: identity is resource owner or has admin role. |
| `within_quota` | `aquilia/auth/clearance.py` | `def within_quota(identity: Any, request: Any, ctx: Any) -> bool` | Condition: identity hasn't exceeded rate/resource quota. |
| `is_same_tenant` | `aquilia/auth/clearance.py` | `def is_same_tenant(identity: Any, request: Any, ctx: Any) -> bool` | Condition: identity's tenant matches resource tenant. |
| `during_hours` | `aquilia/auth/clearance.py` | `def during_hours(start: int = 9, end: int = 17) -> Callable` | Factory: condition that restricts access to business hours (UTC). |
| `require_attribute` | `aquilia/auth/clearance.py` | `def require_attribute(key: str, value: Any = None) -> Callable` | Factory: condition that requires a specific identity attribute. |
| `ip_allowlist` | `aquilia/auth/clearance.py` | `def ip_allowlist(*cidrs: str) -> Callable` | Factory: condition restricting access to specific IP ranges. |
| `grant` | `aquilia/auth/clearance.py` | `def grant(level: AccessLevel = AccessLevel.AUTHENTICATED, entitlements: Sequence[str] = (), conditions: Sequence[Callable] = (), compartment: str &#124; None = None, deny_message: str = 'Insufficient clearance', audit: bool = True) -> Callable` | Decorator to attach clearance requirements to a route method. |
| `exempt` | `aquilia/auth/clearance.py` | `def exempt(fn: Callable) -> Callable` | Decorator to exempt a route from class-level clearance. |
| `get_method_clearance` | `aquilia/auth/clearance.py` | `def get_method_clearance(method: Any) -> Clearance &#124; None` | Extract clearance from a decorated method. |
| `extract_controller_clearance` | `aquilia/auth/clearance.py` | `def extract_controller_clearance(controller_class: type) -> Clearance &#124; None` | Extract clearance from controller class. |
| `build_merged_clearance` | `aquilia/auth/clearance.py` | `def build_merged_clearance(controller_class: type, handler_method: Any) -> Clearance &#124; None` | Build merged clearance from class + method. |
| `authenticated` | `aquilia/auth/decorators.py` | `def authenticated(func: F &#124; None = None, *, login_url: str &#124; None = None, redirect_if_html: bool = False, include_next: bool = True, next_param: str = 'next', redirect_status: int = 303) -> F &#124; Callable[[F], F]` | Decorator requiring authenticated identity. |
| `require_identity` | `aquilia/auth/decorators.py` | `def require_identity(*, roles: list[str] &#124; None = None, scopes: list[str] &#124; None = None, attributes: dict[str, Any] &#124; None = None, require_all_roles: bool = False, require_all_scopes: bool = True, login_url: str &#124; None = None, redirect_if_html: bool = False, include_next: bool = True, next_param: str = 'next', redirect_status: int = 303) -> Callable[[F], F]` | Decorator requiring identity with specific attributes. |
| `requires` | `aquilia/auth/decorators.py` | `def requires(*guards: AuthGuard) -> Callable[[F], F]` | Decorator to require multiple guards. |
| `raise_auth_fault` | `aquilia/auth/faults.py` | `def raise_auth_fault(fault_class: type[Fault], **kwargs)` | Raise an auth fault with context. |
| `is_auth_fault` | `aquilia/auth/faults.py` | `def is_auth_fault(exception: Exception) -> bool` | Check if exception is an auth fault. |
| `require_auth` | `aquilia/auth/guards.py` | `def require_auth(auth_manager: AuthManager, optional: bool = False) -> Callable` | Decorator: Require authentication. |
| `require_scopes` | `aquilia/auth/guards.py` | `def require_scopes(*scopes: str) -> Callable` | Decorator: Require OAuth scopes. |
| `require_roles` | `aquilia/auth/guards.py` | `def require_roles(*roles: str, require_all: bool = False) -> Callable` | Decorator: Require roles. |
| `constant_time_compare` | `aquilia/auth/hardening.py` | `def constant_time_compare(a: str &#124; bytes, b: str &#124; bytes) -> bool` | Compare two strings/bytes in constant time to prevent timing attacks. |
| `generate_secure_token` | `aquilia/auth/hardening.py` | `def generate_secure_token(length: int = 32) -> str` | Generate a cryptographically secure random token. |
| `generate_opaque_id` | `aquilia/auth/hardening.py` | `def generate_opaque_id(prefix: str = 'aq') -> str` | Generate an opaque identifier with prefix. |
| `hash_token` | `aquilia/auth/hardening.py` | `def hash_token(token: str) -> str` | Hash a token for storage (one-way). |
| `hash_sensitive` | `aquilia/auth/hardening.py` | `def hash_sensitive(value: str, salt: str = '') -> str` | Hash sensitive data with optional salt. |
| `get_password_hasher` | `aquilia/auth/hashing.py` | `def get_password_hasher() -> PasswordHasher` | Get default password hasher instance. |
| `hash_password` | `aquilia/auth/hashing.py` | `def hash_password(password: str) -> str` | Hash password with default hasher. |
| `verify_password` | `aquilia/auth/hashing.py` | `def verify_password(password_hash: str, password: str) -> bool` | Verify password with default hasher. |
| `validate_password` | `aquilia/auth/hashing.py` | `def validate_password(password: str, policy: PasswordPolicy &#124; None = None) -> tuple[bool, list[str]]` | Validate password against policy. |
| `bind_identity` | `aquilia/auth/integration/aquila_sessions.py` | `def bind_identity(session: Session, identity: Identity) -> None` | Bind identity to session. |
| `bind_token_claims` | `aquilia/auth/integration/aquila_sessions.py` | `def bind_token_claims(session: Session, claims: TokenClaims) -> None` | Bind token claims to session. |
| `get_identity_id` | `aquilia/auth/integration/aquila_sessions.py` | `def get_identity_id(session: Session) -> str &#124; None` | Get identity ID from session. |
| `get_tenant_id` | `aquilia/auth/integration/aquila_sessions.py` | `def get_tenant_id(session: Session) -> str &#124; None` | Get tenant ID from session. |
| `get_roles` | `aquilia/auth/integration/aquila_sessions.py` | `def get_roles(session: Session) -> list[str]` | Get roles from session. |
| `get_scopes` | `aquilia/auth/integration/aquila_sessions.py` | `def get_scopes(session: Session) -> list[str]` | Get scopes from session. |
| `is_mfa_verified` | `aquilia/auth/integration/aquila_sessions.py` | `def is_mfa_verified(session: Session) -> bool` | Check if MFA was verified for this session. |
| `set_mfa_verified` | `aquilia/auth/integration/aquila_sessions.py` | `def set_mfa_verified(session: Session) -> None` | Mark session as MFA verified. |
| `user_session_policy` | `aquilia/auth/integration/aquila_sessions.py` | `def user_session_policy(ttl: timedelta = timedelta(days=7), idle_timeout: timedelta = timedelta(hours=1), max_sessions: int &#124; None = 5, store_name: str = 'redis') -> SessionPolicy` | Create policy for user web sessions. |
| `api_session_policy` | `aquilia/auth/integration/aquila_sessions.py` | `def api_session_policy(ttl: timedelta = timedelta(hours=1), max_sessions: int &#124; None = None) -> SessionPolicy` | Create policy for API token sessions. |
| `device_session_policy` | `aquilia/auth/integration/aquila_sessions.py` | `def device_session_policy(ttl: timedelta = timedelta(days=90), idle_timeout: timedelta = timedelta(days=30)) -> SessionPolicy` | Create policy for device (mobile app) sessions. |
| `register_auth_providers` | `aquilia/auth/integration/di_providers.py` | `def register_auth_providers(container: Container, config: dict[str, Any] &#124; None = None) -> None` | Register all auth providers in DI container. |
| `create_auth_container` | `aquilia/auth/integration/di_providers.py` | `def create_auth_container(config: dict[str, Any] &#124; None = None, parent: Container &#124; None = None) -> Container` | Create DI container with all auth providers registered. |
| `get_session` | `aquilia/auth/integration/flow_guards.py` | `def get_session(context: Any) -> Session &#124; None` | Extract session from flow context. |
| `get_identity` | `aquilia/auth/integration/flow_guards.py` | `def get_identity(context: Any) -> Identity &#124; None` | Extract identity from flow context. |
| `set_identity` | `aquilia/auth/integration/flow_guards.py` | `def set_identity(context: Any, identity: Identity &#124; None) -> None` | Set identity in flow context. |
| `controller_require_auth` | `aquilia/auth/integration/flow_guards.py` | `def controller_require_auth(optional: bool = False) -> ControllerGuardAdapter` | Create auth guard for Controller pipeline. |
| `controller_require_scopes` | `aquilia/auth/integration/flow_guards.py` | `def controller_require_scopes(*scopes: str, require_all: bool = True) -> ControllerGuardAdapter` | Create scope guard for Controller pipeline. |
| `controller_require_roles` | `aquilia/auth/integration/flow_guards.py` | `def controller_require_roles(*roles: str, require_all: bool = True) -> ControllerGuardAdapter` | Create role guard for Controller pipeline. |
| `controller_require_permission` | `aquilia/auth/integration/flow_guards.py` | `def controller_require_permission(authz_engine: AuthzEngine, permission: str, resource: str &#124; None = None) -> ControllerGuardAdapter` | Create permission guard for Controller pipeline. |
| `require_auth` | `aquilia/auth/integration/flow_guards.py` | `def require_auth(optional: bool = False) -> FlowNode` | Create authentication guard node. |
| `require_scopes` | `aquilia/auth/integration/flow_guards.py` | `def require_scopes(*scopes: str, require_all: bool = True) -> FlowNode` | Create scope guard node. |
| `require_roles` | `aquilia/auth/integration/flow_guards.py` | `def require_roles(*roles: str, require_all: bool = True) -> FlowNode` | Create role guard node. |
| `require_permission` | `aquilia/auth/integration/flow_guards.py` | `def require_permission(authz_engine: AuthzEngine, permission: str, resource: str &#124; None = None) -> FlowNode` | Create permission guard node. |
| `create_auth_middleware_stack` | `aquilia/auth/integration/middleware.py` | `def create_auth_middleware_stack(session_engine: SessionEngine, auth_manager: AuthManager, app_container: Container, fault_engine: FaultEngine &#124; None = None, require_auth: bool = False) -> list[Middleware]` | Create complete middleware stack for authenticated app. |
| `set_auth_runtime_context` | `aquilia/auth/integration/runtime_context.py` | `def set_auth_runtime_context(context: AuthRuntimeContext) -> Token` | Set auth runtime context for current async task execution. |
| `reset_auth_runtime_context` | `aquilia/auth/integration/runtime_context.py` | `def reset_auth_runtime_context(token: Token) -> None` | Reset auth runtime context to previous value. |
| `get_auth_runtime_context` | `aquilia/auth/integration/runtime_context.py` | `def get_auth_runtime_context() -> AuthRuntimeContext &#124; None` | Get current auth runtime context, if any. |
| `Allow` | `aquilia/auth/policy/__init__.py` | `def Allow(reason: str &#124; None = None, **metadata) -> PolicyResult` | Create an Allow decision. |
| `Deny` | `aquilia/auth/policy/__init__.py` | `def Deny(reason: str &#124; None = None, **metadata) -> PolicyResult` | Create a Deny decision. |
| `Abstain` | `aquilia/auth/policy/__init__.py` | `def Abstain(reason: str &#124; None = None) -> PolicyResult` | Create an Abstain decision (defer to next rule/policy). |
| `rule` | `aquilia/auth/policy/__init__.py` | `def rule(func: Callable) -> Callable` | Decorator to mark a method as a policy rule. |

## Constants

| Name | Source | Value or type |
| --- | --- | --- |
| `_CLEARANCE_ATTR` | `aquilia/auth/clearance.py` | `'__aquilia_clearance__'` |
| `F` | `aquilia/auth/decorators.py` | `TypeVar('F', bound=Callable[..., Any])` |
| `SUPPORTED_ALGORITHMS` | `aquilia/auth/hashing.py` | `('argon2id', 'scrypt', 'bcrypt', 'pbkdf2_sha512', 'pbkdf2_sha256')` |
| `_AUTH_RUNTIME_CONTEXT` | `aquilia/auth/integration/runtime_context.py` | `ContextVar[AuthRuntimeContext &#124; None]` |
| `_HMAC_ALGORITHMS` | `aquilia/auth/tokens.py` | `frozenset[str]` |
| `_ASYMMETRIC_ALGORITHMS` | `aquilia/auth/tokens.py` | `frozenset[str]` |
| `_SUPPORTED_ALGORITHMS` | `aquilia/auth/tokens.py` | `frozenset[str]` |
| `_HMAC_DIGEST` | `aquilia/auth/tokens.py` | `dict[str, str]` |
