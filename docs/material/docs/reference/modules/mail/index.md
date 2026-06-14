# Mail Module

> `aquilia.mail` — Multi-provider email delivery

The Mail module provides async email delivery with multiple backends (SMTP, SendGrid, SES), template-based messages, HTML/plain-text envelopes, and a convenient `send_mail` / `asend_mail` API.

## When to Use

Use the Mail module when you need:

- Sending transactional emails from controllers/services
- Template-based email composition
- Multi-provider failover (SMTP → SendGrid → SES)
- Email attachments and inline images
- Async email delivery via background tasks

## Key Classes

| Class | Purpose |
|---|---|
| `MailService` | Central mail delivery service |
| `EmailMessage` | Email message with recipients, body, attachments |
| `EmailMultiAlternatives` | Multipart HTML + plain text email |
| `TemplateMessage` | Template-rendered email |
| `MailEnvelope` | Envelope data (from, to, subject) |
| `MailConfig` | Typed mail configuration |
| `IMailProvider` | Provider interface |
| `SMTPProvider` | SMTP delivery |
| `SendGridProvider` | SendGrid API delivery |
| `SESProvider` | AWS SES delivery |
| `FileProvider` | Writes emails to files (dev) |
| `ConsoleProvider` | Prints emails to console (dev) |

## Quick Example

```python
from aquilia.mail import send_mail, EmailMessage

# Simple send
await send_mail(
    to=["user@example.com"],
    subject="Welcome!",
    body="Thank you for signing up.",
)

# With HTML and attachments
message = EmailMessage(
    subject="Your Report",
    to=["user@example.com"],
    body="Please find your report attached.",
    html="<h1>Report</h1><p>Please find your report attached.</p>",
    attachments=[("report.pdf", pdf_bytes, "application/pdf")],
)
await mail_service.send(message)
```

## Import Path

```python
from aquilia.mail import (
    MailService,
    EmailMessage,
    EmailMultiAlternatives,
    TemplateMessage,
    MailEnvelope,
    MailConfig,
    send_mail,
    asend_mail,
)
```

## Related Modules

- [templates](../templates/index.md) — Template rendering for email bodies
- [integrations](../integrations/index.md) — `MailIntegration` config builder
- [tasks](../tasks/index.md) — Background email delivery