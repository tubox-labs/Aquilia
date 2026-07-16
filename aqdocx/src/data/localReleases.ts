export const localReleases: Record<string, Record<string, string>> = {
  "1.3.2": {
    "README.md": `# Aquilia v1.3.2 Release Notes — "Specula API Observatory"

Aquilia v1.3.2 introduces **Specula**, a major evolution of the framework's documentation and API exploration subsystem. Specula completely replaces the legacy OpenAPI 3.1.0 generator and static Swagger/ReDoc pages with a compiled, introspective ASGI dashboard (the Specula Observatory), reactive hot-reloading streams, automated security and clearance level mapping, a schema-synthesized mock server, and Postman/Insomnia collection exporters.

## Table of Contents

1. [Specula Observatory UI & Integration](observatory.md)
   * The new dashboard philosophy.
   * Integrating Specula via \`Integration.specula(...)\`.
   * UI branding and Server-Sent Events (SSE) live streams.
2. [Spec Compilation & Schema Inference](compilation.md)
   * The compiler-integrated \`SpeculaBuilder\`.
   * Python-to-JSON Schema type mapping.
   * Multi-strategy request body and response resolution.
3. [Automated Security & Clearance Detection](security.md)
   * Inferred security schemes from pipeline guards.
   * Integrated authorization clearance level detection.
   * Extended metadata (\`x-specula-security\`) vendor extensions.
4. [Mock Server & Collection Exports](mock_exports.md)
   * Interactive mocking engine at \`/specula/mock\`.
   * Schema synthesis with configurable recursion depth limits.
   * Dynamic exports for Postman v2.1 and Insomnia v4.
5. [Migration Guide](migration.md)
   * Removing legacy \`OpenAPIIntegration\` references.
   * Replaced classes, paths, and deprecations.

---

## Key Subsystem Improvements

1. **Compilation over Code Scanning**: No more parsing source files or class matching at runtime. Specula extracts endpoint specs directly from Aquilia's compiled in-memory ASGI routing topology.
2. **Developer Reactivity**: Hot-reloading modules push Specula spec invalidations down active Server-Sent Events (SSE) connections, immediately refreshing the developer's dashboard.
3. **Simulated Sandbox**: Frontends can start testing integration before the backend endpoints are written. The mock server synthesizes response payloads matching the exact JSON schemas defined in Contracts or ORM Models.
4. **Complete Security Transparency**: Exposes exact pipeline guards, role requirements, and AccessLevel clearance levels to ensure complete architectural observability.
`,

    "compilation.md": `# Spec Compilation & Schema Inference

Specula features a compiler-integrated OpenAPI 3.1.0 specification engine (\`SpeculaBuilder\`). Instead of scanning source files at startup, it introspects Aquilia's compiled routing topology in memory, extracting schemas, bindings, parameters, and outputs.

---

## Python-to-JSON Schema Mapping

When generating schema objects, Specula inspects standard type hints and maps them to their OpenAPI 3.1.0 JSON Schema equivalents. 

Specula is fully compliant with the OpenAPI 3.1.0 specification:
* **Option types** use \`oneOf\` blocks combined with \`{"type": "null"}\` instead of the deprecated \`nullable\` property.
* **Complex Python structures** map cleanly to nested schemas.

### Mapping Reference Table

| Python Type Hint | JSON Schema Equivalent |
| :--- | :--- |
| \`str\` | \`{"type": "string"}\` |
| \`int\` | \`{"type": "integer"}\` |
| \`float\` | \`{"type": "number", "format": "double"}\` |
| \`bool\` | \`{"type": "boolean"}\` |
| \`bytes\` | \`{"type": "string", "format": "binary"}\` |
| \`None\` / \`type(None)\` | \`{"type": "null"}\` |
| \`Optional[T]\` / \`T \| None\` | \`{"oneOf": [{"type": T_schema}, {"type": "null"}]}\` |
| \`list[T]\` / \`List[T]\` | \`{"type": "array", "items": T_schema}\` |
| \`dict[str, T]\` / \`Dict[str, T]\` | \`{"type": "object", "additionalProperties": T_schema}\` |
| \`tuple[T1, T2]\` | \`{"type": "array", "prefixItems": [T1_schema, T2_schema], "minItems": 2, "maxItems": 2}\` |
| \`Contract\` / \`Model\` | \`{"\$ref": "#/components/schemas/Name"}\` |

---

## Request Body Inference Strategies

Specula resolves request payloads through a 5-tier inference engine, prioritizing explicit developer configurations over implicit code analysis.

### 1. The \`request_contract\` Parameter
If a route decorator declares a validation contract directly, the builder generates a reference schema:
\`\`\`python
@POST("/users", request_contract=UserCreateContract)
async def create_user(self, ctx: RequestCtx): ...
\`\`\`

### 2. Contract Parameter Type Hints
If a route handler receives a parameter type-hinted with an Aquilia \`Contract\` class, it is automatically mapped as the JSON body payload:
\`\`\`python
@POST("/users")
async def create_user(self, ctx: RequestCtx, payload: UserCreateContract): ...
\`\`\`

### 3. Explicit \`Body\` Metadata Annotations
If a parameter is annotated using standard Python type annotations with \`Body()\`, it is mapped to a properties-based object payload:
\`\`\`python
@POST("/items")
async def create_item(self, ctx: RequestCtx, amount: Annotated[int, Body()] = 1): ...
\`\`\`

### 4. Docstring Body Mappings
The builder parses Google-style docstrings, extracting raw examples from \`Body:\` headers:
\`\`\`python
@POST("/items")
async def create_item(self, ctx: RequestCtx):
    """
    Create an item.

    Body: {"name": "Widget", "count": 10}
    """
    ...
\`\`\`

### 5. Source Code Introspection
As a fallback, Specula scans the compiled handler source code for extraction patterns:
* Finding \`await ctx.json()\` infers a generic \`application/json\` object.
* Finding \`await ctx.form()\` infers an \`application/x-www-form-urlencoded\` form.

---

## Response Shapes Resolution

Specula automatically maps success and error response channels.

### Success Shapes
1. **Model / Contract Mappings**: Declaring \`response_model\` or \`response_contract\` registers the corresponding schema (input contracts map with \`Input\` suffix, output contracts map directly) and binds them under status code \`2xx\`.
2. **Standard Output Fallbacks**: If no return contract is specified, Specula inspects handler code:
   * Calls to \`Response.json(...)\` default to \`application/json\`.
   * Calls to \`Response.html(...)\` or template rendering functions default to \`text/html\`.
   * References to \`SSEResponse(...)\` default to \`text/event-stream\`.

### Error Shapes
* **Raises Docstring Section**: Specula compiles exception details declared in Google-style docstrings into typed status responses:
  \`\`\`python
  @GET("/users/<id:int>")
  async def get_user(self, id: int):
      """
      Get user by ID.

      Raises:
          UserNotFoundFault (404): The user does not exist.
      """
      ...
  \`\`\`
  Specula compiles this raises annotation into a structured \`404 Not Found\` response returning the standard \`AquiliaError\` schema.
* **Auto-Validation Errors**: All write routes (\`POST\`, \`PUT\`, \`PATCH\`) automatically carry a default \`422 Unprocessable Entity\` response mapping returning the structured \`AquiliaValidationError\` schema.
`,

    "migration.md": `# OpenAPI to Specula Migration Guide

Aquilia v1.3.2 deprecates and removes the old static OpenAPI/Swagger engine. This guide outlines how to migrate your configuration, imports, and endpoints.

---

## 1. Configuration & Integration Upgrades

The old \`OpenAPIIntegration\` has been replaced by \`SpeculaIntegration\`. In your \`workspace.py\`, update your registrations:

### Legacy Style (Removed)
\`\`\`python
# Replaced by Specula
workspace.integrate(Integration.openapi(
    title="Store API",
    docs_path="/apidocs",
    swagger_ui_theme="dark"
))
\`\`\`

### New Style (Active)
\`\`\`python
from aquilia.integrations import SpeculaIntegration

# Option A: Direct class registration
workspace.integrate(SpeculaIntegration(
    title="Store API",
    ui_path="/apidocs",
    ui_theme="dark"
))

# Option B: Fluent helper
# workspace.integrate(Integration.specula(
#     title="Store API",
#     ui_path="/apidocs",
#     ui_theme="dark"
# ))
\`\`\`

### Parameter Mapping Table

Use this reference table to map configuration options from legacy OpenAPI attributes to Specula attributes:

| Legacy OpenAPI Option | New Specula Option | Notes |
| :--- | :--- | :--- |
| \`docs_path\` | \`ui_path\` | Default changes from \`/docs\` to \`/specula\`. |
| \`openapi_json_path\` | \`json_path\` | Default changes from \`/openapi.json\` to \`/specula/spec.json\`. |
| \`redoc_path\` | (Removed) | ReDoc is deprecated. Use the unified Specula dashboard. |
| \`swagger_ui_theme\` | \`ui_theme\` | Values: \`"auto"\`, \`"light"\`, \`"dark"\`. |
| \`swagger_ui_config\` | (Removed) | Replaced by direct dashboard configuration. |

---

## 2. Replaced Imports & Engines

If you manually generated specs, update your imports and instantiation:

\`\`\`python
# --- Legacy Imports (Removed) ---
# from aquilia.controller.openapi import OpenAPIConfig, OpenAPIGenerator
# config = OpenAPIConfig(title="API")
# spec = OpenAPIGenerator(config=config).generate(router)

# --- New Imports (Active) ---
from aquilia.specula.config import SpeculaConfig
from aquilia.specula.schema.builder import SpeculaBuilder

config = SpeculaConfig(title="API")
spec = SpeculaBuilder(config=config).build(router)
\`\`\`

---

## 3. Redirects & Endpoint Updates

The automatic redirects mapping legacy paths are no longer registered. Update links:

* **Swagger UI Docs**: Old path \`/docs\` is replaced by \`/specula\`.
* **ReDoc Docs**: Old path \`/redoc\` is deprecated. Use the unified \`/specula\` dashboard.
* **JSON Specification**: Old path \`/openapi.json\` is replaced by \`/specula/spec.json\`.
* **YAML Specification**: Specula now supports rendering YAML natively at \`/specula/spec.yaml\`.
`,

    "mock_exports.md": `# Mock Server & Collection Exports

Specula features a schema-driven Mock Server and dynamic collection exporters to support rapid frontend integration and testing.

---

## Interactive Mock Server (\`/specula/mock\`)

The mock server lets developers call any documented API endpoint and receive a plausible response payload without executing any business logic.

### Enabling the Mock Server
The mock server is disabled by default. Enable it in your workspace configuration:

\`\`\`python
workspace.integrate(Integration.specula(
    title="Customer API",
    mock_server_enabled=True,
    mock_max_depth=4 # limit recursive definitions mapping
))
\`\`\`

### How Payload Synthesis Works
When a request is sent to \`/specula/mock/<path>\`, the mock router matches the path against the compiled API specification. It resolves the success response (\`200\`, \`201\`, or \`202\`) and inspects the JSON Schema:

1. **Explicit Examples**: If the schema or individual fields define an \`example\` or \`examples\` block, those values are returned directly.
2. **Plausible Synthesis**: If no examples are configured, Specula inspects the schema field types and synthesizes logical placeholders:
   * **Formatting Matchers**: String formats like \`email\`, \`uuid\`, \`uri\`, and \`date-time\` map to real formatted values (e.g. \`user@example.com\`, \`550e8400-e29b-41d4-a716-446655440000\`).
   * **Key Name Inference**: If a string field matches common keys (such as \`email\` or \`url\`), appropriate values are auto-injected.
   * **Standard Defaults**: Integers default to \`42\`, numbers to \`3.14\`, booleans to \`True\`, and arrays to single-item arrays.
3. **Recursion Safety**: Self-referencing models (e.g., a node containing a list of children of its own type) are automatically truncated when nesting depth exceeds \`mock_max_depth\` (default \`4\`).

---

## Exporters

Specula exposes dynamic endpoints to download client collections configured with your current workspace routing topology and security schemes.

### 1. Postman Collection v2.1
* **Endpoint**: \`/specula/export/postman\`
* **Output**: A compliant Postman v2.1 collection JSON file.
* **Details**:
  * Groups endpoints into folders based on their tags or manifest module names.
  * Translates route variables like \`/users/<id:int>\` into Postman-compatible environment syntax: \`/users/{{id}}\`.
  * Pre-populates request bodies with JSON examples synthesized from Contract definitions.
  * Embeds default authorization headers mapped to the \`{{access_token}}\` environment variable.

### 2. Insomnia v4 Collection
* **Endpoint**: \`/specula/export/insomnia\`
* **Output**: A standard Insomnia v4 export file.
* **Details**:
  * Includes workspace configuration mapping the current API.
  * Sets up base environment variables referencing \`{{ _.base_url }}\`.
  * Configures HTTP methods, headers, and body payloads automatically.
`,

    "observatory.md": `# Specula Observatory UI & Integration

The Specula Observatory is a built-in interactive dashboard served natively by Aquilia at \`/specula\`. It provides a CDN-free developer sandbox that works entirely offline, inline-cached, and features hot-reload awareness.

## Workspace Integration

Specula is registered at the workspace level inside \`workspace.py\`. You configure it using the \`Integration.specula(...)\` builder method or by importing and instantiating \`SpeculaIntegration\` directly:

\`\`\`python
# workspace.py
from aquilia.workspace import Workspace
from aquilia.integrations import Integration, SpeculaIntegration

workspace = (
    Workspace("user-portal")
    
    # Style A: Fluent Integration helper
    .integrate(Integration.specula(
        title="User Portal API",
        version="1.4.0",
        ui_theme="dark"
    ))
    
    # Style B: Direct Instantiation (provides static checks and autocomplete)
    # .integrate(SpeculaIntegration(
    #     title="User Portal API",
    #     version="1.4.0",
    #     ui_theme="dark"
    # ))
)
\`\`\`

---

## Configuration Reference (\`SpeculaConfig\`)

When you configure Specula, your parameters map to the \`SpeculaConfig\` dataclass. The primary settings available are:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **Info / Branding** | | | |
| \`title\` | \`str\` | \`"Aquilia API"\` | Name of the API, visible in the UI header and spec exports. |
| \`version\` | \`str\` | \`"1.0.0"\` | The current API release version. |
| \`description\` | \`str\` | \`""\` | Detailed description of the API. |
| \`ui_theme\` | \`str\` | \`"auto"\` | \`"auto"\` (matches system preferences), \`"light"\`, or \`"dark"\`. |
| \`ui_primary_color\`| \`str\` | \`"#22c55e"\` | Hex code for branding the main interface buttons and tags. |
| **URL Paths** | | | |
| \`ui_path\` | \`str\` | \`"/specula"\` | Browser path to view the Observatory HTML dashboard. |
| \`json_path\` | \`str\` | \`"/specula/spec.json"\`| JSON endpoint serving the raw OpenAPI 3.1.0 spec. |
| \`yaml_path\` | \`str\` | \`"/specula/spec.yaml"\`| YAML endpoint serving the raw OpenAPI 3.1.0 spec. |
| \`stream_path\` | \`str\` | \`"/specula/stream"\`| SSE stream pushing route updates to the UI. |
| \`mock_path\` | \`str\` | \`"/specula/mock"\` | Endpoint path for the mock server router. |
| **Feature Toggles** | | | |
| \`enabled\` | \`bool\` | \`True\` | Master toggle to enable or disable Specula routes. |
| \`include_internal\`| \`bool\` | \`False\` | Whether routes matching \`/_*\` are included in the spec. |
| \`detect_security\` | \`bool\` | \`True\` | Scan route guards and decorators to construct security schemes. |
| \`mock_server_enabled\`| \`bool\` | \`False\` | Set \`True\` to enable schema-synthesized mock responses. |
| \`spec_cache_ttl\` | \`int\` | \`60\` | In-memory cache duration (in seconds) for compiled spec payloads. |

---

## Hot-Reloading SSE Stream (\`/specula/stream\`)

During development, Aquilia runs with file watchers. When you modify controller code, the worker process reloads. 

Specula exposes a native ASGI Server-Sent Events (SSE) stream endpoint at \`/specula/stream\`. When the dashboard is loaded in a browser, it subscribes to this stream. When a reload happens, the server pushes an invalidation event down the pipe:

\`\`\`json
{"event": "update", "data": {"status": "invalidated", "version": "2.0.0"}}
\`\`\`

The Observatory frontend listens to this event and immediately fetches the newly compiled specification and routes dynamically, refreshing the client view with zero hard refreshes.

---

## Production Security Locks

By default, the Specula Observatory is fully open. In production environments, you can lock access down to authenticated users with specific roles:

\`\`\`python
workspace.integrate(Integration.specula(
    title="Corporate Core API",
    docs_auth_required=True,
    docs_roles=["admin", "ops-team"]
))
\`\`\`

When \`docs_auth_required\` is enabled, the Specula controller inspects the request context using the configured \`AuthMiddleware\` pipeline. If the visitor lacks the required roles, they receive a \`403 Forbidden\` response.
`,

    "security.md": `# Automated Security & Clearance Detection

Specula integrates with Aquilia's security pipeline to automatically detect, map, and document authentication configurations. It translates pipeline guards and clearance levels into standard OpenAPI security requirements and rich custom metadata tags.

---

## Inferred Security Schemes

The spec builder scans your controllers' and routes' pipeline nodes and handler decorators to identify authentication mechanisms. It automatically registers and configures security definitions in the OpenAPI \`components.securitySchemes\` catalog:

| Inferred Guard Class Name | Generated Security Scheme | Schema Details |
| :--- | :--- | :--- |
| \`AuthGuard\` / \`Auth\` / \`@authenticated\` | \`bearerAuth\` | HTTP Bearer token (JWT) authentication. |
| \`ApiKeyGuard\` / \`ApiKey\` | \`apiKeyAuth\` | \`X-API-Key\` request header authorization. |
| \`SessionGuard\` / \`Session\` | \`cookieAuth\` | Session-based cookie verification (\`session\`). |
| \`BasicAuthGuard\` / \`Basic\` | \`basicAuth\` | HTTP Basic authentication. |
| \`OAuth2Guard\` / \`OAuth2\` | \`oauth2\` | OAuth2 Authorization Code flow. |

\`\`\`python
# Specula automatically registers bearerAuth with ["read", "write"] scopes
class OrderController(Controller):
    pipeline = [AuthGuard(), ScopeGuard("read", "write")]
    
    @GET("/")
    async def list_orders(self, ctx: RequestCtx): ...
\`\`\`

---

## Integrated Clearance Detection

Specula integrates directly with the \`aquilia.auth.clearance\` system to identify role-based and attribute-based clearance levels. 

The builder resolves the merged clearance level from the controller boundary and individual route overrides:
1. **Public Routes**: If the effective clearance resolves to \`AccessLevel.PUBLIC\` (e.g. via \`@grant(level=AccessLevel.PUBLIC)\`), security requirements are omitted for that route.
2. **Protected Routes**: If the effective clearance is higher than public, \`bearerAuth\` is automatically registered as a requirement.

---

## Rich Metadata Extensions (\`x-specula-security\`)

To support advanced observability and client generation, Specula embeds the full resolved authorization metadata in a custom vendor extension block (\`x-specula-security\`) inside each route's spec operation:

\`\`\`json
"x-specula-security": {
  "authenticated": true,
  "guards": [
    {
      "name": "RoleGuard",
      "type": "instance",
      "roles": ["admin", "compliance"],
      "require_all": false
    }
  ],
  "clearance": {
    "level": "INTERNAL",
    "level_value": 30,
    "entitlements": ["view_audit_logs", "override_fees"],
    "conditions": ["IsDuringOfficeHours", "IPRangeCondition"],
    "compartment": "finance"
  }
}
\`\`\`

This vendor block exposes:
* **\`authenticated\`**: Boolean flag indicating if verification is required.
* **\`guards\`**: Detailed list of active pipeline guard configurations, including roles, scopes, optional tags, resources, and evaluation settings.
* **\`clearance\`**: The full clearance metadata, including \`level\` name, \`level_value\` integer, required \`entitlements\` lists, active \`conditions\` names, and matching resource \`compartment\` boundaries.
`
  },
  "1.3.1": {
    "README.md": `# Aquilia v1.3.1 Release Notes — "Backend Refactoring"

Aquilia v1.3.1 introduces a major rewrite of the authentication (\`aquilia.auth\`) and authorization subsystems. It moves away from rigid string-based strategies and hardcoded guard adapters in favor of a pluggable, class-based backend architecture, a unified permission engine, hardened session serialization, and token clock-skew tolerance.

## Table of Contents

1. [Pluggable Authentication Backends](backends.md)
   * The new \`AuthBackend\` protocol.
   * Built-in backends: \`TokenBackend\`, \`SessionBackend\`, \`PasswordBackend\`, \`ApiKeyBackend\`.
   * The \`resolve_backend\` helper and loading configuration.
2. [Unified Permission & Authorization Engine](guards.md#permissionengine)
   * Role DAG (Directed Acyclic Graph) inheritance.
   * Policy callables and scope checks.
   * Pluggable Flow Guards: \`AuthGuard\`, \`RoleGuard\`, \`ScopeGuard\`, \`PolicyGuard\`.
   * Context-First Decorators: \`@authenticated\`, \`@roles_required\`, \`@scopes_required\`, \`@optional_auth\`.
3. [Session Security Hardening](sessions.md)
   * Elimination of stale permission state in session cookies.
   * The lightweight \`AuthPrincipal\` serialization format.
   * Dynamic resolution of roles and scopes on every request.
4. [Migration Guide](migration.md)
   * Upgrading configuration settings from \`strategies\` to \`backends\`.
   * Replaced classes, decorators, and middleware.

---

## Key Refactoring Goals

1. **Pluggability**: Unify all authentication strategies (Bearer JWTs, Session cookies, Username/Password, API keys) under a single, reusable backend protocol.
2. **Dynamic Privileges**: Resolve permissions, roles, and scopes fresh from the database or cache on every request, preventing privilege escalation through stale session states.
3. **API Simplification**: Consolidate five parallel authorization subsystems (RBAC, ABAC, Clearance, Policy DSL, and custom adapters) into a single, cohesive \`PermissionEngine\`.
4. **Resiliency**: Handle clock drift in distributed clusters by introducing native clock-skew tolerance.`,

    "backends.md": `# Pluggable Authentication Backends

In Aquilia v1.3.1, the authentication workflow is decomposed into single-responsibility **Backends**. A backend is a class that conforms to the \`AuthBackend\` protocol. It is responsible for accepting a credential dictionary and resolving it to an \`Identity\`.

## The \`AuthBackend\` Protocol

The \`AuthBackend\` protocol is defined in \`aquilia.auth.backends.base\` using Python's structural subtyping (\`typing.Protocol\`):

\`\`\`python
from typing import Any, Protocol, runtime_checkable
from aquilia.auth.core import Identity

@runtime_checkable
class AuthBackend(Protocol):
    def accepts(self, credentials: dict[str, Any]) -> bool:
        """Return True if the backend supports the provided credentials."""
        ...

    async def authenticate(self, credentials: dict[str, Any]) -> Identity | None:
        """Verify credentials and resolve them to an Identity.
        
        May raise specific auth faults (e.g., AUTH_TOKEN_EXPIRED, AUTH_INVALID_CREDENTIALS).
        """
        ...
\`\`\`

---

## Built-in Backends

Aquilia provides four native backends to cover standard flows:

### 1. \`TokenBackend\`
Validates JWT Bearer tokens. It verifies signatures, checks \`exp\` and \`nbf\` claims (with clock-skew tolerance), and validates token revocation via \`TokenManager\`.
* **Accepted Credentials**: \`{"token": str}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, token_manager: TokenManager, identity_store: IdentityStore)
  \`\`\`

### 2. \`SessionBackend\`
Restores identity from a cookie-backed session. It looks up the \`identity_id\` from the session data or from \`session.principal\`, and fetches the corresponding active identity.
* **Accepted Credentials**: \`{"session": Session}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, identity_store: IdentityStore)
  \`\`\`

### 3. \`PasswordBackend\`
Authenticates user login credentials. It checks for IP/username brute-force lockouts, resolves usernames or email addresses to an identity, compares password hashes, handles password re-hashing when algorithm parameters upgrade, and checks for multi-factor authentication (MFA) requirements.
* **Accepted Credentials**: \`{"username": str, "password": str}\`
* **Constructor**:
  \`\`\`python
  def __init__(
      self,
      identity_store: IdentityStore,
      credential_store: CredentialStore,
      password_hasher: PasswordHasher,
      rate_limiter: RateLimiter | None = None,
      login_attributes: tuple[str, ...] = ("email", "username", "login"),
  )
  \`\`\`

### 4. \`ApiKeyBackend\`
Authenticates API requests via an opaque API key. It hashes the incoming key using \`HMAC-SHA256\` for lookup, checks expiration and revocation status, and verifies that the key carries the required scopes if requested.
* **Accepted Credentials**: \`{"api_key": str, "required_scopes": list[str] | None}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, credential_store: CredentialStore, identity_store: IdentityStore)
  \`\`\`

---

## The Backend Resolver

To simplify instantiation, the \`resolve_backend\` function maps string identifiers, class references, or dotted import paths to their instantiated backends:

\`\`\`python
def resolve_backend(b: Any, auth_manager: Any) -> Any:
    """Resolve a backend reference (instance, class, short name, or dotted path)
    into an instantiated backend object.
    """
    ...
\`\`\`

It maps:
* Short names: \`"token"\` (TokenBackend), \`"session"\` (SessionBackend), \`"password"\` (PasswordBackend), \`"api_key"\` (ApiKeyBackend).
* Class references: \`TokenBackend\`, \`SessionBackend\`, \`PasswordBackend\`, \`ApiKeyBackend\`.
* Dotted paths: \`"my_app.auth.backends.CustomBackend"\`.

### Example Configuration in \`workspace.py\`

\`\`\`python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    backends = [
        "aquilia.auth.backends.TokenBackend",
        "aquilia.auth.backends.SessionBackend",
        "my_project.auth.CustomBackendClass",  # Dotted class path
    ]
\`\`\``,

    "guards.md": `# Unified Authorization, Middleware & Decorators

Aquilia v1.3.1 unifies identity resolution and request-scoped checks into a single middleware and permission engine.

---

## 1. Unified \`PermissionEngine\`

The \`PermissionEngine\` (defined in \`aquilia.auth.permissions\`) is the central engine for evaluating roles, scopes, and policies. It replaces five separate historical systems and runs check assertions that raise appropriate exceptions on denial.

### Core API Methods

* \`define_role(role: str, *, permissions: list[str] | None = None, inherits: list[str] | None = None) -> None\`: Declare a role and its transitively implied parents.
* \`role_implies(role: str, target: str) -> bool\`: Query the role DAG structure.
* \`register_policy(key: str, policy: PolicyCallable) -> None\`: Define a rule matching the signature \`(identity, resource) -> bool\`.
* \`check_role(identity: Identity, role: str) -> None\`: Asserts role ownership; raises \`AUTHZ_INSUFFICIENT_ROLE\` on failure.
* \`check_scope(identity: Identity, scope: str) -> None\`: Asserts scope ownership; raises \`AUTHZ_INSUFFICIENT_SCOPE\` on failure.
* \`check_policy(key: str, identity: Identity, resource: Any = None) -> None\`: Asserts policy assertion passes; raises \`AUTHZ_POLICY_DENIED\` on failure.
* \`has_role(identity: Identity, role: str) -> bool\`: Returns a boolean indicating role membership.
* \`has_scope(identity: Identity, scope: str) -> bool\`: Returns a boolean indicating scope membership.
* \`evaluate_policy(key: str, identity: Identity, resource: Any = None) -> bool\`: Returns a boolean indicating policy result.

---

## 2. Pluggable Flow Guards

Guards (defined in \`aquilia.auth.guards\`) evaluate context and raise exceptions on denial. They can be placed directly in request pipelines or used as raw classes (for zero-configuration defaults).

### \`AuthGuard\`
Verifies authentication status.
* **Optional Mode**: When \`optional=True\`, anonymous users are allowed.
* **Proactive Auth**: If the identity is not yet resolved, \`AuthGuard\` attempts to proactively extract and authenticate a Bearer token using DI container-resolved \`AuthManager\`.
* **Signature**: \`AuthGuard(auth_manager=None, optional=False)\`

### \`RoleGuard\`
Ensures the identity holds required roles.
* **Resolution**: Uses \`PermissionEngine\` if found in the DI container; otherwise, falls back to direct membership testing of \`identity.get_attribute("roles", [])\`.
* **Signature**: \`RoleGuard(*roles, engine=None, require_all=True)\`

### \`ScopeGuard\`
Ensures the identity holds required scopes.
* **Wildcards**: Supports the wildcard \`"*"\` scope.
* **Signature**: \`ScopeGuard(*scopes, require_all=True)\`

### \`PolicyGuard\`
Evaluates a policy registered in the permission engine.
* **Signature**: \`PolicyGuard(key, engine, resource=None)\`

---

## 3. Context-First Decorators

Decorators (defined in \`aquilia.auth.decorators\`) wrap handlers to execute guard checks and **inject parameters** into the handler's signature (e.g., \`identity\`, \`user\`, \`session\`, \`principal\`).

### \`@authenticated\`
Requires an authenticated identity.
* **Browser Redirection**: If a request is anonymous, has \`redirect_if_html=True\` or \`login_url\` configured, and accepts HTML, it performs a \`303 Redirect\` to the login page with a \`next\` query parameter.
* **Signature**:
  \`\`\`python
  def authenticated(
      func=None,
      *,
      login_url: str | None = None,
      redirect_if_html: bool = False,
      include_next: bool = True,
      next_param: str = "next",
      redirect_status: int = 303,
  )
  \`\`\`

### \`@roles_required\` / \`@scopes_required\`
Evaluates role or scope conditions before executing the controller action.
\`\`\`python
@roles_required("admin", "editor", require_all=False)
async def delete_post(self, ctx: RequestCtx) -> Response:
    ...
\`\`\`

### \`@optional_auth\`
Evaluates the proactive \`AuthGuard(optional=True)\` check. It injects the user if found but does not block anonymous traffic.

### \`@requires\`
Composes multiple guards (both classes and instances) sequentially:
\`\`\`python
@requires(AuthGuard, RoleGuard("admin"))
async def admin_only_action(self, ctx: RequestCtx) -> Response:
    ...
\`\`\`

---

## 4. Unified \`AuthMiddleware\`

The new unified \`AuthMiddleware\` (defined in \`aquilia.auth.middleware\`) coordinates credential resolution from backends on every incoming request.

* **Signatures & Parameters**:
  \`\`\`python
  def __init__(
      self,
      auth_manager: AuthManager,
      session_engine: SessionEngine | None = None,
      *,
      require_auth: bool = False,
      backends: list[AuthBackend] | None = None,
      logger: logging.Logger | None = None,
  )
  \`\`\`
* **Execution Flow**:
  1. **Phase 1: Session Resolution**: If \`session_engine\` is provided, resolves the session and binds it to \`ctx.session\` and \`request.state["session"]\`.
  2. **Phase 2: Credentials Extraction**: Extracts Bearer token, ApiKey, or Session from the request.
  3. **Phase 3: Backend Authentication**: Loops through pluggable \`backends\` (defaults to \`TokenBackend\` and \`SessionBackend\`). The first backend that accepts the credentials and returns an \`Identity\` completes the phase.
  4. **Phase 4: Requirement Enforcement**: If \`require_auth=True\` and no identity is resolved, returns a \`401 Unauthorized\` response immediately.
  5. **Phase 5: Propagation**: Propagates the resolved identity to \`request.state["identity"]\`, \`request.state["authenticated"]\`, and \`ctx.identity\`.
  6. **Phase 6: Downstream Execution**: Calls the next handler in the ASGI middleware chain.
  7. **Phase 7: Session Commitment**: Commits session modifications back to the storage adapter.`,

    "migration.md": `# Migration Guide: v1.3.0 to v1.3.1

Aquilia v1.3.1 consolidates and standardizes authentication and authorization. Follow this guide to upgrade your project.

---

## 1. Upgrading Configuration

The string-based \`strategies\` setting has been removed. You must now configure the list of identity-resolution backends using the \`backends\` parameter. Additionally, the rate-limiting and MFA settings have been promoted to direct configuration parameters on \`AquilaConfig.Auth\`.

### Legacy Configuration (v1.3.0)
\`\`\`python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    strategies = ["token", "session"]
\`\`\`

### Refactored Configuration (v1.3.1)
\`\`\`python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    backends = [
        "aquilia.auth.backends.TokenBackend",
        "aquilia.auth.backends.SessionBackend",
    ]
    # Store type: "memory" or "redis"
    store_type = "memory"
    
    # Rate Limiting configuration parameters
    rate_limit_max_attempts = 5
    rate_limit_window_seconds = 900
    rate_limit_lockout_seconds = 3600
    
    # MFA settings
    mfa_enabled = False
    mfa_required = False
    
    # Clock skew tolerance (in seconds) for JWT validations
    clock_skew_seconds = 5
    
    # Audit trail activation
    audit_enabled = True
\`\`\`

---

## 2. Replaced & Removed Decorators

The legacy decorators \`AdminGuard\` and \`VerifiedEmailGuard\` have been removed.

* **\`AdminGuard\`**: Replace with \`@roles_required("admin")\`.
* **\`VerifiedEmailGuard\`**: Handle verification checks in your identity resolution backend (such as deactivating unverified users) or write a simple custom guard.

#### Before:
\`\`\`python
from aquilia.auth import AdminGuard

@AdminGuard
async def delete_item(ctx):
    ...
\`\`\`

#### After:
\`\`\`python
from aquilia.auth import roles_required

@roles_required("admin")
async def delete_item(ctx):
    ...
\`\`\`

---

## 3. Upgrading Flow Pipeline Guards

All legacy guard adapters (historically located in \`flow_guards.py\`) have been removed. Use the new first-class guards directly.

| Legacy Guard Class (v1.3.0) | Refactored Guard Class (v1.3.1) |
|---|---|
| \`RequireAuthGuard\` | \`AuthGuard\` |
| \`RequireRolesGuard\` | \`RoleGuard\` |
| \`RequireScopesGuard\` | \`ScopeGuard\` |
| \`RequirePolicyGuard\` | \`PolicyGuard\` |

### Pipeline Registration Example

#### Before:
\`\`\`python
from aquilia.auth.integration.flow_guards import RequireAuthGuard, RequireRolesGuard

pipeline.guard(RequireAuthGuard())
pipeline.guard(RequireRolesGuard("admin"))
\`\`\`

#### After:
\`\`\`python
from aquilia.auth.guards import AuthGuard, RoleGuard

# Raw classes can be passed if no parameters are required
pipeline.guard(AuthGuard)
pipeline.guard(RoleGuard("admin"))
\`\`\`

---

## 4. Upgrading Session Guards

The legacy \`SessionGuard\` class and \`@requires\` decorator in \`aquilia.sessions.decorators\` have been removed. Switch to the unified \`PermissionEngine\` and the unified \`@requires\` decorator.

#### Before:
\`\`\`python
from aquilia.sessions.decorators import SessionGuard, requires

class CustomSessionGuard(SessionGuard):
    async def check(self, session: Session) -> bool:
        return bool(session.data.get("special_user"))

@requires(CustomSessionGuard())
async def handler(ctx):
    ...
\`\`\`

#### After:
\`\`\`python
from aquilia.auth.guards import requires

class CustomGuard:
    def check(self, ctx: Any) -> None:
        from aquilia.auth.faults import AUTHZ_POLICY_DENIED
        session = getattr(ctx, "session", None)
        if session is None or not session.data.get("special_user"):
            raise AUTHZ_POLICY_DENIED()

@requires(CustomGuard())
async def handler(ctx):
    ...
\`\`\`

---

## 5. Removing the Fluent \`AuthConfig\` Builder

If you set up custom authentication containers in testing or bootstrapping scripts using the \`AuthConfig\` builder, you must remove it. Configure integrations directly using dictionary payloads or the \`AquilaConfig.Auth\` classes.

#### Before:
\`\`\`python
from aquilia.auth.integration.di_providers import AuthConfig

config = (
    AuthConfig()
    .rate_limit(max_attempts=3)
    .strategies(["token"])
    .build()
)
\`\`\`

#### After:
\`\`\`python
config = {
    "rate_limit": {
        "max_attempts": 3,
    },
    "security": {
        "backends": ["aquilia.auth.backends.TokenBackend"],
    }
}
\`\`\`

---

## 6. Deprecated APIs & Relocations

* **\`AuthManager.logout()\`**: Deprecated in favor of \`AuthManager.sign_out()\`. Calling \`logout()\` now raises a \`DeprecationWarning\` but will invoke \`sign_out()\` internally for backward compatibility.
* **\`OptionalAuthMiddleware\`**: Deprecated in favor of \`AquilAuthMiddleware(require_auth=False)\` or the new \`AuthMiddleware\` class.
* **\`RateLimiter\` relocation**: The \`RateLimiter\` class has been moved from the \`manager\` module to \`aquilia.auth.manager_types\` to prevent circular imports. Update imports if you reference it directly.`,

    "sessions.md": `# Session Security, AuthManager & RateLimiting

Aquilia v1.3.1 introduces substantial security improvements to cookie-based and session-based authentication to prevent privilege escalation, alongside a refined \`AuthManager\` API and a standalone \`RateLimiter\` utility.

---

## 1. Session Serialization Hardening

In previous versions of Aquilia, the full set of user roles, scopes, and attributes was serialized and stored directly inside the session store database (or client-side cookie):

\`\`\`python
# Old, insecure v1.3.0 implementation:
session["roles"] = identity.get_attribute("roles", [])
session["scopes"] = identity.get_attribute("scopes", [])
session["status"] = identity.status.value
\`\`\`

This optimization meant that if an administrator modified a user's permissions, suspended their account, or deleted them, the changes **would not take effect** for requests authenticated via session cookies until their session expired.

In Aquilia v1.3.1, session serialization has been hardened. The \`bind_identity\` function only writes core identifiers:

\`\`\`python
# Hardened v1.3.1 implementation:
session.mark_authenticated(AuthPrincipal.from_identity(identity))
session["identity_id"] = identity.id
if identity.tenant_id is not None:
    session["tenant_id"] = identity.tenant_id
\`\`\`

Notice that **roles, scopes, and user attributes are no longer written to the session store**.

### Active Identity Resolution
* The \`SessionBackend\` captures the active session credentials.
* It extracts the \`identity_id\` (either from \`session.principal\` or from \`session.data["identity_id"]\`).
* It fetches a fresh \`Identity\` object directly from the \`IdentityStore\` on **every single request**.
* Authorization guards evaluate roles and scopes against this fresh database/cache state.

---

## 2. Shared Manager Types: \`RateLimiter\`

To protect brute-force paths (such as username/password login), Aquilia v1.3.1 introduces a standalone \`RateLimiter\` class in \`aquilia.auth.manager_types\` (and re-exported in \`aquilia.auth.manager\` for backward compatibility).

* **Constructor & Parameters**:
  \`\`\`python
  def __init__(
      self,
      max_attempts: int = 5,
      window_seconds: int = 900,
      lockout_duration: int = 3600,
  )
  \`\`\`
  Tracks failed authentication attempts per key (typically a username or IP address) within a sliding time window.
* **Core API Methods**:
  * \`record_attempt(key: str) -> None\`: Records a failed attempt. If attempts exceed \`max_attempts\` within the window, locks out the key.
  * \`is_locked_out(key: str) -> bool\`: Checks if the key is currently locked out.
  * \`get_remaining_attempts(key: str) -> int\`: Returns attempts left before lockout.
  * \`reset(key: str) -> None\`: Clears attempt history for the key on successful authentication.

---

## 3. \`AuthManager\` Refactored APIs

The \`AuthManager\` class (defined in \`aquilia.auth.manager\`) is the central coordinator for authentication operations. The following APIs were updated:

### Token Revocation
The token revocation API now supports access tokens by extracting the unique JWT identifier (\`jti\`) and blacklisting it:
* \`async def revoke_token(self, token: str, token_type: str = "refresh") -> None\`:
  * If \`token_type == "refresh"\`, revokes the refresh token directly.
  * If \`token_type == "access"\`, validates the access token, extracts the \`jti\` claim, and revokes it so subsequent validations reject it.

### Deprecated \`logout()\`
* **Signature**: \`async def logout(self, identity_id=None, session_id=None, access_token=None, refresh_token=None) -> None\`
* **Status**: **Deprecated** in favor of \`sign_out()\`. Raises a \`DeprecationWarning\` when called.

---

## 4. \`SessionAuthBridge\`

The \`SessionAuthBridge\` coordinates actions between \`AuthManager\` and \`SessionEngine\`:
* \`create_auth_session(identity, request, token_claims=None)\`: Resolves and binds authentication credentials to a new session.
* \`rotate_on_privilege_escalation(session, response)\`: Rotates the session ID (session fixation protection) after an escalating event (such as completing an MFA challenge).
* \`logout(session, response)\`: Destroys the current session.
* \`logout_all_devices(identity_id)\`: Revokes and purges all active session identifiers linked to a given identity ID across the session store.`
  }
};
