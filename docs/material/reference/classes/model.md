# Model (ORM)

## Overview

Aquilia's ORM is a pure-Python, async-first, metaclass-driven model system. Models are defined declaratively with field descriptors, and querying uses a chainable, immutable `Q` builder with async terminal methods.

```python
from aquilia.models import Model
from aquilia.models.fields import CharField, IntegerField, DateTimeField, EmailField

class User(Model):
    table = "users"

    name = CharField(max_length=150)
    email = EmailField(unique=True)
    active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            Index(fields=["email", "name"]),
        ]
```

---

## `Model` Base Class

!!! abstract "`aquilia.models.Model`"
    Metaclass: `ModelMeta`

### Class Attributes (set by metaclass)

| Attribute | Type | Description |
|---|---|---|
| `_fields` | `dict[str, Field]` | Field name → Field instance |
| `_m2m_fields` | `dict[str, ManyToManyField]` | M2M field name → Field |
| `_meta` | `Options` | Parsed Meta options |
| `_table_name` | `str` | Database table name |
| `_pk_name` | `str` | Primary key column name |
| `_pk_attr` | `str` | Primary key attribute name |
| `_column_names` | `list[str]` | All column names (excludes M2M) |
| `_attr_names` | `list[str]` | All attribute names (excludes M2M) |
| `_non_m2m_fields` | `list[tuple[str, Field]]` | Pre-built (attr, field) pairs |
| `_col_to_attr` | `dict[str, tuple[str, Field]]` | Column → (attr, field) mapping |
| `objects` | `Manager` | Default query manager |

### Constructor

```python
def __init__(self, **kwargs: Any):
    """Create a model instance (in-memory, not persisted)."""
```

### Instance Attributes

| Property | Type | Description |
|---|---|---|
| `pk` | `Any` | Primary key value (shortcut) |

### Class-Level CRUD

```python
@classmethod
async def create(cls, **data: Any) -> Model:
    """Create and persist a new record."""

@classmethod
async def get(cls, pk: Any = None, **filters: Any) -> Model:
    """Get a single record by PK or filters. Raises ModelNotFoundFault."""

@classmethod
async def get_or_none(cls, pk: Any = None, **filters: Any) -> Model | None:
    """Like get() but returns None instead of raising."""

@classmethod
def query(cls) -> Q:
    """Start a chainable query."""
```

### Instance Methods

```python
async def save(self) -> Model:
    """Persist current state (INSERT or UPDATE)."""

async def update(self, **data) -> Model:
    """Update fields and save."""

async def delete(self) -> None:
    """Delete this record."""

async def refresh(self) -> Model:
    """Reload from database."""

def full_clean(self) -> None:
    """Run all field validators. Raises FieldValidationError."""

async def related(self, name: str) -> Any:
    """Access related objects (FK/M2M)."""
```

### Signals

```python
from aquilia.models.signals import pre_save, post_save, pre_delete, post_delete, pre_init, post_init, m2m_changed

@pre_save.connect
async def before_user_save(sender, instance, created, **kwargs):
    if created:
        instance.welcome_email_sent = False
```

---

## `ModelMeta` Metaclass

!!! abstract "`aquilia.models.ModelMeta`"

Handles field collection, auto-PK injection, Meta parsing, and registration.

```python
class ModelMeta(type):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs,
    ) -> ModelMeta:
```

Key behaviors:

- Auto-injects `BigAutoField` as `id` if no PK declared (non-abstract models)
- Collects `Meta` inner class → `Options`
- Registers model in `ModelRegistry`
- Auto-injects default `Manager` at `objects`

### Table Name Resolution

Priority order: `table = "..."` → `table_name = "..."` → `__tablename__ = "..."`

### `Options`

The parsed `Meta` class:

```python
class Options:
    table_name: str
    abstract: bool
    ordering: list[str]
    unique_together: list[tuple]
    indexes: list
    constraints: list
    managed: bool
    get_latest_by: str | None
    verbose_name: str
    verbose_name_plural: str
    db_tablespace: str
```

```python
class User(Model):
    table = "users"

    class Meta:
        ordering = ["-created_at"]
        unique_together = [("email", "tenant_id")]
        indexes = [Index(fields=["email", "name"])]
        get_latest_by = "created_at"
```

