---
title: "OpenAPI Generation"
description: "How to generate and serve OpenAPI documentation for Aquilia applications"
icon: lucide/file-text
---Aquilia features built-in support for generating OpenAPI 3.1.0 specifications directly from controllers. By introspecting controller class metadata, handler signatures, type hints, docstrings, and pipeline guards, Aquilia can compile a complete API schema and serve interactive documentation using Swagger UI or ReDoc.

The core OpenAPI generation capabilities are implemented in [aquilia/controller/openapi.py](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py).

---

## Configuration with OpenAPIConfig

The [OpenAPIConfig](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L578) dataclass (defined in [openapi.py:L578-L633](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L578-L633)) defines parameters for configuring OpenAPI generation, paths, external docs, and UI themes.

### Parameters Reference

| Field | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `title` | `str` | `"Aquilia API"` | The title of the API. |
| `version` | `str` | `"1.0.0"` | The version of the API. |
| `description` | `str` | `""` | A comprehensive description of the API. |
| `terms_of_service` | `str` | `""` | URL to the terms of service. |
| `contact_name` | `str` | `""` | Contact name for the API. |
| `contact_email` | `str` | `""` | Contact email address. |
| `contact_url` | `str` | `""` | Contact URL. |
| `license_name` | `str` | `""` | Name of the license. |
| `license_url` | `str` | `""` | URL to the license terms. |
| `servers` | `list[dict[str, str]]` | `[]` | List of server URL and description dictionaries representing deployment targets. |
| `docs_path` | `str` | `"/docs"` | Path where the Swagger UI documentation is served. |
| `openapi_json_path` | `str` | `"/openapi.json"` | Path where the raw OpenAPI JSON specification is served. |
| `redoc_path` | `str` | `"/redoc"` | Path where the ReDoc documentation is served. |
| `include_internal` | `bool` | `False` | Whether to include internal routes starting with `/_`. |
| `group_by_module` | `bool` | `True` | Whether to group tags by module. |
| `infer_request_body` | `bool` | `True` | Whether to automatically infer request body schemas from handler signatures, type hints, and source code. |
| `infer_responses` | `bool` | `True` | Whether to automatically infer response schemas from handler source code and route metadata. |
| `detect_security` | `bool` | `True` | Whether to detect security schemes and requirements from controller and route pipeline guards. |
| `external_docs_url` | `str` | `""` | URL for external documentation. |
| `external_docs_description` | `str` | `""` | Description for the external documentation. |
| `swagger_ui_theme` | `str` | `""` | Theme for Swagger UI. Supports `"dark"` or custom themes. |
| `swagger_ui_config` | `dict[str, Any]` |  | Additional configuration options passed directly to the SwaggerUIBundle constructor. |
| `enabled` | `bool` | `True` | Global flag to enable or disable OpenAPI generation features. |


### Configuration Helper Method

- **`from_dict(data)`** ([openapi.py:L624-L632](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L624-L632)): A class method that constructs an [OpenAPIConfig](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L578) object from a dictionary (e.g. workspace configuration), ignoring keys starting with `_` and verifying parameter existence on the configuration object.

---

## Specification Generation with OpenAPIGenerator

The [OpenAPIGenerator](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L638) class (defined in [openapi.py:L638-L961](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L638-L961)) is the primary engine responsible for compiling routing structures into a fully compliant OpenAPI 3.1.0 specification.

### Constructor and Initialization

```python
def __init__(
    self,
    title: str = "Aquilia API",
    version: str = "1.0.0",
    config: OpenAPIConfig | None = None,
):
```

The constructor ([openapi.py:L666-L681](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L666-L681)) accepts an optional [OpenAPIConfig](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L578) object. If omitted, it initializes a default configuration using the provided `title` and `version` parameters.

### The generate() Method

```python
def generate(self, router: ControllerRouter) -> dict[str, Any]:
```

