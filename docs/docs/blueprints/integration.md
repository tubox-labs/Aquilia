---
title: "Integration Helpers"
description: "Helper functions to integrate Blueprints with the Aquilia Controller framework"
icon: lucide/cable
---Aquilia provides a set of integration helpers in [integration.py](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/integration.py) to bridge the gap between Blueprint definitions, request/response lifecycle hooks, dependency injection (DI), and the Controller engine.

---

## Detection Utilities

### `is_blueprint_class()`

Check if an object is a class definition inheriting from `Blueprint` (excluding the base `Blueprint` class itself).

#### Signature
```python
def is_blueprint_class(obj: Any) -> bool:
```

#### Parameters
| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `obj` | `Any` |  | The object to check. |


#### Return Type
- `bool`: `True` if the object is a subclass of `Blueprint` (excluding `Blueprint` itself), otherwise `False`.

#### When to Use
Use this function during route initialization, dependency injection container setup, or annotation parsing to detect whether a route parameter is typed as a Blueprint class.

> [!NOTE]
> Defined in [integration.py:L46-49](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/integration.py#L46-L49).

---

### `is_projected_blueprint()`

Check if an object is a projected Blueprint reference (`_ProjectedRef`), typically represented as `Blueprint["projection"]`.

#### Signature
```python
def is_projected_blueprint(obj: Any) -> bool:
```

#### Parameters
| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `obj` | `Any` |  | The object to check. |


#### Return Type
- `bool`: `True` if the object is an instance of `_ProjectedRef`, otherwise `False`.

#### When to Use
Use this function when verifying type annotations to identify if a specific projection of a Blueprint class is being requested.

> [!NOTE]
> Defined in [integration.py:L51-54](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/integration.py#L51-L54).

---

### `resolve_blueprint_from_annotation()`

Extract the underlying `Blueprint` class and any associated projection name from a type annotation.

#### Signature
```python
def resolve_blueprint_from_annotation(
    annotation: Any,
) -> tuple[type[Blueprint] | None, str | None]:
```

#### Parameters
| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `annotation` | `Any` |  | The type annotation to inspect/resolve. |


#### Return Type
- `tuple[type[Blueprint] | None, str | None]`: A tuple containing:
  1. The resolved `Blueprint` class or `None` if not a Blueprint annotation.
  2. The name of the projection, or `None` if no projection is applied.

#### When to Use
Use this helper during controller configuration to extract Blueprint schema details from method parameter annotations. It correctly handles:
- Raw Blueprints (`MyBlueprint` &rarr; `(MyBlueprint, None)`)
- Projected Blueprints (`MyBlueprint["summary"]` &rarr; `(MyBlueprint, "summary")`)
- Non-blueprint types (&rarr; `(None, None)`)

> [!NOTE]
> Defined in [integration.py:L56-76](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/integration.py#L56-L76).

---

## Lifecycle Binding

### `bind_blueprint_to_request()`

Instantiate, merge parameters from, and validate a `Blueprint` from an incoming HTTP request.

#### Signature
```python
async def bind_blueprint_to_request(
    blueprint_cls: type[Blueprint],
    request: Any,
    *,
    projection: str | None = None,
    partial: bool = False,
    context: dict[str, Any] | None = None,
) -> Blueprint:
```

#### Parameters
| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `blueprint_cls` | `type[Blueprint]` |  | The Blueprint class to instantiate. |
| `request` | `Any` |  | The incoming Aquilia HTTP request object. |
| `projection` | `str \| None` | `None` | Optional projection name to restrict or filter validated data. |
| `partial` | `bool` | `False` | If True, fields not supplied in the request are ignored (useful for PATCH routes). |
| `context` | `dict[str, Any] \| None` | `None` | Extra context mapping (e.g. dependency injection container info) to supply to the BlueprintContext. |


#### Return Type
- `Blueprint`: An instantiated Blueprint instance with input data merged and validation executed (the instance will have been sealed).

#### When to Use
This is the core integration point between the controller execution engine and the Blueprint framework. It is invoked when a controller endpoint receives an incoming request containing an annotated Blueprint argument. The function extracts values from JSON payloads, form data, file uploads, query parameters, headers, cookies, and path parameters, and merges them into a single validation mapping.

> [!IMPORTANT]
> The function implements security limits such as verifying the request content length against `MAX_BODY_SIZE` (default 10 MB, configurable via context) to prevent resource exhaustion attacks.
> 
> Defined in [integration.py:L298-538](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/integration.py#L298-538).

---

### `render_blueprint_response()`

Render Python model instances or lists of data using a designated Blueprint for client response output.

#### Signature
```python
def render_blueprint_response(
    blueprint_or_cls: Blueprint | type[Blueprint],
    data: Any = None,
    *,
    projection: str | None = None,
    many: bool = False,
) -> Any:
```

#### Parameters
| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `blueprint_or_cls` | `Blueprint \| type[Blueprint]` |  | An existing Blueprint instance, a Blueprint class, or a projected Blueprint reference. |
| `data` | `Any` | `None` | The data to render (a single model instance, dictionary, or a collection of elements). |
| `projection` | `str \| None` | `None` | The projection name to apply during serialization (only used when blueprint_or_cls is a class). |
| `many` | `bool` | `False` | Set to True if the input data represents a list/collection of records. |


#### Return Type
- `Any`: A dictionary (or list of dictionaries) containing the serialized blueprint data ready for JSON serialization.

#### When to Use
Use this function in controller action responses (or route response formatters) to serialize model objects, raw dictionaries, or database collections back to the client. It handles:
- Passing in an already instantiated Blueprint (updates its instance reference and accesses `.data`).
- Passing in a class/projected reference (creates an instance and accesses `.data`).

> [!NOTE]
> Defined in [integration.py:L541-581](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/integration.py#L541-581).