---

## `ModelRegistry`

!!! abstract "`aquilia.models.ModelRegistry`"

Global, singleton registry of all model classes.

```python
class ModelRegistry:
    @classmethod
    def register(cls, model_cls: type[Model]) -> None: ...
    @classmethod
    def get(cls, name: str) -> type[Model] | None: ...
    @classmethod
    def all_models(cls) -> dict[str, type[Model]]: ...
    @classmethod
    def set_database(cls, db: AquiliaDatabase) -> None: ...
    @classmethod
    def get_database(cls) -> AquiliaDatabase | None: ...
    @classmethod
    async def create_tables(cls, db: AquiliaDatabase | None = None) -> list[str]: ...
    @classmethod
    def reset(cls) -> None: ...
```

- Lifecycle hooks: `on_startup()` (auto-creates tables if `AQUILIA_AUTO_MIGRATE=1`), `on_shutdown()`.

---

## Field Types

### Base `Field`

```python
class Field:
    _field_type: str = "FIELD"
    _python_type: type = object

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
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `null` | `bool` | `False` | Allow NULL in database |
| `blank` | `bool` | `False` | Allow empty string in validation |
| `default` | `Any` | `UNSET` | Default value or callable |
| `unique` | `bool` | `False` | UNIQUE constraint |
| `primary_key` | `bool` | `False` | Primary key |
| `db_index` | `bool` | `False` | Create database index |
| `db_column` | `str \| None` | `None` | Override column name |
| `choices` | `Sequence \| None` | `None` | Enumerated values |
| `validators` | `list[Callable] \| None` | `None` | Validation callables |
| `help_text` | `str` | `""` | Documentation |
| `editable` | `bool` | `True` | Field is editable |
| `verbose_name` | `str \| None` | `None` | Human-readable label |

#### Key Methods

```python
def has_default(self) -> bool: ...
def get_default(self) -> Any: ...
def to_db(self, value: Any, *, dialect: str = "sqlite") -> Any: ...
def from_db(self, value: Any, *, dialect: str = "sqlite") -> Any: ...
def validate(self, value: Any) -> None: ...  # raises FieldValidationError
def pre_save(self, instance, *, is_create: bool) -> Any: ...
def db_type(self, dialect: str = "sqlite") -> str: ...
```

### Numeric Fields

| Field | Description |
|---|---|
| `AutoField(**kwargs)` | Auto-incrementing primary key |
| `BigAutoField(**kwargs)` | 64-bit auto-increment PK |
| `IntegerField(**kwargs)` | 32-bit integer |
| `BigIntegerField(**kwargs)` | 64-bit integer |
| `SmallIntegerField(**kwargs)` | 16-bit integer |
| `PositiveIntegerField(**kwargs)` | Integer ≥ 0 |
| `PositiveSmallIntegerField(**kwargs)` | Small integer ≥ 0 |
| `FloatField(**kwargs)` | Floating point |
| `DecimalField(*, max_digits, decimal_places, **kwargs)` | Fixed-point decimal |

### Text Fields

| Field | Description |
|---|---|
| `CharField(*, max_length=255, **kwargs)` | VARCHAR |
| `TextField(*, **kwargs)` | TEXT / CLOB |
| `EmailField(*, max_length=254, **kwargs)` | Validated email |
| `URLField(*, max_length=200, **kwargs)` | Validated URL |
| `SlugField(*, max_length=50, **kwargs)` | URL slug (a-z, 0-9, -, _) |
| `UUIDField(*, **kwargs)` | UUID values |

### Boolean / Date Fields

| Field | Description |
|---|---|
| `BooleanField(*, default=False, **kwargs)` | True/False |
| `DateField(*, auto_now=False, auto_now_add=False, **kwargs)` | Date only |
| `DateTimeField(*, auto_now=False, auto_now_add=False, **kwargs)` | Date + time |
| `TimeField(*, auto_now=False, auto_now_add=False, **kwargs)` | Time only |
| `DurationField(*, **kwargs)` | `timedelta` |

!!! note "auto_now vs auto_now_add"
    - `auto_now_add=True`: set on insert only
    - `auto_now=True`: set on every save

### Binary / JSON Fields

| Field | Description |
|---|---|
| `BinaryField(*, max_length=None, **kwargs)` | Raw bytes |
| `JSONField(*, encoder=None, decoder=None, **kwargs)` | JSON stored as TEXT |
| `FileField(*, upload_to="", **kwargs)` | File path storage |
| `FilePathField(*, path="", **kwargs)` | Server filesystem path |
| `ImageField(*, upload_to="", **kwargs)` | Image file with validation |

### Special Fields

| Field | Description |
|---|---|
| `GenericIPAddressField(*, protocol="both", **kwargs)` | IPv4 or IPv6 |
| `ArrayField(*, base_field, size=None, **kwargs)` | PostgreSQL array |
| `HStoreField(*, **kwargs)` | PostgreSQL key-value pairs |
| `EnumField(*, enum_class, **kwargs)` | Python Enum values |
| `GeneratedField(*, expression, output_field, **kwargs)` | Database-generated column |

### Field Mixins

```python
class UniqueMixin:
    unique: bool
