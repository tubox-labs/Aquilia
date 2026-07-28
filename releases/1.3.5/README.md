# Aquilia v1.3.5 Release Notes — "Distributed Tide"

Aquilia v1.3.5 makes the background task system genuinely distributed and durable, and turns the mail subsystem into a production-grade delivery pipeline.

Before this release, background tasks ran in a single process on an in-memory queue — jobs were lost on restart, a second web worker meant a second independent queue, and `backend="redis"` was accepted by configuration and then silently ignored. Mail was sent inline inside the request handler, with no bounce handling and no suppression list.

This release closes both gaps: jobs now execute across multiple worker processes and multiple machines with lease-based coordination and crash recovery; job state survives restarts on Redis or SQL; jobs compose into chains, groups, chords, and arbitrary DAGs; duplicate enqueues are collapsed by an enforced fingerprint; and mail is delivered by background workers with provider webhook processing and automatic suppression of bounced and complaining recipients.

All of it is backward compatible. Change no configuration and v1.3.5 behaves exactly as v1.3.4 did.

---

## Table of Contents

1. [Distributed & Persistent Task Backends](distributed_tasks.md)
   - `RedisBackend` — atomic Lua claim, `SET NX` fingerprint reservation
   - `SQLBackend` — durable queue on the application's own database
   - Lease-based claiming, heartbeat renewal, and crash recovery
   - `Job.to_payload()` / `Job.from_payload()` transport serialization
   - Registry-based callable resolution across process boundaries
2. [Workflows & DAGs](workflows.md)
   - `Signature`, `Workflow`, `WorkflowResult`
   - `chain` (sequential), `group` (parallel), `chord` (fan-in)
   - Arbitrary DAGs via `depends_on`
   - `with_parent_results()` continuation passing
   - Cycle and unknown-dependency validation
3. [Idempotency & Distributed Deduplication](idempotency.md)
   - `Job.fingerprint` finally enforced
   - `dedup="allow" | "skip" | "raise"`
   - Cross-process locking via Redis `SET NX` and a SQL unique constraint
4. [Mail Delivery Queue](mail_queue.md)
   - `EnvelopeStore` — `MemoryEnvelopeStore` and `SQLEnvelopeStore`
   - Background delivery through the existing task scheduler
   - Envelope-ID-only jobs, designed for distributed workers
   - Send-time deduplication by idempotency key and content digest
5. [Bounce Handling, Webhooks & Suppression](bounces_suppression.md)
   - `parse_ses`, `parse_sendgrid`, `parse_mailgun` with signature verification
   - `process_webhook` applying bounces and complaints
   - `SuppressionList` — permanent and TTL suppression, enforced on send
6. [Mail Security, MIME & Templates](mail_security.md)
   - Shared MIME assembly across every provider
   - Real DKIM signing at the byte level
   - XOAUTH2 authentication, TLS enforcement, PII redaction
   - ATS template filters and autoescaping
7. [CLI Changes](cli.md)
   - `aq mail check` validates DKIM configuration
8. [Bug Fixes](bugfixes.md)
   - Mail delivery task unresolvable across processes (CRITICAL)
   - Consumer-only workers polled nothing (CRITICAL)
   - Job results degraded to `repr` strings on persistent backends
   - `queue.persistent` had no configuration surface
9. [Migration Guide](migration.md)
   - Upgrade checklist, per-feature migrations, compatibility notes, known issues

---

## Highlights

### Distributed execution with crash recovery

A worker claims a job under a time-bounded lease and renews it by heartbeat. If the worker dies, the lease lapses and a peer reclaims the job instead of the job being lost.

```python
# workspace.py — production
Integration.tasks(
    backend="redis",
    redis_url="redis://cache:6379/0",
    num_workers=16,
    lease_seconds=120,
)
```

Task code is unchanged between backends. Switching is configuration, not a rewrite.

### Workflows

