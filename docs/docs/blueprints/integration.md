---
title: "Integration Helpers"
description: "Helper functions to integrate Contracts with the Aquilia Controller framework"
icon: lucide/cable
---Aquilia provides a set of integration helpers in [integration.py](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/integration.py) to bridge the gap between Contract definitions, request/response lifecycle hooks, dependency injection (DI), and the Controller engine.

---

## Detection Utilities

### `is_contract_class()`

Check if an object is a class definition inheriting from `Contract` (excluding the base `Contract` class itself).

#### Signature
```python
def is_contract_class(obj: Any) -> bool:
```

#### Parameters
| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `obj` | `Any` |  | The object to check. |


#### Return Type
- `bool`: `True` if the object is a subclass of `Contract` (excluding `Contract` itself), otherwise `False`.

#### When to Use
Use this function during route initialization, dependency injection container setup, or annotation parsing to detect whether a route parameter is typed as a Contract class.

> [!NOTE]
> Defined in [integration.py:L46-49](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/integration.py#L46-L49).

---

### `is_projected_contract()`

Check if an object is a projected Contract reference (`_ProjectedRef`), typically represented as `Contract["projection"]`.

#### Signature
```python
def is_projected_contract(obj: Any) -> bool:
```

#### Parameters
| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `obj` | `Any` |  | The object to check. |


#### Return Type
- `bool`: `True` if the object is an instance of `_ProjectedRef`, otherwise `False`.

#### When to Use
Use this function when verifying type annotations to identify if a specific projection of a Contract class is being requested.

> [!NOTE]
> Defined in [integration.py:L51-54](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/integration.py#L51-L54).

---

### `resolve_contract_from_annotation()`

Extract the underlying `Contract` class and any associated projection name from a type annotation.

#### Signature
```python
def resolve_contract_from_annotation(
    annotation: Any,
) -> tuple[type[Contract] | None, str | None]:
```

#### Parameters
| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `annotation` | `Any` |  | The type annotation to inspect/resolve. |


#### Return Type
- `tuple[type[Contract] | None, str | None]`: A tuple containing:
  1. The resolved `Contract` class or `None` if not a Contract annotation.
  2. The name of the projection, or `None` if no projection is applied.

#### When to Use
Use this helper during controller configuration to extract Contract schema details from method parameter annotations. It correctly handles:
- Raw Contracts (`MyContract` &rarr; `(MyContract, None)`)
- Projected Contracts (`MyContract["summary"]` &rarr; `(MyContract, "summary")`)
- Non-contract types (&rarr; `(None, None)`)

> [!NOTE]
> Defined in [integration.py:L56-76](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/integration.py#L56-L76).

---

## Lifecycle Binding

### `bind_contract_to_request()`

Instantiate, merge parameters from, and validate a `Contract` from an incoming HTTP request.

#### Signature
```python
async def bind_contract_to_request(
    contract_cls: type[Contract],
    request: Any,
    *,
    projection: str | None = None,
    partial: bool = False,
    context: dict[str, Any] | None = None,
) -> Contract:
```

#### Parameters
| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `contract_cls` | `type[Contract]` |  | The Contract class to instantiate. |
| `request` | `Any` |  | The incoming Aquilia HTTP request object. |
| `projection` | `str \| None` | `None` | Optional projection name to restrict or filter validated data. |
| `partial` | `bool` | `False` | If True, fields not supplied in the request are ignored (useful for PATCH routes). |
| `context` | `dict[str, Any] \| None` | `None` | Extra context mapping (e.g. dependency injection container info) to supply to the ContractContext. |


#### Return Type
- `Contract`: An instantiated Contract instance with input data merged and validation executed (the instance will have been sealed).

#### When to Use
This is the core integration point between the controller execution engine and the Contract framework. It is invoked when a controller endpoint receives an incoming request containing an annotated Contract argument. The function extracts values from JSON payloads, form data, file uploads, query parameters, headers, cookies, and path parameters, and merges them into a single validation mapping.

> [!IMPORTANT]
> The function implements security limits such as verifying the request content length against `MAX_BODY_SIZE` (default 10 MB, configurable via context) to prevent resource exhaustion attacks.
> 
> Defined in [integration.py:L298-538](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/integration.py#L298-538).

---

### `render_contract_response()`

Render Python model instances or lists of data using a designated Contract for client response output.

#### Signature
```python
def render_contract_response(
    contract_or_cls: Contract | type[Contract],
    data: Any = None,
    *,
    projection: str | None = None,
    many: bool = False,
) -> Any:
```

#### Parameters
| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `contract_or_cls` | `Contract \| type[Contract]` |  | An existing Contract instance, a Contract class, or a projected Contract reference. |
| `data` | `Any` | `None` | The data to render (a single model instance, dictionary, or a collection of elements). |
| `projection` | `str \| None` | `None` | The projection name to apply during serialization (only used when contract_or_cls is a class). |
| `many` | `bool` | `False` | Set to True if the input data represents a list/collection of records. |


#### Return Type
- `Any`: A dictionary (or list of dictionaries) containing the serialized contract data ready for JSON serialization.

#### When to Use
Use this function in controller action responses (or route response formatters) to serialize model objects, raw dictionaries, or database collections back to the client. It handles:
- Passing in an already instantiated Contract (updates its instance reference and accesses `.data`).
- Passing in a class/projected reference (creates an instance and accesses `.data`).

> [!NOTE]
> Defined in [integration.py:L541-581](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/contracts/integration.py#L541-581).
