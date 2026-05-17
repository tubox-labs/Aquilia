# mail Module

## Purpose

Async mail and provider abstraction. Use this module for email messages, envelopes, templates, provider registries, SMTP, SES, SendGrid, console and file providers, rate limits, queues, and mail testing.

## Source Coverage

- Python files: 14
- Public classes: 41
- Dataclasses: 3
- Enums: 3
- Public functions: 9

## How It Fits In Aquilia

1. Import the package from `aquilia.mail` or its concrete submodules.
2. Configure it through workspace integrations, manifests, or direct service construction depending on the subsystem.
3. Keep business logic outside transport and framework glue so the subsystem stays testable.

## Practical Guidance

- Prefer typed configuration objects and framework helpers over ad hoc dictionaries when they exist.
- Use the tests in `tests/` as behavioral examples when changing this subsystem.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `ProviderConfigBlueprint` | `aquilia/mail/config.py` | Blueprint for a single mail provider configuration. |
| `MailAuthConfigBlueprint` | `aquilia/mail/config.py` | Blueprint for mail provider authentication credentials. |
| `RetryConfigBlueprint` | `aquilia/mail/config.py` | Blueprint for retry / backoff configuration. |
| `RateLimitConfigBlueprint` | `aquilia/mail/config.py` | Blueprint for global and per-domain rate-limiting. |
| `SecurityConfigBlueprint` | `aquilia/mail/config.py` | Blueprint for security / deliverability settings. |
| `TemplateConfigBlueprint` | `aquilia/mail/config.py` | Blueprint for ATS template engine configuration. |
| `QueueConfigBlueprint` | `aquilia/mail/config.py` | Blueprint for queue / storage settings. |
| `ProviderConfig` | `aquilia/mail/config.py` | Attribute-access wrapper for a validated provider config. |
| `RetryConfig` | `aquilia/mail/config.py` | Attribute-access wrapper for a validated retry config. |
| `RateLimitConfig` | `aquilia/mail/config.py` | Attribute-access wrapper for a validated rate-limit config. |
| `SecurityConfig` | `aquilia/mail/config.py` | Attribute-access wrapper for a validated security config. |
| `TemplateConfig` | `aquilia/mail/config.py` | Attribute-access wrapper for a validated template config. |
| `QueueConfig` | `aquilia/mail/config.py` | Attribute-access wrapper for a validated queue config. |
| `MailAuthConfig` | `aquilia/mail/config.py` | Attribute-access wrapper for validated mail authentication credentials. |
| `MailConfig` | `aquilia/mail/config.py` | Top-level mail configuration. |
| `MailConfigProvider` | `aquilia/mail/di_providers.py` | DI provider that builds and validates MailConfig from workspace data. |
| `MailServiceProvider` | `aquilia/mail/di_providers.py` | DI provider for MailService -- the central mail orchestrator. |
| `MailProviderRegistry` | `aquilia/mail/di_providers.py` | Auto-discovers IMailProvider implementations using Aquilia's |
| `EnvelopeStatus` | `aquilia/mail/envelope.py` | Lifecycle status of an envelope. |
| `Priority` | `aquilia/mail/envelope.py` | Named priority levels. |
| `Attachment` | `aquilia/mail/envelope.py` | Attachment metadata (content stored separately in blob store). |
| `MailEnvelope` | `aquilia/mail/envelope.py` | Immutable mail envelope -- the unit of work in the mail pipeline. |
| `MailFault` | `aquilia/mail/faults.py` | Base class for all mail-subsystem faults. |
| `MailSendFault` | `aquilia/mail/faults.py` | Provider-level send failure (transient or permanent). |
| `MailTemplateFault` | `aquilia/mail/faults.py` | Template parse, compile, or render error. |
| `MailConfigFault` | `aquilia/mail/faults.py` | Mail configuration error (missing provider, bad credentials, etc.). |
| `MailSuppressedFault` | `aquilia/mail/faults.py` | Recipient is on the suppression list. |
| `MailRateLimitFault` | `aquilia/mail/faults.py` | Rate limit exceeded for provider or domain. |
| `MailValidationFault` | `aquilia/mail/faults.py` | Invalid email address, missing fields, or envelope validation error. |
| `EmailMessage` | `aquilia/mail/message.py` | A single email message -- the primary API for sending mail. |
| `EmailMultiAlternatives` | `aquilia/mail/message.py` | Email with multiple content alternatives (e.g., plain text + HTML). |
| `TemplateMessage` | `aquilia/mail/message.py` | Email rendered from an Aquilia Template Syntax (ATS) template. |
| `MailService` | `aquilia/mail/service.py` | Central mail service -- owns the pipeline from message to delivery. |
| `ProviderResultStatus` | `aquilia/mail/providers/__init__.py` | Granular result from a provider send attempt. |
| `ProviderResult` | `aquilia/mail/providers/__init__.py` | Result returned by IMailProvider.send(). |
| `IMailProvider` | `aquilia/mail/providers/__init__.py` | Interface that all mail provider backends must implement. |
| `ConsoleProvider` | `aquilia/mail/providers/console.py` | Provider that logs emails to the console instead of sending them. |
| `FileProvider` | `aquilia/mail/providers/file.py` | Mail provider that writes emails to .eml files on disk. |
| `SendGridProvider` | `aquilia/mail/providers/sendgrid.py` | Async SendGrid mail provider using the v3 Web API. |
| `SESProvider` | `aquilia/mail/providers/ses.py` | Async AWS SES mail provider. |
| `SMTPProvider` | `aquilia/mail/providers/smtp.py` | Async SMTP mail provider backed by aiosmtplib. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `create_mail_config` | `aquilia/mail/di_providers.py` | Factory that creates a validated MailConfig. |
| `create_mail_service` | `aquilia/mail/di_providers.py` | Factory that creates a MailService from config. |
| `register_mail_providers` | `aquilia/mail/di_providers.py` | Register all mail DI providers into a container. |
| `set_mail_service` | `aquilia/mail/service.py` | Install a MailService as the module-level singleton (or None to reset). |
| `send_mail` | `aquilia/mail/service.py` | Send an email synchronously. |
| `asend_mail` | `aquilia/mail/service.py` | Send an email asynchronously (Aquilia-native API). |
| `configure` | `aquilia/mail/template/__init__.py` | Set template search directories (called at MailService startup). |
| `render_string` | `aquilia/mail/template/__init__.py` | Render an ATS template string with the given context. |
| `render_template` | `aquilia/mail/template/__init__.py` | Render a named ATS template file with the given context. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/mail/__init__.py` | AquilaMail -- Production-ready async mail subsystem for Aquilia. |
| `aquilia/mail/config.py` | AquilaMail Configuration -- Serializer-based, DI-aware mail configuration. |
| `aquilia/mail/di_providers.py` | AquilaMail -- DI Providers |
| `aquilia/mail/envelope.py` | AquilaMail Envelope -- The internal representation of a mail message. |
| `aquilia/mail/faults.py` | AquilaMail Faults -- Structured, typed fault definitions for the mail subsystem. |
| `aquilia/mail/message.py` | AquilaMail Messages -- Developer-facing message classes. |
| `aquilia/mail/providers/__init__.py` | AquilaMail Provider Interface -- Protocol + result types for mail providers. |
| `aquilia/mail/providers/console.py` | Console Provider -- prints emails to stdout/logger (development). |
| `aquilia/mail/providers/file.py` | File Provider -- Writes emails to .eml files on disk. |
| `aquilia/mail/providers/sendgrid.py` | SendGrid Provider -- Async SendGrid Web API v3 delivery via httpx. |
| `aquilia/mail/providers/ses.py` | AWS SES Provider -- Async Amazon Simple Email Service delivery. |
| `aquilia/mail/providers/smtp.py` | SMTP Provider -- Production-grade async SMTP delivery via aiosmtplib. |
| `aquilia/mail/service.py` | AquilaMail Service -- Main orchestrator for the mail subsystem. |
| `aquilia/mail/template/__init__.py` | AquilaMail ATS (Aquilia Template Syntax) -- Stub module. |

## Testing Pointers

Search `tests/` for `mail` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
