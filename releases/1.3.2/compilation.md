# Spec Compilation & Schema Inference

Specula features a compiler-integrated OpenAPI 3.1.0 specification engine (`SpeculaBuilder`). Instead of scanning source files at startup, it introspects Aquilia's compiled routing topology in memory, extracting schemas, bindings, parameters, and outputs.

---

## Python-to-JSON Schema Mapping

When generating schema objects, Specula inspects standard type hints and maps them to their OpenAPI 3.1.0 JSON Schema equivalents. 

Specula is fully compliant with the OpenAPI 3.1.0 specification:
* **Option types** use `oneOf` blocks combined with `{"type": "null"}` instead of the deprecated `nullable` property.
* **Complex Python structures** map cleanly to nested schemas.

### Mapping Reference Table

| Python Type Hint | JSON Schema Equivalent |
| :--- | :--- |
| `str` | `{"type": "string"}` |
| `int` | `{"type": "integer"}` |
| `float` | `{"type": "number", "format": "double"}` |
| `bool` | `{"type": "boolean"}` |
| `bytes` | `{"type": "string", "format": "binary"}` |
| `None` / `type(None)` | `{"type": "null"}` |
| `Optional[T]` / `T \| None` | `{"oneOf": [{"type": T_schema}, {"type": "null"}]}` |
| `list[T]` / `List[T]` | `{"type": "array", "items": T_schema}` |
| `dict[str, T]` / `Dict[str, T]` | `{"type": "object", "additionalProperties": T_schema}` |
| `tuple[T1, T2]` | `{"type": "array", "prefixItems": [T1_schema, T2_schema], "minItems": 2, "maxItems": 2}` |
| `Contract` / `Model` | `{"$ref": "#/components/schemas/Name"}` |

---

## Request Body Inference Strategies

Specula resolves request payloads through a 5-tier inference engine, prioritizing explicit developer configurations over implicit code analysis.

### 1. The `request_contract` Parameter
If a route decorator declares a validation contract directly, the builder generates a reference schema:
```python
@POST("/users", request_contract=UserCreateContract)
async def create_user(self, ctx: RequestCtx): ...
```

### 2. Contract Parameter Type Hints
If a route handler receives a parameter type-hinted with an Aquilia `Contract` class, it is automatically mapped as the JSON body payload:
```python
@POST("/users")
async def create_user(self, ctx: RequestCtx, payload: UserCreateContract): ...
```

### 3. Explicit `Body` Metadata Annotations
If a parameter is annotated using standard Python type annotations with `Body()`, it is mapped to a properties-based object payload:
```python
@POST("/items")
async def create_item(self, ctx: RequestCtx, amount: Annotated[int, Body()] = 1): ...
```

### 4. Docstring Body Mappings
The builder parses Google-style docstrings, extracting raw examples from `Body:` headers:
```python
@POST("/items")
async def create_item(self, ctx: RequestCtx):
    """
    Create an item.

    Body: {"name": "Widget", "count": 10}
    """
    ...
```

### 5. Source Code Introspection
As a fallback, Specula scans the compiled handler source code for extraction patterns:
* Finding `await ctx.json()` infers a generic `application/json` object.
* Finding `await ctx.form()` infers an `application/x-www-form-urlencoded` form.

---

## Response Shapes Resolution

Specula automatically maps success and error response channels.

### Success Shapes
1. **Model / Contract Mappings**: Declaring `response_model` or `response_contract` registers the corresponding schema (input contracts map with `Input` suffix, output contracts map directly) and binds them under status code `2xx`.
2. **Standard Output Fallbacks**: If no return contract is specified, Specula inspects handler code:
   * Calls to `Response.json(...)` default to `application/json`.
   * Calls to `Response.html(...)` or template rendering functions default to `text/html`.
   * References to `SSEResponse(...)` default to `text/event-stream`.

### Error Shapes
* **Raises Docstring Section**: Specula compiles exception details declared in Google-style docstrings into typed status responses:
  ```python
  @GET("/users/<id:int>")
  async def get_user(self, id: int):
      """
      Get user by ID.

      Raises:
          UserNotFoundFault (404): The user does not exist.
      """
      ...
  ```
  Specula compiles this raises annotation into a structured `404 Not Found` response returning the standard `AquiliaError` schema.
* **Auto-Validation Errors**: All write routes (`POST`, `PUT`, `PATCH`) automatically carry a default `422 Unprocessable Entity` response mapping returning the structured `AquiliaValidationError` schema.
