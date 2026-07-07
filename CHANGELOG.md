# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0b1] — 2026-07-07 — "Ironclad Anchor" (beta)

### Fixed
- **Type inference for `Model.related(name)`**: Added `@overload` signatures to `related()`, enabling IDE autocomplete on related field model attributes (e.g. `await token.related("user", UserModel)`) without manual casting.
- **Instance manager access error handling**: Replaced bare `AttributeError` when attempting to access class-level managers on model instances (e.g. `user.objects.all()`) with a structured `ManagerInstanceAccessFault` (subclassing both `ModelFault` and `AttributeError` for backward compatibility).
- **ORM field `sql_type()` error handling**: Replaced `NotImplementedError` raised in custom field classes missing `sql_type()` implementations with a structured `SchemaFault`.
- **Migration DSL error handling**: Replaced `NotImplementedError` raised when attempting to mechanically reverse irreversible migration operations (like `DropModel` and `RemoveField` rollbacks) with a structured `MigrationFault`.
- **Dependency Injection error handling**: Migrated `DIError` and all its subclasses in `aquilia/di/errors.py` to subclass `DIFault` and participate fully in the Aquilia structured fault handling system, capturing rich diagnostics in metadata.
- **DI CLI missing settings error handling**: Replaced `FileNotFoundError` raised when a settings file is missing during CLI loader setup with `ConfigMissingFault`.
- **Configuration validation error handling**: Changed `ConfigError` in the configuration loader to inherit from `ConfigFault`.
- **Blueprint sync/async validation mismatch error handling**: Replaced `RuntimeError` raises for async ward validation sync mismatch with a structured `BlueprintAsyncMismatchFault` (inheriting from `BlueprintFault` and `RuntimeError`).
- **Blueprint migration error handling**: Replaced raw `ValueError` raised during missing blueprint migration path in `Sigil` validation with a proper validation error response dictionary, preventing unhandled 500 errors on invalid client inputs.
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

### Added
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

### Testing
- New `tests/test_orm_transactions_atomic.py`: reproduces the original report exactly
  (`select_related().filter().first()` before `atomic()`, two `.save()` calls inside it), plus
  commit/rollback, nested savepoints (commit and partial rollback), `durable=True` nesting
  rejection, `on_commit`/`on_rollback` hook scoping, two concurrent `asyncio.Task`s each committing
  independently, the decorator form, `readonly=True` non-contention with a concurrent writer,
  `timeout=` expiry, and `asyncio.CancelledError` mid-transaction rollback.

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

### Testing
- New `TestForeignKeyDescriptor` in `tests/test_related_not_loaded_and_reverse_manager.py`: class-level
  access still returns the `Field` object (not `None`/`AttributeError`), instance-level get/set
  round-trips a real model instance, and hydrated vs. unhydrated instance access resolve to the
  hydrated instance vs. the `RelatedNotLoaded` sentinel respectively — confirms the descriptor swap
  is behaviorally transparent. Full existing suite (6600+ tests, `tests/
  test_related_not_loaded_and_reverse_manager.py` in particular, which exercises `RnlBook.author`
  extensively) passes unchanged.

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

