---
title: "Instantiation Modes"
description: "Understanding Controller lifecycles and instantiation modes in Aquilia"
icon: lucide/cpu
---Aquilia controllers support two distinct instantiation modes that govern their lifecycle, memory footprint, and dependency resolution. These modes are managed by [ControllerFactory](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L24) during application runtime.

---

## The InstantiationMode Enum

The [InstantiationMode](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L17) enum (defined in [aquilia/controller/factory.py:L17-L21](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L17-L21)) determines the lifecycle behavior of a controller:

```python
class InstantiationMode(str, Enum):
    PER_REQUEST = "per_request"
    SINGLETON = "singleton"
```

- **`PER_REQUEST`** ([factory.py:L20](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L20)): A new instance of the controller is created for each incoming request.
- **`SINGLETON`** ([factory.py:L21](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L21)): A single instance of the controller is created once, cached, and shared across all requests.

---

## ControllerFactory.create Method Signature

The factory instantiates controllers using the asynchronous [ControllerFactory.create()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L43) method (defined in [aquilia/controller/factory.py:L43-L72](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L43-L72)):

```python
async def create(
    self,
    controller_class: type,
    mode: InstantiationMode = InstantiationMode.PER_REQUEST,
    request_container: Any | None = None,
    ctx: Any | None = None,
) -> Any:
```

### Parameter Details

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `controller_class` | `type` |  | The controller class type to be instantiated. |
| `mode` | `InstantiationMode` | `InstantiationMode.PER_REQUEST` | Governs whether the factory retrieves a cached instance or constructs a new one. |
| `request_container` | `Any \| None` | `None` | The request-scoped Dependency Injection container. |
| `ctx` | `Any \| None` | `None` | The request context used during instantiation or lifecycle hook invocation. |


---

## Singleton Caching Mechanism

When the controller is configured as a `SINGLETON`, the factory implements a caching mechanism within [ControllerFactory._create_singleton()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L74) (defined in [aquilia/controller/factory.py:L74-L102](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L74-L102)):

1. **Cache Lookup**: Before instantiating, the factory checks if the controller already exists in the `self._singletons` registry ([factory.py:L80-L81](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L80-L81)):
   ```python
   if controller_class in self._singletons:
       return self._singletons[controller_class]
   ```
2. **Scope Validation**: It performs validation to ensure the controller does not violate scope boundary rules ([factory.py:L84](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L84)).
3. **DI Resolution and Instantiation**: It resolves dependencies from the global application container (`self.app_container`) using [ControllerFactory._resolve_and_instantiate()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L126) and instantiates the controller ([factory.py:L87-L90](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L87-L90)).
4. **Hook Execution**: It executes the startup hook (see below) and stores the instance in the cache registry ([factory.py:L101](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L101)).

---

## Startup and Shutdown Hooks

### Startup Hook

For controllers running in `SINGLETON` mode, [ControllerFactory._create_singleton()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L74) ensures that the `on_startup` hook is executed exactly once ([factory.py:L93-L99](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L93-L99)):

```python
# Call on_startup hook once
if controller_class not in self._startup_called:
    if hasattr(instance, "on_startup"):
        if inspect.iscoroutinefunction(instance.on_startup):
            await instance.on_startup(ctx)
        else:
            instance.on_startup(ctx)
    self._startup_called.add(controller_class)
```

!!! warning
    The `on_startup` hook is **only** executed for singletons during their first instantiation.

    For per-request controllers, the factory does not invoke lifecycle hooks because the controller engine handles request/response hooks directly to avoid double invocation ([factory.py:L113-L114](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L113-L114)):
    ```python
    # NOTE: on_request is NOT called here -- the engine handles lifecycle
    # hooks to avoid double invocation.
    ```


### Shutdown Hook

During application shutdown, [ControllerFactory.shutdown()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L309) cleans up all singleton instances by invoking their `on_shutdown` hook ([aquilia/controller/factory.py:L309-L322](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L309-L322)):

```python
async def shutdown(self):
    """Shutdown all singleton controllers."""
    for controller_class, instance in self._singletons.items():
        if hasattr(instance, "on_shutdown"):
            try:
                if inspect.iscoroutinefunction(instance.on_shutdown):
                    await instance.on_shutdown(None)
                else:
                    instance.on_shutdown(None)
            except Exception as e:
                logger.error(
                    f"Error in {controller_class.__name__}.on_shutdown: {e}",
                    exc_info=True,
                )
```

---

## Dependency Injection and Constructor Resolution

To minimize performance overhead associated with run-time reflection (`inspect.signature` and `typing.get_type_hints`), the factory caches analyzed constructor parameters.

### Constructor Reflection Cache

Constructor parameters are cached in the class-level variable [ControllerFactory._ctor_info_cache](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L35-L36) ([factory.py:L35-L36](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L35-L36)):

```python
_ctor_info_cache: dict[type, Any] = {}  # class -> (sig, type_hints, param_specs)
```

