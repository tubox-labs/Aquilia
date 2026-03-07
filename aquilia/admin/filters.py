"""
AquilAdmin -- Advanced Filter System.

Provides a rich filter API inspired by Django's ModelAdmin list filters.
Supports custom filter classes, date range filters, numeric range filters,
choice filters, boolean filters, and related model filters.

Usage:
    from aquilia.admin import ModelAdmin
    from aquilia.admin.filters import (
        DateRangeFilter, NumericRangeFilter, ChoiceFilter,
        BooleanFilter, RelatedModelFilter, AllValuesFilter,
    )

    class OrderAdmin(ModelAdmin):
        model = Order
        list_filter = [
            "status",                           # Simple field filter
            ("created_at", DateRangeFilter),     # Date range with presets
            ("total", NumericRangeFilter),       # Min/max numeric range
            ("customer", RelatedModelFilter),    # FK autocomplete filter
        ]
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, TYPE_CHECKING

if TYPE_CHECKING:
    from aquilia.models.base import Model

logger = logging.getLogger("aquilia.admin.filters")


class ListFilter:
    """
    Base class for admin list view filters.

    A filter provides:
    - A set of choices the user can select from
    - Logic to modify the queryset based on the selected value
    - Template rendering metadata for the filter UI

    Subclass this to create custom filters.
    """

    title: str = ""
    parameter_name: str = ""

    def __init__(self, field_name: str = "", model: Optional[Type[Model]] = None):
        self.field_name = field_name
        self.model = model
        if not self.parameter_name:
            self.parameter_name = field_name
        if not self.title:
            self.title = field_name.replace("_", " ").title()

    def get_choices(self) -> List[Dict[str, Any]]:
        """
        Return list of filter choices.

        Each choice is a dict with:
            - value: The filter value to apply
            - label: Human-readable label
            - selected: Whether this choice is currently active
        """
        return []

    def get_queryset(self, queryset: Any, value: Any) -> Any:
        """
        Apply this filter to the queryset.

        Args:
            queryset: The current queryset
            value: The selected filter value

        Returns:
            Modified queryset
        """
        return queryset

    def to_metadata(self) -> Dict[str, Any]:
        """Serialize filter for template rendering."""
        return {
            "name": self.parameter_name,
            "title": self.title,
            "type": self.__class__.__name__,
            "field_name": self.field_name,
            "choices": self.get_choices(),
        }


class SimpleFilter(ListFilter):
    """
    Filter by exact field value.

    Auto-detects choices from the field definition (if choices are set)
    or from distinct values in the database.
    """

    def get_choices(self) -> List[Dict[str, Any]]:
        choices = [{"value": "", "label": "All", "selected": False}]

        if self.model and self.field_name:
            field = getattr(self.model, "_fields", {}).get(self.field_name)
            if field and field.choices:
                for value, label in field.choices:
                    choices.append({
                        "value": str(value),
                        "label": str(label),
                        "selected": False,
                    })

        return choices


class BooleanFilter(ListFilter):
    """Filter for boolean fields with Yes/No/All choices."""

    def get_choices(self) -> List[Dict[str, Any]]:
        return [
            {"value": "", "label": "All", "selected": False},
            {"value": "true", "label": "Yes", "selected": False},
            {"value": "false", "label": "No", "selected": False},
        ]

    def to_metadata(self) -> Dict[str, Any]:
        data = super().to_metadata()
        data["type"] = "boolean"
        return data


class ChoiceFilter(ListFilter):
    """
    Filter with explicitly defined choices.

    Usage:
        class StatusFilter(ChoiceFilter):
            title = "Status"
            choices_list = [
                ("draft", "Draft"),
                ("published", "Published"),
                ("archived", "Archived"),
            ]
    """

    choices_list: List[Tuple[str, str]] = []

    def get_choices(self) -> List[Dict[str, Any]]:
        choices = [{"value": "", "label": "All", "selected": False}]
        for value, label in self.choices_list:
            choices.append({
                "value": str(value),
                "label": str(label),
                "selected": False,
            })
        return choices


class DateRangeFilter(ListFilter):
    """
    Date range filter with preset periods and custom range support.

    Provides quick filters like "Today", "Past 7 days", "This month",
    "This year", plus a custom date range picker.
    """

    def get_choices(self) -> List[Dict[str, Any]]:
        return [
            {"value": "", "label": "Any date", "selected": False},
            {"value": "today", "label": "Today", "selected": False},
            {"value": "yesterday", "label": "Yesterday", "selected": False},
            {"value": "past_7_days", "label": "Past 7 days", "selected": False},
            {"value": "past_30_days", "label": "Past 30 days", "selected": False},
            {"value": "this_month", "label": "This month", "selected": False},
            {"value": "this_year", "label": "This year", "selected": False},
            {"value": "custom", "label": "Custom range...", "selected": False},
        ]

    def get_date_range(self, value: str) -> Optional[Tuple[datetime, datetime]]:
        """Convert a preset value to a (start, end) datetime pair."""
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        ranges = {
            "today": (today_start, now),
            "yesterday": (today_start - timedelta(days=1), today_start),
            "past_7_days": (today_start - timedelta(days=7), now),
            "past_30_days": (today_start - timedelta(days=30), now),
            "this_month": (today_start.replace(day=1), now),
            "this_year": (today_start.replace(month=1, day=1), now),
        }
        return ranges.get(value)

    def to_metadata(self) -> Dict[str, Any]:
        data = super().to_metadata()
        data["type"] = "date_range"
        data["supports_custom_range"] = True
        return data


class NumericRangeFilter(ListFilter):
    """
    Numeric range filter with min/max inputs.

    Provides quick presets and custom min/max range inputs.
    """

    step: float = 1
    min_value: Optional[float] = None
    max_value: Optional[float] = None

    def get_choices(self) -> List[Dict[str, Any]]:
        return [
            {"value": "", "label": "Any value", "selected": False},
        ]

    def to_metadata(self) -> Dict[str, Any]:
        data = super().to_metadata()
        data["type"] = "numeric_range"
        data["step"] = self.step
        data["min_value"] = self.min_value
        data["max_value"] = self.max_value
        return data


class AllValuesFilter(ListFilter):
    """
    Filter showing all distinct values found in the database.

    Dynamically queries the database for unique values of the field
    and presents them as filter options.
    """

    def to_metadata(self) -> Dict[str, Any]:
        data = super().to_metadata()
        data["type"] = "all_values"
        data["dynamic"] = True
        return data


class RelatedModelFilter(ListFilter):
    """
    Filter for ForeignKey fields using related model's __str__.

    Provides a searchable dropdown of related model instances.
    """

    def to_metadata(self) -> Dict[str, Any]:
        data = super().to_metadata()
        data["type"] = "related_model"
        data["searchable"] = True
        return data


class EmptyFieldFilter(ListFilter):
    """
    Filter to find records where a field is empty/null or not.

    Useful for finding incomplete data or records missing values.
    """

    def get_choices(self) -> List[Dict[str, Any]]:
        return [
            {"value": "", "label": "All", "selected": False},
            {"value": "empty", "label": "Empty", "selected": False},
            {"value": "not_empty", "label": "Not empty", "selected": False},
        ]

    def to_metadata(self) -> Dict[str, Any]:
        data = super().to_metadata()
        data["type"] = "empty_field"
        return data


def resolve_filter(filter_spec: Any, model: Optional[Type[Model]] = None) -> ListFilter:
    """
    Resolve a filter specification into a ListFilter instance.

    Handles:
        - String field name → SimpleFilter
        - Tuple (field_name, FilterClass) → FilterClass instance
        - ListFilter instance → returned as-is

    Args:
        filter_spec: A string, tuple, or ListFilter instance
        model: The model class for context

    Returns:
        A ListFilter instance
    """
    if isinstance(filter_spec, ListFilter):
        return filter_spec

    if isinstance(filter_spec, str):
        # Auto-detect filter type from field
        if model:
            field = getattr(model, "_fields", {}).get(filter_spec)
            if field:
                try:
                    from aquilia.models.fields_module import (
                        BooleanField, DateTimeField, DateField,
                        IntegerField, FloatField, DecimalField,
                        ForeignKey, OneToOneField,
                    )
                    if isinstance(field, BooleanField):
                        return BooleanFilter(filter_spec, model)
                    if isinstance(field, (DateTimeField, DateField)):
                        return DateRangeFilter(filter_spec, model)
                    if isinstance(field, (IntegerField, FloatField, DecimalField)):
                        return NumericRangeFilter(filter_spec, model)
                    if isinstance(field, (ForeignKey, OneToOneField)):
                        return RelatedModelFilter(filter_spec, model)
                except ImportError:
                    pass
        return SimpleFilter(filter_spec, model)

    if isinstance(filter_spec, (list, tuple)) and len(filter_spec) == 2:
        field_name, filter_cls = filter_spec
        if isinstance(filter_cls, type) and issubclass(filter_cls, ListFilter):
            return filter_cls(field_name, model)

    return SimpleFilter(str(filter_spec), model)