### Fixed
- **Non-Integer Foreign Key Primary Keys**: `ForeignKey.validate()`, `to_db()`, and `sql_type()` (`aquilia/models/fields_module.py`) previously hardcoded an `int` primary key, and never unwrapped a related `Model` instance to its `.pk` — assigning a related instance directly (e.g. `Verification(user=some_user)`) or pointing a FK at a UUID/str-keyed model raised `FieldValidationError: Expected integer FK, got <TypeName>` on save/validate. All three now resolve the related model's actual primary-key field and delegate type coercion/conversion to it, falling back to the previous int-cast only when the related model can't be resolved. `schema_snapshot.py`'s `_field_to_sql_type()` (the function driving `makemigrations`) had the same independent `INTEGER`-for-every-FK hardcode and is fixed the same way, so migrations for FK columns pointing at non-integer-PK models now generate the correct column type instead of `INTEGER`.
- **`OneToOneField` Dropped Constructor Kwargs**: `OneToOneField.__init__` re-declared `ForeignKey`'s parameter list without `related_name`/`on_delete`/`on_update`/`db_constraint`, so those were always silently discarded regardless of what a caller passed. It also never actually defaulted `unique=True` (the `kwargs.setdefault("unique", True)` was dead code — `unique` was always already present in the dict from the `unique: bool = False` parameter default). Both are fixed: all `ForeignKey` kwargs are now forwarded, and `unique` correctly defaults to `True`.
- **UUID/Non-Primitive Primary Key Lookups Crashing**: `Model.get(pk=...)` (`aquilia/models/base.py`) and `Q.filter()`/`Q.exclude()` (`aquilia/models/query.py`) bound raw Python values (e.g. a `uuid.UUID` instance) straight into the SQL driver without running them through the owning field's `to_db()`, raising `QueryFault: ... Error binding parameter ... type 'UUID' is not supported` for any lookup on a UUID (or other non-primitively-bindable) field/FK — including the read path (`related()`) behind the FK fixes above. Both now convert filter values through the resolved field's `to_db()` (mirroring the conversion `update()` already applied to SET values), restricted to pure value-comparison lookups (`exact`, `ne`, `in`, `range`, `gt`/`gte`/`lt`/`lte`) so pattern/boolean/date-part lookups (`contains`, `isnull`, `year`, etc.) are left untouched.
- **Admin Bulk-Action CSRF Crash**: `bulk_action()`'s "Delete selected"/bulk-action endpoint (`aquilia/admin/controller.py`) parses its form with `multi=True` to preserve the repeated `selected` checkbox field as a list — which incidentally wrapped the singular `_csrf_token` field in a list too. `AdminCSRFProtection.validate_request()` then called `.encode()` directly on it, crashing every bulk action (including "Delete selected") with `AttributeError: 'list' object has no attribute 'encode'`. `validate_request()` now coerces a list-valued token to its first element before comparison.
- **Stale Manifest Import Paths Never Resynced**: Restructuring a module file into a package (e.g. `modules/auth/models.py` → `modules/auth/models/register.py`) permanently broke `aq discover`/workspace validation. Two compounding bugs in `aquilia/discovery/engine.py`'s `ManifestDiffer`: `_is_declared()` treated any existing manifest ref with a matching class name — regardless of its actual dotted path — as "already declared," so the newly-discovered correct path never generated an `add` action; and the removal loop's `is_moved` guard then also suppressed removing the stale entry. `_is_declared()` now only matches on the exact import path, so a moved class correctly produces an `add` action, which `ManifestWriter._add_component`'s existing class-name-match rewrite logic then applies in place. `_validate_workspace_config()` (`aquilia/cli/commands/run.py`) also only ever checked `<path>.py` when resolving a manifest's dotted import path, so it falsely reported package-style modules (a directory with `__init__.py`) as "file not found" — it now also accepts the package form.
- **`discover_patterns` Was Dead Config**: A module's `discover_patterns` (declared in `manifest.py`, e.g. `["controllers", "services", "models", ...]`) was parsed but never passed into the scanner, and `FileScanner.scan_module()`'s pattern filter only matched a file's bare stem — so a pattern like `"models"` never matched a nested `models/register.py` (stem `"register"`) even once wired up. `discover_patterns` is now read from each module's manifest and passed through to scanning, and the filter matches any path component (directory names as well as the file stem) relative to the module directory.
- **DI Explicit Tag Resolution ("provider not found")**: `Inject(SomeService, tag="...")` raised `ProviderNotFoundFault` even when `SomeService` was correctly registered, because the class-provider registration path (`aquilia/aquilary/core.py:_register_services`) only read a tag from a `@service(tag=...)` class decorator, never from the manifest entry itself, while `aquilia/di/core.py:Registry._load_manifest_services` never propagated a `tags=` value to `ClassProvider` at all. Both paths registered providers under an untagged key while tagged `Inject(...)` calls looked them up under a tagged key. Both now resolve the tag from the manifest entry first, falling back to the class decorator.
- **SMTP/SES/SendGrid Auth Silently Dropped**: `MailService._create_provider()` never read a provider's nested `auth` dict (the shape produced by `MailAuth.plain(...)` / `Integration.MailAuth.plain(...)`), only flat `username`/`password` fields — so any provider configured with per-provider `auth=` connected and sent unauthenticated, surfacing as `(530, '5.7.0 Authentication Required...')` from Gmail and equivalent rejections from other SMTP hosts. Credentials are now read with correct precedence: explicit flat fields → nested `auth` block → `config` dict; the same fix applies to SES's `aws_access_key_id`/`aws_secret_access_key` and SendGrid's `api_key`.
- **Provider-Specific Config Fields Silently Dropped**: `ProviderConfigBlueprint` (`aquilia/mail/config.py`) ignored any provider field not in its small declared schema, so SES's `region`/`configuration_set`, SendGrid's `sandbox_mode`, File's `max_files`, and similar provider-specific options vanished before ever reaching the real provider constructor. `_validate_provider()` now folds unrecognized top-level fields into the provider's `config` dict instead of silently discarding them.
- **`MailAuth.api_key` Field/Classmethod Collision**: The `api_key` dataclass field on `MailAuth` collided with the `api_key()` classmethod defined in the same class body, so the field's default silently resolved to the bound classmethod instead of `None` for every `MailAuth` built without an explicit `api_key=` — corrupting `to_dict()` output (e.g. `Integration.MailAuth.anonymous().to_dict()` incorrectly included an `"api_key"` entry). The field is now stored internally as `api_key_value`; the public `to_dict()` key remains `"api_key"`.
- **Real Mail Provider Compatibility**: Real provider instances imported from `aquilia.mail` (like `SMTPProvider`, `ConsoleProvider`, `FileProvider`, `SESProvider`, `SendGridProvider`) previously lacked a `to_dict()` method, so they were dropped by `MailIntegration.to_dict()`, leaving the configured providers list empty and raising `No mail providers configured` (`MAIL_CONFIG_ERROR`) at runtime. Added a standard `to_dict()` to all five real provider classes that serializes all constructor-supplied fields and config parameters.
- **`Integration.admin` Legacy Flat Options Compatibility**: Restored support for flat legacy properties passed to `Integration.admin(**kwargs)` (such as `enable_*`, `disable_*`, `audit_*`, `monitoring_*`, `sidebar_sections`). The method now resolves, maps, and constructs the corresponding nested builder objects (`AdminModules`, `AdminAudit`, `AdminMonitoring`, `AdminSidebar`) transparently while correctly prioritizing explicitly-passed builder instances over flat parameter overrides.
- **Admin Configuration Builders & Fluent Properties**: Custom `LegacyFluentMixin.__getattribute__` now detects active function call bytecode sequences dynamically at runtime via scan-forward frame inspection. This allows properties/attributes on `AdminAudit`, `AdminMonitoring`, and `AdminSecurity` to correctly resolve to their raw primitive values for direct comparisons (supporting assertions like `is True`/`is False` in older test cases) while still correctly wrapping them in fluent `CallableBool`/`CallableInt`/`CallableStr`/`CallableList` builders when invoked as methods. `AdminModules` also implements a synchronized dual-write `__setattr__`/`__post_init__` pattern keeping the internal `_mailer` and `_testing` slots aligned with their dataclass counterparts.
- **Admin Security & Monitoring Bounds Clamping**: Added robust post-initialization and attribute setter validation checks to `AdminSecurity` and `AdminMonitoring` ensuring that custom integer configuration properties (such as `csrf_max_age`, `csrf_token_length`, `rate_limit_max_attempts`, `rate_limit_window`, `password_min_length`, `event_tracker_max_events`, `refresh_interval`) are strictly clamped to their required minimum bounds.
- **Database Integration Default Connection String**: Corrected default database connection string in `Integration.database()` to `sqlite:///db.sqlite3` to align with the framework's test expectations and fallback behavior.

