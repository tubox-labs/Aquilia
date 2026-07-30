# Multi-Dialect Field Conversion Support

Aquilia v1.3.7 updates `EnumField.to_db()` (`aquilia.models.fields.enum_field`) and `CompositeField.to_db()` (`aquilia.models.fields.composite`) to accept the `dialect` keyword parameter.

---

## Why It Changed

In the Aquilia ORM, all field classes derive from `Field` (`aquilia.models.fields.base.Field`), which defines the method signature:

```python
def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
    ...
```

When contract data is imprinted back onto model instances (`contract.imprint()`) or when query engines compile SQL statements across different database backends (SQLite, PostgreSQL, MySQL, Oracle), the database driver invokes `field.to_db(value, dialect=dialect)`.

Previously:
- `EnumField.to_db(self, value)` and `CompositeField.to_db(self, value)` lacked the `dialect` parameter in their function signatures.
- Calling `contract.imprint()` on a model containing an `EnumField` or `CompositeField` resulted in a fatal `TypeError`:

```text
TypeError: EnumField.to_db() got an unexpected keyword argument 'dialect'
```

---

## What Changed

`EnumField.to_db()` and `CompositeField.to_db()` now explicitly include `dialect: str = "sqlite"` in their method signatures, matching `Field.to_db()`.

### Updated Signatures

```python
# EnumField
def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
    if value is None:
        return None
    if isinstance(value, self.enum_class):
        return value.name if self.store_name else value.value
    return value

# CompositeField
def to_db(self, value: Any, dialect: str = "sqlite") -> Any:
    if value is None:
        return None
    if self.strategy == "json":
        return json.dumps(value)
    return value
```

---

## Code Examples

### Contract Imprinting with EnumField Models

```python
import typing
from aquilia.contracts import Contract, Facet
from aquilia.models import Model
from aquilia.models.enums import TextChoices
from aquilia.models.fields import UUIDField, TextField, EnumField

class UserStatus(TextChoices):
    ACTIVE = "active", "Active"
    SUSPENDED = "suspended", "Suspended"

class UserModel(Model):
    table = "users"
    id = UUIDField(primary_key=True)
    name = TextField()
    status = EnumField(enum_class=UserStatus, default=UserStatus.ACTIVE)

class UserContract(Contract[UserModel]):
    name: typing.Annotated[str, Facet.text()]

    class Spec:
        model = UserModel

# Imprinting works seamlessly across all database dialects
contract = UserContract(data={"name": "Alice"})
assert contract.is_sealed()

user_model = contract.imprint()
assert user_model.status == UserStatus.ACTIVE
```
