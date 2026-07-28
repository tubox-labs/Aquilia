# Migration Guide — Aquilia v1.3.5

Aquilia v1.3.5 is a **backwards-compatible** feature release. No existing API was removed, renamed, or changed in signature. Every workspace, manifest, task, and mail configuration from 1.3.4 continues to work without modification.

This guide covers upgrading, then the optional migrations that let you adopt the new capabilities.

---

## Upgrading

```bash
pip install aquilia==1.3.5
```

Optional extras for the new capabilities:

```bash
pip install aquilia[redis]        # distributed task backend
pip install aquilia[mail-dkim]    # DKIM signing for outbound mail
```

Nothing else is required. If you change no configuration, v1.3.5 behaves exactly as v1.3.4 did:

- Tasks run on `MemoryBackend`, single process.
- Mail sends inline, inside the request.
- No addresses are suppressed.
- No deduplication is applied.

---

## Upgrade Checklist

1. `pip install aquilia==1.3.5`
2. Run your test suite — no changes expected.
3. *(Optional)* Move tasks to a durable backend — see below.
4. *(Optional)* Enable background mail delivery — see below.
5. *(Optional)* Wire provider webhooks for bounce handling.
6. If you use SendGrid or testing helpers, note that third-party `httpx` is no longer required as Aquilia uses native `aquilia.http`.
7. If you use DKIM, run `aq mail check` and install `aquilia[mail-dkim]`.
8. Remove any hand-rolled job deduplication in favour of `dedup="skip"`.
9. Remove any workaround that parsed `repr`-form job results.

---

## Migration 1 — Durable, Distributed Tasks

### Before

```python
# workspace.py
Integration.tasks(num_workers=4)
```

Jobs lived in the web worker process and were lost on restart. Running two web workers meant two independent queues, so a periodic task fired twice.

### After

```python
# workspace.py
Integration.tasks(
    backend="redis",
    redis_url="redis://cache:6379/0",
    num_workers=8,
    lease_seconds=120,
)
```

Or, with no new infrastructure:

```python
Integration.tasks(backend="sql")   # requires Integration.database(...)
```

### What you must check

**Task arguments must be JSON-serializable.** On a durable backend, a non-serializable argument raises `TaskSerializationFault` at `enqueue()`. Audit your enqueue calls for ORM instances, file handles, and custom objects:

```python
# Breaks on a durable backend
await tasks.enqueue(send_welcome, user)          # ORM instance

# Correct
await tasks.enqueue(send_welcome, user.id)       # worker re-loads it
```

**Every worker must import every task module.** Workers resolve jobs by registered name. A worker process that has not imported the module defining a task raises `TaskResolutionFault` for that job. Declaring tasks in your module manifests handles this automatically.

**Task functions should be idempotent.** Distributed backends are at-least-once: a worker that stalls past its lease can have its job reclaimed and run twice.

See [Distributed & Persistent Backends](distributed_tasks.md).

---

## Migration 2 — Replace Hand-Rolled Deduplication

### Before

```python
lock_key = f"job:invoice:{order_id}"
if await redis.set(lock_key, "1", nx=True, ex=3600):
    await tasks.enqueue(send_invoice, order_id)
```

### After

```python
await tasks.enqueue(send_invoice, order_id, dedup="skip")
```

The framework version releases the reservation when the job reaches a terminal state, so a failed job can be retried immediately rather than being blocked until the TTL expires.

Use `dedup="raise"` where a duplicate indicates a caller bug:

```python
from aquilia.tasks import TaskDuplicateFault

try:
    await tasks.enqueue(charge_card, order_id, dedup="raise")
except TaskDuplicateFault:
    return Response.json({"status": "already_processing"}, status=409)
```

The default remains `"allow"`, so nothing changes until you opt in.

See [Idempotency & Deduplication](idempotency.md).

---

## Migration 3 — Replace Ad-Hoc Job Sequencing

### Before

```python
# One long-lived job orchestrating the rest — lost on restart,
# and holding a worker slot while doing nothing
@task(name="pipeline")
async def pipeline(source):
    rows = await extract(source)
    cleaned = await clean(rows)
    await load(cleaned)
```

### After

```python
from aquilia.tasks.workflow import chain

await chain(
    extract.s(source),
    clean.s().with_parent_results(),
    load.s().with_parent_results(),
).run(tasks)
```

Each step is an independent job with its own retry budget. The graph is durable the moment it is submitted, so a restart resumes rather than restarting from the top. A `WAITING` step occupies no worker slot.

See [Workflows & DAGs](workflows.md).

---

## Migration 4 — Background Mail Delivery

### Before

