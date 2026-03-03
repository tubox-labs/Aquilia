"""
AquilAdmin -- Blueprints for Admin Models.

Provides Aquilia Blueprint definitions for serialization,
validation, and projection of all admin models.

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
    ContentType,
    AdminPermission,
    AdminGroup,
    AdminUser,
    AdminLogEntry,
    AdminSession,
    _HAS_ORM,
)

if _HAS_BLUEPRINTS and _HAS_ORM:

    class ContentTypeBlueprint(Blueprint):
        """Blueprint for ContentType serialization."""

        class Spec:
            model = ContentType
            fields = ["id", "app_label", "model"]
            read_only_fields = ["id"]

    class AdminPermissionBlueprint(Blueprint):
        """Blueprint for AdminPermission serialization."""

        class Spec:
            model = AdminPermission
            fields = ["id", "name", "codename", "content_type"]
            read_only_fields = ["id"]

    class AdminGroupBlueprint(Blueprint):
        """Blueprint for AdminGroup serialization."""

        class Spec:
            model = AdminGroup
            fields = ["id", "name", "permissions"]
            read_only_fields = ["id"]

    class AdminUserBlueprint(Blueprint):
        """
        Blueprint for AdminUser serialization.

        Excludes ``password_hash`` from output (write_only).
        """

        class Spec:
            model = AdminUser
            fields = [
                "id", "username", "email", "first_name", "last_name",
                "is_superuser", "is_staff", "is_active",
                "last_login", "date_joined", "groups", "user_permissions",
            ]
            read_only_fields = ["id", "last_login", "date_joined"]

    class AdminUserCreateBlueprint(Blueprint):
        """Blueprint for creating a new AdminUser (accepts password)."""

        class Spec:
            model = AdminUser
            fields = [
                "username", "email", "first_name", "last_name",
                "is_superuser", "is_staff", "is_active",
            ]

    class AdminLogEntryBlueprint(Blueprint):
        """Blueprint for AdminLogEntry serialization (read-only)."""

        class Spec:
            model = AdminLogEntry
            fields = [
                "id", "action_time", "user", "content_type",
                "object_id", "object_repr", "action_flag", "change_message",
            ]
            read_only_fields = [
                "id", "action_time", "user", "content_type",
                "object_id", "object_repr", "action_flag", "change_message",
            ]

    class AdminSessionBlueprint(Blueprint):
        """Blueprint for AdminSession serialization."""

        class Spec:
            model = AdminSession
            fields = ["id", "session_key", "expire_date"]
            read_only_fields = ["id", "session_key"]

else:
    # Stubs when blueprints or ORM are not available
    class ContentTypeBlueprint:  # type: ignore[no-redef]
        pass

    class AdminPermissionBlueprint:  # type: ignore[no-redef]
        pass

    class AdminGroupBlueprint:  # type: ignore[no-redef]
        pass

    class AdminUserBlueprint:  # type: ignore[no-redef]
        pass

    class AdminUserCreateBlueprint:  # type: ignore[no-redef]
        pass

    class AdminLogEntryBlueprint:  # type: ignore[no-redef]
        pass

    class AdminSessionBlueprint:  # type: ignore[no-redef]
        pass


__all__ = [
    "ContentTypeBlueprint",
    "AdminPermissionBlueprint",
    "AdminGroupBlueprint",
    "AdminUserBlueprint",
    "AdminUserCreateBlueprint",
    "AdminLogEntryBlueprint",
    "AdminSessionBlueprint",
]
