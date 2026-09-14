# Migration Audit Response in v1.4.1

During the port of a real NestJS backend (AniWave: 46 routes, 6 modules,
108 tests) to native Aquilia, 27 framework findings were recorded. In
v1.4.1 every finding was **independently re-reproduced against the
framework, root-caused, fixed in the framework, and covered by permanent
regression tests**. The complete per-finding report — root cause, files
changed, tests, and verification commands — is
[`docs/AQUILIA_MIGRATION_AUDIT.md`](../../docs/AQUILIA_MIGRATION_AUDIT.md) §7;
the original audit is preserved verbatim above it.

This document is the summary.

---

## Critical (both confirmed exactly as reported)

| Finding | Defect | Fix |
|---|---|---|
| **F-01** | `ArrayField.base_field` was never serialized — generated migrations contained a bare `fields.ArrayField()` that could not even be imported | `ArrayField.deconstruct()` serializes `base_field` (nested deconstruct dict) + `size`; the codegen renders `fields.ArrayField(base_field=fields.TextField(), size=10)`; `rebuild_field()` rebuilds the nested field |
| **F-02** | FK column types were resolved through the live model registry at apply time — `aq db migrate` never imports workspace models, so UUID-keyed targets rendered `INTEGER` columns (un-appliable DDL: *"incompatible types: integer and uuid"*) | `Reference` now carries the referenced PK's field spec (`to_field`, `to_field_kwargs`) captured at generation time; `ColumnState.sql_type()` renders FK columns from it, making migrations fully self-contained |

Both verified against live PostgreSQL: migrations with UUID FKs and array
columns generate, load in a clean process, and apply cleanly.

## Major

| Finding | Fix |
|---|---|
| **F-03** `CompositePrimaryKey` exported but unwired | Full wiring: `Meta.primary_key` validation, no surrogate `id`, table-level `PRIMARY KEY` in DDL + migrations, tuple `pk`, composite WHERE in save/get/delete/refresh, zero drift |
| **F-04** CLI destroyed multi-line `.module()` blocks | Format-independent (paren-balanced) extraction; undiscovered and unreadable blocks preserved verbatim; AST-based insertion when no integrations marker exists |
| **F-05** `--route-prefix` ignored | Plumbed through `update_workspace_config(overrides=…)` |
| **F-06** Route `status_code=` never applied | `_to_response(result, status_code=…)` applies it to all implicit conversions; explicit `Response` untouched |
| **F-07** Duplicate headers collapsed (multi `Set-Cookie` lost) | Transport returns raw field-line lists; `_raw_headers` preserved; `get_headers()` returns every value; `cookies` sees all cookies |
| **F-08** Lazy bodies raced connection recycling | Response owns its connection until the body is consumed; single release point; pools never resurrect into a closed pool |
| **F-09** `get_or_create`/`update_or_create` not concurrency-safe | Atomic `ON CONFLICT DO NOTHING` path for unique-constrained lookups (+ two latent detection bugs fixed); 100-writer stress on PostgreSQL: 1 row, 1 creator, 0 exceptions |
| **F-10** Bare facet class silently disabled validation | `Annotated[str, EmailFacet]` now instantiates and validates; constructor-requiring facets raise a clear definition-time error |
| **F-11** `depends_on` deprecation recommended a broken replacement | Both spellings verified to create DI links (already fixed in-tree); misleading per-boot deprecation warning withdrawn |
| **F-12** Auth middleware auto-activated from the config section | `AquilaConfig.Auth.enabled` defaults to `False` (opt-in); `Integration.auth(...)` still enables explicitly |

## Minor / Observations

F-13 honest dry-run · F-14 drift-free `aq db diff` (incl. PG adapter fixes:
index columns, PK flags, array types) · F-15 lazy task binding · F-16
stable `SealFault.errors` + no `[BP1xx]` leaks · F-17 TestClient inline
`?query` URLs · F-18 session-scoped app fixture + docs · F-19 redis-py 8
compat + `Secret.resolve()` alias · F-20 pluggable error renderer
(`ExceptionMiddleware(error_renderer=…)` / `FaultHandlingIntegration`) ·
F-21 GUIDE.md regenerated to match reality · F-22 boot noise (admin banner
gated on explicit integration; signing-warning provenance) · F-23 Specula
counts application routes · F-24 nanobind shutdown leaks (plan caches
cleared at exit) · F-25 FK `<attr>_id` raw-value property · F-26 int
converter 404 semantics **confirmed by design** · F-27 composed cache-key
layout documented.

## Framework defects found beyond the audit

- CONTRACT-domain faults rendered **500** instead of **400**.
- PostgreSQL adapter hardcoded `rowcount=1` for every INSERT — conflicted
  upserts reported themselves as created.
- `Model.create()` never snapshotted dirty-tracking state — create →
  modify → save re-INSERTed and violated the PK.
- `filter(<fk_column>=<UUID>)` bound raw `uuid.UUID` objects to the driver.
- `RETURNING "id"` auto-append broke tables without an `id` column.
- Workspace sync silently no-op'd when no integrations marker existed.
- CLI `_detect_workspace_db_url` read **commented-out** config and ignored
  `DatabaseIntegration(url=Env(...))` — now env-var → real-workspace-import
  → comment-stripped static scan, in that order.

## Verification

- 87 new regression tests across 12 new test files; complete suite
  **9488 passed / 0 failed**.
- Live PostgreSQL 16: UUID-FK migration applies, zero false drift on an
  identical schema (real drift still detected), concurrency stress at
  10/50/100 writers, composite-PK inserts.
- Live loopback HTTP server: multi `Set-Cookie` (comma-bearing `Expires`)
  preserved, body readable after client close, connection reuse, 8
  concurrent requests, unread-response non-poisoning.
- One pre-existing failure on `master` (dataengine perf gate) is documented
  and untouched by this release.
