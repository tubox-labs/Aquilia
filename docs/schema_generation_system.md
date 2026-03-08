# Aquilia Blueprint — Schema Generation System

**Module:** `aquilia/blueprints/schema.py` + `core.py`  
**Focus:** OpenAPI / JSON Schema generation  

---

## 1. Current Implementation

### 1.1 Schema Generation Entry Points

```python
# Per-Blueprint schema
schema = UserBlueprint.to_schema(projection="summary", mode="input")

# Multi-Blueprint component schemas
components = generate_component_schemas([UserBlueprint, ProductBlueprint])
```

### 1.2 `Blueprint.to_schema()` (core.py)

```python
@classmethod
def to_schema(cls, *, projection=None, mode="output"):
    projection_fields = cls._projections.resolve(projection)
    properties = {}
    required = []
    
    for fname, facet in cls._all_facets.items():
        if mode == "output" and facet.write_only: continue
        if mode == "input" and facet.read_only: continue
        if projection_fields and fname not in projection_fields: continue
        
        properties[fname] = facet.to_schema()
        if mode == "input" and facet.required:
            required.append(fname)
    
    return {"type": "object", "properties": properties, "required": required}
```

### 1.3 `Facet.to_schema()` Output Examples

```python
# TextFacet(min_length=2, max_length=100)
{"type": "string", "minLength": 2, "maxLength": 100}

# IntFacet(min_value=0, max_value=150)
{"type": "integer", "minimum": 0, "maximum": 150}

# EmailFacet()
{"type": "string", "format": "email"}

# DateTimeFacet()
{"type": "string", "format": "date-time"}

# UUIDFacet()
{"type": "string", "format": "uuid"}

# ListFacet(child=TextFacet(), min_items=1)
{"type": "array", "items": {"type": "string"}, "minItems": 1}

# ChoiceFacet(choices=["a", "b", "c"])
{"type": "string", "enum": ["a", "b", "c"]}

# NestedBlueprintFacet(AddressBlueprint)
{"$ref": "#/components/schemas/AddressBlueprint"}

# PolymorphicFacet([CatBP(), DogBP()])
{"type": "object", "anyOf": [{"$ref": "..."}, {"$ref": "..."}]}
```

---

## 2. Schema Generation Architecture

```
Blueprint.to_schema()
    │
    ├─► Resolve projection → field subset
    ├─► Filter by mode (input/output)
    │
    ├─► For each facet:
    │   └─► facet.to_schema() → JSON Schema fragment
    │
    ├─► Collect required fields
    └─► Assemble final schema object

generate_component_schemas([BP1, BP2, ...])
    │
    ├─► For each Blueprint:
    │   └─► BP.to_schema() → schema dict
    │
    └─► Return {name: schema} dict
```

---

## 3. Current Gaps

| Gap | Impact | Priority |
|-----|--------|----------|
| No `$ref` for nested Blueprints in component schemas | Duplicate schemas | P1 |
| No `example` field support | Poor API docs | P2 |
| No `deprecated` per-field | Missing OpenAPI feature | P3 |
| No `description` from help_text | Missing documentation | P2 |
| No `nullable` support (OpenAPI 3.0) | Incorrect nullable schema | P1 |
| No `oneOf` for discriminated unions | Missing OpenAPI feature | P2 |
| No schema caching | Performance | P3 |
| No `readOnly`/`writeOnly` in nested | Incorrect nested schemas | P2 |

---

## 4. Enhanced Schema Generation Design

### 4.1 Component-Aware Schema Generation

```python
def generate_openapi_schemas(
    blueprints: list[type],
    *,
    ref_prefix: str = "#/components/schemas/",
) -> dict:
    """
    Generate OpenAPI-compatible component schemas with proper $ref.
    
    Returns:
        {
            "UserBlueprint": {...},
            "AddressBlueprint": {...},
            "ProductBlueprint": {...},
        }
    """
    components = {}
    seen = set()
    
    def _collect(bp_cls):
        if bp_cls.__name__ in seen:
            return
        seen.add(bp_cls.__name__)
        
        # Collect nested Blueprints first
        for facet in bp_cls._all_facets.values():
            if isinstance(facet, NestedBlueprintFacet):
                _collect(facet._blueprint_cls)
        
        components[bp_cls.__name__] = bp_cls.to_schema()
    
    for bp in blueprints:
        _collect(bp)
    
    return components
```

### 4.2 Nullable Support

```python
# For allow_null=True facets:
def to_schema(self):
    schema = {"type": self._type_name}
    if self.allow_null:
        schema = {"anyOf": [schema, {"type": "null"}]}
    return schema
```

### 4.3 Example Values

```python
class UserBlueprint(Blueprint):
    name: str = Field(example="Jane Doe")
    email: str = Field(example="jane@example.com")
    age: int = Field(example=28)

# Schema output:
# {"type": "string", "example": "Jane Doe"}
```

---

## 5. Integration with Controller OpenAPI

The controller module's `openapi.py` uses Blueprint schemas for:
- Request body schemas
- Response schemas
- Parameter schemas

```python
@post("/users", request_blueprint=UserBlueprint, response_blueprint=UserBlueprint["summary"])
async def create_user(self, user: UserBlueprint):
    ...
```

Generates:
```yaml
paths:
  /users:
    post:
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/UserBlueprint'
      responses:
        200:
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserBlueprint_summary'
```

---

*End of Schema Generation System — Phase 10*
