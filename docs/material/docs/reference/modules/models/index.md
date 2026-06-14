# Models Module

> `aquilia.models` — Pure-Python async ORM

The Models module provides a pure-Python async ORM with `Model` base class, ~30 field types, foreign keys, many-to-many and one-to-one relationships, query expressions (`Q`), indexes, constraints, and database migrations.

## When to Use

Use the Models module when you need:

- Declaring database models with typed fields
- Expressing complex queries with `Q` expressions
- Database schema migrations (auto-detection and execution)
- Foreign key and relationship management
- Model validation and serialization

## Key Classes

| Class | Purpose |
|---|---|
| `Model` | Base class for all ORM models |
| `ModelMeta` | Metaclass for model registration |
| `ModelRegistry` | Global model registry |
| `Field` | Base field class |
| `Q` | Query expression builder |
| `ForeignKey` | Foreign key relationship |
| `ManyToManyField` | Many-to-many relationship |
| `OneToOneField` | One-to-one relationship |
| `Index` | Database index |
| `UniqueConstraint` | Unique constraint |
| `MigrationRunner` | Executes migration operations |
| `MigrationOps` | Migration operation types |

## Field Types

| Field | Python Type | SQL Type |
|---|---|---|
| `AutoField` | `int` | AUTO_INCREMENT |
| `BigAutoField` | `int` | BIGINT AUTO_INCREMENT |
| `IntegerField` | `int` | INTEGER |
| `BigIntegerField` | `int` | BIGINT |
| `SmallIntegerField` | `int` | SMALLINT |
| `PositiveIntegerField` | `int` | INTEGER UNSIGNED |
| `PositiveSmallIntegerField` | `int` | SMALLINT UNSIGNED |
| `FloatField` | `float` | REAL |
| `DecimalField` | `Decimal` | DECIMAL |
| `BooleanField` | `bool` | BOOLEAN |
| `CharField` | `str` | VARCHAR |
| `TextField` | `str` | TEXT |
| `SlugField` | `str` | VARCHAR |
| `EmailField` | `str` | VARCHAR |
| `URLField` | `str` | VARCHAR |
| `UUIDField` | `UUID` | UUID |
| `DateField` | `date` | DATE |
| `TimeField` | `time` | TIME |
| `DateTimeField` | `datetime` | DATETIME |
| `DurationField` | `timedelta` | INTERVAL |
| `BinaryField` | `bytes` | BLOB |
| `JSONField` | `dict/list` | JSON |
| `ArrayField` | `list` | ARRAY |
| `FileField` | `str` | VARCHAR |
| `ImageField` | `str` | VARCHAR |
| `FilePathField` | `str` | VARCHAR |
| `GenericIPAddressField` | `str` | VARCHAR |
| `HStoreField` | `dict` | HSTORE |
| `GeneratedField` | varies | GENERATED |

## Quick Example

```python
from aquilia.models import Model, CharField, IntegerField, ForeignKey, Q

class Author(Model):
    name: str = CharField(max_length=100)
    email: str = CharField(max_length=255, unique=True)

class Book(Model):
    title: str = CharField(max_length=255)
    author = ForeignKey(Author, on_delete="CASCADE")
    pages: int = IntegerField(default=0)

# Query
books = await Book.objects.filter(
    Q(title__contains="Python") & Q(pages__gt=200)
).order_by("-title").limit(10)

# Create
book = await Book.objects.create(
    title="Async Python",
    author=author,
    pages=350,
)
```

## Migrations

```bash
# Create migrations
aq db makemigrations

# Apply migrations
aq db migrate

# Show SQL
aq db sqlmigrate myapp 0001

# Show status
aq db status
```

## Import Path

```python
from aquilia.models import (
    Model,
    ModelMeta,
    ModelRegistry,
    Field,
    Q,
    ForeignKey,
    ManyToManyField,
    OneToOneField,
    Index,
    UniqueConstraint,
    MigrationRunner,
    MigrationOps,
    IntegerField,
    CharField,
    TextField,
    BooleanField,
    DateTimeField,
    JSONField,
)
```

## Related Modules

- [db](../db/index.md) — Database connection layer
- [sqlite](../sqlite/index.md) — Native SQLite operations
- [blueprints](../blueprints/index.md) — Blueprint validation for model data
- [cli](../cli/index.md) — `aq db` migration commands