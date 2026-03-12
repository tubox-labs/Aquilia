"""
AquilAdmin -- Structured Faults for Admin System.

All admin errors use Aquilia's Fault system for structured,
typed, recoverable error handling.

Fault Hierarchy:
    AdminFault (base)
    ├── AdminAuthenticationFault     (401 -- login failures)
    ├── AdminAuthorizationFault      (403 -- permission denied)
    ├── AdminCSRFViolationFault      (403 -- CSRF token invalid/missing)
    ├── AdminRateLimitFault          (429 -- too many attempts)
    ├── AdminModelNotFoundFault      (404 -- model not in registry)
    ├── AdminRecordNotFoundFault     (404 -- DB record missing)
    ├── AdminValidationFault         (422 -- form/field validation)
    ├── AdminActionFault             (400 -- bulk action failure)
    ├── AdminConfigurationFault      (500 -- missing dependency/misconfiguration)
    ├── AdminRegistrationFault       (500 -- model registration error)
    ├── AdminInlineFault             (400 -- inline FK resolution error)
    ├── AdminTemplateFault           (500 -- template rendering error)
    ├── AdminExportFault             (500 -- export generation error)
    └── AdminSecurityFault           (403 -- generic security violation)
"""

from __future__ import annotations

from typing import Any

from aquilia.faults import Fault
from aquilia.faults.core import FaultDomain

# Custom fault domain for admin subsystem
ADMIN_DOMAIN = FaultDomain.custom("ADMIN", "Admin dashboard faults")


# ═══════════════════════════════════════════════════════════════════════════════
#  Base Admin Fault
# ═══════════════════════════════════════════════════════════════════════════════


class AdminFault(Fault):
    """Base fault for all admin operations."""

    domain = ADMIN_DOMAIN


# ═══════════════════════════════════════════════════════════════════════════════
#  Authentication / Authorization Faults
# ═══════════════════════════════════════════════════════════════════════════════


class AdminAuthenticationFault(AdminFault):
    """Admin authentication failed."""

    code = "ADMIN_AUTH_FAILED"
    status = 401

    def __init__(self, reason: str = "Invalid credentials"):
        super().__init__(
            message=f"Admin authentication failed: {reason}",
            code=self.code,
            status=self.status,
        )
        self.reason = reason


class AdminAuthorizationFault(AdminFault):
    """Admin authorization failed -- insufficient permissions."""

    code = "ADMIN_AUTHZ_DENIED"
    status = 403

    def __init__(self, action: str = "", resource: str = ""):
        msg = "Admin access denied"
        if action and resource:
            msg = f"Permission denied: cannot {action} on {resource}"
        elif action:
            msg = f"Permission denied: {action}"
        super().__init__(
            message=msg,
            code=self.code,
            status=self.status,
        )
        self.action = action
        self.resource = resource


# ═══════════════════════════════════════════════════════════════════════════════
#  Security Faults (CSRF, Rate Limit, Generic Security)
# ═══════════════════════════════════════════════════════════════════════════════


class AdminSecurityFault(AdminFault):
    """Base fault for admin security violations."""

    code = "ADMIN_SECURITY_ERROR"
    status = 403

    def __init__(self, reason: str = "Security violation", **metadata: Any):
        super().__init__(
            message=f"Admin security error: {reason}",
            code=self.code,
            status=self.status,
        )
        self.reason = reason
        self.metadata: dict[str, Any] = metadata


class AdminCSRFViolationFault(AdminSecurityFault):
    """
    CSRF token validation failed.

    Raised when a POST/PUT/DELETE request to an admin endpoint
    has a missing, expired, or invalid CSRF token.
    """

    code = "ADMIN_CSRF_VIOLATION"
    status = 403

    def __init__(self, reason: str = "CSRF token validation failed"):
        super().__init__(reason=reason)


class AdminRateLimitFault(AdminSecurityFault):
    """
    Rate limit exceeded for admin operation.

    Raised when login attempts or sensitive operations exceed
    the configured rate limit thresholds.
    """

    code = "ADMIN_RATE_LIMIT"
    status = 429

    def __init__(
        self,
        *,
        limit: int = 0,
        window: int = 0,
        retry_after: int = 0,
        operation: str = "login",
    ):
        msg = f"Rate limit exceeded for {operation}"
        if retry_after > 0:
            msg += f" (retry after {retry_after}s)"
        super().__init__(reason=msg)
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        self.operation = operation


# ═══════════════════════════════════════════════════════════════════════════════
#  Model / Record Faults
# ═══════════════════════════════════════════════════════════════════════════════


class AdminModelNotFoundFault(AdminFault):
    """Requested model is not registered with admin."""

    code = "ADMIN_MODEL_NOT_FOUND"
    status = 404

    def __init__(self, model_name: str = ""):
        super().__init__(
            message=f"Model not found in admin: {model_name}" if model_name else "Model not found in admin",
            code=self.code,
            status=self.status,
        )
        self.model_name = model_name


class AdminRecordNotFoundFault(AdminFault):
    """Record not found in database."""

    code = "ADMIN_RECORD_NOT_FOUND"
    status = 404

    def __init__(self, model_name: str = "", pk: str = ""):
        msg = "Record not found"
        if model_name and pk:
            msg = f"{model_name} with pk={pk} not found"
        super().__init__(
            message=msg,
            code=self.code,
            status=self.status,
        )
        self.model_name = model_name
        self.pk = pk