The [generate()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L683-L757) method takes a [ControllerRouter](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/router.py) instance and generates a complete OpenAPI 3.1.0 specification dictionary containing:
- **`openapi`**: The specification version, pinned to `"3.1.0"` ([openapi.py:L711](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L711)).
- **`info`**: An info object built by `_build_info()` detailing the title, version, description, contact details, and license info ([openapi.py:L712](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L712), [openapi.py:L760-L791](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L760-L791)).
- **`paths`**: An object containing endpoints mapped from the compiled routes ([openapi.py:L713](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L713)).
- **`servers`**: Targets generated from config, defaulting to `[{"url": "/", "description": "Current server"}]` ([openapi.py:L717-L719](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L717-L719), [openapi.py:L793-L798](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L793-L798)).
- **`tags`**: Sorted tag mappings representing controller and endpoint groupings ([openapi.py:L721-L723](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L721-L723)).
- **`components`**: Dedicated schemas registry. By default, it populates:
  - Custom data schemas (`schemas`) resolved from `response_model` type annotations ([openapi.py:L727-L728](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L727-L728)).
  - Security schemes (`securitySchemes`) extracted from pipeline guards ([openapi.py:L729-L730](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L729-L730)).
  - A default `ErrorResponse` schema with fields: `error` (string, required), `code` (string), and `detail` (object) ([openapi.py:L733-L745](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L733-L745)).
- **`externalDocs`**: Optional links and descriptions for external documentation resource references ([openapi.py:L749-L755](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L749-L755)).

---

## Interactive Documentation HTML Generators

Aquilia provides helper functions to render interactive frontends for OpenAPI specs, pulling assets from high-speed CDNs.

### Swagger UI Generation

The [generate_swagger_html()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1027) function (defined in [openapi.py:L1027-L1055](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1027-L1055)) constructs the Swagger UI page.

- **Parameters**: 
  - `config`: An [OpenAPIConfig](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L578) configuration object.
- **Implementation & CDN Resources**:
  - Uses Swagger UI version `5.18.2` (defined as `_SWAGGER_UI_VERSION` at [openapi.py:L965](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L965)).
  - Fetches the styles from `swagger-ui.css` and JavaScript logic from `swagger-ui-bundle.js` and `swagger-ui-standalone-preset.js` via `cdn.jsdelivr.net` ([openapi.py:L975-L976](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L975-L976), [openapi.py:L994-L997](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L994-L997)).
  - Injects theme CSS rules; specifically, if `swagger_ui_theme` is `"dark"`, it appends CSS rules using a color inversion filter to render the dark mode display ([openapi.py:L1030-L1038](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1030-L1038)).
  - Serializes `swagger_ui_config` parameters (converting string and boolean formats) and formats them into the `SwaggerUIBundle` constructor call ([openapi.py:L1040-L1047](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1040-L1047)).
- **Output**: Returns a complete, self-contained HTML page string ([openapi.py:L967-L1024](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L967-L1024)) initialized to fetch the specification JSON from `config.openapi_json_path`.

### ReDoc Generation

The [generate_redoc_html()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1084) function (defined in [openapi.py:L1084-L1089](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1084-L1089)) constructs a minimalist, responsive ReDoc page.

- **Parameters**: 
  - `config`: An [OpenAPIConfig](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L578) configuration object.
- **Implementation & CDN Resources**:
  - Fetches fonts (Montserrat & Roboto) from Google Fonts ([openapi.py:L1066-L1067](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1066-L1067)).
  - Loads the ReDoc standalone package bundle `redoc.standalone.js` from `cdn.redoc.ly` ([openapi.py:L1079](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1079)).
  - Configures the `<redoc>` HTML tag properties including the specification URL from `config.openapi_json_path` ([openapi.py:L1073-L1078](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1073-L1078)).
- **Output**: Returns a complete, self-contained HTML page string ([openapi.py:L1060-L1081](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L1060-L1081)) configured to render documentation in a multi-panel layout.

---

## How Controller Metadata Feeds OpenAPI

During router scanning, [OpenAPIGenerator](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L638) processes each [CompiledRoute](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/compiler.py) object ([openapi.py:L801-L830](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L801-L830)) and extracts routing schemas.

### Route and Path Processing

- **Paths**: The route pattern regex is converted into a standard OpenAPI path template (e.g. converting `/user/(?P<id>[^/]+)` to `/user/{id}`) using [generate_openapi_path()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/patterns/openapi.py) ([openapi.py:L816](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L816)).
- **HTTP Methods**: Extracted directly from `route.http_method` (e.g., `get` or `post`) ([openapi.py:L817](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L817)).
- **Operation ID**: Auto-generated by stripping `"Controller"` suffix from the class name and appending the handler method name (e.g., `UserController.get_profile` -> `User_get_profile`) ([openapi.py:L841-L843](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L841-L843)).

