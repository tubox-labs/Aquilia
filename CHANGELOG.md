# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.9] — 2026-07-30 — "Database Sentinel"

This release introduces strict `auto_migrate=False` schema enforcement, a non-fatal database startup readiness model (`DatabaseState`), a single-authority migration execution engine (`MigrationRunner`, `DDLExecutor`, `MigrationPlanner`), typed statement intermediate representations (`ExecutableStatement`), backend adapter DDL error encapsulation, and atomic transactional DDL & migration rollback guarantees across the Aquilia Database, ORM, and Server Startup lifecycle subsystems.

Full notes: [`releases/1.3.9/`](releases/1.3.9/README.md)

### Added

#### Database & ORM — DDL Execution & Migration Planning
- **DDL Executor Subsystem** (`aquilia.models.ddl_executor.DDLExecutor`) — Single-authority DDL statement compiler and executor featuring lazy operation compilation, async Python operation dispatch, and backend error tolerance delegation.
- **Typed Statement Intermediate Representation** (`aquilia.models.ddl_executor.ExecutableStatement`) — Strongly-typed statement dataclass replacing raw SQL string arrays, carrying `StatementType` categories (`CREATE_TABLE`, `ALTER_TABLE`, `CREATE_INDEX`, `PYTHON_CALLABLE`, `COMMENT`, etc.), description metadata, and operation references.
- **Execution Diagnostics & Metrics** (`aquilia.models.ddl_executor.ExecutionResult`) — Structured execution result capturing executed statement count, skipped count, duration in milliseconds, and diagnostic logs.
- **Migration & Initial Schema Planner** (`aquilia.models.migration_planner.MigrationPlanner` & `InitialSchemaPlanner`) — Dedicated planning authority generating clean initial DDL operations (`CreateModel`, `CreateIndex`, `AddConstraint`) directly from model descriptors without empty-snapshot diffing hacks.
- **Backend Adapter DDL Error Hook** (`aquilia.db.backends.base.DatabaseAdapter.should_ignore_ddl_error()`) — Encapsulates backend-specific ignorable DDL errors (such as MySQL error `1061` for duplicate key names and `1091` for missing index drops) within the database adapter layer.

#### Database & ORM — Startup Readiness & State Management
- **DatabaseState Enum Model** (`aquilia.models.startup_guard.DatabaseState`) — Clean state classification (`READY`, `MISSING_DATABASE`, `PENDING_MIGRATIONS`, `CORRUPTED_HISTORY`, `SCHEMA_MISMATCH`, `UNAVAILABLE`) for structured readiness tracking.
- **Database State Inspector** (`aquilia.models.startup_guard.get_db_state()`) — Helper function providing state inspection of target database connection URL and migrations directory.
- **Non-Fatal Terminal Warning Banner** (`aquilia.models.startup_guard._warn_not_ready()`) — Formatted yellow terminal diagnostic banner instructing developers on required `aq db` commands without raising fatal `SchemaFault` process crashes.

#### Tests
- **Migration Engine Refactor Verification Test Suite** (`tests/test_migration_engine_refactor_verification.py`) — Exhaustive test suite verifying `ModelRegistry` execution removal, `MigrationRunner` sole execution authority, `InitialSchemaPlanner` direct planning, `DDLExecutor` typed statement handling, backend error encapsulation, tracking history recording, and atomic step rollbacks.
- **Migration Subsystem Architecture Test Suite** (`tests/test_migration_architecture_audit.py`) — Audit test suite verifying strict `auto_migrate=False` enforcement, non-fatal readiness warnings, and atomic DDL transaction rollbacks.
- **Migration Subsystem Bug Reproduction Test Suite** (`tests/test_migration_architecture_repro.py`) — Minimal reproduction test suite isolating root causes for Bug 1, Bug 2, and Bug 3.

### Refactored

#### Database & ORM — Elimination of Split-Brain DDL Execution
- **`ModelRegistry` Stripped of Execution Authority** (`aquilia.models.registry.ModelRegistry`) — `ModelRegistry` now acts purely as a model metadata and dependency topology registry. All DDL string loops, manual transaction blocks, string comment parsing (`sql.startswith("--")`), and hardcoded MySQL error handling were completely removed. `ModelRegistry.create_tables()` and `ModelRegistry.drop_tables()` delegate directly to `MigrationRunner`.
- **Sole Execution Authority** (`aquilia.models.migration_runner.MigrationRunner`) — `MigrationRunner` is the single execution engine for initial schema setup, incremental migrations, rollbacks, and tracking table management.
- **Authoritative Revision Zero History** (`aquilia_migrations`) — Initial schema creation via `create_initial_schema()` records a `0000_initial_schema` entry in `aquilia_migrations`, maintaining clean history from revision zero.

#### Server & Startup Execution
- **Strict `auto_migrate=False` Enforcement** (`aquilia.server.AquiliaServer._register_models()`) — `auto_migrate=False` explicitly suppresses all `CREATE TABLE`, `ALTER TABLE`, and schema modification operations on startup, overriding default `auto_create=True` settings.
- **Configuration Precedence Tracker** (`aquilia.server.AquiliaServer`) — Added `explicit_auto_migrate_false` tracking across workspace, integration, and environment variable configuration layers.

#### Database & ORM — Transactional DDL & Integrity
- **Atomic Multi-Table Schema Creation** (`aquilia.models.ddl_executor.DDLExecutor`) — Enclosed statement execution in `async with target_db.transaction():` context, guaranteeing 0 partial tables on DDL failure.
- **Atomic Migration Execution & Rollback** (`aquilia.models.migration_runner.MigrationRunner`) — All migration plans and rollback steps execute within atomic database transactions.

### Fixed

- **Implicit Table Creation under `auto_migrate=False`** — Fixed `auto_create=True` bypassing `auto_migrate=False` during server startup.
- **Fatal Process Termination on Uninitialized Database** — Fixed `startup_guard.py` raising a fatal `SchemaFault` and process termination on missing databases or pending migrations under `auto_migrate=False`.
- **Partial Schema Pollution on Migration Failure** — Fixed un-wrapped DDL execution in `create_tables()` and legacy migration runner by executing statements inside atomic database transactions.
- **Split-Brain Schema Generation Logic** — Fixed `ModelRegistry` running duplicate, un-tracked DDL routines by unifying initial schema creation and migration execution under `MigrationRunner` and `DDLExecutor`.

## [1.3.8] — 2026-07-30 — "Migration Architect"

This release introduces a complete architectural overhaul of the ORM Migration DSL Generator, post-order topological model dependency ordering for `CreateModel` DDL operations, character-split index normalization, strict foreign key target table name resolution, scalar Enum default serialization, and migration revision dependencies metadata.

Full notes: [`releases/1.3.8/`](releases/1.3.8/README.md)

### Added

#### Database & ORM — Migration DSL Generator & Topological Ordering
- **Topological Model Creation Sorting** (`aquilia.models.schema_snapshot._topologically_sort_models()`) — Post-order depth-first traversal of model dependency graphs ensures referenced tables (`users`) are created before dependent tables (`email_verification`, `user_roles`) in generated migrations.
- **Foreign Key Target Table Resolver** (`aquilia.models.schema_snapshot._resolve_target_table()`) — Multi-pass target table resolution pipeline resolves target model metadata, `ModelRegistry` entries, and PascalCase-to-snake_case fallbacks (`"UserModel"` $\rightarrow$ `"users"`).
- **Database Column Name Resolver** (`aquilia.models.schema_snapshot._resolve_db_column_name()`) — Maps model attribute names to underlying database column names (`"user"` $\rightarrow$ `"user_id"`) across indexes and table constraints.
- **Migration Dependencies Metadata** (`aquilia.models.migration_gen._render_migration_file()`) — Generated DSL migration modules now include prerequisite revision IDs in `Meta.dependencies`.

#### Tests
- **Migration Generator Correctness Test Suite** (`tests/test_migration_dsl_generator_correctness.py`) — Comprehensive test suite verifying all 19 migration generator correctness rules, AST parsing, loading, and DDL execution on SQLite.

### Improved

#### Models & Serialization
- **Character-Split Index Normalization** (`aquilia.models.index`, `aquilia.models.fields_module`) — Normalizes string index fields into `list[str]` arrays, eliminating character-split index columns (`['t', 'o', 'k', 'e', 'n']`) and corrupted index names (`idx_email_verification_t_o_k_e_n`).
- **Scalar Enum Default Unwrapping** (`aquilia.models.schema_snapshot._serialize_field()`, `aquilia.models.migration_dsl._format_default()`) — Unwraps `Enum` member instances to scalar string/int primitives (`default='active'`), fixing Python `SyntaxError` on migration load.
- **Foreign Key Type Inference Consistency** (`aquilia.models.schema_snapshot._field_to_sql_type()`) — Dynamically inspects target primary key types to emit consistent column types (`col_type="VARCHAR(36)"`) across referencing foreign key column definitions.
- **Foreign Key Metadata Preservation** (`aquilia.models.migration_gen._render_column_def()`) — Renders `null=True`, `on_delete`, `on_update`, and `col_type` in `C.foreign_key()` DSL calls.

### Fixed

- **AST Syntax Error on Enum Migration Load** — Fixed stringified Enum representation output (`default=<UserStatus.ACTIVE: 'active'>`) by serializing DB-storable primitive values.
- **Foreign Key DDL Execution Failures** — Fixed `CreateModel` execution order for added models using topological graph sorting.
- **Foreign Key Target Table Reference Crashes** — Fixed target table references pointing to un-pluralized class name stubs (`"usersmodel"`) instead of actual table names (`"users"`).

## [1.3.7] — 2026-07-30 — "Thread Sentinel"

This release introduces thread-safe ModelRegistry registration with re-entrant locking (`threading.RLock`) and reverse-relation cache invalidation, thread-isolated BaseManager descriptor subclass binding via shallow copying, standard Python type hint annotation support for `NestedContractFacet`, dialect parameter support across `EnumField` and `CompositeField` `to_db()` methods, and comprehensive 10-point industry docstrings across the Contracts subsystem.

Full notes: [`releases/1.3.7/`](releases/1.3.7/README.md)

### Added

#### Contracts — Type Hint Annotations & Docstrings
- **NestedContractFacet Type Annotations** (`aquilia.contracts.annotations`) — Support for `name: NestedContractFacet[SubContract]`, `name: SubContract`, and list variations (`list[SubContract]`) in `ContractMeta`.
- **10-Point Standard Docstrings** (`aquilia.contracts`) — Added comprehensive industry docstrings across `facets.py`, `exceptions.py`, `integration.py`, `lenses.py`, `pipeline.py`, `projections.py`, `schema.py`, and `ward.py`.

#### Tests
- **ORM & Model Concurrency Test Suite** (`tests/test_models_thread_safety_and_docstrings.py`) — Multi-threaded concurrent tests verifying thread-safe `ModelRegistry` registration, manager subclass isolation, and reverse-relation cache invalidation.
- **EnumField & Nested Annotations Test Suite** (`tests/test_enum_field_dialect_and_nested_annotations.py`) — Tests verifying dialect parameter handling in `EnumField.to_db()` and `CompositeField.to_db()`, and nested contract type annotations.

### Refactored

#### Models — Thread Safety & Descriptor Isolation
- **ModelRegistry RLock Guard** (`aquilia.models.registry.ModelRegistry`) — Added class-level `threading.RLock()` guarding `register()`, `reset()`, `set_database()`, `get_model()`, `_resolve_relations()`, `create_tables()`, and `drop_tables()`.
- **Reverse Relation Cache Invalidation** (`aquilia.models.base.Model._clear_reverse_relation_caches()`) — Dynamic invalidation of `_reverse_fk_cache` and `_reverse_relation_cache` when models are registered or reset.
- **BaseManager Descriptor Subclass Copying** (`aquilia.models.manager.BaseManager.__get__()`) — Returns a bound shallow copy (`copy.copy(self)`) when accessed on subclasses, preventing cross-thread manager state pollution.

### Fixed

- **EnumField & CompositeField `to_db()` Dialect Parameter** — `EnumField.to_db()` and `CompositeField.to_db()` now accept `dialect="sqlite"`, resolving `TypeError` when imprinting contracts into ORM models (`contract.imprint()`).
- **Bytecode Cache & Snapshot Assertions** — Resolved HMAC secret warning and envelope dict format assertions in bytecode cache and schema snapshot test suite.

## [1.3.6] — 2026-07-29 — "Artifact Forge"

This release introduces the Artifact Subsystem, unifying all framework-generated metadata, caches, and compiled representations into a single production-grade infrastructure with atomic writes and HMAC integrity checks.

The framework now writes all artifacts to `.aquilia/artifacts/` using a standardized JSON envelope. This replaces the scattered, ad-hoc file I/O previously used by the template, discovery, and WebSocket engines. For most applications, this is entirely transparent, though CI/CD pipelines caching the old `artifacts/` directory will need a small adjustment.

Full notes: [`releases/1.3.6/`](releases/1.3.6/README.md)

### Added

#### Artifacts — Store & Backends
- **`aquilia.artifacts`** — New package containing the unified `ArtifactStore`, `ArtifactEnvelope`, `JSONFileBackend`, and `MemoryBackend`.
- **`ArtifactStore`** (`aquilia.artifacts.store.ArtifactStore`) — Async facade providing `get`, `put`, `verify`, `status`, and `prune`. Supports `ArtifactTransaction` for all-or-nothing commits of multiple artifacts.
- **`JSONFileBackend`** (`aquilia.artifacts.backends.json_file.JSONFileBackend`) — Physical storage layer with guaranteed atomic writes via `tempfile.mkstemp`, `os.fsync`, and `os.replace`.
- **`ArtifactRegistry`** (`aquilia.artifacts.registry.ArtifactRegistry`) — Central registry for artifact schemas and behavior (`ArtifactTypeDescriptor`).
- **`ArtifactEnvelope`** (`aquilia.artifacts.envelope.ArtifactEnvelope`) — Standardized wire format carrying schema versions, timestamps, and payload fingerprints.
- **`HMAC-SHA256 Signing`** (`aquilia.artifacts.integrity`) — Native payload signing (`sign_payload`, `verify_payload`) applied directly via backend `signed=True`.

#### Artifacts — CLI & DI
- **`aq artifacts` CLI commands** — `status` to list disk contents, `verify` to check integrity, and `clean` to prune orphans.
- **`ArtifactStoreProvider`** (`aquilia.artifacts.di.ArtifactStoreProvider`) — App-scoped DI provider available via `provide_artifact_store()`.
- **`AQUILIA_ARTIFACT_ROOT`** — Configuration surface to override the `.aquilia/artifacts` path globally or via `[aquilia.artifacts] root` in TOML.

### Changed

#### Subsystems Migrated
- **Discovery Engine** (`aquilia.discovery.engine`) — `DiscoveryCache` migrated to `ArtifactStore`.
- **Aquilary Registry** (`aquilia.aquilary.core`) — `export_manifest()` migrated to signed artifacts.
- **Schema Snapshots** (`aquilia.models.schema_snapshot`) — Migrated to `ArtifactEnvelope`.
- **Template Manifest** (`aquilia.templates.manifest_integration`) — Path changed to `.aquilia/artifacts/templates.json`.
- **Template Bytecode** (`aquilia.templates.bytecode_cache`) — Path changed to `.aquilia/artifacts/templates.bytecode.json`. Default `cache_dir` parameter is now `None`.
- **Socket Compiler** (`aquilia.sockets.compile`) — Path changed to `.aquilia/artifacts/ws.json`.
- **MCP Indexer** (`aquilia.mcp.context.indexer`) — Migrated to `ArtifactStore`.

### Fixed

- **Centralized Atomic Write Guarantees** — Some subsystems previously used `Path.write_text()` or `Path.replace()`, risking partial writes. All writes now use the rigorous `JSONFileBackend`.
- **Inconsistent HMAC Verification** — Subsystems like discovery cache now automatically inherit integrity verification.
- **Directory Clutter** — Artifacts no longer pollute the project root with the generic `artifacts/` folder.

## [1.3.5] — 2026-07-28 — "Distributed Tide"

Background tasks become genuinely distributed and durable, mail becomes a production delivery pipeline, and a deep audit of the Contracts subsystem closes a silent validation bypass. Jobs now execute across multiple worker processes and machines with lease-based coordination and crash recovery; job state survives restarts on Redis or SQL; jobs compose into chains, groups, chords, and arbitrary DAGs; duplicate enqueues are collapsed by an enforced fingerprint; mail is delivered by background workers with provider webhook processing and automatic suppression of bounced recipients; and nested Contract validation runs the child's full pipeline instead of a structural pass only.

The tasks, mail, and HTTP work is fully backward compatible. The Contracts audit ships four deliberate behavioral corrections, each replacing behavior that was incorrect — see **Changed** below.

Full notes: [`releases/1.3.5/`](releases/1.3.5/README.md)

### Added

#### Tasks — Distributed & Persistent Backends
- **`RedisBackend`** (`aquilia.tasks.backends.RedisBackend`) — multi-process, multi-machine task queue with durable job state. Claims are atomic through a Lua script against a sorted set; fingerprint reservation uses `SET NX`. Requires `pip install aquilia[redis]` and `redis_url`.
- **`SQLBackend`** (`aquilia.tasks.backends.SQLBackend`) — durable job state on the application's existing database (SQLite, PostgreSQL, MySQL, Oracle), requiring no new infrastructure. A claim is a conditional `UPDATE ... WHERE id = ? AND state = ?` inside a transaction, so it works on every dialect without `SELECT ... FOR UPDATE SKIP LOCKED`. Creates `aquilia_tasks` and `aquilia_task_locks` on first `initialize()`.
- **Lease-based crash recovery** — a worker claims a job for `lease_seconds`, renews it every `heartbeat_interval`, and a reclaim loop returns jobs whose lease lapsed to the runnable pool every `reclaim_interval`. A killed worker's job is retried by a peer instead of being lost. Distributed backends provide **at-least-once** delivery; task functions should be idempotent.
- **`Job.to_payload()` / `Job.from_payload()`** — JSON transport form for jobs crossing a process boundary. `to_payload()` validates `args`/`kwargs` against `json.dumps` and raises `TaskSerializationFault` at the call site rather than failing on a remote worker. `from_payload()` leaves the callable unset; the worker resolves it from `func_ref` through the `@task` registry, so a queue entry can never name an unregistered function.
- **New `Integration.tasks()` options** — `redis_url` (default `None`, falls back to `$REDIS_URL`), `redis_prefix` (`"aquilia:tasks:"`), `sql_table` (`"aquilia_tasks"`), `lease_seconds` (`300.0`), `heartbeat_interval` (`30.0`), `reclaim_interval` (`60.0`), `dedup_ttl` (`3600.0`), `worker_id` (`None`, defaults to `hostname:pid:random`).

#### Tasks — Workflows & DAGs
- **`Workflow`, `Signature`, `WorkflowResult`** (`aquilia.tasks.workflow`) — job graphs with declared dependencies. Every job is created up front with its dependencies recorded, so the graph is durable the moment it is submitted and needs no orchestrator process. Dependent jobs start `WAITING` and are released by the backend as their dependencies complete.
- **`chain(*signatures)`** — strictly sequential execution.
- **`group(signatures)`** — parallel fan-out with no inter-step dependencies.
- **`chord(header, callback)`** — parallel header plus a fan-in callback that runs once every header job completes.
- **Arbitrary DAGs** — `Workflow.add(signature, depends_on=[...])` expresses any acyclic shape; `chain`/`group`/`chord` are conveniences over it.
- **`Signature.with_parent_results()`** — the step receives its dependencies' return values as a `parent_results` keyword. The stored marker is a plain string, keeping the job JSON-serializable and letting results be read after a restart.
- **`_TaskDescriptor.s(*args, **kwargs)`** — builds a `Signature` from a `@task`-decorated function, matching Celery's naming.
- **Graph validation** — empty workflows, cycles, and unknown dependency indices raise `TaskWorkflowFault` before anything is enqueued, so a malformed workflow never partially executes.

