"""
AquilaMail Messages -- Developer-facing message classes.

API:
    EmailMessage          -- plain text (optionally with HTML)
    EmailMultiAlternatives -- plain text + HTML + arbitrary MIME alternatives
    TemplateMessage       -- rendered from an ATS template

All classes support both sync (.send()) and async (.asend()) delivery.
"""

from __future__ import annotations

import asyncio
import hashlib
import re
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from .envelope import Attachment, MailEnvelope, Priority
from .faults import MailValidationFault

# Basic email regex for fast validation (not RFC-complete but practical)
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$")


def _validate_email(addr: str, field_name: str = "email") -> str:
    """Validate and normalise a single email address."""
    addr = addr.strip()
    if not addr:
        raise MailValidationFault(f"Empty {field_name} address", field=field_name)
    # Handle "Display Name <addr>" format
    if "<" in addr and addr.endswith(">"):
        display, raw = addr.rsplit("<", 1)
        raw = raw.rstrip(">").strip()
    else:
        raw = addr
    if not _EMAIL_RE.match(raw):
        raise MailValidationFault(f"Invalid {field_name} address: {addr!r}", field=field_name)
    return addr


def _validate_list(addrs: Sequence[str] | str | None, field_name: str) -> list[str]:
    """Validate recipient addresses, accepting either a list or a single string."""
    if not addrs:
        return []
    if isinstance(addrs, str):
        addrs = [addrs]
    return [_validate_email(a, field_name) for a in addrs]


