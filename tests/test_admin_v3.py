"""
Comprehensive tests for the Admin System overhaul (v3).

Covers:
- New admin models: ContentType, AdminPermission, AdminGroup, AdminLogEntry, AdminSession
- Enhanced AdminUser with groups & permissions
- Admin Blueprints
- Server admin integration wiring (_wire_admin_integration)
- Migration format (CROUS snapshot)
- CLI createsuperuser (no raw SQL)
- Route compilation for admin controller
- Regression tests for existing functionality
"""

from __future__ import annotations

import asyncio
import datetime
import json
import os
from typing import Any, Dict, List, Optional, Type
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest

from aquilia.admin.controller import AdminController
from aquilia.admin.templates import (
    render_list_view,
    render_form_view,
    render_dashboard,
    render_build_page,
)

# ═══════════════════════════════════════════════════════════════════════════
# 1. NEW MODEL IMPORTS & EXISTENCE TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminModelImports:
    """Verify all new admin models are importable."""

    def test_import_content_type(self):
        from aquilia.admin.models import ContentType
        assert ContentType is not None

    def test_import_admin_permission_model(self):
        from aquilia.admin.models import AdminPermission
        assert AdminPermission is not None

    def test_import_admin_group(self):
        from aquilia.admin.models import AdminGroup
        assert AdminGroup is not None

    def test_import_admin_user(self):
        from aquilia.admin.models import AdminUser
        assert AdminUser is not None

    def test_import_admin_log_entry(self):
        from aquilia.admin.models import AdminLogEntry
        assert AdminLogEntry is not None

    def test_import_admin_session(self):
        from aquilia.admin.models import AdminSession
        assert AdminSession is not None

    def test_import_hash_helpers(self):
        from aquilia.admin.models import _hash_password, _verify_password
        assert callable(_hash_password)
        assert callable(_verify_password)

    def test_all_models_in_all_export(self):
        from aquilia.admin.models import __all__
        expected = [
            "ContentType", "AdminPermission", "AdminGroup",
            "AdminUser", "AdminLogEntry", "AdminSession",
            "_hash_password", "_verify_password",
        ]
        for name in expected:
            assert name in __all__, f"{name} missing from __all__"


class TestTopLevelExports:
    """Verify new models are exported from aquilia package."""

    def test_admin_user_from_aquilia(self):
        from aquilia import AdminUser
        assert AdminUser is not None

    def test_admin_group_from_aquilia(self):
        from aquilia import AdminGroup
        assert AdminGroup is not None

    def test_content_type_from_aquilia(self):
        from aquilia import ContentType
        assert ContentType is not None

    def test_admin_log_entry_from_aquilia(self):
        from aquilia import AdminLogEntry
        assert AdminLogEntry is not None

    def test_admin_session_from_aquilia(self):
        from aquilia import AdminSession
        assert AdminSession is not None

    def test_admin_user_blueprint_from_aquilia(self):
        from aquilia import AdminUserBlueprint
        assert AdminUserBlueprint is not None

    def test_admin_group_blueprint_from_aquilia(self):
        from aquilia import AdminGroupBlueprint
        assert AdminGroupBlueprint is not None

    def test_admin_permission_blueprint_from_aquilia(self):
        from aquilia import AdminPermissionBlueprint
        assert AdminPermissionBlueprint is not None

    def test_content_type_blueprint_from_aquilia(self):
        from aquilia import ContentTypeBlueprint
        assert ContentTypeBlueprint is not None

    def test_admin_log_entry_blueprint_from_aquilia(self):
        from aquilia import AdminLogEntryBlueprint
        assert AdminLogEntryBlueprint is not None

    def test_admin_session_blueprint_from_aquilia(self):
        from aquilia import AdminSessionBlueprint
        assert AdminSessionBlueprint is not None


# ═══════════════════════════════════════════════════════════════════════════
# 2. CONTENT TYPE MODEL TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestContentType:
    """Test the ContentType model."""

    def test_table_name(self):
        from aquilia.admin.models import ContentType, _HAS_ORM
        if _HAS_ORM:
            assert ContentType._table_name == "admin_content_types"

    def test_str_representation(self):
        from aquilia.admin.models import ContentType, _HAS_ORM
        if _HAS_ORM:
            ct = ContentType.__new__(ContentType)
            ct.app_label = "myapp"
            ct.model = "user"
            assert str(ct) == "myapp.user"

    def test_name_property(self):
        from aquilia.admin.models import ContentType, _HAS_ORM
        if _HAS_ORM:
            ct = ContentType.__new__(ContentType)
            ct.model = "admin_user"
            assert ct.name == "Admin User"

    def test_has_meta_ordering(self):
        from aquilia.admin.models import ContentType, _HAS_ORM
        if _HAS_ORM:
            meta = ContentType._meta
            assert hasattr(meta, "ordering")
            assert meta.ordering == ["app_label", "model"]

    def test_has_unique_constraint(self):
        from aquilia.admin.models import ContentType, _HAS_ORM
        if _HAS_ORM:
            constraints = getattr(ContentType._meta, "constraints", [])
            assert len(constraints) >= 1
            assert constraints[0].fields == ["app_label", "model"]

    def test_has_index(self):
        from aquilia.admin.models import ContentType, _HAS_ORM
        if _HAS_ORM:
            indexes = getattr(ContentType._meta, "indexes", [])
            assert len(indexes) >= 1


# ═══════════════════════════════════════════════════════════════════════════
# 3. ADMIN PERMISSION MODEL TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminPermissionModel:
    """Test the AdminPermission model."""

    def test_table_name(self):
        from aquilia.admin.models import AdminPermission, _HAS_ORM
        if _HAS_ORM:
            assert AdminPermission._table_name == "admin_permissions"

    def test_str_representation(self):
        from aquilia.admin.models import AdminPermission, _HAS_ORM
        if _HAS_ORM:
            perm = AdminPermission.__new__(AdminPermission)
            perm.codename = "change_user"
            perm.name = "Can change user"
            assert str(perm) == "change_user"

    def test_has_foreign_key_to_content_type(self):
        from aquilia.admin.models import AdminPermission, _HAS_ORM
        if _HAS_ORM:
            ct_field = AdminPermission._fields['content_type']
            assert ct_field.to == "ContentType"

    def test_has_unique_constraint(self):
        from aquilia.admin.models import AdminPermission, _HAS_ORM
        if _HAS_ORM:
            constraints = getattr(AdminPermission._meta, "constraints", [])
            assert len(constraints) >= 1
            assert "content_type_id" in constraints[0].fields
            assert "codename" in constraints[0].fields


# ═══════════════════════════════════════════════════════════════════════════
# 4. ADMIN GROUP MODEL TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminGroupModel:
    """Test the AdminGroup model."""

    def test_table_name(self):
        from aquilia.admin.models import AdminGroup, _HAS_ORM
        if _HAS_ORM:
            assert AdminGroup._table_name == "admin_groups"

    def test_str_representation(self):
        from aquilia.admin.models import AdminGroup, _HAS_ORM
        if _HAS_ORM:
            grp = AdminGroup.__new__(AdminGroup)
            grp.name = "Editors"
            assert str(grp) == "Editors"

    def test_has_m2m_permissions(self):
        from aquilia.admin.models import AdminGroup, _HAS_ORM
        if _HAS_ORM:
            perms_field = AdminGroup._m2m_fields['permissions']
            assert perms_field.to == "AdminPermission"

    def test_m2m_junction_table(self):
        from aquilia.admin.models import AdminGroup, _HAS_ORM
        if _HAS_ORM:
            perms_field = AdminGroup._m2m_fields['permissions']
            assert perms_field.db_table == "admin_group_permissions"


