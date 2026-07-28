"""
AquilaMail -- async mail subsystem for Aquilia.

Features:
- Aquilia Template Syntax (ATS) for mail bodies — expressions and filters,
  HTML-autoescaped by default (:mod:`aquilia.mail.template`)
- Provider-agnostic sending (SMTP, SES, SendGrid, console, file, custom)
- Priority-ordered provider failover
- Per-provider rate limiting (token bucket, from ``rate_limit_per_min``)
- Retry with exponential backoff, delivered through :mod:`aquilia.tasks`
- Shared MIME construction with optional DKIM signing
  (:mod:`aquilia.mail.mime`; requires ``dkimpy``)
- TLS, XOAUTH2 for Gmail / Microsoft 365, env-var credential indirection
- Durable envelope store and queued background delivery through
  :mod:`aquilia.tasks` (:mod:`aquilia.mail.store`)
- Bounce/complaint webhooks with signature verification, and automatic
  suppression (:mod:`aquilia.mail.webhooks`, :mod:`aquilia.mail.suppression`)
- PII redaction of recipient addresses in logs and faults
  (:mod:`aquilia.mail.redaction`)
- Observability: inspector trace spans, structured faults, admin dashboard
- DI-scoped, manifest-wired, lifecycle-aware

Not implemented today (deliberately absent, not stubbed):

- Delivery / open / click tracking storage
- Template control flow (``if``/``for``) and inheritance — ATS raises on
  these rather than emitting raw tags

Quick Start:
    from aquilia.mail import send_mail, asend_mail

    # Async — the normal path inside controllers, middleware and tasks
    await asend_mail(
        subject="Hello",
        body="Welcome!",
        to=["user@example.com"],
    )

    # Synchronous — scripts and management commands only; raises if called
    # from inside a running event loop
    send_mail(
        subject="Hello",
        body="Welcome!",
        from_email="noreply@myapp.com",
        to=["user@example.com"],
    )

    # Template-based
    from aquilia.mail import TemplateMessage
    msg = TemplateMessage(
        template="welcome.aqt",
        context={"user": {"name": "Asha"}},
        to=["asha@example.com"],
    )
    await msg.asend()
"""

from aquilia._version import __version__  # noqa: F401 — re-exported

from .config import (
    MailConfig,
    # Config wrapper objects (backward-compatible attribute access)
    ProviderConfig,
    # Config contracts (Aquilia Contract-based validation)
    ProviderConfigContract,
    QueueConfig,
    QueueConfigContract,
    RateLimitConfig,
    RateLimitConfigContract,
    RetryConfig,
    RetryConfigContract,
    SecurityConfig,
    SecurityConfigContract,
    TemplateConfig,
    TemplateConfigContract,
)

# ── DI providers ───────────────────────────────────────────────────
from .di_providers import (
    MailConfigProvider,
    MailProviderRegistry,
    MailServiceProvider,
    register_mail_providers,
)

# ── Envelope & config ──────────────────────────────────────────────
from .envelope import EnvelopeStatus, MailEnvelope, Priority

# ── Faults ──────────────────────────────────────────────────────────
from .faults import (
    MailConfigFault,
    MailFault,
    MailRateLimitFault,
    MailSendFault,
    MailSuppressedFault,
    MailTemplateFault,
    MailValidationFault,
)

# ── Core message types ──────────────────────────────────────────────
from .message import (
    EmailMessage,
    EmailMultiAlternatives,
    TemplateMessage,
)

# ── MIME construction & DKIM ────────────────────────────────────────
from .mime import build_mime_message, message_to_bytes, sign_dkim

# ── Provider interface & implementations ─────────────────────────────
from .providers import (
    ConsoleProvider,
    FileProvider,
    IMailProvider,
    ProviderResult,
    ProviderResultStatus,
    SendGridProvider,
    SESProvider,
    SMTPProvider,
)

# ── PII redaction ───────────────────────────────────────────────────
from .redaction import redact_email, redact_pii

# ── Convenience API ─────────────────────────────────────────────────
from .service import asend_mail, send_mail

# ── Envelope store (durable queued delivery) ───────────────────────
from .store import EnvelopeStore, MemoryEnvelopeStore, SQLEnvelopeStore

# ── Suppression list (bounces, complaints, opt-outs) ───────────────
from .suppression import (
    MemorySuppressionList,
    SQLSuppressionList,
    SuppressionEntry,
    SuppressionList,
    SuppressionReason,
)

# ── Provider webhooks ───────────────────────────────────────────────
from .webhooks import (
    EventType,
    WebhookEvent,
    parse_mailgun,
    parse_sendgrid,
    parse_ses,
    process_webhook,
)

__all__ = [
    # Message types
    "EmailMessage",
    "EmailMultiAlternatives",
    "TemplateMessage",
    # Convenience
    "send_mail",
    "asend_mail",
    # Envelope
    "MailEnvelope",
    "EnvelopeStatus",
    "Priority",
    # Config
    "MailConfig",
    # Config contracts
    "ProviderConfigContract",
    "RetryConfigContract",
    "RateLimitConfigContract",
    "SecurityConfigContract",
    "TemplateConfigContract",
    "QueueConfigContract",
    # Config wrappers
    "ProviderConfig",
    "RetryConfig",
    "RateLimitConfig",
    "SecurityConfig",
    "TemplateConfig",
    "QueueConfig",
    # Provider interface
    "IMailProvider",
    "ProviderResult",
    "ProviderResultStatus",
    # Provider implementations
    "ConsoleProvider",
    "FileProvider",
    "SendGridProvider",
    "SESProvider",
    "SMTPProvider",
    # MIME & DKIM
    "build_mime_message",
    "message_to_bytes",
    "sign_dkim",
    # PII redaction
    "redact_email",
    "redact_pii",
    # Envelope store
    "EnvelopeStore",
    "MemoryEnvelopeStore",
    "SQLEnvelopeStore",
    # Suppression
    "SuppressionList",
    "MemorySuppressionList",
    "SQLSuppressionList",
    "SuppressionEntry",
    "SuppressionReason",
    # Webhooks
    "EventType",
    "WebhookEvent",
    "parse_ses",
    "parse_sendgrid",
    "parse_mailgun",
    "process_webhook",
    # DI
    "MailConfigProvider",
    "MailServiceProvider",
    "MailProviderRegistry",
    "register_mail_providers",
    # Faults
    "MailFault",
    "MailSendFault",
    "MailTemplateFault",
    "MailConfigFault",
    "MailSuppressedFault",
    "MailRateLimitFault",
    "MailValidationFault",
]
