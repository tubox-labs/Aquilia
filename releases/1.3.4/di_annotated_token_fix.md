# DI String Token Resolution & RequestDAG Hardening — Release Notes

## Executive Summary

Aquilia v1.3.4 includes a critical resolution and type-introspection fix for the Dependency Injection (`aquilia.di`) container engine. This release fixes `PROVIDER_NOT_FOUND` errors encountered when using string tokens within `Annotated` type hints (e.g., `cross_app: Annotated[Any, Inject("modules.auth.services:CrossAppService")]`), unifies descriptor unwrapping across `Container` and `RequestDAG`, and adds exhaustive docstrings across all `Inject`, `Dep`, and `RequestDAG` APIs.

---

## Issue & Root Cause Analysis

### The Bug
When declaring cross-module or string-tokenized dependencies in controllers, services, or handler signatures using `typing.Annotated`:
```python
cross_app: typing.Annotated[typing.Any, Inject("modules.auth.services:CrossAppService")]
```
the container resolution engine raised a `ProviderNotFoundError`:
```text
DI provider 'typing.Annotated[typing.Any, Inject(token='modules.auth.services:CrossAppService', tag=None, optional=False, _inject_token='modules.auth.services:CrossAppService', _inject_tag=None, _inject_optional=False)]' not found
```

### Root Causes
1. **Container Token Key Stringification (`aquilia/di/core.py`)**:
   `Container._token_to_key(token)` checked `isinstance(token, str)` and `isinstance(token, type)`. Because `typing.Annotated[T, ...]` is represented internally as a `_AnnotatedAlias` rather than a standard `type`, both checks failed. The method fell through to `str(token)`, turning the entire annotation object into the string key `"typing.Annotated[typing.Any, Inject(...)]"`, causing container lookups to search for that string literal rather than extracting the target token `"modules.auth.services:CrossAppService"`.

2. **Annotation Unpacking (`aquilia/di/dep.py`)**:
   `_unpack_annotation(annotation)` extracted `base_type = args[0]` (which was `typing.Any`) and ignored `Inject._inject_token` / `Inject.token` when mapping `Inject` to `Dep`. Sub-dependency resolution then attempted to resolve `typing.Any` from the container instead of the explicit string token.

3. **Auto-Inject Type Hint Stripping (`aquilia/di/decorators.py`)**:
   `@auto_inject` called `get_type_hints(func)` without `include_extras=True`, which stripped `Annotated` metadata before handing the parameter hint to `container.resolve_async()`.

---

## Technical Solution

### 1. Recursive Token & Metadata Unwrapper (`Container._unwrap_token`)
In `aquilia/di/core.py`, added `Container._unwrap_token()`:
```python
def _unwrap_token(
    self,
    token: Any,
    tag: str | None = None,
    optional: bool = False,
) -> tuple[Any, str | None, bool]:
    """
    Unwrap Annotated[T, Inject(...)] / Annotated[T, Dep(...)] / Inject(...) / Dep(...) / Optional[T].

    Returns:
        Tuple of (unwrapped_token, effective_tag, effective_optional).
    """
```
- Operates recursively over `Annotated[T, Inject(...)]`, `Annotated[T, Dep(...)]`, direct `Inject` instances, and `Optional[T]` unions.
- Extracts `_inject_token` / `token`, `_inject_tag` / `tag`, and `_inject_optional` / `optional` metadata flags.
- Used consistently across `Container.resolve()`, `Container.resolve_async()`, `Container.is_registered()`, `Container._token_to_key()`, and `Container._resolve_from_container()`.

### 2. Enhanced Annotation Unpacker (`_unpack_annotation`)
In `aquilia/di/dep.py`, updated `_unpack_annotation()`:
```python
if isinstance(meta, _get_inject_class()) or hasattr(meta, "_inject_token"):
    injected_tok = getattr(meta, "_inject_token", None) or getattr(meta, "token", None)
    target_type = injected_tok if injected_tok is not None else base_type
    return (
        target_type,
        Dep(
            tag=getattr(meta, "tag", None) or getattr(meta, "_inject_tag", None),
        ),
    )
```

### 3. Auto-Inject Extra Preservations
In `aquilia/di/decorators.py`, updated `@auto_inject` to execute `get_type_hints(func, include_extras=True)` to preserve `Inject` markers on function parameters.

### 4. Comprehensive Docstrings
Added detailed, standardized docstrings featuring `Args:`, `Returns:`, `Note:`, and `Usage::` blocks across:
- `Inject` & `inject` (`aquilia/di/decorators.py`)
- `Dep` (`aquilia/di/dep.py`)
- `RequestDAG` and all DAG methods/helpers (`aquilia/di/request_dag.py`)
- Core DAG resolution methods (`aquilia/di/core.py`)

---

## Code Example

### Cross-App String Token Injection
```python
from typing import Annotated, Any
from aquilia.di import Container, Inject, auto_inject

class CrossAppService:
    def get_status(self) -> str:
        return "active"

container = Container()
svc = CrossAppService()
await container.register_instance("modules.auth.services:CrossAppService", svc)

# 1. Direct container resolution via Annotated string token
cross_app = await container.resolve_async(
    Annotated[Any, Inject("modules.auth.services:CrossAppService")]
)
assert cross_app.get_status() == "active"

# 2. Constructor parameter injection
class AuthController:
    def __init__(
        self,
        cross_app: Annotated[Any, Inject("modules.auth.services:CrossAppService")],
    ):
        self.cross_app = cross_app

container.bind(AuthController, AuthController)
controller = await container.resolve_async(AuthController)
assert controller.cross_app is svc
```

---

## Verification & Test Results

A new brutal regression test suite was added to [`tests/test_di_annotated_inject_fix.py`](../../tests/test_di_annotated_inject_fix.py), verifying:
1. Sync & Async resolution of `Annotated[Any, Inject("token")]`.
2. Lowercase `inject("token")` helper functions.
3. Tagged and optional dependency fallbacks.
4. Direct `Inject("token")` marker resolution.
5. Constructor (`ClassProvider`) parameter injection.
6. Factory (`FactoryProvider`) parameter injection.
7. `RequestDAG` resolution of string-tokenized `Dep` lookups.
8. `@auto_inject` function resolution.
9. Cross-app linked containers (`add_dependency_link`) resolution.

### Test Execution Summary
```bash
./.venv/bin/pytest tests/test_di_system.py tests/test_di_enterprise_features.py tests/test_di_production_hardening.py tests/test_dep_precedence.py tests/test_di_annotated_inject_fix.py
======================== 287 passed in 1.51s ========================
```
