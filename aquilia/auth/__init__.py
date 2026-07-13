"""
AquilAuth - Production-grade Authentication & Authorization System

Core Principles:
1. **Context-first** — identity is resolved once per request and passed explicitly.
2. **Pluggable backends** — single-responsibility handlers authenticate credentials.
3. **Typed & explicit** — no ambient authority; everything is injected.
4. **Composable guards** — auth/authz guards stack as pipeline nodes.
5. **Audited & testable** — all sensitive operations emit audit events.
6. **Separation of concerns** — clear boundaries between components.
"""

from __future__ import annotations

# Core types
from .audit import (
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    AuditStore,
    AuditTrail,
    LoggingAuditStore,
    MemoryAuditStore,
)

# Authorization engines (legacy — use PermissionEngine for new code)
from .authz import ABACEngine, AuthzEngine, RBACEngine

# Pluggable backends (new, strategy-free)
from .backends import (
    ApiKeyBackend,
    AuthBackend,
    PasswordBackend,
    SessionBackend,
    TokenBackend,
    resolve_backend,
)

# Clearance System
from .clearance import (
    AccessLevel,
    Clearance,
    ClearanceEngine,
    ClearanceGuard,
    ClearanceVerdict,
    during_hours,
    exempt,
    grant,
    ip_allowlist,
    is_owner_or_admin,
    is_same_tenant,
    is_verified,
    require_attribute,
    within_quota,
)
from .core import (
    ApiKeyCredential,
    AuthResult,
    Credential,
    CredentialStatus,
    CredentialStore,
    Identity,
    IdentityStatus,
    IdentityStore,
    IdentityType,
    MFACredential,
    OAuthClient,
    OAuthClientStore,
    PasswordCredential,
    TokenClaims,
)

# New decorators
from .decorators import (
    authenticated,
    optional_auth,
    roles_required,
    scopes_required,
)

# Faults
from .faults import (
    AUTH_ACCOUNT_LOCKED,
    AUTH_ACCOUNT_SUSPENDED,
    AUTH_BACKUP_CODE_EXHAUSTED,
    AUTH_BACKUP_CODE_INVALID,
    AUTH_CLIENT_INVALID,
    AUTH_CONSENT_REQUIRED,
    AUTH_DEVICE_CODE_EXPIRED,
    AUTH_DEVICE_CODE_PENDING,
    AUTH_GRANT_INVALID,
    AUTH_INVALID_CREDENTIALS,
    AUTH_KEY_EXPIRED,
    AUTH_KEY_REVOKED,
    AUTH_MFA_ALREADY_ENROLLED,
    AUTH_MFA_INVALID,
    AUTH_MFA_NOT_ENROLLED,
    AUTH_MFA_REQUIRED,
    AUTH_PASSWORD_BREACHED,
    AUTH_PASSWORD_REUSED,
    AUTH_PASSWORD_WEAK,
    AUTH_PKCE_INVALID,
    AUTH_RATE_LIMITED,
    AUTH_REDIRECT_URI_MISMATCH,
    AUTH_REQUIRED,
    AUTH_SCOPE_INVALID,
    AUTH_SESSION_HIJACK_DETECTED,
    AUTH_SESSION_INVALID,
    AUTH_SESSION_REQUIRED,
    AUTH_SLOW_DOWN,
    AUTH_TOKEN_EXPIRED,
    AUTH_TOKEN_INVALID,
    AUTH_TOKEN_REVOKED,
    AUTH_WEBAUTHN_INVALID,
    AUTHZ_INSUFFICIENT_ROLE,
    AUTHZ_INSUFFICIENT_SCOPE,
    AUTHZ_POLICY_DENIED,
    AUTHZ_RESOURCE_FORBIDDEN,
    AUTHZ_TENANT_MISMATCH,
)

# New guard system
from .guards import (
    AuthGuard,
    Guard,
    PolicyGuard,
    RoleGuard,
    ScopeGuard,
    requires,
)

# Password hashing
from .hashing import (
    HasherConfig,
    PasswordHasher,
    PasswordPolicy,
    hash_password,
    validate_password,
    verify_password,
)

# Manager types
from .manager import AuthManager, RateLimiter, SignInProvisionPolicy

# MFA
from .mfa import MFAManager

# New authentication middleware
from .middleware import AuthMiddleware

# OAuth2
from .oauth import OAuth2Manager

# New unified permission engine
from .permissions import PermissionEngine

# Stores
from .stores import (
    MemoryCredentialStore,
    MemoryIdentityStore,
    MemoryTokenStore,
)

