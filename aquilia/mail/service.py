"""
AquilaMail Service -- Main orchestrator for the mail subsystem.

MailService is the DI-registered singleton that owns the envelope store,
dispatcher, providers, template engine, and metrics.  It is the single
entry point for all mail operations.

Module-level convenience functions (send_mail, asend_mail) delegate to
the active MailService instance.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from ..di.decorators import service
from .config import MailConfig
from .envelope import EnvelopeStatus, MailEnvelope
from .faults import MailConfigFault

logger = logging.getLogger("aquilia.mail")

# ── Module-level singleton reference ────────────────────────────────

_mail_service: MailService | None = None


def _get_mail_service() -> MailService:
    """Return the active MailService (set during server startup)."""
    if _mail_service is None:
        raise MailConfigFault(
            "MailService not initialised.  Ensure mail integration is enabled "
            "in your workspace.py or that AquiliaServer has started.",
            config_key="mail.enabled",
        )
    return _mail_service


def set_mail_service(svc: MailService | None) -> None:
    """Install a MailService as the module-level singleton (or None to reset)."""
    global _mail_service
    _mail_service = svc


# ── Convenience functions ───────────────────────────────────────────


def send_mail(
    subject: str,
    body: str,
    from_email: str | None = None,
    to: Sequence[str] | str | None = None,
    cc: Sequence[str] | str | None = None,
    bcc: Sequence[str] | str | None = None,
    reply_to: str | None = None,
    headers: dict[str, str] | None = None,
    attachments: Sequence[tuple[str, bytes, str]] | None = None,
    priority: int = 50,
    fail_silently: bool = False,
    **kwargs: Any,
) -> str | None:
    """
    Send an email synchronously.

    Usage:
        send_mail(
            subject="Invoice",
            body="Please find your invoice attached.",
            to=["user@example.com"],
            attachments=[("invoice.pdf", pdf_bytes, "application/pdf")],
        )

    Args:
        attachments: Optional sequence of attachments as
            ``(filename, content_bytes, content_type)`` tuples.

    Returns:
        envelope_id on success, None if fail_silently.
    """
    from .message import EmailMessage

    msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=to,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
        headers=headers,
        attachments=list(attachments) if attachments is not None else None,
        priority=priority,
        **kwargs,
    )
    return msg.send(fail_silently=fail_silently)


async def asend_mail(
    subject: str,
    body: str,
    from_email: str | None = None,
    to: Sequence[str] | str | None = None,
    cc: Sequence[str] | str | None = None,
    bcc: Sequence[str] | str | None = None,
    reply_to: str | None = None,
    headers: dict[str, str] | None = None,
    attachments: Sequence[tuple[str, bytes, str]] | None = None,
    priority: int = 50,
    fail_silently: bool = False,
    **kwargs: Any,
) -> str | None:
    """
    Send an email asynchronously (Aquilia-native API).

    Usage:
        await asend_mail(
            subject="Welcome",
            body="Your account is ready.",
            to="user@example.com",
            attachments=[("welcome.txt", b"Welcome!", "text/plain")],
        )

    Args:
        attachments: Optional sequence of attachments as
            ``(filename, content_bytes, content_type)`` tuples.

    Returns:
        envelope_id on success, None if fail_silently.
    """
    from .message import EmailMessage

    msg = EmailMessage(
        subject=subject,
        body=body,
        from_email=from_email,
        to=to,
        cc=cc,
        bcc=bcc,
        reply_to=reply_to,
        headers=headers,
        attachments=list(attachments) if attachments is not None else None,
        priority=priority,
        **kwargs,
    )
    return await msg.asend(fail_silently=fail_silently)


# ── MailService ─────────────────────────────────────────────────────


@service(scope="app", name="MailService")
class MailService:
    """
    Central mail service -- owns the pipeline from message to delivery.

    Lifecycle:
        AquiliaServer.__init__  →  MailService created, registered in DI
        AquiliaServer.startup   →  MailService.on_startup (connect providers)
        AquiliaServer.shutdown  →  MailService.on_shutdown (flush + disconnect)

    Responsibilities:
        - Accept EmailMessage / TemplateMessage objects
        - Build envelopes, store in queue, dispatch
        - Manage providers, rate limits, retries
        - Expose metrics and trace spans
    """

    def __init__(self, config: MailConfig | None = None):
        self.config = config or MailConfig()
        self._providers: dict[str, Any] = {}  # name → IMailProvider
        self._started = False
        self.logger = logger

        # Sub-components (initialized lazily or at startup)
        self._store = None  # EnvelopeStore
        self._dispatcher = None  # Dispatcher
        self._template_renderer = None  # ATS renderer

    # ── Lifecycle ───────────────────────────────────────────────────

    async def on_startup(self) -> None:
        """Initialize providers, store, dispatcher."""
        if self._started:
            return

        # Initialize providers from config
        for pc in self.config.providers:
            if not pc.enabled:
                continue
            # Apply top-level auth to providers that lack their own credentials
            self._apply_global_auth(pc)
            try:
                provider = self._create_provider(pc)
                await provider.initialize()
                self._providers[pc.name] = provider
            except Exception as e:
                self.logger.error(f"  Provider '{pc.name}' failed: {e}")

        # Console fallback for development
        if self.config.console_backend and "console" not in self._providers:
            from .providers.console import ConsoleProvider

            cp = ConsoleProvider()
            await cp.initialize()
            self._providers["console"] = cp

        self._started = True

    async def on_shutdown(self) -> None:
        """Shutdown providers and flush queue."""
        if not self._started:
            return
        for name, provider in self._providers.items():
            try:
                await provider.shutdown()
            except Exception as e:
                self.logger.warning(f"  Provider '{name}' shutdown error: {e}")
        self._providers.clear()
        self._started = False

    # ── Auth propagation ────────────────────────────────────────────

    def _apply_global_auth(self, pc: Any) -> None:
        """
        Apply top-level ``MailConfig.auth`` to a provider config when the
        provider has no explicit ``username``/``password``.

        The global auth acts as a default -- individual providers can
        override it by setting their own credentials.
        """
        if self.config.auth is None:
            return
        # Provider already has explicit credentials -- skip
        if pc.username or pc.password:
            return
        # Provider has its own nested auth dict -- skip
        if getattr(pc, "auth", None) is not None:
            return
        # Apply from the global MailAuthConfig
        auth = self.config.auth
        method = getattr(auth, "method", "plain")
        if method in ("plain", "ntlm"):
            uname = getattr(auth, "username", None)
            pwd = getattr(auth, "password", None)
            if uname:
                pc.username = uname
            if pwd:
                pc.password = pwd

    # ── Provider factory ────────────────────────────────────────────

    def _create_provider(self, pc: Any) -> Any:
        """
        Instantiate a provider from ProviderConfig.

        Uses hard-coded mappings for built-in types, then falls back
        to the MailProviderRegistry (discovery system) for custom types.
        """

        if pc.type == "smtp":
            from .providers.smtp import SMTPProvider

            return SMTPProvider(
                name=pc.name,
                host=pc.host or pc.config.get("host", "localhost"),
                port=pc.port or pc.config.get("port", 587),
                username=pc.username or pc.config.get("username"),
                password=pc.password or pc.config.get("password"),
                use_tls=pc.use_tls,
                use_ssl=pc.use_ssl,
                timeout=pc.timeout,
            )
        elif pc.type == "ses":
            from .providers.ses import SESProvider

            return SESProvider(
                name=pc.name,
                region=pc.config.get("region", "us-east-1"),
                **{k: v for k, v in pc.config.items() if k != "region"},
            )
        elif pc.type == "sendgrid":
            from .providers.sendgrid import SendGridProvider

            return SendGridProvider(
                name=pc.name,
                api_key=pc.config.get("api_key", ""),
            )
        elif pc.type == "console":
            from .providers.console import ConsoleProvider

            return ConsoleProvider(name=pc.name)
        elif pc.type == "file":
            from .providers.file import FileProvider

            return FileProvider(
                name=pc.name,
                output_dir=pc.config.get("output_dir", "/tmp/aquilia_mail"),
            )
        else:
            # Fallback: try discovery-based provider registry
            provider_cls = self._resolve_provider_via_discovery(pc.type)
            if provider_cls is not None:
                return provider_cls(name=pc.name, **pc.config)
            raise MailConfigFault(
                f"Unknown mail provider type: {pc.type!r}",
                config_key=f"mail.providers.{pc.name}.type",
            )

    def _resolve_provider_via_discovery(self, provider_type: str) -> Any:
        """
        Try to resolve a provider class via the MailProviderRegistry.

        Uses Aquilia's PackageScanner / discovery system to find
        IMailProvider implementations registered in the app.
        """
        try:
            from .di_providers import MailProviderRegistry

            registry = MailProviderRegistry()
            return registry.get_provider_class(provider_type)
        except Exception:
            return None

    # ── Send pipeline ───────────────────────────────────────────────

    async def send_message(self, message: Any) -> str:
        """
        Accept an EmailMessage, build envelope, dispatch.

        This is the main entry point used by message.send() / .asend().

        Returns:
            envelope_id
        """

        envelope, blobs = message.build_envelope(
            default_from=self.config.default_from,
        )

        # Apply subject prefix
        if self.config.subject_prefix:
            envelope.subject = self.config.subject_prefix + envelope.subject

        # In preview mode, just log -- don't actually send
        if self.config.preview_mode:
            envelope.status = EnvelopeStatus.SENT
            return envelope.id

        # Direct dispatch (synchronous send for now; PR5 adds queue + dispatcher)
        await self._dispatch_direct(envelope)
        return envelope.id

    async def _dispatch_direct(self, envelope: MailEnvelope) -> None:
        """
        Dispatch an envelope directly (no queue).

        Tries providers in priority order.  Falls back to next on transient error.
        """
        if not self._providers:
            if self.config.console_backend:
                # Auto-create console provider
                from .providers.console import ConsoleProvider

                cp = ConsoleProvider()
                await cp.initialize()
                self._providers["console"] = cp
            else:
                raise MailConfigFault(
                    "No mail providers configured",
                    config_key="mail.providers",
                )

        # Sort providers by priority (lower = preferred)
        sorted_providers = sorted(
            self._providers.values(),
            key=lambda p: getattr(p, "priority", 50),
        )

        last_error: Exception | None = None
        for provider in sorted_providers:
            try:
                envelope.status = EnvelopeStatus.SENDING
                envelope.provider_name = provider.name
                result = await provider.send(envelope)

                if result.is_success:
                    envelope.status = EnvelopeStatus.SENT
                    envelope.provider_message_id = result.provider_message_id
                    return
                elif result.should_retry:
                    self.logger.warning(f"Transient failure from {provider.name}: {result.error_message}")
                    last_error = Exception(result.error_message)
                    continue
                else:
                    # Permanent failure
                    envelope.status = EnvelopeStatus.FAILED
                    envelope.error_message = result.error_message
                    from .faults import MailSendFault

                    raise MailSendFault(
                        f"Permanent send failure via {provider.name}: {result.error_message}",
                        provider=provider.name,
                        transient=False,
                        envelope_id=envelope.id,
                    )
            except Exception as e:
                last_error = e
                self.logger.warning(f"Provider {provider.name} error: {e}")
                continue

        # All providers failed
        envelope.status = EnvelopeStatus.FAILED
        envelope.error_message = str(last_error)
        from .faults import MailSendFault

        raise MailSendFault(
            f"All providers failed for envelope {envelope.id}: {last_error}",
            provider="all",
            transient=True,
            envelope_id=envelope.id,
        )

    # ── Introspection ───────────────────────────────────────────────

    def get_provider_names(self) -> list[str]:
        """Return names of registered providers."""
        return list(self._providers.keys())

    def is_healthy(self) -> bool:
        """Quick health check."""
        return self._started and len(self._providers) > 0
