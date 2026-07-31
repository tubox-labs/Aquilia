"""
Aquilia Model System -- Pure Python, production-grade ORM.

Usage:
    from aquilia.models import Model
    from aquilia.models.fields import (
        CharField, IntegerField, DateTimeField, ForeignKey, ManyToManyField,
    )

    class User(Model):
        table = "users"

        name = CharField(max_length=150)
        email = EmailField(unique=True)
        active = BooleanField(default=True)
        created_at = DateTimeField(auto_now_add=True)

        class Meta:
            ordering = ["-created_at"]

Public API:
    - Model: Base class for all models
    - Fields: All field types (Char, Integer, DateTime, FK, M2M, etc.)
    - Q: Query builder
    - ModelRegistry: Global model registry
    - Migrations: MigrationEngine, Operation, ProjectState
    - Database: AquiliaDatabase (re-exported from aquilia.db)
    - Faults: ModelNotFoundFault, QueryFault, etc.

Map of this package's public surface (grouped by why you'd reach for it):

- **Core model system** (``Model``, ``ModelMeta``, ``ModelRegistry``,
  ``Options``, ``Q``) -- ``Model`` is the base class every model subclasses;
  ``Q`` builds compound filter expressions (``Q(a=1) | Q(b=2)``);
  ``ModelRegistry`` looks up model classes by table/name at runtime.
  ``NewModelRegistry``/``QueryBuilder``/``QNode``/``QCombination``/
  ``Prefetch``/``EnhancedOptions`` are newer, parallel split-module
  implementations (from ``registry.py``/``query.py``/``options.py``) kept
  available under aliased names alongside the originals for incremental
  migration -- prefer the unaliased ``Model``/``Q``/``ModelRegistry``/
  ``Options`` unless you specifically need the newer implementation.
- **Manager** (``Manager``, ``BaseManager``, ``QuerySet``) -- the
  ``objects``-style query interface attached to each ``Model``.
- **Fields** -- the full field type catalogue (numeric, text, date/time,
  boolean, binary/JSON, relationship, IP/network, file/media, PostgreSQL,
  meta/special) plus **mixins & composites**
  (``NullableMixin``/``UniqueMixin``/``IndexedMixin``/``AutoNowMixin``/
  ``ChoiceMixin``/``EncryptedMixin``, ``CompositeField``/
  ``CompositePrimaryKey``/``CompositeAttribute``, ``EnumField``). See
  ``aquilia.models.fields`` for the detailed map; everything there is
  re-exported here too so ``from aquilia.models import CharField`` works
  without a separate import. ``EncryptedMixin`` is security-sensitive --
  see its docstring in ``fields/mixins.py`` before relying on it.
- **Expressions & Aggregates** (``F``, ``Value``, ``RawSQL``, ``Case``/
  ``When``, ``Subquery``/``Exists``/``OuterRef``, string/math/date
  functions like ``Concat``/``Upper``/``Round``/``Now``, and aggregates
  ``Sum``/``Avg``/``Count``/``Max``/``Min``/``StdDev``/``Variance``/
  ``ArrayAgg``/``StringAgg``/``GroupConcat``/``BoolAnd``/``BoolOr``) --
  reach for these to express computed values, conditionals, and
  aggregations directly in queries instead of pulling data into Python.
- **Signals** (``Signal``, ``pre_save``/``post_save``, ``pre_delete``/
  ``post_delete``, ``pre_init``/``post_init``, ``m2m_changed``,
  ``pre_migrate``/``post_migrate``, ``receiver``, ``class_prepared``) --
  hook into model/migration lifecycle events.
- **Transactions** (``atomic``, ``Atomic``, ``TransactionManager``) --
  wrap a block of ORM calls in a real database transaction.
- **Deletion behavior** (``CASCADE``, ``SET_NULL``, ``PROTECT``,
  ``SET_DEFAULT``, ``DO_NOTHING``, ``RESTRICT``, ``SET``,
  ``OnDeleteHandler``, ``ProtectedError``, ``RestrictedError``) -- the
  ``on_delete`` constants/handlers used by ``ForeignKey``/``OneToOneField``.
- **Enums / Choices** (``Choices``, ``TextChoices``, ``IntegerChoices``) --
  base classes for declaring a field's ``choices`` as a Python enum.
- **SQL Builder** (``SQLBuilder``, ``InsertBuilder``, ``UpdateBuilder``,
  ``DeleteBuilder``, ``CreateTableBuilder``) -- lower-level SQL
  construction, mostly used internally by the manager/migration layers.
- **Constraints & Indexes** (``CheckConstraint``, ``ExclusionConstraint``,
  ``Deferrable``, ``GinIndex``, ``GistIndex``, ``BrinIndex``,
  ``HashIndex``, ``FunctionalIndex``) -- declared on a model's ``Meta`` to
  add database-level constraints and specialized index types.
- **Migrations** (``MigrationEngine``, ``MigrationGraph``, ``MigrationNode``,
  ``MigrationStatus``, ``Operation``, ``ProjectState``) -- the migration
  system: ``MigrationEngine`` generates, plans, and applies migrations;
  ``ProjectState`` is the schema state they transform. Operations and schema
  state live in :mod:`aquilia.models.migration`, which generated migration
  files import directly. ``check_db_ready``/``DatabaseNotReadyError`` guard
  startup against an unmigrated database.
- **Faults** (``ModelFault``, ``ModelNotFoundFault``,
  ``ModelRegistrationFault``, ``MigrationFault``,
  ``MigrationConflictFault``, ``QueryFault``, ``DatabaseConnectionFault``,
  ``SchemaFault``) -- re-exported from ``aquilia.faults.domains`` for
  convenience so ORM callers can catch/raise them without a second import.
"""

