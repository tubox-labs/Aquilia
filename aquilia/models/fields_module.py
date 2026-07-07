"""
Aquilia Model Fields -- Pure Python, production-grade field system.

Every field is production-ready with full validation, SQL generation,
and serialization. Aquilia fields use a unique descriptive API:

    class User(Model):
        table = "users"

        name = Char(max_length=150)
        email = Email(max_length=255, unique=True)
        age = Integer(null=True)
        bio = Text(blank=True)
        joined = DateTime(auto_now_add=True)

No $ prefixes -- just clean, expressive Python.
"""

from __future__ import annotations

import copy
import datetime
import decimal
import ipaddress
import json
import re
import uuid
from collections.abc import Callable, Sequence
from typing import (
    TYPE_CHECKING,
    Any,
    Generic,
    TypeVar,
    overload,
)

if TYPE_CHECKING:
    from .base import Model
    from .relations import Related

#: Bound to Model -- lets ForeignKey/OneToOneField infer *which* model
#: they point to from their own constructor argument (`ForeignKey(User)`
#: binds TModel=User), the same convention Manager/QuerySet/Q already use
#: (aquilia/models/manager.py) and RelatedNotLoaded now uses too
#: (aquilia/models/relations.py).
TModel = TypeVar("TModel", bound="Model")

#: The Python value a scalar field reads/writes (`str` for CharField, `int`
#: for IntegerField, `datetime.datetime` for DateTimeField, ...). Unlike
#: TModel above, T is never inferred from a constructor argument -- each
#: concrete field's Python type is fixed at the class level (matching its
#: existing `_python_type` class attribute), so every concrete subclass
#: just names its T directly (`class CharField(Field[str])`) with no
#: forward-reference/string ambiguity of the kind ForeignKey's `to=` has.
T = TypeVar("T")

__all__: list[str] = []


# ── FK action normalization ───────────────────────────────────────────────────

_ON_DELETE_SQL_MAP: dict[str, str] = {
    "CASCADE": "CASCADE",
    "SET_NULL": "SET NULL",
    "SET NULL": "SET NULL",
    "SETNULL": "SET NULL",
    "SET_DEFAULT": "SET DEFAULT",
    "SET DEFAULT": "SET DEFAULT",
    "SETDEFAULT": "SET DEFAULT",
    "RESTRICT": "RESTRICT",
    "NO_ACTION": "NO ACTION",
    "NO ACTION": "NO ACTION",
    "DO_NOTHING": "NO ACTION",
    "DO NOTHING": "NO ACTION",
    "DONOTHING": "NO ACTION",
    "PROTECT": "RESTRICT",
}


def _normalize_fk_action(action: str) -> str:
    """Normalize a Python on_delete/on_update constant to valid SQL."""
    return _ON_DELETE_SQL_MAP.get(action.upper().strip(), action)


# ── Field Errors ─────────────────────────────────────────────────────────────

# Import the Fault base so field validation errors flow through the fault pipeline
from ..faults.domains import FieldValidationFault as _FieldValidationFault


class FieldValidationError(_FieldValidationFault, ValueError):
    """Raised when field validation fails.

    Inherits from both ``FieldValidationFault`` (Aquilia fault pipeline)
    and ``ValueError`` (backward compatibility with existing except clauses).
    """

    def __init__(self, field_name: str, message: str, value: Any = None):
        self.field_name = field_name
        self.value = value
        # Initialize the Fault side (FieldValidationFault)
        _FieldValidationFault.__init__(self, field_name=field_name, reason=message)
        # Override the message to match the established format
        self.args = (f"Field '{field_name}': {message}",)


# ── Sentinel ─────────────────────────────────────────────────────────────────


