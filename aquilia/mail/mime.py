"""
AquilaMail MIME construction and DKIM signing.

Shared by every provider that has to hand a real RFC 5322 message to a
transport — currently :mod:`~aquilia.mail.providers.smtp` (via
``send_message``) and :mod:`~aquilia.mail.providers.ses` (via raw send).
Both used to hand-roll multipart assembly; keeping one builder means
attachment handling, inline-image CID wiring, tracking headers and DKIM
signing are fixed once rather than twice.

Structure produced::

    multipart/mixed
    ├── multipart/alternative        (only when an HTML body exists)
    │   ├── text/plain
    │   └── text/html
    ├── attachment 1
    └── attachment N

Attachment bytes are carried on the envelope under
``metadata["blob:<digest>"]``, populated by
:meth:`~aquilia.mail.service.MailService.send_message` from the blob map that
:meth:`~aquilia.mail.message.EmailMessage.build_envelope` returns.

DKIM:
    :func:`sign_dkim` adds a ``DKIM-Signature`` header using ``dkimpy``.
    Signing is opt-in through ``MailConfig.security``; a misconfigured or
    unavailable signer raises rather than sending unsigned mail, because a
    silently unsigned message from a domain publishing a strict DMARC policy
    is worse than a failed send.

Examples::

    from aquilia.mail.mime import build_mime_message, message_to_bytes

    msg = build_mime_message(envelope)
    raw = message_to_bytes(msg)
"""

from __future__ import annotations

import os
from email import encoders
from email.message import Message
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from typing import Any

from .envelope import MailEnvelope
from .faults import MailConfigFault, MailSendFault

__all__ = [
    "build_mime_message",
    "extract_domain",
    "message_to_bytes",
    "sign_dkim",
]


def extract_domain(email: str) -> str:
    """
    Extract the domain part of an address, tolerating display-name form.

    Args:
        email: ``"user@example.com"`` or ``"Name <user@example.com>"``.

    Returns:
        The domain, or ``"localhost"`` when the address has no ``@``.

    Examples::

        extract_domain("Asha <asha@example.com>")   # 'example.com'
        extract_domain("operator")                  # 'localhost'
    """
    if "<" in email:
        email = email.split("<")[1].rstrip(">")
    return email.rsplit("@", 1)[-1] if "@" in email else "localhost"


def build_mime_message(
    envelope: MailEnvelope,
    *,
    extra_headers: dict[str, str] | None = None,
) -> MIMEMultipart:
    """
    Build a complete MIME message from an envelope.

    Args:
        envelope: Source envelope; attachment payloads are read from
            ``envelope.metadata["blob:<digest>"]``.
        extra_headers: Provider-specific headers merged last (e.g. an ESP's
            configuration-set header).

    Returns:
        A ``multipart/mixed`` message with a generated ``Message-ID`` and
        Aquilia tracking headers (``X-Aquilia-Envelope-ID`` and, when set,
        trace and tenant IDs).

    Notes:
        Bcc recipients are deliberately **not** written as a header — they
        are passed to the transport's recipient list instead, so they stay
        invisible to everyone who receives the message.

    Examples::

        msg = build_mime_message(envelope)
        msg["Message-ID"]        # '<...@example.com>'
    """
    msg = MIMEMultipart("mixed")

    msg["From"] = envelope.from_email
    msg["To"] = ", ".join(envelope.to)
    if envelope.cc:
        msg["Cc"] = ", ".join(envelope.cc)
    msg["Subject"] = envelope.subject
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain=extract_domain(envelope.from_email))

    if envelope.reply_to:
        msg["Reply-To"] = envelope.reply_to

    for key, value in envelope.headers.items():
        msg[key] = value

    msg["X-Aquilia-Envelope-ID"] = envelope.id
    if envelope.trace_id:
        msg["X-Aquilia-Trace-ID"] = envelope.trace_id
    if envelope.tenant_id:
        msg["X-Aquilia-Tenant-ID"] = envelope.tenant_id

    for key, value in (extra_headers or {}).items():
        msg[key] = value

    if envelope.body_html:
        alt = MIMEMultipart("alternative")
        alt.attach(MIMEText(envelope.body_text, "plain", "utf-8"))
        alt.attach(MIMEText(envelope.body_html, "html", "utf-8"))
        msg.attach(alt)
    else:
        msg.attach(MIMEText(envelope.body_text, "plain", "utf-8"))

    for attachment in envelope.attachments:
        maintype, _, subtype = attachment.content_type.partition("/")
        part = MIMEBase(maintype or "application", subtype or "octet-stream")
        part.set_payload(envelope.metadata.get(f"blob:{attachment.digest}", b""))
        encoders.encode_base64(part)

        if attachment.inline and attachment.content_id:
            part.add_header("Content-Disposition", "inline", filename=attachment.filename)
            part.add_header("Content-ID", f"<{attachment.content_id}>")
        else:
            part.add_header("Content-Disposition", "attachment", filename=attachment.filename)
        msg.attach(part)

    return msg


