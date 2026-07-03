---
title: "Blueprint Exceptions"
description: "Detailed guide to the BlueprintFault error hierarchy and fault domain in Aquilia"
icon: lucide/alert-triangle
---
## Overview

All validation and execution errors in Blueprints participate in Aquilia's unified fault domain system. They inherit from a common base class, `BlueprintFault`, and provide structured payloads for API error responses.

---

## The BLUEPRINT Fault Domain

!!! info
    Evidence: `aquilia/blueprints/exceptions.py:16-19`


Aquilia groups Blueprint-related errors under a single fault domain [BLUEPRINT](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L16-L19).

```python
BLUEPRINT = FaultDomain(
    name="BLUEPRINT",
    description="Blueprint contract violations -- casting, sealing, imprinting",
)
```

---

## Base Exception: BlueprintFault

!!! info
    Evidence: `aquilia/blueprints/exceptions.py:25-57`


[BlueprintFault](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L25-L57) is the base exception class for all Blueprint errors. It inherits from `Fault` and exposes the following settings:
- **Domain**: [BLUEPRINT](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L16-L19)
- **Severity**: `Severity.ERROR`
- **Default Code**: `"BP000"`
- **Public**: `True` (meaning it is safe to return to API clients)

### Signature
```python
def __init__(
    self,
    message: str = "Blueprint validation failed",
    *,
    errors: dict[str, list[str]] | None = None,
    code: str | None = None,
    metadata: dict[str, Any] | None = None,
):
```

### JSON Response Format
The [as_response_body](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/blueprints/exceptions.py#L48-L56) method converts the exception into a structured payload for HTTP responses:
```json
{
  "fault": "BP000",
  "message": "Blueprint validation failed",
  "errors": {
    "field_name": ["Error message"]
  }
}
```

---

## Specific Blueprint Exceptions

### CastFault (BP100)

!!! info
    Evidence: `aquilia/blueprints/exceptions.py:62-80`


Raised when incoming data cannot be coerced into the type required by the field's Facet.

- **Fault Code**: `BP100`
- **Key attributes**: `field` (name of the field that failed casting)
- **Example payload**:
  ```json
  {
    "fault": "BP100",
    "message": "Cast failed for 'age': Invalid value",
    "errors": {
      "age": ["Invalid value"]
    }
  }
  ```

---

### SealFault (BP200)

!!! info
    Evidence: `aquilia/blueprints/exceptions.py:82-109`


Raised when one or more validation constraints are broken during the blueprint sealing phase (such as custom `@ward` methods or facet validation constraints).

- **Fault Code**: `BP200`
- **Key attributes**: `field_errors` (mapping of field names to their validation error lists)
- **Error details construction**: If a single field fails, it populates `metadata["details"]` with `{"field": ..., "reason": ...}`. For multiple fields, it populates `{"fields": [{"field": ..., "reasons": ...}, ...]}`.

---

### ImprintFault (BP300)

!!! info
    Evidence: `aquilia/blueprints/exceptions.py:111-115`


Raised when writing (imprinting) validated data back to the database or model instance fails.

- **Fault Code**: `BP300`

---

### ProjectionFault (BP400)

!!! info
    Evidence: `aquilia/blueprints/exceptions.py:117-127`


Raised when a projection requested by name is not found in the blueprint spec.

- **Fault Code**: `BP400`
- **Key attributes**: `projection` (the requested projection name), `available` (list of valid projection names configured in the Spec)

---

### LensDepthFault (BP500)

!!! info
    Evidence: `aquilia/blueprints/exceptions.py:129-139`


Raised when traversing nested relationships using Lenses exceeds the configured maximum depth limit.

- **Fault Code**: `BP500`
- **Key attributes**: `path` (traversal path where the limit was hit), `max_depth` (the maximum allowed depth limit)

---

### LensCycleFault (BP501)

!!! info
    Evidence: `aquilia/blueprints/exceptions.py:141-150`


Raised when a circular reference loop is detected during Lens modeling.

- **Fault Code**: `BP501`
- **Key attributes**: `cycle_path` (the list of fields showing the cycle loop, e.g., `["author", "posts", "author"]`)

---

## Code Example

Catching and responding with Blueprint validation faults:

```python
from aquilia.blueprints import Blueprint, IntFacet, TextFacet
from aquilia.blueprints.exceptions import BlueprintFault

class UserBlueprint(Blueprint):
    class Spec:
        fields = {
            "id": IntFacet(),
            "username": TextFacet(min_length=3),
        }

try:
    bp = UserBlueprint(data={"username": "ab"}) # Too short
    if not bp.is_sealed():
        # Will raise SealFault or we can raise it manually
        pass
except BlueprintFault as fault:
    print(fault.as_response_body())
    # Output:
    # {
    #   'fault': 'BP200',
    #   'message': 'Blueprint validation failed',
    #   'errors': {'username': ['Must be at least 3 characters']}
    # }
```
