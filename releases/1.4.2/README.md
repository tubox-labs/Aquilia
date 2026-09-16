# Aquilia v1.4.2 Release Notes — "Depths Unknown"

Aquilia v1.4.2 is a **forensic-verification release** that follows v1.4.1 "Safe Harbor".
A third audit wave re-verified every finding of the AniWave post-implementation report
against the framework source — nine specialized subsystem auditors plus two independent
cross-review validators — then repaired everything it confirmed, along with a large set
of previously-unreported defects found by an aggressive independent hunt. Several of the
new findings were more severe than anything in the original report: a production
SendGrid integration sending unauthenticated mail for its entire life, one HTTP
client pool that poisoned cross-request data on abandoned streams, a SQLite layer where
one request's rollback silently destroyed other requests' committed writes, and a dev
CLI that could delete its users' manifest declarations.

```bash
pip install --upgrade aquilia==1.4.2
```

Full forensic report: [`docs/AQUILIA_POST_IMPLEMENTATION_AUDIT_FIXES.md`](../../docs/AQUILIA_POST_IMPLEMENTATION_AUDIT_FIXES.md)

---

## Headline Repairs

```
┌────────────────────────────┐  ┌──────────────────────────────────────────┐
│  Every report finding      │  │  And beneath them, the unreported ones:  │
│  re-verified at runtime    │  │  HEAD framing, dead constructor headers, │
│  then fixed — one refuted  │  │  transaction bleed, worker death per     │
│  (stale after the 1.4.1    │  │  CancelledError, manifest destruction,   │
│  auth rebuild)             │  │  secrets leaking through projections     │
└────────────────────────────┘  └──────────────────────────────────────────┘
```

### The findings report — verdict and resolution

All framework findings in `AQUILIA_POST_IMPLEMENTATION_FINDINGS.md` verified true
against the current source except **F-CORE-06** (auth string-token DI — stale after the
1.4.1 auth rebuild; class and string tokens normalize to identical dotted keys). The
rest are fixed, each with a permanent regression test:

- **`Request.path_params`** is a property (contract path binding, clearance
  compartments, guard contexts, and debug pages all silently never saw path params).
- **Nested-contract errors** keep their real messages under dotted paths
  (`device.deviceId`), in both the engine's aggregation and `SealFault` details.
- **Boot is cwd-independent** — `Runtime.configure` passes the absolute workspace file
  (a wrong-cwd deployment previously served an unconfigured app, silently).
- **Singleton controllers** resolve from the owning module's DI container.
- **The `aq run` validator** resolves refs by import (the text-scraper falsely rejected
  framework/cross-module refs and crashed on `redis://` URLs); the discovery differ
  never removes manifest entries by default; `aq manifest update` refuses destructive
  writes on failed imports.
- **Contracts**: all three declaration styles return validated data on attribute
  access; `Optional[T]` honored with raw facets in `Annotated`; the default projection
  excludes silently-derived model columns (the **secrets leak** —
  `refresh_token_hash`-style columns no longer appear without explicit opt-in).
- **ORM upserts** accept FK-column keys (`user_id`) that `filter`/`create` always
  accepted.

### The independent hunt — worst new defects (all fixed)

