# Aquilia Blueprint — DTO System Design

**Module:** `aquilia/blueprints/`  
**Focus:** Data Transfer Object patterns and best practices  

---

## 1. Blueprint as DTO

Aquilia's Blueprint serves as the framework's native DTO (Data Transfer Object)
system. Unlike traditional DTOs (passive data carriers), Blueprints are
**active DTOs** with built-in validation, projection, and write-back capabilities.

### 1.1 DTO Lifecycle

```
                         ┌──────────────────┐
                         │   Blueprint DTO   │
                         │                  │
        Inbound ──────► │  Cast → Seal     │ ──────► validated_data
        (request)        │                  │         (trusted dict)
                         │  Extract → Mold  │ ◄────── Model Instance
        Outbound ◄────── │                  │         (outbound dict)
        (response)       │                  │
                         │  Imprint         │ ──────► Model Write
                         └──────────────────┘
```

### 1.2 DTO Patterns Supported

| Pattern | Blueprint Feature | Example |
|---------|-------------------|---------|
| Input DTO | `data=` parameter + `is_sealed()` | Request body validation |
| Output DTO | `instance=` parameter + `to_dict()` | Response serialization |
| Projection DTO | `projection=` parameter | Field subsetting per endpoint |
| Partial DTO | `partial=True` | PATCH operations |
| Batch DTO | `many=True` | Bulk create/update |
| Nested DTO | `NestedBlueprintFacet` | Embedded objects |
| Polymorphic DTO | `PolymorphicFacet` | Union types |
| Computed DTO | `Computed` / `@computed` | Derived fields |
| Write-through DTO | `imprint()` | Direct model persistence |

---

## 2. DTO Declaration Styles

### 2.1 Annotation-Based (Recommended)

```python
class UserDTO(Blueprint):
    name: str = Field(min_length=2, max_length=100)
    email: str = Field(pattern=r"^[\w.+-]+@[\w-]+\.[\w.]+$")
    age: int = Field(ge=0, le=150)
    role: str = Field(default="user", choices=["user", "admin"])
    bio: str | None = None

    class Spec:
        model = User
        projections = {
            "summary": ["name", "email"],
            "detail": "__all__",
        }
```

### 2.2 Explicit Facet-Based

```python
class UserDTO(Blueprint):
    name = TextFacet(min_length=2, max_length=100)
    email = EmailFacet()
    age = IntFacet(min_value=0, max_value=150)
    role = ChoiceFacet(choices=["user", "admin"], default="user")
    bio = TextFacet(allow_null=True, required=False)

    class Spec:
        model = User
```

### 2.3 Model-Derived (Minimal)

```python
class UserDTO(Blueprint):
    class Spec:
        model = User
        fields = "__all__"
        read_only_fields = ("id", "created_at")
```

---

## 3. DTO Composition Patterns

### 3.1 Nested DTOs

```python
class AddressDTO(Blueprint):
    street: str
    city: str
    country: str = Field(choices=COUNTRY_CODES)

class UserDTO(Blueprint):
    name: str
    address: AddressDTO  # Nested DTO
```

### 3.2 List of DTOs

```python
class OrderDTO(Blueprint):
    items: list[OrderItemDTO]  # List of nested DTOs
    total: float
```

### 3.3 Polymorphic DTOs

```python
class PaymentDTO(Blueprint):
    method: CardPaymentDTO | BankPaymentDTO  # Union type → PolymorphicFacet
    amount: Decimal
```

### 3.4 Projected DTOs

```python
class ProductDTO(Blueprint):
    class Spec:
        model = Product
        projections = {
            "list": ["id", "name", "price"],
            "detail": ["id", "name", "price", "description", "images"],
            "admin": "__all__",
        }

# Usage:
@get("/products")
async def list_products(self) -> list:
    products = await Product.objects.all()
    bp = ProductDTO(instance=products, many=True, projection="list")
    return bp.data

@get("/products/{id}")
async def get_product(self, id: int) -> dict:
    product = await Product.objects.get(id=id)
    bp = ProductDTO(instance=product, projection="detail")
    return bp.data
```

---

## 4. DTO Security Guidelines

### 4.1 Always Use Specific Fields

```python
# BAD: Exposes all model fields including internal ones
class Spec:
    fields = "__all__"

# GOOD: Explicit field list
class Spec:
    fields = ["name", "email", "role"]
```

### 4.2 Mark Sensitive Fields as Write-Only

```python
class UserDTO(Blueprint):
    password: str = Field(write_only=True, min_length=8)
    email_verified: bool = Field(read_only=True)
```

### 4.3 Use Projections for Role-Based Access

```python
class Spec:
    projections = {
        "public": ["id", "name", "avatar"],
        "self": ["id", "name", "avatar", "email", "settings"],
        "admin": "__all__",
    }
```

### 4.4 Enable Unknown Field Rejection (After Fix)

```python
class Spec:
    extra_fields = "reject"  # Prevents mass assignment
```

---

## 5. DTO Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| One Blueprint for all operations | Read/write concerns mixed | Separate Input/Output Blueprints |
| No projections | All fields exposed everywhere | Define role-based projections |
| `fields = "__all__"` | Internal fields leaked | Explicit field lists |
| No write_only on passwords | Passwords in responses | `write_only=True` |
| Direct model → JSON | No validation or formatting | Always use Blueprint |
| Nested depth unlimited | Stack overflow risk | Set `depth` in Spec |

---

*End of DTO System Design — Phase 10*
