---
title: "Auto OpenAPI Setup Tutorial"
description: "Generating and serving interactive Swagger UI and ReDoc pages automatically from controllers"
icon: lucide/workflow
---Serving interactive API documentation directly from your web application improves developer experience and ensures your API specifications remain in sync with your actual backend logic. Aquilia offers robust built-in support for generating OpenAPI 3.1.0 specifications by introspecting your controllers, routes, guards, and type hints.

This tutorial guides you through configuring, generating, and serving **Swagger UI** and **ReDoc** documentation interfaces inside an Aquilia app.

---

### Step 1: OpenAPIConfig Setup

The first step in generating documentation is defining your API's metadata and serving paths using [OpenAPIConfig](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L578) (defined in [openapi.py:L578-L633](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L578-L633)).

You can instantiate this configuration class with your API's basic details:

```python
from aquilia.controller.openapi import OpenAPIConfig

config = OpenAPIConfig(
    title="Aquilia Application API",
    version="1.0.0",
    description="Comprehensive developer documentation for the Aquilia backend application services.",
    docs_path="/docs",                  # Swagger UI location
    openapi_json_path="/openapi.json",  # Raw JSON specification location
    redoc_path="/redoc"                 # ReDoc UI location
)
```

!!! info
    By default, `OpenAPIConfig` serves Swagger UI at `/docs`, ReDoc at `/redoc`, and the raw specification at `/openapi.json` (as documented in [openapi.py:L72-L86](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L72-L86)).


---

### Step 2: Generate Specification with `OpenAPIGenerator`

The [OpenAPIGenerator](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L638) class (defined in [openapi.py:L638-L961](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L638-L961)) is the core compiler. It scans an active [ControllerRouter](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/router.py) and compiles all route definitions into a compliant OpenAPI 3.1.0 schema dictionary.

Pass your `OpenAPIConfig` to the generator and call `generate()`:

```python
from aquilia.controller.openapi import OpenAPIGenerator
from aquilia.controller.router import ControllerRouter

# Initialize the compiler
generator = OpenAPIGenerator(config=config)

# Compile controller routes to OpenAPI spec format
# router should be your application's ControllerRouter instance
openapi_spec = generator.generate(router)
```

The returned `openapi_spec` is a dictionary conforming to the OpenAPI 3.1.0 standard, complete with `paths`, `components`, `tags`, and `security` mappings (documented in [openapi.py:L711-L755](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L711-L755)).

---

### Step 3: Mount Routes to Serve Swagger UI

Aquilia provides [generate_swagger_html()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1027) (defined in [openapi.py:L1027-L1055](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1027-L1055)) to render a complete HTML page including Swagger UI Javascript and CSS fetched from high-speed CDNs.

To serve this page, set up a route inside a documentation controller:

```python
from aquilia.controller import Controller, GET, Response
from aquilia.controller.openapi import generate_swagger_html

class DocsController(Controller):
    # ... setup controller initialization with config

    @GET("/")
    async def get_swagger_ui(self):
        """Render the interactive Swagger UI console."""
        html = generate_swagger_html(self.config)
        return Response.html(html)
```

> [!TIP]
> You can toggle a sleek dark theme easily by setting `swagger_ui_theme="dark"` inside `OpenAPIConfig` ([openapi.py:L122-L125](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L122-L125)).

---

### Step 4: Mount Routes to Serve ReDoc

Similarly, Aquilia offers a minimalist, multi-panel documentation style via [generate_redoc_html()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1084) (defined in [openapi.py:L1084-L1089](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1084-L1089)).

Mount it under your configured `redoc_path`:

```python
from aquilia.controller import Controller, GET, Response
from aquilia.controller.openapi import generate_redoc_html

class DocsController(Controller):
    # ... setup controller initialization with config

    @GET("/redoc")
    async def get_redoc_ui(self):
        """Render the ReDoc api reference console."""
        html = generate_redoc_html(self.config)
        return Response.html(html)
```

---

### Step 5: Enriching Endpoints with Metadata

