# Blueprint

## Overview

A **Blueprint** is a first-class framework primitive — a contract between a Model and the outside world. It declares:

- **Facets** — what the world sees (field-level primitives)
- **Projections** — named subsets of facets
- **Casts** — inbound coercion (`dict → Python`)
- **Seals** — integrity enforcement (validation)
- **Imprints** — write-back (`validated → Model`)
- **Lenses** — relational views through other Blueprints

!!! note
    This is NOT a serializer. It is a declarative contract system that integrates with controllers, OpenAPI generation, and the DI container.

---

## `Blueprint` Base Class

!!! abstract "`aquilia.blueprints.Blueprint`"
    Metaclass: `BlueprintMeta`

### Spec Inner Class

Configuration is declared via the `Spec` inner class (not `Meta`):

```python
class ProductBlueprint(Blueprint):
    class Spec:
        model = Product
        fields = ["id", "name", "price"]           # explicit field list
        exclude = ["internal_notes"]                # exclude fields
        read_only_fields = ("id", "created_at")
        write_only_fields = ("password",)
        extra_facets = {}                           # custom Facet overrides
        projections = {
            "summary": ["id", "name", "price"],
            "detail": "__all__",
            "admin": "__all__",
        }
        default_projection = "detail"
        depth = 3                                    # max nesting depth for Lenses
        validators = []                              # blueprint-level validators
        extra_fields = "ignore"                      # "ignore" | "reject"
        max_many_items = 10000                       # max list items
```

| Spec Attribute | Type | Default | Description |
|---|---|---|---|
| `model` | `type \| None` | `None` | Model class to auto-derive facets from |
| `fields` | `list[str] \| None` | `None` | Explicit fields (None = all) |
| `exclude` | `list[str] \| None` | `None` | Fields to exclude |
| `read_only_fields` | `tuple[str, ...]` | `()` | Read-only fields |
| `write_only_fields` | `tuple[str, ...]` | `()` | Write-only fields |
| `extra_facets` | `dict` | `{}` | Custom facet overrides |
| `projections` | `dict \| None` | `None` | Named field subsets |
| `default_projection` | `str \| None` | `None` | Default projection name |
| `depth` | `int` | `3` | Max Lens nesting depth |
| `validators` | `list` | `[]` | Blueprint-level validators |
| `extra_fields` | `str` | `"ignore"` | `"ignore"` or `"reject"` |
| `max_many_items` | `int` | `10000` | Max items when molding lists |

### Usage

```python
# Outbound: Model → dict
bp = ProductBlueprint(instance=product)
data = bp.data               # respects default projection

# With projection
bp = ProductBlueprint(instance=product, projection="summary")
data = bp.data

# Inbound: dict → validated
bp = ProductBlueprint(data={"name": "Widget", "price": 9.99})
if bp.is_sealed():
    product = await bp.imprint()    # creates or updates model instance

# Subscript syntax returns ProjectedRef for route decorators
@GET("/products", response_blueprint=ProductBlueprint["summary"])
async def list_products(self, ctx):
    return await Product.objects.all()
```

### Key Properties / Methods

| Property/Method | Description |
|---|---|
| `bp.data` | Outbound dict (respects projection) |
| `bp.validated_data` | Inbound validated dict (after sealing) |
| `bp.is_sealed()` | `True` if inbound data passed validation |
| `bp.seal_errors()` | Dict of field validation errors |
| `bp.is_valid()` | Alias for `is_sealed()` |
| `await bp.imprint()` | Write validated data back to model |
| `bp.to_json()` | Serialize to JSON string |

---

## `BlueprintMeta`

!!! abstract "`aquilia.blueprints.BlueprintMeta`"

The metaclass handles:

1. Collecting declared `Facet` instances from namespace
2. Parsing the `Spec` inner class
3. Auto-deriving facets from Model fields (when `Spec.model` is set)
4. Building the `ProjectionRegistry`
5. Supporting `Blueprint["projection"]` subscript syntax
6. Inheriting facets from parent Blueprints

```python
class BlueprintMeta(type):
    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        namespace: dict[str, Any],
        **kwargs,
    ) -> BlueprintMeta:
```

---

## Facets

A **Facet** is a single data point in a Blueprint — the equivalent of a serializer field but with Blueprint-native lifecycle: `cast` (inbound) → `seal` (validate) → `mold` (outbound).

