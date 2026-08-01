"""
AquilaMail — provider webhook processing.

Email delivery is asynchronous beyond the SMTP handshake: a provider accepts
a message, then reports minutes later that it bounced or was marked as spam.
Without consuming those callbacks an application never learns an address is
dead and keeps sending to it, which is what destroys sender reputation.

This module normalises each provider's payload into a common
:class:`WebhookEvent`, so application code handles one shape instead of three.
:func:`process_webhook` then applies the consequence — auto-suppressing hard
bounces and complaints.

Supported providers: Amazon SES (via SNS), SendGrid, Mailgun.

Security:
    Every parser verifies the provider's signature before trusting a payload.
    A webhook endpoint is public by definition; without verification anyone
    could POST a forged "complaint" for an arbitrary address and suppress a
    competitor's mail, or forge "delivered" to hide real failures.  Signature
    checks use :func:`hmac.compare_digest` so a timing side channel cannot
    leak the expected value.

Examples::

    from aquilia.mail.webhooks import parse_sendgrid, process_webhook

    @POST("/webhooks/sendgrid")
    async def sendgrid_hook(self, ctx: RequestCtx):
        raw = await ctx.body()
        events = parse_sendgrid(
            raw,
            headers=ctx.headers,
            public_key=settings.SENDGRID_WEBHOOK_KEY,
        )
        await process_webhook(events, suppression=mail.suppression)
        return Response.json({"ok": True})
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from aquilia.mail.faults import MailConfigFault, MailValidationFault
from aquilia.mail.suppression import SuppressionList, SuppressionReason, normalize_email

logger = logging.getLogger("aquilia.mail.webhooks")

__all__ = [
    "EventType",
    "WebhookEvent",
    "parse_mailgun",
    "parse_ses",
    "parse_sendgrid",
    "process_webhook",
]


class EventType(str, Enum):
    """
    Normalised delivery event, mapped from each provider's vocabulary.

    Attributes:
        DELIVERED: Accepted by the recipient's server.
        HARD_BOUNCE: Permanent failure; suppress the address.
        SOFT_BOUNCE: Temporary failure; suppress briefly.
        COMPLAINT: Marked as spam; suppress permanently.
        REJECTED: Provider refused before sending.
        OPENED: Recipient opened the message.
        CLICKED: Recipient clicked a link.
        UNSUBSCRIBED: Recipient opted out; suppress permanently.
        DEFERRED: Delivery postponed; retried by the provider.
        UNKNOWN: Unrecognised event, preserved for observability rather than
            dropped, so a provider adding a new type is visible.
    """

    DELIVERED = "delivered"
    HARD_BOUNCE = "hard_bounce"
    SOFT_BOUNCE = "soft_bounce"
    COMPLAINT = "complaint"
    REJECTED = "rejected"
    OPENED = "opened"
    CLICKED = "clicked"
    UNSUBSCRIBED = "unsubscribed"
    DEFERRED = "deferred"
    UNKNOWN = "unknown"

    @property
    def suppression_reason(self) -> SuppressionReason | None:
        """The suppression this event implies, or ``None`` if it implies none."""
        return {
            EventType.HARD_BOUNCE: SuppressionReason.HARD_BOUNCE,
            EventType.SOFT_BOUNCE: SuppressionReason.SOFT_BOUNCE,
            EventType.COMPLAINT: SuppressionReason.COMPLAINT,
            EventType.UNSUBSCRIBED: SuppressionReason.UNSUBSCRIBE,
        }.get(self)


@dataclass
class WebhookEvent:
    """
    One normalised delivery event.

    Attributes:
        event_type: Normalised :class:`EventType`.
        email: Affected recipient.
        provider: Reporting provider (``"ses"``, ``"sendgrid"``, ``"mailgun"``).
        timestamp: When the provider recorded the event.
        message_id: Provider message ID, for correlating with an envelope.
        envelope_id: Aquilia envelope ID, when the provider echoed the
            ``X-Aquilia-Envelope-ID`` header back.
        detail: Diagnostic text, e.g. the SMTP rejection line.
        raw: The original provider payload, kept for auditing.
    """

    event_type: EventType
    email: str
    provider: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    message_id: str | None = None
    envelope_id: str | None = None
    detail: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type.value,
            "email": self.email,
            "provider": self.provider,
            "timestamp": self.timestamp.isoformat(),
            "message_id": self.message_id,
            "envelope_id": self.envelope_id,
            "detail": self.detail,
        }


def _ts(value: Any) -> datetime:
    """Parse a provider timestamp (epoch or ISO) into an aware datetime."""
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.now(timezone.utc)


# ── Amazon SES ──────────────────────────────────────────────────────


def parse_ses(payload: bytes | str | dict[str, Any], *, verify_topic_arn: str | None = None) -> list[WebhookEvent]:
    """
    Parse an Amazon SES notification delivered over SNS.

    Args:
        payload: The SNS envelope — raw body or decoded dict.
        verify_topic_arn: Expected ``TopicArn``.  When given, a notification
            from any other topic is rejected, which prevents an attacker with
            a valid SNS subscription of their own from injecting events.

    Returns:
        Normalised events; empty for non-notification SNS control messages.

    Raises:
        MailValidationFault: If the payload is malformed or the topic does not
            match.

    Notes:
        SNS also signs messages with an X.509 certificate.  Verifying that
        requires fetching and validating AWS's signing certificate, which is
        outside this function's scope — put the endpoint behind
        ``verify_topic_arn`` plus HTTPS, and prefer configuring SES to deliver
        into SQS when stronger authentication is needed.

    Examples::

        events = parse_ses(raw_body, verify_topic_arn=settings.SES_TOPIC_ARN)
    """
    data = _decode_json(payload, provider="ses")

    if verify_topic_arn:
        actual = data.get("TopicArn")
        if actual != verify_topic_arn:
            raise MailValidationFault(
                f"SES webhook rejected: TopicArn {actual!r} does not match the configured topic",
                field="TopicArn",
            )

    # SNS wraps the SES payload as a JSON string in "Message".
    message = data.get("Message", data)
    if isinstance(message, str):
        try:
            message = json.loads(message)
        except json.JSONDecodeError as e:
            raise MailValidationFault(f"SES webhook has a malformed Message body: {e}", field="Message") from e

    notification_type = str(message.get("notificationType") or message.get("eventType") or "").lower()
    mail_data = message.get("mail", {})
    message_id = mail_data.get("messageId")
    envelope_id = (mail_data.get("headers") and _header_value(mail_data["headers"], "X-Aquilia-Envelope-ID")) or None

    events: list[WebhookEvent] = []

    if notification_type == "bounce":
        bounce = message.get("bounce", {})
        # SES distinguishes Permanent from Transient; treating a Transient
        # bounce as permanent would suppress a mailbox that was merely full.
        permanent = str(bounce.get("bounceType", "")).lower() == "permanent"
        event_type = EventType.HARD_BOUNCE if permanent else EventType.SOFT_BOUNCE
        for recipient in bounce.get("bouncedRecipients", []):
            events.append(
                WebhookEvent(
                    event_type=event_type,
                    email=recipient.get("emailAddress", ""),
                    provider="ses",
                    timestamp=_ts(bounce.get("timestamp")),
                    message_id=message_id,
                    envelope_id=envelope_id,
                    detail=recipient.get("diagnosticCode") or bounce.get("bounceSubType"),
                    raw=message,
                )
            )

    elif notification_type == "complaint":
        complaint = message.get("complaint", {})
        for recipient in complaint.get("complainedRecipients", []):
            events.append(
                WebhookEvent(
                    event_type=EventType.COMPLAINT,
                    email=recipient.get("emailAddress", ""),
                    provider="ses",
                    timestamp=_ts(complaint.get("timestamp")),
                    message_id=message_id,
                    envelope_id=envelope_id,
                    detail=complaint.get("complaintFeedbackType"),
                    raw=message,
                )
            )

    elif notification_type == "delivery":
        delivery = message.get("delivery", {})
        for address in delivery.get("recipients", []):
            events.append(
                WebhookEvent(
                    event_type=EventType.DELIVERED,
                    email=address,
                    provider="ses",
                    timestamp=_ts(delivery.get("timestamp")),
                    message_id=message_id,
                    envelope_id=envelope_id,
                    raw=message,
                )
            )

    return events


def _header_value(headers: list[dict[str, Any]], name: str) -> str | None:
    """Case-insensitively read a header from SES's list-of-dicts format."""
    for header in headers:
        if str(header.get("name", "")).lower() == name.lower():
            return header.get("value")
    return None