# ═══════════════════════════════════════════════════════════════════════════════
#  Validation Faults
# ═══════════════════════════════════════════════════════════════════════════════


class AdminValidationFault(AdminFault):
    """Validation error when creating/updating records."""

    code = "ADMIN_VALIDATION_ERROR"
    status = 422

    def __init__(self, errors: dict | list | str = "Validation failed"):
        if isinstance(errors, dict):
            msg = "; ".join(f"{k}: {v}" for k, v in errors.items())
        elif isinstance(errors, list):
            msg = "; ".join(str(e) for e in errors)
        else:
            msg = str(errors)
        super().__init__(
            message=f"Validation error: {msg}",
            code=self.code,
            status=self.status,
        )
        self.errors = errors


# ═══════════════════════════════════════════════════════════════════════════════
#  Action Faults
# ═══════════════════════════════════════════════════════════════════════════════


class AdminActionFault(AdminFault):
    """Bulk action execution failed."""

    code = "ADMIN_ACTION_FAILED"
    status = 400

    def __init__(self, action_name: str = "", reason: str = ""):
        msg = f"Action '{action_name}' failed" if action_name else "Action failed"
        if reason:
            msg += f": {reason}"
        super().__init__(
            message=msg,
            code=self.code,
            status=self.status,
        )
        self.action_name = action_name
        self.reason = reason


# ═══════════════════════════════════════════════════════════════════════════════
#  Configuration Faults
# ═══════════════════════════════════════════════════════════════════════════════


class AdminConfigurationFault(AdminFault):
    """
    Admin system misconfiguration or missing dependency.

    Raised when a required dependency (Jinja2, ORM, etc.) is not
    available or when configuration is invalid.
    """

    code = "ADMIN_CONFIG_ERROR"
    status = 500

    def __init__(self, reason: str = "Admin configuration error", *, dependency: str = ""):
        msg = reason
        if dependency:
            msg = f"Missing dependency '{dependency}': {reason}"
        super().__init__(
            message=msg,
            code=self.code,
            status=self.status,
        )
        self.reason = reason
        self.dependency = dependency


# ═══════════════════════════════════════════════════════════════════════════════
#  Registration Faults
# ═══════════════════════════════════════════════════════════════════════════════


class AdminRegistrationFault(AdminFault):
    """
    Model registration error.

    Raised when a ModelAdmin is missing a model class, or when
    an invalid argument is passed to ``@register``.
    """

    code = "ADMIN_REGISTRATION_ERROR"
    status = 500

    def __init__(self, reason: str = "Model registration failed", *, model_name: str = ""):
        msg = reason
        if model_name:
            msg = f"Registration failed for '{model_name}': {reason}"
        super().__init__(
            message=msg,
            code=self.code,
            status=self.status,
        )
        self.reason = reason
        self.model_name = model_name


# ═══════════════════════════════════════════════════════════════════════════════
#  Inline Faults
# ═══════════════════════════════════════════════════════════════════════════════


class AdminInlineFault(AdminFault):
    """
    Inline model configuration error.

    Raised when FK resolution for an InlineModelAdmin fails --
    either no ForeignKey to the parent, or ambiguous multiple FKs.
    """

    code = "ADMIN_INLINE_ERROR"
    status = 400

    def __init__(
        self,
        reason: str = "Inline configuration error",
        *,
        inline_model: str = "",
        parent_model: str = "",
    ):
        msg = reason
        if inline_model and parent_model:
            msg = f"Inline '{inline_model}' → '{parent_model}': {reason}"
        super().__init__(
            message=msg,
            code=self.code,
            status=self.status,
        )
        self.reason = reason
        self.inline_model = inline_model
        self.parent_model = parent_model


# ═══════════════════════════════════════════════════════════════════════════════
#  Template Faults
# ═══════════════════════════════════════════════════════════════════════════════


class AdminTemplateFault(AdminFault):
    """
    Template rendering error.

    Raised when an admin template fails to render or when
    the template engine (Jinja2) is unavailable.
    """

    code = "ADMIN_TEMPLATE_ERROR"
    status = 500

    def __init__(self, reason: str = "Template error", *, template_name: str = ""):
        msg = reason
        if template_name:
            msg = f"Template '{template_name}': {reason}"
        super().__init__(
            message=msg,
            code=self.code,
            status=self.status,
        )
        self.reason = reason
        self.template_name = template_name


# ═══════════════════════════════════════════════════════════════════════════════
#  Export Faults
# ═══════════════════════════════════════════════════════════════════════════════


class AdminExportFault(AdminFault):
    """
    Export generation error.

    Raised when data export (CSV, JSON, XML) fails during
    rendering or serialisation.
    """

    code = "ADMIN_EXPORT_ERROR"
    status = 500

    def __init__(self, reason: str = "Export failed", *, export_format: str = ""):
        msg = reason
        if export_format:
            msg = f"Export ({export_format}): {reason}"
        super().__init__(
            message=msg,
            code=self.code,
            status=self.status,
        )
        self.reason = reason
        self.export_format = export_format
