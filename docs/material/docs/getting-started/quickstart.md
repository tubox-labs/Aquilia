# Quickstart

Build and serve an Aquilia application in under 5 minutes. This guide assumes Python 3.10+ and `pip install aquilia` are already set up.

---

## Step 1 — Create a Workspace

Every Aquilia project starts with a workspace. The `aq init` command scaffolds the directory structure:

```bash
aq init workspace my-api
cd my-api
```

This creates:

```
my-api/
├── workspace.py          # Orchestration root — modules, integrations, security
├── config/
│   └── __init__.py
├── .env.example
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

The generated `workspace.py` is immediately runnable:

```python
from aquilia import Module, Workspace
from aquilia.integrations import DiIntegration, RoutingIntegration, FaultHandlingIntegration

workspace = (
    Workspace("my-api", version="1.0.0", description="My API")
    .runtime(mode="dev", port=8000, reload=True)
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RoutingIntegration(strict_matching=True))
    .integrate(FaultHandlingIntegration(default_strategy="propagate"))
    .security(cors_enabled=True, helmet_enabled=True)
)
```

??? tip "What each integration does"
    - `DiIntegration(auto_wire=True)` — enables automatic dependency injection across all modules
    - `RoutingIntegration(strict_matching=True)` — ensures exact route matching with no fallback
    - `FaultHandlingIntegration(default_strategy="propagate")` — maps structured faults to HTTP responses

---

## Step 2 — Add a Module

Modules are the organizational unit in Aquilia. Each module has its own controllers, services, models, and manifest:

```bash
aq add module users
```

This generates:

```
modules/
└── users/
    ├── __init__.py
    ├── manifest.py          # Declares controllers, services, models
    ├── controllers.py        # HTTP endpoint handlers
    ├── services.py           # Business logic
    └── models.py             # Data models
```

The `workspace.py` is automatically updated with the new module:

```python
workspace = (
    Workspace("my-api", version="1.0.0", description="My API")
    # ...
    .module(Module("users", version="1.0.0").route_prefix("/users").tags("users"))
    # ...
)
```

---

## Step 3 — Write a Controller

Open `modules/users/controllers.py` and define an endpoint:

```python
from aquilia import Controller, GET, POST, RequestCtx, Response
from aquilia.faults import NotFoundFault

# In-memory store for demonstration
_users: list[dict] = [
    {"id": "1", "name": "Alice", "email": "alice@example.com"},
    {"id": "2", "name": "Bob",  "email": "bob@example.com"},
]

class UsersController(Controller):
    prefix = "/users"
    tags   = ["users"]

    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        """Return all users. Supports ?search= query parameter."""
        search = ctx.query_param("search")
        if search:
            filtered = [u for u in _users if search.lower() in u["name"].lower()]
            return Response.json({"users": filtered})
        return Response.json({"users": _users})

    @GET("/<user_id:str>")
    async def get_user(self, ctx: RequestCtx, user_id: str):
        """Return a single user by ID."""
        for user in _users:
            if user["id"] == user_id:
                return Response.json(user)
        raise NotFoundFault(detail=f"User {user_id} not found")

    @POST("/", status_code=201)
    async def create_user(self, ctx: RequestCtx):
        """Create a new user from JSON body."""
        body = await ctx.json()
        user = {"id": str(len(_users) + 1), **body}
        _users.append(user)
        return Response.json(user, status=201)
```

The `manifest.py` already references this controller:

```python
from aquilia import AppManifest
from aquilia.manifest import FaultHandlingConfig

manifest = AppManifest(
    name="users",
    version="1.0.0",
    description="User management module",
    controllers=["modules.users.controllers:UsersController"],
    services=[],
    models=[],
    base_path="modules.users",
    tags=["users"],
    faults=FaultHandlingConfig(default_domain="USERS", strategy="propagate"),
)
```

---

## Step 4 — Validate

Before running, validate that the workspace is well-formed:

```bash
aq validate
```

Expected output:

```
✓ Workspace 'my-api' is valid
✓ 1 module(s) discovered
✓ 1 controller(s) with 3 route(s)
✓ 0 service(s), 0 model(s)
✓ DI graph is acyclic
✓ Route table is unambiguous
```

This checks:
- All manifests are syntactically valid
- All declared controllers exist and are importable
- The dependency graph has no cycles
- No two routes conflict (same method + same path)

??? warning "If validation fails"
    Common issues and their fixes:

    - **Module not found**: Verify the module path in `manifest.py` matches the filesystem path
    - **Controller not importable**: Check that the class name matches exactly
    - **Route conflict**: Two controllers have the same HTTP method and path pattern
    - **Circular dependency**: A service depends on itself through the DI chain

---

## Step 5 — Serve

Start the development server:

```bash
aq serve
```

```
⚓ Aquilia 1.1.2 "Crimson Gale"
├─ Workspace: my-api v1.0.0
├─ Environment: dev
├─ Server: http://127.0.0.1:8000
├─ Hot reload: enabled
└─ 3 route(s) mounted
```

Test the endpoints:

```bash
# List all users
$ curl http://127.0.0.1:8000/users/
{"users": [{"id": "1", "name": "Alice", "email": "alice@example.com"}, {"id": "2", "name": "Bob", "email": "bob@example.com"}]}

# Get a specific user
$ curl http://127.0.0.1:8000/users/1
{"id": "1", "name": "Alice", "email": "alice@example.com"}

# Create a new user
$ curl -X POST http://127.0.0.1:8000/users/ -H "Content-Type: application/json" -d '{"name": "Carol", "email": "carol@example.com"}'
{"id": "3", "name": "Carol", "email": "carol@example.com"}

# Get a non-existent user (structured fault response)
$ curl http://127.0.0.1:8000/users/99
{"error": {"code": "NOT_FOUND", "message": "User 99 not found", "domain": "HTTP", "severity": "WARN"}}
```

Notice the structured error response for the 404 — this is the `FaultEngine` converting a `NotFoundFault` into an HTTP response with domain, code, and severity.

---

## Step 6 — Inspect

While the server is running, inspect the compiled state in another terminal:

```bash
# List all routes
$ aq inspect routes

  METHOD   PATH                    HANDLER                    CONTROLLER
 ──────────────────────────────────────────────────────────────────────────
  GET      /users/                 list_users                 UsersController
  GET      /users/<user_id:str>    get_user                   UsersController
  POST     /users/                 create_user                UsersController

# List DI providers
$ aq inspect providers

  SCOPE       NAME                    TYPE
 ───────────────────────────────────────────────────────────
  singleton   config_loader           ConfigLoader
  request     request_context         RequestCtx
```

---

## Next Steps

Now that you have a running API, deepen your understanding:

<div class="grid cards" markdown>

-   :material-school:{ .lg .middle } **First Project**

    ---

    Add a service layer, blueprint validation, and dependency injection to your API.

    [:octicons-arrow-right-24: Build a real project](first-project.md)

-   :material-shield:{ .lg .middle } **Add Authentication**

    ---

    Protect your endpoints with JWT, sessions, or clearance-based access control.

    [:octicons-arrow-right-24: Authentication guide](../guides/authentication.md)

-   :material-database:{ .lg .middle } **Add a Database**

    ---

    Replace the in-memory store with the async ORM and SQLite or PostgreSQL.

    [:octicons-arrow-right-24: Database guide](../reference/modules/models/index.md)

-   :material-layers:{ .lg .middle } **Add More Modules**

    ---

    Organize your codebase with multiple modules, each with its own controllers, services, and models.

    [:octicons-arrow-right-24: Multi-module workspace](../examples/multi-module.md)

</div>