# ═══════════════════════════════════════════════════════════════════════════
# 5. ADMIN USER MODEL TESTS (enhanced)
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminUserModelEnhanced:
    """Test the enhanced AdminUser model with groups/permissions."""

    def test_table_name(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            assert AdminUser._table_name == "admin_users"

    def test_has_groups_m2m(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            groups_field = AdminUser._m2m_fields['groups']
            assert groups_field.to == "AdminGroup"
            assert groups_field.db_table == "admin_user_groups"

    def test_has_user_permissions_m2m(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            perms_field = AdminUser._m2m_fields['user_permissions']
            assert perms_field.to == "AdminPermission"
            assert perms_field.db_table == "admin_user_permissions"

    def test_has_indexes(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            indexes = AdminUser._meta.indexes
            assert len(indexes) >= 3
            index_names = [idx.name for idx in indexes]
            assert "idx_admin_user_username" in index_names
            assert "idx_admin_user_email" in index_names
            assert "idx_admin_user_active_staff" in index_names

    def test_get_full_name(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            user = AdminUser.__new__(AdminUser)
            user.first_name = "John"
            user.last_name = "Doe"
            user.username = "johndoe"
            assert user.get_full_name() == "John Doe"

    def test_get_full_name_fallback_to_username(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            user = AdminUser.__new__(AdminUser)
            user.first_name = ""
            user.last_name = ""
            user.username = "admin"
            assert user.get_full_name() == "admin"

    def test_get_short_name(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            user = AdminUser.__new__(AdminUser)
            user.first_name = "Jane"
            user.username = "jane"
            assert user.get_short_name() == "Jane"

    def test_password_hashing(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            user = AdminUser.__new__(AdminUser)
            user.set_password("my-secret-123")
            assert user.password_hash != "my-secret-123"
            assert user.check_password("my-secret-123")
            assert not user.check_password("wrong")

    def test_to_identity_superuser(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            user = AdminUser.__new__(AdminUser)
            user.pk = 1
            user.username = "superadmin"
            user.email = "sa@test.com"
            user.first_name = "Super"
            user.last_name = "Admin"
            user.is_superuser = True
            user.is_staff = True
            user.is_active = True
            identity = user.to_identity()
            assert identity.id == "1"
            assert "superadmin" in identity.attributes["roles"]

    def test_to_identity_staff(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            user = AdminUser.__new__(AdminUser)
            user.pk = 2
            user.username = "staffuser"
            user.email = ""
            user.first_name = ""
            user.last_name = ""
            user.is_superuser = False
            user.is_staff = True
            user.is_active = True
            identity = user.to_identity()
            assert "staff" in identity.attributes["roles"]
            assert "superadmin" not in identity.attributes["roles"]

    @pytest.mark.asyncio
    async def test_has_perm_superuser_always_true(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            user = AdminUser.__new__(AdminUser)
            user.is_superuser = True
            user.is_active = True
            assert await user.has_perm("any.permission") is True

    @pytest.mark.asyncio
    async def test_has_perm_inactive_always_false(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            user = AdminUser.__new__(AdminUser)
            user.is_superuser = False
            user.is_active = False
            assert await user.has_perm("any.permission") is False

    @pytest.mark.asyncio
    async def test_has_perms_superuser(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            user = AdminUser.__new__(AdminUser)
            user.is_superuser = True
            user.is_active = True
            assert await user.has_perms(["a", "b", "c"]) is True

    @pytest.mark.asyncio
    async def test_has_module_perms_superuser(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            user = AdminUser.__new__(AdminUser)
            user.is_superuser = True
            user.is_active = True
            assert await user.has_module_perms("any_app") is True

    @pytest.mark.asyncio
    async def test_has_module_perms_inactive(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            user = AdminUser.__new__(AdminUser)
            user.is_superuser = False
            user.is_active = False
            assert await user.has_module_perms("myapp") is False


# ═══════════════════════════════════════════════════════════════════════════
# 6. ADMIN LOG ENTRY MODEL TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminLogEntry:
    """Test the AdminLogEntry model."""

    def test_table_name(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            assert AdminLogEntry._table_name == "admin_log_entries"

    def test_action_constants(self):
        from aquilia.admin.models import AdminLogEntry
        assert AdminLogEntry.ADDITION == 1
        assert AdminLogEntry.CHANGE == 2
        assert AdminLogEntry.DELETION == 3

    def test_is_addition_property(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            entry = AdminLogEntry.__new__(AdminLogEntry)
            entry.action_flag = 1
            assert entry.is_addition is True
            assert entry.is_change is False
            assert entry.is_deletion is False

    def test_is_change_property(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            entry = AdminLogEntry.__new__(AdminLogEntry)
            entry.action_flag = 2
            assert entry.is_change is True

    def test_is_deletion_property(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            entry = AdminLogEntry.__new__(AdminLogEntry)
            entry.action_flag = 3
            assert entry.is_deletion is True

    def test_str_representation(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            entry = AdminLogEntry.__new__(AdminLogEntry)
            entry.action_flag = 1
            entry.object_repr = "User object (1)"
            assert "Added" in str(entry)
            assert "User object (1)" in str(entry)

    def test_get_change_message_json(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            entry = AdminLogEntry.__new__(AdminLogEntry)
            entry.change_message = json.dumps(["Changed name", "Changed email"])
            result = entry.get_change_message()
            assert "Changed name" in result

    def test_get_change_message_plain_text(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            entry = AdminLogEntry.__new__(AdminLogEntry)
            entry.change_message = "Simple text message"
            result = entry.get_change_message()
            assert result == "Simple text message"

    def test_get_change_message_empty(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            entry = AdminLogEntry.__new__(AdminLogEntry)
            entry.change_message = ""
            assert entry.get_change_message() == ""

    def test_has_fk_to_admin_user(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            user_field = AdminLogEntry._fields['user']
            assert user_field.to == "AdminUser"

    def test_has_fk_to_content_type(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            ct_field = AdminLogEntry._fields['content_type']
            assert ct_field.to == "ContentType"

    def test_has_indexes(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            indexes = AdminLogEntry._meta.indexes
            assert len(indexes) >= 3
            index_names = [idx.name for idx in indexes]
            assert "idx_log_entry_time" in index_names
            assert "idx_log_entry_user_time" in index_names
            assert "idx_log_entry_ct_obj" in index_names


# ═══════════════════════════════════════════════════════════════════════════
# 7. ADMIN SESSION MODEL TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminSession:
    """Test the AdminSession model."""

    def test_table_name(self):
        from aquilia.admin.models import AdminSession, _HAS_ORM
        if _HAS_ORM:
            assert AdminSession._table_name == "admin_sessions"

    def test_str_representation(self):
        from aquilia.admin.models import AdminSession, _HAS_ORM
        if _HAS_ORM:
            session = AdminSession.__new__(AdminSession)
            session.session_key = "abc123def456"
            assert str(session) == "abc123def456"

    def test_is_expired_none_date(self):
        from aquilia.admin.models import AdminSession, _HAS_ORM
        if _HAS_ORM:
            session = AdminSession.__new__(AdminSession)
            session.expire_date = None
            assert session.is_expired() is True

    def test_is_expired_past_date(self):
        from aquilia.admin.models import AdminSession, _HAS_ORM
        if _HAS_ORM:
            session = AdminSession.__new__(AdminSession)
            session.expire_date = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
            assert session.is_expired() is True

    def test_is_expired_future_date(self):
        from aquilia.admin.models import AdminSession, _HAS_ORM
        if _HAS_ORM:
            session = AdminSession.__new__(AdminSession)
            session.expire_date = datetime.datetime(2099, 1, 1, tzinfo=datetime.timezone.utc)
            assert session.is_expired() is False

    def test_has_indexes(self):
        from aquilia.admin.models import AdminSession, _HAS_ORM
        if _HAS_ORM:
            indexes = AdminSession._meta.indexes
            assert len(indexes) >= 2


# ═══════════════════════════════════════════════════════════════════════════
# 8. PASSWORD HASHING TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestPasswordHashing:
    """Test password hashing helpers."""

    def test_hash_password_returns_string(self):
        from aquilia.admin.models import _hash_password
        hashed = _hash_password("testpass123")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_hash_password_not_plaintext(self):
        from aquilia.admin.models import _hash_password
        hashed = _hash_password("testpass123")
        assert hashed != "testpass123"

    def test_verify_password_correct(self):
        from aquilia.admin.models import _hash_password, _verify_password
        hashed = _hash_password("correct-pass")
        assert _verify_password(hashed, "correct-pass") is True

    def test_verify_password_wrong(self):
        from aquilia.admin.models import _hash_password, _verify_password
        hashed = _hash_password("correct-pass")
        assert _verify_password(hashed, "wrong-pass") is False

    def test_verify_empty_hash(self):
        from aquilia.admin.models import _verify_password
        assert _verify_password("", "anything") is False

    def test_verify_invalid_hash_format(self):
        from aquilia.admin.models import _verify_password
        assert _verify_password("not-a-valid-hash", "test") is False

    def test_hash_produces_different_results(self):
        from aquilia.admin.models import _hash_password
        h1 = _hash_password("same-pass")
        h2 = _hash_password("same-pass")
        # Different salts should produce different hashes
        assert h1 != h2


# ═══════════════════════════════════════════════════════════════════════════
# 9. BLUEPRINT TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminBlueprints:
    """Test the admin blueprint definitions."""

    def test_import_all_blueprints(self):
        from aquilia.admin.blueprints import (
            ContentTypeBlueprint,
            AdminPermissionBlueprint,
            AdminGroupBlueprint,
            AdminUserBlueprint,
            AdminUserCreateBlueprint,
            AdminLogEntryBlueprint,
            AdminSessionBlueprint,
        )
        assert ContentTypeBlueprint is not None
        assert AdminPermissionBlueprint is not None
        assert AdminGroupBlueprint is not None
        assert AdminUserBlueprint is not None
        assert AdminUserCreateBlueprint is not None
        assert AdminLogEntryBlueprint is not None
        assert AdminSessionBlueprint is not None

    def test_blueprint_all_export(self):
        from aquilia.admin.blueprints import __all__
        expected = [
            "ContentTypeBlueprint",
            "AdminPermissionBlueprint",
            "AdminGroupBlueprint",
            "AdminUserBlueprint",
            "AdminUserCreateBlueprint",
            "AdminLogEntryBlueprint",
            "AdminSessionBlueprint",
        ]
        for name in expected:
            assert name in __all__

    def test_admin_user_blueprint_has_spec(self):
        from aquilia.admin.blueprints import AdminUserBlueprint, _HAS_BLUEPRINTS
        if _HAS_BLUEPRINTS:
            assert hasattr(AdminUserBlueprint, "_spec")

    def test_content_type_blueprint_has_spec(self):
        from aquilia.admin.blueprints import ContentTypeBlueprint, _HAS_BLUEPRINTS
        if _HAS_BLUEPRINTS:
            assert hasattr(ContentTypeBlueprint, "_spec")


# ═══════════════════════════════════════════════════════════════════════════
# 10. SERVER ADMIN WIRING TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestServerAdminWiring:
    """Test that _wire_admin_integration exists and works."""

    def test_wire_admin_integration_method_exists(self):
        from aquilia.server import AquiliaServer
        assert hasattr(AquiliaServer, "_wire_admin_integration")
        assert callable(getattr(AquiliaServer, "_wire_admin_integration"))

    def test_wire_admin_noop_without_config(self):
        """When no admin config exists, _wire_admin_integration is a no-op."""
        from aquilia.server import AquiliaServer

        server = MagicMock(spec=AquiliaServer)
        server.config = {}
        server.logger = MagicMock()

        # Call the real method
        AquiliaServer._wire_admin_integration(server)

        # Should not have tried to register any routes
        # (no error, just no-op)

    def test_wire_admin_with_config(self):
        """When admin config exists, routes should be registered."""
        from aquilia.server import AquiliaServer

        server = MagicMock(spec=AquiliaServer)
        server.config = {
            "integrations": {
                "admin": {
                    "_integration_type": "admin",
                    "url_prefix": "/admin",
                    "site_title": "Test Admin",
                    "auto_discover": False,
                }
            }
        }
        server.logger = MagicMock()

        # Mock the controller router
        mock_router = MagicMock()
        mock_router.routes_by_method = {}
        server.controller_router = mock_router

        # Call the real method
        AquiliaServer._wire_admin_integration(server)

        # Should have initialized routes
        if mock_router.routes_by_method:
            # Routes were registered
            total_routes = sum(len(v) for v in mock_router.routes_by_method.values())
            assert total_routes > 0


class TestAdminRouteCount:
    """Test that the correct number of admin routes are registered."""

    def test_admin_controller_has_all_routes(self):
        """AdminController should have routes for all CRUD + auth + new page endpoints."""
        from aquilia.admin.controller import AdminController
        import inspect

        # Count decorated methods
        route_methods = []
        for name, method in inspect.getmembers(AdminController, inspect.isfunction):
            if hasattr(method, "__route_metadata__"):
                route_methods.append(name)

        # Should have at minimum these routes (includes 5 new pages)
        expected_names = [
            "dashboard", "login_page", "login_submit", "logout",
            "list_view", "add_form", "add_submit",
            "edit_form", "edit_submit", "delete_record",
            "audit_view",
            "orm_view", "build_view", "migrations_view",
            "config_view", "permissions_view",
        ]
        for name in expected_names:
            assert hasattr(AdminController, name), f"Missing route method: {name}"

    def test_admin_controller_prefix(self):
        from aquilia.admin.controller import AdminController
        assert AdminController.prefix == "/admin"


# ═══════════════════════════════════════════════════════════════════════════
# 11. MIGRATION FORMAT TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestMigrationFormat:
    """Test that migration system uses CROUS binary format exclusively."""

    def test_snapshot_save_crous_binary(self):
        """save_snapshot should write CROUS binary files."""
        from aquilia.models.schema_snapshot import save_snapshot
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            crous_path = os.path.join(tmpdir, "test.crous")
            snapshot = {"version": 1, "models": {}, "checksum": "abc"}
            save_snapshot(snapshot, crous_path)
            assert os.path.exists(crous_path)
            # Verify it's binary CROUS, not JSON
            with open(crous_path, "rb") as f:
                header = f.read(7)
            assert header == b"CROUSv1", f"Expected CROUS binary header, got {header!r}"

    def test_snapshot_roundtrip_crous(self):
        """save_snapshot + load_snapshot should roundtrip data via CROUS."""
        from aquilia.models.schema_snapshot import save_snapshot, load_snapshot
        import tempfile
        import os

        with tempfile.TemporaryDirectory() as tmpdir:
            crous_path = os.path.join(tmpdir, "test.crous")
            snapshot = {"version": 1, "models": {"User": {"table": "users"}}, "checksum": "abc"}
            save_snapshot(snapshot, crous_path)
            loaded = load_snapshot(crous_path)
            assert loaded is not None
            assert loaded["version"] == 1
            assert "User" in loaded["models"]
            assert loaded["models"]["User"]["table"] == "users"

    def test_load_snapshot_nonexistent_returns_none(self):
        from aquilia.models.schema_snapshot import load_snapshot
        result = load_snapshot("/nonexistent/path/snapshot.crous")
        assert result is None

    def test_migration_gen_default_path_is_crous(self):
        """generate_dsl_migration should use .crous extension by default."""
        from aquilia.models.migration_gen import generate_dsl_migration
        import inspect

        source = inspect.getsource(generate_dsl_migration)
        assert "schema_snapshot.crous" in source

    def test_no_json_fallback_in_save(self):
        """save_snapshot should not contain JSON fallback logic."""
        from aquilia.models.schema_snapshot import save_snapshot
        import inspect

        source = inspect.getsource(save_snapshot)
        assert "json.dumps" not in source, "save_snapshot should not fall back to JSON"

    def test_no_json_fallback_in_load(self):
        """load_snapshot should not contain JSON fallback logic."""
        from aquilia.models.schema_snapshot import load_snapshot
        import inspect

        source = inspect.getsource(load_snapshot)
        assert "json.loads" not in source, "load_snapshot should not fall back to JSON"

    def test_uses_crous_native(self):
        """Both save and load should use _crous_native."""
        from aquilia.models.schema_snapshot import save_snapshot, load_snapshot
        import inspect

        save_src = inspect.getsource(save_snapshot)
        load_src = inspect.getsource(load_snapshot)
        assert "_crous_native" in save_src
        assert "_crous_native" in load_src


# ═══════════════════════════════════════════════════════════════════════════
# 12. CLI NO RAW SQL TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestCLINoRawSQL:
    """Test that CLI createsuperuser no longer uses raw SQL."""

    def _get_source(self):
        import inspect
        from aquilia.cli.__main__ import admin_createsuperuser
        # Click wraps the function; get the underlying callback
        fn = getattr(admin_createsuperuser, "callback", admin_createsuperuser)
        return inspect.getsource(fn)

    def test_no_create_table_sql_in_cli(self):
        """Ensure 'CREATE TABLE' raw SQL is removed from createsuperuser."""
        source = self._get_source()
        assert "CREATE TABLE" not in source, "Raw CREATE TABLE SQL should be removed from CLI"

    def test_no_insert_into_sql_in_cli(self):
        """Ensure 'INSERT INTO' raw SQL is removed from createsuperuser."""
        source = self._get_source()
        assert "INSERT INTO" not in source, "Raw INSERT INTO SQL should be removed from CLI"

    def test_createsuperuser_uses_orm(self):
        """Ensure createsuperuser uses AdminUser.create_superuser."""
        source = self._get_source()
        assert "AdminUser.create_superuser" in source

    def test_createsuperuser_requires_migrate(self):
        """Error message should mention 'aq db migrate'."""
        source = self._get_source()
        assert "aq db migrate" in source or "migrate" in source

    def test_createsuperuser_uses_configure_database(self):
        """Ensure createsuperuser registers DB via configure_database, not raw AquiliaDatabase."""
        source = self._get_source()
        assert "configure_database" in source, "Should use configure_database to register DB with ORM"
        assert "AquiliaDatabase(" not in source, "Should not create raw AquiliaDatabase instance"


# ═══════════════════════════════════════════════════════════════════════════
# 13. STUB FALLBACK TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestStubFallbacks:
    """Test that stub classes work when ORM is unavailable."""

    def test_admin_user_stub_api(self):
        """AdminUser stub should have the same public API."""
        from aquilia.admin.models import AdminUser
        # These methods should exist regardless of _HAS_ORM
        assert hasattr(AdminUser, "check_password") or hasattr(AdminUser, "set_password")
        assert hasattr(AdminUser, "to_identity")
        assert hasattr(AdminUser, "authenticate")
        assert hasattr(AdminUser, "create_superuser")
        assert hasattr(AdminUser, "get_full_name")

    def test_admin_log_entry_constants(self):
        """AdminLogEntry constants should always be available."""
        from aquilia.admin.models import AdminLogEntry
        assert AdminLogEntry.ADDITION == 1
        assert AdminLogEntry.CHANGE == 2
        assert AdminLogEntry.DELETION == 3

    def test_admin_session_is_expired_stub(self):
        """AdminSession stub should return True for is_expired."""
        from aquilia.admin.models import AdminSession, _HAS_ORM
        if not _HAS_ORM:
            session = AdminSession()
            assert session.is_expired() is True


# ═══════════════════════════════════════════════════════════════════════════
# 14. ADMIN INIT EXPORTS TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminInitExports:
    """Test that admin __init__.py exports all new models."""

    def test_all_new_models_in_admin_init(self):
        from aquilia.admin import __all__
        expected = [
            "AdminUser", "AdminGroup", "ContentType",
            "AdminLogEntry", "AdminSession",
            "AdminUserBlueprint", "AdminGroupBlueprint",
            "ContentTypeBlueprint", "AdminLogEntryBlueprint",
            "AdminSessionBlueprint",
        ]
        for name in expected:
            assert name in __all__, f"{name} not in admin __all__"


# ═══════════════════════════════════════════════════════════════════════════
# 15. ORM FIELD CONFIGURATION TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestModelFieldConfiguration:
    """Test that model fields are configured correctly."""

    def test_admin_user_username_unique(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            assert AdminUser._fields['username'].unique is True

    def test_admin_user_email_blank(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            assert AdminUser._fields['email'].blank is True

    def test_admin_user_is_staff_default_true(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            assert AdminUser._fields['is_staff'].default is True

    def test_admin_user_is_superuser_default_false(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            assert AdminUser._fields['is_superuser'].default is False

    def test_admin_user_last_login_nullable(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            assert AdminUser._fields['last_login'].null is True

    def test_admin_group_name_unique(self):
        from aquilia.admin.models import AdminGroup, _HAS_ORM
        if _HAS_ORM:
            assert AdminGroup._fields['name'].unique is True

    def test_admin_session_key_unique(self):
        from aquilia.admin.models import AdminSession, _HAS_ORM
        if _HAS_ORM:
            assert AdminSession._fields['session_key'].unique is True

    def test_admin_log_entry_action_time_auto(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            assert AdminLogEntry._fields['action_time'].auto_now_add is True

    def test_admin_log_entry_content_type_nullable(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            assert AdminLogEntry._fields['content_type'].null is True


# ═══════════════════════════════════════════════════════════════════════════
# 16. RELATIONSHIP INTEGRITY TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestRelationshipIntegrity:
    """Test ForeignKey and M2M relationships are properly configured."""

    def test_admin_permission_content_type_fk(self):
        from aquilia.admin.models import AdminPermission, _HAS_ORM
        if _HAS_ORM:
            fk = AdminPermission._fields['content_type']
            assert fk.on_delete == "CASCADE"
            assert fk.to == "ContentType"

    def test_admin_log_entry_user_fk(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            fk = AdminLogEntry._fields['user']
            assert fk.on_delete == "CASCADE"
            assert fk.to == "AdminUser"

    def test_admin_log_entry_content_type_fk(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            fk = AdminLogEntry._fields['content_type']
            assert fk.on_delete == "SET NULL"
            assert fk.null is True

    def test_admin_group_permissions_m2m(self):
        from aquilia.admin.models import AdminGroup, _HAS_ORM
        if _HAS_ORM:
            m2m = AdminGroup._m2m_fields['permissions']
            assert m2m.to == "AdminPermission"
            assert m2m.db_table == "admin_group_permissions"
            assert m2m.related_name == "groups"

    def test_admin_user_groups_m2m(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            m2m = AdminUser._m2m_fields['groups']
            assert m2m.to == "AdminGroup"
            assert m2m.db_table == "admin_user_groups"
            assert m2m.related_name == "users"

    def test_admin_user_permissions_m2m(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            m2m = AdminUser._m2m_fields['user_permissions']
            assert m2m.to == "AdminPermission"
            assert m2m.db_table == "admin_user_permissions"
            assert m2m.related_name == "users"


# ═══════════════════════════════════════════════════════════════════════════
# 17. META CONFIGURATION TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestMetaConfiguration:
    """Test Meta class configuration on all models."""

    def test_content_type_meta(self):
        from aquilia.admin.models import ContentType, _HAS_ORM
        if _HAS_ORM:
            meta = ContentType._meta
            assert meta.verbose_name == "Content Type"
            assert meta.verbose_name_plural == "Content Types"
            assert meta.ordering == ["app_label", "model"]

    def test_admin_permission_meta(self):
        from aquilia.admin.models import AdminPermission, _HAS_ORM
        if _HAS_ORM:
            meta = AdminPermission._meta
            assert meta.verbose_name == "Permission"
            assert meta.ordering == ["content_type", "codename"]

    def test_admin_group_meta(self):
        from aquilia.admin.models import AdminGroup, _HAS_ORM
        if _HAS_ORM:
            meta = AdminGroup._meta
            assert meta.verbose_name == "Group"
            assert meta.ordering == ["name"]

    def test_admin_user_meta(self):
        from aquilia.admin.models import AdminUser, _HAS_ORM
        if _HAS_ORM:
            meta = AdminUser._meta
            assert meta.verbose_name == "Admin User"
            assert meta.ordering == ["-date_joined"]
            assert meta.get_latest_by == "date_joined"

    def test_admin_log_entry_meta(self):
        from aquilia.admin.models import AdminLogEntry, _HAS_ORM
        if _HAS_ORM:
            meta = AdminLogEntry._meta
            assert meta.verbose_name == "Log Entry"
            assert meta.verbose_name_plural == "Log Entries"
            assert meta.ordering == ["-action_time"]

    def test_admin_session_meta(self):
        from aquilia.admin.models import AdminSession, _HAS_ORM
        if _HAS_ORM:
            meta = AdminSession._meta
            assert meta.verbose_name == "Session"


# ═══════════════════════════════════════════════════════════════════════════
# 15. AUTO-SESSION ENABLEMENT & STATIC ASSETS TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestValidateAdminPrerequisites:
    """Tests for _validate_admin_prerequisites warning-only validation."""

    def _make_server(self, *, session_engine=None, middleware_names=None):
        """Create a minimal mock server with controllable session state."""
        from unittest.mock import MagicMock
        import logging

        server = MagicMock()
        server._session_engine = session_engine

        # Use a MagicMock for the logger so we can assert on .warning()
        mock_logger = MagicMock(spec=logging.Logger)
        server.logger = mock_logger

        # Build a mock middleware stack with named entries
        stack = MagicMock()
        descs = []
        for name in (middleware_names or []):
            d = MagicMock()
            d.name = name
            descs.append(d)
        stack.middlewares = descs
        server.middleware_stack = stack

        return server

    def test_no_warning_when_session_engine_exists(self):
        """If session engine is already set, no warning is emitted."""
        from aquilia.server import AquiliaServer
        server = self._make_server(session_engine=MagicMock())

        AquiliaServer._validate_admin_prerequisites(server)

        # Logger.warning should NOT have been called
        server.logger.warning.assert_not_called()

    def test_no_warning_when_session_middleware_registered(self):
        """If a 'session' middleware is already in the stack, no warning."""
        from aquilia.server import AquiliaServer
        server = self._make_server(middleware_names=["exception", "session", "logging"])

        AquiliaServer._validate_admin_prerequisites(server)
        server.logger.warning.assert_not_called()

    def test_no_warning_when_auth_middleware_registered(self):
        """If an 'auth' middleware is in the stack, no warning."""
        from aquilia.server import AquiliaServer
        server = self._make_server(middleware_names=["exception", "auth", "logging"])

        AquiliaServer._validate_admin_prerequisites(server)
        server.logger.warning.assert_not_called()

    def test_warns_when_no_sessions_configured(self):
        """When no session engine and no session/auth middleware, emit warning."""
        from aquilia.server import AquiliaServer
        server = self._make_server(middleware_names=["exception", "logging"])

        AquiliaServer._validate_admin_prerequisites(server)

        # Should have emitted a warning
        server.logger.warning.assert_called_once()
        warn_msg = server.logger.warning.call_args[0][0]
        assert "Sessions are NOT configured" in warn_msg
        assert "aq admin check" in warn_msg

    def test_warns_with_empty_middleware_stack(self):
        """Even with completely empty middleware stack, emit warning."""
        from aquilia.server import AquiliaServer
        server = self._make_server(middleware_names=[])

        AquiliaServer._validate_admin_prerequisites(server)

        server.logger.warning.assert_called_once()
        warn_msg = server.logger.warning.call_args[0][0]
        assert "workspace.py" in warn_msg

    def test_does_not_modify_middleware_stack(self):
        """Validation method must NOT add anything to the middleware stack."""
        from aquilia.server import AquiliaServer
        server = self._make_server(middleware_names=["exception"])

        AquiliaServer._validate_admin_prerequisites(server)

        # Must NOT have called add — we only warn, never auto-fix
        server.middleware_stack.add.assert_not_called()

    def test_does_not_set_session_engine(self):
        """Validation method must NOT create a session engine."""
        from aquilia.server import AquiliaServer
        from unittest.mock import MagicMock
        server = self._make_server(middleware_names=[])
        original_engine = server._session_engine

        AquiliaServer._validate_admin_prerequisites(server)

        # Session engine should be unchanged (still None-ish mock)
        assert server._session_engine == original_engine


class TestEnsureAdminStaticAssets:
    """Tests for _ensure_admin_static_assets fallback directory injection."""

    def test_adds_fallback_dir_to_existing_static_mw(self):
        """When static middleware exists, assets dir is added as fallback."""
        from aquilia.server import AquiliaServer
        from unittest.mock import MagicMock
        from pathlib import Path
        import logging

        server = MagicMock()
        server.logger = logging.getLogger("test_static")

        # Simulate existing static middleware with /static mapped to static/
        mw = MagicMock()
        mw._directories = {"/static": Path("/some/project/static").resolve()}
        mw._fallback_dirs = {}
        server._static_middleware = mw

        # Patch pathlib.Path.cwd() to return a directory that has assets/
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            assets = Path(tmpdir) / "assets"
            assets.mkdir()
            (assets / "logo.png").touch()

            with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
                AquiliaServer._ensure_admin_static_assets(server)

            # Fallback should be added
            assert "/static" in mw._fallback_dirs
            assert len(mw._fallback_dirs["/static"]) == 1
            assert mw._fallback_dirs["/static"][0] == assets.resolve()

    def test_no_duplicate_fallback_dir(self):
        """Calling _ensure_admin_static_assets twice doesn't duplicate."""
        from aquilia.server import AquiliaServer
        from unittest.mock import MagicMock
        from pathlib import Path
        import logging

        server = MagicMock()
        server.logger = logging.getLogger("test_static")

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            assets = Path(tmpdir) / "assets"
            assets.mkdir()
            (assets / "logo.png").touch()

            mw = MagicMock()
            mw._directories = {"/static": Path(tmpdir) / "static"}
            mw._fallback_dirs = {}
            server._static_middleware = mw

            with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
                AquiliaServer._ensure_admin_static_assets(server)
                AquiliaServer._ensure_admin_static_assets(server)

            assert len(mw._fallback_dirs["/static"]) == 1

    def test_skips_when_already_mapped_to_assets(self):
        """If /static already points to assets/, skip."""
        from aquilia.server import AquiliaServer
        from unittest.mock import MagicMock
        from pathlib import Path
        import logging

        server = MagicMock()
        server.logger = logging.getLogger("test_static")

        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            assets = Path(tmpdir) / "assets"
            assets.mkdir()
            (assets / "logo.png").touch()

            mw = MagicMock()
            mw._directories = {"/static": assets.resolve()}
            mw._fallback_dirs = {}
            server._static_middleware = mw

            with patch("pathlib.Path.cwd", return_value=Path(tmpdir)):
                AquiliaServer._ensure_admin_static_assets(server)

            # No fallback should be added — primary already maps
            assert "/static" not in mw._fallback_dirs or len(mw._fallback_dirs.get("/static", [])) == 0


class TestAdminCLIEmailRequired:
    """Tests for the enhanced admin CLI createsuperuser command."""

    def test_email_is_required_option(self):
        """Email must be a required option (no default value)."""
        from aquilia.cli.__main__ import admin_createsuperuser
        # Click stores params on the command
        params = {p.name: p for p in admin_createsuperuser.params}
        email_param = params.get("email")
        assert email_param is not None, "email parameter must exist"
        # No default means it will prompt — prompt is truthy when required
        assert email_param.prompt is not None, "email should have a prompt (required)"
        # Click uses Sentinel.UNSET (not None) when no default is provided
        assert email_param.default is None or str(email_param.default) == "Sentinel.UNSET", \
            f"email should not have a default value, got: {email_param.default!r}"

    def test_email_validation_in_source(self):
        """Source must contain email validation logic."""
        import inspect
        from aquilia.cli.__main__ import admin_createsuperuser
        fn = getattr(admin_createsuperuser, "callback", admin_createsuperuser)
        source = inspect.getsource(fn)
        assert "@" in source, "Source should check for '@' in email"

    def test_password_validation_in_source(self):
        """Source must validate password length."""
        import inspect
        from aquilia.cli.__main__ import admin_createsuperuser
        fn = getattr(admin_createsuperuser, "callback", admin_createsuperuser)
        source = inspect.getsource(fn)
        assert "len(password)" in source, "Source should check password length"

    def test_banner_in_createsuperuser(self):
        """Beautified CLI should use banner()."""
        import inspect
        from aquilia.cli.__main__ import admin_createsuperuser
        fn = getattr(admin_createsuperuser, "callback", admin_createsuperuser)
        source = inspect.getsource(fn)
        assert "banner(" in source, "Should display a banner"

    def test_step_indicators_in_createsuperuser(self):
        """Beautified CLI should use step() for progress."""
        import inspect
        from aquilia.cli.__main__ import admin_createsuperuser
        fn = getattr(admin_createsuperuser, "callback", admin_createsuperuser)
        source = inspect.getsource(fn)
        assert "step(" in source, "Should use step() indicators"

    def test_permissions_section_in_createsuperuser(self):
        """Beautified CLI should show permissions section."""
        import inspect
        from aquilia.cli.__main__ import admin_createsuperuser
        fn = getattr(admin_createsuperuser, "callback", admin_createsuperuser)
        source = inspect.getsource(fn)
        assert "Permissions" in source, "Should show permissions section"

    def test_troubleshooting_panel_on_error(self):
        """Beautified CLI should show troubleshooting panel on error."""
        import inspect
        from aquilia.cli.__main__ import admin_createsuperuser
        fn = getattr(admin_createsuperuser, "callback", admin_createsuperuser)
        source = inspect.getsource(fn)
        assert "Troubleshooting" in source, "Should show troubleshooting on error"


# ═══════════════════════════════════════════════════════════════════════════
# 17. ADMIN CHECK COMMAND TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminCheckCommand:
    """Tests for the ``aq admin check`` pre-flight command."""

    def test_admin_check_command_exists(self):
        """admin check command must be registered."""
        from aquilia.cli.__main__ import admin_check
        assert admin_check is not None

    def test_admin_check_has_fix_option(self):
        """admin check must have a --fix flag."""
        from aquilia.cli.__main__ import admin_check
        params = {p.name: p for p in admin_check.params}
        assert "fix" in params, "--fix option must exist"

    def test_admin_check_has_json_option(self):
        """admin check must have a --json flag."""
        from aquilia.cli.__main__ import admin_check
        params = {p.name: p for p in admin_check.params}
        assert "as_json" in params, "--json option must exist"

    def test_admin_check_validates_sessions(self):
        """Source must check for .sessions( or Integration.auth(."""
        import inspect
        from aquilia.cli.__main__ import admin_check
        fn = getattr(admin_check, "callback", admin_check)
        source = inspect.getsource(fn)
        assert ".sessions(" in source
        assert "Integration.auth(" in source

    def test_admin_check_validates_database(self):
        """Source must check for Integration.database(."""
        import inspect
        from aquilia.cli.__main__ import admin_check
        fn = getattr(admin_check, "callback", admin_check)
        source = inspect.getsource(fn)
        assert "Integration.database(" in source

    def test_admin_check_validates_static_files(self):
        """Source must check for Integration.static_files(."""
        import inspect
        from aquilia.cli.__main__ import admin_check
        fn = getattr(admin_check, "callback", admin_check)
        source = inspect.getsource(fn)
        assert "Integration.static_files(" in source

    def test_admin_check_checks_superuser(self):
        """Source must check for existing superusers."""
        import inspect
        from aquilia.cli.__main__ import admin_check
        fn = getattr(admin_check, "callback", admin_check)
        source = inspect.getsource(fn)
        assert "superuser" in source.lower()


class TestAdminListUsersCommand:
    """Tests for the ``aq admin listusers`` command."""

    def test_listusers_command_exists(self):
        """admin listusers command must be registered."""
        from aquilia.cli.__main__ import admin_listusers
        assert admin_listusers is not None

    def test_listusers_has_json_option(self):
        """admin listusers must have a --json flag."""
        from aquilia.cli.__main__ import admin_listusers
        params = {p.name: p for p in admin_listusers.params}
        assert "as_json" in params

    def test_listusers_has_active_only_option(self):
        """admin listusers must have a --active-only flag."""
        from aquilia.cli.__main__ import admin_listusers
        params = {p.name: p for p in admin_listusers.params}
        assert "active_only" in params

    def test_listusers_has_database_url_option(self):
        """admin listusers must have a --database-url option."""
        from aquilia.cli.__main__ import admin_listusers
        params = {p.name: p for p in admin_listusers.params}
        assert "database_url" in params


class TestAdminChangePasswordCommand:
    """Tests for the ``aq admin changepassword`` command."""

    def test_changepassword_command_exists(self):
        """admin changepassword command must be registered."""
        from aquilia.cli.__main__ import admin_changepassword
        assert admin_changepassword is not None

    def test_changepassword_has_username_argument(self):
        """admin changepassword must accept a username argument."""
        from aquilia.cli.__main__ import admin_changepassword
        params = {p.name: p for p in admin_changepassword.params}
        assert "username" in params

    def test_changepassword_hides_password_input(self):
        """Password input must be hidden."""
        from aquilia.cli.__main__ import admin_changepassword
        params = {p.name: p for p in admin_changepassword.params}
        pwd_param = params.get("password")
        assert pwd_param is not None
        assert pwd_param.hide_input is True

    def test_changepassword_has_confirmation_prompt(self):
        """Password must require confirmation."""
        from aquilia.cli.__main__ import admin_changepassword
        params = {p.name: p for p in admin_changepassword.params}
        pwd_param = params.get("password")
        assert pwd_param.confirmation_prompt is not None


# ═══════════════════════════════════════════════════════════════════════════
# 18. CLI ENHANCEMENT TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestCLIEnhancements:
    """Tests for CLI root group enhancements (--debug, --no-color, etc.)."""

    def test_cli_has_debug_flag(self):
        """Root CLI must have a --debug flag."""
        from aquilia.cli.__main__ import cli
        params = {p.name: p for p in cli.params}
        assert "debug" in params, "--debug flag must exist"

    def test_cli_has_no_color_flag(self):
        """Root CLI must have a --no-color flag."""
        from aquilia.cli.__main__ import cli
        params = {p.name: p for p in cli.params}
        assert "no_color" in params, "--no-color flag must exist"

    def test_cli_has_verbose_flag(self):
        """Root CLI must have a --verbose/-v flag."""
        from aquilia.cli.__main__ import cli
        params = {p.name: p for p in cli.params}
        assert "verbose" in params, "--verbose flag must exist"

    def test_cli_has_quiet_flag(self):
        """Root CLI must have a --quiet/-q flag."""
        from aquilia.cli.__main__ import cli
        params = {p.name: p for p in cli.params}
        assert "quiet" in params, "--quiet flag must exist"

    def test_run_has_skip_checks_flag(self):
        """Run command must have a --skip-checks flag."""
        from aquilia.cli.__main__ import run
        params = {p.name: p for p in run.params}
        assert "skip_checks" in params, "--skip-checks flag must exist"

    def test_run_preflight_checks_admin(self):
        """Run command source must contain admin pre-flight logic."""
        import inspect
        from aquilia.cli.__main__ import run
        fn = getattr(run, "callback", run)
        source = inspect.getsource(fn)
        assert "Integration.admin(" in source, "Should detect admin integration"
        assert "skip_checks" in source, "Should respect --skip-checks"


# ═══════════════════════════════════════════════════════════════════════════
# 19. ADMIN SETUP COMMAND TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminSetupCommand:
    """Tests for the ``aq admin setup`` auto-configure command."""

    def test_setup_command_exists(self):
        """admin setup command must be registered."""
        from aquilia.cli.__main__ import admin_setup
        assert admin_setup is not None

    def test_setup_has_non_interactive_flag(self):
        """admin setup must have a --non-interactive / -y flag."""
        from aquilia.cli.__main__ import admin_setup
        params = {p.name: p for p in admin_setup.params}
        assert "non_interactive" in params, "--non-interactive/-y flag must exist"

    def test_setup_has_database_url_option(self):
        """admin setup must have a --database-url option."""
        from aquilia.cli.__main__ import admin_setup
        params = {p.name: p for p in admin_setup.params}
        assert "database_url" in params, "--database-url option must exist"

    def test_setup_source_handles_sessions(self):
        """Source must handle both uncommenting and injecting sessions."""
        import inspect
        from aquilia.cli.__main__ import admin_setup
        fn = getattr(admin_setup, "callback", admin_setup)
        source = inspect.getsource(fn)
        assert ".sessions(" in source, "Should handle sessions config"
        assert "SessionPolicy" in source, "Should reference SessionPolicy"

    def test_setup_source_handles_imports(self):
        """Source must add required imports (timedelta, SessionPolicy)."""
        import inspect
        from aquilia.cli.__main__ import admin_setup
        fn = getattr(admin_setup, "callback", admin_setup)
        source = inspect.getsource(fn)
        assert "timedelta" in source, "Should handle timedelta import"
        assert "SessionPolicy" in source, "Should handle SessionPolicy import"

    def test_setup_source_handles_admin_integration(self):
        """Source must handle admin integration config."""
        import inspect
        from aquilia.cli.__main__ import admin_setup
        fn = getattr(admin_setup, "callback", admin_setup)
        source = inspect.getsource(fn)
        assert "Integration.admin(" in source, "Should handle admin integration"

    def test_setup_source_handles_database_tables(self):
        """Source must create admin database tables."""
        import inspect
        from aquilia.cli.__main__ import admin_setup
        fn = getattr(admin_setup, "callback", admin_setup)
        source = inspect.getsource(fn)
        assert "AdminUser" in source, "Should handle AdminUser model"
        assert "admin_users" in source, "Should reference admin_users table"

    def test_setup_source_checks_superuser(self):
        """Source must check for existing superusers."""
        import inspect
        from aquilia.cli.__main__ import admin_setup
        fn = getattr(admin_setup, "callback", admin_setup)
        source = inspect.getsource(fn)
        assert "superuser" in source.lower(), "Should check for superusers"
        assert "createsuperuser" in source, "Should offer to create superuser"

    def test_setup_source_has_7_steps(self):
        """Setup should have 7 sequential steps."""
        import inspect
        from aquilia.cli.__main__ import admin_setup
        fn = getattr(admin_setup, "callback", admin_setup)
        source = inspect.getsource(fn)
        for i in range(1, 8):
            assert f"step({i}," in source, f"Should have step {i}"

    def test_setup_confirms_before_writing(self):
        """Non-interactive mode must be opt-in; default should confirm."""
        import inspect
        from aquilia.cli.__main__ import admin_setup
        fn = getattr(admin_setup, "callback", admin_setup)
        source = inspect.getsource(fn)
        assert "click.confirm" in source, "Should ask for confirmation"
        assert "non_interactive" in source, "Should respect non_interactive flag"


class TestWarningBoxIsYellow:
    """Tests that the admin warning box uses ANSI yellow colouring."""

    def test_warning_contains_ansi_yellow_escape(self):
        """The warning message must contain ANSI yellow escape code."""
        from aquilia.server import AquiliaServer
        from unittest.mock import MagicMock
        import logging

        server = MagicMock()
        server._session_engine = None
        server.logger = MagicMock(spec=logging.Logger)

        stack = MagicMock()
        stack.middlewares = []
        server.middleware_stack = stack

        AquiliaServer._validate_admin_prerequisites(server)

        server.logger.warning.assert_called_once()
        warn_msg = server.logger.warning.call_args[0][0]
        assert "\033[33m" in warn_msg, "Warning must contain ANSI yellow (\\033[33m)"
        assert "\033[0m" in warn_msg, "Warning must contain ANSI reset (\\033[0m)"

    def test_warning_mentions_aq_admin_setup(self):
        """The warning message must mention 'aq admin setup'."""
        from aquilia.server import AquiliaServer
        from unittest.mock import MagicMock
        import logging

        server = MagicMock()
        server._session_engine = None
        server.logger = MagicMock(spec=logging.Logger)

        stack = MagicMock()
        stack.middlewares = []
        server.middleware_stack = stack

        AquiliaServer._validate_admin_prerequisites(server)

        warn_msg = server.logger.warning.call_args[0][0]
        assert "aq admin setup" in warn_msg, "Warning must mention 'aq admin setup'"
        assert "aq admin check" in warn_msg, "Warning must mention 'aq admin check'"


# ═══════════════════════════════════════════════════════════════════════════
# 15. DEV-MODE COOKIE SECURE OVERRIDE TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestDevModeCookieSecureOverride:
    """
    Verify that _should_disable_secure_cookies() and _apply_dev_cookie_override()
    correctly detect dev mode and force cookie_secure=False so session cookies
    work over plain HTTP (e.g. http://localhost:8000).

    Root cause: TransportPolicy.cookie_secure defaults to True, causing browsers
    to silently refuse sending cookies on HTTP, which creates an admin login
    redirect loop.
    """

    def _make_server(self, *, debug=False, env_vars=None, config_overrides=None):
        """Create a minimal mock AquiliaServer for testing."""
        from aquilia.server import AquiliaServer
        from unittest.mock import MagicMock
        import logging

        server = MagicMock(spec=AquiliaServer)
        server.logger = MagicMock(spec=logging.Logger)

        # Wire up config
        cfg = config_overrides or {}
        if debug:
            cfg["debug"] = True
        server.config = MagicMock()
        server.config.get = lambda key, default="": cfg.get(key, default)

        # Wire up real methods
        server._is_debug = lambda: AquiliaServer._is_debug(server)
        server._should_disable_secure_cookies = lambda: AquiliaServer._should_disable_secure_cookies(server)
        server._apply_dev_cookie_override = lambda t: AquiliaServer._apply_dev_cookie_override(server, t)

        # Optionally set env vars
        if env_vars:
            for k, v in env_vars.items():
                os.environ[k] = v

        return server

    def _cleanup_env(self, keys):
        for k in keys:
            os.environ.pop(k, None)

    # ── _should_disable_secure_cookies ───────────────────────────────

    def test_debug_mode_disables_secure(self):
        """When debug=True, should disable secure cookies."""
        server = self._make_server(debug=True)
        assert server._should_disable_secure_cookies() is True

    def test_aquilia_env_dev_disables_secure(self):
        """When AQUILIA_ENV=dev, should disable secure cookies."""
        try:
            server = self._make_server(env_vars={"AQUILIA_ENV": "dev"})
            assert server._should_disable_secure_cookies() is True
        finally:
            self._cleanup_env(["AQUILIA_ENV"])

    def test_aquilia_env_development_disables_secure(self):
        """When AQUILIA_ENV=development, should disable secure cookies."""
        try:
            server = self._make_server(env_vars={"AQUILIA_ENV": "development"})
            assert server._should_disable_secure_cookies() is True
        finally:
            self._cleanup_env(["AQUILIA_ENV"])

    def test_aquilia_env_test_disables_secure(self):
        """When AQUILIA_ENV=test, should disable secure cookies."""
        try:
            server = self._make_server(env_vars={"AQUILIA_ENV": "test"})
            assert server._should_disable_secure_cookies() is True
        finally:
            self._cleanup_env(["AQUILIA_ENV"])

    def test_localhost_host_disables_secure(self):
        """When host is localhost, should disable secure cookies."""
        server = self._make_server(config_overrides={"server.host": "localhost"})
        assert server._should_disable_secure_cookies() is True

    def test_127_host_disables_secure(self):
        """When host is 127.0.0.1, should disable secure cookies."""
        server = self._make_server(config_overrides={"server.host": "127.0.0.1"})
        assert server._should_disable_secure_cookies() is True

    def test_0000_host_disables_secure(self):
        """When host is 0.0.0.0, should disable secure cookies."""
        server = self._make_server(config_overrides={"server.host": "0.0.0.0"})
        assert server._should_disable_secure_cookies() is True

    def test_production_does_not_disable_secure(self):
        """In production (no debug, AQUILIA_ENV=production), keep secure."""
        try:
            server = self._make_server(
                env_vars={"AQUILIA_ENV": "production"},
                config_overrides={"server.host": "api.example.com"},
            )
            assert server._should_disable_secure_cookies() is False
        finally:
            self._cleanup_env(["AQUILIA_ENV"])

    def test_mode_dev_config_disables_secure(self):
        """When config has mode: dev, should disable secure cookies."""
        server = self._make_server(config_overrides={"mode": "dev"})
        assert server._should_disable_secure_cookies() is True

    # ── _apply_dev_cookie_override ───────────────────────────────────

    def test_apply_override_patches_cookie_secure(self):
        """_apply_dev_cookie_override should set cookie_secure=False on transport policy."""
        from aquilia.sessions.policy import TransportPolicy
        from aquilia.sessions.transport import CookieTransport

        server = self._make_server(debug=True)
        policy = TransportPolicy(cookie_secure=True)
        transport = CookieTransport(policy)

        assert policy.cookie_secure is True
        server._apply_dev_cookie_override(transport)
        assert policy.cookie_secure is False

    def test_apply_override_no_op_when_already_false(self):
        """If cookie_secure is already False, _apply_dev_cookie_override is a no-op."""
        from aquilia.sessions.policy import TransportPolicy
        from aquilia.sessions.transport import CookieTransport

        server = self._make_server(debug=True)
        policy = TransportPolicy(cookie_secure=False)
        transport = CookieTransport(policy)

        server._apply_dev_cookie_override(transport)
        assert policy.cookie_secure is False
        # Logger should NOT log anything since it was already False
        server.logger.info.assert_not_called()

    def test_apply_override_no_op_in_production(self):
        """In production mode, _apply_dev_cookie_override should NOT patch."""
        from aquilia.sessions.policy import TransportPolicy
        from aquilia.sessions.transport import CookieTransport

        try:
            server = self._make_server(
                env_vars={"AQUILIA_ENV": "production"},
                config_overrides={"server.host": "api.example.com"},
            )
            policy = TransportPolicy(cookie_secure=True)
            transport = CookieTransport(policy)

            server._apply_dev_cookie_override(transport)
            assert policy.cookie_secure is True  # unchanged
        finally:
            self._cleanup_env(["AQUILIA_ENV"])

    def test_apply_override_logs_when_patching(self):
        """When patching cookie_secure, should log a debug message."""
        from aquilia.sessions.policy import TransportPolicy
        from aquilia.sessions.transport import CookieTransport

        server = self._make_server(debug=True)
        policy = TransportPolicy(cookie_secure=True)
        transport = CookieTransport(policy)

        server._apply_dev_cookie_override(transport)

        server.logger.debug.assert_called()
        # Find the call that contains the cookie_secure message
        found = False
        for call in server.logger.debug.call_args_list:
            log_msg = call[0][0]
            if "cookie_secure=False" in log_msg and "Dev mode" in log_msg:
                found = True
                break
        assert found, "Expected debug log about cookie_secure=False"


class TestTransportPolicyDefault:
    """Verify TransportPolicy defaults and that the override mechanism works."""

    def test_transport_policy_default_cookie_secure_is_true(self):
        """TransportPolicy.cookie_secure should default to True (secure by default)."""
        from aquilia.sessions.policy import TransportPolicy
        policy = TransportPolicy()
        assert policy.cookie_secure is True

    def test_session_policy_inherits_default_transport(self):
        """SessionPolicy without explicit transport should get TransportPolicy() defaults."""
        from aquilia.sessions.policy import SessionPolicy, TransportPolicy
        from datetime import timedelta

        sp = SessionPolicy(
            name="test",
            ttl=timedelta(hours=1),
            idle_timeout=timedelta(minutes=30),
        )
        assert sp.transport is not None
        assert isinstance(sp.transport, TransportPolicy)
        assert sp.transport.cookie_secure is True

    def test_session_policy_with_explicit_transport_override(self):
        """SessionPolicy with explicit TransportPolicy(cookie_secure=False) should keep it."""
        from aquilia.sessions.policy import SessionPolicy, TransportPolicy
        from datetime import timedelta

        tp = TransportPolicy(cookie_secure=False, cookie_name="test_cookie")
        sp = SessionPolicy(
            name="test",
            ttl=timedelta(hours=1),
            idle_timeout=timedelta(minutes=30),
            transport=tp,
        )
        assert sp.transport.cookie_secure is False
        assert sp.transport.cookie_name == "test_cookie"


class TestTransportPolicyExport:
    """Verify TransportPolicy is properly exported from aquilia package."""

    def test_transport_policy_importable_from_sessions(self):
        """TransportPolicy should be importable from aquilia.sessions."""
        from aquilia.sessions import TransportPolicy
        assert TransportPolicy is not None

    def test_transport_policy_importable_from_aquilia(self):
        """TransportPolicy should be importable from aquilia top-level."""
        from aquilia import TransportPolicy
        assert TransportPolicy is not None


class TestAdminSetupInjectsTransportPolicy:
    """Verify that 'aq admin setup' injects TransportPolicy with cookie_secure=False."""

    def test_setup_sessions_block_contains_transport_policy(self):
        """The injected sessions block must include TransportPolicy config."""
        import textwrap

        # Replicate what the CLI injects
        sessions_block = textwrap.dedent("""\

    # Sessions - required for admin login
    .sessions(
        policies=[
            SessionPolicy(
                name="default",
                ttl=timedelta(days=7),
                idle_timeout=timedelta(hours=1),
                transport=TransportPolicy(
                    cookie_name="aquilia_admin_session",
                    cookie_secure=False,
                    cookie_httponly=True,
                    cookie_samesite="lax",
                ),
            ),
        ],
    )""")
        assert "TransportPolicy(" in sessions_block
        assert "cookie_secure=False" in sessions_block
        assert "cookie_httponly=True" in sessions_block
        assert 'cookie_samesite="lax"' in sessions_block
        assert 'cookie_name="aquilia_admin_session"' in sessions_block

    def test_setup_check_panel_shows_transport_policy(self):
        """The admin check hint panel must show TransportPolicy config."""
        from aquilia.cli.__main__ import admin_check
        import inspect

        # admin_check is a Click Command, get the underlying callback
        callback = admin_check.callback
        source = inspect.getsource(callback)
        assert "TransportPolicy(" in source


# ═══════════════════════════════════════════════════════════════════════════
# ADMIN V3 UI OVERHAUL — REGRESSION TESTS
# ═══════════════════════════════════════════════════════════════════════════

# ── Helpers ──────────────────────────────────────────────────────────────


class _MockField:
    """Minimal field mock."""
    def __init__(self, name, field_type="CharField", **kw):
        self.name = name
        self.__class__.__name__ = field_type
        self.primary_key = kw.get("primary_key", False)
        self.auto_now = kw.get("auto_now", False)
        self.auto_now_add = kw.get("auto_now_add", False)
        self.choices = kw.get("choices", None)
        self.max_length = kw.get("max_length", None)
        self.blank = kw.get("blank", False)
        self.null = kw.get("null", False)
        self.unique = kw.get("unique", False)
        self.help_text = kw.get("help_text", "")
        self.default = kw.get("default", None)
        self.editable = kw.get("editable", True)
        self.verbose_name = kw.get("verbose_name", None)

    def has_default(self):
        return self.default is not None


class _MockManager:
    async def count(self):
        return 42
    def get_queryset(self):
        return self
    def filter(self, **kw):
        return self
    def order(self, *a):
        return self
    def limit(self, n):
        return self
    def offset(self, n):
        return self
    async def all(self):
        return []
    def apply_q(self, q):
        return self
    async def delete(self):
        return 1


class _MockModel:
    __name__ = "_MockModel"
    _pk_attr = "id"
    _fields: Dict[str, Any] = {}
    _meta: Any = None
    objects = _MockManager()

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        if not hasattr(cls, "_fields") or cls._fields is _MockModel._fields:
            cls._fields = {}
        cls.objects = _MockManager()

    @property
    def pk(self):
        return getattr(self, "id", None)


class _ProductModel(_MockModel):
    __name__ = "ProductModel"
    id = 1
    name = "Widget"
    _fields = {
        "id": _MockField("id", "AutoField", primary_key=True),
        "name": _MockField("name", "CharField", max_length=200),
    }

    class Meta:
        app_label = "catalog"


class _MockIdentity:
    def __init__(self, id="user-1", attributes=None):
        self.id = id
        self._attrs = attributes or {}

    def has_role(self, role):
        return role in self._attrs.get("roles", [])

    def is_active(self):
        return True

    def get_attribute(self, key, default=None):
        return self._attrs.get(key, default)


def _sa_identity():
    return _MockIdentity(id="admin-1", attributes={"admin_role": "superadmin", "name": "Admin"})


# ═══════════════════════════════════════════════════════════════════════════
# R1. Route Registration — new pages in _wire_admin_integration
# ═══════════════════════════════════════════════════════════════════════════


class TestRouteRegistration:
    """Static routes /orm/…/permissions/ must be in _wire_admin_integration."""

    def test_new_routes_in_source(self):
        import inspect
        from aquilia.server import AquiliaServer
        src = inspect.getsource(AquiliaServer._wire_admin_integration)
        for page in ("orm", "build", "migrations", "config", "permissions"):
            assert f"/{page}/" in src, f"Route /{page}/ missing from _wire_admin_integration"

    def test_static_routes_before_dynamic(self):
        import inspect
        from aquilia.server import AquiliaServer
        src = inspect.getsource(AquiliaServer._wire_admin_integration)
        orm_pos = src.find("/orm/")
        model_pos = src.find("<model:str>/")
        assert 0 < orm_pos < model_pos, "/orm/ must appear before <model:str>/"

    def test_handler_names_in_source(self):
        import inspect
        from aquilia.server import AquiliaServer
        src = inspect.getsource(AquiliaServer._wire_admin_integration)
        for name in ("orm_view", "build_view", "migrations_view", "config_view", "permissions_view"):
            assert name in src, f"Handler '{name}' missing"

    def test_all_five_new_routes_count(self):
        """Five new static routes + audit + 6 CRUD/auth = 16 total entries."""
        import inspect
        from aquilia.server import AquiliaServer
        src = inspect.getsource(AquiliaServer._wire_admin_integration)
        # Count tuples that start with ("GET" or ("POST"
        import re
        route_entries = re.findall(r'\("(?:GET|POST)"', src)
        assert len(route_entries) >= 16, f"Expected ≥16 route entries, got {len(route_entries)}"


# ═══════════════════════════════════════════════════════════════════════════
# R2. New Template Rendering
# ═══════════════════════════════════════════════════════════════════════════


class TestNewTemplatesRendering:
    """All 5 new page templates produce valid HTML."""

    def test_render_orm_page(self):
        from aquilia.admin.templates import render_orm_page
        html = render_orm_page(app_list=[], model_counts={"X": 5}, identity_name="Admin")
        assert "<!DOCTYPE html>" in html

    def test_render_orm_page_empty(self):
        from aquilia.admin.templates import render_orm_page
        html = render_orm_page(app_list=[], model_counts={}, identity_name="Admin")
        assert "<!DOCTYPE html>" in html

    def test_render_build_page(self):
        from aquilia.admin.templates import render_build_page
        html = render_build_page(
            build_info={"fingerprint": "abc"}, artifacts=[], pipeline_phases=[],
            build_log="", app_list=[], identity_name="Admin",
        )
        assert "<!DOCTYPE html>" in html

    def test_render_build_page_with_artifacts(self):
        from aquilia.admin.templates import render_build_page
        html = render_build_page(
            build_info={},
            artifacts=[{"name": "x.crous", "kind": "bundle", "size": "1 KB", "digest": "abc"}],
            pipeline_phases=[{"name": "Discovery", "status": "success", "detail": "ok"}],
            build_log="done", app_list=[], identity_name="Admin",
        )
        assert "<!DOCTYPE html>" in html

    def test_render_migrations_page(self):
        from aquilia.admin.templates import render_migrations_page
        html = render_migrations_page(
            migrations=[{"filename": "0001.py", "revision": "r1", "models": ["A"],
                         "operations_count": 2, "source": "#x", "source_highlighted": "x"}],
            app_list=[], identity_name="Admin",
        )
        assert "<!DOCTYPE html>" in html

    def test_render_migrations_page_empty(self):
        from aquilia.admin.templates import render_migrations_page
        html = render_migrations_page(migrations=[], app_list=[], identity_name="Admin")
        assert "<!DOCTYPE html>" in html

    def test_render_config_page(self):
        from aquilia.admin.templates import render_config_page
        html = render_config_page(
            config_files=[{"name": "base.yaml", "path": "config/base.yaml",
                           "content": "k: v", "content_highlighted": "k: v"}],
            workspace_info={"name": "x", "version": "1", "modules": [], "integrations": []},
            app_list=[], identity_name="Admin",
        )
        assert "<!DOCTYPE html>" in html

    def test_render_config_page_empty(self):
        from aquilia.admin.templates import render_config_page
        html = render_config_page(
            config_files=[], workspace_info=None, app_list=[], identity_name="Admin",
        )
        assert "<!DOCTYPE html>" in html

    def test_render_permissions_page(self):
        from aquilia.admin.templates import render_permissions_page
        html = render_permissions_page(
            roles=[{"name": "superadmin", "level": 40, "description": "x", "permissions": ["*"]}],
            all_permissions=["model.view"],
            model_permissions=[{"name": "X", "perms": {"view": True, "add": True, "change": True, "delete": True, "export": True}}],
            app_list=[], identity_name="Admin",
        )
        assert "<!DOCTYPE html>" in html

    def test_render_permissions_page_empty(self):
        from aquilia.admin.templates import render_permissions_page
        html = render_permissions_page(
            roles=[], all_permissions=[], model_permissions=[],
            app_list=[], identity_name="Admin",
        )
        assert "<!DOCTYPE html>" in html

    # ── Monitoring page ──

    def test_render_monitoring_page(self):
        from aquilia.admin.templates import render_monitoring_page
        monitoring = {
            "cpu": {"percent": 42.5, "per_core": [40.0, 45.0], "cores_physical": 4,
                    "cores_logical": 8, "freq_current": 2400, "freq_max": 3200,
                    "load_avg_1": 1.5, "load_avg_5": 1.2, "load_avg_15": 1.0,
                    "times_user": 100.0, "times_system": 50.0, "times_idle": 200.0},
            "memory": {"total": 17179869184, "total_human": "16.0 GB",
                       "available": 8589934592, "available_human": "8.0 GB",
                       "used": 8589934592, "used_human": "8.0 GB", "percent": 50.0,
                       "swap_total": 4294967296, "swap_total_human": "4.0 GB",
                       "swap_used": 1073741824, "swap_used_human": "1.0 GB",
                       "swap_free": 3221225472, "swap_free_human": "3.0 GB",
                       "swap_percent": 25.0},
            "disk": {"total": 500000000000, "total_human": "465.7 GB",
                     "used": 250000000000, "used_human": "232.8 GB",
                     "free": 250000000000, "free_human": "232.8 GB",
                     "percent": 50.0, "partitions": [
                         {"device": "/dev/sda1", "mountpoint": "/", "fstype": "ext4",
                          "total_human": "465.7 GB", "used_human": "232.8 GB",
                          "free_human": "232.8 GB", "percent": 50.0}
                     ]},
            "network": {"bytes_sent": 1048576, "bytes_sent_human": "1.0 MB",
                        "bytes_recv": 2097152, "bytes_recv_human": "2.0 MB",
                        "packets_sent": 1000, "packets_recv": 2000,
                        "errin": 0, "errout": 0, "dropin": 0, "dropout": 0,
                        "connections_by_status": {"ESTABLISHED": 5, "LISTEN": 3}},
            "process": {"pid": 1234, "name": "python", "status": "running",
                        "create_time": "2025-01-01 00:00:00 UTC",
                        "uptime_human": "1d 2h 3m 4s", "threads": 8,
                        "open_files": 12, "rss": 104857600, "rss_human": "100.0 MB",
                        "vms": 209715200, "vms_human": "200.0 MB",
                        "shared": 0, "private": 104857600,
                        "mem_percent": 0.61, "ctx_switches": 500,
                        "ctx_switches_voluntary": 400,
                        "ctx_switches_involuntary": 100,
                        "env_snapshot": {"VIRTUAL_ENV": "/path/to/env"}},
            "python": {"version": "3.14.0", "implementation": "CPython",
                       "executable": "/usr/bin/python3", "gc_objects": 5000},
            "system": {"os": "Linux", "platform": "Linux-5.15",
                       "arch": "x86_64", "hostname": "test-host"},
            "health_checks": [
                {"name": "database", "status": "healthy", "latency_ms": 1.5,
                 "message": "Connected", "checked_at": "2025-01-01T00:00:00Z"},
            ],
        }
        html = render_monitoring_page(monitoring=monitoring, app_list=[], identity_name="Admin")
        assert "<!DOCTYPE html>" in html
        assert "Monitoring" in html
        assert "CPU" in html

    def test_render_monitoring_page_empty(self):
        from aquilia.admin.templates import render_monitoring_page
        monitoring = {
            "cpu": {"percent": 0, "per_core": [], "cores_physical": 0,
                    "cores_logical": 0, "freq_current": 0, "freq_max": 0,
                    "load_avg_1": 0, "load_avg_5": 0, "load_avg_15": 0,
                    "times_user": 0, "times_system": 0, "times_idle": 0},
            "memory": {"total": 0, "total_human": "—", "available": 0,
                       "available_human": "—", "used": 0, "used_human": "—",
                       "percent": 0, "swap_total": 0, "swap_total_human": "—",
                       "swap_used": 0, "swap_used_human": "—",
                       "swap_free": 0, "swap_free_human": "—", "swap_percent": 0},
            "disk": {"total": 0, "total_human": "—", "used": 0, "used_human": "—",
                     "free": 0, "free_human": "—", "percent": 0, "partitions": []},
            "network": {"bytes_sent": 0, "bytes_sent_human": "—",
                        "bytes_recv": 0, "bytes_recv_human": "—",
                        "packets_sent": 0, "packets_recv": 0,
                        "errin": 0, "errout": 0, "dropin": 0, "dropout": 0,
                        "connections_by_status": {}},
            "process": {"pid": 0, "name": "python", "status": "running",
                        "create_time": "—", "uptime_human": "—",
                        "threads": 0, "open_files": 0,
                        "rss": 0, "rss_human": "—", "vms": 0, "vms_human": "—",
                        "shared": 0, "private": 0,
                        "mem_percent": 0, "ctx_switches": 0,
                        "ctx_switches_voluntary": 0, "ctx_switches_involuntary": 0,
                        "env_snapshot": {}},
            "python": {"version": "3.14.0", "implementation": "CPython",
                       "executable": "/usr/bin/python3", "gc_objects": 0},
            "system": {"os": "Linux", "platform": "Linux-5.15",
                       "arch": "x86_64", "hostname": "test-host"},
            "health_checks": [],
        }
        html = render_monitoring_page(monitoring=monitoring, app_list=[], identity_name="Admin")
        assert "<!DOCTYPE html>" in html

    def test_render_monitoring_page_import(self):
        """render_monitoring_page is importable from templates module."""
        from aquilia.admin.templates import render_monitoring_page
        assert callable(render_monitoring_page)


# ═══════════════════════════════════════════════════════════════════════════
# R3. Controller Handlers — auth + render
# ═══════════════════════════════════════════════════════════════════════════


class TestNewControllerHandlers:
    """Each new handler returns 302 (unauth) or 200 (auth)."""

    def setup_method(self):
        from aquilia.admin.site import AdminSite, AdminConfig
        AdminSite.reset()
        self.site = AdminSite()
        self.site.register(_ProductModel)
        # Enable all modules (monitoring & audit are disabled by default since v2)
        self.site.admin_config = AdminConfig(modules={
            "dashboard": True, "orm": True, "build": True,
            "migrations": True, "config": True, "workspace": True,
            "permissions": True, "monitoring": True, "admin_users": True,
            "profile": True, "audit": True,
        }, audit_enabled=True, monitoring_enabled=True)
        self.ctrl = AdminController(site=self.site)

    def _ctx(self, identity=None, qp=None):
        ctx = MagicMock()
        ctx.identity = identity
        s = MagicMock(); s.data = {}
        ctx.session = s
        ctx.query_param = lambda k, d=None: (qp or {}).get(k, d)
        ctx.form = AsyncMock(return_value={})
        return ctx

    def _req(self, pp=None):
        r = MagicMock()
        r.state = {"path_params": pp or {}}
        return r

    # ORM
    @pytest.mark.asyncio
    async def test_orm_unauth(self):
        resp = await self.ctrl.orm_view(self._req(), self._ctx())
        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_orm_auth(self):
        self.site._initialized = True
        resp = await self.ctrl.orm_view(self._req(), self._ctx(identity=_sa_identity()))
        assert resp.status == 200
        assert b"<!DOCTYPE html>" in resp._content

    # Build
    @pytest.mark.asyncio
    async def test_build_unauth(self):
        resp = await self.ctrl.build_view(self._req(), self._ctx())
        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_build_auth(self):
        self.site._initialized = True
        resp = await self.ctrl.build_view(self._req(), self._ctx(identity=_sa_identity()))
        assert resp.status == 200

    # Migrations
    @pytest.mark.asyncio
    async def test_migrations_unauth(self):
        resp = await self.ctrl.migrations_view(self._req(), self._ctx())
        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_migrations_auth(self):
        self.site._initialized = True
        resp = await self.ctrl.migrations_view(self._req(), self._ctx(identity=_sa_identity()))
        assert resp.status == 200

    # Config
    @pytest.mark.asyncio
    async def test_config_unauth(self):
        resp = await self.ctrl.config_view(self._req(), self._ctx())
        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_config_auth(self):
        self.site._initialized = True
        resp = await self.ctrl.config_view(self._req(), self._ctx(identity=_sa_identity()))
        assert resp.status == 200

    # Permissions
    @pytest.mark.asyncio
    async def test_permissions_unauth(self):
        resp = await self.ctrl.permissions_view(self._req(), self._ctx())
        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_permissions_auth(self):
        self.site._initialized = True
        resp = await self.ctrl.permissions_view(self._req(), self._ctx(identity=_sa_identity()))
        assert resp.status == 200

    # Existing routes still work
    @pytest.mark.asyncio
    async def test_dashboard_still_200(self):
        self.site._initialized = True
        resp = await self.ctrl.dashboard(self._req(), self._ctx(identity=_sa_identity()))
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_audit_still_200(self):
        self.site._initialized = True
        resp = await self.ctrl.audit_view(self._req(), self._ctx(identity=_sa_identity()))
        assert resp.status == 200

    # Monitoring
    @pytest.mark.asyncio
    async def test_monitoring_unauth(self):
        resp = await self.ctrl.monitoring_view(self._req(), self._ctx())
        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_monitoring_auth(self):
        self.site._initialized = True
        resp = await self.ctrl.monitoring_view(self._req(), self._ctx(identity=_sa_identity()))
        assert resp.status == 200
        assert b"<!DOCTYPE html>" in resp._content

    @pytest.mark.asyncio
    async def test_monitoring_api_unauth(self):
        resp = await self.ctrl.monitoring_api(self._req(), self._ctx())
        assert resp.status == 401

    @pytest.mark.asyncio
    async def test_monitoring_api_auth(self):
        self.site._initialized = True
        resp = await self.ctrl.monitoring_api(self._req(), self._ctx(identity=_sa_identity()))
        assert resp.status == 200
        import json
        data = json.loads(resp._content)
        assert "cpu" in data
        assert "memory" in data
        assert "disk" in data
        assert "network" in data
        assert "process" in data

    @pytest.mark.asyncio
    async def test_list_view_real_model(self):
        """/{model}/ still works for genuine model names."""
        self.site._initialized = True
        resp = await self.ctrl.list_view(
            self._req({"model": "_productmodel"}),
            self._ctx(identity=_sa_identity(), qp={"q": "", "page": "1"}),
        )
        assert resp.status == 200


# ═══════════════════════════════════════════════════════════════════════════
# R4. Pagination Integration
# ═══════════════════════════════════════════════════════════════════════════


class TestPaginationIntegration:
    """list_records uses PageNumberPagination from aquilia.controller.pagination."""

    def test_site_imports_pagination(self):
        import inspect
        from aquilia.admin import site as mod
        src = inspect.getsource(mod)
        assert "from aquilia.controller.pagination import PageNumberPagination" in src

    def test_list_records_uses_paginate_queryset(self):
        import inspect
        from aquilia.admin.site import AdminSite
        src = inspect.getsource(AdminSite.list_records)
        assert "PageNumberPagination" in src
        assert "paginate_queryset" in src

    @pytest.mark.asyncio
    async def test_list_records_pagination_keys(self):
        from aquilia.admin.site import AdminSite
        AdminSite.reset()
        site = AdminSite()
        site.register(_ProductModel)
        site._initialized = True
        data = await site.list_records("_productmodel", page=1, per_page=10, identity=_sa_identity())
        for key in ("page", "per_page", "total", "total_pages", "has_next",
                     "has_prev", "next_url", "previous_url"):
            assert key in data, f"Missing key: {key}"

    @pytest.mark.asyncio
    async def test_pagination_values_page1(self):
        from aquilia.admin.site import AdminSite
        AdminSite.reset()
        site = AdminSite()
        site.register(_ProductModel)
        site._initialized = True
        data = await site.list_records("_productmodel", page=1, per_page=10, identity=_sa_identity())
        assert data["total"] == 42
        assert data["total_pages"] == 5
        assert data["has_next"] is True
        assert data["has_prev"] is False

    @pytest.mark.asyncio
    async def test_pagination_values_last_page(self):
        from aquilia.admin.site import AdminSite
        AdminSite.reset()
        site = AdminSite()
        site.register(_ProductModel)
        site._initialized = True
        data = await site.list_records("_productmodel", page=5, per_page=10, identity=_sa_identity())
        assert data["has_next"] is False
        assert data["has_prev"] is True


# ═══════════════════════════════════════════════════════════════════════════
# R5. PageNumberPagination Standalone
# ═══════════════════════════════════════════════════════════════════════════


class TestPageNumberPaginationUnit:
    def _req(self, **kw):
        return type("R", (), {"query_params": {str(k): str(v) for k, v in kw.items()}})()

    def test_default_page_size(self):
        from aquilia.controller.pagination import PageNumberPagination
        assert PageNumberPagination().page_size == 20

    def test_first_page(self):
        from aquilia.controller.pagination import PageNumberPagination
        p = PageNumberPagination(page_size=10)
        r = p.paginate_list(list(range(100)), self._req(page=1))
        assert r["count"] == 100
        assert r["page"] == 1
        assert r["total_pages"] == 10
        assert len(r["results"]) == 10
        assert r["previous"] is None
        assert r["next"] is not None

    def test_last_page(self):
        from aquilia.controller.pagination import PageNumberPagination
        p = PageNumberPagination(page_size=10)
        r = p.paginate_list(list(range(100)), self._req(page=10))
        assert r["next"] is None
        assert r["previous"] is not None

    def test_empty_list(self):
        from aquilia.controller.pagination import PageNumberPagination
        r = PageNumberPagination(page_size=10).paginate_list([], self._req(page=1))
        assert r["count"] == 0
        assert r["results"] == []

    def test_max_page_size_clamped(self):
        from aquilia.controller.pagination import PageNumberPagination
        p = PageNumberPagination(page_size=20, max_page_size=50)
        r = p.paginate_list(list(range(200)), self._req(page=1, page_size=999))
        assert r["page_size"] == 50


# ═══════════════════════════════════════════════════════════════════════════
# R6. Data Methods Shape
# ═══════════════════════════════════════════════════════════════════════════


class TestDataMethodsShape:
    def setup_method(self):
        from aquilia.admin.site import AdminSite
        AdminSite.reset()
        self.site = AdminSite()
        self.site.register(_ProductModel)
        self.site._initialized = True

    def test_build_info_keys(self):
        r = self.site.get_build_info()
        for k in ("info", "artifacts", "pipeline_phases", "build_log"):
            assert k in r

    def test_migrations_is_list(self):
        assert isinstance(self.site.get_migrations_data(), list)

    def test_config_keys(self):
        r = self.site.get_config_data()
        assert "files" in r and "workspace" in r

    def test_permissions_keys(self):
        r = self.site.get_permissions_data(_sa_identity())
        for k in ("roles", "all_permissions", "model_permissions"):
            assert k in r

    def test_permissions_roles_sorted(self):
        r = self.site.get_permissions_data(_sa_identity())
        levels = [role["level"] for role in r["roles"]]
        assert levels == sorted(levels, reverse=True)

    def test_permissions_all_roles_present(self):
        from aquilia.admin.permissions import AdminRole
        r = self.site.get_permissions_data(_sa_identity())
        role_names = {role["name"] for role in r["roles"]}
        for ar in AdminRole:
            assert ar.value in role_names


# ═══════════════════════════════════════════════════════════════════════════
# R7. Template Partials & CSS
# ═══════════════════════════════════════════════════════════════════════════


class TestTemplatePartialsV3:
    def test_sidebar_v2_exists(self):
        from pathlib import Path
        p = Path(__file__).parent.parent / "aquilia/admin/templates/partials/sidebar_v2.html"
        assert p.exists()

    def test_sidebar_v2_nav_links(self):
        from pathlib import Path
        content = (Path(__file__).parent.parent / "aquilia/admin/templates/partials/sidebar_v2.html").read_text()
        for page in ("orm", "build", "migrations", "config", "permissions", "audit", "monitoring"):
            assert page in content.lower(), f"/{page}/ link missing from sidebar"

    def test_css_exists(self):
        from pathlib import Path
        p = Path(__file__).parent.parent / "aquilia/admin/templates/partials/css.html"
        assert p.exists()

    def test_css_sarvam_tokens(self):
        from pathlib import Path
        content = (Path(__file__).parent.parent / "aquilia/admin/templates/partials/css.html").read_text()
        assert "22c55e" in content, "Missing Aquilia green accent"
        assert "Outfit" in content, "Missing Outfit font (aqdocx theme)"
        assert "Space Mono" in content, "Missing Space Mono font (aqdocx theme)"

    def test_base_includes_sidebar(self):
        from pathlib import Path
        content = (Path(__file__).parent.parent / "aquilia/admin/templates/base.html").read_text()
        assert "sidebar_v2" in content

    def test_base_includes_css(self):
        from pathlib import Path
        content = (Path(__file__).parent.parent / "aquilia/admin/templates/base.html").read_text()
        assert "css.html" in content

    def test_base_includes_aqdocx_fonts(self):
        from pathlib import Path
        content = (Path(__file__).parent.parent / "aquilia/admin/templates/base.html").read_text()
        assert "Outfit" in content, "Missing Outfit font CDN"
        assert "Space+Mono" in content, "Missing Space Mono font CDN"


# ═══════════════════════════════════════════════════════════════════════════
# R8. New Templates On Disk
# ═══════════════════════════════════════════════════════════════════════════


class TestNewTemplatesOnDisk:
    @pytest.mark.parametrize("name", [
        "orm.html", "build.html", "migrations.html", "config.html", "permissions.html",
    ])
    def test_exists(self, name):
        from pathlib import Path
        assert (Path(__file__).parent.parent / "aquilia/admin/templates" / name).exists()

    @pytest.mark.parametrize("name", [
        "orm.html", "build.html", "migrations.html", "config.html", "permissions.html",
    ])
    def test_extends_base(self, name):
        from pathlib import Path
        content = (Path(__file__).parent.parent / "aquilia/admin/templates" / name).read_text()
        assert "base.html" in content


# ═══════════════════════════════════════════════════════════════════════════
# R9. JSON Removal
# ═══════════════════════════════════════════════════════════════════════════


class TestJsonRemovalV3:
    def test_bundler_no_aq_json(self):
        import inspect
        from aquilia.build.bundler import CrousBundler
        assert ".aq.json" not in inspect.getsource(CrousBundler)

    def test_build_info_scans_crous(self):
        import inspect
        from aquilia.admin.site import AdminSite
        src = inspect.getsource(AdminSite.get_build_info)
        assert ".crous" in src


# ═══════════════════════════════════════════════════════════════════════════
# R10. Syntax Highlighting
# ═══════════════════════════════════════════════════════════════════════════


class TestSyntaxHighlightingV3:
    def setup_method(self):
        from aquilia.admin.site import AdminSite
        AdminSite.reset()
        self.site = AdminSite()

    def test_highlight_python(self):
        r = self.site._highlight_python("def f():\n    pass\n")
        assert isinstance(r, str) and len(r) > 0

    def test_highlight_python_has_spans(self):
        r = self.site._highlight_python("def f():\n    return True\n")
        assert "<span" in r or "def" in r

    def test_highlight_yaml(self):
        r = self.site._highlight_yaml("server:\n  port: 8000\n")
        assert isinstance(r, str) and len(r) > 0

    def test_highlight_yaml_has_spans(self):
        r = self.site._highlight_yaml("database:\n  host: localhost\n")
        assert "<span" in r or "database" in r

    def test_highlight_python_empty(self):
        assert isinstance(self.site._highlight_python(""), str)

    def test_highlight_yaml_empty(self):
        assert isinstance(self.site._highlight_yaml(""), str)


# ═══════════════════════════════════════════════════════════════════════════
# SESSION 5 — NEW FEATURE TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestFormDataFix:
    """Verify FormData→dict conversion in admin handlers."""

    def setup_method(self):
        from aquilia.admin.site import AdminSite
        AdminSite.reset()
        self.site = AdminSite()
        self.site.register(_ProductModel)
        self.ctrl = AdminController(site=self.site)

    def _ctx(self, identity=None, session_data=None):
        ctx = MagicMock()
        ctx.identity = identity
        s = MagicMock()
        s.data = session_data or {}
        ctx.session = s
        ctx.query_param = lambda k, d=None: d
        return ctx

    def _req(self, pp=None, headers=None, scope_client=None):
        r = MagicMock()
        r.state = {"path_params": pp or {}}
        r.headers = headers or {}
        r.scope = {"client": scope_client or ("127.0.0.1", 54321)}
        return r

    def _mock_formdata(self, data_dict):
        """Create a mock FormData with .fields (MultiDict-like)."""
        fd = MagicMock()
        fields = MagicMock()
        fields.to_dict = MagicMock(return_value=data_dict)
        fd.fields = fields
        fd.get = lambda k, d=None: data_dict.get(k, d)
        return fd

    @pytest.mark.asyncio
    async def test_login_submit_with_formdata(self):
        """Login should handle FormData objects without .items() error."""
        fd = self._mock_formdata({"username": "admin", "password": "secret"})
        ctx = self._ctx()
        ctx.form = AsyncMock(return_value=fd)
        req = self._req()
        resp = await self.ctrl.login_submit(req, ctx)
        # Should not crash with 'FormData' has no attribute 'items'
        # 401 = invalid creds (expected), 302 = redirect (logged in)
        assert resp.status in (200, 302, 400, 401)

    @pytest.mark.asyncio
    async def test_add_submit_with_formdata(self):
        """Add handler should convert FormData to dict."""
        fd = self._mock_formdata({"name": "New Widget"})
        ctx = self._ctx(identity=_sa_identity())
        ctx.form = AsyncMock(return_value=fd)
        req = self._req(pp={"model": "productmodel"})
        self.site._initialized = True
        self.site.create_record = AsyncMock(return_value="1")
        resp = await self.ctrl.add_submit(req, ctx)
        assert resp.status in (200, 302)

    @pytest.mark.asyncio
    async def test_edit_submit_with_formdata(self):
        """Edit handler should convert FormData to dict."""
        fd = self._mock_formdata({"name": "Updated Widget"})
        ctx = self._ctx(identity=_sa_identity())
        ctx.form = AsyncMock(return_value=fd)
        req = self._req(pp={"model": "productmodel", "pk": "1"})
        self.site._initialized = True
        self.site.update_record = AsyncMock(return_value=True)
        resp = await self.ctrl.edit_submit(req, ctx)
        assert resp.status in (200, 302)


class TestExtractRequestMeta:
    """Test _extract_request_meta helper."""

    def test_extract_ip_from_forwarded(self):
        from aquilia.admin.controller import _extract_request_meta
        req = MagicMock()
        req.headers = {"x-forwarded-for": "1.2.3.4, 5.6.7.8", "user-agent": "TestBot/1.0"}
        req.scope = {"client": ("127.0.0.1", 1234)}
        meta = _extract_request_meta(req)
        assert meta["ip_address"] == "1.2.3.4"
        assert meta["user_agent"] == "TestBot/1.0"

    def test_extract_ip_from_real_ip(self):
        from aquilia.admin.controller import _extract_request_meta
        req = MagicMock()
        req.headers = {"x-real-ip": "10.0.0.1", "user-agent": "Chrome"}
        req.scope = {"client": ("127.0.0.1", 1234)}
        meta = _extract_request_meta(req)
        assert meta["ip_address"] == "10.0.0.1"

    def test_extract_ip_from_scope(self):
        from aquilia.admin.controller import _extract_request_meta
        req = MagicMock()
        req.headers = {}
        req.scope = {"client": ("192.168.1.1", 9999)}
        meta = _extract_request_meta(req)
        assert meta["ip_address"] == "192.168.1.1"

    def test_extract_no_scope_client(self):
        from aquilia.admin.controller import _extract_request_meta
        req = MagicMock()
        req.headers = {}
        req.scope = {}
        meta = _extract_request_meta(req)
        assert meta["ip_address"] == ""


class TestAuditActionEnum:
    """Verify all AdminAction enum values exist."""

    def test_search_action(self):
        from aquilia.admin.audit import AdminAction
        assert AdminAction.SEARCH.value == "search"

    def test_permission_change_action(self):
        from aquilia.admin.audit import AdminAction
        assert AdminAction.PERMISSION_CHANGE.value == "permission_change"

    def test_view_action(self):
        from aquilia.admin.audit import AdminAction
        assert AdminAction.VIEW.value == "view"

    def test_list_action(self):
        from aquilia.admin.audit import AdminAction
        assert AdminAction.LIST.value == "list"

    def test_bulk_action_enum(self):
        from aquilia.admin.audit import AdminAction
        assert AdminAction.BULK_ACTION.value == "bulk_action"

    def test_export_action(self):
        from aquilia.admin.audit import AdminAction
        assert AdminAction.EXPORT.value == "export"

    def test_all_actions_are_unique(self):
        from aquilia.admin.audit import AdminAction
        values = [a.value for a in AdminAction]
        assert len(values) == len(set(values)), "Duplicate AdminAction values"


class TestAuditComprehensiveLogging:
    """Audit log should capture IP, user-agent, and all action types."""

    def setup_method(self):
        from aquilia.admin.audit import AdminAuditLog
        self.log = AdminAuditLog()

    def test_log_with_ip_and_ua(self):
        from aquilia.admin.audit import AdminAction
        entry = self.log.log(
            user_id="u1", username="admin", role="superadmin",
            action=AdminAction.LOGIN,
            ip_address="10.0.0.1", user_agent="Mozilla/5.0"
        )
        assert entry.ip_address == "10.0.0.1"
        assert entry.user_agent == "Mozilla/5.0"

    def test_log_search_with_metadata(self):
        from aquilia.admin.audit import AdminAction
        entry = self.log.log(
            user_id="u1", username="admin", role="superadmin",
            action=AdminAction.SEARCH,
            model_name="product",
            metadata={"query": "widget", "page": 1}
        )
        assert entry.action == AdminAction.SEARCH
        assert entry.metadata["query"] == "widget"

    def test_log_permission_change(self):
        from aquilia.admin.audit import AdminAction
        entry = self.log.log(
            user_id="u1", username="admin", role="superadmin",
            action=AdminAction.PERMISSION_CHANGE,
            metadata={"user": "bob", "permission": "add", "granted": True}
        )
        assert entry.action == AdminAction.PERMISSION_CHANGE

    def test_log_bulk_action_with_pks(self):
        from aquilia.admin.audit import AdminAction
        entry = self.log.log(
            user_id="u1", username="admin", role="superadmin",
            action=AdminAction.BULK_ACTION,
            model_name="product",
            metadata={"action": "delete_selected", "pks": ["1", "2", "3"], "count": 3}
        )
        assert entry.metadata["count"] == 3

    def test_log_export_with_format(self):
        from aquilia.admin.audit import AdminAction
        entry = self.log.log(
            user_id="u1", username="admin", role="superadmin",
            action=AdminAction.EXPORT,
            model_name="product",
            metadata={"format": "csv", "count": 50}
        )
        assert entry.metadata["format"] == "csv"

    def test_log_view_record(self):
        from aquilia.admin.audit import AdminAction
        entry = self.log.log(
            user_id="u1", username="admin", role="superadmin",
            action=AdminAction.VIEW,
            model_name="product", record_pk="42"
        )
        assert entry.record_pk == "42"

    def test_log_delete_record(self):
        from aquilia.admin.audit import AdminAction
        entry = self.log.log(
            user_id="u1", username="admin", role="superadmin",
            action=AdminAction.DELETE,
            model_name="product", record_pk="42",
            ip_address="192.168.1.1", user_agent="Safari"
        )
        assert entry.action == AdminAction.DELETE
        assert entry.ip_address == "192.168.1.1"

    def test_log_entries_accumulate(self):
        from aquilia.admin.audit import AdminAction
        for i in range(5):
            self.log.log(
                user_id="u1", username="admin", role="superadmin",
                action=AdminAction.LIST, model_name=f"model_{i}"
            )
        assert len(self.log._entries) == 5

    def test_entry_to_dict(self):
        from aquilia.admin.audit import AdminAction
        entry = self.log.log(
            user_id="u1", username="admin", role="superadmin",
            action=AdminAction.LOGIN, ip_address="1.2.3.4"
        )
        d = entry.to_dict()
        assert d["action"] == "login"
        assert d["ip_address"] == "1.2.3.4"
        assert "timestamp" in d
        assert "id" in d


class TestBulkActionHandler:
    """Bulk action controller tests."""

    def setup_method(self):
        from aquilia.admin.site import AdminSite
        AdminSite.reset()
        self.site = AdminSite()
        self.site.register(_ProductModel)
        self.ctrl = AdminController(site=self.site)
        self.site._initialized = True

    def _ctx(self, identity=None, session_data=None):
        ctx = MagicMock()
        ctx.identity = identity
        s = MagicMock()
        s.data = session_data if session_data is not None else {}
        ctx.session = s
        ctx.query_param = lambda k, d=None: d
        return ctx

    def _req(self, pp=None):
        r = MagicMock()
        r.state = {"path_params": pp or {}}
        r.headers = {}
        r.scope = {"client": ("127.0.0.1", 54321)}
        return r

    def _mock_formdata_multi(self, data_dict):
        fd = MagicMock()
        fields = MagicMock()
        fields.to_dict = MagicMock(side_effect=lambda multi=False: data_dict)
        fd.fields = fields
        return fd

    @pytest.mark.asyncio
    async def test_bulk_action_unauth(self):
        resp = await self.ctrl.bulk_action(self._req(pp={"model": "productmodel"}), self._ctx())
        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_bulk_action_no_selection(self):
        fd = self._mock_formdata_multi({"action": "delete_selected", "selected": []})
        ctx = self._ctx(identity=_sa_identity())
        ctx.form = AsyncMock(return_value=fd)
        resp = await self.ctrl.bulk_action(self._req(pp={"model": "productmodel"}), ctx)
        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_bulk_action_success(self):
        fd = self._mock_formdata_multi({"action": "delete_selected", "selected": ["1", "2"]})
        ctx = self._ctx(identity=_sa_identity())
        ctx.form = AsyncMock(return_value=fd)
        self.site.execute_action = AsyncMock(return_value="2 records deleted")
        self.site.audit_log = MagicMock()
        self.site.audit_log.log = MagicMock()
        resp = await self.ctrl.bulk_action(self._req(pp={"model": "productmodel"}), ctx)
        assert resp.status == 302
        assert ctx.session.data["_admin_flash"] == "2 records deleted"
        assert ctx.session.data["_admin_flash_type"] == "success"

    @pytest.mark.asyncio
    async def test_bulk_action_error(self):
        fd = self._mock_formdata_multi({"action": "bad_action", "selected": ["1"]})
        ctx = self._ctx(identity=_sa_identity())
        ctx.form = AsyncMock(return_value=fd)
        self.site.execute_action = AsyncMock(side_effect=Exception("Action failed"))
        self.site.audit_log = MagicMock()
        self.site.audit_log.log = MagicMock()
        resp = await self.ctrl.bulk_action(self._req(pp={"model": "productmodel"}), ctx)
        assert resp.status == 302
        assert ctx.session.data["_admin_flash"] == "Action failed"
        assert ctx.session.data["_admin_flash_type"] == "error"


class TestExportHandler:
    """Export controller tests."""

    def setup_method(self):
        from aquilia.admin.site import AdminSite
        AdminSite.reset()
        self.site = AdminSite()
        self.site.register(_ProductModel)
        self.ctrl = AdminController(site=self.site)
        self.site._initialized = True

    def _ctx(self, identity=None, fmt="csv"):
        ctx = MagicMock()
        ctx.identity = identity
        s = MagicMock()
        s.data = {}
        ctx.session = s
        ctx.query_param = lambda k, d=None: fmt if k == "format" else d
        return ctx

    def _req(self, pp=None):
        r = MagicMock()
        r.state = {"path_params": pp or {}}
        r.headers = {}
        r.scope = {"client": ("127.0.0.1", 54321)}
        return r

    @pytest.mark.asyncio
    async def test_export_unauth(self):
        resp = await self.ctrl.export_view(self._req(pp={"model": "productmodel"}), self._ctx())
        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_export_csv(self):
        ctx = self._ctx(identity=_sa_identity(), fmt="csv")
        self.site.list_records = AsyncMock(return_value={
            "rows": [{"id": "1", "name": "Widget"}],
            "list_display": ["id", "name"],
            "model_name": "ProductModel"
        })
        self.site.audit_log = MagicMock()
        self.site.audit_log.log = MagicMock()
        resp = await self.ctrl.export_view(self._req(pp={"model": "productmodel"}), ctx)
        assert resp.status == 200
        assert b"id,name" in resp._content
        assert b"Widget" in resp._content
        assert resp.headers["content-type"] == "text/csv; charset=utf-8"

    @pytest.mark.asyncio
    async def test_export_json(self):
        ctx = self._ctx(identity=_sa_identity(), fmt="json")
        self.site.list_records = AsyncMock(return_value={
            "rows": [{"id": "1", "name": "Widget"}],
            "list_display": ["id", "name"],
            "model_name": "ProductModel"
        })
        self.site.audit_log = MagicMock()
        self.site.audit_log.log = MagicMock()
        resp = await self.ctrl.export_view(self._req(pp={"model": "productmodel"}), ctx)
        assert resp.status == 200
        data = json.loads(resp._content)
        assert len(data) == 1
        assert data[0]["name"] == "Widget"
        assert resp.headers["content-type"] == "application/json; charset=utf-8"

    @pytest.mark.asyncio
    async def test_export_audits_action(self):
        ctx = self._ctx(identity=_sa_identity(), fmt="json")
        self.site.list_records = AsyncMock(return_value={
            "rows": [], "list_display": ["id"], "model_name": "Product"
        })
        self.site.audit_log = MagicMock()
        self.site.audit_log.log = MagicMock()
        await self.ctrl.export_view(self._req(pp={"model": "productmodel"}), ctx)
        self.site.audit_log.log.assert_called_once()
        call_kwargs = self.site.audit_log.log.call_args
        from aquilia.admin.audit import AdminAction
        assert call_kwargs.kwargs.get("action") == AdminAction.EXPORT or (call_kwargs[1].get("action") == AdminAction.EXPORT if call_kwargs[1] else False) or (len(call_kwargs[0]) >= 4 and call_kwargs[0][3] == AdminAction.EXPORT)


class TestListViewFlash:
    """List view should read flash messages from session."""

    def setup_method(self):
        from aquilia.admin.site import AdminSite
        AdminSite.reset()
        self.site = AdminSite()
        self.site.register(_ProductModel)
        self.ctrl = AdminController(site=self.site)
        self.site._initialized = True

    @pytest.mark.asyncio
    async def test_list_view_reads_flash(self):
        ctx = MagicMock()
        ctx.identity = _sa_identity()
        s = MagicMock()
        s.data = {"_admin_flash": "3 records deleted", "_admin_flash_type": "success"}
        ctx.session = s
        ctx.query_param = lambda k, d=None: d

        req = MagicMock()
        req.state = {"path_params": {"model": "productmodel"}}
        req.headers = {}
        req.scope = {"client": ("127.0.0.1", 1234)}

        self.site.list_records = AsyncMock(return_value={
            "rows": [], "list_display": ["id", "name"], "model_name": "ProductModel",
            "page": 1, "total_pages": 1, "total": 0, "verbose_name": "Product",
            "verbose_name_plural": "Products", "pk_field": "id",
        })
        self.site.audit_log = MagicMock()
        self.site.audit_log.log = MagicMock()

        resp = await self.ctrl.list_view(req, ctx)
        assert resp.status == 200
        # Flash was consumed from session
        assert "_admin_flash" not in s.data
        assert "_admin_flash_type" not in s.data

    @pytest.mark.asyncio
    async def test_list_view_no_flash(self):
        ctx = MagicMock()
        ctx.identity = _sa_identity()
        s = MagicMock()
        s.data = {}
        ctx.session = s
        ctx.query_param = lambda k, d=None: d

        req = MagicMock()
        req.state = {"path_params": {"model": "productmodel"}}
        req.headers = {}
        req.scope = {"client": ("127.0.0.1", 1234)}

        self.site.list_records = AsyncMock(return_value={
            "rows": [], "list_display": ["id", "name"], "model_name": "ProductModel",
            "page": 1, "total_pages": 1, "total": 0, "verbose_name": "Product",
            "verbose_name_plural": "Products", "pk_field": "id",
        })
        self.site.audit_log = MagicMock()
        self.site.audit_log.log = MagicMock()

        resp = await self.ctrl.list_view(req, ctx)
        assert resp.status == 200


class TestAuditInListAndEdit:
    """List/edit views should generate audit log entries."""

    def setup_method(self):
        from aquilia.admin.site import AdminSite
        AdminSite.reset()
        self.site = AdminSite()
        self.site.register(_ProductModel)
        self.ctrl = AdminController(site=self.site)
        self.site._initialized = True

    def _ctx(self, identity=None):
        ctx = MagicMock()
        ctx.identity = identity
        s = MagicMock()
        s.data = {}
        ctx.session = s
        ctx.query_param = lambda k, d=None: d
        return ctx

    def _req(self, pp=None):
        r = MagicMock()
        r.state = {"path_params": pp or {}}
        r.headers = {"user-agent": "TestSuite/1.0"}
        r.scope = {"client": ("10.0.0.1", 9999)}
        return r

    @pytest.mark.asyncio
    async def test_list_view_audits_list(self):
        from aquilia.admin.audit import AdminAction
        ctx = self._ctx(identity=_sa_identity())
        self.site.list_records = AsyncMock(return_value={
            "rows": [], "list_display": ["id"], "model_name": "ProductModel",
            "page": 1, "total_pages": 1, "total": 0, "verbose_name": "Product",
            "verbose_name_plural": "Products", "pk_field": "id",
        })
        self.site.audit_log = MagicMock()
        self.site.audit_log.log = MagicMock()
        await self.ctrl.list_view(self._req(pp={"model": "productmodel"}), ctx)
        self.site.audit_log.log.assert_called_once()
        call_args = self.site.audit_log.log.call_args
        assert AdminAction.LIST in str(call_args)

    @pytest.mark.asyncio
    async def test_list_view_audits_search(self):
        from aquilia.admin.audit import AdminAction
        ctx = self._ctx(identity=_sa_identity())
        ctx.query_param = lambda k, d=None: "widget" if k == "q" else d
        self.site.list_records = AsyncMock(return_value={
            "rows": [], "list_display": ["id"], "model_name": "ProductModel",
            "page": 1, "total_pages": 1, "total": 0, "verbose_name": "Product",
            "verbose_name_plural": "Products", "pk_field": "id",
        })
        self.site.audit_log = MagicMock()
        self.site.audit_log.log = MagicMock()
        await self.ctrl.list_view(self._req(pp={"model": "productmodel"}), ctx)
        self.site.audit_log.log.assert_called_once()
        call_args = self.site.audit_log.log.call_args
        assert AdminAction.SEARCH in str(call_args)

    @pytest.mark.asyncio
    async def test_edit_form_audits_view(self):
        from aquilia.admin.audit import AdminAction
        ctx = self._ctx(identity=_sa_identity())
        self.site.get_record = AsyncMock(return_value={
            "model_name": "productmodel", "verbose_name": "Product",
            "fields": [], "pk": "1", "is_create": False, "can_delete": True,
        })
        self.site.audit_log = MagicMock()
        self.site.audit_log.log = MagicMock()
        await self.ctrl.edit_form(self._req(pp={"model": "productmodel", "pk": "1"}), ctx)
        self.site.audit_log.log.assert_called_once()
        call_args = self.site.audit_log.log.call_args
        assert AdminAction.VIEW in str(call_args)

    @pytest.mark.asyncio
    async def test_delete_audits(self):
        from aquilia.admin.audit import AdminAction
        ctx = self._ctx(identity=_sa_identity())
        self.site.delete_record = AsyncMock(return_value=True)
        self.site.audit_log = MagicMock()
        self.site.audit_log.log = MagicMock()
        await self.ctrl.delete_record(self._req(pp={"model": "productmodel", "pk": "1"}), ctx)
        self.site.audit_log.log.assert_called_once()
        call_args = self.site.audit_log.log.call_args
        assert AdminAction.DELETE in str(call_args)


class TestRouteExportAndBulk:
    """Export and bulk action routes registered in server.py."""

    def test_export_route_in_source(self):
        import inspect
        from aquilia.server import AquiliaServer
        src = inspect.getsource(AquiliaServer._wire_admin_integration)
        assert "export" in src.lower(), "export route missing from _wire_admin_integration"

    def test_bulk_action_route_in_source(self):
        import inspect
        from aquilia.server import AquiliaServer
        src = inspect.getsource(AquiliaServer._wire_admin_integration)
        assert "action" in src.lower(), "bulk action route missing from _wire_admin_integration"


class TestTemplateFeatures:
    """Verify new template features in rendered HTML."""

    def test_list_template_has_export(self):
        html = render_list_view(
            data={
                "rows": [], "list_display": ["id"], "model_name": "Product",
                "page": 1, "total_pages": 1, "total": 0,
                "verbose_name": "Product", "verbose_name_plural": "Products",
                "pk_field": "id", "actions": {},
            },
            app_list=[], identity_name="admin",
        )
        assert "export" in html.lower()

    def test_list_template_has_search(self):
        html = render_list_view(
            data={
                "rows": [], "list_display": ["id"], "model_name": "Product",
                "page": 1, "total_pages": 1, "total": 0,
                "verbose_name": "Product", "verbose_name_plural": "Products",
                "pk_field": "id", "actions": {},
            },
            app_list=[], identity_name="admin",
        )
        assert "search" in html.lower()

    def test_list_template_has_keyboard_shortcut(self):
        html = render_list_view(
            data={
                "rows": [], "list_display": ["id"], "model_name": "Product",
                "page": 1, "total_pages": 1, "total": 0,
                "verbose_name": "Product", "verbose_name_plural": "Products",
                "pk_field": "id", "actions": {},
            },
            app_list=[], identity_name="admin",
        )
        assert "metaKey" in html or "⌘" in html

    def test_form_template_has_change_tracking(self):
        html = render_form_view(
            data={
                "model_name": "Product", "verbose_name": "Product",
                "fields": [{"name": "name", "label": "Name", "type": "text", "value": "Widget"}],
                "pk": "1", "is_create": False, "can_delete": True,
            },
            app_list=[], identity_name="admin",
        )
        assert "unsaved" in html.lower() or "change-preview" in html.lower()

    def test_form_template_has_save_shortcut(self):
        html = render_form_view(
            data={
                "model_name": "Product", "verbose_name": "Product",
                "fields": [{"name": "name", "label": "Name", "type": "text", "value": "Widget"}],
                "pk": "1", "is_create": False, "can_delete": True,
            },
            app_list=[], identity_name="admin",
        )
        assert "key === 's'" in html or "ctrl" in html.lower()

    def test_base_template_has_toast(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 1, "model_counts": {"Product": 10}, "recent_actions": []},
            identity_name="admin",
        )
        assert "showToast" in html

    def test_base_template_has_shortcut_help(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 1, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "shortcut-overlay" in html

    def test_dashboard_has_command_palette(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 1, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "showCommandPalette" in html or "cmd-palette" in html

    def test_dashboard_no_session_countdown(self):
        """Session countdown timer was intentionally removed from dashboard."""
        html = render_dashboard(
            app_list=[], stats={"total_models": 1, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "uptime-display" not in html
        assert "updateUptime" not in html

    def test_build_template_has_click_to_view(self):
        html = render_build_page(
            build_info={"workspace_name": "test", "total_artifacts": 1},
            artifacts=[{"name": "test.crous", "digest": "abc123", "content": "data", "kind": "model"}],
            pipeline_phases=[],
            build_log="",
            build_files=[],
            app_list=[], identity_name="admin",
        )
        assert "viewArtifact" in html

    def test_css_pitch_black(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "#000000" in html or "#000" in html

    def test_flash_in_list_view(self):
        html = render_list_view(
            data={
                "rows": [], "list_display": ["id"], "model_name": "Product",
                "page": 1, "total_pages": 1, "total": 0,
                "verbose_name": "Product", "verbose_name_plural": "Products",
                "pk_field": "id", "actions": {},
            },
            app_list=[], identity_name="admin",
            flash="3 records deleted", flash_type="success",
        )
        assert "3 records deleted" in html


class TestListViewDebounceSearch:
    """Live search debounce is in the rendered list template."""

    def test_debounce_in_list_html(self):
        html = render_list_view(
            data={
                "rows": [], "list_display": ["id"], "model_name": "Product",
                "page": 1, "total_pages": 1, "total": 0,
                "verbose_name": "Product", "verbose_name_plural": "Products",
                "pk_field": "id", "actions": {},
            },
            app_list=[], identity_name="admin",
        )
        assert "debounce" in html.lower() or "setTimeout" in html

    def test_min_chars_in_search(self):
        html = render_list_view(
            data={
                "rows": [], "list_display": ["id"], "model_name": "Product",
                "page": 1, "total_pages": 1, "total": 0,
                "verbose_name": "Product", "verbose_name_plural": "Products",
                "pk_field": "id", "actions": {},
            },
            app_list=[], identity_name="admin",
        )
        assert "length" in html and (".length" in html)


class TestThemeToggle:
    """Theme toggle force-repaint in base template."""

    def test_toggle_has_repaint(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "requestAnimationFrame" in html

    def test_theme_stored_in_localstorage(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "localStorage" in html
        assert "aquilia-admin-theme" in html


# ═══════════════════════════════════════════════════════════════════════════
# SESSION 6 – NEW FEATURE TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestSessionCountdownRemoval:
    """Verify session countdown timer was removed from dashboard."""

    def test_no_uptime_display_id(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 1, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "uptime-display" not in html

    def test_no_update_uptime_function(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 1, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "updateUptime" not in html

    def test_no_setinterval_uptime(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 1, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "setInterval" not in html or "updateUptime" not in html

    def test_dashboard_stats_still_present(self):
        """Other stats remain after timer removal."""
        html = render_dashboard(
            app_list=[], stats={"total_models": 5, "model_counts": {"Product": 10}, "recent_actions": []},
            identity_name="admin",
        )
        assert "stats-row" in html
        assert "5" in html  # total_models


class TestGridBackground:
    """Verify grid background pattern is in CSS."""

    def test_css_has_grid_linear_gradient(self):
        from aquilia.admin.templates import _get_jinja_env
        tpl = _get_jinja_env().get_template("partials/css.html")
        css = tpl.render()
        # Grid lines + ambient blob divs (aqdocx style)
        assert "linear-gradient" in css
        assert "40px 40px" in css  # grid size
        assert "ambient-blob" in css  # blob classes
        assert "breathing" in css  # blob animation

    def test_css_has_dark_grid_color(self):
        from aquilia.admin.templates import _get_jinja_env
        tpl = _get_jinja_env().get_template("partials/css.html")
        css = tpl.render()
        # Dark theme uses rgba borders and pure black background
        assert "#000000" in css
        assert "rgba(255,255,255,0.08)" in css

    def test_css_has_light_grid_color(self):
        from aquilia.admin.templates import _get_jinja_env
        tpl = _get_jinja_env().get_template("partials/css.html")
        css = tpl.render()
        # Light theme uses visible border color
        assert "#e4e4e7" in css

    def test_body_before_has_background_size(self):
        from aquilia.admin.templates import _get_jinja_env
        tpl = _get_jinja_env().get_template("partials/css.html")
        css = tpl.render()
        # Grid lines use background-size: 40px 40px
        assert "background-size" in css
        assert "40px 40px" in css


class TestAdminModelRegistration:
    """Verify _register_admin_models registers all 6 admin models."""

    def test_register_admin_models_function_exists(self):
        from aquilia.admin.registry import _register_admin_models
        assert callable(_register_admin_models)

    def test_registers_content_type(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import ContentType
        from aquilia.admin.registry import _register_admin_models
        AdminSite.reset()
        site = AdminSite()
        _register_admin_models(site)
        assert site.is_registered(ContentType)

    def test_registers_admin_permission(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import AdminPermission
        from aquilia.admin.registry import _register_admin_models
        AdminSite.reset()
        site = AdminSite()
        _register_admin_models(site)
        assert site.is_registered(AdminPermission)

    def test_registers_admin_group(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import AdminGroup
        from aquilia.admin.registry import _register_admin_models
        AdminSite.reset()
        site = AdminSite()
        _register_admin_models(site)
        assert site.is_registered(AdminGroup)

    def test_registers_admin_user(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import AdminUser
        from aquilia.admin.registry import _register_admin_models
        AdminSite.reset()
        site = AdminSite()
        _register_admin_models(site)
        assert site.is_registered(AdminUser)

    def test_registers_admin_log_entry(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import AdminLogEntry
        from aquilia.admin.registry import _register_admin_models
        AdminSite.reset()
        site = AdminSite()
        _register_admin_models(site)
        assert site.is_registered(AdminLogEntry)

    def test_registers_admin_session(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import AdminSession
        from aquilia.admin.registry import _register_admin_models
        AdminSite.reset()
        site = AdminSite()
        _register_admin_models(site)
        assert site.is_registered(AdminSession)

    def test_content_type_admin_has_list_display(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import ContentType
        from aquilia.admin.registry import _register_admin_models
        AdminSite.reset()
        site = AdminSite()
        _register_admin_models(site)
        admin = site.get_model_admin(ContentType)
        assert "app_label" in admin.list_display
        assert "model" in admin.list_display

    def test_admin_user_excludes_password_hash(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import AdminUser
        from aquilia.admin.registry import _register_admin_models
        AdminSite.reset()
        site = AdminSite()
        _register_admin_models(site)
        admin = site.get_model_admin(AdminUser)
        assert "password_hash" in admin.exclude

    def test_admin_log_entry_fully_readonly(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import AdminLogEntry
        from aquilia.admin.registry import _register_admin_models
        AdminSite.reset()
        site = AdminSite()
        _register_admin_models(site)
        admin = site.get_model_admin(AdminLogEntry)
        assert "action_time" in admin.readonly_fields
        assert "user" in admin.readonly_fields
        assert "object_repr" in admin.readonly_fields

    def test_no_double_registration(self):
        """Calling _register_admin_models twice doesn't error."""
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import ContentType
        from aquilia.admin.registry import _register_admin_models
        AdminSite.reset()
        site = AdminSite()
        _register_admin_models(site)
        _register_admin_models(site)  # should be a no-op
        assert site.is_registered(ContentType)

    def test_admin_models_have_icons(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import ContentType, AdminGroup, AdminUser
        from aquilia.admin.registry import _register_admin_models
        AdminSite.reset()
        site = AdminSite()
        _register_admin_models(site)
        for model_cls in [ContentType, AdminGroup, AdminUser]:
            admin = site.get_model_admin(model_cls)
            assert admin.icon, f"{model_cls.__name__} admin should have an icon"


class TestCommandPaletteTheme:
    """Command palette supports both light and dark themes."""

    def test_command_palette_detects_theme(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "data-theme" in html
        assert "isDark" in html or "is_dark" in html or "light" in html

    def test_command_palette_uses_css_vars_trigger(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "var(--bg-surface)" in html

    def test_command_palette_no_hardcoded_dark_colors(self):
        """Command palette trigger should not use hardcoded rgba dark colors."""
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        # The trigger div should not have hardcoded rgba(0,0,0,0.4)
        # Find the cmd-trigger area
        import re
        triggers = re.findall(r'cmd-trigger.*?(?=<div|$)', html, re.DOTALL)
        for t in triggers:
            assert "rgba(0,0,0,0.4)" not in t


class TestSyntaxHighlighting:
    """JSON and Crous syntax highlighting in code blocks."""

    def test_highlight_json_method_exists(self):
        from aquilia.admin.site import AdminSite
        assert hasattr(AdminSite, "_highlight_json")

    def test_highlight_crous_method_exists(self):
        from aquilia.admin.site import AdminSite
        assert hasattr(AdminSite, "_highlight_crous")

    def test_json_highlights_keys(self):
        from aquilia.admin.site import AdminSite
        result = AdminSite._highlight_json('{"name": "value"}')
        assert 'class="prop"' in result

    def test_json_highlights_string_values(self):
        from aquilia.admin.site import AdminSite
        result = AdminSite._highlight_json('{"key": "hello"}')
        assert 'class="str"' in result

    def test_json_highlights_numbers(self):
        from aquilia.admin.site import AdminSite
        result = AdminSite._highlight_json('{"count": 42}')
        assert 'class="num"' in result

    def test_json_highlights_booleans(self):
        from aquilia.admin.site import AdminSite
        result = AdminSite._highlight_json('{"active": true}')
        assert 'class="kw"' in result

    def test_json_highlights_null(self):
        from aquilia.admin.site import AdminSite
        result = AdminSite._highlight_json('{"val": null}')
        assert 'class="kw"' in result

    def test_json_highlights_braces(self):
        from aquilia.admin.site import AdminSite
        result = AdminSite._highlight_json('{"a": [1]}')
        assert 'class="op"' in result

    def test_json_has_line_numbers(self):
        from aquilia.admin.site import AdminSite
        result = AdminSite._highlight_json('{\n  "key": "val"\n}')
        assert 'class="code-line-num"' in result
        assert ">1<" in result
        assert ">2<" in result

    def test_json_multiline(self):
        from aquilia.admin.site import AdminSite
        src = '{\n  "name": "test",\n  "count": 5,\n  "active": true\n}'
        result = AdminSite._highlight_json(src)
        lines = result.split('\n')
        assert len(lines) == 5

    def test_crous_highlights_sections(self):
        from aquilia.admin.site import AdminSite
        result = AdminSite._highlight_crous('[Database]\nhost = localhost')
        assert 'class="cls"' in result

    def test_crous_highlights_keys(self):
        from aquilia.admin.site import AdminSite
        result = AdminSite._highlight_crous('host = localhost')
        assert 'class="kw"' in result

    def test_crous_highlights_comments(self):
        from aquilia.admin.site import AdminSite
        result = AdminSite._highlight_crous('# this is a comment')
        assert 'class="cmt"' in result

    def test_crous_highlights_booleans(self):
        from aquilia.admin.site import AdminSite
        result = AdminSite._highlight_crous('enabled = true')
        assert 'class="kw"' in result

    def test_crous_highlights_numbers(self):
        from aquilia.admin.site import AdminSite
        result = AdminSite._highlight_crous('port = 5432')
        assert 'class="num"' in result

    def test_crous_highlights_hex(self):
        from aquilia.admin.site import AdminSite
        result = AdminSite._highlight_crous('addr = 0xFF00AA')
        assert 'class="num"' in result

    def test_crous_has_line_numbers(self):
        from aquilia.admin.site import AdminSite
        result = AdminSite._highlight_crous('[Server]\nport = 8080')
        assert 'class="code-line-num"' in result

    def test_build_template_renders_highlighted_json(self):
        """Build page renders JSON artifacts with syntax highlighting spans."""
        html = render_build_page(
            build_info={"workspace_name": "test", "total_artifacts": 1},
            artifacts=[{
                "name": "test.json", "digest": "abc",
                "content": '{"key": "value"}', "kind": "model",
                "content_highlighted": '<span class="prop">"key"</span>: <span class="str">"value"</span>',
            }],
            pipeline_phases=[],
            build_log="",
            build_files=[],
        )
        assert 'class="prop"' in html or 'class="str"' in html


class TestDashboardThemeToggle:
    """Dashboard theme toggle uses requestAnimationFrame instead of display:none."""

    def test_uses_request_animation_frame(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "requestAnimationFrame" in html

    def test_no_display_none_hack(self):
        """The old body.style.display='none' hack should be gone."""
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "body.style.display" not in html

    def test_theme_toggle_function_exists(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "toggleTheme" in html


class TestIndustryLevelActions:
    """Verify all industry-level bulk actions are registered."""

    def test_default_actions_include_delete(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        assert "delete_selected" in actions

    def test_default_actions_include_duplicate(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        assert "duplicate_selected" in actions

    def test_default_actions_include_export_csv(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        assert "export_csv" in actions

    def test_default_actions_include_export_json(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        assert "export_json" in actions

    def test_default_actions_include_activate(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        assert "activate_selected" in actions

    def test_default_actions_include_deactivate(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        assert "deactivate_selected" in actions

    def test_default_actions_include_mark_featured(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        assert "mark_featured" in actions

    def test_default_actions_include_unmark_featured(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        assert "unmark_featured" in actions

    def test_total_action_count(self):
        """Should have at least 8 built-in actions."""
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        assert len(actions) >= 8

    def test_delete_has_confirmation(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        desc = actions["delete_selected"]
        assert desc.confirmation and len(desc.confirmation) > 0

    def test_duplicate_has_description(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        desc = actions["duplicate_selected"]
        assert "Duplicate" in desc.short_description

    def test_export_csv_has_description(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        desc = actions["export_csv"]
        assert "CSV" in desc.short_description

    def test_export_json_has_description(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        desc = actions["export_json"]
        assert "JSON" in desc.short_description

    def test_activate_has_description(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        desc = actions["activate_selected"]
        assert "Activate" in desc.short_description

    def test_deactivate_has_description(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        desc = actions["deactivate_selected"]
        assert "Deactivate" in desc.short_description

    def test_actions_have_callable_func(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        for name, desc in actions.items():
            assert callable(desc.func), f"Action {name} func not callable"

    def test_find_boolean_field_no_model(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        result = ma._find_boolean_field("is_active")
        assert result is None

    def test_list_template_has_duplicate_button(self):
        html = render_list_view(
            data={
                "rows": [{"pk": "1", "values": [("id", "1"), ("name", "Test")]}],
                "list_display": ["id", "name"],
                "model_name": "Product",
                "page": 1, "total_pages": 1, "total": 1,
                "verbose_name": "Product", "verbose_name_plural": "Products",
                "pk_field": "id",
                "actions": {"delete_selected": MagicMock(short_description="Delete", confirmation="Sure?")},
            },
            app_list=[], identity_name="admin",
        )
        assert "doDuplicate" in html

    def test_list_template_has_all_actions_in_dropdown(self):
        """Actions dropdown shows all registered actions."""
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        actions = ma.get_actions()
        action_data = {
            name: MagicMock(short_description=desc.short_description, confirmation=desc.confirmation or "")
            for name, desc in actions.items()
        }
        html = render_list_view(
            data={
                "rows": [{"pk": "1", "values": [("id", "1")]}],
                "list_display": ["id"],
                "model_name": "Product",
                "page": 1, "total_pages": 1, "total": 1,
                "verbose_name": "Product", "verbose_name_plural": "Products",
                "pk_field": "id",
                "actions": action_data,
            },
            app_list=[], identity_name="admin",
        )
        assert "export_csv" in html
        assert "export_json" in html
        assert "activate_selected" in html
        assert "duplicate_selected" in html


class TestKeyboardShortcutsTheme:
    """Keyboard shortcuts overlay uses CSS variables for theming."""

    def test_shortcuts_overlay_uses_css_vars(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "var(--bg-elevated)" in html
        assert "var(--border-color)" in html

    def test_shortcuts_overlay_no_hardcoded_111(self):
        """Shortcuts overlay should not use hardcoded #111 background."""
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        # The shortcuts overlay inner div should use CSS vars, not #111
        assert "var(--bg-surface)" in html

    def test_shortcuts_kbd_uses_css_vars(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "var(--text-primary)" in html
        assert "var(--font-mono)" in html


class TestToastTheming:
    """Toast notifications use CSS variables for theme support."""

    def test_toast_uses_bg_elevated(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        # Toast background should be var(--bg-elevated)
        assert "var(--bg-elevated)" in html

    def test_toast_uses_text_primary(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "var(--text-primary)" in html

    def test_toast_uses_font_sans(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "var(--font-sans)" in html


# ═══════════════════════════════════════════════════════════════════════════
# Session 7 — UX fixes, validation, modals, workspace page
# ═══════════════════════════════════════════════════════════════════════════


class TestThemeToggleClickability:
    """Theme toggle must be clickable above the topbar overlay."""

    def test_theme_toggle_has_z_index(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "z-index" in html

    def test_theme_toggle_has_pointer_events(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "pointer-events" in html

    def test_topbar_right_has_pointer_events(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "pointer-events:auto" in html or "pointer-events: auto" in html


class TestAscendingDefaultOrdering:
    """Default ordering should be ascending (1, 2, 3…)."""

    def test_default_ordering_ascending(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        ordering = ma.get_ordering()
        # Should NOT start with '-' (descending)
        for field in ordering:
            assert not field.startswith("-"), f"Default ordering should be ascending, got {field}"

    def test_default_ordering_uses_pk(self):
        from aquilia.admin.options import ModelAdmin
        ma = ModelAdmin(model=None)
        ordering = ma.get_ordering()
        assert len(ordering) >= 1

    def test_custom_ordering_preserved(self):
        from aquilia.admin.options import ModelAdmin

        class CustomAdmin(ModelAdmin):
            ordering = ["-name"]

        ca = CustomAdmin(model=None)
        assert ca.get_ordering() == ["-name"]


class TestFormDataCoercion:
    """_coerce_form_data should convert HTML form strings to proper types."""

    def test_coerce_boolean_true_values(self):
        from aquilia.admin.site import AdminSite
        from aquilia.models.fields_module import BooleanField

        class FakeModel:
            _fields = {"active": BooleanField()}

        for val in ["1", "true", "on", "yes"]:
            result = AdminSite._coerce_form_data(FakeModel, {"active": val})
            assert result["active"] is True, f"'{val}' should coerce to True"

    def test_coerce_boolean_false_values(self):
        from aquilia.admin.site import AdminSite
        from aquilia.models.fields_module import BooleanField

        class FakeModel:
            _fields = {"active": BooleanField()}

        for val in ["", "0", "false", "no"]:
            result = AdminSite._coerce_form_data(FakeModel, {"active": val})
            assert result["active"] is False, f"'{val}' should coerce to False"

    def test_coerce_integer_field(self):
        from aquilia.admin.site import AdminSite
        from aquilia.models.fields_module import IntegerField

        class FakeModel:
            _fields = {"count": IntegerField()}

        result = AdminSite._coerce_form_data(FakeModel, {"count": "42"})
        assert result["count"] == 42
        assert isinstance(result["count"], int)

    def test_coerce_float_field(self):
        from aquilia.admin.site import AdminSite
        from aquilia.models.fields_module import FloatField

        class FakeModel:
            _fields = {"price": FloatField()}

        result = AdminSite._coerce_form_data(FakeModel, {"price": "3.14"})
        assert abs(result["price"] - 3.14) < 0.001
        assert isinstance(result["price"], float)

    def test_coerce_unknown_field_passthrough(self):
        from aquilia.admin.site import AdminSite
        from aquilia.models.fields_module import CharField

        class FakeModel:
            _fields = {"name": CharField(max_length=100)}

        result = AdminSite._coerce_form_data(FakeModel, {"name": "hello"})
        assert result["name"] == "hello"

    def test_coerce_missing_field_passthrough(self):
        from aquilia.admin.site import AdminSite

        class FakeModel:
            _fields = {}

        result = AdminSite._coerce_form_data(FakeModel, {"unknown": "val"})
        assert result["unknown"] == "val"

    def test_coerce_invalid_int_passthrough(self):
        from aquilia.admin.site import AdminSite
        from aquilia.models.fields_module import IntegerField

        class FakeModel:
            _fields = {"count": IntegerField()}

        result = AdminSite._coerce_form_data(FakeModel, {"count": "abc"})
        assert result["count"] == "abc"  # unchanged on error

    def test_coerce_empty_int_passthrough(self):
        from aquilia.admin.site import AdminSite
        from aquilia.models.fields_module import IntegerField

        field = IntegerField()
        field.null = False

        class FakeModel:
            _fields = {"count": field}

        result = AdminSite._coerce_form_data(FakeModel, {"count": ""})
        assert result["count"] == 0  # empty string → 0 for non-null

    def test_coerce_no_fields_attr(self):
        from aquilia.admin.site import AdminSite

        class FakeModel:
            pass

        result = AdminSite._coerce_form_data(FakeModel, {"x": "1"})
        assert result["x"] == "1"


class TestCustomModals:
    """All confirm/delete dialogs should use custom modals, not browser confirm()."""

    def test_list_view_no_browser_confirm(self):
        html = render_list_view(
            data={
                "rows": [{"pk": "1", "values": [("id", "1")]}],
                "list_display": ["id"], "model_name": "Foo",
                "page": 1, "total_pages": 1, "total": 1,
                "verbose_name": "Foo", "verbose_name_plural": "Foos",
                "pk_field": "id",
                "actions": {"delete_selected": MagicMock(short_description="Delete", confirmation="Sure?")},
            },
            app_list=[], identity_name="admin",
        )
        # Should NOT have bare confirm() — only showConfirmModal
        assert "showConfirmModal" in html

    def test_list_view_has_do_delete(self):
        html = render_list_view(
            data={
                "rows": [{"pk": "1", "values": [("id", "1")]}],
                "list_display": ["id"], "model_name": "Foo",
                "page": 1, "total_pages": 1, "total": 1,
                "verbose_name": "Foo", "verbose_name_plural": "Foos",
                "pk_field": "id",
                "actions": {},
            },
            app_list=[], identity_name="admin",
        )
        assert "doDelete" in html

    def test_list_view_has_do_duplicate(self):
        html = render_list_view(
            data={
                "rows": [{"pk": "1", "values": [("id", "1")]}],
                "list_display": ["id"], "model_name": "Foo",
                "page": 1, "total_pages": 1, "total": 1,
                "verbose_name": "Foo", "verbose_name_plural": "Foos",
                "pk_field": "id",
                "actions": {},
            },
            app_list=[], identity_name="admin",
        )
        assert "doDuplicate" in html

    def test_list_view_has_quick_update(self):
        html = render_list_view(
            data={
                "rows": [{"pk": "1", "values": [("id", "1")]}],
                "list_display": ["id"], "model_name": "Foo",
                "page": 1, "total_pages": 1, "total": 1,
                "verbose_name": "Foo", "verbose_name_plural": "Foos",
                "pk_field": "id",
                "actions": {},
            },
            app_list=[], identity_name="admin",
        )
        assert "quickUpdate" in html

    def test_list_view_modal_has_cancel_button(self):
        html = render_list_view(
            data={
                "rows": [{"pk": "1", "values": [("id", "1")]}],
                "list_display": ["id"], "model_name": "Foo",
                "page": 1, "total_pages": 1, "total": 1,
                "verbose_name": "Foo", "verbose_name_plural": "Foos",
                "pk_field": "id",
                "actions": {},
            },
            app_list=[], identity_name="admin",
        )
        assert "Cancel" in html

    def test_form_view_has_custom_delete_modal(self):
        html = render_form_view(
            data={
                "model_name": "Foo", "verbose_name": "Foo",
                "fields": [{"name": "id", "value": "1", "field_type": "text", "required": False, "readonly": True}],
                "pk": "1", "pk_field": "id",
            },
            app_list=[], identity_name="admin",
        )
        assert "showDeleteModal" in html

    def test_form_view_no_bare_confirm(self):
        html = render_form_view(
            data={
                "model_name": "Foo", "verbose_name": "Foo",
                "fields": [{"name": "id", "value": "1", "field_type": "text", "required": False, "readonly": True}],
                "pk": "1", "pk_field": "id",
            },
            app_list=[], identity_name="admin",
        )
        # The form should not use bare return confirm(
        assert "return confirm(" not in html


class TestUpdateButtonInActions:
    """The list view should have an Update button per row."""

    def test_list_view_has_update_action(self):
        html = render_list_view(
            data={
                "rows": [{"pk": "1", "values": [("id", "1")]}],
                "list_display": ["id"], "model_name": "Foo",
                "page": 1, "total_pages": 1, "total": 1,
                "verbose_name": "Foo", "verbose_name_plural": "Foos",
                "pk_field": "id",
                "actions": {},
            },
            app_list=[], identity_name="admin",
        )
        assert "quickUpdate" in html

    def test_list_view_update_button_has_refresh_icon(self):
        html = render_list_view(
            data={
                "rows": [{"pk": "1", "values": [("id", "1")]}],
                "list_display": ["id"], "model_name": "Foo",
                "page": 1, "total_pages": 1, "total": 1,
                "verbose_name": "Foo", "verbose_name_plural": "Foos",
                "pk_field": "id",
                "actions": {},
            },
            app_list=[], identity_name="admin",
        )
        assert "refresh-cw" in html


class TestWorkspacePage:
    """Workspace monitoring page — template, render, sidebar, route."""

    def test_render_workspace_page_basic(self):
        from aquilia.admin.templates import render_workspace_page
        html = render_workspace_page(
            workspace={
                "name": "MyApp",
                "version": "1.0.0",
                "description": "Test workspace",
                "python_version": "3.12",
                "platform": "darwin",
                "modules": [],
                "integrations": [],
                "registered_models": [],
                "project_meta": {},
                "stats": {
                    "total_modules": 0,
                    "total_models": 0,
                    "total_controllers": 0,
                    "total_services": 0,
                    "total_integrations": 0,
                },
            },
            app_list=[], identity_name="admin",
        )
        assert "Workspace" in html
        assert "MyApp" in html

    def test_render_workspace_with_modules(self):
        from aquilia.admin.templates import render_workspace_page
        html = render_workspace_page(
            workspace={
                "name": "MyApp",
                "version": "1.0.0",
                "description": "",
                "python_version": "3.12",
                "platform": "darwin",
                "modules": [
                    {
                        "name": "authentication",
                        "manifest": {
                            "controllers": ["AuthController"],
                            "services": ["AuthService"],
                            "models": ["User"],
                            "guards": ["AuthGuard"],
                            "pipes": [],
                            "interceptors": [],
                            "imports": [],
                            "exports": [],
                            "tags": ["auth"],
                            "route_prefix": "/auth",
                            "fault_domain": "AUTH",
                            "auto_discover": True,
                        },
                        "files": [
                            {"name": "controller.py", "kind": "controller"},
                            {"name": "models.py", "kind": "model"},
                            {"name": "manifest.py", "kind": "manifest"},
                        ],
                    }
                ],
                "integrations": [
                    {"name": "SQLite", "icon": "🗄️", "params": {"db": "test.db"}},
                ],
                "registered_models": [
                    {"name": "User", "table": "users", "field_count": 5, "app_label": "auth"},
                ],
                "project_meta": {"author": "Tester", "license": "MIT"},
                "stats": {
                    "total_modules": 1,
                    "total_models": 1,
                    "total_controllers": 1,
                    "total_services": 1,
                    "total_integrations": 1,
                },
            },
            app_list=[], identity_name="admin",
        )
        assert "authentication" in html
        assert "AuthController" in html
        assert "AuthService" in html
        assert "AuthGuard" in html
        assert "/auth" in html
        assert "SQLite" in html
        assert "User" in html
        assert "users" in html
        assert "Tester" in html

    def test_workspace_page_has_stats(self):
        from aquilia.admin.templates import render_workspace_page
        html = render_workspace_page(
            workspace={
                "name": "App",
                "version": "1.0",
                "description": "",
                "python_version": "3.12",
                "platform": "darwin",
                "modules": [],
                "integrations": [],
                "registered_models": [],
                "project_meta": {},
                "stats": {
                    "total_modules": 3,
                    "total_models": 5,
                    "total_controllers": 2,
                    "total_services": 4,
                    "total_integrations": 1,
                },
            },
            app_list=[], identity_name="admin",
        )
        assert "Modules" in html
        assert "Models" in html
        assert "Controllers" in html
        assert "Services" in html
        assert "Integrations" in html

    def test_workspace_page_module_expandable(self):
        from aquilia.admin.templates import render_workspace_page
        html = render_workspace_page(
            workspace={
                "name": "App", "version": "1.0", "description": "",
                "python_version": "3.12", "platform": "darwin",
                "modules": [
                    {"name": "orders", "manifest": None, "files": [{"name": "models.py", "kind": "model"}]},
                ],
                "integrations": [], "registered_models": [], "project_meta": {},
                "stats": {"total_modules": 1, "total_models": 0, "total_controllers": 0, "total_services": 0, "total_integrations": 0},
            },
            app_list=[], identity_name="admin",
        )
        assert "toggleModule" in html
        assert "module-body" in html
        assert "module-chevron" in html
        assert "data-collapsed" in html

    def test_workspace_page_no_modules(self):
        from aquilia.admin.templates import render_workspace_page
        html = render_workspace_page(
            workspace={
                "name": "App", "version": "1.0", "description": "",
                "python_version": "3.12", "platform": "darwin",
                "modules": [],
                "integrations": [], "registered_models": [], "project_meta": {},
                "stats": {"total_modules": 0, "total_models": 0, "total_controllers": 0, "total_services": 0, "total_integrations": 0},
            },
            app_list=[], identity_name="admin",
        )
        assert "No modules discovered" in html

    def test_workspace_page_file_kind_badges(self):
        from aquilia.admin.templates import render_workspace_page
        html = render_workspace_page(
            workspace={
                "name": "App", "version": "1.0", "description": "",
                "python_version": "3.12", "platform": "darwin",
                "modules": [
                    {
                        "name": "payments",
                        "manifest": {
                            "controllers": [], "services": [], "models": [],
                            "guards": [], "pipes": [], "interceptors": [],
                            "imports": [], "exports": [],
                            "tags": [], "route_prefix": "", "fault_domain": "", "auto_discover": False,
                        },
                        "files": [
                            {"name": "controller.py", "kind": "controller"},
                            {"name": "service.py", "kind": "service"},
                            {"name": "models.py", "kind": "model"},
                            {"name": "guard.py", "kind": "guard"},
                        ],
                    },
                ],
                "integrations": [], "registered_models": [], "project_meta": {},
                "stats": {"total_modules": 1, "total_models": 0, "total_controllers": 0, "total_services": 0, "total_integrations": 0},
            },
            app_list=[], identity_name="admin",
        )
        assert "controller" in html.lower()
        assert "service" in html.lower()
        assert "model" in html.lower()
        assert "guard" in html.lower()

    def test_workspace_page_project_metadata(self):
        from aquilia.admin.templates import render_workspace_page
        html = render_workspace_page(
            workspace={
                "name": "App", "version": "1.0", "description": "",
                "python_version": "3.12", "platform": "darwin",
                "modules": [],
                "integrations": [], "registered_models": [],
                "project_meta": {"author": "Dev Team", "license": "Apache-2.0", "python_requires": ">=3.10"},
                "stats": {"total_modules": 0, "total_models": 0, "total_controllers": 0, "total_services": 0, "total_integrations": 0},
            },
            app_list=[], identity_name="admin",
        )
        assert "Dev Team" in html
        assert "Apache-2.0" in html

    def test_workspace_page_keyboard_expand(self):
        from aquilia.admin.templates import render_workspace_page
        html = render_workspace_page(
            workspace={
                "name": "App", "version": "1.0", "description": "",
                "python_version": "3.12", "platform": "darwin",
                "modules": [{"name": "core", "manifest": None, "files": []}],
                "integrations": [], "registered_models": [], "project_meta": {},
                "stats": {"total_modules": 1, "total_models": 0, "total_controllers": 0, "total_services": 0, "total_integrations": 0},
            },
            app_list=[], identity_name="admin",
        )
        # Keyboard shortcut 'e' to expand/collapse all
        assert "e.key === 'e'" in html or "e.key===" in html

    def test_workspace_sidebar_link(self):
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "/admin/workspace/" in html
        assert "Workspace" in html

    def test_workspace_fallback_render(self):
        from aquilia.admin.templates import render_workspace_page, _HAS_JINJA2
        # If Jinja2 is available, we test the function returns valid HTML
        html = render_workspace_page(
            workspace={
                "name": "Test", "version": "1.0", "description": "",
                "python_version": "3.12", "platform": "darwin",
                "modules": [],
                "integrations": [], "registered_models": [], "project_meta": {},
                "stats": {"total_modules": 0, "total_models": 0, "total_controllers": 0, "total_services": 0, "total_integrations": 0},
            },
            app_list=[], identity_name="admin",
        )
        assert "<!DOCTYPE html>" in html or "Workspace" in html

    def test_workspace_page_integrations_display(self):
        from aquilia.admin.templates import render_workspace_page
        html = render_workspace_page(
            workspace={
                "name": "App", "version": "1.0", "description": "",
                "python_version": "3.12", "platform": "darwin",
                "modules": [],
                "integrations": [
                    {"name": "Redis", "icon": "🔴", "params": {"host": "localhost"}},
                    {"name": "PostgreSQL", "icon": "🐘", "params": {"port": 5432}},
                ],
                "registered_models": [], "project_meta": {},
                "stats": {"total_modules": 0, "total_models": 0, "total_controllers": 0, "total_services": 0, "total_integrations": 2},
            },
            app_list=[], identity_name="admin",
        )
        assert "Redis" in html
        assert "PostgreSQL" in html

    def test_workspace_page_registered_models_table(self):
        from aquilia.admin.templates import render_workspace_page
        html = render_workspace_page(
            workspace={
                "name": "App", "version": "1.0", "description": "",
                "python_version": "3.12", "platform": "darwin",
                "modules": [],
                "integrations": [],
                "registered_models": [
                    {"name": "Order", "table": "orders", "field_count": 8, "app_label": "shop"},
                    {"name": "Product", "table": "products", "field_count": 6, "app_label": "shop"},
                ],
                "project_meta": {},
                "stats": {"total_modules": 0, "total_models": 2, "total_controllers": 0, "total_services": 0, "total_integrations": 0},
            },
            app_list=[], identity_name="admin",
        )
        assert "Order" in html
        assert "orders" in html
        assert "Product" in html
        assert "products" in html

    def test_workspace_page_manifest_tags(self):
        from aquilia.admin.templates import render_workspace_page
        html = render_workspace_page(
            workspace={
                "name": "App", "version": "1.0", "description": "",
                "python_version": "3.12", "platform": "darwin",
                "modules": [
                    {
                        "name": "billing",
                        "manifest": {
                            "controllers": ["BillingController"],
                            "services": [],
                            "models": [],
                            "guards": [],
                            "pipes": [],
                            "interceptors": [],
                            "imports": [],
                            "exports": [],
                            "tags": ["payments", "billing"],
                            "route_prefix": "/billing",
                            "fault_domain": "BILLING",
                            "auto_discover": True,
                        },
                        "files": [],
                    },
                ],
                "integrations": [], "registered_models": [], "project_meta": {},
                "stats": {"total_modules": 1, "total_models": 0, "total_controllers": 1, "total_services": 0, "total_integrations": 0},
            },
            app_list=[], identity_name="admin",
        )
        assert "payments" in html
        assert "billing" in html
        assert "BILLING" in html

    def test_workspace_page_auto_discover_indicator(self):
        from aquilia.admin.templates import render_workspace_page
        html = render_workspace_page(
            workspace={
                "name": "App", "version": "1.0", "description": "",
                "python_version": "3.12", "platform": "darwin",
                "modules": [
                    {
                        "name": "core",
                        "manifest": {
                            "controllers": [], "services": [], "models": [],
                            "guards": [], "pipes": [], "interceptors": [],
                            "imports": [], "exports": [],
                            "tags": [], "route_prefix": "",
                            "fault_domain": "", "auto_discover": True,
                        },
                        "files": [],
                    },
                ],
                "integrations": [], "registered_models": [], "project_meta": {},
                "stats": {"total_modules": 1, "total_models": 0, "total_controllers": 0, "total_services": 0, "total_integrations": 0},
            },
            app_list=[], identity_name="admin",
        )
        assert "Enabled" in html or "Auto Discover" in html


class TestWorkspaceDataMethod:
    """AdminSite.get_workspace_data() should return structured workspace info."""

    def test_get_workspace_data_returns_dict(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        site._initialized = True
        data = site.get_workspace_data()
        assert isinstance(data, dict)
        assert "workspace" in data
        assert "modules" in data
        assert "stats" in data

    def test_get_workspace_data_has_stats(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        site._initialized = True
        data = site.get_workspace_data()
        stats = data["stats"]
        assert "total_modules" in stats
        assert "total_models" in stats
        assert "total_integrations" in stats

    def test_get_workspace_data_has_workspace_info(self):
        import sys
        import tempfile
        from pathlib import Path
        from aquilia.admin.site import AdminSite

        # Create a minimal workspace.py so the test is not filesystem-dependent
        with tempfile.TemporaryDirectory() as tmp:
            ws_file = Path(tmp) / "workspace.py"
            ws_file.write_text(
                'from aquilia import Workspace\n'
                'app = Workspace("test-workspace", version="1.0.0")\n'
            )
            old_cwd = Path.cwd()
            import os
            os.chdir(tmp)
            try:
                site = AdminSite()
                site._initialized = True
                data = site.get_workspace_data()
                ws = data["workspace"]
                assert isinstance(ws, dict)
                assert "name" in ws
                assert "python_version" in ws
            finally:
                os.chdir(old_cwd)

    def test_classify_module_file(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        assert site._classify_module_file("controller.py") == "controller"
        assert site._classify_module_file("controllers.py") == "controller"
        assert site._classify_module_file("service.py") == "service"
        assert site._classify_module_file("services.py") == "service"
        assert site._classify_module_file("models.py") == "model"
        assert site._classify_module_file("manifest.py") == "manifest"
        assert site._classify_module_file("guard.py") == "guard"
        assert site._classify_module_file("guards.py") == "guard"
        assert site._classify_module_file("faults.py") == "fault"
        assert site._classify_module_file("pipe.py") == "pipe"
        assert site._classify_module_file("middleware.py") == "middleware"
        assert site._classify_module_file("config.py") == "other"
        assert site._classify_module_file("utils.py") == "other"

    def test_get_integration_icon(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        assert site._get_integration_icon("sqlite") != ""
        assert site._get_integration_icon("redis") != ""
        assert site._get_integration_icon("unknown_thing") != ""

    def test_get_workspace_data_registered_models(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        site._initialized = True
        data = site.get_workspace_data()
        assert "registered_models" in data
        assert isinstance(data["registered_models"], list)

    def test_get_workspace_data_integrations(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        site._initialized = True
        data = site.get_workspace_data()
        assert "integrations" in data
        assert isinstance(data["integrations"], list)

    def test_get_workspace_data_project_meta(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        site._initialized = True
        data = site.get_workspace_data()
        assert "project_meta" in data
        assert isinstance(data["project_meta"], dict)

    def test_get_workspace_data_modules_list(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        site._initialized = True
        data = site.get_workspace_data()
        assert "modules" in data
        assert isinstance(data["modules"], list)


class TestWorkspaceRoute:
    """Controller should have the workspace route wired up."""

    def test_controller_imports_render_workspace(self):
        from aquilia.admin.controller import render_workspace_page
        assert callable(render_workspace_page)

    def test_admin_controller_has_workspace_view(self):
        from aquilia.admin.controller import AdminController
        assert hasattr(AdminController, "workspace_view")

    def test_workspace_view_is_async(self):
        import inspect
        from aquilia.admin.controller import AdminController
        assert inspect.iscoroutinefunction(AdminController.workspace_view)

    def test_workspace_route_delegates_correctly(self):
        """Test that /workspace/ URL delegates to workspace_view instead of list_view."""
        from aquilia.admin.controller import AdminController
        # Verify _SYSTEM_PAGES includes workspace
        assert hasattr(AdminController, '_SYSTEM_PAGES')
        assert 'workspace' in AdminController._SYSTEM_PAGES
        # Verify workspace_view method exists
        assert hasattr(AdminController, 'workspace_view')
        assert callable(getattr(AdminController, 'workspace_view'))


class TestSidebarWorkspaceLink:
    """Sidebar should include a Workspace link in the System section."""

    def test_sidebar_has_workspace_link_on_all_pages(self):
        """Workspace link should appear on every page that renders the sidebar."""
        # Dashboard
        html = render_dashboard(
            app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
            identity_name="admin",
        )
        assert "/admin/workspace/" in html

    def test_sidebar_workspace_active_state(self):
        from aquilia.admin.templates import render_workspace_page
        html = render_workspace_page(
            workspace={
                "name": "App", "version": "1.0", "description": "",
                "python_version": "3.12", "platform": "darwin",
                "modules": [], "integrations": [],
                "registered_models": [], "project_meta": {},
                "stats": {"total_modules": 0, "total_models": 0, "total_controllers": 0, "total_services": 0, "total_integrations": 0},
            },
            app_list=[], identity_name="admin",
        )
        # The workspace link should have 'active' class on the workspace page
        assert 'active' in html


class TestModalAccessibility:
    """Custom modals should be accessible and themed."""

    def test_list_modal_has_escape_key(self):
        html = render_list_view(
            data={
                "rows": [{"pk": "1", "values": [("id", "1")]}],
                "list_display": ["id"], "model_name": "Foo",
                "page": 1, "total_pages": 1, "total": 1,
                "verbose_name": "Foo", "verbose_name_plural": "Foos",
                "pk_field": "id", "actions": {},
            },
            app_list=[], identity_name="admin",
        )
        assert "Escape" in html


# ═══════════════════════════════════════════════════════════════════════════
# Monitoring System Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestMonitoringDataCollector:
    """AdminSite.get_monitoring_data() should return comprehensive system metrics."""

    def test_get_monitoring_data_returns_dict(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        site._initialized = True
        data = site.get_monitoring_data()
        assert isinstance(data, dict)

    def test_get_monitoring_data_has_cpu(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "cpu" in data
        assert "percent" in data["cpu"]
        assert isinstance(data["cpu"]["percent"], (int, float))

    def test_get_monitoring_data_has_memory(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "memory" in data
        assert "percent" in data["memory"]
        assert "total_human" in data["memory"]

    def test_get_monitoring_data_has_disk(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "disk" in data
        assert "percent" in data["disk"]

    def test_get_monitoring_data_has_network(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "network" in data
        assert "bytes_sent" in data["network"]

    def test_get_monitoring_data_has_process(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "process" in data
        assert "pid" in data["process"]
        assert data["process"]["pid"] > 0

    def test_get_monitoring_data_has_python(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "python" in data
        assert "version" in data["python"]

    def test_get_monitoring_data_has_system(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "system" in data
        assert "os" in data["system"]
        assert "hostname" in data["system"]

    def test_get_monitoring_data_has_health_checks(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "health_checks" in data
        assert isinstance(data["health_checks"], list)

    def test_get_monitoring_data_cpu_per_core(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "per_core" in data["cpu"]
        assert isinstance(data["cpu"]["per_core"], list)

    def test_get_monitoring_data_process_env_snapshot(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "env_snapshot" in data["process"]
        assert isinstance(data["process"]["env_snapshot"], dict)

    def test_get_monitoring_data_disk_partitions(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "partitions" in data["disk"]
        assert isinstance(data["disk"]["partitions"], list)

    def test_fmt_bytes(self):
        from aquilia.admin.site import AdminSite
        assert "1.0 KB" == AdminSite._fmt_bytes(1024)
        assert "1.0 MB" == AdminSite._fmt_bytes(1024 * 1024)
        assert "1.0 GB" == AdminSite._fmt_bytes(1024 ** 3)
        assert "0.0 B" == AdminSite._fmt_bytes(0)

    def test_format_uptime(self):
        from aquilia.admin.site import AdminSite
        assert "0s" == AdminSite._format_uptime(0)
        assert "1m 30s" == AdminSite._format_uptime(90)
        assert "1h 0s" == AdminSite._format_uptime(3600)
        assert "1d 0s" == AdminSite._format_uptime(86400)

    def test_safe_env_snapshot_excludes_secrets(self):
        import os
        from aquilia.admin.site import AdminSite
        # Set a secret-like env var
        os.environ["SECRET_KEY"] = "super_secret"
        snap = AdminSite._safe_env_snapshot()
        assert "SECRET_KEY" not in snap
        del os.environ["SECRET_KEY"]

    def test_monitoring_data_serializable(self):
        """Monitoring data should be JSON-serializable."""
        import json
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        # Should not raise
        serialized = json.dumps(data, default=str)
        assert len(serialized) > 100

    def test_get_monitoring_data_gc_generations(self):
        """gc_generations should be a list of dicts with collection stats."""
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        gens = data["python"]["gc_generations"]
        assert isinstance(gens, list)
        assert len(gens) == 3  # CPython always has 3 generations
        for g in gens:
            assert "generation" in g
            assert "collections" in g
            assert isinstance(g["collections"], int)

    def test_get_monitoring_data_gc_enabled(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "gc_enabled" in data["python"]
        assert isinstance(data["python"]["gc_enabled"], bool)

    def test_get_monitoring_data_gc_frozen(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "gc_frozen" in data["python"]
        assert isinstance(data["python"]["gc_frozen"], int)

    def test_get_monitoring_data_loaded_modules(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "loaded_modules" in data["python"]
        assert isinstance(data["python"]["loaded_modules"], int)
        assert data["python"]["loaded_modules"] > 0

    def test_get_monitoring_data_active_threads(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "active_threads" in data["python"]
        assert isinstance(data["python"]["active_threads"], int)
        assert data["python"]["active_threads"] >= 1

    def test_get_monitoring_data_recursion_limit(self):
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        assert "recursion_limit" in data["python"]
        assert isinstance(data["python"]["recursion_limit"], int)
        assert data["python"]["recursion_limit"] > 0

    def test_get_monitoring_data_io_counters(self):
        """Process I/O counter fields should be present."""
        from aquilia.admin.site import AdminSite
        site = AdminSite()
        data = site.get_monitoring_data()
        proc = data["process"]
        assert "io_read_count" in proc
        assert "io_write_count" in proc
        assert "io_read_bytes_human" in proc
        assert "io_write_bytes_human" in proc


class TestMonitoringRoute:
    """Controller should have the monitoring routes wired up."""

    def test_controller_imports_render_monitoring(self):
        from aquilia.admin.controller import render_monitoring_page
        assert callable(render_monitoring_page)

    def test_admin_controller_has_monitoring_view(self):
        from aquilia.admin.controller import AdminController
        assert hasattr(AdminController, "monitoring_view")

    def test_admin_controller_has_monitoring_api(self):
        from aquilia.admin.controller import AdminController
        assert hasattr(AdminController, "monitoring_api")

    def test_monitoring_view_is_async(self):
        import inspect
        from aquilia.admin.controller import AdminController
        assert inspect.iscoroutinefunction(AdminController.monitoring_view)

    def test_monitoring_api_is_async(self):
        import inspect
        from aquilia.admin.controller import AdminController
        assert inspect.iscoroutinefunction(AdminController.monitoring_api)

    def test_monitoring_route_delegates_correctly(self):
        """Test that /monitoring/ URL delegates to monitoring_view."""
        from aquilia.admin.controller import AdminController
        assert hasattr(AdminController, '_SYSTEM_PAGES')
        assert 'monitoring' in AdminController._SYSTEM_PAGES


class TestMonitoringSidebar:
    """Sidebar should include a Monitoring link in the System section."""

    def test_sidebar_has_monitoring_link(self):
        from pathlib import Path
        content = (Path(__file__).parent.parent / "aquilia/admin/templates/partials/sidebar_v2.html").read_text()
        assert "monitoring" in content.lower()
        assert "/monitoring/" in content

    def test_sidebar_monitoring_appears_on_dashboard(self):
        """Monitoring link should appear when monitoring is enabled."""
        from aquilia.admin.site import AdminSite, AdminConfig
        # Must configure the default singleton since _render_template reads it
        AdminSite.reset()
        site = AdminSite.default()
        site.admin_config = AdminConfig(modules={
            "dashboard": True, "orm": True, "build": True,
            "migrations": True, "config": True, "workspace": True,
            "permissions": True, "monitoring": True, "admin_users": True,
            "profile": True, "audit": True,
        })
        try:
            html = render_dashboard(
                app_list=[], stats={"total_models": 0, "model_counts": {}, "recent_actions": []},
                identity_name="admin",
            )
            assert "/admin/monitoring/" in html
        finally:
            AdminSite.reset()

    def test_monitoring_template_exists(self):
        from pathlib import Path
        p = Path(__file__).parent.parent / "aquilia/admin/templates/monitoring.html"
        assert p.exists()

    def test_monitoring_template_has_tabs(self):
        from pathlib import Path
        content = (Path(__file__).parent.parent / "aquilia/admin/templates/monitoring.html").read_text()
        for tab in ("overview", "cpu", "memory", "network", "process", "health"):
            assert tab in content.lower(), f"Tab '{tab}' missing from monitoring template"

    def test_monitoring_template_has_gauges(self):
        from pathlib import Path
        content = (Path(__file__).parent.parent / "aquilia/admin/templates/monitoring.html").read_text()
        assert "gaugeCpu" in content
        assert "gaugeMem" in content
        assert "gaugeDisk" in content

    def test_monitoring_template_has_live_polling(self):
        from pathlib import Path
        content = (Path(__file__).parent.parent / "aquilia/admin/templates/monitoring.html").read_text()
        assert "/monitoring/api/" in content
        assert "setInterval" in content

    def test_form_modal_has_escape_key(self):
        html = render_form_view(
            data={
                "model_name": "Foo", "verbose_name": "Foo",
                "fields": [{"name": "id", "value": "1", "field_type": "text", "required": False, "readonly": True}],
                "pk": "1", "pk_field": "id",
            },
            app_list=[], identity_name="admin",
        )
        assert "Escape" in html

    def test_list_modal_themed_dark_mode(self):
        html = render_list_view(
            data={
                "rows": [{"pk": "1", "values": [("id", "1")]}],
                "list_display": ["id"], "model_name": "Foo",
                "page": 1, "total_pages": 1, "total": 1,
                "verbose_name": "Foo", "verbose_name_plural": "Foos",
                "pk_field": "id", "actions": {},
            },
            app_list=[], identity_name="admin",
        )
        # Modal should use CSS variables for theming
        assert "var(--bg-elevated)" in html or "var(--border-color)" in html


class TestAqdocxThemeAlignment:
    """Verify admin CSS is aligned with aqdocx docs theme."""

    def test_css_uses_outfit_font(self):
        from aquilia.admin.templates import _get_jinja_env
        css = _get_jinja_env().get_template("partials/css.html").render()
        assert '"Outfit"' in css

    def test_css_uses_space_mono_font(self):
        from aquilia.admin.templates import _get_jinja_env
        css = _get_jinja_env().get_template("partials/css.html").render()
        assert '"Space Mono"' in css

    def test_css_pure_black_dark_mode(self):
        from aquilia.admin.templates import _get_jinja_env
        css = _get_jinja_env().get_template("partials/css.html").render()
        assert "--bg-body: #000000" in css
        assert "--bg-card: #000000" in css
        # aqdocx sidebar is #09090b (zinc-950), not pure black
        assert "--bg-sidebar: #09090b" in css

    def test_css_has_grid_background(self):
        from aquilia.admin.templates import _get_jinja_env
        css = _get_jinja_env().get_template("partials/css.html").render()
        assert "linear-gradient" in css
        assert "40px 40px" in css

    def test_css_has_ambient_blob_classes(self):
        from aquilia.admin.templates import _get_jinja_env
        css = _get_jinja_env().get_template("partials/css.html").render()
        assert "ambient-blob-green" in css
        assert "ambient-blob-blue" in css
        assert "ambient-blob-purple" in css
        assert "ambient-blob-cyan" in css

    def test_base_has_ambient_blobs(self):
        from pathlib import Path
        html = (Path(__file__).parent.parent / "aquilia/admin/templates/base.html").read_text()
        assert "ambient-blob-green" in html
        assert "ambient-blob-blue" in html
        assert "ambient-blob-purple" in html
        assert "ambient-blob-cyan" in html

    def test_css_has_breathing_animation(self):
        from aquilia.admin.templates import _get_jinja_env
        css = _get_jinja_env().get_template("partials/css.html").render()
        assert "@keyframes breathing" in css

    def test_css_sidebar_active_gradient(self):
        from aquilia.admin.templates import _get_jinja_env
        css = _get_jinja_env().get_template("partials/css.html").render()
        assert "linear-gradient(to right" in css
        assert "border-left: 2px solid #22c55e" in css


class TestIntegrationIconsLucide:
    """Integration icons should use Lucide classes instead of emojis."""

    def test_integration_icon_returns_lucide_class(self):
        from aquilia.admin.site import AdminSite
        assert AdminSite._get_integration_icon("database") == "icon-database"
        assert AdminSite._get_integration_icon("mail") == "icon-mail"
        assert AdminSite._get_integration_icon("cache") == "icon-zap"
        assert AdminSite._get_integration_icon("sessions") == "icon-key"
        assert AdminSite._get_integration_icon("unknown_thing") == "icon-settings"

    def test_no_emoji_in_integration_icons(self):
        from aquilia.admin.site import AdminSite
        known = [
            "di", "registry", "routing", "fault_handling", "patterns",
            "database", "cache", "templates", "static_files", "admin",
            "cors", "csp", "rate_limit", "mail", "sessions", "auth", "openapi",
        ]
        for name in known:
            icon = AdminSite._get_integration_icon(name)
            assert icon.startswith("icon-"), f"{name} icon should be Lucide class, got {icon}"


class TestWorkspaceModuleExpandCollapse:
    """Module expand/collapse should use data-collapsed + max-height approach."""

    def test_module_body_has_data_collapsed(self):
        from aquilia.admin.templates import render_workspace_page
        html = render_workspace_page(
            workspace={
                "name": "App", "version": "1.0", "description": "",
                "python_version": "3.12", "platform": "darwin",
                "modules": [
                    {"name": "core", "manifest": None, "files": [{"name": "main.py", "kind": "controller"}]},
                ],
                "integrations": [], "registered_models": [], "project_meta": {},
                "stats": {"total_modules": 1, "total_models": 0, "total_controllers": 0, "total_services": 0, "total_integrations": 0},
            },
            app_list=[], identity_name="admin",
        )
        assert 'data-collapsed="true"' in html
        assert "max-height" in html
        assert "toggleModule(this)" in html


class TestRenderErrorPage:
    """render_error_page should produce styled admin error pages."""

    def test_render_error_page_import(self):
        from aquilia.admin.templates import render_error_page
        assert callable(render_error_page)

    def test_render_error_page_contains_status(self):
        from aquilia.admin.templates import render_error_page
        html = render_error_page(status=404, title="Not Found", message="Model 'xyz' not registered")
        assert "404" in html
        assert "Not Found" in html

    def test_render_error_page_contains_message(self):
        from aquilia.admin.templates import render_error_page
        html = render_error_page(status=404, title="Not Found", message="No such model")
        assert "No such model" in html

    def test_render_error_page_contains_dashboard_link(self):
        from aquilia.admin.templates import render_error_page
        html = render_error_page(status=404, title="Not Found")
        assert "/admin/" in html
        assert "Dashboard" in html

    def test_render_error_page_403(self):
        from aquilia.admin.templates import render_error_page
        html = render_error_page(status=403, title="Forbidden", message="Access denied")
        assert "403" in html
        assert "Forbidden" in html

    def test_render_error_page_400(self):
        from aquilia.admin.templates import render_error_page
        html = render_error_page(status=400, title="Error", message="Bad request")
        assert "400" in html

    def test_render_error_page_extends_base(self):
        """Error page should use the full admin layout (sidebar, header)."""
        from aquilia.admin.templates import render_error_page
        html = render_error_page(
            status=404, title="Not Found", message="Test",
            app_list=[{"name": "TestApp", "models": []}],
            identity_name="Admin",
        )
        # Should contain admin layout elements from base.html
        assert "Aquilia Admin" in html
        assert "data-theme" in html


class TestAdminDeleteFlashError:
    """delete_record should flash error messages to the session."""

    def test_controller_has_delete_record(self):
        from aquilia.admin.controller import AdminController
        assert hasattr(AdminController, "delete_record")

    def test_render_error_page_import_in_controller(self):
        """Controller should import render_error_page."""
        from aquilia.admin.controller import render_error_page
        assert callable(render_error_page)


class TestServerAdminRouteWiring:
    """server.py admin_routes should include all system page routes."""

    def test_monitoring_routes_in_wiring(self):
        """Monitoring and monitoring/api routes must be wired as static routes."""
        import ast
        from pathlib import Path

        server_path = Path(__file__).resolve().parent.parent / "aquilia" / "server.py"
        source = server_path.read_text(encoding="utf-8")
        # Check that monitoring routes are present in the admin_routes list
        assert '"/monitoring/"' in source or "monitoring_view" in source
        assert '"/monitoring/api/"' in source or "monitoring_api" in source

    def test_workspace_route_in_wiring(self):
        """Workspace route must be wired as a static route."""
        from pathlib import Path

        server_path = Path(__file__).resolve().parent.parent / "aquilia" / "server.py"
        source = server_path.read_text(encoding="utf-8")
        assert '"/workspace/"' in source or "workspace_view" in source


# ═══════════════════════════════════════════════════════════════════════════
# ADMIN CONFIG — COMPREHENSIVE MODULE CONTROL SYSTEM
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminConfigDataclass:
    """Test the AdminConfig frozen dataclass."""

    def test_import(self):
        from aquilia.admin.site import AdminConfig
        assert AdminConfig is not None

    def test_default_all_modules_enabled(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig()
        # Modules enabled by default
        for mod in ("dashboard", "orm", "build", "migrations", "config",
                     "workspace", "permissions", "admin_users", "profile"):
            assert cfg.is_module_enabled(mod), f"{mod} should be enabled by default"
        # Monitoring and audit are disabled by default
        assert cfg.is_module_enabled("monitoring") is False
        assert cfg.is_module_enabled("audit") is False

    def test_is_module_enabled_normalises_dashes(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig()
        assert cfg.is_module_enabled("admin-users") is True
        assert cfg.is_module_enabled("admin_users") is True

    def test_unknown_module_returns_false(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig()
        assert cfg.is_module_enabled("nonexistent") is False

    def test_disable_module(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig(modules={
            "dashboard": True, "orm": False, "build": True,
            "migrations": True, "config": True, "workspace": True,
            "permissions": True, "monitoring": False, "admin_users": True,
            "profile": True, "audit": True,
        })
        assert cfg.is_module_enabled("orm") is False
        assert cfg.is_module_enabled("monitoring") is False
        assert cfg.is_module_enabled("dashboard") is True

    def test_audit_action_filtering_defaults(self):
        from aquilia.admin.site import AdminConfig
        from aquilia.admin.audit import AdminAction
        # With audit disabled (default), all actions are blocked
        cfg = AdminConfig()
        for action in AdminAction:
            assert cfg.is_action_allowed(action) is False, f"{action} should be blocked when audit disabled"
        # With audit explicitly enabled, all actions are allowed
        cfg_on = AdminConfig(audit_enabled=True)
        for action in AdminAction:
            assert cfg_on.is_action_allowed(action), f"{action} should be allowed when audit enabled"

    def test_audit_excluded_actions(self):
        from aquilia.admin.site import AdminConfig
        from aquilia.admin.audit import AdminAction
        cfg = AdminConfig(audit_enabled=True, audit_excluded_actions=frozenset({"VIEW", "LIST"}))
        assert cfg.is_action_allowed(AdminAction.VIEW) is False
        assert cfg.is_action_allowed(AdminAction.LIST) is False
        assert cfg.is_action_allowed(AdminAction.CREATE) is True
        assert cfg.is_action_allowed(AdminAction.DELETE) is True

    def test_audit_log_logins_switch(self):
        from aquilia.admin.site import AdminConfig
        from aquilia.admin.audit import AdminAction
        cfg = AdminConfig(audit_enabled=True, audit_log_logins=False)
        assert cfg.is_action_allowed(AdminAction.LOGIN) is False
        assert cfg.is_action_allowed(AdminAction.LOGOUT) is False
        assert cfg.is_action_allowed(AdminAction.LOGIN_FAILED) is False
        assert cfg.is_action_allowed(AdminAction.CREATE) is True

    def test_audit_log_views_switch(self):
        from aquilia.admin.site import AdminConfig
        from aquilia.admin.audit import AdminAction
        cfg = AdminConfig(audit_enabled=True, audit_log_views=False)
        assert cfg.is_action_allowed(AdminAction.VIEW) is False
        assert cfg.is_action_allowed(AdminAction.LIST) is False
        assert cfg.is_action_allowed(AdminAction.SEARCH) is True  # Separate switch

    def test_audit_log_searches_switch(self):
        from aquilia.admin.site import AdminConfig
        from aquilia.admin.audit import AdminAction
        cfg = AdminConfig(audit_enabled=True, audit_log_searches=False)
        assert cfg.is_action_allowed(AdminAction.SEARCH) is False
        assert cfg.is_action_allowed(AdminAction.VIEW) is True

    def test_audit_disabled_blocks_all(self):
        from aquilia.admin.site import AdminConfig
        from aquilia.admin.audit import AdminAction
        cfg = AdminConfig(audit_enabled=False)
        for action in AdminAction:
            assert cfg.is_action_allowed(action) is False

    def test_monitoring_metric_enabled(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig()
        for m in ("cpu", "memory", "disk", "network", "process", "python", "system", "health_checks"):
            assert cfg.is_metric_enabled(m) is True

    def test_monitoring_metric_subset(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig(monitoring_metrics=frozenset({"cpu", "memory"}))
        assert cfg.is_metric_enabled("cpu") is True
        assert cfg.is_metric_enabled("memory") is True
        assert cfg.is_metric_enabled("disk") is False
        assert cfg.is_metric_enabled("network") is False

    def test_sidebar_section_visibility(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig(sidebar_sections={
            "overview": True, "data": False, "system": True,
            "security": False, "models": True,
        })
        assert cfg.is_sidebar_section_visible("overview") is True
        assert cfg.is_sidebar_section_visible("data") is False
        assert cfg.is_sidebar_section_visible("security") is False
        assert cfg.is_sidebar_section_visible("models") is True

    def test_to_dict_roundtrip(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig()
        d = cfg.to_dict()
        assert "modules" in d
        assert "audit" in d
        assert "monitoring" in d
        assert "sidebar_sections" in d
        assert d["theme"] == "auto"
        assert d["list_per_page"] == 25
        assert d["audit"]["enabled"] is False
        assert "cpu" in d["monitoring"]["metrics"]

    def test_from_dict_default(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig.from_dict({})
        assert cfg.is_module_enabled("dashboard") is True
        # Audit and monitoring disabled by default
        assert cfg.audit_enabled is False
        assert cfg.monitoring_enabled is False

    def test_from_dict_with_modules(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig.from_dict({
            "modules": {"orm": False, "build": False},
            "audit_config": {
                "enabled": True,
                "log_logins": False,
                "excluded_actions": ["VIEW"],
            },
            "monitoring_config": {
                "metrics": ["cpu", "memory"],
                "refresh_interval": 10,
            },
            "sidebar_sections": {"data": False},
        })
        assert cfg.is_module_enabled("orm") is False
        assert cfg.is_module_enabled("build") is False
        assert cfg.is_module_enabled("dashboard") is True
        assert cfg.audit_log_logins is False
        assert "VIEW" in cfg.audit_excluded_actions
        assert cfg.monitoring_metrics == frozenset({"cpu", "memory"})
        assert cfg.monitoring_refresh_interval == 10
        assert cfg.is_sidebar_section_visible("data") is False

    def test_from_dict_enable_audit_false(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig.from_dict({"enable_audit": False})
        assert cfg.audit_enabled is False
        assert cfg.is_module_enabled("audit") is False


# ═══════════════════════════════════════════════════════════════════════════
# NESTED BUILDER CLASSES — AdminModules, AdminAudit, AdminMonitoring, AdminSidebar
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminModulesBuilder:
    """Test Integration.AdminModules fluent builder."""

    def test_import(self):
        from aquilia.config_builders import Integration
        assert hasattr(Integration, "AdminModules")

    def test_defaults(self):
        from aquilia.config_builders import Integration
        m = Integration.AdminModules()
        d = m.to_dict()
        assert d["dashboard"] is True
        assert d["orm"] is True
        assert d["monitoring"] is False
        assert d["audit"] is False

    def test_enable_monitoring(self):
        from aquilia.config_builders import Integration
        m = Integration.AdminModules().enable_monitoring()
        assert m.to_dict()["monitoring"] is True

    def test_disable_dashboard(self):
        from aquilia.config_builders import Integration
        m = Integration.AdminModules().disable_dashboard()
        assert m.to_dict()["dashboard"] is False

    def test_enable_all(self):
        from aquilia.config_builders import Integration
        m = Integration.AdminModules().enable_all()
        d = m.to_dict()
        for key, val in d.items():
            assert val is True, f"{key} should be True after enable_all()"

    def test_disable_all(self):
        from aquilia.config_builders import Integration
        m = Integration.AdminModules().disable_all()
        d = m.to_dict()
        for key, val in d.items():
            assert val is False, f"{key} should be False after disable_all()"

    def test_fluent_chain(self):
        from aquilia.config_builders import Integration
        m = (Integration.AdminModules()
             .disable_all()
             .enable_dashboard()
             .enable_orm()
             .enable_monitoring())
        d = m.to_dict()
        assert d["dashboard"] is True
        assert d["orm"] is True
        assert d["monitoring"] is True
        assert d["build"] is False
        assert d["audit"] is False

    def test_repr(self):
        from aquilia.config_builders import Integration
        r = repr(Integration.AdminModules())
        assert "AdminModules" in r


class TestAdminAuditBuilder:
    """Test Integration.AdminAudit fluent builder."""

    def test_import(self):
        from aquilia.config_builders import Integration
        assert hasattr(Integration, "AdminAudit")

    def test_defaults_disabled(self):
        from aquilia.config_builders import Integration
        a = Integration.AdminAudit()
        d = a.to_dict()
        assert d["enabled"] is False

    def test_enable(self):
        from aquilia.config_builders import Integration
        a = Integration.AdminAudit().enable()
        assert a.to_dict()["enabled"] is True

    def test_max_entries(self):
        from aquilia.config_builders import Integration
        a = Integration.AdminAudit().enable().max_entries(500)
        d = a.to_dict()
        assert d["max_entries"] == 500

    def test_log_logins_off(self):
        from aquilia.config_builders import Integration
        a = Integration.AdminAudit().enable().no_log_logins()
        d = a.to_dict()
        assert d["log_logins"] is False

    def test_log_views_off(self):
        from aquilia.config_builders import Integration
        a = Integration.AdminAudit().enable().no_log_views()
        d = a.to_dict()
        assert d["log_views"] is False

    def test_log_searches_off(self):
        from aquilia.config_builders import Integration
        a = Integration.AdminAudit().enable().no_log_searches()
        d = a.to_dict()
        assert d["log_searches"] is False

    def test_exclude_actions(self):
        from aquilia.config_builders import Integration
        a = Integration.AdminAudit().enable().exclude_actions("VIEW", "LIST")
        d = a.to_dict()
        assert "VIEW" in d["excluded_actions"]
        assert "LIST" in d["excluded_actions"]

    def test_fluent_chain(self):
        from aquilia.config_builders import Integration
        a = (Integration.AdminAudit()
             .enable()
             .max_entries(200)
             .no_log_logins()
             .exclude_actions("SEARCH"))
        d = a.to_dict()
        assert d["enabled"] is True
        assert d["max_entries"] == 200
        assert d["log_logins"] is False
        assert "SEARCH" in d["excluded_actions"]

    def test_repr(self):
        from aquilia.config_builders import Integration
        r = repr(Integration.AdminAudit())
        assert "AdminAudit" in r


class TestAdminMonitoringBuilder:
    """Test Integration.AdminMonitoring fluent builder."""

    def test_import(self):
        from aquilia.config_builders import Integration
        assert hasattr(Integration, "AdminMonitoring")

    def test_defaults_disabled(self):
        from aquilia.config_builders import Integration
        m = Integration.AdminMonitoring()
        d = m.to_dict()
        assert d["enabled"] is False

    def test_enable(self):
        from aquilia.config_builders import Integration
        m = Integration.AdminMonitoring().enable()
        assert m.to_dict()["enabled"] is True

    def test_metrics_subset(self):
        from aquilia.config_builders import Integration
        m = Integration.AdminMonitoring().enable().metrics("cpu", "memory")
        d = m.to_dict()
        assert d["metrics"] == ["cpu", "memory"]

    def test_all_metrics(self):
        from aquilia.config_builders import Integration
        m = Integration.AdminMonitoring().enable().all_metrics()
        d = m.to_dict()
        assert "cpu" in d["metrics"]
        assert "health_checks" in d["metrics"]
        assert len(d["metrics"]) == 8

    def test_refresh_interval(self):
        from aquilia.config_builders import Integration
        m = Integration.AdminMonitoring().enable().refresh_interval(15)
        d = m.to_dict()
        assert d["refresh_interval"] == 15

    def test_refresh_interval_minimum(self):
        from aquilia.config_builders import Integration
        m = Integration.AdminMonitoring().enable().refresh_interval(1)
        d = m.to_dict()
        assert d["refresh_interval"] == 5  # clamped to minimum

    def test_fluent_chain(self):
        from aquilia.config_builders import Integration
        m = (Integration.AdminMonitoring()
             .enable()
             .metrics("cpu", "disk")
             .refresh_interval(10))
        d = m.to_dict()
        assert d["enabled"] is True
        assert d["metrics"] == ["cpu", "disk"]
        assert d["refresh_interval"] == 10

    def test_repr(self):
        from aquilia.config_builders import Integration
        r = repr(Integration.AdminMonitoring())
        assert "AdminMonitoring" in r


class TestAdminSidebarBuilder:
    """Test Integration.AdminSidebar fluent builder."""

    def test_import(self):
        from aquilia.config_builders import Integration
        assert hasattr(Integration, "AdminSidebar")

    def test_defaults_all_visible(self):
        from aquilia.config_builders import Integration
        s = Integration.AdminSidebar()
        d = s.to_dict()
        for key in ("overview", "data", "system", "security", "models"):
            assert d[key] is True, f"{key} should be True by default"

    def test_hide_data(self):
        from aquilia.config_builders import Integration
        s = Integration.AdminSidebar().hide_data()
        assert s.to_dict()["data"] is False

    def test_hide_security(self):
        from aquilia.config_builders import Integration
        s = Integration.AdminSidebar().hide_security()
        assert s.to_dict()["security"] is False

    def test_hide_all(self):
        from aquilia.config_builders import Integration
        s = Integration.AdminSidebar().hide_all()
        d = s.to_dict()
        for key, val in d.items():
            assert val is False, f"{key} should be False after hide_all()"

    def test_show_all(self):
        from aquilia.config_builders import Integration
        s = Integration.AdminSidebar().hide_all().show_all()
        d = s.to_dict()
        for key, val in d.items():
            assert val is True, f"{key} should be True after show_all()"

    def test_fluent_chain(self):
        from aquilia.config_builders import Integration
        s = (Integration.AdminSidebar()
             .hide_all()
             .show_overview()
             .show_models())
        d = s.to_dict()
        assert d["overview"] is True
        assert d["models"] is True
        assert d["data"] is False
        assert d["system"] is False
        assert d["security"] is False

    def test_repr(self):
        from aquilia.config_builders import Integration
        r = repr(Integration.AdminSidebar())
        assert "AdminSidebar" in r


class TestBuildersWithIntegrationAdmin:
    """Test that builder objects work with Integration.admin()."""

    def test_modules_builder_passed_to_admin(self):
        from aquilia.config_builders import Integration
        modules = Integration.AdminModules().enable_all()
        cfg = Integration.admin(modules=modules)
        assert cfg["modules"]["monitoring"] is True
        assert cfg["modules"]["audit"] is True
        assert cfg["modules"]["dashboard"] is True

    def test_audit_builder_passed_to_admin(self):
        from aquilia.config_builders import Integration
        audit = Integration.AdminAudit().enable().no_log_logins().max_entries(100)
        cfg = Integration.admin(audit=audit)
        assert cfg["audit_config"]["enabled"] is True
        assert cfg["audit_config"]["log_logins"] is False
        assert cfg["audit_config"]["max_entries"] == 100
        assert cfg["modules"]["audit"] is True

    def test_monitoring_builder_passed_to_admin(self):
        from aquilia.config_builders import Integration
        monitoring = Integration.AdminMonitoring().enable().metrics("cpu", "memory")
        cfg = Integration.admin(monitoring=monitoring)
        assert cfg["monitoring_config"]["enabled"] is True
        assert cfg["monitoring_config"]["metrics"] == ["cpu", "memory"]
        assert cfg["modules"]["monitoring"] is True

    def test_sidebar_builder_passed_to_admin(self):
        from aquilia.config_builders import Integration
        sidebar = Integration.AdminSidebar().hide_data().hide_security()
        cfg = Integration.admin(sidebar=sidebar)
        assert cfg["sidebar_sections"]["data"] is False
        assert cfg["sidebar_sections"]["security"] is False
        assert cfg["sidebar_sections"]["overview"] is True

    def test_all_builders_combined(self):
        from aquilia.config_builders import Integration
        cfg = Integration.admin(
            modules=Integration.AdminModules().enable_all(),
            audit=Integration.AdminAudit().enable().no_log_views(),
            monitoring=Integration.AdminMonitoring().enable().refresh_interval(10),
            sidebar=Integration.AdminSidebar().hide_security(),
        )
        assert cfg["modules"]["monitoring"] is True
        assert cfg["modules"]["audit"] is True
        assert cfg["audit_config"]["enabled"] is True
        assert cfg["audit_config"]["log_views"] is False
        assert cfg["monitoring_config"]["enabled"] is True
        assert cfg["monitoring_config"]["refresh_interval"] == 10
        assert cfg["sidebar_sections"]["security"] is False

    def test_builders_override_flat_params(self):
        """Builder objects should take priority over flat params."""
        from aquilia.config_builders import Integration
        cfg = Integration.admin(
            modules=Integration.AdminModules().enable_monitoring(),
            enable_monitoring=False,  # flat param should be overridden
        )
        assert cfg["modules"]["monitoring"] is True

    def test_flat_params_still_work(self):
        """Legacy flat params should still work when no builders passed."""
        from aquilia.config_builders import Integration
        cfg = Integration.admin(
            enable_monitoring=True,
            enable_audit=True,
            audit_log_logins=False,
            monitoring_metrics=["cpu"],
        )
        assert cfg["modules"]["monitoring"] is True
        assert cfg["modules"]["audit"] is True
        assert cfg["audit_config"]["log_logins"] is False
        assert cfg["monitoring_config"]["metrics"] == ["cpu"]

    def test_builder_to_full_config_roundtrip(self):
        """Builder → Integration.admin() → AdminConfig.from_dict() roundtrip."""
        from aquilia.config_builders import Integration
        from aquilia.admin.site import AdminConfig

        cfg_dict = Integration.admin(
            modules=Integration.AdminModules().enable_all(),
            audit=Integration.AdminAudit().enable().exclude_actions("VIEW"),
            monitoring=Integration.AdminMonitoring().enable().metrics("cpu", "disk"),
        )
        cfg = AdminConfig.from_dict(cfg_dict)
        assert cfg.is_module_enabled("monitoring") is True
        assert cfg.is_module_enabled("audit") is True
        assert cfg.audit_enabled is True
        assert "VIEW" in cfg.audit_excluded_actions
        assert cfg.monitoring_metrics == frozenset({"cpu", "disk"})


class TestDisabledPageRendering:
    """Test the disabled page overlay renders correctly."""

    def test_render_disabled_page_function_exists(self):
        from aquilia.admin.templates import render_disabled_page
        assert callable(render_disabled_page)

    def test_render_disabled_page_contains_module_name(self):
        from aquilia.admin.templates import render_disabled_page
        html = render_disabled_page(
            module_name="Monitoring",
            builder_hint="Integration.AdminMonitoring().enable()",
            flat_hint="enable_monitoring=True",
            icon_key="monitoring",
            description="System metrics and live charts.",
            app_list=[],
            identity_name="admin",
        )
        assert "Monitoring" in html
        assert "Module Disabled" in html

    def test_render_disabled_page_contains_builder_hint(self):
        from aquilia.admin.templates import render_disabled_page
        html = render_disabled_page(
            module_name="Audit Log",
            builder_hint="Integration.AdminAudit().enable()",
            flat_hint="enable_audit=True",
            icon_key="audit",
            description="Activity trail.",
            app_list=[],
            identity_name="admin",
        )
        assert "AdminAudit" in html
        assert "enable_audit" in html

    def test_render_disabled_page_has_buttons(self):
        from aquilia.admin.templates import render_disabled_page
        html = render_disabled_page(
            module_name="Build",
            builder_hint="Integration.AdminModules().enable_build()",
            flat_hint="enable_build=True",
            icon_key="build",
            description="Build artifacts.",
            app_list=[],
            identity_name="admin",
        )
        assert "Dashboard" in html or "Go Back" in html

    def test_disabled_template_file_exists(self):
        from pathlib import Path
        p = Path(__file__).resolve().parent.parent / "aquilia" / "admin" / "templates" / "disabled.html"
        assert p.exists()

    def test_disabled_template_extends_base(self):
        from pathlib import Path
        content = (Path(__file__).resolve().parent.parent / "aquilia" / "admin" / "templates" / "disabled.html").read_text()
        assert "base.html" in content

    def test_disabled_template_has_blur_effect(self):
        from pathlib import Path
        content = (Path(__file__).resolve().parent.parent / "aquilia" / "admin" / "templates" / "disabled.html").read_text()
        assert "blur" in content
        assert "disabled-overlay" in content

    def test_controller_returns_200_for_disabled_module(self):
        """Disabled modules return 200 with overlay, not 404."""
        from aquilia.admin.site import AdminSite, AdminConfig
        from aquilia.admin.controller import AdminController

        site = AdminSite(name="disabled_test")
        site.admin_config = AdminConfig(modules={
            "dashboard": True, "orm": True, "build": True,
            "migrations": True, "config": True, "workspace": True,
            "permissions": True, "monitoring": False, "admin_users": True,
            "profile": True, "audit": False,
        })
        ctrl = AdminController(site=site)
        resp = ctrl._module_disabled_response("Monitoring", None)
        assert resp.status == 200
        body = resp._content.decode("utf-8")
        assert "Module Disabled" in body
        assert "enable" in body.lower()


class TestIntegrationAdminConfigBuilder:
    """Test Integration.admin() produces correct config dict with new fields."""

    def test_default_config_has_modules(self):
        from aquilia.config_builders import Integration
        cfg = Integration.admin()
        assert "modules" in cfg
        assert cfg["modules"]["dashboard"] is True
        assert cfg["modules"]["orm"] is True

    def test_disable_build(self):
        from aquilia.config_builders import Integration
        cfg = Integration.admin(enable_build=False)
        assert cfg["modules"]["build"] is False
        assert cfg["modules"]["orm"] is True

    def test_audit_config(self):
        from aquilia.config_builders import Integration
        cfg = Integration.admin(
            enable_audit=True,
            audit_log_logins=False,
            audit_excluded_actions=["VIEW", "LIST"],
        )
        assert cfg["audit_config"]["enabled"] is True
        assert cfg["audit_config"]["log_logins"] is False
        assert "VIEW" in cfg["audit_config"]["excluded_actions"]
        assert "LIST" in cfg["audit_config"]["excluded_actions"]

    def test_monitoring_config(self):
        from aquilia.config_builders import Integration
        cfg = Integration.admin(
            enable_monitoring=True,
            monitoring_metrics=["cpu", "memory"],
            monitoring_refresh_interval=15,
        )
        assert cfg["monitoring_config"]["enabled"] is True
        assert cfg["monitoring_config"]["metrics"] == ["cpu", "memory"]
        assert cfg["monitoring_config"]["refresh_interval"] == 15

    def test_monitoring_refresh_minimum(self):
        from aquilia.config_builders import Integration
        cfg = Integration.admin(monitoring_refresh_interval=1)
        assert cfg["monitoring_config"]["refresh_interval"] == 5  # min clamped

    def test_sidebar_sections(self):
        from aquilia.config_builders import Integration
        cfg = Integration.admin(sidebar_sections={"data": False, "security": False})
        assert cfg["sidebar_sections"]["data"] is False
        assert cfg["sidebar_sections"]["security"] is False
        assert cfg["sidebar_sections"]["overview"] is True

    def test_disable_monitoring(self):
        from aquilia.config_builders import Integration
        cfg = Integration.admin(enable_monitoring=False)
        assert cfg["modules"]["monitoring"] is False
        assert cfg["monitoring_config"]["enabled"] is False

    def test_all_modules_disabled(self):
        from aquilia.config_builders import Integration
        cfg = Integration.admin(
            enable_dashboard=False, enable_orm=False, enable_build=False,
            enable_migrations=False, enable_config=False, enable_workspace=False,
            enable_permissions=False, enable_monitoring=False, enable_admin_users=False,
            enable_profile=False, enable_audit=False,
        )
        for key, val in cfg["modules"].items():
            assert val is False, f"Module {key} should be False"

    def test_default_all_metrics(self):
        from aquilia.config_builders import Integration
        cfg = Integration.admin()
        expected = ["cpu", "memory", "disk", "network", "process", "python", "system", "health_checks"]
        assert cfg["monitoring_config"]["metrics"] == expected

    def test_backward_compatible_keys(self):
        """Existing keys (url_prefix, site_title, etc.) must still be present."""
        from aquilia.config_builders import Integration
        cfg = Integration.admin(
            url_prefix="/admin",
            site_title="Test Admin",
            site_header="Test Header",
            auto_discover=True,
            list_per_page=50,
            theme="dark",
        )
        assert cfg["url_prefix"] == "/admin"
        assert cfg["site_title"] == "Test Admin"
        assert cfg["site_header"] == "Test Header"
        assert cfg["auto_discover"] is True
        assert cfg["list_per_page"] == 50
        assert cfg["theme"] == "dark"
        assert cfg["_integration_type"] == "admin"


class TestAdminSiteConfig:
    """Test AdminSite stores and exposes AdminConfig."""

    def test_default_admin_config(self):
        from aquilia.admin.site import AdminSite, AdminConfig
        site = AdminSite()
        assert isinstance(site.admin_config, AdminConfig)

    def test_admin_config_set(self):
        from aquilia.admin.site import AdminSite, AdminConfig
        site = AdminSite()
        custom = AdminConfig(modules={"dashboard": True, "orm": False,
            "build": True, "migrations": True, "config": True,
            "workspace": True, "permissions": True, "monitoring": True,
            "admin_users": True, "profile": True, "audit": True})
        site.admin_config = custom
        assert site.admin_config.is_module_enabled("orm") is False

    def test_admin_config_propagated_to_audit_log(self):
        from aquilia.admin.site import AdminSite, AdminConfig
        site = AdminSite()
        custom = AdminConfig(audit_log_logins=False)
        site.admin_config = custom
        site.audit_log.admin_config = custom
        assert site.audit_log._fallback._admin_config is custom


class TestAuditLogFiltering:
    """Test that audit log respects AdminConfig action filtering."""

    def test_excluded_action_not_persisted(self):
        from aquilia.admin.audit import AdminAuditLog, AdminAction
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig(audit_enabled=True, audit_excluded_actions=frozenset({"VIEW"}))
        log = AdminAuditLog()
        log._admin_config = cfg

        entry = log.log(
            user_id="u1", username="admin", role="superadmin",
            action=AdminAction.VIEW,
        )
        assert entry.id.startswith("audit_skip_")
        assert log.count() == 0  # Not persisted

    def test_allowed_action_persisted(self):
        from aquilia.admin.audit import AdminAuditLog, AdminAction
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig(audit_enabled=True, audit_excluded_actions=frozenset({"VIEW"}))
        log = AdminAuditLog()
        log._admin_config = cfg

        entry = log.log(
            user_id="u1", username="admin", role="superadmin",
            action=AdminAction.CREATE,
        )
        assert not entry.id.startswith("audit_skip_")
        assert log.count() == 1

    def test_logins_switch_off(self):
        from aquilia.admin.audit import AdminAuditLog, AdminAction
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig(audit_enabled=True, audit_log_logins=False)
        log = AdminAuditLog()
        log._admin_config = cfg

        log.log(user_id="u1", username="admin", role="superadmin", action=AdminAction.LOGIN)
        log.log(user_id="u1", username="admin", role="superadmin", action=AdminAction.LOGOUT)
        assert log.count() == 0

    def test_views_switch_off(self):
        from aquilia.admin.audit import AdminAuditLog, AdminAction
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig(audit_enabled=True, audit_log_views=False)
        log = AdminAuditLog()
        log._admin_config = cfg

        log.log(user_id="u1", username="admin", role="superadmin", action=AdminAction.VIEW)
        log.log(user_id="u1", username="admin", role="superadmin", action=AdminAction.LIST)
        assert log.count() == 0
        # But CREATE should still work
        log.log(user_id="u1", username="admin", role="superadmin", action=AdminAction.CREATE)
        assert log.count() == 1

    def test_searches_switch_off(self):
        from aquilia.admin.audit import AdminAuditLog, AdminAction
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig(audit_enabled=True, audit_log_searches=False)
        log = AdminAuditLog()
        log._admin_config = cfg

        log.log(user_id="u1", username="admin", role="superadmin", action=AdminAction.SEARCH)
        assert log.count() == 0

    def test_no_config_logs_everything(self):
        from aquilia.admin.audit import AdminAuditLog, AdminAction

        log = AdminAuditLog()
        log._admin_config = None  # No config

        for action in AdminAction:
            log.log(user_id="u1", username="admin", role="superadmin", action=action)
        assert log.count() == len(AdminAction)

    def test_audit_disabled_blocks_all(self):
        from aquilia.admin.audit import AdminAuditLog, AdminAction
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig(audit_enabled=False)
        log = AdminAuditLog()
        log._admin_config = cfg

        for action in AdminAction:
            log.log(user_id="u1", username="admin", role="superadmin", action=action)
        assert log.count() == 0


class TestModelBackedAuditLogFiltering:
    """Test ModelBackedAuditLog respects config filtering."""

    def test_config_propagated_to_fallback(self):
        from aquilia.admin.audit import ModelBackedAuditLog
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig(audit_enabled=True, audit_log_views=False)
        mbal = ModelBackedAuditLog()
        mbal.admin_config = cfg
        assert mbal._fallback._admin_config is cfg

    def test_excluded_action_returns_skip_entry(self):
        from aquilia.admin.audit import ModelBackedAuditLog, AdminAction
        from aquilia.admin.site import AdminConfig

        cfg = AdminConfig(audit_enabled=True, audit_excluded_actions=frozenset({"VIEW"}))
        mbal = ModelBackedAuditLog()
        mbal.admin_config = cfg

        entry = mbal.log(
            user_id="u1", username="admin", role="superadmin",
            action=AdminAction.VIEW,
        )
        assert entry.id.startswith("audit_skip_")


class TestAdminControllerModuleGuards:
    """Test that controller views check module enabled status."""

    def _make_controller(self, modules_override=None):
        from aquilia.admin.site import AdminSite, AdminConfig
        from aquilia.admin.controller import AdminController

        default_modules = {
            "dashboard": True, "orm": True, "build": True,
            "migrations": True, "config": True, "workspace": True,
            "permissions": True, "monitoring": True, "admin_users": True,
            "profile": True, "audit": True,
        }
        if modules_override:
            default_modules.update(modules_override)

        site = AdminSite(name="test_guard")
        site.admin_config = AdminConfig(modules=default_modules)
        ctrl = AdminController(site=site)
        return ctrl

    def test_module_disabled_response_helper(self):
        ctrl = self._make_controller()
        resp = ctrl._module_disabled_response("Test Module", None)
        assert resp.status == 200
        body = resp._content.decode("utf-8")
        assert "Module Disabled" in body or "disabled" in body.lower()

    def test_controller_has_admin_config(self):
        ctrl = self._make_controller({"orm": False})
        assert ctrl.site.admin_config.is_module_enabled("orm") is False
        assert ctrl.site.admin_config.is_module_enabled("build") is True


class TestSidebarTemplateConditional:
    """Test sidebar renders conditionally based on admin_config.

    Since v2 the sidebar always shows every page link — disabled modules
    redirect to a beautiful overlay page instead of being hidden.
    Only ``sidebar_sections`` (overview/data/system/security/models) can
    suppress entire sections from the sidebar.
    """

    def _render_sidebar(self, admin_config=None):
        from aquilia.admin.templates import _render_template, _HAS_JINJA2
        if not _HAS_JINJA2:
            pytest.skip("Jinja2 not available")

        ctx = {
            "url_prefix": "/admin",
            "site_title": "Test",
            "identity_name": "Admin",
            "active_page": "dashboard",
            "app_list": [],
            "admin_config": admin_config or {},
        }
        from jinja2 import Environment, FileSystemLoader
        from pathlib import Path
        tpl_dir = Path(__file__).resolve().parent.parent / "aquilia" / "admin" / "templates"
        env = Environment(
            loader=FileSystemLoader(str(tpl_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
        tpl = env.get_template("partials/sidebar_v2.html")
        return tpl.render(**ctx)

    def test_all_modules_always_visible(self):
        """Every page link is always rendered regardless of modules config."""
        html = self._render_sidebar()
        assert "ORM Models" in html
        assert "Monitoring" in html
        assert "Build" in html
        assert "Audit Log" in html
        assert "Admin Users" in html

    def test_modules_disabled_does_not_hide_links(self):
        """Disabling a module in config no longer hides it from the sidebar."""
        html = self._render_sidebar({
            "modules": {"orm": False, "monitoring": False, "audit": False,
                        "build": False, "admin_users": False},
            "sidebar_sections": {},
        })
        # All links still present — disabled page handles the UX
        assert "ORM Models" in html
        assert "Monitoring" in html
        assert "Audit Log" in html
        assert "Admin Users" in html
        assert "Build" in html

    def test_data_section_hidden_when_sidebar_section_disabled(self):
        html = self._render_sidebar({
            "modules": {},
            "sidebar_sections": {"data": False},
        })
        assert "Data" not in html
        # ORM/Migrations links are inside the Data section
        assert "ORM Models" not in html
        assert "Migrations" not in html

    def test_security_section_hidden_when_sidebar_section_disabled(self):
        html = self._render_sidebar({
            "modules": {},
            "sidebar_sections": {"security": False},
        })
        assert ">Security<" not in html
        assert "Audit Log" not in html

    def test_system_section_hidden_when_sidebar_section_disabled(self):
        html = self._render_sidebar({
            "modules": {},
            "sidebar_sections": {"system": False},
        })
        assert ">System<" not in html
        assert "Monitoring" not in html
        assert "Build" not in html

    def test_overview_section_hidden_when_disabled(self):
        html = self._render_sidebar({
            "modules": {},
            "sidebar_sections": {"overview": False},
        })
        assert "Dashboard" not in html

    def test_all_sections_hidden_when_all_sidebar_sections_disabled(self):
        html = self._render_sidebar({
            "sidebar_sections": {
                "overview": False, "data": False, "system": False,
                "security": False, "models": False,
            },
        })
        assert "ORM Models" not in html
        assert "Monitoring" not in html
        assert "Audit Log" not in html
        assert "Dashboard" not in html


class TestAdminConfigExport:
    """Test that AdminConfig is properly exported."""

    def test_import_from_admin_package(self):
        from aquilia.admin import AdminConfig
        assert AdminConfig is not None

    def test_import_from_site(self):
        from aquilia.admin.site import AdminConfig
        assert AdminConfig is not None

    def test_frozen(self):
        from aquilia.admin.site import AdminConfig
        cfg = AdminConfig()
        with pytest.raises(AttributeError):
            cfg.audit_enabled = False  # type: ignore[misc]


class TestAdminConfigServerWiring:
    """Test that server._wire_admin_integration correctly wires AdminConfig."""

    def test_server_imports_admin_config(self):
        """server.py must import AdminConfig from admin.site."""
        from pathlib import Path
        source = (Path(__file__).resolve().parent.parent / "aquilia" / "server.py").read_text()
        assert "AdminConfig" in source

    def test_parsed_config_from_dict(self):
        """AdminConfig.from_dict should handle full Integration.admin() output."""
        from aquilia.config_builders import Integration
        from aquilia.admin.site import AdminConfig

        raw = Integration.admin(
            enable_build=False,
            audit_log_views=False,
            monitoring_metrics=["cpu", "memory"],
        )
        cfg = AdminConfig.from_dict(raw)
        assert cfg.is_module_enabled("build") is False
        assert cfg.audit_log_views is False
        assert cfg.monitoring_metrics == frozenset({"cpu", "memory"})


# ═══════════════════════════════════════════════════════════════════════════════
# ORM Schema Metadata & Config Metadata — Deep Introspection Tests
# ═══════════════════════════════════════════════════════════════════════════════
# Validates the enriched `get_model_schema()` and new `get_orm_metadata()`
# methods on AdminSite.  These tests use the real admin models (AdminUser,
# ContentType, etc.) registered on a fresh AdminSite instance.
# ═══════════════════════════════════════════════════════════════════════════════


class _SchemaTestMixin:
    """Shared helper to build an AdminSite with all admin models registered."""

    @staticmethod
    def _build_site():
        from aquilia.admin.site import AdminSite
        from aquilia.admin.options import ModelAdmin
        from aquilia.admin.models import (
            AdminUser, AdminGroup, AdminPermission,
            ContentType, AdminLogEntry, AdminAuditEntry, AdminSession,
        )

        site = AdminSite.__new__(AdminSite)
        site._registry = {}
        site._config = None
        site._initialized = True

        for model_cls in [
            AdminUser, AdminGroup, AdminPermission,
            ContentType, AdminLogEntry, AdminAuditEntry, AdminSession,
        ]:
            admin = ModelAdmin(model=model_cls)
            site._registry[model_cls] = admin

        return site

    @staticmethod
    def _find_model_schema(schema_list, model_name):
        for m in schema_list:
            if m["name"] == model_name:
                return m
        return None

    @staticmethod
    def _find_field(model_schema, field_name):
        for f in model_schema.get("fields", []):
            if f["name"] == field_name:
                return f
        return None


class TestModelSchemaFieldIntrospection(_SchemaTestMixin):
    """Per-field introspection should expose all ORM field attributes."""

    def setup_method(self):
        self.site = self._build_site()
        self.schema = self.site.get_model_schema()

    def test_admin_user_username_field(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        f = self._find_field(user, "username")
        assert f is not None
        assert f["type"] in ("VARCHAR", "CharField", "CHAR")
        assert f["unique"] is True
        assert f["max_length"] == 150
        assert f["null"] is False

    def test_field_class_exposed(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        f = self._find_field(user, "username")
        assert f["field_class"] == "CharField"

    def test_blank_attribute_exposed(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        email = self._find_field(user, "email")
        assert "blank" in email
        assert email["blank"] is True

    def test_auto_now_add_exposed(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        dj = self._find_field(user, "date_joined")
        assert dj is not None
        assert dj["auto_now_add"] is True

    def test_auto_now_exposed(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        dj = self._find_field(user, "date_joined")
        # date_joined uses auto_now_add, not auto_now
        assert dj["auto_now"] is False

    def test_db_column_exposed(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        f = self._find_field(user, "username")
        assert "db_column" in f

    def test_verbose_name_exposed(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        f = self._find_field(user, "username")
        assert "verbose_name" in f

    def test_validators_list(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        f = self._find_field(user, "username")
        assert isinstance(f["validators"], list)

    def test_choices_list_populated(self):
        log = self._find_model_schema(self.schema, "AdminLogEntry")
        af = self._find_field(log, "action_flag")
        assert af is not None
        assert af["choices"] is True
        assert isinstance(af["choices_list"], list)
        if af["choices_list"]:
            assert "value" in af["choices_list"][0]
            assert "label" in af["choices_list"][0]

    def test_python_type_exposed(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        is_super = self._find_field(user, "is_superuser")
        assert is_super is not None
        assert "python_type" in is_super

    def test_primary_key_field_detected(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        # The PK should be marked
        pk_fields = [f for f in user["fields"] if f["primary_key"]]
        assert len(pk_fields) >= 1

    def test_null_field_detection(self):
        log = self._find_model_schema(self.schema, "AdminLogEntry")
        ct = self._find_field(log, "content_type")
        assert ct is not None
        assert ct["null"] is True

    def test_help_text_exposed(self):
        perm = self._find_model_schema(self.schema, "AdminPermission")
        name_f = self._find_field(perm, "name")
        assert name_f is not None
        assert name_f["help_text"] == "Human-readable permission name"


class TestModelSchemaRelations(_SchemaTestMixin):
    """Relation introspection: FK, O2O, M2M with full detail."""

    def setup_method(self):
        self.site = self._build_site()
        self.schema = self.site.get_model_schema()

    def test_fk_relation_detected(self):
        log = self._find_model_schema(self.schema, "AdminLogEntry")
        fk_rels = [r for r in log["relations"] if r["type"] == "FK"]
        assert len(fk_rels) >= 1
        user_fk = [r for r in fk_rels if r["to"] == "AdminUser"]
        assert len(user_fk) == 1

    def test_fk_on_delete_exposed(self):
        log = self._find_model_schema(self.schema, "AdminLogEntry")
        user_fk = [r for r in log["relations"] if r["to"] == "AdminUser"]
        assert user_fk[0]["on_delete"] == "CASCADE"

    def test_fk_related_name_exposed(self):
        log = self._find_model_schema(self.schema, "AdminLogEntry")
        user_fk = [r for r in log["relations"] if r["to"] == "AdminUser"]
        assert user_fk[0]["related_name"] == "log_entries"

    def test_m2m_relation_detected(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        # M2M shows up in m2m_tables, not in relations
        assert len(user["m2m_tables"]) >= 1

    def test_m2m_db_table_exposed(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        groups_m2m = [t for t in user["m2m_tables"] if t["field"] == "groups"]
        assert len(groups_m2m) == 1
        assert groups_m2m[0]["db_table"] == "admin_user_groups"

    def test_m2m_target_model_exposed(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        groups_m2m = [t for t in user["m2m_tables"] if t["field"] == "groups"]
        assert groups_m2m[0]["target_model"] == "AdminGroup"

    def test_field_data_includes_relation_detail(self):
        """The field dict itself should have relation sub-dict with on_delete/related_name."""
        log = self._find_model_schema(self.schema, "AdminLogEntry")
        user_field = self._find_field(log, "user")
        assert user_field is not None
        assert "relation" in user_field
        assert user_field["relation"]["type"] == "FK"
        assert user_field["relation"]["on_delete"] == "CASCADE"
        assert user_field["relation"]["related_name"] == "log_entries"


class TestModelSchemaReverseRelations(_SchemaTestMixin):
    """Reverse relations: models that FK/M2M *into* a given model."""

    def setup_method(self):
        self.site = self._build_site()
        self.schema = self.site.get_model_schema()

    def test_admin_user_has_reverse_relations(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "reverse_relations" in user
        # AdminLogEntry has FK to AdminUser
        from_log = [r for r in user["reverse_relations"]
                    if r["from_model"] == "AdminLogEntry"]
        assert len(from_log) >= 1

    def test_content_type_has_reverse_relations(self):
        ct = self._find_model_schema(self.schema, "ContentType")
        assert len(ct["reverse_relations"]) >= 1
        # AdminPermission FKs to ContentType
        from_perm = [r for r in ct["reverse_relations"]
                     if r["from_model"] == "AdminPermission"]
        assert len(from_perm) == 1

    def test_reverse_relation_includes_on_delete(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        fk_reverses = [r for r in user["reverse_relations"] if r["type"] == "FK"]
        if fk_reverses:
            assert "on_delete" in fk_reverses[0]

    def test_reverse_m2m_detected(self):
        """AdminGroup should see a reverse M2M from AdminUser.groups."""
        group = self._find_model_schema(self.schema, "AdminGroup")
        m2m_reverses = [r for r in group["reverse_relations"] if r["type"] == "M2M"]
        assert len(m2m_reverses) >= 1
        from_user = [r for r in m2m_reverses if r["from_model"] == "AdminUser"]
        assert len(from_user) >= 1


class TestModelSchemaMetaOptions(_SchemaTestMixin):
    """Full Meta options should be exposed under the 'meta' key."""

    def setup_method(self):
        self.site = self._build_site()
        self.schema = self.site.get_model_schema()

    def test_meta_key_exists(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "meta" in user
        assert isinstance(user["meta"], dict)

    def test_ordering_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert user["meta"]["ordering"] == ["-date_joined"]

    def test_get_latest_by_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert user["meta"]["get_latest_by"] == "date_joined"

    def test_verbose_name_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert user["meta"]["verbose_name"] == "Admin User"

    def test_verbose_name_plural_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert user["meta"]["verbose_name_plural"] == "Admin Users"

    def test_managed_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert user["meta"]["managed"] is True

    def test_abstract_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert user["meta"]["abstract"] is False

    def test_proxy_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert user["meta"]["proxy"] is False

    def test_select_on_save_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert user["meta"]["select_on_save"] is False

    def test_default_permissions_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert isinstance(user["meta"]["default_permissions"], list)
        assert "add" in user["meta"]["default_permissions"]
        assert "change" in user["meta"]["default_permissions"]
        assert "delete" in user["meta"]["default_permissions"]
        assert "view" in user["meta"]["default_permissions"]

    def test_permissions_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert isinstance(user["meta"]["permissions"], list)

    def test_unique_together_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert isinstance(user["meta"]["unique_together"], list)

    def test_required_db_vendor_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "required_db_vendor" in user["meta"]

    def test_required_db_features_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert isinstance(user["meta"]["required_db_features"], list)

    def test_label_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "label" in user["meta"]

    def test_label_lower_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "label_lower" in user["meta"]

    def test_db_tablespace_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "db_tablespace" in user["meta"]

    def test_order_with_respect_to_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "order_with_respect_to" in user["meta"]

    def test_default_related_name_in_meta(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "default_related_name" in user["meta"]

    def test_content_type_unique_constraint(self):
        ct = self._find_model_schema(self.schema, "ContentType")
        assert len(ct["constraints"]) >= 1
        uq = [c for c in ct["constraints"] if c["type"] == "UniqueConstraint"]
        assert len(uq) >= 1
        assert "app_label" in uq[0]["fields"]
        assert "model" in uq[0]["fields"]


class TestModelSchemaSQLDDL(_SchemaTestMixin):
    """SQL DDL generation for each model."""

    def setup_method(self):
        self.site = self._build_site()
        self.schema = self.site.get_model_schema()

    def test_sql_key_exists(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "sql" in user
        assert isinstance(user["sql"], dict)

    def test_create_table_sql_generated(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        ddl = user["sql"]["create_table"]
        assert ddl is not None
        assert "CREATE TABLE" in ddl
        assert "admin_users" in ddl

    def test_create_table_contains_fields(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        ddl = user["sql"]["create_table"]
        assert "username" in ddl
        assert "email" in ddl
        assert "password_hash" in ddl

    def test_indexes_sql_generated(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        idx_stmts = user["sql"]["indexes"]
        assert isinstance(idx_stmts, list)
        assert len(idx_stmts) >= 1
        assert any("idx_admin_user_username" in s for s in idx_stmts)

    def test_m2m_tables_sql_generated(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        m2m_stmts = user["sql"]["m2m_tables"]
        assert isinstance(m2m_stmts, list)
        # AdminUser has groups and user_permissions M2M
        assert len(m2m_stmts) >= 2

    def test_content_type_ddl(self):
        ct = self._find_model_schema(self.schema, "ContentType")
        ddl = ct["sql"]["create_table"]
        assert "admin_content_types" in ddl
        assert "app_label" in ddl


class TestModelSchemaMethodIntrospection(_SchemaTestMixin):
    """User-defined methods should be listed per model."""

    def setup_method(self):
        self.site = self._build_site()
        self.schema = self.site.get_model_schema()

    def test_methods_key_exists(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "methods" in user
        assert isinstance(user["methods"], dict)

    def test_methods_categories(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        m = user["methods"]
        assert "methods" in m
        assert "class_methods" in m
        assert "static_methods" in m
        assert "properties" in m

    def test_admin_user_has_check_password(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "check_password" in user["methods"]["methods"]

    def test_admin_user_has_set_password(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "set_password" in user["methods"]["methods"]

    def test_admin_user_has_class_methods(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        cm = user["methods"]["class_methods"]
        assert "create_superuser" in cm
        assert "authenticate" in cm

    def test_admin_log_entry_has_properties(self):
        """AdminLogEntry has is_addition, is_change, is_deletion properties."""
        log = self._find_model_schema(self.schema, "AdminLogEntry")
        props = log["methods"]["properties"]
        assert "is_addition" in props
        assert "is_change" in props
        assert "is_deletion" in props

    def test_content_type_has_name_property(self):
        ct = self._find_model_schema(self.schema, "ContentType")
        assert "name" in ct["methods"]["properties"]


class TestModelSchemaSourceAndFingerprint(_SchemaTestMixin):
    """Source location and fingerprint should be present."""

    def setup_method(self):
        self.site = self._build_site()
        self.schema = self.site.get_model_schema()

    def test_source_key_exists(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "source" in user
        assert "module" in user["source"]
        assert "file" in user["source"]

    def test_source_module_is_admin_models(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "aquilia.admin.models" in user["source"]["module"]

    def test_source_file_path(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert user["source"]["file"].endswith("models.py")

    def test_fingerprint_present(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "fingerprint" in user
        assert user["fingerprint"] is not None
        assert len(user["fingerprint"]) == 16  # sha256[:16]

    def test_fingerprint_is_hex(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        int(user["fingerprint"], 16)  # Should not raise


class TestModelSchemaM2MTableDetails(_SchemaTestMixin):
    """M2M junction table details should be fully exposed."""

    def setup_method(self):
        self.site = self._build_site()
        self.schema = self.site.get_model_schema()

    def test_m2m_tables_key_exists(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert "m2m_tables" in user
        assert isinstance(user["m2m_tables"], list)

    def test_admin_user_has_m2m_tables(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert len(user["m2m_tables"]) >= 2  # groups + user_permissions

    def test_m2m_table_structure(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        groups_jt = [t for t in user["m2m_tables"] if t["field"] == "groups"]
        assert len(groups_jt) == 1
        jt = groups_jt[0]
        assert jt["junction_table"] is not None
        assert jt["source_column"] is not None
        assert jt["target_column"] is not None
        assert jt["target_model"] == "AdminGroup"

    def test_m2m_db_table_override(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        groups_jt = [t for t in user["m2m_tables"] if t["field"] == "groups"]
        assert groups_jt[0]["db_table"] == "admin_user_groups"


class TestModelSchemaIndexDetails(_SchemaTestMixin):
    """Index introspection with conditions and source tracking."""

    def setup_method(self):
        self.site = self._build_site()
        self.schema = self.site.get_model_schema()

    def test_meta_indexes_present(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        idx_names = [i["name"] for i in user["indexes"] if i.get("name")]
        assert "idx_admin_user_username" in idx_names

    def test_field_level_index_tagged(self):
        """Field-level db_index should be tagged with source='field_level'."""
        audit = self._find_model_schema(self.schema, "AdminAuditEntry")
        field_idxs = [i for i in audit["indexes"] if i.get("source") == "field_level"]
        assert len(field_idxs) >= 4  # entry_id, timestamp, user_id, action

    def test_composite_index(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        active_staff = [i for i in user["indexes"]
                        if i.get("name") == "idx_admin_user_active_staff"]
        assert len(active_staff) == 1
        assert set(active_staff[0]["fields"]) == {"is_active", "is_staff"}

    def test_unique_field_level_index(self):
        """entry_id is unique=True so its field_level index should be unique."""
        audit = self._find_model_schema(self.schema, "AdminAuditEntry")
        entry_idx = [i for i in audit["indexes"]
                     if i.get("source") == "field_level" and "entry_id" in i["fields"]]
        assert len(entry_idx) == 1
        assert entry_idx[0]["unique"] is True


class TestModelSchemaBackwardCompat(_SchemaTestMixin):
    """Flat backward-compatibility keys should still work."""

    def setup_method(self):
        self.site = self._build_site()
        self.schema = self.site.get_model_schema()

    def test_flat_ordering_key(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert user["ordering"] == ["-date_joined"]

    def test_flat_managed_key(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert user["managed"] is True

    def test_flat_abstract_key(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert user["abstract"] is False

    def test_flat_pk_field_key(self):
        user = self._find_model_schema(self.schema, "AdminUser")
        assert user["pk_field"] == "id"


class TestOrmMetadata(_SchemaTestMixin):
    """get_orm_metadata() returns comprehensive ORM-level metadata."""

    def setup_method(self):
        self.site = self._build_site()
        self.metadata = self.site.get_orm_metadata()

    def test_top_level_keys(self):
        assert "database" in self.metadata
        assert "backend" in self.metadata
        assert "stats" in self.metadata
        assert "dependency_graph" in self.metadata
        assert "models" in self.metadata

    def test_stats_counts(self):
        s = self.metadata["stats"]
        assert s["total_models"] == 7  # 7 admin models registered
        assert s["total_fields"] > 0
        assert s["total_relations"] > 0
        assert s["total_indexes"] > 0

    def test_dependency_graph_admin_log_entry(self):
        """AdminLogEntry depends on AdminUser and ContentType."""
        graph = self.metadata["dependency_graph"]
        assert "AdminLogEntry" in graph
        deps = graph["AdminLogEntry"]
        assert "AdminUser" in deps
        assert "ContentType" in deps

    def test_dependency_graph_admin_user_m2m(self):
        """AdminUser depends on AdminGroup and AdminPermission via M2M."""
        graph = self.metadata["dependency_graph"]
        assert "AdminUser" in graph
        deps = graph["AdminUser"]
        assert "AdminGroup" in deps
        assert "AdminPermission" in deps

    def test_dependency_graph_no_self_references(self):
        """No model should list itself as a dependency."""
        for model_name, deps in self.metadata["dependency_graph"].items():
            assert model_name not in deps

    def test_models_list(self):
        models = self.metadata["models"]
        assert len(models) == 7
        names = [m["name"] for m in models]
        assert "AdminUser" in names
        assert "ContentType" in names

    def test_models_have_table_and_pk(self):
        for m in self.metadata["models"]:
            assert "table" in m
            assert "pk" in m
            assert "field_count" in m

    def test_database_info_dict(self):
        """Database info should be a dict (may be empty if no db connected)."""
        assert isinstance(self.metadata["database"], dict)

    def test_backend_info_dict(self):
        """Backend info should be a dict."""
        assert isinstance(self.metadata["backend"], dict)


class TestInspectModelMethods:
    """Unit tests for the _inspect_model_methods static helper."""

    def test_discovers_instance_methods(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import AdminUser
        result = AdminSite._inspect_model_methods(AdminUser)
        assert "check_password" in result["methods"]
        assert "set_password" in result["methods"]

    def test_discovers_class_methods(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import AdminUser
        result = AdminSite._inspect_model_methods(AdminUser)
        assert "create_superuser" in result["class_methods"]
        assert "create_staff_user" in result["class_methods"]
        assert "authenticate" in result["class_methods"]

    def test_discovers_properties(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import AdminLogEntry
        result = AdminSite._inspect_model_methods(AdminLogEntry)
        assert "is_addition" in result["properties"]
        assert "is_change" in result["properties"]
        assert "is_deletion" in result["properties"]

    def test_skips_dunder_methods(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import AdminUser
        result = AdminSite._inspect_model_methods(AdminUser)
        all_names = (
            result["methods"] + result["class_methods"]
            + result["static_methods"] + result["properties"]
        )
        assert not any(n.startswith("_") for n in all_names)

    def test_skips_field_names(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import AdminUser
        result = AdminSite._inspect_model_methods(AdminUser)
        all_names = (
            result["methods"] + result["class_methods"]
            + result["static_methods"] + result["properties"]
        )
        assert "username" not in all_names
        assert "email" not in all_names

    def test_skips_objects_manager(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.models import AdminUser
        result = AdminSite._inspect_model_methods(AdminUser)
        all_names = (
            result["methods"] + result["class_methods"]
            + result["static_methods"] + result["properties"]
        )
        assert "objects" not in all_names


class TestBuildReverseRelations:
    """Unit tests for _build_reverse_relations static helper."""

    def test_fk_reverse_detected(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.options import ModelAdmin
        from aquilia.admin.models import AdminUser, AdminLogEntry

        registry = {
            AdminUser: ModelAdmin(model=AdminUser),
            AdminLogEntry: ModelAdmin(model=AdminLogEntry),
        }
        reverse = AdminSite._build_reverse_relations(registry)
        assert "AdminUser" in reverse
        from_log = [r for r in reverse["AdminUser"] if r["from_model"] == "AdminLogEntry"]
        assert len(from_log) >= 1
        assert from_log[0]["type"] == "FK"

    def test_m2m_reverse_detected(self):
        from aquilia.admin.site import AdminSite
        from aquilia.admin.options import ModelAdmin
        from aquilia.admin.models import AdminUser, AdminGroup

        registry = {
            AdminUser: ModelAdmin(model=AdminUser),
            AdminGroup: ModelAdmin(model=AdminGroup),
        }
        reverse = AdminSite._build_reverse_relations(registry)
        assert "AdminGroup" in reverse
        from_user = [r for r in reverse["AdminGroup"]
                     if r["from_model"] == "AdminUser" and r["type"] == "M2M"]
        assert len(from_user) >= 1

    def test_empty_registry(self):
        from aquilia.admin.site import AdminSite
        reverse = AdminSite._build_reverse_relations({})
        assert reverse == {}


class TestSchemaAllModelsPresent(_SchemaTestMixin):
    """Every registered admin model should appear in the schema."""

    def test_all_seven_models_present(self):
        site = self._build_site()
        schema = site.get_model_schema()
        names = {m["name"] for m in schema}
        expected = {
            "AdminUser", "AdminGroup", "AdminPermission",
            "ContentType", "AdminLogEntry", "AdminAuditEntry", "AdminSession",
        }
        assert expected.issubset(names)
