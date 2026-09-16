# Aquilia v1.4.2

Release date: 2026-09-16
Release Name: "Depths Unknown"

## Summary

Aquilia v1.4.2 is a forensic-verification release. A third audit wave re-verified every finding of the AniWave post-implementation findings report against the framework source — nine specialized subsystem auditors plus two independent cross-review validators — and repaired everything it confirmed, along with a large set of previously-unreported defects found by an aggressive independent hunt. The worst new findings were more severe than anything in the original report: the HTTP client's constructor `headers=` were never sent (a production SendGrid integration ran unauthenticated its entire life), abandoned streams poisoned the shared connection pool with cross-request corruption, one request's SQLite rollback silently destroyed other requests' committed writes, a task body raising `CancelledError` killed its worker permanently, and the dev CLI could silently delete hand-written manifest declarations.

Every fix was reproduced at runtime before being fixed and is covered by permanent regression tests. Full report: `docs/AQUILIA_POST_IMPLEMENTATION_AUDIT_FIXES.md`; release documentation: `releases/1.4.2/README.md`.

## Key Changes

- **Core**: `Request.path_params` is a property; nested-contract errors flatten to dotted paths with real messages; boot is cwd-independent; singleton controllers resolve from the owning module container; filter failures fail closed; `Response(headers=...)` validates; malformed JSON surfaces as invalid-JSON.
- **HTTP client**: true incremental streaming; pool release gated on clean body completion; HEAD/204/304 framing; trailer parsing; total deadline; per-request `follow_redirects`; redirect cookies + intermediate draining; constructor headers/default params actually sent; streaming uploads; opt-in retries; proxy support (CONNECT + SNI to target); 64 MB response cap; `pool.py` deprecated.
- **DB/ORM**: cross-task transaction bleed eliminated; `CancelledError` rollback; cross-process migration lock; `RunPython` inside the history transaction; FK-column keys accepted across the upsert family; unknown-field validation in `order`/`values`/`only`; UTC-normalized datetime storage; dialect-aware `ignore_conflicts` + real bulk batching.
- **Tasks**: dependency-failure propagation (`fail_orphaned_dependents`); worker survives job-level `CancelledError`; timeouts can't be swallowed; bounded `stop()`; scheduler dedup across processes; unsatisfiable cron faults at construction; `attempt_epoch` zombie-write guard; non-retryable faults dead-letter immediately.
- **Cache**: registry-scoped `clear()` (no more foreign-key deletion); `BlockingConnectionPool`; `None` caching; `l1_ttl` wired; tags on bulk paths; atomic `touch`; composite increment fix; full-fidelity `get_many`; event-loop hang guard; middleware body round-trip; uniform never-raise surface.
- **CLI/manifest**: import-based `aq run` validation; validate-before-mutate; non-zero exit codes; never-remove differ default with `--prune` opt-in; `auto_discover=False` respected; `aq manifest update` refuses destructive writes, detects real controllers, emits modern syntax.
- **Contracts**: attribute access returns validated data for all declaration styles; `Optional[T]` honored with raw facets; `ClassVar` excluded; bare `Field()` faults; implicit model derivation non-required; **default projection excludes silently-derived model columns (secrets-leak fix)**; clean list-child error labels.
- **Auth/sessions/admin**: pre-auth admin routes public; session path-prefix scoping + `persist_anonymous`; session-ID rotation on admin login; identity re-resolution per request; env-superuser gated to dev/test with timing-safe compare; password-backend timing parity; `aq admin` scaffolds secure, admin-scoped sessions.
- **Docs**: GUIDE.md §11/§22/§23 rewritten against real APIs; every import statement runtime-verified; 1,063 broken doc links repaired.

## Verification

Complete suite: 10,053 passed, 0 failed, 9 skipped (407 new regression tests across 9 new test files; baseline 9,646). `ruff check` clean across the framework. One report finding refuted (F-CORE-06 — stale after the 1.4.1 auth rebuild).
