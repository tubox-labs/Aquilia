"""
Aquilia Model System -- Pure Python, production-grade ORM.

The model system has been completely rewritten from the old AMDL DSL
to a pure Pythonic, metaclass-driven architecture.

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
    - Migrations: MigrationRunner, MigrationOps, generate_migration_file
    - Database: AquiliaDatabase (re-exported from aquilia.db)
    - Faults: ModelNotFoundFault, QueryFault, etc.
"""

# ── New Pure Python Model System ─────────────────────────────────────────────

# Re-export model-specific faults for convenience
from ..faults.domains import (
    AMDLParseFault,
    DatabaseConnectionFault,
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

# ── Legacy AMDL compatibility layer ─────────────────────────────────────────
# These are preserved for backward compatibility with existing code that
# imports AMDL types. They still function but are deprecated.
from .ast_nodes import (
    AMDLFile,
    FieldType,
    HookNode,
    IndexNode,
    LinkKind,
    LinkNode,
    MetaNode,
    ModelNode,
    NoteNode,
    SlotNode,
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

# ── Expression / Aggregate system ────────────────────────────────────────────
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
    # IP/Network
    GenericIPAddressField,
    HStoreField,
    ImageField,
    Index,
    InetAddressField,
    IntegerField,
    IntegerRangeField,
    JSONField,
    ManyToManyField,
    OneToOneField,
    OrderWrt,
    PositiveBigIntegerField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    RangeField,
    RelationField,
    SlugField,
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
from .migration_dsl import (
    AddConstraint as DSLAddConstraint,
)
from .migration_dsl import (
    AddField as DSLAddField,
)
from .migration_dsl import (
    AlterField as DSLAlterField,
)

# ── New Migration DSL System ─────────────────────────────────────────────────
from .migration_dsl import (
    C,
    ColumnDef,
    Migration,
    Operation,
    columns,
)
from .migration_dsl import (
    CreateIndex as DSLCreateIndex,
)
from .migration_dsl import (
    CreateModel as DSLCreateModel,
)
from .migration_dsl import (
    DropIndex as DSLDropIndex,
)
from .migration_dsl import (
    DropModel as DSLDropModel,
)
from .migration_dsl import (
    RemoveConstraint as DSLRemoveConstraint,
)
from .migration_dsl import (
    RemoveField as DSLRemoveField,
)
from .migration_dsl import (
    RenameField as DSLRenameField,
)
from .migration_dsl import (
    RenameModel as DSLRenameModel,
)
from .migration_dsl import (
    RunPython as DSLRunPython,
)
from .migration_dsl import (
    RunSQL as DSLRunSQL,
)
from .migration_gen import (
    generate_dsl_migration,
)
from .migration_runner import (
    MigrationRunner as DSLMigrationRunner,
)
from .migration_runner import (
    check_db_exists,
    check_migrations_applied,
)
from .migrations import (
    MigrationInfo,
    MigrationOps,
    MigrationRunner,
    generate_migration_file,
    generate_migration_from_models,
    op,
)
from .options import Options as EnhancedOptions
from .parser import (
    AMDLParseError,
    parse_amdl,
    parse_amdl_directory,
    parse_amdl_file,
)
from .query import Prefetch, QCombination, QNode
from .query import Q as QueryBuilder

# New split-module exports (available but not replacing base.py)
from .registry import ModelRegistry as NewModelRegistry
from .runtime import (
    ModelProxy,
    generate_create_index_sql,
    generate_create_table_sql,
)
from .runtime import (
    ModelRegistry as LegacyModelRegistry,
)
from .runtime import (
    Q as LegacyQ,
)
from .schema_snapshot import (
    ModelDiff,
    SchemaDiff,
    compute_diff,
    create_snapshot,
    diff_to_operations,
    load_snapshot,
    save_snapshot,
)

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

__all__ = [
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
    # ── Legacy AMDL (backward compat) ────────────────────────────────
    "AMDLFile",
    "FieldType",
    "HookNode",
    "IndexNode",
    "LinkKind",
    "LinkNode",
    "MetaNode",
    "ModelNode",
    "NoteNode",
    "SlotNode",
    "AMDLParseError",
    "parse_amdl",
    "parse_amdl_file",
    "parse_amdl_directory",
    "ModelProxy",
    "LegacyModelRegistry",
    "LegacyQ",
    "generate_create_table_sql",
    "generate_create_index_sql",
    # Migrations
    "MigrationOps",
    "MigrationRunner",
    "MigrationInfo",
    "generate_migration_file",
    "generate_migration_from_models",
    "op",
    # New Migration DSL
    "Migration",
    "Operation",
    "DSLCreateModel",
    "DSLDropModel",
    "DSLRenameModel",
    "DSLAddField",
    "DSLRemoveField",
    "DSLAlterField",
    "DSLRenameField",
    "DSLCreateIndex",
    "DSLDropIndex",
    "DSLRunSQL",
    "DSLRunPython",
    "DSLAddConstraint",
    "DSLRemoveConstraint",
    "ColumnDef",
    "columns",
    "C",
    "create_snapshot",
    "save_snapshot",
    "load_snapshot",
    "compute_diff",
    "diff_to_operations",
    "SchemaDiff",
    "ModelDiff",
    "DSLMigrationRunner",
    "check_db_exists",
    "check_migrations_applied",
    "check_db_ready",
    "DatabaseNotReadyError",
    "generate_dsl_migration",
    # Faults (re-exported)
    "ModelFault",
    "AMDLParseFault",
    "ModelNotFoundFault",
    "ModelRegistrationFault",
    "MigrationFault",
    "MigrationConflictFault",
    "QueryFault",
    "DatabaseConnectionFault",
    "SchemaFault",
]