### `Facet` Base

```python
class Facet:
    _type_name: str = "any"    # JSON Schema type

    def __init__(
        self,
        *,
        source: str | None = None,        # Model attribute name
        required: bool | None = None,     # Auto-detected if None
        read_only: bool = False,
        write_only: bool = False,
        default: Any = UNSET,
        allow_null: bool = False,
        allow_blank: bool = False,
        label: str | None = None,
        help_text: str | None = None,
        validators: Sequence[Callable] | None = None,
    ):
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `source` | `str \| None` | `None` | Model attribute (defaults to facet name) |
| `required` | `bool \| None` | `None` | Auto-detected from model field if None |
| `read_only` | `bool` | `False` | Only appears in output |
| `write_only` | `bool` | `False` | Only accepted as input |
| `default` | `Any` | `UNSET` | Default value |
| `allow_null` | `bool` | `False` | Accept `None` |
| `allow_blank` | `bool` | `False` | Accept empty string |
| `label` | `str \| None` | `None` | Human-readable label |
| `help_text` | `str \| None` | `None` | Documentation |
| `validators` | `Sequence[Callable] \| None` | `None` | Extra callable validators |

#### Lifecycle Methods

```python
def cast(self, value: Any) -> Any:
    """Cast inbound value to internal Python type. Raises CastFault."""

def mold(self, value: Any) -> Any:
    """Shape outbound value for response."""

def seal(self, value: Any) -> Any:
    """Run validators on cast value."""

def extract(self, instance: Any) -> Any:
    """Extract facet value from a model instance (supports dotted sources)."""

def to_schema(self) -> dict[str, Any]:
    """Generate JSON Schema for this facet."""

def bind(self, name: str, blueprint: Blueprint) -> None:
    """Attach facet to Blueprint."""

def clone(self) -> Facet:
    """Shallow copy for Blueprint inheritance."""
```

### Text Facets

#### `TextFacet`

```python
class TextFacet(Facet):
    _type_name = "string"

    def __init__(
        self,
        *,
        min_length: int | None = None,
        max_length: int | None = None,
        trim: bool = True,
        pattern: str | None = None,   # ReDoS-protected
        **kwargs,
    ):
```

#### `EmailFacet(TextFacet)`

Lowercases value; validates with `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`.

#### `URLFacet(TextFacet)`

Validates `https?://` URLs.

#### `SlugFacet(TextFacet)`

Lowercases; validates `^[-a-zA-Z0-9_]+$`.

#### `IPFacet(TextFacet)`

Validates IPv4/IPv6 via `ipaddress.ip_address`.

### Numeric Facets

#### `IntFacet`

```python
class IntFacet(Facet):
    _type_name = "integer"

    def __init__(
        self,
        *,
        min_value: int | None = None,
        max_value: int | None = None,
        **kwargs,
    ):
```

#### `FloatFacet`

```python
class FloatFacet(Facet):
    _type_name = "number"

    def __init__(
        self,
        *,
        min_value: float | None = None,
        max_value: float | None = None,
        allow_nan: bool = False,
        allow_infinity: bool = False,
        **kwargs,
    ):
```

#### `DecimalFacet`

```python
class DecimalFacet(Facet):
    _type_name = "number"

    def __init__(
        self,
        *,
        max_digits: int | None = None,
        decimal_places: int | None = None,
        **kwargs,
    ):
```

### Boolean / Date / Time Facets

#### `BoolFacet`

```python
class BoolFacet(Facet):
    _type_name = "boolean"
```

#### `DateFacet`

```python
class DateFacet(Facet):
    _type_name = "string"     # format: "date"

    def __init__(
        self,
        *,
        input_formats: list[str] | None = None,
        **kwargs,
    ):
```

#### `TimeFacet`

```python
class TimeFacet(Facet):
    _type_name = "string"     # format: "time"
```

#### `DateTimeFacet`

```python
class DateTimeFacet(Facet):
    _type_name = "string"     # format: "date-time"

    def __init__(
        self,
        *,
        input_formats: list[str] | None = None,
        **kwargs,
    ):
```

#### `DurationFacet`

```python
class DurationFacet(Facet):
    _type_name = "string"     # format: "duration"
```

### Structured Facets