class NullableMixin:
    null: bool
class IndexedMixin:
    db_index: bool
class AutoNowMixin:
    auto_now: bool
    auto_now_add: bool
class ChoiceMixin:
    choices: Sequence
class EncryptedMixin:
    encryption_key: str
```

---

## Relationship Fields

### `ForeignKey`

```python
class ForeignKey(Field):
    def __init__(
        self,
        to: type[Model] | str,
        *,
        on_delete: str = "CASCADE",
        on_update: str = "CASCADE",
        related_name: str | None = None,
        null: bool = False,
        **kwargs,
    ):
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `to` | `type[Model] \| str` | — | Target model (class or string ref) |
| `on_delete` | `str` | `"CASCADE"` | Delete behavior |
| `on_update` | `str` | `"CASCADE"` | Update behavior |
| `related_name` | `str \| None` | `None` | Reverse accessor name |
| `null` | `bool` | `False` | Allow NULL |

| `on_delete` Value | Behavior |
|---|---|
| `CASCADE` | Delete related objects |
| `SET_NULL` | Set FK to NULL |
| `SET_DEFAULT` | Set FK to default |
| `RESTRICT` / `PROTECT` | Prevent deletion |
| `DO_NOTHING` | No action |

### `ManyToManyField`

```python
class ManyToManyField(Field):
    def __init__(
        self,
        to: type[Model] | str,
        *,
        through: type[Model] | str | None = None,
        related_name: str | None = None,
        **kwargs,
    ):
```

### `OneToOneField`

```python
class OneToOneField(ForeignKey):
    def __init__(self, to, *, on_delete="CASCADE", **kwargs):
        kwargs["unique"] = True
        super().__init__(to, on_delete=on_delete, **kwargs)
```

### Composite Fields

```python
class CompositePrimaryKey(Field): ...
class CompositeField(Field): ...
class CompositeAttribute:
    """Attribute accessor for composite field components."""
```

---

## Constraints

### `Index`

```python
class Index:
    def __init__(
        self,
        *expressions: str | F,
        fields: list[str] | None = None,
        name: str | None = None,
        condition: Q | None = None,
    ):
```

```python
class Meta:
    indexes = [
        Index(fields=["email", "name"]),
        Index(fields=["-created_at"], name="created_desc_idx"),
    ]
```

### `UniqueConstraint`

```python
class UniqueConstraint:
    def __init__(
        self,
        *expressions,
        fields: list[str] | None = None,
        name: str | None = None,
        condition: Q | None = None,
        deferrable: str | None = None,
    ):
```

### `CheckConstraint`

```python
class CheckConstraint:
    def __init__(
        self,
        *,
        check: str,
        name: str,
        violation_error_message: str | None = None,
    ):
```

```python
class Meta:
    constraints = [
        CheckConstraint(check="age >= 0 AND age <= 200", name="valid_age"),
    ]
```

### `ExclusionConstraint` (PostgreSQL)

```python
class ExclusionConstraint:
    def __init__(
        self,
        *,
        name: str,
        expressions: list[tuple[str, str]],
        condition: Q | None = None,
        deferrable: str | None = None,
    ):
```

### `Deferrable`

