# Mail Notifications

The Mail Notifications example demonstrates a welcome notification pipeline that
builds `EmailMessage` envelopes and delivers them through Aquilia's file-based
mail provider.

---

## What It Demonstrates

- `MailIntegration` with `FileProvider` for local file delivery
- `EmailMessage` envelope construction with subject, body, recipients, and attachments
- File-based mail delivery writing `.eml` files and `index.jsonl` entries
- Provider lifecycle: `initialize()` before `send()`
- Attachment handling with digest-based blob storage
- `ProviderResultStatus` for tracking delivery outcomes

## Key Files

| File | Purpose |
| ---- | ------- |
| `workspace.py` | Wires `MailIntegration` with `FileProvider` |
| `modules/notifications/manifest.py` | Declares `NotificationsController` and `NotificationService` |
| `modules/notifications/controllers.py` | Welcome notification endpoint |
| `modules/notifications/services.py` | `NotificationService` building and sending envelopes |

## Workspace Configuration

```python
from aquilia.integrations import DiIntegration, FileProvider, MailIntegration

workspace = (
    Workspace("mail-notifications-app", version="1.0.0")
    .runtime(mode="dev", host="127.0.0.1", port=8064, reload=True)
    .module(Module("notifications", version="1.0.0").route_prefix("/notifications"))
    .integrate(MailIntegration(
        default_from="noreply@example.test",
        providers=[FileProvider(name="file", output_dir="var/mail")],
    ))
    .integrate(DiIntegration(auto_wire=True))
)
```

## Mail Envelope Construction

The `NotificationService` builds and sends `EmailMessage` envelopes:

```python
from aquilia.mail import EmailMessage, MailEnvelope, ProviderResultStatus

class NotificationService:
    def __init__(self):
        self._provider = FileProvider(name="file", output_dir="var/mail")
        self._initialized = False

    async def _ensure_initialized(self):
        if not self._initialized:
            await self._provider.initialize()
            self._initialized = True

    async def send_welcome(self, email: str, name: str) -> dict:
        await self._ensure_initialized()

        message = EmailMessage(
            subject=f"Welcome, {name}!",
            body_text=f"Hello {name},\n\nWelcome to our platform.",
            body_html=f"<h1>Welcome, {name}!</h1><p>We're glad you're here.</p>",
            to=[email],
            from_address="noreply@example.test",
        )

        envelope = MailEnvelope(message=message, metadata={})

        result = await self._provider.send(envelope)
        return {"sent": result.status == ProviderResultStatus.SENT, "status": result.status.value}
```

Key concepts:

- `EmailMessage` holds subject, text/HTML body, recipients, sender, and attachments
- `MailEnvelope` wraps a message with provider-specific metadata
- Providers must be `initialize()`d before `send()` is called
- `FileProvider` writes `.eml` files to disk and appends delivery records to `index.jsonl`

## Delivery Flow

1. Controller receives a POST request with recipient email and name
2. `NotificationService` builds an `EmailMessage` with a welcome template
3. The message is wrapped in a `MailEnvelope`
4. `FileProvider.send()` writes the envelope to `var/mail/<timestamp>.eml`
5. A corresponding entry is appended to `var/mail/index.jsonl`
6. The result status is returned to the controller

## Running

```bash
cd examples/mail_notifications_app
python -m uvicorn runtime:app --reload --port 8064
```

```bash
# Send a welcome notification
curl -X POST http://127.0.0.1:8064/notifications/welcome \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","name":"Alice"}'

# Check the output directory
ls var/mail/

# Run tests
python -m pytest examples/mail_notifications_app -q
```

## What You'll Learn

- How to configure `MailIntegration` with `FileProvider` for development
- How to construct `EmailMessage` envelopes with text and HTML bodies
- How to manage provider lifecycle with `initialize()` and `send()`
- How to handle `ProviderResultStatus` for delivery outcome tracking
- How the file provider writes mail artifacts for inspection during development