"""
AquilAdmin -- ModelAdmin Options.

Declarative per-model configuration for the admin interface.

Usage:
    class UserAdmin(ModelAdmin):
        model = User
        list_display = ["id", "name", "email", "active"]
        list_filter = ["active", "created_at"]
        search_fields = ["name", "email"]
        fieldsets = [
            ("Basic Info", {"fields": ["name", "email"]}),
            ("Status", {"fields": ["active", "created_at"]}),
        ]
        ordering = ["-created_at"]
        list_per_page = 25
        actions = ["delete_selected", "activate", "deactivate"]
        readonly_fields = ["created_at", "updated_at"]
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from aquilia.models.base import Model
    from aquilia.auth.core import Identity

logger = logging.getLogger("aquilia.admin.options")


# ── Action descriptor ────────────────────────────────────────────────────────

class AdminActionDescriptor:
    """
    Describes a bulk action available in the admin list view.

    Usage:
        def activate_users(model_admin, request, queryset):
            count = await queryset.update({"active": True})
            return f"Activated {count} users"

        activate_users.short_description = "Activate selected users"
        activate_users.confirmation = "Are you sure you want to activate these users?"
    """
    def __init__(
        self,
        func: Callable,
        name: str = "",
        short_description: str = "",
        confirmation: str = "",
        permission: str = "",
    ):
        self.func = func
        self.name = name or func.__name__
        self.short_description = short_description or getattr(func, "short_description", self.name.replace("_", " ").title())
        self.confirmation = confirmation or getattr(func, "confirmation", "")
        self.permission = permission or getattr(func, "permission", "")


def action(
    short_description: str = "",
    confirmation: str = "",
    permission: str = "",
):
    """
    Decorator to mark a method as an admin action.

    Usage:
        class UserAdmin(ModelAdmin):
            model = User

            @action(short_description="Activate selected users", confirmation="Confirm?")
            async def activate(self, request, queryset):
                return await queryset.update({"active": True})
    """
    def decorator(func: Callable) -> Callable:
        func._admin_action = True
        func.short_description = short_description or func.__name__.replace("_", " ").title()
        func.confirmation = confirmation
        func.permission = permission
        return func
    return decorator


# ── ModelAdmin ────────────────────────────────────────────────────────────────

class ModelAdmin:
    """
    Declarative admin configuration for a model.

    Class attributes configure how the model appears in the admin interface.
    All attributes have sensible defaults -- a model registered with the
    bare ModelAdmin class will auto-detect its fields and provide full CRUD.

    Attributes:
        model: The Model class to administer
        list_display: Fields to show in list view (auto-detected if empty)
        list_display_links: Fields that link to edit page (default: first field)
        list_filter: Fields to filter by in sidebar
        list_editable: Fields editable directly in list view
        search_fields: Fields to search (supports __ lookups)
        ordering: Default ordering ("-field" for descending)
        list_per_page: Rows per page (default 25)
        list_max_show_all: Max rows for "Show All" (default 200)
        fieldsets: Grouped fields for edit form
        readonly_fields: Fields that cannot be edited
        exclude: Fields to exclude from forms
        actions: Bulk actions (list of callables or method names)
        date_hierarchy: Field for date-based drill-down
        save_on_top: Show save buttons at top of form
        show_full_result_count: Show total count in list
        prepopulated_fields: Auto-populate fields from others
        raw_id_fields: FK fields shown as raw IDs instead of selects
        preserve_filters: Keep filter state across pages
    """

    # ── Model reference ──────────────────────────────────────────────
    model: Optional[Type[Model]] = None

    # ── List view configuration ──────────────────────────────────────
    list_display: List[str] = []
    list_display_links: Optional[List[str]] = None
    list_filter: List[str] = []
    list_editable: List[str] = []
    search_fields: List[str] = []
    ordering: List[str] = []
    list_per_page: int = 25
    list_max_show_all: int = 200
    date_hierarchy: Optional[str] = None
    show_full_result_count: bool = True
    preserve_filters: bool = True

    # ── Detail/Form view configuration ───────────────────────────────
    fieldsets: Optional[List[Tuple[str, Dict[str, Any]]]] = None
    fields: Optional[List[str]] = None
    readonly_fields: List[str] = []
    exclude: List[str] = []
    prepopulated_fields: Dict[str, List[str]] = {}
    raw_id_fields: List[str] = []
    save_on_top: bool = False

    # ── Actions ──────────────────────────────────────────────────────
    actions: List[Any] = []

    # ── Display ──────────────────────────────────────────────────────
    empty_value_display: str = "--"
    verbose_name: Optional[str] = None
    verbose_name_plural: Optional[str] = None
    icon: str = "list"  # Emoji icon for nav

    def __init__(self, model: Optional[Type[Model]] = None):
        if model is not None:
            self.model = model
        self._actions: Dict[str, AdminActionDescriptor] = {}
        self._setup_actions()

    def _setup_actions(self) -> None:
        """Discover and register actions from class methods and actions list."""
        # Built-in delete action
        self._actions["delete_selected"] = AdminActionDescriptor(
            func=self._action_delete_selected,
            name="delete_selected",
            short_description="Delete selected records",
            confirmation="Are you sure you want to delete the selected records? This action cannot be undone.",
        )

        # Built-in duplicate action
        self._actions["duplicate_selected"] = AdminActionDescriptor(
            func=self._action_duplicate_selected,
            name="duplicate_selected",
            short_description="Duplicate selected records",
            confirmation="",
        )

        # Built-in export actions
        self._actions["export_csv"] = AdminActionDescriptor(
            func=self._action_export_csv,
            name="export_csv",
            short_description="Export selected as CSV",
        )
        self._actions["export_json"] = AdminActionDescriptor(
            func=self._action_export_json,
            name="export_json",
            short_description="Export selected as JSON",
        )

        # Built-in activate/deactivate (for models with is_active/active field)
        self._actions["activate_selected"] = AdminActionDescriptor(
            func=self._action_activate_selected,
            name="activate_selected",
            short_description="Activate selected records",
        )
        self._actions["deactivate_selected"] = AdminActionDescriptor(
            func=self._action_deactivate_selected,
            name="deactivate_selected",
            short_description="Deactivate selected records",
        )

        # Built-in mark as featured/unfeatured
        self._actions["mark_featured"] = AdminActionDescriptor(
            func=self._action_mark_featured,
            name="mark_featured",
            short_description="Mark as featured",
        )
        self._actions["unmark_featured"] = AdminActionDescriptor(
            func=self._action_unmark_featured,
            name="unmark_featured",
            short_description="Unmark featured",
        )

        # Discover methods decorated with @action
        for attr_name in dir(self.__class__):
            if attr_name.startswith("_"):
                continue
            method = getattr(self.__class__, attr_name, None)
            if method and getattr(method, "_admin_action", False):
                self._actions[attr_name] = AdminActionDescriptor(func=method)

        # Register actions from actions list
        for act in self.actions:
            if isinstance(act, str):
                if act in self._actions:
                    continue
                method = getattr(self, act, None)
                if method:
                    self._actions[act] = AdminActionDescriptor(func=method)
            elif callable(act):
                name = getattr(act, "__name__", str(act))
                self._actions[name] = AdminActionDescriptor(func=act)

    # ── Auto-detection ───────────────────────────────────────────────

    def get_list_display(self) -> List[str]:
        """
        Get fields to display in list view.
        Auto-detects from model if not explicitly set.
        """
        if self.list_display:
            return list(self.list_display)

        if self.model is None:
            return ["__str__"]

        # Auto-detect: pk + first 5 non-pk fields
        fields = []
        pk_name = getattr(self.model, "_pk_attr", "id")
        fields.append(pk_name)

        for attr_name, field in self.model._fields.items():
            if attr_name == pk_name:
                continue
            if len(fields) >= 6:
                break
            fields.append(attr_name)

        return fields

    def get_list_filter(self) -> List[str]:
        """Get filter fields. Auto-detects boolean and choice fields."""
        if self.list_filter:
            return list(self.list_filter)

        if self.model is None:
            return []

        from aquilia.models.fields_module import BooleanField, DateTimeField, DateField

        filters = []
        for attr_name, field in self.model._fields.items():
            if isinstance(field, BooleanField):
                filters.append(attr_name)
            elif field.choices:
                filters.append(attr_name)
            elif isinstance(field, (DateTimeField, DateField)):
                filters.append(attr_name)
            if len(filters) >= 5:
                break
        return filters

    def get_search_fields(self) -> List[str]:
        """Get search fields. Auto-detects CharField and TextField."""
        if self.search_fields:
            return list(self.search_fields)

        if self.model is None:
            return []

        from aquilia.models.fields_module import CharField, TextField, EmailField

        search = []
        for attr_name, field in self.model._fields.items():
            if isinstance(field, (CharField, TextField, EmailField)):
                search.append(attr_name)
            if len(search) >= 4:
                break
        return search

    def get_fields(self) -> List[str]:
        """Get editable fields for the form view."""
        if self.fields:
            return [f for f in self.fields if f not in self.exclude]

        if self.model is None:
            return []

        from aquilia.models.fields_module import AutoField, BigAutoField

        editable = []
        for attr_name, field in self.model._fields.items():
            if attr_name in self.exclude:
                continue
            # Skip auto-increment PKs from editable list
            if isinstance(field, (AutoField, BigAutoField)):
                continue
            if field.editable:
                editable.append(attr_name)
        return editable

    def get_readonly_fields(self) -> List[str]:
        """Get read-only fields."""
        readonly = list(self.readonly_fields)

        if self.model:
            from aquilia.models.fields_module import AutoField, BigAutoField
            for attr_name, field in self.model._fields.items():
                if isinstance(field, (AutoField, BigAutoField)) and attr_name not in readonly:
                    readonly.append(attr_name)
                if hasattr(field, "auto_now") and field.auto_now and attr_name not in readonly:
                    readonly.append(attr_name)
                if hasattr(field, "auto_now_add") and field.auto_now_add and attr_name not in readonly:
                    readonly.append(attr_name)

        return readonly

    def get_fieldsets(self) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Get fieldsets for the form view.
        Auto-generates a single fieldset if not explicitly set.
        """
        if self.fieldsets:
            return list(self.fieldsets)

        fields = self.get_fields()
        if not fields:
            return []

        return [("General", {"fields": fields})]

    def get_ordering(self) -> List[str]:
        """Get default ordering."""
        if self.ordering:
            return list(self.ordering)

        if self.model and hasattr(self.model, "_meta"):
            meta_ordering = getattr(self.model._meta, "ordering", None)
            if meta_ordering:
                return list(meta_ordering)

        # Default: order by PK ascending (1, 2, 3, ...)
        pk = getattr(self.model, "_pk_attr", "id") if self.model else "id"
        return [pk]

    def get_model_name(self) -> str:
        """Get human-readable model name."""
        if self.verbose_name:
            return self.verbose_name
        if self.model:
            return self.model.__name__
        return "Unknown"

    def get_model_name_plural(self) -> str:
        """Get plural model name."""
        if self.verbose_name_plural:
            return self.verbose_name_plural
        name = self.get_model_name()
        if name.endswith("s"):
            return name + "es"
        elif name.endswith("y"):
            return name[:-1] + "ies"
        return name + "s"

    def get_app_label(self) -> str:
        """Get app label for grouping."""
        if self.model and hasattr(self.model, "_meta"):
            return getattr(self.model._meta, "app_label", "") or "default"
        return "default"

    def get_actions(self) -> Dict[str, AdminActionDescriptor]:
        """Get available actions."""
        return dict(self._actions)

    # ── Field metadata for templates ─────────────────────────────────

    def get_field_metadata(self, field_name: str) -> Dict[str, Any]:
        """Get metadata about a field for template rendering."""
        if not self.model or field_name not in self.model._fields:
            return {"name": field_name, "type": "text", "label": field_name.replace("_", " ").title()}

        field = self.model._fields[field_name]
        return {
            "name": field_name,
            "column": field.name,
            "type": self._get_field_input_type(field),
            "label": field.verbose_name or field_name.replace("_", " ").title(),
            "required": not field.null and not field.has_default(),
            "readonly": field_name in self.get_readonly_fields(),
            "help_text": field.help_text,
            "choices": field.choices,
            "max_length": getattr(field, "max_length", None),
        }

    def _get_field_input_type(self, field: Any) -> str:
        """Map model field to HTML input type."""
        from aquilia.models.fields_module import (
            BooleanField, IntegerField, BigIntegerField, SmallIntegerField,
            FloatField, DecimalField, DateField, TimeField, DateTimeField,
            EmailField, URLField, TextField, JSONField, UUIDField,
            PositiveIntegerField, PositiveSmallIntegerField,
        )

        if isinstance(field, BooleanField):
            return "checkbox"
        if isinstance(field, (IntegerField, BigIntegerField, SmallIntegerField,
                              PositiveIntegerField, PositiveSmallIntegerField)):
            return "number"
        if isinstance(field, (FloatField, DecimalField)):
            return "number"
        if isinstance(field, DateTimeField):
            return "datetime-local"
        if isinstance(field, DateField):
            return "date"
        if isinstance(field, TimeField):
            return "time"
        if isinstance(field, EmailField):
            return "email"
        if isinstance(field, URLField):
            return "url"
        if isinstance(field, TextField):
            return "textarea"
        if isinstance(field, JSONField):
            return "textarea"
        if isinstance(field, UUIDField):
            return "text"
        if field.choices:
            return "select"
        return "text"

    # ── Permissions ──────────────────────────────────────────────────

    def has_view_permission(self, identity: Optional[Identity] = None) -> bool:
        """Check if user can view records."""
        if identity is None:
            return False
        return identity.is_active()

    def has_add_permission(self, identity: Optional[Identity] = None) -> bool:
        """Check if user can add records."""
        if identity is None:
            return False
        return identity.has_role("admin") or identity.has_role("staff")

    def has_change_permission(self, identity: Optional[Identity] = None) -> bool:
        """Check if user can change records."""
        if identity is None:
            return False
        return identity.has_role("admin") or identity.has_role("staff")

    def has_delete_permission(self, identity: Optional[Identity] = None) -> bool:
        """Check if user can delete records."""
        if identity is None:
            return False
        return identity.has_role("admin")

    def has_module_permission(self, identity: Optional[Identity] = None) -> bool:
        """Check if user can access this model's admin section."""
        return self.has_view_permission(identity)

    # ── Value formatting ─────────────────────────────────────────────

    def format_value(self, field_name: str, value: Any) -> str:
        """Format a field value for display."""
        if value is None:
            return self.empty_value_display

        if isinstance(value, bool):
            return "yes" if value else "no"

        if isinstance(value, (list, dict)):
            import json
            return json.dumps(value, default=str, indent=2)

        return str(value)

    # ── Built-in actions ─────────────────────────────────────────────

    async def _action_delete_selected(self, request: Any, queryset: Any) -> str:
        """Built-in delete action."""
        count = await queryset.delete()
        return f"Deleted {count} record(s)"

    async def _action_duplicate_selected(self, request: Any, queryset: Any) -> str:
        """Duplicate selected records by creating copies with cleared PKs."""
        records = await queryset.all()
        if not records:
            return "No records to duplicate"
        count = 0
        pk_attr = getattr(self.model, "_pk_attr", "id") if self.model else "id"
        for record in records:
            data = {}
            if isinstance(record, dict):
                data = {k: v for k, v in record.items() if k != pk_attr and not k.startswith("_")}
            else:
                for field_name in (self.model._fields if self.model else {}):
                    if field_name == pk_attr:
                        continue
                    val = getattr(record, field_name, None)
                    if val is not None:
                        data[field_name] = val
            try:
                if self.model:
                    await self.model.create(**data)
                    count += 1
            except Exception:
                pass
        return f"Duplicated {count} record(s)"

    async def _action_export_csv(self, request: Any, queryset: Any) -> str:
        """Export selected records as CSV (server-side marker for redirect)."""
        records = await queryset.all()
        return f"Exported {len(records)} record(s) as CSV"

    async def _action_export_json(self, request: Any, queryset: Any) -> str:
        """Export selected records as JSON (server-side marker for redirect)."""
        records = await queryset.all()
        return f"Exported {len(records)} record(s) as JSON"

    async def _action_activate_selected(self, request: Any, queryset: Any) -> str:
        """Set is_active=True on selected records."""
        active_field = self._find_boolean_field("is_active", "active", "enabled")
        if not active_field:
            return "This model has no active/enabled field"
        count = await queryset.update({active_field: True})
        count = count if isinstance(count, int) else 0
        return f"Activated {count} record(s)"

    async def _action_deactivate_selected(self, request: Any, queryset: Any) -> str:
        """Set is_active=False on selected records."""
        active_field = self._find_boolean_field("is_active", "active", "enabled")
        if not active_field:
            return "This model has no active/enabled field"
        count = await queryset.update({active_field: False})
        count = count if isinstance(count, int) else 0
        return f"Deactivated {count} record(s)"

    async def _action_mark_featured(self, request: Any, queryset: Any) -> str:
        """Set is_featured=True on selected records."""
        feat_field = self._find_boolean_field("is_featured", "featured", "pinned", "starred")
        if not feat_field:
            return "This model has no featured/pinned field"
        count = await queryset.update({feat_field: True})
        count = count if isinstance(count, int) else 0
        return f"Marked {count} record(s) as featured"

    async def _action_unmark_featured(self, request: Any, queryset: Any) -> str:
        """Set is_featured=False on selected records."""
        feat_field = self._find_boolean_field("is_featured", "featured", "pinned", "starred")
        if not feat_field:
            return "This model has no featured/pinned field"
        count = await queryset.update({feat_field: False})
        count = count if isinstance(count, int) else 0
        return f"Unmarked {count} record(s) from featured"

    def _find_boolean_field(self, *candidates: str) -> Optional[str]:
        """Find the first matching boolean field name on the model."""
        if not self.model:
            return None
        from aquilia.models.fields_module import BooleanField
        for name in candidates:
            if name in self.model._fields:
                field = self.model._fields[name]
                if isinstance(field, BooleanField):
                    return name
        return None
