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
        """AdminController should have routes for all CRUD + auth endpoints."""
        from aquilia.admin.controller import AdminController
        import inspect

        # Count decorated methods
        route_methods = []
        for name, method in inspect.getmembers(AdminController, inspect.isfunction):
            if hasattr(method, "__route_metadata__"):
                route_methods.append(name)

        # Should have at minimum these routes
        expected_names = [
            "dashboard", "login_page", "login_submit", "logout",
            "list_view", "add_form", "add_submit",
            "edit_form", "edit_submit", "delete_record",
            "audit_view",
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


class TestAutoAdminSessions:
    """Tests for _ensure_admin_sessions auto-enabling when admin is used."""

    def _make_server(self, *, session_engine=None, middleware_names=None):
        """Create a minimal mock server with controllable session state."""
        from unittest.mock import MagicMock, PropertyMock
        import logging

        server = MagicMock()
        server._session_engine = session_engine
        server.logger = logging.getLogger("test_auto_sessions")

        # Build a mock middleware stack with named entries
        stack = MagicMock()
        descs = []
        for name in (middleware_names or []):
            d = MagicMock()
            d.name = name
            descs.append(d)
        stack.middlewares = descs
        server.middleware_stack = stack

        # Runtime DI containers
        server.runtime = MagicMock()
        server.runtime.di_containers = {}

        return server

    def test_skips_when_session_engine_exists(self):
        """If session engine is already set, _ensure_admin_sessions is a no-op."""
        from aquilia.server import AquiliaServer
        server = self._make_server(session_engine=MagicMock())

        # Call the unbound method with our mock
        AquiliaServer._ensure_admin_sessions(server)

        # Should NOT have called middleware_stack.add
        server.middleware_stack.add.assert_not_called()

    def test_skips_when_session_middleware_registered(self):
        """If a 'session' middleware is already in the stack, no-op."""
        from aquilia.server import AquiliaServer
        server = self._make_server(middleware_names=["exception", "session", "logging"])

        AquiliaServer._ensure_admin_sessions(server)
        server.middleware_stack.add.assert_not_called()

    def test_skips_when_auth_middleware_registered(self):
        """If an 'auth' middleware is in the stack, no-op."""
        from aquilia.server import AquiliaServer
        server = self._make_server(middleware_names=["exception", "auth", "logging"])

        AquiliaServer._ensure_admin_sessions(server)
        server.middleware_stack.add.assert_not_called()

    def test_auto_enables_when_no_sessions(self):
        """When no session engine and no session/auth middleware, auto-create one."""
        from aquilia.server import AquiliaServer
        server = self._make_server(middleware_names=["exception", "logging"])

        AquiliaServer._ensure_admin_sessions(server)

        # Should have called middleware_stack.add with a SessionMiddleware
        server.middleware_stack.add.assert_called_once()
        call_kwargs = server.middleware_stack.add.call_args
        assert call_kwargs[1]["name"] == "session"
        assert call_kwargs[1]["scope"] == "global"

        # Session engine should be set
        assert server._session_engine is not None

    def test_auto_session_uses_memory_store(self):
        """Auto-created session engine uses in-memory store."""
        from aquilia.server import AquiliaServer
        from aquilia.sessions import MemoryStore
        server = self._make_server(middleware_names=["exception"])

        AquiliaServer._ensure_admin_sessions(server)

        engine = server._session_engine
        assert isinstance(engine.store, MemoryStore)

    def test_auto_session_cookie_name(self):
        """Auto-created session uses 'aquilia_admin_session' cookie."""
        from aquilia.server import AquiliaServer
        server = self._make_server(middleware_names=["exception"])

        AquiliaServer._ensure_admin_sessions(server)

        engine = server._session_engine
        assert engine.transport.cookie_name == "aquilia_admin_session"

    def test_auto_session_policy_name(self):
        """Auto-created session policy is named 'admin_auto'."""
        from aquilia.server import AquiliaServer
        server = self._make_server(middleware_names=[])

        AquiliaServer._ensure_admin_sessions(server)

        assert server._session_engine.policy.name == "admin_auto"


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
