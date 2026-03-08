"""
AquilAdmin -- Lifecycle Hooks System.

Provides a hook mechanism for ModelAdmin to intercept and customize
the behavior of CRUD operations, form processing, and queryset building.

Provides a first-class hook system built into Aquilia Admin.

Usage:
    from aquilia.admin.hooks import AdminHooksMixin

    class ArticleAdmin(ModelAdmin, AdminHooksMixin):
        model = Article

        def save_model(self, request, obj, form_data, change):
            # Custom save logic, e.g. set author on creation
            if not change:
                obj.author = request.identity.username
            super().save_model(request, obj, form_data, change)

        def delete_model(self, request, obj):
            # Soft delete instead of hard delete
            obj.is_deleted = True
            obj.save()

        def get_queryset(self, request):
            # Only show non-deleted records
            qs = super().get_queryset(request)
            return qs.filter(is_deleted=False)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from aquilia.models.base import Model

logger = logging.getLogger("aquilia.admin.hooks")


class AdminHooksMixin:
    """
    Mixin providing lifecycle hook methods for ModelAdmin.

    These hooks are called at specific points in the admin CRUD lifecycle
    to allow customization of behavior without overriding the entire view.

    Hook call order for saving:
        1. get_form_fields(request, obj) → field definitions
        2. clean_form(request, form_data, obj, change) → validated data
        3. before_save(request, obj, form_data, change)
        4. save_model(request, obj, form_data, change)
        5. save_related(request, obj, form_data, change)
        6. after_save(request, obj, form_data, change)
        7. log_change(request, obj, message)

    Hook call order for deleting:
        1. before_delete(request, obj)
        2. delete_model(request, obj)
        3. after_delete(request, obj)
        4. log_deletion(request, obj)
    """

    # -- Queryset Hooks --

    def get_queryset(self, request: Any = None) -> Any:
        """
        Return the base queryset for list views.

        Override to filter records globally (e.g. multi-tenancy,
        soft deletes, ownership-based access).

        Default: returns all records via model.objects.all()
        """
        model = getattr(self, "model", None)
        if model and hasattr(model, "objects"):
            return model.objects.all()
        return None

    def get_object(self, request: Any = None, pk: Any = None) -> Any:
        """
        Retrieve a single object by primary key.

        Override to add custom access control or eager loading.
        """
        qs = self.get_queryset(request)
        if qs is not None and pk is not None:
            return qs.filter(pk=pk).first()
        return None

    # -- Form / Field Hooks --

    def get_form_fields(self, request: Any = None, obj: Any = None) -> List[Dict[str, Any]]:
        """
        Return the field definitions for the add/edit form.

        Override to dynamically modify fields based on the request
        or the object being edited.
        """
        fields = getattr(self, "fields", None)
        if fields:
            return fields
        return []

    def clean_form(
        self,
        request: Any,
        form_data: Dict[str, Any],
        obj: Any = None,
        change: bool = False,
    ) -> Dict[str, Any]:
        """
        Validate and clean form data before saving.

        Override to add custom validation rules.

        Args:
            request: The HTTP request
            form_data: Raw form data dict
            obj: The model instance (None for creates)
            change: True if editing, False if creating

        Returns:
            Cleaned form data dict

        Raises:
            ValueError: If validation fails
        """
        return form_data

    def get_readonly_fields_for_request(
        self, request: Any = None, obj: Any = None
    ) -> List[str]:
        """
        Return readonly fields, possibly varying by request/object.

        Override to make fields readonly conditionally.
        """
        return list(getattr(self, "readonly_fields", []))

    def get_fieldsets_for_request(
        self, request: Any = None, obj: Any = None
    ) -> Optional[List]:
        """
        Return fieldsets, possibly varying by request/object.

        Override to show different fieldsets for different users
        or for create vs edit.
        """
        return getattr(self, "fieldsets", None)

    # -- Save Hooks --

    def before_save(
        self,
        request: Any,
        obj: Any,
        form_data: Dict[str, Any],
        change: bool = False,
    ) -> None:
        """
        Called before save_model().

        Use for pre-processing, setting computed fields, etc.
        """
        pass

    def save_model(
        self,
        request: Any,
        obj: Any,
        form_data: Dict[str, Any],
        change: bool = False,
    ) -> None:
        """
        Persist the model instance to the database.

        Override to customize save behavior (soft saves, versioning, etc).

        Default: calls obj.save()
        """
        if hasattr(obj, "save"):
            obj.save()

    def save_related(
        self,
        request: Any,
        obj: Any,
        form_data: Dict[str, Any],
        change: bool = False,
    ) -> None:
        """
        Save related/inline objects after the main object is saved.

        Called after save_model(). Override to handle inline saves,
        many-to-many relationships, etc.
        """
        pass

    def after_save(
        self,
        request: Any,
        obj: Any,
        form_data: Dict[str, Any],
        change: bool = False,
    ) -> None:
        """
        Called after save_model() and save_related().

        Use for post-save actions: cache invalidation, notifications,
        webhook triggers, etc.
        """
        pass

    # -- Delete Hooks --

    def before_delete(self, request: Any, obj: Any) -> None:
        """
        Called before delete_model().

        Use for pre-deletion checks or cascade logic.
        Raise an exception to prevent deletion.
        """
        pass

    def delete_model(self, request: Any, obj: Any) -> None:
        """
        Delete the model instance.

        Override for soft deletes, archival, or cascade behavior.

        Default: calls obj.delete()
        """
        if hasattr(obj, "delete"):
            obj.delete()

    def after_delete(self, request: Any, obj: Any) -> None:
        """
        Called after delete_model().

        Use for post-delete cleanup, cache invalidation, etc.
        """
        pass

    # -- Bulk Action Hooks --

    def before_bulk_action(
        self, request: Any, action_name: str, queryset: Any
    ) -> Any:
        """
        Called before executing a bulk action.

        Override to modify the queryset or perform checks.
        Return the (possibly modified) queryset.
        """
        return queryset

    def after_bulk_action(
        self, request: Any, action_name: str, queryset: Any, result: Any = None
    ) -> None:
        """
        Called after a bulk action completes.

        Use for logging, notifications, etc.
        """
        pass

    # -- Logging Hooks --

    def log_addition(self, request: Any, obj: Any, message: str = "") -> None:
        """Log the creation of a new object."""

    def log_change(self, request: Any, obj: Any, message: str = "") -> None:
        """Log a change to an existing object."""

    def log_deletion(self, request: Any, obj: Any) -> None:
        """Log the deletion of an object."""

    # -- View Customization Hooks --

    def get_list_display_for_request(self, request: Any = None) -> Optional[List[str]]:
        """
        Return list_display columns, possibly varying by request.

        Override to show different columns based on user role.
        """
        return getattr(self, "list_display", None)

    def get_search_fields_for_request(self, request: Any = None) -> Optional[List[str]]:
        """
        Return search fields, possibly varying by request.
        """
        return getattr(self, "search_fields", None)

    def get_actions_for_request(self, request: Any = None) -> Optional[List]:
        """
        Return available actions, possibly varying by request.

        Override to conditionally enable/disable actions based on
        user permissions.
        """
        return getattr(self, "actions", None)

    def get_ordering_for_request(self, request: Any = None) -> Optional[List[str]]:
        """
        Return ordering, possibly varying by request.
        """
        return getattr(self, "ordering", None)

    # -- Response Hooks --

    def response_add(self, request: Any, obj: Any) -> Optional[Any]:
        """
        Determine the response after a successful add.

        Override to redirect to a custom URL after creation.
        Return None for default behavior.
        """
        return None

    def response_change(self, request: Any, obj: Any) -> Optional[Any]:
        """
        Determine the response after a successful edit.

        Override to redirect to a custom URL after editing.
        Return None for default behavior.
        """
        return None

    def response_delete(self, request: Any, obj: Any) -> Optional[Any]:
        """
        Determine the response after a successful delete.

        Override to redirect to a custom URL after deletion.
        Return None for default behavior.
        """
        return None

    # -- Inline Hooks --

    def get_inlines(self, request: Any = None, obj: Any = None) -> List:
        """
        Return inline classes, possibly varying by request/object.

        Override to conditionally show/hide inlines.
        """
        return list(getattr(self, "inlines", []))

    def get_inline_instances(self, request: Any = None, obj: Any = None) -> List:
        """
        Instantiate inline classes.

        Returns InlineModelAdmin instances configured for the parent model.
        """
        inlines = self.get_inlines(request, obj)
        instances = []
        model = getattr(self, "model", None)
        for inline_cls in inlines:
            if isinstance(inline_cls, type):
                try:
                    instance = inline_cls()
                    if model and hasattr(instance, "resolve_fk_name"):
                        instance.resolve_fk_name(model)
                    instances.append(instance)
                except Exception as exc:
                    logger.error("Failed to instantiate inline %s: %s", inline_cls, exc)
            else:
                instances.append(inline_cls)
        return instances


class SoftDeleteMixin:
    """
    Mixin for soft-delete support in ModelAdmin.

    Requires the model to have an `is_deleted` boolean field
    and optionally a `deleted_at` datetime field.

    Usage:
        class ArticleAdmin(ModelAdmin, SoftDeleteMixin):
            model = Article
            soft_delete_field = "is_deleted"
            soft_delete_timestamp_field = "deleted_at"  # optional
    """

    soft_delete_field: str = "is_deleted"
    soft_delete_timestamp_field: Optional[str] = "deleted_at"
    show_deleted: bool = False  # Whether to show deleted records in list view

    def get_queryset(self, request: Any = None) -> Any:
        """Filter out soft-deleted records by default."""
        qs = super().get_queryset(request)  # type: ignore
        if qs is not None and not self.show_deleted:
            try:
                qs = qs.filter(**{self.soft_delete_field: False})
            except Exception:
                pass
        return qs

    def delete_model(self, request: Any, obj: Any) -> None:
        """Soft delete: set the flag instead of actually deleting."""
        setattr(obj, self.soft_delete_field, True)
        if self.soft_delete_timestamp_field:
            setattr(obj, self.soft_delete_timestamp_field, datetime.now(timezone.utc))
        if hasattr(obj, "save"):
            obj.save()

    def restore_model(self, request: Any, obj: Any) -> None:
        """Restore a soft-deleted record."""
        setattr(obj, self.soft_delete_field, False)
        if self.soft_delete_timestamp_field:
            setattr(obj, self.soft_delete_timestamp_field, None)
        if hasattr(obj, "save"):
            obj.save()


class VersioningMixin:
    """
    Mixin for automatic version tracking on save.

    Stores a version history of changes for each record.

    Requires the model to have a `version` integer field.
    """

    version_field: str = "version"

    def before_save(
        self,
        request: Any,
        obj: Any,
        form_data: Dict[str, Any],
        change: bool = False,
    ) -> None:
        """Increment version number on save."""
        if change and hasattr(obj, self.version_field):
            current = getattr(obj, self.version_field, 0) or 0
            setattr(obj, self.version_field, current + 1)
        super().before_save(request, obj, form_data, change)  # type: ignore


class TimestampMixin:
    """
    Mixin for automatic timestamp management.

    Sets created_at on create and updated_at on every save.
    """

    created_at_field: str = "created_at"
    updated_at_field: str = "updated_at"

    def before_save(
        self,
        request: Any,
        obj: Any,
        form_data: Dict[str, Any],
        change: bool = False,
    ) -> None:
        """Set timestamps automatically."""
        now = datetime.now(timezone.utc)
        if not change and hasattr(obj, self.created_at_field):
            if not getattr(obj, self.created_at_field, None):
                setattr(obj, self.created_at_field, now)
        if hasattr(obj, self.updated_at_field):
            setattr(obj, self.updated_at_field, now)
        super().before_save(request, obj, form_data, change)  # type: ignore
