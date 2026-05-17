# Mail Configuration

Async mail subsystem with message classes, config blueprints, providers, DI registration, templates, faults, and convenience send APIs.

This page distinguishes direct configuration APIs from indirect runtime wiring. All class names and source files below are extracted from the current source tree.

## Configuration Model

This module exposes config-oriented public classes. Use the table below to locate exact constructors and `to_dict()` behavior in `api-reference.md`.

## Source Inventory

| File | Lines | Public classes | Public functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/mail/__init__.py` | 156 | 0 | 0 | AquilaMail -- Production-ready async mail subsystem for Aquilia. |
| `aquilia/mail/config.py` | 819 | 15 | 0 | AquilaMail Configuration -- Serializer-based, DI-aware mail configuration. |
| `aquilia/mail/di_providers.py` | 298 | 3 | 3 | AquilaMail -- DI Providers |
| `aquilia/mail/envelope.py` | 261 | 4 | 0 | AquilaMail Envelope -- The internal representation of a mail message. |
| `aquilia/mail/faults.py` | 179 | 7 | 0 | AquilaMail Faults -- Structured, typed fault definitions for the mail subsystem. |
| `aquilia/mail/message.py` | 368 | 3 | 0 | AquilaMail Messages -- Developer-facing message classes. |
| `aquilia/mail/providers/__init__.py` | 129 | 3 | 0 | AquilaMail Provider Interface -- Protocol + result types for mail providers. |
| `aquilia/mail/providers/console.py` | 86 | 1 | 0 | Console Provider -- prints emails to stdout/logger (development). |
| `aquilia/mail/providers/file.py` | 351 | 1 | 0 | File Provider -- Writes emails to .eml files on disk. |
| `aquilia/mail/providers/sendgrid.py` | 396 | 1 | 0 | SendGrid Provider -- Async SendGrid Web API v3 delivery via httpx. |
| `aquilia/mail/providers/ses.py` | 440 | 1 | 0 | AWS SES Provider -- Async Amazon Simple Email Service delivery. |
| `aquilia/mail/providers/smtp.py` | 536 | 1 | 0 | SMTP Provider -- Production-grade async SMTP delivery via aiosmtplib. |
| `aquilia/mail/service.py` | 433 | 1 | 3 | AquilaMail Service -- Main orchestrator for the mail subsystem. |
| `aquilia/mail/template/__init__.py` | 147 | 0 | 3 | AquilaMail ATS (Aquilia Template Syntax) -- Stub module. |

## Detected Config-Oriented Classes

| Class | Source | Methods | Summary |
| --- | --- | --- | --- |
| `ProviderConfigBlueprint` | `aquilia/mail/config.py` | `validate` | Blueprint for a single mail provider configuration. |
| `MailAuthConfigBlueprint` | `aquilia/mail/config.py` | `validate` | Blueprint for mail provider authentication credentials. |
| `RetryConfigBlueprint` | `aquilia/mail/config.py` | `validate` | Blueprint for retry / backoff configuration. |
| `RateLimitConfigBlueprint` | `aquilia/mail/config.py` |  | Blueprint for global and per-domain rate-limiting. |
| `SecurityConfigBlueprint` | `aquilia/mail/config.py` | `validate` | Blueprint for security / deliverability settings. |
| `TemplateConfigBlueprint` | `aquilia/mail/config.py` |  | Blueprint for ATS template engine configuration. |
| `QueueConfigBlueprint` | `aquilia/mail/config.py` |  | Blueprint for queue / storage settings. |
| `ProviderConfig` | `aquilia/mail/config.py` |  | Attribute-access wrapper for a validated provider config. |
| `RetryConfig` | `aquilia/mail/config.py` |  | Attribute-access wrapper for a validated retry config. |
| `RateLimitConfig` | `aquilia/mail/config.py` |  | Attribute-access wrapper for a validated rate-limit config. |
| `SecurityConfig` | `aquilia/mail/config.py` |  | Attribute-access wrapper for a validated security config. |
| `TemplateConfig` | `aquilia/mail/config.py` |  | Attribute-access wrapper for a validated template config. |
| `QueueConfig` | `aquilia/mail/config.py` |  | Attribute-access wrapper for a validated queue config. |
| `MailAuthConfig` | `aquilia/mail/config.py` | `plain`, `api_key`, `aws_ses`, `oauth2`, `anonymous` | Attribute-access wrapper for validated mail authentication credentials. |
| `MailConfig` | `aquilia/mail/config.py` | `to_dict`, `from_dict`, `development`, `production` | Top-level mail configuration. |
| `MailConfigProvider` | `aquilia/mail/di_providers.py` | `provide` | DI provider that builds and validates MailConfig from workspace data. |
| `MailServiceProvider` | `aquilia/mail/di_providers.py` | `provide` | DI provider for MailService -- the central mail orchestrator. |
| `MailProviderRegistry` | `aquilia/mail/di_providers.py` | `add_scan_package`, `discover`, `get_provider_class`, `list_types` | Auto-discovers IMailProvider implementations using Aquilia's PackageScanner (discovery system). |
| `MailConfigFault` | `aquilia/mail/faults.py` |  | Mail configuration error (missing provider, bad credentials, etc.). |
| `ProviderResultStatus` | `aquilia/mail/providers/__init__.py` |  | Granular result from a provider send attempt. |
| `ProviderResult` | `aquilia/mail/providers/__init__.py` | `is_success`, `should_retry` | Result returned by IMailProvider.send(). |
| `IMailProvider` | `aquilia/mail/providers/__init__.py` | `send`, `send_batch`, `health_check`, `initialize`, `shutdown` | Interface that all mail provider backends must implement. |
| `ConsoleProvider` | `aquilia/mail/providers/console.py` | `initialize`, `shutdown`, `send`, `send_batch`, `health_check` | Provider that logs emails to the console instead of sending them. |
| `FileProvider` | `aquilia/mail/providers/file.py` | `initialize`, `shutdown`, `send`, `send_batch`, `health_check`, `list_files`, `read_last`, `clear` | Mail provider that writes emails to .eml files on disk. |
| `SendGridProvider` | `aquilia/mail/providers/sendgrid.py` | `initialize`, `shutdown`, `send`, `send_batch`, `health_check` | Async SendGrid mail provider using the v3 Web API. |
| `SESProvider` | `aquilia/mail/providers/ses.py` | `initialize`, `shutdown`, `send`, `send_batch`, `health_check` | Async AWS SES mail provider. |
| `SMTPProvider` | `aquilia/mail/providers/smtp.py` | `initialize`, `shutdown`, `send`, `send_batch`, `health_check` | Async SMTP mail provider backed by aiosmtplib. |

## Runtime Wiring Paths

- `workspace.py` defines workspace-level structure with `Workspace`, `Module`, and `Integration` builders.
- `modules/<name>/manifest.py` defines module internals with `AppManifest`.
- `ConfigLoader.get(...)` resolves dotted configuration paths at runtime.
- `AquiliaServer` consumes resolved config during middleware and subsystem setup.
- Subsystems with optional providers only require optional dependencies when their backend/provider is configured.

## Verification Checklist

1. Run `aq validate` to verify manifests.
2. Run `aq inspect config` to inspect resolved configuration.
3. Run `aq doctor` for workspace and integration diagnostics.
4. For server-only wiring, start via `aq run` and check startup logs plus `GET /_health`.

## Related Pages

- `api-reference.md` for exact class fields, methods, constants, and signatures.
- `integration-guide.md` for the workspace/manifest wiring pattern.
- `edge-cases-and-limitations.md` for fallback and compatibility behavior.