#### `UUIDFacet`

```python
class UUIDFacet(Facet):
    _type_name = "string"     # format: "uuid"
```

#### `ListFacet`

```python
class ListFacet(Facet):
    _type_name = "array"

    def __init__(
        self,
        child: Facet | None = None,
        *,
        min_length: int | None = None,
        max_length: int | None = None,
        **kwargs,
    ):
```

#### `DictFacet`

```python
class DictFacet(Facet):
    _type_name = "object"
```

#### `JSONFacet`

```python
class JSONFacet(Facet):
    _type_name = "object"
```

#### `FileFacet`

```python
class FileFacet(Facet):
    _type_name = "string"     # format: "binary"
```

#### `ChoiceFacet`

```python
class ChoiceFacet(Facet):
    _type_name = "string"

    def __init__(
        self,
        choices: Sequence[tuple[Any, str]],
        **kwargs,
    ):
```

---

## Special Facets

### `Constant`

Always returns a fixed value.

```python
class Constant(Facet):
    def __init__(self, value: Any, **kwargs):
        self.constant_value = value
        kwargs.setdefault("read_only", True)
```

### `Computed`

Computed from other fields at mold time. Created via `@computed` decorator or `Field` annotation.

```python
class Computed(Facet):
    def __init__(
        self,
        func: Callable,
        *,
        depends_on: list[str] | None = None,
        **kwargs,
    ):
```

### `WriteOnly`

```python
class WriteOnly(Facet):
    """Factory: creates a write-only facet."""
    def __init__(self, child: Facet, **kwargs):
```

### `ReadOnly`

```python
class ReadOnly(Facet):
    """Factory: creates a read-only facet."""
    def __init__(self, child: Facet, **kwargs):
```

### `Hidden`

Never appears in output, never accepts input. Used for internal state.

```python
class Hidden(Facet):
    def __init__(self, **kwargs):
        kwargs["read_only"] = True
        kwargs["write_only"] = True
```

### `Inject`

Injected from the DI container rather than from request data.

```python
class Inject(Facet):
    def __init__(
        self,
        provider: str | type | None = None,
        *,
        tag: str | None = None,
        **kwargs,
    ):
```

---

## Annotations

### `Field`

Descriptor for type-annotation-based facet declaration:

```python
class Field:
    def __init__(
        self,
        *,
        source: str | None = None,
        required: bool = True,
        default: Any = UNSET,
        validators: list[Callable] | None = None,
    ):
```

```python
class ProductBlueprint(Blueprint):
    name: str = Field(source="product_name", required=True, max_length=200)
    price: float = Field(default=0.0)
```

### `NestedBlueprintFacet`

Lets you declare a Lens via type annotation:

```python
class NestedBlueprintFacet:
    def __init__(
        self,
        blueprint: type[Blueprint],
        *,
        many: bool = False,
        depth: int = 3,
        projection: str | None = None,
    ):
```

### `computed()`

```python
def computed(depends_on: list[str] | None = None) -> Callable:
    """Decorator to mark a method as a Computed facet."""
```

```python
class OrderBlueprint(Blueprint):
    total = IntFacet()
    tax = IntFacet()

    @computed(depends_on=["total", "tax"])
    def grand_total(self):
        return self.total + self.tax
```

---

## Lenses

A `Lens` provides a relational view through another Blueprint with depth control and cycle detection.

```python
class Lens(Facet):
    _type_name = "object"

    def __init__(
        self,
        target: type[Blueprint] | _ProjectedRef | None = None,
        *,
        many: bool = False,
        depth: int = 3,
        projection: str | None = None,
        **kwargs,
    ):
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `target` | `type[Blueprint] \| ProjectedRef \| None` | `None` | Target Blueprint |
| `many` | `bool` | `False` | `True` for to-many relations |
| `depth` | `int` | `3` | Max nesting depth |
| `projection` | `str \| None` | `None` | Named projection on target |

```python
class OrderBlueprint(Blueprint):
    customer = Lens(UserBlueprint["public"])       # to-one
    items = Lens(OrderItemBlueprint, many=True)    # to-many