class _Unset:
    """Sentinel for distinguishing 'not set' from None."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __repr__(self):
        return "<UNSET>"

    def __bool__(self):
        return False


UNSET = _Unset()


# ── Base Field ───────────────────────────────────────────────────────────────


class Field(Generic[T]):
    """
    Base field descriptor -- all Aquilia fields inherit from this.

    Core parameters (shared by every field):
        null        – Allow NULL in database (default False)
        blank       – Allow empty string in validation (default False)
        default     – Default value or callable
        unique      – Add UNIQUE constraint
        primary_key – Mark as primary key
        db_index    – Create database index
        db_column   – Override column name
        choices     – Restrict to enumerated values
        validators  – List of validation callables
        help_text   – Documentation string
        editable    – Whether field is editable (default True)
        verbose_name – Human-readable field label

    ``Field`` is a real generic data descriptor (defines both ``__get__``
    and ``__set__``): reading ``instance.name`` where
    ``name = CharField(...)`` resolves to ``str`` (not the ``CharField``
    object) because ``CharField(Field[str])`` binds T=str -- every concrete
    field names its Python value type directly at the class level (see the
    ``T`` TypeVar above), mirroring the ``ForeignKey``/``OneToOneField``
    generic descriptor pattern (which uses its own ``TModel`` axis for the
    related-model case instead). Class-level access (``Model.name``) still
    returns the ``Field`` object itself, unchanged.

    This does not encode ``null=True`` in the declared type: a nullable
    field is still declared as ``Field[T]``, not ``Field[T | None]``,
    because nullability is a runtime constructor argument, not something
    knowable from the field's class alone -- the same tradeoff already
    accepted for ``Related[TModel]`` (which spells out ``None`` explicitly
    because a relation's "loaded or not" state genuinely can't be known
    from the declaration either).
    """

    # Subclass-specific
    _field_type: str = "FIELD"
    _python_type: type = object

    # Counter for field ordering
    _creation_counter = 0

    def __init__(
        self,
        *,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        self.null = null
        self.blank = blank
        self.default = default
        self.unique = unique
        self.primary_key = primary_key
        self.db_index = db_index
        self.db_column = db_column
        self.choices = choices
        self.validators = validators or []
        self.help_text = help_text
        self.editable = editable
        self.verbose_name = verbose_name

        # Set by metaclass
        self.name: str = ""
        self.attr_name: str = ""
        self.model: type[Model] | None = None

        # Ordering
        self._order = Field._creation_counter
        Field._creation_counter += 1

    def __set_name__(self, owner: type, name: str) -> None:
        """Bind this field to the attribute name it was assigned to on ``owner``.

        Called automatically by Python when the class body finishes
        executing (the standard descriptor protocol hook) -- not something
        callers invoke directly. Sets ``attr_name`` to the Python attribute
        name (e.g. ``"name"``), and ``name`` (the DB column name) to
        ``db_column`` if one was given, otherwise to the same attribute
        name. Also derives a human-readable ``verbose_name`` (``"joined_at"``
        -> ``"Joined At"``) when one wasn't supplied explicitly.
        """
        self.name = self.db_column or name
        self.attr_name = name
        if self.verbose_name is None:
            self.verbose_name = name.replace("_", " ").title()

    @overload
    def __get__(self, instance: None, owner: type | None = None) -> Field[T]: ...
    @overload
    def __get__(self, instance: Model, owner: type | None = None) -> T: ...

    def __get__(self, instance: Model | None, owner: type | None = None) -> Any:
        """Return the raw ``Field`` object for class-level access, or ``instance.__dict__[attr_name]`` (typed as ``T``) for instance access.

        Reading an attribute that was never set on the instance returns
        ``None`` (``dict.get`` default), not an ``AttributeError`` and not
        the class-level ``Field`` object -- see ``only()``/``defer()`` in
        ``aquilia/models/base.py`` for how a deliberately-excluded field is
        distinguished from a genuine ``NULL`` despite this.
        """
        if instance is None:
            # Class-level access (Model.name, introspection, query-builder
            # field resolution) still returns the Field object itself.
            return self
        return instance.__dict__.get(self.attr_name)

    def __set__(self, instance: Model, value: T) -> None:
        """Write *value* into ``instance.__dict__[attr_name]`` -- the same slot every ``setattr()``/``from_row()``/``save()`` call site already uses."""
        instance.__dict__[self.attr_name] = value

    def __repr__(self) -> str:
        """Return ``<ClassName: column_name>`` for debugging/logging."""
        return f"<{self.__class__.__name__}: {self.name}>"

    @property
    def column_name(self) -> str:
        """Database column name -- ``db_column`` if given, otherwise the field's attribute name.

        Prefer this over touching ``db_column``/``name`` directly when
        generating SQL; it always resolves to the name actually written to
        the schema, regardless of which of the two attributes was set.
        """
        return self.db_column or self.name

    def has_default(self) -> bool:
        """Return whether a default was configured (distinguishing "no default" from a default of ``None``).

        ``UNSET`` (the module-level sentinel), not ``None``, is what marks
        "no default was given" -- ``default=None`` is a legitimate,
        explicit default for a nullable field.
        """
        return self.default is not UNSET

    def get_default(self) -> Any:
        """Resolve the field's default value for use at insert time.

        Returns ``None`` if no default was configured. If ``default`` is
        callable (e.g. ``datetime.datetime.now``, ``list``, ``uuid.uuid4``),
        it is invoked and the result returned -- this is how mutable
        defaults (lists, dicts) avoid being shared across instances, and how
        time-based defaults get a fresh value per row. Non-callable defaults
        are deep-copied for the same mutable-sharing reason (e.g.
        ``default=[]`` must not hand out the same list object to every
        instance).
        """
        if self.default is UNSET:
            return None
        if callable(self.default):
            return self.default()
        return copy.deepcopy(self.default)

    def validate(self, value: Any) -> Any:
        """
        Validate and coerce value. Returns cleaned value.
        Override in subclasses for type-specific validation.
        """
        if value is None:
            # blank=True means field can be empty (validated before save)
            # null=True means field can be NULL in database
            # If blank=True, allow None during validation (will be set by auto_now/default)
            if not self.blank and not self.null:
                raise FieldValidationError(self.name, "Cannot be null")
            return None

        if self.choices:
            valid_values = [c[0] for c in self.choices]
            if value not in valid_values:
                raise FieldValidationError(
                    self.name,
                    f"Invalid choice '{value}'. Must be one of: {valid_values}",
                    value,
                )

        for validator in self.validators:
            validator(value)

        return value

    def to_python(self, value: Any) -> Any:
        """Convert a raw value coming out of the DB driver into this field's Python representation.

        The base implementation is a pass-through (``None`` stays ``None``,
        everything else is returned unchanged) -- it exists so generic code
        can call ``field.to_python(row_value)`` uniformly. Concrete fields
        override this to parse driver-returned strings/numbers into richer
        types, e.g. ``DateTimeField.to_python`` parses an ISO-8601 string
        (as returned by the SQLite driver) into a ``datetime.datetime``,
        and ``JSONField.to_python`` runs ``json.loads`` on a stored TEXT
        column. This is the inverse operation of ``to_db``.
        """
        if value is None:
            return None
        return value

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Convert a Python value into the representation the given SQL ``dialect`` expects on write.

        The base implementation is a pass-through. Concrete fields override
        this for dialect-specific encoding -- e.g. ``BooleanField`` writes
        native ``bool`` for ``"postgresql"`` (asyncpg expects it) but ``0``/
        ``1`` for SQLite/MySQL/Oracle; ``DateTimeField`` serializes to an
        ISO-8601 string only for SQLite, passing native ``datetime`` objects
        through unchanged for dialects whose drivers accept them directly.
        This is the inverse operation of ``to_python``.
        """
        if value is None:
            return None
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """Return the SQL column type string for ``dialect`` (e.g. ``"VARCHAR(255)"``, ``"INTEGER"``).

        Every concrete field must implement this -- there is no sensible
        generic SQL type for the abstract base, so calling it directly on
        ``Field`` raises ``NotImplementedError``. Dialect values used
        throughout this module are ``"sqlite"`` (default), ``"postgresql"``,
        ``"mysql"``, and ``"oracle"``.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement sql_type()")

    def sql_column_def(self, dialect: str = "sqlite") -> str:
        """Generate the full ``CREATE TABLE``-style column definition for this field.

        Composes the column name, ``sql_type(dialect)``, and, in order:
        a dialect-appropriate ``PRIMARY KEY``/auto-increment clause (see
        ``AutoField``/``BigAutoField``/``SmallAutoField`` handling below --
        PostgreSQL relies on ``SERIAL``-family types implying identity,
        MySQL needs an explicit ``AUTO_INCREMENT``, Oracle needs
        ``GENERATED ALWAYS AS IDENTITY``, SQLite needs ``AUTOINCREMENT``),
        ``UNIQUE`` (skipped when already a primary key), ``NOT NULL``
        (skipped for nullable fields and primary keys, which are implicitly
        non-null), and a ``DEFAULT`` clause when a non-callable default is
        set and ``_sql_default`` doesn't suppress it for the dialect.
        Used by schema generation and migration DDL, not by ordinary query
        building.
        """
        parts = [f'"{self.column_name}"', self.sql_type(dialect)]

        if self.primary_key:
            if isinstance(self, (AutoField, BigAutoField, SmallAutoField)):
                if dialect == "postgresql":
                    # SERIAL/BIGSERIAL/SMALLSERIAL already implies NOT NULL
                    parts.append("PRIMARY KEY")
                elif dialect == "mysql":
                    parts.append("PRIMARY KEY")
                    parts.append("AUTO_INCREMENT")
                elif dialect == "oracle":
                    # Oracle 12c+ IDENTITY column
                    parts.append("GENERATED ALWAYS AS IDENTITY")
                    parts.append("PRIMARY KEY")
                else:
                    parts.append("PRIMARY KEY")
                    parts.append("AUTOINCREMENT")
            else:
                parts.append("PRIMARY KEY")
        if self.unique and not self.primary_key:
            parts.append("UNIQUE")
        if not self.null and not self.primary_key:
            parts.append("NOT NULL")
        if self.has_default():
            sql_default = self._sql_default(dialect)
            if sql_default is not None:
                parts.append(f"DEFAULT {sql_default}")

        return " ".join(parts)

    def _sql_default(self, dialect: str = "sqlite") -> str | None:
        """Get SQL DEFAULT clause value.

        MySQL does not allow DEFAULT on TEXT, BLOB, JSON, or GEOMETRY
        columns (error 1101).  When the dialect is ``mysql`` and the
        resolved SQL type is one of these, return ``None`` so the DDL
        omits the clause.  The Python-level default still applies at
        INSERT time.
        """
        if self.default is UNSET or callable(self.default):
            return None

        # MySQL TEXT/BLOB/JSON cannot have a DEFAULT clause.
        if dialect == "mysql":
            sql_type = self.sql_type(dialect).upper()
            _NO_DEFAULT_TYPES = {
                "TEXT",
                "TINYTEXT",
                "MEDIUMTEXT",
                "LONGTEXT",
                "BLOB",
                "TINYBLOB",
                "MEDIUMBLOB",
                "LONGBLOB",
                "JSON",
                "GEOMETRY",
            }
            if sql_type in _NO_DEFAULT_TYPES:
                return None

        if isinstance(self.default, bool):
            if dialect == "postgresql":
                return "TRUE" if self.default else "FALSE"
            if dialect == "oracle":
                return "1" if self.default else "0"
            return "1" if self.default else "0"
        if isinstance(self.default, (int, float)):
            return str(self.default)
        if isinstance(self.default, str):
            return f"'{self.default}'"
        return None

    def deconstruct(self) -> dict[str, Any]:
        """Serialize this field's defining state to a plain, JSON-friendly ``dict``.

        Used by the migration system to snapshot a model's schema and diff
        it against a previous snapshot to detect field changes. Always
        includes ``type`` (the concrete field class name), ``null``,
        ``unique``, ``primary_key``, and ``db_index``; conditionally
        includes ``db_column`` and ``default`` (only when a non-callable
        default is set -- callables aren't meaningfully diffable/
        serializable, so they're omitted). Subclasses with extra
        constructor arguments that affect the schema (``max_length``,
        ``max_digits``/``decimal_places``, ``to``, ...) override this,
        call ``super().deconstruct()``, and add their own keys.
        """
        data: dict[str, Any] = {
            "type": self.__class__.__name__,
            "null": self.null,
            "unique": self.unique,
            "primary_key": self.primary_key,
            "db_index": self.db_index,
        }
        if self.db_column:
            data["db_column"] = self.db_column
        if self.has_default() and not callable(self.default):
            data["default"] = self.default
        return data

    def clone(self) -> Field:
        """Return an independent deep copy of this field, including its ``choices``/``validators`` lists.

        Used when a field instance needs to be duplicated across models or
        reused with modifications without the two copies aliasing mutable
        state (e.g. abstract base model fields being copied onto each
        concrete subclass).
        """
        return copy.deepcopy(self)


# ═══════════════════════════════════════════════════════════════════════════════
# NUMERIC FIELDS
# ═══════════════════════════════════════════════════════════════════════════════


class AutoField(Field[int]):
    """Auto-incrementing integer primary key (32-bit).

    Django-style ``id`` column: ``primary_key`` defaults to ``True`` here
    (unlike the base ``Field``), so declaring ``id = AutoField()`` is enough
    to get a self-incrementing PK. The constructor re-declares every keyword
    from ``Field.__init__`` explicitly (rather than accepting ``**kwargs``)
    purely so IDEs/type checkers see ``AutoField``'s actual signature --
    including its different ``primary_key`` default -- instead of an opaque
    ``**kwargs``.

    A value of ``None`` passed to ``validate()`` is accepted and passed
    through unchanged (the database/driver is responsible for generating
    the actual id on insert); any other value is coerced to ``int``.
    """

    _field_type = "AUTO"
    _python_type = int

    def __init__(
        self,
        *,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = True,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        super().__init__(
            null=null,
            blank=blank,
            default=default,
            unique=unique,
            primary_key=primary_key,
            db_index=db_index,
            db_column=db_column,
            choices=choices,
            validators=validators,
            help_text=help_text,
            editable=editable,
            verbose_name=verbose_name,
        )

    def validate(self, value: Any) -> Any:
        """Pass ``None`` through untouched (DB-assigned id) or coerce anything else to ``int``.

        Raises ``FieldValidationError`` if a non-``None`` value can't be
        converted to ``int`` (e.g. a non-numeric string).
        """
        if value is None:
            return None  # Auto-generated
        if not isinstance(value, int):
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise FieldValidationError(self.name, f"Expected integer, got {type(value).__name__}")
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``SERIAL`` on PostgreSQL, ``NUMBER(10)`` on Oracle, ``INTEGER`` elsewhere.

        The actual ``AUTOINCREMENT``/``AUTO_INCREMENT``/``IDENTITY``
        behavior for non-PostgreSQL dialects is added separately in
        ``Field.sql_column_def`` when ``primary_key`` is set, not here.
        """
        if dialect == "postgresql":
            return "SERIAL"
        if dialect == "oracle":
            return "NUMBER(10)"
        return "INTEGER"


class BigAutoField(Field[int]):
    """Auto-incrementing 64-bit integer primary key.

    Same shape as ``AutoField`` (``primary_key`` defaults to ``True``,
    ``None`` is accepted for DB-assigned values), sized for tables expected
    to exceed the 32-bit ``AutoField`` range (~2.1 billion rows).
    """

    _field_type = "BIGAUTO"
    _python_type = int

    def __init__(
        self,
        *,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = True,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        super().__init__(
            null=null,
            blank=blank,
            default=default,
            unique=unique,
            primary_key=primary_key,
            db_index=db_index,
            db_column=db_column,
            choices=choices,
            validators=validators,
            help_text=help_text,
            editable=editable,
            verbose_name=verbose_name,
        )

    def validate(self, value: Any) -> Any:
        """Pass ``None`` through untouched (DB-assigned id) or coerce anything else to ``int``."""
        if value is None:
            return None
        if not isinstance(value, int):
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise FieldValidationError(self.name, f"Expected integer, got {type(value).__name__}")
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``BIGSERIAL`` on PostgreSQL, ``NUMBER(19)`` on Oracle, ``INTEGER`` elsewhere (SQLite ``INTEGER`` is 64-bit)."""
        if dialect == "postgresql":
            return "BIGSERIAL"
        if dialect == "oracle":
            return "NUMBER(19)"
        return "INTEGER"


class SmallAutoField(AutoField):
    """Auto-incrementing 16-bit integer primary key.

    Inherits ``AutoField``'s constructor (``primary_key=True`` by default)
    but tightens ``validate()`` to the signed 16-bit range (-32768 to
    32767), matching the storage this maps to on dialects with a distinct
    ``SMALLSERIAL``/``SMALLINT`` type.
    """

    _field_type = "SMALLAUTO"
    _python_type = int

    def validate(self, value: Any) -> Any:
        """Coerce to ``int`` and enforce the signed 16-bit range; ``None`` passes through (DB-assigned)."""
        if value is None:
            return None
        if not isinstance(value, int):
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise FieldValidationError(self.name, f"Expected integer, got {type(value).__name__}")
        if not (-32768 <= value <= 32767):
            raise FieldValidationError(self.name, f"Value {value} out of 16-bit integer range")
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``SMALLSERIAL`` on PostgreSQL, ``NUMBER(5)`` on Oracle, ``INTEGER`` elsewhere."""
        if dialect == "postgresql":
            return "SMALLSERIAL"
        if dialect == "oracle":
            return "NUMBER(5)"
        return "INTEGER"


class IntegerField(Field[int]):
    """Standard 32-bit integer field (-2147483648 to 2147483647).

    Example::

        class Product(Model):
            quantity = IntegerField(default=0)
    """

    _field_type = "INTEGER"
    _python_type = int

    def validate(self, value: Any) -> Any:
        """Run base ``Field`` validation (null/choices/validators), then coerce to ``int`` and enforce the 32-bit range.

        Raises ``FieldValidationError`` if the value can't be converted to
        ``int`` or falls outside the 32-bit signed range.
        """
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, int):
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise FieldValidationError(self.name, f"Expected integer, got {type(value).__name__}")
        if not (-2_147_483_648 <= value <= 2_147_483_647):
            raise FieldValidationError(self.name, f"Value {value} out of 32-bit integer range")
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``NUMBER(10)`` on Oracle, ``INTEGER`` everywhere else."""
        if dialect == "oracle":
            return "NUMBER(10)"
        return "INTEGER"


class BigIntegerField(Field[int]):
    """64-bit integer field, unbounded beyond Python ``int``/``str`` coercion (no explicit range check)."""

    _field_type = "BIGINT"
    _python_type = int

    def validate(self, value: Any) -> Any:
        """Run base ``Field`` validation, then coerce to ``int``. No range check is applied (unlike ``IntegerField``)."""
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, int):
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise FieldValidationError(self.name, f"Expected integer, got {type(value).__name__}")
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``BIGINT`` on PostgreSQL, ``NUMBER(19)`` on Oracle, ``INTEGER`` on SQLite (already 64-bit there)."""
        if dialect == "postgresql":
            return "BIGINT"
        if dialect == "oracle":
            return "NUMBER(19)"
        return "INTEGER"


class SmallIntegerField(Field[int]):
    """16-bit integer field (-32768 to 32767)."""

    _field_type = "SMALLINT"
    _python_type = int

    def validate(self, value: Any) -> Any:
        """Run base ``Field`` validation, coerce to ``int``, and enforce the signed 16-bit range."""
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, int):
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise FieldValidationError(self.name, f"Expected integer, got {type(value).__name__}")
        if not (-32_768 <= value <= 32_767):
            raise FieldValidationError(self.name, f"Value {value} out of 16-bit integer range")
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``SMALLINT`` on PostgreSQL, ``NUMBER(5)`` on Oracle, ``INTEGER`` on SQLite (no smaller native type)."""
        if dialect == "postgresql":
            return "SMALLINT"
        if dialect == "oracle":
            return "NUMBER(5)"
        return "INTEGER"


class PositiveIntegerField(Field[int]):
    """Positive 32-bit integer field (0 to 2147483647).

    Note the range check is purely a Python-level ``validate()`` constraint
    -- ``sql_type`` still maps to a plain (signed) ``INTEGER``/``NUMBER(10)``
    column, since none of the supported dialects have an unsigned integer
    type usable here without dialect-specific ``CHECK`` constraints.
    """

    _field_type = "POSINT"
    _python_type = int

    def validate(self, value: Any) -> Any:
        """Coerce to ``int`` and require ``0 <= value <= 2147483647``."""
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, int):
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise FieldValidationError(self.name, f"Expected integer, got {type(value).__name__}")
        if value < 0:
            raise FieldValidationError(self.name, f"Value must be >= 0, got {value}")
        if value > 2_147_483_647:
            raise FieldValidationError(self.name, f"Value {value} exceeds maximum (2147483647)")
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``NUMBER(10)`` on Oracle, ``INTEGER`` elsewhere (no dialect-native unsigned type is used)."""
        if dialect == "oracle":
            return "NUMBER(10)"
        return "INTEGER"


class PositiveSmallIntegerField(Field[int]):
    """Positive 16-bit integer field (0 to 32767)."""

    _field_type = "POSSMALLINT"
    _python_type = int

    def validate(self, value: Any) -> Any:
        """Coerce to ``int`` and require ``0 <= value <= 32767``."""
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, int):
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise FieldValidationError(self.name, f"Expected integer, got {type(value).__name__}")
        if value < 0:
            raise FieldValidationError(self.name, f"Value must be >= 0, got {value}")
        if value > 32_767:
            raise FieldValidationError(self.name, f"Value {value} exceeds maximum (32767)")
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``SMALLINT`` on PostgreSQL, ``NUMBER(5)`` on Oracle, ``INTEGER`` on SQLite."""
        if dialect == "postgresql":
            return "SMALLINT"
        if dialect == "oracle":
            return "NUMBER(5)"
        return "INTEGER"


class PositiveBigIntegerField(Field[int]):
    """Positive 64-bit integer field (0 to 9223372036854775807)."""

    _field_type = "POSBIGINT"
    _python_type = int

    def validate(self, value: Any) -> Any:
        """Coerce to ``int`` and require ``0 <= value <= 9223372036854775807``."""
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, int):
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise FieldValidationError(self.name, f"Expected integer, got {type(value).__name__}")
        if value < 0:
            raise FieldValidationError(self.name, f"Value must be >= 0, got {value}")
        if value > 9_223_372_036_854_775_807:
            raise FieldValidationError(self.name, f"Value {value} exceeds maximum (9223372036854775807)")
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``BIGINT`` on PostgreSQL, ``NUMBER(19)`` on Oracle, ``INTEGER`` on SQLite (already 64-bit there)."""
        if dialect == "postgresql":
            return "BIGINT"
        if dialect == "oracle":
            return "NUMBER(19)"
        return "INTEGER"