```python
Integration.mail(default_from="noreply@example.com", providers=[...])
```

`asend()` performed the SMTP conversation inside the request. Response time was tied to provider latency.

### After

```python
Integration.tasks(backend="redis", redis_url="redis://cache:6379/0")

Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
    queue_persistent=True,
)
```

**Call sites do not change.** `EmailMessage(...).asend()` still returns an envelope ID; it now returns before delivery completes.

### What you must check

**Code that assumed mail was sent on return.** With the queue enabled, a returned envelope ID means *accepted*, not *delivered*. Poll status where that distinction matters:

```python
envelope = await mail.store.get(envelope_id)
envelope.status   # QUEUED → SENDING → SENT / FAILED / BOUNCED / CANCELLED
```

**Tests asserting on a mail outbox.** Tests that send through a queued service must drive the task manager, or configure the mail service without `queue_enabled` for that test.

**`queue_persistent=True` requires `Integration.database(...)`.** Without a reachable database, mail logs an error and falls back to in-memory stores.

See [Mail Delivery Queue](mail_queue.md).

---

## Migration 5 — Bounce Handling

New capability; there is nothing to migrate from. Add a webhook endpoint:

```python
from aquilia import Controller, POST, RequestCtx, Response
from aquilia.mail import parse_ses, process_webhook

class MailWebhookController(Controller):
    prefix = "/webhooks/mail"

    @POST("/ses")
    async def ses(self, ctx: RequestCtx):
        events = parse_ses(await ctx.body(), verify_topic_arn=SES_TOPIC_ARN)
        return Response.json(await process_webhook(
            events,
            suppression=self.mail.suppression,
            store=self.mail.store,
        ))
```

Two things to get right:

- **Verify signatures.** Pass `verify_topic_arn` (SES), `public_key` (SendGrid), or `signing_key` (Mailgun). An unverified endpoint lets anyone forge a bounce and suppress an arbitrary address.
- **Exempt the path from CSRF.** Providers do not carry your CSRF token; signature verification is the authenticity check.

If you already maintain a suppression list in your own tables, import it:

```python
for row in await LegacySuppression.all():
    await mail.suppression.suppress(row.email, reason=SuppressionReason.HARD_BOUNCE)
```

See [Bounce Handling & Suppression](bounces_suppression.md).

---

## Migration 6 — Job Result Handling

If you worked around results arriving as `repr` strings on a persistent backend, remove the workaround:

```python
# Before — parsing the repr form back
total = sum(int(r) for r in parent_results)

# After — JSON-safe values round-trip intact
total = sum(parent_results)
```

Values that are not JSON-serializable still arrive as `repr` strings, which is unavoidable — return dicts, lists, and primitives from steps whose results are consumed downstream.

See [Bug Fixes](bugfixes.md).

---

## Deprecated Features

None. No API was deprecated in this release.

## Removed Features

None.

## Breaking Changes

None.

The one behavior change worth noting is not an API break: with `dkim_enabled=True` and an incomplete configuration, sends now fail rather than shipping unsigned mail. Run `aq mail check` after enabling DKIM. See [CLI Changes](cli.md).

---

## Compatibility Notes

| Area | Notes |
|---|---|
| Python | 3.10–3.13, unchanged |
| Existing manifests | No changes required |
| `MemoryBackend` | Behavior unchanged; still the default |
| Inline mail | Behavior unchanged; still the default |
| `TaskManager.enqueue()` | New keyword-only params, all defaulted to prior behavior |
| `MailService` | New `store` / `suppression` attributes; constructor arguments still win |
| Task result values | JSON-safe values now round-trip; previously `repr` on persistent backends |

---

## Known Issues

- **Redis backend lacks automated test coverage** in this release; the SQL backend carries the durable-path integration tests. The Redis implementation is exercised manually and by the shared backend contract.
- **Mailgun signature verification is opt-in.** Omitting `signing_key` parses without verification and logs a warning. Treat it as required in production.
- **No built-in webhook route.** Applications wire `parse_*` and `process_webhook` into their own controller, so path, authentication, and CSRF policy stay under application control.
- **Workflow steps whose parent failed remain `WAITING`** rather than being cancelled. They will not run; inspect them with `failed_jobs()`.

---

## Related

- [Release Overview](README.md)
- [Distributed & Persistent Backends](distributed_tasks.md)
- [Workflows & DAGs](workflows.md)
- [Idempotency & Deduplication](idempotency.md)
- [Mail Delivery Queue](mail_queue.md)
- [Bounce Handling & Suppression](bounces_suppression.md)
- [Mail Security & MIME](mail_security.md)
- [CLI Changes](cli.md)
- [Bug Fixes](bugfixes.md)
