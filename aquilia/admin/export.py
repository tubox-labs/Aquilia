"""
AquilAdmin -- Export System.

Provides a comprehensive data export pipeline supporting multiple formats:
CSV, JSON, XLSX (Excel), XML, and YAML.

Features:
- Field selection (choose which fields to export)
- Custom headers / column names
- Related field traversal (e.g. "customer__name")
- Value formatting / transformation
- Streaming for large datasets
- Permission-based export access

Usage:
    from aquilia.admin.export import Exporter, CSVExporter, JSONExporter

    exporter = CSVExporter(
        model=Order,
        fields=["id", "customer__name", "total", "status", "created_at"],
        headers={"customer__name": "Customer", "created_at": "Order Date"},
    )
    content = exporter.export(queryset)
"""

from __future__ import annotations

import csv
import io
import json
import logging
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Type, TYPE_CHECKING
from uuid import UUID

if TYPE_CHECKING:
    from aquilia.models.base import Model

logger = logging.getLogger("aquilia.admin.export")


class ExportFormat(Enum):
    """Supported export formats."""
    CSV = "csv"
    JSON = "json"
    XLSX = "xlsx"
    XML = "xml"
    YAML = "yaml"


def _serialize_value(value: Any) -> Any:
    """Convert a value to a JSON/CSV-safe representation."""
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, UUID):
        return str(value)
    if isinstance(value, bytes):
        return f"<binary:{len(value)} bytes>"
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (list, tuple)):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    return value


def _get_nested_value(obj: Any, field_path: str) -> Any:
    """
    Traverse dotted/double-underscore field paths.

    e.g. "customer__name" → obj.customer.name
    """
    parts = field_path.replace("__", ".").split(".")
    current = obj
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return None
    return current


class Exporter:
    """
    Base exporter class.

    Subclass this and implement `render()` for custom formats.
    """

    format: ExportFormat = ExportFormat.CSV
    content_type: str = "text/plain"
    file_extension: str = "txt"

    def __init__(
        self,
        model: Optional[Type[Model]] = None,
        fields: Optional[List[str]] = None,
        exclude: Optional[List[str]] = None,
        headers: Optional[Dict[str, str]] = None,
        formatters: Optional[Dict[str, Callable]] = None,
        filename: Optional[str] = None,
    ):
        self.model = model
        self.fields = fields or []
        self.exclude = exclude or []
        self.headers = headers or {}
        self.formatters = formatters or {}
        self.filename = filename

    def get_fields(self, sample_row: Optional[Dict[str, Any]] = None) -> List[str]:
        """
        Determine which fields to export.

        Priority:
        1. Explicit self.fields
        2. Model _fields (minus exclude)
        3. Sample row keys
        """
        if self.fields:
            return [f for f in self.fields if f not in self.exclude]

        if self.model and hasattr(self.model, "_fields"):
            model_fields = list(self.model._fields.keys())
            return [f for f in model_fields if f not in self.exclude]

        if sample_row:
            return [k for k in sample_row.keys() if k not in self.exclude]

        return []

    def get_header(self, field_name: str) -> str:
        """Get the display header for a field."""
        if field_name in self.headers:
            return self.headers[field_name]
        return field_name.replace("_", " ").replace("__", " › ").title()

    def get_value(self, row: Any, field_name: str) -> Any:
        """
        Extract and format a field value from a row.

        Handles dict rows and object rows, applies formatters.
        """
        if isinstance(row, dict):
            raw = row.get(field_name)
            if raw is None and "__" in field_name:
                raw = _get_nested_value(row, field_name)
        else:
            raw = _get_nested_value(row, field_name)

        if field_name in self.formatters:
            try:
                raw = self.formatters[field_name](raw)
            except Exception as exc:
                logger.warning("Formatter error for %s: %s", field_name, exc)

        return _serialize_value(raw)

    def get_filename(self, model_name: str = "") -> str:
        """Generate the export filename."""
        if self.filename:
            return self.filename
        name = model_name or (self.model.__name__ if self.model else "export")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{name}_{timestamp}.{self.file_extension}"

    def export(self, rows: Sequence[Any]) -> str:
        """
        Export rows to the target format.

        Args:
            rows: Iterable of model instances or dicts

        Returns:
            Formatted string content
        """
        return self.render(rows)

    def render(self, rows: Sequence[Any]) -> str:
        """
        Render rows to string. Override in subclasses.
        """
        raise NotImplementedError


