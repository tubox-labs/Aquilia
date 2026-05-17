# Controllers Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `CompiledRoute` | `aquilia/controller/compiler.py` | controller_class: type, controller_metadata: ControllerMetadata, route_metadata: RouteMetadata, compiled_pattern: CompiledPattern, full_path: str, http_method: str, specificity: int, app_name: str &#124; None, version_metadata: dict[str, Any] &#124; None | A compiled controller route with pattern and handler. |
| `CompiledController` | `aquilia/controller/compiler.py` | controller_class: type, metadata: ControllerMetadata, routes: list[CompiledRoute] | A fully compiled controller with all routes. |
| `ParameterMetadata` | `aquilia/controller/metadata.py` | name: str, type: type, default: Any, source: str, required: bool, pattern: str &#124; None | Metadata for a route method parameter. |
| `RouteMetadata` | `aquilia/controller/metadata.py` | http_method: str, path_template: str, full_path: str, handler_name: str, parameters: list[ParameterMetadata], pipeline: list[Any], summary: str, description: str, tags: list[str], deprecated: bool, response_model: type &#124; None, status_code: int, ... | Metadata for a single route (controller method). |
| `ControllerMetadata` | `aquilia/controller/metadata.py` | class_name: str, module_path: str, prefix: str, routes: list[RouteMetadata], pipeline: list[Any], tags: list[str], instantiation_mode: str, constructor_params: list[ParameterMetadata], version: Any &#124; None | Complete metadata for a Controller class. |
| `ParsedDocstring` | `aquilia/controller/openapi.py` | summary: str, description: str, params: dict[str, str], returns: str, raises: list[dict[str, str]], request_body: str &#124; None | Parsed handler docstring with structured sections. |
| `OpenAPIConfig` | `aquilia/controller/openapi.py` | title: str, version: str, description: str, terms_of_service: str, contact_name: str, contact_email: str, contact_url: str, license_name: str, license_url: str, servers: list[dict[str, str]], docs_path: str, openapi_json_path: str, ... | Configuration for OpenAPI spec generation. |
| `ControllerRouteMatch` | `aquilia/controller/router.py` | route: CompiledRoute, params: dict[str, Any], query: dict[str, Any] | Result of a successful controller route match. |

## Common Entry Points

- No dedicated workspace integration was detected from module naming. Configure this module through direct constructors, manifests, or the subsystem that owns it.

## Precedence Model

Aquilia generally resolves configuration in this order:

1. Explicit constructor arguments or typed integration dataclass values.
2. `Workspace` builder methods and `Workspace.integrate(...)` output.
3. `ConfigLoader` defaults and environment overlays.
4. Runtime defaults inside the subsystem service or provider constructor.

When this module is registered through an `AppManifest`, keep component declarations inside `modules/<name>/manifest.py` and keep cross-cutting integration settings in `workspace.py`.

## Datatype Guidance

- Prefer typed dataclasses, policy objects, and config objects listed above when they exist.
- Keep secret values in environment-backed config, not literal strings in committed workspace files.
- Keep runtime-only state in services, stores, providers, or request state rather than static configuration.
- Use `to_dict()` on integration dataclasses when you need to inspect exactly what enters `ConfigLoader`.