def _load_dkim_key(security: Any) -> bytes:
    """
    Load the DKIM private key from a file path or environment variable.

    Precedence: ``dkim_private_key_path`` then ``dkim_private_key_env``.

    Raises:
        MailConfigFault: If neither source yields a key, or the file is
            unreadable.
    """
    path = getattr(security, "dkim_private_key_path", None)
    if path:
        try:
            with open(path, "rb") as fh:
                return fh.read()
        except OSError as e:
            raise MailConfigFault(
                f"Cannot read DKIM private key at {path!r}: {e}",
                config_key="mail.security.dkim_private_key_path",
            ) from e

    env_name = getattr(security, "dkim_private_key_env", None)
    if env_name:
        raw = os.environ.get(str(env_name))
        if raw:
            return raw.encode()

    raise MailConfigFault(
        "DKIM signing is enabled but no private key was found. Set "
        "mail.security.dkim_private_key_path or the environment variable named by "
        "mail.security.dkim_private_key_env.",
        config_key="mail.security.dkim_private_key_path",
    )


def sign_dkim(raw_message: bytes, security: Any) -> bytes:
    """
    Prepend a ``DKIM-Signature`` header to a serialized MIME message.

    Args:
        raw_message: The full message bytes, as produced by
            :func:`message_to_bytes`.
        security: ``MailConfig.security`` — supplies ``dkim_enabled``,
            ``dkim_domain``, ``dkim_selector`` and the key location.

    Returns:
        The signed message.  Returns ``raw_message`` unchanged when
        ``dkim_enabled`` is false.

    Raises:
        MailConfigFault: If signing is enabled but the domain or key is
            missing, or ``dkimpy`` is not installed.
        MailSendFault: If the signer rejects the message.

    Security:
        Failures raise instead of degrading to an unsigned send: a receiver
        enforcing DMARC would reject or quarantine the unsigned copy, and a
        silent downgrade hides that from the operator.

    Examples::

        raw = message_to_bytes(build_mime_message(envelope))
        raw = sign_dkim(raw, config.security)
    """
    if not getattr(security, "dkim_enabled", False):
        return raw_message

    domain = getattr(security, "dkim_domain", None)
    if not domain:
        raise MailConfigFault(
            "DKIM signing is enabled but mail.security.dkim_domain is unset.",
            config_key="mail.security.dkim_domain",
        )

    try:
        import dkim as dkimpy
    except ImportError as e:
        raise MailConfigFault(
            "DKIM signing requires the 'dkimpy' package. Install it with: pip install dkimpy",
            config_key="mail.security.dkim_enabled",
        ) from e

    selector = getattr(security, "dkim_selector", None) or "aquilia"
    private_key = _load_dkim_key(security)

    try:
        signature = dkimpy.sign(
            message=raw_message,
            selector=str(selector).encode(),
            domain=str(domain).encode(),
            privkey=private_key,
            include_headers=[b"From", b"To", b"Subject", b"Date", b"Message-ID"],
        )
    except Exception as e:
        raise MailSendFault(
            f"DKIM signing failed for domain {domain!r}: {e}",
            provider="dkim",
            transient=False,
        ) from e

    return signature + raw_message


def message_to_bytes(msg: Message, security: Any = None) -> bytes:
    """
    Serialize a MIME message, applying DKIM signing when configured.

    Args:
        msg: The message to serialize.
        security: ``MailConfig.security``, or ``None`` to skip signing.

    Returns:
        The wire-format message bytes.

    Examples::

        raw = message_to_bytes(build_mime_message(envelope), config.security)
    """
    raw = msg.as_bytes()
    return sign_dkim(raw, security) if security is not None else raw