# ── SendGrid ────────────────────────────────────────────────────────

_SENDGRID_EVENTS = {
    "delivered": EventType.DELIVERED,
    "bounce": EventType.HARD_BOUNCE,
    "blocked": EventType.SOFT_BOUNCE,
    "deferred": EventType.DEFERRED,
    "dropped": EventType.REJECTED,
    "spamreport": EventType.COMPLAINT,
    "unsubscribe": EventType.UNSUBSCRIBED,
    "group_unsubscribe": EventType.UNSUBSCRIBED,
    "open": EventType.OPENED,
    "click": EventType.CLICKED,
    "processed": EventType.UNKNOWN,
}


def parse_sendgrid(
    payload: bytes | str,
    *,
    headers: dict[str, str] | None = None,
    public_key: str | None = None,
    max_age_seconds: float = 600.0,
) -> list[WebhookEvent]:
    """
    Parse a SendGrid Event Webhook batch.

    Args:
        payload: Raw request body.  Must be the exact bytes received — the
            signature covers them verbatim, so re-serialising breaks it.
        headers: Request headers carrying the signature and timestamp.
        public_key: SendGrid's base64 ECDSA verification key.  When provided,
            the signature is verified and an invalid payload is rejected.
        max_age_seconds: Reject signatures older than this, so a captured
            request cannot be replayed indefinitely.

    Returns:
        Normalised events.

    Raises:
        MailValidationFault: If the payload is malformed, or verification fails.
        MailConfigFault: If ``public_key`` is set but ``cryptography`` is not
            installed — failing loudly beats silently skipping verification.

    Warning:
        Omitting ``public_key`` leaves the endpoint unauthenticated: anyone
        who learns the URL can forge bounce and complaint events. Always pass
        it in production.

    Examples::

        events = parse_sendgrid(raw, headers=ctx.headers, public_key=KEY)
    """
    if public_key:
        _verify_sendgrid_signature(payload, headers or {}, public_key, max_age_seconds)
    elif headers is not None:
        logger.warning(
            "SendGrid webhook processed without signature verification. "
            "Set public_key so forged bounce/complaint events are rejected."
        )

    data = _decode_json(payload, provider="sendgrid")
    batch = data if isinstance(data, list) else [data]

    events: list[WebhookEvent] = []
    for item in batch:
        if not isinstance(item, dict):
            continue
        event_type = _SENDGRID_EVENTS.get(str(item.get("event", "")).lower(), EventType.UNKNOWN)

        # SendGrid marks async bounces with type="blocked" for soft failures.
        if event_type is EventType.HARD_BOUNCE and str(item.get("type", "")).lower() == "blocked":
            event_type = EventType.SOFT_BOUNCE

        events.append(
            WebhookEvent(
                event_type=event_type,
                email=item.get("email", ""),
                provider="sendgrid",
                timestamp=_ts(item.get("timestamp")),
                message_id=item.get("sg_message_id"),
                envelope_id=item.get("aquilia_envelope_id"),
                detail=item.get("reason") or item.get("response"),
                raw=item,
            )
        )
    return events