```python
class Deferrable:
    DEFERRED = "DEFERRABLE INITIALLY DEFERRED"
    IMMEDIATE = "DEFERRABLE INITIALLY IMMEDIATE"
```

---

## Query Building (`Q` objects)

### `QNode` (Composable Filter)

```python
class QNode:
    AND = "AND"
    OR = "OR"

    def __init__(self, **kwargs: Any):
        self.filters: dict[str, Any] = kwargs
        self.negated: bool = False
        self.children: list[QNode] = []
        self.connector: str = self.AND

    def __and__(self, other: QNode) -> QNode: ...
    def __or__(self, other: QNode) -> QNode: ...
    def __invert__(self) -> QNode: ...
```

```python
from aquilia.models.query import QNode as QF

active_admins = QF(active=True) & QF(role="admin")
special_or_banned = ~QF(banned=True) | QF(is_special=True)

users = await User.objects.filter(active_admins).all()
```

### Lookup Suffixes

| Suffix | SQL |
|---|---|
| `__exact` | `=` |
| `__iexact` | `LIKE` (case-insensitive) |
| `__contains` | `LIKE %value%` |
| `__icontains` | `LIKE` (case-insensitive) |
| `__startswith` | `LIKE value%` |
| `__endswith` | `LIKE %value` |
| `__gt` | `>` |
| `__gte` | `>=` |
| `__lt` | `<` |
| `__lte` | `<=` |
| `__in` | `IN (...)` |
| `__isnull` | `IS NULL` / `IS NOT NULL` |
| `__ne` | `!=` |
| `__range` | `BETWEEN` |
| `__year` / `__month` / `__day` | `strftime` |

```python
users = await User.objects.filter(age__gte=18, email__icontains="gmail").all()
```

### Query Chain Methods

```python
class Q:
    def filter(self, *args: QNode, **filters: Any) -> Q: ...
    def exclude(self, *args: QNode, **filters: Any) -> Q: ...
    def order(self, *fields: str) -> Q: ...
    def limit(self, n: int) -> Q: ...
    def offset(self, n: int) -> Q: ...
    def select_related(self, *fields: str) -> Q: ...
    def prefetch_related(self, *lookups: str | Prefetch) -> Q: ...
    def distinct(self) -> Q: ...
    def only(self, *fields: str) -> Q: ...
    def defer(self, *fields: str) -> Q: ...
    def annotated(self, **annotations) -> Q: ...

    # Terminal (async)
    async def all(self) -> list[Model]: ...
    async def first(self) -> Model | None: ...
    async def one(self) -> Model: ...          # strict get, raises if != 1
    async def count(self) -> int: ...
    async def exists(self) -> bool: ...
    async def update(self, **data) -> int: ... # returns affected rows
    async def delete(self) -> int: ...
    async def aggregate(self, **aggregates) -> dict: ...
    async def values(self, *fields) -> list[dict]: ...
    async def values_list(self, *fields, flat=False) -> list: ...
```

### `Prefetch`

```python
class Prefetch:
    def __init__(
        self,
        lookup: str,
        queryset: Q | None = None,
        to_attr: str | None = None,
    ):
```

```python
users = await User.objects.prefetch_related(
    Prefetch("orders", queryset=Order.objects.filter(total__gt=500))
).all()
```

---

## Expressions

```python
from aquilia.models.expression import F, Value, Func, Coalesce, Case, When, Subquery, OuterRef

# F expressions
User.objects.filter(login_count__gt=F("allowed_logins"))

# Case/When
User.objects.annotated(
    tier=Case(
        When(points__gte=1000, then=Value("gold")),
        When(points__gte=500, then=Value("silver")),
        default=Value("bronze"),
    )
)
```

| Expression | Description |
|---|---|
| `F(name)` | Reference a field value |
| `Value(val)` | Literal value |
| `Coalesce(*exprs)` | First non-null |
| `Case(*cases, default=None)` | CASE WHEN |
| `When(condition, then)` | WHEN clause |
| `Subquery(qs)` | Subquery |
| `OuterRef(field)` | Reference outer query field |
| `Now()` | `CURRENT_TIMESTAMP` |
| `Concat(*exprs)` | String concatenation |
| `Lower(expr)`, `Upper(expr)` | Case conversion |
| `Length(expr)` | String length |
| `Abs(expr)`, `Round(expr)` | Math |
| `Exists(queryset)` | EXISTS subquery |

