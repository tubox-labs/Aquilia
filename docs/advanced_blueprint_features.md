# Aquilia Blueprint — Advanced Features Design

**Module:** `aquilia/blueprints/`  
**Focus:** Feature expansion and modern framework comparison  

---

## 1. Current Feature Set

| Feature | Status | Comparison |
|---------|--------|------------|
| Type-annotation fields | ✅ Full | Parity with Pydantic v2 |
| Explicit field declaration | ✅ Full | Parity with DRF |
| Model auto-derivation | ✅ Full | Parity with DRF |
| Nested Blueprints | ✅ Full | Parity with Pydantic |
| List/Dict facets | ✅ Full | Parity with Pydantic |
| Polymorphic (Union) | ✅ Full | Parity with Pydantic |
| Forward references | ✅ Full | Parity with Pydantic |
| Projections | ✅ Unique | Not in DRF/Pydantic |
| Lenses (depth control) | ✅ Unique | Not in DRF/Pydantic |
| Async validation | ✅ Unique | Not in DRF/Pydantic |
| Imprint (write-back) | ✅ Unique | Not in Pydantic |
| Schema generation | ✅ Basic | Behind Pydantic v2 |
| Computed fields | ✅ Full | Parity with Pydantic |
| DI integration | ✅ Unique | Not in DRF/Pydantic |

---

## 2. Modern Framework Research

### 2.1 Pydantic v2 Features to Consider

| Feature | Pydantic v2 | Aquilia Status | Recommendation |
|---------|-------------|----------------|----------------|
| Rust core (pydantic-core) | ✅ | ❌ N/A | Not applicable |
| Model validators | ✅ `@model_validator` | ✅ `validate()` | Feature parity |
| Field validators | ✅ `@field_validator` | ✅ `seal_*()` | Feature parity |
| Discriminated unions | ✅ `Discriminator` | ❌ Missing | **Implement** |
| Serialization modes | ✅ `mode='json'/'python'` | ❌ Missing | Consider |
| Strict mode | ✅ `strict=True` | ❌ Missing | **Implement** |
| Custom types | ✅ `__get_pydantic_core_schema__` | ❌ Missing | Add plugin API |
| Alias support | ✅ `alias='field_name'` | ✅ `source='field_name'` | Parity |
| JSON Schema $ref | ✅ Full | ✅ Basic | Enhance |
| Functional validators | ✅ `@field_validator` | ✅ validators list | Parity |
| Before/after validators | ✅ `mode='before'/'after'` | ❌ Missing | **Implement** |

### 2.2 Marshmallow Features to Consider

| Feature | Marshmallow | Aquilia Status | Recommendation |
|---------|-------------|----------------|----------------|
| Pre/post load hooks | ✅ `@pre_load` | ❌ Missing | **Implement** |
| Pre/post dump hooks | ✅ `@post_dump` | ❌ Missing | **Implement** |
| Nested loading | ✅ `Nested()` | ✅ NestedBlueprintFacet | Parity |
| Schema context | ✅ `.context` | ✅ `.context` | Parity |
| Many=True | ✅ Full | ✅ Full | Parity |
| Error messages i18n | ✅ Configurable | ❌ Missing | Consider |

### 2.3 TypedDict / attrs Features

| Feature | Implementation | Aquilia Status | Recommendation |
|---------|---------------|----------------|----------------|
| Frozen instances | `@frozen` | ❌ Missing | Consider |
| Slots optimization | `__slots__` | ❌ Partial | **Implement** |
| Equality by value | `__eq__` | ❌ Missing | Consider |
| Hash support | `__hash__` | ❌ Missing | Consider |

---

## 3. Proposed Advanced Features

### 3.1 Discriminated Unions

```python
class CatBlueprint(Blueprint):
    type: str = Field(default="cat")
    meow_volume: int

class DogBlueprint(Blueprint):
    type: str = Field(default="dog")
    bark_volume: int

class PetBlueprint(Blueprint):
    # Discriminated by "type" field
    pet: CatBlueprint | DogBlueprint = Field(discriminator="type")
```

**Implementation:** Add `DiscriminatorFacet` that reads the discriminator
field value before attempting cast on the correct child Blueprint.

### 3.2 Before/After Hooks

```python
class UserBlueprint(Blueprint):
    @before_cast
    def normalize_email(self, data):
        if "email" in data:
            data["email"] = data["email"].lower().strip()
        return data

    @after_seal
    def add_defaults(self, validated):
        validated.setdefault("role", "user")
        return validated

    @before_mold
    def filter_sensitive(self, instance):
        # Modify instance before molding
        return instance

    @after_mold
    def add_links(self, data):
        data["_links"] = {"self": f"/api/users/{data['id']}"}
        return data
```

### 3.3 Strict Mode

```python
class StrictUserBlueprint(Blueprint):
    class Spec:
        strict = True  # No type coercion — type must match exactly

    name: str    # Must be str, not int
    age: int     # Must be int, not "42"
```

**Implementation:** In strict mode, `cast()` checks `isinstance()` instead
of attempting conversion.

### 3.4 Blueprint Composition

```python
class TimestampMixin(Blueprint):
    created_at: datetime = Field(read_only=True)
    updated_at: datetime = Field(read_only=True)

class AuditMixin(Blueprint):
    created_by: int = Field(read_only=True)
    updated_by: int = Field(read_only=True)

class UserBlueprint(TimestampMixin, AuditMixin, Blueprint):
    name: str
    email: str
```

**Status:** Already partially supported through metaclass inheritance.
Need formal documentation and tests.

### 3.5 Conditional Fields

```python
class PaymentBlueprint(Blueprint):
    method: str = Field(choices=["card", "bank", "crypto"])
    
    # Only required when method == "card"
    card_number: str = Field(required_when=lambda data: data.get("method") == "card")
    
    # Only included in output when user is admin
    internal_ref: str = Field(visible_when=lambda ctx: ctx.get("is_admin"))
```

### 3.6 Error Message Customization

```python
class UserBlueprint(Blueprint):
    name: str = Field(
        min_length=2,
        error_messages={
            "min_length": "Name must be at least {min_length} characters",
            "required": "Please provide your name",
            "blank": "Name cannot be empty",
        }
    )
```

---

## 4. Schema Generation Enhancements

### 4.1 Current Limitations

- No `$ref` deduplication for nested Blueprints
- No discriminator support in schemas
- No example values in schemas
- No deprecation markers per field

### 4.2 Proposed Enhancements

```python
class UserBlueprint(Blueprint):
    name: str = Field(
        min_length=2,
        example="John Doe",
        deprecated=False,
        description="User's full name",
    )
    
    @classmethod
    def to_schema(cls, *, include_examples=True):
        # Enhanced schema with examples, deprecation, etc.
        ...
```

---

## 5. Implementation Priority

| Feature | Priority | Effort | Impact |
|---------|----------|--------|--------|
| Discriminated unions | P1 | Medium | High |
| Before/after hooks | P1 | Medium | High |
| Strict mode | P2 | Low | Medium |
| Conditional fields | P2 | Medium | High |
| Error message i18n | P3 | Medium | Medium |
| Schema enhancements | P2 | Low | Medium |
| Frozen instances | P3 | Low | Low |

---

*End of Advanced Blueprint Features — Phase 10*
