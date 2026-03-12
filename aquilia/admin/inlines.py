"""
AquilAdmin -- Inline Model Admin.

Provides the ability to edit related models on the same page as the
parent model inline within the AquilAdmin interface.

Supports both Tabular (compact table) and Stacked (full form) layouts
for editing related objects inline within the parent form.

Usage:
    from aquilia.admin import ModelAdmin, TabularInline, StackedInline
    from myapp.models import Author, Book

    class BookInline(TabularInline):
        model = Book
        fk_name = "author"
        extra = 1
        max_num = 10
        fields = ["title", "isbn", "published_date"]
        readonly_fields = ["isbn"]

    class AuthorAdmin(ModelAdmin):
        model = Author
        inlines = [BookInline]
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aquilia.auth.core import Identity
    from aquilia.models.base import Model

logger = logging.getLogger("aquilia.admin.inlines")


class InlineModelAdmin:
    """
    Base class for inline model editing within a parent form.

    An inline allows editing related model instances directly on the
    parent model's add/edit page, without navigating to a separate page.

    Attributes:
        model: The related Model class to edit inline
        fk_name: Name of the ForeignKey field on the inline model that
                 points to the parent model. Auto-detected if only one FK exists.
        fields: List of field names to display (auto-detected if empty)
        readonly_fields: Fields that cannot be edited inline
        exclude: Fields to hide from the inline form
        extra: Number of empty forms to display for adding new records
        max_num: Maximum number of inline forms to display
        min_num: Minimum number of inline forms to display
        can_delete: Whether inline records can be deleted
        verbose_name: Display name for the inline
        verbose_name_plural: Plural display name
        ordering: Default ordering for inline records
        show_change_link: Show a link to the full change form
        classes: Extra CSS classes for the inline fieldset
        template: Layout template type ("tabular" or "stacked")
    """

    model: type[Model] | None = None
    fk_name: str | None = None
    fields: list[str] | None = None
    readonly_fields: list[str] = []
    exclude: list[str] = []
    extra: int = 3
    max_num: int | None = None
    min_num: int | None = None
    can_delete: bool = True
    verbose_name: str | None = None
    verbose_name_plural: str | None = None
    ordering: list[str] | None = None
    show_change_link: bool = False
    classes: list[str] = []
    template: str = "tabular"  # "tabular" or "stacked"

    def __init__(self, parent_model: type[Model] | None = None):
        self._parent_model = parent_model
        self._fk_field = None

    def get_fk_name(self) -> str:
        """
        Get or auto-detect the FK field name linking to the parent model.

        If fk_name is explicitly set, use it. Otherwise, scan the inline
        model's fields for a ForeignKey pointing to the parent model.

        Raises ValueError if auto-detection finds zero or multiple FKs.
        """
        if self.fk_name:
            return self.fk_name

        if not self.model or not self._parent_model:
            return ""

        try:
            from aquilia.models.fields_module import ForeignKey, OneToOneField
        except ImportError:
            return ""

        fk_candidates = []
        for attr_name, field in getattr(self.model, "_fields", {}).items():
            if isinstance(field, (ForeignKey, OneToOneField)):
                target = field.to if isinstance(field.to, str) else (field.to.__name__ if field.to else None)
                if target == self._parent_model.__name__:
                    fk_candidates.append(attr_name)

        if len(fk_candidates) == 1:
            return fk_candidates[0]
        elif len(fk_candidates) == 0:
            from .faults import AdminInlineFault

            raise AdminInlineFault(
                reason="No ForeignKey found. Set fk_name explicitly.",
                inline_model=self.model.__name__,
                parent_model=self._parent_model.__name__,
            )
        else:
            from .faults import AdminInlineFault

            raise AdminInlineFault(
                reason=f"Multiple ForeignKeys found: {fk_candidates}. Set fk_name explicitly.",
                inline_model=self.model.__name__,
                parent_model=self._parent_model.__name__,
            )

    def get_fields(self) -> list[str]:
        """Get fields to display in the inline form."""
        if self.fields:
            return [f for f in self.fields if f not in self.exclude]

        if self.model is None:
            return []

        try:
            from aquilia.models.fields_module import AutoField, BigAutoField
        except ImportError:
            return list(getattr(self.model, "_fields", {}).keys())

        fk_name = self.get_fk_name()
        editable = []
        for attr_name, field in self.model._fields.items():
            if attr_name in self.exclude:
                continue
            if attr_name == fk_name:
                continue  # Hide the FK to parent
            if isinstance(field, (AutoField, BigAutoField)):
                continue
            if field.editable:
                editable.append(attr_name)
        return editable

    def get_readonly_fields(self) -> list[str]:
        """Get read-only fields for the inline."""
        readonly = list(self.readonly_fields)

        if self.model:
            try:
                from aquilia.models.fields_module import AutoField, BigAutoField

                for attr_name, field in self.model._fields.items():
                    if isinstance(field, (AutoField, BigAutoField)) and attr_name not in readonly:
                        readonly.append(attr_name)
            except ImportError:
                pass
        return readonly

    def get_verbose_name(self) -> str:
        """Get display name for this inline."""
        if self.verbose_name:
            return self.verbose_name
        if self.model:
            return self.model.__name__
        return "Inline"

    def get_verbose_name_plural(self) -> str:
        """Get plural display name."""
        if self.verbose_name_plural:
            return self.verbose_name_plural
        name = self.get_verbose_name()
        if name.endswith("s"):
            return name + "es"
        elif name.endswith("y"):
            return name[:-1] + "ies"
        return name + "s"

    def get_ordering(self) -> list[str]:
        """Get ordering for inline records."""
        if self.ordering:
            return list(self.ordering)
        pk = getattr(self.model, "_pk_attr", "id") if self.model else "id"
        return [pk]

    def has_add_permission(self, identity: Identity | None = None) -> bool:
        """Check if user can add inline records."""
        if identity is None:
            return False
        return identity.is_active()

    def has_change_permission(self, identity: Identity | None = None) -> bool:
        """Check if user can change inline records."""
        if identity is None:
            return False
        return identity.is_active()

    def has_delete_permission(self, identity: Identity | None = None) -> bool:
        """Check if user can delete inline records."""
        if identity is None:
            return False
        return self.can_delete and identity.is_active()

    def get_field_metadata(self, field_name: str) -> dict[str, Any]:
        """Get metadata about a field for template rendering."""
        if not self.model or field_name not in self.model._fields:
            return {
                "name": field_name,
                "type": "text",
                "label": field_name.replace("_", " ").title(),
            }

        field = self.model._fields[field_name]
        return {
            "name": field_name,
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
        try:
            from aquilia.models.fields_module import (
                BigIntegerField,
                BooleanField,
                DateField,
                DateTimeField,
                DecimalField,
                EmailField,
                FloatField,
                IntegerField,
                JSONField,
                SmallIntegerField,
                TextField,
                TimeField,
                URLField,
            )
        except ImportError:
            return "text"

        if isinstance(field, BooleanField):
            return "checkbox"
        if isinstance(field, (IntegerField, BigIntegerField, SmallIntegerField)):
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
        if field.choices:
            return "select"
        return "text"

    def to_template_data(self, records: list[Any] = None, parent_pk: Any = None) -> dict[str, Any]:
        """
        Serialize inline configuration and data for template rendering.

        Returns a dict suitable for passing to Jinja2 templates.
        """
        fields = self.get_fields()
        field_metadata = [self.get_field_metadata(f) for f in fields]

        existing_records = []
        if records:
            pk_attr = getattr(self.model, "_pk_attr", "id") if self.model else "id"
            for record in records:
                row = {"pk": None, "fields": {}}
                if isinstance(record, dict):
                    row["pk"] = record.get(pk_attr)
                    for f in fields:
                        row["fields"][f] = record.get(f, "")
                else:
                    row["pk"] = getattr(record, pk_attr, None)
                    for f in fields:
                        row["fields"][f] = getattr(record, f, "")
                existing_records.append(row)

        return {
            "model_name": self.model.__name__ if self.model else "Inline",
            "verbose_name": self.get_verbose_name(),
            "verbose_name_plural": self.get_verbose_name_plural(),
            "fk_name": self.get_fk_name() if self.model and self._parent_model else "",
            "fields": fields,
            "field_metadata": field_metadata,
            "readonly_fields": self.get_readonly_fields(),
            "template": self.template,
            "extra": self.extra,
            "max_num": self.max_num,
            "min_num": self.min_num,
            "can_delete": self.can_delete,
            "show_change_link": self.show_change_link,
            "classes": self.classes,
            "records": existing_records,
            "parent_pk": parent_pk,
        }


class TabularInline(InlineModelAdmin):
    """
    Inline rendered as a compact table with one row per record.

    Each field appears as a column, making it ideal for models with
    few fields or when you need to see many records at once.
    """

    template = "tabular"


class StackedInline(InlineModelAdmin):
    """
    Inline rendered as a full form stacked vertically.

    Each record gets its own fieldset-like section, ideal for models
    with many fields or when fields need more visual space.
    """

    template = "stacked"