```python
from aquilia.tasks.workflow import chain, chord

# Sequential, each step fed by the previous
await chain(
    extract.s(source),
    transform.s().with_parent_results(),
    load.s().with_parent_results(),
).run(tasks)

# Parallel shards, then a fan-in callback
await chord(
    [shard.s(n) for n in range(8)],
    merge.s().with_parent_results(),
).run(tasks)
```

The graph is durable the moment it is submitted. No orchestrator process, and a `WAITING` step holds no worker slot.

### Enforced idempotency

```python
# Ten identical requests; one job.
await tasks.enqueue(rebuild_index, dedup="skip")
```

Correctness comes from the storage layer — Redis `SET NX`, or a SQL primary-key constraint — so two racing processes produce one job.

### Background mail delivery

```python
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
    queue_persistent=True,
)
```

`asend()` returns as soon as the envelope is stored. Delivery, retries, and backoff run on a worker — reusing the task scheduler rather than introducing a second queue.

### Automatic bounce suppression

```python
events = parse_ses(await ctx.body(), verify_topic_arn=SES_TOPIC_ARN)
await process_webhook(events, suppression=mail.suppression, store=mail.store)
```

A hard bounce or spam complaint removes the address from every future send, protecting sender reputation without application code.

---

## What's New

| Capability | Summary |
|---|---|
| `RedisBackend` | Distributed, durable task queue with atomic Lua claim |
| `SQLBackend` | Durable task queue on the existing application database |
| `Job.to_payload()` / `from_payload()` | JSON transport form with fail-at-enqueue validation |
| `Workflow`, `Signature`, `WorkflowResult` | Job graphs with dependencies |
| `chain`, `group`, `chord` | Sequential, parallel, and fan-in composition |
| `dedup="skip" \| "raise"` | Enforced fingerprint deduplication |
| `TaskDuplicateFault`, `TaskSerializationFault`, `TaskBackendFault`, `TaskWorkflowFault` | New structured faults |
| `EnvelopeStore` | Durable record of accepted mail |
| `SuppressionList` | Bounce and complaint suppression, enforced on send |
| `parse_ses` / `parse_sendgrid` / `parse_mailgun` | Provider webhook parsing with signature verification |
| `process_webhook` | Applies delivery events to suppression and envelope status |
| `build_mime_message` / `message_to_bytes` / `sign_dkim` | Shared MIME assembly and DKIM signing |
| `redact_email` / `redact_pii` | PII redaction for mail logs |
| `MailAuth.oauth2(...)` | XOAUTH2 bearer-token SMTP authentication |
| `aquilia[mail-dkim]` | New optional extra for DKIM signing |

---

## Major Improvements

- **Backend selection is honest.** `backend="redis"` used to log a warning and fall back to in-memory. It now builds a real Redis backend; only an unknown backend name or an unreachable service falls back, and both say so loudly.
- **Serialization fails at the call site.** A non-JSON argument raises `TaskSerializationFault` at `enqueue()`, not on a remote worker hours later.
- **Queue discovery.** A consumer-only worker polls the queues declared by its `@task` descriptors, plus any queue it discovers on the shared backend.
- **Mail providers share one MIME implementation.** Header handling, attachments, and tracking headers no longer drift between SMTP, SES, SendGrid, and the development backends.
- **Graceful degradation everywhere.** An unreachable Redis, database, or DKIM dependency degrades with an error naming exactly what was lost, rather than aborting startup.

---

## Performance Improvements

- Mail moves off the request path entirely: a full SMTP conversation becomes one store write plus one enqueue.
- Workflow steps in `WAITING` consume no worker slot, replacing the pattern of a long-lived job blocking on its children.
- `dedup="skip"` collapses duplicate work before it executes — the cheapest possible optimization for a burst of identical requests.
- `MemoryBackend` is untouched; single-process applications see no change.
- `SQLBackend` claim is a single conditional `UPDATE` in a transaction; `RedisBackend` claim is one round trip against a sorted set.

---

## Developer Experience Improvements

