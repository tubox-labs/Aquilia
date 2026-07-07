"""
Aquilia Model Fields Package -- split-module field system.

This package re-exports all fields from the original monolithic fields.py
AND adds new field types from sub-modules. Existing imports like
``from aquilia.models.fields import CharField`` continue to work.

New sub-modules:
    base      -- Field base class and core API
    mixins    -- NullableMixin, UniqueMixin, IndexedMixin, ChoiceMixin, EncryptedMixin
    primitives-- IntegerField, FloatField, CharField, etc.
    relation  -- ForeignKey, OneToOneField, ManyToManyField
    file      -- FileField, ImageField with storage hooks
    json_field-- JSONField with schema validation
    composite -- CompositeField, CompositePrimaryKey, CompositeAttribute
    uuid_field-- Enhanced UUIDField
    binary_field-- Enhanced BinaryField
    auto_field-- AutoField, BigAutoField
    enum_field-- EnumField

Map of this package's public surface (what's exported here, and why you'd
reach for it):

- **Base** (``Field``, ``FieldValidationError``, ``Index``,
  ``UniqueConstraint``, ``UNSET``) -- the foundation every field builds on.
  Reach for ``Field`` when writing a brand-new field type or a mixin;
  ``UNSET`` is the sentinel used to distinguish "no default supplied" from
  an explicit ``None`` default.
- **Numeric** (``IntegerField``, ``BigIntegerField``, ``SmallIntegerField``,
  ``PositiveIntegerField``, ``PositiveSmallIntegerField``, ``FloatField``,
  ``DecimalField``, plus auto-incrementing ``AutoField``/``BigAutoField``/
  ``SmallAutoField``) -- standard numeric column types and PK generators.
- **Text** (``CharField``, ``VarcharField``, ``TextField``, ``SlugField``,
  ``EmailField``, ``URLField``, ``UUIDField``, ``FilePathField``, and the
  case-insensitive ``CICharField``/``CIEmailField``/``CITextField``
  variants) -- string-backed columns with built-in format validation.
- **Date/Time** (``DateField``, ``TimeField``, ``DateTimeField``,
  ``DurationField``) -- combine with ``AutoNowMixin`` for auto-updating
  timestamp columns (e.g. ``updated_at``).
- **Boolean** (``BooleanField``).
- **Binary/Special** (``BinaryField``, ``JSONField``) -- raw bytes and
  structured JSON storage.
- **Relationships** (``RelationField``, ``ForeignKey``, ``OneToOneField``,
  ``ManyToManyField``) -- reach for these to model FK/M2M associations
  between models.
- **IP/Network** (``GenericIPAddressField``, ``InetAddressField``).
- **File/Media** (``FileField``, ``ImageField``) -- fields with storage
  backend hooks (see ``aquilia.storage``).
- **PostgreSQL-specific** (``ArrayField``, ``HStoreField``, ``RangeField``
  and its typed variants ``IntegerRangeField``/``BigIntegerRangeField``/
  ``DecimalRangeField``/``DateRangeField``/``DateTimeRangeField``) -- only
  meaningful on a PostgreSQL-backed database.
- **Meta/Special** (``GeneratedField``, ``OrderWrt``) -- computed columns
  and ordering-support columns.
- **Mixins** (``NullableMixin``, ``UniqueMixin``, ``IndexedMixin``,
  ``AutoNowMixin``, ``ChoiceMixin``, ``EncryptedMixin``) -- composable
  behaviors layered onto any ``Field`` subclass via multiple inheritance
  (mixin goes to the left, e.g. ``class X(NullableMixin, CharField)``).
  ``EncryptedMixin`` is security-sensitive -- read its docstring in
  ``mixins.py`` before using it to store real secrets.
- **Composite fields** (``CompositeField``, ``CompositePrimaryKey``,
  ``CompositeAttribute``) -- multi-column logical fields (e.g. composite
  primary keys).
- **Enum** (``EnumField``) -- typed Python ``Enum``-backed column.
- **Validators** (``BaseValidator``, ``ValidationError``, and the concrete
  ``MinValueValidator``/``MaxValueValidator``/``MinLengthValidator``/
  ``MaxLengthValidator``/``RegexValidator``/``EmailValidator``/
  ``URLValidator``/``SlugValidator``/``ProhibitNullCharactersValidator``/
  ``DecimalValidator``/``FileExtensionValidator``/``StepValueValidator``/
  ``RangeValidator``) -- reusable value validators, typically passed via a
  field's ``validators=[...]`` argument.
- **Lookups** (``Lookup`` base class plus ``Exact``/``IExact``/
  ``Contains``/``IContains``/``StartsWith``/``IStartsWith``/``EndsWith``/
  ``IEndsWith``/``In``/``Gt``/``Gte``/``Lt``/``Lte``/``IsNull``/``Range``/
  ``Regex``/``IRegex``, plus ``register_lookup``/``resolve_lookup``/
  ``lookup_registry``) -- the ``field__lookup=value`` query-filter system;
  see ``lookups.py`` for the full extensible registry, including lookups
  not re-exported here (``Date``, ``Year``, ``Month``, ``Day``) which are
  available directly from ``aquilia.models.fields.lookups``.
"""

