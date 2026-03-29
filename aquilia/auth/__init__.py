"""
AquilAuth - Authentication & Authorization System

Production-grade, Aquilia-native auth system with:
- Multiple authentication methods (password, API key, OAuth2, MFA, passwordless)
- Authorization engine (RBAC, ABAC, policy DSL)
- Token management with key rotation
- Deep integration with Sessions, DI, Flow, Faults

Design Philosophy:
1. Manifest-first: Auth config declared in manifests, compiled to crous
2. Least privilege: Default-deny for all protected resources
3. Typed & explicit: No ambient authority, everything injected
4. Composable guards: Auth/authz are Flow pipeline nodes
5. Audited & testable: All sensitive operations emit audit events
6. Separation of concerns: Clear boundaries between components

Status: Core implementation complete, ready for integration testing.
"""

# Core types
# Audit Trail
from .audit import (
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    AuditStore,
    AuditTrail,
    LoggingAuditStore,
    MemoryAuditStore,
)

# Authorization engines
from .authz import ABACEngine, AuthzEngine, RBACEngine

# Clearance System (Unique Aquilia access control)
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
    # Built-in conditions
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
from .decorators import AdminGuard, VerifiedEmailGuard, authenticated

# Faults
from .faults import (
    AUTH_ACCOUNT_LOCKED,
    AUTH_ACCOUNT_SUSPENDED,
    AUTH_BACKUP_CODE_EXHAUSTED,
    AUTH_BACKUP_CODE_INVALID,
    AUTH_CLIENT_INVALID,
    # OAuth faults
    AUTH_CONSENT_REQUIRED,
    AUTH_DEVICE_CODE_EXPIRED,
    AUTH_DEVICE_CODE_PENDING,
    AUTH_GRANT_INVALID,
    # Authentication faults
    AUTH_INVALID_CREDENTIALS,
    AUTH_KEY_EXPIRED,
    AUTH_KEY_REVOKED,
    AUTH_MFA_ALREADY_ENROLLED,
    AUTH_MFA_INVALID,
    # MFA faults
    AUTH_MFA_NOT_ENROLLED,
    AUTH_MFA_REQUIRED,
    AUTH_PASSWORD_BREACHED,
    AUTH_PASSWORD_REUSED,
    # Credential faults
    AUTH_PASSWORD_WEAK,
    AUTH_PKCE_INVALID,
    AUTH_RATE_LIMITED,
    AUTH_REDIRECT_URI_MISMATCH,
    AUTH_REQUIRED,
    AUTH_SCOPE_INVALID,
    AUTH_SESSION_HIJACK_DETECTED,
    AUTH_SESSION_INVALID,
    # Session faults
    AUTH_SESSION_REQUIRED,
    AUTH_SLOW_DOWN,
    AUTH_TOKEN_EXPIRED,
    AUTH_TOKEN_INVALID,
    AUTH_TOKEN_REVOKED,
    AUTH_WEBAUTHN_INVALID,
    AUTHZ_INSUFFICIENT_ROLE,
    AUTHZ_INSUFFICIENT_SCOPE,
    # Authorization faults
    AUTHZ_POLICY_DENIED,
    AUTHZ_RESOURCE_FORBIDDEN,
    AUTHZ_TENANT_MISMATCH,
)

# Security Hardening
from .hardening import (
    CSRFProtection,
    RequestFingerprint,
    SecurityHeaders,
    TokenBinder,
    constant_time_compare,
    generate_opaque_id,
    generate_secure_token,
    hash_sensitive,
    hash_token,
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

# Manager
from .manager import AuthManager, RateLimiter, SignInProvisionPolicy

# MFA
from .mfa import MFAManager

# OAuth2
from .oauth import OAuth2Manager

# Policy DSL
from .policy import (
    Abstain,
    Allow,
    Deny,
    Policy,
    PolicyDecision,
    PolicyRegistry,
    PolicyResult,
    rule,
)

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
    "authenticated",
    "AdminGuard",
    "VerifiedEmailGuard",
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
    # Manager
    "AuthManager",
    "RateLimiter",
    "SignInProvisionPolicy",
    # Authorization
    "AuthzEngine",
    "RBACEngine",
    "ABACEngine",
    # Policy DSL
    "Policy",
    "PolicyResult",
    "PolicyDecision",
    "PolicyRegistry",
    "Allow",
    "Deny",
    "Abstain",
    "rule",
    # OAuth2
    "OAuth2Manager",
    # MFA
    "MFAManager",
    # Stores
    "MemoryIdentityStore",
    "MemoryCredentialStore",
    "MemoryTokenStore",
    # Clearance System
    "AccessLevel",
    "Clearance",
    "ClearanceVerdict",
    "ClearanceEngine",
    "ClearanceGuard",
    "grant",
    "exempt",
    "is_verified",
    "is_owner_or_admin",
    "within_quota",
    "is_same_tenant",
    "during_hours",
    "require_attribute",
    "ip_allowlist",
    # Audit Trail
    "AuditEventType",
    "AuditSeverity",
    "AuditEvent",
    "AuditStore",
    "MemoryAuditStore",
    "LoggingAuditStore",
    "AuditTrail",
    # Security Hardening
    "constant_time_compare",
    "CSRFProtection",
    "RequestFingerprint",
    "SecurityHeaders",
    "TokenBinder",
    "generate_secure_token",
    "generate_opaque_id",
    "hash_token",
    "hash_sensitive",
]


from aquilia._version import __version__  # noqa: F401 — re-exported