| Defect | Impact before the fix |
|---|---|
| HEAD/204/304 responses misframed | HEAD on keep-alive blocked, misread, and poisoned the connection pool |
| `AsyncHTTPClient(headers=...)` never sent | The SendGrid provider's `Authorization` header was dead — **every SendGrid send was unauthenticated** |
| Cross-task SQLite transaction bleed | One request's rollback silently destroyed other requests' committed writes (they received normal pks) |
| `db.transaction()` leaked on `CancelledError` | The engine wedged permanently after one cancellation |
| No cross-process migration lock | Concurrent boots raced (3 processes → 2 failures) |
| Task body raising `CancelledError` | Killed its worker loop permanently; job frozen in RUNNING |
| Defeatable task timeouts | A body swallowing cancellation overran and was recorded as **success** |
| `stop()` on Python 3.12+ | Hung forever on a CancelledError-swallowing task |
| Redis pool exhaustion | Burst traffic silently dropped writes (30/40 ops failed silently) |
| Cache `clear()` prefix scan | Deleted **foreign** keys sharing the prefix (another app's sessions) |
| `MemoryBackend(max_size=0)` | Froze the entire event loop (infinite eviction loop, no await point) |
| CacheMiddleware through redis | Bodies corrupted on every HIT (bytes → repr string) |
| `aq manifest update` on failed import | Silently **emptied** controllers/services declarations |
| Dependency-failure propagation | Docstring-only — dependents stayed WAITING forever on all three backends |
| Unsatisfiable cron (Feb 30) | Fired hourly forever instead of never |

Plus the full tail: HTTP streaming/pooling/redirects/cookies/proxy/retry, cache tag
fidelity, task zombie-write guards, ORM field validation, admin session fixation,
env-superuser in production, username-enumeration timing, header injection, filter
fail-open (ACL bypass class), 1,063 broken doc links, and GUIDE.md §11/§22/§23
rewritten against the real APIs.

## Behavior changes to note when upgrading

- **HTTP client**: `total` timeout now bounds the whole body (escape hatch:
  `TimeoutConfig.slow()/no_timeout()`); responses larger than 64 MB fault
  (`max_response_size=None` disables); corrupt gzip raises `DecodingFault` (was: raw
  bytes passthrough); `read()` after `iter_bytes()` raises `StreamConsumedFault`;
  unknown session kwargs raise `TypeError`; the default client does not retry
  (opt in via `RetryConfig`/`HTTPClientBuilder.retry()`); `aquilia/http/pool.py` emits
  a `DeprecationWarning` (removal in 2.0.0).
- **Contracts**: nested error keys are dotted paths; silently-derived model columns
  leave the default output projection (a `RuntimeWarning` names them; declare
  `Spec.projections = {"full": "__all__"}` for the previous full output); implicit
  model derivation no longer auto-requires every column; per-field cast error
  messages drop the stacked `Cast failed for` prefixes (list children gain
  `item {i}:` labels).
- **Engine**: malformed JSON bodies with a JSON content-type now return an
  invalid-JSON fault (was: per-field "required" errors); queryset filter failures
  now fail closed with a 500 (was: unfiltered data returned).
- **Cache**: DI-built redis backends no longer double-prefix keys (existing
  double-prefixed entries age out via TTL — bump `key_version` to force a flush);
  `redis_decode_responses` default is now `False` (the effective behavior all along).
- **Tasks**: dependency-failed jobs become `FAILED` (were: WAITING forever);
  non-retryable faults (e.g. unresolvable `func_ref`) dead-letter immediately;
  unsatisfiable cron expressions raise at construction.
- **ORM**: `order()`/`values()`/`only()`/`defer()`/`group_by()` raise on unknown
  fields (were: silent no-ops); aware datetimes are stored UTC-normalized on sqlite.
- **Admin**: the env-superuser fallback is refused outside dev/test mode; admin
  sessions rotate their ID on login and re-resolve the identity per request; `aq admin`
  scaffolds admin-scoped sessions (`path_prefix="/admin"`, `persist_anonymous=False`,
  `cookie_secure=True`).

## Verification

- Complete suite: **10,053 passed, 0 failed, 9 skipped** (407 new regression tests
  across 9 new test files; baseline 9,646).
- Every reported finding re-verified against source before fixing; every fix
  reproduced at runtime first.
- `ruff check` clean across the `aquilia/` package.
- Docs: every import statement in GUIDE.md/README.md executed against the package;
  1,063 broken doc links repaired.

## Known deferred items (maintainer decisions recorded in the audit report)

- Token→session identity binding: kept and now documented (CSRF implications noted);
  an opt-out flag needs an authentication-semantics decision.
- Engine throttle-before-guards ordering: interceptors remain the correct seam.
- The `otel` subsystem remains unwired (documented as manual/experimental).
