# auth Module

## Purpose

Authentication, authorization, clearance, token, and MFA system. Use this module for identities, credentials, JWT and refresh token lifecycles, guards, policy checks, audit trails, OAuth, MFA, API keys, CSRF, and request hardening.

## Source Coverage

- Python files: 24
- Public classes: 164
- Dataclasses: 25
- Enums: 10
- Public functions: 61

## How It Fits In Aquilia

1. Create identities and credentials in stores, or let AuthManager provision during development sign in.
2. Issue access and refresh tokens through TokenManager and AuthManager.
3. Protect handlers with authenticated, requires, AdminGuard, VerifiedEmailGuard, clearance grants, or flow guards.

## Practical Guidance

- Production disables implicit username bootstrap through secure defaults. Seed identities and credentials explicitly for deployed systems.
- Do not log raw tokens, API keys, password hashes, or Secret.reveal output.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `AuditEventType` | `aquilia/auth/audit.py` | Categories of security events. |
| `AuditSeverity` | `aquilia/auth/audit.py` | Severity levels for audit events. |
| `AuditEvent` | `aquilia/auth/audit.py` | Structured security audit event. |
| `AuditStore` | `aquilia/auth/audit.py` | Base class for audit event storage. |
| `MemoryAuditStore` | `aquilia/auth/audit.py` | In-memory audit store for development/testing. |
| `LoggingAuditStore` | `aquilia/auth/audit.py` | Audit store that logs to Python logging framework. |
| `AuditTrail` | `aquilia/auth/audit.py` | Central audit trail for security events. |
| `Decision` | `aquilia/auth/authz.py` | Authorization decision. |
| `AuthzContext` | `aquilia/auth/authz.py` | Authorization context for policy evaluation. |
| `AuthzResult` | `aquilia/auth/authz.py` | Authorization result. |
| `RBACEngine` | `aquilia/auth/authz.py` | Role-Based Access Control engine. |
| `ABACEngine` | `aquilia/auth/authz.py` | Attribute-Based Access Control engine. |
| `ScopeChecker` | `aquilia/auth/authz.py` | OAuth2-style scope checking. |
| `AuthzEngine` | `aquilia/auth/authz.py` | Unified authorization engine. |
| `PolicyBuilder` | `aquilia/auth/authz.py` | Helper for building common authorization policies. |
| `AccessLevel` | `aquilia/auth/clearance.py` | Hierarchical access tiers -- higher ordinal = stricter. |
| `ClearanceCondition` | `aquilia/auth/clearance.py` | A callable predicate evaluated at request time. |
| `Clearance` | `aquilia/auth/clearance.py` | Immutable clearance requirement descriptor. |
| `ClearanceVerdict` | `aquilia/auth/clearance.py` | Result of a clearance evaluation. |
| `ClearanceEngine` | `aquilia/auth/clearance.py` | Evaluates clearance requirements against request context. |
| `ClearanceGuard` | `aquilia/auth/clearance.py` | Pipeline guard that enforces Clearance requirements. |
| `IdentityType` | `aquilia/auth/core.py` | Type of authenticated principal. |
| `IdentityStatus` | `aquilia/auth/core.py` | Identity status. |
| `Identity` | `aquilia/auth/core.py` | Authenticated principal (user or service). |
| `CredentialStatus` | `aquilia/auth/core.py` | Credential status. |
| `Credential` | `aquilia/auth/core.py` | Base protocol for credentials. |
| `PasswordCredential` | `aquilia/auth/core.py` | Password-based credential. |
| `ApiKeyCredential` | `aquilia/auth/core.py` | API key credential (long-lived). |
| `OAuthClient` | `aquilia/auth/core.py` | OAuth2/OIDC client. |
| `MFACredential` | `aquilia/auth/core.py` | Multi-factor authentication credential. |
| `TokenClaims` | `aquilia/auth/core.py` | Access token claims (JWT payload). |
| `AuthResult` | `aquilia/auth/core.py` | Result of authentication operation. |
| `IdentityStore` | `aquilia/auth/core.py` | Protocol for identity storage. |
| `CredentialStore` | `aquilia/auth/core.py` | Protocol for credential storage. |
| `OAuthClientStore` | `aquilia/auth/core.py` | Protocol for OAuth client storage. |
| `CrousArtifact` | `aquilia/auth/crous.py` | Base crous artifact. |
| `KeyArtifact` | `aquilia/auth/crous.py` | Cryptographic key artifact. |
| `PolicyArtifact` | `aquilia/auth/crous.py` | Authorization policy artifact. |
| `AuditEventArtifact` | `aquilia/auth/crous.py` | Audit event artifact. |
| `ArtifactSigner` | `aquilia/auth/crous.py` | Signs and verifies crous artifacts. |
| `MemoryArtifactStore` | `aquilia/auth/crous.py` | In-memory artifact store for development/testing. |
| `AuditLogger` | `aquilia/auth/crous.py` | Audit event logger with crous artifact integration. |
| `AuthorizationRequiredFault` | `aquilia/auth/decorators.py` | Raised when authorization check fails. |
| `AuthGuard` | `aquilia/auth/decorators.py` | Base class for authentication/authorization guards. |
| `AdminGuard` | `aquilia/auth/decorators.py` | Guard that requires admin role. |
| `VerifiedEmailGuard` | `aquilia/auth/decorators.py` | Guard that requires verified email. |
| `RoleGuard` | `aquilia/auth/decorators.py` | Guard that requires specific role(s). |
| `ScopeGuard` | `aquilia/auth/decorators.py` | Guard that requires specific scope(s). |
| `AUTH_INVALID_CREDENTIALS` | `aquilia/auth/faults.py` | Invalid username or password. |
| `AUTH_TOKEN_INVALID` | `aquilia/auth/faults.py` | Invalid or malformed token. |
| `AUTH_TOKEN_EXPIRED` | `aquilia/auth/faults.py` | Access token has expired. |
| `AUTH_TOKEN_REVOKED` | `aquilia/auth/faults.py` | Token has been revoked. |
| `AUTH_MFA_REQUIRED` | `aquilia/auth/faults.py` | Multi-factor authentication required. |
| `AUTH_MFA_INVALID` | `aquilia/auth/faults.py` | Invalid MFA code. |
| `AUTH_ACCOUNT_SUSPENDED` | `aquilia/auth/faults.py` | Account is suspended. |
| `AUTH_ACCOUNT_LOCKED` | `aquilia/auth/faults.py` | Account is locked due to failed login attempts. |
| `AUTH_RATE_LIMITED` | `aquilia/auth/faults.py` | Too many authentication attempts. |
| `AUTH_REQUIRED` | `aquilia/auth/faults.py` | Authentication required but not provided. |
| `AUTH_CLIENT_INVALID` | `aquilia/auth/faults.py` | Invalid OAuth client credentials. |
| `AUTH_GRANT_INVALID` | `aquilia/auth/faults.py` | Invalid OAuth grant (code, refresh token, etc.). |
| `AUTH_REDIRECT_URI_MISMATCH` | `aquilia/auth/faults.py` | OAuth redirect URI doesn't match registered URI. |
| `AUTH_SCOPE_INVALID` | `aquilia/auth/faults.py` | Requested scope is invalid or not allowed. |
| `AUTH_PKCE_INVALID` | `aquilia/auth/faults.py` | PKCE code verifier doesn't match challenge. |
| `AUTHZ_POLICY_DENIED` | `aquilia/auth/faults.py` | Authorization policy denied access. |
| `AUTHZ_INSUFFICIENT_SCOPE` | `aquilia/auth/faults.py` | Token missing required scopes. |
| `AUTHZ_INSUFFICIENT_ROLE` | `aquilia/auth/faults.py` | Identity missing required role. |
| `AUTHZ_RESOURCE_FORBIDDEN` | `aquilia/auth/faults.py` | Access to resource is forbidden. |
| `AUTHZ_TENANT_MISMATCH` | `aquilia/auth/faults.py` | Identity tenant doesn't match resource tenant. |
| `AUTH_PASSWORD_WEAK` | `aquilia/auth/faults.py` | Password doesn't meet policy requirements. |
| `AUTH_PASSWORD_BREACHED` | `aquilia/auth/faults.py` | Password found in breach database. |
| `AUTH_PASSWORD_REUSED` | `aquilia/auth/faults.py` | Password was recently used. |
| `AUTH_KEY_EXPIRED` | `aquilia/auth/faults.py` | API key has expired. |
| `AUTH_KEY_REVOKED` | `aquilia/auth/faults.py` | API key has been revoked. |
| `AUTH_SESSION_REQUIRED` | `aquilia/auth/faults.py` | Session required but not found. |
| `AUTH_SESSION_INVALID` | `aquilia/auth/faults.py` | Session is invalid or corrupted. |
| `AUTH_SESSION_HIJACK_DETECTED` | `aquilia/auth/faults.py` | Potential session hijacking detected. |
| `AUTH_CONSENT_REQUIRED` | `aquilia/auth/faults.py` | User consent required for OAuth flow. |
| `AUTH_DEVICE_CODE_PENDING` | `aquilia/auth/faults.py` | Device code authorization pending. |
| `AUTH_DEVICE_CODE_EXPIRED` | `aquilia/auth/faults.py` | Device code has expired. |
| `AUTH_SLOW_DOWN` | `aquilia/auth/faults.py` | Device flow polling too fast. |

