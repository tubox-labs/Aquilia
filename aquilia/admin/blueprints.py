"""
AquilAdmin -- Blueprints for Admin Models.

Provides Aquilia Blueprint definitions for serialization,
validation, and projection of the admin models.

Each Blueprint uses the ``Spec`` inner class to bind to a model
and define which fields are readable, writable, and projected.

Usage::

    from aquilia.admin.blueprints import AdminUserBlueprint

    # Serialize an AdminUser instance
    data = AdminUserBlueprint.seal(user)

    # Validate input data
    cast = AdminUserBlueprint.cast(request_data)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

try:
    from aquilia.blueprints.core import Blueprint
    _HAS_BLUEPRINTS = True
except ImportError:
    _HAS_BLUEPRINTS = False

from .models import (
    AdminUser,
    AdminAuditEntry,
    AdminAPIKey,
    AdminPreference,
    _HAS_ORM,
)

if _HAS_BLUEPRINTS and _HAS_ORM:

    class AdminUserBlueprint(Blueprint):
        """Blueprint for AdminUser serialization.

        Excludes ``password_hash`` from output (write_only).
        """

        class Spec:
            model = AdminUser
            fields = [
                "id", "username", "email", "display_name",
                "role", "is_active",
                "login_count", "last_login_at", "last_active_at",
                "created_at", "updated_at", "avatar_url",
            ]
            read_only_fields = ["id", "login_count", "last_login_at", "last_active_at", "created_at"]

    class AdminUserCreateBlueprint(Blueprint):
        """Blueprint for creating a new AdminUser (accepts password)."""

        class Spec:
            model = AdminUser
            fields = [
                "username", "email", "display_name", "role", "is_active",
            ]

    class AdminAuditEntryBlueprint(Blueprint):
        """Blueprint for AdminAuditEntry serialization (read-only)."""

        class Spec:
            model = AdminAuditEntry
            fields = [
                "id", "user_id", "username", "ip_address",
                "action", "resource_type", "resource_id", "summary",
                "detail", "diff", "timestamp", "severity", "category",
            ]
            read_only_fields = [
                "id", "user_id", "username", "ip_address",
                "action", "resource_type", "resource_id", "summary",
                "detail", "diff", "timestamp", "severity", "category",
            ]

    class AdminAPIKeyBlueprint(Blueprint):
        """Blueprint for AdminAPIKey serialization.

        Excludes ``key_hash`` — the raw key is only shown once on creation.
        """

        class Spec:
            model = AdminAPIKey
            fields = [
                "id", "user_id", "name", "prefix", "scopes",
                "is_active", "last_used_at", "expires_at", "created_at",
            ]
            read_only_fields = ["id", "prefix", "last_used_at", "created_at"]

    class AdminPreferenceBlueprint(Blueprint):
        """Blueprint for AdminPreference serialization."""

        class Spec:
            model = AdminPreference
            fields = ["id", "user_id", "namespace", "data", "updated_at"]
            read_only_fields = ["id", "updated_at"]

else:
    # Stubs when blueprints or ORM are not available
    class AdminUserBlueprint:  # type: ignore[no-redef]
        pass

    class AdminUserCreateBlueprint:  # type: ignore[no-redef]
        pass

    class AdminAuditEntryBlueprint:  # type: ignore[no-redef]
        pass

    class AdminAPIKeyBlueprint:  # type: ignore[no-redef]
        pass

    class AdminPreferenceBlueprint:  # type: ignore[no-redef]
        pass


# ── Backward-compat aliases (import these names won't crash) ──────────

ContentTypeBlueprint = type("ContentTypeBlueprint", (), {})
AdminPermissionBlueprint = type("AdminPermissionBlueprint", (), {})
AdminGroupBlueprint = type("AdminGroupBlueprint", (), {})
AdminLogEntryBlueprint = type("AdminLogEntryBlueprint", (), {})
AdminSessionBlueprint = type("AdminSessionBlueprint", (), {})


__all__ = [
    # Active blueprints
    "AdminUserBlueprint",
    "AdminUserCreateBlueprint",
    "AdminAuditEntryBlueprint",
    "AdminAPIKeyBlueprint",
    "AdminPreferenceBlueprint",
    # Backward-compat stubs
    "ContentTypeBlueprint",
    "AdminPermissionBlueprint",
    "AdminGroupBlueprint",
    "AdminLogEntryBlueprint",
    "AdminSessionBlueprint",
]