class EmailMessage:
    """
    A single email message -- the primary API for sending mail.

    Integrated with Aquilia's envelope pipeline, DI, and fault system.

    Usage:
        msg = EmailMessage(
            subject="Hello",
            body="World",
            to=["user@example.com"],
        )
        msg.send()            # sync
        await msg.asend()     # async

        # With attachments
        msg.attach("report.pdf", pdf_bytes, "application/pdf")
        msg.attach_file("/tmp/invoice.pdf")
    """

    def __init__(
        self,
        subject: str = "",
        body: str = "",
        from_email: str | None = None,
        to: Sequence[str] | str | None = None,
        cc: Sequence[str] | str | None = None,
        bcc: Sequence[str] | str | None = None,
        reply_to: str | None = None,
        headers: dict[str, str] | None = None,
        attachments: list[tuple[str, bytes, str]] | None = None,
        priority: int = Priority.NORMAL.value,
        idempotency_key: str | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.subject = subject
        self.body = body
        self.from_email = from_email  # None → uses MailConfig.default_from
        self.to = _validate_list(to, "to")
        self.cc = _validate_list(cc, "cc")
        self.bcc = _validate_list(bcc, "bcc")
        self.reply_to = reply_to
        self.extra_headers = headers or {}
        self.priority = priority
        self.idempotency_key = idempotency_key
        self.tenant_id = tenant_id
        self.metadata = metadata or {}

        # Attachment buffer: list of (filename, content_bytes, content_type)
        self._attachments: list[tuple[str, bytes, str]] = list(attachments or [])
        self._alternatives: list[tuple[str, str]] = []  # (content, mimetype)

    # ── Attachment API ──────────────────────────────────────────────

    def attach(
        self,
        filename: str,
        content: bytes,
        content_type: str = "application/octet-stream",
    ) -> EmailMessage:
        """Attach raw bytes."""
        self._attachments.append((filename, content, content_type))
        return self

    def attach_file(
        self,
        path: str | Path,
        content_type: str | None = None,
    ) -> EmailMessage:
        """Attach a file from disk."""
        p = Path(path)
        if not p.exists():
            raise FileNotFoundError(f"Attachment not found: {p}")
        if content_type is None:
            import mimetypes

            content_type, _ = mimetypes.guess_type(str(p))
            content_type = content_type or "application/octet-stream"
        self._attachments.append((p.name, p.read_bytes(), content_type))
        return self

    # ── Envelope builder ────────────────────────────────────────────

    def _build_attachment_records(self) -> tuple[list[Attachment], dict[str, bytes]]:
        """
        Build Attachment records and a digest→bytes map for blob storage.

        Returns:
            (attachment_records, blobs_to_store)
        """
        records: list[Attachment] = []
        blobs: dict[str, bytes] = {}
        for filename, content, ct in self._attachments:
            digest = hashlib.sha256(content).hexdigest()
            records.append(
                Attachment(
                    filename=filename,
                    content_type=ct,
                    digest=digest,
                    size=len(content),
                )
            )
            blobs[digest] = content
        return records, blobs

    def build_envelope(
        self,
        default_from: str = "noreply@localhost",
    ) -> tuple[MailEnvelope, dict[str, bytes]]:
        """
        Build a MailEnvelope + blob map ready for storage and dispatch.

        Args:
            default_from: Fallback from address if self.from_email is None.

        Returns:
            (envelope, attachment_blobs)
        """
        if not self.to and not self.cc and not self.bcc:
            raise MailValidationFault(
                "At least one recipient (to, cc, or bcc) is required",
                field="to",
            )

        att_records, blobs = self._build_attachment_records()

        body_html: str | None = None
        if self._alternatives:
            for content, mimetype in self._alternatives:
                if mimetype == "text/html":
                    body_html = content
                    break

        envelope = MailEnvelope(
            from_email=self.from_email or default_from,
            to=list(self.to),
            cc=list(self.cc),
            bcc=list(self.bcc),
            reply_to=self.reply_to,
            subject=self.subject,
            body_text=self.body,
            body_html=body_html,
            headers=dict(self.extra_headers),
            attachments=att_records,
            priority=self.priority,
            idempotency_key=self.idempotency_key,
            tenant_id=self.tenant_id,
            metadata=self.metadata,
        )
        envelope.compute_digest()
        return envelope, blobs

    # ── Send API ────────────────────────────────────────────────────

    def send(self, fail_silently: bool = False) -> str | None:
        """
        Send synchronously, from outside an event loop.

        Aquilia's request pipeline is async: inside a controller, middleware,
        task, or any other coroutine, use :meth:`asend` instead.  A synchronous
        send cannot drive the loop that is already running, so calling this
        from async context raises :class:`~aquilia.mail.faults.MailConfigFault`
        with that instruction rather than the opaque
        ``RuntimeError: This event loop is already running``.

        This method is for genuinely synchronous entry points — management
        commands, scripts, and sync-only third-party callbacks.

        Args:
            fail_silently: Swallow send errors and return ``None``.  Does not
                suppress the async-context guard, which is a programming
                error rather than a delivery failure.

        Returns:
            The envelope ID on success, or ``None`` when ``fail_silently``
            absorbed an error.

        Raises:
            MailConfigFault: If called while an event loop is running, or if
                no :class:`~aquilia.mail.service.MailService` is installed.
            MailSendFault: On delivery failure when ``fail_silently`` is off.

        Examples::

            # In a script / management command
            EmailMessage(subject="Nightly", body="ok", to="ops@x.com").send()

            # In an Aquilia controller — use asend()
            await EmailMessage(subject="Hi", body="ok", to=user.email).asend()
        """
        from .faults import MailConfigFault
        from .service import _get_mail_service

        try:
            asyncio.get_running_loop()
        except RuntimeError:
            pass  # No running loop — a synchronous send is valid here.
        else:
            raise MailConfigFault(
                "EmailMessage.send() cannot run inside a running event loop. "
                "Use 'await message.asend()' (or 'await asend_mail(...)') from "
                "async code such as controllers, middleware, and tasks.",
                config_key="mail.send",
            )

        svc = _get_mail_service()
        try:
            return asyncio.run(svc.send_message(self))
        except Exception:
            if fail_silently:
                return None
            raise

    async def asend(self, fail_silently: bool = False) -> str | None:
        """
        Send asynchronously — the primary API inside Aquilia.

        Args:
            fail_silently: Swallow send errors and return ``None``.

        Returns:
            The envelope ID on success, or ``None`` when ``fail_silently``
            absorbed an error.

        Raises:
            MailConfigFault: If no MailService is installed or no provider
                is configured.
            MailValidationFault: If the message has no recipients.
            MailSendFault: On delivery failure when ``fail_silently`` is off.

        Examples::

            msg = EmailMessage(subject="Welcome", body="Hi", to=user.email)
            envelope_id = await msg.asend()
        """
        from .service import _get_mail_service

        svc = _get_mail_service()
        try:
            return await svc.send_message(self)
        except Exception:
            if fail_silently:
                return None
            raise

    def __repr__(self) -> str:
        return f"EmailMessage(subject={self.subject!r}, to={self.to!r})"


class EmailMultiAlternatives(EmailMessage):
    """
    Email with multiple content alternatives (e.g., plain text + HTML).

    Usage:
        msg = EmailMultiAlternatives(
            subject="Newsletter",
            body="Plain text fallback",
            to=["subscriber@example.com"],
        )
        msg.attach_alternative("<h1>HTML version</h1>", "text/html")
        await msg.asend()
    """

    def attach_alternative(self, content: str, mimetype: str = "text/html") -> EmailMultiAlternatives:
        """Add an alternative content representation."""
        self._alternatives.append((content, mimetype))
        return self


class TemplateMessage(EmailMessage):
    """
    Email rendered from an Aquilia Template Syntax (ATS) template.

    The template is rendered at build_envelope() time.  The rendered HTML
    becomes the body_html and an auto-generated plain text becomes body_text.

    Usage:
        msg = TemplateMessage(
            template="welcome.aqt",
            context={"user": {"name": "Asha"}},
            to=["asha@example.com"],
            subject="Welcome, << user.name >>!",
        )
        await msg.asend()
    """

    def __init__(
        self,
        template: str,
        context: dict[str, Any] | None = None,
        *,
        subject: str = "",
        from_email: str | None = None,
        to: Sequence[str] | None = None,
        cc: Sequence[str] | None = None,
        bcc: Sequence[str] | None = None,
        reply_to: str | None = None,
        headers: dict[str, str] | None = None,
        attachments: list[tuple[str, bytes, str]] | None = None,
        priority: int = Priority.NORMAL.value,
        idempotency_key: str | None = None,
        tenant_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        super().__init__(
            subject=subject,
            body="",  # populated after render
            from_email=from_email,
            to=to,
            cc=cc,
            bcc=bcc,
            reply_to=reply_to,
            headers=headers,
            attachments=attachments,
            priority=priority,
            idempotency_key=idempotency_key,
            tenant_id=tenant_id,
            metadata=metadata,
        )
        self.template_name = template
        self.template_context = context or {}

    def build_envelope(self, default_from: str = "noreply@localhost") -> tuple[MailEnvelope, dict[str, bytes]]:
        """
        Build the envelope, rendering the ATS template first.

        The template body is rendered with HTML autoescaping enabled (see
        :mod:`aquilia.mail.template`); the subject is rendered **without**
        escaping because a mail header is plain text — escaping there would
        turn ``Asha & Co`` into ``Asha &amp; Co`` in the recipient's inbox.

        Returns:
            ``(envelope, attachment_blobs)`` — same contract as
            :meth:`EmailMessage.build_envelope`.

        Raises:
            MailTemplateFault: If the template is missing or uses syntax ATS
                does not support.
            MailValidationFault: If no recipient is set.
        """
        from .template import render_string, render_template

        # Render the ATS template (HTML body → autoescaped)
        rendered_html = render_template(self.template_name, self.template_context)

        # Auto-generate plain text from HTML (basic strip)
        rendered_text = _html_to_text(rendered_html)

        # Subject may contain ATS expressions -- render inline, unescaped
        if "<<" in self.subject:
            self.subject = render_string(self.subject, self.template_context, autoescape=False)

        self.body = rendered_text
        self._alternatives.append((rendered_html, "text/html"))

        envelope, blobs = super().build_envelope(default_from)
        envelope.template_name = self.template_name
        envelope.template_context = self.template_context
        return envelope, blobs

    def __repr__(self) -> str:
        return f"TemplateMessage(template={self.template_name!r}, to={self.to!r})"


# ── Helpers ─────────────────────────────────────────────────────────

_TAG_RE = re.compile(r"<[^>]+>")
_MULTI_WS_RE = re.compile(r"\s+")


def _html_to_text(html: str) -> str:
    """Basic HTML → plain text conversion for multipart fallback."""
    text = html
    # Convert <br> to newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    # Convert </p>, </div>, </tr> to double newlines
    text = re.sub(r"</(p|div|tr|li|h[1-6])>", "\n\n", text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = _TAG_RE.sub("", text)
    # Collapse whitespace
    lines = []
    for line in text.split("\n"):
        stripped = _MULTI_WS_RE.sub(" ", line).strip()
        if stripped:
            lines.append(stripped)
    return "\n".join(lines)