# ── New Pure Python Model System ─────────────────────────────────────────────

# Re-export model-specific faults for convenience
from ..faults.domains import (
    DatabaseConnectionFault,
    ManagerInstanceAccessFault,
    MigrationConflictFault,
    MigrationFault,
    ModelFault,
    ModelNotFoundFault,
    ModelRegistrationFault,
    QueryFault,
    SchemaFault,
)
from .aggregate import (
    Aggregate,
    ArrayAgg,
    Avg,
    BoolAnd,
    BoolOr,
    Count,
    GroupConcat,
    Max,
    Min,
    StdDev,
    StringAgg,
    Sum,
    Variance,
)
from .base import (
    Model,
    ModelMeta,
    ModelRegistry,
    Options,
    Q,
)

# ── Constraints & Indexes ────────────────────────────────────────────────────
from .constraint import CheckConstraint, Deferrable, ExclusionConstraint
from .cte import CTE, CTECol, CTEReference, RecursiveCTE

# ── Deletion constants ───────────────────────────────────────────────────────
from .deletion import (
    CASCADE,
    DO_NOTHING,
    PROTECT,
    RESTRICT,
    SET,
    SET_DEFAULT,
    SET_NULL,
    OnDeleteHandler,
    ProtectedError,
    RestrictedError,
    normalize_on_delete,
)

# ── Enums / Choices ──────────────────────────────────────────────────────────
from .enums import Choices, IntegerChoices, TextChoices
from .expression import (
    Abs,
    Case,
    Cast,
    Coalesce,
    Col,
    CombinedExpression,
    Concat,
    Exists,
    Expression,
    ExpressionWrapper,
    F,
    Func,
    Greatest,
    Least,
    Left,
    Length,
    Lower,
    LTrim,
    Now,
    NullIf,
    # String/math/date functions
    OrderBy,
    OuterRef,
    Power,
    RawSQL,
    Replace,
    Right,
    Round,
    RTrim,
    Star,
    Subquery,
    Substr,
    Trim,
    Upper,
    Value,
    When,
)