During [ControllerFactory._resolve_and_instantiate()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L126), the factory checks the cache registry before analyzing the class constructor ([factory.py:L147-L150](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L147-L150)):

```python
ctor_info = ControllerFactory._ctor_info_cache.get(controller_class)
if ctor_info is None:
    ctor_info = self._analyze_constructor(controller_class)
    ControllerFactory._ctor_info_cache[controller_class] = ctor_info
```

### Analysis Process

The reflection logic resides in [ControllerFactory._analyze_constructor()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L178) ([factory.py:L178-L211](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L178-L211)):
- Iterates over the `__init__` signature parameters (skipping `self`, [factory.py:L195](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L195)).
- Extracts type hints using `typing.get_type_hints` ([factory.py:L184-L189](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L184-L189)).
- Performs intelligent parameter type inference: if a parameter has no type hint but has a default value that is a class type, it infers the parameter type as the class type ([factory.py:L201-L203](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L201-L203)).
- Returns a list of tuples containing `(param_name, param_type, has_default, default_val)` ([factory.py:L207](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L207)).

### Clearing Caches

The cache can be cleared programmatically using [ControllerFactory.clear_caches()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L395) ([factory.py:L395-L403](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L395-L403)) to avoid memory leaks during hot reload or test execution teardown:

```python
@classmethod
def clear_caches(cls):
    cls._ctor_info_cache.clear()
```

---

## Scope Validation and ScopeViolationError

Aquilia strictly validates dependency injection scopes to prevent **captive dependencies** (e.g., when a long-lived `SINGLETON` controller captures a short-lived request-scoped dependency).

If a validation boundary is crossed, a [ScopeViolationError](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L405) is raised ([aquilia/controller/factory.py:L405-L414](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L405-L414)):

```python
class ScopeViolationError(Exception):
    def __init__(self, controller_class: type, provider: type):
        self.controller_class = controller_class
        self.provider = provider
        super().__init__(
            f"Singleton controller {controller_class.__name__} cannot "
            f"inject request-scoped provider {provider.__name__}"
        )
```

### Validation Execution

Validation occurs during singleton creation inside [ControllerFactory.validate_scope()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L324) ([aquilia/controller/factory.py:L324-L386](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L324-L386)):

```python
# Check provider scope -- use public API where available
provider = None
if hasattr(self.app_container, "get_provider"):
    provider = self.app_container.get_provider(param_type)
...
if provider and hasattr(provider, "meta") and hasattr(provider.meta, "scope"):
    # Singleton/App controllers CANNOT depend on Request/Ephemeral scopes
    if provider.meta.scope in ("request", "ephemeral", "transient"):
        raise ScopeViolationError(controller_class, param_type)
```

---

## Architectural Comparison: When to Use Which?

Choosing the right mode is critical for application reliability and speed:

| Instantiation Mode | Scope Lifetime | Recommended Use Cases | Scope Violations |
| :--- | :--- | :--- | :--- |
| **`SINGLETON`** | Application-wide (Created once) | Stateless controllers, global caches, configuration services, logging proxies. | Throws [ScopeViolationError](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L405) if requesting `request`, `ephemeral`, or `transient` services. |
| **`PER_REQUEST`** | Single Request (Created per request) | Controllers injecting request context, user sessions, request-scoped transactions, or tenant databases. | No scope restrictions; can inject all scopes. |

---

## Code Examples

### 1. Singleton Controller (Stateless)

This controller resolves global application-scoped dependencies and executes `on_startup` once:

```python
from aquilia.controller.base import Controller
from aquilia.controller.factory import InstantiationMode
from myapp.services import GlobalConfigService

class MetricsController(Controller):
    instantiation_mode = InstantiationMode.SINGLETON

    def __init__(self, config: GlobalConfigService):
        self.config = config

    async def on_startup(self, ctx):
        # Executes exactly once when the first request triggers instantiation
        await self.config.load_defaults()
```

### 2. Per-Request Controller (Stateful)

This controller resolves request-scoped dependencies, such as the current database session:

```python
from aquilia.controller.base import Controller
from aquilia.controller.factory import InstantiationMode
from myapp.db import DbSession

class UserController(Controller):
    instantiation_mode = InstantiationMode.PER_REQUEST

    def __init__(self, db: DbSession):
        self.db = db  # Resolved from the request_container (unique per request)
```

### 3. Scope Violation Example

The following code is invalid and will trigger a [ScopeViolationError](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/factory.py#L405) at runtime because a singleton attempts to inject a request-scoped dependency:

```python
from aquilia.controller.base import Controller
from aquilia.controller.factory import InstantiationMode
from myapp.auth import CurrentUserContext  # Scope: "request"

class AdminController(Controller):
    instantiation_mode = InstantiationMode.SINGLETON

    # Error: Cannot inject a request-scoped provider into a singleton controller!
    def __init__(self, auth_ctx: CurrentUserContext):
        self.auth_ctx = auth_ctx
```