### Summary and Description Extraction

The generator determines endpoint summaries and descriptions using a fallback hierarchy:

1. **Summary** ([openapi.py:L846](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L846)):
   - Explicitly configured `route_meta.summary`.
   - The first non-empty line of the handler's docstring (parsed via `_parse_docstring`).
   - Auto-formatted handler method name (e.g., `list_items` -> `"List Items"`).
2. **Description** ([openapi.py:L847](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L847)):
   - Explicitly configured `route_meta.description`.
   - The remaining body content of the handler's docstring.

### Tag Grouping

Tags group operations into logical sections inside interactive UIs:
- The generator checks for explicit route-level tags (`route_meta.tags`), falling back to controller-level tags (`route.controller_metadata.tags`), and finally defaulting to the class name without `"Controller"` ([openapi.py:L858-L863](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L858-L863)).
- The tag's general description is automatically fetched from the first line of the parent controller class's docstring ([openapi.py:L873-L876](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L873-L876)).

### Parameter and Header Introspection

Parameters are parsed and appended to the operation specifications:
- **Path Parameters**: Deduced from route path tokens via [generate_openapi_params()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/patterns/openapi.py) ([openapi.py:L880](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L880)).
- **Query and Header Parameters**: Loaded by iterating over configured metadata in [_add_query_params_from_metadata()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L923) ([openapi.py:L923-L961](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L923-L961)).
  - Translates Python annotations (such as `int`, `str`, `Optional`) into JSON schema components using [_python_type_to_schema()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L51) ([openapi.py:L51-L108](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L51-L108)).
  - Includes default values if configured on the parameters ([openapi.py:L944-L945](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L944-L945)).
  - Maps parameter descriptions from matching names in docstring parameter blocks (e.g. `Args:` or `Params:`) ([openapi.py:L883-L887](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L883-L887), [openapi.py:L942-L943](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L942-L943), [openapi.py:L957-L958](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L957-L958)).

### Request Body Inference

If HTTP methods include `POST`, `PUT`, or `PATCH`, the generator attempts to infer the request body schema through multiple strategies ([openapi.py:L308-L422](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L308-L422)):

1. **Parameter Metadata**: Searches parameter collections for body definitions (`param_meta.source == "body"`) and converts their types to schemas ([openapi.py:L319-L339](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L319-L339)).
2. **Type Hints and Annotated Annotations**: Checks if parameters are annotated with `Annotated[X, Body(...)]` ([openapi.py:L341-L371](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L341-L371)).
3. **Docstring Objects**: Extracts inline JSON definitions using a `Body: { ... }` pattern inside docstring comments ([openapi.py:L373-L395](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L373-L395)).
4. **Source Code Extraction**: Performs static checks on the handler function source string. If `ctx.json()` is found, it maps an `application/json` object schema. If `ctx.form()` is found, it maps `application/x-www-form-urlencoded` ([openapi.py:L397-L420](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L397-L420)).

### Response Schema Inference

The [_build_responses()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L470) helper compiles standard success and error response schemas ([openapi.py:L470-L534](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L470-L534)):
- **Success Response**: Maps to the HTTP `status_code` specified on the route (defaults to `200`).
  - If `response_model` (e.g. a dataclass or a generic type) is configured on the route, it converts the model using [_dataclass_to_schema()](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L110) and registers it as a reusable component component ([openapi.py:L486-L491](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L486-L491), [openapi.py:L703-L707](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L703-L707)).
  - If no model is configured, it checks the handler source code to determine the format: `Response.html` maps to `text/html`, `Response.text` to `text/plain`, and `Response.json` defaults to `application/json` ([openapi.py:L493-L506](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L493-L506)).
- **Error Responses**:
  - Exception classes declared in the docstring `Raises:` section are documented under their respective HTTP status codes, mapped to the reusable `ErrorResponse` component ([openapi.py:L510-L517](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L510-L517)).
  - General status error codes inside the handler source (e.g. `status_code=400` or `status=403`) are extracted via regex and mapped to the standard error response component ([openapi.py:L519-L530](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L519-L530)).