def _verify_sendgrid_signature(
    payload: bytes | str,
    headers: dict[str, str],
    public_key: str,
    max_age_seconds: float,
) -> None:
    """
    Verify SendGrid's ECDSA webhook signature.

    Raises:
        MailValidationFault: On a missing, stale, or invalid signature.
        MailConfigFault: If ``cryptography`` is unavailable.
    """
    lowered = {k.lower(): v for k, v in headers.items()}
    signature = lowered.get("x-twilio-email-event-webhook-signature")
    timestamp = lowered.get("x-twilio-email-event-webhook-timestamp")

    if not signature or not timestamp:
        raise MailValidationFault(
            "SendGrid webhook is missing its signature headers; rejecting as unverified.",
            field="signature",
        )

    # Reject stale signatures so a captured request cannot be replayed later.
    try:
        age = abs(time.time() - float(timestamp))
    except ValueError as e:
        raise MailValidationFault(f"SendGrid webhook timestamp is malformed: {timestamp!r}", field="timestamp") from e
    if age > max_age_seconds:
        raise MailValidationFault(
            f"SendGrid webhook signature is {age:.0f}s old (limit {max_age_seconds:.0f}s); rejecting as a replay.",
            field="timestamp",
        )

    try:
        from cryptography.exceptions import InvalidSignature
        from cryptography.hazmat.primitives.asymmetric import ec
        from cryptography.hazmat.primitives.hashes import SHA256
        from cryptography.hazmat.primitives.serialization import load_der_public_key
    except ImportError as e:
        raise MailConfigFault(
            "Verifying SendGrid webhooks requires the 'cryptography' package. Install with: pip install cryptography",
            config_key="mail.webhooks.sendgrid_public_key",
        ) from e

    body = payload.encode() if isinstance(payload, str) else payload
    signed = timestamp.encode() + body

    try:
        key = load_der_public_key(base64.b64decode(public_key))
        key.verify(base64.b64decode(signature), signed, ec.ECDSA(SHA256()))
    except InvalidSignature as e:
        raise MailValidationFault(
            "SendGrid webhook signature is invalid; payload may be forged.",
            field="signature",
        ) from e
    except Exception as e:
        raise MailValidationFault(f"SendGrid webhook signature could not be verified: {e}", field="signature") from e


