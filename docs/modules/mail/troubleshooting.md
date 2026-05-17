# Mail Troubleshooting

Async mail subsystem with message classes, config blueprints, providers, DI registration, templates, faults, and convenience send APIs.

## Fast Diagnosis Flow

1. Confirm the command is run from a directory containing `workspace.py` unless it is help/version/init/doctor.
2. Run `aq doctor` for workspace, environment, registry, integration, and deployment checks.
3. Run `aq validate` to catch manifest errors.
4. Run `aq inspect config` to inspect resolved settings.
5. Run `aq inspect modules` and `aq inspect routes` when discovery or routing is suspect.
6. Check `api-reference.md` for exact public API signatures.

## Module-Relevant Commands

- `aq mail check`
- `aq mail send-test`
- `aq mail inspect`

## Symptoms And Actions

| Symptom | Likely Source | Action |
| --- | --- | --- |
| Import error during startup | Bad manifest class path or optional provider dependency | Check `modules/<name>/manifest.py`, install the relevant extra, and rerun `aq validate`. |
| Route not found | Controller omitted from manifest, wrong route prefix, or startup conflict | Run `aq inspect routes`; inspect controller decorators and `Module.route_prefix()`. |
| Dependency not found | Service not registered or constructor annotation cannot be resolved | Check `AppManifest.services`, DI provider registrations, and `aq inspect di`. |
| Config value missing | Dotenv/env overlay not loaded or wrong nested key | Check `ConfigLoader` precedence and `AQ_` double-underscore key names. |
| Production security failure | Insecure secret or required key not configured | Set `AQ_SECRET_KEY`, `SECRET_KEY`, or Python-native secret config. |
| Optional subsystem unavailable | Provider/backend dependency or startup connection failed | Check startup logs; optional subsystems often log non-fatal failures. |

## Source Files To Inspect

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
