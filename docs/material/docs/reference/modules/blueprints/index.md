# Blueprints Module

> `aquilia.blueprints` — Request/response contracts with validation

Blueprints define typed contracts between HTTP requests/responses and your application logic. They validate, cast, seal, and project data — automatically generating OpenAPI schemas and providing structured error responses.

## When to Use

Use Blueprints when you need:

- Request body validation with structured error responses
- Response data projection (hide/expose fields per context)
- Automatic OpenAPI schema generation from your data contracts
- Type coercion and casting for incoming JSON
- Computed fields, read-only fields, and write-only fields

## Key Classes

| Class | Purpose |
|---|---|
| `Blueprint` | Base class for data contracts |
| `BlueprintMeta` | Metaclass that processes field declarations |
| `Facet` | Base class for field type definitions |
| `Lens` | Field-level inclusion/exclusion for projections |
| `Field` | Declares a field with facets and metadata |
| `Computed` | Field computed from other fields |
| `Constant` | Fixed-value field |
| `ReadOnly` | Field excluded from input but included in output |
| `WriteOnly` | Field included in input but excluded from output |
| `Hidden` | Field excluded from both input and output |
| `Inject` | Field injected by the framework (not from client) |

## Facet Types

| Facet | Validates |
|---|---|
| `TextFacet` | String values |
| `IntFacet` | Integer values |
| `FloatFacet` | Float values |
| `DecimalFacet` | Decimal values |
| `BoolFacet` | Boolean values |
| `DateFacet` | Date strings |
| `TimeFacet` | Time strings |
| `DateTimeFacet` | DateTime strings |
| `DurationFacet` | Duration strings |
| `UUIDFacet` | UUID strings |
| `EmailFacet` | Email addresses |
| `URLFacet` | URLs |
| `SlugFacet` | Slug-format strings |
| `IPFacet` | IP addresses |
| `ListFacet` | List/array values |
| `DictFacet` | Object/dict values |
| `JSONFacet` | Arbitrary JSON |
| `FileFacet` | File uploads |
| `ChoiceFacet` | Enumeration of allowed values |

## Quick Example

```python
from aquilia.blueprints import Blueprint, TextFacet, IntFacet, EmailFacet, Computed

class UserBlueprint(Blueprint):
    name: str = TextFacet(min_length=1, max_length=100)
    email: str = EmailFacet()
    age: int = IntFacet(min_value=0, max_value=150)
    display_name: str = Computed(lambda self: f"{self.name} <{self.email}>")

# Validate and seal input
try:
    user = UserBlueprint.seal({"name": "Alice", "email": "alice@example.com", "age": 30})
    print(user.name)   # "Alice"
    print(user.display_name)  # "Alice <alice@example.com>"
except SealFault as e:
    # Returns structured validation errors
    pass

# Generate OpenAPI schema
from aquilia.blueprints import generate_schema
schema = generate_schema(UserBlueprint)
```

## Import Path

```python
from aquilia.blueprints import (
    Blueprint,
    BlueprintMeta,
    Facet,
    Lens,
    TextFacet,
    IntFacet,
    FloatFacet,
    DecimalFacet,
    BoolFacet,
    DateFacet,
    TimeFacet,
    DateTimeFacet,
    DurationFacet,
    UUIDFacet,
    EmailFacet,
    URLFacet,
    SlugFacet,
    IPFacet,
    ListFacet,
    DictFacet,
    JSONFacet,
    FileFacet,
    ChoiceFacet,
    Computed,
    Constant,
    ReadOnly,
    WriteOnly,
    Hidden,
    Inject,
    generate_schema,
    is_blueprint_class,
)
```

## Related Modules

- [controller](../controller/index.md) — Validate request bodies against blueprints
- [models](../models/index.md) — ORM models vs blueprint contracts
- [core/response](../core/response.md) — Response handling with blueprint projections