# New sub-module exports
from .fields import (
    AutoNowMixin,
    ChoiceMixin,
    CompositeAttribute,
    CompositeField,
    CompositePrimaryKey,
    EncryptedField,
    EncryptedMixin,
    EnumField,
    IndexedMixin,
    NullableMixin,
    UniqueMixin,
)
from .fields_module import (
    UNSET,
    # PostgreSQL
    ArrayField,
    # Numeric
    AutoField,
    BigAutoField,
    BigIntegerField,
    BigIntegerRangeField,
    # Binary/Special
    BinaryField,
    # Boolean
    BooleanField,
    # Text
    CharField,
    CICharField,
    CIEmailField,
    CITextField,
    # Date/Time
    DateField,
    DateRangeField,
    DateTimeField,
    DateTimeRangeField,
    DecimalField,
    DecimalRangeField,
    DurationField,
    EmailField,
    # Base
    Field,
    FieldValidationError,
    # File/Media
    FileField,
    FilePathField,
    FloatField,
    # Relationships
    ForeignKey,
    # Meta/Special
    GeneratedField,
    GenericForeignKey,
    # IP/Network
    GenericIPAddressField,
    GeometryField,
    HStoreField,
    ImageField,
    Index,
    InetAddressField,
    IntegerField,
    IntegerRangeField,
    JSONField,
    ManyToManyField,
    MoneyField,
    OneToOneField,
    OrderWrt,
    PointField,
    PositiveBigIntegerField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    RangeField,
    RelationField,
    SlugField,
    SmallAutoField,
    SmallIntegerField,
    TextField,
    TimeField,
    UniqueConstraint,
    URLField,
    UUIDField,
)
from .index import (
    BrinIndex,
    FunctionalIndex,
    GinIndex,
    GistIndex,
    HashIndex,
)
from .manager import BaseManager, Manager, QuerySet

# ── Migrations ───────────────────────────────────────────────────────────────
from .migration import (
    MigrationEngine,
    MigrationGraph,
    MigrationNode,
    MigrationStatus,
    Operation,
    ProjectState,
)
from .options import Options as EnhancedOptions
from .query import Prefetch, QCombination, QNode
from .query import Q as QueryBuilder

# New split-module exports (available but not replacing base.py)
from .registry import ModelRegistry as NewModelRegistry
from .relations import Related, RelatedNotLoaded

# ── Signals ──────────────────────────────────────────────────────────────────
from .signals import (
    Signal,
    class_prepared,
    m2m_changed,
    post_delete,
    post_init,
    post_migrate,
    post_save,
    pre_delete,
    pre_init,
    pre_migrate,
    pre_save,
    receiver,
)

# ── SQL Builder ──────────────────────────────────────────────────────────────
from .sql_builder import (
    AlterTableBuilder,
    CreateTableBuilder,
    DeleteBuilder,
    InsertBuilder,
    SQLBuilder,
    UpdateBuilder,
    UpsertBuilder,
)
from .startup_guard import (
    DatabaseNotReadyError,
    check_db_ready,
)

# ── Transactions ─────────────────────────────────────────────────────────────
from .transactions import Atomic, TransactionManager, atomic

# ── Expression / Aggregate system ────────────────────────────────────────────
from .window import (
    DenseRank,
    FirstValue,
    FrameBound,
    FrameType,
    Lag,
    LastValue,
    Lead,
    NthValue,
    Ntile,
    Rank,
    RowNumber,
    Window,
    WindowFrame,
    WindowFunction,
)