You can customize how your endpoints look and group in the interactive UIs by supplying docstrings and route metadata parameters:

1. **Summary & Description**: The generator looks at the route's explicit metadata or parses the handler's docstrings (as shown in [openapi.py:L846-L847](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L846-L847)). The first line maps to the **Summary**, and the remaining lines map to the **Description**.
2. **Tags**: Organize operations into sections. The generator fallbacks from route-level `route_meta.tags` to controller-level `tags` class properties (documented in [openapi.py:L858-L863](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L858-L863)).
3. **Deprecated**: Mark routes as outdated or retired using the `deprecated=True` attribute inside the route handler parameters or metadata.

```python
from aquilia.controller import Controller, GET

class UserController(Controller):
    tags = ["User Management"]  # Controller-level tag grouping

    @GET("/{id}", deprecated=True)
    async def get_user_legacy(self, id: int):
        """
        Legacy User Details retrieval.
        
        This endpoint is deprecated and will be removed in future versions.
        Use GET /v2/users/{id} instead.
        """
        # Inferred summary: "Legacy User Details retrieval."
        # Inferred description: "This endpoint is deprecated and will be removed..."
        # Marked as deprecated in the generated Swagger / ReDoc UI.
        pass
```

---

### Step 6: `request_blueprint` and `response_blueprint` Usage

To enforce structure validation and compile precise JSON schemas automatically, you can explicitly configure `request_blueprint` and `response_blueprint` within your route decorators. 

Rather than relying purely on docstring comments, using request and response blueprints allows the `OpenAPIGenerator` to parse class properties directly and populate schema structures under `components/schemas` (similar to standard dataclass translation described in [openapi.py:L486-L491](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L486-L491)).

```python
from dataclasses import dataclass
from aquilia.controller import Controller, POST, Response

@dataclass
class UserCreatePayload:
    username: str
    email: str
    age: int = 18

@dataclass
class UserCreationResponse:
    id: int
    username: str
    status: str = "created"

class UserController(Controller):
    
    @POST(
        "/register", 
        request_blueprint=UserCreatePayload, 
        response_blueprint=UserCreationResponse
    )
    async def register_user(self, ctx):
        """
        Register a new application user.
        
        Decrypts request body payloads against UserCreatePayload structure
        and returns details mapping to UserCreationResponse.
        """
        body = await ctx.json()
        # Request body and response structures are compiled automatically in the OpenAPI UI.
        return Response.json({"id": 101, "username": body["username"], "status": "created"})
```

---

### Complete Documentation Controller Example

Below is a complete, ready-to-run implementation of a Documentation Controller that serves your application's raw specification JSON, Swagger UI, and ReDoc:

```python
from aquilia.controller import Controller, GET, Response
from aquilia.controller.router import ControllerRouter
from aquilia.controller.openapi import (
    OpenAPIConfig,
    OpenAPIGenerator,
    generate_swagger_html,
    generate_redoc_html,
)

class DocsController(Controller):
    tags = ["System Documentation"]

    def __init__(self, router: ControllerRouter):
        self.router = router
        self.config = OpenAPIConfig(
            title="Aquilia Application API",
            version="1.0.0",
            description="API Reference & Interactive Testing Console",
            docs_path="/docs",
            openapi_json_path="/docs/openapi.json",
            redoc_path="/docs/redoc"
        )
        self.generator = OpenAPIGenerator(config=self.config)

    @GET("/openapi.json")
    async def get_openapi_json(self):
        """Get the raw OpenAPI 3.1.0 specification JSON."""
        spec = self.generator.generate(self.router)
        return Response.json(spec)

    @GET("/")
    async def get_swagger_docs(self):
        """Render the Swagger UI interactive documentation console."""
        html = generate_swagger_html(self.config)
        return Response.html(html)

    @GET("/redoc")
    async def get_redoc_docs(self):
        """Render the ReDoc API Reference console."""
        html = generate_redoc_html(self.config)
        return Response.html(html)
```
