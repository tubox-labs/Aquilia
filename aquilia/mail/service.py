"""
AquilaMail Service — orchestrator for the mail subsystem.

:class:`MailService` is the DI-registered singleton that owns provider
instances, credential resolution, per-provider rate limiting, retry
scheduling, and trace instrumentation.  It is the single entry point for
all mail operations.

Pipeline as implemented::

    EmailMessage / TemplateMessage
        │ build_envelope()          → MailEnvelope (+ attachment blobs)
        ▼
    MailService.send_message()
        │ subject prefix, preview-mode short circuit
        ▼
    MailService._dispatch_direct()
        │ providers sorted by priority
        │ per-provider token bucket (rate_limit_per_min)
        │ provider.send() → ProviderResult
        │   success  → EnvelopeStatus.SENT
        │   transient/rate-limited → next provider; if all exhausted,
        │              schedule a retry (see _schedule_retry) while
        │              envelope.attempts < envelope.max_attempts
        │   permanent → EnvelopeStatus.FAILED, raise MailSendFault
        ▼
    Provider (SMTP / SES / SendGrid / console / file)

Retries are delivered by :mod:`aquilia.tasks` when a ``TaskManager`` is
available, so mail reuses the task system's backoff and dead-lettering
rather than reimplementing a scheduler.  Without a task manager, delivery
is single-attempt-per-call and the fault surfaces to the caller.

Module-level convenience functions (:func:`send_mail`, :func:`asend_mail`)
delegate to the active :class:`MailService` instance.
"""

from __future__ import annotations

import logging
import os
import random
import time
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Any

from ..di.decorators import service
from ..tasks.decorators import task
from .config import MailConfig
from .envelope import EnvelopeStatus, MailEnvelope
from .faults import MailConfigFault, MailRateLimitFault
from .redaction import redact_pii

logger = logging.getLogger("aquilia.mail")


def _utcnow() -> datetime:
    """Current UTC time as a timezone-aware datetime."""
    return datetime.now(timezone.utc)


# ── Module-level singleton reference ────────────────────────────────

_mail_service: MailService | None = None


def _get_mail_service() -> MailService:
    """
    Return the active MailService installed at server startup.

    Raises:
        MailConfigFault: If mail is disabled or the server has not started.
    """
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


# ── Rate limiting ───────────────────────────────────────────────────


class _TokenBucket:
    """
    Monotonic-clock token bucket used to throttle a single provider.

    Capacity equals the per-minute allowance, refilled continuously at
    ``rate_per_min / 60`` tokens per second.  A burst up to the full minute's
    allowance is permitted, after which sends are paced by the refill rate —
    the standard shape ESPs expect and the reason a plain fixed-window
    counter is not used (it allows a 2× burst across a window boundary).

    Async-safety:
        Not internally locked.  Each bucket is only touched from the
        service's own coroutine while dispatching, and a lost token under
        interleaving is a rounding error, not a correctness problem — the
        provider still enforces its own hard limit.

    Args:
        rate_per_min: Allowed messages per minute.  Values ≤ 0 disable
            throttling entirely.

    Examples::

        bucket = _TokenBucket(600)     # 10/s sustained
        bucket.acquire()               # True while budget remains
        bucket.retry_after()           # seconds until the next token
    """

    __slots__ = ("rate_per_min", "_tokens", "_updated")

    def __init__(self, rate_per_min: float) -> None:
        self.rate_per_min = float(rate_per_min)
        self._tokens = float(rate_per_min)
        self._updated = time.monotonic()

    @property
    def enabled(self) -> bool:
        """True when this bucket actually throttles (positive rate)."""
        return self.rate_per_min > 0

    def _refill(self) -> None:
        """Add tokens accrued since the last observation, capped at capacity."""
        now = time.monotonic()
        elapsed = now - self._updated
        self._updated = now
        self._tokens = min(self.rate_per_min, self._tokens + elapsed * self.rate_per_min / 60.0)

    def acquire(self) -> bool:
        """
        Consume one token if available.

        Returns:
            ``True`` when the send may proceed, ``False`` when the provider
            is over its configured rate.
        """
        if not self.enabled:
            return True
        self._refill()
        if self._tokens >= 1.0:
            self._tokens -= 1.0
            return True
        return False

    def retry_after(self) -> float:
        """Seconds until at least one token is available."""
        if not self.enabled or self._tokens >= 1.0:
            return 0.0
        return (1.0 - self._tokens) * 60.0 / self.rate_per_min


# ── MailService ─────────────────────────────────────────────────────


