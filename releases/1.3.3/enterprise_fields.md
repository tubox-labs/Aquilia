# Enterprise Field Types — Aquilia v1.3.3

Four new field types close the gap flagged by a senior-engineer assessment
of the ORM's field system: currency-aware money storage, transparent
field-level encryption, portable spatial data, and polymorphic relations.
All four are additive, require no new dependencies, and needed no changes
to schema-generation or migration dialect-mapping code — each subclasses an
existing field whose `isinstance()`-based SQL-type dispatch already matches
subclasses.

```python
from aquilia.models import (
    MoneyField, EncryptedField, PointField, GeometryField, GenericForeignKey,
)
```

---

## MoneyField

`DecimalField` plus a `currency` code. Precision/storage behavior is
identical to `DecimalField` — values are stored as `str()` (never a
binary float), avoiding rounding error entirely.

```python
from aquilia.models import Model, MoneyField

class Order(Model):
    table = "orders"

    total = MoneyField(max_digits=12, decimal_places=2, currency="USD")
    shipping = MoneyField(max_digits=8, decimal_places=2, currency="EUR", default="0.00")
```

```python
order = await Order.create(total="149.99")
order.total          # Decimal('149.99')
order.currency if hasattr(order, "currency") else Order.total.currency  # "USD" — the field's currency, not per-row
```

**Signature:**

```python
MoneyField(
    currency: str = "USD",      # 3-letter code, shape-validated (not an ISO 4217 lookup table)
    max_digits: int = 10,
    decimal_places: int = 2,
    **field_kwargs,             # null, blank, default, unique, db_index, ...
)
```

- `currency` is metadata carried on the *field*, not encoded per-row — if
  you need a different currency per row, pair `MoneyField` with a sibling
  `CharField`/`choices` column and read both.
- Only the 3-uppercase-letter *shape* is validated (`^[A-Z]{3}$`), not
  membership in the real ISO 4217 table — a well-formed but unrecognized
  code (e.g. a test/private currency) is accepted on purpose. Raises
  `FieldValidationError` on construction for a malformed code (`"dollars"`,
  `"US"`, `"usd"`).
- `deconstruct()` includes `currency` for migration diffing.

```python
MoneyField(currency="dollars")  # raises FieldValidationError immediately
```

---

## EncryptedField

Transparent application-layer encryption at the storage boundary — built on
the existing `EncryptedMixin` (`aquilia/models/fields/mixins.py`), wrapping
`TextField`. Plaintext is validated as a normal `TextField` on assignment;
encryption/decryption happens only at `to_db()`/`to_python()` (i.e., only
on the wire to/from the database).

```python
import os
from aquilia.models import Model, EncryptedField

# Configure once, at app startup — before any encrypted field is saved/read.
EncryptedField.configure_encryption_key(os.environ["ENCRYPTION_KEY"])

class User(Model):
    table = "users"

    email = CharField(max_length=255, unique=True)
    ssn = EncryptedField(null=True)
    api_key = EncryptedField(null=True)
```

```python
user = await User.create(email="a@test.com", ssn="123-45-6789")
# The `ssn` column in the database holds ciphertext, not plaintext.

reloaded = await User.get(pk=user.pk)
reloaded.ssn  # "123-45-6789" — decrypted transparently on read
```

**Encryption backend priority** (see `EncryptedMixin`'s docstring for full
detail):

1. **Custom callables** — `EncryptedField.configure_encryption(encrypt_fn, decrypt_fn)`
2. **Fernet** (`cryptography` package, if installed) — `configure_encryption_key(key)`
3. **AES-256-GCM stdlib fallback** — same `configure_encryption_key(key)` call, used automatically when `cryptography` isn't installed. No extra packages required.
4. **Base64 placeholder** — used only if no backend was ever configured. **Not encryption** — trivially reversible. Emits a loud `UserWarning` every time it's hit specifically so this can't go unnoticed in production.

```python
# Custom backend (e.g. delegate to a KMS/HSM)
EncryptedField.configure_encryption(my_kms_encrypt, my_kms_decrypt)
```

> **Security note:** call `configure_encryption_key()` or
> `configure_encryption()` before any real secret is ever saved. If you see
> the `UserWarning` about base64 fallback in your logs, no backend has been
> configured and nothing is actually encrypted yet.

