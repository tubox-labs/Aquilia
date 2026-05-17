# Mail Documentation

This directory is the professional documentation set for `mail`. It is implementation-driven and aligned with the current source files under `aquilia/mail`.

## What This Covers

The async mail subsystem with configuration, messages, envelopes, provider registry, SMTP, SES, SendGrid, console, file providers, templates, and testing helpers.

## Source Files Read

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

## Document Map

- `architecture.md`: Runtime architecture and module boundaries
- `configuration.md`: Configuration entry points, datatypes, and precedence
- `api-reference.md`: Classes, methods, functions, constants, and data fields extracted from source
- `integration-guide.md`: How to wire the module into a real Aquilia application
- `cli-reference.md`: Command line surface and operational commands
- `edge-cases-and-limitations.md`: Known edge cases and implementation limits
- `troubleshooting.md`: Common failures and diagnosis steps
- `examples.md`: Code examples and usage patterns

## Public Surface Snapshot

- Python files: 14
- Public classes: 41
- Configuration or dataclass-like types: 11
- Public functions: 9
- Constants detected: 12

## Fast Start

```python
from aquilia.mail import EmailMessage, MailConfig, MailService
from aquilia.mail.providers.console import ConsoleProvider

service = MailService(config=MailConfig(default_from="noreply@example.test"), provider=ConsoleProvider())
message = EmailMessage(to=["user@example.test"], subject="Welcome", body="Hello")
result = await service.send(message)
```

## Read Next

Start with `architecture.md` if you are learning how the subsystem fits into runtime boot. Use `api-reference.md` when you need exact methods, datatypes, and class fields. Use `examples.md` for copyable patterns that match the current code.