@service(scope="app", name="MailService")
class MailService:
    """
    Central mail service — owns the pipeline from message to delivery.

    Lifecycle:
        ``AquiliaServer.__init__``  → MailService created, registered in DI
        ``AquiliaServer.startup``   → :meth:`on_startup` (build providers)
        ``AquiliaServer.shutdown``  → :meth:`on_shutdown` (disconnect)

    Responsibilities:
        - Build envelopes from :class:`~aquilia.mail.message.EmailMessage`
        - Resolve provider credentials, including ``*_env`` indirection
        - Throttle each provider to its ``rate_limit_per_min``
        - Fail over across providers, then schedule retries with backoff
        - Emit inspector trace spans for outbound mail

    Async-safety:
        A single app-scoped instance is shared across concurrent requests.
        Provider objects manage their own connection pools; the rate-limit
        buckets are per provider and lock-free (see :class:`_TokenBucket`).

    Attributes:
        config: Effective :class:`~aquilia.mail.config.MailConfig`.
        logger: Subsystem logger (``aquilia.mail``).

    Examples::

        svc = MailService(MailConfig(console_backend=True))
        await svc.on_startup()
        await svc.send_message(EmailMessage(subject="Hi", body="x", to="a@b.c"))
        await svc.on_shutdown()
    """

    #: Task queue used for background delivery and retries.
    retry_queue: str = "mail"

    def __init__(
        self,
        config: MailConfig | None = None,
        *,
        store: Any = None,
        suppression: Any = None,
    ):
        self.config = config or MailConfig()
        self._providers: dict[str, Any] = {}  # name → IMailProvider
        self._rate_limiters: dict[str, _TokenBucket] = {}  # provider name → bucket
        self._task_manager: Any = None  # set via bind_task_manager()
        self._started = False
        self.logger = logger

        from .store import MemoryEnvelopeStore
        from .suppression import MemorySuppressionList

        #: Durable record of accepted mail. Defaults to in-process; pair a
        #: SQLEnvelopeStore with a persistent task backend for real durability.
        self.store = store if store is not None else MemoryEnvelopeStore()
        #: Recipients that must not be emailed (bounces, complaints, opt-outs).
        self.suppression = suppression if suppression is not None else MemorySuppressionList()
        #: True when the caller supplied stores explicitly, so
        #: ``queue.persistent`` must not replace them.
        self._stores_explicit = store is not None or suppression is not None

    # ── Lifecycle ───────────────────────────────────────────────────

    async def on_startup(self) -> None:
        """
        Build and connect every enabled provider, then arm its rate limiter.

        A provider that fails to construct or connect is logged and skipped
        rather than aborting startup — a degraded mail path must not take the
        whole application down, and remaining providers still serve traffic.

        Side effects:
            Populates the provider map and the per-provider token buckets,
            and configures the ATS template search path from
            ``MailConfig.templates.dirs``.
        """
        if self._started:
            return

        self._configure_templates()

        # Prepare durable stores before any provider, so a queued send always
        # has somewhere to record the envelope.
        await self._prepare_stores()

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
                self._rate_limiters[pc.name] = _TokenBucket(getattr(pc, "rate_limit_per_min", 0) or 0)
            except Exception as e:
                self.logger.error(f"  Provider '{pc.name}' failed: {e}")

        # Console fallback for development
        if self.config.console_backend and "console" not in self._providers:
            from .providers.console import ConsoleProvider

            cp = ConsoleProvider()
            await cp.initialize()
            self._providers["console"] = cp

        self._started = True

    def _upgrade_stores_if_persistent(self) -> None:
        """
        Swap the in-memory stores for database-backed ones when configured.

        Driven by ``MailConfig.queue.persistent`` so a workspace gets durable
        envelopes and suppression records from configuration alone, without
        every construction path (DI provider, factory, server) having to build
        the stores itself.

        Explicitly-supplied stores always win: a caller that passed its own
        store meant it.
        """
        if self._stores_explicit or not getattr(self.config.queue, "persistent", False):
            return

        from .store import SQLEnvelopeStore
        from .suppression import SQLSuppressionList

        self.store = SQLEnvelopeStore()
        self.suppression = SQLSuppressionList()
        self._stores_explicit = True

    async def _prepare_stores(self) -> None:
        """
        Select and initialize the envelope store and suppression list.

        A configured database that turns out to be unavailable falls back to
        the in-memory stores with a loud warning rather than aborting startup:
        mail degrades to non-durable instead of taking the application down,
        and the warning names the durability that was lost.
        """
        self._upgrade_stores_if_persistent()

        try:
            await self.store.initialize()
            if self.suppression is not None:
                await self.suppression.initialize()
            return
        except Exception as e:
            self.logger.error(
                "Persistent mail stores unavailable (%s); falling back to in-memory. "
                "Queued mail and suppression records will NOT survive a restart.",
                e,
            )

        from .store import MemoryEnvelopeStore
        from .suppression import MemorySuppressionList

        self.store = MemoryEnvelopeStore()
        self.suppression = MemorySuppressionList()
        await self.store.initialize()
        await self.suppression.initialize()

    def _configure_templates(self) -> None:
        """Point the ATS renderer at the configured template directories."""
        dirs = getattr(self.config.templates, "dirs", None)
        if dirs:
            from .template import configure

            configure(list(dirs))

    async def on_shutdown(self) -> None:
        """
        Disconnect every provider and reset service state.

        Shutdown errors are logged, never raised: one misbehaving provider
        must not prevent the others from releasing their connections.
        """
        if not self._started:
            return
        for name, provider in self._providers.items():
            try:
                await provider.shutdown()
            except Exception as e:
                self.logger.warning(f"  Provider '{name}' shutdown error: {e}")
        self._providers.clear()
        self._rate_limiters.clear()
        self._started = False

    # ── Auth propagation ────────────────────────────────────────────

    def _apply_global_auth(self, pc: Any) -> None:
        """
        Apply top-level ``MailConfig.auth`` to a provider config that has none.

        Global auth is a default: a provider with its own flat credentials or
        its own nested ``auth`` block is left untouched.  ``*_env`` fields are
        resolved through :meth:`_resolve_credential`, so a global
        ``password_env`` reaches the provider as an actual password rather
        than as an unread variable name.

        Args:
            pc: Provider configuration, mutated in place.

        Side effects:
            Sets ``pc.username`` / ``pc.password`` when the global auth
            supplies them and the provider does not.
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
            pwd = self._resolve_credential(
                {
                    "password": getattr(auth, "password", None),
                    "password_env": getattr(auth, "password_env", None),
                },
                "password",
            )
            if uname:
                pc.username = uname
            if pwd:
                pc.password = pwd

    # ── Credential resolution ───────────────────────────────────────

    @staticmethod
    def _resolve_credential(
        auth: dict[str, Any],
        key: str,
        *,
        env_key: str | None = None,
    ) -> str | None:
        """
        Resolve one credential from an auth block, honouring ``*_env`` indirection.

        ``MailAuth`` models every secret twice: a literal field (``password``)
        and an environment-variable name (``password_env``).  The documented
        12-factor pattern is the latter, so it must actually be read — a
        deployment that only sets ``password_env`` would otherwise construct
        an unauthenticated provider and fail (or silently relay) at send time.

        Precedence: literal value wins, then the named environment variable.

        Args:
            auth: Serialized ``MailAuth`` dict (see ``MailAuth.to_dict``).
            key: Literal field name, e.g. ``"password"``.
            env_key: Environment-name field; defaults to ``f"{key}_env"``.

        Returns:
            The resolved secret, or ``None`` when neither source yields one.

        Security:
            The resolved value is never logged; only the *name* of a missing
            environment variable is reported.

        Examples::

            MailService._resolve_credential({"password_env": "SMTP_PASS"}, "password")
            # → os.environ["SMTP_PASS"], or None if unset
        """
        literal = auth.get(key)
        if literal:
            return str(literal)

        env_name = auth.get(env_key or f"{key}_env")
        if not env_name:
            return None

        value = os.environ.get(str(env_name))
        if not value:
            logger.warning(
                "Mail credential %r references environment variable %r, which is unset or empty.",
                key,
                env_name,
            )
            return None
        return value

    # ── Provider factory ────────────────────────────────────────────

    def _create_provider(self, pc: Any) -> Any:
        """
        Instantiate a provider from a ``ProviderConfig``.

        Uses hard-coded mappings for built-in types, then falls back to the
        :class:`~aquilia.mail.di_providers.MailProviderRegistry` (discovery
        system) for custom types.

        Credential precedence: explicit flat fields (``pc.username`` etc.)
        win over a nested ``pc.auth`` block, which wins over ``pc.config``.
        Within the ``auth`` block, a literal value wins over its ``*_env``
        counterpart, which is resolved from the process environment by
        :meth:`_resolve_credential`.

        Args:
            pc: Validated provider configuration.

        Returns:
            An initialised-but-not-yet-connected provider instance.

        Raises:
            MailConfigFault: If ``pc.type`` matches no built-in provider and
                no discovered provider class.
        """
        auth: dict[str, Any] = getattr(pc, "auth", None) or {}
        config = dict(pc.config or {})
        rate_limit = getattr(pc, "rate_limit_per_min", 600)

        if pc.type == "smtp":
            from .providers.smtp import SMTPProvider

            config.pop("host", None)
            config.pop("port", None)
            config.pop("username", None)
            config.pop("password", None)
            return SMTPProvider(
                name=pc.name,
                host=pc.host or pc.config.get("host", "localhost"),
                port=pc.port or pc.config.get("port", 587),
                username=pc.username or auth.get("username") or pc.config.get("username"),
                password=(pc.password or self._resolve_credential(auth, "password") or pc.config.get("password")),
                use_tls=pc.use_tls,
                use_ssl=pc.use_ssl,
                timeout=pc.timeout,
                oauth2_token=self._resolve_oauth2_token(auth),
                priority=pc.priority,
                rate_limit_per_min=rate_limit,
                security=self.config.security,
                **config,
            )
        elif pc.type == "ses":
            from .providers.ses import SESProvider

            config.pop("region", None)
            config.pop("aws_access_key_id", None)
            config.pop("aws_secret_access_key", None)
            config.pop("aws_session_token", None)
            return SESProvider(
                name=pc.name,
                region=auth.get("aws_region") or pc.config.get("region", "us-east-1"),
                aws_access_key_id=(
                    self._resolve_credential(auth, "aws_access_key_id") or pc.config.get("aws_access_key_id")
                ),
                aws_secret_access_key=(
                    self._resolve_credential(auth, "aws_secret_access_key") or pc.config.get("aws_secret_access_key")
                ),
                aws_session_token=auth.get("aws_session_token") or pc.config.get("aws_session_token"),
                priority=pc.priority,
                rate_limit_per_min=rate_limit,
                security=self.config.security,
                **config,
            )
        elif pc.type == "sendgrid":
            from .providers.sendgrid import SendGridProvider

            config.pop("api_key", None)
            return SendGridProvider(
                name=pc.name,
                api_key=self._resolve_credential(auth, "api_key") or pc.config.get("api_key", ""),
                priority=pc.priority,
                rate_limit_per_min=rate_limit,
                **config,
            )
        elif pc.type == "console":
            from .providers.console import ConsoleProvider

            return ConsoleProvider(name=pc.name)
        elif pc.type == "file":
            from .providers.file import FileProvider

            config.pop("output_dir", None)
            return FileProvider(
                name=pc.name,
                output_dir=pc.config.get("output_dir", "/tmp/aquilia_mail"),
                **config,
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

    def _resolve_oauth2_token(self, auth: dict[str, Any]) -> str | None:
        """
        Extract an OAuth2 access token for SMTP XOAUTH2, if one is configured.

        Only the ``oauth2`` auth method yields a token.  Aquilia does not run
        the client-credentials/refresh exchange itself: supply a current
        ``access_token`` (directly or via ``access_token_env``) from whatever
        already owns the refresh cycle in your deployment.

        Args:
            auth: Serialized ``MailAuth`` dict.

        Returns:
            The bearer token for XOAUTH2, or ``None`` for non-OAuth2 auth.
        """
        if auth.get("method") != "oauth2":
            return None
        return self._resolve_credential(auth, "access_token")

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
        Build an envelope from a message and dispatch it.

        Main entry point behind :meth:`EmailMessage.send` and
        :meth:`EmailMessage.asend`.

        Args:
            message: An :class:`~aquilia.mail.message.EmailMessage` (or any
                object exposing ``build_envelope(default_from=...)``).

        Returns:
            The envelope ID.  In preview mode the envelope is marked ``SENT``
            without contacting any provider, so the ID identifies a message
            that was deliberately not delivered.

        Raises:
            MailValidationFault: If the message has no recipients.
            MailConfigFault: If no provider is configured.
            MailSendFault: On permanent failure, or on transient failure that
                could not be scheduled for retry.

        Side effects:
            Emits an inspector trace span on the ``MAIL`` lane when a request
            trace is active.

        Examples::

            envelope_id = await svc.send_message(
                EmailMessage(subject="Hi", body="there", to="user@example.com")
            )
        """
        t0 = None
        trace = None
        try:
            from aquilia.inspector.trace import current_trace

            trace = current_trace()
            if trace is not None:
                t0 = time.monotonic()
        except ImportError:
            pass

        envelope, blobs = message.build_envelope(
            default_from=self.config.default_from,
        )

        # Attachment bytes travel with the envelope so providers can build
        # real MIME parts; without this the payloads resolve to b"".
        for digest, content in blobs.items():
            envelope.metadata[f"blob:{digest}"] = content

        # Apply subject prefix
        if self.config.subject_prefix:
            envelope.subject = self.config.subject_prefix + envelope.subject

        # Drop recipients that already bounced or complained, before any
        # provider is contacted. Sending to them costs reputation and, on SES,
        # risks account suspension.
        if not await self._apply_suppression(envelope):
            await self.store.save(envelope)
            return envelope.id

        # Collapse a duplicate submission (a retried HTTP request, a
        # double-clicked button) onto the original envelope.
        duplicate = await self._find_duplicate(envelope)
        if duplicate is not None:
            self.logger.info(
                "Reusing envelope %s for duplicate submission (digest match)",
                duplicate.id,
            )
            return duplicate.id

        # In preview mode, just log -- don't actually send
        if self.config.preview_mode:
            envelope.status = EnvelopeStatus.SENT
            await self.store.save(envelope)
            res_id = envelope.id
        elif self._should_queue():
            res_id = await self._enqueue_delivery(envelope)
        else:
            await self.store.save(envelope)
            await self._dispatch_direct(envelope)
            res_id = envelope.id

        if trace is not None and t0 is not None:
            try:
                from aquilia.inspector.trace import Lane, SpanStatus

                now_offset = (time.monotonic() - trace.started_monotonic) * 1000.0
                duration_ms = (time.monotonic() - t0) * 1000.0

                trace.add_span(
                    lane=Lane.MAIL,
                    label=f"Outbound Email: {envelope.subject}",
                    start_offset_ms=max(0.0, now_offset - duration_ms),
                    duration_ms=duration_ms,
                    status=SpanStatus.OK,
                    detail={
                        "envelope_id": envelope.id,
                        "subject": envelope.subject,
                        "from": envelope.from_email,
                        "to": list(envelope.to),
                        "cc": list(envelope.cc),
                        "status": str(envelope.status.value)
                        if hasattr(envelope.status, "value")
                        else str(envelope.status),
                    },
                )
            except Exception:
                pass

        return res_id

    async def send_envelope(self, envelope: MailEnvelope) -> None:
        """
        Dispatch an already-built envelope.

        Used by the delivery task, which loads an envelope from the store by
        ID rather than receiving a live object.

        Args:
            envelope: Envelope to deliver, mutated in place with the outcome.

        Raises:
            MailSendFault: On permanent failure, or on transient failure with
                no retry budget left.
        """
        await self._dispatch_direct(envelope)

    # ── Queueing ────────────────────────────────────────────────────

    def _should_queue(self) -> bool:
        """
        Whether delivery should go through the task queue.

        Requires both a running task manager and ``MailConfig.queue.enabled``.
        Without a manager the send must happen inline, or the envelope would
        be recorded as queued and never delivered.
        """
        if not getattr(self.config.queue, "enabled", False):
            return False
        return self._get_task_manager() is not None

    async def _enqueue_delivery(self, envelope: MailEnvelope, *, delay: float | None = None) -> str:
        """
        Persist the envelope and schedule its delivery as a background task.

        Only the envelope **ID** is passed to the task.  A live
        :class:`MailEnvelope` could not survive a persistent or distributed
        task backend, which serialises jobs as JSON; the worker re-loads the
        envelope from the store instead.  This is what lets mail delivery run
        on another process or machine without any API change.

        Args:
            envelope: Envelope to deliver.
            delay: Seconds to wait before the first attempt.

        Returns:
            The envelope ID, returned to the caller immediately — delivery
            completes asynchronously.
        """
        envelope.status = EnvelopeStatus.QUEUED
        if delay:
            envelope.next_attempt_at = _utcnow() + timedelta(seconds=delay)
        await self.store.save(envelope)

        manager = self._get_task_manager()
        await manager.enqueue(
            _deliver_envelope_task,
            envelope.id,
            queue=self.retry_queue,
            delay=delay,
            max_retries=0,  # Mail owns its own retry policy and backoff.
            metadata={"envelope_id": envelope.id},
        )
        return envelope.id

    async def _apply_suppression(self, envelope: MailEnvelope) -> bool:
        """
        Remove suppressed recipients from an envelope.

        Args:
            envelope: Envelope being prepared, mutated in place.

        Returns:
            ``True`` if any deliverable recipient remains.  ``False`` marks
            the envelope ``CANCELLED`` — every recipient is suppressed, so
            there is nothing legitimate left to send.

        Notes:
            Partial suppression is deliberate: one bounced address in a
            three-recipient message must not block the other two.
        """
        if self.suppression is None:
            return True

        cancelled_all = True
        for attr in ("to", "cc", "bcc"):
            addresses = getattr(envelope, attr)
            if not addresses:
                continue
            deliverable, suppressed = await self.suppression.filter_recipients(addresses)
            if suppressed:
                self.logger.info(
                    "Skipping %d suppressed recipient(s) on envelope %s",
                    len(suppressed),
                    envelope.id,
                )
                envelope.metadata.setdefault("suppressed_recipients", []).extend(suppressed)
            setattr(envelope, attr, deliverable)
            if deliverable:
                cancelled_all = False

        if cancelled_all:
            envelope.status = EnvelopeStatus.CANCELLED
            envelope.error_message = "All recipients are suppressed"
            self.logger.warning("Envelope %s cancelled: every recipient is suppressed", envelope.id)
            return False
        return True

    async def _find_duplicate(self, envelope: MailEnvelope) -> MailEnvelope | None:
        """
        Find a recent envelope representing the same send.

        Matches the caller's ``idempotency_key`` first, then the content
        digest within ``MailConfig.queue.dedupe_window_seconds``.  Guards
        against the classic double-send: a retried request or a
        double-clicked button producing two identical emails.

        Returns:
            The existing envelope, or ``None`` when this is new work.
        """
        window = float(getattr(self.config.queue, "dedupe_window_seconds", 0) or 0)

        if envelope.idempotency_key:
            existing = await self.store.find_by_idempotency_key(envelope.idempotency_key)
            if existing is not None and existing.id != envelope.id:
                return existing

        if window > 0 and envelope.digest:
            existing = await self.store.find_by_digest(envelope.digest, within_seconds=window)
            if existing is not None and existing.id != envelope.id:
                return existing

        return None

    def _rate_limiter_for(self, provider: Any) -> _TokenBucket:
        """
        Return (creating if needed) the token bucket guarding ``provider``.

        Providers created outside :meth:`on_startup` — the console fallback,
        or anything injected by a test — get a bucket lazily from their own
        ``rate_limit_per_min`` attribute, defaulting to unthrottled.
        """
        bucket = self._rate_limiters.get(provider.name)
        if bucket is None:
            bucket = _TokenBucket(getattr(provider, "rate_limit_per_min", 0) or 0)
            self._rate_limiters[provider.name] = bucket
        return bucket

    def _scrub(self, text: str) -> str:
        """
        Redact recipient addresses from text bound for logs or faults.

        Controlled by ``MailConfig.security.pii_redaction_enabled``.  Applied
        only to observability output — never to the delivered message, which
        obviously needs real addresses.
        """
        return redact_pii(
            text,
            enabled=bool(getattr(self.config.security, "pii_redaction_enabled", False)),
        )

    async def _dispatch_direct(self, envelope: MailEnvelope) -> None:
        """
        Deliver an envelope, failing over across providers then retrying.

        Providers are tried in ascending ``priority``.  Each is gated by its
        token bucket: an over-rate provider is skipped rather than being
        handed a send it would reject, which preserves the failover chain
        instead of burning the attempt.

        Outcomes:
            - **Success** — envelope becomes ``SENT`` and carries the
              provider's message ID.
            - **Permanent failure** — envelope becomes ``FAILED`` and
              :class:`~aquilia.mail.faults.MailSendFault` is raised
              immediately; trying another provider would only repeat a
              rejection the recipient's server already made final.
            - **Transient / rate-limited** — the next provider is tried.  If
              all are exhausted, a retry is scheduled while
              ``envelope.attempts < envelope.max_attempts``; otherwise the
              envelope becomes ``FAILED`` and the fault propagates.

        Args:
            envelope: Envelope to deliver, mutated in place.

        Raises:
            MailConfigFault: If no providers are configured.
            MailSendFault: On permanent failure, or on transient failure with
                no retry budget or no task manager to carry the retry.
        """
        from .faults import MailSendFault

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

        envelope.attempts += 1
        envelope.last_attempt_at = _utcnow()

        last_error: Exception | None = None
        retry_after: float | None = None

        for provider in sorted_providers:
            bucket = self._rate_limiter_for(provider)
            if not bucket.acquire():
                wait = bucket.retry_after()
                retry_after = wait if retry_after is None else min(retry_after, wait)
                self.logger.warning(
                    "Provider %s over its rate limit (%s/min); skipping for %.1fs",
                    provider.name,
                    bucket.rate_per_min,
                    wait,
                )
                last_error = last_error or MailRateLimitFault(
                    f"Provider {provider.name} exceeded {bucket.rate_per_min}/min",
                    scope=provider.name,
                    retry_after=wait,
                )
                continue

            try:
                envelope.status = EnvelopeStatus.SENDING
                envelope.provider_name = provider.name
                result = await provider.send(envelope)

                if result.is_success:
                    envelope.status = EnvelopeStatus.SENT
                    envelope.provider_message_id = result.provider_message_id
                    envelope.error_message = None
                    envelope.next_attempt_at = None
                    await self.store.save(envelope)
                    return
                elif result.should_retry:
                    self.logger.warning(
                        "Transient failure from %s: %s",
                        provider.name,
                        self._scrub(str(result.error_message)),
                    )
                    last_error = MailSendFault(
                        f"Transient send failure via {provider.name}: {result.error_message}",
                        provider=provider.name,
                        transient=True,
                        envelope_id=envelope.id,
                    )
                    if result.retry_after is not None:
                        retry_after = (
                            result.retry_after if retry_after is None else min(retry_after, result.retry_after)
                        )
                    continue
                else:
                    # Permanent failure -- the recipient server said no. Another
                    # provider would get the same answer, so stop here.
                    envelope.status = EnvelopeStatus.FAILED
                    envelope.error_message = result.error_message
                    await self.store.save(envelope)
                    raise MailSendFault(
                        f"Permanent send failure via {provider.name}: {result.error_message}",
                        provider=provider.name,
                        transient=False,
                        envelope_id=envelope.id,
                    )
            except MailSendFault as e:
                if not e.recoverable:
                    raise
                last_error = e
                continue
            except Exception as e:
                last_error = e
                self.logger.warning("Provider %s error: %s", provider.name, self._scrub(str(e)))
                continue

        # Every provider failed transiently -- retry if budget remains.
        if await self._schedule_retry(envelope, retry_after):
            return

        envelope.status = EnvelopeStatus.FAILED
        envelope.error_message = str(last_error)
        await self.store.save(envelope)

        raise MailSendFault(
            f"All providers failed for envelope {envelope.id} "
            f"(attempt {envelope.attempts}/{envelope.max_attempts}): {self._scrub(str(last_error))}",
            provider="all",
            transient=True,
            envelope_id=envelope.id,
        )

    # ── Retry ───────────────────────────────────────────────────────

    def _retry_delay(self, envelope: MailEnvelope, retry_after: float | None) -> float:
        """
        Compute the delay before the next delivery attempt.

        A provider-supplied ``retry_after`` (SMTP 4xx guidance, an ESP's
        ``Retry-After`` header) always wins — it reflects the remote server's
        own recovery estimate.  Otherwise exponential backoff is derived from
        ``MailConfig.retry``: ``base_delay * 2**(attempts-1)``, clamped to
        ``max_delay``, with optional full jitter to avoid retry stampedes
        when a provider recovers.
        """
        if retry_after is not None:
            return max(0.0, float(retry_after))

        retry_cfg = self.config.retry
        base = float(getattr(retry_cfg, "base_delay", 1.0) or 1.0)
        max_delay = float(getattr(retry_cfg, "max_delay", 3600.0) or 3600.0)
        delay = min(base * (2 ** max(0, envelope.attempts - 1)), max_delay)

        if getattr(retry_cfg, "jitter", True):
            delay *= 0.5 + random.random() / 2.0
        return delay

    async def _schedule_retry(self, envelope: MailEnvelope, retry_after: float | None) -> bool:
        """
        Queue a delayed re-delivery of ``envelope`` through the task system.

        Mail deliberately does not run its own scheduler: :mod:`aquilia.tasks`
        already implements delayed enqueue, backoff and dead-lettering, and a
        second implementation would drift from it.  When no ``TaskManager`` is
        available (mail enabled, tasks disabled), no retry is possible and the
        caller surfaces the failure instead.

        Args:
            envelope: Envelope that failed transiently.
            retry_after: Provider-supplied delay hint, if any.

        Returns:
            ``True`` if a retry was scheduled — the envelope stays ``QUEUED``
            with ``next_attempt_at`` set.  ``False`` if the retry budget is
            exhausted or no task manager is available.
        """
        if envelope.attempts >= envelope.max_attempts:
            return False

        manager = self._get_task_manager()
        if manager is None:
            self.logger.warning(
                "Envelope %s failed transiently but no TaskManager is available to retry it. "
                "Enable Integration.tasks() to get automatic mail retries.",
                envelope.id,
            )
            return False

        delay = self._retry_delay(envelope, retry_after)
        envelope.status = EnvelopeStatus.QUEUED
        envelope.next_attempt_at = _utcnow() + timedelta(seconds=delay)
        # Persist before scheduling: the worker loads the envelope by ID, so
        # an unsaved envelope would make the retry task unresolvable.
        await self.store.save(envelope)

        await manager.enqueue(
            _deliver_envelope_task,
            envelope.id,
            queue=self.retry_queue,
            delay=delay,
            max_retries=0,  # Mail owns retry counting via envelope.attempts.
            metadata={"envelope_id": envelope.id},
        )
        self.logger.info(
            "Envelope %s scheduled for retry %d/%d in %.1fs",
            envelope.id,
            envelope.attempts + 1,
            envelope.max_attempts,
            delay,
        )
        return True

    def _get_task_manager(self) -> Any:
        """
        Return the running :class:`~aquilia.tasks.engine.TaskManager`, if any.

        The manager is injected by ``AquiliaServer._setup_tasks`` via
        :meth:`bind_task_manager`.  A manager that exists but has not started
        is treated as absent: enqueueing into a stopped manager would silently
        park the retry forever.

        Returns:
            The active task manager, or ``None`` when tasks are disabled or
            not yet running.
        """
        manager = self._task_manager
        if manager is None:
            return None
        return manager if getattr(manager, "is_running", False) else None

    def bind_task_manager(self, manager: Any) -> None:
        """
        Attach the application's task manager for retry delivery.

        Called during server setup.  Passing ``None`` detaches, which disables
        automatic retries and makes transient failures surface to the caller.

        Args:
            manager: The :class:`~aquilia.tasks.engine.TaskManager` instance.

        Examples::

            svc.bind_task_manager(server._task_manager)
        """
        self._task_manager = manager

    # ── Introspection ───────────────────────────────────────────────

    def get_provider_names(self) -> list[str]:
        """Return the names of every initialised provider."""
        return list(self._providers.keys())

    def is_healthy(self) -> bool:
        """True when the service has started and holds at least one provider."""
        return self._started and len(self._providers) > 0

    async def get_stats(self) -> dict[str, Any]:
        """
        Delivery statistics for the admin dashboard.

        Includes whether queued mail is actually durable, so an operator can
        see at a glance that "queued" on an in-memory store does not survive a
        restart.

        Returns:
            Envelope counts by status, suppression size, and durability flags.
        """
        store_stats = await self.store.stats()
        suppressed = await self.suppression.list_all(limit=1_000_000) if self.suppression else []
        manager = self._get_task_manager()
        return {
            "envelopes": store_stats,
            "suppressed_count": len(suppressed),
            "providers": self.get_provider_names(),
            "queue_enabled": self._should_queue(),
            "durable_queue": bool(
                self.store.is_persistent and manager is not None and getattr(manager, "is_persistent", False)
            ),
            "store_persistent": self.store.is_persistent,
            "suppression_persistent": bool(self.suppression and self.suppression.is_persistent),
        }


