"""
AquilAdmin -- Admin Permission & Role System.

Integrates with Aquilia Auth RBAC/ABAC for admin access control.
Defines standard admin roles and per-model permission checks.

Admin Roles:
    - superadmin: Full access to everything including user management
    - staff: Full CRUD on models, audit log, exports
    - viewer: Read-only access to admin dashboard
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from aquilia.auth.core import Identity


class AdminRole(str, Enum):
    """Built-in admin roles with hierarchical permissions.

    Only three tiers:
    - **superadmin** – unrestricted, can manage users & system.
    - **staff**      – day-to-day CRUD, exports, bulk actions.
    - **viewer**     – read-only dashboard access.
    """
    SUPERADMIN = "superadmin"
    STAFF = "staff"
    VIEWER = "viewer"

    @property
    def level(self) -> int:
        """Numeric hierarchy level (higher = more permissions)."""
        return {
            AdminRole.VIEWER: 10,
            AdminRole.STAFF: 20,
            AdminRole.SUPERADMIN: 40,
        }[self]


class AdminPermission(str, Enum):
    """Fine-grained admin permissions."""
    # Dashboard
    DASHBOARD_VIEW = "admin.dashboard.view"

    # Model CRUD
    MODEL_VIEW = "admin.model.view"
    MODEL_ADD = "admin.model.add"
    MODEL_CHANGE = "admin.model.change"
    MODEL_DELETE = "admin.model.delete"
    MODEL_EXPORT = "admin.model.export"

    # Bulk actions
    ACTION_EXECUTE = "admin.action.execute"

    # Audit log
    AUDIT_VIEW = "admin.audit.view"

    # User management
    USER_MANAGE = "admin.user.manage"
    ROLE_MANAGE = "admin.role.manage"


# ── Permission matrix ────────────────────────────────────────────────────────

# Maps roles to their granted permissions
ROLE_PERMISSIONS: dict[AdminRole, set[AdminPermission]] = {
    AdminRole.VIEWER: {
        AdminPermission.DASHBOARD_VIEW,
        AdminPermission.MODEL_VIEW,
    },
    AdminRole.STAFF: {
        AdminPermission.DASHBOARD_VIEW,
        AdminPermission.MODEL_VIEW,
        AdminPermission.MODEL_ADD,
        AdminPermission.MODEL_CHANGE,
        AdminPermission.MODEL_DELETE,
        AdminPermission.MODEL_EXPORT,
        AdminPermission.ACTION_EXECUTE,
        AdminPermission.AUDIT_VIEW,
    },
    AdminRole.SUPERADMIN: set(AdminPermission),  # All permissions
}


def get_admin_role(identity: Optional["Identity"]) -> Optional[AdminRole]:
    """
    Determine the admin role for an identity.

    Checks identity attributes for 'admin_role' or 'roles' list.
    Returns None if the identity has no admin access.
    """
    if identity is None:
        return None

    if not identity.is_active():
        return None

    # Check explicit admin_role attribute
    admin_role = identity.get_attribute("admin_role")
    if admin_role:
        # Legacy: "admin" role maps to STAFF (admin tier was removed)
        if admin_role == "admin":
            return AdminRole.STAFF
        try:
            return AdminRole(admin_role)
        except ValueError:
            pass

    # Check roles list for admin roles
    roles = identity.get_attribute("roles", [])
    if "superadmin" in roles or "super_admin" in roles:
        return AdminRole.SUPERADMIN
    if "admin" in roles or "staff" in roles:
        return AdminRole.STAFF
    if "viewer" in roles:
        return AdminRole.VIEWER

    # Check is_staff / is_superuser flags
    if identity.get_attribute("is_superuser"):
        return AdminRole.SUPERADMIN
    if identity.get_attribute("is_staff"):
        return AdminRole.STAFF

    return None


def has_admin_permission(
    identity: Optional["Identity"],
    permission: AdminPermission,
) -> bool:
    """
    Check if an identity has a specific admin permission.

    Uses role-based hierarchy: higher roles include all lower permissions.
    """
    role = get_admin_role(identity)
    if role is None:
        return False

    return permission in ROLE_PERMISSIONS.get(role, set())


def has_model_permission(
    identity: Optional["Identity"],
    model_name: str,
    action: str,
) -> bool:
    """
    Check if an identity can perform an action on a model.

    Args:
        identity: The authenticated identity
        model_name: The model class name
        action: One of "view", "add", "change", "delete"

    Returns:
        True if allowed
    """
    permission_map = {
        "view": AdminPermission.MODEL_VIEW,
        "add": AdminPermission.MODEL_ADD,
        "change": AdminPermission.MODEL_CHANGE,
        "delete": AdminPermission.MODEL_DELETE,
        "export": AdminPermission.MODEL_EXPORT,
    }

    perm = permission_map.get(action)
    if perm is None:
        return False

    if not has_admin_permission(identity, perm):
        return False

    # Check runtime model permission overrides first
    model_overrides = _MODEL_PERMISSION_OVERRIDES.get(model_name, {})
    if action in model_overrides:
        return model_overrides[action]

    # Check model-specific permissions on identity attributes
    model_perms = identity.get_attribute("admin_model_permissions", {}) if identity else {}
    if model_perms:
        model_actions = model_perms.get(model_name, [])
        if model_actions and action not in model_actions:
            return False

    return True


def require_admin_access(identity: Optional["Identity"]) -> None:
    """
    Raise AdminAuthorizationFault if identity has no admin access.

    Use as a guard at the top of admin controller methods.
    """
    from .faults import AdminAuthorizationFault

    role = get_admin_role(identity)
    if role is None:
        raise AdminAuthorizationFault("No admin access")


# ── Runtime permission management ────────────────────────────────────────


# Runtime overrides for per-model permissions.
# Maps model_name -> {action -> bool} to allow/deny specific model actions
# beyond the role-based defaults.
_MODEL_PERMISSION_OVERRIDES: dict[str, dict[str, bool]] = {}


def update_role_permissions(
    role: AdminRole,
    permission: AdminPermission,
    *,
    granted: bool,
) -> None:
    """
    Grant or revoke a specific permission for a role at runtime.

    This modifies the in-memory ``ROLE_PERMISSIONS`` matrix.
    Changes persist for the lifetime of the process.

    Args:
        role: The admin role to modify
        permission: The permission to grant or revoke
        granted: True to grant, False to revoke

    Raises:
        ValueError: If trying to revoke from SUPERADMIN (always has all)
    """
    if role == AdminRole.SUPERADMIN:
        if not granted:
            raise ValueError("Cannot revoke permissions from SUPERADMIN role")
        return  # SUPERADMIN always has all permissions

    perms = ROLE_PERMISSIONS.setdefault(role, set())
    if granted:
        perms.add(permission)
    else:
        perms.discard(permission)


def set_model_permission_override(
    model_name: str,
    action: str,
    *,
    allowed: bool,
) -> None:
    """
    Set a per-model permission override.

    Overrides the default role-based model permission check for a
    specific model and action combination.

    Args:
        model_name: The model class name (e.g. "User", "BlogPost")
        action: One of "view", "add", "change", "delete", "export"
        allowed: True to allow, False to deny
    """
    _MODEL_PERMISSION_OVERRIDES.setdefault(model_name, {})[action] = allowed


def get_model_permission_overrides() -> dict[str, dict[str, bool]]:
    """Return the current model permission overrides."""
    return dict(_MODEL_PERMISSION_OVERRIDES)


def clear_model_permission_overrides(model_name: Optional[str] = None) -> None:
    """
    Clear model permission overrides.

    Args:
        model_name: If provided, clear only overrides for that model.
                    If None, clear all overrides.
    """
    if model_name is None:
        _MODEL_PERMISSION_OVERRIDES.clear()
    else:
        _MODEL_PERMISSION_OVERRIDES.pop(model_name, None)