---

## Aggregates

```python
from aquilia.models.aggregate import Count, Sum, Avg, Min, Max, StdDev, Variance, ArrayAgg, StringAgg

stats = await Order.objects.aggregate(
    total=Sum("amount"),
    avg_order=Avg("amount"),
    order_count=Count("id"),
)
```

---

## Migrations

### `MigrationRunner`

```python
class MigrationRunner:
    def __init__(
        self,
        db: AquiliaDatabase,
        migrations_dir: str | Path = "migrations",
        *,
        dialect: str = "sqlite",
    ):
```

```python
runner = MigrationRunner(db, "migrations/")
await runner.ensure_tracking_table()                    # creates aquilia_migrations
applied = await runner.get_applied()                     # list of applied revisions
pending = await runner.get_pending()                     # list of pending migrations
await runner.migrate()                                   # apply all pending
await runner.migrate(fake=True)                          # mark applied only
await runner.migrate(target="0010_initial")              # migrate to target
stmts = await runner.plan()                              # preview SQL (dry-run)
```

### Migration DSL

```python
from aquilia.models.migration_dsl import Migration

class Migration_0002_add_email(Migration):
    revision = "0002"
    slug = "add_email"

    operations = [
        ops.AddField("users", "email", EmailField(unique=True)),
        ops.AddIndex("users", ["email"]),
        ops.RenameColumn("users", "name", "full_name"),
    ]
```

| Operation | Description |
|---|---|
| `ops.CreateModel(model)` | Create table |
| `ops.DeleteModel(model)` | Drop table |
| `ops.AddField(table, name, field)` | Add column |
| `ops.RemoveField(table, name)` | Drop column |
| `ops.AlterField(table, name, field)` | Alter column |
| `ops.RenameField(table, old, new)` | Rename column |
| `ops.AddIndex(table, fields)` | Create index |
| `ops.RemoveIndex(table, name)` | Drop index |

### CLI

```bash
aq makemigrations          # Generate migration files
aq migrate                 # Apply pending migrations
aq migrate --fake          # Mark as applied
aq sqlmigrate 0002         # Show SQL for migration
aq showmigrations          # List all migrations with status
aq inspectdb               # Introspect existing DB
```

---

## Full Example

```python
from aquilia.models import Model, Q
from aquilia.models.fields import (
    AutoField, CharField, IntegerField, FloatField,
    BooleanField, DateTimeField, EmailField, ForeignKey,
    ManyToManyField, TextField,
)
from aquilia.models.constraint import Index, UniqueConstraint, CheckConstraint
from aquilia.models.expression import F, Value, Case, When
from aquilia.models.aggregate import Count, Sum, Avg

class Category(Model):
    table = "categories"

    name = CharField(max_length=100, unique=True)
    description = TextField(blank=True)

class Product(Model):
    table = "products"

    name = CharField(max_length=200, db_index=True)
    sku = CharField(max_length=50, unique=True)
    price = FloatField()
    stock = IntegerField(default=0)
    active = BooleanField(default=True)
    category = ForeignKey(Category, on_delete="SET_NULL", null=True, related_name="products")
    tags = ManyToManyField("Tag", related_name="products")
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            Index(fields=["name", "active"]),
            Index(fields=["-price"], name="price_desc"),
        ]
        constraints = [
            CheckConstraint(check="price >= 0", name="positive_price"),
            CheckConstraint(check="stock >= 0", name="positive_stock"),
        ]

# Queries
products = await Product.objects.filter(
    active=True,
    category__name="Electronics",
    price__gte=10.0,
    price__lte=500.0,
).select_related("category").prefetch_related("tags").order("-price").limit(20).all()

count = await Product.objects.filter(stock__gt=0).count()

stats = await Product.objects.filter(active=True).aggregate(
    total_value=Sum(F("price") * F("stock")),
    avg_price=Avg("price"),
    total_products=Count("id"),
)

# Create with relationship
product = await Product.create(
    name="Wireless Headphones",
    sku="WH-001",
    price=99.99,
    stock=150,
    category=await Category.get(name="Electronics"),
)

# Access related
cat = await product.related("category")
tags = await product.related("tags")
```