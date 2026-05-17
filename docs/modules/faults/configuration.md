# Faults Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `FaultContext` | `aquilia/faults/core.py` | fault: Fault, trace_id: str, timestamp: datetime, app: str &#124; None, route: str &#124; None, request_id: str &#124; None, cause: Exception &#124; None, stack: list[Any], metadata: dict[str, Any], parent: FaultContext &#124; None | Runtime context wrapper for faults. |
| `Resolved` | `aquilia/faults/core.py` | response: Any | Fault was resolved and should not propagate further. |
| `Transformed` | `aquilia/faults/core.py` | fault: Fault, preserve_context: bool | Fault was transformed into another fault. |
| `Escalate` | `aquilia/faults/core.py` | See class attributes and constructor methods. | Fault should escalate to next handler in chain. |
| `ExceptionMapping` | `aquilia/faults/default_handlers.py` | exception_type: type[Exception], fault_factory: Callable[[Exception], Any], retryable: bool | Maps exception type to Fault factory. |
| `HTTPResponse` | `aquilia/faults/default_handlers.py` | status_code: int, body: dict[str, Any], headers: dict[str, str] | HTTP response representation. |

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
