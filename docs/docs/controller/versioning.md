---
title: "Versioning"
description: "API versioning at the controller and route levels in Aquilia"
icon: lucide/git-branch
---Aquilia provides a flexible, declarative routing and API versioning system. Versioning can be defined globally at the controller level or overridden at the individual route level. Under the hood, version bindings are extracted during compile-time/registration and stored directly on controller method functions as metadata.

This guide covers how versioning is implemented and configured in Aquilia.

---

## Controller-Level Versioning

At the controller level, versioning is defined by setting the `version` class attribute.

As defined in [`aquilia/controller/base.py`](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L556):
```python
class Controller(metaclass=_ControllerMeta):
    # ...
    version: str | None = None  # API version: "v1", "v2", etc.
```

When you specify `version` on a subclass of [`Controller`](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L497), it establishes the default API version for all routes defined in that controller.

For example, see [`aquilia/controller/base.py` line 532-538](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/base.py#L532-L538):
```python
class UsersController(Controller):
    prefix = "/users"
    version = "v1"
    # ...
```

---

## Route-Level Versioning

Individual route decorators allow you to override or extend the controller's default version using the `version` parameter.

In [`aquilia/controller/decorators.py` line 64](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L64), the base class [`RouteDecorator`](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L30) supports a `version` parameter in its constructor:

```python
class RouteDecorator:
    def __init__(
        self,
        path: str | None = None,
        *,
        # ...
        # ── API Versioning ───────────────────────────────────────────
        version: str | list[str] | None = None,
    ):
```

This parameter is saved as an instance attribute (`self.version`) at [`aquilia/controller/decorators.py` line 122](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L122):
```python
        self.version = version
```

All standard HTTP decorators inherit this parameter, including:
- [`GET`](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L180) (line 204)
- [`POST`](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L230) (line 254)
- [`PUT`](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L280) (line 304)
- [`PATCH`](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L330) (line 354)
- [`DELETE`](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L380) (line 404)
- [`route`](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L630) (line 651)

Setting `version` on a route decorator overrides the controller-level `version` attribute for that specific route (see [`aquilia/controller/decorators.py` lines 98-101](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L98-L101)).

---

## Metadata Storage: `__version_metadata__`

When a controller method is decorated with a route decorator, metadata is extracted and stored directly on the decorated function.

First, standard route metadata is collected into a `metadata` dictionary and appended to the function's `__route_metadata__` list. This includes storing the version at [`aquilia/controller/decorators.py` line 162](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L162):
```python
            "version": self.version,
```

Second, if `version` is specified, the decorator attaches or updates the [`__version_metadata__`](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L168-L175) attribute on the function. This attribute is used during server registration.

As shown in [`aquilia/controller/decorators.py` lines 168-175](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L168-L175):
```python
        if self.version is not None:
            if not hasattr(func_any, "__version_metadata__"):
                func_any.__version_metadata__ = {}
            versions = self.version if isinstance(self.version, list) else [self.version]
            existing = func_any.__version_metadata__.get("versions", [])
            func_any.__version_metadata__["versions"] = list(
                dict.fromkeys(existing + versions),  # deduplicate, preserve order
            )
```

The system initializes [`__version_metadata__`](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L168-L175) as a dictionary containing a `"versions"` key mapped to a list of version strings.

---

## List vs Single Version Binding

Aquilia supports binding routes to either a single version or multiple versions simultaneously:
1. **Single Version**: You can pass a string (e.g., `version="1.0"`).
2. **Multiple Versions**: You can pass a list of strings (e.g., `version=["1.0", "2.0"]`).

The decorator normalizes the input into a list of strings when saving to [`__version_metadata__`](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L168-L175) (see [`aquilia/controller/decorators.py` line 171](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L171)):
```python
            versions = self.version if isinstance(self.version, list) else [self.version]
```

This allows a single handler method to handle requests across multiple distinct API versions without repeating the route decoration.

---

## Deduplication and Order Preservation

Aquilia prevents double decoration and metadata pollution through two levels of deduplication:

### 1. Route Metadata Deduplication
To prevent the same route (matching HTTP method and URL path) from being added multiple times to a handler's `__route_metadata__` list, the decorator performs a check at [`aquilia/controller/decorators.py` lines 136-138](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L136-L138):

```python
        for existing in func_any.__route_metadata__:
            if existing["http_method"] == self.method and existing["path"] == self.path:
                return func
```

If a matching method and path combination is already present, the decorator returns the function early without adding duplicate metadata.

### 2. Version List Deduplication
When multiple decorators or multiple version arguments are used, version lists are merged and deduplicated while preserving their declaration order. This is achieved using `dict.fromkeys()` at [`aquilia/controller/decorators.py` lines 173-175](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/decorators.py#L173-L175):

```python
            func_any.__version_metadata__["versions"] = list(
                dict.fromkeys(existing + versions),  # deduplicate, preserve order
            )
```

By leveraging `dict.fromkeys()`, Aquilia ensures that versions are unique list elements while keeping the original order intact.

---

## Versioning Configurations Reference



---

## Code Examples

Here is a complete example demonstrating controller-level versioning, route-level version overrides, list version binding, and multi-decorator version accumulation:

```python
from aquilia.controller.base import Controller
from aquilia.controller.decorators import GET, POST, route

class MyController(Controller):
    prefix = "/items"
    
    # 1. Controller-level version: default for all routes in this controller is "v1"
    version = "v1"

    @GET("/")
    async def list_items(self, ctx):
        # Uses the default controller version: "v1"
        return {"items": []}

    # 2. Route-level version override (Single Version)
    @GET("/{id:int}", version="v2")
    async def get_item(self, ctx, id: int):
        # Overrides controller default; only accessible via "v2"
        return {"id": id, "version": "v2"}

    # 3. Route-level version override (Multiple Versions)
    @POST("/", version=["v1.1", "v2"])
    async def create_item(self, ctx):
        # Accessible via both "v1.1" and "v2" API versions
        return {"status": "created"}

    # 4. Multi-decorator version accumulation
    # Applying multiple route decorators accumulating version lists
    @route("GET", "/search", version="v1")
    @route("GET", "/search", version="v2")
    async def search_items(self, ctx):
        # Thanks to `dict.fromkeys` deduplication, __version_metadata__["versions"]
        # will cleanly resolve to ["v2", "v1"] (depending on decorator execution order)
        return {"results": []}
```

!!! info "Compilation Metadata"
    Behind the scenes, Aquilia's application routing engine parses `__version_metadata__` and `__route_metadata__` to register the appropriate URL handlers for version-based request dispatching.