- One mental model for background work: mail delivery is an ordinary task on an ordinary queue, visible in the admin dashboard alongside everything else.
- `aq mail check` catches DKIM misconfiguration before the first send fails.
- Structured faults name the failure precisely — `TaskSerializationFault` reports which argument, `TaskWorkflowFault` names the cycle.
- The `aquilia.tasks` package docstring no longer claims distributed backends and workflows are unimplemented.

---

## Security Improvements

- **Webhook signature verification** for SES (topic ARN), SendGrid (ECDSA public key), and Mailgun (HMAC signing key), with replay rejection via a timestamp window. Without it, anyone can forge a bounce and suppress an arbitrary address.
- **DKIM signing** applied at the byte level immediately before transmission, covering exactly what the provider receives. Failures raise rather than shipping unsigned mail.
- **TLS enforcement** on SMTP remains on by default.
- **PII redaction** masks recipient local parts in logs while preserving domains.
- **Registry-only callable resolution** means a queue entry can never name a function the application did not register — a durable queue is not an arbitrary-code-execution channel.
- **Parameterized SQL throughout** the new backends and stores; table and column identifiers are validated against a restricted character set.

---

## Bug Fixes

| Issue | Subsystem | Fix |
|---|---|---|
| Mail delivery task unresolvable across processes | Mail / Tasks | Delivery registered as `@task(name="aquilia.mail.deliver")`; workers resolve it by stable name. |
| Consumer-only workers polled nothing | Tasks | Queues seeded from `@task` descriptors and refreshed from `backend.get_queue_stats()`. |
| Job results degraded to `repr` strings | Tasks | JSON-safe values round-trip; only non-serializable values fall back to `repr`. |
| `queue.persistent` had no config surface | Mail | Threaded through `Integration.mail`, `MailIntegration`, `QueueConfigContract`, and store selection. |
| `Job.fingerprint` computed but never read | Tasks | Enforced at enqueue via `dedup`. |
| `MailSuppressedFault` unreachable | Mail | Now part of a working suppression path. |
| Stale package docstring | Tasks | No longer lists shipped features as "deliberately absent". |

---

## Breaking Changes

None. See [Migration Guide](migration.md).

---

## Deprecated / Removed

Nothing was deprecated or removed in this release.

---

## Internal Refactoring

- MIME assembly extracted from four providers into `aquilia/mail/mime.py`.
- PII redaction extracted into `aquilia/mail/redaction.py`.
- The `TaskBackend` ABC gained `heartbeat`, `reclaim_expired`, `reserve_fingerprint`, `release_fingerprint`, and `get_dependency_results`, so `MemoryBackend` and the durable backends satisfy one contract.
- SMTP provider restructured around shared MIME assembly, byte-level signing, and pluggable authentication.

---

## Compatibility

| Area | Status |
|---|---|
| Python 3.10–3.13 | Supported, unchanged |
| Existing workspaces and manifests | No changes required |
| Existing `@task` functions | No changes required |
| Existing mail call sites | No changes required |
| Default behavior | Identical to v1.3.4 |

---

## Known Issues

- The Redis backend has no automated test coverage in this release; the SQL backend carries the durable-path integration tests.
- Mailgun signature verification is opt-in and warns when omitted.
- No built-in webhook route ships; applications wire the parsers into their own controller.
- Workflow steps whose parent failed remain `WAITING` rather than being cancelled.

Details and workarounds in the [Migration Guide](migration.md#known-issues).

---

## Testing

`tests/test_tasks_mail_enterprise.py` adds 43 tests covering job serialization, deduplication semantics, workflow composition and validation, durable-backend behavior driven against real SQLite (restart survival, cross-process queue discovery, cross-manager deduplication, lease reclaim), the mail delivery queue, suppression, webhook parsing and processing, and template autoescaping.

`tests/test_audit_tasks_mail.py` covers the mail provider, DKIM, MIME, redaction, and rate-limiting paths.

Full suite: 7,189 passing.

---

## Credits

Thanks to everyone who reported that `backend="redis"` did not do anything.