# Token management
from .tokens import (
    KeyAlgorithm,
    KeyDescriptor,
    KeyRing,
    KeyStatus,
    TokenConfig,
    TokenManager,
    TokenStore,
    constant_time_compare,
    generate_opaque_id,
    generate_secure_token,
    hash_sensitive,
    hash_token,
)

__all__ = [
    # Core types
    "Identity",
    "IdentityType",
    "IdentityStatus",
    "IdentityStore",
    "Credential",
    "CredentialStatus",
    "CredentialStore",
    "PasswordCredential",
    "ApiKeyCredential",
    "OAuthClient",
    "OAuthClientStore",
    "MFACredential",
    "TokenClaims",
    "AuthResult",
    # Password hashing
    "PasswordHasher",
    "PasswordPolicy",
    "HasherConfig",
    "hash_password",
    "verify_password",
    "validate_password",
    # Token management
    "KeyDescriptor",
    "KeyRing",
    "KeyAlgorithm",
    "KeyStatus",
    "TokenManager",
    "TokenConfig",
    "TokenStore",
    # Backends
    "AuthBackend",
    "PasswordBackend",
    "TokenBackend",
    "ApiKeyBackend",
    "SessionBackend",
    "resolve_backend",
    # Permissions
    "PermissionEngine",
    # Guards
    "Guard",
    "AuthGuard",
    "RoleGuard",
    "ScopeGuard",
    "PolicyGuard",
    "requires",
    # Decorators
    "authenticated",
    "optional_auth",
    "roles_required",
    "scopes_required",
    # Middleware
    "AuthMiddleware",
    # Manager
    "AuthManager",
    "RateLimiter",
    "SignInProvisionPolicy",
    # Authorization engines
    "AuthzEngine",
    "RBACEngine",
    "ABACEngine",
    # OAuth2
    "OAuth2Manager",
    # MFA
    "MFAManager",
    # Clearance System
    "Clearance",
    "ClearanceEngine",
    "ClearanceGuard",
    "ClearanceVerdict",
    "AccessLevel",
    "ip_allowlist",
    "during_hours",
    "is_same_tenant",
    "is_owner_or_admin",
    "exempt",
    "grant",
    "is_verified",
    "require_attribute",
    "within_quota",
    # Stores
    "MemoryIdentityStore",
    "MemoryCredentialStore",
    "MemoryTokenStore",
    # Audit Trail
    "AuditEvent",
    "AuditEventType",
    "AuditSeverity",
    "AuditTrail",
    "AuditStore",
    "MemoryAuditStore",
    "LoggingAuditStore",
    # Faults
    "AUTH_INVALID_CREDENTIALS",
    "AUTH_TOKEN_INVALID",
    "AUTH_TOKEN_EXPIRED",
    "AUTH_TOKEN_REVOKED",
    "AUTH_MFA_REQUIRED",
    "AUTH_MFA_INVALID",
    "AUTH_ACCOUNT_SUSPENDED",
    "AUTH_ACCOUNT_LOCKED",
    "AUTH_RATE_LIMITED",
    "AUTH_REQUIRED",
    "AUTH_CLIENT_INVALID",
    "AUTH_GRANT_INVALID",
    "AUTH_REDIRECT_URI_MISMATCH",
    "AUTH_SCOPE_INVALID",
    "AUTH_PKCE_INVALID",
    "AUTHZ_POLICY_DENIED",
    "AUTHZ_INSUFFICIENT_SCOPE",
    "AUTHZ_INSUFFICIENT_ROLE",
    "AUTHZ_RESOURCE_FORBIDDEN",
    "AUTHZ_TENANT_MISMATCH",
    "AUTH_PASSWORD_WEAK",
    "AUTH_PASSWORD_BREACHED",
    "AUTH_PASSWORD_REUSED",
    "AUTH_KEY_EXPIRED",
    "AUTH_KEY_REVOKED",
    "AUTH_SESSION_REQUIRED",
    "AUTH_SESSION_INVALID",
    "AUTH_SESSION_HIJACK_DETECTED",
    "AUTH_CONSENT_REQUIRED",
    "AUTH_DEVICE_CODE_PENDING",
    "AUTH_DEVICE_CODE_EXPIRED",
    "AUTH_SLOW_DOWN",
    "AUTH_MFA_NOT_ENROLLED",
    "AUTH_MFA_ALREADY_ENROLLED",
    "AUTH_WEBAUTHN_INVALID",
    "AUTH_BACKUP_CODE_INVALID",
    "AUTH_BACKUP_CODE_EXHAUSTED",
    # Utility functions
    "constant_time_compare",
    "generate_secure_token",
    "generate_opaque_id",
    "hash_token",
    "hash_sensitive",
]

from aquilia._version import __version__  # noqa: F401 — re-exported
