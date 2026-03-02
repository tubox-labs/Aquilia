"""
Comprehensive tests for the Aquilia Admin System (AquilAdmin).

Covers:
- ModelAdmin options & auto-detection
- AdminSite registration & singleton
- Permissions (RBAC roles & permissions)
- Audit trail logging
- Registry (register decorator & autodiscover)
- Faults hierarchy
- Controller route handlers
- Template rendering
- CLI integration
"""

from __future__ import annotations

import asyncio
import datetime
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ── Admin system imports ────────────────────────────────────────────────

from aquilia.admin.faults import (
    AdminFault,
    AdminAuthenticationFault,
    AdminAuthorizationFault,
    AdminModelNotFoundFault,
    AdminRecordNotFoundFault,
    AdminValidationFault,
    AdminActionFault,
)
from aquilia.admin.permissions import (
    AdminRole,
    AdminPermission,
    ROLE_PERMISSIONS,
    get_admin_role,
    has_admin_permission,
    has_model_permission,
    require_admin_access,
)
from aquilia.admin.audit import (
    AdminAction,
    AdminAuditEntry,
    AdminAuditLog,
)
from aquilia.admin.options import (
    ModelAdmin,
    AdminActionDescriptor,
    action,
)
from aquilia.admin.registry import (
    register,
    autodiscover,
    flush_pending_registrations,
    _pending_registrations,
)
from aquilia.admin.site import AdminSite
from aquilia.admin.templates import (
    render_login_page,
    render_dashboard,
    render_list_view,
    render_form_view,
    render_audit_page,
)
from aquilia.admin.controller import (
    AdminController,
    _html_response,
    _redirect,
    _get_identity,
    _get_identity_name,
)


# ═══════════════════════════════════════════════════════════════════════════
# Test helpers: Mock models and identities
# ═══════════════════════════════════════════════════════════════════════════


class MockField:
    """Minimal field mock for auto-detection tests."""
    def __init__(self, name: str, field_type: str = "CharField", **kwargs):
        self.name = name
        self.__class__.__name__ = field_type
        self.primary_key = kwargs.get("primary_key", False)
        self.auto_now = kwargs.get("auto_now", False)
        self.auto_now_add = kwargs.get("auto_now_add", False)
        self.choices = kwargs.get("choices", None)
        self.max_length = kwargs.get("max_length", None)
        self.blank = kwargs.get("blank", False)
        self.null = kwargs.get("null", False)
        self.unique = kwargs.get("unique", False)
        self.help_text = kwargs.get("help_text", "")
        self.default = kwargs.get("default", None)
        self.editable = kwargs.get("editable", True)
        self.verbose_name = kwargs.get("verbose_name", None)

    def has_default(self) -> bool:
        return self.default is not None


class MockManager:
    """Minimal ORM manager mock."""
    async def count(self):
        return 42

    def get_queryset(self):
        return self

    def filter(self, **kwargs):
        return self

    def order(self, *args):
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

    async def update(self, data):
        return 1


class MockModel:
    """
    Minimal Model mock that mirrors aquilia.models.base.Model enough
    for admin tests.
    """
    __name__ = "MockModel"
    _pk_attr = "id"
    _fields: Dict[str, MockField] = {}
    _meta: Any = None
    objects = MockManager()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not hasattr(cls, "_fields") or cls._fields is MockModel._fields:
            cls._fields = {}
        cls.objects = MockManager()

    @classmethod
    async def create(cls, **kwargs):
        obj = cls()
        for k, v in kwargs.items():
            setattr(obj, k, v)
        obj.id = 1
        return obj

    @classmethod
    async def get(cls, pk=None, **kwargs):
        obj = cls()
        obj.id = pk or 1
        return obj

    @property
    def pk(self):
        return getattr(self, "id", None)


class UserModel(MockModel):
    """Test user model with typical fields."""
    __name__ = "UserModel"
    id = 1
    name = "Alice"
    email = "alice@example.com"
    active = True
    created_at = datetime.datetime(2024, 1, 1)

    _fields = {
        "id": MockField("id", "AutoField", primary_key=True),
        "name": MockField("name", "CharField", max_length=100),
        "email": MockField("email", "EmailField"),
        "active": MockField("active", "BooleanField"),
        "created_at": MockField("created_at", "DateTimeField", auto_now_add=True),
        "updated_at": MockField("updated_at", "DateTimeField", auto_now=True),
    }

    class Meta:
        app_label = "accounts"


class PostModel(MockModel):
    """Test post model."""
    __name__ = "PostModel"
    id = 1
    title = "Hello World"
    content = "Test post content"
    published = False

    _fields = {
        "id": MockField("id", "BigAutoField", primary_key=True),
        "title": MockField("title", "CharField", max_length=200),
        "content": MockField("content", "TextField"),
        "published": MockField("published", "BooleanField"),
    }

    class Meta:
        app_label = "blog"


