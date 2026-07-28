# Bounce Handling, Webhooks & Suppression Lists — Aquilia v1.3.5

Provider delivery events are now parsed, verified, and applied. A hard bounce or spam complaint automatically removes the address from all future sends. Before this release, `MailSuppressedFault` existed in the fault taxonomy but nothing raised it — there was no suppression list and no webhook handling at all.

---

## Motivation

Deliverability is reputation, and reputation is destroyed by continuing to mail addresses that bounce. Every ESP tracks bounce and complaint rates; exceed their thresholds and legitimate mail starts landing in spam or being rejected outright.

Handling this correctly requires three things Aquilia did not have: parsing each provider's webhook format, verifying those webhooks are genuine, and a persistent list consulted on every send.

---

## Architecture

```
provider webhook (HTTP POST)
        │
        ▼
parse_ses / parse_sendgrid / parse_mailgun    ← verify signature, normalize
        │
        ▼
   list[WebhookEvent]                          ← provider-neutral
        │
        ▼
   process_webhook(events, suppression=..., store=...)
        │
        ├─ suppress the address (permanent or TTL)
        └─ update the envelope's status
        │
        ▼
next send → MailService filters suppressed recipients
```

---

## Webhook Parsing

Three provider parsers normalize into one vocabulary:

```python
from aquilia.mail import parse_ses, parse_sendgrid, parse_mailgun

parse_ses(payload, *, verify_topic_arn=None)
parse_sendgrid(payload, *, headers=None, public_key=None, max_age_seconds=600.0)
parse_mailgun(payload, *, signing_key=None, max_age_seconds=600.0)
```

Each returns `list[WebhookEvent]`:

```python
@dataclass
class WebhookEvent:
    event_type: EventType
    email: str
    provider: str
    timestamp: datetime
    message_id: str | None = None
    envelope_id: str | None = None   # from the X-Aquilia-Envelope-ID header
    detail: str | None = None        # e.g. the SMTP rejection line
    raw: dict[str, Any]              # original payload, kept for auditing
```

`EventType` normalizes each provider's vocabulary: `DELIVERED`, `HARD_BOUNCE`, `SOFT_BOUNCE`, `COMPLAINT`, `REJECTED`, `OPENED`, `CLICKED`, `UNSUBSCRIBED`, `DEFERRED`, `UNKNOWN`. An unrecognized event becomes `UNKNOWN` and is preserved rather than dropped, so a provider adding a new type stays visible.

### Signature verification

**Verify webhooks in production.** An unverified endpoint lets anyone POST a forged bounce and suppress an arbitrary address — a trivial denial-of-service against your own users.

- **SES** — pass `verify_topic_arn` to reject notifications from any other SNS topic.
- **SendGrid** — pass `public_key` (the ECDSA verification key from your SendGrid settings) with the request `headers`. Replays older than `max_age_seconds` are rejected.
- **Mailgun** — pass `signing_key`. The HMAC signature and timestamp are verified.

Omitting these parameters parses without verification and logs a warning naming the risk.

---

## Suppression Lists

```python
from aquilia.mail import SuppressionReason

await suppression.suppress(
    email,
    reason=SuppressionReason.HARD_BOUNCE,
    expires_in=None,      # seconds; ignored for permanent reasons
    provider="ses",
    detail="550 5.1.1 user unknown",
)
await suppression.unsuppress(email)          # -> bool
await suppression.is_suppressed(email)       # -> bool
await suppression.get(email)                 # -> SuppressionEntry | None
await suppression.list_all(limit=100, offset=0)
await suppression.filter_recipients(emails)  # -> (allowed, blocked)
await suppression.cleanup()                  # drop expired entries
```

| Reason | Permanence |
|---|---|
| `HARD_BOUNCE` | Permanent — the address does not exist |
| `SOFT_BOUNCE` | Expires (defaults to 24 hours) — mailbox full, server down |
| `COMPLAINT` | Permanent — the most reputation-damaging signal a provider tracks |
| `UNSUBSCRIBE` | Permanent |
| `MANUAL` | Permanent — operator-added |

Two implementations ship: `MemorySuppressionList` (default) and `SQLSuppressionList` (table `aquilia_mail_suppressions`, selected by `queue_persistent=True`).

Addresses are normalized — lowercased and trimmed — before storage and lookup, so `User@Example.COM` and ` user@example.com ` are the same entry.

---

## Wiring a Webhook Endpoint

Aquilia does not register a webhook route for you; the path, authentication, and CSRF exemption belong to the application. The handler is a few lines:

```python
from aquilia import Controller, POST, RequestCtx, Response
from aquilia.mail import parse_ses, process_webhook

class MailWebhookController(Controller):
    prefix = "/webhooks/mail"

    @POST("/ses")
    async def ses(self, ctx: RequestCtx):
        events = parse_ses(await ctx.body(), verify_topic_arn=SES_TOPIC_ARN)
        summary = await process_webhook(
            events,
            suppression=self.mail.suppression,
            store=self.mail.store,
        )
        return Response.json(summary)   # {"suppressed": 2, "delivered": 5, "ignored": 1}
```

Exempt the webhook path from CSRF — providers do not carry your CSRF token. Rely on signature verification for authenticity instead.

---

## Enforcement on Send

`MailService` consults the suppression list while preparing every envelope. Suppressed recipients are removed; if *every* recipient is suppressed the envelope is marked `CANCELLED` and no delivery is attempted.

```python
await mail.suppression.suppress("bounced@example.com", reason=SuppressionReason.HARD_BOUNCE)

envelope_id = await EmailMessage(subject="Hi", body="x", to="bounced@example.com").asend()
envelope = await mail.store.get(envelope_id)
envelope.status    # EnvelopeStatus.CANCELLED
```

---

## Edge Cases

**Partial suppression.** An envelope with three recipients where one is suppressed sends to the remaining two. Only an envelope with no deliverable recipients is cancelled.

**Soft bounce TTL.** `process_webhook` suppresses soft bounces for `soft_bounce_ttl` (default 86,400 seconds) rather than permanently, since the cause is usually transient. Tune it per provider.

**Events with no address.** Counted as `ignored` rather than raising — a malformed event should not fail the whole batch.

**Non-suppressing events.** `DELIVERED`, `OPENED`, `CLICKED`, and `DEFERRED` update envelope status where applicable but never suppress.

**Malformed payloads.** A body that is not valid JSON raises `MailFault`, so a broken request surfaces as a 4xx rather than being silently swallowed.

**Envelope correlation.** Providers that echo custom headers return `X-Aquilia-Envelope-ID`, letting an event update the exact envelope. Providers that do not echo headers still suppress by address; the envelope simply is not correlated.

---

## Performance Implications

One suppression lookup per envelope on the send path. `MemorySuppressionList` is a dict lookup. `SQLSuppressionList` is an indexed primary-key read; `filter_recipients` batches a multi-recipient envelope rather than issuing one query per address.

Webhook processing is O(n) in events, with one suppression write per suppressing event.

---

## Compatibility

Purely additive. `MailService.suppression` defaults to an empty `MemorySuppressionList`, so no address is suppressed until a webhook or an operator adds one — existing applications see no behavioral change. `MailSuppressedFault`, previously unreachable, is now part of a working path.

---

## Related

- [Mail Delivery Queue](mail_queue.md)
- [Mail Security & MIME](mail_security.md)
- [Migration Guide](migration.md)
