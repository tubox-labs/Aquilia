# Mail Architecture

Async mail subsystem with message classes, config contracts, providers, DI registration, templates, faults, and convenience send APIs.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
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

## Internal Shape

`mail` has 14 Python files, 41 public classes, 9 public module-level functions, and 14 constants or module flags detected by AST.

## Runtime Responsibilities

- This module has `aq` command coverage documented in `cli-reference.md`; 3 commands map to this subsystem.

## Internal Imports

| Import | Count |
| --- | ---: |
| `..envelope` | 5 |
| `..providers` | 5 |
| `.envelope` | 3 |
| `.faults` | 3 |
| `..di.decorators` | 2 |
| `.config` | 2 |
| `..contracts.core` | 1 |
| `..contracts.facets` | 1 |
| `..faults` | 1 |
| `..faults.core` | 1 |
| `.console` | 1 |
| `.di_providers` | 1 |
| `.file` | 1 |
| `.message` | 1 |
| `.providers` | 1 |
| `.sendgrid` | 1 |
| `.service` | 1 |
| `.ses` | 1 |
| `.smtp` | 1 |
| `aquilia._version` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `email` | 15 |
| `__future__` | 13 |
| `typing` | 10 |
| `collections` | 7 |
| `logging` | 7 |
| `asyncio` | 4 |
| `contextlib` | 3 |
| `pathlib` | 3 |
| `dataclasses` | 2 |
| `datetime` | 2 |
| `enum` | 2 |
| `hashlib` | 2 |
| `re` | 2 |
| `base64` | 1 |
| `json` | 1 |
| `ssl` | 1 |
| `time` | 1 |
| `uuid` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `ProviderConfigContract` | `aquilia/mail/config.py` | Contract for a single mail provider configuration. |
| `MailAuthConfigContract` | `aquilia/mail/config.py` | Contract for mail provider authentication credentials. |
| `RetryConfigContract` | `aquilia/mail/config.py` | Contract for retry / backoff configuration. |
| `RateLimitConfigContract` | `aquilia/mail/config.py` | Contract for global and per-domain rate-limiting. |
| `SecurityConfigContract` | `aquilia/mail/config.py` | Contract for security / deliverability settings. |
| `TemplateConfigContract` | `aquilia/mail/config.py` | Contract for ATS template engine configuration. |
| `QueueConfigContract` | `aquilia/mail/config.py` | Contract for queue / storage settings. |
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
| `MailProviderRegistry` | `aquilia/mail/di_providers.py` | Auto-discovers IMailProvider implementations using Aquilia's PackageScanner (discovery system). |
| `MailConfigFault` | `aquilia/mail/faults.py` | Mail configuration error (missing provider, bad credentials, etc.). |
| `ProviderResultStatus` | `aquilia/mail/providers/__init__.py` | Granular result from a provider send attempt. |
| `ProviderResult` | `aquilia/mail/providers/__init__.py` | Result returned by IMailProvider.send(). |
| `IMailProvider` | `aquilia/mail/providers/__init__.py` | Interface that all mail provider backends must implement. |
| `ConsoleProvider` | `aquilia/mail/providers/console.py` | Provider that logs emails to the console instead of sending them. |
| `FileProvider` | `aquilia/mail/providers/file.py` | Mail provider that writes emails to .eml files on disk. |
| `SendGridProvider` | `aquilia/mail/providers/sendgrid.py` | Async SendGrid mail provider using the v3 Web API. |
| `SESProvider` | `aquilia/mail/providers/ses.py` | Async AWS SES mail provider. |
| `SMTPProvider` | `aquilia/mail/providers/smtp.py` | Async SMTP mail provider backed by aiosmtplib. |

## Error Handling

Fault/error classes defined here:

`MailFault`, `MailSendFault`, `MailTemplateFault`, `MailConfigFault`, `MailSuppressedFault`, `MailRateLimitFault`, `MailValidationFault`
