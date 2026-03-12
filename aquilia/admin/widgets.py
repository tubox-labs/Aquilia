"""
AquilAdmin -- Dashboard Widget System.

Provides a composable widget/metric system for the AquilAdmin dashboard.

Widgets are registered on the AdminSite or ModelAdmin to display
stats, charts, recent activity, and custom content on the dashboard.

Usage:
    from aquilia.admin.widgets import (
        CountWidget, StatWidget, ChartWidget,
        RecentActivityWidget, TableWidget,
    )

    class SiteAdmin(AdminSite):
        widgets = [
            CountWidget(
                title="Total Users",
                model="User",
                icon="users",
                color="blue",
            ),
            StatWidget(
                title="Revenue",
                value_fn=lambda: "$12,345",
                change="+12.5%",
                trend="up",
                icon="dollar-sign",
            ),
            ChartWidget(
                title="Registrations",
                chart_type="line",
                data_fn=get_chart_data,
            ),
            RecentActivityWidget(
                title="Recent Activity",
                limit=10,
            ),
        ]
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger("aquilia.admin.widgets")


class WidgetSize(Enum):
    """Widget size on the dashboard grid."""

    SMALL = "sm"  # 1/4 width
    MEDIUM = "md"  # 1/2 width
    LARGE = "lg"  # 3/4 width
    FULL = "full"  # Full width


class WidgetPosition(Enum):
    """Widget placement section."""

    TOP = "top"
    MAIN = "main"
    SIDEBAR = "sidebar"
    BOTTOM = "bottom"


@dataclass
class AdminWidget:
    """
    Base class for dashboard widgets.

    Attributes:
        title: Widget title
        icon: Feather icon name
        size: Widget width on grid
        position: Where on dashboard to place this widget
        order: Sort order within position
        permission: Permission required to see this widget
        refresh_interval: Auto-refresh interval in seconds (0 = no refresh)
        css_classes: Additional CSS classes
        visible: Whether widget is visible
    """

    title: str = ""
    icon: str = ""
    size: WidgetSize = WidgetSize.SMALL
    position: WidgetPosition = WidgetPosition.TOP
    order: int = 0
    permission: str | None = None
    refresh_interval: int = 0
    css_classes: str = ""
    visible: bool = True

    def get_data(self) -> dict[str, Any]:
        """
        Return data for rendering this widget.
        Override in subclasses for dynamic data.
        """
        return {}

    def to_template_data(self) -> dict[str, Any]:
        """Serialize widget for template rendering."""
        return {
            "type": self.__class__.__name__,
            "title": self.title,
            "icon": self.icon,
            "size": self.size.value,
            "position": self.position.value,
            "order": self.order,
            "permission": self.permission,
            "refresh_interval": self.refresh_interval,
            "css_classes": self.css_classes,
            "visible": self.visible,
            "data": self.get_data(),
        }


@dataclass
class CountWidget(AdminWidget):
    """
    Displays a count of records in a model.

    Shows the total number of records with an optional filter,
    plus a trend indicator (change from previous period).

    Example:
        CountWidget(
            title="Active Users",
            model_name="User",
            filter_field="is_active",
            filter_value=True,
            icon="users",
            color="green",
        )
    """

    model_name: str = ""
    filter_field: str | None = None
    filter_value: Any = None
    color: str = "blue"
    count: int = 0
    change_percent: float | None = None
    trend: str = ""  # "up", "down", "flat"
    link: str = ""  # URL to navigate to on click
    footer_text: str = ""

    def get_data(self) -> dict[str, Any]:
        return {
            "model_name": self.model_name,
            "filter_field": self.filter_field,
            "filter_value": self.filter_value,
            "color": self.color,
            "count": self.count,
            "change_percent": self.change_percent,
            "trend": self.trend,
            "link": self.link,
            "footer_text": self.footer_text,
        }


@dataclass
class StatWidget(AdminWidget):
    """
    Displays a single statistic value with trend.

    Example:
        StatWidget(
            title="Revenue",
            value="$12,345",
            change="+12.5%",
            trend="up",
            icon="dollar-sign",
            color="green",
        )
    """

    value: str = ""
    value_fn: Callable | None = None
    change: str = ""
    trend: str = ""  # "up", "down", "flat"
    color: str = "blue"
    suffix: str = ""
    prefix: str = ""
    link: str = ""
    footer_text: str = ""

    def get_data(self) -> dict[str, Any]:
        val = self.value
        if self.value_fn:
            try:
                val = str(self.value_fn())
            except Exception as exc:
                logger.error("StatWidget %s value_fn error: %s", self.title, exc)
                val = "Error"
        return {
            "value": val,
            "change": self.change,
            "trend": self.trend,
            "color": self.color,
            "suffix": self.suffix,
            "prefix": self.prefix,
            "link": self.link,
            "footer_text": self.footer_text,
        }


@dataclass
class ChartWidget(AdminWidget):
    """
    Displays a chart (line, bar, pie, doughnut, area).

    Example:
        ChartWidget(
            title="Registrations",
            chart_type="line",
            labels=["Mon", "Tue", "Wed", "Thu", "Fri"],
            datasets=[
                {"label": "Users", "data": [10, 20, 15, 30, 25]},
            ],
        )
    """

    chart_type: str = "line"  # line, bar, pie, doughnut, area
    labels: list[str] = field(default_factory=list)
    datasets: list[dict[str, Any]] = field(default_factory=list)
    data_fn: Callable | None = None
    color_scheme: str = "default"
    show_legend: bool = True
    height: int = 300

    def __init__(self, **kwargs):
        # Handle fields with mutable defaults properly
        self.labels = kwargs.pop("labels", [])
        self.datasets = kwargs.pop("datasets", [])
        self.data_fn = kwargs.pop("data_fn", None)
        self.chart_type = kwargs.pop("chart_type", "line")
        self.color_scheme = kwargs.pop("color_scheme", "default")
        self.show_legend = kwargs.pop("show_legend", True)
        self.height = kwargs.pop("height", 300)
        super().__init__(**kwargs)

    def get_data(self) -> dict[str, Any]:
        labels = self.labels
        datasets = self.datasets
        if self.data_fn:
            try:
                result = self.data_fn()
                if isinstance(result, dict):
                    labels = result.get("labels", labels)
                    datasets = result.get("datasets", datasets)
            except Exception as exc:
                logger.error("ChartWidget %s data_fn error: %s", self.title, exc)

        return {
            "chart_type": self.chart_type,
            "labels": labels,
            "datasets": datasets,
            "color_scheme": self.color_scheme,
            "show_legend": self.show_legend,
            "height": self.height,
        }


@dataclass
class RecentActivityWidget(AdminWidget):
    """
    Displays recent admin activity log entries.

    Automatically pulls from the audit log.
    """

    limit: int = 10
    actions: list[str] | None = None
    show_user: bool = True
    show_timestamp: bool = True
    show_model: bool = True

    def __init__(self, **kwargs):
        self.limit = kwargs.pop("limit", 10)
        self.actions = kwargs.pop("actions", None)
        self.show_user = kwargs.pop("show_user", True)
        self.show_timestamp = kwargs.pop("show_timestamp", True)
        self.show_model = kwargs.pop("show_model", True)
        super().__init__(**kwargs)
        if not self.icon:
            self.icon = "activity"
        if self.size == WidgetSize.SMALL:
            self.size = WidgetSize.MEDIUM

    def get_data(self) -> dict[str, Any]:
        return {
            "limit": self.limit,
            "actions": self.actions,
            "show_user": self.show_user,
            "show_timestamp": self.show_timestamp,
            "show_model": self.show_model,
        }


@dataclass
class TableWidget(AdminWidget):
    """
    Displays a data table on the dashboard.

    Can show top records, summary data, or any tabular data.

    Example:
        TableWidget(
            title="Top Products",
            columns=["Name", "Sales", "Revenue"],
            rows=[
                ["Widget A", 150, "$1,500"],
                ["Widget B", 120, "$1,200"],
            ],
        )
    """

    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    data_fn: Callable | None = None
    model_name: str = ""
    show_link: bool = True
    max_rows: int = 10

    def __init__(self, **kwargs):
        self.columns = kwargs.pop("columns", [])
        self.rows = kwargs.pop("rows", [])
        self.data_fn = kwargs.pop("data_fn", None)
        self.model_name = kwargs.pop("model_name", "")
        self.show_link = kwargs.pop("show_link", True)
        self.max_rows = kwargs.pop("max_rows", 10)
        super().__init__(**kwargs)
        if self.size == WidgetSize.SMALL:
            self.size = WidgetSize.MEDIUM

    def get_data(self) -> dict[str, Any]:
        columns = self.columns
        rows = self.rows
        if self.data_fn:
            try:
                result = self.data_fn()
                if isinstance(result, dict):
                    columns = result.get("columns", columns)
                    rows = result.get("rows", rows)
            except Exception as exc:
                logger.error("TableWidget %s data_fn error: %s", self.title, exc)

        return {
            "columns": columns,
            "rows": rows[: self.max_rows],
            "model_name": self.model_name,
            "show_link": self.show_link,
            "total_rows": len(rows),
        }


@dataclass
class ListWidget(AdminWidget):
    """
    Displays a simple list of items on the dashboard.

    Example:
        ListWidget(
            title="Quick Links",
            items=[
                {"label": "Documentation", "url": "/docs", "icon": "book"},
                {"label": "Settings", "url": "/admin/config", "icon": "settings"},
            ],
        )
    """

    items: list[dict[str, Any]] = field(default_factory=list)
    items_fn: Callable | None = None
    show_icon: bool = True

    def __init__(self, **kwargs):
        self.items = kwargs.pop("items", [])
        self.items_fn = kwargs.pop("items_fn", None)
        self.show_icon = kwargs.pop("show_icon", True)
        super().__init__(**kwargs)

    def get_data(self) -> dict[str, Any]:
        items = self.items
        if self.items_fn:
            try:
                items = self.items_fn()
            except Exception as exc:
                logger.error("ListWidget %s items_fn error: %s", self.title, exc)
        return {
            "items": items,
            "show_icon": self.show_icon,
        }


@dataclass
class ProgressWidget(AdminWidget):
    """
    Displays a progress bar or set of progress bars.

    Example:
        ProgressWidget(
            title="Storage Usage",
            bars=[
                {"label": "Images", "value": 75, "max": 100, "color": "blue"},
                {"label": "Documents", "value": 30, "max": 100, "color": "green"},
            ],
        )
    """

    bars: list[dict[str, Any]] = field(default_factory=list)
    bars_fn: Callable | None = None

    def __init__(self, **kwargs):
        self.bars = kwargs.pop("bars", [])
        self.bars_fn = kwargs.pop("bars_fn", None)
        super().__init__(**kwargs)

    def get_data(self) -> dict[str, Any]:
        bars = self.bars
        if self.bars_fn:
            try:
                bars = self.bars_fn()
            except Exception as exc:
                logger.error("ProgressWidget %s bars_fn error: %s", self.title, exc)
        return {"bars": bars}


@dataclass
class CustomHTMLWidget(AdminWidget):
    """
    Widget that renders custom HTML content.

    For advanced use cases where built-in widgets don't suffice.
    """

    html_content: str = ""
    html_fn: Callable | None = None

    def get_data(self) -> dict[str, Any]:
        html = self.html_content
        if self.html_fn:
            try:
                html = str(self.html_fn())
            except Exception as exc:
                logger.error("CustomHTMLWidget %s html_fn error: %s", self.title, exc)
        return {"html_content": html}


class WidgetRegistry:
    """
    Registry for dashboard widgets.

    Manages a collection of widgets and provides methods to query,
    filter, and organize them for dashboard rendering.
    """

    def __init__(self):
        self._widgets: list[AdminWidget] = []

    def register(self, widget: AdminWidget) -> None:
        """Register a widget."""
        self._widgets.append(widget)

    def unregister(self, widget: AdminWidget) -> None:
        """Unregister a widget."""
        self._widgets = [w for w in self._widgets if w is not widget]

    def clear(self) -> None:
        """Remove all widgets."""
        self._widgets.clear()

    def get_widgets(self, position: WidgetPosition | None = None) -> list[AdminWidget]:
        """
        Get widgets, optionally filtered by position.

        Returns widgets sorted by order.
        """
        widgets = [w for w in self._widgets if w.visible]
        if position:
            widgets = [w for w in widgets if w.position == position]
        return sorted(widgets, key=lambda w: w.order)

    def get_widgets_by_size(self, size: WidgetSize) -> list[AdminWidget]:
        """Get widgets of a specific size."""
        return [w for w in self._widgets if w.visible and w.size == size]

    def to_template_data(self, position: WidgetPosition | None = None) -> list[dict[str, Any]]:
        """Serialize all matching widgets for template rendering."""
        return [w.to_template_data() for w in self.get_widgets(position)]

    @property
    def count(self) -> int:
        """Return total number of registered widgets."""
        return len(self._widgets)


# Default global widget registry
_default_registry = WidgetRegistry()


def get_widget_registry() -> WidgetRegistry:
    """Get the default widget registry."""
    return _default_registry


def register_widget(widget: AdminWidget) -> AdminWidget:
    """Register a widget to the default registry."""
    _default_registry.register(widget)
    return widget
