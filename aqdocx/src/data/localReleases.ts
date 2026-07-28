export const localReleases: Record<string, Record<string, string>> = {
  "1.3.5": {
    "README.md": `# Aquilia v1.3.5 Release Notes — "Distributed Tide"

Aquilia v1.3.5 makes the background task system genuinely distributed and durable, and turns the mail subsystem into a production-grade delivery pipeline.

Before this release, background tasks ran in a single process on an in-memory queue — jobs were lost on restart, a second web worker meant a second independent queue, and \`backend="redis"\` was accepted by configuration and then silently ignored. Mail was sent inline inside the request handler, with no bounce handling and no suppression list.

This release closes both gaps: jobs now execute across multiple worker processes and multiple machines with lease-based coordination and crash recovery; job state survives restarts on Redis or SQL; jobs compose into chains, groups, chords, and arbitrary DAGs; duplicate enqueues are collapsed by an enforced fingerprint; and mail is delivered by background workers with provider webhook processing and automatic suppression of bounced and complaining recipients.

All of it is backward compatible. Change no configuration and v1.3.5 behaves exactly as v1.3.4 did.

---

## Table of Contents

1. [Distributed & Persistent Task Backends](distributed_tasks.md)
   - \`RedisBackend\` — atomic Lua claim, \`SET NX\` fingerprint reservation
   - \`SQLBackend\` — durable queue on the application's own database
   - Lease-based claiming, heartbeat renewal, and crash recovery
   - \`Job.to_payload()\` / \`Job.from_payload()\` transport serialization
   - Registry-based callable resolution across process boundaries
2. [Workflows & DAGs](workflows.md)
   - \`Signature\`, \`Workflow\`, \`WorkflowResult\`
   - \`chain\` (sequential), \`group\` (parallel), \`chord\` (fan-in)
   - Arbitrary DAGs via \`depends_on\`
   - \`with_parent_results()\` continuation passing
   - Cycle and unknown-dependency validation
3. [Idempotency & Distributed Deduplication](idempotency.md)
   - \`Job.fingerprint\` finally enforced
   - \`dedup="allow" | "skip" | "raise"\`
   - Cross-process locking via Redis \`SET NX\` and a SQL unique constraint
4. [Mail Delivery Queue](mail_queue.md)
   - \`EnvelopeStore\` — \`MemoryEnvelopeStore\` and \`SQLEnvelopeStore\`
   - Background delivery through the existing task scheduler
   - Envelope-ID-only jobs, designed for distributed workers
   - Send-time deduplication by idempotency key and content digest
5. [Bounce Handling, Webhooks & Suppression](bounces_suppression.md)
   - \`parse_ses\`, \`parse_sendgrid\`, \`parse_mailgun\` with signature verification
   - \`process_webhook\` applying bounces and complaints
   - \`SuppressionList\` — permanent and TTL suppression, enforced on send
6. [Mail Security, MIME & Templates](mail_security.md)
   - Shared MIME assembly across every provider
   - Real DKIM signing at the byte level
   - XOAUTH2 authentication, TLS enforcement, PII redaction
   - ATS template filters and autoescaping
7. [Native HTTP Client & Dependency Cleanup](http_native.md)
   - Zero third-party HTTP client dependencies (\`httpx\` removed)
   - \`SendGridProvider\` and \`LiveServerTestCase\` updated to \`aquilia.http\`
8. [CLI Changes](cli.md)
   - \`aq mail check\` validates DKIM configuration
9. [Bug Fixes](bugfixes.md)
   - Mail delivery task unresolvable across processes (CRITICAL)
   - Consumer-only workers polled nothing (CRITICAL)
   - Job results degraded to \`repr\` strings on persistent backends
   - \`queue.persistent\` had no configuration surface
10. [Migration Guide](migration.md)
   - Upgrade checklist, per-feature migrations, compatibility notes, known issues

---

## Highlights

### Distributed execution with crash recovery

A worker claims a job under a time-bounded lease and renews it by heartbeat. If the worker dies, the lease lapses and a peer reclaims the job instead of the job being lost.

\`\`\`python
# workspace.py — production
Integration.tasks(
    backend="redis",
    redis_url="redis://cache:6379/0",
    num_workers=16,
    lease_seconds=120,
)
\`\`\`

Task code is unchanged between backends. Switching is configuration, not a rewrite.

### Workflows

\`\`\`python
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
\`\`\`

The graph is durable the moment it is submitted. No orchestrator process, and a \`WAITING\` step holds no worker slot.

### Enforced idempotency

\`\`\`python
# Ten identical requests; one job.
await tasks.enqueue(rebuild_index, dedup="skip")
\`\`\`

Correctness comes from the storage layer — Redis \`SET NX\`, or a SQL primary-key constraint — so two racing processes produce one job.

### Background mail delivery

\`\`\`python
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
    queue_persistent=True,
)
\`\`\`

\`asend()\` returns as soon as the envelope is stored. Delivery, retries, and backoff run on a worker — reusing the task scheduler rather than introducing a second queue.

### Automatic bounce suppression

\`\`\`python
events = parse_ses(await ctx.body(), verify_topic_arn=SES_TOPIC_ARN)
await process_webhook(events, suppression=mail.suppression, store=mail.store)
\`\`\`

A hard bounce or spam complaint removes the address from every future send, protecting sender reputation without application code.

---

## What's New

| Capability | Summary |
|---|---|
| \`RedisBackend\` | Distributed, durable task queue with atomic Lua claim |
| \`SQLBackend\` | Durable task queue on the existing application database |
| \`Job.to_payload()\` / \`from_payload()\` | JSON transport form with fail-at-enqueue validation |
| \`Workflow\`, \`Signature\`, \`WorkflowResult\` | Job graphs with dependencies |
| \`chain\`, \`group\`, \`chord\` | Sequential, parallel, and fan-in composition |
| \`dedup="skip" \\| "raise"\` | Enforced fingerprint deduplication |
| \`TaskDuplicateFault\`, \`TaskSerializationFault\`, \`TaskBackendFault\`, \`TaskWorkflowFault\` | New structured faults |
| \`EnvelopeStore\` | Durable record of accepted mail |
| \`SuppressionList\` | Bounce and complaint suppression, enforced on send |
| \`parse_ses\` / \`parse_sendgrid\` / \`parse_mailgun\` | Provider webhook parsing with signature verification |
| \`process_webhook\` | Applies delivery events to suppression and envelope status |
| \`build_mime_message\` / \`message_to_bytes\` / \`sign_dkim\` | Shared MIME assembly and DKIM signing |
| \`redact_email\` / \`redact_pii\` | PII redaction for mail logs |
| \`MailAuth.oauth2(...)\` | XOAUTH2 bearer-token SMTP authentication |
| \`aquilia[mail-dkim]\` | New optional extra for DKIM signing |

---

## Major Improvements

- **Backend selection is honest.** \`backend="redis"\` used to log a warning and fall back to in-memory. It now builds a real Redis backend; only an unknown backend name or an unreachable service falls back, and both say so loudly.
- **Serialization fails at the call site.** A non-JSON argument raises \`TaskSerializationFault\` at \`enqueue()\`, not on a remote worker hours later.
- **Queue discovery.** A consumer-only worker polls the queues declared by its \`@task\` descriptors, plus any queue it discovers on the shared backend.
- **Mail providers share one MIME implementation.** Header handling, attachments, and tracking headers no longer drift between SMTP, SES, SendGrid, and the development backends.
- **Graceful degradation everywhere.** An unreachable Redis, database, or DKIM dependency degrades with an error naming exactly what was lost, rather than aborting startup.

---

## Performance Improvements

- Mail moves off the request path entirely: a full SMTP conversation becomes one store write plus one enqueue.
- Workflow steps in \`WAITING\` consume no worker slot, replacing the pattern of a long-lived job blocking on its children.
- \`dedup="skip"\` collapses duplicate work before it executes — the cheapest possible optimization for a burst of identical requests.
- \`MemoryBackend\` is untouched; single-process applications see no change.
- \`SQLBackend\` claim is a single conditional \`UPDATE\` in a transaction; \`RedisBackend\` claim is one round trip against a sorted set.

---

## Developer Experience Improvements

- One mental model for background work: mail delivery is an ordinary task on an ordinary queue, visible in the admin dashboard alongside everything else.
- \`aq mail check\` catches DKIM misconfiguration before the first send fails.
- Structured faults name the failure precisely — \`TaskSerializationFault\` reports which argument, \`TaskWorkflowFault\` names the cycle.
- The \`aquilia.tasks\` package docstring no longer claims distributed backends and workflows are unimplemented.

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
| Mail delivery task unresolvable across processes | Mail / Tasks | Delivery registered as \`@task(name="aquilia.mail.deliver")\`; workers resolve it by stable name. |
| Consumer-only workers polled nothing | Tasks | Queues seeded from \`@task\` descriptors and refreshed from \`backend.get_queue_stats()\`. |
| Job results degraded to \`repr\` strings | Tasks | JSON-safe values round-trip; only non-serializable values fall back to \`repr\`. |
| \`queue.persistent\` had no config surface | Mail | Threaded through \`Integration.mail\`, \`MailIntegration\`, \`QueueConfigContract\`, and store selection. |
| \`Job.fingerprint\` computed but never read | Tasks | Enforced at enqueue via \`dedup\`. |
| \`MailSuppressedFault\` unreachable | Mail | Now part of a working suppression path. |
| Stale package docstring | Tasks | No longer lists shipped features as "deliberately absent". |

---

## Breaking Changes

None. See [Migration Guide](migration.md).

---

## Deprecated / Removed

Nothing was deprecated or removed in this release.

---

## Internal Refactoring

- MIME assembly extracted from four providers into \`aquilia/mail/mime.py\`.
- PII redaction extracted into \`aquilia/mail/redaction.py\`.
- The \`TaskBackend\` ABC gained \`heartbeat\`, \`reclaim_expired\`, \`reserve_fingerprint\`, \`release_fingerprint\`, and \`get_dependency_results\`, so \`MemoryBackend\` and the durable backends satisfy one contract.
- SMTP provider restructured around shared MIME assembly, byte-level signing, and pluggable authentication.

---

## Compatibility

| Area | Status |
|---|---|
| Python 3.10–3.13 | Supported, unchanged |
| Existing workspaces and manifests | No changes required |
| Existing \`@task\` functions | No changes required |
| Existing mail call sites | No changes required |
| Default behavior | Identical to v1.3.4 |

---

## Known Issues

- The Redis backend has no automated test coverage in this release; the SQL backend carries the durable-path integration tests.
- Mailgun signature verification is opt-in and warns when omitted.
- No built-in webhook route ships; applications wire the parsers into their own controller.
- Workflow steps whose parent failed remain \`WAITING\` rather than being cancelled.

Details and workarounds in the [Migration Guide](migration.md#known-issues).

---

## Testing

\`tests/test_tasks_mail_enterprise.py\` adds 43 tests covering job serialization, deduplication semantics, workflow composition and validation, durable-backend behavior driven against real SQLite (restart survival, cross-process queue discovery, cross-manager deduplication, lease reclaim), the mail delivery queue, suppression, webhook parsing and processing, and template autoescaping.

\`tests/test_audit_tasks_mail.py\` covers the mail provider, DKIM, MIME, redaction, and rate-limiting paths.

Full suite: 7,189 passing.

---

## Credits

Thanks to everyone who reported that \`backend="redis"\` did not do anything.
`,
    "bounces_suppression.md": `# Bounce Handling, Webhooks & Suppression Lists — Aquilia v1.3.5

Provider delivery events are now parsed, verified, and applied. A hard bounce or spam complaint automatically removes the address from all future sends. Before this release, \`MailSuppressedFault\` existed in the fault taxonomy but nothing raised it — there was no suppression list and no webhook handling at all.

---

## Motivation

Deliverability is reputation, and reputation is destroyed by continuing to mail addresses that bounce. Every ESP tracks bounce and complaint rates; exceed their thresholds and legitimate mail starts landing in spam or being rejected outright.

Handling this correctly requires three things Aquilia did not have: parsing each provider's webhook format, verifying those webhooks are genuine, and a persistent list consulted on every send.

---

## Architecture

\`\`\`
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
\`\`\`

---

## Webhook Parsing

Three provider parsers normalize into one vocabulary:

\`\`\`python
from aquilia.mail import parse_ses, parse_sendgrid, parse_mailgun

parse_ses(payload, *, verify_topic_arn=None)
parse_sendgrid(payload, *, headers=None, public_key=None, max_age_seconds=600.0)
parse_mailgun(payload, *, signing_key=None, max_age_seconds=600.0)
\`\`\`

Each returns \`list[WebhookEvent]\`:

\`\`\`python
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
\`\`\`

\`EventType\` normalizes each provider's vocabulary: \`DELIVERED\`, \`HARD_BOUNCE\`, \`SOFT_BOUNCE\`, \`COMPLAINT\`, \`REJECTED\`, \`OPENED\`, \`CLICKED\`, \`UNSUBSCRIBED\`, \`DEFERRED\`, \`UNKNOWN\`. An unrecognized event becomes \`UNKNOWN\` and is preserved rather than dropped, so a provider adding a new type stays visible.

### Signature verification

**Verify webhooks in production.** An unverified endpoint lets anyone POST a forged bounce and suppress an arbitrary address — a trivial denial-of-service against your own users.

- **SES** — pass \`verify_topic_arn\` to reject notifications from any other SNS topic.
- **SendGrid** — pass \`public_key\` (the ECDSA verification key from your SendGrid settings) with the request \`headers\`. Replays older than \`max_age_seconds\` are rejected.
- **Mailgun** — pass \`signing_key\`. The HMAC signature and timestamp are verified.

Omitting these parameters parses without verification and logs a warning naming the risk.

---

## Suppression Lists

\`\`\`python
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
\`\`\`

| Reason | Permanence |
|---|---|
| \`HARD_BOUNCE\` | Permanent — the address does not exist |
| \`SOFT_BOUNCE\` | Expires (defaults to 24 hours) — mailbox full, server down |
| \`COMPLAINT\` | Permanent — the most reputation-damaging signal a provider tracks |
| \`UNSUBSCRIBE\` | Permanent |
| \`MANUAL\` | Permanent — operator-added |

Two implementations ship: \`MemorySuppressionList\` (default) and \`SQLSuppressionList\` (table \`aquilia_mail_suppressions\`, selected by \`queue_persistent=True\`).

Addresses are normalized — lowercased and trimmed — before storage and lookup, so \`User@Example.COM\` and \` user@example.com \` are the same entry.

---

## Wiring a Webhook Endpoint

Aquilia does not register a webhook route for you; the path, authentication, and CSRF exemption belong to the application. The handler is a few lines:

\`\`\`python
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
\`\`\`

Exempt the webhook path from CSRF — providers do not carry your CSRF token. Rely on signature verification for authenticity instead.

---

## Enforcement on Send

\`MailService\` consults the suppression list while preparing every envelope. Suppressed recipients are removed; if *every* recipient is suppressed the envelope is marked \`CANCELLED\` and no delivery is attempted.

\`\`\`python
await mail.suppression.suppress("bounced@example.com", reason=SuppressionReason.HARD_BOUNCE)

envelope_id = await EmailMessage(subject="Hi", body="x", to="bounced@example.com").asend()
envelope = await mail.store.get(envelope_id)
envelope.status    # EnvelopeStatus.CANCELLED
\`\`\`

---

## Edge Cases

**Partial suppression.** An envelope with three recipients where one is suppressed sends to the remaining two. Only an envelope with no deliverable recipients is cancelled.

**Soft bounce TTL.** \`process_webhook\` suppresses soft bounces for \`soft_bounce_ttl\` (default 86,400 seconds) rather than permanently, since the cause is usually transient. Tune it per provider.

**Events with no address.** Counted as \`ignored\` rather than raising — a malformed event should not fail the whole batch.

**Non-suppressing events.** \`DELIVERED\`, \`OPENED\`, \`CLICKED\`, and \`DEFERRED\` update envelope status where applicable but never suppress.

**Malformed payloads.** A body that is not valid JSON raises \`MailFault\`, so a broken request surfaces as a 4xx rather than being silently swallowed.

**Envelope correlation.** Providers that echo custom headers return \`X-Aquilia-Envelope-ID\`, letting an event update the exact envelope. Providers that do not echo headers still suppress by address; the envelope simply is not correlated.

---

## Performance Implications

One suppression lookup per envelope on the send path. \`MemorySuppressionList\` is a dict lookup. \`SQLSuppressionList\` is an indexed primary-key read; \`filter_recipients\` batches a multi-recipient envelope rather than issuing one query per address.

Webhook processing is O(n) in events, with one suppression write per suppressing event.

---

## Compatibility

Purely additive. \`MailService.suppression\` defaults to an empty \`MemorySuppressionList\`, so no address is suppressed until a webhook or an operator adds one — existing applications see no behavioral change. \`MailSuppressedFault\`, previously unreachable, is now part of a working path.

---

## Related

- [Mail Delivery Queue](mail_queue.md)
- [Mail Security & MIME](mail_security.md)
- [Migration Guide](migration.md)
`,
    "bugfixes.md": `# Bug Fixes — Aquilia v1.3.5

Four defects were found and fixed while auditing the enterprise task and mail work. Three would only surface once a durable or distributed backend was in use — which is exactly what this release enables, so each would have been a first-day production failure for anyone adopting the new capability.

---

## 1. Mail delivery task unresolvable across processes

**Severity:** Critical, on any persistent backend.

### Previous behavior

Background mail delivery enqueued a plain module-level function. On \`MemoryBackend\` this worked, because the job carried the live callable in-process.

The moment a durable backend was configured, delivery stopped. The job serialized to a module-path reference, and the consuming worker — which resolves callables through the \`@task\` registry rather than importing arbitrary paths — could not resolve it. Envelopes sat in \`QUEUED\` forever. Nothing crashed loudly; mail simply never arrived.

### Root cause

\`_deliver_envelope_task\` was a bare \`async def\`, never registered with \`@task\`. Worker resolution goes through \`get_task(job.func_ref)\`, which only knows about registered descriptors. This is a deliberate security property — a queue entry must not be able to name arbitrary importable code — but it means an unregistered function is unreachable.

### New behavior

The delivery task is registered under a stable name:

\`\`\`python
@task(name="aquilia.mail.deliver", queue=MailService.retry_queue, max_retries=0)
async def _deliver_envelope_task(envelope_id: str) -> None: ...
\`\`\`

A worker in any process resolves it by name. The name is stable, so a future rename of the Python function does not orphan jobs already in the queue.

### User impact

Anyone enabling \`queue_enabled=True\` together with \`backend="redis"\` or \`backend="sql"\` would have had silently undelivered mail. Fixed before either capability shipped.

---

## 2. Consumer-only workers polled nothing

**Severity:** Critical, for distributed deployments.

### Previous behavior

A dedicated worker process — one that consumes jobs but never enqueues any — processed nothing. Jobs queued by web workers on any queue other than \`default\` were ignored indefinitely.

### Root cause

\`TaskManager._queues\` was populated exclusively as a side effect of \`enqueue()\`. A process that never enqueues therefore knew about exactly one queue: its configured \`default_queue\`. The worker loop iterates the known queue set, so work on \`mail\`, \`reports\`, or any other queue was invisible to it.

This was harmless while everything ran in one process — the enqueuer and the worker were the same object. It becomes fatal the moment producer and consumer are separate processes, which is the entire point of a distributed backend.

### New behavior

Two additions:

1. \`_bind_task_descriptors()\` registers the queue of every \`@task\` descriptor, so importing a task module is enough to poll its queue.
2. On a distributed backend, the manager adopts queues reported by \`backend.get_queue_stats()\` at startup and refreshes them on each reclaim tick — so a queue created by a peer after startup is picked up.

### User impact

Dedicated worker processes now consume the queues their producers use, without needing to be told which those are.

---

## 3. Job results degraded to repr strings on persistent backends

**Severity:** High — silent data corruption in workflows.

### Previous behavior

\`\`\`python
# In-process
job.result.value    # 4  (int)

# Same job on a SQL or Redis backend
job.result.value    # '4'  (str)
\`\`\`

A chord callback consuming \`parent_results\` received \`['4', '6']\` instead of \`[4, 6]\`. Arithmetic silently produced string concatenation or a \`TypeError\` far from the cause.

### Root cause

\`JobResult.to_dict()\` serialized unconditionally with \`repr(self.value)\`. The rationale — an arbitrary return value is not guaranteed to be JSON-compatible — was sound, but the blanket application destroyed values that serialize perfectly well.

### New behavior

JSON-safe values round-trip unchanged; only genuinely non-serializable values fall back to \`repr\`:

\`\`\`python
value = self.value
if value is not None:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        value = repr(value)
\`\`\`

### User impact

Workflow fan-in receives real values on every backend. Applications that had adapted to the string form — parsing \`repr\` output back — should remove that workaround.

\`\`\`python
# Before — workaround
total = sum(int(r) for r in parent_results)

# After
total = sum(parent_results)
\`\`\`

---

## 4. \`queue.persistent\` had no configuration surface or wiring

**Severity:** Medium — an advertised capability that could not be reached.

### Previous behavior

\`SQLEnvelopeStore\` and \`SQLSuppressionList\` existed and worked, but nothing constructed them from configuration. The only way to get durable mail state was to instantiate the stores by hand and pass them to \`MailService(store=..., suppression=...)\`. The \`queue\` config block had no \`persistent\` key at all, so setting it in \`workspace.py\` was silently dropped by contract validation.

### New behavior

\`persistent\` is a real config field, threaded end to end:

- \`Integration.mail(queue_persistent=True)\`
- \`MailIntegration.queue_persistent\`
- \`QueueConfigContract.persistent\`
- \`MailService._prepare_stores()\` selects SQL-backed stores when set

An unavailable database logs an error naming the durability that was lost and falls back to in-memory stores, rather than aborting startup — mail degrades to non-durable instead of taking the application down.

Explicitly-supplied stores still win: a caller passing \`store=\` meant it, and configuration does not override that.

### User impact

Durable envelope and suppression storage is now reachable from \`workspace.py\`.

---

## Documentation Correctness Fix

The \`aquilia.tasks\` package docstring listed "Persistent or distributed backends", "Job chaining / workflow DAGs" under **"Not implemented today (deliberately absent, not stubbed)"**. All three shipped in this release; the docstring is updated. It now documents the at-least-once delivery contract instead, and the one thing still genuinely absent (per-queue rate limiting).

---

## Related

- [Distributed & Persistent Backends](distributed_tasks.md)
- [Workflows & DAGs](workflows.md)
- [Mail Delivery Queue](mail_queue.md)
- [Migration Guide](migration.md)
`,
    "cli.md": `# CLI Changes — Aquilia v1.3.5

No commands were added, removed, or renamed in this release. One existing command gained new validation.

---

## \`aq mail check\`

\`aq mail check\` validates mail configuration without sending anything. It now also validates DKIM configuration.

### Why

DKIM signing failures raise at send time rather than silently shipping an unsigned message — a receiving server treats a missing signature very differently from an invalid one, and an operator who enabled DKIM expects signed mail or a loud error. That is the right runtime behavior, but it means a misconfiguration is not discovered until the first real send, possibly in production.

\`aq mail check\` now surfaces both failure modes up front.

### New checks

When \`dkim_enabled\` is true:

1. **\`dkim_domain\` unset** — signing cannot proceed without a domain.
2. **\`dkimpy\` not installed** — the signing dependency is missing.

### Output

\`\`\`
$ aq mail check
DKIM is enabled but dkim_domain is unset -- sends will fail
DKIM is enabled but 'dkimpy' is not installed -- pip install aquilia[mail-dkim]
\`\`\`

A clean configuration reports no issues, as before.

### Recommended workflow

\`\`\`bash
# After enabling DKIM in workspace.py
pip install aquilia[mail-dkim]
aq mail check                          # verify configuration
aq mail send-test --to you@example.com # verify real delivery
\`\`\`

Add \`aq mail check\` to CI or a deploy preflight step for any application that sends mail.

---

## Unchanged Commands

\`aq mail send-test\` and \`aq mail inspect\` are unchanged. No flags were added, changed, or deprecated, and no output formats changed.

Background task workers are not started by a dedicated CLI command; a worker process is a normal Aquilia application configured with \`num_workers\` and a shared backend. See [Distributed & Persistent Backends](distributed_tasks.md).

---

## Related

- [Mail Security & MIME](mail_security.md)
- [Migration Guide](migration.md)
`,
    "distributed_tasks.md": `# Distributed & Persistent Task Backends — Aquilia v1.3.5

Background tasks now run across multiple worker processes and multiple machines, with job state that survives a restart. Before this release the only backend was \`MemoryBackend\`: jobs lived in the worker process and were lost on restart, and \`backend="redis"\` logged a warning and silently fell back to in-memory.

---

## Motivation

The task system was single-process. That is fine for a cron-like cleanup job, but it fails the moment an application scales horizontally:

- Two web workers each ran their own queue, so a periodic task fired twice.
- A deploy dropped every queued job on the floor.
- A worker crash lost whatever that worker was executing, permanently.
- \`Integration.tasks(backend="redis")\` was accepted by config validation and then ignored at runtime.

---

## Design Goals

1. **Backend choice is configuration, not code.** Task functions, decorators, and \`enqueue()\` calls are identical on every backend.
2. **No lost work on crash.** A worker that dies mid-job must have that job picked up by a peer.
3. **Fail at enqueue, not on a remote worker.** Anything that cannot cross a process boundary must be rejected at the call site, where the stack trace is useful.
4. **Existing single-process apps unaffected.** \`memory\` stays the default and behaves exactly as before.

---

## Architecture

### Job serialization

A job that crosses a process boundary cannot carry a live Python callable or arbitrary objects. Two new methods on \`Job\` define the transport form:

\`\`\`python
payload = job.to_payload()      # JSON-compatible dict
restored = Job.from_payload(payload)
\`\`\`

\`to_payload()\` validates \`args\` and \`kwargs\` against \`json.dumps\` and raises \`TaskSerializationFault\` if they cannot be represented. \`from_payload()\` deliberately leaves the callable unset — the worker resolves it from \`func_ref\` through the \`@task\` registry, so a queue entry can never name a function the application did not register.

\`Job.to_dict()\` is unchanged and remains the human-facing view used by the admin dashboard.

### Lease-based claiming

Both durable backends use the same coordination model:

1. A worker claims a job and takes a lease for \`lease_seconds\` (default \`300.0\`).
2. While executing, it renews the lease every \`heartbeat_interval\` seconds (default \`30.0\`).
3. A background reclaim loop sweeps every \`reclaim_interval\` seconds (default \`60.0\`) and returns jobs whose lease lapsed to the runnable pool.

If a worker is killed, its lease expires and a peer reclaims the job instead of the job being lost.

**This is at-least-once delivery.** A worker that stalls past its lease — a long GC pause, a blocked event loop — can have its job reclaimed and executed a second time. Task functions should be idempotent.

### \`RedisBackend\`

Multi-process and multi-machine, backed by Redis. Claims are atomic through a Lua script against a sorted set; fingerprint reservation uses \`SET NX\`. Fastest option, and the right default for high throughput.

### \`SQLBackend\`

Durable state on the database the application already uses — no new infrastructure. Works on SQLite, PostgreSQL, MySQL, and Oracle through Aquilia's existing parameterized query layer.

A claim is a conditional \`UPDATE ... WHERE id = ? AND state = ?\` inside a transaction; \`rowcount == 0\` means another worker won the race, so the loser moves on rather than double-running the job. This works on every supported dialect without needing \`SELECT ... FOR UPDATE SKIP LOCKED\`, which SQLite does not have.

Two tables are created on first \`initialize()\`:

\`\`\`
aquilia_tasks(
    id TEXT PRIMARY KEY, queue TEXT, priority INTEGER, state TEXT,
    func_ref TEXT, payload TEXT,             -- full JSON job
    available_at TEXT,                        -- when it may run
    lease_expires_at TEXT, owner TEXT,        -- distributed claim
    dedup_key TEXT, workflow_id TEXT,
    created_at TEXT, completed_at TEXT, sequence INTEGER
)
aquilia_task_locks(fingerprint TEXT PRIMARY KEY, job_id TEXT, expires_at TEXT)
\`\`\`

The unique primary key on \`aquilia_task_locks.fingerprint\` is what makes deduplication correct under concurrency: two workers racing to reserve the same fingerprint both attempt an \`INSERT\`, and the database rejects exactly one.

Redis is faster and scales further. SQL wins when you cannot add a Redis dependency, or when you want jobs to commit in the *same transaction* as the business data that created them, so a rolled-back request cannot leave an orphaned job behind. Above roughly a few hundred jobs/second, prefer Redis.

---

## Configuration

\`\`\`python
# workspace.py

# Development — single process, non-durable (default, unchanged)
Integration.tasks(num_workers=4)

# Production — distributed workers, durable queue
Integration.tasks(
    backend="redis",
    redis_url="redis://cache:6379/0",
    redis_prefix="aquilia:tasks:",
    num_workers=16,
    lease_seconds=120,
    heartbeat_interval=30,
    reclaim_interval=60,
)

# Durable without extra infrastructure
Integration.tasks(backend="sql", sql_table="aquilia_tasks")
\`\`\`

### New options

| Option | Default | Purpose |
|---|---|---|
| \`backend\` | \`"memory"\` | \`"memory"\`, \`"redis"\`, or \`"sql"\` (aliases: \`"database"\`, \`"db"\`) |
| \`redis_url\` | \`None\` | Redis connection URL; falls back to \`$REDIS_URL\` |
| \`redis_prefix\` | \`"aquilia:tasks:"\` | Key namespace, so several apps can share one Redis |
| \`sql_table\` | \`"aquilia_tasks"\` | Job table name for the SQL backend |
| \`lease_seconds\` | \`300.0\` | How long a claimed job stays owned before a peer may reclaim it |
| \`heartbeat_interval\` | \`30.0\` | Lease renewal cadence; must be well under \`lease_seconds\` |
| \`reclaim_interval\` | \`60.0\` | How often to sweep for jobs abandoned by crashed workers |
| \`dedup_ttl\` | \`3600.0\` | How long a deduplication reservation is held |
| \`worker_id\` | \`None\` | Worker identity recorded as a job's owner; defaults to \`hostname:pid:random\` |

Install the Redis extra with \`pip install aquilia[redis]\`. The SQL backend requires \`Integration.database(...)\` and no extra dependency.

---

## Usage

Task code does not change between backends:

\`\`\`python
from aquilia.tasks import task

@task(queue="reports", max_retries=3)
async def rebuild_report(report_id: int) -> dict:
    return {"rebuilt": report_id}
\`\`\`

\`\`\`python
job_id = await tasks.enqueue(rebuild_report, 42)
job = await tasks.get_job(job_id)
\`\`\`

### Running a dedicated worker process

A process that only consumes work is a normal Aquilia app with \`num_workers\` set and no enqueueing of its own. The queues it polls are derived from the \`@task\` descriptors it has imported, plus any queue it discovers on the shared backend — so a worker does not need to know in advance which queues its producers use.

---

## Edge Cases

**Non-serializable arguments.** On a persistent backend, passing an object JSON cannot represent raises \`TaskSerializationFault\` at \`enqueue()\`:

\`\`\`python
await tasks.enqueue(process, open("f.txt"))   # TaskSerializationFault
\`\`\`

This is deliberate. The alternative is a job that enqueues cleanly and then fails unrecoverably on a remote worker, far from the call site. On \`MemoryBackend\` live objects still work, because the job never leaves the process.

**Unregistered task names.** A worker resolves \`func_ref\` through the \`@task\` registry. If the consumer process has not imported the module that registers the task, the job raises \`TaskResolutionFault\` rather than executing arbitrary named code. Ensure every worker imports the same task modules.

**Backend unavailable at startup.** A Redis or database that cannot be reached logs an error naming the durability that was lost and falls back to \`MemoryBackend\`, rather than aborting startup. The application still serves requests; queued jobs are not durable until the backend recovers and the process restarts.

**Unknown backend name.** A typo such as \`backend="rabbitmq"\` logs a warning listing the valid values and uses \`MemoryBackend\`. A typo does not take production down.

**Clock skew across machines.** Leases are stored as absolute timestamps. Significant clock skew between workers can cause premature reclaim (duplicate execution) or delayed reclaim. Run NTP.

---

## Performance Implications

- \`MemoryBackend\` is unchanged; single-process applications see no difference.
- \`RedisBackend\` claim is one round trip against an in-memory sorted set.
- \`SQLBackend\` claim is one \`UPDATE\` inside a transaction. Throughput is bounded by database write capacity; above a few hundred jobs/second prefer Redis.
- The reclaim loop runs once per \`reclaim_interval\` per process and issues one sweep query. Raising \`reclaim_interval\` reduces load; lowering it shortens the window during which a crashed worker's job sits idle.

---

## Compatibility

Fully backward compatible. \`memory\` remains the default, \`MemoryBackend\` behavior is unchanged, and every existing \`@task\` and \`enqueue()\` call works untouched. The new configuration options are additive with defaults matching prior behavior.

---

## Related

- [Workflows & DAGs](workflows.md) — composing jobs, which requires a shared backend to span processes
- [Idempotency & Deduplication](idempotency.md) — the distributed lock built on this coordination layer
- [Mail Delivery Queue](mail_queue.md) — the first framework subsystem to run on it
- [Migration Guide](migration.md)
`,
    "http_native.md": `# Native HTTP Client & Third-Party HTTP Removal — Aquilia v1.3.5

In Aquilia v1.3.5, all remaining traces of third-party HTTP clients (specifically \`httpx\`) have been completely removed from the framework codebase, dependencies, test suite, and documentation in favor of Aquilia's native zero-dependency \`aquilia.http\` client.

---

## 1. Overview & Motivation

Aquilia features a production-grade, fully asynchronous HTTP client implementation in \`aquilia.http\` built directly on Python standard library primitives (\`asyncio\`, \`ssl\`, \`gzip\`, \`zlib\`).

Previously, optional subsystems like \`SendGridProvider\` and test helpers like \`LiveServerTestCase\` relied on \`httpx\` as a third-party dependency. In v1.3.5:

1. **SendGrid Mail Provider** (\`aquilia.mail.providers.sendgrid.SendGridProvider\`) uses native \`aquilia.http.AsyncHTTPClient\`.
2. **\`LiveServerTestCase\`** (\`aquilia.testing.cases.LiveServerTestCase\`) documentation and usage examples use native \`aquilia.http.AsyncHTTPClient\`.
3. **Dependency Clean-Up**: \`httpx\` has been removed from \`pyproject.toml\`, \`setup.py\`, \`aquilia.egg-info\`, and all extra dependency bundles (\`mail-sendgrid\`, \`testing\`, \`dev\`).

---

## 2. Changes in SendGrid Provider

The \`SendGridProvider\` now initializes \`AsyncHTTPClient\` directly from \`aquilia.http\`:

\`\`\`python
from aquilia.http import AsyncHTTPClient

class SendGridProvider:
    async def initialize(self) -> None:
        self._client = AsyncHTTPClient(
            base_url=self.api_base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "User-Agent": "aquilia-mail/1.0",
            },
            timeout=self.timeout,
        )
\`\`\`

Error handling consumes the async \`HTTPClientResponse\` API:

\`\`\`python
body = await response.json()
\`\`\`

---

## 3. Backward Compatibility & \`aclose\` Alias

To ensure smooth transition for any external callers expecting \`aclose()\`, \`aquilia.http.AsyncHTTPClient\` now provides an alias:

\`\`\`python
class AsyncHTTPClient:
    async def close(self) -> None: ...

    aclose = close
\`\`\`

Both \`await client.close()\` and \`await client.aclose()\` work seamlessly.

---

## 4. Dependencies Updated

- \`mail-sendgrid\` extra: no longer installs \`httpx\`.
- \`testing\` extra: no longer installs \`httpx\`.
- \`dev\` extra: no longer installs \`httpx\`.
`,
    "idempotency.md": `# Idempotency & Distributed Deduplication — Aquilia v1.3.5

\`Job.fingerprint\` existed since the task system shipped but nothing ever read it. As of v1.3.5 it is enforced at enqueue time, and on durable backends that enforcement is a real distributed lock: two processes racing to queue the same work produce one job, not two.

---

## Motivation

The classic double-send. A user double-clicks, a retried HTTP request replays, a webhook is delivered twice, two web workers react to the same event — and the same background job is queued twice. Applications worked around this with their own Redis \`SETNX\` guards or a \`processed\` table, reimplementing per project what the framework already had the raw material for.

\`Job.fingerprint\` was computed and stored. It simply had no readers.

---

## How It Works

### The fingerprint

A stable digest over \`func_ref\`, \`queue\`, \`args\`, and \`kwargs\` — two enqueue calls that would do identical work share a fingerprint:

\`\`\`python
job.fingerprint    # 12-hex-character digest
\`\`\`

It is computed from the JSON form when possible, so equal-but-not-identical values agree across processes: a tuple \`(1, 2)\` and a list \`[1, 2]\` produce the same fingerprint. Non-JSON values fall back to \`repr\`, which keeps the in-memory backend working with live objects.

### The \`dedup\` parameter

\`\`\`python
await manager.enqueue(rebuild_index, dedup="allow")   # default — always enqueue
await manager.enqueue(rebuild_index, dedup="skip")    # return the in-flight job's ID
await manager.enqueue(rebuild_index, dedup="raise")   # raise TaskDuplicateFault
\`\`\`

| Mode | Behavior |
|---|---|
| \`"allow"\` | Always enqueue. Preserves historical behavior, so existing code is unaffected. |
| \`"skip"\` | If identical work is already in flight, return that job's ID instead of enqueueing a second copy. |
| \`"raise"\` | Raise \`TaskDuplicateFault\` instead. Use when a duplicate indicates a caller bug. |

A reservation is held for \`dedup_ttl\` seconds (default \`3600.0\`) and released when the job reaches a terminal state.

### Distributed enforcement

The backend owns the reservation, so correctness under concurrency comes from the storage layer, not from application-level check-then-act:

- **\`RedisBackend\`** — \`SET NX\` on the fingerprint key. Exactly one caller wins.
- **\`SQLBackend\`** — \`INSERT\` into \`aquilia_task_locks\`, whose \`fingerprint\` column is the primary key. Two workers racing both attempt the insert and the database rejects exactly one.
- **\`MemoryBackend\`** — an in-process map, correct within a single process.

---

## Examples

### Collapsing a burst

\`\`\`python
# Ten requests arrive; one job runs.
job_id = await tasks.enqueue(rebuild_search_index, dedup="skip")
\`\`\`

### Treating a duplicate as an error

\`\`\`python
from aquilia.tasks import TaskDuplicateFault

try:
    await tasks.enqueue(charge_card, order_id, dedup="raise")
except TaskDuplicateFault:
    return Response.json({"status": "already_processing"}, status=409)
\`\`\`

### Across processes

\`\`\`python
# Web worker A and web worker B, sharing one Redis or SQL backend
a = await tasks.enqueue(send_invoice, order_id, dedup="skip")
b = await tasks.enqueue(send_invoice, order_id, dedup="skip")
assert a == b   # one job
\`\`\`

---

## Before vs After

\`\`\`python
# Before v1.3.5 — hand-rolled guard in every application
lock_key = f"job:invoice:{order_id}"
if await redis.set(lock_key, "1", nx=True, ex=3600):
    await tasks.enqueue(send_invoice, order_id)
\`\`\`

\`\`\`python
# v1.3.5
await tasks.enqueue(send_invoice, order_id, dedup="skip")
\`\`\`

The framework version is also correct in a case the hand-rolled one usually is not: the reservation is released when the job reaches a terminal state, so a failed job can be retried immediately instead of being blocked until the TTL expires.

---

## Edge Cases

**Deduplication suppresses duplicate *enqueues*, not duplicate *execution*.** Distributed backends are at-least-once: a job whose worker stalls past its lease may be reclaimed and run twice. Task functions should still be idempotent. These are two different guarantees and \`dedup\` provides only the first.

**Fingerprints include the queue.** The same function with the same arguments on two different queues is two different fingerprints, and both will be enqueued.

**Argument order matters for positional arguments.** \`f(1, 2)\` and \`f(2, 1)\` are distinct. Keyword arguments are sorted, so \`f(a=1, b=2)\` and \`f(b=2, a=1)\` match.

**Non-JSON arguments still deduplicate in-process.** The \`repr\` fallback means two live objects deduplicate only if their \`repr\` matches. On a persistent backend such arguments raise \`TaskSerializationFault\` before dedup is reached.

**The default is unchanged.** Existing code that never passes \`dedup\` continues to enqueue every call. This is deliberate — silently collapsing jobs in an existing application would be a breaking behavioral change.

---

## Performance Implications

\`dedup="allow"\` (the default) adds no work: no fingerprint reservation is attempted. \`"skip"\` and \`"raise"\` add one reservation operation per enqueue — a single \`SET NX\` on Redis, a single \`INSERT\` on SQL. In exchange, collapsed duplicates avoid an entire job execution.

---

## Compatibility

Fully backward compatible. \`dedup\` is a new keyword-only parameter defaulting to \`"allow"\`, which is exactly the prior behavior. \`TaskDuplicateFault\` is a new fault raised only when explicitly requested via \`dedup="raise"\`.

---

## Related

- [Distributed & Persistent Backends](distributed_tasks.md) — the coordination layer this builds on
- [Workflows & DAGs](workflows.md)
- [Migration Guide](migration.md)
`,
    "mail_queue.md": `# Mail Delivery Queue — Aquilia v1.3.5

Outbound mail can now be delivered by background workers instead of inside the request handler. \`send_message()\` persists an envelope, schedules a delivery job, and returns — the SMTP conversation happens on a worker, with retries, backoff, and delayed sends managed by the task scheduler.

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

\`\`\`
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
\`\`\`

### \`EnvelopeStore\`

The durable record of accepted mail. Two implementations ship:

| Class | Durability |
|---|---|
| \`MemoryEnvelopeStore\` | In-process, bounded (\`max_envelopes\`, default 10,000). Default. |
| \`SQLEnvelopeStore\` | Application database, table \`aquilia_mail_envelopes\`. |

The interface covers \`save\`, \`get\`, \`list_by_status\`, \`find_by_digest\`, \`find_by_idempotency_key\`, \`cleanup\`, and \`stats\`.

### The delivery task

Delivery is a registered task named \`aquilia.mail.deliver\`, on queue \`mail\`.

**It takes an envelope ID, not an envelope.** A live \`MailEnvelope\` cannot survive a persistent or distributed backend, which serializes jobs as JSON. The worker — which may be in another process entirely — reloads the envelope from the shared store. This is what lets mail delivery run on another machine without any API change.

It is registered under a stable name rather than enqueued as a bare callable, so a worker in another process resolves it through the \`@task\` registry; a module-path reference would not survive a rename.

Mail owns its own retry policy, so the job is enqueued with \`max_retries=0\` and the mail service schedules its own follow-up attempts with backoff.

---

## Configuration

\`\`\`python
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
\`\`\`

| Option | Default | Purpose |
|---|---|---|
| \`queue_enabled\` | \`False\` | Deliver via background tasks instead of inside the request |
| \`queue_persistent\` | \`False\` | Keep envelopes and suppression records in the application database |
| \`queue_dedupe_window_seconds\` | \`3600\` | Window in which an identical send is collapsed rather than sent twice |
| \`queue_retention_days\` | \`30\` | How long delivered envelopes are retained |

For an end-to-end durable path, pair \`queue_persistent=True\` with a durable task backend:

\`\`\`python
Integration.tasks(backend="redis", redis_url="redis://cache:6379/0")
Integration.mail(queue_enabled=True, queue_persistent=True, ...)
\`\`\`

\`queue_persistent=True\` requires \`Integration.database(...)\`.

---

## Usage

Call sites are identical whether the queue is on or off:

\`\`\`python
from aquilia.mail import EmailMessage

envelope_id = await EmailMessage(
    subject="Welcome",
    body="Thanks for signing up",
    to=user.email,
).asend()
\`\`\`

With the queue enabled, \`asend()\` returns as soon as the envelope is stored — typically sub-millisecond — and delivery completes on a worker. The returned envelope ID is the handle for checking status:

\`\`\`python
envelope = await mail.store.get(envelope_id)
envelope.status      # QUEUED → SENDING → SENT / FAILED / BOUNCED / CANCELLED
envelope.attempts
\`\`\`

---

## Send-Time Deduplication

Independent of the task system's job-level deduplication, mail collapses duplicate *sends*:

- An explicit \`idempotency_key\` on the message matches first.
- Otherwise a content digest matches within \`queue_dedupe_window_seconds\`.

This guards the classic double-send: a retried request or a double-clicked button producing two identical emails.

---

## Edge Cases

**No task manager, queue enabled.** Delivery falls back to inline sending. Recording an envelope as queued when nothing can deliver it would silently drop mail. The fallback also applies when a manager exists but has not been started — enqueueing into a stopped manager would park the message forever.

**Persistent stores with no database.** If \`queue_persistent=True\` but the database is unavailable, mail logs an error naming the durability that was lost and falls back to in-memory stores rather than aborting startup.

**Every recipient suppressed.** The envelope is marked \`CANCELLED\` and no delivery job is scheduled. See [Bounce Handling & Suppression](bounces_suppression.md).

**Missing envelope at delivery time.** A delivery job whose envelope has been cleaned up or cancelled logs a warning and is treated as success rather than retried forever — no amount of retrying will bring it back.

**Attachments.** Attachment payloads live in envelope metadata as blobs keyed by digest, so an envelope reloaded on another worker still carries its attachments.

---

## Performance Implications

Request-path cost drops from a full SMTP conversation (tens to hundreds of milliseconds, or a provider timeout on failure) to one store write plus one enqueue. Throughput of actual delivery becomes a function of worker count and provider rate limits rather than request concurrency.

\`MemoryEnvelopeStore\` evicts oldest-first past \`max_envelopes\`; an evicted envelope's delivery job will find nothing and give up. Use \`queue_persistent=True\` for any deployment where that matters.

---

## Compatibility

Fully backward compatible. \`queue_enabled\` defaults to \`False\`, so mail continues to send inline exactly as before unless explicitly enabled. \`EmailMessage\`, \`send_message()\`, and \`asend()\` signatures are unchanged. \`MailService.store\` and \`MailService.suppression\` are new attributes; passing explicit \`store=\` / \`suppression=\` to the constructor still overrides configuration.

---

## Related

- [Bounce Handling & Suppression](bounces_suppression.md)
- [Distributed & Persistent Backends](distributed_tasks.md)
- [Mail Security & MIME](mail_security.md)
- [Migration Guide](migration.md)
`,
    "mail_security.md": `# Mail Security, MIME & Templates — Aquilia v1.3.5

The mail subsystem's message construction, signing, logging, and templating were consolidated and hardened. MIME assembly now lives in one place shared by every provider, DKIM signing is real, log output redacts personal data on request, and the ATS template engine gained a documented filter set with autoescaping on by default.

---

## Shared MIME Assembly

Every provider previously built its own MIME message, which meant header handling, attachment encoding, and multipart structure drifted between SMTP, SES, SendGrid, and the file/console backends. \`aquilia/mail/mime.py\` is now the single implementation:

\`\`\`python
from aquilia.mail import build_mime_message, message_to_bytes, sign_dkim

build_mime_message(envelope, *, extra_headers=None)   # -> MIMEMultipart
message_to_bytes(msg, security=None)                  # -> bytes, DKIM-signed if configured
sign_dkim(raw_message, security)                      # -> bytes
\`\`\`

\`build_mime_message()\` produces a \`multipart/mixed\` message with a generated \`Message-ID\` and Aquilia tracking headers — \`X-Aquilia-Envelope-ID\`, plus trace and tenant IDs when set. Attachment payloads are read from envelope metadata, so an envelope reloaded on another worker still carries its attachments. The \`extra_headers\` argument is merged last, letting a provider add its own header (an ESP configuration set, for example) without forking the builder.

\`extract_domain(email)\` is also exported, used for per-domain rate limiting and DKIM domain defaulting.

### Why it matters

Bugs fixed in one provider now apply to all of them, and the \`X-Aquilia-Envelope-ID\` header is emitted consistently — which is what lets provider webhooks correlate a bounce back to the exact envelope. See [Bounce Handling & Suppression](bounces_suppression.md).

---

## DKIM Signing

DKIM signing is applied at the byte level, immediately before transmission, so the signature covers exactly what the provider receives.

\`\`\`python
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    dkim_enabled=True,
    dkim_domain="example.com",
    dkim_selector="aquilia",
)
\`\`\`

| Option | Default | Purpose |
|---|---|---|
| \`dkim_enabled\` | \`False\` | Sign outbound mail |
| \`dkim_domain\` | \`None\` | Signing domain (\`d=\`). Required when enabled |
| \`dkim_selector\` | \`"aquilia"\` | Selector (\`s=\`); must match your DNS TXT record |
| \`dkim_private_key_path\` | \`None\` | Path to the PEM private key |
| \`dkim_private_key_env\` | \`"AQUILIA_DKIM_PRIVATE_KEY"\` | Environment variable holding the PEM key |

Signing requires the \`dkimpy\` package:

\`\`\`bash
pip install aquilia[mail-dkim]
\`\`\`

**DKIM failures raise at send time rather than shipping an unsigned message.** Silently sending unsigned mail would defeat the purpose — a receiving server treats a missing signature very differently from an invalid one, and an operator who enabled DKIM expects signed mail or an error.

Because that failure is at send time, \`aq mail check\` now validates the configuration up front:

\`\`\`
$ aq mail check
DKIM is enabled but dkim_domain is unset -- sends will fail
DKIM is enabled but 'dkimpy' is not installed -- pip install aquilia[mail-dkim]
\`\`\`

---

## TLS Enforcement

\`require_tls\` defaults to \`True\`. SMTP delivery negotiates STARTTLS and aborts rather than transmitting credentials or message content in cleartext. Disable only for a local development relay.

---

## XOAUTH2 Authentication

\`MailAuth.oauth2()\` supports SMTP providers that require bearer tokens (Gmail, Microsoft 365):

\`\`\`python
Integration.mail(
    auth=MailAuth.oauth2(
        client_id="...",
        client_secret_env="MAIL_OAUTH_SECRET",
        access_token_env="MAIL_OAUTH_TOKEN",
        token_url="https://oauth2.googleapis.com/token",
        scope="https://mail.google.com/",
    ),
    providers=[...],
)
\`\`\`

Aquilia does not perform the token exchange. Supply a currently valid token — literally or through \`access_token_env\` — from whatever component owns the refresh cycle. \`token_url\`, \`scope\`, and \`refresh_token\` are recorded for that component's use. The token is presented to SMTP via the XOAUTH2 mechanism.

---

## PII Redaction in Logs

Mail logs contain recipient addresses by nature. \`pii_redaction\` masks them:

\`\`\`python
Integration.mail(pii_redaction=True, ...)
\`\`\`

\`\`\`python
from aquilia.mail import redact_email, redact_pii

redact_email("alice@example.com")               # "a***e@example.com"
redact_pii("contact alice@example.com", enabled=True)
\`\`\`

Local parts are masked while the domain is preserved, so logs remain useful for diagnosing a domain-wide delivery problem without recording individual identities. Off by default — enabling it reduces debuggability, which should be a deliberate choice.

---

## ATS Templates

The mail template engine (\`<< expression >>\` syntax, distinct from the Jinja engine used for HTML views) gained a documented public API and filter set.

\`\`\`python
from aquilia.mail.template import configure, register_filter, render_string, render_template, FILTERS

configure(template_dirs=["mail_templates"])
render_string(template_text, context, *, autoescape=True)
render_template(template_name, context, *, template_dirs=None, autoescape=None)
register_filter(name, fn)
\`\`\`

### Autoescaping

**Interpolated values are HTML-escaped by default.** A username containing \`<script>\` cannot inject markup into an HTML mail body.

\`\`\`python
render_string("<p><< name >></p>", {"name": "<script>alert(1)</script>"})
# '<p>&lt;script&gt;alert(1)&lt;/script&gt;</p>'
\`\`\`

Two escape hatches:

- The \`safe\` filter, for a value that is known-good markup: \`<< body|safe >>\`
- \`autoescape=False\`, for plain-text bodies and subject headers, where escaping would corrupt output (\`&amp;\` in a subject line)

Subject rendering uses \`autoescape=False\` internally for exactly this reason.

### Built-in filters

\`currency\`, \`default\`, \`escape\`, \`join\`, \`length\`, \`lower\`, \`safe\`, \`title\`, \`trim\`, \`truncate\`, \`upper\`.

\`\`\`
<< total|currency("EUR") >>        →  EUR 12.50
<< blurb|truncate(5) >>            →  abcde…
<< tags|join(", ") >>
<< nickname|default("friend") >>
<< name|trim|title >>
\`\`\`

Filters compose left to right. Arguments must be literals — no expressions — so a template cannot execute arbitrary code.

Register your own:

\`\`\`python
register_filter("shout", lambda v: f"{v}!!!")
\`\`\`

### Control flow is rejected, loudly

Jinja-style control tags (\`[[% if %]]\`, \`[[% for %]]\`) are **not** supported and raise \`MailTemplateFault\` rather than being passed through. Shipping a raw \`[[% if %]]\` token to a recipient's inbox is worse than failing the render. Build conditional content in Python and pass the result in the context.

### Error behavior

- Unknown filter, malformed filter arguments, or a control-flow tag → \`MailTemplateFault\`
- A missing context variable renders as empty rather than raising, so an optional field does not break a send
- Dotted lookups work against dicts and objects: \`<< user.name >>\`

---

## Provider Changes

All providers now build messages through the shared MIME layer:

- **SMTP** — restructured around shared MIME assembly, byte-level DKIM signing, STARTTLS enforcement, and XOAUTH2 authentication.
- **SES** — sends the fully assembled raw message, preserving custom headers and the DKIM signature.
- **SendGrid** — consistent header handling and attachment encoding.
- **Console / File** — render the same MIME structure as production providers, so what you inspect in development matches what ships.

---

## Compatibility

Backward compatible. \`require_tls\` already defaulted to \`True\`. DKIM, PII redaction, and OAuth2 are opt-in. Template rendering already autoescaped; this release documents the behavior and the filter set rather than changing it. Provider configuration and \`EmailMessage\` signatures are unchanged.

The one behavior worth calling out: with \`dkim_enabled=True\` and a broken configuration, sends now **fail** instead of shipping unsigned mail. Run \`aq mail check\` after enabling DKIM.

---

## Related

- [Mail Delivery Queue](mail_queue.md)
- [Bounce Handling & Suppression](bounces_suppression.md)
- [CLI Changes](cli.md)
- [Migration Guide](migration.md)
`,
    "migration.md": `# Migration Guide — Aquilia v1.3.5

Aquilia v1.3.5 is a **backwards-compatible** feature release. No existing API was removed, renamed, or changed in signature. Every workspace, manifest, task, and mail configuration from 1.3.4 continues to work without modification.

This guide covers upgrading, then the optional migrations that let you adopt the new capabilities.

---

## Upgrading

\`\`\`bash
pip install aquilia==1.3.5
\`\`\`

Optional extras for the new capabilities:

\`\`\`bash
pip install aquilia[redis]        # distributed task backend
pip install aquilia[mail-dkim]    # DKIM signing for outbound mail
\`\`\`

Nothing else is required. If you change no configuration, v1.3.5 behaves exactly as v1.3.4 did:

- Tasks run on \`MemoryBackend\`, single process.
- Mail sends inline, inside the request.
- No addresses are suppressed.
- No deduplication is applied.

---

## Upgrade Checklist

1. \`pip install aquilia==1.3.5\`
2. Run your test suite — no changes expected.
3. *(Optional)* Move tasks to a durable backend — see below.
4. *(Optional)* Enable background mail delivery — see below.
5. *(Optional)* Wire provider webhooks for bounce handling.
6. If you use SendGrid or testing helpers, note that third-party \`httpx\` is no longer required as Aquilia uses native \`aquilia.http\`.
7. If you use DKIM, run \`aq mail check\` and install \`aquilia[mail-dkim]\`.
8. Remove any hand-rolled job deduplication in favour of \`dedup="skip"\`.
9. Remove any workaround that parsed \`repr\`-form job results.

---

## Migration 1 — Durable, Distributed Tasks

### Before

\`\`\`python
# workspace.py
Integration.tasks(num_workers=4)
\`\`\`

Jobs lived in the web worker process and were lost on restart. Running two web workers meant two independent queues, so a periodic task fired twice.

### After

\`\`\`python
# workspace.py
Integration.tasks(
    backend="redis",
    redis_url="redis://cache:6379/0",
    num_workers=8,
    lease_seconds=120,
)
\`\`\`

Or, with no new infrastructure:

\`\`\`python
Integration.tasks(backend="sql")   # requires Integration.database(...)
\`\`\`

### What you must check

**Task arguments must be JSON-serializable.** On a durable backend, a non-serializable argument raises \`TaskSerializationFault\` at \`enqueue()\`. Audit your enqueue calls for ORM instances, file handles, and custom objects:

\`\`\`python
# Breaks on a durable backend
await tasks.enqueue(send_welcome, user)          # ORM instance

# Correct
await tasks.enqueue(send_welcome, user.id)       # worker re-loads it
\`\`\`

**Every worker must import every task module.** Workers resolve jobs by registered name. A worker process that has not imported the module defining a task raises \`TaskResolutionFault\` for that job. Declaring tasks in your module manifests handles this automatically.

**Task functions should be idempotent.** Distributed backends are at-least-once: a worker that stalls past its lease can have its job reclaimed and run twice.

See [Distributed & Persistent Backends](distributed_tasks.md).

---

## Migration 2 — Replace Hand-Rolled Deduplication

### Before

\`\`\`python
lock_key = f"job:invoice:{order_id}"
if await redis.set(lock_key, "1", nx=True, ex=3600):
    await tasks.enqueue(send_invoice, order_id)
\`\`\`

### After

\`\`\`python
await tasks.enqueue(send_invoice, order_id, dedup="skip")
\`\`\`

The framework version releases the reservation when the job reaches a terminal state, so a failed job can be retried immediately rather than being blocked until the TTL expires.

Use \`dedup="raise"\` where a duplicate indicates a caller bug:

\`\`\`python
from aquilia.tasks import TaskDuplicateFault

try:
    await tasks.enqueue(charge_card, order_id, dedup="raise")
except TaskDuplicateFault:
    return Response.json({"status": "already_processing"}, status=409)
\`\`\`

The default remains \`"allow"\`, so nothing changes until you opt in.

See [Idempotency & Deduplication](idempotency.md).

---

## Migration 3 — Replace Ad-Hoc Job Sequencing

### Before

\`\`\`python
# One long-lived job orchestrating the rest — lost on restart,
# and holding a worker slot while doing nothing
@task(name="pipeline")
async def pipeline(source):
    rows = await extract(source)
    cleaned = await clean(rows)
    await load(cleaned)
\`\`\`

### After

\`\`\`python
from aquilia.tasks.workflow import chain

await chain(
    extract.s(source),
    clean.s().with_parent_results(),
    load.s().with_parent_results(),
).run(tasks)
\`\`\`

Each step is an independent job with its own retry budget. The graph is durable the moment it is submitted, so a restart resumes rather than restarting from the top. A \`WAITING\` step occupies no worker slot.

See [Workflows & DAGs](workflows.md).

---

## Migration 4 — Background Mail Delivery

### Before

\`\`\`python
Integration.mail(default_from="noreply@example.com", providers=[...])
\`\`\`

\`asend()\` performed the SMTP conversation inside the request. Response time was tied to provider latency.

### After

\`\`\`python
Integration.tasks(backend="redis", redis_url="redis://cache:6379/0")

Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
    queue_persistent=True,
)
\`\`\`

**Call sites do not change.** \`EmailMessage(...).asend()\` still returns an envelope ID; it now returns before delivery completes.

### What you must check

**Code that assumed mail was sent on return.** With the queue enabled, a returned envelope ID means *accepted*, not *delivered*. Poll status where that distinction matters:

\`\`\`python
envelope = await mail.store.get(envelope_id)
envelope.status   # QUEUED → SENDING → SENT / FAILED / BOUNCED / CANCELLED
\`\`\`

**Tests asserting on a mail outbox.** Tests that send through a queued service must drive the task manager, or configure the mail service without \`queue_enabled\` for that test.

**\`queue_persistent=True\` requires \`Integration.database(...)\`.** Without a reachable database, mail logs an error and falls back to in-memory stores.

See [Mail Delivery Queue](mail_queue.md).

---

## Migration 5 — Bounce Handling

New capability; there is nothing to migrate from. Add a webhook endpoint:

\`\`\`python
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
\`\`\`

Two things to get right:

- **Verify signatures.** Pass \`verify_topic_arn\` (SES), \`public_key\` (SendGrid), or \`signing_key\` (Mailgun). An unverified endpoint lets anyone forge a bounce and suppress an arbitrary address.
- **Exempt the path from CSRF.** Providers do not carry your CSRF token; signature verification is the authenticity check.

If you already maintain a suppression list in your own tables, import it:

\`\`\`python
for row in await LegacySuppression.all():
    await mail.suppression.suppress(row.email, reason=SuppressionReason.HARD_BOUNCE)
\`\`\`

See [Bounce Handling & Suppression](bounces_suppression.md).

---

## Migration 6 — Job Result Handling

If you worked around results arriving as \`repr\` strings on a persistent backend, remove the workaround:

\`\`\`python
# Before — parsing the repr form back
total = sum(int(r) for r in parent_results)

# After — JSON-safe values round-trip intact
total = sum(parent_results)
\`\`\`

Values that are not JSON-serializable still arrive as \`repr\` strings, which is unavoidable — return dicts, lists, and primitives from steps whose results are consumed downstream.

See [Bug Fixes](bugfixes.md).

---

## Deprecated Features

None. No API was deprecated in this release.

## Removed Features

None.

## Breaking Changes

None.

The one behavior change worth noting is not an API break: with \`dkim_enabled=True\` and an incomplete configuration, sends now fail rather than shipping unsigned mail. Run \`aq mail check\` after enabling DKIM. See [CLI Changes](cli.md).

---

## Compatibility Notes

| Area | Notes |
|---|---|
| Python | 3.10–3.13, unchanged |
| Existing manifests | No changes required |
| \`MemoryBackend\` | Behavior unchanged; still the default |
| Inline mail | Behavior unchanged; still the default |
| \`TaskManager.enqueue()\` | New keyword-only params, all defaulted to prior behavior |
| \`MailService\` | New \`store\` / \`suppression\` attributes; constructor arguments still win |
| Task result values | JSON-safe values now round-trip; previously \`repr\` on persistent backends |

---

## Known Issues

- **Redis backend lacks automated test coverage** in this release; the SQL backend carries the durable-path integration tests. The Redis implementation is exercised manually and by the shared backend contract.
- **Mailgun signature verification is opt-in.** Omitting \`signing_key\` parses without verification and logs a warning. Treat it as required in production.
- **No built-in webhook route.** Applications wire \`parse_*\` and \`process_webhook\` into their own controller, so path, authentication, and CSRF policy stay under application control.
- **Workflow steps whose parent failed remain \`WAITING\`** rather than being cancelled. They will not run; inspect them with \`failed_jobs()\`.

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
`,
    "workflows.md": `# Workflows & DAGs — Aquilia v1.3.5

Jobs can now declare dependencies on other jobs. Sequential chains, parallel groups, fan-in callbacks, and arbitrary directed acyclic graphs are all expressed through the same queue and the same workers — equivalent to Celery Canvas or BullMQ Flows.

Previously there was no way to say "run B after A". Applications either awaited a job's completion inside another job (occupying a worker slot while doing nothing) or polled \`get_job()\` in application code.

---

## Motivation

Real background work is rarely one isolated function:

- An import pipeline extracts, transforms, then loads.
- A report shards across N workers and merges the results.
- A deploy runs migrations, then warms caches, then notifies.

Without dependency support, each of these had to be orchestrated by a long-lived coroutine that survives for the whole pipeline — which loses everything on restart and does not distribute.

---

## Design Goals

1. **The graph is durable the moment it is submitted.** Every job is created up front with its dependencies recorded, so the workflow survives a restart on a persistent backend.
2. **No orchestrator process.** The backend releases dependent jobs as their dependencies complete. Nothing needs to stay resident.
3. **Reuse the existing queue.** Workflows are ordinary jobs with a \`depends_on\` field, not a parallel execution system.
4. **A failed step stops its branch.** Downstream jobs must not run on missing input.

---

## Architecture

### \`Signature\`

A task plus the arguments it will be called with, not yet enqueued — the same concept as Celery's signature, and named the same way.

\`\`\`python
from aquilia.tasks.workflow import Signature

step = Signature(send_email, ("user@example.com",), {"subject": "Hi"})
\`\`\`

Or, more idiomatically, from a \`@task\` descriptor:

\`\`\`python
step = send_email.s("user@example.com", subject="Hi")
\`\`\`

\`with_parent_results()\` returns a copy that receives its dependencies' return values as a \`parent_results\` keyword at execution time:

\`\`\`python
merge.s().with_parent_results()   # merge(parent_results=[...])
\`\`\`

The marker stored in the job's kwargs is a plain string, replaced with real values by the worker at execution time. That keeps the job JSON-serializable and lets results be read after a restart.

### \`Workflow\`

The graph builder. \`add()\` returns an index used to declare dependencies:

\`\`\`python
from aquilia.tasks.workflow import Workflow

wf = Workflow("nightly")
extract = wf.add(extract_rows.s(source))
clean   = wf.add(clean_rows.s(), depends_on=[extract])
enrich  = wf.add(enrich_rows.s(), depends_on=[extract])
wf.add(load_rows.s().with_parent_results(), depends_on=[clean, enrich])

result = await wf.run(manager)
\`\`\`

\`run()\` validates the graph, enqueues every node with its dependencies already wired, and returns a \`WorkflowResult\`. Dependent jobs start in \`WAITING\` and are released by the backend as their dependencies complete.

### \`WorkflowResult\`

\`\`\`python
await result.is_complete(manager)    # every terminal job reached a terminal state
await result.results(manager)        # terminal jobs' return values, in declaration order
await result.failed_jobs(manager)    # jobs that ended FAILED or DEAD
\`\`\`

\`is_complete()\` returns \`True\` for failure as well as success — use \`failed_jobs()\` to distinguish.

---

## Helpers

### \`chain\` — sequential

Each step waits for the previous one to complete successfully.

\`\`\`python
from aquilia.tasks.workflow import chain

await chain(
    extract.s(source),
    transform.s().with_parent_results(),
    load.s().with_parent_results(),
).run(manager)
\`\`\`

### \`group\` — parallel

Pure fan-out. Every step runs concurrently with no dependencies between them.

\`\`\`python
from aquilia.tasks.workflow import group

await group([shard.s(n) for n in range(8)]).run(manager)
\`\`\`

### \`chord\` — parallel then fan-in

A \`group\` header plus a callback that runs once every header job has completed, receiving their results.

\`\`\`python
from aquilia.tasks.workflow import chord

await chord(
    [shard.s(n) for n in range(8)],
    merge.s().with_parent_results(),
).run(manager)
\`\`\`

### Arbitrary DAGs

\`chain\`, \`group\`, and \`chord\` are conveniences over \`Workflow.add(..., depends_on=[...])\`. Any acyclic shape — diamonds, multi-level fan-out/fan-in, mixed widths — is expressible directly.

---

## Validation

Graph errors raise \`TaskWorkflowFault\` before anything is enqueued, so a malformed workflow never partially executes:

- An empty workflow.
- A cycle — detected by depth-first traversal with a path stack; the fault names the cycle.
- A dependency index that does not exist.

\`\`\`python
wf = Workflow("bad")
wf.add(step.s(), depends_on=[99])   # TaskWorkflowFault — unknown dependency
\`\`\`

---

## Edge Cases

**A failed dependency does not release its dependents.** If a step exhausts its retries, everything downstream stays \`WAITING\` rather than running on missing input. Inspect with \`failed_jobs()\`. These jobs are not automatically cancelled — a \`WAITING\` job whose parent is dead will not run and will not complete.

**Result fidelity.** Dependency results arrive as the actual returned value when it is JSON-compatible. A non-JSON return value degrades to its \`repr\` on a persistent backend, because an arbitrary object cannot be reconstructed from JSON. Return dicts, lists, and primitives from steps whose results are consumed downstream.

**Serialization applies to every step.** \`Workflow.run()\` enqueues through the normal path, so a step with non-serializable arguments raises \`TaskSerializationFault\` on a persistent backend — at submission, before any step runs.

**Workflows do not span backends.** Every job in a workflow lives on the manager it was submitted to. To span processes, use a shared durable backend.

**Ordering within a group is not guaranteed.** \`results()\` returns terminal values in *declaration* order, but execution order and completion order are arbitrary.

---

## Performance Implications

Workflow submission is O(n) enqueues for n steps, performed up front. There is no polling process and no idle worker held open waiting for a dependency — a \`WAITING\` job occupies no worker slot. Dependency resolution is one lookup per dependency at release time.

For very wide graphs (thousands of parallel steps), submission cost is dominated by the enqueue round trips; on \`RedisBackend\` these are pipelined by the backend.

---

## Compatibility

Purely additive. \`Workflow\`, \`Signature\`, \`WorkflowResult\`, \`chain\`, \`group\`, and \`chord\` are new exports from \`aquilia.tasks\`. The \`depends_on\`, \`workflow_id\`, and \`initial_state\` parameters on \`TaskManager.enqueue()\` are new keyword-only arguments with defaults that preserve prior behavior. No existing API changed.

---

## Related

- [Distributed & Persistent Backends](distributed_tasks.md) — required for workflows that span processes
- [Idempotency & Deduplication](idempotency.md)
- [Migration Guide](migration.md)
`
  },
  "1.3.4": {
    "README.md": `# Aquilia v1.3.4 Release Notes — "Structural Integrity & Controller Expansion"

Aquilia v1.3.4 is a major architecture audit and feature release focusing on framework stability, registry correctness, controller integrity, workspace discovery robustness, and scalability.

This release combines Phase 1 (registry, workspace, config, and runtime audit fixes) with Phase 2 (controller system audit fixes, strict resolved-import discovery mode, distributed throttle backends, and Resource / ViewSet CRUD controllers).

## Table of Contents

1. [Phase 1: Round 1 Bugfixes](bugfixes_r1.md)
2. [Phase 1: Round 2 Bugfixes](bugfixes_r2.md)
3. [Phase 1: Performance Improvements](performance.md)
4. [Phase 1: Manifest System Changes](manifest_system.md)
5. [Phase 1: Workspace Discovery Enhancements](workspace_discovery.md)
6. [Phase 1: CLI Updates](cli.md)
7. [Phase 2: Controller System Audit Fixes](controller_audit.md)
8. [Phase 2: Strict Resolved-Import Discovery Mode](strict_discovery.md)
9. [Phase 2: Distributed Throttle Backends](distributed_throttle.md)
10. [Phase 2: Resource / ViewSet CRUD Controllers](resource_viewset.md)
11. [Migration Guide](migration.md)
`,
    "controller_audit.md": `# Controller System Audit Fixes

Details of the fixes applied to ControllerEngine, AuthManager, and routing in Aquilia v1.3.4 (§6.1–§8 of architectural audit report).

## §6.1 Lifecycle Hook Bypass (CRITICAL)
is_simple check now consults _has_lifecycle_hooks cache. Simple routes on controllers with custom on_request/on_response execute hooks unconditionally.

## §6.2 Unintended Token Generation (SECURITY)
Added issue_tokens: bool = True to authenticate_password() and SignInProvisionPolicy. Set False for session-only auth without minting JWTs.

## §6.3 Forward-Reference Type Resolution (BUG)
Exact string match replaces substring matching in _extract_method_params(). Fallback to __annotations__ when get_type_hints() raises.

## §6.4 Dynamic Segment Route Conflict False Positives (BUG)
_routes_conflict() compares type castors. /<id:int> and /<slug:str> are no longer flagged as conflicts.

## §5.3 Class-Level Cache Contamination (ARCH)
Added clear_caches() classmethods to ControllerEngine and ControllerFactory to flush id()-keyed caches between test runs.
`,
    "strict_discovery.md": `# Strict Resolved-Import Discovery Mode

Runtime-import-based discovery engine (StrictDiscoveryEngine) using importlib and inspect.getmro().

- Resolves transitive inheritance chains and aliased imports (e.g. Controller as Base)
- CLI usage: aq discover --strict
- Programmatic usage: engine.discover(strict=True)
- Handles ImportError gracefully per file with log warning
`,
    "distributed_throttle.md": `# Distributed Throttle Backends

Pluggable ThrottleBackend architecture supporting single-instance and multi-worker cluster rate limiting.

- MemoryThrottleBackend: sliding window with asyncio.Lock and LRU eviction
- RedisThrottleBackend: Redis sorted set sliding window with fail_open graceful degradation
- Ergonomic factories: Throttle.with_redis() and Throttle.with_memory()
`,
    "resource_viewset.md": `# Resource & ViewSet CRUD Controllers

Declarative CRUD controller abstraction via Resource[T], CRUDResource[T], ReadOnlyResource[T], and @action decorator.

- Auto-registers list (GET /), retrieve (GET /{id}), create (POST /), update (PUT /{id}), partial_update (PATCH /{id}), destroy (DELETE /{id})
- Custom routes via @action(detail=True/False)
`,
    "migration.md": `# Migration Guide — Aquilia v1.3.4

Complete migration instructions for all v1.3.4 changes.

- Secret(env="VAR") explicit environment variable lookup
- AppManifest(imports=[...]) v2 API preference
- AQUILIA_FAIL_FAST=1 startup error option
- authenticate_password(issue_tokens=False) session auth pattern
- Throttle.with_redis() distributed rate limiting upgrade

## Phase 3 - Cache, Storage & Filesystem

Every public API is preserved. Three behaviours change as corrections of clearly-wrong behaviour:

- Cache keys gain a version segment (key_version now reaches the key builder). Expect one cold cache on deploy, or set key_version=0 to keep the old layout.
- @cached no longer drops the first positional argument, so decorated functions stop returning other calls' values. Flush affected namespaces on a distributed backend.
- Authenticated responses are no longer served from the shared HTTP cache. Opt in with cache_authenticated=True plus the identity header in vary_headers.

Optional adoption: Integration.filesystem() for a DI-injectable FileSystem, distributed_stampede_lock for cross-process coalescing, serializer_secret_key for signed pickle, multipart_threshold for large S3 objects, and allow_unsandboxed=False for a fail-loudly sandbox posture.
`,
    "cache_audit.md": `# Cache System Audit Fixes

Fixes applied to aquilia.cache in v1.3.4, from the Cache & Storage architectural audit.

## Critical

- @cached dropped the first positional argument, so all calls to a single-argument function collapsed onto one key and returned another call's value. A silent data-correctness bug, not an error.
- CacheMiddleware cached identity-bearing responses under an identity-independent key, serving the first authenticated user's response to everyone. Requests carrying Cookie or Authorization now bypass the cache, and Set-Cookie responses are never stored, unless cache_authenticated=True is set alongside the identity header in vary_headers.
- The middleware read a nonexistent Response.content, so every cached entry stored an empty body. Response now exposes public content and body() accessors; unmaterialisable content is treated as not cacheable.
- Server._setup_cache() passed an invalid ttl= argument; the TypeError was swallowed and the middleware was silently never installed even when enabled.

## Correctness

- key_version was parsed from config and never reached the key builder, so the documented mass-invalidation workflow did nothing.
- decorators.py held a second key builder pinned at version=0, embedding the namespace twice and ignoring key_prefix. Decorator and service keys now share one layout.
- Functions returning None were never cached and recomputed forever. They are cached now; opt out with condition=lambda r: r is not None.
- Cache-Control no-store/private and the X-Cache-TTL override were read case-sensitively against a lowercase header map and never matched.

## Performance and leaks

- LFU eviction was a linear scan despite documenting O(log n). A real (frequency, key) min-heap now backs it.
- The TTL heap grew without bound when the same TTL'd key was rewritten. Both heaps compact against live entries: 2,000 rewrites now bound the heap to at most 16 entries.

## Redis

- The docstring claimed Lua atomicity that did not exist; increment() was a check-then-act race. It now runs the existence check and INCRBY in one script.
- Tag and namespace sets accumulated members whose keys expired naturally. A Lua prune removes them during ordinary reads.
- get() never returned tags, silently diverging from MemoryBackend. A TTL-matched sidecar restores tags and namespace.
- Stampede prevention was per-process. RedisBackend now offers a leased, token-checked SET NX PX lock so only one worker in the fleet recomputes.

## Configuration

- serializer="pickle" was unreachable because no secret key could be supplied. Added serializer_secret_key.
- CompositeBackend discarded async L2 write tasks, so shutdown could drop them. Tasks are tracked and drained.`,
    "storage_filesystem_audit.md": `# Storage & Filesystem Audit Fixes

Fixes applied to aquilia.storage and aquilia.filesystem in v1.3.4. The central finding was that path containment had been implemented twice - correctly in filesystem, incorrectly in storage. There is now exactly one implementation, used by both.

## Critical

- The streaming path ignored its sandbox entirely. stream_read and stream_copy accepted config and sandbox arguments and never passed them to the validator, while presenting the same method shape as the protected whole-file helpers. Paths are now validated before any descriptor is opened.
- Every FileSystem directory method raised TypeError: list_dir() got an unexpected keyword argument 'config'. The underlying functions now accept and enforce config and sandbox.
- LocalStorage used str.startswith() for containment, so /var/data-private satisfied a root of /var/data. It now delegates to the framework's canonical validate_path, which resolves symlinks and compares path components.

## Performance and scale

- Local and S3 backends buffered whole objects in memory despite documenting a streaming contract. Both stream in chunks now; content materialises only on an explicit read().
- S3 used put_object for everything, capping objects at 5 GB. Multipart upload is used above multipart_threshold, and a failed part aborts the upload.
- All cloud backends used the shared default executor via the deprecated get_event_loop(). A dedicated bounded pool (aquilia-storage threads, AQUILIA_STORAGE_MAX_WORKERS) replaces it.

## Robustness

- StorageRegistry.initialize_all() aborted the whole subsystem if any backend failed. Only a failing default backend is fatal now; optional backends degrade and report unhealthy.
- FileSystemConfig gained allow_unsandboxed. Setting it to False makes an unset sandbox_root a boot-time error instead of silently disabling containment.
- validate_path documents that symlinks are always resolved for containment regardless of follow_symlinks, which governs metadata semantics only.
- StorageRegistry.create_backend() imports any dotted path in configuration; the trust boundary is now documented.`,
    "subsystem_lifecycle.md": `# Subsystem Lifecycle & Health

Boot, health, and DI integration changes for cache, storage, and filesystem in v1.3.4.

## Filesystem is a first-class subsystem

Previously FileSystem required manual construction and DI registration, with no managed pool lifecycle and no health reporting. Integration.filesystem() now registers it in every DI container, starts the pool at startup, and drains it at shutdown. Disabled by default, so existing applications are unaffected.

## Health checks reflect reality

Cache and storage health were registered as literal HEALTHY without probing anything, so an unreachable backend was invisible to /health. The cache now performs a real write/read/delete round trip; storage pings every backend and publishes one storage.alias entry per disk plus a healthy/degraded/unhealthy aggregate naming the failing aliases; the filesystem reports pool state.

## StorageSubsystem clarified, not deleted

StorageSubsystem is the BootContext entry point for embedders, tests, and alternative runners, while AquiliaServer boots storage through its own ordered setup sequence. Both share StorageRegistry, so behaviour cannot diverge - only the orchestration differs. This is now stated in the module docstring rather than left ambiguous.

## DI exception contract restored

patch_di_container() re-raised ProviderNotFoundFault in place of ProviderNotFoundError, so every handler catching ProviderNotFoundError silently stopped working once any server was constructed. The conversion was redundant - ProviderNotFoundError already subclasses DIFault. The original error is now enriched in place and re-raised unchanged, and the patch is idempotent.`
  },
  "1.3.2": {
    "README.md": `# Aquilia v1.3.2 Release Notes — "Specula API Observatory"

Aquilia v1.3.2 introduces **Specula**, a major evolution of the framework's documentation and API exploration subsystem. Specula completely replaces the legacy OpenAPI 3.1.0 generator and static Swagger/ReDoc pages with a compiled, introspective ASGI dashboard (the Specula Observatory), reactive hot-reloading streams, automated security and clearance level mapping, a schema-synthesized mock server, and Postman/Insomnia collection exporters.

## Table of Contents

1. [Specula Observatory UI & Integration](observatory.md)
   * The new dashboard philosophy.
   * Integrating Specula via \`Integration.specula(...)\`.
   * UI branding and Server-Sent Events (SSE) live streams.
2. [Spec Compilation & Schema Inference](compilation.md)
   * The compiler-integrated \`SpeculaBuilder\`.
   * Python-to-JSON Schema type mapping.
   * Multi-strategy request body and response resolution.
3. [Automated Security & Clearance Detection](security.md)
   * Inferred security schemes from pipeline guards.
   * Integrated authorization clearance level detection.
   * Extended metadata (\`x-specula-security\`) vendor extensions.
4. [Mock Server & Collection Exports](mock_exports.md)
   * Interactive mocking engine at \`/specula/mock\`.
   * Schema synthesis with configurable recursion depth limits.
   * Dynamic exports for Postman v2.1 and Insomnia v4.
5. [Migration Guide](migration.md)
   * Removing legacy \`OpenAPIIntegration\` references.
   * Replaced classes, paths, and deprecations.

---

## Key Subsystem Improvements

1. **Compilation over Code Scanning**: No more parsing source files or class matching at runtime. Specula extracts endpoint specs directly from Aquilia's compiled in-memory ASGI routing topology.
2. **Developer Reactivity**: Hot-reloading modules push Specula spec invalidations down active Server-Sent Events (SSE) connections, immediately refreshing the developer's dashboard.
3. **Simulated Sandbox**: Frontends can start testing integration before the backend endpoints are written. The mock server synthesizes response payloads matching the exact JSON schemas defined in Contracts or ORM Models.
4. **Complete Security Transparency**: Exposes exact pipeline guards, role requirements, and AccessLevel clearance levels to ensure complete architectural observability.
`,

    "compilation.md": `# Spec Compilation & Schema Inference

Specula features a compiler-integrated OpenAPI 3.1.0 specification engine (\`SpeculaBuilder\`). Instead of scanning source files at startup, it introspects Aquilia's compiled routing topology in memory, extracting schemas, bindings, parameters, and outputs.

---

## Python-to-JSON Schema Mapping

When generating schema objects, Specula inspects standard type hints and maps them to their OpenAPI 3.1.0 JSON Schema equivalents. 

Specula is fully compliant with the OpenAPI 3.1.0 specification:
* **Option types** use \`oneOf\` blocks combined with \`{"type": "null"}\` instead of the deprecated \`nullable\` property.
* **Complex Python structures** map cleanly to nested schemas.

### Mapping Reference Table

| Python Type Hint | JSON Schema Equivalent |
| :--- | :--- |
| \`str\` | \`{"type": "string"}\` |
| \`int\` | \`{"type": "integer"}\` |
| \`float\` | \`{"type": "number", "format": "double"}\` |
| \`bool\` | \`{"type": "boolean"}\` |
| \`bytes\` | \`{"type": "string", "format": "binary"}\` |
| \`None\` / \`type(None)\` | \`{"type": "null"}\` |
| \`Optional[T]\` / \`T \| None\` | \`{"oneOf": [{"type": T_schema}, {"type": "null"}]}\` |
| \`list[T]\` / \`List[T]\` | \`{"type": "array", "items": T_schema}\` |
| \`dict[str, T]\` / \`Dict[str, T]\` | \`{"type": "object", "additionalProperties": T_schema}\` |
| \`tuple[T1, T2]\` | \`{"type": "array", "prefixItems": [T1_schema, T2_schema], "minItems": 2, "maxItems": 2}\` |
| \`Contract\` / \`Model\` | \`{"\$ref": "#/components/schemas/Name"}\` |

---

## Request Body Inference Strategies

Specula resolves request payloads through a 5-tier inference engine, prioritizing explicit developer configurations over implicit code analysis.

### 1. The \`request_contract\` Parameter
If a route decorator declares a validation contract directly, the builder generates a reference schema:
\`\`\`python
@POST("/users", request_contract=UserCreateContract)
async def create_user(self, ctx: RequestCtx): ...
\`\`\`

### 2. Contract Parameter Type Hints
If a route handler receives a parameter type-hinted with an Aquilia \`Contract\` class, it is automatically mapped as the JSON body payload:
\`\`\`python
@POST("/users")
async def create_user(self, ctx: RequestCtx, payload: UserCreateContract): ...
\`\`\`

### 3. Explicit \`Body\` Metadata Annotations
If a parameter is annotated using standard Python type annotations with \`Body()\`, it is mapped to a properties-based object payload:
\`\`\`python
@POST("/items")
async def create_item(self, ctx: RequestCtx, amount: Annotated[int, Body()] = 1): ...
\`\`\`

### 4. Docstring Body Mappings
The builder parses Google-style docstrings, extracting raw examples from \`Body:\` headers:
\`\`\`python
@POST("/items")
async def create_item(self, ctx: RequestCtx):
    """
    Create an item.

    Body: {"name": "Widget", "count": 10}
    """
    ...
\`\`\`

### 5. Source Code Introspection
As a fallback, Specula scans the compiled handler source code for extraction patterns:
* Finding \`await ctx.json()\` infers a generic \`application/json\` object.
* Finding \`await ctx.form()\` infers an \`application/x-www-form-urlencoded\` form.

---

## Response Shapes Resolution

Specula automatically maps success and error response channels.

### Success Shapes
1. **Model / Contract Mappings**: Declaring \`response_model\` or \`response_contract\` registers the corresponding schema (input contracts map with \`Input\` suffix, output contracts map directly) and binds them under status code \`2xx\`.
2. **Standard Output Fallbacks**: If no return contract is specified, Specula inspects handler code:
   * Calls to \`Response.json(...)\` default to \`application/json\`.
   * Calls to \`Response.html(...)\` or template rendering functions default to \`text/html\`.
   * References to \`SSEResponse(...)\` default to \`text/event-stream\`.

### Error Shapes
* **Raises Docstring Section**: Specula compiles exception details declared in Google-style docstrings into typed status responses:
  \`\`\`python
  @GET("/users/<id:int>")
  async def get_user(self, id: int):
      """
      Get user by ID.

      Raises:
          UserNotFoundFault (404): The user does not exist.
      """
      ...
  \`\`\`
  Specula compiles this raises annotation into a structured \`404 Not Found\` response returning the standard \`AquiliaError\` schema.
* **Auto-Validation Errors**: All write routes (\`POST\`, \`PUT\`, \`PATCH\`) automatically carry a default \`422 Unprocessable Entity\` response mapping returning the structured \`AquiliaValidationError\` schema.
`,

    "migration.md": `# OpenAPI to Specula Migration Guide

Aquilia v1.3.2 deprecates and removes the old static OpenAPI/Swagger engine. This guide outlines how to migrate your configuration, imports, and endpoints.

---

## 1. Configuration & Integration Upgrades

The old \`OpenAPIIntegration\` has been replaced by \`SpeculaIntegration\`. In your \`workspace.py\`, update your registrations:

### Legacy Style (Removed)
\`\`\`python
# Replaced by Specula
workspace.integrate(Integration.openapi(
    title="Store API",
    docs_path="/apidocs",
    swagger_ui_theme="dark"
))
\`\`\`

### New Style (Active)
\`\`\`python
from aquilia.integrations import SpeculaIntegration

# Option A: Direct class registration
workspace.integrate(SpeculaIntegration(
    title="Store API",
    ui_path="/apidocs",
    ui_theme="dark"
))

# Option B: Fluent helper
# workspace.integrate(Integration.specula(
#     title="Store API",
#     ui_path="/apidocs",
#     ui_theme="dark"
# ))
\`\`\`

### Parameter Mapping Table

Use this reference table to map configuration options from legacy OpenAPI attributes to Specula attributes:

| Legacy OpenAPI Option | New Specula Option | Notes |
| :--- | :--- | :--- |
| \`docs_path\` | \`ui_path\` | Default changes from \`/docs\` to \`/specula\`. |
| \`openapi_json_path\` | \`json_path\` | Default changes from \`/openapi.json\` to \`/specula/spec.json\`. |
| \`redoc_path\` | (Removed) | ReDoc is deprecated. Use the unified Specula dashboard. |
| \`swagger_ui_theme\` | \`ui_theme\` | Values: \`"auto"\`, \`"light"\`, \`"dark"\`. |
| \`swagger_ui_config\` | (Removed) | Replaced by direct dashboard configuration. |

---

## 2. Replaced Imports & Engines

If you manually generated specs, update your imports and instantiation:

\`\`\`python
# --- Legacy Imports (Removed) ---
# from aquilia.controller.openapi import OpenAPIConfig, OpenAPIGenerator
# config = OpenAPIConfig(title="API")
# spec = OpenAPIGenerator(config=config).generate(router)

# --- New Imports (Active) ---
from aquilia.specula.config import SpeculaConfig
from aquilia.specula.schema.builder import SpeculaBuilder

config = SpeculaConfig(title="API")
spec = SpeculaBuilder(config=config).build(router)
\`\`\`

---

## 3. Redirects & Endpoint Updates

The automatic redirects mapping legacy paths are no longer registered. Update links:

* **Swagger UI Docs**: Old path \`/docs\` is replaced by \`/specula\`.
* **ReDoc Docs**: Old path \`/redoc\` is deprecated. Use the unified \`/specula\` dashboard.
* **JSON Specification**: Old path \`/openapi.json\` is replaced by \`/specula/spec.json\`.
* **YAML Specification**: Specula now supports rendering YAML natively at \`/specula/spec.yaml\`.
`,

    "mock_exports.md": `# Mock Server & Collection Exports

Specula features a schema-driven Mock Server and dynamic collection exporters to support rapid frontend integration and testing.

---

## Interactive Mock Server (\`/specula/mock\`)

The mock server lets developers call any documented API endpoint and receive a plausible response payload without executing any business logic.

### Enabling the Mock Server
The mock server is disabled by default. Enable it in your workspace configuration:

\`\`\`python
workspace.integrate(Integration.specula(
    title="Customer API",
    mock_server_enabled=True,
    mock_max_depth=4 # limit recursive definitions mapping
))
\`\`\`

### How Payload Synthesis Works
When a request is sent to \`/specula/mock/<path>\`, the mock router matches the path against the compiled API specification. It resolves the success response (\`200\`, \`201\`, or \`202\`) and inspects the JSON Schema:

1. **Explicit Examples**: If the schema or individual fields define an \`example\` or \`examples\` block, those values are returned directly.
2. **Plausible Synthesis**: If no examples are configured, Specula inspects the schema field types and synthesizes logical placeholders:
   * **Formatting Matchers**: String formats like \`email\`, \`uuid\`, \`uri\`, and \`date-time\` map to real formatted values (e.g. \`user@example.com\`, \`550e8400-e29b-41d4-a716-446655440000\`).
   * **Key Name Inference**: If a string field matches common keys (such as \`email\` or \`url\`), appropriate values are auto-injected.
   * **Standard Defaults**: Integers default to \`42\`, numbers to \`3.14\`, booleans to \`True\`, and arrays to single-item arrays.
3. **Recursion Safety**: Self-referencing models (e.g., a node containing a list of children of its own type) are automatically truncated when nesting depth exceeds \`mock_max_depth\` (default \`4\`).

---

## Exporters

Specula exposes dynamic endpoints to download client collections configured with your current workspace routing topology and security schemes.

### 1. Postman Collection v2.1
* **Endpoint**: \`/specula/export/postman\`
* **Output**: A compliant Postman v2.1 collection JSON file.
* **Details**:
  * Groups endpoints into folders based on their tags or manifest module names.
  * Translates route variables like \`/users/<id:int>\` into Postman-compatible environment syntax: \`/users/{{id}}\`.
  * Pre-populates request bodies with JSON examples synthesized from Contract definitions.
  * Embeds default authorization headers mapped to the \`{{access_token}}\` environment variable.

### 2. Insomnia v4 Collection
* **Endpoint**: \`/specula/export/insomnia\`
* **Output**: A standard Insomnia v4 export file.
* **Details**:
  * Includes workspace configuration mapping the current API.
  * Sets up base environment variables referencing \`{{ _.base_url }}\`.
  * Configures HTTP methods, headers, and body payloads automatically.
`,

    "observatory.md": `# Specula Observatory UI & Integration

The Specula Observatory is a built-in interactive dashboard served natively by Aquilia at \`/specula\`. It provides a CDN-free developer sandbox that works entirely offline, inline-cached, and features hot-reload awareness.

## Workspace Integration

Specula is registered at the workspace level inside \`workspace.py\`. You configure it using the \`Integration.specula(...)\` builder method or by importing and instantiating \`SpeculaIntegration\` directly:

\`\`\`python
# workspace.py
from aquilia.workspace import Workspace
from aquilia.integrations import Integration, SpeculaIntegration

workspace = (
    Workspace("user-portal")
    
    # Style A: Fluent Integration helper
    .integrate(Integration.specula(
        title="User Portal API",
        version="1.4.0",
        ui_theme="dark"
    ))
    
    # Style B: Direct Instantiation (provides static checks and autocomplete)
    # .integrate(SpeculaIntegration(
    #     title="User Portal API",
    #     version="1.4.0",
    #     ui_theme="dark"
    # ))
)
\`\`\`

---

## Configuration Reference (\`SpeculaConfig\`)

When you configure Specula, your parameters map to the \`SpeculaConfig\` dataclass. The primary settings available are:

| Parameter | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| **Info / Branding** | | | |
| \`title\` | \`str\` | \`"Aquilia API"\` | Name of the API, visible in the UI header and spec exports. |
| \`version\` | \`str\` | \`"1.0.0"\` | The current API release version. |
| \`description\` | \`str\` | \`""\` | Detailed description of the API. |
| \`ui_theme\` | \`str\` | \`"auto"\` | \`"auto"\` (matches system preferences), \`"light"\`, or \`"dark"\`. |
| \`ui_primary_color\`| \`str\` | \`"#22c55e"\` | Hex code for branding the main interface buttons and tags. |
| **URL Paths** | | | |
| \`ui_path\` | \`str\` | \`"/specula"\` | Browser path to view the Observatory HTML dashboard. |
| \`json_path\` | \`str\` | \`"/specula/spec.json"\`| JSON endpoint serving the raw OpenAPI 3.1.0 spec. |
| \`yaml_path\` | \`str\` | \`"/specula/spec.yaml"\`| YAML endpoint serving the raw OpenAPI 3.1.0 spec. |
| \`stream_path\` | \`str\` | \`"/specula/stream"\`| SSE stream pushing route updates to the UI. |
| \`mock_path\` | \`str\` | \`"/specula/mock"\` | Endpoint path for the mock server router. |
| **Feature Toggles** | | | |
| \`enabled\` | \`bool\` | \`True\` | Master toggle to enable or disable Specula routes. |
| \`include_internal\`| \`bool\` | \`False\` | Whether routes matching \`/_*\` are included in the spec. |
| \`detect_security\` | \`bool\` | \`True\` | Scan route guards and decorators to construct security schemes. |
| \`mock_server_enabled\`| \`bool\` | \`False\` | Set \`True\` to enable schema-synthesized mock responses. |
| \`spec_cache_ttl\` | \`int\` | \`60\` | In-memory cache duration (in seconds) for compiled spec payloads. |

---

## Hot-Reloading SSE Stream (\`/specula/stream\`)

During development, Aquilia runs with file watchers. When you modify controller code, the worker process reloads. 

Specula exposes a native ASGI Server-Sent Events (SSE) stream endpoint at \`/specula/stream\`. When the dashboard is loaded in a browser, it subscribes to this stream. When a reload happens, the server pushes an invalidation event down the pipe:

\`\`\`json
{"event": "update", "data": {"status": "invalidated", "version": "2.0.0"}}
\`\`\`

The Observatory frontend listens to this event and immediately fetches the newly compiled specification and routes dynamically, refreshing the client view with zero hard refreshes.

---

## Production Security Locks

By default, the Specula Observatory is fully open. In production environments, you can lock access down to authenticated users with specific roles:

\`\`\`python
workspace.integrate(Integration.specula(
    title="Corporate Core API",
    docs_auth_required=True,
    docs_roles=["admin", "ops-team"]
))
\`\`\`

When \`docs_auth_required\` is enabled, the Specula controller inspects the request context using the configured \`AuthMiddleware\` pipeline. If the visitor lacks the required roles, they receive a \`403 Forbidden\` response.
`,

    "security.md": `# Automated Security & Clearance Detection

Specula integrates with Aquilia's security pipeline to automatically detect, map, and document authentication configurations. It translates pipeline guards and clearance levels into standard OpenAPI security requirements and rich custom metadata tags.

---

## Inferred Security Schemes

The spec builder scans your controllers' and routes' pipeline nodes and handler decorators to identify authentication mechanisms. It automatically registers and configures security definitions in the OpenAPI \`components.securitySchemes\` catalog:

| Inferred Guard Class Name | Generated Security Scheme | Schema Details |
| :--- | :--- | :--- |
| \`AuthGuard\` / \`Auth\` / \`@authenticated\` | \`bearerAuth\` | HTTP Bearer token (JWT) authentication. |
| \`ApiKeyGuard\` / \`ApiKey\` | \`apiKeyAuth\` | \`X-API-Key\` request header authorization. |
| \`SessionGuard\` / \`Session\` | \`cookieAuth\` | Session-based cookie verification (\`session\`). |
| \`BasicAuthGuard\` / \`Basic\` | \`basicAuth\` | HTTP Basic authentication. |
| \`OAuth2Guard\` / \`OAuth2\` | \`oauth2\` | OAuth2 Authorization Code flow. |

\`\`\`python
# Specula automatically registers bearerAuth with ["read", "write"] scopes
class OrderController(Controller):
    pipeline = [AuthGuard(), ScopeGuard("read", "write")]
    
    @GET("/")
    async def list_orders(self, ctx: RequestCtx): ...
\`\`\`

---

## Integrated Clearance Detection

Specula integrates directly with the \`aquilia.auth.clearance\` system to identify role-based and attribute-based clearance levels. 

The builder resolves the merged clearance level from the controller boundary and individual route overrides:
1. **Public Routes**: If the effective clearance resolves to \`AccessLevel.PUBLIC\` (e.g. via \`@grant(level=AccessLevel.PUBLIC)\`), security requirements are omitted for that route.
2. **Protected Routes**: If the effective clearance is higher than public, \`bearerAuth\` is automatically registered as a requirement.

---

## Rich Metadata Extensions (\`x-specula-security\`)

To support advanced observability and client generation, Specula embeds the full resolved authorization metadata in a custom vendor extension block (\`x-specula-security\`) inside each route's spec operation:

\`\`\`json
"x-specula-security": {
  "authenticated": true,
  "guards": [
    {
      "name": "RoleGuard",
      "type": "instance",
      "roles": ["admin", "compliance"],
      "require_all": false
    }
  ],
  "clearance": {
    "level": "INTERNAL",
    "level_value": 30,
    "entitlements": ["view_audit_logs", "override_fees"],
    "conditions": ["IsDuringOfficeHours", "IPRangeCondition"],
    "compartment": "finance"
  }
}
\`\`\`

This vendor block exposes:
* **\`authenticated\`**: Boolean flag indicating if verification is required.
* **\`guards\`**: Detailed list of active pipeline guard configurations, including roles, scopes, optional tags, resources, and evaluation settings.
* **\`clearance\`**: The full clearance metadata, including \`level\` name, \`level_value\` integer, required \`entitlements\` lists, active \`conditions\` names, and matching resource \`compartment\` boundaries.
`
  },
  "1.3.1": {
    "README.md": `# Aquilia v1.3.1 Release Notes — "Backend Refactoring"

Aquilia v1.3.1 introduces a major rewrite of the authentication (\`aquilia.auth\`) and authorization subsystems. It moves away from rigid string-based strategies and hardcoded guard adapters in favor of a pluggable, class-based backend architecture, a unified permission engine, hardened session serialization, and token clock-skew tolerance.

## Table of Contents

1. [Pluggable Authentication Backends](backends.md)
   * The new \`AuthBackend\` protocol.
   * Built-in backends: \`TokenBackend\`, \`SessionBackend\`, \`PasswordBackend\`, \`ApiKeyBackend\`.
   * The \`resolve_backend\` helper and loading configuration.
2. [Unified Permission & Authorization Engine](guards.md#permissionengine)
   * Role DAG (Directed Acyclic Graph) inheritance.
   * Policy callables and scope checks.
   * Pluggable Flow Guards: \`AuthGuard\`, \`RoleGuard\`, \`ScopeGuard\`, \`PolicyGuard\`.
   * Context-First Decorators: \`@authenticated\`, \`@roles_required\`, \`@scopes_required\`, \`@optional_auth\`.
3. [Session Security Hardening](sessions.md)
   * Elimination of stale permission state in session cookies.
   * The lightweight \`AuthPrincipal\` serialization format.
   * Dynamic resolution of roles and scopes on every request.
4. [Migration Guide](migration.md)
   * Upgrading configuration settings from \`strategies\` to \`backends\`.
   * Replaced classes, decorators, and middleware.

---

## Key Refactoring Goals

1. **Pluggability**: Unify all authentication strategies (Bearer JWTs, Session cookies, Username/Password, API keys) under a single, reusable backend protocol.
2. **Dynamic Privileges**: Resolve permissions, roles, and scopes fresh from the database or cache on every request, preventing privilege escalation through stale session states.
3. **API Simplification**: Consolidate five parallel authorization subsystems (RBAC, ABAC, Clearance, Policy DSL, and custom adapters) into a single, cohesive \`PermissionEngine\`.
4. **Resiliency**: Handle clock drift in distributed clusters by introducing native clock-skew tolerance.
5. **DI Scope Performance**: Deprecate the class/object-based \`ServiceScope\` Enum in favor of high-performance raw string literals backed by \`typing.Literal\` to eliminate import-time namespace scanning and runtime attribute lookup overhead.`,

    "backends.md": `# Pluggable Authentication Backends

In Aquilia v1.3.1, the authentication workflow is decomposed into single-responsibility **Backends**. A backend is a class that conforms to the \`AuthBackend\` protocol. It is responsible for accepting a credential dictionary and resolving it to an \`Identity\`.

## The \`AuthBackend\` Protocol

The \`AuthBackend\` protocol is defined in \`aquilia.auth.backends.base\` using Python's structural subtyping (\`typing.Protocol\`):

\`\`\`python
from typing import Any, Protocol, runtime_checkable
from aquilia.auth.core import Identity

@runtime_checkable
class AuthBackend(Protocol):
    def accepts(self, credentials: dict[str, Any]) -> bool:
        """Return True if the backend supports the provided credentials."""
        ...

    async def authenticate(self, credentials: dict[str, Any]) -> Identity | None:
        """Verify credentials and resolve them to an Identity.
        
        May raise specific auth faults (e.g., AUTH_TOKEN_EXPIRED, AUTH_INVALID_CREDENTIALS).
        """
        ...
\`\`\`

---

## Built-in Backends

Aquilia provides four native backends to cover standard flows:

### 1. \`TokenBackend\`
Validates JWT Bearer tokens. It verifies signatures, checks \`exp\` and \`nbf\` claims (with clock-skew tolerance), and validates token revocation via \`TokenManager\`.
* **Accepted Credentials**: \`{"token": str}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, token_manager: TokenManager, identity_store: IdentityStore)
  \`\`\`

### 2. \`SessionBackend\`
Restores identity from a cookie-backed session. It looks up the \`identity_id\` from the session data or from \`session.principal\`, and fetches the corresponding active identity.
* **Accepted Credentials**: \`{"session": Session}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, identity_store: IdentityStore)
  \`\`\`

### 3. \`PasswordBackend\`
Authenticates user login credentials. It checks for IP/username brute-force lockouts, resolves usernames or email addresses to an identity, compares password hashes, handles password re-hashing when algorithm parameters upgrade, and checks for multi-factor authentication (MFA) requirements.
* **Accepted Credentials**: \`{"username": str, "password": str}\`
* **Constructor**:
  \`\`\`python
  def __init__(
      self,
      identity_store: IdentityStore,
      credential_store: CredentialStore,
      password_hasher: PasswordHasher,
      rate_limiter: RateLimiter | None = None,
      login_attributes: tuple[str, ...] = ("email", "username", "login"),
  )
  \`\`\`

### 4. \`ApiKeyBackend\`
Authenticates API requests via an opaque API key. It hashes the incoming key using \`HMAC-SHA256\` for lookup, checks expiration and revocation status, and verifies that the key carries the required scopes if requested.
* **Accepted Credentials**: \`{"api_key": str, "required_scopes": list[str] | None}\`
* **Constructor**:
  \`\`\`python
  def __init__(self, credential_store: CredentialStore, identity_store: IdentityStore)
  \`\`\`

---

## The Backend Resolver

To simplify instantiation, the \`resolve_backend\` function maps string identifiers, class references, or dotted import paths to their instantiated backends:

\`\`\`python
def resolve_backend(b: Any, auth_manager: Any) -> Any:
    """Resolve a backend reference (instance, class, short name, or dotted path)
    into an instantiated backend object.
    """
    ...
\`\`\`

It maps:
* Short names: \`"token"\` (TokenBackend), \`"session"\` (SessionBackend), \`"password"\` (PasswordBackend), \`"api_key"\` (ApiKeyBackend).
* Class references: \`TokenBackend\`, \`SessionBackend\`, \`PasswordBackend\`, \`ApiKeyBackend\`.
* Dotted paths: \`"my_app.auth.backends.CustomBackend"\`.

### Example Configuration in \`workspace.py\`

\`\`\`python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    backends = [
        "aquilia.auth.backends.TokenBackend",
        "aquilia.auth.backends.SessionBackend",
        "my_project.auth.CustomBackendClass",  # Dotted class path
    ]
\`\`\``,

    "guards.md": `# Unified Authorization, Middleware & Decorators

Aquilia v1.3.1 unifies identity resolution and request-scoped checks into a single middleware and permission engine.

---

## 1. Unified \`PermissionEngine\`

The \`PermissionEngine\` (defined in \`aquilia.auth.permissions\`) is the central engine for evaluating roles, scopes, and policies. It replaces five separate historical systems and runs check assertions that raise appropriate exceptions on denial.

### Core API Methods

* \`define_role(role: str, *, permissions: list[str] | None = None, inherits: list[str] | None = None) -> None\`: Declare a role and its transitively implied parents.
* \`role_implies(role: str, target: str) -> bool\`: Query the role DAG structure.
* \`register_policy(key: str, policy: PolicyCallable) -> None\`: Define a rule matching the signature \`(identity, resource) -> bool\`.
* \`check_role(identity: Identity, role: str) -> None\`: Asserts role ownership; raises \`AUTHZ_INSUFFICIENT_ROLE\` on failure.
* \`check_scope(identity: Identity, scope: str) -> None\`: Asserts scope ownership; raises \`AUTHZ_INSUFFICIENT_SCOPE\` on failure.
* \`check_policy(key: str, identity: Identity, resource: Any = None) -> None\`: Asserts policy assertion passes; raises \`AUTHZ_POLICY_DENIED\` on failure.
* \`has_role(identity: Identity, role: str) -> bool\`: Returns a boolean indicating role membership.
* \`has_scope(identity: Identity, scope: str) -> bool\`: Returns a boolean indicating scope membership.
* \`evaluate_policy(key: str, identity: Identity, resource: Any = None) -> bool\`: Returns a boolean indicating policy result.

---

## 2. Pluggable Flow Guards

Guards (defined in \`aquilia.auth.guards\`) evaluate context and raise exceptions on denial. They can be placed directly in request pipelines or used as raw classes (for zero-configuration defaults).

### \`AuthGuard\`
Verifies authentication status.
* **Optional Mode**: When \`optional=True\`, anonymous users are allowed.
* **Proactive Auth**: If the identity is not yet resolved, \`AuthGuard\` attempts to proactively extract and authenticate a Bearer token using DI container-resolved \`AuthManager\`.
* **Signature**: \`AuthGuard(auth_manager=None, optional=False)\`

### \`RoleGuard\`
Ensures the identity holds required roles.
* **Resolution**: Uses \`PermissionEngine\` if found in the DI container; otherwise, falls back to direct membership testing of \`identity.get_attribute("roles", [])\`.
* **Signature**: \`RoleGuard(*roles, engine=None, require_all=True)\`

### \`ScopeGuard\`
Ensures the identity holds required scopes.
* **Wildcards**: Supports the wildcard \`"*"\` scope.
* **Signature**: \`ScopeGuard(*scopes, require_all=True)\`

### \`PolicyGuard\`
Evaluates a policy registered in the permission engine.
* **Signature**: \`PolicyGuard(key, engine, resource=None)\`

---

## 3. Context-First Decorators

Decorators (defined in \`aquilia.auth.decorators\`) wrap handlers to execute guard checks and **inject parameters** into the handler's signature (e.g., \`identity\`, \`user\`, \`session\`, \`principal\`).

### \`@authenticated\`
Requires an authenticated identity.
* **Browser Redirection**: If a request is anonymous, has \`redirect_if_html=True\` or \`login_url\` configured, and accepts HTML, it performs a \`303 Redirect\` to the login page with a \`next\` query parameter.
* **Signature**:
  \`\`\`python
  def authenticated(
      func=None,
      *,
      login_url: str | None = None,
      redirect_if_html: bool = False,
      include_next: bool = True,
      next_param: str = "next",
      redirect_status: int = 303,
  )
  \`\`\`

### \`@roles_required\` / \`@scopes_required\`
Evaluates role or scope conditions before executing the controller action.
\`\`\`python
@roles_required("admin", "editor", require_all=False)
async def delete_post(self, ctx: RequestCtx) -> Response:
    ...
\`\`\`

### \`@optional_auth\`
Evaluates the proactive \`AuthGuard(optional=True)\` check. It injects the user if found but does not block anonymous traffic.

### \`@requires\`
Composes multiple guards (both classes and instances) sequentially:
\`\`\`python
@requires(AuthGuard, RoleGuard("admin"))
async def admin_only_action(self, ctx: RequestCtx) -> Response:
    ...
\`\`\`

---

## 4. Unified \`AuthMiddleware\`

The new unified \`AuthMiddleware\` (defined in \`aquilia.auth.middleware\`) coordinates credential resolution from backends on every incoming request.

* **Signatures & Parameters**:
  \`\`\`python
  def __init__(
      self,
      auth_manager: AuthManager,
      session_engine: SessionEngine | None = None,
      *,
      require_auth: bool = False,
      backends: list[AuthBackend] | None = None,
      logger: logging.Logger | None = None,
  )
  \`\`\`
* **Execution Flow**:
  1. **Phase 1: Session Resolution**: If \`session_engine\` is provided, resolves the session and binds it to \`ctx.session\` and \`request.state["session"]\`.
  2. **Phase 2: Credentials Extraction**: Extracts Bearer token, ApiKey, or Session from the request.
  3. **Phase 3: Backend Authentication**: Loops through pluggable \`backends\` (defaults to \`TokenBackend\` and \`SessionBackend\`). The first backend that accepts the credentials and returns an \`Identity\` completes the phase.
  4. **Phase 4: Requirement Enforcement**: If \`require_auth=True\` and no identity is resolved, returns a \`401 Unauthorized\` response immediately.
  5. **Phase 5: Propagation**: Propagates the resolved identity to \`request.state["identity"]\`, \`request.state["authenticated"]\`, and \`ctx.identity\`.
  6. **Phase 6: Downstream Execution**: Calls the next handler in the ASGI middleware chain.
  7. **Phase 7: Session Commitment**: Commits session modifications back to the storage adapter.`,

    "migration.md": `# Migration Guide: v1.3.0 to v1.3.1

Aquilia v1.3.1 consolidates and standardizes authentication and authorization. Follow this guide to upgrade your project.

---

## 1. Upgrading Configuration

The string-based \`strategies\` setting has been removed. You must now configure the list of identity-resolution backends using the \`backends\` parameter. Additionally, the rate-limiting and MFA settings have been promoted to direct configuration parameters on \`AquilaConfig.Auth\`.

### Legacy Configuration (v1.3.0)
\`\`\`python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    strategies = ["token", "session"]
\`\`\`

### Refactored Configuration (v1.3.1)
\`\`\`python
class auth(AquilaConfig.Auth):
    secret_key = Secret(env="AQ_SECRET_KEY", default="change-me")
    backends = [
        "aquilia.auth.backends.TokenBackend",
        "aquilia.auth.backends.SessionBackend",
    ]
    # Store type: "memory" or "redis"
    store_type = "memory"
    
    # Rate Limiting configuration parameters
    rate_limit_max_attempts = 5
    rate_limit_window_seconds = 900
    rate_limit_lockout_seconds = 3600
    
    # MFA settings
    mfa_enabled = False
    mfa_required = False
    
    # Clock skew tolerance (in seconds) for JWT validations
    clock_skew_seconds = 5
    
    # Audit trail activation
    audit_enabled = True
\`\`\`

---

## 2. Replaced & Removed Decorators

The legacy decorators \`AdminGuard\` and \`VerifiedEmailGuard\` have been removed.

* **\`AdminGuard\`**: Replace with \`@roles_required("admin")\`.
* **\`VerifiedEmailGuard\`**: Handle verification checks in your identity resolution backend (such as deactivating unverified users) or write a simple custom guard.

#### Before:
\`\`\`python
from aquilia.auth import AdminGuard

@AdminGuard
async def delete_item(ctx):
    ...
\`\`\`

#### After:
\`\`\`python
from aquilia.auth import roles_required

@roles_required("admin")
async def delete_item(ctx):
    ...
\`\`\`

---

## 3. Upgrading Flow Pipeline Guards

All legacy guard adapters (historically located in \`flow_guards.py\`) have been removed. Use the new first-class guards directly.

| Legacy Guard Class (v1.3.0) | Refactored Guard Class (v1.3.1) |
|---|---|
| \`RequireAuthGuard\` | \`AuthGuard\` |
| \`RequireRolesGuard\` | \`RoleGuard\` |
| \`RequireScopesGuard\` | \`ScopeGuard\` |
| \`RequirePolicyGuard\` | \`PolicyGuard\` |

### Pipeline Registration Example

#### Before:
\`\`\`python
from aquilia.auth.integration.flow_guards import RequireAuthGuard, RequireRolesGuard

pipeline.guard(RequireAuthGuard())
pipeline.guard(RequireRolesGuard("admin"))
\`\`\`

#### After:
\`\`\`python
from aquilia.auth.guards import AuthGuard, RoleGuard

# Raw classes can be passed if no parameters are required
pipeline.guard(AuthGuard)
pipeline.guard(RoleGuard("admin"))
\`\`\`

---

## 4. Upgrading Session Guards

The legacy \`SessionGuard\` class and \`@requires\` decorator in \`aquilia.sessions.decorators\` have been removed. Switch to the unified \`PermissionEngine\` and the unified \`@requires\` decorator.

#### Before:
\`\`\`python
from aquilia.sessions.decorators import SessionGuard, requires

class CustomSessionGuard(SessionGuard):
    async def check(self, session: Session) -> bool:
        return bool(session.data.get("special_user"))

@requires(CustomSessionGuard())
async def handler(ctx):
    ...
\`\`\`

#### After:
\`\`\`python
from aquilia.auth.guards import requires

class CustomGuard:
    def check(self, ctx: Any) -> None:
        from aquilia.auth.faults import AUTHZ_POLICY_DENIED
        session = getattr(ctx, "session", None)
        if session is None or not session.data.get("special_user"):
            raise AUTHZ_POLICY_DENIED()

@requires(CustomGuard())
async def handler(ctx):
    ...
\`\`\`

---

## 5. Removing the Fluent \`AuthConfig\` Builder

If you set up custom authentication containers in testing or bootstrapping scripts using the \`AuthConfig\` builder, you must remove it. Configure integrations directly using dictionary payloads or the \`AquilaConfig.Auth\` classes.

#### Before:
\`\`\`python
from aquilia.auth.integration.di_providers import AuthConfig

config = (
    AuthConfig()
    .rate_limit(max_attempts=3)
    .strategies(["token"])
    .build()
)
\`\`\`

#### After:
\`\`\`python
config = {
    "rate_limit": {
        "max_attempts": 3,
    },
    "security": {
        "backends": ["aquilia.auth.backends.TokenBackend"],
    }
}
\`\`\`

---

## 6. Deprecated APIs & Relocations

* **\`AuthManager.logout()\`**: Deprecated in favor of \`AuthManager.sign_out()\`. Calling \`logout()\` now raises a \`DeprecationWarning\` but will invoke \`sign_out()\` internally for backward compatibility.
* **\`OptionalAuthMiddleware\`**: Deprecated in favor of \`AquilAuthMiddleware(require_auth=False)\` or the new \`AuthMiddleware\` class.
* **\`RateLimiter\` relocation**: The \`RateLimiter\` class has been moved from the \`manager\` module to \`aquilia.auth.manager_types\` to prevent circular imports. Update imports if you reference it directly.
* **\`ServiceScope\` Enum class**: Deprecated in favor of plain string literals (e.g., \`"singleton"\`, \`"app"\`, \`"request"\`, \`"transient"\`, \`"pooled"\`, \`"ephemeral"\`) paired with \`typing.Literal\` type hints (\`ServiceScopeLiteral\`). Using \`ServiceScope.SINGLETON\` or other members will now emit a \`DeprecationWarning\`.`,

    "sessions.md": `# Session Security, AuthManager & RateLimiting

Aquilia v1.3.1 introduces substantial security improvements to cookie-based and session-based authentication to prevent privilege escalation, alongside a refined \`AuthManager\` API and a standalone \`RateLimiter\` utility.

---

## 1. Session Serialization Hardening

In previous versions of Aquilia, the full set of user roles, scopes, and attributes was serialized and stored directly inside the session store database (or client-side cookie):

\`\`\`python
# Old, insecure v1.3.0 implementation:
session["roles"] = identity.get_attribute("roles", [])
session["scopes"] = identity.get_attribute("scopes", [])
session["status"] = identity.status.value
\`\`\`

This optimization meant that if an administrator modified a user's permissions, suspended their account, or deleted them, the changes **would not take effect** for requests authenticated via session cookies until their session expired.

In Aquilia v1.3.1, session serialization has been hardened. The \`bind_identity\` function only writes core identifiers:

\`\`\`python
# Hardened v1.3.1 implementation:
session.mark_authenticated(AuthPrincipal.from_identity(identity))
session["identity_id"] = identity.id
if identity.tenant_id is not None:
    session["tenant_id"] = identity.tenant_id
\`\`\`

Notice that **roles, scopes, and user attributes are no longer written to the session store**.

### Active Identity Resolution
* The \`SessionBackend\` captures the active session credentials.
* It extracts the \`identity_id\` (either from \`session.principal\` or from \`session.data["identity_id"]\`).
* It fetches a fresh \`Identity\` object directly from the \`IdentityStore\` on **every single request**.
* Authorization guards evaluate roles and scopes against this fresh database/cache state.

---

## 2. Shared Manager Types: \`RateLimiter\`

To protect brute-force paths (such as username/password login), Aquilia v1.3.1 introduces a standalone \`RateLimiter\` class in \`aquilia.auth.manager_types\` (and re-exported in \`aquilia.auth.manager\` for backward compatibility).

* **Constructor & Parameters**:
  \`\`\`python
  def __init__(
      self,
      max_attempts: int = 5,
      window_seconds: int = 900,
      lockout_duration: int = 3600,
  )
  \`\`\`
  Tracks failed authentication attempts per key (typically a username or IP address) within a sliding time window.
* **Core API Methods**:
  * \`record_attempt(key: str) -> None\`: Records a failed attempt. If attempts exceed \`max_attempts\` within the window, locks out the key.
  * \`is_locked_out(key: str) -> bool\`: Checks if the key is currently locked out.
  * \`get_remaining_attempts(key: str) -> int\`: Returns attempts left before lockout.
  * \`reset(key: str) -> None\`: Clears attempt history for the key on successful authentication.

---

## 3. \`AuthManager\` Refactored APIs

The \`AuthManager\` class (defined in \`aquilia.auth.manager\`) is the central coordinator for authentication operations. The following APIs were updated:

### Token Revocation
The token revocation API now supports access tokens by extracting the unique JWT identifier (\`jti\`) and blacklisting it:
* \`async def revoke_token(self, token: str, token_type: str = "refresh") -> None\`:
  * If \`token_type == "refresh"\`, revokes the refresh token directly.
  * If \`token_type == "access"\`, validates the access token, extracts the \`jti\` claim, and revokes it so subsequent validations reject it.

### Deprecated \`logout()\`
* **Signature**: \`async def logout(self, identity_id=None, session_id=None, access_token=None, refresh_token=None) -> None\`
* **Status**: **Deprecated** in favor of \`sign_out()\`. Raises a \`DeprecationWarning\` when called.

---

## 4. \`SessionAuthBridge\`

The \`SessionAuthBridge\` coordinates actions between \`AuthManager\` and \`SessionEngine\`:
* \`create_auth_session(identity, request, token_claims=None)\`: Resolves and binds authentication credentials to a new session.
* \`rotate_on_privilege_escalation(session, response)\`: Rotates the session ID (session fixation protection) after an escalating event (such as completing an MFA challenge).
* \`logout(session, response)\`: Destroys the current session.
* \`logout_all_devices(identity_id)\`: Revokes and purges all active session identifiers linked to a given identity ID across the session store.`
  }
};
