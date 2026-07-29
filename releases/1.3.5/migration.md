# Migration Guide — Aquilia v1.3.5

Aquilia v1.3.5 is a feature release with **no API removals or signature changes**. Every workspace, manifest, task, and mail configuration from 1.3.4 continues to work without modification.

The tasks, mail, and HTTP work is fully backward compatible. The **Contracts audit ships four behavioral corrections** — each replacing behavior that was incorrect — which require a review pass if your application uses nested Contracts, to-many Lenses, or integer fields fed by JSON. Those are covered first, since they are the only part of this release that can change how existing code behaves.

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

For tasks and mail, nothing else is required. If you change no configuration, those subsystems behave exactly as in v1.3.4:

- Tasks run on `MemoryBackend`, single process.
- Mail sends inline, inside the request.
- No addresses are suppressed.
- No deduplication is applied.

Contracts require a review pass — see [Migration 0](#migration-0--contracts-behavioral-review) below.

---

## Upgrade Checklist

1. `pip install aquilia==1.3.5`
2. **Review Contract behavioral changes — see [Migration 0](#migration-0--contracts-behavioral-review).**
3. Run your test suite. Expect failures only where a nested Contract rule was previously inert, or a to-many Lens was serialized without prefetching.
4. *(Optional)* Generate Contract type stubs: `aq contracts stubs myapp.contracts`.
5. *(Optional)* Migrate `seal_*` validators to `@ward` — see [Migration 7](#migration-7--seal_-validators-to-ward).
6. *(Optional)* Move tasks to a durable backend — see below.
7. *(Optional)* Enable background mail delivery — see below.
8. *(Optional)* Wire provider webhooks for bounce handling.
9. If you use SendGrid or testing helpers, note that third-party `httpx` is no longer required as Aquilia uses native `aquilia.http`.
10. If you use DKIM, run `aq mail check` and install `aquilia[mail-dkim]`.
11. Remove any hand-rolled job deduplication in favour of `dedup="skip"`.
12. Remove any workaround that parsed `repr`-form job results.

---

## Migration 0 — Contracts Behavioral Review

**Required if your application uses Contracts.** Four corrections can change whether an existing payload is accepted.

### 0.1 — Nested Contract rules are now enforced

**What changed.** A nested Contract was validated structurally only. Every `@ward` method and every `validate()` override declared on a nested Contract was silently skipped. They now run.

**Why.** `Sigil.validate()` recursed into the child's compiled schema rather than instantiating the child Contract, so the ward phase was never reached. A nested Contract expressing an authorization check enforced nothing.

**How to check.** Find nested Contracts that declare rules:

```bash
# Contracts referenced by another Contract's field, that declare a ward
grep -rn "@ward\|def validate(self" --include="*.py" myapp/
```

For each, confirm the rule is one you actually want enforced. A rule written years ago against an assumption that no longer holds will now start rejecting live traffic.

```python
class LineItem(Contract):
    qty = IntFacet()

    @ward
    def qty_positive(self, data):
        if data["qty"] < 1:
            self.reject("qty", "Must be at least 1")

class Order(Contract):
    items: list[LineItem] = None

# v1.3.4: True  (the ward never ran)
# v1.3.5: False, errors = {"items": {"0": {"qty": ["Must be at least 1"]}}}
Order(data={"items": [{"qty": 0}]}).is_sealed()
```

**Also affected: async wards.** A Contract whose *nested* child declares `@ward(mode="async")` now correctly reports `has_async_wards is True`, so calling `is_sealed()` raises `ContractAsyncMismatchFault` instead of skipping the ward. Switch those call sites to `is_sealed_async()`.

Details: [Nested Validation Pipeline](contracts_pipeline.md).

### 0.2 — `Lens(many=True)` raises on an unresolved relation

**What changed.** An un-awaited related manager produced an empty list. It now raises `LensUnresolvedFault` (`BP503`).

**Why.** `[]` is indistinguishable from "this record genuinely has no related rows", so the previous behavior shipped wrong data to clients with no signal.

**How to fix.** Three options:

```python
# 1. Prefetch — best for hot paths
order = await Order.objects.prefetch_related("items").get(pk=1)
OrderContract(instance=order).data

# 2. Materialize explicitly
order.items = await order.items.all()
OrderContract(instance=order).data

# 3. Use the new async serializer, which awaits for you
await OrderContract.to_dict_async(order)
```

### 0.3 — Malformed-body error shape changed

**What changed.** A scalar or list request body previously produced a "This field is required" error per field. It now produces one document-level error.

```python
# v1.3.4
UserContract(data="not an object").errors
# {"name": ["This field is required"], "email": ["This field is required"]}

# v1.3.5
UserContract(data="not an object").errors
# {"__all__": ["Expected an object, got str"]}
```

**Who is affected.** Clients that parse a 422 response body and assume every key is a field name. Treat `__all__` as a document-level error and render it separately from field errors.

### 0.4 — `IntFacet` rejects fractional input

**What changed.** `3.9` was silently truncated to `3`. It is now rejected. `3.0` is still accepted.

**Why.** `int(3.9)` returned `3` while the string `"3.9"` was correctly rejected — the same logical input behaved differently depending on wire type. Silent truncation of a quantity or a price in cents is a data-integrity bug that surfaces far from its cause.

**How to fix.** If a client legitimately sends fractional values you intend to round, do it explicitly before validation, or use `FloatFacet`/`DecimalFacet` and round in your handler.

### 0.5 — `"__minimal__"` projections return fewer fields

**What changed.** `"__minimal__"` stored an empty placeholder that no code resolved. Because an empty set is falsy, the per-field filter passed *every* field. It now resolves to primary-key facets plus every `read_only` facet.

**Who is affected.** Anyone using `"__minimal__"`. The previous output — all fields, including ones deliberately kept private — was never correct. Verify the new field set matches what the projection was meant to expose.

---

## Migration 7 — `seal_*` Validators to `@ward`

**Optional in 1.x. Required before 2.0.0.**

Methods named `seal_*` or `async_seal_*` still register as validators and still run, but now emit a `DeprecationWarning`.

### Find every affected method

```bash
python -W error::DeprecationWarning -c "import myapp.contracts"
```

Or fail the test suite on it:

```toml
[tool.pytest.ini_options]
filterwarnings = ["error::DeprecationWarning"]
```

Registration happens at class-body evaluation, so importing the module is enough — no request needs to run.

### Before

```python
class OrderContract(Contract):
    def seal_total(self, data):
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    async def async_seal_stock(self, data):
        if not await in_stock(data["sku"]):
            self.reject("sku", "Out of stock")
```

The name was the registration. Renaming `seal_total` during a cleanup removed the rule with no error and no failing test.

### After

```python
class OrderContract(Contract):
    @ward
    def total_not_negative(self, data):          # rename is now safe
        if data["total"] < 0:
            self.reject("total", "Must not be negative")

    @ward(mode="async")
    async def stock_available(self, data):
        if not await in_stock(data["sku"]):
            self.reject("sku", "Out of stock")
```

Two things change beyond the decorator: `mode="async"` becomes explicit rather than inferred from `iscoroutinefunction`, and methods can be renamed to describe the rule.

**Intermediate step:** adding `@ward` without renaming silences the warning immediately, since the decorator is the registration and the name becomes irrelevant.

```python
@ward
def seal_total(self, data): ...    # no warning; rename later
```

Details: [Stub Generation & Deprecations](contracts_tooling.md#deprecated-the-seal_--async_seal_-prefix-convention).

---

## Migration 8 — Adopt Contract Type Stubs

**Optional.** Makes Contract fields visible to `mypy` and `pyright`.

### Before

```python
contract = UserContract(data=payload)
contract.is_sealed()
reveal_type(contract.email)   # Any
contract.emial                # typo survives review
```

### After

```bash
aq contracts stubs myapp.contracts
git add myapp/contracts.pyi
```

```python
reveal_type(contract.email)   # str
contract.emial                # error: "UserContract" has no attribute "emial"
```

### Keeping stubs honest

```yaml
- name: Check Contract stubs are current
  run: aq contracts stubs myapp.contracts --check
```

`--check` exits non-zero on a missing or stale stub and prints the regeneration command. Generation is deterministic, so it cannot fail at random.

Details: [Stub Generation & Deprecations](contracts_tooling.md).

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

**The `seal_*` / `async_seal_*` Contract validator naming convention.** Deprecated in 1.3.0, removed in 2.0.0.

Behavior is unchanged in 1.x — these methods continue to register and run exactly as before. Declaring one now emits a `DeprecationWarning` naming its exact replacement decorator. Migration is mechanical; see [Migration 7](#migration-7--seal_-validators-to-ward).

Nothing else was deprecated.

## Removed Features

The third-party `httpx` dependency was removed in favour of the native `aquilia.http` client. No public API changed. See [Native HTTP Client](http_native.md).

## Breaking Changes

The tasks, mail, and HTTP work introduces no breaking changes.

**Contracts ships four behavioral corrections**, each replacing behavior that was incorrect:

| Change | Previously | Now | Action |
|---|---|---|---|
| Nested Contract rules enforced | Nested `@ward` / `validate()` never ran | Runs, and rejects | Review nested Contracts — see [0.1](#01--nested-contract-rules-are-now-enforced) |
| `Lens(many=True)` unresolved | Returned `[]` | Raises `LensUnresolvedFault` | Prefetch, materialize, or use `to_dict_async()` — see [0.2](#02--lensmanytrue-raises-on-an-unresolved-relation) |
| Malformed-body errors | Per-field "required" | `{"__all__": [...]}` | Update clients that parse 422 bodies — see [0.3](#03--malformed-body-error-shape-changed) |
| `IntFacet` fractional input | `3.9` became `3` | Rejected | Round explicitly, or use `FloatFacet` — see [0.4](#04--intfacet-rejects-fractional-input) |

`"__minimal__"` projections also return a restricted field set now; the previous output was never correct. See [0.5](#05--__minimal__-projections-return-fewer-fields).

Two further behavior changes worth noting, neither an API break:

- With `dkim_enabled=True` and an incomplete configuration, sends now fail rather than shipping unsigned mail. Run `aq mail check` after enabling DKIM. See [CLI Changes](cli.md).
- A Contract with async wards *nested* beneath it now correctly raises `ContractAsyncMismatchFault` from `is_sealed()`. Previously it reported no async wards and skipped them silently.

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
| `Contract` public API | No signature changes. `is_sealed()` / `is_sealed_async()` gained an optional keyword-only `groups` parameter, defaulting to prior behavior. |
| `@ward` | `order`, `when`, and `groups` are optional; a bare `@ward` behaves exactly as before |
| `Spec` | `frozen` and `fail_fast` both default to `False` — prior behavior |
| Validation messages | Byte-identical unless an i18n catalog defines the `contracts.` namespace |
| `get_nested_contract_cls()` | Still present, now delegating to `resolve_nested()` |
| Contract `.pyi` stubs | Entirely opt-in; not generating them changes nothing |

---

## Known Issues

- **Redis backend lacks automated test coverage** in this release; the SQL backend carries the durable-path integration tests. The Redis implementation is exercised manually and by the shared backend contract.
- **Mailgun signature verification is opt-in.** Omitting `signing_key` parses without verification and logs a warning. Treat it as required in production.
- **No built-in webhook route.** Applications wire `parse_*` and `process_webhook` into their own controller, so path, authentication, and CSRF policy stay under application control.
- **Workflow steps whose parent failed remain `WAITING`** rather than being cancelled. They will not run; inspect them with `failed_jobs()`.
- **Generic Contracts (`Contract[T]`) are not supported.** `Contract.__class_getitem__` already means *projection* (`UserContract["public"]`), so type parameterization needs an API decision: dispatch on argument type (backward compatible, but one syntax with two meanings), or move projections to an explicit method (cleaner, but breaks every existing subscript call site). `typing.Self`, `Protocol`, and `NewType` resolution are blocked behind the same decision. Deferred rather than guessed.
- **`.pyi` stubs replace their module for the type checker.** The generator reproduces the whole module surface, not only its Contracts. Anything it cannot render faithfully is emitted as `Any` and named in the command output.
- **`to_dict_async()` awaits relations sequentially.** Prefetching remains the right choice on hot paths; the async path exists so a missing prefetch degrades performance rather than raising.

---

## Related

- [Release Overview](README.md)
- [Distributed & Persistent Backends](distributed_tasks.md)
- [Workflows & DAGs](workflows.md)
- [Idempotency & Deduplication](idempotency.md)
- [Mail Delivery Queue](mail_queue.md)
- [Bounce Handling & Suppression](bounces_suppression.md)
- [Mail Security & MIME](mail_security.md)
- [Contracts — Nested Validation Pipeline](contracts_pipeline.md)
- [Contracts — Validation Control & Typing](contracts_validation.md)
- [Contracts — Stub Generation & Deprecations](contracts_tooling.md)
- [CLI Changes](cli.md)
- [Bug Fixes](bugfixes.md)