@task(name="aquilia.mail.deliver", queue=MailService.retry_queue, max_retries=0)
async def _deliver_envelope_task(envelope_id: str) -> None:
    """
    Task entry point that delivers a stored envelope.

    Scheduled by :meth:`MailService._enqueue_delivery` and
    :meth:`MailService._schedule_retry`.

    Takes an envelope **ID**, not an envelope: a job must be JSON-serialisable
    to reach a persistent or distributed task backend, and a live
    :class:`MailEnvelope` is not.  The worker — which may be in another
    process entirely — loads the envelope from the shared store.

    Registered under a stable name rather than enqueued as a bare callable:
    a worker in another process resolves the job through the ``@task``
    registry, and a module-path reference would not survive a rename.

    Args:
        envelope_id: ID of the envelope to deliver.

    Raises:
        MailSendFault: If the attempt fails and no retry budget remains, so
            the task system dead-letters the job.

    Notes:
        A missing envelope is logged and treated as success rather than
        retried forever: it means the envelope was cleaned up or cancelled,
        and no amount of retrying will bring it back.
    """
    service = _get_mail_service()
    envelope = await service.store.get(envelope_id)
    if envelope is None:
        logger.warning("Delivery task for unknown envelope %s; it was cancelled or cleaned up.", envelope_id)
        return
    await service.send_envelope(envelope)
