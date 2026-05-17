# Mail Notifications App

## Purpose

Shows a real mail notification workflow that builds `EmailMessage` envelopes and delivers through Aquilia's file provider.

## Architecture

- `workspace.py` wires `MailIntegration` with a `FileProvider`.
- `NotificationService` builds messages, attaches files, copies attachment blobs to the envelope, and calls the provider.
- `AppManifest` exposes the notification controller and service.

## Setup

```bash
python -m pip install -e ".[dev]"
python -m pytest examples/mail_notifications_app -q
```

## Run

```bash
cd examples/mail_notifications_app
python -m uvicorn runtime:app --reload --port 8064
```

## Expected Behavior

`POST /notifications/welcome` writes an `.eml` file and `index.jsonl` entry instead of sending external mail.

## Common Pitfalls

- Provider delivery needs `initialize()` before `send()`.
- Attachments are represented in envelopes by digest; file provider reads bytes from `envelope.metadata["blob:<digest>"]`.

## Extension Ideas

Add templates, retries, provider failover, queue-backed dispatch, and SendGrid or SES configuration.

## Related APIs

`EmailMessage`, `MailEnvelope`, `FileProvider`, `ProviderResultStatus`, `MailIntegration`.
