"""
AMDL AST Node Types -- Aquilia Model Definition Language.

.. deprecated:: 1.0
    The AMDL system is deprecated. Use the Python-native ``Model`` class
    system (``aquilia.models.base.Model``) instead. AMDL will be removed
    in a future release.

These dataclasses represent the parsed structure of `.amdl` files.
Each node maps directly to an AMDL directive.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

warnings.warn(
    "The AMDL AST nodes module (aquilia.models.ast_nodes) is deprecated. "
    "Use the Python-native Model class system (aquilia.models.base.Model) instead. "
    "AMDL will be removed in a future release.",
    DeprecationWarning,
    stacklevel=2,
)


class FieldType(str, Enum):
    """Built-in AMDL field types."""

    AUTO = "Auto"
    INT = "Int"
    BIGINT = "BigInt"
    STR = "Str"
    TEXT = "Text"
    BOOL = "Bool"
    FLOAT = "Float"
    DECIMAL = "Decimal"
    JSON = "JSON"
    BYTES = "Bytes"
    DATETIME = "DateTime"
    DATE = "Date"
    TIME = "Time"
    UUID = "UUID"
    ENUM = "Enum"
    FOREIGN_KEY = "ForeignKey"


class LinkKind(str, Enum):
    """Relationship cardinality."""

    ONE = "ONE"
    MANY = "MANY"
    MANY_THROUGH = "MANY_THROUGH"


@dataclass
class SlotNode:
    """
    Represents a `slot` directive -- a model field/column.

    Example AMDL:
        slot username :: Str [max=150, unique]
    """

    name: str
    field_type: FieldType
    type_params: tuple[Any, ...] | None = None  # e.g., Decimal(10,2) -> (10, 2)
    modifiers: dict[str, Any] = field(default_factory=dict)
    is_pk: bool = False
    is_unique: bool = False
    is_nullable: bool = False
    max_length: int | None = None
    default_expr: str | None = None  # e.g., "now_utc()"
    note: str | None = None
    line_number: int = 0
    source_file: str = ""


@dataclass
class LinkNode:
    """
    Represents a `link` directive -- a relationship.

    Example AMDL:
        link profile -> ONE Profile [fk=user_id, back=user]
    """

    name: str
    kind: LinkKind
    target_model: str
    fk_field: str | None = None
    back_name: str | None = None
    through_model: str | None = None
    modifiers: dict[str, Any] = field(default_factory=dict)
    line_number: int = 0
    source_file: str = ""


@dataclass
class IndexNode:
    """
    Represents an `index` directive.

    Example AMDL:
        index [username, email] unique
    """

    fields: list[str] = field(default_factory=list)
    is_unique: bool = False
    name: str | None = None
    line_number: int = 0
    source_file: str = ""


@dataclass
class HookNode:
    """
    Represents a `hook` directive -- lifecycle binding.

    Example AMDL:
        hook before_save -> hash_password
    """

    event: str  # e.g., "before_save", "after_delete", "validate"
    handler_name: str
    line_number: int = 0
    source_file: str = ""


@dataclass
class MetaNode:
    """
    Represents a `meta` directive.

    Example AMDL:
        meta table = "aq_user"
    """

    key: str
    value: str
    line_number: int = 0
    source_file: str = ""


@dataclass
class NoteNode:
    """
    Represents a `note` directive -- freeform documentation.

    Example AMDL:
        note "This model stores user accounts"
    """

    text: str
    line_number: int = 0
    source_file: str = ""


@dataclass
class ModelNode:
    """
    Represents a complete MODEL stanza.

    Contains all slots, links, indexes, hooks, meta, and notes.
    """

    name: str
    slots: list[SlotNode] = field(default_factory=list)
    links: list[LinkNode] = field(default_factory=list)
    indexes: list[IndexNode] = field(default_factory=list)
    hooks: list[HookNode] = field(default_factory=list)
    meta: dict[str, str] = field(default_factory=dict)
    notes: list[str] = field(default_factory=list)
    source_file: str = ""
    start_line: int = 0
    end_line: int = 0

    @property
    def table_name(self) -> str:
        """Get table name from meta or derive from model name."""
        return self.meta.get("table", self.name.lower())

    @property
    def pk_slot(self) -> SlotNode | None:
        """Get primary key slot, if any."""
        for s in self.slots:
            if s.is_pk:
                return s
        return None

    def get_slot(self, name: str) -> SlotNode | None:
        """Find slot by name."""
        for s in self.slots:
            if s.name == name:
                return s
        return None

    def fingerprint(self) -> str:
        """Compute a deterministic hash for migration diffing."""
        import hashlib
        import json

        data = {
            "name": self.name,
            "table": self.table_name,
            "slots": [
                {
                    "name": s.name,
                    "type": s.field_type.value,
                    "pk": s.is_pk,
                    "unique": s.is_unique,
                    "nullable": s.is_nullable,
                    "max": s.max_length,
                    "default": s.default_expr,
                }
                for s in self.slots
            ],
            "indexes": [{"fields": idx.fields, "unique": idx.is_unique} for idx in self.indexes],
        }
        raw = json.dumps(data, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class AMDLFile:
    """
    Represents a parsed `.amdl` file containing one or more models.
    """

    path: str
    models: list[ModelNode] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
