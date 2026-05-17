# Testing Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `TestConfig` | `aquilia/testing/config.py` | See class attributes and constructor methods. | Lightweight config wrapper for test overrides. |
| `EffectCall` | `aquilia/testing/effects.py` | action: str, mode: str &#124; None, resource: Any, success: bool &#124; None, timestamp: float | Record of an acquire or release call on a MockEffectProvider. |
| `CapturedFault` | `aquilia/testing/faults.py` | fault: Fault, domain: str &#124; None, app_name: str &#124; None, handler_name: str &#124; None, timestamp: float | A fault captured by :class:`MockFaultEngine`. |
| `CapturedMail` | `aquilia/testing/mail.py` | to: list[str], subject: str, body: str, html_body: str, from_email: str, cc: list[str], bcc: list[str], reply_to: str &#124; None, attachments: list[dict[str, Any]], headers: dict[str, str], provider: str, template_name: str &#124; None | A mail message captured during testing. |

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