# ── Mailgun ─────────────────────────────────────────────────────────

_MAILGUN_EVENTS = {
    "delivered": EventType.DELIVERED,
    "failed": EventType.HARD_BOUNCE,
    "rejected": EventType.REJECTED,
    "complained": EventType.COMPLAINT,
    "unsubscribed": EventType.UNSUBSCRIBED,
    "opened": EventType.OPENED,
    "clicked": EventType.CLICKED,
    "accepted": EventType.UNKNOWN,
}


def parse_mailgun(
    payload: bytes | str | dict[str, Any],
    *,
    signing_key: str | None = None,
    max_age_seconds: float = 600.0,
) -> list[WebhookEvent]:
    """
    Parse a Mailgun webhook payload.

    Args:
        payload: Request body or decoded dict.
        signing_key: Mailgun HTTP webhook signing key.  When provided, the
            HMAC signature is verified.
        max_age_seconds: Reject signatures older than this.

    Returns:
        Normalised events.

    Raises:
        MailValidationFault: On malformed payload or failed verification.

    Warning:
        Without ``signing_key`` the endpoint is unauthenticated and accepts
        forged events. Always pass it in production.

    Examples::

        events = parse_mailgun(raw, signing_key=settings.MAILGUN_SIGNING_KEY)
    """
    data = _decode_json(payload, provider="mailgun")

    if signing_key:
        _verify_mailgun_signature(data.get("signature", {}), signing_key, max_age_seconds)
    else:
        logger.warning(
            "Mailgun webhook processed without signature verification. "
            "Set signing_key so forged bounce/complaint events are rejected."
        )

    event_data = data.get("event-data", data)
    severity = str(event_data.get("severity", "")).lower()
    event_name = str(event_data.get("event", "")).lower()
    event_type = _MAILGUN_EVENTS.get(event_name, EventType.UNKNOWN)

    # Mailgun reports both hard and soft failures as "failed"; only severity
    # distinguishes them, and treating temporary as permanent would suppress
    # a working address.
    if event_type is EventType.HARD_BOUNCE and severity == "temporary":
        event_type = EventType.SOFT_BOUNCE

    recipient = event_data.get("recipient", "")
    message = event_data.get("message", {})
    headers = message.get("headers", {}) if isinstance(message, dict) else {}

    return [
        WebhookEvent(
            event_type=event_type,
            email=recipient,
            provider="mailgun",
            timestamp=_ts(event_data.get("timestamp")),
            message_id=headers.get("message-id"),
            envelope_id=(event_data.get("user-variables") or {}).get("aquilia_envelope_id"),
            detail=(event_data.get("delivery-status") or {}).get("message") or event_data.get("reason"),
            raw=event_data,
        )
    ]