### Security Detection

Security requirements are compiled from guards attached to controllers or route handlers ([openapi.py:L239-L291](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L239-L291), [openapi.py:L539-L572](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L539-L572)):
- Class names matching `"oauth"` compile as `oauth2` flow components ([openapi.py:L261-L272](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L261-L272)).
- Class names matching `"apikey"` compile as header `apiKeyAuth` with `X-API-Key` parameter requirements ([openapi.py:L273-L280](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L273-L280)).
- Class names matching `"authguard"` or exactly `"auth"` compile as standard HTTP JWT `bearerAuth` ([openapi.py:L281-L288](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L281-L288)).
- Scope/role mappings: If a guard exposes `scopes` or `roles` attributes, these scopes are automatically attached as scopes required for that specific operation ([openapi.py:L559-L570](file:///Users/kuroyami/TuboxLabProject/aquilia-docs/aquilia/controller/openapi.py#L559-L570)).

---

## Serving Swagger and ReDoc from a Controller

To serve the generated documentation interactively, create a dedicated documentation controller that registers paths mapping to `OpenAPIGenerator` outputs.

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
    tags = ["System"]

    def __init__(self, router: ControllerRouter):
        self.router = router
        self.config = OpenAPIConfig(
            title="Aquilia Application API",
            version="1.4.0",
            description="Documentation for the main application API services.",
            docs_path="/docs",
            openapi_json_path="/docs/openapi.json",
            redoc_path="/docs/redoc"
        )
        self.generator = OpenAPIGenerator(config=self.config)

    @GET("/openapi.json")
    async def get_openapi_json(self):
        """Get raw OpenAPI 3.1.0 specification JSON."""
        spec = self.generator.generate(self.router)
        return Response.json(spec)

    @GET("/")
    async def get_swagger_docs(self):
        """Render the Swagger UI documentation interactive console."""
        html = generate_swagger_html(self.config)
        return Response.html(html)

    @GET("/redoc")
    async def get_redoc_docs(self):
        """Render the ReDoc api reference console."""
        html = generate_redoc_html(self.config)
        return Response.html(html)
```

---

## End-to-End Code Example

The following example showcases:
1. Defining a data contract (dataclass) representing a response model.
2. A secure controller with route parameters, query parameters, validation metadata, and pipeline guards.
3. Exposing the generated docs.

```python
from dataclasses import dataclass
from typing import Annotated, Optional
from aquilia.controller import Controller, GET, POST, Response
from aquilia.controller.guards import AuthGuard, ScopeGuard
from aquilia.controller.router import ControllerRouter
from aquilia.controller.openapi import (
    OpenAPIConfig,
    OpenAPIGenerator,
    generate_swagger_html
)

# 1. Define JSON schemas through dataclasses
@dataclass
class UserProfile:
    """User profile data details."""
    user_id: int
    username: str
    email: str
    is_active: bool = True

# 2. Main API Controller
class UserController(Controller):
    prefix = "/users"
    tags = ["User Management"]
    pipeline = [AuthGuard()]  # Adds bearerAuth security scheme automatically

    @GET("/{id}")
    async def get_user(self, id: int, status: Optional[str] = "active") -> UserProfile:
        """
        Retrieve user details by ID.

        Args:
            id: The unique identifier of the user.
            status: Query parameter to filter status condition.

        Raises:
            UserNotFoundError (404): If the user does not exist in our systems.
            UnauthorizedError (401): If no auth token is provided.
        """
        # Inferred response code is 200, response_model is UserProfile.
        # Path parameter 'id' and query parameter 'status' are documented automatically.
        return UserProfile(user_id=id, username="alice", email="alice@example.com")

    @POST("/create")
    async def create_user(self, ctx) -> UserProfile:
        """
        Create a new system user profile.

        Body: {
            "username": "bob",
            "email": "bob@example.com"
        }
        """
        # Inferred request body will parse the docstring 'Body' pattern
        # and document username and email fields.
        body_data = await ctx.json()
        return UserProfile(user_id=42, username=body_data["username"], email=body_data["email"])
```
