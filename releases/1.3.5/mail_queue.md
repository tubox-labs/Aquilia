# Mail Delivery Queue — Aquilia v1.3.5

Outbound mail can now be delivered by background workers instead of inside the request handler. `send_message()` persists an envelope, schedules a delivery job, and returns — the SMTP conversation happens on a worker, with retries, backoff, and delayed sends managed by the task scheduler.

This reuses Aquilia's existing task system. No second queue implementation was introduced.

---

## Motivation

Sending mail inside a request handler ties the response time of a user-facing endpoint to a third party's SMTP latency. A slow provider makes signup slow; an unreachable provider makes signup fail. Retrying meant either blocking the request further or losing the message.

---

## Design Goals

1. **Reuse the scheduler.** Retries, delayed delivery, persistence, and worker execution are the task system's job, not mail's.
2. **Same API whether queued or not.** Enabling the queue is a configuration change; call sites are unchanged.
3. **Survive the jump to distributed workers with no API change.** The delivery job had to be designed for a persistent backend from day one.
4. **Never accept mail that cannot be sent.** Recording an envelope as queued when nothing can deliver it is worse than sending inline.

---

## Architecture

```
send_message()
  │
  ├─ build envelope (validate, apply suppression, dedupe)
  ├─ EnvelopeStore.save(envelope)          ← durable record
  └─ enqueue "aquilia.mail.deliver"(envelope_id)
                    │
                    ▼
             task worker (possibly another process)
                    │
                    ├─ EnvelopeStore.get(envelope_id)
                    ├─ provider.send(...)  → SENT
                    └─ on failure → schedule retry with backoff
```

### `EnvelopeStore`

The durable record of accepted mail. Two implementations ship:

| Class | Durability |
|---|---|
| `MemoryEnvelopeStore` | In-process, bounded (`max_envelopes`, default 10,000). Default. |
| `SQLEnvelopeStore` | Application database, table `aquilia_mail_envelopes`. |

The interface covers `save`, `get`, `list_by_status`, `find_by_digest`, `find_by_idempotency_key`, `cleanup`, and `stats`.

### The delivery task

Delivery is a registered task named `aquilia.mail.deliver`, on queue `mail`.

**It takes an envelope ID, not an envelope.** A live `MailEnvelope` cannot survive a persistent or distributed backend, which serializes jobs as JSON. The worker — which may be in another process entirely — reloads the envelope from the shared store. This is what lets mail delivery run on another machine without any API change.

It is registered under a stable name rather than enqueued as a bare callable, so a worker in another process resolves it through the `@task` registry; a module-path reference would not survive a rename.

Mail owns its own retry policy, so the job is enqueued with `max_retries=0` and the mail service schedules its own follow-up attempts with backoff.

---

## Configuration

```python
# workspace.py

# Inline delivery (default, unchanged)
Integration.mail(default_from="noreply@example.com", providers=[...])

# Background delivery
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
)

# Background delivery with durable envelopes and suppression
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
    queue_persistent=True,
)
```

| Option | Default | Purpose |
|---|---|---|
| `queue_enabled` | `False` | Deliver via background tasks instead of inside the request |
| `queue_persistent` | `False` | Keep envelopes and suppression records in the application database |
| `queue_dedupe_window_seconds` | `3600` | Window in which an identical send is collapsed rather than sent twice |
| `queue_retention_days` | `30` | How long delivered envelopes are retained |

For an end-to-end durable path, pair `queue_persistent=True` with a durable task backend:

```python
Integration.tasks(backend="redis", redis_url="redis://cache:6379/0")
Integration.mail(queue_enabled=True, queue_persistent=True, ...)
```

`queue_persistent=True` requires `Integration.database(...)`.

---

## Usage

Call sites are identical whether the queue is on or off:

```python
from aquilia.mail import EmailMessage

envelope_id = await EmailMessage(
    subject="Welcome",
    body="Thanks for signing up",
    to=user.email,
).asend()
```

With the queue enabled, `asend()` returns as soon as the envelope is stored — typically sub-millisecond — and delivery completes on a worker. The returned envelope ID is the handle for checking status:

```python
envelope = await mail.store.get(envelope_id)
envelope.status      # QUEUED → SENDING → SENT / FAILED / BOUNCED / CANCELLED
envelope.attempts
```

---

## Send-Time Deduplication

Independent of the task system's job-level deduplication, mail collapses duplicate *sends*:

- An explicit `idempotency_key` on the message matches first.
- Otherwise a content digest matches within `queue_dedupe_window_seconds`.

This guards the classic double-send: a retried request or a double-clicked button producing two identical emails.

---

## Edge Cases

**No task manager, queue enabled.** Delivery falls back to inline sending. Recording an envelope as queued when nothing can deliver it would silently drop mail. The fallback also applies when a manager exists but has not been started — enqueueing into a stopped manager would park the message forever.

**Persistent stores with no database.** If `queue_persistent=True` but the database is unavailable, mail logs an error naming the durability that was lost and falls back to in-memory stores rather than aborting startup.

**Every recipient suppressed.** The envelope is marked `CANCELLED` and no delivery job is scheduled. See [Bounce Handling & Suppression](bounces_suppression.md).

**Missing envelope at delivery time.** A delivery job whose envelope has been cleaned up or cancelled logs a warning and is treated as success rather than retried forever — no amount of retrying will bring it back.

**Attachments.** Attachment payloads live in envelope metadata as blobs keyed by digest, so an envelope reloaded on another worker still carries its attachments.

---

## Performance Implications

Request-path cost drops from a full SMTP conversation (tens to hundreds of milliseconds, or a provider timeout on failure) to one store write plus one enqueue. Throughput of actual delivery becomes a function of worker count and provider rate limits rather than request concurrency.

`MemoryEnvelopeStore` evicts oldest-first past `max_envelopes`; an evicted envelope's delivery job will find nothing and give up. Use `queue_persistent=True` for any deployment where that matters.

---

## Compatibility

Fully backward compatible. `queue_enabled` defaults to `False`, so mail continues to send inline exactly as before unless explicitly enabled. `EmailMessage`, `send_message()`, and `asend()` signatures are unchanged. `MailService.store` and `MailService.suppression` are new attributes; passing explicit `store=` / `suppression=` to the constructor still overrides configuration.

---

## Related

- [Bounce Handling & Suppression](bounces_suppression.md)
- [Distributed & Persistent Backends](distributed_tasks.md)
- [Mail Security & MIME](mail_security.md)
- [Migration Guide](migration.md)
