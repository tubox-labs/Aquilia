# Mail Documentation

Async mail subsystem with message classes, config blueprints, providers, DI registration, templates, faults, and convenience send APIs.

## Coverage Snapshot

- Source files: 14
- Source lines: 4599
- Public classes: 41
- Public module functions: 9
- Constants/module flags: 14
- Public exports in `__all__`: 40

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

- `architecture.md`: module boundaries, dependencies, lifecycle, and extension points.
- `configuration.md`: configuration classes, builders, server wiring, and precedence.
- `api-reference.md`: source-extracted classes, methods, functions, constants, exports, and signatures.
- `integration-guide.md`: how to wire the module into an Aquilia app.
- `cli-reference.md`: mounted `aq` commands for this module, if any.
- `examples.md`: usage examples derived from source and checked example apps.
- `edge-cases-and-limitations.md`: implementation limits and compatibility behavior.
- `troubleshooting.md`: diagnostic commands and common failure patterns.