**Bug fixed while shipping this:** `EncryptedMixin.to_db()` previously
didn't accept the `dialect` keyword argument that every real
`Model.save()` call site passes (`field.to_db(value, dialect=dialect)`) —
so a real encrypted field would `TypeError` the moment it was saved through
a model. `EncryptedMixin` was, until now, only ever exercised standalone in
tests, never through an actual `Model.save()`. `to_db()` now accepts (and
ignores — encryption doesn't vary per dialect) `dialect`.

---

## PointField / GeometryField

Portable, GeoJSON-backed spatial fields — both subclass `JSONField` and
store data as `TEXT`/`JSONB` exactly like any other JSON value. No PostGIS
extension, no native geometry column type, no new dependency. This trades
native spatial indexing/query operators for zero-setup portability across
SQLite/PostgreSQL/MySQL.

```python
from aquilia.models import Model, GeometryField, PointField

class Store(Model):
    table = "stores"

    name = CharField(max_length=100)
    location = PointField()

class Region(Model):
    table = "regions"

    name = CharField(max_length=100)
    boundary = GeometryField(null=True)
```

```python
store = await Store.create(
    name="Flagship",
    location={"type": "Point", "coordinates": [-122.4194, 37.7749]},  # [lon, lat]
)

region = await Region.create(
    name="Downtown",
    boundary={
        "type": "Polygon",
        "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
    },
)
```

- **`PointField`** requires `{"type": "Point", "coordinates": [lon, lat]}`
  — exactly 2 numeric coordinates. Raises `FieldValidationError` for any
  other shape or geometry type.
- **`GeometryField`** accepts any standard GeoJSON geometry type: `Point`,
  `LineString`, `Polygon`, `MultiPoint`, `MultiLineString`,
  `MultiPolygon`, `GeometryCollection` — validated against
  `{"type": <one of those>, "coordinates": [...]}`.

```python
# Rejected — wrong geometry type for PointField
await Store.create(name="X", location={"type": "Polygon", "coordinates": [...]})
# FieldValidationError: Expected a GeoJSON Point with 2 numeric coordinates [lon, lat], got ...

# Rejected — unknown geometry type
await Region.create(name="X", boundary={"type": "NotAShape", "coordinates": []})
# FieldValidationError: Expected a GeoJSON geometry dict with 'type' in [...] ...
```

> **When you outgrow this:** if you need native spatial indexes (PostGIS
> `GIST`, MySQL `SPATIAL`), spatial query operators (`ST_Contains`,
> `ST_Distance`), or geometry validation beyond well-formed GeoJSON shape,
> you'll want a dedicated PostGIS/spatial-extension integration — that's
> out of scope for this JSON-backed field pair, which optimizes for
> portability and zero setup.

---

## GenericForeignKey

A polymorphic relation to *any* registered model — Django's
"virtual field" pattern. Unlike `ForeignKey`, it doesn't own a database
column of its own: you declare two real columns yourself (a model-label
column and a stringified-PK column), and `GenericForeignKey` resolves
between them.

```python
from aquilia.models import Model, AutoField, CharField, GenericForeignKey

class Comment(Model):
    table = "comments"

    id = AutoField(primary_key=True)
    body = CharField(max_length=1000)
    content_type = CharField(max_length=255)   # e.g. "User", "Post", "Ticket"
    object_id = CharField(max_length=255)      # stringified PK — works for int or UUID PKs
    target = GenericForeignKey("content_type", "object_id")
```

```python
post = await Post.get(pk=1)
comment = Comment(body="Nice post!")
Comment.target.attach(comment, post)   # sets content_type="Post", object_id=str(post.pk)
await comment.save()

# ... later, after loading a row back from the DB:
reloaded = await Comment.get(pk=comment.pk)
target = await Comment.target.resolve(reloaded)   # -> the Post instance, or None
```

**Why this isn't a transparent attribute (unlike Django's `GenericForeignKey`):**
Aquilia is async-native — there's no way to do a lazy synchronous DB fetch
on plain attribute access (`comment.target`) the way Django's sync ORM can.
Resolution is instead an explicit async method:

```python
await SomeModel.some_gfk_field.resolve(instance)  # -> resolved instance, or None
```

**Why no `ContentType` model:** Django's `GenericForeignKey` looks up a
`content_type_id` against a database-backed `ContentType` table. Aquilia
reuses the already-existing, in-memory `ModelRegistry.get(label)` lookup —
the same primitive `ForeignKey` already uses for string-based relation
resolution — so no extra table, migration, or registry sync step is needed.

```python
class GenericForeignKey:
    def __init__(self, ct_field: str = "content_type", fk_field: str = "object_id"): ...

    async def resolve(self, instance: Model) -> Model | None:
        """Look up the target row, or None if unset / the row is gone."""

    def attach(self, instance: Model, target: Model) -> None:
        """Set ct_field/fk_field on instance to point at target."""
```

Not a `Field` subclass — `ModelMeta`'s column-collection scan
(`isinstance(value, Field)`) skips it entirely, so it owns no schema column
and doesn't appear in generated `CREATE TABLE` DDL. It's purely a
convenience wrapper over the two columns you declare.

```python
# Unset target resolves to None, not an error
empty_comment = await Comment.create(body="orphan", content_type="", object_id="")
await Comment.target.resolve(empty_comment)  # None
```

---

## Backend & Dependency Summary

| Field | Storage | New dependency |
|---|---|---|
| `MoneyField` | `DECIMAL(m,d)` / `NUMBER(m,d)` (Oracle) — same as `DecimalField` | None |
| `EncryptedField` | `TEXT` / `CLOB` (Oracle) — same as `TextField` | None (uses `cryptography` if already installed, else a stdlib AES-GCM fallback) |
| `PointField` / `GeometryField` | `JSONB` (PostgreSQL) / `TEXT` (SQLite, MySQL) / `CLOB` (Oracle) — same as `JSONField` | None |
| `GenericForeignKey` | No column of its own — pairs with two user-declared columns | None |

### Regression Tests — `tests/test_orm_enterprise_fields.py` (14 tests)

| Group | Coverage |
|---|---|
| `MoneyField` | Default currency, precision/`max_digits` enforcement, malformed currency code rejection, `deconstruct()` includes `currency` |
| `EncryptedField` | Round-trip through a configured key, `to_db(value, dialect=...)` regression (the fixed bug) |
| `PointField` / `GeometryField` | Valid `Point` accepted, non-`Point` geometry rejected by `PointField`, wrong coordinate count rejected, `Polygon` accepted by `GeometryField`, unknown geometry type rejected, JSON round-trip |
| `GenericForeignKey` | Live-DB `attach()` + `resolve()` round-trip, `resolve()` returns `None` when unset |