__all__ = [
    "Window",
    "WindowFunction",
    "Rank",
    "DenseRank",
    "RowNumber",
    "Ntile",
    "Lag",
    "Lead",
    "FirstValue",
    "LastValue",
    "NthValue",
    "FrameType",
    "FrameBound",
    "WindowFrame",
    "CTE",
    "RecursiveCTE",
    "CTEReference",
    "CTECol",
    # ── New Pure Python Model System ─────────────────────────────────
    "Model",
    "ModelMeta",
    "ModelRegistry",
    "Options",
    "Q",
    # New split modules
    "NewModelRegistry",
    "QueryBuilder",
    "QNode",
    "QCombination",
    "Prefetch",
    "EnhancedOptions",
    # Manager
    "Manager",
    "BaseManager",
    "QuerySet",
    # Fields
    "Field",
    "FieldValidationError",
    "Index",
    "UniqueConstraint",
    "UNSET",
    "AutoField",
    "BigAutoField",
    "IntegerField",
    "BigIntegerField",
    "SmallIntegerField",
    "PositiveIntegerField",
    "PositiveSmallIntegerField",
    "PositiveBigIntegerField",
    "FloatField",
    "DecimalField",
    "CharField",
    "TextField",
    "SlugField",
    "EmailField",
    "URLField",
    "UUIDField",
    "FilePathField",
    "DateField",
    "TimeField",
    "DateTimeField",
    "DurationField",
    "BooleanField",
    "BinaryField",
    "JSONField",
    "ForeignKey",
    "OneToOneField",
    "ManyToManyField",
    "RelationField",
    "GenericForeignKey",
    "SmallAutoField",
    "MoneyField",
    "EncryptedField",
    "PointField",
    "GeometryField",
    # Relation type helpers
    "Related",
    "RelatedNotLoaded",
    "GenericIPAddressField",
    "InetAddressField",
    "FileField",
    "ImageField",
    "ArrayField",
    "HStoreField",
    "RangeField",
    "IntegerRangeField",
    "BigIntegerRangeField",
    "DecimalRangeField",
    "DateRangeField",
    "DateTimeRangeField",
    "CICharField",
    "CIEmailField",
    "CITextField",
    "GeneratedField",
    "OrderWrt",
    # Field mixins & composites
    "NullableMixin",
    "UniqueMixin",
    "IndexedMixin",
    "AutoNowMixin",
    "ChoiceMixin",
    "EncryptedMixin",
    "CompositeField",
    "CompositePrimaryKey",
    "CompositeAttribute",
    "EnumField",
    # Expressions & Aggregates
    "Expression",
    "F",
    "Value",
    "RawSQL",
    "Col",
    "Star",
    "CombinedExpression",
    "When",
    "Case",
    "Subquery",
    "Exists",
    "OuterRef",
    "ExpressionWrapper",
    "Func",
    "Cast",
    "Coalesce",
    "Greatest",
    "Least",
    "NullIf",
    # String/math/date functions
    "OrderBy",
    "Length",
    "Upper",
    "Lower",
    "Trim",
    "LTrim",
    "RTrim",
    "Concat",
    "Left",
    "Right",
    "Substr",
    "Replace",
    "Abs",
    "Round",
    "Power",
    "Now",
    "Aggregate",
    "Sum",
    "Avg",
    "Count",
    "Max",
    "Min",
    "StdDev",
    "Variance",
    "ArrayAgg",
    "StringAgg",
    "GroupConcat",
    "BoolAnd",
    "BoolOr",
    # Signals
    "Signal",
    "pre_save",
    "post_save",
    "pre_delete",
    "post_delete",
    "pre_init",
    "post_init",
    "m2m_changed",
    "receiver",
    "class_prepared",
    "pre_migrate",
    "post_migrate",
    # Transactions
    "atomic",
    "Atomic",
    "TransactionManager",
    # Deletion
    "CASCADE",
    "SET_NULL",
    "PROTECT",
    "SET_DEFAULT",
    "DO_NOTHING",
    "RESTRICT",
    "OnDeleteHandler",
    "SET",
    "ProtectedError",
    "RestrictedError",
    # Enums / Choices
    "Choices",
    "TextChoices",
    "IntegerChoices",
    # SQL Builder
    "SQLBuilder",
    "InsertBuilder",
    "UpdateBuilder",
    "DeleteBuilder",
    "CreateTableBuilder",
    # Constraints & Indexes
    "CheckConstraint",
    "ExclusionConstraint",
    "Deferrable",
    "GinIndex",
    "GistIndex",
    "BrinIndex",
    "HashIndex",
    "FunctionalIndex",
    # Migrations
    "MigrationEngine",
    "MigrationGraph",
    "MigrationNode",
    "MigrationStatus",
    "Operation",
    "ProjectState",
    "check_db_ready",
    "DatabaseNotReadyError",
    # Faults (re-exported)
    "ModelFault",
    "ModelNotFoundFault",
    "ModelRegistrationFault",
    "MigrationFault",
    "MigrationConflictFault",
    "QueryFault",
    "DatabaseConnectionFault",
    "SchemaFault",
    "ManagerInstanceAccessFault",
]
