"""
AquilaMail -- Production-ready async mail subsystem for Aquilia.

Ergonomic mail API with Aquilia-native features:
- Unique Aquilia Template Syntax (ATS) for mail templates
- Provider-agnostic sending (SMTP, SES, SendGrid, custom)
- Reliable delivery: retries, backoff, idempotency, rate-limiting
- Bounce & complaint handling, suppression lists
- Observability: metrics, tracing, structured logs
- Security: DKIM signing, TLS, PII redaction
- DI-scoped, manifest-wired, lifecycle-aware

Quick Start:
    from aquilia.mail import send_mail, asend_mail

    # Synchronous
    send_mail(
        subject="Hello",
        body="Welcome!",
        from_email="noreply@myapp.com",
        to=["user@example.com"],
    )

    # Async
    await asend_mail(
        subject="Hello",
        body="Welcome!",
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
    # Config blueprints (Aquilia Blueprint-based validation)
    ProviderConfigBlueprint,
    QueueConfig,
    QueueConfigBlueprint,
    RateLimitConfig,
    RateLimitConfigBlueprint,
    RetryConfig,
    RetryConfigBlueprint,
    SecurityConfig,
    SecurityConfigBlueprint,
    TemplateConfig,
    TemplateConfigBlueprint,
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

# ── Convenience API ─────────────────────────────────────────────────
from .service import asend_mail, send_mail

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
    # Config blueprints
    "ProviderConfigBlueprint",
    "RetryConfigBlueprint",
    "RateLimitConfigBlueprint",
    "SecurityConfigBlueprint",
    "TemplateConfigBlueprint",
    "QueueConfigBlueprint",
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