### Changed
- **Mail Integration Consolidation**: Removed three redundant, independently-drifting declarations of the same provider config fields (`aquilia/integrations/_legacy.py`'s `Integration.MailProvider.*`, `aquilia/integrations/mail.py`'s `SmtpProvider`/`SesProvider`/`SendGridProvider`/`ConsoleProvider`/`FileProvider` dataclasses, and `aquilia/mail/config.py`'s Blueprint schema). `SmtpProvider`, `SesProvider`, `SendGridProvider`, `ConsoleProvider`, `FileProvider`, and `Integration.MailProvider.*` are now thin wrappers around the real `aquilia.mail.providers` classes — field names and defaults live in exactly one place (the real provider `__init__`). `MailAuth` moved to `aquilia.mail.auth` as the single canonical implementation, re-exported from both `aquilia.integrations.mail` and `aquilia.integrations.Integration.MailAuth`. As part of this consolidation, Console/File provider builders' default `rate_limit_per_min` changed from a special-cased `10000` to the standard `600` shared by all provider types.
- **Legacy Integration System Removal**: Removed the monolithic `aquilia/integrations/_legacy.py` configuration builder shim entirely. Replaced it with a lightweight, typed wrapper `aquilia/integrations/integration.py` that retains identical public static methods (e.g. `Integration.mail()`, `Integration.admin()`, etc.) but delegates internally to the corresponding typed dataclasses and leverages runtime reflection to filter fields and merge arbitrary `**kwargs` cleanly.

## [1.2.3] — 2026-07-01 — "Kraken's Wake"

### Added
- **Automatic Port Switching**: Added a production-grade, internal port auto-switching fallback mechanism to development and production server run sequences. If the configured port is already occupied, the server automatically scans and binds to the next sequential available port (up to 100 attempts) and logs a warning message detailing the switch, preventing address-already-in-use startup crashes.

### Performance
- **SQLite Double Thread-Pool Hop**: Merged `AsyncConnection.execute`/`execute_many`/`fetch_all`/`fetch_one` in `aquilia/sqlite/_connection.py` from two separate `run_in_executor` dispatches (one for `execute`/`executemany`, a second for `fetchone`/`fetchall`/`commit`) into a single combined thread-pool hop per call, cutting per-query thread-dispatch overhead roughly in half. Measured **+16% req/s on db_single, +18% on db_queries, +9% on db_updates** benchmark scenarios.

### Fixed
- **Multi-Database `.using(alias)` Silent No-Op**: `Q.using()` / `Manager.using()` / `Model.using()` previously recorded the alias but never resolved it to an actual connection, so every query silently executed against the default database regardless of the alias passed. `Q.using()` now resolves the alias via `get_database(alias)` immediately and rebinds the queryset, raising `DatabaseConnectionFault` for unknown aliases instead of failing silently.
- **Silent Data Corruption on `only()`/`defer()` Field Access**: Accessing a field excluded via `only()`/`defer()` previously leaked the raw class-level `Field` metadata object (or, in a naive fix, would have silently returned `None`, indistinguishable from a real database `NULL`). Instances with deferred fields now have their class swapped to a small cached guard subclass that raises `DeferredFieldAccessFault` (a subclass of `AttributeError`, so `getattr(obj, name, default)` call sites like dirty-field tracking and `to_dict()` still degrade to *default* as before) on direct access. Fully-loaded instances are completely unaffected and incur zero extra overhead. `refresh()`/`refresh_from_db()` correctly clears the guard once all fields are loaded.
- **Non-Transactional Cascade Delete**: `Model.delete_instance()`'s reverse-FK cascade loop (potentially several DELETE/UPDATE statements across related tables) and the final row delete now run inside a single `AquiliaDatabase.transaction()`, so a failure partway through (e.g. a `PROTECT` check on a later table) rolls back any earlier `CASCADE`/`SET_NULL` steps instead of leaving the database partially cascaded.
- **`_DepthHolder` Weak-Reference Crash**: Fixed `aquilia/models/transactions.py`'s `_DepthHolder.__slots__` omitting `__weakref__`, which raised `TypeError: cannot create weak reference` the moment `atomic()`'s per-task depth tracker (`WeakValueDictionary`) was actually entered via `async with atomic(): ...` inside a running event loop task.
- **Empty Blueprint AttributeError**: Fixed an early-return check in `BlueprintMeta.__new__` that skipped schema and projections compilation for subclasses with no fields/model, preventing `AttributeError` when validating empty or dynamically declared blueprints.
- **Strict `class Meta` Rejection**: Hardened blueprint definitions to raise a `BlueprintFault` during class initialization if Django/DRF-style `class Meta` is defined, forcing the use of `class Spec` to avoid collisions with Model Meta metadata.
- **Automatic Class-Attribute Blueprint Nesting**: Automatically wrap assigned `Blueprint` subclasses to class attributes (e.g., `name = UserNameBlueprint`) inside a `NestedBlueprintFacet` during metaclass creation.
- **ORM Schema Creation with Expressions**: Skip expression-based unique constraints in `generate_create_table_sql()` and instead generate them as separate `CREATE UNIQUE INDEX` statements in `generate_index_sql()`, preventing database engines (SQLite, Postgres, etc.) from raising `expressions prohibited in PRIMARY KEY and UNIQUE constraints`.
- **Migration Constraint Translation**: Updated `AddConstraint` to compile expression-based unique constraints (containing function calls/expressions) into `CREATE UNIQUE INDEX` statements for all database dialects (SQLite, Postgres, MySQL, Oracle).
- **Strict Safe-DB Startup Guard**: Hardened the startup sequence to raise a `SchemaFault` and immediately halt the server startup if the database is missing or unapplied migrations exist when migrations are present in the project.
- **Registry Route Prefix Validation**: Accept and utilize `workspace_modules` configuration overrides inside `RegistryValidator.validate_manifests` and `_validate_route_conflicts` to correctly resolve module route prefixes during startup and CLI `validate`/`doctor` calls, preventing false-positive `RouteConflictError` crashes.
- **Outbound Blueprint Projection Overrides**: Removed raw inbound validated data serialization bypass from `Blueprint._to_dict_instance` to ensure wrapping/response blueprints correctly apply their own projection and write-only filters on nested or returned blueprint instances.
- **ORM Persistence and UUID Primary Keys**: Fixed `ImprintFault` causing programming errors ("type 'UUID' is not supported") on SQLite databases by ensuring all primary key bindings convert values via `field.to_db()` and restricting `lastrowid` assignment to integer-based AutoFields.
- **Computed Blueprint Fields**: Fixed `Computed.extract()` in computed facets to correctly bind the blueprint instance as `self` when executing unbound methods.
- **Admin Panel PK Resolution**: Resolved list view and record endpoint 404 errors by dynamically resolving primary key field names using `model_cls._pk_attr` instead of hardcoding `id`.
- **Nested Blueprint Facet Typing**: Added generic parameterization to `Blueprint[ModelT]` and updated `imprint` overload signatures to enable IDE autocomplete for imprinted model instances.
- **Empty Datetime and Format Coercion**: Handled empty string inputs (`""`) gracefully in `to_python` and `validate` methods for `DateTimeField`, `DateField`, `TimeField`, `UUIDField`, and `DecimalField` (coercing them to `None` for nullable fields), resolving the `Invalid isoformat string` and parsing errors in the admin panel edit forms.
- **ORM `blank=True, null=False` String Field Coercion**: Coerced `None` input to empty string `""` for string-based fields (`CharField`, `TextField`, `GenericIPAddressField`, etc.) when `blank=True` and `null=False` to prevent database `NOT NULL` integrity constraint errors, adhering to standard ORM validation conventions.
- **Insert Query NOT NULL Inclusion**: Ensured `Model.save()`'s INSERT query builder always includes columns defined as `NOT NULL` even if their value is `None` at Python-level, enabling proper database-level constraint enforcement and/or field coercion.

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
- **Test Generation**: Added `Blueprint.example()` for random schema-valid dictionary generation, and `Blueprint.strategy()` for Hypothesis integration.
- **Discriminated Unions (`BlueprintUnion`)**: Support concrete type union validation (e.g. `Circle | Square`) with automated Literal or explicit `Spec.discriminator` dispatching.
- **Form & File Uploads via Blueprints (`UploadFile` and `FormData`)**: Added first-class support for explicit and implicit file uploads and form inputs in Blueprints. Support includes single/multiple/optional file uploads, custom content types, size limits, primitive type castings, and nested blueprints for form/multipart data validation.
- **Unified Request Input Resolution**: Centralized query parameters, cookies, path parameters, headers, and request bodies into a unified resolution layer (`extract_value_from_request`).
- **Standardized DI Parameter Casting & New Facets**: Equipped RequestDAG and controller engine to dynamically resolve and cast parameters using `SetFacet`, `TupleFacet`, `EnumFacet`, and `BoolFacet` validation rules. Added `Cookie(...)` and `Path(...)` extraction support.
- **Click-based Aquilary CLI commands**: Added the `aquilary` CLI group under the `aq` main tool, providing native `validate`, `inspect`, `freeze`, `graph`, and `run` subcommands.
- **Aquilary CLI test coverage**: Added automated test coverage for the Click-based aquilary commands in `tests/test_aquilary_cli.py`.

### Removed
- **Artifact System**:
  - Entirely removed the redundant `aquilia.artifacts` module (`core`, `builder`, `reader`, `kinds`, `store`).
  - Removed `compile` and `freeze` commands from the CLI as the core ASGI server runtime is manifest-driven and does not require pre-compiled artifacts.
  - Rewrote `aq ws inspect` and `aq ws gen-client` to statically introspect workspace socket controllers in real-time in memory instead of relying on compiled `ws.surp` artifact files.

### Changed
- **Database Introspection and Migration Rollback**:
  - Enhanced `create_snapshot_from_db` to map tables back to namespaced codebase model class names, resolve field `max_length` constraints from sql column types using regex, and align serialization constraints with codebase model snapshots.
  - Upgraded `MigrationRunner` rollback execution to support target revision `"zero"`, reverting all applied migrations in chronological order.
- **Scaffolding Integration API migration**:
  - Updated workspace generator to generate templates utilizing the new type-safe, validated integrations API (`aquilia/integrations/*`) instead of the legacy `Integration` config helper.
- **Boilerplate reduction and scaffolding cleanup**:
  - Removed generation of redundant files (`Makefile`, `.editorconfig`, `Dockerfile`, `docker-compose.yml`) from default workspace scaffolding.
  - Eliminated automatic generation of empty directories (`locales`, `templates`, `assets`, `artifacts`) to keep new workspaces lightweight.
  - Switched generated module controllers to automatically use input validation blueprints instead of parsing bodies with raw `ctx.json()`.
- **Zero Runtime Dependencies**: Completely migrated the Blueprints validation engine to pure-Python using only Python standard library modules.
- **Deep Performance Optimizations**:
  - Implemented lazy nested wrapping in `DataObject` to eagerly wrap items only when accessed, caching the result.
  - Extracted dynamically-compiled wrapper classes in `wrap_callable_attribute` to module scope.
  - Cached compiled regexes, sigil validations, and pre-loaded types at module-level in `sigil.py`.
  - Replaced manual sigil validation in request blueprint binding with direct `bp.is_sealed` lookup and validation caching.
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
- **Dependency Precedence over Request Body**: Fixed parameter source classification and binding to ensure that explicit `Dep(...)` declarations (such as `param: T = Dep(callable)`) take precedence over implicit source type-based classification (such as `Blueprint subclass` → `source="body"`). Explicit dependency parameters are now correctly classified as `source="dep"` and resolved via `RequestDAG`, preventing request body payloads from overriding the dependency results.
- **Multiple Blueprint Parameter Support**: Fixed parameter binding and validation to support multiple blueprint parameters in a single handler. Resolves all blueprint arguments from the same request body, supports async validation via `is_sealed_async` when available, and consolidates validation errors across all blueprints into a single unified `SealFault`. Also added `BlueprintContext` and `LazyServiceProxy` to enable blueprints to lazily resolve and invoke DI container services via `self.context[key]`.
- **String Annotation Evaluation (PEP 563)**: Fixed annotation parsing inside `_safe_resolve_annotation` to prevent incorrect splitting of PEP 604 unions (e.g. `str | None`) when they are nested inside generic subscripts (like `Annotated[str | None]`). Improved resolution by attempting `eval()` within the `AutoResolveMapping` namespace before falling back, enabling robust resolution of complex pipeline operator `>>` expressions.
- **Ward execution attribute collision**: Resolved validation crash when using `@ward` methods on models with fields named `items`, `keys`, `values`, `get` or other dictionary method names. Overrode `__getattribute__` on `DataObject` to prioritize dictionary keys over class-level dictionary methods.
- **Union schema generation crash**: Corrected literal constraint schema generation for unions (e.g. `Circle | Square`) which crashed with a `TypeError: 'set' object is not subscriptable`. Changed `ChoiceFacet.allowed_values` property to return an ordered `tuple` of keys rather than an unordered `set`.
- **Serialization failure in `to_dict` and `to_dict_many`**: Fixed `to_dict()` and `to_dict_many()` serialization to work correctly when called as class methods (e.g. `Blueprint.to_dict(instance)`) and support inbound validated data mapping (when `instance` is None) on `many=True` and `many=False` blueprints. Implemented `BlueprintSerializationDescriptor` to cleanly route class-level vs instance-level method calls.
- **Form URL Encoded & Multipart Blueprint validation**: Resolved critical validation failure where blueprints bound to form or multipart request payloads lost all fields because the validation engine strictly checked `isinstance(data, dict)`. Blueprints and `Sigil` validation now support mapping-like objects (such as `FormData` and `MultiDict`).
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

### Removed
- Removed `aquilia/config_builders.py` — the 5420-line god-file has been deleted.

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

### Removed
- Removed aquilia/mlops/ in its entirety
- Removed duplicate aquilia/aquilia_mcp/ package (canonical is aquilia.mcp)
- Removed AMDL DSL: parser, AST nodes, __init__old.py, AMDLParseFault
- Removed aquilia/patterns/lsp/ Language Server Protocol server

### Changed
- URL pattern documentation: guillemet delimiters replaced with brace syntax {id:int}
- Moved ruff from dependencies to [dev] optional extra
- Moved asyncpg from dependencies to new [postgres] optional extra
- Fixed broken GitHub URLs (axiomchronicles → tubox-labs)

### Added
- aquilia/sse/ — Server-Sent Events: SSEEvent, SSEResponse, json/text stream helpers
- aquilia/otel/ — OpenTelemetry: OTelConfig, OTelMiddleware, no-op fallback
- aquilia/controller/validation.py — @validate_body(BlueprintClass) decorator
- aquilia/sqlite/_config.py — SqlitePoolConfig with full parameter surface
- New [postgres] optional extra (asyncpg)
- New [otel] optional extra (opentelemetry-*)

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

### Removed
- Removed the React-style `aquilia/build` package and the `aq build` command.
- Removed automatic build-gating from `aq run`, `aq serve`, and `aq deploy`; runtime and deploy generation now use native workspace loading and live introspection.
- Removed the Admin Build page, `/admin/build/` route, sidebar/search links, and `AdminModules.build` configuration surface.

### Changed
- `aq compile` now writes explicit artifacts through `WorkspaceCompiler` without depending on a build pipeline.
- `aq freeze` now creates an integrity snapshot for generated artifacts under `artifacts/`.
- Deployment Makefile generation now calls `python -m aquilia.cli compile`.

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

#### Blueprints (Phase 11)
- Audit of `aquilia/blueprints/` — annotations, facets, core, integration
- Secured blueprint registration against namespace collisions

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

### Security Fixes
- **CRITICAL**: Eliminated unsafe `pickle.load()` deserialization in `templates/bytecode_cache.py` and `templates/manager.py` — replaced with HMAC-verified JSON (SHA-256)
- **HIGH**: Hardened `storage/base.py._normalize_path()` — rejects null bytes (`\x00`), `..` traversal segments, paths >1024 chars
- **HIGH**: Task `func_ref` resolution in `tasks/engine.py` now only resolves via the registered `@task` registry (allowlist), preventing arbitrary code execution
- **MEDIUM**: Added deprecation warning to regex-based `sanitize_html()` in `templates/security.py`
- **MEDIUM**: ORM parameterized queries and field name validation against SQL injection
- **MEDIUM**: Session fixation protection and secure cookie flags
- **LOW**: Auth token rotation hardening, CSRF double-submit validation

### Changed
- `aquilia/faults/core.py` — added `FaultDomain.STORAGE`, `FaultDomain.TASKS`, `FaultDomain.TEMPLATE` standard domains
- `aquilia/storage/base.py` — `StorageError` now inherits from `Fault` (was `Exception`)
- `aquilia/storage/__init__.py` — exports `StorageIOFault`, `StorageConfigFault`, `STORAGE_DOMAIN`
- `aquilia/tasks/__init__.py` — exports all task fault classes
- `aquilia/templates/__init__.py` — exports all template fault classes
- Bytecode cache schema version bumped from `1.0` to `1.1` (JSON+HMAC format)

### Tests
- **5,085 total tests passing** (up from baseline), 0 failures
- `tests/test_phase14_faults_subsystems.py` — 118 tests (admin faults + subsystem integration)
- `tests/test_phase15_faults_security.py` — 120 tests (fault migration + security audit)
- `tests/test_admin_security.py` — admin security regression tests
- `tests/test_blueprint_security.py` — blueprint security tests
- `tests/test_orm_security.py` — ORM injection and security tests
- `tests/test_session_security.py` — session security tests
- `tests/test_integration_wiring.py` — cross-subsystem integration tests
- Updated existing tests to expect new `Fault` types instead of raw exceptions

## [1.0.0] - Initial Release

### Added
- Manifest-First Architecture implementation (`AppManifest`)
- Scoped Dependency Injection framework targeting Singleton, App, and Request contexts.
- Async-Native core using Uvicorn and ASGI specifications.
- Foundation for Integrated MLOps (Artifact Registry, Lineage Tracing, Shadow Deployments).
- Core subsystems: Flow (routing), Faults (error handling), and essential services.
