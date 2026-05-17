# Mail Configuration

## Configuration Entry Points

The implementation exposes the following configuration-like classes, policies, integrations, or dataclasses.

| Type | Source | Fields | Purpose |
| --- | --- | --- | --- |
| `ProviderConfig` | `aquilia/mail/config.py` | See class attributes and constructor methods. | Attribute-access wrapper for a validated provider config. |
| `RetryConfig` | `aquilia/mail/config.py` | See class attributes and constructor methods. | Attribute-access wrapper for a validated retry config. |
| `RateLimitConfig` | `aquilia/mail/config.py` | See class attributes and constructor methods. | Attribute-access wrapper for a validated rate-limit config. |
| `SecurityConfig` | `aquilia/mail/config.py` | See class attributes and constructor methods. | Attribute-access wrapper for a validated security config. |
| `TemplateConfig` | `aquilia/mail/config.py` | See class attributes and constructor methods. | Attribute-access wrapper for a validated template config. |
| `QueueConfig` | `aquilia/mail/config.py` | See class attributes and constructor methods. | Attribute-access wrapper for a validated queue config. |
| `MailAuthConfig` | `aquilia/mail/config.py` | See class attributes and constructor methods. | Attribute-access wrapper for validated mail authentication credentials. |
| `MailConfig` | `aquilia/mail/config.py` | See class attributes and constructor methods. | Top-level mail configuration. |
| `Attachment` | `aquilia/mail/envelope.py` | filename: str, content_type: str, digest: str, size: int, inline: bool, content_id: str &#124; None | Attachment metadata (content stored separately in blob store). |
| `MailEnvelope` | `aquilia/mail/envelope.py` | id: str, created_at: datetime, status: EnvelopeStatus, priority: int, from_email: str, to: list[str], cc: list[str], bcc: list[str], reply_to: str &#124; None, subject: str, body_text: str, body_html: str &#124; None, ... | Immutable mail envelope -- the unit of work in the mail pipeline. |
| `ProviderResult` | `aquilia/mail/providers/__init__.py` | status: ProviderResultStatus, provider_message_id: str &#124; None, error_message: str &#124; None, raw_response: dict[str, Any] &#124; None, retry_after: float &#124; None | Result returned by IMailProvider.send(). |

## Common Entry Points

- `MailConfig`
- `ProviderConfig`
- `MailIntegration`

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