# ── Re-export everything from the original monolithic fields.py ──────────────
# This keeps backward compatibility: ``from aquilia.models.fields import X``
# works whether X lives in the old fields.py or new sub-modules.

from ..fields_module import (
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
    PositiveIntegerField,
    PositiveSmallIntegerField,
    RangeField,
    # Relationships
    RelationField,
    SlugField,
    SmallAutoField,
    SmallIntegerField,
    TextField,
    TimeField,
    UniqueConstraint,
    URLField,
    UUIDField,
    VarcharField,
    _Unset,
)
from .composite import (
    CompositeAttribute,
    CompositeField,
    CompositePrimaryKey,
)
from .enum_field import EnumField
from .lookups import (
    Contains,
    EndsWith,
    Exact,
    Gt,
    Gte,
    IContains,
    IEndsWith,
    IExact,
    In,
    IRegex,
    IsNull,
    IStartsWith,
    Lookup,
    Lt,
    Lte,
    Range,
    Regex,
    StartsWith,
    lookup_registry,
    register_lookup,
    resolve_lookup,
)

# ── New sub-module exports ───────────────────────────────────────────────────
from .mixins import (
    AutoNowMixin,
    ChoiceMixin,
    EncryptedMixin,
    IndexedMixin,
    NullableMixin,
    UniqueMixin,
)
from .validators import (
    BaseValidator,
    DecimalValidator,
    EmailValidator,
    FileExtensionValidator,
    MaxLengthValidator,
    MaxValueValidator,
    MinLengthValidator,
    MinValueValidator,
    ProhibitNullCharactersValidator,
    RangeValidator,
    RegexValidator,
    SlugValidator,
    StepValueValidator,
    URLValidator,
    ValidationError,
)

__all__ = [
    # Base
    "Field",
    "FieldValidationError",
    "Index",
    "UniqueConstraint",
    "UNSET",
    # Numeric
    "AutoField",
    "BigAutoField",
    "SmallAutoField",
    "IntegerField",
    "BigIntegerField",
    "SmallIntegerField",
    "PositiveIntegerField",
    "PositiveSmallIntegerField",
    "FloatField",
    "DecimalField",
    # Text
    "CharField",
    "VarcharField",
    "TextField",
    "SlugField",
    "EmailField",
    "URLField",
    "UUIDField",
    "FilePathField",
    # Date/Time
    "DateField",
    "TimeField",
    "DateTimeField",
    "DurationField",
    # Boolean
    "BooleanField",
    # Binary/Special
    "BinaryField",
    "JSONField",
    # Relationships
    "RelationField",
    "ForeignKey",
    "OneToOneField",
    "ManyToManyField",
    # IP/Network
    "GenericIPAddressField",
    "InetAddressField",
    # File/Media
    "FileField",
    "ImageField",
    # PostgreSQL
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
    # Meta/Special
    "GeneratedField",
    "OrderWrt",
    # New sub-module exports
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
    # Validators
    "BaseValidator",
    "ValidationError",
    "MinValueValidator",
    "MaxValueValidator",
    "MinLengthValidator",
    "MaxLengthValidator",
    "RegexValidator",
    "EmailValidator",
    "URLValidator",
    "SlugValidator",
    "ProhibitNullCharactersValidator",
    "DecimalValidator",
    "FileExtensionValidator",
    "StepValueValidator",
    "RangeValidator",
    # Lookups
    "Lookup",
    "Exact",
    "IExact",
    "Contains",
    "IContains",
    "StartsWith",
    "IStartsWith",
    "EndsWith",
    "IEndsWith",
    "In",
    "Gt",
    "Gte",
    "Lt",
    "Lte",
    "IsNull",
    "Range",
    "Regex",
    "IRegex",
    "register_lookup",
    "resolve_lookup",
    "lookup_registry",
]