#### Tasks — Idempotency
- **`dedup` parameter on `TaskManager.enqueue()`** — `"allow"` (default, unchanged behavior), `"skip"` (return the in-flight job's ID), or `"raise"` (raise `TaskDuplicateFault`). Matched on `Job.fingerprint`, which was previously computed but never read.
- **Distributed deduplication** — enforcement lives in the storage layer, so two racing processes produce one job: Redis `SET NX`, or a primary-key `INSERT` into `aquilia_task_locks` on SQL. Reservations are released when the job reaches a terminal state, so a failed job can be retried immediately rather than waiting out the TTL.

#### Tasks — Faults
- **`TaskSerializationFault`**, **`TaskBackendFault`**, **`TaskDuplicateFault`**, **`TaskWorkflowFault`** — new structured faults following the framework's fault contract.

#### Mail — Delivery Queue
- **`EnvelopeStore`** with `MemoryEnvelopeStore` (bounded, default) and `SQLEnvelopeStore` (table `aquilia_mail_envelopes`) — a durable record of accepted mail, supporting `save`, `get`, `list_by_status`, `find_by_digest`, `find_by_idempotency_key`, `cleanup`, and `stats`.
- **Background delivery through the existing task scheduler** — no second queue implementation. `send_message()` persists an envelope, enqueues the registered `aquilia.mail.deliver` task, and returns; retries, backoff, and delayed sends are managed by the scheduler.
- **Envelope-ID-only delivery jobs** — the job carries an envelope **ID**, not a live `MailEnvelope`, so delivery runs on another process or machine with no API change. The worker reloads the envelope from the shared store.
- **Send-time deduplication** — an explicit `idempotency_key` matches first, otherwise a content digest within `queue_dedupe_window_seconds`.
- **New `Integration.mail()` options** — `queue_enabled` (`False`), `queue_persistent` (`False`), `queue_dedupe_window_seconds` (`3600`), `queue_retention_days` (`30`).

#### Mail — Bounce Handling, Webhooks & Suppression
- **`parse_ses`, `parse_sendgrid`, `parse_mailgun`** — provider webhook parsers normalizing into provider-neutral `WebhookEvent` objects with a shared `EventType` vocabulary (`DELIVERED`, `HARD_BOUNCE`, `SOFT_BOUNCE`, `COMPLAINT`, `REJECTED`, `OPENED`, `CLICKED`, `UNSUBSCRIBED`, `DEFERRED`, `UNKNOWN`). An unrecognized event becomes `UNKNOWN` and is preserved rather than dropped.
- **`process_webhook(events, *, suppression=None, store=None, soft_bounce_ttl=86400.0)`** — applies delivery events: suppresses bad addresses and updates envelope status. Returns counts keyed by `suppressed`, `delivered`, and `ignored`.
- **`SuppressionList`** with `MemorySuppressionList` (default) and `SQLSuppressionList` (table `aquilia_mail_suppressions`) — `suppress`, `unsuppress`, `is_suppressed`, `get`, `list_all`, `filter_recipients`, `cleanup`. Addresses are normalized (lowercased, trimmed) before storage and lookup.
- **`SuppressionReason`** — `HARD_BOUNCE`, `SOFT_BOUNCE` (expiring), `COMPLAINT`, `UNSUBSCRIBE`, `MANUAL`, with an `is_permanent` property.
- **Enforcement on send** — suppressed recipients are removed while preparing every envelope; an envelope whose recipients are all suppressed is marked `CANCELLED` and never dispatched.

#### Mail — MIME, DKIM & Security
- **`aquilia/mail/mime.py`** — shared MIME assembly used by every provider: `build_mime_message(envelope, *, extra_headers=None)`, `message_to_bytes(msg, security=None)`, `sign_dkim(raw_message, security)`, `extract_domain(email)`. Emits `X-Aquilia-Envelope-ID` plus trace and tenant headers, which is what lets provider webhooks correlate a bounce back to an exact envelope.
- **DKIM signing** applied at the byte level immediately before transmission, so the signature covers exactly what the provider receives. Configured via `dkim_enabled`, `dkim_domain`, `dkim_selector`, `dkim_private_key_path`, `dkim_private_key_env`.
- **`aquilia[mail-dkim]`** — new optional extra (`dkimpy>=1.1.0`).
- **`MailAuth.oauth2(...)`** — XOAUTH2 bearer-token SMTP authentication for Gmail and Microsoft 365, accepting `access_token` / `access_token_env`. Aquilia does not perform the token exchange; supply a valid token from whatever component owns the refresh cycle.
- **`aquilia/mail/redaction.py`** — `redact_email(address)` and `redact_pii(text, *, enabled=True)`. Masks local parts while preserving domains, so logs stay useful for diagnosing domain-wide delivery problems without recording individual identities. Enabled with `pii_redaction=True`.

#### Mail — Templates
- **Documented ATS public API** — `configure(template_dirs)`, `render_string(text, context, *, autoescape=True)`, `render_template(name, context, *, template_dirs=None, autoescape=None)`, `register_filter(name, fn)`, and the `FILTERS` registry.
- **Built-in filters** — `currency`, `default`, `escape`, `join`, `length`, `lower`, `safe`, `title`, `trim`, `truncate`, `upper`. Filters compose left to right; arguments must be literals, so a template cannot execute arbitrary code.

#### HTTP Client — Zero External Dependencies
- **`AsyncHTTPClient.aclose` method alias** — added `aclose = close` on `aquilia.http.AsyncHTTPClient` for compatibility with async context managers and explicit close callers.

#### Contracts — Async Serialization
- **`Contract.to_dict_async()` / `to_dict_many_async()`** — serialization that awaits ORM relations, so a to-many `Lens` no longer has to be prefetched before rendering. Prefetching remains the right choice on hot paths; the async path exists so a missing prefetch costs a query rather than raising.
- **`Lens.mold_async()`** — awaits a related manager or async iterator. Sync and async share one field-molding generator (`_mold_steps`), so projections, `write_only` exclusion, and computed fields cannot drift between the two.

#### Contracts — Validation Control
- **`@ward(order=...)`** — sort key within the ward phase; lower runs first, ties keep definition order. Use it when one ward's rejection makes another's work redundant.
- **`@ward(when=...)`** — predicate receiving the validated data; the ward runs only when it returns truthy. A predicate that raises is treated as "does not apply" rather than manufacturing a field error attributed to the ward it was gating.
- **`@ward(groups=...)`** — validation groups, selected per pass with `is_sealed(groups=...)` / `is_sealed_async(groups=...)`. An ungrouped ward always runs, since it expresses an invariant that holds regardless of which group was requested. Groups propagate to nested Contracts.
- **`Spec.fail_fast`** — stop at the first ward error instead of accumulating. Defaults to `False`, unchanged.
- **`Spec.frozen`** — validated data rejects mutation after sealing, so the guarantee `is_sealed()` gives does not expire on the next assignment.
- **`Contract.copy(update=...)` / `copy_async(update=...)`** — derive an updated Contract, re-validating by default. Pass `validate=False` to build a payload in stages.
- **`Contract.__eq__`** — compares class and validated data, falling back to raw input when unsealed. Contracts remain unhashable, with an explicit message naming the reason rather than a silent `__hash__ = None`.

#### Contracts — Facets and Typing
- **`BytesFacet`** — binary data with base64 (default) or hex wire encoding, and `min_length`/`max_length` constraints applied to the *decoded* size.
- **`PathFacet`** — filesystem paths validated as `pathlib.PurePosixPath`, rejecting absolute paths and `..` traversal by default and null bytes unconditionally.
- **`SecretFacet`** and **`Secret`** — sensitive strings masked in `repr`/`str`, `write_only` by default, with constant-time equality and an explicit `.reveal()`.
- **`MACAddressFacet`** — accepts colon, dash, and Cisco notations, normalizing to lowercase colon-separated form.
- **Annotation routing** for `pathlib.Path`, `ipaddress.IPv4Address` / `IPv6Address`, and `Secret`.

#### Contracts — Data Sources
- **`Contract.from_env()`** — build a Contract from environment variables with an optional prefix. Values cast through the normal facet pipeline, so configuration gets the same validation as request data. Absent variables are omitted rather than set empty, so each field's `default` and `required` rules decide the outcome. Validates by default, so configuration errors surface at startup.
- **`Contract.from_cli()`** — build a Contract from `--flag value`, `--flag=value`, and bare `--flag` arguments. Dashes map to underscores; a repeated flag collects into a list; unknown flags are ignored.
- **Input adapters** — dataclasses, attrs classes, and `TypedDict` values are first-class Contract input at every level, adapted at a single point (`sigil.adapt_input`) that feeds the existing cast/seal pipeline rather than a parallel one.

#### Contracts — Tooling
- **`aq contracts stubs MODULES...`** — emits `.pyi` stubs so `mypy` and `pyright` see Contract fields, which are otherwise invisible because they are built at class-body evaluation and served through `__getattr__`. `--check` fails CI on a missing or stale stub; `--path` sets the import root. Generation is deterministic, so `--check` cannot fail at random.
- **`generate_module_stub()` / `write_module_stub()` / `StubReport`** (`aquilia.contracts`) — the Python API behind the command.
- **`Facet.python_type()`** — each facet reports the Python type its validated value has, making facets the source of truth for stub generation rather than a parallel mapping table.

#### Contracts — Messages and Faults
- **`aquilia.contracts.messages`** — every built-in validation message resolves through `contract_message()`, which reads the `contracts.` namespace of the active i18n catalog with ICU-style `{name}` substitution and falls back to the built-in English text. 33 keys ship. Applications without i18n configured see byte-identical messages. Resolution never raises: failing to render the message for a rejected payload would turn a 422 into a 500.
- **`NestingDepthFault`** (`BP502`), **`LensUnresolvedFault`** (`BP503`), **`StubGenerationFault`** (`BP600`) — structured faults for inbound recursion limits, unresolved relational serialization, and stub generation failures.
- **`MAX_NESTING_DEPTH`** (`aquilia.contracts.exceptions`) — single authoritative nesting limit shared by the Sigil and facet layers.
- **`resolve_nested()` / `is_nested_facet()`** (`aquilia.contracts.sigil`) — nested-Contract resolution that looks through container facets. `get_nested_contract_cls()` remains, now delegating to `resolve_nested()`.

### Changed

- **`backend="redis"` now builds a real backend.** Previously it logged a warning ("not implemented") and silently fell back to `MemoryBackend`. Only an unknown backend name or an unreachable service falls back now, and both log a message naming the durability that was lost.
- **`JobResult.to_dict()` preserves JSON-safe values.** Previously every value was serialized as `repr(value)`, so a workflow fan-in on a persistent backend received `'4'` instead of `4`. Non-serializable values still fall back to `repr`.
- **Mail providers share one MIME implementation.** SMTP, SES, SendGrid, console, and file backends no longer each build their own message, so header handling, attachment encoding, and tracking headers cannot drift between them.
- **SendGrid Mail Provider adopts native `aquilia.http`.** Replaced `httpx.AsyncClient` with native `aquilia.http.AsyncHTTPClient` and async `HTTPClientResponse` parsing across `SendGridProvider`.
- **Testing & Documentation adopt native `aquilia.http`.** Replaced all `httpx` imports across `LiveServerTestCase`, docstrings, and `aqdocx` release examples with native `aquilia.http`.
- **`aq mail check` validates DKIM configuration** — reports a missing `dkim_domain` and a missing `dkimpy` install. DKIM failures raise at send time rather than shipping unsigned mail, so this check surfaces the misconfiguration before the first real send.
- **DKIM misconfiguration now fails the send.** With `dkim_enabled=True` and an incomplete configuration, sends raise instead of silently shipping an unsigned message. Not an API break, but a behavior change for anyone who had DKIM half-configured.

#### Contracts — behavioral corrections

Four corrections that can change whether an existing payload is accepted. Each replaces behavior that was incorrect. See [`releases/1.3.5/migration.md`](releases/1.3.5/migration.md#migration-0--contracts-behavioral-review) for the review steps.

- **Nested Contract rules are now enforced.** A nested Contract's `@ward` methods and object-level `validate()` override never ran; they now do, with errors reported at the failing field's path (`{"items": {"1": {"qty": [...]}}}`). Payloads previously accepted may now be rejected — correctly.
- **`Lens(many=True)` raises on an unresolved relation** instead of returning `[]`. An empty list is indistinguishable from "this record genuinely has no related rows", so the previous behavior shipped wrong data to clients with no signal. Prefetch the relation, assign an awaited list, or use `to_dict_async()`.
- **Malformed request bodies report a document-level error.** A scalar or list body was coerced to `{}`, producing "This field is required" per field — a misdiagnosis that sent developers hunting the wrong bug. Now `{"__all__": ["Expected an object, got str"]}`. Clients that parse a 422 body and assume every key is a field name should render `__all__` separately.
- **`IntFacet` rejects fractional input.** `3.9` was silently truncated to `3`, while the string `"3.9"` was correctly rejected — the same logical input behaved differently depending on wire type. Integral floats (`3.0`) are still accepted; `NaN` and `Infinity` are rejected explicitly.

Additionally, `"__minimal__"` projections now return a restricted field set (primary-key plus `read_only` facets) rather than every field; the previous output was never correct.

#### Contracts — other changes

- **PEP 604 unions are recognized in polymorphic field resolution.** The union branch checked only `origin is Union`, missing every `A | B` annotation, whose origin is `types.UnionType`. A union member with no facet mapping now emits a `UserWarning` at class-definition time rather than being dropped silently and surfacing later as a confusing "wrong type" rejection.
- **`seal_many(parallel=True)` documented honestly** — structural validation and ward dispatch are pure-Python CPU work that CPython's GIL serializes, so the flag only helps when ward methods block on I/O, or under a free-threaded interpreter build.
- **Dead legacy scanning removed.** `ContractMeta.__new__` scanned `dir(cls)` for `seal_*`/`async_seal_*` into `_seal_methods`, which nothing ever read; `collect_ward_methods()` already folds the legacy convention into `_ward_methods` with correct mode tracking.

### Fixed

- **Mail delivery task was unresolvable across processes (CRITICAL).** `_deliver_envelope_task` was a bare function, never registered with `@task`. On any persistent backend the consuming worker could not resolve it through the registry, so envelopes sat in `QUEUED` forever with no error. Now registered as `@task(name="aquilia.mail.deliver")` under a stable name that survives a Python-level rename.
- **Consumer-only workers polled nothing (CRITICAL).** `TaskManager._queues` was populated only as a side effect of `enqueue()`, so a dedicated worker process that never enqueues knew about exactly one queue — its `default_queue` — and ignored all peer-produced work. Queues are now seeded from every `@task` descriptor and, on distributed backends, refreshed from `backend.get_queue_stats()` at startup and on each reclaim tick.
- **Job results degraded to `repr` strings on persistent backends.** A chord callback received `['4', '6']` instead of `[4, 6]`, producing string concatenation or a `TypeError` far from the cause.
- **`queue.persistent` had no configuration surface.** `SQLEnvelopeStore` and `SQLSuppressionList` existed but nothing constructed them from config, and `QueueConfigContract` had no `persistent` field, so setting it in `workspace.py` was silently dropped in validation. Now threaded through `Integration.mail(queue_persistent=...)`, `MailIntegration`, the contract, and store selection, with graceful degradation to in-memory when the database is unavailable.
- **`Job.fingerprint` was computed but never read.** Now enforced through `dedup`.
- **`MailSuppressedFault` was unreachable.** Defined in the fault taxonomy but never raised; now part of a working suppression path.

#### Contracts

- **Nested Contracts never ran their wards or `validate()` hook (CRITICAL).** `Sigil.validate()` recursed into `nested_cls._sigil.validate()` — the *structural* pass only. It never instantiated the nested Contract, so every `@ward` method and the object-level `validate()` override on it were silently skipped. A nested Contract expressing an authorization check or a cross-field invariant enforced nothing, and the payload was accepted. Nested validation now runs the child's full pipeline through a shared `run_nested_contract()` helper.
- **`list[Contract]` annotations bypassed nested validation entirely (CRITICAL).** `items: list[Item]` builds `ListFacet(child=NestedContractFacet)`, while `NestedContractFacet(Item, many=True)` builds a different facet. Detection matched only the latter, so the far more common annotated spelling was classified as an ordinary list — meaning the fix above did not reach it, `has_async_wards` reported `False` for Contracts whose children declared async wards, and JSON Schema emitted an untyped array instead of an array of `$ref`. Detection now looks through container facets via `resolve_nested()`.
- **`has_async_wards` consulted only the top-level class.** A Contract whose *nested* child declared an async ward reported `False`, so callers took the sync path and the ward never ran — a silent skip rather than the intended `ContractAsyncMismatchFault`. The property now walks the facet tree, memoized per class, with cycle detection for self-referential Contracts and no caching of answers that depended on an unresolved forward reference.
- **Top-level async wards bypassed group and ordering semantics.** `is_sealed_async()` ran async wards through its own inline loop rather than the shared `_run_ward_phase_async()`, so `groups`, `when`, `order`, and `fail_fast` applied on the bulk paths but not the single-item one. The duplicate loop is gone.
- **Nested-Contract recursion had no depth guard on the real validation path.** `MAX_NESTING_DEPTH` was enforced only in `NestedContractFacet.cast()`, which the primary path never called — so a few kilobytes of deeply nested JSON against any endpoint accepting a self-referential Contract raised an uncaught `RecursionError` in the request coroutine. Depth is now threaded through `Sigil.validate()` and yields a structured error.
- **The recursion-depth counter was global mutable state mislabeled "thread-local".** `NestedContractFacet._current_nesting_depth` was a plain class attribute mutated with `+=`/`-=`, shared across every instance, class, and thread. Concurrent validation could both reject shallow payloads spuriously and undercount deep ones, defeating the guard. Replaced with a `contextvars.ContextVar`, correct for threads and asyncio tasks alike.
- **`"__minimal__"` projections exposed every field.** `ProjectionRegistry.configure()` stored an empty `frozenset()` placeholder that no code resolved; because an empty set is falsy, the per-field filter passed every field — so a projection declared specifically to minimize exposed data returned all of them, including fields intended to stay private. Both projection filters now compare against `None` rather than truthiness, so an empty projection renders `{}`.
- **`validate()` ran up to three times per row in bulk paths.** `seal_many()` and `seal_stream()` duplicated the ward-invocation block five times and read `inst.errors`, a property that lazily triggers a full `is_sealed()` cycle. Any `validate()` override with side effects fired three times per record. Row sealing is now a single `_seal_row()` / `_seal_row_async()` pair shared by every entry point, removing roughly 200 lines of duplication.
- **Async validation was impossible for `many=True` Contracts.** `_seal_many()` called each child's synchronous `is_sealed()`, so a child with async wards raised `ContractAsyncMismatchFault` from inside the loop — propagating out of the very `is_sealed_async()` call meant to handle it. Added `_seal_many_async()`, which dispatches per item with correctly aggregated per-index errors. Items validate sequentially: unbounded concurrency over a 10,000-item batch would exhaust the database connection pool.
- **`bytes` fields were non-functional end to end.** `bytes` annotations mapped to `TextFacet`, whose cast whitelist *rejects real `bytes`* — so a `payload: bytes` field rejected every genuine value while accepting plain strings. `bytes` now routes to the new `BytesFacet`.
- **`@computed` methods ran against an uninitialized shell instance.** Because facets are class-level and `Facet.bind()` was never called, `Computed.extract()` reconstructed an owner via `cls.__new__(cls)`, skipping `__init__`. Any computed field touching `self.context`, `self.instance`, or `self._validated_data` raised `AttributeError` in production, while doc-style examples using only the `instance` argument kept working. The live Contract instance is now threaded in explicitly.
- **Hot-path imports hoisted to module scope** (`contracts/sigil.py`). `get_field_value()`, `get_keys()`, `check_strict_type()`, and `Sigil.validate()` re-executed `from .facets import ...` on every call — once per field, per request.

### Security

- **Webhook signature verification** — SES via `verify_topic_arn`, SendGrid via an ECDSA `public_key` with replay rejection over `max_age_seconds`, Mailgun via an HMAC `signing_key`. Without verification, anyone can POST a forged bounce and suppress an arbitrary address — a trivial denial of service against your own users. Omitting these parameters parses without verification and logs a warning naming the risk.
- **DKIM signing failures raise rather than shipping unsigned mail**, since a receiving server treats a missing signature very differently from an invalid one.
- **Registry-only callable resolution** — a durable queue entry can never name a function the application did not register, so the queue is not an arbitrary-code-execution channel.
- **PII redaction** for recipient addresses in mail logs.
- **Parameterized SQL throughout** the new backends and stores; table and column identifiers are validated against a restricted character set before interpolation into DDL.
- **TLS enforcement** on SMTP remains on by default (`require_tls=True`).
- **`PathFacet` rejects path escapes by default** — absolute paths and `..` traversal are refused unless explicitly opted out, and null bytes are refused unconditionally (they truncate at the OS layer, so a name passing an extension check can open a different file). Windows separators are normalized before the `..` check, so a backslash cannot smuggle a segment past it on a POSIX server.
- **`SecretFacet` masks sensitive values in `repr`, `str`, and logs**, is `write_only` by default, and compares in constant time via `hmac.compare_digest` so a submitted-versus-stored comparison does not leak the shared-prefix length through timing.
- **`"__minimal__"` projections no longer leak every field** — a projection declared specifically to minimize exposed data was returning all of them, including fields intended to stay private.
- **Nested Contract authorization rules are enforced** — a `@ward` on a nested Contract expressing an access check previously never ran.
- **The nesting-depth guard now applies to the real validation path**, so deeply nested JSON yields a structured error rather than an uncaught `RecursionError` in the request coroutine, and its counter is per-task/per-thread rather than process-global.

### Performance

- **Mail leaves the request path.** A full SMTP conversation (tens to hundreds of milliseconds, or a provider timeout on failure) becomes one store write plus one enqueue.
- **`WAITING` workflow steps occupy no worker slot**, replacing the pattern of a long-lived job blocking on its children.
- **`dedup="skip"` collapses duplicate work before it executes.**
- **`SQLBackend` claim is a single conditional `UPDATE`** inside a transaction; **`RedisBackend` claim is one round trip** against a sorted set.
- **`MemoryBackend` is untouched** — single-process applications see no change.
- **Contract bulk validation runs `validate()` once per row** instead of up to three times. `seal_many()` and `seal_stream()` read `inst.errors`, a property that lazily triggered a full `is_sealed()` cycle; roughly 200 lines of duplicated ward-invocation logic collapsed into one shared row-sealing pair.
- **Contract hot-path imports hoisted to module scope.** `get_field_value()`, `get_keys()`, `check_strict_type()`, and `Sigil.validate()` re-executed `from .facets import ...` on every call — once per field, per request.
- **`has_async_wards` is memoized per Contract class**, so the facet-tree walk costs nothing after the first call. Contract classes compile once at import, so the answer cannot change at runtime.
- **Contract `.pyi` stub generation is deterministic**, so a CI `--check` run is a byte comparison rather than a regeneration.

### Documentation

- **`releases/1.3.5/`** — thirteen-page release notes covering distributed backends, workflows, idempotency, the mail delivery queue, bounce handling, mail security and MIME, the native HTTP client, the Contracts nested-validation pipeline, Contracts validation control and typing, Contracts stub generation and deprecations, CLI changes, bug fixes, and a migration guide with an upgrade checklist, per-feature before/after migrations, compatibility notes, and known issues.
- **`docs/developer-guide.md`** — new sections on durable and distributed backends, idempotency, workflows, the mail delivery queue, and bounces and suppression.
- **`docs/docs/contracts/async-pipeline.md`** and **`docs/docs/contracts/validation-control.md`** — new pages on async validation and serialization, and on ward ordering, conditions, groups, and fail-fast.
- **`docs/docs/contracts/ward.md`** — rewritten deprecation section covering the `seal_*` migration with rationale, before/after examples, and instructions for finding every affected method.
- **Corrected the `aquilia.tasks` package docstring**, which listed persistent/distributed backends and workflow DAGs under "Not implemented today (deliberately absent, not stubbed)". All shipped in this release. The docstring now documents the at-least-once delivery contract and the one capability still genuinely absent (per-queue rate limiting).

### Deprecated

- **The `seal_*` / `async_seal_*` Contract validator naming convention.** Deprecated in 1.3.0, removed in 2.0.0. A Contract declaring an undecorated `seal_*`/`async_seal_*` method now emits a `DeprecationWarning` at class-body evaluation naming the exact replacement decorator for that method. Behavior is unchanged in 1.x — these methods continue to register and run exactly as before, since a rule that stopped firing in a feature release would ship the very bug the deprecation warns about.

  The convention is going away because the name *is* the registration: renaming `seal_total` during a cleanup removes the rule with no error and no warning; a helper legitimately named `seal_envelope` is executed as a validator on every request; async mode was inferred from `iscoroutinefunction` rather than declared, so a validator awaiting the database while written as a sync `def` created a coroutine that was never awaited; and ordering, conditions, and groups have nowhere to live in a naming convention.

  Migration is mechanical — decorate the method with `@ward` (or `@ward(mode="async")`); the body does not change. Adding the decorator without renaming silences the warning immediately. Find every affected method with `python -W error::DeprecationWarning -c "import myapp.contracts"`, or by setting `filterwarnings = ["error::DeprecationWarning"]` in `pyproject.toml`. Timeline constants are exported as `DEPRECATED_PREFIX_SINCE` and `DEPRECATED_PREFIX_REMOVED_IN` from `aquilia.contracts.ward`.

### Removed

- **Third-party `httpx` dependency removed.** Entirely removed `httpx` from `pyproject.toml`, `setup.py`, `aquilia.egg-info`, and extra dependency bundles (`mail-sendgrid`, `testing`, `dev`). Framework core and optional mail/testing modules now operate with zero third-party HTTP client dependencies.

## [1.3.4] — 2026-07-24 — "Structural Integrity"

A comprehensive two-round architectural audit of the Aquilary registry, Auto-Discovery engine, Manifest system, Workspace architecture, Configuration system, and aq CLI. 13 bugs fixed; no breaking changes. All v1.3.3 applications run without modification.

### Added

#### CLI — `aq validate --deprecated`
- **`aq validate --deprecated`** — new flag that scans all discovered module manifests for deprecated field usage. Detected fields: `route_prefix` (use `Module.route_prefix()` in `workspace.py`), `database` (use `DatabaseIntegration` in `workspace.py`), `middlewares` (use `middleware` list), `depends_on` (use `imports` list). Exits with code `1` when deprecated fields are found (plain-text mode). Use `--json` for machine-readable output suitable for CI gating.
- **`AQUILIA_FAIL_FAST=1`** environment variable — when set, the ASGI entrypoint re-raises startup exceptions instead of catching them and serving HTTP 500 stubs. Recommended for production. Opt-in; existing deployments are unaffected.

#### Aquilary — Discovery Diagnostics
- **`perform_autodiscovery()` failure logging** — all 6 discovery phases (controllers, services, socket controllers, tasks, models, middleware) now emit `logger.warning(..., exc_info=True)` when a scan step raises. Previously: `except Exception: pass`. Developers now see the module name and full traceback for any import error in a scanned package.

#### Runtime — `_load_workspace_from_exec()`
- New internal method on `AquiliaRuntime` that executes `workspace.py` and returns `(workspace_name, module_names, modules_dict)` in a single exec pass. Used as the primary workspace discovery mechanism, replacing the previous regex approach. `_load_workspace_modules()` delegates to it, eliminating the duplicate workspace.py execution.

#### Dependency Injection — String Token Resolution (`aquilia/di/core.py`, `aquilia/di/dep.py`, `aquilia/di/decorators.py`)
- **`Annotated[Any, Inject("token")]` string token resolution failure (`PROVIDER_NOT_FOUND`)**: Passing `typing.Annotated[typing.Any, Inject("modules.auth.services:CrossAppService")]` directly into `container.resolve()`, `container.resolve_async()`, or `RequestDAG` raised `ProviderNotFoundError` because `_token_to_key` converted `_AnnotatedAlias` into its string representation `"typing.Annotated[typing.Any, Inject(...)]"` instead of unwrapping the target token. Fixed: added `Container._unwrap_token()` to recursively unwrap `Annotated` aliases, `Inject` instances, `Dep` instances, and `Optional[T]` unions. Fixed `_unpack_annotation` in `dep.py` to extract `Inject.token`. Updated `@auto_inject` in `decorators.py` to use `get_type_hints(func, include_extras=True)`. Added comprehensive, detailed docstrings across `Inject`, `inject`, `Dep`, `RequestDAG`, and core DAG methods.

#### Configuration — `Secret` Positional-Value Ambiguity (`aquilia/pyconfig.py`)
- **`Secret("MY_VAR")` silently reinterpreted as env-var lookup**: When a single positional string was passed, the code checked whether an environment variable with that name existed and used its value if found. This meant `Secret("MY_DATABASE_URL")` was almost certainly doing an env-var lookup rather than storing the literal string — a confusing and dangerous silent behavior. Fixed: the positional argument is now always a literal value. Use `Secret(env="MY_VAR")` for explicit env-var binding. `DeprecationWarning` emitted for positional identifiers matching `^[A-Z][A-Z0-9_]*$` (common env-var naming patterns).

#### Aquilary — `ManifestWriter` Corruption Risk (`aquilia/discovery/engine.py`)
- **No post-write AST validation**: The `ManifestWriter` rewrote `manifest.py` files without validating that the output was syntactically valid Python. A malformed template expansion could replace a working manifest with invalid Python, silently corrupting the module discovery state across all subsequent runs. Fixed: `ast.parse()` now runs on the rewritten output string before any bytes are written to disk. If parsing fails, the write is aborted and the original file is preserved. The exception is logged and re-raised.

#### Aquilary — Recursive Graph Algorithms → Iterative (`aquilia/aquilary/graph.py`)
- **`DependencyGraph.topological_sort()` (Tarjan SCC) stack overflow**: The Tarjan strongly-connected-components algorithm used Python recursion. On dependency graphs with ≥ ~500 modules in a single chain, this hit Python's default recursion limit and raised `RecursionError: maximum recursion depth exceeded`. Converted to an explicit-stack iterative implementation using a `[(node, iterator)]` stack and an explicit DFS state machine.
- **`DependencyGraph.get_transitive_dependencies()` stack overflow**: The recursive tree-walker for transitive dependency resolution had the same problem. Converted to explicit iterative BFS using a `collections.deque`.
- Both conversions are behavior-preserving: any dependency graph that compiled before continues to compile identically.

#### Aquilary — O(n²) Manifest Registry Lookup (`aquilia/aquilary/core.py`)
- **Phase 5 dependency graph construction nested a linear scan inside a per-module loop**: For each of the `n` modules, the code searched the full `manifests` list by name — a quadratic operation. At 1,000 modules this is ~1,000,000 comparisons during startup. Fixed: a `{manifest.name: manifest}` index dict is pre-built before the loop; Phase 5 lookup is now O(1) per module, O(n) total.

#### Entrypoint — Silent Startup Failure Serving (`aquilia/entrypoint.py`)
- **Broad `except Exception: pass` swallowed all startup errors**: A DI configuration error, missing module, or invalid workspace caused the application to start successfully but respond with HTTP 500 stubs to every request, with no indication in logs of what failed. Fixed via opt-in `AQUILIA_FAIL_FAST=1`: when set, the entrypoint re-raises the exception after logging it, ensuring process managers (systemd, Docker, Kubernetes) see a non-zero exit code and restart or alert.

#### Discovery — SHA-256 Hashing on Every Scan (`aquilia/discovery/engine.py`)
- **Cache check computed SHA-256 over full file content unconditionally**: The discovery cache was designed to avoid re-parsing unchanged files, but the cache check always read and hashed the entire file — defeating I/O savings while still paying for hashing. Fixed: mtime + file size fast-path added. When both values match the cached record, the file is considered unchanged and SHA-256 is skipped entirely. SHA-256 still runs on first scan and whenever mtime or size changes (guaranteeing correctness on systems that backdated mtimes).

#### Manifest System — `imports` Field Ignored by Dependency Graph (`aquilia/aquilary/core.py`, `aquilia/manifest.py`)
- **Phase 3 graph construction read only `depends_on`**: The `AquilaryRegistry` Phase 3 loop called `dep_graph.add_node(name, deps)` where `deps` was always `getattr(manifest, 'depends_on', [])`. The v2-preferred `imports` field was never read. A manifest declaring `AppManifest(imports=["auth"])` produced zero dependency edges, resulting in: (1) wrong topological load order (auth may be initialized after billing), (2) DI cross-module services silently unresolvable — `DIFault` raised on first request to a cross-module endpoint. Fixed: Phase 3 now uses `getattr(manifest, 'imports', None) or getattr(manifest, 'depends_on', [])`, identical to the logic `aquilary/validator.py:335` already used.
- **`AppManifest.__post_init__` only synced one direction**: Previously `depends_on → imports` sync was implemented but `imports → depends_on` was not. A manifest using the v2 API (`imports=[...]`) never populated `depends_on`, so any code reading `depends_on` (including the old Phase 3) silently got an empty list. Fixed: bidirectional sync — whichever field is set first populates the other. `depends_on` usage emits `DeprecationWarning`.

#### Aquilary — Silent Autodiscovery Failures (`aquilia/aquilary/core.py`)
- **All 6 discovery phases used `except Exception: pass` or `contextlib.suppress(Exception)`**: A controller with a syntax error, a service with a missing import, or a socket controller in a broken package produced no output during startup — the developer had no way to know the class was never registered. All 6 handlers now emit `logger.warning("Auto-discovery: {phase} scan failed for module '%s': %s", ctx.name, exc, exc_info=True)` with the full traceback.

#### Aquilary — `except (ImportError, Exception)` Masks Surp Decode Failures (`aquilia/aquilary/core.py`)
- **`_from_frozen_manifest()` used `except (ImportError, Exception)`**: This is redundant (`Exception` already covers `ImportError`) and caused a subtle bug: when `surp` was installed but its `decode()` raised (e.g., version mismatch, corrupted artifact), the exception was caught by the broad handler and the code silently fell through to reading a `.json` file that may not exist. The actual decode error was hidden. Fixed: split into `except ImportError` (silent fallback to JSON — correct for "surp not installed") and `except Exception` (log + re-raise — surfaces real decode failures).

#### Aquilary — Dead `_build_router` Code Removed (`aquilia/aquilary/core.py`)
- Deleted the 30-line commented-out `_build_router` method and its orphaned call-site comment (`# self._build_router()`). The flow/router system it referenced was deprecated in an earlier release. Dead code belongs in git history, not production source.

#### Runtime — Regex-Based Workspace Module Discovery (`aquilia/runtime.py`)
- **`discover()` used regex over raw `workspace.py` source**: The regular expression `r'\.module\(\s*Module\(\s*["\']([^"\']+)["\']'` matched only literal string arguments — `Module("name")`. Any dynamically computed module name (environment variable, list comprehension, loop variable, multi-line call) was silently missed. No error was produced; those modules simply weren't discovered. Refactored: new `_load_workspace_from_exec()` executes `workspace.py` via `importlib.util.spec_from_file_location`, calls `workspace.to_dict()`, and derives both module names and workspace name from the real `Workspace` object. Regex kept as a logged fallback for cases where exec fails (import error in `workspace.py` itself).

#### Aquilary — Manifest Loader Executes Code It Promises Not To (`aquilia/aquilary/loader.py`)
- **`ManifestLoader._load_from_python_file()` documented "NEVER triggers import-time side effects" but called `exec_module()` unconditionally**: The class docstring made a promise the implementation didn't keep. Any module-level `print()`, singleton registration, network call, or decorator that triggers registration ran every time the manifest loader touched the file. Fixed: two-phase approach:
  - **Phase 1 (AST — zero side effects)**: Parse the file with `ast.parse()`, find the `manifest = <expr>` assignment, compile and `eval()` the expression in a restricted namespace containing only `AppManifest` and `Module`. No code is executed. Works for the common `manifest = AppManifest(name="...", ...)` pattern.
  - **Phase 2 (exec fallback — logged warning)**: When the AST expression cannot be statically evaluated (imports, conditionals, function calls), falls back to `_load_from_python_file_exec()` with a `logger.warning` that lists the file and states that module-level code will execute. The `sys.modules` save/restore race condition is eliminated in the Phase 1 path.

### Deprecated

- **`Secret("ALL_CAPS_IDENTIFIER")`** — positional strings matching `^[A-Z][A-Z0-9_]*$` emit `DeprecationWarning`. Use `Secret(env="VAR")` for env-var binding.
- **`AppManifest(depends_on=[...])`** — use `imports=[...]` (v2 API). `DeprecationWarning` emitted. Both fields remain functional and are kept in sync.

### Tests
- Added `tests/test_manifest_bidirectional_sync.py` — 12 tests covering `imports→depends_on`, `depends_on→imports`, DeprecationWarning, empty list behavior, conflict resolution.
- Added `tests/test_secret_disambiguation.py` — 8 tests: literal value, env-var explicit, env-var implicit legacy, DeprecationWarning for ALL_CAPS.
- Added `tests/test_graph_iterative.py` — 15 tests: 500-deep chain (no RecursionError), SCC correctness, transitive deps correctness, empty/single-node graphs.
- Added `tests/test_discovery_mtime_cache.py` — 6 tests: fast-path hit, fast-path miss on mtime change, fast-path miss on size change, first-scan always hashes.
- Added `tests/test_discovery_audit.py` — 22 tests covering autodiscovery diagnostics logging, middleware/controller/service/socket/model/task scan failure logging.
- Added `tests/test_workspace_exec_discovery.py` — 9 tests: dynamic module list, env-var conditional, loop-built modules, fallback on exec failure.
- Added `tests/test_validate_deprecated_flag.py` — 11 tests: `--deprecated` detects each deprecated field, clean manifests pass, `--json` output format.
- Updated `tests/test_integration_resolution.py` — updated to use `Secret(env=...)` API.

#### Discovery — Strict Resolved-Import Mode
- **`StrictDiscoveryEngine`** (`aquilia/discovery/engine.py`): New discovery engine subclass that uses `importlib.util.spec_from_file_location` and actual `inspect.getmro()` to discover workspace components instead of the default AST parsing.
- Correctly discovers classes using transitive inheritance, aliased imports (`Controller as Base`), and re-exports (`__all__`).
- Safe execution: handles `ImportError` gracefully per-file with a warning log, allowing discovery to continue.
- **`AutoDiscoveryEngine.discover(strict=True)`** — explicitly invoke strict discovery.
- **`aq discover --strict`** — CLI flag to use strict discovery mode.

#### Controllers — Distributed Throttle Backends
- **`ThrottleBackend` Protocol** (`aquilia/controller/throttle.py`): New abstraction for rate limiting with `is_allowed`, `get_count`, `reset`, and `close` async methods.
- **`MemoryThrottleBackend`**: Async-safe sliding window tracking using `asyncio.Lock`, with LRU eviction and periodic cleanup.
- **`RedisThrottleBackend`**: Redis-backed sliding window using sorted sets, with lazy connection and `fail_open` degradation support (requires `redis.asyncio`).
- **`Throttle` Updates**: Added `backend` parameter, `async def acheck(request)`, and ergonomic factories: `Throttle.with_memory(limit, window)` and `Throttle.with_redis(url, limit, window)`.
- **`ThrottleConfig`**: New dataclass in `aquilia.integrations.throttle` for dependency injection.

#### Controllers — Resource / ViewSet CRUD
- **`Resource[T]`** (`aquilia/controller/resource.py`): Generic base class that auto-registers CRUD routes based on the presence of `list`, `retrieve`, `create`, `update`, `partial_update`, and `destroy` methods via `__init_subclass__`.
- Supports explicit `id_param` and `id_type` configuration (defaults: `"id"` and `"int"`).
- **`@action` decorator**: Registers custom routes on a `Resource` with `detail=True` (mounts on `/{id}/...`) or `detail=False`.
- Pre-composed mixins (`ListMixin`, `RetrieveMixin`, etc.) and classes (`ReadOnlyResource[T]`, `CRUDResource[T]`).
- Routes integrate seamlessly with existing `ControllerCompiler` logic.

### Fixed (Phase 2)

#### Controllers — Lifecycle Hook Bypass (CRITICAL)
- **`ControllerEngine` fast-path skipped `on_request`/`on_response` for "simple" routes**: A route that required no pipeline, contract, or filters was executed via a fast path that completely ignored controller-level lifecycle hooks. Fixed: `is_simple` now consults the `_has_lifecycle_hooks` cache; any route belonging to a controller with custom lifecycle hooks is safely removed from the fast path.

#### Authentication — Unintended Token Generation (SECURITY)
- **`AuthManager.authenticate_password()` always issued JWTs**: Even in session-only authentication flows, successful authentication generated access and refresh tokens unnecessarily. Fixed: Added `issue_tokens: bool = True` to both `authenticate_password()` and `SignInProvisionPolicy`. Passing `False` skips token generation while fully resolving the identity.

#### Dependency Injection — Forward-Reference Type Resolution (BUG)
- **`metadata.py` `_extract_method_params()` misclassified types**: Used naive substring matching (`"Request" in param_type`) to detect the context request, which caused valid domain types like `PasswordResetRequest` to be silently stripped from the payload body parameters. Fixed: Upgraded to exact suffix matching. Added an `__annotations__` fallback for when `get_type_hints()` fails due to unresolvable forward references.

#### Controllers — Dynamic Segment Route Conflicts (BUG)
- **`ControllerCompiler` false-positive conflicts**: Controllers registering routes at the exact same path position with different type castors (e.g., `/<id:int>` vs `/<slug:str>`) raised a conflict error. Fixed: `_routes_conflict()` now considers type castors; mismatched types are no longer considered conflicting routes.

#### Controllers — Class-Level Cache Contamination (ARCH)
- **Stale cache entries from `id()` reuse**: Both `ControllerEngine` and `ControllerFactory` maintained `id()`-keyed caches (`_simple_route_cache`, `_clearance_cache`, etc.). Garbage-collected objects could have their memory addresses reused by new objects, serving them stale cached values. Fixed: Added `clear_caches()` classmethods to both classes for deterministic flushing between application tests/reloads.

#### Controllers — Router Performance (PERF)
- **`ControllerRouter.url_for()` O(n·m) linear scan**: Generating URLs required scanning the entire registered route list. Fixed: Added `_name_index` dictionary populated at initialization. `url_for()` lookups are now O(1).

### Added (Phase 3)

#### Cache — Configuration & Key Building
- **`CacheConfig.key_builder`** — select the key layout: `"default"` (colon segments) or `"hash"` (SHA-256 fixed length). Unknown values raise `ConfigInvalidFault` instead of silently falling back.
- **`CacheConfig.serializer_secret_key`** — HMAC signing key for the pickle serializer. Makes `serializer="pickle"` reachable through standard configuration for the first time; omitting it raises an actionable fault naming the exact setting.
- **`build_key_builder(strategy, *, version)`** factory and a `KeyBuilder` protocol documenting the contract for custom key builders. `CacheService.key_builder`, `key_prefix`, and `default_namespace` are now public properties.

#### Cache — Cross-Process Stampede Prevention
- **Distributed lock contract on `CacheBackend`** — `supports_distributed_lock`, `try_acquire_lock(key, ttl)`, and `release_lock(key, token)`. Implemented in `RedisBackend` with `SET NX PX` and a token-checked Lua release, so a holder whose lease expired cannot delete a lock another worker has since acquired. In-process backends advertise `False`, making the scope limitation explicit rather than implied.
- **New config**: `distributed_stampede_lock` (default `true`), `stampede_lock_ttl` (default `30.0`), `stampede_poll_interval` (default `0.05`). Verified with six independent backends sharing one Redis: one loader invocation total, versus six before.

#### Cache — Middleware
- **`CacheMiddleware(cache_authenticated=...)`** — explicit opt-in for caching identity-bearing responses, valid only when the identity header is also present in `vary_headers`.
- **`CacheMiddleware.drain(timeout=5.0)`** — awaits in-flight stale-while-revalidate refreshes, which are now tracked rather than fire-and-forget.

#### Cache — Diagnostics
- **`MemoryBackend.ttl_heap_size` / `lfu_heap_size`** — expose internal heap lengths for leak triage and tests.
- **`CompositeBackend.pending_writes` and `drain(timeout)`** — observe and await in-flight async L2 writes.

#### Storage
- **`aquilia/storage/executor.py`** — a dedicated, bounded thread pool (`run_blocking`, `get_executor`, `shutdown_executor`) shared by all cloud backends, replacing the interpreter's default executor. Threads are named `aquilia-storage`; size via `AQUILIA_STORAGE_MAX_WORKERS` (default `min(32, cpu_count + 4)`).
- **`S3Config.multipart_threshold` and `multipart_chunk_size`** — enable true S3 multipart upload, lifting the 5 GB single-request limit and bounding peak memory to one part. A failed part aborts the upload rather than leaving an incomplete one billing.
- **`LocalStorage.root`** — exposes the resolved sandbox root.

#### Filesystem
- **`FileSystemConfig.allow_unsandboxed`** (default `true`) — set to `false` to make an unset `sandbox_root` a loud configuration error instead of silently disabling path containment.
- **`FileSystem.copy_tree()` and `FileSystem.walk()`** — previously missing from the facade despite existing in the underlying module.
- **`AsyncFileStream.path` / `AsyncWriteStream.path`** — the resolved, sandbox-validated path.

#### Runtime — Filesystem Subsystem
- **`Integration.filesystem()`** — the filesystem is now a first-class subsystem. `Server._setup_filesystem()` builds a `FileSystem` over a dedicated pool and registers it in every DI container; the pool starts at `startup()` and drains at `shutdown()`. Keys: `enabled`, `sandbox_root`, `allow_unsandboxed`, `max_pool_threads`, `max_path_length`, `follow_symlinks`, `atomic_writes`. Disabled by default; manual registration continues to work.

#### HTTP
- **`Response.content` property and `Response.body()`** — public accessors for response content. `body()` returns encoded bytes, or `None` for streaming/awaitable content that cannot be materialised without consuming the stream.

### Changed (Phase 3)

- **Cache keys now carry the configured version.** Because `key_version` defaults to `1` and previously did nothing, generated keys gain a `v1:` segment (`aq:users:user:123` becomes `aq:v1:users:user:123`). Old entries are unreachable and expire under their own TTL — a one-time cold cache on deploy. Set `key_version=0` to keep the previous layout.
- **Decorator and service cache keys share one layout.** `@cached` no longer embeds the namespace twice and now carries the configured `key_prefix` and `key_version`.
- **`None` results are cached.** Functions returning `None` were recomputed on every call forever; they now cache for their TTL. Opt out with `condition=lambda r: r is not None`.
- **Authenticated responses are no longer served from the shared HTTP cache.** Requests carrying `Cookie` or `Authorization` bypass the cache, and responses setting `Set-Cookie` are never stored; both are marked `X-Cache: PRIVATE`. Opt in with `cache_authenticated=True` plus the identity header in `vary_headers`.
- **Storage registry boot is criticality-aware.** A failing default backend raises `BackendUnavailableError`; a failing optional backend is logged, reported unhealthy, and no longer prevents the application from starting. Shutdown logs failures instead of silently swallowing them.
- **`StorageSubsystem` is documented as the `BootContext` entry point** for embedders and alternative runners, complementing (not competing with) `AquiliaServer._setup_storage()`. Both share `StorageRegistry`, so behaviour cannot diverge.

### Fixed (Phase 3)

#### Cache — `@cached` Returned Values From Other Calls (CRITICAL)
- **First positional argument was excluded from every cache key**: the decorator decided whether to strip a bound `self` with `hasattr(args[0], "__class__")`, which is true for every Python object. All calls to a single-argument function collapsed onto one key, so `fetch(2)` silently returned `fetch(1)`'s value. Fixed with a real method check based on the function's qualified name and the runtime type of the first argument. This was a silent data-correctness bug, not an error — flush affected namespaces after upgrading.

#### Cache — HTTP Response Cache Leaked Across Users (CRITICAL / SECURITY)
- **Default `vary_headers` excluded `Cookie` and `Authorization`**: with the middleware at `scope="global"`, the first authenticated user to hit a path had their response cached and served to every subsequent visitor until the TTL expired — the cache-poisoning class behind numerous real-world CDN data leaks. The safe configuration was not the default. Fixed with two safeguards that cannot be disabled implicitly: identity-bearing requests bypass the cache unless explicitly opted in, and `Set-Cookie` responses are never stored.

#### Cache — Response Bodies Were Cached Empty (BUG)
- **Middleware read a nonexistent `Response.content`**: the attribute had been made private, and a `hasattr` guard converted the resulting failure into a silent `b""` default. Every cached entry had an empty body and an ETag computed over empty bytes, so a cache *hit* served a blank response. Fixed by adding public `content`/`body()` accessors; content that cannot be materialised is treated as not cacheable rather than stored as a blank.

#### Cache — Middleware Was Never Installed (BUG)
- **`Server._setup_cache()` passed an invalid `ttl=` argument** to `CacheMiddleware`. The `TypeError` was swallowed by a broad `except`, logged as a non-fatal init failure, and the response cache was silently never installed even when explicitly enabled. Configured `cacheable_methods`, `vary_headers`, and `stale_while_revalidate` were also dropped. Fixed, and `set_default_cache_service()` is now invoked so `@cached` on standalone functions resolves the configured service.

#### Cache — Header Casing (BUG)
- **Mixed-case header writes bypassed `Response`'s lowercase normalisation**: `Cache-Control: no-store` / `private` and the `X-Cache-TTL` per-route override were read with mixed-case names against a lowercase mapping and never matched. Fixed: all writes go through `Response.set_header()`, and reads are case-insensitive.

#### Cache — Dead `key_version` Configuration (BUG)
- **`CacheConfig.key_version` never reached the key builder**: it was parsed from config and exposed in `to_dict()`, but `CacheService` constructed `DefaultKeyBuilder()` with no arguments, which defaults to `version=0` and omits the version segment. The documented mass-invalidation workflow silently did nothing. Fixed.

#### Cache — Duplicated Key Builders (ARCH)
- **`decorators.py` held a second module-level builder** pinned at `version=0` and invisible to the configured `key_prefix`. Its `from_args()` already prefixed the namespace, and `CacheService` prefixed it again, embedding the namespace twice in every decorator key. Fixed: the decorator computes only the call signature and the service applies namespace, prefix, and version exactly once.

#### Cache — LFU Eviction Was O(n) (PERF)
- **Docstring claimed "Min-heap + frequency counter with O(log n) eviction"; the code did `min(self._freq_counter, key=...)`** — a linear scan over every key on every eviction, with no LFU heap existing at all. Fixed with a real `(frequency, key)` min-heap using lazy invalidation, giving amortised O(log n).

#### Cache — Unbounded Memory Heap Growth (BUG)
- **`_ttl_heap` grew without bound**: `set()` pushed a tuple on every TTL'd write and `_evict_key()` — the single index-cleanup path — never touched the heap. Workloads that rewrite the same TTL'd key (session refresh, rate-limit counters) leaked steadily in long-running processes without affecting correctness, so tests never caught it. Fixed with lazy invalidation and bulk compaction against live entries: 2,000 rewrites of one key now bound the heap to ≤ 16 entries, versus 2,000 before.

#### Cache — Redis Claimed Lua Atomicity That Did Not Exist (BUG / DOCS)
- **Docstring advertised "Lua scripts for atomic operations"; no `EVAL` or `register_script` call existed.** `increment()` was an `exists()` check followed by a separate `incrby()` — a check-then-act race where concurrent callers on a missing key can both observe "absent". Fixed with a real Lua script evaluating both steps atomically. Verified against live Redis: 50 concurrent increments on a counter seeded at 10 produced 50 distinct results with a maximum of exactly 60.

#### Cache — Redis Tag and Namespace Sets Grew Forever (BUG)
- **Nothing removed set membership when a key expired via Redis' own TTL.** Workloads relying on natural expiry accumulated stale members indefinitely. Fixed with a Lua prune that returns live members and `SREM`s the rest in the same round trip, invoked by `delete_by_tags`, `clear(namespace)`, and `keys(namespace=...)`.

#### Cache — Redis `get()` Always Returned Empty Tags (BUG)
- **Tags and namespace were not fetched back on read**, so code written and tested against `MemoryBackend` that inspected `entry.tags` silently misbehaved against Redis in production. Fixed with a TTL-matched sidecar hash that expires with the entry; `keys()` filters internal `_meta:`, `_tags:`, and `_ns:` keys from results.

#### Cache — Composite Async L2 Writes Could Be Dropped (BUG)
- **`asyncio.ensure_future(...)` results were discarded**, so writes could be garbage-collected mid-flight and `shutdown()` had no way to await them — on the code path whose entire purpose is L2 durability. Fixed by tracking tasks until completion and draining on shutdown. Verified against live Redis: 25 async writes followed immediately by shutdown produced 25 durable entries with tags intact.

#### Cache — Pickle Serializer Was Unreachable (BUG)
- **`create_cache_backend()` called `get_serializer()` without a secret key**, and no such field existed in `CacheConfig`, so `serializer="pickle"` always raised — a documented option unreachable through any standard configuration flow. Fixed via `serializer_secret_key`; the serializer still refuses to run unsigned.

#### Filesystem — Streaming Bypassed Sandbox Validation (CRITICAL / SECURITY)
- **`stream_read`, `stream_copy`, `AsyncFileStream`, and `AsyncWriteStream` accepted `config` and `sandbox` arguments and ignored them entirely** — `_security` was not even imported. The `FileSystem` facade exposed identical method shapes on both sides, so a developer assuming parity between `read_file(sandbox=...)` and `stream_read(sandbox=...)` got complete path-traversal exposure on the second call, with no error and no warning, on the code path recommended for large user-uploaded files. Fixed: paths are validated and canonicalised at construction, before any descriptor is opened.

#### Filesystem — Directory Operations Raised `TypeError` (CRITICAL)
- **Every `FileSystem` directory method was unusable**: `list_dir`, `scan_dir`, `make_dir`, `remove_dir`, and `remove_tree` passed `config=`/`sandbox=` to `_directory` functions that accepted neither, raising `TypeError: list_dir() got an unexpected keyword argument 'config'`. Fixed: the underlying functions accept and enforce both, closing the same traversal gap as the streaming path.

#### Storage — `LocalStorage` Containment Bypass (CRITICAL / SECURITY)
- **`str(full).startswith(str(self._root))` allowed sibling-directory escape**: with a root of `/var/data`, the path `/var/data-private/secret.txt` satisfies the prefix test despite being outside the root. The framework's own `filesystem/_security.py` already handled this correctly — `storage/backends/local.py` reimplemented sandboxing independently and incorrectly. Fixed by delegating to the single canonical `validate_path`, which resolves symlinks and compares path components.

#### Storage — Full-File Buffering Contradicted the Streaming Contract (PERF)
- **`LocalStorage.open()` called `read_bytes()` and `S3Storage.open()` called `Body.read()`**, materialising entire objects in memory despite `StorageFile` being documented as supporting `async for chunk in sf`. Multi-gigabyte transfers risked out-of-memory failures. Fixed: local reads/writes/copies go through the filesystem streaming primitives and S3 iterates `StreamingBody` in chunks; content materialises only if `read()` is called explicitly.

#### Storage — Deprecated and Unbounded Executor Usage (SCALE)
- **Every cloud backend called `asyncio.get_event_loop().run_in_executor(None, ...)`**, placing storage I/O on the interpreter's shared default executor with no way to size or observe it, using the deprecated loop accessor inside coroutines. Fixed across S3, GCS, Azure, SFTP, and `StorageBackend._read_content`.

#### Runtime — Health Checks Reported Hardcoded `HEALTHY` (BUG)
- **Cache and storage health were registered as literal `HEALTHY` without probing anything.** An unreachable cache backend, or one storage disk out of five being down, was invisible to `/health`. Fixed: cache performs a real write/read/delete round trip, storage pings every backend and registers a `storage.<alias>` entry per disk plus a `healthy`/`degraded`/`unhealthy` aggregate naming the failing aliases, and the filesystem reports pool state.

#### Dependency Injection — Patch Broke the Public Exception Contract (CRITICAL)
- **`patch_di_container()` re-raised `ProviderNotFoundFault` in place of `ProviderNotFoundError`.** Since the former is not a subclass of the latter, every `except ProviderNotFoundError` handler silently stopped working the moment any server was constructed in the process. The conversion was also redundant — `ProviderNotFoundError` already subclasses `DIFault`. Fixed: the original error is enriched in place with `provider`, `tag`, and `candidates` metadata and re-raised unchanged. The patch is now idempotent; repeated server construction previously stacked wrappers without bound.

### Security (Phase 3)

- **Two critical path-traversal exposures closed** — the filesystem streaming path silently ignored its sandbox argument, and `LocalStorage` used a prefix-match containment check vulnerable to sibling-directory escape. Path containment now has exactly one implementation in the framework, used by both subsystems.
- **Cross-user HTTP response cache leak closed** — authenticated responses are no longer served from a shared, identity-independent cache entry.
- **Secure-by-default opt-in added** — `allow_unsandboxed=False` turns a missing sandbox root into a loud configuration error.
- **Signed pickle serialization made usable** — the HMAC-signed serializer is reachable through configuration and still refuses to deserialize unsigned payloads.
- **Trust boundary documented** — `StorageRegistry.create_backend()` imports any dotted path in configuration and is effectively an arbitrary-module-load primitive; storage configuration must never be derived from request data.

### Performance (Phase 3)

- LFU eviction is amortised O(log n) instead of O(n) per eviction.
- TTL and LFU heaps are bounded relative to live entries, eliminating a slow memory leak in long-running processes.
- Redis `get()` fetches value, TTL, and metadata in a single pipelined round trip.
- Local and S3 object reads are memory-bounded to one chunk regardless of object size.
- S3 uploads above the threshold use multipart, lifting the 5 GB limit and bounding peak memory to one part.
- Storage I/O runs on a dedicated bounded pool instead of competing with unrelated work on the shared default executor.

### Documentation (Phase 3)

- Comprehensive docstrings — description, arguments, returns, raises, notes, and usage examples — across every new and modified public API in `aquilia.cache`, `aquilia.storage`, and `aquilia.filesystem`.
- Docstring/implementation drift corrected where documentation claimed behaviour the code did not have (LFU heap eviction, Redis Lua atomicity, storage streaming without full materialisation).
- `validate_path` now documents that symlinks are always resolved for the containment check regardless of `follow_symlinks`, which governs metadata semantics only.
- New release note pages: [Cache System Audit Fixes](releases/1.3.4/cache_audit.md), [Storage & Filesystem Audit Fixes](releases/1.3.4/storage_filesystem_audit.md), [Subsystem Lifecycle & Health](releases/1.3.4/subsystem_lifecycle.md).

### Tests (Phase 3)

- **`tests/test_cache_storage_filesystem_audit.py`** — 59 regression tests pinning every Phase 3 finding, named by audit ID. Coverage includes cross-user cache leakage through the real `Request`/`Response` pipeline, sibling-directory traversal via planted symlinks, streaming sandbox enforcement on both source and destination, heap-growth bounds, decorator key correctness, and registry failure semantics.
- Redis-backed behaviour (Lua atomics, tag pruning, sidecar round-trip, distributed locking, composite write durability) verified against a live Redis 7 instance in addition to the offline suite.
- Full suite: 7,023 passing, 21 skipped. Ruff lint and format clean.

## [1.3.3] — 2026-07-21 — "Analytical Depths"

### Added

#### ORM — Window Function Support (`aquilia.models.window`)
- **`Window(expression, *, partition_by, order_by, frame)`** — first-class `OVER (...)` expression. Wraps any aggregate or window function with a full window clause. Integrates with `annotate()`, `order_by()`, `values()`, and `values_list()` without restrictions.
- **Ranking functions**: `Rank()` → `RANK()`, `DenseRank()` → `DENSE_RANK()`, `RowNumber()` → `ROW_NUMBER()`.
- **Distribution**: `Ntile(n)` → `NTILE(n)`.
- **Offset functions**: `Lag(expr, offset=1, default=None)` → `LAG(expr, offset[, default])`, `Lead(expr, offset=1, default=None)` → `LEAD(expr, offset[, default])`.
- **Value access**: `FirstValue(expr)` → `FIRST_VALUE(expr)`, `LastValue(expr)` → `LAST_VALUE(expr)`, `NthValue(expr, n)` → `NTH_VALUE(expr, n)`.
- **Aggregate windows**: Any existing aggregate (`Sum`, `Avg`, `Count`, `Max`, `Min`) can be used directly inside `Window(...)` for running totals, cumulative averages, etc.
- **Frame clauses** via `WindowFrame(frame_type, start, end)` + `FrameBound` helpers (`FrameBound.unbounded_preceding()`, `FrameBound.current_row()`, `FrameBound.unbounded_following()`, `FrameBound.preceding(n)`, `FrameBound.following(n)`). Frame types: `FrameType.ROWS`, `FrameType.RANGE`, `FrameType.GROUPS`.
- **Partition**: `partition_by` accepts `str`, `F()`, or a list of either — rendered as quoted identifiers.
- **Ordering**: `order_by` inside the window accepts `str` (prefix `-` for DESC), `OrderBy`, or a list of both.
- Full `as_sql(dialect)` support across SQLite 3.25+, PostgreSQL 8.4+, MySQL 8.0+.

#### ORM — CTE Support (`aquilia.models.cte`)
- **`Q.cte(name)`** — creates a `CTE` object from any queryset. Non-executing; wraps the queryset's compiled SQL as a named CTE.
- **`Q.with_cte(*ctes)`** — registers one or more `CTE` or `RecursiveCTE` objects. Chains additively. Automatically promotes preamble to `WITH RECURSIVE` when any recursive CTE is present.
- **`CTE`** class — represents `name AS (SELECT ...)`. Call `.col('field')` to get a `CTECol` expression reference for use inside other queries.
- **`CTECol(cte_name, column)`** — `Expression` subclass rendering `"cte_name"."column"`, for referencing CTE columns in filters and annotations.
- **`CTEReference`** — used inside recursive lambda to reference the CTE itself. Supports `.col('field')` returning `CTECol`.

#### ORM — Recursive CTE Support (`aquilia.models.cte`)
- **`Q.recursive_cte(name, anchor, recursive, *, union_all=True)`** — high-level API for `WITH RECURSIVE`. Accepts:
  - `anchor`: lambda `(Q) → Q` — the base, non-recursive term.
  - `recursive`: lambda `(CTEReference) → Q` — the recursive term; use `cte_ref.col('id')` for self-referential joins.
  - `union_all`: `True` (default) for `UNION ALL`, `False` for deduplicating `UNION`.
- Supports tree traversal (folder trees, comment trees, org charts), dependency graphs, and category hierarchies.
- **`RecursiveCTE`** class — renders as `name AS (anchor UNION [ALL] recursive_part)`.
- CTE parameters are prepended before annotation and WHERE parameters in the final bind list, preserving correct positional order.
- Cyclic-guard: the SQL engine handles cycle termination natively; Aquilia emits the correct `WITH RECURSIVE` syntax.

#### ORM — Bug Fixes (from audit in this release)
- **`UUIDField(auto=True)` NULL insert bug**: `setdefault` on pre-populated `kwargs` dict was a no-op. Fixed to explicit `UNSET` sentinel check — `auto=True` fields now always generate a UUID default, never `NULL`.
- **Transaction nesting depth tracker memory leak and `id()` reuse contamination**: Replaced `WeakValueDictionary` keyed on `id(task)` with a `contextvars.ContextVar[int]` — consistent with all other Aquilia subsystems, leak-free, and isolation-safe under `asyncio.gather()`.

#### ORM — Security & Concurrency Hardening (from senior-engineer assessment)
- **Widened raw-SQL safety guard on `Q.where()`/`Q.having()`** (`aquilia/models/query.py`): both methods previously used two separate, inconsistent keyword blocklists — `where()` only rejected `DROP/ALTER/TRUNCATE/EXEC/EXECUTE` via a trailing-space substring match (vulnerable to false positives like `"AIRDROP "`), `having()` had a wider-but-still-incomplete set and no word-boundary matching. Replaced both with one shared, word-boundary regex guard (`_reject_unsafe_clause`) that additionally blocks `DELETE`, `INSERT`, `UPDATE`, `MERGE`, SQL comment markers (`--`, `/*`, `*/`), and bare `;` (statement-stacking). A column literally named `updated_at` no longer false-positives on `UPDATE`. This is a secondary guardrail, not the actual injection defense — parameter binding remains the real protection; the guard only catches unparameterized raw clauses.
- **`get_or_create()` / `update_or_create()` now emit `RuntimeWarning`** (`aquilia/models/base.py`): both are a plain SELECT-then-INSERT/UPDATE and were already documented as non-atomic, but nothing surfaced that at runtime. They now warn on every call, pointing at `find_or_create()` (backed by `INSERT ... ON CONFLICT`) for race-free upserts under concurrent access. Fixed once in the canonical `Model` classmethods — `Manager.get_or_create()`/`update_or_create()` and `Q.get_or_create()`/`update_or_create()` both forward into these, so the warning covers all three call sites.

#### ORM — Enterprise Field Types
- **`MoneyField(DecimalField)`** — currency-aware decimal field. Adds a `currency` parameter (3-letter code, shape-validated, no bundled ISO 4217 table) alongside `DecimalField`'s existing precision-safe storage; `deconstruct()` includes `currency` for migration diffing.
- **`EncryptedField(EncryptedMixin, TextField)`** — transparent application-layer encryption at the storage boundary, built on the existing (previously unused-in-production) `EncryptedMixin`. Fixed a latent bug found while wiring this up: `EncryptedMixin.to_db()` didn't accept the `dialect` keyword argument every real `Model.save()` call site passes (`field.to_db(value, dialect=dialect)`), so any mixed-in encrypted field would raise `TypeError` the moment it was actually saved through a model — only ever exercised standalone in tests before. `to_db()` now accepts (and ignores) `dialect`.
- **`PointField` / `GeometryField` (both `JSONField` subclasses)** — portable GeoJSON-backed spatial fields. `GeometryField` validates a `{"type": <GeoJSON type>, "coordinates": [...]}` shape against the standard GeoJSON geometry types; `PointField` further restricts to a single `Point` with 2 numeric coordinates. Stored as `TEXT`/`JSONB` exactly like any other JSON value — no PostGIS/native geometry column and no new dependency.
- **`GenericForeignKey`** — polymorphic relation to any registered model, Django's "virtual field" pattern: deliberately *not* a `Field` subclass (so `ModelMeta`'s column-collection scan ignores it), attached alongside two real columns the model declares itself (a model-label column + a stringified-PK column). Resolution is an explicit async method — `await field.resolve(instance)` — rather than a transparent attribute, since Aquilia is async-native and can't do a lazy synchronous DB fetch on attribute access. Reuses the existing `ModelRegistry.get(label)` lookup (the same primitive `ForeignKey` already uses for string-based relation resolution) instead of introducing an app-level `ContentType` model.
- All four field types required no new dependencies and no changes to schema-generation/migration dialect-mapping code — each subclasses an existing field whose `isinstance()`-based SQL-type dispatch already matches subclasses.

### Fixed
- `UUIDField(auto=True)` produced `NULL` primary keys on `create()` and `save()`. All existing UUID-PK round-trip, FK reference, and multi-create tests pass.
- Transaction nesting depth could be inherited or corrupted by sibling/child tasks due to `id()` reuse. Depth is now fully task-local via `ContextVar`.
- `Q.where()`'s raw-SQL guard missed `DELETE`/`INSERT`/`UPDATE`/`MERGE` and comment-injection markers; `Q.having()`'s guard used the same weak substring matching. Both now share one word-boundary regex guard.
- `EncryptedMixin.to_db()` signature mismatch (`TypeError` on real `dialect=` keyword calls) — see Enterprise Field Types above.
- Resolved Issue #59: `Controller.render()` / `Response.render()` raised `[TEMPLATE_RENDER_ERROR] No TemplateEngine available`. Prioritized `container.resolve_async()` over `container.resolve()` in `Response.render()` to prevent event loop sync-bridge failures, added `_integration_type: "templates"` to `TemplatesIntegration._Builder`, stored `template_engine` in `TemplateMiddleware` request state, auto-enabled template discovery when `templates/` exists, and bound template search paths to `workspace_root`.

### Documentation
- Documented Aquilia's deliberate lack of an identity map and unit-of-work (no session-scoped object identity, no deferred-flush batching) in `aqdocx/orm_new_pages_content.md`, alongside the existing `get_or_create`/`update_or_create`/`find_or_create` guidance.

### Tests
- Added 34 regression tests (`tests/test_uuid_pk_auto.py`) covering UUID field init, validation, serialisation, SQL types, deconstruct, DB create/round-trip, and FK references.
- Added 19 regression/concurrency tests (`tests/test_txn_depth_contextvar.py`) covering depth tracking, concurrent task isolation, `id()` reuse non-contamination, savepoint behaviour, decorator form, and commit/rollback hooks.
- Added window function SQL generation and integration tests (`tests/test_window_functions.py`).
- Added CTE and recursive CTE tests (`tests/test_cte_queries.py`).
- Added `TestWhereHavingClauseGuard` to `tests/test_orm_security.py` covering DML/DDL keyword rejection, comment-marker rejection, and identifier-substring false-positive avoidance on `Q.where()`/`Q.having()`.
- Added `tests/test_orm_concurrency_warnings.py` covering the new `get_or_create()`/`update_or_create()` `RuntimeWarning` and confirming `find_or_create()` does not warn.
- Added `tests/test_orm_enterprise_fields.py` (14 tests) covering `MoneyField` precision/currency validation, `EncryptedField` round-trips (including the `dialect=` regression), `PointField`/`GeometryField` GeoJSON validation, and a live-DB `GenericForeignKey` attach/resolve round-trip.

### Backend Compatibility
| Feature | SQLite | PostgreSQL | MySQL/MariaDB |
|---|---|---|---|
| Window Functions | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 |
| CTEs | ≥ 3.8.3 | ≥ 8.4 | ≥ 8.0 |
| Recursive CTEs | ≥ 3.8.3 | ≥ 8.4 | ≥ 8.0 |
| Frame Clauses | ≥ 3.25 | ≥ 8.4 | ≥ 8.0 |
| `MoneyField` / `EncryptedField` | ✓ | ✓ | ✓ |
| `PointField` / `GeometryField` | ✓ (TEXT) | ✓ (JSONB) | ✓ (TEXT) |
| `GenericForeignKey` | ✓ | ✓ | ✓ |

## [1.3.2] — 2026-07-17 — "Specula API Observatory"

### Added
- **Specula API Observatory (`aquilia.specula`)**: Replaces the entire legacy, static OpenAPI engine with a first-class, metadata-enriched Specula compiler. Features a modern, CDN-free interactive UI dashboard hosted locally at `/specula`.
- **Specula Config & Integration**: Accessible via `Integration.specula(...)` or the direct class `SpeculaIntegration` in `workspace.py`, supporting custom paths, themes, cache TTL, and mock parameters.
- **Dynamic Spec Compilation (`SpeculaBuilder`)**: Directly constructs OpenAPI 3.1.0 specifications from compiler topologies, routing, type annotations, and clearance metadata with zero code scanning.
- **Interactive Mock Server (`/specula/mock`)**: Automatically serves plausible example payloads computed dynamically from JSON Schema structures up to a configurable recursion depth.
- **Auto-Detection of Security & Clearance**: Inspects pipeline guards, `@authenticated` decorators, and AccessLevel clearance settings to dynamically define OpenAPI security requirements and populate detailed vendor extensions (`x-specula-security`).
- **Postman & Insomnia Exports**: Exposes endpoints (`/specula/export/postman` and `/specula/export/insomnia`) to download collections dynamically configured with your API topology.
- **Server-Sent Events (SSE) Stream (`/specula/stream`)**: Automatically pushes invalidation events to the client browser to refresh the Observatory dashboard during local code hot-reloading.

### Removed
- Legacy OpenAPI generator engine (`aquilia.controller.openapi`), static swagger/redoc HTML generators, and redirect endpoints `/docs` and `/redoc`.
- Backward-compatibility aliases for legacy `OpenAPIConfig` and `Integration.openapi(...)`.

## [1.3.1] — 2026-07-13 — "Backend Refactoring"

### Added
- **Pluggable Auth Backends** (`aquilia.auth.backends`): Introduced a single-responsibility, backend-driven architecture for resolving identities from credentials. Out-of-the-box backends:
  - `TokenBackend`: Validates JWT tokens from the `Authorization: Bearer` header.
  - `SessionBackend`: Resolves identity from active sessions.
  - `PasswordBackend`: Authenticates username/password combinations.
  - `ApiKeyBackend`: Validates custom API keys (`x-api-key` or `ApiKey` header).
- **First-class Flow Guards**: `AuthGuard`, `RoleGuard`, `ScopeGuard`, and `PolicyGuard` are now first-class objects that can be referenced as classes (e.g. `pipeline.guard(AuthGuard)`) or instantiated with parameters (e.g. `pipeline.guard(RoleGuard("admin"))`).
- **Context-First Decorators**: Simplified and ergonomic decorators for endpoint protection:
  - `@authenticated`
  - `@roles_required("admin", "staff")`
  - `@scopes_required("read", "write")`
  - `@optional_auth`
- **PermissionEngine**: Unifies role hierarchies and fine-grained authorization policies under a single component.
- **Clock-Skew Tolerance**: Added `clock_skew_seconds` parameter to `TokenConfig` and `AquilaConfig.Auth` (default `0`) to permit clock drift tolerance during JWT `exp` and `nbf` validation.
- **Relocated RateLimiter**: Moved rate limiting tracking to a standalone `RateLimiter` class in `aquilia.auth.manager_types.py` to prevent circular imports.
- **Pluggable Auth Middleware**: Unified request authentication pipeline under a new `AuthMiddleware` class (`aquilia.auth.middleware.AuthMiddleware`).
- **Expanded PyConfig parameters**: Added settings `rate_limit_max_attempts`, `rate_limit_window_seconds`, `rate_limit_lockout_seconds`, `mfa_enabled`, `mfa_required`, `clock_skew_seconds`, and `audit_enabled` directly to `AquilaConfig.Auth`.

### Changed
- **Session Security Hardening**: To prevent stale privileges, global session integration now only serializes `identity_id` and `tenant_id` inside sessions. User roles, scopes, and attributes are resolved fresh from the identity store on every request.
- **Backend Configuration**: Replaced string-based `strategies` in `AquilaConfig.Auth` and `AquilAuthMiddleware` with the `backends` parameter, taking resolved backend references (dotted paths, classes, or short names).
- **Token Revocation Enhancement**: `AuthManager.revoke_token()` now supports revoking access tokens directly by extracting their `jti` claim and adding it to the revocation blacklist.
- **DI Service Scopes Optimization**: Migrated the Dependency Injection (DI) service scope definitions (like `"singleton"`, `"app"`, `"request"`, `"transient"`, `"pooled"`, `"ephemeral"`) from `ServiceScope` enum members to high-performance string literals backed by `typing.Literal` type hints (`ServiceScopeLiteral`). This completely eliminates runtime import/lookup overhead and leverages Python's built-in string interning for maximum efficiency during dependency resolution.

### Deprecated
- `AuthManager.logout()` is deprecated in favor of `sign_out()`.
- `OptionalAuthMiddleware` is deprecated in favor of `AquilAuthMiddleware(require_auth=False)`.
- The `ServiceScope` Enum class is deprecated across both `aquilia.di` and `aquilia.manifest` modules. Calling it or accessing its attributes triggers a `DeprecationWarning`. Use plain string literals (e.g. `"singleton"`, `"app"`) instead.

### Removed
- Legacy guard adapters (`flow_guards.py`) and authentication policy DSL (`policy/` directory).
- `surp.py` formatting helpers inside `aquilia/auth`.
- Fluent builder `AuthConfig` in favor of declarative `AquilaConfig.Auth`.
- `SessionGuard` and `requires` decorators from `aquilia.sessions.decorators`.
- Legacy decorators `AdminGuard` and `VerifiedEmailGuard`.

## [1.3.0] — 2026-07-11 — "Ironclad Anchor"

### Renamed
- `Blueprint` → `Contract` throughout — all classes, modules, paths, and docs.
  The concept is unchanged; only the identifier has been renamed.
  Fault codes (BP000–BP501) are unchanged.

### Added
- **`Attributes` fluent builder for Controllers** (`aquilia.controller.attrs`):
  Introduced `Attributes()`, a fluent method-chaining builder that provides
  an ergonomic alternative to inline `Controller` class attribute declarations.

  ```python
  from aquilia import Controller, GET, Attributes, RequestCtx

  class ProductsController(Controller):
      attr = (
          Attributes()
          .prefix("/products")
          .tags("Products")
          .pipeline(AuthPipeline)
          .instantiation_mode("singleton")
          .timeout(30.0)
          .max_body_size(4096)
      )

      @GET("/")
      async def list_products(self, ctx: RequestCtx):
          ...
  ```

  Supported methods: `.prefix()`, `.pipeline()`, `.tags()`, `.instantiation_mode()`,
  `.version()`, `.throttle()`, `.interceptors()`, `.exception_filters()`,
  `.timeout()`, `.max_body_size()`.

  Implementation notes:
  - Uses `__set_name__` descriptor protocol — configuration is applied at
    class-definition time with zero request-path overhead.
  - Uses `__slots__` for ~40% faster attribute access and lower memory.
  - Validates configuration eagerly in `__set_name__`, raising `ConfigInvalidFault`
    at class-definition time (not at dispatch time).
  - Fully backwards-compatible — all existing inline declarations continue to
    work unchanged.
  - When both inline attributes and `Attributes()` configure the same field,
    the builder value takes precedence (it applies after the class body).
  - Imported and re-exported from `aquilia` top-level: `from aquilia import Attributes`.
- **Configurable Authentication Strategies**: Enabled configuring active auth strategies ("token", "session") on `AquilAuthMiddleware`, `AuthConfig`, and `AuthIntegration` to allow users to enforce only session-based authentication, only token-based authentication, or both at the same time.
- **Native PyConfig & DotEnv Resolution Support for Integrations**:
  - Native support for `Env` and `Secret` wrappers directly in integrations and provider wrappers.
  - Automatic resolution of `Env`, `Secret`, and PyConfig configuration objects/fields at the correct lifecycle stage.
  - Automatic type conversion and casting of environment variables (e.g. `Env("PORT", cast=int)` resolves to an integer).
  - Secure automatic secret resolution through `Secret` wrappers without requiring manual `reveal()` or primitive extraction.
  - Complete backwards compatibility and zero breaking changes for existing string-based and int-based configurations.
- **`Field` Positional & Ellipsis Support** (`aquilia/contracts/annotations.py`):
  - Support passing a single positional default argument to `Field()`.
  - Passing `...` (Ellipsis) positionally now automatically translates to `required=True` with `UNSET` default:
    ```python
    message: str = Field(...)  # translates to required=True, default=UNSET
    ```
  - Positional defaults (such as `Field("default_val")`) are natively resolved.
  - Adding contradictory arguments like `Field(..., default="val")` raises a structured `ConfigInvalidFault` rather than a generic Python `TypeError`.
- **`EffectNotAcquiredFault`** (`aquilia.faults.domains`): New structured
  fault subclassing `EffectFault` that replaces the bare
  `EffectFault(code="EFFECT_NOT_ACQUIRED")` raised by `ctx.get_effect()`,
  `FlowContext.get_effect()`, and `EffectRegistry.get_provider()`. The new
  fault carries rich diagnostics in `metadata`:
  - `effect`: the effect name that was requested
  - `registered`: all effects currently in the registry
  - `middleware_active`: whether `EffectMiddleware` ran for this request
  - `hint`: a concise, actionable remediation message tailored to the
    probable root cause (missing `@requires`, unregistered provider, or
    inactive middleware)
- **`_DeferredEffectRegistry`** (`aquilia.middleware_ext.effect_middleware`):
  Lazy proxy that delegates `has_effect`, `acquire`, `release`, and
  `providers` to a live `EffectRegistry` resolved at request time via a
  zero-argument callable. Eliminates the need for `EffectMiddleware` to have
  a fully-populated registry at construction time, correctly handling the
  ASGI startup ordering where providers are registered in `on_startup()`
  long after the middleware stack is built in `__init__()`.
- **`atomic()` as a decorator**: `@atomic()` on an `async def` now wraps the whole call in its own
  transaction (Tortoise-ORM-style), constructing a fresh `Atomic` per call so concurrent calls to
  the decorated function don't share mutable transaction state.
- **`atomic(readonly=True)`**: hints that a block only reads. On SQLite this routes to a reader
  connection instead of contending for the pool's single writer (Aquilia's own N-readers+1-writer
  design already made this possible; `atomic()` just wasn't using it). Other backends pass
  `readonly` straight to their native read-only transaction support (asyncpg `transaction(readonly=
  True)`, `SET TRANSACTION READ ONLY` for MySQL/Oracle).
- **`atomic(timeout=...)`** (seconds): Prisma-style interactive-transaction timeout. A watchdog
  cancels the enclosing task if the block hasn't finished in time; the transaction is rolled back
  and a `QueryFault` is raised instead of leaving a transaction open indefinitely.
- **`RelatedManager` / `Model.related_manager()`**: reverse relations (rows in another table whose `ForeignKey` points back at an instance) can now be accessed lazily and chained like any other queryset: `await user.related_manager("verifications").filter(expires_at__gt=now).order("-created_at").first()`. Previously `Model.related()` was the only reverse-relation entry point and always eagerly awaited a fully materialized list. `related()` itself is unchanged in contract — it now delegates to `related_manager(name).all()` (or `.first()` for a `OneToOneField`'s reverse side, matching its actual 1:1 cardinality instead of returning a list).
- **`RelatedNotLoaded` sentinel** (`aquilia.models.relations`): reading a `ForeignKey`/`OneToOneField` attribute that hasn't been hydrated via `select_related()`, `prefetch_related()`, or `await instance.related(name)` now returns this sentinel instead of the raw stored id. Cheap operations work directly on it without a query (`.pk`/`.id`, `bool(...)`, `== other_instance`/`== raw_pk`); any other attribute access raises `RelatedNotLoadedFault` with actionable guidance. Aquilia's DB layer is 100% async and `__get__` can't be `async def`, so — unlike Django's `ForwardManyToOneDescriptor` — there is no transparent hidden query; hydration stays explicit and awaited, this only replaces the previous silent-wrong-type footgun on the read side.
- **`RelatedNotLoadedFault`, `RelatedTypeMismatchFault`, `RelatedNameConflictFault`** (`aquilia/faults/domains.py`): new `ModelFault` subclasses. The first is raised by the `RelatedNotLoaded` sentinel (dual-inherits `AttributeError`, same pattern as `DeferredFieldAccessFault`, so defensive `hasattr()`/`getattr(..., default)` call sites keep degrading gracefully). The second is raised when assigning an instance of the wrong model to a `ForeignKey`. The third is raised when two `ForeignKey`s targeting the same model would resolve to the same reverse-accessor name.
- **`Model._reverse_relation_map()`**: cached (same lazy-on-first-use pattern as the existing `_get_reverse_fk_refs()`) map from reverse-accessor name — `related_name` or the default `f"{model}_set"` — to the referencing model/column, replacing `related()`'s previous per-call O(models × fields) linear scan with an O(1) lookup, and giving reverse relations a default accessor name for the first time (previously `related()`'s reverse branch only worked when `related_name` was explicitly set).

### Changed
- **`ForeignKey`/`OneToOneField` are now real, generic data descriptors** (`aquilia/models/fields_module.py`): previously neither defined `__get__`/`__set__` at all — every FK "attribute" was a plain instance-`__dict__` entry that happened to shadow the class-level `Field` object via Python's normal (non-descriptor) attribute lookup. A static type checker therefore saw `instance.author` as a bare `ForeignKey` (the class-body assignment's own type), not the real runtime union of a hydrated model instance, the `RelatedNotLoaded` sentinel, or `None` — so it could never catch a missing `select_related()`/`related()` call before it crashed at runtime. `ForeignKey`/`OneToOneField` are now `Generic[TModel]` (bound from their own constructor argument, e.g. `ForeignKey(User)` binds `TModel=User`, the same convention `Manager`/`QuerySet`/`Q` already use) with a real `@overload`-typed `__get__`/`__set__`. `RelatedNotLoaded` is now `Generic[TModel]` too, and a new `Related[TModel]` alias (`aquilia/models/relations.py`) spells out the full union: `TModel | RelatedNotLoaded[TModel] | None`. A plain, unannotated field declaration — `author = ForeignKey(User, related_name="posts")` — now resolves `instance.author` to `User | RelatedNotLoaded[User] | None` for mypy/pyright with no extra syntax; `Related[TModel]` is exported for the cases outside a field declaration where the union needs to be named explicitly (a function parameter/return type, a local variable). This is a pure typing/mediation change with zero runtime behavior change: `__get__`/`__set__` read and write the exact same `instance.__dict__[self.attr_name]` slot every existing call site (`Model.__init__`, `Model.from_row()`, `select_related`/`prefetch_related` hydration, `Model.related()`'s cache-on-resolve) already used — a data descriptor takes priority over instance-`__dict__` shadowing regardless, so every one of those call sites keeps working unchanged, and class-level access (`Model.author`, used throughout SQL generation/introspection/admin for `field.related_model` etc.) still returns the `Field` object itself. `ManyToManyField` is unaffected — it was already excluded from this attribute-storage path (`_attr_names`/`_column_names` in `metaclass.py`) and never stored a `RelatedNotLoaded`-wrapped forward value.
- **`ForeignKey._coerce_to_pk()` now validates related-model type**: assigning an instance of the wrong model (e.g. a `Book` to a `User`-typed FK) previously took `.pk` off of any duck-typed object with `.pk`/`._fields` attributes with no type check, only surfacing as a confusing failure elsewhere (or never, if the two models' PK types happened to collide). It now raises `RelatedTypeMismatchFault` immediately when `related_model` is resolved; falls back to duck-typing when it's still an unresolved lazy string reference (best-effort, not a regression).
- **`Model.related()` forward-FK branch caches its result**: previously re-queried on every call even if the attribute already held a hydrated instance. Now checks for an already-hydrated instance first (zero-query fast path) and, when it does query, overwrites the attribute with the resolved instance so subsequent bare attribute access — not just future `related()` calls — is instant and correctly typed.
- **`Model.__eq__` returns `NotImplemented` (not `False`) for a type mismatch**, letting Python fall back to the other operand's own `__eq__` — needed so dirty-field tracking doesn't flag a `ForeignKey` as changed merely because `related()`/`select_related()` replaced an unhydrated `RelatedNotLoaded` sentinel with the equivalent hydrated instance (same underlying pk).

### Fixed
- **Auth Strategy Isolation**: Separated token extraction and session identity loading based on configured active auth strategies, ensuring they do not run concurrently when not desired.
- **`SessionPrincipal`/`AuthPrincipal` Parameter Resolution & `@exempt` Class Bypass**:
  - Classify `SessionPrincipal` and `AuthPrincipal` parameters (as well as parameters named `"principal"`) as `"di"` source parameters in route compilation rather than falling back to `"query"` parameters, preventing `TypeError` on route handler invocations.
  - Automatically resolve requested `SessionPrincipal`/`AuthPrincipal` parameters in `ControllerEngine._bind_parameters` by extracting the principal from the request session or constructing an `AuthPrincipal` from the active identity.
  - Replace the `elif` parameter injection structures in `@authenticated` and `@require_identity` decorators with individual `if` blocks to support injecting multiple requested authentication and session parameters (such as `user`/`identity`, `session`, and `principal` simultaneously) into route handler signatures.
  - Update `ControllerEngine` to retrieve route handler methods prior to executing the class-level pipeline, allowing the engine to check for `@exempt` (clearance level `AccessLevel.PUBLIC`) decorators and bypass/filter out all security-related guards from both class-level and route-level pipelines.
- **Swallowed manifest import errors during static module discovery** (`aquilia/runtime.py`):
  - Previously, when statically declared modules in `workspace.py` failed to import their `manifest.py` (e.g. due to syntax errors or TypeErrors on startup), `AquiliaRuntime.discover()` caught the exception, logged it, but silently allowed startup to continue. This resulted in missing routes returning `404 Not Found` rather than causing an expected boot crash.
  - Now, discovery re-raises the exception, forcing a clean and loud startup crash when a statically declared core module fails to load.
- **`EFFECT_NOT_ACQUIRED` on all requests when using `@requires()` with a manually-configured `EffectMiddleware`**: Three interacting bugs caused every `ctx.get_effect("DBTx")` / `ctx.get_effect("Cache")` call to fail even when the middleware was present in the workspace `MiddlewareChain`:
  1. Bootstrap ordering — empty registry at construction time: `_instantiate_middleware()` (called during `Server.__init__()`) resolved the `EffectRegistry` from DI immediately — before the ASGI lifespan `on_startup()` event had a chance to register `DBTx`, `Cache`, `Queue`, and `Storage` providers. The result was an `EffectMiddleware` instance permanently bound to an empty registry. Fixed by introducing a `_DeferredEffectRegistry` proxy that lazily resolves `server._effect_registry` on every request.
  2. `EffectSubsystem._register_middleware()` silently skipped when providers were absent: The condition `if self._registry and self._registry.providers:` prevented `EffectMiddleware` from being registered by the subsystem when no providers were configured in the `effects.providers` config section. The guard has been relaxed to `if self._registry:` so the middleware is always registered when the subsystem is active.
  3. Opaque error message with no actionable information: Replaced with the new `EffectNotAcquiredFault`.
- **Type inference for `Model.related(name)`**: Added `@overload` signatures to `related()`, enabling IDE autocomplete on related field model attributes without manual casting.
- **Instance manager access error handling**: Replaced bare `AttributeError` when attempting to access class-level managers on model instances with a structured `ManagerInstanceAccessFault`.
- **ORM field `sql_type()` error handling**: Replaced `NotImplementedError` raised in custom field classes missing `sql_type()` implementations with a structured `SchemaFault`.
- **Migration DSL error handling**: Replaced `NotImplementedError` raised when attempting to mechanically reverse irreversible migration operations with a structured `MigrationFault`.
- **Dependency Injection error handling**: Migrated `DIError` and all its subclasses in `aquilia/di/errors.py` to subclass `DIFault` and participate fully in the Aquilia structured fault handling system, capturing rich diagnostics in metadata.
- **DI CLI missing settings error handling**: Replaced `FileNotFoundError` raised when a settings file is missing during CLI loader setup with `ConfigMissingFault`.
- **Configuration validation error handling**: Changed `ConfigError` in the configuration loader to inherit from `ConfigFault`.
- **Blueprint sync/async validation mismatch error handling**: Replaced `RuntimeError` raises for async ward validation sync mismatch with a structured `BlueprintAsyncMismatchFault`.
- **Blueprint migration error handling**: Replaced raw `ValueError` raised during missing blueprint migration path in `Sigil` validation with a proper validation error response dictionary, preventing unhandled 500 errors on invalid client inputs.
- **ASGI middleware chain error handling**: Replaced `RuntimeError` raised when the ASGI middleware chain is not initialized with a structured `SystemFault`.
- **Pattern compiler error handling**: Subclassed `PatternSyntaxError`, `PatternSemanticError`, and `RouteAmbiguityError` from `RoutingFault` in `patterns/diagnostics/errors.py`.
- **`atomic()` never actually started a database transaction**: `Atomic` now routes through connection-bound `begin()`/`commit()`/`rollback()` (plus savepoint wrappers) rather than executing raw SQL text statements.
- **Isolation level silently no-op'd for Postgres/MySQL**: Isolation is now passed directly into each adapter's `begin(isolation=...)`.
- **Authentication & Session Forensic Audit fixes**:
  - `MemoryCredentialStore` updated to satisfy `CredentialStore` protocol.
  - Removed `@dataclass` from `Credential` protocol.
  - Added `MemoryOAuthClientStore.list_all()`.
  - Rejected suspended/expired API keys in `authenticate_api_key`.
  - Resolved nonexistent method call in `RequireSessionAuthGuard`.
  - Fixed argument order and await in `RequirePolicyGuard`.
  - Passed `resource` parameter to RBAC check in `RequirePermissionGuard`.
  - Propagated resolved identity into context and state in `set_identity()`.
  - Replaced hardcoded template `can()` helper with real RBAC check.
  - Omitted symmetric HMAC key from JWKS-style `KeyDescriptor.to_dict()` safe dump.
  - Fixed refresh token rotation claim loss.
  - Enforced client secret validation in OAuth2 confidential client flow.
  - Enforced PKCE check in `grant_authorization_code()`.
  - Fixed SHA algorithm mismatch in `TOTPProvider.algorithm`.
  - Resolved session rotation commit concurrency safety checks.
  - Marked new anonymous sessions dirty on first response.
  - Handled corrupted session files gracefully.
  - Use `get_attribute` fallback in `AdminAuthGuard`.
  - Secured `MemoryStore.exists()` and `FileStore.delete()` under `self._lock`.
- Reverse-relation resolution (`Model.related()`) previously required an explicit `related_name` on the `ForeignKey` and re-scanned every registered model's every field on every call; it now has a default accessor name and an O(1) cached lookup, and fails fast with `RelatedNameConflictFault` if two FKs would collide on the same name.
- **Path Traversal in `LocalStorage.listdir()`**: `listdir()` now normalizes and confines its `path` argument the same way every sibling method already does, matching the `S3Storage`/`SFTPStorage` backends and the framework's stated file-path-validation invariant.

### Testing
- New `tests/test_orm_transactions_atomic.py` for transaction tests.
- New `TestForeignKeyDescriptor` in `tests/test_related_not_loaded_and_reverse_manager.py`.
- Updated `tests/test_auth_system.py` clearance fixtures.

## [1.3.01b] — 2026-07-11

### Added
- **Configurable Authentication Strategies**: Enabled configuring active auth strategies ("token", "session") on `AquilAuthMiddleware`, `AuthConfig`, and `AuthIntegration` to allow users to enforce only session-based authentication, only token-based authentication, or both at the same time.

### Fixed
- **Auth Strategy Isolation**: Separated token extraction and session identity loading based on configured active auth strategies, ensuring they do not run concurrently when not desired.

## [1.3.0b1] — 2026-07-07 — "Ironclad Anchor" (beta)

### Added

- **Native PyConfig & DotEnv Resolution Support for Integrations**:
  - Native support for `Env` and `Secret` wrappers directly in integrations and provider wrappers.
  - Automatic resolution of `Env`, `Secret`, and PyConfig configuration objects/fields at the correct lifecycle stage.
  - Automatic type conversion and casting of environment variables (e.g. `Env("PORT", cast=int)` resolves to an integer).
  - Secure automatic secret resolution through `Secret` wrappers without requiring manual `reveal()` or primitive extraction.
  - Complete backwards compatibility and zero breaking changes for existing string-based and int-based configurations.
- **`Field` Positional & Ellipsis Support** (`aquilia/contracts/annotations.py`):
  - Support passing a single positional default argument to `Field()`.
  - Passing `...` (Ellipsis) positionally now automatically translates to `required=True` with `UNSET` default:
    ```python
    message: str = Field(...)  # translates to required=True, default=UNSET
    ```
  - Positional defaults (such as `Field("default_val")`) are natively resolved.
  - Adding contradictory arguments like `Field(..., default="val")` raises a structured `ConfigInvalidFault` rather than a generic Python `TypeError`.
- **`EffectNotAcquiredFault`** (`aquilia.faults.domains`): New structured
  fault subclassing `EffectFault` that replaces the bare
  `EffectFault(code="EFFECT_NOT_ACQUIRED")` raised by `ctx.get_effect()`,
  `FlowContext.get_effect()`, and `EffectRegistry.get_provider()`. The new
  fault carries rich diagnostics in `metadata`:
  - `effect`: the effect name that was requested
  - `registered`: all effects currently in the registry
  - `middleware_active`: whether `EffectMiddleware` ran for this request
  - `hint`: a concise, actionable remediation message tailored to the
    probable root cause (missing `@requires`, unregistered provider, or
    inactive middleware)

  The fault is `public=True` so the `hint` is visible in JSON error
  responses (including in debug mode), making it trivial to self-diagnose
  effect configuration issues.

- **`_DeferredEffectRegistry`** (`aquilia.middleware_ext.effect_middleware`):
  Lazy proxy that delegates `has_effect`, `acquire`, `release`, and
  `providers` to a live `EffectRegistry` resolved at request time via a
  zero-argument callable. Eliminates the need for `EffectMiddleware` to have
  a fully-populated registry at construction time, correctly handling the
  ASGI startup ordering where providers are registered in `on_startup()`
  long after the middleware stack is built in `__init__()`.

- **`atomic()` as a decorator**: `@atomic()` on an `async def` now wraps the whole call in its own
  transaction (Tortoise-ORM-style), constructing a fresh `Atomic` per call so concurrent calls to
  the decorated function don't share mutable transaction state.
- **`atomic(readonly=True)`**: hints that a block only reads. On SQLite this routes to a reader
  connection instead of contending for the pool's single writer (Aquilia's own N-readers+1-writer
  design already made this possible; `atomic()` just wasn't using it). Other backends pass
  `readonly` straight to their native read-only transaction support (asyncpg `transaction(readonly=
  True)`, `SET TRANSACTION READ ONLY` for MySQL/Oracle).
- **`atomic(timeout=...)`** (seconds): Prisma-style interactive-transaction timeout. A watchdog
  cancels the enclosing task if the block hasn't finished in time; the transaction is rolled back
  and a `QueryFault` is raised instead of leaving a transaction open indefinitely.

### Changed

- **`ForeignKey`/`OneToOneField` are now real, generic data descriptors** (`aquilia/models/
  fields_module.py`): previously neither defined `__get__`/`__set__` at all — every FK "attribute"
  was a plain instance-`__dict__` entry that happened to shadow the class-level `Field` object via
  Python's normal (non-descriptor) attribute lookup. A static type checker therefore saw
  `instance.author` as a bare `ForeignKey` (the class-body assignment's own type), not the real
  runtime union of a hydrated model instance, the `RelatedNotLoaded` sentinel, or `None` — so it
  could never catch a missing `select_related()`/`related()` call before it crashed at runtime.
  `ForeignKey`/`OneToOneField` are now `Generic[TModel]` (bound from their own constructor argument,
  e.g. `ForeignKey(User)` binds `TModel=User`, the same convention `Manager`/`QuerySet`/`Q` already
  use) with a real `@overload`-typed `__get__`/`__set__`. `RelatedNotLoaded` is now `Generic[TModel]`
  too, and a new `Related[TModel]` alias (`aquilia/models/relations.py`) spells out the full union:
  `TModel | RelatedNotLoaded[TModel] | None`. A plain, **unannotated** field declaration —
  `author = ForeignKey(User, related_name="posts")` — now resolves `instance.author` to
  `User | RelatedNotLoaded[User] | None` for mypy/pyright with no extra syntax; `Related[TModel]` is
  exported for the cases outside a field declaration where the union needs to be named explicitly
  (a function parameter/return type, a local variable). This is a pure typing/mediation change with
  zero runtime behavior change: `__get__`/`__set__` read and write the exact same
  `instance.__dict__[self.attr_name]` slot every existing call site (`Model.__init__`,
  `Model.from_row()`, `select_related`/`prefetch_related` hydration, `Model.related()`'s
  cache-on-resolve) already used — a data descriptor takes priority over instance-`__dict__`
  shadowing regardless, so every one of those call sites keeps working unchanged, and class-level
  access (`Model.author`, used throughout SQL generation/introspection/admin for
  `field.related_model` etc.) still returns the `Field` object itself. `ManyToManyField` is
  unaffected — it was already excluded from this attribute-storage path (`_attr_names`/
  `_column_names` in `metaclass.py`) and never stored a `RelatedNotLoaded`-wrapped forward value.

### Fixed

- **`SessionPrincipal`/`AuthPrincipal` Parameter Resolution & `@exempt` Class Bypass**:
  - Classify `SessionPrincipal` and `AuthPrincipal` parameters (as well as parameters named `"principal"`) as `"di"` source parameters in route compilation rather than falling back to `"query"` parameters, preventing `TypeError` on route handler invocations.
  - Automatically resolve requested `SessionPrincipal`/`AuthPrincipal` parameters in `ControllerEngine._bind_parameters` by extracting the principal from the request session or constructing an `AuthPrincipal` from the active identity.
  - Replace the `elif` parameter injection structures in `@authenticated` and `@require_identity` decorators with individual `if` blocks to support injecting multiple requested authentication and session parameters (such as `user`/`identity`, `session`, and `principal` simultaneously) into route handler signatures.
  - Update `ControllerEngine` to retrieve route handler methods prior to executing the class-level pipeline, allowing the engine to check for `@exempt` (clearance level `AccessLevel.PUBLIC`) decorators and bypass/filter out all security-related guards from both class-level and route-level pipelines.
- **Swallowed manifest import errors during static module discovery** (`aquilia/runtime.py`):
  - Previously, when statically declared modules in `workspace.py` failed to import their `manifest.py` (e.g. due to syntax errors or TypeErrors on startup), `AquiliaRuntime.discover()` caught the exception, logged it, but silently allowed startup to continue. This resulted in missing routes returning `404 Not Found` rather than causing an expected boot crash.
  - Now, discovery re-raises the exception, forcing a clean and loud startup crash when a statically declared core module fails to load.
- **`EFFECT_NOT_ACQUIRED` on all requests when using `@requires()` with a
  manually-configured `EffectMiddleware`**: Three interacting bugs caused
  every `ctx.get_effect("DBTx")` / `ctx.get_effect("Cache")` call to fail
  even when the middleware was present in the workspace `MiddlewareChain`:

  1. **Bootstrap ordering — empty registry at construction time**:
     `_instantiate_middleware()` (called during `Server.__init__()`) resolved
     the `EffectRegistry` from DI immediately — before the ASGI lifespan
     `on_startup()` event had a chance to register `DBTx`, `Cache`, `Queue`,
     and `Storage` providers (Step 3.5).  The result was an `EffectMiddleware`
     instance permanently bound to an empty registry, so
     `registry.has_effect(name)` always returned `False` and effects were
     silently skipped. Fixed by introducing a `_DeferredEffectRegistry` proxy
     (see *Added* below) that lazily resolves `server._effect_registry` on
     every request instead of at construction time.

  2. **`EffectSubsystem._register_middleware()` silently skipped when
     providers were absent**: The condition `if self._registry and
     self._registry.providers:` prevented `EffectMiddleware` from being
     registered by the subsystem when no providers were configured in the
     `effects.providers` config section — even though core providers
     (DBTx, Cache, etc.) are auto-registered later in `on_startup()`.
     The guard has been relaxed to `if self._registry:` so the middleware
     is always registered when the subsystem is active.

  3. **Opaque error message with no actionable information**: The previous
     `EffectFault(code="EFFECT_NOT_ACQUIRED", message="... Use @requires()")`
     was always raised regardless of the actual root cause (missing
     `@requires`, missing provider registration, or missing middleware),
     making it impossible to diagnose the real issue from the error response
     alone. Replaced with the new `EffectNotAcquiredFault` (see *Added*).

- **Type inference for `Model.related(name)`**: Added `@overload` signatures to `related()`, enabling IDE autocomplete on related field model attributes (e.g. `await token.related("user", UserModel)`) without manual casting.
- **Instance manager access error handling**: Replaced bare `AttributeError` when attempting to access class-level managers on model instances (e.g. `user.objects.all()`) with a structured `ManagerInstanceAccessFault` (subclassing both `ModelFault` and `AttributeError` for backward compatibility).
- **ORM field `sql_type()` error handling**: Replaced `NotImplementedError` raised in custom field classes missing `sql_type()` implementations with a structured `SchemaFault`.
- **Migration DSL error handling**: Replaced `NotImplementedError` raised when attempting to mechanically reverse irreversible migration operations (like `DropModel` and `RemoveField` rollbacks) with a structured `MigrationFault`.
- **Dependency Injection error handling**: Migrated `DIError` and all its subclasses in `aquilia/di/errors.py` to subclass `DIFault` and participate fully in the Aquilia structured fault handling system, capturing rich diagnostics in metadata.
- **DI CLI missing settings error handling**: Replaced `FileNotFoundError` raised when a settings file is missing during CLI loader setup with `ConfigMissingFault`.
- **Configuration validation error handling**: Changed `ConfigError` in the configuration loader to inherit from `ConfigFault`.
- **Contract sync/async validation mismatch error handling**: Replaced `RuntimeError` raises for async ward validation sync mismatch with a structured `ContractAsyncMismatchFault` (inheriting from `ContractFault` and `RuntimeError`).
- **Contract migration error handling**: Replaced raw `ValueError` raised during missing contract migration path in `Sigil` validation with a proper validation error response dictionary, preventing unhandled 500 errors on invalid client inputs.
- **ASGI middleware chain error handling**: Replaced `RuntimeError` raised when the ASGI middleware chain is not initialized with a structured `SystemFault`.
- **Pattern compiler error handling**: Subclassed `PatternSyntaxError`, `PatternSemanticError`, and `RouteAmbiguityError` from `RoutingFault` in `patterns/diagnostics/errors.py`.
- **`atomic()` never actually started a database transaction**: `Atomic.__aenter__`/`__aexit__`
  (`aquilia/models/transactions.py`) drove the transaction by sending literal `"BEGIN"` /
  `"SAVEPOINT ..."` / `"RELEASE SAVEPOINT ..."` / `"COMMIT"` / `"ROLLBACK"` through
  `AquiliaDatabase.execute()` — the exact same auto-commit code path as an ordinary query. Every
  backend's adapter (`aquilia/db/backends/{sqlite,postgres,mysql,oracle}.py`) only disables
  per-statement auto-commit once its own `begin()` pins a dedicated connection and flips an
  internal `_in_transaction` flag; `Atomic` never called that `begin()`/`commit()`/`rollback()`
  path (`AquiliaDatabase` didn't even expose it publicly — only the private `transaction()`
  async-contextmanager used it internally, for `Model.delete_instance()` cascades and the
  migration runner). So the literal `"BEGIN"` text auto-committed on its own the instant it ran,
  collapsing the transaction before the block's own statements executed; by the time `atomic()`
  issued its own `"COMMIT"` at block exit, the database had nothing open to commit, surfacing as
  `QueryFault(code="QUERY_FAILED", operation="execute", metadata.sql="COMMIT",
  metadata.reason="... cannot commit - no transaction is active")` on SQLite (equivalent errors on
  other backends). Every statement issued inside `async with atomic(): ...` — including any
  `Model.save()` calls, which were never at fault — ran autocommitted and independent of one
  another instead of atomically. `AquiliaDatabase` now exposes public `begin()`/`commit()`/
  `rollback()` (mirroring its existing `savepoint()`/`release_savepoint()`/
  `rollback_to_savepoint()` wrappers), and `Atomic` routes through them (plus the savepoint
  wrappers for nesting) instead of raw SQL text — the same adapter machinery already proven
  correct by the cascade-delete and migration-runner call sites.
- **Isolation level silently no-op'd for Postgres/MySQL**: `atomic(isolation="SERIALIZABLE")`
  issued a separate `SET TRANSACTION ISOLATION LEVEL ...` statement through the auto-commit
  `execute()` path *before* `"BEGIN"` — since `execute()` auto-acquires and releases a pooled
  connection per call, the isolation-level statement could land on a different physical connection
  than the one the following `BEGIN` pinned moments later, silently discarding it. Isolation is now
  passed directly into each adapter's `begin(isolation=...)`, set on the exact connection/session the
  transaction actually runs on (asyncpg's native `transaction(isolation=...)` for Postgres, `SET
  TRANSACTION ISOLATION LEVEL` on the dedicated session before `START TRANSACTION` for MySQL, `SET
  TRANSACTION ISOLATION LEVEL` before any DML for Oracle; SQLite has no session isolation levels and
  ignores the parameter).

### Testing

- New `tests/test_orm_transactions_atomic.py`: reproduces the original report exactly
  (`select_related().filter().first()` before `atomic()`, two `.save()` calls inside it), plus
  commit/rollback, nested savepoints (commit and partial rollback), `durable=True` nesting
  rejection, `on_commit`/`on_rollback` hook scoping, two concurrent `asyncio.Task`s each committing
  independently, the decorator form, `readonly=True` non-contention with a concurrent writer,
  `timeout=` expiry, and `asyncio.CancelledError` mid-transaction rollback.

- New `TestForeignKeyDescriptor` in `tests/test_related_not_loaded_and_reverse_manager.py`: class-level
  access still returns the `Field` object (not `None`/`AttributeError`), instance-level get/set
  round-trips a real model instance, and hydrated vs. unhydrated instance access resolve to the
  hydrated instance vs. the `RelatedNotLoaded` sentinel respectively — confirms the descriptor swap
  is behaviorally transparent. Full existing suite (6600+ tests, `tests/
  test_related_not_loaded_and_reverse_manager.py` in particular, which exercises `RnlBook.author`
  extensively) passes unchanged.

### Fixed — Authentication & Session Forensic Audit

A full forensic audit of `aquilia/auth/` and `aquilia/sessions/` uncovered and fixed
protocol/implementation drift, broken guard call chains, a credential-leaking
serialization path, and several session lifecycle correctness bugs. No public API
signatures were removed; new keyword-only parameters were added where needed.

- **`CredentialStore` protocol/implementation mismatch** (`aquilia/auth/stores.py`):
  `MemoryCredentialStore` implemented zero of the protocol's declared write methods
  under their real names (`save_password` instead of `create_password`/
  `update_password`, `get_api_key_by_prefix` instead of `get_api_key_by_hash`, no
  `revoke_api_key`/`create_mfa`/`update_mfa` at all). Any custom `CredentialStore`
  written strictly against the published protocol would crash `AuthManager` with
  `AttributeError` the moment it authenticated. Added `create_password`,
  `update_password`, `create_api_key`, `get_api_key_by_hash` (O(1), indexed by hash —
  replaces the O(n) prefix scan), `revoke_api_key` (soft, sets `CredentialStatus.REVOKED`),
  `create_mfa`, `update_mfa` so the store now genuinely satisfies `CredentialStore`.
  `aquilia/auth/manager.py` updated to call the protocol-correct methods.
- **`Credential` protocol wrongly decorated `@dataclass`** (`aquilia/auth/core.py`):
  made it directly instantiable, defeating structural-typing enforcement. Removed the
  decorator; `Credential` is dead/orphaned (no concrete credential type inherits from
  it) and is now a proper `Protocol`.
- **`MemoryOAuthClientStore` missing `list_all`** (`aquilia/auth/stores.py`): the
  `OAuthClientStore` protocol declares `list_all()`; the implementation only had
  `list(owner_id=..., limit=..., offset=...)`. Added `list_all()` as a thin wrapper.
- **Suspended/expired API keys were not rejected** (`aquilia/auth/manager.py`,
  `authenticate_api_key`): only `status == "revoked"` was checked; `CredentialStatus.SUSPENDED`
  and `.EXPIRED` were silently accepted. Now rejects all three non-active statuses.
- **`RequireSessionAuthGuard` called a nonexistent `identity_store.get_identity()`**
  (`aquilia/auth/integration/flow_guards.py`): the `IdentityStore` protocol (and the
  sibling `AquilAuthMiddleware`) both use `.get(identity_id)`. Fixed to match — this
  guard raised `AttributeError` on every session-authenticated request.
- **`RequirePolicyGuard` called `authz_engine.abac.evaluate()` with swapped
  arguments and missing `await`** (`aquilia/auth/integration/flow_guards.py`):
  `ABACEngine.evaluate(context, policy_id)` is synchronous and takes the context
  first; the guard called `evaluate(self.policy_name, authz_ctx)` without awaiting,
  so `decision` was an unawaited coroutine that could never equal `Decision.ALLOW` —
  every policy-guarded route was unconditionally denied. Fixed argument order and
  removed the erroneous `await`.
- **`RequirePermissionGuard`'s `resource` parameter was accepted but never passed**
  to the authorization check (`aquilia/auth/integration/flow_guards.py`): resource-scoped
  permission checks silently degraded to resource-agnostic ones. Now routes through
  `authz_engine.rbac.check(authz_ctx, permission)`, which carries `resource` in the
  `AuthzContext`.
  `identity.tenant_id`/`.scopes`/`.roles` directly, which crash or silently return
  nothing against the real `Identity` model (roles/scopes live in `attributes`, only
  reachable via `get_attribute()`). Both guards, plus `ClearanceEngine` and
  `templates/auth_integration.py`'s `can()` helper, now use a shared
  attribute-first-then-`get_attribute`-fallback accessor.
- **`set_identity()` never propagated the resolved identity into the dict/state
  context** (`aquilia/auth/integration/flow_guards.py`): only `request.state["identity"]`
  was set. `ControllerGuardAdapter`'s sync-back step reads `result_ctx["identity"]`,
  which — because `set_identity` skipped it — stayed at its stale pre-guard value
  (usually `None`). Any guard used via `.for_controller()` left `ctx.identity` unset
  even after successful authentication. Fixed to also set `context["identity"]` /
  `context.state["identity"]`.
- **Template `can()` permission helper was a hardcoded `return True` placeholder**
  (`aquilia/templates/auth_integration.py`): granted every permission for every
  resource to any authenticated user whenever an `authz_engine` was wired in,
  regardless of the requested permission. Now builds a real `AuthzContext` and
  checks it against `authz_engine.rbac`.
- **Template `is_owner()` helper read a nonexistent `identity.identity_id`**
  (`aquilia/templates/auth_integration.py`): the real `Identity` field is `.id`;
  calling `is_owner(resource)` raised `AttributeError` on every real `Identity`.
  Fixed to read `.id`.
- **`ClearanceEngine.resolve_identity_level`/`resolve_entitlements` and
  `clearance.is_owner_or_admin`** (`aquilia/auth/clearance.py`) read
  `identity.roles`/`.scopes`/`.permissions` as direct attributes, which are always
  empty for the real `Identity` model — role-based access-level elevation and
  entitlement resolution silently never worked. Fixed with the same
  attribute-first-then-`get_attribute` fallback used in the guards above.
- **`Clearance.merge()` silently downgraded class-level access requirements**
  (`aquilia/auth/clearance.py`): `grant()`'s `level` parameter defaulted to
  `AccessLevel.AUTHENTICATED`, indistinguishable from "not specified" — any
  method-level `@grant(entitlements=[...])` that didn't restate `level` silently
  reset the merged clearance to `AUTHENTICATED`, undoing a stricter class-level
  `Clearance(level=AccessLevel.INTERNAL, ...)` baseline. `grant()`'s `level` now
  defaults to `None` (genuinely unspecified); `Clearance.merge()` inherits the base
  level whenever the override didn't specify one. Added `Clearance.effective_level`
  for callers that need the resolved (non-`None`) level.
- **`TokenConfig.algorithm` was dead configuration defaulting to `RS256`**
  (`aquilia/auth/tokens.py`), contradicting the module's own documented "HS256 by
  default, zero extra dependencies" behavior. The field was never read anywhere —
  actual signing algorithm is a property of the active `KeyDescriptor` inside the
  `KeyRing`. Removed the misleading field; documented where the algorithm is
  actually configured.
- **`KeyRingProvider` hard-coded `RS256`** (`aquilia/auth/integration/di_providers.py`):
  crashed DI-based zero-config app startup with `ConfigInvalidFault` whenever the
  `cryptography` package wasn't installed, contradicting the documented zero-dependency
  default used by `server.py`'s own bootstrap path. Now defaults to `HS256`.
- **`AuthManagerProvider` declared and stored an unused `token_store` dependency**
  (`aquilia/auth/integration/di_providers.py`) that was never forwarded to
  `AuthManager(...)`. Removed the dead parameter.
- **`KeyDescriptor.to_dict()` leaked the live HMAC signing secret even in "safe"
  mode** (`aquilia/auth/tokens.py`): for symmetric algorithms (HS256/HS384/HS512),
  `public_key_pem` IS the shared secret (there's no separate public key for HMAC).
  `include_private_key=False` only withheld the `private_key` field, so a
  "public JWKS-style" dump of an HS256 `KeyRing` (`to_dict(include_private_keys=False)`)
  still published the field an attacker needs to forge arbitrary valid tokens. Now
  `public_key` is omitted from the safe serialization for symmetric algorithms too.
- **Refresh token rotation dropped `roles`/`tenant_id` claims**
  (`aquilia/auth/tokens.py`, `aquilia/auth/stores.py`): `TokenStore.save_refresh_token`
  never persisted `roles`/`tenant_id`, so `refresh_access_token()` silently reissued
  an access token stripped of role claims on every refresh — breaking role-based
  access checks after the first token refresh. `TokenStore` protocol,
  `MemoryTokenStore`, `RedisTokenStore`, and `TokenManager.issue_refresh_token`/
  `refresh_access_token` now thread `roles`/`tenant_id` through the full round trip.
- **OAuth2 confidential-client impersonation** (`aquilia/auth/oauth.py`,
  `OAuth2Manager.validate_client`): a client secret was only verified if the caller
  happened to supply one — omitting it (or passing an empty string) bypassed secret
  verification entirely for confidential clients. `validate_client()` now always
  requires and verifies the secret for any client with a stored
  `client_secret_hash`; added a `require_secret` flag (set at the two
  token-issuing endpoints, `exchange_authorization_code` and
  `client_credentials_grant`) so browser-redirect endpoints that never carry a
  secret over the wire (`authorize`, `device_authorization`) are unaffected.
- **`grant_authorization_code()` didn't re-check PKCE** (`aquilia/auth/oauth.py`):
  `client.require_pkce` was only enforced in `authorize()` (the consent-UI step);
  a direct caller of `grant_authorization_code()` could skip PKCE entirely. Now
  re-validates the client and `require_pkce` inside `grant_authorization_code()` too.
- **`TOTPProvider.algorithm` constructor parameter was dead** (`aquilia/auth/mfa.py`):
  `generate_code()` always hard-coded SHA1 regardless of the configured algorithm,
  while `generate_provisioning_uri()` advertised whatever algorithm was configured —
  a mismatch that breaks verification for any authenticator app that honors the
  provisioning URI's `algorithm` parameter. `generate_code()` now dispatches on
  `self.algorithm` (SHA1/SHA256/SHA512, per RFC 6238).
- **Session rotation could leave a request with no valid session at all**
  (`aquilia/sessions/engine.py`, `SessionEngine.commit`): rotation unconditionally
  deleted the *old* session from the store before the concurrency check that could
  reject the commit ran — if `check_concurrency` then raised, the new (rotated)
  session was never saved and the *old* one was already gone. Concurrency is now
  checked before rotation, so a rejected commit leaves the pre-existing session
  untouched.
- **New anonymous sessions were never persisted on their first response**
  (`aquilia/sessions/engine.py`, `SessionEngine._create_new`): `flags` is a plain
  `set`, not the dirty-tracked `data` dict — mutating it (`RENEWABLE`/`EPHEMERAL`)
  never marked the session dirty, so `commit()` saw `is_dirty=False` and skipped
  `store.save()`, even though `transport.inject()` still issued a session cookie
  unconditionally for the never-persisted session. `_create_new` now calls
  `session.mark_dirty()` explicitly.
- **Corrupted on-disk session files crashed the request instead of degrading
  gracefully** (`aquilia/sessions/engine.py`, `SessionEngine._load_existing`):
  `FileStore.load()` can raise `SessionStoreCorruptedFault` for a malformed JSON
  session file; `resolve()` didn't catch it, unlike every other invalid-session case
  (expired, idle-timeout, fingerprint-mismatch), which all fall back to a fresh
  session. Now caught and handled the same way.
- **`AdminAuthGuard` read `identity.roles` directly, bypassing `get_attribute`**
  (`aquilia/admin/subsystems.py`): same root cause as the guard/clearance fixes
  above — real `Identity` has no `.roles` attribute, so the admin panel's own
  auth guard fell through to an empty role list and rejected every real admin.
  `aquilia/admin/permissions.py` already did this correctly; `AdminAuthGuard`
  now uses the same `get_attribute`-first fallback chain.
- **`aquilia/auth/policy/__init__.py` module docstring example used
  `identity.roles` directly** instead of `identity.has_role(...)` — corrected
  (documentation-only; the executable `Policy`/`PolicyRegistry` code was
  already correct).
- **Inconsistent locking in `MemoryStore.exists()` and `FileStore.delete()`**
  (`aquilia/sessions/store.py`): every other method on both stores serializes on
  `self._lock`; these two didn't, breaking the stores' own lock discipline (a latent
  race for `MemoryStore.exists()`, a real TOCTOU window for `FileStore.delete()`
  racing concurrent `save()`/`cleanup_expired()`/`list_by_principal()` calls on the
  same file). Both now acquire the lock.

### Testing

- Updated `tests/test_auth_system.py` clearance fixtures (`TestClearanceEngine._make_identity`,
  `TestBuiltInConditions`) to back `get_attribute()` with a real `attributes` dict instead of
  setting bare `.roles`/`.scopes` `MagicMock` attributes — the fixtures were masking the exact
  `identity.roles`/`.scopes` direct-attribute-access bug fixed above.
- Full existing suite (6680 tests) passes unchanged; `ruff check` clean on all modified files.

## [1.3.0b0] — 2026-07-06 — "Ironclad Anchor" (beta)

### Added

- **`RelatedManager` / `Model.related_manager()`**: reverse relations (rows in another table whose `ForeignKey` points back at an instance) can now be accessed lazily and chained like any other queryset: `await user.related_manager("verifications").filter(expires_at__gt=now).order("-created_at").first()`. Previously `Model.related()` was the only reverse-relation entry point and always eagerly awaited a fully materialized list. `related()` itself is unchanged in contract — it now delegates to `related_manager(name).all()` (or `.first()` for a `OneToOneField`'s reverse side, matching its actual 1:1 cardinality instead of returning a list).
- **`RelatedNotLoaded` sentinel** (`aquilia.models.relations`): reading a `ForeignKey`/`OneToOneField` attribute that hasn't been hydrated via `select_related()`, `prefetch_related()`, or `await instance.related(name)` now returns this sentinel instead of the raw stored id. Cheap operations work directly on it without a query (`.pk`/`.id`, `bool(...)`, `== other_instance`/`== raw_pk`); any other attribute access raises `RelatedNotLoadedFault` with actionable guidance. Aquilia's DB layer is 100% async and `__get__` can't be `async def`, so — unlike Django's `ForwardManyToOneDescriptor` — there is no transparent hidden query; hydration stays explicit and awaited, this only replaces the previous silent-wrong-type footgun on the read side.
- **`RelatedNotLoadedFault`, `RelatedTypeMismatchFault`, `RelatedNameConflictFault`** (`aquilia/faults/domains.py`): new `ModelFault` subclasses. The first is raised by the `RelatedNotLoaded` sentinel (dual-inherits `AttributeError`, same pattern as `DeferredFieldAccessFault`, so defensive `hasattr()`/`getattr(..., default)` call sites keep degrading gracefully). The second is raised when assigning an instance of the wrong model to a `ForeignKey`. The third is raised when two `ForeignKey`s targeting the same model would resolve to the same reverse-accessor name.
- **`Model._reverse_relation_map()`**: cached (same lazy-on-first-use pattern as the existing `_get_reverse_fk_refs()`) map from reverse-accessor name — `related_name` or the default `f"{model}_set"` — to the referencing model/column, replacing `related()`'s previous per-call O(models × fields) linear scan with an O(1) lookup, and giving reverse relations a default accessor name for the first time (previously `related()`'s reverse branch only worked when `related_name` was explicitly set).

### Changed

- **`ForeignKey._coerce_to_pk()` now validates related-model type**: assigning an instance of the wrong model (e.g. a `Book` to a `User`-typed FK) previously took `.pk` off of *any* duck-typed object with `.pk`/`._fields` attributes with no type check, only surfacing as a confusing failure elsewhere (or never, if the two models' PK types happened to collide). It now raises `RelatedTypeMismatchFault` immediately when `related_model` is resolved; falls back to duck-typing when it's still an unresolved lazy string reference (best-effort, not a regression).
- **`Model.related()` forward-FK branch caches its result**: previously re-queried on every call even if the attribute already held a hydrated instance. Now checks for an already-hydrated instance first (zero-query fast path) and, when it does query, overwrites the attribute with the resolved instance so subsequent *bare* attribute access — not just future `related()` calls — is instant and correctly typed.
- **`Model.__eq__` returns `NotImplemented` (not `False`) for a type mismatch**, letting Python fall back to the other operand's own `__eq__` — needed so dirty-field tracking doesn't flag a `ForeignKey` as changed merely because `related()`/`select_related()` replaced an unhydrated `RelatedNotLoaded` sentinel with the equivalent hydrated instance (same underlying pk).

### Fixed

- Reverse-relation resolution (`Model.related()`) previously required an explicit `related_name` on the `ForeignKey` and re-scanned every registered model's every field on every call; it now has a default accessor name and an O(1) cached lookup, and fails fast with `RelatedNameConflictFault` if two FKs would collide on the same name.
- **Path Traversal in `LocalStorage.listdir()`**: every other `LocalStorage` method (`save`, `open`, `delete`, `stat`, `url`, `copy`) routes its path argument through `_normalize_path()` (rejects `..` segments and null bytes) and `_full_path()` (resolves and confines the result to `config.root`) — `listdir()` (`aquilia/storage/backends/local.py`) did neither, building its target with a raw `self._root / path`, so `await storage.listdir("../secret_sibling")` listed a directory entirely outside the configured storage root. `listdir()` now normalizes and confines its `path` argument the same way every sibling method already does, matching the `S3Storage`/`SFTPStorage` backends (which already normalize their `listdir` path) and the framework's stated file-path-validation invariant.

### Known Issues

- **Ambiguous column name with `select_related()` + `filter()`**: filtering on a column name shared by both the base table and a joined table (e.g. `id`) raises `ambiguous column name` because `QuerySet._build_select()` (`aquilia/models/query.py`) doesn't qualify the column with its owning table in the generated `WHERE` clause. Pre-existing, not addressed here — workaround is to filter on unambiguous column names until `_build_select()` gets its own fix pass.

## [1.2.5] — 2026-07-06 — "Kraken's Wake"

### Fixed

- **Admin Bulk Action Dispatch Crash**: `ModelAdmin._setup_actions()` (`aquilia/admin/options.py`) registered every built-in action (`delete_selected`, `duplicate_selected`, `export_csv`, `export_json`, `activate_selected`, `deactivate_selected`, `mark_featured`, `unmark_featured`) and string-named custom actions from the `actions = [...]` list as **bound** methods (`func=self._action_x` / `getattr(self, act)`). `AdminSite.execute_action()` (`aquilia/admin/site.py`) calls `action_desc.func(admin, request, queryset)` per `AdminActionDescriptor`'s documented unbound-function contract — the same contract the `@action`-decorated-method discovery path already honors correctly (it registers via `getattr(self.__class__, attr_name)`). Registering bound methods meant `self` was captured twice (once implicitly at registration, once explicitly at the call site), so every built-in action crashed with `TypeError: ModelAdmin._action_x() takes 3 positional arguments but 4 were given`. All built-in and string-named custom action registrations now resolve the method via the class (`type(self)._action_x` / `getattr(self.__class__, act)`), matching the already-correct `@action` discovery path.
- **Admin Bulk-Delete Bypassed Relational Cascade Handling**: `_action_delete_selected` called `queryset.delete()` — a raw bulk `DELETE FROM ...` that, by its own docstring, skips `on_delete` cascade handlers (CASCADE/SET_NULL/PROTECT/RESTRICT) and delete signals entirely. Deleting rows referenced by other tables' foreign keys through the admin UI silently orphaned child rows instead of cascading or raising a protection error, unlike `Model.delete_instance()` which correctly walks reverse-FK refs inside a transaction. The action now iterates `queryset.all()` and calls `delete_instance()` per record, restoring correct relational integrity handling (and delete signals) for admin bulk-delete, mirroring the per-row pattern every other built-in admin action already uses.
- **`select_related()` Not Applied by `first()`/`one()`**: `QuerySet.all()` (`aquilia/models/query.py`) was the only terminal method that post-processed `select_related`'s joined columns into a hydrated related-model instance; `first()` and `one()` called `from_row()` directly on the raw row, so the FK attribute kept whatever `from_row` set it to from the unprefixed column — the raw stored FK value, never a related-model instance. A query like `await Model.objects.select_related("user").filter(...).first()` returned an object whose `.user` was a bare string/int PK, crashing with `AttributeError` on any subsequent attribute access (e.g. `existing_token_model.user.name`) despite `select_related` being requested. The row→instance hydration logic (select_related column-splitting, previously inlined only in `all()`) is now a shared `_hydrate_rows()` helper reused by `all()`, `first()`, and `one()` (which `last()` already delegates to `first()` for), so every terminal method now honors both `select_related` and `prefetch_related` consistently.
- **QuerySet/Manager Chain Loses Model-Identity Typing**: `Q`, `QuerySet`, `BaseManager`, and `Manager` (`aquilia/models/query.py`, `aquilia/models/manager.py`) were plain, non-generic classes, so every chained call (`.filter()`, `.select_related()`, etc.) widened the result to the bare `Q`/`Model` base — IDEs and mypy lost all field-name autocomplete on the model returned by `.first()`/`.all()`/`.get()`/etc. after any chain, even though the query worked correctly at runtime. `Q`/`QuerySet`/`BaseManager`/`Manager` are now generic over the owning model type, and `Model.objects` (`aquilia/models/base.py`) is declared `ClassVar[Manager[Self]]` instead of a bare `ClassVar[Manager]` — every concrete model automatically gets `Manager[ThatModel]`/`Q[ThatModel]` typing with no per-model annotation needed. `Model`'s own classmethods/instance methods that return `Self` at runtime already (`create`, `get`, `get_or_none`, `get_or_create`, `update_or_create`, `find_or_create`, `query`, `all`, `latest`, `earliest`, `raw`, `using`, `save`, `refresh`, `bulk_create`, `bulk_update`, `from_row`) are now annotated `Self`-returning to match, so e.g. `await UserModel.objects.filter(...).first()` and `await UserModel.get(...)` both resolve to `UserModel | None` / `UserModel`, not the bare `Model` base. Resolving individual *field* attributes to their Python value type (e.g. a `CharField` showing as `str` rather than the `Field` descriptor class) is a separate, pre-existing, sitewide framework characteristic and is not addressed by this fix.

## [1.2.4] — 2026-07-05 — "Kraken's Wake"

### Added

- **`Env` Auto-Resolve**: `aquilia.pyconfig.Env` now implements the descriptor protocol (`__get__`), so config values resolve automatically on plain attribute access (e.g. `ProdEnv.mail.email_port`) instead of requiring an explicit `.resolve()` call. `Secret` intentionally does **not** gain this behavior — `.reveal()` remains required, preserving the "never leak a secret via bare attribute access" guarantee. Internal introspection (`AquilaConfig.to_dict()`, `_class_to_dict()`, and `__init_subclass__`'s section-inheritance loop) now reads raw `Env`/`Secret` wrappers via `inspect.getattr_static()` instead of `getattr()`/`inspect.getmembers()`, avoiding double-resolution and preventing required env vars from being eagerly (and prematurely) resolved just by defining a config subclass.
- **Manifest-Declared DI Tags**: `ServiceConfig` gained a `tag` field so manifest-registered services can declare an explicit DI tag directly, instead of only via a `@service(tag=...)` class decorator.

### Changed

- **Mail Integration Consolidation**: Removed three redundant, independently-drifting declarations of the same provider config fields (`aquilia/integrations/_legacy.py`'s `Integration.MailProvider.*`, `aquilia/integrations/mail.py`'s `SmtpProvider`/`SesProvider`/`SendGridProvider`/`ConsoleProvider`/`FileProvider` dataclasses, and `aquilia/mail/config.py`'s Contract schema). `SmtpProvider`, `SesProvider`, `SendGridProvider`, `ConsoleProvider`, `FileProvider`, and `Integration.MailProvider.*` are now thin wrappers around the real `aquilia.mail.providers` classes — field names and defaults live in exactly one place (the real provider `__init__`). `MailAuth` moved to `aquilia.mail.auth` as the single canonical implementation, re-exported from both `aquilia.integrations.mail` and `aquilia.integrations.Integration.MailAuth`. As part of this consolidation, Console/File provider builders' default `rate_limit_per_min` changed from a special-cased `10000` to the standard `600` shared by all provider types.
- **Legacy Integration System Removal**: Removed the monolithic `aquilia/integrations/_legacy.py` configuration builder shim entirely. Replaced it with a lightweight, typed wrapper `aquilia/integrations/integration.py` that retains identical public static methods (e.g. `Integration.mail()`, `Integration.admin()`, etc.) but delegates internally to the corresponding typed dataclasses and leverages runtime reflection to filter fields and merge arbitrary `**kwargs` cleanly.

### Fixed

- **Non-Integer Foreign Key Primary Keys**: `ForeignKey.validate()`, `to_db()`, and `sql_type()` (`aquilia/models/fields_module.py`) previously hardcoded an `int` primary key, and never unwrapped a related `Model` instance to its `.pk` — assigning a related instance directly (e.g. `Verification(user=some_user)`) or pointing a FK at a UUID/str-keyed model raised `FieldValidationError: Expected integer FK, got <TypeName>` on save/validate. All three now resolve the related model's actual primary-key field and delegate type coercion/conversion to it, falling back to the previous int-cast only when the related model can't be resolved. `schema_snapshot.py`'s `_field_to_sql_type()` (the function driving `makemigrations`) had the same independent `INTEGER`-for-every-FK hardcode and is fixed the same way, so migrations for FK columns pointing at non-integer-PK models now generate the correct column type instead of `INTEGER`.
- **`OneToOneField` Dropped Constructor Kwargs**: `OneToOneField.__init__` re-declared `ForeignKey`'s parameter list without `related_name`/`on_delete`/`on_update`/`db_constraint`, so those were always silently discarded regardless of what a caller passed. It also never actually defaulted `unique=True` (the `kwargs.setdefault("unique", True)` was dead code — `unique` was always already present in the dict from the `unique: bool = False` parameter default). Both are fixed: all `ForeignKey` kwargs are now forwarded, and `unique` correctly defaults to `True`.
- **UUID/Non-Primitive Primary Key Lookups Crashing**: `Model.get(pk=...)` (`aquilia/models/base.py`) and `Q.filter()`/`Q.exclude()` (`aquilia/models/query.py`) bound raw Python values (e.g. a `uuid.UUID` instance) straight into the SQL driver without running them through the owning field's `to_db()`, raising `QueryFault: ... Error binding parameter ... type 'UUID' is not supported` for any lookup on a UUID (or other non-primitively-bindable) field/FK — including the read path (`related()`) behind the FK fixes above. Both now convert filter values through the resolved field's `to_db()` (mirroring the conversion `update()` already applied to SET values), restricted to pure value-comparison lookups (`exact`, `ne`, `in`, `range`, `gt`/`gte`/`lt`/`lte`) so pattern/boolean/date-part lookups (`contains`, `isnull`, `year`, etc.) are left untouched.
- **Admin Bulk-Action CSRF Crash**: `bulk_action()`'s "Delete selected"/bulk-action endpoint (`aquilia/admin/controller.py`) parses its form with `multi=True` to preserve the repeated `selected` checkbox field as a list — which incidentally wrapped the singular `_csrf_token` field in a list too. `AdminCSRFProtection.validate_request()` then called `.encode()` directly on it, crashing every bulk action (including "Delete selected") with `AttributeError: 'list' object has no attribute 'encode'`. `validate_request()` now coerces a list-valued token to its first element before comparison.
- **Stale Manifest Import Paths Never Resynced**: Restructuring a module file into a package (e.g. `modules/auth/models.py` → `modules/auth/models/register.py`) permanently broke `aq discover`/workspace validation. Two compounding bugs in `aquilia/discovery/engine.py`'s `ManifestDiffer`: `_is_declared()` treated any existing manifest ref with a matching class name — regardless of its actual dotted path — as "already declared," so the newly-discovered correct path never generated an `add` action; and the removal loop's `is_moved` guard then also suppressed removing the stale entry. `_is_declared()` now only matches on the exact import path, so a moved class correctly produces an `add` action, which `ManifestWriter._add_component`'s existing class-name-match rewrite logic then applies in place. `_validate_workspace_config()` (`aquilia/cli/commands/run.py`) also only ever checked `<path>.py` when resolving a manifest's dotted import path, so it falsely reported package-style modules (a directory with `__init__.py`) as "file not found" — it now also accepts the package form.
- **`discover_patterns` Was Dead Config**: A module's `discover_patterns` (declared in `manifest.py`, e.g. `["controllers", "services", "models", ...]`) was parsed but never passed into the scanner, and `FileScanner.scan_module()`'s pattern filter only matched a file's bare stem — so a pattern like `"models"` never matched a nested `models/register.py` (stem `"register"`) even once wired up. `discover_patterns` is now read from each module's manifest and passed through to scanning, and the filter matches any path component (directory names as well as the file stem) relative to the module directory.
- **DI Explicit Tag Resolution ("provider not found")**: `Inject(SomeService, tag="...")` raised `ProviderNotFoundFault` even when `SomeService` was correctly registered, because the class-provider registration path (`aquilia/aquilary/core.py:_register_services`) only read a tag from a `@service(tag=...)` class decorator, never from the manifest entry itself, while `aquilia/di/core.py:Registry._load_manifest_services` never propagated a `tags=` value to `ClassProvider` at all. Both paths registered providers under an untagged key while tagged `Inject(...)` calls looked them up under a tagged key. Both now resolve the tag from the manifest entry first, falling back to the class decorator.
- **SMTP/SES/SendGrid Auth Silently Dropped**: `MailService._create_provider()` never read a provider's nested `auth` dict (the shape produced by `MailAuth.plain(...)` / `Integration.MailAuth.plain(...)`), only flat `username`/`password` fields — so any provider configured with per-provider `auth=` connected and sent unauthenticated, surfacing as `(530, '5.7.0 Authentication Required...')` from Gmail and equivalent rejections from other SMTP hosts. Credentials are now read with correct precedence: explicit flat fields → nested `auth` block → `config` dict; the same fix applies to SES's `aws_access_key_id`/`aws_secret_access_key` and SendGrid's `api_key`.
- **Provider-Specific Config Fields Silently Dropped**: `ProviderConfigContract` (`aquilia/mail/config.py`) ignored any provider field not in its small declared schema, so SES's `region`/`configuration_set`, SendGrid's `sandbox_mode`, File's `max_files`, and similar provider-specific options vanished before ever reaching the real provider constructor. `_validate_provider()` now folds unrecognized top-level fields into the provider's `config` dict instead of silently discarding them.
- **`MailAuth.api_key` Field/Classmethod Collision**: The `api_key` dataclass field on `MailAuth` collided with the `api_key()` classmethod defined in the same class body, so the field's default silently resolved to the bound classmethod instead of `None` for every `MailAuth` built without an explicit `api_key=` — corrupting `to_dict()` output (e.g. `Integration.MailAuth.anonymous().to_dict()` incorrectly included an `"api_key"` entry). The field is now stored internally as `api_key_value`; the public `to_dict()` key remains `"api_key"`.
- **Real Mail Provider Compatibility**: Real provider instances imported from `aquilia.mail` (like `SMTPProvider`, `ConsoleProvider`, `FileProvider`, `SESProvider`, `SendGridProvider`) previously lacked a `to_dict()` method, so they were dropped by `MailIntegration.to_dict()`, leaving the configured providers list empty and raising `No mail providers configured` (`MAIL_CONFIG_ERROR`) at runtime. Added a standard `to_dict()` to all five real provider classes that serializes all constructor-supplied fields and config parameters.
- **`Integration.admin` Legacy Flat Options Compatibility**: Restored support for flat legacy properties passed to `Integration.admin(**kwargs)` (such as `enable_*`, `disable_*`, `audit_*`, `monitoring_*`, `sidebar_sections`). The method now resolves, maps, and constructs the corresponding nested builder objects (`AdminModules`, `AdminAudit`, `AdminMonitoring`, `AdminSidebar`) transparently while correctly prioritizing explicitly-passed builder instances over flat parameter overrides.
- **Admin Configuration Builders & Fluent Properties**: Custom `LegacyFluentMixin.__getattribute__` now detects active function call bytecode sequences dynamically at runtime via scan-forward frame inspection. This allows properties/attributes on `AdminAudit`, `AdminMonitoring`, and `AdminSecurity` to correctly resolve to their raw primitive values for direct comparisons (supporting assertions like `is True`/`is False` in older test cases) while still correctly wrapping them in fluent `CallableBool`/`CallableInt`/`CallableStr`/`CallableList` builders when invoked as methods. `AdminModules` also implements a synchronized dual-write `__setattr__`/`__post_init__` pattern keeping the internal `_mailer` and `_testing` slots aligned with their dataclass counterparts.
- **Admin Security & Monitoring Bounds Clamping**: Added robust post-initialization and attribute setter validation checks to `AdminSecurity` and `AdminMonitoring` ensuring that custom integer configuration properties (such as `csrf_max_age`, `csrf_token_length`, `rate_limit_max_attempts`, `rate_limit_window`, `password_min_length`, `event_tracker_max_events`, `refresh_interval`) are strictly clamped to their required minimum bounds.
- **Database Integration Default Connection String**: Corrected default database connection string in `Integration.database()` to `sqlite:///db.sqlite3` to align with the framework's test expectations and fallback behavior.

## [1.2.3] — 2026-07-01 — "Kraken's Wake"

### Added

- **Automatic Port Switching**: Added a production-grade, internal port auto-switching fallback mechanism to development and production server run sequences. If the configured port is already occupied, the server automatically scans and binds to the next sequential available port (up to 100 attempts) and logs a warning message detailing the switch, preventing address-already-in-use startup crashes.

### Fixed

- **Multi-Database `.using(alias)` Silent No-Op**: `Q.using()` / `Manager.using()` / `Model.using()` previously recorded the alias but never resolved it to an actual connection, so every query silently executed against the default database regardless of the alias passed. `Q.using()` now resolves the alias via `get_database(alias)` immediately and rebinds the queryset, raising `DatabaseConnectionFault` for unknown aliases instead of failing silently.
- **Silent Data Corruption on `only()`/`defer()` Field Access**: Accessing a field excluded via `only()`/`defer()` previously leaked the raw class-level `Field` metadata object (or, in a naive fix, would have silently returned `None`, indistinguishable from a real database `NULL`). Instances with deferred fields now have their class swapped to a small cached guard subclass that raises `DeferredFieldAccessFault` (a subclass of `AttributeError`, so `getattr(obj, name, default)` call sites like dirty-field tracking and `to_dict()` still degrade to *default* as before) on direct access. Fully-loaded instances are completely unaffected and incur zero extra overhead. `refresh()`/`refresh_from_db()` correctly clears the guard once all fields are loaded.
- **Non-Transactional Cascade Delete**: `Model.delete_instance()`'s reverse-FK cascade loop (potentially several DELETE/UPDATE statements across related tables) and the final row delete now run inside a single `AquiliaDatabase.transaction()`, so a failure partway through (e.g. a `PROTECT` check on a later table) rolls back any earlier `CASCADE`/`SET_NULL` steps instead of leaving the database partially cascaded.
- **`_DepthHolder` Weak-Reference Crash**: Fixed `aquilia/models/transactions.py`'s `_DepthHolder.__slots__` omitting `__weakref__`, which raised `TypeError: cannot create weak reference` the moment `atomic()`'s per-task depth tracker (`WeakValueDictionary`) was actually entered via `async with atomic(): ...` inside a running event loop task.
- **Empty Contract AttributeError**: Fixed an early-return check in `ContractMeta.__new__` that skipped schema and projections compilation for subclasses with no fields/model, preventing `AttributeError` when validating empty or dynamically declared contracts.
- **Strict `class Meta` Rejection**: Hardened contract definitions to raise a `ContractFault` during class initialization if Django/DRF-style `class Meta` is defined, forcing the use of `class Spec` to avoid collisions with Model Meta metadata.
- **Automatic Class-Attribute Contract Nesting**: Automatically wrap assigned `Contract` subclasses to class attributes (e.g., `name = UserNameContract`) inside a `NestedContractFacet` during metaclass creation.
- **ORM Schema Creation with Expressions**: Skip expression-based unique constraints in `generate_create_table_sql()` and instead generate them as separate `CREATE UNIQUE INDEX` statements in `generate_index_sql()`, preventing database engines (SQLite, Postgres, etc.) from raising `expressions prohibited in PRIMARY KEY and UNIQUE constraints`.
- **Migration Constraint Translation**: Updated `AddConstraint` to compile expression-based unique constraints (containing function calls/expressions) into `CREATE UNIQUE INDEX` statements for all database dialects (SQLite, Postgres, MySQL, Oracle).
- **Strict Safe-DB Startup Guard**: Hardened the startup sequence to raise a `SchemaFault` and immediately halt the server startup if the database is missing or unapplied migrations exist when migrations are present in the project.
- **Registry Route Prefix Validation**: Accept and utilize `workspace_modules` configuration overrides inside `RegistryValidator.validate_manifests` and `_validate_route_conflicts` to correctly resolve module route prefixes during startup and CLI `validate`/`doctor` calls, preventing false-positive `RouteConflictError` crashes.
- **Outbound Contract Projection Overrides**: Removed raw inbound validated data serialization bypass from `Contract._to_dict_instance` to ensure wrapping/response contracts correctly apply their own projection and write-only filters on nested or returned contract instances.
- **ORM Persistence and UUID Primary Keys**: Fixed `ImprintFault` causing programming errors ("type 'UUID' is not supported") on SQLite databases by ensuring all primary key bindings convert values via `field.to_db()` and restricting `lastrowid` assignment to integer-based AutoFields.
- **Computed Contract Fields**: Fixed `Computed.extract()` in computed facets to correctly bind the contract instance as `self` when executing unbound methods.
- **Admin Panel PK Resolution**: Resolved list view and record endpoint 404 errors by dynamically resolving primary key field names using `model_cls._pk_attr` instead of hardcoding `id`.
- **Nested Contract Facet Typing**: Added generic parameterization to `Contract[ModelT]` and updated `imprint` overload signatures to enable IDE autocomplete for imprinted model instances.
- **Empty Datetime and Format Coercion**: Handled empty string inputs (`""`) gracefully in `to_python` and `validate` methods for `DateTimeField`, `DateField`, `TimeField`, `UUIDField`, and `DecimalField` (coercing them to `None` for nullable fields), resolving the `Invalid isoformat string` and parsing errors in the admin panel edit forms.
- **ORM `blank=True, null=False` String Field Coercion**: Coerced `None` input to empty string `""` for string-based fields (`CharField`, `TextField`, `GenericIPAddressField`, etc.) when `blank=True` and `null=False` to prevent database `NOT NULL` integrity constraint errors, adhering to standard ORM validation conventions.
- **Insert Query NOT NULL Inclusion**: Ensured `Model.save()`'s INSERT query builder always includes columns defined as `NOT NULL` even if their value is `None` at Python-level, enabling proper database-level constraint enforcement and/or field coercion.

### Performance

- **SQLite Double Thread-Pool Hop**: Merged `AsyncConnection.execute`/`execute_many`/`fetch_all`/`fetch_one` in `aquilia/sqlite/_connection.py` from two separate `run_in_executor` dispatches (one for `execute`/`executemany`, a second for `fetchone`/`fetchall`/`commit`) into a single combined thread-pool hop per call, cutting per-query thread-dispatch overhead roughly in half. Measured **+16% req/s on db_single, +18% on db_queries, +9% on db_updates** benchmark scenarios.

## [1.2.2] — 2026-07-01 — "Kraken's Wake"

### Fixed

- **Database Integration Configuration**: Fixed `Workspace.integrate()` to correctly handle `DatabaseIntegration` protocol instances and set `self._database_config`. This ensures the database configurations are correctly populated in the root configuration layout and resolved at ASGI app startup.
- **ORM Schema Expression Serialization**: Added automatic string casting for expression constraints (like `Lower` or `Upper`) and expression-based index fields within the admin dashboard's model metadata collection (`get_model_schema()`). This prevents `TypeError: Object of type Lower is not JSON serializable` when inspecting models that use function-based constraints or indexes.
- **Auto-Discovery Integration in CLI**: Replaced the legacy parser inside the server startup sequence with the unified next-generation `AutoDiscoveryEngine` to automatically sync manifests when running the development server.
- **SQLite Alter Constraints**: Modified migration translation to translate `UniqueConstraint` into unique indexes when applying migrations on SQLite databases.

## [1.2.1] — 2026-07-01 — "Kraken's Wake"

### Fixed

- **Startup dependency decoupling**: Decoupled `jinja2` and `markupsafe` from core dependencies, moving them to the `aquilia[template]` extras bundle to keep core installation lightweight.
- **Lazy Imports**: Converted eager template imports to a module-level lazy `__getattr__` import resolution mechanism, preventing startup crashes when `jinja2` is not installed.
- **Windows File Locking**: Resolved a trace storage lock issue on Windows by explicitly closing all SQLite connections in `SQLiteTraceStore`.
- **Toolbar Nonce Compatibility**: Injected toolbar now parses JSON trace payload dynamically by finding the script tag end delimiter instead of matching the full signature, allowing parsing even when CSP nonces are present.

## [1.2.0] — 2026-06-28 — "Kraken's Wake"

### Added

- **Database CLI Enhancements**:
  - Added `aq db history` subcommand to display a chronological list of applied migrations with timestamps, slugs, and checksum signatures.
  - Added `aq db rollback` subcommand supporting step-based (`--step`), timestamp-based (`--timestamp`), and zero-target rollbacks with dry-run planning (`--plan`).
  - Added `aq db check` subcommand to perform diagnostic validation of migration naming conventions, duplicate revision detection, and checksum verification.
  - Added `aq db diff` subcommand to run schema drift checks comparing the active database against code models (`--compare models`) or migration snapshots (`--compare migrations`). Formatted output as a unified, code-level Git-style diff representation.
  - Added `aq db seed` subcommand to load and run Python database seed scripts (`seeds.py`).
  - Added `aq db reset` subcommand to safely drop all tables (disabling FKs) and migrate the schema from scratch.
  - Added `aq db flush` subcommand to truncate data rows across all user tables (disabling FKs) without modifying the schema.
- **Click CLI Help Custom Colorization**:
  - Overrode options formatting across the entire CLI using `AquiliaCommand` and `AquiliaGroup` subclasses. Formats option flags in bold green, help text in white, and headers in bold cyan.
  - Forced colorization contexts globally unless `--no-color` is specified, ensuring options are colored even when CLI output is captured or piped.
  - Implemented a recursive `_upgrade_command_tree` utility inside command registration to automatically apply color options to all subgroups and nested subcommands.
- **Manifest-Level API Versioning Override**:
  - Replaced the legacy workspace-level `Module().versioning()` builder API with a first-class manifest-level `AppManifest.versioning` property configured directly in `manifest.py`.
  - Introduced `AppVersioningConfig` dataclass and a convenience `versioning()` helper to expose a structured, comprehensive configuration API supporting full strategy overrides (e.g., `strategy`, `versions`, `header_name`, `url_prefix`, `default_version`, `require_version`, `sunset_policy`, etc.) for self-independent module versioning.
  - Updated `VersionStrategy` and `VersionMiddleware` to dynamically instantiate and apply local `VersionStrategy` overrides per-module based on longest prefix matched request paths, falling back to workspace-level configurations.
  - Fixed a missing configuration mapping in `AquiliaServer._setup_versioning` to correctly pass and honor the workspace-level `url_position` (or `position`) parameters from the workspace configuration dictionary.
  - Implemented automatic version segment index detection in `URLPathResolver` to seamlessly handle `url_position="after"` layouts and variable prefix depths without requiring manual segment index configuration.
  - Implemented extensive unit, integration, and O(k) matching performance stress tests to verify correctness of overriding rules and matching latency under load.
- **Request Inspector** (`aquilia.inspector`): Full per-request execution tracing with swimlane-based timeline visualization in the admin panel.
  - Core data model: `RequestTrace`, `Span`, `Lane`, `SpanStatus`, `ExceptionNode`, `ResponseSummary` with contextvar-based request-scoped traces.
  - `InspectorMiddleware`: Captures request/response lifecycle, redacts sensitive headers and bodies, and auto-records middleware timing spans.
  - Per-middleware timing: Wraps each registered middleware to emit individual `middleware` lane spans with class name labels.
  - DI diagnostics listener: Bridges `Container.add_diagnostic_listener()` events into `dependency` lane spans for every `resolve_async` call.
  - Fault bridge: Listens to `FaultEngine.on_fault` and records `exception` lane spans with full stack frames, fault codes, and fingerprints.
  - HTTP client hook: `InspectorHTTPClientMiddleware` emits `external_http` lane spans for outbound requests with method/URL/status.
  - Query Inspector correlation: `QueryInspector.record()` now cross-links SQL queries to the active request trace via `_CURRENT_TRACE`.
  - Replay & Export: `build_replay_request()` reconstructs cURL-compatible request dicts; `export_traces()` / `import_traces()` support JSON round-trip.
  - SSE streaming: `SSEStreamManager` pushes live trace events to connected admin panel clients via Server-Sent Events.
  - Plugin API: `register_lane()` and `span_context()` allow user code to emit custom lane spans.
  - Ring-buffer collector: `InspectorCollector` stores the last N traces (configurable via `max_traces`) with O(1) commit and lookup.
  - Configurable redaction: Header names, body field paths, and query params are redacted before storage (customizable blocklists).
  - Admin panel integration: Full "Request Inspector" page with waterfall timeline, request/response details, spans table, and SSE live-stream toggle.
  - Workspace fluent API: `Workspace.inspector(enabled=True, max_traces=200)` for zero-boilerplate opt-in.
  - `InspectorConfig.from_dict()` class method with safe defaults and production guard (`force_enable_in_prod`).
  - 15 dedicated test files covering config, trace model, collector, redaction, faults, middleware, DI listener, fault bridge, HTTP client hook, query correlation, replay/export, plugins, SSE streaming, admin UI, and workspace/server wiring.
- **Container self-registration**: DI containers now register themselves under the `Container` token, enabling provider adapters to receive the container via dependency injection.
- **`Container.add_diagnostic_listener()` public API**: Allows external subsystems (like the inspector) to observe dependency resolution events.
- **Explicit Cross-field validation (`@ward`)**: Introduced `@ward` decorator and `collect_ward_methods()` metadata engine to register cross-field constraints.
- **Intermediate Representation (`Sigil`)**: Added `Sigil` compilation engine to track class validation schemas, generate Draft 2020-12 JSON Schemas, execute sequential schema migrations, and generate stable structural hashes.
- **Transforms and Pipelines (`>>`)**: Introduced chaining operators `>>` on facets to build transform pipelines using standard transformations (`strip`, `lower`, `slugify`, etc.).
- **Bulk & Stream Validation**: Implemented `seal_many` (with ThreadPoolExecutor parallel mode), `seal_stream` (for async NDJSON streaming), and `seal_columnar` (for bulk ETL columnar passes).
- **Test Generation**: Added `Contract.example()` for random schema-valid dictionary generation, and `Contract.strategy()` for Hypothesis integration.
- **Discriminated Unions (`ContractUnion`)**: Support concrete type union validation (e.g. `Circle | Square`) with automated Literal or explicit `Spec.discriminator` dispatching.
- **Form & File Uploads via Contracts (`UploadFile` and `FormData`)**: Added first-class support for explicit and implicit file uploads and form inputs in Contracts. Support includes single/multiple/optional file uploads, custom content types, size limits, primitive type castings, and nested contracts for form/multipart data validation.
- **Unified Request Input Resolution**: Centralized query parameters, cookies, path parameters, headers, and request bodies into a unified resolution layer (`extract_value_from_request`).
- **Standardized DI Parameter Casting & New Facets**: Equipped RequestDAG and controller engine to dynamically resolve and cast parameters using `SetFacet`, `TupleFacet`, `EnumFacet`, and `BoolFacet` validation rules. Added `Cookie(...)` and `Path(...)` extraction support.
- **Click-based Aquilary CLI commands**: Added the `aquilary` CLI group under the `aq` main tool, providing native `validate`, `inspect`, `freeze`, `graph`, and `run` subcommands.
- **Aquilary CLI test coverage**: Added automated test coverage for the Click-based aquilary commands in `tests/test_aquilary_cli.py`.

### Changed

- **Database Introspection and Migration Rollback**:
  - Enhanced `create_snapshot_from_db` to map tables back to namespaced codebase model class names, resolve field `max_length` constraints from sql column types using regex, and align serialization constraints with codebase model snapshots.
  - Upgraded `MigrationRunner` rollback execution to support target revision `"zero"`, reverting all applied migrations in chronological order.
- **Scaffolding Integration API migration**:
  - Updated workspace generator to generate templates utilizing the new type-safe, validated integrations API (`aquilia/integrations/*`) instead of the legacy `Integration` config helper.
- **Boilerplate reduction and scaffolding cleanup**:
  - Removed generation of redundant files (`Makefile`, `.editorconfig`, `Dockerfile`, `docker-compose.yml`) from default workspace scaffolding.
  - Eliminated automatic generation of empty directories (`locales`, `templates`, `assets`, `artifacts`) to keep new workspaces lightweight.
  - Switched generated module controllers to automatically use input validation contracts instead of parsing bodies with raw `ctx.json()`.
- **Zero Runtime Dependencies**: Completely migrated the Contracts validation engine to pure-Python using only Python standard library modules.
- **Deep Performance Optimizations**:
  - Implemented lazy nested wrapping in `DataObject` to eagerly wrap items only when accessed, caching the result.
  - Extracted dynamically-compiled wrapper classes in `wrap_callable_attribute` to module scope.
  - Cached compiled regexes, sigil validations, and pre-loaded types at module-level in `sigil.py`.
  - Replaced manual sigil validation in request contract binding with direct `bp.is_sealed` lookup and validation caching.
  - Made SQLite `Row` inherit from `dict` and return rows directly from the adapter with zero conversion loops.
  - Cached the query inspector instance globally to prevent dynamic imports and lookups on every query.
  - Passed and reused `ResolveCtx` inside `resolve_async` to avoid redundant context allocations.
  - Leveraged fast `orjson` parsing directly on raw bytes inside `Request.json` when available.
  - Inspected coroutines once at decoration time in `@cached` and `@invalidate` decorators, removing reflection overhead.
  - Cached split parts of dotted sources in `Facet.extract`.
  - Added direct class check fast-path (`res.__class__ is Response`) inside middleware dispatch to bypass `isinstance` overhead.
  - Optimized DI container registration inside the ASGI pipeline (`asgi.py`) to run synchronously and direct-cache the Request instance, avoiding async registration.
  - Redefined `Headers` to eagerly decode and index raw connection byte keys and values to strings, removing lookup overhead.
  - Fixed controller instantiation in the execution engine to support and correctly utilize `instantiation_mode = "singleton"`.

### Removed

- **Artifact System**:
  - Entirely removed the redundant `aquilia.artifacts` module (`core`, `builder`, `reader`, `kinds`, `store`).
  - Removed `compile` and `freeze` commands from the CLI as the core ASGI server runtime is manifest-driven and does not require pre-compiled artifacts.
  - Rewrote `aq ws inspect` and `aq ws gen-client` to statically introspect workspace socket controllers in real-time in memory instead of relying on compiled `ws.surp` artifact files.

### Fixed

- **Discovery system improvements**:
  - Aligned static `ASTClassifier` predicates and suffix checks with runtime `PackageScanner` to ensure consistent discovery of controllers and services.
  - Implemented complete middleware auto-discovery supporting classes inheriting from `aquilia.middleware.Middleware`.
  - Fixed sync engine and `_compute_import_path` namespace preservation to retain the full dotted parent package prefix (e.g. `modules.users.controllers:UsersController`) when updating `manifest.py`.
  - Added safe standard imports relative to workspace root in database model registration to prevent duplicate model class loading and class identity conflicts.
  - Refactored `WorkspaceGenerator` discovery merge phase to preserve full namespaced dotted paths instead of class names.
  - Added static auto-discovery support for socket controllers.
- **Windows compatibility fixes**:
  - Replaced unix-specific `ProcessLookupError` exception handling with generic `OSError` in the `mcp` CLI commands, allowing the background daemon lifecycle to run correctly on Windows.
  - Handled missing `signal.SIGKILL` gracefully in process termination routines on Windows.
- **`RequestIdMiddleware` stability**: Preserves pool-assigned `request_id` from `_ctx_pool.acquire()` instead of regenerating it, ensuring consistent request IDs across middleware, DI, and logging.
- **Defensive inspector config access**: All `get_inspector_config()` calls in `AquiliaServer` use `hasattr()` guards so mocked configs (plain dicts in tests) don't raise `AttributeError`.
- **Dependency Precedence over Request Body**: Fixed parameter source classification and binding to ensure that explicit `Dep(...)` declarations (such as `param: T = Dep(callable)`) take precedence over implicit source type-based classification (such as `Contract subclass` → `source="body"`). Explicit dependency parameters are now correctly classified as `source="dep"` and resolved via `RequestDAG`, preventing request body payloads from overriding the dependency results.
- **Multiple Contract Parameter Support**: Fixed parameter binding and validation to support multiple contract parameters in a single handler. Resolves all contract arguments from the same request body, supports async validation via `is_sealed_async` when available, and consolidates validation errors across all contracts into a single unified `SealFault`. Also added `ContractContext` and `LazyServiceProxy` to enable contracts to lazily resolve and invoke DI container services via `self.context[key]`.
- **String Annotation Evaluation (PEP 563)**: Fixed annotation parsing inside `_safe_resolve_annotation` to prevent incorrect splitting of PEP 604 unions (e.g. `str | None`) when they are nested inside generic subscripts (like `Annotated[str | None]`). Improved resolution by attempting `eval()` within the `AutoResolveMapping` namespace before falling back, enabling robust resolution of complex pipeline operator `>>` expressions.
- **Ward execution attribute collision**: Resolved validation crash when using `@ward` methods on models with fields named `items`, `keys`, `values`, `get` or other dictionary method names. Overrode `__getattribute__` on `DataObject` to prioritize dictionary keys over class-level dictionary methods.
- **Union schema generation crash**: Corrected literal constraint schema generation for unions (e.g. `Circle | Square`) which crashed with a `TypeError: 'set' object is not subscriptable`. Changed `ChoiceFacet.allowed_values` property to return an ordered `tuple` of keys rather than an unordered `set`.
- **Serialization failure in `to_dict` and `to_dict_many`**: Fixed `to_dict()` and `to_dict_many()` serialization to work correctly when called as class methods (e.g. `Contract.to_dict(instance)`) and support inbound validated data mapping (when `instance` is None) on `many=True` and `many=False` contracts. Implemented `ContractSerializationDescriptor` to cleanly route class-level vs instance-level method calls.
- **Form URL Encoded & Multipart Contract validation**: Resolved critical validation failure where contracts bound to form or multipart request payloads lost all fields because the validation engine strictly checked `isinstance(data, dict)`. Contracts and `Sigil` validation now support mapping-like objects (such as `FormData` and `MultiDict`).
- **Missing content-type routing**: Fixed body parser selection in `ControllerEngine._get_body()` to route to `json()`, `form()`, or `multipart()` based on the `Content-Type` header, ensuring multipart payloads are parsed.
- **Empty string coercion**: Coerces empty string `""` values submitted in forms to `None` for nullable fields, or `UNSET` to allow default value injection.
- **String annotation resolution for modules**: Improved `_safe_resolve_annotation` to support attribute traversal on module-level types (e.g. `uuid.UUID` or `datetime.date`) when using string-based runtime annotations.
- **Incorrect RegistryFault kwargs**: Corrected the `RegistryFault` call parameters to match its domain constructor signature.
- **Middleware Standardization**: Refactored core framework and extension middlewares to inherit from the `Middleware` base class and follow the standard execution signature: `async def __call__(self, request, ctx, next_handler)`.
- **Dynamic Middleware Setup**: Fixed instantiation of dynamically configured middlewares in `AquiliaServer._instantiate_middleware` by auto-injecting the `EffectRegistry` for `EffectMiddleware` and `FlowContextMiddleware`.
- **Type-Aware Parameter Injection**: Extended parameter binding in `ControllerEngine` to dynamically detect and inject `RequestCtx`, `Request`, and `FlowContext` parameters based on their type annotation, regardless of the parameter name (e.g. `req: RequestCtx` or `ctx: FlowContext` are now correctly injected). Excluded special parameters from static route query/path metadata compile passes.
- **Bidirectional Effect Context Fallback**: Updated `FlowContext` and `RequestCtx` to automatically fall back to and copy pre-acquired request-level effects in their constructor and effect resolution methods, ensuring compatibility when accessed from handler methods decorated with `@requires`.
- **Render deployment runtime**: Added `"runtime": "image"` in the Render API service creation and update payloads for Docker-image-backed services to resolve `[PROVIDER_API_ERROR] [400] invalid runtime` failures.
- **Removed backup code**: Deleted the deprecated `render_backup_phase10` provider directory.
- **Robust backwards-compatible `RegistryFault`**: Modified the `RegistryFault` constructor to gracefully handle legacy calls using `name` and positional formatting, avoiding `TypeError` exceptions.
- **Fingerprint generation in CLI**: Fixed the fingerprint generation crash in `validate` and `doctor` commands that attempted to call `FingerprintGenerator.generate` as a class method without required arguments.
- **Instantiated manifest loading**: Enhanced manifest loading to support instantiated `AppManifest` definitions in python files, resolving failures to load module configs.
- **Frozen manifest serialization**: Resolved type serialization errors when freezing complex middleware and service list items, and enabled `_register_services` to handle dictionary config items loaded from frozen manifests.
- **CLI imports reliability**: Injected the workspace root into `sys.path` within `aquilary` CLI handlers, preventing `No module named 'modules'` exceptions during import operations.
- **Dependency Graph cycle detection fix**: Fixed a silent failure in `aquilia.aquilary.graph.DependencyGraph` where self-loop cycles (a module depending on itself) were not detected by Tarjan's algorithm, resulting in empty or incomplete topological load orders. Added length-matching verification in `topological_sort` and self-loop detection in `find_cycle` to raise `DependencyCycleError` robustly.
- **Request Inspector Correctness & Unification**:
  - Unified `QueryInspector` to subscribe to `InspectorCollector` trace completion events instead of being called directly from the database engine, avoiding circular dependencies and coupling.
  - Fixed query parameter redaction in `InspectorMiddleware` to run incoming query params through a redaction pass.
  - Fixed SQL bind parameters redaction by adding support for tuples/lists recursion in `redact_body_keys_recursive` and applying it to query records.
  - Synced default configuration options for `redact_headers` and `redact_body_keys` between `InspectorConfig` and `ConfigLoader`.
  - Added `"signature"` to the default body keys redaction blocklist.
  - Fixed ORM model names not being threaded to SQL spans in `db/engine.py` by introducing `current_model_var` and wrapping database connections in `QuerySetDatabaseWrapper`.
- **Request Inspector Toolbar Injection Core**:
  - Implemented `ToolbarInjectionMiddleware` to inject a collapsed debugging toolbar tab and panel shell into qualifying HTML responses.
  - Lazily hydrates debugging panels (Timer, SQL, Request, Response, Headers) on the client side using embedded JSON trace data to avoid server-side template rendering overhead.
  - Implemented eligibility filters (content-type, response type, redirect skipping, and path exclusion) to ensure robust toolbar injection.
- **Request Inspector Lane Expansion**:
  - Expanded `Lane` enum with `VERSIONS`, `SETTINGS`, `STATIC`, `TEMPLATES`, `CACHE`, and `SIGNALS` lanes.
  - Wired versions collection dynamically into the trace initialization.
  - Wired settings lookup instrumentation inside `ConfigLoader.get`.
  - Wired template rendering instrumentation inside `TemplateEngine.render` and `render_sync`.
  - Wired cache backend request timing and hit/miss reporting inside `CacheService` methods.
  - Wired model signals dispatch tracing inside `Signal.send`, `send_sync`, and `robust_send`.
  - Wired static file serving telemetry inside `StaticMiddleware.__call__`.
- **Request Inspector Beyond-DJDT Panels & Pluggable Storage**:
  - Implemented pluggable `TraceStore` interface with memory-backed `MemoryTraceStore` (ring-buffer) and disk-backed `SQLiteTraceStore`.
  - Refactored `InspectorCollector` to delegate trace storage, listing, fetching, and clearing to the configured `TraceStore`.
  - Added `store` and `store_path` settings to `InspectorConfig` and `ConfigLoader` defaults.
  - Wired background task enqueue tracing in `TaskManager.enqueue` to log `Lane.TASKS` events.
  - Wired WebSocket broadcast and publish_room message tracing in `SocketController` to log `Lane.SOCKETS` events.
  - Wired outbound email envelope metadata logging in `MailService.send_message` under `Lane.MAIL`.
  - Capture active session ID, user ID, clearance levels, roles, and request locale dynamically inside the middleware request-response loop under `auth` and `i18n` trace spans.
- **Request Inspector Advanced Capabilities (EXPLAIN, cProfile, Redirects, OTel)**:
  - Wired background query plan logging (`EXPLAIN`) for database queries exceeding the slow threshold.
  - Implemented single-flight request profiling using standard library `cProfile` and `pstats` when `X-Profile: true` header or `?profile=true` query parameter is supplied.
  - Implemented client-side cookie redirect folding to capture redirect history and display it inside a clean "Redirects" panel on the injected toolbar.
  - Correlated request trace IDs with OpenTelemetry trace and span contexts when active.
- **Request Inspector Sampling, Security Hardening & Design Consolidation**:
  - Added configurable `sampling_rate` (0.0–1.0) to `InspectorConfig` for probabilistic request tracing. Defaults to 1.0 (trace all requests).
  - Added `authorized_ips` (IP allowlist, defaults to `127.0.0.1` / `::1`) and `dashboard_auth_token` (optional Bearer token) to gate access to the inspector dashboard and API endpoints.
  - Wired `_check_inspector_auth` authorization guard into all 5 inspector admin controller endpoints.
  - Extracted CSS design tokens from the injected toolbar template into a reusable `_CSS_DESIGN_TOKENS` constant for sharing between the toolbar and standalone dashboard.

## [1.1.2] — 2026-06-12 — "Crimson Gale"

### Fixed

- **`name 'Entry' is not defined` server crash**: `Integration.middleware.Entry` is a
  `@dataclass` nested inside `middleware` which is nested inside `Integration`. Python
  class bodies do not create enclosing scopes for nested function bodies, so the bare
  `Entry(...)` call inside `Chain.use()` raised `NameError`. Fixed by using the
  fully-qualified `Integration.middleware.Entry(...)` path.
- **Generated workspace missing `Integration` import**: Commit `ca37a5e` removed
  `Integration` from the generated `workspace.py` imports but the template body still
  called `Integration.middleware.defaults()`, `Integration.di(...)`, etc. Restored
  `Integration` to the import lines in both full and minimal templates.
- **`.env` values never reflected in workspace config**: Three related bugs conspired
  to make `.env`-defined values invisible:
  1. `Workspace.to_dict()` read `os.environ.get("AQ_ENV", "dev")` **before** dotenv
     was loaded, so a `.env` with `AQ_ENV=prod` always selected `DevEnv`.
  2. `_default_dotenv_search_paths()` listed `.env.example` **after** `.env`, and
     since `merged_values.update()` lets later files win, `.env.example` clobbered
     `.env` values (e.g. `AQ_HOST=127.0.0.1` overrode `ProdEnv`'s `0.0.0.0`).
  3. `ConfigLoader._load_pyconfig_file()` had the same order-of-operations bug.
- **`AQ_ENV`/`AQUILIA_ENV` inconsistency**: `Workspace.to_dict()` only checked
  `AQ_ENV` but the runtime sets `AQUILIA_ENV`. Now both are checked with
  `AQUILIA_ENV` taking precedence.
- **Removed template files from dotenv search paths**: `.env.example`, `.env.defaults`,
  and `.env.default` are **templates** meant to be copied, not config sources.
  They are no longer loaded by the default dotenv search.
- **`.env.example` used wrong variable names**: Generated `.env.example` documented
  `AQUILIA_MODE`, `AQUILIA_HOST`, `SECRET_KEY` — none of which match the
  `AQ_ENV`, `AQ_HOST`, `AQ_SECRET_KEY` names the framework actually reads.

## [1.1.1] — 2026-06-09 — "Sea Serpent"

### Changed

- Extracted `Workspace`, `Module`, and supporting dataclasses (`RuntimeConfig`,
  `ModuleConfig`, `AuthConfig`) into a clean `aquilia/workspace.py` module.
- `Workspace.integrate()` accepts `aquilia.integrations.*` typed dataclasses
  directly via the `IntegrationConfig` protocol (already partially supported).
- `Workspace.i18n()`, `Workspace.tasks()`, and `Workspace.storage()` convenience
  methods now use `I18nIntegration`, `TasksIntegration`, and `StorageIntegration`
  typed dataclasses internally instead of the legacy `Integration.*` static methods.
- Moved the legacy `Integration` class to `aquilia/integrations/_legacy.py`
  for backward compatibility.  Existing code using `Integration.mail(...)`,
  `Integration.admin(...)`, etc. continues to work.
- Updated all example workspace files to use typed integration dataclasses
  from `aquilia.integrations` instead of the `Integration` static API.
- Updated all test imports to use `aquilia.workspace` and
  `aquilia.integrations` directly.

### Removed

- Removed `aquilia/config_builders.py` — the 5420-line god-file has been deleted.

### Fixed

- **Thread safety**: Replaced `bool` flag `_dotenv_lock` with `threading.RLock()`
  in `pyconfig.py` — two threads loading dotenv simultaneously no longer corrupt
  `os.environ`.
- **I18n default values**: Fixed broken `dataclasses.field()` usage on plain
  class attributes in `AquilaConfig.I18n` (replaced with plain lists).
- **Catalog format consistency**: `ConfigLoader.get_i18n_config()` now defaults to
  `"json"` (was `"surp"`), matching `AquilaConfig.I18n.catalog_format`.
- **`for_env()` recursion**: `AquilaConfig.for_env()` now recursively searches all
  subclass depths (was limited to 2 levels).
- **Step numbering**: Renumbered `ConfigLoader.load()` steps to remove the gap
  (Step 4 → Step 3, Step 4.5 → Step 4).
- **Config boilerplate**: Added `ConfigLoader.get_subsystem_config()` generic method;
  10 of 12 subsystem config getters are now thin wrappers, cutting boilerplate by ~80%.
- **Config package**: Created `aquilia/config/` package as a canonical re-export hub.
  `from aquilia.config import Workspace, Module, AquilaConfig, Env, Secret` works.
- **pyproject.toml**: Removed `psutil>=7.2.2` from core dependencies (now optional).
  Removed empty `templates`, `db`, and `files` extras. Fixed stale MLOps comment.

## [1.1.0] — 2026-06-08 — "Black Pearl"

### Added

- aquilia/sse/ — Server-Sent Events: SSEEvent, SSEResponse, json/text stream helpers
- aquilia/otel/ — OpenTelemetry: OTelConfig, OTelMiddleware, no-op fallback
- aquilia/controller/validation.py — @validate_body(ContractClass) decorator
- aquilia/sqlite/_config.py — SqlitePoolConfig with full parameter surface
- New [postgres] optional extra (asyncpg)
- New [otel] optional extra (opentelemetry-*)

### Changed

- URL pattern documentation: guillemet delimiters replaced with brace syntax {id:int}
- Moved ruff from dependencies to [dev] optional extra
- Moved asyncpg from dependencies to new [postgres] optional extra
- Fixed broken GitHub URLs (axiomchronicles → tubox-labs)

### Removed

- Removed aquilia/mlops/ in its entirety
- Removed duplicate aquilia/aquilia_mcp/ package (canonical is aquilia.mcp)
- Removed AMDL DSL: parser, AST nodes, __init__old.py, AMDLParseFault
- Removed aquilia/patterns/lsp/ Language Server Protocol server

### Fixed

- aiosqlite removed as framework dependency; only available via [sqlite-compat]

## [1.0.5] — 2026-06-04 — "Jolly Roger"

### Added

- Added a production-grade, source-backed Aquilia MCP server under `aquilia.mcp` with JSON-RPC stdio support, tool/resource/prompt registries, persistent repository indexing, installer helpers, and canonical `python -m aquilia.mcp` entrypoints.
- Added MCP tools and prompts for framework API discovery, bootstrap/runtime explanation, workspace and module scaffolding guidance, manifest-plan validation, integration recommendations, deprecation guarding, CLI discovery, example lookup, and agent prompt generation.
- Added practical MCP documentation and bootstrap configs for Claude, Codex, and Gemini CLI under `docs/mcp/` and `examples/mcp_bootstrap/`.

### Changed

- Replaced the Crous/Crousr binary serialization stack with Surp across runtime request and response helpers, compiled artifacts, Aquilary registry loading, admin audit persistence, i18n catalogs, model snapshots, WebSocket artifacts, template cache metadata, analytics cache, provider credential stores, and CLI workflows.
- Renamed public binary payload helpers and decorators from Crous terminology to Surp terminology, including `Request.surp()`, `Response.surp()`, `requires_surp`, `SurpCatalog`, and related availability helpers.
- Updated generated artifact extensions and documentation from `.crous` to `.surp` while preserving JSON fallback paths where the framework already supported them.
- Updated package dependencies to install `surp` instead of `crousr` and `crous-native`.
- Allowed `aq i18n init --format surp` to create Surp-backed starter catalogs.
- Rewired `aq mcp` commands to the canonical `aquilia.mcp` package while preserving the existing `aquilia.mcp` compatibility surface.

### Removed

- Removed Crous-specific imports, native backend probing, API names, file extensions, and request/response tests.

### Security

- Hardened MCP resource access and diagnostics with read-only defaults, path traversal and null-byte rejection, binary-file guards, bounded stdio frames, strict tool input validation, and secret redaction in doctor output.

### Tests

- Added Surp request/response coverage and updated admin, i18n, provider, regression, and security tests for the new Surp-backed behavior.
- Added MCP protocol, stdio transport, indexer/search, tool, prompt, installer, CLI, and end-to-end stdio session coverage for the canonical package.
- Verified the migration with bytecode compilation, focused Surp/i18n/provider tests, stale-reference scans, and a full test run with only the sandbox-local loopback test requiring an isolated permissioned rerun.
- Verified MCP changes with focused MCP tests, Ruff checks, bytecode compilation, index generation, and a full test suite run.

### Tooling

- Began tracking the repository-local `.agents/` skill definitions and stopped ignoring local agent skill metadata.
- Added `aq mcp` workflows for serving, index building, doctor diagnostics, agent installation, tool and prompt listing, and source-backed query testing.

## [1.0.4] — 2026-05-17

### Changed

- `aq compile` now writes explicit artifacts through `WorkspaceCompiler` without depending on a build pipeline.
- `aq freeze` now creates an integrity snapshot for generated artifacts under `artifacts/`.
- Deployment Makefile generation now calls `python -m aquilia.cli compile`.

### Removed

- Removed the React-style `aquilia/build` package and the `aq build` command.
- Removed automatic build-gating from `aq run`, `aq serve`, and `aq deploy`; runtime and deploy generation now use native workspace loading and live introspection.
- Removed the Admin Build page, `/admin/build/` route, sidebar/search links, and `AdminModules.build` configuration surface.

### Fixed

- Isolated independent SQLite `:memory:` pools while preserving shared state across connections within the same pool.

### Documentation

- Updated CLI, deployment, admin, release, and getting-started docs to reflect the native Python runtime structure.

## [1.0.1] — 2026-03-08

### Added — Comprehensive Framework Audit (Phases 1–15)

#### Core & Server (Phases 1–6)
- Full security audit of `aquilia/server.py`, `aquilia/engine.py`, `aquilia/flow.py`, `aquilia/middleware.py`
- Hardened `aquilia/request.py` and `aquilia/response.py` against header injection and content-type attacks
- Hardened `aquilia/asgi.py` ASGI lifecycle handling

#### Dependency Injection (Phase 7)
- Security audit of `aquilia/di/` — scope isolation, cycle detection, provider resolution
- Fixed potential DI graph leaks across request boundaries

#### Auth System (Phase 8)
- Comprehensive audit of `aquilia/auth/` — JWT, session, MFA, OAuth, RBAC
- Hardened token lifecycle, password hashing (Argon2), CSRF protection
- Fixed clearance level escalation edge cases in `aquilia/auth/clearance.py`

#### Controller System (Phase 9)
- Audit of `aquilia/controller/` — routing, filters, pagination, factory
- Secured filter/pagination against injection and overflow attacks

#### Sessions (Phase 10)
- Audit of `aquilia/sessions/` — store, transport, engine
- Hardened session fixation protection and cookie security flags

#### Contracts (Phase 11)
- Audit of `aquilia/contracts/` — annotations, facets, core, integration
- Secured contract registration against namespace collisions

#### ORM & Models (Phase 12)
- Comprehensive audit of `aquilia/models/` — query builder, fields, transactions, migrations
- Parameterized all raw SQL paths, field name validation, safe deletion cascades
- Protected against SQL injection in expression engine and lookup system

#### Admin Module (Phase 13)
- Deep security audit of `aquilia/admin/` — controller, site, registry, permissions, inlines, templates
- Created `aquilia/admin/security.py` with CSRF, rate-limiting, input validation, audit logging
- Role-based permission enforcement across all admin endpoints

#### Admin Fault Migration & Subsystem Integration (Phase 14)
- Replaced all raw exceptions in `aquilia/admin/` with structured `Fault` subclasses
- Created `aquilia/admin/faults.py` with `ADMIN_DOMAIN` and 7 fault classes
- Created `aquilia/admin/subsystems.py` integrating cache/effects/tasks/flow/lifecycle
- Added admin-specific config builders to `aquilia/config_builders.py`

#### Tasks, Storage & Templates — Fault Migration & Security (Phase 15)
- **Tasks**: Created `aquilia/tasks/faults.py` with `TASKS_DOMAIN`, `TaskScheduleFault`, `TaskNotBoundFault`, `TaskEnqueueFault`, `TaskResolutionFault`
- **Storage**: Converted `StorageError` hierarchy to inherit from `Fault` with `STORAGE_DOMAIN`; added `StorageIOFault`, `StorageConfigFault`
- **Templates**: Created `aquilia/templates/faults.py` with `TEMPLATE_DOMAIN`, `TemplateEngineUnavailableFault`, `TemplateCacheIntegrityFault`
- **Fault core**: Registered 3 new standard domains — `STORAGE`, `TASKS`, `TEMPLATE` on `FaultDomain`

### Changed

- `aquilia/faults/core.py` — added `FaultDomain.STORAGE`, `FaultDomain.TASKS`, `FaultDomain.TEMPLATE` standard domains
- `aquilia/storage/base.py` — `StorageError` now inherits from `Fault` (was `Exception`)
- `aquilia/storage/__init__.py` — exports `StorageIOFault`, `StorageConfigFault`, `STORAGE_DOMAIN`
- `aquilia/tasks/__init__.py` — exports all task fault classes
- `aquilia/templates/__init__.py` — exports all template fault classes
- Bytecode cache schema version bumped from `1.0` to `1.1` (JSON+HMAC format)

### Security Fixes

- **CRITICAL**: Eliminated unsafe `pickle.load()` deserialization in `templates/bytecode_cache.py` and `templates/manager.py` — replaced with HMAC-verified JSON (SHA-256)
- **HIGH**: Hardened `storage/base.py._normalize_path()` — rejects null bytes (`\x00`), `..` traversal segments, paths >1024 chars
- **HIGH**: Task `func_ref` resolution in `tasks/engine.py` now only resolves via the registered `@task` registry (allowlist), preventing arbitrary code execution
- **MEDIUM**: Added deprecation warning to regex-based `sanitize_html()` in `templates/security.py`
- **MEDIUM**: ORM parameterized queries and field name validation against SQL injection
- **MEDIUM**: Session fixation protection and secure cookie flags
- **LOW**: Auth token rotation hardening, CSRF double-submit validation

### Tests

- **5,085 total tests passing** (up from baseline), 0 failures
- `tests/test_phase14_faults_subsystems.py` — 118 tests (admin faults + subsystem integration)
- `tests/test_phase15_faults_security.py` — 120 tests (fault migration + security audit)
- `tests/test_admin_security.py` — admin security regression tests
- `tests/test_contract_security.py` — contract security tests
- `tests/test_orm_security.py` — ORM injection and security tests
- `tests/test_session_security.py` — session security tests
- `tests/test_integration_wiring.py` — cross-subsystem integration tests
- Updated existing tests to expect new `Fault` types instead of raw exceptions

## [1.0.0] — Initial Release

### Added

- Manifest-First Architecture implementation (`AppManifest`)
- Scoped Dependency Injection framework targeting Singleton, App, and Request contexts.
- Async-Native core using Uvicorn and ASGI specifications.
- Foundation for Integrated MLOps (Artifact Registry, Lineage Tracing, Shadow Deployments).
- Core subsystems: Flow (routing), Faults (error handling), and essential services.