class FloatField(Field[float]):
    """Double-precision floating-point field.

    Accepts ``int`` or ``float`` input (or a numeric string) and always
    returns a Python ``float`` from ``validate()`` -- there is no
    precision/scale enforcement (use ``DecimalField`` when exact decimal
    arithmetic matters, e.g. money).
    """

    _field_type = "FLOAT"
    _python_type = float

    def validate(self, value: Any) -> Any:
        """Coerce ``int``/``float``/numeric-string input to ``float``.

        Raises ``FieldValidationError`` if the value can't be converted to
        a number.
        """
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, (int, float)):
            try:
                value = float(value)
            except (TypeError, ValueError):
                raise FieldValidationError(self.name, f"Expected number, got {type(value).__name__}")
        return float(value)

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``DOUBLE PRECISION`` on PostgreSQL, ``BINARY_DOUBLE`` on Oracle, ``REAL`` on SQLite/MySQL."""
        if dialect == "postgresql":
            return "DOUBLE PRECISION"
        if dialect == "oracle":
            return "BINARY_DOUBLE"
        return "REAL"


class DecimalField(Field[decimal.Decimal]):
    """Fixed-precision decimal field -- for values where binary-float rounding error is unacceptable (money, quantities).

    Args:
        max_digits: Total number of significant digits allowed, counting
            both sides of the decimal point (default 10).
        decimal_places: Number of digits after the decimal point (default
            2). Must be ``<= max_digits``; whole-number digits allowed is
            ``max_digits - decimal_places``.

    Stored as a string in the database (via ``to_db``) and reconstructed
    as ``decimal.Decimal`` on read, avoiding float round-tripping entirely.

    Example::

        class Order(Model):
            total = DecimalField(max_digits=12, decimal_places=2)

        order.total = "19.99"   # validate() coerces to Decimal("19.99")
    """

    _field_type = "DECIMAL"
    _python_type = decimal.Decimal

    def __init__(
        self,
        *,
        max_digits: int = 10,
        decimal_places: int = 2,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        self.max_digits = max_digits
        self.decimal_places = decimal_places
        super().__init__(**kwargs)

    def validate(self, value: Any) -> Any:
        """Coerce input to ``decimal.Decimal`` and enforce ``max_digits``/``decimal_places``.

        An empty/whitespace-only string is treated as ``None`` before the
        base null/blank check runs. Non-``Decimal`` input (``str``, ``int``,
        ``float``) is converted via ``Decimal(str(value))`` -- values are
        stringified first specifically to avoid ``float``'s binary
        representation introducing spurious extra digits (e.g.
        ``Decimal(0.1)`` vs ``Decimal("0.1")``). Raises
        ``FieldValidationError`` if conversion fails, or if the value has
        more whole-number digits than ``max_digits - decimal_places``, more
        fractional digits than ``decimal_places``, or more total
        significant digits than ``max_digits``.
        """
        if isinstance(value, str) and value.strip() == "":
            value = None
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, decimal.Decimal):
            try:
                value = decimal.Decimal(str(value))
            except (TypeError, ValueError, decimal.InvalidOperation):
                raise FieldValidationError(self.name, f"Expected decimal, got {type(value).__name__}")

        # Check digits -- correctly count whole and decimal parts
        sign, digits, exponent = value.as_tuple()
        if exponent >= 0:
            # No decimal places -- e.g. Decimal('123') has exponent=0, digits=(1,2,3)
            whole_digits = len(digits) + exponent
            dec_digits = 0
        else:
            # Negative exponent -- e.g. Decimal('12.34') has exponent=-2
            dec_digits = abs(exponent)
            whole_digits = max(0, len(digits) - dec_digits)

        if whole_digits > (self.max_digits - self.decimal_places):
            raise FieldValidationError(
                self.name,
                f"Ensure that there are no more than "
                f"{self.max_digits - self.decimal_places} digits before the decimal point "
                f"({whole_digits} found)",
            )
        if dec_digits > self.decimal_places:
            raise FieldValidationError(
                self.name,
                f"Ensure that there are no more than {self.decimal_places} decimal places ({dec_digits} found)",
            )
        if len(digits) > self.max_digits:
            raise FieldValidationError(
                self.name,
                f"Ensure that there are no more than {self.max_digits} digits in total ({len(digits)} found)",
            )
        return value

    def to_python(self, value: Any) -> Any:
        """Convert a raw DB value (string, number, or already a ``Decimal``) to ``decimal.Decimal``.

        An empty/whitespace-only string returns ``None`` rather than
        raising, since blank text columns and true NULLs both need to map
        back to "no value".
        """
        if value is None:
            return None
        if isinstance(value, str) and value.strip() == "":
            return None
        return decimal.Decimal(str(value))

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Serialize the ``Decimal`` to ``str`` for storage (preserves exact precision across all dialects)."""
        if value is None:
            return None
        return str(value)

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``NUMBER(max_digits,decimal_places)`` on Oracle, ``DECIMAL(max_digits,decimal_places)`` elsewhere."""
        if dialect == "oracle":
            return f"NUMBER({self.max_digits},{self.decimal_places})"
        return f"DECIMAL({self.max_digits},{self.decimal_places})"

    def deconstruct(self) -> dict[str, Any]:
        """Extend ``Field.deconstruct()`` with ``max_digits``/``decimal_places`` for migration diffing."""
        d = super().deconstruct()
        d["max_digits"] = self.max_digits
        d["decimal_places"] = self.decimal_places
        return d


# ═══════════════════════════════════════════════════════════════════════════════
# TEXT / STRING FIELDS
# ═══════════════════════════════════════════════════════════════════════════════


class CharField(Field[str]):
    """Short text field, stored as ``VARCHAR(max_length)``.

    Args:
        max_length: Maximum number of characters allowed (default 255).
            Enforced both in ``validate()`` and in the generated
            ``VARCHAR``/``VARCHAR2`` column type.

    Follows the Django convention that a ``null=False`` string field never
    stores SQL ``NULL``: when ``blank=True`` and ``null=False``, a missing
    value is coerced to ``""`` (both in ``validate()`` and again defensively
    in ``to_db()``) so there is exactly one representation of "no value" for
    such fields, not two (``NULL`` and ``""``).

    Example::

        class User(Model):
            name = CharField(max_length=150)
            bio = CharField(max_length=500, blank=True)
    """

    _field_type = "CHAR"
    _python_type = str

    def __init__(
        self,
        *,
        max_length: int = 255,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        self.max_length = max_length
        super().__init__(**kwargs)

    def validate(self, value: Any) -> Any:
        """Coerce to ``str``, enforce blank/non-blank and ``max_length``, and apply the "no value = ''" convention.

        Non-string input is stringified via ``str(value)``. When the
        (post-null-check) value is empty or whitespace-only, it's rejected
        unless ``blank=True``. Raises ``FieldValidationError`` for a blank
        value with ``blank=False``, or a value longer than ``max_length``.
        """
        value = super().validate(value)
        if value is None:
            # String fields with blank=True, null=False store "" not NULL
            # (Django convention: avoid two representations of "no data").
            if self.blank and not self.null:
                return ""
            return None
        if not isinstance(value, str):
            value = str(value)
        # blank=True allows empty/whitespace-only strings;
        # blank=False rejects them
        if not value.strip() and not self.blank:
            raise FieldValidationError(self.name, "Cannot be blank")
        if len(value) > self.max_length:
            raise FieldValidationError(self.name, f"Max length is {self.max_length}, got {len(value)} characters")
        return value

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Coerce ``None`` to ``""`` when the column is ``NOT NULL`` (``null=False``), then defer to ``Field.to_db``."""
        # String fields with null=False must never write NULL to the database.
        # Coerce None to "" to satisfy the NOT NULL constraint.
        if value is None and not self.null:
            return ""
        return super().to_db(value, dialect)

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``VARCHAR2(max_length)`` on Oracle, ``VARCHAR(max_length)`` elsewhere."""
        if dialect == "oracle":
            return f"VARCHAR2({self.max_length})"
        return f"VARCHAR({self.max_length})"

    def deconstruct(self) -> dict[str, Any]:
        """Extend ``Field.deconstruct()`` with ``max_length`` for migration diffing."""
        d = super().deconstruct()
        d["max_length"] = self.max_length
        return d


class VarcharField(CharField):
    """Explicit alias for CharField, representing a variable-length string.

    Behaves identically to ``CharField`` in every respect -- only the
    ``_field_type`` tag (``"VARCHAR"``) differs, which is purely
    informational (introspection/tooling display), not something
    ``sql_type``/``validate`` branch on.
    """

    _field_type = "VARCHAR"


class TextField(Field[str]):
    """Long text field with no length restriction, stored as ``TEXT``/``CLOB``.

    Same "no value = ''" convention as ``CharField`` for non-nullable
    blank-allowed fields, but with no ``max_length`` to enforce.
    """

    _field_type = "TEXT"
    _python_type = str

    def validate(self, value: Any) -> Any:
        """Coerce to ``str`` and enforce blank/non-blank; no length limit is applied."""
        value = super().validate(value)
        if value is None:
            # String fields with blank=True, null=False store "" not NULL.
            if self.blank and not self.null:
                return ""
            return None
        if not isinstance(value, str):
            value = str(value)
        if not value.strip() and not self.blank:
            raise FieldValidationError(self.name, "Cannot be blank")
        return value

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Coerce ``None`` to ``""`` when the column is ``NOT NULL`` (``null=False``), then defer to ``Field.to_db``."""
        # String fields with null=False must never write NULL to the database.
        if value is None and not self.null:
            return ""
        return super().to_db(value, dialect)

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``CLOB`` on Oracle, ``TEXT`` elsewhere."""
        if dialect == "oracle":
            return "CLOB"
        return "TEXT"


class SlugField(CharField):
    """URL-friendly slug field -- a ``CharField`` restricted to ``[-a-zA-Z0-9_]+``.

    Args:
        max_length: Defaults to 50 here (vs. 255 for plain ``CharField``),
            matching the short, URL-embeddable strings slugs are meant to be.

    Example::

        class Post(Model):
            slug = SlugField(unique=True)   # e.g. "my-first-post"
    """

    _field_type = "SLUG"
    _SLUG_RE = re.compile(r"^[-a-zA-Z0-9_]+$")

    def __init__(
        self,
        *,
        max_length: int = 50,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        super().__init__(max_length=max_length, **kwargs)

    def validate(self, value: Any) -> Any:
        """Run ``CharField`` validation, then require the value to match ``^[-a-zA-Z0-9_]+$``.

        Raises ``FieldValidationError`` if the (non-``None``) value contains
        anything other than letters, digits, hyphens, or underscores.
        """
        value = super().validate(value)
        if value is None:
            return None
        if not self._SLUG_RE.match(value):
            raise FieldValidationError(
                self.name, f"Invalid slug '{value}'. Only letters, numbers, hyphens, and underscores allowed."
            )
        return value


class EmailField(CharField):
    """Email address field -- a ``CharField`` validated against an RFC-5322-ish regex.

    Args:
        max_length: Defaults to 254 (the maximum valid email length per
            RFC 5321/5322), vs. 255 for plain ``CharField``.

    Valid addresses are lowercased on validation, so ``"User@Example.com"``
    and ``"user@example.com"`` end up stored identically -- pair with
    ``unique=True`` to get case-insensitive uniqueness without a
    dialect-specific ``CITEXT``/collation (see ``CIEmailField`` for the
    alternative approach on PostgreSQL).
    """

    _field_type = "EMAIL"
    _EMAIL_RE = re.compile(
        r"^[a-zA-Z0-9.!#$%&\'*+/=?^_`{|}~-]+@"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
    )

    def __init__(
        self,
        *,
        max_length: int = 254,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        super().__init__(max_length=max_length, **kwargs)

    def validate(self, value: Any) -> Any:
        """Run ``CharField`` validation, check the address against the email regex, and lowercase the result.

        Raises ``FieldValidationError`` if the (non-``None``) value doesn't
        look like a valid email address.
        """
        value = super().validate(value)
        if value is None:
            return None
        if not self._EMAIL_RE.match(value):
            raise FieldValidationError(self.name, f"Invalid email address: '{value}'")
        return value.lower()


class URLField(CharField):
    """URL field -- a ``CharField`` validated as an ``http(s)://`` URL.

    Args:
        max_length: Defaults to 200 (vs. 255 for plain ``CharField``).

    Only ``http://`` and ``https://`` schemes are accepted (see
    ``_URL_RE``) -- other schemes (``ftp://``, ``mailto:``, relative paths)
    are rejected.
    """

    _field_type = "URL"
    _URL_RE = re.compile(
        r"^https?://"
        r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)*"
        r"[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
        r"(?::\d+)?"
        r"(?:/[^\s]*)?$"
    )

    def __init__(
        self,
        *,
        max_length: int = 200,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        super().__init__(max_length=max_length, **kwargs)

    def validate(self, value: Any) -> Any:
        """Run ``CharField`` validation, then require the value to match ``^https?://...``.

        Raises ``FieldValidationError`` if the (non-``None``) value isn't a
        well-formed ``http``/``https`` URL.
        """
        value = super().validate(value)
        if value is None:
            return None
        if not self._URL_RE.match(value):
            raise FieldValidationError(self.name, f"Invalid URL: '{value}'")
        return value


class UUIDField(Field[uuid.UUID]):
    """UUID field -- stored as ``VARCHAR(36)`` (native ``UUID`` on PostgreSQL).

    Args:
        auto: When ``True``, sets ``default=uuid.uuid4`` (unless a default
            was already supplied), so every new instance gets a fresh
            random UUID without the caller assigning one explicitly.

    Example::

        class Session(Model):
            id = UUIDField(auto=True, primary_key=True)
    """

    _field_type = "UUID"
    _python_type = uuid.UUID

    def __init__(
        self,
        *,
        auto: bool = False,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        self.auto = auto
        if auto:
            kwargs.setdefault("default", uuid.uuid4)
        super().__init__(**kwargs)

    def validate(self, value: Any) -> Any:
        """Coerce ``str``/``uuid.UUID`` input to ``uuid.UUID``.

        An empty/whitespace-only string is treated as ``None`` before the
        base null/blank check runs. Raises ``FieldValidationError`` if a
        string isn't a parseable UUID, or if the value is neither a string
        nor a ``UUID``.
        """
        if isinstance(value, str) and value.strip() == "":
            value = None
        value = super().validate(value)
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        if isinstance(value, str):
            try:
                return uuid.UUID(value)
            except ValueError:
                raise FieldValidationError(self.name, f"Invalid UUID: '{value}'")
        raise FieldValidationError(self.name, f"Expected UUID, got {type(value).__name__}")

    def to_python(self, value: Any) -> Any:
        """Convert a raw DB value (string or already a ``UUID``) to ``uuid.UUID``; blank strings become ``None``."""
        if value is None:
            return None
        if isinstance(value, uuid.UUID):
            return value
        if isinstance(value, str) and value.strip() == "":
            return None
        return uuid.UUID(str(value))

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Serialize the ``UUID`` to its canonical hyphenated ``str`` form for storage."""
        if value is None:
            return None
        return str(value)

    def sql_type(self, dialect: str = "sqlite") -> str:
        """Native ``UUID`` on PostgreSQL, ``VARCHAR2(36)`` on Oracle, ``VARCHAR(36)`` elsewhere."""
        if dialect == "postgresql":
            return "UUID"
        if dialect == "oracle":
            return "VARCHAR2(36)"
        return "VARCHAR(36)"


class FilePathField(CharField):
    """File system path field -- a ``CharField`` for storing a path, with metadata about what it should point to.

    Args:
        path: Base directory the field's choices/browsing should be
            restricted to (informational -- not enforced by ``validate()``,
            which is inherited unchanged from ``CharField``).
        match: Optional regex filename filter (informational, same caveat).
        recursive: Whether subdirectories of ``path`` should be included
            (informational, same caveat).
        allow_files: Whether plain files are valid choices (informational).
        allow_folders: Whether directories are valid choices (informational).
        max_length: Defaults to 100 (vs. 255 for plain ``CharField``).

    These extra constructor arguments describe intended usage (e.g. for
    admin-UI file browsers or codegen) but do not themselves change
    ``validate``/``to_db``/``sql_type`` behavior beyond what ``CharField``
    already does -- this field does not touch the filesystem.
    """

    _field_type = "FILEPATH"

    def __init__(
        self,
        *,
        path: str = "",
        match: str | None = None,
        recursive: bool = False,
        allow_files: bool = True,
        allow_folders: bool = False,
        max_length: int = 100,
        **kwargs,
    ):
        self.path = path
        self.match = match
        self.recursive = recursive
        self.allow_files = allow_files
        self.allow_folders = allow_folders
        super().__init__(max_length=max_length, **kwargs)


# ═══════════════════════════════════════════════════════════════════════════════
# DATE & TIME FIELDS
# ═══════════════════════════════════════════════════════════════════════════════


class DateField(Field[datetime.date]):
    """Date field (year, month, day), stored as ``DATE``.

    Args:
        auto_now: When ``True``, ``pre_save()`` overwrites the field with
            today's date on *every* save (create and update) -- e.g. a
            "last modified" date. Implies ``blank=True`` (the value is
            auto-populated, so it shouldn't be required at validation
            time).
        auto_now_add: When ``True``, ``pre_save()`` sets today's date only
            on the *first* save (``is_create=True``) and leaves the field
            alone afterward -- e.g. a "created" date. Also implies
            ``blank=True``, and defaults ``default`` to
            ``datetime.date.today`` so an in-memory instance has a sensible
            value even before it's persisted.

    Example::

        class Event(Model):
            event_date = DateField()
            created = DateField(auto_now_add=True)
    """

    _field_type = "DATE"
    _python_type = datetime.date

    def __init__(
        self,
        *,
        auto_now: bool = False,
        auto_now_add: bool = False,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
        # auto_now and auto_now_add fields should be blank=True (auto-populated)
        if auto_now or auto_now_add:
            kwargs.setdefault("blank", True)
        if auto_now_add:
            kwargs.setdefault("default", datetime.date.today)
        super().__init__(**kwargs)

    def validate(self, value: Any) -> Any:
        """Coerce ``str``/``datetime``/``date`` input to ``datetime.date``.

        A ``datetime.datetime`` is truncated to its ``.date()``; an
        empty/whitespace-only string is treated as ``None``; a non-empty
        string is parsed with ``date.fromisoformat``. Raises
        ``FieldValidationError`` for an unparseable string or any other
        type.
        """
        if isinstance(value, str) and value.strip() == "":
            value = None
        value = super().validate(value)
        if value is None:
            return None
        if isinstance(value, datetime.datetime):
            return value.date()
        if isinstance(value, datetime.date):
            return value
        if isinstance(value, str):
            try:
                return datetime.date.fromisoformat(value)
            except ValueError:
                raise FieldValidationError(self.name, f"Invalid date format: '{value}'")
        raise FieldValidationError(self.name, f"Expected date, got {type(value).__name__}")

    def to_python(self, value: Any) -> Any:
        """Parse a raw DB value (ISO-8601 string or already a ``date``) into ``datetime.date``; blank strings become ``None``."""
        if value is None:
            return None
        if isinstance(value, datetime.date):
            return value
        if isinstance(value, str):
            if value.strip() == "":
                return None
            return datetime.date.fromisoformat(value)
        return value

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Serialize for storage: ISO-8601 ``str`` on SQLite, native ``date`` object on other dialects (driver-native)."""
        if value is None:
            return None
        if isinstance(value, datetime.date):
            # PostgreSQL/MySQL/Oracle drivers expect native datetime objects;
            # SQLite stores dates as ISO-8601 text.
            if dialect == "sqlite":
                return value.isoformat()
            return value
        return str(value)

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``DATE`` on every supported dialect."""
        return "DATE"

    def pre_save(self, instance: Any, is_create: bool) -> Any:
        """Compute the value to write on save: today's date for ``auto_now``, or for ``auto_now_add`` on create only.

        Otherwise returns the field's current value on ``instance``
        unchanged. Called by the model's save pipeline immediately before
        the row is written -- not part of ``validate()``/``to_db()``.
        """
        if self.auto_now:
            return datetime.date.today()
        if self.auto_now_add and is_create:
            return datetime.date.today()
        return getattr(instance, self.attr_name, None)


class TimeField(Field[datetime.time]):
    """Time field (hour, minute, second, microsecond), stored as ``TIME``.

    Args:
        auto_now: When ``True``, ``pre_save()`` overwrites the field with
            the current UTC time on every save. Implies ``blank=True``.
        auto_now_add: When ``True``, ``pre_save()`` sets the current UTC
            time only on the first save (``is_create=True``). Also implies
            ``blank=True``.

    Unlike ``DateField``/``DateTimeField``, ``auto_now_add`` here does not
    set a ``default=...`` -- an in-memory pre-save instance simply has no
    value until ``pre_save()`` runs.
    """

    _field_type = "TIME"
    _python_type = datetime.time

    def __init__(
        self,
        *,
        auto_now: bool = False,
        auto_now_add: bool = False,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
        # auto_now and auto_now_add fields should be blank=True (auto-populated)
        if auto_now or auto_now_add:
            kwargs.setdefault("blank", True)
        super().__init__(**kwargs)

    def validate(self, value: Any) -> Any:
        """Coerce ``str``/``time`` input to ``datetime.time``.

        An empty/whitespace-only string is treated as ``None``; a
        non-empty string is parsed with ``time.fromisoformat``. Raises
        ``FieldValidationError`` for an unparseable string or any other
        type.
        """
        if isinstance(value, str) and value.strip() == "":
            value = None
        value = super().validate(value)
        if value is None:
            return None
        if isinstance(value, datetime.time):
            return value
        if isinstance(value, str):
            try:
                return datetime.time.fromisoformat(value)
            except ValueError:
                raise FieldValidationError(self.name, f"Invalid time format: '{value}'")
        raise FieldValidationError(self.name, f"Expected time, got {type(value).__name__}")

    def to_python(self, value: Any) -> Any:
        """Parse a raw DB value (ISO-8601 string or already a ``time``) into ``datetime.time``; blank strings become ``None``."""
        if value is None:
            return None
        if isinstance(value, datetime.time):
            return value
        if isinstance(value, str):
            if value.strip() == "":
                return None
            return datetime.time.fromisoformat(value)
        return value

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Serialize for storage: ISO-8601 ``str`` on SQLite, native ``time`` object on other dialects (driver-native)."""
        if value is None:
            return None
        if isinstance(value, datetime.time):
            # PostgreSQL/MySQL/Oracle drivers expect native time objects;
            # SQLite stores times as ISO-8601 text.
            if dialect == "sqlite":
                return value.isoformat()
            return value
        return str(value)

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``TIME`` on every supported dialect."""
        return "TIME"

    def pre_save(self, instance: Any, is_create: bool) -> Any:
        """Compute the value to write on save: current UTC time for ``auto_now``, or for ``auto_now_add`` on create only.

        Otherwise returns the field's current value on ``instance``
        unchanged.
        """
        if self.auto_now:
            return datetime.datetime.now(datetime.timezone.utc).time()
        if self.auto_now_add and is_create:
            return datetime.datetime.now(datetime.timezone.utc).time()
        return getattr(instance, self.attr_name, None)


class DateTimeField(Field[datetime.datetime]):
    """DateTime field with timezone support, stored as ``TIMESTAMP`` (``TIMESTAMP WITH TIME ZONE`` on PostgreSQL/Oracle).

    Args:
        auto_now: When ``True``, ``pre_save()`` overwrites the field with
            the current UTC datetime on every save (e.g. "updated_at").
            Implies ``blank=True``.
        auto_now_add: When ``True``, ``pre_save()`` sets the current UTC
            datetime only on the first save (e.g. "created_at"). Also
            implies ``blank=True``, and -- unlike ``TimeField`` -- defaults
            ``default`` to a callable returning the current UTC time, so an
            in-memory instance already has a timestamp before its first save.

    Example::

        class Post(Model):
            created_at = DateTimeField(auto_now_add=True)
            updated_at = DateTimeField(auto_now=True)
    """

    _field_type = "DATETIME"
    _python_type = datetime.datetime

    def __init__(
        self,
        *,
        auto_now: bool = False,
        auto_now_add: bool = False,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
        # auto_now and auto_now_add fields should be blank=True (auto-populated)
        if auto_now or auto_now_add:
            kwargs["blank"] = True
        if auto_now_add and kwargs.get("default") is UNSET:
            kwargs["default"] = lambda: datetime.datetime.now(datetime.timezone.utc)
        super().__init__(**kwargs)

    def validate(self, value: Any) -> Any:
        """Coerce ``str``/``datetime`` input to ``datetime.datetime``.

        An empty/whitespace-only string is treated as ``None``; a
        non-empty string is parsed with ``datetime.fromisoformat``. Raises
        ``FieldValidationError`` for an unparseable string or any other
        type. Does not itself enforce timezone-awareness -- both naive and
        aware datetimes pass validation (see ``to_db`` for where naive
        values are handled for PostgreSQL).
        """
        if isinstance(value, str) and value.strip() == "":
            value = None
        value = super().validate(value)
        if value is None:
            return None
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.datetime.fromisoformat(value)
            except ValueError:
                raise FieldValidationError(self.name, f"Invalid datetime format: '{value}'")
        raise FieldValidationError(self.name, f"Expected datetime, got {type(value).__name__}")

    def to_python(self, value: Any) -> Any:
        """Parse a raw DB value (ISO-8601 string or already a ``datetime``) into ``datetime.datetime``; blank strings become ``None``."""
        if value is None:
            return None
        if isinstance(value, datetime.datetime):
            return value
        if isinstance(value, str):
            if value.strip() == "":
                return None
            return datetime.datetime.fromisoformat(value)
        return value

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Serialize for storage, handling dialect-specific timezone quirks.

        SQLite gets an ISO-8601 string. Other dialects get the native
        ``datetime`` object, except that on PostgreSQL a naive (tz-less)
        datetime is assumed to be UTC and given an explicit ``tzinfo``
        before being handed to the driver -- PostgreSQL's
        ``TIMESTAMP WITH TIME ZONE`` columns require tz-aware input, and a
        naive datetime reaching asyncpg would otherwise raise a "can't
        subtract offset-naive and offset-aware datetimes" error deep in the
        driver.
        """
        if value is None:
            return None
        if isinstance(value, datetime.datetime):
            # PostgreSQL/MySQL/Oracle drivers expect native datetime objects;
            # SQLite stores datetimes as ISO-8601 text.
            if dialect == "sqlite":
                return value.isoformat()
            # PostgreSQL TIMESTAMP WITH TIME ZONE requires tz-aware datetimes.
            # If a naive datetime slips through, assume UTC to avoid
            # "can't subtract offset-naive and offset-aware datetimes".
            if dialect == "postgresql" and value.tzinfo is None:
                value = value.replace(tzinfo=datetime.timezone.utc)
            return value
        return str(value)

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``TIMESTAMP WITH TIME ZONE`` on PostgreSQL/Oracle, plain ``TIMESTAMP`` on SQLite/MySQL."""
        if dialect == "postgresql":
            return "TIMESTAMP WITH TIME ZONE"
        if dialect == "oracle":
            return "TIMESTAMP WITH TIME ZONE"
        return "TIMESTAMP"

    def pre_save(self, instance: Any, is_create: bool) -> Any:
        """Compute the value to write on save: current UTC datetime for ``auto_now``, or for ``auto_now_add`` on create only.

        Otherwise returns the field's current value on ``instance``
        unchanged.
        """
        if self.auto_now:
            return datetime.datetime.now(datetime.timezone.utc)
        if self.auto_now_add and is_create:
            return datetime.datetime.now(datetime.timezone.utc)
        return getattr(instance, self.attr_name, None)


class DurationField(Field[datetime.timedelta]):
    """Stores a ``datetime.timedelta`` as an integer count of microseconds (``INTERVAL`` on PostgreSQL/Oracle).

    Caveat: numeric input is interpreted differently by ``validate()`` vs.
    ``to_python()`` -- ``validate()`` treats a raw ``int``/``float`` as
    **seconds** (``timedelta(seconds=value)``, the natural unit when a
    caller assigns a plain number in Python code), while ``to_python()``
    treats one as **microseconds** (``timedelta(microseconds=value)``, the
    unit the DB column actually stores, as produced by ``to_db()``). This
    is intentional given the two call sites' different sources of numeric
    input, not a bug, but worth knowing if you're calling either method
    directly rather than going through the field's normal validate/save or
    read path.
    """

    _field_type = "DURATION"
    _python_type = datetime.timedelta

    def validate(self, value: Any) -> Any:
        """Coerce ``timedelta``/numeric input to ``datetime.timedelta``; a raw number is interpreted as **seconds**.

        Raises ``FieldValidationError`` for any other type.
        """
        value = super().validate(value)
        if value is None:
            return None
        if isinstance(value, datetime.timedelta):
            return value
        if isinstance(value, (int, float)):
            return datetime.timedelta(seconds=value)
        raise FieldValidationError(self.name, f"Expected timedelta, got {type(value).__name__}")

    def to_python(self, value: Any) -> Any:
        """Convert a raw DB value to ``datetime.timedelta``; a raw number is interpreted as **microseconds** (the storage unit)."""
        if value is None:
            return None
        if isinstance(value, datetime.timedelta):
            return value
        if isinstance(value, (int, float)):
            return datetime.timedelta(microseconds=value)
        return value

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Serialize a ``timedelta`` to an integer microsecond count for storage."""
        if value is None:
            return None
        if isinstance(value, datetime.timedelta):
            return int(value.total_seconds() * 1_000_000)
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``INTERVAL`` on PostgreSQL, ``INTERVAL DAY TO SECOND`` on Oracle, ``INTEGER`` (microseconds) elsewhere."""
        if dialect == "postgresql":
            return "INTERVAL"
        if dialect == "oracle":
            return "INTERVAL DAY TO SECOND"
        return "INTEGER"  # microseconds


# ═══════════════════════════════════════════════════════════════════════════════
# BOOLEAN FIELDS
# ═══════════════════════════════════════════════════════════════════════════════


class BooleanField(Field[bool]):
    """Boolean field -- stored as native ``BOOLEAN`` on PostgreSQL, ``INTEGER``/``NUMBER(1)`` (0/1) elsewhere.

    Example::

        class Task(Model):
            is_done = BooleanField(default=False)
    """

    _field_type = "BOOL"
    _python_type = bool

    def validate(self, value: Any) -> Any:
        """Coerce ``bool``/``int``/``str`` input to ``bool``.

        Accepted truthy strings (case-insensitive): ``"true"``, ``"1"``,
        ``"yes"``. Accepted falsy strings: ``"false"``, ``"0"``, ``"no"``.
        Any other string, or any other type, raises
        ``FieldValidationError``. Note this overrides the null-handling in
        ``Field.validate`` directly rather than calling ``super()`` --
        ``blank`` is not consulted here, only ``null``.
        """
        if value is None:
            if self.null:
                return None
            raise FieldValidationError(self.name, "Cannot be null")
        if isinstance(value, bool):
            return value
        if isinstance(value, int):
            return bool(value)
        if isinstance(value, str):
            if value.lower() in ("true", "1", "yes"):
                return True
            if value.lower() in ("false", "0", "no"):
                return False
        raise FieldValidationError(self.name, f"Expected boolean, got {type(value).__name__}")

    def to_python(self, value: Any) -> Any:
        """Coerce any raw DB value to ``bool`` via Python truthiness (``None`` stays ``None``)."""
        if value is None:
            return None
        return bool(value)

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Native ``bool`` for PostgreSQL (asyncpg requires it); ``1``/``0`` for SQLite/MySQL/Oracle."""
        if value is None:
            return None
        # PostgreSQL BOOLEAN columns require native Python bool via asyncpg;
        # SQLite/MySQL/Oracle store bools as INTEGER/NUMBER(1) → use 0/1.
        if dialect == "postgresql":
            return bool(value)
        return 1 if value else 0

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``BOOLEAN`` on PostgreSQL, ``NUMBER(1)`` on Oracle, ``INTEGER`` on SQLite/MySQL."""
        if dialect == "postgresql":
            return "BOOLEAN"
        if dialect == "oracle":
            return "NUMBER(1)"
        return "INTEGER"


# ═══════════════════════════════════════════════════════════════════════════════
# BINARY / SPECIAL DATA FIELDS
# ═══════════════════════════════════════════════════════════════════════════════


class BinaryField(Field[bytes]):
    """Binary data field -- stored as ``BLOB``/``BYTEA``.

    Args:
        max_length: Optional maximum size in bytes; enforced in
            ``validate()`` only (not reflected in ``sql_type()``, which is
            a fixed BLOB-family type regardless).
    """

    _field_type = "BINARY"
    _python_type = bytes

    def __init__(
        self,
        *,
        max_length: int | None = None,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        self.max_length = max_length
        super().__init__(**kwargs)

    def validate(self, value: Any) -> Any:
        """Run base ``Field`` validation, then require the value be a ``bytes``-like object within ``max_length``.

        Accepts ``bytes``, ``bytearray``, or ``memoryview`` and normalizes
        to ``bytes``. Raises ``FieldValidationError`` for any other type,
        or if ``max_length`` is set and exceeded.
        """
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, (bytes, bytearray, memoryview)):
            raise FieldValidationError(self.name, f"Expected bytes, got {type(value).__name__}")
        if self.max_length and len(value) > self.max_length:
            raise FieldValidationError(self.name, f"Max length is {self.max_length} bytes")
        return bytes(value)

    def to_python(self, value: Any) -> Any:
        """Normalize a raw DB value to ``bytes`` (converting a driver-returned ``memoryview`` if needed)."""
        if value is None:
            return None
        if isinstance(value, memoryview):
            return bytes(value)
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``BYTEA`` on PostgreSQL, ``BLOB`` on SQLite/Oracle."""
        if dialect == "postgresql":
            return "BYTEA"
        if dialect == "oracle":
            return "BLOB"
        return "BLOB"


class JSONField(Field[Any]):
    """JSON data field -- native ``JSONB`` on PostgreSQL, ``CLOB``/``TEXT`` (serialized) elsewhere.

    Args:
        encoder: Optional ``json.JSONEncoder`` subclass passed as ``cls=``
            to ``json.dumps`` in both ``validate()`` (serializability check)
            and ``to_db()`` -- use this to support custom types (e.g.
            ``Decimal``, custom dataclasses) in stored JSON.
        decoder: Accepted and stored on the field but not currently
            consulted by ``to_python()``, which always uses plain
            ``json.loads``; reserved for future symmetry with ``encoder``.

    Example::

        class Product(Model):
            metadata = JSONField(default=dict)

        product.metadata = {"color": "red", "sizes": [1, 2, 3]}
    """

    _field_type = "JSON"
    _python_type = dict

    def __init__(
        self,
        *,
        encoder: type | None = None,
        decoder: Callable | None = None,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        self.encoder = encoder
        self.decoder = decoder
        super().__init__(**kwargs)

    def validate(self, value: Any) -> Any:
        """Run base ``Field`` validation, then require the value be JSON-serializable via ``json.dumps``.

        Raises ``FieldValidationError`` if ``json.dumps(value, cls=self.encoder)``
        raises ``TypeError``/``ValueError``. The Python value itself
        (dict/list/whatever) is returned unchanged, not the serialized
        string -- serialization happens later in ``to_db``.
        """
        value = super().validate(value)
        if value is None:
            return None
        # Must be JSON-serializable
        try:
            json.dumps(value, cls=self.encoder)
        except (TypeError, ValueError) as e:
            raise FieldValidationError(self.name, f"Value is not JSON serializable: {e}")
        return value

    def to_python(self, value: Any) -> Any:
        """Parse a raw DB string via ``json.loads``; non-string values (e.g. already-decoded PostgreSQL JSONB) pass through.

        If the stored string isn't valid JSON, it's returned as-is rather
        than raising -- callers that need strict decoding should validate
        separately.
        """
        if value is None:
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
        return value

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Serialize non-string Python values via ``json.dumps(cls=self.encoder)``; an already-``str`` value passes through unchanged."""
        if value is None:
            return None
        if isinstance(value, str):
            return value
        return json.dumps(value, cls=self.encoder)

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``JSONB`` on PostgreSQL (indexable, binary-stored), ``CLOB`` on Oracle, ``TEXT`` on SQLite/MySQL."""
        if dialect == "postgresql":
            return "JSONB"
        if dialect == "oracle":
            return "CLOB"
        return "TEXT"


# ═══════════════════════════════════════════════════════════════════════════════
# RELATIONSHIP FIELDS
# ═══════════════════════════════════════════════════════════════════════════════


class RelationField(Field[Any]):
    """Shared base for ``ForeignKey``, ``OneToOneField``, and ``ManyToManyField``.

    Holds the common ``to`` (related model, class or string
    forward-reference) machinery -- lazy resolution via ``related_model``/
    ``resolve_model``, and PK-field lookup via ``_resolve_pk_field`` -- that
    every relation field needs regardless of cardinality. Not used
    directly; always subclassed. Parametrized as ``Field[Any]`` because the
    concrete relation subclasses each define their own, more specific
    ``__get__``/``__set__`` overloads (typed over ``TModel``, the related
    model) rather than using this class's inherited scalar-value typing.

    Args: same as ``Field`` (``null``, ``blank``, ``default``, etc.) plus:
        to: The related model -- an actual class, or a string
            forward-reference (e.g. ``"User"``) resolved later against the
            model registry, once every model in the app has been loaded.
            String refs are the standard way to avoid circular imports
            across manifest modules, at the cost of static type inference
            (see ``ForeignKey``'s docstring for the annotation workaround).
    """

    def __init__(
        self,
        to: str | type[Model],
        *,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        self.to = to
        self._related_model: type[Model] | None = None
        super().__init__(**kwargs)

    @property
    def related_model(self) -> type[Model] | None:
        """Return the related model class, resolving it lazily and caching the result.

        If ``to`` was given as an actual class, that class is returned
        immediately (and cached in ``_related_model``). If ``to`` was given
        as a string forward-reference, returns whatever was last resolved
        by ``resolve_model``/``_resolve_pk_field`` -- ``None`` if resolution
        hasn't happened yet.
        """
        if self._related_model is not None:
            return self._related_model
        if isinstance(self.to, type):
            self._related_model = self.to
        return self._related_model

    def resolve_model(self, registry: dict[str, type[Model]]) -> None:
        """Resolve a string ``to`` reference against ``registry`` (model name -> class) and cache the result.

        No-op if ``to`` is already an actual class. Called once the full
        set of models is known (all manifests discovered), since a
        forward-referenced model may not exist yet at field-declaration time.
        """
        if isinstance(self.to, str):
            self._related_model = registry.get(self.to)

    def _resolve_pk_field(self) -> Field | None:
        """Return the related model's primary-key ``Field``, resolving the model itself if needed.

        Falls back to ``ModelRegistry.get`` (a global by-name lookup) when
        ``related_model`` hasn't been resolved yet via ``resolve_model`` --
        this lets ``validate``/``to_db``/``sql_type`` on FK-family fields
        work correctly even before the owning module explicitly wires up
        the model registry. Returns ``None`` if the related model can't be
        found by either path.
        """
        model = self.related_model
        if model is None and isinstance(self.to, str):
            from .registry import ModelRegistry

            model = ModelRegistry.get(self.to)
            if model is not None:
                self._related_model = model
        if model is None:
            return None
        return model._fields.get(model._pk_attr)


class ForeignKey(RelationField, Generic[TModel]):
    """
    Many-to-one relationship field.

    Usage:
        class Post(Model):
            author = ForeignKey(User, related_name="posts")

    ``ForeignKey`` is a real generic descriptor: ``TModel`` is inferred from
    the ``to`` constructor argument, so a plain, unannotated declaration like
    the one above resolves ``post.author`` to
    ``User | RelatedNotLoaded[User] | None`` (``aquilia.models.relations.Related``)
    instead of the bare ``ForeignKey`` field object -- but **only when ``to``
    is an actual class reference**, as above. A type checker cannot infer a
    TypeVar from a runtime string, so the equally common cross-module
    pattern that avoids circular imports --

        class Post(Model):
            author = ForeignKey("User", related_name="posts")

    -- leaves ``TModel`` unresolved and ``post.author`` degrades to
    ``Any``. Add an explicit annotation to get the same full typing back:

        class Post(Model):
            author: ForeignKey[User] = ForeignKey("User", related_name="posts")

    ``reveal_type(post.author)`` confirms which case you're in -- the full
    union for a class ref or an already-annotated string ref, ``Any`` for an
    unannotated string ref.

    Reading this attribute on a loaded instance:
        - After ``select_related("author")``, ``prefetch_related("author")``,
          or ``await post.related("author")`` -- a real ``User`` instance
          (or ``None`` for a nullable FK with no value).
        - Otherwise -- a ``RelatedNotLoaded`` sentinel wrapping the raw
          stored id (see ``aquilia.models.relations.RelatedNotLoaded``).
          Cheap operations (``.pk``, ``bool(...)``, ``==``) work directly
          on it without a query; anything else raises
          ``RelatedNotLoadedFault`` with guidance on how to hydrate it.
          This is deliberate, not an oversight: Aquilia's DB layer is
          entirely async and Python's descriptor protocol can't run a
          hidden query synchronously the way Django's
          ``ForwardManyToOneDescriptor`` does on first access, so unlike
          Django there is no implicit lazy query here -- hydration is
          always explicit and awaited.

    Writing this attribute:
        post.author = some_user      # a User instance, None, or a raw pk
        await post.save()

    Assigning an instance of the wrong related model (e.g. a ``Book`` to
    a ``User``-typed FK) raises ``RelatedTypeMismatchFault`` at
    validate()/save() time rather than silently taking its ``.pk``.

    ``ForeignKey`` is a real data descriptor (defines both ``__get__`` and
    ``__set__``): it -- not plain instance-``__dict__`` shadowing -- is what
    mediates every read/write of the attribute now. This is a transparent
    drop-in for every existing ``setattr(instance, name, value)``/
    ``getattr(instance, name)`` call site in the ORM (``Model.__init__``,
    ``Model.from_row()``, ``select_related``/``prefetch_related`` hydration,
    ``Model.related()``'s cache-on-resolve): they all already store/read the
    value at ``instance.__dict__[self.attr_name]``, which is exactly where
    ``__get__``/``__set__`` below keep it -- nothing about *where* the value
    lives changes, only that a descriptor now mediates access to it.
    """

    _field_type = "FK"
    _python_type = int

    def __init__(
        self,
        to: type[TModel] | str,
        *,
        related_name: str | None = None,
        on_delete: str = "CASCADE",
        on_update: str = "CASCADE",
        db_constraint: bool = True,
        **kwargs,
    ):
        """Declare a many-to-one relationship to ``to``.

        Args:
            to: The related model -- a class reference or a string
                forward-reference (see the class docstring for the
                resulting typing difference).
            related_name: Attribute name for the reverse accessor on the
                related model (e.g. ``user.posts`` for
                ``ForeignKey(User, related_name="posts")`` on ``Post``).
                Defaults to the owning model's lowercased name + ``"_set"``
                when not given (handled by the model/registry layer, not
                here).
            on_delete: SQL ``ON DELETE`` action -- accepts Django-style
                constants (``"CASCADE"``, ``"SET_NULL"``, ``"PROTECT"``,
                ``"RESTRICT"``, ``"DO_NOTHING"``, ...) or raw SQL keywords;
                normalized to valid SQL via ``_normalize_fk_action`` when
                the DDL is generated. Stored upper-cased.
            on_update: Same normalization as ``on_delete``, for
                ``ON UPDATE``.
            db_constraint: When ``False``, skip generating an actual SQL
                ``REFERENCES ... ON DELETE ... ON UPDATE ...`` clause --
                useful for logical-only relations or where FK constraints
                are managed outside the framework.
            **kwargs: Forwarded to ``RelationField.__init__``/
                ``Field.__init__`` (``null``, ``unique``, ``default``, ...).
        """
        self.related_name = related_name
        self.on_delete = on_delete.upper()
        self.on_update = on_update.upper()
        self.db_constraint = db_constraint
        super().__init__(to=to, **kwargs)

    def __set_name__(self, owner: type, name: str) -> None:
        """Bind this FK to its attribute name, defaulting the DB column to ``"{name}_id"`` unless ``db_column`` was given.

        This is why an unannotated ``author = ForeignKey(User)`` produces
        an ``author_id`` column rather than ``author`` -- the Python
        attribute stays ``author`` (accessed via the descriptor), but the
        underlying SQL column follows the conventional ``_id`` suffix.
        """
        # FK column name gets _id suffix unless db_column is explicit
        if not self.db_column:
            self.db_column = f"{name}_id"
        super().__set_name__(owner, name)
        self.name = self.db_column

    @overload
    def __get__(self, instance: None, owner: type | None = None) -> ForeignKey[TModel]: ...
    @overload
    def __get__(self, instance: Model, owner: type | None = None) -> Related[TModel]: ...

    def __get__(self, instance: Model | None, owner: type | None = None) -> Any:
        if instance is None:
            # Class-level access (Model.author, introspection, query-builder
            # field resolution) still returns the Field object itself.
            return self
        return instance.__dict__.get(self.attr_name)

    def __set__(self, instance: Model, value: Related[TModel] | TModel) -> None:
        instance.__dict__[self.attr_name] = value

    def _coerce_to_pk(self, value: Any) -> Any:
        """Unwrap a related Model instance (or unloaded relation) to its primary key value.

        Validates the assigned instance's type against the resolved
        ``related_model`` when possible, so assigning the wrong model (e.g.
        a ``Book`` to an ``author`` FK expecting ``User``) fails immediately
        with ``RelatedTypeMismatchFault`` instead of silently taking
        ``.pk`` and only surfacing as a confusing failure elsewhere (or
        never, if the two models' PK types happen to collide). Falls back
        to duck-typing when ``related_model`` is still an unresolved lazy
        string reference -- best-effort, not a regression from before.
        """
        from .relations import RelatedNotLoaded

        if isinstance(value, RelatedNotLoaded):
            return value.pk

        if hasattr(value, "pk") and hasattr(value, "_fields"):
            related_model = self.related_model
            if related_model is not None and not isinstance(value, related_model):
                from ..faults.domains import RelatedTypeMismatchFault

                raise RelatedTypeMismatchFault(
                    field_name=self.name,
                    expected_model=related_model.__name__,
                    got_type=type(value).__name__,
                )
            return value.pk
        return value

    def validate(self, value: Any) -> Any:
        """Unwrap a related instance/``RelatedNotLoaded`` to its pk (via ``_coerce_to_pk``), then validate that pk.

        If the related model's primary-key field can be resolved
        (``_resolve_pk_field``), delegates to *that* field's ``validate``
        so the FK inherits the PK's exact type semantics (e.g. a
        ``UUIDField`` PK gets UUID validation, not integer coercion).
        Falls back to plain ``int`` coercion when the related model/PK
        can't be resolved yet. Raises ``FieldValidationError`` for
        ``None`` on a non-nullable FK, or for a value that can't be
        coerced to the expected PK type.
        """
        if value is None:
            if self.null:
                return None
            raise FieldValidationError(self.name, "Cannot be null")
        value = self._coerce_to_pk(value)
        pk_field = self._resolve_pk_field()
        if pk_field is not None:
            return pk_field.validate(value)
        if not isinstance(value, int):
            try:
                value = int(value)
            except (TypeError, ValueError):
                raise FieldValidationError(self.name, f"Expected integer FK, got {type(value).__name__}")
        return value

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Unwrap to the related pk, then delegate to the related PK field's ``to_db`` when it's resolvable.

        Ensures the stored value has whatever dialect-specific
        representation the *related* model's primary key requires (e.g. a
        UUID PK is serialized to ``str`` the same way a plain ``UUIDField``
        would be), not a hardcoded integer assumption.
        """
        if value is None:
            return None
        value = self._coerce_to_pk(value)
        pk_field = self._resolve_pk_field()
        if pk_field is not None:
            return pk_field.to_db(value, dialect=dialect)
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """Match the related model's primary-key SQL type when resolvable; otherwise fall back to ``NUMBER(10)``/``INTEGER``.

        This is what lets a FK pointing at a UUID-keyed model get a
        ``UUID``/``VARCHAR(36)`` column instead of an ``INTEGER`` one.
        """
        pk_field = self._resolve_pk_field()
        if pk_field is not None:
            return pk_field.sql_type(dialect=dialect)
        if dialect == "oracle":
            return "NUMBER(10)"
        return "INTEGER"

    def sql_column_def(self, dialect: str = "sqlite") -> str:
        """Extend ``Field.sql_column_def`` with a ``REFERENCES ... ON DELETE ... ON UPDATE ...`` clause.

        The clause is only appended when ``db_constraint`` is ``True`` and
        the related model can be resolved; ``on_delete``/``on_update`` are
        normalized to valid SQL via ``_normalize_fk_action`` first. When
        the related model can't be resolved (e.g. an unresolved forward
        string reference) or ``db_constraint=False``, only the base column
        definition is returned with no FK constraint at all.
        """
        base = super().sql_column_def(dialect)
        if self.db_constraint and self.related_model:
            table = getattr(self.related_model, "_table_name", self.related_model.__name__.lower())
            pk = getattr(self.related_model, "_pk_name", "id")
            base += f' REFERENCES "{table}"("{pk}")'
            base += f" ON DELETE {_normalize_fk_action(self.on_delete)}"
            base += f" ON UPDATE {_normalize_fk_action(self.on_update)}"
        return base

    def deconstruct(self) -> dict[str, Any]:
        """Extend ``Field.deconstruct()`` with ``to`` (model name, not the class object), ``on_delete``, and ``related_name``."""
        d = super().deconstruct()
        d["to"] = self.to if isinstance(self.to, str) else self.to.__name__
        d["on_delete"] = self.on_delete
        d["related_name"] = self.related_name
        return d


class OneToOneField(ForeignKey[TModel], Generic[TModel]):
    """
    One-to-one relationship field.

    Usage:
        class Profile(Model):
            user = OneToOneField(User, related_name="profile")

    Forward access follows ForeignKey's RelatedNotLoaded contract exactly
    (including the ``Related[TModel]``/descriptor typing above). Reverse
    access via ``await user.related("profile")`` returns a single instance
    (or ``None``) instead of a list, matching this field's actual 1:1
    cardinality -- unlike a plain ForeignKey's reverse side, which is
    always a list since multiple rows can reference the same target.
    """

    _field_type = "O2O"

    def __init__(
        self,
        to: type[TModel] | str,
        *,
        related_name: str | None = None,
        on_delete: str = "CASCADE",
        on_update: str = "CASCADE",
        db_constraint: bool = True,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = True,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        """Declare a one-to-one relationship to ``to``.

        Identical to ``ForeignKey.__init__`` except ``unique`` defaults to
        ``True`` here (vs. ``False`` for a plain ``ForeignKey``) -- the
        ``UNIQUE`` constraint on the FK column is what actually enforces
        1:1 cardinality at the database level; everything else (``on_delete``,
        ``on_update``, ``db_constraint``, ``related_name``) behaves exactly
        as documented on ``ForeignKey``.
        """
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        super().__init__(
            to=to,
            related_name=related_name,
            on_delete=on_delete,
            on_update=on_update,
            db_constraint=db_constraint,
            **kwargs,
        )


class ManyToManyField(RelationField):
    """
    Many-to-many relationship field.

    Creates a junction table automatically. Not a real column -- virtual:
    ``sql_type``/``sql_column_def`` both return ``""``, since there is no
    column on the owning model's table to define; the relationship lives
    entirely in a separate junction table (see ``junction_table_name``/
    ``junction_columns``).

    Args:
        to: The related model -- a class reference or string
            forward-reference, same as ``RelationField.to``.
        related_name: Attribute name for the reverse accessor on the
            related model.
        through: Optional explicit "through" model for the junction table,
            when extra columns (e.g. a timestamp on the association) are
            needed beyond the two FK columns. When omitted, an implicit
            junction table is assumed.
        through_fields: Optional explicit ``(source_fk_col, target_fk_col)``
            pair identifying which two columns on ``through`` link back to
            the source and target models; only meaningful together with
            ``through``.
        db_table: Optional explicit junction table name, overriding the
            auto-generated one from ``junction_table_name``.

    Usage:
        class Post(Model):
            tags = ManyToManyField("Tag", related_name="posts")
    """

    _field_type = "M2M"

    def __init__(
        self,
        to: str | type[Model],
        *,
        related_name: str | None = None,
        through: str | type[Model] | None = None,
        through_fields: tuple[str, str] | None = None,
        db_table: str | None = None,
        **kwargs,
    ):
        """Declare a many-to-many relationship to ``to``.

        ``null``, ``unique``, and ``db_index`` are silently dropped from
        ``kwargs`` before reaching ``RelationField.__init__`` -- they're
        meaningless for a field that never becomes an actual column.
        """
        self.related_name = related_name
        self.through = through
        self.through_fields = through_fields
        self.db_table = db_table
        # M2M is never an actual column
        kwargs.pop("null", None)
        kwargs.pop("unique", None)
        kwargs.pop("db_index", None)
        super().__init__(to=to, **kwargs)

    def junction_table_name(self, source_model: type[Model]) -> str:
        """Return the junction table name: ``db_table`` if set, otherwise ``"{source_table}_{attr_name}"``.

        E.g. for ``Post.tags = ManyToManyField("Tag")``, this yields
        ``"post_tags"`` (assuming ``Post``'s table name is ``"post"``).
        """
        if self.db_table:
            return self.db_table
        source = getattr(source_model, "_table_name", source_model.__name__.lower())
        target = self.to if isinstance(self.to, str) else self.to.__name__
        target = target.lower()
        return f"{source}_{self.attr_name}"

    def junction_columns(self, source_model: type[Model]) -> tuple[str, str]:
        """Return ``(source_fk_column, target_fk_column)`` names for the junction table.

        Uses ``through_fields`` verbatim when given; otherwise defaults to
        ``"{source_model_name}_id"``/``"{target_model_name}_id"``.
        """
        if self.through_fields:
            return self.through_fields
        source_name = source_model.__name__.lower()
        target_name = self.to if isinstance(self.to, str) else self.to.__name__
        target_name = target_name.lower()
        return (f"{source_name}_id", f"{target_name}_id")

    def sql_type(self, dialect: str = "sqlite") -> str:
        """Always ``""`` -- a M2M field is never a real column on the owning table."""
        return ""  # Not a real column

    def sql_column_def(self, dialect: str = "sqlite") -> str:
        """Always ``""`` -- a M2M field is never a real column on the owning table."""
        return ""  # Not a real column

    def deconstruct(self) -> dict[str, Any]:
        """Extend ``Field.deconstruct()`` with ``to``, ``related_name``, and (if set) ``through`` -- all as plain names, not classes."""
        d = super().deconstruct()
        d["to"] = self.to if isinstance(self.to, str) else self.to.__name__
        d["related_name"] = self.related_name
        if self.through:
            d["through"] = self.through if isinstance(self.through, str) else self.through.__name__
        return d


# ═══════════════════════════════════════════════════════════════════════════════
# IP & NETWORK FIELDS
# ═══════════════════════════════════════════════════════════════════════════════


class GenericIPAddressField(Field[str]):
    """IPv4 or IPv6 address field, stored as ``INET`` on PostgreSQL, ``VARCHAR(39)`` elsewhere (39 chars fits any IPv6 form).

    Args:
        protocol: ``"both"`` (default), ``"ipv4"``, or ``"ipv6"`` --
            restricts ``validate()`` to addresses of that family.
        unpack_ipv4: Accepted and stored but not currently consulted by
            ``validate``/``to_python``/``to_db`` -- reserved for
            IPv4-in-IPv6 (``::ffff:0:0/96``) unpacking support.
    """

    _field_type = "IP"
    _python_type = str

    def __init__(
        self,
        *,
        protocol: str = "both",
        unpack_ipv4: bool = False,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        self.protocol = protocol.lower()
        self.unpack_ipv4 = unpack_ipv4
        super().__init__(**kwargs)

    def validate(self, value: Any) -> Any:
        """Parse and normalize the value via ``ipaddress.ip_address``, optionally restricted to ``protocol``.

        Non-string input is stringified first. Note: because
        ``FieldValidationError`` itself subclasses ``ValueError``, the
        ``except ValueError`` below also catches the protocol-mismatch
        errors raised just above it -- so a wrong-family address (e.g. an
        IPv6 literal on a ``protocol="ipv4"`` field) surfaces to the caller
        as the generic ``"Invalid IP address: '...'"`` message rather than
        the more specific ``"Expected IPv4 address"``/``"Expected IPv6
        address"`` text.
        """
        value = super().validate(value)
        if value is None:
            # String-backed field: blank=True, null=False → store "" not NULL.
            if self.blank and not self.null:
                return ""
            return None
        if not isinstance(value, str):
            value = str(value)
        try:
            addr = ipaddress.ip_address(value)
            if self.protocol == "ipv4" and not isinstance(addr, ipaddress.IPv4Address):
                raise FieldValidationError(self.name, "Expected IPv4 address")
            if self.protocol == "ipv6" and not isinstance(addr, ipaddress.IPv6Address):
                raise FieldValidationError(self.name, "Expected IPv6 address")
            return str(addr)
        except ValueError:
            raise FieldValidationError(self.name, f"Invalid IP address: '{value}'")

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Coerce ``None`` to ``""`` when the column is ``NOT NULL`` (``null=False``), then defer to ``Field.to_db``."""
        if value is None and not self.null:
            return ""
        return super().to_db(value, dialect)

    def sql_type(self, dialect: str = "sqlite") -> str:
        """Native ``INET`` on PostgreSQL, ``VARCHAR2(39)`` on Oracle, ``VARCHAR(39)`` elsewhere."""
        if dialect == "postgresql":
            return "INET"
        if dialect == "oracle":
            return "VARCHAR2(39)"
        return "VARCHAR(39)"


# ═══════════════════════════════════════════════════════════════════════════════
# FILE & MEDIA FIELDS
# ═══════════════════════════════════════════════════════════════════════════════


class FileField(CharField):
    """File path/URL field -- a ``CharField`` storing the path/URL to an uploaded file, not the file bytes themselves.

    Args:
        upload_to: A subdirectory path (``str``) or a callable
            ``(instance, filename) -> str`` used by the upload-handling
            layer to decide where to store the file. Purely informational
            at the field level -- ``validate``/``to_db``/``sql_type`` are
            inherited unchanged from ``CharField`` and don't touch the
            filesystem or consult ``upload_to`` themselves; actual file
            storage/move logic lives in the storage subsystem
            (``aquilia/storage/``), not here.
        max_length: Defaults to 100 (vs. 255 for plain ``CharField``).
    """

    _field_type = "FILE"

    def __init__(
        self,
        *,
        upload_to: str | Callable = "",
        max_length: int = 100,
        **kwargs,
    ):
        self.upload_to = upload_to
        super().__init__(max_length=max_length, **kwargs)


class ImageField(FileField):
    """Image file field -- a ``FileField`` that additionally records which sibling fields hold the image's dimensions.

    Args:
        width_field: Name of another field on the same model to be kept in
            sync with the image's width (informational metadata for the
            upload-handling layer -- this field itself does not read image
            files or perform any image-specific validation beyond what
            ``FileField``/``CharField`` already do).
        height_field: Same, for the image's height.
    """

    _field_type = "IMAGE"

    def __init__(
        self,
        *,
        width_field: str | None = None,
        height_field: str | None = None,
        **kwargs,
    ):
        self.width_field = width_field
        self.height_field = height_field
        super().__init__(**kwargs)


# ═══════════════════════════════════════════════════════════════════════════════
# ADVANCED / POSTGRESQL-SPECIFIC FIELDS
# ═══════════════════════════════════════════════════════════════════════════════


class ArrayField(Field[list[Any]]):
    """PostgreSQL array field -- native ``<type>[]`` on PostgreSQL, JSON-encoded ``TEXT`` on other dialects.

    Args:
        base_field: A ``Field`` instance describing the element type (e.g.
            ``IntegerField()`` for an array of ints). Each element is
            validated with ``base_field.validate(item)``, and the
            PostgreSQL column type is derived from
            ``base_field.sql_type(dialect)`` + ``"[]"``.
        size: Optional maximum element count, enforced in ``validate()``
            only (not reflected in the generated SQL type).

    Example::

        class Article(Model):
            tags = ArrayField(CharField(max_length=50), size=10)
    """

    _field_type = "ARRAY"

    def __init__(self, base_field: Field, *, size: int | None = None, **kwargs):
        self.base_field = base_field
        self.size = size
        super().__init__(**kwargs)

    def validate(self, value: Any) -> Any:
        """Require a ``list``/``tuple`` within ``size``, and validate every element with ``base_field.validate``.

        Raises ``FieldValidationError`` if the value isn't a list/tuple,
        exceeds ``size`` (when set), or any element fails the base field's
        own validation.
        """
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, (list, tuple)):
            raise FieldValidationError(self.name, f"Expected list, got {type(value).__name__}")
        if self.size and len(value) > self.size:
            raise FieldValidationError(self.name, f"Max {self.size} elements, got {len(value)}")
        return [self.base_field.validate(item) for item in value]

    def to_python(self, value: Any) -> Any:
        """Parse a raw DB value: a JSON string (the non-PostgreSQL storage form) is decoded; anything else is coerced to ``list``."""
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return list(value)

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Serialize to a JSON string for storage.

        Used as-is for non-PostgreSQL dialects (SQLite/MySQL/Oracle have no
        native array type); on PostgreSQL the actual driver-level array
        encoding is expected to be handled by the adapter layer, not here.
        """
        if value is None:
            return None
        # SQLite: store as JSON
        return json.dumps(value)

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``"{base_field_sql_type}[]"`` on PostgreSQL (e.g. ``"INTEGER[]"``), ``TEXT`` (JSON fallback) elsewhere."""
        if dialect == "postgresql":
            return f"{self.base_field.sql_type(dialect)}[]"
        return "TEXT"  # JSON fallback


class HStoreField(Field[dict[str, "str | None"]]):
    """PostgreSQL ``hstore`` field -- a flat string-to-string(-or-``None``) key/value map, JSON-encoded on other dialects."""

    _field_type = "HSTORE"

    def validate(self, value: Any) -> Any:
        """Require a ``dict`` whose keys are ``str`` and whose values are ``str`` or ``None``.

        Raises ``FieldValidationError`` for a non-dict value, a non-string
        key, or a value that's neither ``str`` nor ``None`` (unlike a
        general ``JSONField``, arbitrary nested structures aren't allowed
        -- ``hstore`` is flat by design).
        """
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, dict):
            raise FieldValidationError(self.name, f"Expected dict, got {type(value).__name__}")
        for k, v in value.items():
            if not isinstance(k, str):
                raise FieldValidationError(self.name, "All keys must be strings")
            if not isinstance(v, (str, type(None))):
                raise FieldValidationError(self.name, "All values must be strings or None")
        return value

    def to_python(self, value: Any) -> Any:
        """Parse a raw DB value: a JSON string (the non-PostgreSQL storage form) is decoded; anything else passes through."""
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return value

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Serialize the dict to a JSON string for storage (the PostgreSQL-native ``hstore`` encoding is handled by the adapter)."""
        if value is None:
            return None
        return json.dumps(value)

    def sql_type(self, dialect: str = "sqlite") -> str:
        """Native ``HSTORE`` on PostgreSQL, ``TEXT`` (JSON fallback) elsewhere."""
        if dialect == "postgresql":
            return "HSTORE"
        return "TEXT"


class RangeField(Field[list[Any]]):
    """Base class for PostgreSQL range fields (``int4range``, ``numrange``, ``daterange``, ...).

    A range value is represented in Python as a plain 2-element
    ``[lower, upper]`` list -- not PostgreSQL's ``psycopg`` ``Range``
    object -- and JSON-encoded for storage on every dialect (subclasses
    only differ in which native PostgreSQL range type ``sql_type`` maps
    to; non-PostgreSQL dialects always fall back to ``TEXT``).
    """

    _field_type = "RANGE"

    def validate(self, value: Any) -> Any:
        """Require a 2-element ``list``/``tuple`` (``[lower, upper]``); does not itself validate element types or ``lower <= upper``."""
        value = super().validate(value)
        if value is None:
            return None
        if not isinstance(value, (list, tuple)) or len(value) != 2:
            raise FieldValidationError(self.name, "Range must be a 2-element [lower, upper]")
        return list(value)

    def to_python(self, value: Any) -> Any:
        """Parse a raw DB value: a JSON string is decoded; anything else is coerced to ``list``."""
        if value is None:
            return None
        if isinstance(value, str):
            return json.loads(value)
        return list(value)

    def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
        """Serialize the ``[lower, upper]`` pair to a JSON string for storage."""
        if value is None:
            return None
        return json.dumps(value)


class IntegerRangeField(RangeField):
    """Range of 32-bit integers -- PostgreSQL ``int4range``."""

    _field_type = "INT4RANGE"

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``INT4RANGE`` on PostgreSQL, ``TEXT`` (JSON fallback) elsewhere."""
        if dialect == "postgresql":
            return "INT4RANGE"
        return "TEXT"


class BigIntegerRangeField(RangeField):
    """Range of 64-bit integers -- PostgreSQL ``int8range``."""

    _field_type = "INT8RANGE"

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``INT8RANGE`` on PostgreSQL, ``TEXT`` (JSON fallback) elsewhere."""
        if dialect == "postgresql":
            return "INT8RANGE"
        return "TEXT"


class DecimalRangeField(RangeField):
    """Range of numeric/decimal values -- PostgreSQL ``numrange``."""

    _field_type = "NUMRANGE"

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``NUMRANGE`` on PostgreSQL, ``TEXT`` (JSON fallback) elsewhere."""
        if dialect == "postgresql":
            return "NUMRANGE"
        return "TEXT"


class DateRangeField(RangeField):
    """Range of dates -- PostgreSQL ``daterange``."""

    _field_type = "DATERANGE"

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``DATERANGE`` on PostgreSQL, ``TEXT`` (JSON fallback) elsewhere."""
        if dialect == "postgresql":
            return "DATERANGE"
        return "TEXT"


class DateTimeRangeField(RangeField):
    """Range of timezone-aware timestamps -- PostgreSQL ``tstzrange``."""

    _field_type = "TSTZRANGE"

    def sql_type(self, dialect: str = "sqlite") -> str:
        """``TSTZRANGE`` on PostgreSQL, ``TEXT`` (JSON fallback) elsewhere."""
        if dialect == "postgresql":
            return "TSTZRANGE"
        return "TEXT"


# Case-insensitive text fields (PostgreSQL CITEXT)


class CICharField(CharField):
    """Case-insensitive CharField (PostgreSQL CITEXT).

    Lower-cases the value in Python at ``validate()`` time on every
    dialect, so equality/uniqueness comparisons are case-insensitive even
    on backends without a native citext type -- native ``CITEXT`` is used
    only as an extra guarantee on PostgreSQL.
    """

    _field_type = "CICHAR"

    def validate(self, value: Any) -> Any:
        """Delegate to ``CharField.validate``, then lower-case the result (``None`` passes through unchanged)."""
        value = super().validate(value)
        if value is not None:
            value = value.lower()
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """Native ``CITEXT`` on PostgreSQL; ``VARCHAR(max_length)`` elsewhere (case-folding is Python-side there)."""
        if dialect == "postgresql":
            return "CITEXT"
        return f"VARCHAR({self.max_length})"


class CIEmailField(EmailField):
    """Case-insensitive EmailField (PostgreSQL CITEXT).

    Inherits ``EmailField``'s format validation as-is; only ``sql_type``
    differs. Note this does NOT lower-case the value in Python the way
    ``CICharField``/``CITextField`` do -- case-insensitivity on
    non-PostgreSQL dialects relies entirely on query-level handling.
    """

    _field_type = "CIEMAIL"

    def sql_type(self, dialect: str = "sqlite") -> str:
        """Native ``CITEXT`` on PostgreSQL; ``VARCHAR(max_length)`` elsewhere."""
        if dialect == "postgresql":
            return "CITEXT"
        return f"VARCHAR({self.max_length})"


class CITextField(TextField):
    """Case-insensitive TextField (PostgreSQL CITEXT).

    Lower-cases the value in Python at ``validate()`` time on every
    dialect, so equality/uniqueness comparisons are case-insensitive even
    on backends without a native citext type.
    """

    _field_type = "CITEXT"

    def validate(self, value: Any) -> Any:
        """Delegate to ``TextField.validate``, then lower-case the result (``None`` passes through unchanged)."""
        value = super().validate(value)
        if value is not None:
            value = value.lower()
        return value

    def sql_type(self, dialect: str = "sqlite") -> str:
        """Native ``CITEXT`` on PostgreSQL; ``TEXT`` elsewhere."""
        if dialect == "postgresql":
            return "CITEXT"
        return "TEXT"


class InetAddressField(GenericIPAddressField):
    """PostgreSQL INET field -- stores IP address with optional netmask."""

    _field_type = "INET"


# ═══════════════════════════════════════════════════════════════════════════════
# META / SPECIAL-PURPOSE FIELDS
# ═══════════════════════════════════════════════════════════════════════════════


class GeneratedField(Field[Any]):
    """
    Database-computed generated column (SQL ``GENERATED ALWAYS AS (...)``).

    The value is never written by the application -- ``editable`` is
    forced to ``False`` in ``__init__`` regardless of what's passed -- it's
    computed by the database from ``expression`` on every read (VIRTUAL)
    or write (STORED), and read back like any other column.

    Args:
        expression: Raw SQL expression the database evaluates to produce
            the column's value (e.g. ``"price * quantity"``). Not
            validated or escaped here -- treat it as trusted DDL, not
            user input.
        output_field: Optional ``Field`` instance describing the
            expression's result type, used only to pick a concrete
            ``sql_type()`` (e.g. ``DecimalField()`` for a numeric
            expression); defaults to a generic ``TEXT`` column when omitted.
        db_persist: ``True`` for ``STORED`` (computed at write time and
            physically stored, so it's directly indexable), ``False`` for
            ``VIRTUAL`` (computed at read time, no storage).

    Example::

        class OrderItem(Model):
            price = DecimalField()
            quantity = IntegerField()
            total = GeneratedField(
                expression="price * quantity",
                output_field=DecimalField(),
            )
    """

    _field_type = "GENERATED"

    def __init__(
        self,
        *,
        expression: str,
        output_field: Field | None = None,
        db_persist: bool = True,
        **kwargs,
    ):
        self.expression = expression
        self.output_field = output_field
        self.db_persist = db_persist
        kwargs["editable"] = False
        super().__init__(**kwargs)

    def sql_type(self, dialect: str = "sqlite") -> str:
        """Delegate to ``output_field.sql_type(dialect)`` when set; otherwise fall back to ``TEXT``."""
        if self.output_field:
            return self.output_field.sql_type(dialect)
        return "TEXT"

    def sql_column_def(self, dialect: str = "sqlite") -> str:
        """Render the full ``"col" TYPE GENERATED ALWAYS AS (expression) STORED|VIRTUAL`` column definition."""
        col_type = self.sql_type(dialect)
        mode = "STORED" if self.db_persist else "VIRTUAL"
        return f'"{self.column_name}" {col_type} GENERATED ALWAYS AS ({self.expression}) {mode}'


class OrderWrt(IntegerField):
    """
    Internal ordering helper field ("order with respect to").

    An integer position column defaulting to ``0`` and indexed by
    default (``db_index=True``), intended for models that need a stable,
    explicit row ordering (e.g. drag-and-drop reorderable lists) that
    isn't captured by any other field. Currently a thin ``IntegerField``
    specialization -- reordering logic itself (renumbering siblings on
    insert/move) is the caller's responsibility, not automated here.
    """

    _field_type = "ORDERWRT"

    def __init__(
        self,
        *,
        null: bool = False,
        blank: bool = False,
        default: Any = UNSET,
        unique: bool = False,
        primary_key: bool = False,
        db_index: bool = False,
        db_column: str | None = None,
        choices: Sequence[tuple[Any, str]] | None = None,
        validators: list[Callable] | None = None,
        help_text: str = "",
        editable: bool = True,
        verbose_name: str | None = None,
    ):
        kwargs = {
            "null": null,
            "blank": blank,
            "default": default,
            "unique": unique,
            "primary_key": primary_key,
            "db_index": db_index,
            "db_column": db_column,
            "choices": choices,
            "validators": validators,
            "help_text": help_text,
            "editable": editable,
            "verbose_name": verbose_name,
        }
        kwargs.setdefault("default", 0)
        kwargs.setdefault("db_index", True)
        super().__init__(**kwargs)


# ═══════════════════════════════════════════════════════════════════════════════
# INDEX / CONSTRAINT HELPERS
# ═══════════════════════════════════════════════════════════════════════════════


class Index:
    """
    Composite index declaration.

    Usage in Meta:
        class Meta:
            indexes = [
                Index(fields=["email", "username"], unique=True),
                Index(fields=["created_at"], name="idx_created"),
            ]
    """

    def __init__(
        self,
        *,
        fields: list[str],
        name: str | None = None,
        unique: bool = False,
    ):
        """Declare an index over ``fields`` (column names, or schema expressions -- see ``sql()``).

        Args:
            fields: Column names to index, in order. Order matters for
                multi-column indexes (matches SQL's leftmost-prefix rule).
            name: Explicit index name; auto-generated as
                ``idx_{table}_{field_names}`` when omitted.
            unique: Emit ``CREATE UNIQUE INDEX`` instead of a plain index.
        """
        self.fields = fields
        self.name = name
        self.unique = unique

    def sql(self, table_name: str, dialect: str = "sqlite") -> str:
        """Render this index as a ``CREATE [UNIQUE] INDEX IF NOT EXISTS ...`` statement for *table_name*.

        Each entry in ``fields`` may be a plain column name (``str``) or a
        schema expression object, which is compiled via
        ``schema_snapshot._compile_schema_expression`` (resolved lazily to
        avoid a circular import) using this index's ``model`` attribute
        (set by the metaclass) for field lookups. MySQL omits
        ``IF NOT EXISTS`` since it doesn't support that clause on
        ``CREATE INDEX``.
        """
        from .schema_snapshot import _compile_schema_expression

        model_cls = getattr(self, "model", None)

        name_parts = []
        for f in self.fields:
            if isinstance(f, str):
                name_parts.append(f)
            else:
                name_parts.append(f"{type(f).__name__.lower()}")

        idx_name = self.name or f"idx_{table_name}_{'_'.join(name_parts)}"
        u = "UNIQUE " if self.unique else ""

        cols = []
        for f in self.fields:
            if isinstance(f, str):
                cols.append(f'"{f}"')
            else:
                cols.append(_compile_schema_expression(f, model_cls, dialect))

        cols_str = ", ".join(cols)
        ine = "" if dialect == "mysql" else " IF NOT EXISTS"
        return f'CREATE {u}INDEX{ine} "{idx_name}" ON "{table_name}" ({cols_str});'


class UniqueConstraint:
    """
    Unique constraint declaration.

    Usage in Meta:
        class Meta:
            constraints = [
                UniqueConstraint(fields=["email", "tenant_id"], name="uq_email_tenant"),
            ]
    """

    def __init__(self, *, fields: list[str], name: str | None = None):
        """Declare a ``UNIQUE (col1, col2, ...)`` table-level constraint over *fields*.

        Args:
            fields: Column names the constraint applies to jointly (the
                combination must be unique, not each column individually).
            name: Explicit constraint name; migration/schema-generation
                code is expected to derive a default when omitted.
        """
        self.fields = fields
        self.name = name

    def deconstruct(self) -> dict[str, Any]:
        """Serialize to a plain dict (``type``, ``fields``, ``name``) for migration-file generation/diffing."""
        return {
            "type": "UniqueConstraint",
            "fields": self.fields,
            "name": self.name,
        }