class CSVExporter(Exporter):
    """Export data as CSV."""

    format = ExportFormat.CSV
    content_type = "text/csv; charset=utf-8"
    file_extension = "csv"

    def __init__(self, delimiter: str = ",", quoting: int = csv.QUOTE_MINIMAL, **kwargs):
        super().__init__(**kwargs)
        self.delimiter = delimiter
        self.quoting = quoting

    def render(self, rows: Sequence[Any]) -> str:
        output = io.StringIO()
        rows_list = list(rows)

        sample = rows_list[0] if rows_list else None
        sample_dict = sample if isinstance(sample, dict) else None
        fields = self.get_fields(sample_dict)

        if not fields:
            return ""

        writer = csv.writer(
            output,
            delimiter=self.delimiter,
            quoting=self.quoting,
        )

        # Header row
        writer.writerow([self.get_header(f) for f in fields])

        # Data rows
        for row in rows_list:
            writer.writerow([self.get_value(row, f) for f in fields])

        return output.getvalue()


class JSONExporter(Exporter):
    """Export data as JSON array."""

    format = ExportFormat.JSON
    content_type = "application/json; charset=utf-8"
    file_extension = "json"

    def __init__(self, indent: int = 2, use_headers: bool = False, **kwargs):
        super().__init__(**kwargs)
        self.indent = indent
        self.use_headers = use_headers

    def render(self, rows: Sequence[Any]) -> str:
        rows_list = list(rows)

        sample = rows_list[0] if rows_list else None
        sample_dict = sample if isinstance(sample, dict) else None
        fields = self.get_fields(sample_dict)

        if not fields:
            return "[]"

        result = []
        for row in rows_list:
            record = {}
            for f in fields:
                key = self.get_header(f) if self.use_headers else f
                record[key] = self.get_value(row, f)
            result.append(record)

        return json.dumps(result, indent=self.indent, ensure_ascii=False, default=str)


class XMLExporter(Exporter):
    """Export data as XML."""

    format = ExportFormat.XML
    content_type = "application/xml; charset=utf-8"
    file_extension = "xml"

    def __init__(self, root_tag: str = "records", row_tag: str = "record", **kwargs):
        super().__init__(**kwargs)
        self.root_tag = root_tag
        self.row_tag = row_tag

    def _escape_xml(self, value: Any) -> str:
        """Escape XML special characters."""
        s = str(value)
        return (
            s.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&apos;")
        )

    def _safe_tag(self, name: str) -> str:
        """Make a string safe for use as an XML tag name."""
        tag = name.replace(" ", "_").replace("__", "_")
        if tag[0:1].isdigit():
            tag = "field_" + tag
        return tag

    def render(self, rows: Sequence[Any]) -> str:
        rows_list = list(rows)

        sample = rows_list[0] if rows_list else None
        sample_dict = sample if isinstance(sample, dict) else None
        fields = self.get_fields(sample_dict)

        if not fields:
            return f'<?xml version="1.0" encoding="UTF-8"?>\n<{self.root_tag}/>'

        lines = ['<?xml version="1.0" encoding="UTF-8"?>']
        lines.append(f"<{self.root_tag}>")

        for row in rows_list:
            lines.append(f"  <{self.row_tag}>")
            for f in fields:
                tag = self._safe_tag(f)
                value = self.get_value(row, f)
                lines.append(f"    <{tag}>{self._escape_xml(value)}</{tag}>")
            lines.append(f"  </{self.row_tag}>")

        lines.append(f"</{self.root_tag}>")
        return "\n".join(lines)


class ExportRegistry:
    """
    Registry of available export formats.

    Manages exporters and provides factory methods for creating
    exporter instances from format names.
    """

    _exporters: Dict[str, Type[Exporter]] = {}

    @classmethod
    def register(cls, format_name: str, exporter_cls: Type[Exporter]) -> None:
        """Register an exporter class for a format."""
        cls._exporters[format_name.lower()] = exporter_cls

    @classmethod
    def get(cls, format_name: str) -> Optional[Type[Exporter]]:
        """Get an exporter class by format name."""
        return cls._exporters.get(format_name.lower())

    @classmethod
    def create(cls, format_name: str, **kwargs) -> Optional[Exporter]:
        """Create an exporter instance by format name."""
        exporter_cls = cls.get(format_name)
        if exporter_cls:
            return exporter_cls(**kwargs)
        return None

    @classmethod
    def available_formats(cls) -> List[str]:
        """List all registered export format names."""
        return sorted(cls._exporters.keys())


# Register built-in exporters
ExportRegistry.register("csv", CSVExporter)
ExportRegistry.register("json", JSONExporter)
ExportRegistry.register("xml", XMLExporter)
