# Mail Architecture

## Runtime Role

The async mail subsystem with configuration, messages, envelopes, provider registry, SMTP, SES, SendGrid, console, file providers, templates, and testing helpers.

The implementation is split across 14 Python files. The module boundary is visible in the file inventory below and the API reference is generated from the same source files.

## Primary Source Files

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

## Internal Dependency Shape

The table below is derived from import statements in the module. It shows which top-level packages this module depends on most often.

| Imported package | Import count |
| --- | --- |
| `email` | 15 |
| `__future__` | 13 |
| `typing` | 10 |
| `envelope` | 8 |
| `collections` | 7 |
| `logging` | 7 |
| `providers` | 6 |
| `faults` | 5 |
| `asyncio` | 4 |
| `contextlib` | 3 |
| `pathlib` | 3 |
| `blueprints` | 2 |
| `config` | 2 |
| `dataclasses` | 2 |
| `datetime` | 2 |
| `di` | 2 |
| `enum` | 2 |
| `hashlib` | 2 |
| `re` | 2 |
| `aquilia` | 1 |
| `base64` | 1 |
| `console` | 1 |
| `di_providers` | 1 |
| `file` | 1 |
| `json` | 1 |
| `message` | 1 |
| `sendgrid` | 1 |
| `service` | 1 |
| `ses` | 1 |
| `smtp` | 1 |

## Data And Control Flow

1. Configuration or direct construction creates the public service objects, controllers, providers, or helpers for this module.
2. Runtime code imports the registered classes from manifests, workspace integrations, middleware stacks, or direct application code.
3. Public methods perform validation and convert invalid states into typed Aquilia faults where the implementation defines fault classes.
4. Integration points return Python data structures, `Response` objects, provider results, jobs, sessions, connections, or model instances depending on the subsystem.

## Boundary Rules

- Keep application-specific business decisions outside framework classes unless the class is explicitly a service or controller owned by your app.
- Prefer the public exports and typed configuration dataclasses shown in `api-reference.md`.
- When a module supplies both a low-level primitive and a high-level service, use the service in application code and keep primitives for tests, providers, or advanced integrations.
