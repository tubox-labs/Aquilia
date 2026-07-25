# Resource ViewSets

In Aquilia, a `Resource` (often known as a ViewSet in other frameworks like Django REST Framework) is a controller abstraction that auto-generates RESTful CRUD routes. Instead of writing separate `@GET`, `@POST`, `@PUT`, and `@DELETE` decorators for standard operations, you can inherit from `Resource` and simply implement the corresponding methods.

This pattern drastically reduces boilerplate while maintaining full compatibility with the existing Controller ecosystem (pipelines, throttling, interceptors).

## Why use Resource ViewSets?

### Before: Plain Controller Boilerplate

```python
from aquilia.controller import Controller, GET, POST, PUT, PATCH, DELETE

class PostController(Controller):
    prefix = "/posts"

    @GET("/")
    async def list_posts(self, ctx):
        pass

    @GET("/{id:int}")
    async def retrieve_post(self, ctx, id: int):
        pass

    @POST("/")
    async def create_post(self, ctx):
        pass

    @PUT("/{id:int}")
    async def update_post(self, ctx, id: int):
        pass

    @DELETE("/{id:int}")
    async def destroy_post(self, ctx, id: int):
        pass
```

### After: Resource ViewSet

```python
from aquilia.controller.resource import CRUDResource

class PostResource(CRUDResource[Post]):
    prefix = "/posts"

    async def list(self, ctx):
        pass

    async def retrieve(self, ctx, id: int):
        pass

    async def create(self, ctx):
        pass

    async def update(self, ctx, id: int):
        pass

    async def destroy(self, ctx, id: int):
        pass
```

## `Resource[T]` Base Class

The `Resource[T]` class is a generic `Controller`. It provides the foundation for auto-registering standard REST methods.

### Class Variables

You can customize the route parameters generated for detailed views by overriding these class variables:

- `id_param` (str, default `"id"`): The name of the path parameter used for detailed routes. (Can also be set via `lookup_field`).
- `id_type` (str, default `"int"`): The path parameter type converter (e.g., `"int"`, `"str"`, `"uuid"`).
- `actions` (set[str] | None): If specified, only the standard CRUD actions listed in this set will be auto-registered.
- `model` / `serializer` (type | None): Optional hooks for integrating with generic ORM bindings and validation.

### Auto-Registered Routes

When you implement any of the following method names on a `Resource`, they are automatically wrapped in the appropriate routing decorator:

| Method Name      | HTTP Verb | Path              | Description                          |
|------------------|-----------|-------------------|--------------------------------------|
| `list`           | `GET`     | `/`               | Retrieve a collection of items       |
| `retrieve`       | `GET`     | `/{id:int}`       | Retrieve a single item by ID         |
| `create`         | `POST`    | `/`               | Create a new item                    |
| `update`         | `PUT`     | `/{id:int}`       | Fully replace an existing item       |
| `partial_update` | `PATCH`   | `/{id:int}`       | Partially modify an existing item    |
| `destroy`        | `DELETE`  | `/{id:int}`       | Delete an existing item              |

*(Assuming `id_param="id"` and `id_type="int"`)*

## The `@action` Decorator

If you need a custom endpoint outside the standard CRUD operations (e.g., publishing a post, fetching recent comments), use the `@action` decorator.

```python
from aquilia.controller.resource import Resource, action

class PostResource(Resource[Post]):
    # A detail route operates on a specific instance
    # Path: POST /posts/{id:int}/publish
    @action(methods=["POST"], detail=True)
    async def publish(self, ctx, id: int):
        pass

    # A non-detail (collection) route operates on the whole collection
    # Path: GET /posts/recent
    @action(methods=["GET"], detail=False)
    async def recent(self, ctx):
        pass
```

### `@action` Parameters

- `methods` (list[str]): A list of HTTP verbs (default `["GET"]`).
- `detail` (bool): If `True`, the `id_param` is prepended to the path (e.g. `/{id:int}/{url_path}`). If `False`, it applies to the base URL (`/{url_path}`).
- `url_path` (str | None): The URL segment for this action. If omitted, defaults to the method name.
- `**kwargs`: Any additional arguments are forwarded to the underlying `@route` decorator (e.g., `summary`, `response_model`, `tags`).

## Mixins and Pre-built Resources

Aquilia provides mixins for composing your own Resource bases, as well as a few pre-packaged bases:

- **Mixins:** `ListMixin`, `RetrieveMixin`, `CreateMixin`, `UpdateMixin`, `DestroyMixin`.
- **`ReadOnlyResource[T]`**: Inherits from `Resource[T]`, `ListMixin`, and `RetrieveMixin`. Good for read-only models.
- **`CRUDResource[T]`**: Inherits from `Resource[T]` and all 5 standard CRUD mixins.

```python
from aquilia.controller.resource import Resource, CreateMixin, RetrieveMixin

class AppendOnlyResource(CreateMixin, RetrieveMixin, Resource[MyModel]):
    # Only `/` (POST) and `/{id:int}` (GET) will be routed.
    pass
```

## Integration with Controller Features

`Resource` is a subclass of `Controller`. Everything that works on a standard controller works here:

- **Throttling**: `throttle = Throttle(limit=10, window=60)`
- **Pipelines / Guards**: `pipeline = [Auth.guard()]`
- **Prefixes**: `prefix = "/v1/users"`
- **Interceptors**: Pre/post request hooks apply natively.

## Limitations and Edge Cases

- **Custom Decorator Ordering**: Because `Resource` auto-generates routes inside `__init_subclass__`, manual `@GET` / `@POST` decorators on standard method names (`list`, `create`, etc.) may cause duplicate route metadata if not careful. Stick to the implicit auto-registration for standard methods, and use `@action` for custom ones.
- **Route Conflicts**: If you define an `@action(detail=False, url_path="123")` and a standard `retrieve` method, a request to `/123` might conflict depending on route specificity. (Aquilia's routing tree usually prioritizes static strings over path variables, but it's best to avoid ambiguous URLs).