def _verify_mailgun_signature(signature: dict[str, Any], signing_key: str, max_age_seconds: float) -> None:
    """
    Verify Mailgun's HMAC-SHA256 webhook signature.

    Raises:
        MailValidationFault: On a missing, stale, or invalid signature.
    """
    token = signature.get("token")
    timestamp = signature.get("timestamp")
    provided = signature.get("signature")

    if not (token and timestamp and provided):
        raise MailValidationFault(
            "Mailgun webhook is missing its signature block; rejecting as unverified.",
            field="signature",
        )

    try:
        age = abs(time.time() - float(timestamp))
    except (TypeError, ValueError) as e:
        raise MailValidationFault(f"Mailgun webhook timestamp is malformed: {timestamp!r}", field="timestamp") from e
    if age > max_age_seconds:
        raise MailValidationFault(
            f"Mailgun webhook signature is {age:.0f}s old (limit {max_age_seconds:.0f}s); rejecting as a replay.",
            field="timestamp",
        )

    expected = hmac.new(
        signing_key.encode(),
        f"{timestamp}{token}".encode(),
        hashlib.sha256,
    ).hexdigest()

    # compare_digest: constant time, so a timing side channel cannot reveal
    # the expected signature byte by byte.
    if not hmac.compare_digest(expected, str(provided)):
        raise MailValidationFault(
            "Mailgun webhook signature is invalid; payload may be forged.",
            field="signature",
        )


def _decode_json(payload: bytes | str | dict[str, Any] | list[Any], *, provider: str) -> Any:
    """Decode a webhook body, raising a typed fault on malformed JSON."""
    if isinstance(payload, (dict, list)):
        return payload
    try:
        return json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as e:
        raise MailValidationFault(f"{provider} webhook payload is not valid JSON: {e}", field="payload") from e


# ── Consequences ────────────────────────────────────────────────────


async def process_webhook(
    events: list[WebhookEvent],
    *,
    suppression: SuppressionList | None = None,
    store: Any = None,
    soft_bounce_ttl: float = 86400.0,
) -> dict[str, int]:
    """
    Apply delivery events: suppress bad addresses and update envelope status.

    This is where a webhook stops being a log line and starts protecting
    deliverability — a hard bounce or complaint removes the address from all
    future sends automatically.

    Args:
        events: Normalised events from a ``parse_*`` function.
        suppression: List to update.  Omit to record status only.
        store: Optional :class:`~aquilia.mail.store.EnvelopeStore` whose
            envelopes should be marked bounced.
        soft_bounce_ttl: How long a soft bounce suppresses an address.

    Returns:
        Counts keyed by outcome: ``suppressed``, ``delivered``, ``ignored``.

    Examples::

        events = parse_ses(body)
        summary = await process_webhook(events, suppression=mail.suppression)
        # {"suppressed": 2, "delivered": 5, "ignored": 1}
    """
    from aquilia.mail.envelope import EnvelopeStatus

    counts = {"suppressed": 0, "delivered": 0, "ignored": 0}

    for event in events:
        if not event.email:
            counts["ignored"] += 1
            continue

        reason = event.event_type.suppression_reason
        if reason and suppression is not None:
            await suppression.suppress(
                event.email,
                reason=reason,
                expires_in=soft_bounce_ttl if reason is SuppressionReason.SOFT_BOUNCE else None,
                provider=event.provider,
                detail=event.detail,
            )
            counts["suppressed"] += 1
        elif event.event_type is EventType.DELIVERED:
            counts["delivered"] += 1
        else:
            counts["ignored"] += 1

        if store is not None and event.envelope_id:
            envelope = await store.get(event.envelope_id)
            if envelope is not None:
                if event.event_type in (EventType.HARD_BOUNCE, EventType.SOFT_BOUNCE):
                    envelope.status = EnvelopeStatus.BOUNCED
                    envelope.error_message = event.detail
                elif event.event_type is EventType.DELIVERED:
                    envelope.status = EnvelopeStatus.SENT
                await store.save(envelope)

    if counts["suppressed"]:
        logger.info(
            "Webhook processed: suppressed %d recipient(s) from %s",
            counts["suppressed"],
            events[0].provider if events else "unknown",
        )
    return counts


def normalize_recipient(email: str) -> str:
    """Re-exported from :mod:`aquilia.mail.suppression` for webhook callers."""
    return normalize_email(email)
