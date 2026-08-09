# Native Router Memory Leak Fix — v1.4.0b3

## Overview

In Aquilia v1.4.0b1 and v1.4.0b2, native C++ extensions (`aquilia._core.Router`) were introduced to accelerate HTTP route matching. During server shutdown, ASGI lifespan termination, or test suite execution, compiled native C++ `Router` instances could remain referenced by Python objects, producing nanobind leak warnings on process exit:

```
nanobind: leaked 1 instance of type 'aquilia._core.Router'!
```

Aquilia v1.4.0b3 resolves these leak warnings by implementing explicit native resource deallocation routines across `ControllerRouter`, `AquiliaServer`, and `ASGIAdapter`.

---

## Root Cause Analysis

1. **`ControllerRouter` Ownership**: `ControllerRouter` held a long-lived reference to `_native` (`aquilia._core.Router`). When routes were recompiled or the router was shut down, internal native method arrays (`_native_methods`, `_native_routes`) were cleared, but the primary `_native` C++ object reference was retained.
2. **Server Lifespan Teardown**: `AquiliaServer.shutdown()` closed database connections and cancelled tasks, but did not instruct its `controller_router` instance to release its native engine handles.
3. **ASGI Lifespan Teardown**: `ASGIAdapter` held circular references in `_cached_middleware_chain`, `_default_container`, and `_server_runtime`, preventing the underlying server instance from being garbage collected at the end of ASGI lifespan `lifespan.shutdown`.

---

## Technical Solution

### 1. `ControllerRouter.clear()` API

`ControllerRouter` now exposes an explicit `.clear()` method that releases all C++ extension references and resets compiler state:

```python
# aquilia/controller/router.py

class ControllerRouter:
    def clear(self) -> None:
        """Clear all route indices and release native engine resources."""
        self.compiled_controllers.clear()
        self.routes_by_method.clear()
        self.matcher = PatternMatcher()
        self._static_routes.clear()
        self._dynamic_routes.clear()
        self._tries.clear()
        self._name_index.clear()
        self._native_methods.clear()
        self._native_routes.clear()
        self._native = None  # Release nanobind C++ extension handle
        self._initialized = False
```

`ControllerRouter.initialize()` also invokes this cleanup prior to building new native route tables, preventing orphan C++ references during hot-reloads.

---

### 2. `AquiliaServer.shutdown()` Integration

`AquiliaServer.shutdown()` now invokes `clear()` on its `controller_router`:

```python
# aquilia/server.py

async def shutdown(self) -> None:
    # ... database disconnect & task cancellation ...

    # Clear controller router and release native engine resources
    if hasattr(self, "controller_router") and self.controller_router is not None:
        try:
            self.controller_router.clear()
        except Exception as e:
            self.logger.warning(f"Error clearing controller router: {e}")

    self._startup_complete = False
```

---

### 3. `ASGIAdapter.shutdown()` Clean Teardown

`ASGIAdapter` implements a dedicated `.shutdown()` method that is invoked during ASGI `lifespan.shutdown`:

```python
# aquilia/asgi.py

class ASGIAdapter:
    async def shutdown(self) -> None:
        """Shutdown underlying server and release cached references."""
        if self.server:
            await self.server.shutdown()
        self._cached_middleware_chain = None
        self._default_container = None
        self._server_runtime = None
```

---

## Verification & Unit Testing

The fix is verified in `tests/engine/test_memory.py`:

```python
def test_controller_router_clear_releases_native_instance() -> None:
    router = ControllerRouter()
    router.initialize()
    assert router._native is not None

    router.clear()
    assert router._native is None
    assert not router._initialized

@pytest.mark.asyncio
async def test_server_shutdown_clears_controller_router_native_instance() -> None:
    server = AquiliaServer(manifests=[manifest], config=loader)
    server.controller_router.initialize()
    server._startup_complete = True

    assert server.controller_router._native is not None

    await server.shutdown()
    assert server.controller_router._native is None
```

All 49 CLI and engine memory tests pass cleanly without emitting nanobind warnings.
