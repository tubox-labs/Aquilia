"""
AquilAdmin -- Contracts for Admin Models.

Provides Aquilia Contract definitions for serialization,
validation, and projection of the admin models.

Each Contract uses the ``Spec`` inner class to bind to a model
and define which fields are readable, writable, and projected.

Usage::

    from aquilia.admin.contracts import AdminUserContract

    # Serialize an AdminUser instance
    data = AdminUserContract.seal(user)

    # Validate input data
    cast = AdminUserContract.cast(request_data)
"""

from __future__ import annotations

try:
    from aquilia.contracts.core import Contract

    _HAS_CONTRACTS = True
except ImportError:
    _HAS_CONTRACTS = False

from .models import (
    _HAS_ORM,
    AdminAPIKey,
    AdminAuditEntry,
    AdminPreference,
    AdminUser,
)

if _HAS_CONTRACTS and _HAS_ORM:

    class AdminUserContract(Contract):
        """Contract for AdminUser serialization.

        Excludes ``password_hash`` from output (write_only).
        """

        class Spec:
            model = AdminUser
            fields = [
                "id",
                "username",
                "email",
                "display_name",
                "role",
                "is_active",
                "login_count",
                "last_login_at",
                "last_active_at",
                "created_at",
                "updated_at",
                "avatar_url",
            ]
            read_only_fields = ["id", "login_count", "last_login_at", "last_active_at", "created_at"]

    class AdminUserCreateContract(Contract):
        """Contract for creating a new AdminUser (accepts password)."""

        class Spec:
            model = AdminUser
            fields = [
                "username",
                "email",
                "display_name",
                "role",
                "is_active",
            ]

    class AdminAuditEntryContract(Contract):
        """Contract for AdminAuditEntry serialization (read-only)."""

        class Spec:
            model = AdminAuditEntry
            fields = [
                "id",
                "user_id",
                "username",
                "ip_address",
                "action",
                "resource_type",
                "resource_id",
                "summary",
                "detail",
                "diff",
                "timestamp",
                "severity",
                "category",
            ]
            read_only_fields = [
                "id",
                "user_id",
                "username",
                "ip_address",
                "action",
                "resource_type",
                "resource_id",
                "summary",
                "detail",
                "diff",
                "timestamp",
                "severity",
                "category",
            ]

    class AdminAPIKeyContract(Contract):
        """Contract for AdminAPIKey serialization.

        Excludes ``key_hash`` — the raw key is only shown once on creation.
        """

        class Spec:
            model = AdminAPIKey
            fields = [
                "id",
                "user_id",
                "name",
                "prefix",
                "scopes",
                "is_active",
                "last_used_at",
                "expires_at",
                "created_at",
            ]
            read_only_fields = ["id", "prefix", "last_used_at", "created_at"]

    class AdminPreferenceContract(Contract):
        """Contract for AdminPreference serialization."""

        class Spec:
            model = AdminPreference
            fields = ["id", "user_id", "namespace", "data", "updated_at"]
            read_only_fields = ["id", "updated_at"]

else:
    # Stubs when contracts or ORM are not available
    class AdminUserContract:  # type: ignore[no-redef]
        pass

    class AdminUserCreateContract:  # type: ignore[no-redef]
        pass

    class AdminAuditEntryContract:  # type: ignore[no-redef]
        pass

    class AdminAPIKeyContract:  # type: ignore[no-redef]
        pass

    class AdminPreferenceContract:  # type: ignore[no-redef]
        pass


# ── Backward-compat aliases (import these names won't crash) ──────────

ContentTypeContract = type("ContentTypeContract", (), {})
AdminPermissionContract = type("AdminPermissionContract", (), {})
AdminGroupContract = type("AdminGroupContract", (), {})
AdminLogEntryContract = type("AdminLogEntryContract", (), {})
AdminSessionContract = type("AdminSessionContract", (), {})


__all__ = [
    # Active contracts
    "AdminUserContract",
    "AdminUserCreateContract",
    "AdminAuditEntryContract",
    "AdminAPIKeyContract",
    "AdminPreferenceContract",
    # Backward-compat stubs
    "ContentTypeContract",
    "AdminPermissionContract",
    "AdminGroupContract",
    "AdminLogEntryContract",
    "AdminSessionContract",
]