class MockIdentity:
    """Mock identity for permission tests."""
    def __init__(
        self,
        id: str = "user-1",
        roles: Optional[List[str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        is_superuser: bool = False,
        is_staff: bool = False,
    ):
        self.id = id
        self._attrs = attributes or {}
        if roles:
            self._attrs["roles"] = roles
        if is_superuser:
            self._attrs["is_superuser"] = True
        if is_staff:
            self._attrs["is_staff"] = True

    def has_role(self, role: str) -> bool:
        return role in self._attrs.get("roles", [])

    def is_active(self) -> bool:
        return True

    def get_attribute(self, key: str, default: Any = None) -> Any:
        return self._attrs.get(key, default)


# ═══════════════════════════════════════════════════════════════════════════
# 1. FAULTS TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminFaults:
    """Test the admin fault hierarchy."""

    def test_admin_fault_base(self):
        f = AdminFault(code="ADMIN_TEST", message="Something went wrong")
        assert "Something went wrong" in str(f)

    def test_authentication_fault_status(self):
        f = AdminAuthenticationFault()
        assert f.status == 401

    def test_authentication_fault_message(self):
        f = AdminAuthenticationFault("bad token")
        assert "bad token" in str(f)

    def test_authorization_fault_status(self):
        f = AdminAuthorizationFault(action="delete", resource="user")
        assert f.status == 403

    def test_authorization_fault_message(self):
        f = AdminAuthorizationFault(action="edit", resource="settings")
        msg = str(f)
        assert "edit" in msg or "settings" in msg or "permission" in msg.lower()

    def test_model_not_found_fault_status(self):
        f = AdminModelNotFoundFault("Widget")
        assert f.status == 404

    def test_model_not_found_fault_message(self):
        f = AdminModelNotFoundFault("Widget")
        assert "Widget" in str(f)

    def test_record_not_found_fault_status(self):
        f = AdminRecordNotFoundFault("User", "42")
        assert f.status == 404

    def test_record_not_found_fault_message(self):
        f = AdminRecordNotFoundFault("User", "42")
        msg = str(f)
        assert "User" in msg or "42" in msg

    def test_validation_fault_status(self):
        f = AdminValidationFault("Invalid email")
        assert f.status == 422

    def test_action_fault_status(self):
        f = AdminActionFault("delete_all", "Permission denied")
        assert f.status == 400

    def test_action_fault_message(self):
        f = AdminActionFault("nuke", "Not allowed")
        msg = str(f)
        assert "nuke" in msg or "Not allowed" in msg

    def test_faults_inherit_from_admin_fault(self):
        for cls in (
            AdminAuthenticationFault,
            AdminAuthorizationFault,
            AdminModelNotFoundFault,
            AdminRecordNotFoundFault,
            AdminValidationFault,
            AdminActionFault,
        ):
            assert issubclass(cls, AdminFault)

    def test_faults_inherit_from_exception(self):
        for cls in (AdminFault, AdminAuthenticationFault, AdminValidationFault):
            assert issubclass(cls, Exception)


# ═══════════════════════════════════════════════════════════════════════════
# 2. PERMISSIONS TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminPermissions:
    """Test RBAC role/permission system."""

    def test_admin_role_enum_values(self):
        assert AdminRole.SUPERADMIN.value == "superadmin"
        assert AdminRole.ADMIN.value == "admin"
        assert AdminRole.STAFF.value == "staff"
        assert AdminRole.VIEWER.value == "viewer"

    def test_admin_role_levels(self):
        assert AdminRole.SUPERADMIN.level > AdminRole.ADMIN.level
        assert AdminRole.ADMIN.level > AdminRole.STAFF.level
        assert AdminRole.STAFF.level > AdminRole.VIEWER.level

    def test_admin_permission_enum(self):
        assert AdminPermission.MODEL_VIEW.value == "admin.model.view"
        assert AdminPermission.MODEL_ADD.value == "admin.model.add"
        assert AdminPermission.MODEL_CHANGE.value == "admin.model.change"
        assert AdminPermission.MODEL_DELETE.value == "admin.model.delete"
        assert AdminPermission.AUDIT_VIEW.value == "admin.audit.view"

    def test_superadmin_has_all_permissions(self):
        perms = ROLE_PERMISSIONS[AdminRole.SUPERADMIN]
        for p in AdminPermission:
            assert p in perms, f"Superadmin missing {p}"

    def test_viewer_has_limited_permissions(self):
        perms = ROLE_PERMISSIONS[AdminRole.VIEWER]
        assert AdminPermission.MODEL_VIEW in perms
        assert AdminPermission.MODEL_DELETE not in perms
        assert AdminPermission.USER_MANAGE not in perms

    def test_staff_cannot_delete(self):
        perms = ROLE_PERMISSIONS[AdminRole.STAFF]
        assert AdminPermission.MODEL_DELETE not in perms

    def test_get_admin_role_from_admin_role_attr(self):
        identity = MockIdentity(attributes={"admin_role": "admin"})
        role = get_admin_role(identity)
        assert role == AdminRole.ADMIN

    def test_get_admin_role_from_roles_list(self):
        identity = MockIdentity(roles=["superadmin"])
        role = get_admin_role(identity)
        assert role == AdminRole.SUPERADMIN

    def test_get_admin_role_from_is_superuser(self):
        identity = MockIdentity(is_superuser=True)
        role = get_admin_role(identity)
        assert role == AdminRole.SUPERADMIN

    def test_get_admin_role_from_is_staff(self):
        identity = MockIdentity(is_staff=True)
        role = get_admin_role(identity)
        assert role == AdminRole.STAFF

    def test_get_admin_role_none_for_regular_user(self):
        identity = MockIdentity()
        role = get_admin_role(identity)
        assert role is None

    def test_has_admin_permission_superadmin(self):
        identity = MockIdentity(attributes={"admin_role": "superadmin"})
        assert has_admin_permission(identity, AdminPermission.USER_MANAGE) is True

    def test_has_admin_permission_viewer(self):
        identity = MockIdentity(attributes={"admin_role": "viewer"})
        assert has_admin_permission(identity, AdminPermission.MODEL_VIEW) is True
        assert has_admin_permission(identity, AdminPermission.MODEL_DELETE) is False

    def test_has_admin_permission_no_role(self):
        identity = MockIdentity()
        assert has_admin_permission(identity, AdminPermission.MODEL_VIEW) is False

    def test_has_model_permission_view(self):
        identity = MockIdentity(attributes={"admin_role": "viewer"})
        assert has_model_permission(identity, "user", "view") is True

    def test_has_model_permission_delete_denied(self):
        identity = MockIdentity(attributes={"admin_role": "viewer"})
        assert has_model_permission(identity, "user", "delete") is False

    def test_require_admin_access_passes(self):
        identity = MockIdentity(attributes={"admin_role": "admin"})
        # Should not raise
        require_admin_access(identity)

    def test_require_admin_access_fails(self):
        identity = MockIdentity()
        with pytest.raises(AdminAuthorizationFault):
            require_admin_access(identity)


# ═══════════════════════════════════════════════════════════════════════════
# 3. AUDIT TRAIL TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminAudit:
    """Test audit trail logging."""

    def test_admin_action_enum(self):
        assert AdminAction.LOGIN.value == "login"
        assert AdminAction.CREATE.value == "create"
        assert AdminAction.UPDATE.value == "update"
        assert AdminAction.DELETE.value == "delete"
        assert AdminAction.BULK_ACTION.value == "bulk_action"

    def test_audit_entry_creation(self):
        entry = AdminAuditEntry(
            id="ae-1",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            user_id="u1",
            username="admin",
            role="superadmin",
            action=AdminAction.CREATE,
            model_name="User",
            record_pk="42",
        )
        assert entry.user_id == "u1"
        assert entry.action == AdminAction.CREATE
        assert entry.model_name == "User"
        assert entry.success is True

    def test_audit_entry_to_dict(self):
        entry = AdminAuditEntry(
            id="ae-2",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            user_id="u1",
            username="admin",
            role="superadmin",
            action=AdminAction.LOGIN,
        )
        d = entry.to_dict()
        assert d["user_id"] == "u1"
        assert d["action"] == "login"
        assert "timestamp" in d

    def test_audit_entry_is_frozen(self):
        entry = AdminAuditEntry(
            id="ae-3",
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            user_id="u1",
            username="admin",
            role="superadmin",
            action=AdminAction.LOGIN,
        )
        with pytest.raises(Exception):
            entry.user_id = "u2"

    def test_audit_log_empty(self):
        log = AdminAuditLog()
        assert log.count() == 0
        assert log.get_entries() == []

    def test_audit_log_add_entry(self):
        log = AdminAuditLog()
        log.log(
            user_id="u1",
            username="admin",
            role="superadmin",
            action=AdminAction.LOGIN,
        )
        assert log.count() == 1

    def test_audit_log_multiple_entries(self):
        log = AdminAuditLog()
        for i in range(5):
            log.log(
                user_id=f"u{i}",
                username=f"user{i}",
                role="admin",
                action=AdminAction.VIEW,
            )
        assert log.count() == 5

    def test_audit_log_limit(self):
        log = AdminAuditLog()
        for i in range(10):
            log.log(
                user_id=f"u{i}",
                username=f"user{i}",
                role="admin",
                action=AdminAction.VIEW,
            )
        entries = log.get_entries(limit=3)
        assert len(entries) == 3

    def test_audit_log_filter_by_action(self):
        log = AdminAuditLog()
        log.log(user_id="u1", username="a", role="admin", action=AdminAction.LOGIN)
        log.log(user_id="u1", username="a", role="admin", action=AdminAction.CREATE)
        log.log(user_id="u1", username="a", role="admin", action=AdminAction.LOGIN)

        entries = log.get_entries(action=AdminAction.LOGIN)
        assert len(entries) == 2

    def test_audit_log_filter_by_user(self):
        log = AdminAuditLog()
        log.log(user_id="u1", username="alice", role="admin", action=AdminAction.VIEW)
        log.log(user_id="u2", username="bob", role="admin", action=AdminAction.VIEW)

        entries = log.get_entries(user_id="u1")
        assert len(entries) == 1
        assert entries[0].user_id == "u1"

    def test_audit_log_clear(self):
        log = AdminAuditLog()
        log.log(user_id="u1", username="a", role="admin", action=AdminAction.LOGIN)
        assert log.count() == 1
        log.clear()
        assert log.count() == 0

    def test_audit_log_retention(self):
        log = AdminAuditLog(max_entries=5)
        for i in range(10):
            log.log(
                user_id=f"u{i}",
                username=f"user{i}",
                role="admin",
                action=AdminAction.VIEW,
            )
        # Should have been trimmed to max_entries
        assert log.count() <= 5

    def test_audit_log_with_changes(self):
        log = AdminAuditLog()
        log.log(
            user_id="u1",
            username="admin",
            role="superadmin",
            action=AdminAction.UPDATE,
            model_name="User",
            record_pk="1",
            changes={"name": {"old": "Alice", "new": "Bob"}},
        )
        entry = log.get_entries()[0]
        assert entry.changes == {"name": {"old": "Alice", "new": "Bob"}}

    def test_audit_log_failed_action(self):
        log = AdminAuditLog()
        log.log(
            user_id="u1",
            username="admin",
            role="superadmin",
            action=AdminAction.LOGIN_FAILED,
            success=False,
            error_message="Invalid credentials",
        )
        entry = log.get_entries()[0]
        assert entry.success is False
        assert entry.error_message == "Invalid credentials"


# ═══════════════════════════════════════════════════════════════════════════
# 4. MODEL ADMIN OPTIONS TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestModelAdmin:
    """Test ModelAdmin auto-detection and configuration."""

    def test_default_model_admin(self):
        admin = ModelAdmin(model=UserModel)
        assert admin.model is UserModel

    def test_auto_detect_list_display(self):
        admin = ModelAdmin(model=UserModel)
        display = admin.get_list_display()
        # Should include non-auto fields
        assert "name" in display
        assert "email" in display

    def test_explicit_list_display(self):
        class CustomAdmin(ModelAdmin):
            list_display = ["id", "name"]

        admin = CustomAdmin(model=UserModel)
        assert admin.get_list_display() == ["id", "name"]

    def test_auto_detect_search_fields(self):
        class CustomAdmin(ModelAdmin):
            search_fields = ["name", "email"]

        admin = CustomAdmin(model=UserModel)
        search = admin.get_search_fields()
        assert "name" in search
        assert "email" in search

    def test_auto_detect_list_filter(self):
        class CustomAdmin(ModelAdmin):
            list_filter = ["active"]

        admin = CustomAdmin(model=UserModel)
        filters = admin.get_list_filter()
        assert "active" in filters

    def test_auto_detect_fields(self):
        class CustomAdmin(ModelAdmin):
            fields = ["name", "email", "active"]

        admin = CustomAdmin(model=UserModel)
        fields = admin.get_fields()
        assert "name" in fields
        assert "email" in fields

    def test_auto_detect_readonly_fields(self):
        admin = ModelAdmin(model=UserModel)
        readonly = admin.get_readonly_fields()
        # auto_now and auto_now_add fields detected via hasattr
        # MockField has auto_now and auto_now_add attrs but is not isinstance of real fields
        # The logic uses hasattr checks which work with our mocks
        assert "created_at" in readonly
        assert "updated_at" in readonly

    def test_get_fieldsets_auto(self):
        admin = ModelAdmin(model=UserModel)
        fieldsets = admin.get_fieldsets()
        assert len(fieldsets) > 0
        # First fieldset should be a tuple (name, dict with "fields")
        name, config = fieldsets[0]
        assert "fields" in config

    def test_explicit_fieldsets(self):
        class CustomAdmin(ModelAdmin):
            fieldsets = [
                ("Personal", {"fields": ["name", "email"]}),
                ("Status", {"fields": ["active"]}),
            ]

        admin = CustomAdmin(model=UserModel)
        fs = admin.get_fieldsets()
        assert len(fs) == 2
        assert fs[0][0] == "Personal"

    def test_get_model_name(self):
        admin = ModelAdmin(model=UserModel)
        name = admin.get_model_name()
        assert isinstance(name, str)
        assert len(name) > 0

    def test_get_model_name_plural(self):
        admin = ModelAdmin(model=UserModel)
        plural = admin.get_model_name_plural()
        assert plural.endswith("s") or plural.endswith("es")

    def test_get_app_label(self):
        admin = ModelAdmin(model=UserModel)
        label = admin.get_app_label()
        # Should detect from Meta or derive from module
        assert isinstance(label, str)

    def test_get_ordering_default(self):
        admin = ModelAdmin(model=UserModel)
        ordering = admin.get_ordering()
        assert isinstance(ordering, list)

    def test_explicit_ordering(self):
        class CustomAdmin(ModelAdmin):
            ordering = ["-created_at"]

        admin = CustomAdmin(model=UserModel)
        assert admin.get_ordering() == ["-created_at"]

    def test_format_value_none(self):
        admin = ModelAdmin(model=UserModel)
        assert admin.format_value("name", None) == "—"

    def test_format_value_bool_true(self):
        admin = ModelAdmin(model=UserModel)
        assert admin.format_value("active", True) == "✓"

    def test_format_value_bool_false(self):
        admin = ModelAdmin(model=UserModel)
        assert admin.format_value("active", False) == "✗"

    def test_format_value_string(self):
        admin = ModelAdmin(model=UserModel)
        assert admin.format_value("name", "Alice") == "Alice"

    def test_format_value_datetime(self):
        admin = ModelAdmin(model=UserModel)
        dt = datetime.datetime(2024, 1, 15, 10, 30)
        formatted = admin.format_value("created_at", dt)
        assert "2024" in formatted

    def test_get_field_metadata(self):
        admin = ModelAdmin(model=UserModel)
        meta = admin.get_field_metadata("name")
        assert meta["name"] == "name"
        assert "type" in meta or "input_type" in meta
        assert "label" in meta

    def test_field_metadata_email(self):
        admin = ModelAdmin(model=UserModel)
        meta = admin.get_field_metadata("email")
        # MockField won't pass isinstance(EmailField) - it returns 'text' or 'select'
        assert meta["name"] == "email"
        assert "type" in meta or "input_type" in meta

    def test_field_metadata_boolean(self):
        admin = ModelAdmin(model=UserModel)
        meta = admin.get_field_metadata("active")
        assert meta["name"] == "active"
        assert "type" in meta or "input_type" in meta

    def test_permissions_default(self):
        admin = ModelAdmin(model=UserModel)
        # Without identity, should default to True (or based on internal logic)
        # At minimum, these methods should not raise
        admin.has_view_permission(None)
        admin.has_add_permission(None)
        admin.has_change_permission(None)
        admin.has_delete_permission(None)

    def test_get_actions_default(self):
        admin = ModelAdmin(model=UserModel)
        actions = admin.get_actions()
        # Should have delete_selected by default
        assert "delete_selected" in actions

    def test_custom_action_decorator(self):
        class CustomAdmin(ModelAdmin):
            @action(short_description="Activate selected")
            async def activate(self, request, queryset):
                pass

        admin = CustomAdmin(model=UserModel)
        actions = admin.get_actions()
        assert "activate" in actions
        assert actions["activate"].short_description == "Activate selected"

    def test_list_per_page_default(self):
        admin = ModelAdmin(model=UserModel)
        assert admin.list_per_page == 25

    def test_custom_list_per_page(self):
        class CustomAdmin(ModelAdmin):
            list_per_page = 50

        admin = CustomAdmin(model=UserModel)
        assert admin.list_per_page == 50

    def test_icon_default(self):
        admin = ModelAdmin(model=UserModel)
        assert isinstance(admin.icon, str)

    def test_has_module_permission(self):
        admin = ModelAdmin(model=UserModel)
        # Should not raise
        result = admin.has_module_permission(None)
        assert isinstance(result, bool)


# ═══════════════════════════════════════════════════════════════════════════
# 5. ADMIN ACTION DESCRIPTOR TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminActionDescriptor:
    """Test action descriptors."""

    def test_from_function(self):
        def my_action(admin, request, qs):
            pass

        desc = AdminActionDescriptor(my_action)
        assert desc.name == "my_action"
        assert desc.func is my_action

    def test_short_description(self):
        def activate(admin, request, qs):
            pass
        activate.short_description = "Activate Users"

        desc = AdminActionDescriptor(activate)
        assert desc.short_description == "Activate Users"

    def test_custom_name(self):
        def do_stuff(admin, request, qs):
            pass

        desc = AdminActionDescriptor(do_stuff, name="custom_name")
        assert desc.name == "custom_name"

    def test_confirmation_message(self):
        def danger(admin, request, qs):
            pass

        desc = AdminActionDescriptor(danger, confirmation="Are you sure?")
        assert desc.confirmation == "Are you sure?"


# ═══════════════════════════════════════════════════════════════════════════
# 6. ADMIN SITE TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminSite:
    """Test the AdminSite central registry."""

    def setup_method(self):
        AdminSite.reset()

    def test_default_singleton(self):
        site1 = AdminSite.default()
        site2 = AdminSite.default()
        assert site1 is site2

    def test_reset_clears_singleton(self):
        site1 = AdminSite.default()
        AdminSite.reset()
        site2 = AdminSite.default()
        assert site1 is not site2

    def test_default_properties(self):
        site = AdminSite.default()
        assert site.name == "admin"
        assert site.title == "Aquilia Admin"
        assert site.url_prefix == "/admin"

    def test_custom_properties(self):
        site = AdminSite(
            name="custom",
            title="My Admin",
            header="My Admin Header",
            url_prefix="/my-admin",
        )
        assert site.name == "custom"
        assert site.title == "My Admin"
        assert site.url_prefix == "/my-admin"

    def test_register_model(self):
        site = AdminSite()
        site.register(UserModel)
        assert site.is_registered(UserModel)

    def test_register_model_with_admin_class(self):
        class UserAdmin(ModelAdmin):
            list_display = ["name", "email"]

        site = AdminSite()
        site.register(UserModel, UserAdmin)
        admin = site.get_model_admin(UserModel)
        assert isinstance(admin, UserAdmin)

    def test_unregister_model(self):
        site = AdminSite()
        site.register(UserModel)
        site.unregister(UserModel)
        assert not site.is_registered(UserModel)

    def test_get_model_admin_by_class(self):
        site = AdminSite()
        site.register(UserModel)
        admin = site.get_model_admin(UserModel)
        assert isinstance(admin, ModelAdmin)

    def test_get_model_admin_by_name(self):
        site = AdminSite()
        site.register(UserModel)
        admin = site.get_model_admin("usermodel")
        assert isinstance(admin, ModelAdmin)

    def test_get_model_admin_not_found(self):
        site = AdminSite()
        with pytest.raises(AdminModelNotFoundFault):
            site.get_model_admin("NonExistent")

    def test_get_model_class_by_name(self):
        site = AdminSite()
        site.register(UserModel)
        cls = site.get_model_class("UserModel")
        assert cls is UserModel

    def test_get_model_class_case_insensitive(self):
        site = AdminSite()
        site.register(UserModel)
        cls = site.get_model_class("usermodel")
        assert cls is UserModel

    def test_get_model_class_not_found(self):
        site = AdminSite()
        with pytest.raises(AdminModelNotFoundFault):
            site.get_model_class("NonExistent")

    def test_register_admin_direct(self):
        site = AdminSite()
        admin = ModelAdmin(model=UserModel)
        site.register_admin(UserModel, admin)
        assert site.is_registered(UserModel)
        assert site.get_model_admin(UserModel) is admin

    def test_get_registered_models(self):
        site = AdminSite()
        site.register(UserModel)
        site.register(PostModel)
        models = site.get_registered_models()
        assert "UserModel" in models
        assert "PostModel" in models

    def test_get_app_list_no_models(self):
        site = AdminSite()
        app_list = site.get_app_list()
        assert app_list == []

    def test_get_app_list_with_models(self):
        site = AdminSite()
        site.register(UserModel)
        site.register(PostModel)
        app_list = site.get_app_list()
        assert len(app_list) >= 1

    def test_not_initialized_initially(self):
        site = AdminSite()
        assert not site._initialized

    def test_audit_log_exists(self):
        site = AdminSite()
        assert isinstance(site.audit_log, AdminAuditLog)


class TestAdminSiteCRUD:
    """Test AdminSite CRUD operations."""

    def setup_method(self):
        AdminSite.reset()
        self.site = AdminSite()
        self.site.register(UserModel)

    @pytest.mark.asyncio
    async def test_get_dashboard_stats(self):
        stats = await self.site.get_dashboard_stats()
        assert "total_models" in stats
        assert stats["total_models"] == 1
        assert "model_counts" in stats
        assert "recent_actions" in stats

    @pytest.mark.asyncio
    async def test_list_records(self):
        data = await self.site.list_records("UserModel")
        assert "rows" in data
        assert "total" in data
        assert "page" in data
        assert "total_pages" in data
        assert data["model_name"] == "UserModel"

    @pytest.mark.asyncio
    async def test_list_records_pagination_info(self):
        data = await self.site.list_records("UserModel", page=1, per_page=10)
        assert data["page"] == 1
        assert data["per_page"] == 10
        assert isinstance(data["has_next"], bool)
        assert isinstance(data["has_prev"], bool)

    @pytest.mark.asyncio
    async def test_list_records_unknown_model(self):
        with pytest.raises(AdminModelNotFoundFault):
            await self.site.list_records("NonExistent")

    @pytest.mark.asyncio
    async def test_get_record(self):
        data = await self.site.get_record("UserModel", 1)
        assert "pk" in data
        assert "fields" in data
        assert "model_name" in data

    @pytest.mark.asyncio
    async def test_create_record(self):
        record = await self.site.create_record(
            "UserModel",
            {"name": "Bob", "email": "bob@example.com"},
        )
        assert record is not None

    @pytest.mark.asyncio
    async def test_create_record_with_audit(self):
        identity = MockIdentity(
            id="admin-1",
            roles=["admin", "superadmin"],
            attributes={"admin_role": "superadmin", "name": "Admin"},
        )
        await self.site.create_record(
            "UserModel",
            {"name": "Bob"},
            identity=identity,
        )
        assert self.site.audit_log.count() >= 1
        entry = self.site.audit_log.get_entries()[0]
        assert entry.action == AdminAction.CREATE

    @pytest.mark.asyncio
    async def test_delete_record(self):
        result = await self.site.delete_record("UserModel", 1)
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_record_with_audit(self):
        identity = MockIdentity(
            id="admin-1",
            roles=["admin", "superadmin"],
            attributes={"admin_role": "superadmin", "name": "Admin"},
        )
        await self.site.delete_record("UserModel", 1, identity=identity)
        entries = self.site.audit_log.get_entries(action=AdminAction.DELETE)
        assert len(entries) == 1


# ═══════════════════════════════════════════════════════════════════════════
# 7. REGISTRY (register decorator & autodiscover) TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminRegistry:
    """Test @register decorator and autodiscover()."""

    def setup_method(self):
        AdminSite.reset()
        _pending_registrations.clear()

    def test_register_decorator_basic(self):
        """Register a ModelAdmin via the @register decorator."""
        @register
        class TestAdmin(ModelAdmin):
            model = UserModel

        # Should be in pending registrations
        assert len(_pending_registrations) >= 1

    def test_register_with_model_arg(self):
        """Register with model as argument."""
        @register(UserModel)
        class TestAdmin(ModelAdmin):
            pass

        assert len(_pending_registrations) >= 1

    def test_flush_pending_registrations(self):
        @register
        class TestAdmin(ModelAdmin):
            model = UserModel

        site = AdminSite.default()
        count = flush_pending_registrations()
        assert count >= 1
        assert site.is_registered(UserModel)

    def test_autodiscover_with_model_registry(self):
        """autodiscover() should register models from ModelRegistry."""
        AdminSite.reset()

        # Create a model with proper _meta
        class DiscoverableModel(MockModel):
            __name__ = "DiscoverableModel"
            _fields = {"id": MockField("id", "AutoField", primary_key=True)}
            class _meta_cls:
                abstract = False
                app_label = "testapp"
            _meta = _meta_cls()

        with patch("aquilia.models.registry.ModelRegistry") as mock_reg:
            mock_reg.all_models.return_value = {"DiscoverableModel": DiscoverableModel}
            discovered = autodiscover()

        assert "DiscoverableModel" in discovered


# ═══════════════════════════════════════════════════════════════════════════
# 8. TEMPLATE RENDERING TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminTemplates:
    """Test HTML template rendering."""

    def test_render_login_page(self):
        html = render_login_page()
        assert "<!DOCTYPE html>" in html
        assert "login" in html.lower() or "Login" in html
        assert "<form" in html
        assert "username" in html
        assert "password" in html

    def test_render_login_page_with_error(self):
        html = render_login_page(error="Invalid credentials")
        assert "Invalid credentials" in html

    def test_render_dashboard(self):
        html = render_dashboard(
            app_list=[
                {
                    "app_label": "accounts",
                    "app_name": "Accounts",
                    "models": [
                        {
                            "name": "User",
                            "name_plural": "Users",
                            "model_name": "User",
                            "url_name": "user",
                            "icon": "👤",
                            "perms": {"view": True, "add": True, "change": True, "delete": True},
                        },
                    ],
                },
            ],
            stats={"total_models": 1, "model_counts": {"User": 42}, "recent_actions": []},
            identity_name="Admin",
        )
        assert "<!DOCTYPE html>" in html
        assert "Admin" in html
        assert "User" in html

    def test_render_list_view(self):
        html = render_list_view(
            data={
                "rows": [
                    {"pk": 1, "name": "Alice", "email": "alice@test.com"},
                ],
                "total": 1,
                "page": 1,
                "per_page": 25,
                "total_pages": 1,
                "has_next": False,
                "has_prev": False,
                "list_display": ["name", "email"],
                "list_filter": [],
                "search_fields": ["name"],
                "ordering": None,
                "search": "",
                "model_name": "User",
                "verbose_name": "User",
                "verbose_name_plural": "Users",
                "actions": {},
            },
            app_list=[],
            identity_name="Admin",
        )
        assert "<!DOCTYPE html>" in html
        assert "Alice" in html

    def test_render_form_view(self):
        html = render_form_view(
            data={
                "pk": 1,
                "fields": [
                    {"name": "name", "label": "Name", "input_type": "text", "value": "Alice", "required": True, "readonly": False, "help_text": ""},
                    {"name": "email", "label": "Email", "input_type": "email", "value": "alice@test.com", "required": True, "readonly": False, "help_text": ""},
                ],
                "fieldsets": [("General", {"fields": ["name", "email"]})],
                "model_name": "User",
                "verbose_name": "User",
                "can_change": True,
                "can_delete": True,
            },
            app_list=[],
            identity_name="Admin",
        )
        assert "<!DOCTYPE html>" in html
        assert "Alice" in html
        assert "<form" in html

    def test_render_form_view_create_mode(self):
        html = render_form_view(
            data={
                "pk": "",
                "fields": [
                    {"name": "name", "label": "Name", "input_type": "text", "value": "", "required": True, "readonly": False, "help_text": ""},
                ],
                "fieldsets": [("General", {"fields": ["name"]})],
                "model_name": "User",
                "verbose_name": "User",
                "can_delete": False,
            },
            app_list=[],
            identity_name="Admin",
            is_create=True,
        )
        assert "<!DOCTYPE html>" in html
        assert "Add" in html or "Create" in html or "add" in html

    def test_render_form_view_with_flash(self):
        html = render_form_view(
            data={
                "pk": 1,
                "fields": [],
                "fieldsets": [],
                "model_name": "User",
                "verbose_name": "User",
                "can_delete": False,
            },
            app_list=[],
            identity_name="Admin",
            flash="Something went wrong",
            flash_type="error",
        )
        assert "Something went wrong" in html

    def test_render_audit_page(self):
        html = render_audit_page(
            entries=[
                {
                    "timestamp": "2024-01-15T10:30:00",
                    "user_id": "u1",
                    "username": "admin",
                    "role": "superadmin",
                    "action": "create",
                    "model_name": "User",
                    "record_pk": "1",
                    "success": True,
                },
            ],
            app_list=[],
            identity_name="Admin",
            total=1,
        )
        assert "<!DOCTYPE html>" in html
        assert "Audit" in html or "audit" in html

    def test_theme_colors_in_css(self):
        """Verify Aquilia green theme colors are used."""
        html = render_login_page()
        assert "#22c55e" in html or "22c55e" in html  # Aquilia green accent
        assert "Inter" in html or "inter" in html  # Font

    def test_dark_mode_support(self):
        html = render_login_page()
        assert "dark" in html.lower() or "theme" in html.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 9. CONTROLLER TESTS
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminControllerHelpers:
    """Test controller helper functions."""

    def test_html_response(self):
        resp = _html_response("<h1>Hello</h1>")
        assert resp.status == 200
        assert resp.headers["content-type"] == "text/html; charset=utf-8"
        assert b"Hello" in resp._content

    def test_html_response_custom_status(self):
        resp = _html_response("Not found", status=404)
        assert resp.status == 404

    def test_redirect(self):
        resp = _redirect("/admin/")
        assert resp.status == 302
        assert resp.headers["location"] == "/admin/"

    def test_get_identity_name_none(self):
        assert _get_identity_name(None) == "Anonymous"

    def test_get_identity_name_with_name(self):
        identity = MockIdentity(attributes={"name": "Alice"})
        assert _get_identity_name(identity) == "Alice"

    def test_get_identity_name_with_username(self):
        identity = MockIdentity(attributes={"username": "bob"})
        assert _get_identity_name(identity) == "bob"


class TestAdminControllerInit:
    """Test AdminController initialization."""

    def setup_method(self):
        AdminSite.reset()

    def test_controller_prefix(self):
        assert AdminController.prefix == "/admin"

    def test_controller_default_site(self):
        ctrl = AdminController()
        assert isinstance(ctrl.site, AdminSite)

    def test_controller_custom_site(self):
        site = AdminSite(name="custom")
        ctrl = AdminController(site=site)
        assert ctrl.site.name == "custom"


class TestAdminControllerRoutes:
    """Test admin controller route handlers."""

    def setup_method(self):
        AdminSite.reset()
        self.site = AdminSite()
        self.site.register(UserModel)
        self.ctrl = AdminController(site=self.site)

    def _make_ctx(self, identity=None, session_data=None, query_params=None):
        """Create a mock RequestCtx."""
        ctx = MagicMock()
        ctx.identity = identity

        # Session mock
        session = MagicMock()
        session.data = session_data or {}
        ctx.session = session

        # Query params
        ctx.query_param = lambda key, default=None: (query_params or {}).get(key, default)

        # Form data
        ctx.form = AsyncMock(return_value={})

        return ctx

    def _make_request(self, path_params=None):
        """Create a mock request with path_params in state."""
        req = MagicMock()
        req.state = {"path_params": path_params or {}}
        return req

    @pytest.mark.asyncio
    async def test_dashboard_redirects_without_auth(self):
        ctx = self._make_ctx()
        req = self._make_request()
        resp = await self.ctrl.dashboard(req, ctx)
        assert resp.status == 302
        assert resp.headers["location"] == "/admin/login"

    @pytest.mark.asyncio
    async def test_login_page_renders(self):
        ctx = self._make_ctx()
        req = self._make_request()
        resp = await self.ctrl.login_page(req, ctx)
        assert resp.status == 200
        assert b"login" in resp._content.lower() or b"Login" in resp._content

    @pytest.mark.asyncio
    async def test_login_submit_empty_credentials(self):
        ctx = self._make_ctx()
        ctx.form = AsyncMock(return_value={"username": "", "password": ""})
        req = self._make_request()
        resp = await self.ctrl.login_submit(req, ctx)
        assert resp.status == 400

    @pytest.mark.asyncio
    async def test_login_submit_invalid_credentials(self):
        ctx = self._make_ctx()
        ctx.form = AsyncMock(return_value={"username": "wrong", "password": "wrong"})
        req = self._make_request()

        # Ensure env vars don't match
        with patch.dict(os.environ, {"AQUILIA_ADMIN_USER": "admin", "AQUILIA_ADMIN_PASSWORD": "admin"}):
            resp = await self.ctrl.login_submit(req, ctx)
        assert resp.status == 401

    @pytest.mark.asyncio
    async def test_login_submit_valid_credentials(self):
        ctx = self._make_ctx(session_data={})
        ctx.form = AsyncMock(return_value={"username": "admin", "password": "admin"})
        req = self._make_request()

        with patch.dict(os.environ, {"AQUILIA_ADMIN_USER": "admin", "AQUILIA_ADMIN_PASSWORD": "admin"}):
            resp = await self.ctrl.login_submit(req, ctx)
        assert resp.status == 302
        assert resp.headers["location"] == "/admin/"

    @pytest.mark.asyncio
    async def test_logout_redirects(self):
        ctx = self._make_ctx()
        req = self._make_request()
        resp = await self.ctrl.logout(req, ctx)
        assert resp.status == 302
        assert resp.headers["location"] == "/admin/login"

    @pytest.mark.asyncio
    async def test_list_view_redirects_without_auth(self):
        ctx = self._make_ctx()
        req = self._make_request({"model": "usermodel"})
        resp = await self.ctrl.list_view(req, ctx)
        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_add_form_redirects_without_auth(self):
        ctx = self._make_ctx()
        req = self._make_request({"model": "usermodel"})
        resp = await self.ctrl.add_form(req, ctx)
        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_edit_form_redirects_without_auth(self):
        ctx = self._make_ctx()
        req = self._make_request({"model": "usermodel", "pk": "1"})
        resp = await self.ctrl.edit_form(req, ctx)
        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_delete_redirects_without_auth(self):
        ctx = self._make_ctx()
        req = self._make_request({"model": "usermodel", "pk": "1"})
        resp = await self.ctrl.delete_record(req, ctx)
        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_audit_view_redirects_without_auth(self):
        ctx = self._make_ctx()
        req = self._make_request()
        resp = await self.ctrl.audit_view(req, ctx)
        assert resp.status == 302

    @pytest.mark.asyncio
    async def test_dashboard_renders_for_admin(self):
        identity = MockIdentity(
            id="admin-1",
            attributes={"admin_role": "superadmin", "name": "Admin"},
        )
        ctx = self._make_ctx(identity=identity)
        req = self._make_request()
        self.site._initialized = True

        resp = await self.ctrl.dashboard(req, ctx)
        assert resp.status == 200
        assert b"<!DOCTYPE html>" in resp._content

    @pytest.mark.asyncio
    async def test_list_view_renders_for_admin(self):
        identity = MockIdentity(
            id="admin-1",
            attributes={"admin_role": "superadmin", "name": "Admin"},
        )
        ctx = self._make_ctx(identity=identity, query_params={"q": "", "page": "1"})
        req = self._make_request({"model": "usermodel"})
        self.site._initialized = True

        resp = await self.ctrl.list_view(req, ctx)
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_add_form_renders_for_admin(self):
        identity = MockIdentity(
            id="admin-1",
            attributes={"admin_role": "superadmin", "name": "Admin"},
        )
        ctx = self._make_ctx(identity=identity)
        req = self._make_request({"model": "UserModel"})
        self.site._initialized = True

        resp = await self.ctrl.add_form(req, ctx)
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_edit_form_renders_for_admin(self):
        identity = MockIdentity(
            id="admin-1",
            attributes={"admin_role": "superadmin", "name": "Admin"},
        )
        ctx = self._make_ctx(identity=identity)
        req = self._make_request({"model": "UserModel", "pk": "1"})
        self.site._initialized = True

        resp = await self.ctrl.edit_form(req, ctx)
        assert resp.status == 200

    @pytest.mark.asyncio
    async def test_delete_record_for_admin(self):
        identity = MockIdentity(
            id="admin-1",
            attributes={"admin_role": "superadmin", "name": "Admin"},
        )
        ctx = self._make_ctx(identity=identity)
        req = self._make_request({"model": "UserModel", "pk": "1"})
        self.site._initialized = True

        resp = await self.ctrl.delete_record(req, ctx)
        assert resp.status == 302  # redirect after delete

    @pytest.mark.asyncio
    async def test_audit_view_denied_for_viewer(self):
        identity = MockIdentity(
            id="viewer-1",
            attributes={"admin_role": "viewer", "name": "Viewer"},
        )
        ctx = self._make_ctx(identity=identity)
        req = self._make_request()
        self.site._initialized = True

        resp = await self.ctrl.audit_view(req, ctx)
        # viewer doesn't have AUDIT_VIEW permission → redirect
        assert resp.status == 302


# ═══════════════════════════════════════════════════════════════════════════
# 10. INTEGRATION TESTS — Imports from aquilia package
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminExports:
    """Test that admin exports are available from aquilia package."""

    def test_import_admin_site(self):
        from aquilia import AdminSite
        assert AdminSite is not None

    def test_import_model_admin(self):
        from aquilia import ModelAdmin
        assert ModelAdmin is not None

    def test_import_register(self):
        from aquilia import register
        assert callable(register)

    def test_import_autodiscover(self):
        from aquilia import autodiscover
        assert callable(autodiscover)

    def test_import_admin_controller(self):
        from aquilia import AdminController
        assert AdminController is not None

    def test_import_admin_permission(self):
        from aquilia import AdminPermission
        assert AdminPermission is not None

    def test_import_admin_role(self):
        from aquilia import AdminRole
        assert AdminRole is not None

    def test_import_admin_audit_log(self):
        from aquilia import AdminAuditLog
        assert AdminAuditLog is not None

    def test_import_admin_action(self):
        from aquilia import AdminAction
        assert AdminAction is not None

    def test_import_admin_fault(self):
        from aquilia import AdminFault
        assert AdminFault is not None

    def test_import_admin_authentication_fault(self):
        from aquilia import AdminAuthenticationFault
        assert AdminAuthenticationFault is not None

    def test_import_admin_authorization_fault(self):
        from aquilia import AdminAuthorizationFault
        assert AdminAuthorizationFault is not None

    def test_import_admin_validation_fault(self):
        from aquilia import AdminValidationFault
        assert AdminValidationFault is not None

    def test_import_admin_model_not_found_fault(self):
        from aquilia import AdminModelNotFoundFault
        assert AdminModelNotFoundFault is not None

    def test_import_admin_record_not_found_fault(self):
        from aquilia import AdminRecordNotFoundFault
        assert AdminRecordNotFoundFault is not None

    def test_import_admin_action_fault(self):
        from aquilia import AdminActionFault
        assert AdminActionFault is not None


# ═══════════════════════════════════════════════════════════════════════════
# 11. EDGE CASES
# ═══════════════════════════════════════════════════════════════════════════


class TestAdminEdgeCases:
    """Test edge cases and error paths."""

    def setup_method(self):
        AdminSite.reset()

    def test_register_same_model_twice(self):
        site = AdminSite()
        site.register(UserModel)
        # Re-register should overwrite
        site.register(UserModel)
        assert site.is_registered(UserModel)

    def test_unregister_not_registered(self):
        site = AdminSite()
        # Should not raise
        site.unregister(UserModel)

    def test_model_admin_without_model(self):
        # ModelAdmin with no model should handle gracefully
        admin = ModelAdmin()
        # Methods should not crash even without model
        assert admin.model is None

    def test_empty_fields_model(self):
        """Model with no _fields dict."""
        class EmptyModel(MockModel):
            __name__ = "EmptyModel"
            _fields = {}

        admin = ModelAdmin(model=EmptyModel)
        # pk is always included
        display = admin.get_list_display()
        assert len(display) <= 1  # at most pk

    def test_audit_log_ordering(self):
        """Entries should be newest-first."""
        log = AdminAuditLog()
        log.log(user_id="u1", username="a", role="admin", action=AdminAction.LOGIN)
        log.log(user_id="u2", username="b", role="admin", action=AdminAction.LOGOUT)

        entries = log.get_entries()
        assert len(entries) == 2
        # Most recent should be first
        assert entries[0].user_id == "u2"

    def test_multiple_admin_sites(self):
        site1 = AdminSite(name="admin1")
        site2 = AdminSite(name="admin2")
        site1.register(UserModel)
        assert site1.is_registered(UserModel)
        assert not site2.is_registered(UserModel)

    def test_admin_role_ordering(self):
        """Verify role hierarchy ordering."""
        assert AdminRole.SUPERADMIN.level > AdminRole.VIEWER.level
        roles = sorted(AdminRole, key=lambda r: r.level, reverse=True)
        assert roles[0] == AdminRole.SUPERADMIN

    def test_format_value_list(self):
        admin = ModelAdmin(model=UserModel)
        result = admin.format_value("tags", ["a", "b"])
        assert isinstance(result, str)

    def test_format_value_long_string(self):
        admin = ModelAdmin(model=UserModel)
        long_str = "x" * 1000
        result = admin.format_value("content", long_str)
        # Should truncate or return as-is
        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_list_records_with_search(self):
        site = AdminSite()
        site.register(UserModel)
        data = await site.list_records("UserModel", search="alice")
        assert "rows" in data

    @pytest.mark.asyncio
    async def test_list_records_with_ordering(self):
        site = AdminSite()
        site.register(UserModel)
        data = await site.list_records("UserModel", ordering="-name")
        assert data["ordering"] == "-name"

    @pytest.mark.asyncio
    async def test_list_records_with_filters(self):
        site = AdminSite()
        site.register(UserModel)
        data = await site.list_records("UserModel", filters={"active": True})
        assert "rows" in data

    def test_admin_permission_string_values(self):
        """All permissions should have dot-notation values."""
        for perm in AdminPermission:
            assert "." in perm.value

    @pytest.mark.asyncio
    async def test_controller_authenticate_env_credentials(self):
        """Test the environment-based authentication fallback."""
        ctrl = AdminController()

        with patch.dict(os.environ, {"AQUILIA_ADMIN_USER": "root", "AQUILIA_ADMIN_PASSWORD": "secret"}):
            identity = await ctrl._authenticate_admin("root", "secret")
            assert identity is not None
            assert identity.id == "admin-1"

            # Wrong password
            bad = await ctrl._authenticate_admin("root", "wrong")
            assert bad is None
