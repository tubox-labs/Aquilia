# Resource / ViewSet CRUD Controllers

Aquilia v1.3.4 introduces `Resource` controllers (located in `aquilia/controller/resource.py`), bringing robust, DRY, auto-generated CRUD routing to the framework. Inspired by Django REST Framework's ViewSets, this feature integrates natively with Aquilia's asynchronous architecture and controller routing.

## Motivation & DX Goals

Writing standard CRUD endpoints (`GET /`, `GET /{id}`, `POST /`, `PUT /{id}`, `DELETE /{id}`) in plain Controllers requires significant boilerplate. The `Resource` base class eliminates this by leveraging `__init_subclass__` to automatically register routes based on the presence of predefined method names, heavily reducing boilerplate while maintaining complete customization.

## API Reference

### `Resource[T]`

The base generic class inheriting from `Controller`. It maps specific method names to specific RESTful routes:

| Method defined in subclass | Auto-Generated Route |
|----------------------------|----------------------|
| `list` | `GET /` |
| `retrieve` | `GET /{id:type}` |
| `create` | `POST /` |
| `update` | `PUT /{id:type}` |
| `partial_update` | `PATCH /{id:type}` |
| `destroy` | `DELETE /{id:type}` |

**Class Variables:**
- `id_param: str = "id"`: The name of the path parameter.
- `id_type: str = "int"`: The type castor for the path parameter (e.g., `"int"`, `"str"`, `"uuid"`).
- `lookup_field: str = "id"`: Alias for `id_param`.
- `actions: set[str] | None`: An explicit allowlist of CRUD actions to generate. If `None`, it generates routes for any method you've implemented.

### Mixins and Flavors

Aquilia provides pre-configured combinations:

- **`ReadOnlyResource[T]`**: Inherits `ListMixin`, `RetrieveMixin`.
- **`CRUDResource[T]`**: Inherits `ListMixin`, `RetrieveMixin`, `CreateMixin`, `UpdateMixin`, `DestroyMixin`.

Mixins simply define the async method signatures (raising `NotImplementedError` if not overridden), which prompts the `Resource` metaclass to generate the routes.

### `@action` Decorator

Use the `@action` decorator to add custom, non-standard routes to a resource.

```python
from aquilia.controller.resource import action

@action(methods=["POST"], detail=True, url_path="deactivate")
async def deactivate_user(self, ctx, id: int):
    # Generates: POST /{id:int}/deactivate
    ...
```

- `detail=True`: Injects the `{id:type}` path segment.
- `detail=False`: Mounts directly to `/url_path`.

## Examples

### Complete CRUD Implementation

```python
from aquilia.controller.resource import CRUDResource, action
from aquilia.controller.decorators import GET

class UserResource(CRUDResource):
    id_param = "user_id"
    id_type = "uuid"
    
    async def list(self, ctx):
        return await User.objects.all()

    async def retrieve(self, ctx, user_id):
        return await User.objects.get(id=user_id)

    async def create(self, ctx, payload: UserCreateRequest):
        return await User.create(**payload.dict())

    async def destroy(self, ctx, user_id):
        await User.objects.filter(id=user_id).delete()
        return None

    @action(methods=["GET"], detail=True)
    async def permissions(self, ctx, user_id):
        # Route: GET /{user_id:uuid}/permissions
        return {"perms": ["read", "write"]}
```

## Integration with Pipeline, Throttle, and Clearances

Because `Resource` is a transparent subclass of `Controller`, all existing controller-level features apply flawlessly. You can define `pipeline`, `clearance`, and `throttle` at the class level exactly as you would for a standard controller.

```python
class SecureAdminResource(CRUDResource):
    clearance = AccessLevel.ADMIN
    pipeline = Pipeline().guard(AuthGuard)
    
    async def list(self, ctx):
        pass
```

## Limitations

- The metaclass route generation occurs at class definition time (`__init_subclass__`). It generates routes with standard Aquilia decorators transparently, so they appear to the `ControllerCompiler` as standard routes. 
- You still need to implement the actual DB logic within the methods. (Full Model-View integration is outside the scope of the routing layer).
