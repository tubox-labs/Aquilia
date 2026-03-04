"""
AquilAdmin -- Structured Faults for Admin System.

All admin errors use Aquilia's Fault system for structured,
typed, recoverable error handling.
"""

from __future__ import annotations

from aquilia.faults import Fault
from aquilia.faults.core import FaultDomain

# Custom fault domain for admin subsystem
ADMIN_DOMAIN = FaultDomain.custom("ADMIN", "Admin dashboard faults")


# ── Base Admin Fault ─────────────────────────────────────────────────────────

class AdminFault(Fault):
    """Base fault for all admin operations."""
    domain = ADMIN_DOMAIN


# ── Authentication Faults ────────────────────────────────────────────────────

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


# ── Authorization Faults ─────────────────────────────────────────────────────

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


# ── Model / Record Faults ────────────────────────────────────────────────────

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


# ── Validation Faults ────────────────────────────────────────────────────────

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


# ── Action Faults ─────────────────────────────────────────────────────────────

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
