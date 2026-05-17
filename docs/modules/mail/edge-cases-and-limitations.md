# Mail Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `MailFault` | `aquilia/mail/faults.py` | Base class for all mail-subsystem faults. |
| `MailSendFault` | `aquilia/mail/faults.py` | Provider-level send failure (transient or permanent). |
| `MailTemplateFault` | `aquilia/mail/faults.py` | Template parse, compile, or render error. |
| `MailConfigFault` | `aquilia/mail/faults.py` | Mail configuration error (missing provider, bad credentials, etc.). |
| `MailSuppressedFault` | `aquilia/mail/faults.py` | Recipient is on the suppression list. |
| `MailRateLimitFault` | `aquilia/mail/faults.py` | Rate limit exceeded for provider or domain. |
| `MailValidationFault` | `aquilia/mail/faults.py` | Invalid email address, missing fields, or envelope validation error. |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/mail/__init__.py`: AquilaMail -- Production-ready async mail subsystem for Aquilia.
- `aquilia/mail/config.py`: AquilaMail Configuration -- Serializer-based, DI-aware mail configuration.
- `aquilia/mail/di_providers.py`: AquilaMail -- DI Providers
- `aquilia/mail/envelope.py`: AquilaMail Envelope -- The internal representation of a mail message.
- `aquilia/mail/faults.py`: AquilaMail Faults -- Structured, typed fault definitions for the mail subsystem.
- `aquilia/mail/message.py`: AquilaMail Messages -- Developer-facing message classes.
- `aquilia/mail/providers/__init__.py`: AquilaMail Provider Interface -- Protocol + result types for mail providers.
- `aquilia/mail/providers/console.py`: Console Provider -- prints emails to stdout/logger (development).
- `aquilia/mail/providers/file.py`: File Provider -- Writes emails to .eml files on disk.
- `aquilia/mail/providers/sendgrid.py`: SendGrid Provider -- Async SendGrid Web API v3 delivery via httpx.
- `aquilia/mail/providers/ses.py`: AWS SES Provider -- Async Amazon Simple Email Service delivery.
- `aquilia/mail/providers/smtp.py`: SMTP Provider -- Production-grade async SMTP delivery via aiosmtplib.
- `aquilia/mail/service.py`: AquilaMail Service -- Main orchestrator for the mail subsystem.
- `aquilia/mail/template/__init__.py`: AquilaMail ATS (Aquilia Template Syntax) -- Stub module.