Only the first 80 classes are shown here. See the file inventory for the rest of the package.

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `is_verified` | `aquilia/auth/clearance.py` | Condition: identity must have 'verified' attribute or status ACTIVE. |
| `is_owner_or_admin` | `aquilia/auth/clearance.py` | Condition: identity is resource owner or has admin role. |
| `within_quota` | `aquilia/auth/clearance.py` | Condition: identity hasn't exceeded rate/resource quota. |
| `is_same_tenant` | `aquilia/auth/clearance.py` | Condition: identity's tenant matches resource tenant. |
| `during_hours` | `aquilia/auth/clearance.py` | Factory: condition that restricts access to business hours (UTC). |
| `require_attribute` | `aquilia/auth/clearance.py` | Factory: condition that requires a specific identity attribute. |
| `ip_allowlist` | `aquilia/auth/clearance.py` | Factory: condition restricting access to specific IP ranges. |
| `grant` | `aquilia/auth/clearance.py` | Decorator to attach clearance requirements to a route method. |
| `exempt` | `aquilia/auth/clearance.py` | Decorator to exempt a route from class-level clearance. |
| `get_method_clearance` | `aquilia/auth/clearance.py` | Extract clearance from a decorated method. |
| `extract_controller_clearance` | `aquilia/auth/clearance.py` | Extract clearance from controller class. |
| `build_merged_clearance` | `aquilia/auth/clearance.py` | Build merged clearance from class + method. |
| `authenticated` | `aquilia/auth/decorators.py` | Decorator requiring authenticated identity. |
| `require_identity` | `aquilia/auth/decorators.py` | Decorator requiring identity with specific attributes. |
| `requires` | `aquilia/auth/decorators.py` | Decorator to require multiple guards. |
| `raise_auth_fault` | `aquilia/auth/faults.py` | Raise an auth fault with context. |
| `is_auth_fault` | `aquilia/auth/faults.py` | Check if exception is an auth fault. |
| `require_auth` | `aquilia/auth/guards.py` | Decorator: Require authentication. |
| `require_scopes` | `aquilia/auth/guards.py` | Decorator: Require OAuth scopes. |
| `require_roles` | `aquilia/auth/guards.py` | Decorator: Require roles. |
| `constant_time_compare` | `aquilia/auth/hardening.py` | Compare two strings/bytes in constant time to prevent timing attacks. |
| `generate_secure_token` | `aquilia/auth/hardening.py` | Generate a cryptographically secure random token. |
| `generate_opaque_id` | `aquilia/auth/hardening.py` | Generate an opaque identifier with prefix. |
| `hash_token` | `aquilia/auth/hardening.py` | Hash a token for storage (one-way). |
| `hash_sensitive` | `aquilia/auth/hardening.py` | Hash sensitive data with optional salt. |
| `get_password_hasher` | `aquilia/auth/hashing.py` | Get default password hasher instance. |
| `hash_password` | `aquilia/auth/hashing.py` | Hash password with default hasher. |
| `verify_password` | `aquilia/auth/hashing.py` | Verify password with default hasher. |
| `validate_password` | `aquilia/auth/hashing.py` | Validate password against policy. |
| `bind_identity` | `aquilia/auth/integration/aquila_sessions.py` | Bind identity to session. |
| `bind_token_claims` | `aquilia/auth/integration/aquila_sessions.py` | Bind token claims to session. |
| `get_identity_id` | `aquilia/auth/integration/aquila_sessions.py` | Get identity ID from session. |
| `get_tenant_id` | `aquilia/auth/integration/aquila_sessions.py` | Get tenant ID from session. |
| `get_roles` | `aquilia/auth/integration/aquila_sessions.py` | Get roles from session. |
| `get_scopes` | `aquilia/auth/integration/aquila_sessions.py` | Get scopes from session. |
| `is_mfa_verified` | `aquilia/auth/integration/aquila_sessions.py` | Check if MFA was verified for this session. |
| `set_mfa_verified` | `aquilia/auth/integration/aquila_sessions.py` | Mark session as MFA verified. |
| `user_session_policy` | `aquilia/auth/integration/aquila_sessions.py` | Create policy for user web sessions. |
| `api_session_policy` | `aquilia/auth/integration/aquila_sessions.py` | Create policy for API token sessions. |
| `device_session_policy` | `aquilia/auth/integration/aquila_sessions.py` | Create policy for device (mobile app) sessions. |
| `register_auth_providers` | `aquilia/auth/integration/di_providers.py` | Register all auth providers in DI container. |
| `create_auth_container` | `aquilia/auth/integration/di_providers.py` | Create DI container with all auth providers registered. |
| `get_session` | `aquilia/auth/integration/flow_guards.py` | Extract session from flow context. |
| `get_identity` | `aquilia/auth/integration/flow_guards.py` | Extract identity from flow context. |
| `set_identity` | `aquilia/auth/integration/flow_guards.py` | Set identity in flow context. |
| `controller_require_auth` | `aquilia/auth/integration/flow_guards.py` | Create auth guard for Controller pipeline. |
| `controller_require_scopes` | `aquilia/auth/integration/flow_guards.py` | Create scope guard for Controller pipeline. |
| `controller_require_roles` | `aquilia/auth/integration/flow_guards.py` | Create role guard for Controller pipeline. |
| `controller_require_permission` | `aquilia/auth/integration/flow_guards.py` | Create permission guard for Controller pipeline. |
| `require_auth` | `aquilia/auth/integration/flow_guards.py` | Create authentication guard node. |
| `require_scopes` | `aquilia/auth/integration/flow_guards.py` | Create scope guard node. |
| `require_roles` | `aquilia/auth/integration/flow_guards.py` | Create role guard node. |
| `require_permission` | `aquilia/auth/integration/flow_guards.py` | Create permission guard node. |
| `create_auth_middleware_stack` | `aquilia/auth/integration/middleware.py` | Create complete middleware stack for authenticated app. |
| `set_auth_runtime_context` | `aquilia/auth/integration/runtime_context.py` | Set auth runtime context for current async task execution. |
| `reset_auth_runtime_context` | `aquilia/auth/integration/runtime_context.py` | Reset auth runtime context to previous value. |
| `get_auth_runtime_context` | `aquilia/auth/integration/runtime_context.py` | Get current auth runtime context, if any. |
| `Allow` | `aquilia/auth/policy/__init__.py` | Create an Allow decision. |
| `Deny` | `aquilia/auth/policy/__init__.py` | Create a Deny decision. |
| `Abstain` | `aquilia/auth/policy/__init__.py` | Create an Abstain decision (defer to next rule/policy). |
| `rule` | `aquilia/auth/policy/__init__.py` | Decorator to mark a method as a policy rule. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/auth/__init__.py` | AquilAuth - Authentication & Authorization System |
| `aquilia/auth/audit.py` | AquilAuth - Security Audit Trail |
| `aquilia/auth/authz.py` | AquilAuth - Authorization Engine |
| `aquilia/auth/clearance.py` | Aquilia Clearance System -- Unique declarative access control. |
| `aquilia/auth/core.py` | AquilAuth - Core Types |
| `aquilia/auth/crous.py` | AquilAuth - Crous Artifacts |
| `aquilia/auth/decorators.py` | AquilAuth - Authentication Decorators and Guards. |
| `aquilia/auth/faults.py` | AquilAuth - Authentication/Authorization Faults |
| `aquilia/auth/guards.py` | AquilAuth - Guards and Flow Integration |
| `aquilia/auth/hardening.py` | AquilAuth - Security Hardening Utilities |
| `aquilia/auth/hashing.py` | AquilAuth - Password Hashing |
| `aquilia/auth/integration/__init__.py` | AquilAuth - Integration package. |
| `aquilia/auth/integration/aquila_sessions.py` | AquilAuth - Aquilia Sessions Integration |
| `aquilia/auth/integration/di_providers.py` | AquilAuth - DI Providers |
| `aquilia/auth/integration/flow_guards.py` | AquilAuth - Flow & Controller Guards (Deep Integration) |
| `aquilia/auth/integration/middleware.py` | AquilAuth - Unified Middleware |
| `aquilia/auth/integration/runtime_context.py` | AquilAuth runtime context bridge. |
| `aquilia/auth/integration/sessions.py` | AquilAuth - Session Integration |
| `aquilia/auth/manager.py` | AquilAuth - Authentication Manager |
| `aquilia/auth/mfa.py` | AquilAuth - MFA Providers |
| `aquilia/auth/oauth.py` | AquilAuth - OAuth2/OIDC Flows |
| `aquilia/auth/policy/__init__.py` | AquilAuth - Policy DSL Module |
| `aquilia/auth/stores.py` | AquilAuth - Credential and Token Stores |
| `aquilia/auth/tokens.py` | AquilAuth - Token Management |

## Testing Pointers

Search `tests/` for `auth` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