```

### Cycle Detection

Lens tracks `_seen` set of Blueprint class ids during molding; raises `LensCycleFault` on recursion.

---

## `ProjectionRegistry`

Manages named field subsets defined in `Spec.projections`.

```python
class ProjectionRegistry:
    def configure(
        self,
        projections: dict[str, str | list[str]] | None,
        default: str | None,
        all_facet_names: set[str],
        write_only_names: set[str],
    ) -> None: ...

    def resolve(self, name: str | None) -> frozenset[str]: ...
    def get_default_projection_name(self) -> str | None: ...
```

Special values:

| Value | Meaning |
|---|---|
| `"__all__"` | All non-write-only facets |
| `"__minimal__"` | Only PK + read-only facets |
| `"-field"` (prefix) | Exclusion: all except `field` |

```python
class Spec:
    projections = {
        "public": ["-password", "-email", "-internal_notes"],
    }
```

---

## Schema Generation

### `generate_schema(blueprint_cls, *, projection=None)`

```python
def generate_schema(
    blueprint_cls: type[Blueprint],
    *,
    projection: str | None = None,
) -> dict[str, Any]:
    """Generate OpenAPI-compatible JSON Schema for a Blueprint."""
```

### `generate_component_schemas(*blueprint_classes)`

```python
def generate_component_schemas(
    *blueprint_classes: type[Blueprint],
) -> dict[str, dict[str, Any]]:
    """Generate OpenAPI component schemas for multiple Blueprints."""
```

---

## Integration

### `bind_blueprint_to_request(blueprint_cls, data, *, projection=None)`

```python
def bind_blueprint_to_request(
    blueprint_cls: type[Blueprint],
    data: dict[str, Any],
    *,
    projection: str | None = None,
) -> Blueprint:
    """Create and seal a Blueprint instance from request data."""
```

### `render_blueprint_response(instance, blueprint_cls, *, projection=None)`

```python
async def render_blueprint_response(
    instance: Any,
    blueprint_cls: type[Blueprint],
    *,
    projection: str | None = None,
) -> dict[str, Any]:
    """Render a model instance to dict through a Blueprint."""
```

### `is_blueprint_class(obj) → bool`

```python
def is_blueprint_class(obj: Any) -> bool: ...
```

### `is_projected_blueprint(obj) → bool`

```python
def is_projected_blueprint(obj: Any) -> bool:
    """True if obj is a ProjectedRef (Blueprint["projection"])."""
```

### `resolve_blueprint_from_annotation(annotation) → (BlueprintClass | None, projection | None)`

```python
def resolve_blueprint_from_annotation(annotation: Any) -> tuple[type[Blueprint] | None, str | None]:
```

---

## Full Example

```python
from aquilia.blueprints import (
    Blueprint, Facet, Lens, Computed, Constant,
    TextFacet, IntFacet, FloatFacet, DateTimeFacet,
    EmailFacet, Field, computed, NestedBlueprintFacet,
)

class ProductBlueprint(Blueprint):
    class Spec:
        model = Product
        projections = {
            "summary": ["id", "name", "sku", "price", "active"],
            "detail": "__all__",
        }
        default_projection = "summary"
        read_only_fields = ("id", "created_at", "updated_at")
        depth = 3

    # Facet declarations
    name = TextFacet(min_length=1, max_length=200)
    sku = TextFacet(min_length=3, max_length=50, pattern=r"^[A-Z0-9\-]+$")
    price = FloatFacet(min_value=0.01, max_value=999999.99)
    description = TextFacet(required=False, allow_blank=True)
    category = Lens(CategoryBlueprint["public"], many=False)
    tags = Lens(TagBlueprint, many=True, depth=2)

    # Constant value
    version = Constant("2.0")

    # Computed from model attributes
    @computed(depends_on=["price", "discount"])
    def final_price(self):
        if hasattr(self.instance, "discount") and self.instance.discount:
            return self.instance.price * (1 - self.instance.discount / 100)
        return self.instance.price if hasattr(self.instance, "price") else 0

# Route usage
@GET("/products", response_blueprint=ProductBlueprint["summary"])
async def list_products(self, ctx):
    products = await Product.objects.filter(active=True).all()
    return products

@POST("/products", request_blueprint=ProductBlueprint,
       response_blueprint=ProductBlueprint["detail"])
@validate_body(ProductBlueprint)
async def create_product(self, ctx: RequestCtx, body: dict):
    product = await Product.create(**body)
    return product
```