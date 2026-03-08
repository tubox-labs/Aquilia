# Aquilia Framework — Source Code Research Report

> **Directories scanned:** `discovery/`, `faults/`, `i18n/`, `mail/`, `middleware_ext/`  
> **Total files:** 43 Python files  
> **Total lines:** ~14,600

---

## Table of Contents

1. [discovery/](#1-discovery)
2. [faults/](#2-faults)
3. [i18n/](#3-i18n)
4. [mail/](#4-mail)
5. [middleware_ext/](#5-middleware_ext)

---

## 1. discovery/

### 1.1 `aquilia/discovery/__init__.py` — 52 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `PackageScanner` (from `..utils`), everything from `.engine` |
| **Classes** | — |
| **Standalone Functions** | — |
| **Design Patterns** | Re-export façade |
| **Security** | — |

**Exports:** `PackageScanner`, `AutoDiscoveryEngine`, `ASTClassifier`, `FileScanner`, `ManifestDiffer`, `ManifestWriter`, `ClassifiedComponent`, `DiscoveryResult`, `SyncAction`, `SyncReport`

---

### 1.2 `aquilia/discovery/engine.py` — 674 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `ast`, `logging`, `re`, `pathlib.Path`, `dataclasses`, `..manifest.ComponentKind` |
| **Design Patterns** | Pipeline (FileScanner → ASTClassifier → ManifestDiffer → ManifestWriter), Dataclass-centric value objects |
| **Security** | **AST-only analysis — never executes scanned code.** Safe for untrusted modules. |

#### Classes

| Class | Type | Methods / Properties |
|-------|------|---------------------|
| `ClassifiedComponent` | `@dataclass` | Fields: `name`, `kind`, `file_path`, `line`, `import_path`, `bases`, `decorators` |
| `DiscoveryResult` | `@dataclass` | Fields: `module_name`, `components`, `errors`, `files_scanned`; Properties: `controllers`, `services`, `middleware`, `guards`, `models`, `pipes`, `interceptors` |
| `SyncAction` | `@dataclass` | Fields: `action` (`"add"`/`"remove"`), `component`, `field_name` |
| `SyncReport` | `@dataclass` | Fields: `module_name`, `manifest_path`, `actions`, `dry_run`; Properties: `added`, `has_changes` |
| `ASTClassifier` | class | `classify_file(path)`, `_classify_class(node)`, `_extract_base_names(node)`, `_extract_decorator_names(node)`; Class attrs: `CONTROLLER_BASES`, `SERVICE_BASES`, `MIDDLEWARE_BASES`, `GUARD_BASES`, `MODEL_BASES`, `PIPE_BASES`, `INTERCEPTOR_BASES` + corresponding `_DECORATORS` sets |
| `FileScanner` | class | `scan_module(module_path)`, `discover_modules(modules_dir)`; `SKIP_FILES`, `SKIP_PREFIXES` |
| `ManifestDiffer` | class | `diff(module_name, manifest_path, result)`, `_is_declared(manifest_data, component)`; `KIND_TO_FIELD` mapping |
| `ManifestWriter` | class | `write_sync_actions(manifest_path, actions)`, `_add_component(content, action)`; Regex-based manifest.py file manipulation |
| `AutoDiscoveryEngine` | class | `discover(module_path)`, `discover_all(modules_dir)`, `sync_manifest(module_path)`, `sync_all(modules_dir)`, `_compute_import_path(file_path, module_path)`, `_parse_manifest_refs(manifest_path)` |

---

## 2. faults/

### 2.1 `aquilia/faults/__init__.py` — 112 lines

| Item | Detail |
|------|--------|
| **Key Imports** | Re-exports from `.core`, `.handlers`, `.default_handlers`, `.domains`, `.engine` |
| **Classes** | — |
| **Standalone Functions** | — |
| **Design Patterns** | Re-export façade |
| **Security** | — |

---

### 2.2 `aquilia/faults/core.py` — ~340 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `enum`, `dataclasses`, `hashlib`, `time`, `uuid`, `traceback`, `typing` |
| **Design Patterns** | Value objects (frozen dataclasses), Union types for algebraic result (`FaultResult = Resolved | Transformed | Escalate`), Operator overloading (`__rshift__` for fault chaining) |
| **Security** | **`_hash_identifier()` hashes sensitive identifiers with SHA-256**; `public` flag controls whether fault details leak to clients; `fingerprint()` for dedup uses SHA-256 |

#### Classes

| Class | Type | Methods / Properties |
|-------|------|---------------------|
| `Severity` | `str, Enum` | `INFO`, `WARN`, `ERROR`, `FATAL`; aliases `LOW`/`MEDIUM`/`HIGH`/`CRITICAL` |
| `FaultDomain` | custom class | `name`, `value`, `description`; classmethod `custom(name, value, desc)`. Singletons: `CONFIG`, `REGISTRY`, `DI`, `ROUTING`, `FLOW`, `EFFECT`, `IO`, `SECURITY`, `SYSTEM`, `MODEL`, `CACHE` |
| `RecoveryStrategy` | `str, Enum` | `PROPAGATE`, `RETRY`, `FALLBACK`, `MASK`, `CIRCUIT_BREAK` |
| `Fault` | `Exception` | `__init__(code, message, domain, severity, retryable, public, metadata)`, `to_dict()`, `__rshift__(transform)`, `_hash_identifier(value)` |
| `FaultContext` | `@dataclass(slots=True)` | Fields: `fault`, `trace_id`, `timestamp`, `app`, `route`, `request_id`, `cause`, `stack`, `metadata`, `parent`; classmethod `capture(fault, **extras)`, `fingerprint()`, `to_dict()` |
| `Resolved` | `@dataclass(frozen=True)` | `response` |
| `Transformed` | `@dataclass(frozen=True)` | `fault`, `preserve_context` |
| `Escalate` | `@dataclass(frozen=True)` | (empty) |

**Type alias:** `FaultResult = Resolved | Transformed | Escalate`

---

### 2.3 `aquilia/faults/handlers.py` — ~170 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `abc.ABC`, `logging`, `typing`, `.core` classes |
| **Design Patterns** | **Chain of Responsibility** (handler chain), **Composite** (`CompositeHandler`), **Scoped Registry** (route → controller → app → global) |
| **Security** | — |

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `FaultHandler` | `ABC` | abstract `handle(ctx) → FaultResult`, abstract `can_handle(ctx) → bool` |
| `CompositeHandler` | `FaultHandler` | `__init__(handlers)`, `can_handle(ctx)`, `handle(ctx)` — tries handlers in order, returns first non-`Escalate` |
| `ScopedHandlerRegistry` | class | `_global`, `_app`, `_controller`, `_route` dicts; `register_global(handler)`, `register_app(app, handler)`, `register_controller(controller, handler)`, `register_route(route, handler)`, `get_handlers(app, controller, route) → List[FaultHandler]` — returns Route → Controller → App → Global order |

---

### 2.4 `aquilia/faults/default_handlers.py` — ~340 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `time`, `logging`, `typing`, `.core`, `.handlers.FaultHandler` |
| **Design Patterns** | Strategy pattern (each handler is a strategy), built-in exception mapping |
| **Security** | **`SecurityFaultHandler`: masks sensitive fault messages with generic text to prevent information leakage** |

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `ExceptionMapping` | `@dataclass(frozen=True)` | `exception_type`, `fault_factory`, `retryable` |
| `ExceptionAdapter` | `FaultHandler` | `can_handle()`, `handle()` — maps Python exceptions (`ConnectionError`, `TimeoutError`, `PermissionError`, `FileNotFoundError`, `ValueError`, `KeyError`, `RuntimeError`, `MemoryError`, `RecursionError`) to domain `Fault` objects |
| `RetryHandler` | `FaultHandler` | `can_handle()`, `handle()` — exponential backoff retry with per-fingerprint attempt tracking |
| `SecurityFaultHandler` | `FaultHandler` | `can_handle()`, `handle()` — **intercepts SECURITY-domain faults, replaces detailed messages with generic "An error occurred" to prevent info leakage** |
| `ResponseMapper` | `FaultHandler` | `can_handle()`, `handle()` — maps faults to HTTP status via `_DOMAIN_STATUS` mapping |
| `HTTPResponse` | `@dataclass(frozen=True)` | `status_code`, `body`, `headers` |
| `FatalHandler` | `FaultHandler` | `can_handle()`, `handle()` — terminates server process on FATAL severity |
| `LoggingHandler` | `FaultHandler` | `can_handle()`, `handle()` — structured logging, always escalates |

---

### 2.5 `aquilia/faults/engine.py` — ~320 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `contextvars`, `logging`, `time`, `typing`, `.core`, `.handlers`, `.default_handlers` |
| **Design Patterns** | **Pipeline** (Origin → Annotation → Propagation → Resolution → Emission), Context variables for request-scoped state |
| **Security** | ContextVars ensure fault context doesn't leak between concurrent requests |

#### Context Variables
- `_current_app`, `_current_route`, `_current_request_id`

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `FaultEngine` | class | `__init__(registry, ...)`, `register_global(handler)`, `register_app(app, handler)`, `register_controller(ctrl, handler)`, `register_route(route, handler)`, `on_fault(exception, **extras)`, `process(fault, **extras)`, `set_context(app, route, request_id)`, `clear_context()`, `get_history()`, `get_stats()` |
| `FaultMiddleware` | class | `__init__(engine)`, `__call__(request, handler)` — bridges FaultEngine with ASGI request/response |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `get_default_engine()` | Returns singleton `FaultEngine` with all default handlers |
| `process_fault(exception, **extras)` | Convenience wrapper |

---

### 2.6 `aquilia/faults/domains.py` — 690 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `.core.Fault`, `.core.Severity`, `.core.FaultDomain`, `typing` |
| **Design Patterns** | Domain-specific exception hierarchy, each fault carries structured metadata |
| **Security** | Security faults (`AuthenticationFault`, `AuthorizationFault`, `CSRFViolationFault`, `CORSViolationFault`, `RateLimitExceededFault`, `CSPViolationFault`) are explicitly marked `public=True` with sanitized messages |

#### Fault Classes (37 total)

| Domain | Fault Classes |
|--------|--------------|
| **CONFIG** | `ConfigFault`, `ConfigMissingFault`, `ConfigInvalidFault` |
| **REGISTRY** | `RegistryFault`, `DependencyCycleFault`, `ManifestInvalidFault` |
| **DI** | `DIFault`, `ProviderNotFoundFault`, `ScopeViolationFault`, `DIResolutionFault` |
| **ROUTING** | `RoutingFault`, `RouteNotFoundFault`, `RouteAmbiguousFault`, `PatternInvalidFault` |
| **FLOW** | `FlowFault`, `HandlerFault`, `MiddlewareFault`, `FlowCancelledFault` |
| **EFFECT** | `EffectFault`, `DatabaseFault`, `CacheFault` |
| **IO** | `IOFault`, `NetworkFault`, `FilesystemFault` |
| **SECURITY** | `SecurityFault`, `AuthenticationFault`, `AuthorizationFault`, `CSRFViolationFault`, `CORSViolationFault`, `RateLimitExceededFault`, `CSPViolationFault` |
| **SYSTEM** | `SystemFault`, `UnrecoverableFault`, `ResourceExhaustedFault` |
| **MODEL** | `ModelFault`, `AMDLParseFault`, `ModelNotFoundFault`, `ModelRegistrationFault`, `MigrationFault`, `MigrationConflictFault`, `QueryFault`, `DatabaseConnectionFault`, `SchemaFault` |

---

### 2.7 `aquilia/faults/integrations/__init__.py` — ~120 lines

| Item | Detail |
|------|--------|
| **Key Imports** | All integration sub-modules |
| **Design Patterns** | Façade for subsystem patching |
| **Security** | — |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `patch_all_subsystems(runtime)` | Patches registry, DI, routing, models |
| `create_all_integration_handlers()` | Returns list of all integration fault handlers |

---

### 2.8 `aquilia/faults/integrations/registry.py` — ~130 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `..core.Fault`, `..core.FaultDomain`, `..handlers.FaultHandler` |
| **Design Patterns** | **Monkey-patching** (patches `RuntimeRegistry` methods) |
| **Security** | — |

#### Fault Classes
- `ManifestLoadFault`, `AppContextInvalidFault`, `RouteCompilationFault`, `DependencyResolutionFault`

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `patch_runtime_registry(runtime)` | Wraps registry methods to raise structured faults |
| `create_registry_fault_handler()` | Returns handler for REGISTRY domain |

---

### 2.9 `aquilia/faults/integrations/di.py` — ~160 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `..core.Fault`, `..core.FaultDomain`, `..handlers.FaultHandler`, `...di.Container` |
| **Design Patterns** | **Monkey-patching** (patches `Container.resolve`, `resolve_async`, `register`) |
| **Security** | — |

#### Fault Classes
- `CircularDependencyFault`, `ProviderRegistrationFault`, `AsyncResolutionFault`

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `patch_di_container(container)` | Wraps DI container methods with fault-raising wrappers |
| `create_di_fault_handler()` | Returns handler for DI domain |

---

### 2.10 `aquilia/faults/integrations/routing.py` — ~170 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `re`, `..core.Fault`, `..core.FaultDomain`, `..handlers.FaultHandler` |
| **Design Patterns** | Guard functions (validation before routing) |
| **Security** | **`validate_route_pattern()` checks for regex injection / malicious patterns** |

#### Fault Classes
- `RouteConflictFault`, `MethodNotAllowedFault`, `RouteParameterFault`

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `create_routing_fault_handler()` | Returns handler for ROUTING domain |
| `safe_route_lookup(router, method, path)` | Wraps router lookup with fault handling |
| `validate_route_pattern(pattern)` | Validates route patterns (regex safety) |

---

### 2.11 `aquilia/faults/integrations/flow.py` — ~280 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `asyncio`, `functools`, `..core`, `..handlers.FaultHandler` |
| **Design Patterns** | Decorator-based fault injection (`fault_aware_handler`), middleware functions |
| **Security** | — |

#### Fault Classes
- `PipelineAbortedFault`, `HandlerTimeoutFault`, `MiddlewareChainFault`

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `fault_handling_middleware()` | Async middleware wrapping handler with fault engine |
| `timeout_middleware(seconds)` | Middleware that raises `HandlerTimeoutFault` on timeout |
| `fault_aware_handler(handler)` | Decorator that catches exceptions and converts to faults |
| `create_flow_fault_handler()` | Returns handler for FLOW domain |
| `with_cancellation_handling(handler)` | Wraps handler with `asyncio.CancelledError` handling |
| `is_fault_retryable(fault)` | Check if a fault should be retried |
| `should_abort_pipeline(fault)` | Check if a fault should abort the pipeline |

---

### 2.12 `aquilia/faults/integrations/models.py` — ~220 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `logging`, `..core`, `..handlers.FaultHandler` |
| **Design Patterns** | **Monkey-patching** (patches AMDL registry + Python ORM registry + database engine) |
| **Security** | — |

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `ModelFaultHandler` | `FaultHandler` | `can_handle()`, `handle()` — handles MODEL domain faults |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `create_model_fault_handler()` | Returns `ModelFaultHandler` |
| `patch_model_registry(registry)` | Patches model registry (both AMDL and Python ORM) |
| `patch_database_engine(engine)` | Patches DB engine with fault-raising wrappers |
| `patch_all_model_subsystems(runtime)` | Convenience to patch all model-related subsystems |

---

## 3. i18n/

### 3.1 `aquilia/i18n/__init__.py` — 201 lines

| Item | Detail |
|------|--------|
| **Key Imports** | Re-exports from all i18n sub-modules |
| **Design Patterns** | Re-export façade |
| **Security** | — |

**Exports:** `Locale`, `parse_locale`, `normalize_locale`, `match_locale`, `parse_accept_language`, `negotiate_locale`, `TranslationCatalog`, `MemoryCatalog`, `FileCatalog`, `CrousCatalog`, `NamespacedCatalog`, `MergedCatalog`, `PluralCategory`, `select_plural`, `get_plural_rule`, `MessageFormatter`, `format_message`, `format_number`, `format_currency`, `format_date`, `format_time`, `I18nService`, `I18nConfig`, `MissingKeyStrategy`, `create_i18n_service`, `LocaleResolver`, `HeaderLocaleResolver`, `CookieLocaleResolver`, `QueryLocaleResolver`, `PathLocaleResolver`, `SessionLocaleResolver`, `ChainLocaleResolver`, `I18nMiddleware`, `build_resolver`, `LazyString`, `LazyPluralString`, `lazy_t`, `lazy_tn`, `set_lazy_context`, `clear_lazy_context`, `I18nFault`, `MissingTranslationFault`, `InvalidLocaleFault`, `CatalogLoadFault`, `PluralRuleFault`, `register_i18n_providers`, `register_i18n_request_providers`, `register_i18n_template_globals`, `I18nTemplateExtension`

---

### 3.2 `aquilia/i18n/locale.py` — ~340 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `dataclasses`, `re`, `typing` |
| **Design Patterns** | Frozen value object (immutable Locale), BCP 47 compliance |
| **Security** | Regex-validated locale tags prevent injection |

#### Constants
- `LOCALE_PATTERN` — BCP 47 regex
- `_ACCEPT_LANG_RE` — Accept-Language header regex

#### Classes

| Class | Type | Methods / Properties |
|-------|------|---------------------|
| `Locale` | `@dataclass(frozen=True, slots=True)` | `language`, `script`, `region`, `variant`; `__post_init__()` (normalizes casing); Properties: `tag`, `language_tag`, `fallback_chain`; `matches(other)` |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `parse_locale(tag)` | Parse BCP 47 tag → `Locale` |
| `normalize_locale(tag)` | Normalize tag string |
| `match_locale(requested, available)` | Find best match |
| `parse_accept_language(header)` | Parse `Accept-Language` header → list of `(Locale, quality)` |
| `negotiate_locale(accept_header, available, default)` | Content negotiation |

---

### 3.3 `aquilia/i18n/catalog.py` — 816 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `abc.ABC`, `json`, `hashlib`, `pathlib`, `threading`, `time`, `typing`, optional `yaml` |
| **Design Patterns** | **Strategy** (multiple catalog backends), **Composite** (`MergedCatalog`), **Decorator** (`NamespacedCatalog`), **Hot-reload** (`FileCatalog` mtime tracking) |
| **Security** | **`CrousCatalog`: SHA-256 fingerprint in binary envelope for integrity verification**; atomic writes prevent corruption |

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `TranslationCatalog` | `ABC` | abstract `get(locale, key, default)`, `get_plural(locale, key, count, default)`, `has(locale, key)`, `locales()`, `keys(locale)` |
| `MemoryCatalog` | `TranslationCatalog` | `__init__(data)`, all abstract methods + `add_locale(locale, translations)`, deep merge, dot-notation key resolution |
| `FileCatalog` | `TranslationCatalog` | `__init__(directory, ...)`, all abstract methods + `reload()`, hot-reload via mtime tracking, JSON/YAML support |
| `CrousCatalog` | `TranslationCatalog` | `__init__(path, ...)`, all abstract methods + `compile_from_json(json_dir, output)`, CROUS binary format with envelope (header + SHA-256 fingerprint) |
| `NamespacedCatalog` | `TranslationCatalog` | `__init__(catalog, namespace)`, prefixes all keys with namespace |
| `MergedCatalog` | `TranslationCatalog` | `__init__(catalogs)`, layered fallback across multiple catalogs |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `has_crous()` | Check for `crous` library availability |

---

### 3.4 `aquilia/i18n/plural.py` — 529 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `enum`, `typing` |
| **Design Patterns** | CLDR plural rules, lookup table mapping ~50 languages to rule functions |
| **Security** | — |

#### Classes

| Class | Type | Values |
|-------|------|--------|
| `PluralCategory` | `str, Enum` | `ZERO`, `ONE`, `TWO`, `FEW`, `MANY`, `OTHER` |

#### Constants
- `CLDR_PLURAL_RULES` — dict mapping language codes to rule functions (~50 languages)

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `_operands(n)` | Extract CLDR operands (n, i, v, w, f, t) |
| `_plural_english(n)`, `_plural_french(n)`, `_plural_no_plural(n)`, `_plural_arabic(n)`, `_plural_russian(n)`, `_plural_polish(n)`, `_plural_czech(n)`, `_plural_romanian(n)`, `_plural_german(n)`, `_plural_latvian(n)`, `_plural_lithuanian(n)`, `_plural_welsh(n)`, `_plural_irish(n)`, `_plural_slovenian(n)`, `_plural_maltese(n)`, `_plural_hebrew(n)` | Language-specific plural rule implementations |
| `get_plural_rule(locale)` | Get rule function for a locale |
| `select_plural(locale, count)` | Select `PluralCategory` for a count |

---

### 3.5 `aquilia/i18n/formatter.py` — 577 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `re`, `datetime`, `typing`, `.plural`, `.locale` |
| **Design Patterns** | ICU MessageFormat parser, locale-aware formatting |
| **Security** | — |

#### Constants
- `_NUMBER_FORMATS`, `_CURRENCY_SYMBOLS`, `_ORDINAL_SUFFIXES_EN`, `_DATE_FORMATS`, `_TIME_FORMATS`

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `MessageFormatter` | class | `__init__(plural_rules, ...)`, `format(locale, pattern, args)`, `_format_plural(locale, arg_name, count, spec, args)`, `_format_select(arg_name, value, spec, args)` |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `_find_icu_args(pattern)` | ICU argument parser handling nested braces |
| `format_message(locale, pattern, **kwargs)` | Format ICU message |
| `format_number(n, locale)` | Locale-aware number formatting |
| `format_decimal(n, locale, decimals)` | Decimal formatting |
| `format_percent(n, locale)` | Percentage formatting |
| `format_currency(n, currency, locale)` | Currency formatting |
| `format_ordinal(n, locale)` | Ordinal formatting |
| `format_date(dt, locale, style)` | Date formatting |
| `format_time(dt, locale, style)` | Time formatting |
| `format_datetime(dt, locale, date_style, time_style)` | DateTime formatting |

---

### 3.6 `aquilia/i18n/service.py` — ~420 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `dataclasses`, `logging`, `typing`, `.catalog`, `.formatter`, `.locale`, `.plural` |
| **Design Patterns** | **Service layer** (central orchestrator), Strategy for missing key handling, Factory method |
| **Security** | — |

#### Classes

| Class | Type | Methods / Properties |
|-------|------|---------------------|
| `MissingKeyStrategy` | `str, Enum` | `RETURN_KEY`, `RETURN_EMPTY`, `RETURN_DEFAULT`, `RAISE`, `LOG_AND_KEY` |
| `I18nConfig` | `@dataclass` | `default_locale`, `fallback_locale`, `available_locales`, `catalog_type`, `catalog_dir`, `missing_key_strategy`, `auto_reload`, `reload_interval`, `namespace`, etc.; `from_dict()`, `to_dict()` |
| `I18nService` | class | `t(locale, key, **args)`, `tn(locale, key, count, **args)`, `tp(locale, key, context, **args)`, `has(locale, key)`, `available_locales()`, `is_available(locale)`, `negotiate(accept_header)`, `locale(tag)`, `reload_catalogs()`; Internal: `_resolve(locale, key)`, `_handle_missing(locale, key, default)`, `_build_catalog(config)` |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `create_i18n_service(config)` | Factory function |

---

### 3.7 `aquilia/i18n/lazy.py` — ~250 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `typing`, `.service.I18nService`, `.locale.Locale` |
| **Design Patterns** | **Proxy** (lazy evaluation), full `str` protocol implementation |
| **Security** | — |

#### Module-level State
- `_service_ref`, `_locale_ref` — module globals

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `LazyString` | class (`__slots__`) | `__init__(key, args, default)`, `__str__()`, `__repr__()`, `__eq__()`, `__hash__()`, `__len__()`, `__contains__()`, `__add__()`, `__radd__()`, `__format__()`, `__iter__()`, `upper()`, `lower()`, `strip()`, `replace()`, `format()`, `split()`, `join()`, `startswith()`, `endswith()` |
| `LazyPluralString` | `LazyString` | `__init__(key, count, args, default)`, `__str__()` — plural-aware |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `set_lazy_context(service, locale)` | Set module globals for lazy resolution |
| `clear_lazy_context()` | Clear module globals |
| `lazy_t(key, **kwargs)` | Factory → `LazyString` |
| `lazy_tn(key, count, **kwargs)` | Factory → `LazyPluralString` |

---

### 3.8 `aquilia/i18n/middleware.py` — ~350 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `abc.ABC`, `re`, `typing`, `.locale`, `.service.I18nService` |
| **Design Patterns** | **Strategy** (locale resolvers), **Chain of Responsibility** (`ChainLocaleResolver`), **Factory** (`build_resolver`) |
| **Security** | — |

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `LocaleResolver` | `ABC` | abstract `resolve(request) → Optional[Locale]` |
| `HeaderLocaleResolver` | `LocaleResolver` | `resolve()` — parses `Accept-Language` header |
| `CookieLocaleResolver` | `LocaleResolver` | `__init__(cookie_name="aq_locale")`, `resolve()` |
| `QueryLocaleResolver` | `LocaleResolver` | `__init__(param_name="lang")`, `resolve()` |
| `PathLocaleResolver` | `LocaleResolver` | `resolve()` — extracts locale from URL path prefix |
| `SessionLocaleResolver` | `LocaleResolver` | `resolve()` — reads from session |
| `ChainLocaleResolver` | `LocaleResolver` | `__init__(resolvers)`, `resolve()` — tries each resolver in order |
| `I18nMiddleware` | class | `__init__(service, resolver, ...)`, `__call__(request, ctx, next)` — injects `locale`, `locale_obj`, `i18n` into `request.state`; manages lazy context |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `build_resolver(config)` | Factory: builds resolver chain from config dict |
| `_get_header(request, name)` | Helper |
| `_get_cookies(request)` | Helper |
| `_get_query_params(request)` | Helper |
| `_get_path(request)` | Helper |
| `_get_state(request, key)` | Helper |

---

### 3.9 `aquilia/i18n/faults.py` — ~170 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `..faults.core.Fault`, `..faults.core.FaultDomain`, `..faults.core.Severity` |
| **Design Patterns** | Domain-specific fault hierarchy |
| **Security** | — |

Registers `FaultDomain.I18N`.

#### Fault Classes

| Class | Superclass | Description |
|-------|-----------|-------------|
| `I18nFault` | `Fault` | Base i18n fault |
| `MissingTranslationFault` | `I18nFault` | Missing translation key |
| `InvalidLocaleFault` | `I18nFault` | Invalid locale tag |
| `CatalogLoadFault` | `I18nFault` | Failed to load catalog |
| `PluralRuleFault` | `I18nFault` | Plural rule evaluation error |

---

### 3.10 `aquilia/i18n/di_integration.py` — ~110 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `typing`, `..di.Container`, `.service.I18nService`, `.service.I18nConfig` |
| **Design Patterns** | DI provider registration |
| **Security** | — |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `register_i18n_providers(container, config)` | Registers `I18nService` + `I18nConfig` in DI container (handles multiple container API styles) |
| `register_i18n_request_providers(container, service)` | Per-request `Locale` injection |

---

### 3.11 `aquilia/i18n/template_integration.py` — ~200 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `typing`, `.service.I18nService`, `.formatter` |
| **Design Patterns** | Template engine integration (Jinja2 + Aquilia ATS) |
| **Security** | — |

#### Classes

| Class | Type | Description |
|-------|------|-------------|
| `I18nTemplateExtension` | class | Descriptor for Aquilia's template engine |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `register_i18n_template_globals(env, service)` | Registers `_()`, `_n()`, `_p()`, `gettext()`, `ngettext()` globals + `translate`, `format_number`, `format_currency`, `format_date` filters on Jinja2 `Environment` |
| `_get_ctx_locale()` | Resolve locale from template context |

---

## 4. mail/

### 4.1 `aquilia/mail/__init__.py` — ~140 lines

| Item | Detail |
|------|--------|
| **Key Imports** | Re-exports from all mail sub-modules |
| **Design Patterns** | Re-export façade |
| **Security** | — |

---

### 4.2 `aquilia/mail/config.py` — 739 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `typing`, `..blueprints` (Serializer system), `..faults` |
| **Design Patterns** | **Builder** (Blueprint validation), **Configuration Object** pattern, Factory methods (`development()`, `production()`) |
| **Security** | **`write_only` fields for passwords, API keys, tokens (never serialized back); DKIM config; `require_tls` enforcement; `pii_redaction_enabled` option; `allowed_from_domains` whitelist** |

#### Blueprint Classes (Aquilia Serializer system)

| Blueprint | Validates |
|-----------|-----------|
| `ProviderConfigBlueprint` | Provider configuration (name, type, host, port, auth, priority, etc.) |
| `MailAuthConfigBlueprint` | Auth method, username, password (write_only), api_key (write_only), token (write_only), etc. |
| `RetryConfigBlueprint` | max_retries, backoff_factor, retryable_statuses, max_delay |
| `RateLimitConfigBlueprint` | max_per_second, max_per_minute, max_per_hour, max_per_day, burst_size |
| `SecurityConfigBlueprint` | dkim_enabled, dkim_selector, dkim_domain, dkim_private_key (write_only), require_tls, pii_redaction_enabled, allowed_from_domains |
| `TemplateConfigBlueprint` | template_dir, engine, cache, auto_text, default_context |
| `QueueConfigBlueprint` | enabled, backend, max_size, workers, retry_delay |

#### Config Wrapper Classes

| Class | Base | Convenience Constructors |
|-------|------|------------------------|
| `_ConfigObject` | — | `to_dict()`, `__getattr__()` (attribute-access over dict) |
| `ProviderConfig` | `_ConfigObject` | — |
| `RetryConfig` | `_ConfigObject` | — |
| `RateLimitConfig` | `_ConfigObject` | — |
| `SecurityConfig` | `_ConfigObject` | — |
| `TemplateConfig` | `_ConfigObject` | — |
| `QueueConfig` | `_ConfigObject` | — |
| `MailAuthConfig` | `_ConfigObject` | `.plain(user, pwd)`, `.api_key(key)`, `.aws_ses(key_id, secret, region)`, `.oauth2(client_id, secret, token_url)`, `.anonymous()` |
| `MailConfig` | class (slots) | `__init__(...)`, `to_dict()`, `from_dict(data)`, `development()`, `production(default_from, **overrides)` |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `_validate_sub(blueprint_cls, data, wrapper_cls)` | Validate data through blueprint → wrapper |
| `_validate_auth(value)` | Validate/coerce auth config |
| `_validate_provider(data)` | Validate single provider dict |
| `_coerce_providers(items)` | Convert list of dicts to validated `ProviderConfig` objects |
| `_coerce_sub(value, blueprint_cls, wrapper_cls)` | Accept wrapper/dict/None → validated wrapper |

---

### 4.3 `aquilia/mail/envelope.py` — ~250 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `dataclasses`, `enum`, `hashlib`, `time`, `uuid`, `typing` |
| **Design Patterns** | Value object (dataclass), content-addressed dedup |
| **Security** | **SHA-256 content digest for attachment integrity; idempotency key for exactly-once delivery** |

#### Classes

| Class | Type | Fields / Methods |
|-------|------|-----------------|
| `EnvelopeStatus` | `str, Enum` | `QUEUED`, `SENDING`, `SENT`, `FAILED`, `BOUNCED`, `CANCELLED` |
| `Priority` | `int, Enum` | `CRITICAL=0`, `HIGH=25`, `NORMAL=50`, `LOW=75`, `BULK=100` |
| `Attachment` | `@dataclass` | `filename`, `content_type`, `digest` (SHA-256), `size`, `inline`, `content_id` |
| `MailEnvelope` | `@dataclass` | `id`, `status`, `from_email`, `to`, `cc`, `bcc`, `reply_to`, `subject`, `body_text`, `body_html`, `template_name`, `template_context`, `attachments`, `priority`, `retry_count`, `max_retries`, `provider_affinity`, `idempotency_key`, `tenant_id`, `trace_id`, `tags`, `metadata`, `errors`; Methods: `compute_digest()`, `all_recipients()`, `recipient_domains()`, `to_dict()`, `from_dict()` |

---

### 4.4 `aquilia/mail/faults.py` — ~170 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `..faults.core.Fault`, `..faults.core.FaultDomain`, `..faults.core.Severity` |
| **Design Patterns** | Domain-specific fault hierarchy |
| **Security** | — |

Registers `FaultDomain.MAIL`.

#### Fault Classes

| Class | Superclass | Key Fields |
|-------|-----------|------------|
| `MailFault` | `Fault` | `envelope_id`, `recoverable` |
| `MailSendFault` | `MailFault` | `transient` (transient vs permanent) |
| `MailTemplateFault` | `MailFault` | Template rendering errors |
| `MailConfigFault` | `MailFault` | Configuration errors |
| `MailSuppressedFault` | `MailFault` | Email suppressed by policy |
| `MailRateLimitFault` | `MailFault` | Provider rate limit hit |
| `MailValidationFault` | `MailFault` | Validation errors |

---

### 4.5 `aquilia/mail/message.py` — ~350 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `typing`, `pathlib`, `mimetypes`, `.envelope`, `.service` |
| **Design Patterns** | Fluent API (message builder), Template method (`TemplateMessage` overrides `build_envelope`) |
| **Security** | **`_validate_email()` validates email addresses before sending** |

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `EmailMessage` | class | `__init__(subject, body, from_email, to, ...)`, `attach(filename, content, mimetype)`, `attach_file(path)`, `build_envelope()`, `send()`, `asend()` |
| `EmailMultiAlternatives` | `EmailMessage` | `attach_alternative(content, mimetype)` |
| `TemplateMessage` | `EmailMessage` | `__init__(..., template_name, context)`, `build_envelope()` — renders ATS template at build time |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `_validate_email(addr)` | Email address validation |
| `_validate_list(addrs)` | Validate list of email addresses |
| `_html_to_text(html)` | Strip HTML to plain text fallback |

---

### 4.6 `aquilia/mail/service.py` — ~320 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `logging`, `typing`, `.config.MailConfig`, `.envelope`, `.providers`, `..di` decorators |
| **Design Patterns** | **Service layer** (singleton), **Factory** (provider creation), **Strategy** (provider dispatch), Priority-ordered fallback |
| **Security** | — |

#### Module-level State
- `_mail_service` — singleton

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `MailService` | `@service` | `on_startup()`, `on_shutdown()`, `_apply_global_auth(config)`, `_create_provider(provider_config)` (factory: smtp/ses/sendgrid/console/file + discovery), `send_message(message_or_envelope)`, `_dispatch_direct(envelope)` (tries providers in priority order), `get_provider_names()`, `is_healthy()` |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `_get_mail_service()` | Get singleton |
| `set_mail_service(service)` | Set singleton |
| `send_mail(subject, body, from_email, to, ...)` | Sync convenience |
| `asend_mail(subject, body, from_email, to, ...)` | Async convenience |

---

### 4.7 `aquilia/mail/di_providers.py` — ~240 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `typing`, `..di`, `.config.MailConfig`, `.service.MailService`, `..discovery.PackageScanner` |
| **Design Patterns** | DI provider registration, Auto-discovery |
| **Security** | — |

#### Classes

| Class | Type | Description |
|-------|------|-------------|
| `MailConfigProvider` | `@service` | Provides validated `MailConfig` |
| `MailServiceProvider` | `@service` | Provides `MailService` singleton |
| `MailProviderRegistry` | `@service` | Auto-discovers `IMailProvider` implementations via `PackageScanner` |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `create_mail_config(raw_config)` | Factory |
| `create_mail_service(config)` | Factory |
| `register_mail_providers(container, config)` | Full DI wiring |

---

### 4.8 `aquilia/mail/providers/__init__.py` — ~130 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `enum`, `dataclasses`, `typing` |
| **Design Patterns** | Protocol-based interface (`IMailProvider`) |
| **Security** | — |

#### Classes

| Class | Type | Members |
|-------|------|---------|
| `ProviderResultStatus` | `str, Enum` | `SUCCESS`, `TRANSIENT_FAILURE`, `PERMANENT_FAILURE`, `RATE_LIMITED` |
| `ProviderResult` | `@dataclass` | `status`, `provider_message_id`, `error_message`, `raw_response`, `retry_after` |
| `IMailProvider` | `Protocol` | `send(envelope)`, `send_batch(envelopes)`, `health_check()`, `initialize()`, `shutdown()` |

---

### 4.9 `aquilia/mail/providers/console.py` — ~100 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `logging`, `.ProviderResult`, `.ProviderResultStatus`, `..envelope.MailEnvelope` |
| **Design Patterns** | Null object (always succeeds) |
| **Security** | — |

#### Classes

| Class | Methods |
|-------|---------|
| `ConsoleProvider` | `__init__(name)`, `initialize()`, `shutdown()`, `send(envelope)`, `send_batch(envelopes)`, `health_check()` — logs to console, always healthy |

---

### 4.10 `aquilia/mail/providers/file.py` — 375 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `asyncio`, `json`, `pathlib`, `email.mime`, `logging`, `.ProviderResult`, `..envelope` |
| **Design Patterns** | File-based output, RFC 2822 `.eml` format, JSONL index |
| **Security** | — |

#### Classes

| Class | Methods |
|-------|---------|
| `FileProvider` | `__init__(name, output_dir, file_extension, max_files)`, `initialize()`, `shutdown()`, `send(envelope)` (writes .eml + JSONL index), `send_batch(envelopes)`, `health_check()`, `list_files()`, `read_last()`, `clear()` |

---

### 4.11 `aquilia/mail/providers/sendgrid.py` — 426 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `httpx`, `logging`, `typing`, `.ProviderResult`, `..envelope` |
| **Design Patterns** | HTTP API client, error classification by HTTP status |
| **Security** | — |

#### Classes

| Class | Methods |
|-------|---------|
| `SendGridProvider` | `__init__(name, api_key, sandbox_mode, ...)`, `initialize()`, `shutdown()`, `send(envelope)` (v3 API), `_handle_error_response(response, envelope)`, `send_batch(envelopes)`, `health_check()` (scopes endpoint), `_classify_exception(error)` |

---

### 4.12 `aquilia/mail/providers/ses.py` — 466 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `aiobotocore`/`boto3`, `logging`, `typing`, `email.mime`, `.ProviderResult`, `..envelope` |
| **Design Patterns** | AWS SDK integration, raw MIME vs structured API dispatch |
| **Security** | — |

#### Constants
- `_THROTTLE_CODES` — set of AWS error codes for rate limiting
- `_PERMANENT_CODES` — set of AWS error codes for permanent failures

#### Classes

| Class | Methods |
|-------|---------|
| `SESProvider` | `__init__(name, region, access_key_id, secret_access_key, ...)`, `initialize()`, `shutdown()`, `send(envelope)`, `_send_raw(envelope)`, `_send_structured(envelope)`, `send_batch(envelopes)`, `health_check()` (GetAccount), `_classify_error(error)` |

---

### 4.13 `aquilia/mail/providers/smtp.py` — 549 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `asyncio`, `aiosmtplib`, `email.mime`, `ssl`, `logging`, `typing`, `.ProviderResult`, `..envelope` |
| **Design Patterns** | Connection pooling (keep-alive + reconnect), MIME message builder |
| **Security** | **SSL context construction with `certifi` fallback; certificate validation; TLS/SSL enforcement** |

#### Constants
- `_TRANSIENT_CODES` — set of SMTP codes (421, 450, 451, etc.)
- `_PERMANENT_CODES` — set of SMTP codes (501, 550, 551, etc.)

#### Classes

| Class | Methods |
|-------|---------|
| `SMTPProvider` | `__init__(name, host, port, use_tls, use_ssl, username, password, ...)`, `initialize()`, `shutdown()`, `_build_ssl_context()`, `_acquire_connection()`, `_release_connection(conn)`, `_build_mime_message(envelope)`, `send(envelope)`, `send_batch(envelopes)` (connection reuse), `health_check()` (NOOP), `_classify_error(error)`, `_extract_smtp_code(error)`, `_is_connection_error(error)` |

---

### 4.14 `aquilia/mail/template/__init__.py` — ~150 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `re`, `pathlib`, `typing` |
| **Design Patterns** | Simple template engine (ATS stub) |
| **Security** | — |

#### Constants
- `_EXPR_RE` — regex for `<< expr >>` template syntax

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `_resolve_dotted(obj, key)` | Resolve dotted key path |
| `_substitute(template, context)` | Substitute `<< expr >>` expressions |
| `render_string(template, context)` | Render template string |
| `render_template(template_name, context)` | Render template file |
| `configure(template_dir, **options)` | Configure template engine |

---

## 5. middleware_ext/

### 5.1 `aquilia/middleware_ext/__init__.py` — 93 lines

| Item | Detail |
|------|--------|
| **Key Imports** | Re-exports from all middleware_ext sub-modules |
| **Design Patterns** | Re-export façade |
| **Security** | — |

**Exports:** `RequestScopeMiddleware`, `SimplifiedRequestScopeMiddleware`, `SessionMiddleware`, `CORSMiddleware`, `CSPMiddleware`, `CSPPolicy`, `CSRFError`, `CSRFMiddleware`, `HSTSMiddleware`, `HTTPSRedirectMiddleware`, `ProxyFixMiddleware`, `SecurityHeadersMiddleware`, `csrf_exempt`, `csrf_token_func`, `RateLimitMiddleware`, `RateLimitRule`, `ip_key_extractor`, `api_key_extractor`, `user_key_extractor`, `StaticMiddleware`, `EnhancedLoggingMiddleware`, `CombinedLogFormatter`, `StructuredLogFormatter`, `DevLogFormatter`, `EffectMiddleware`, `FlowContextMiddleware`

---

### 5.2 `aquilia/middleware_ext/effect_middleware.py` — ~230 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `logging`, `time`, `typing`, `..effects.EffectRegistry`, `..request.Request`, `..response.Response`, `..middleware.Handler` |
| **Design Patterns** | Per-request resource lifecycle (acquire/release), Effect system integration |
| **Security** | Ensures DB transactions are rolled back on failure (`success=False`) |

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `EffectMiddleware` | class | `__init__(effect_registry, auto_detect=True)`, `__call__(request, handler)`, `_detect_required_effects(request) → Set[str]` (checks `route_effects`, `__flow_effects__`, `pipeline_effects`), `_get_effect_mode(request, effect_name)` (infers read/write from HTTP method for DB effects) |
| `FlowContextMiddleware` | class | `__init__(effect_registry=None)`, `__call__(request, handler)` — creates `FlowContext` per request, stores in `request.state["flow_context"]`, disposes on exit |

---

### 5.3 `aquilia/middleware_ext/logging.py` — ~275 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `logging`, `time`, `datetime`, `typing`, `aquilia.request.Request`, `aquilia.response.Response` |
| **Design Patterns** | **Strategy** (pluggable log formatters), ANSI color-coded output |
| **Security** | — |

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `_LogFormatter` | abstract base | `format_request(**kwargs) → str` |
| `CombinedLogFormatter` | `_LogFormatter` | Apache Combined Log Format |
| `StructuredLogFormatter` | `_LogFormatter` | JSON structured log |
| `DevLogFormatter` | `_LogFormatter` | Color-coded terminal output |
| `LoggingMiddleware` | class | `__init__(logger_name, format, level, error_level, slow_threshold_ms, skip_paths, log_request_body, include_headers)`, `__call__(request, ctx, next_handler)` — measures timing, selects log level (error for 5xx, warning for slow), skips configurable paths |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `_status_color(status)` | ANSI color for HTTP status |
| `_method_color(method)` | ANSI color for HTTP method |

---

### 5.4 `aquilia/middleware_ext/rate_limit.py` — ~370 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `math`, `time`, `collections.defaultdict`, `typing`, `aquilia.request.Request`, `aquilia.response.Response`, `aquilia.faults.domains.RateLimitExceededFault` |
| **Design Patterns** | **Token Bucket** algorithm, **Sliding Window Counter** algorithm, Strategy (pluggable key extractors), Lazy eviction for memory efficiency |
| **Security** | **Rate limiting protects against DoS; API key truncation in `api_key_extractor` (32 chars max) for safety; integrates with fault system** |

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `_TokenBucket` | class (`__slots__`) | `__init__(capacity, refill_rate)`, `consume(tokens=1) → (allowed, retry_after)`, property `remaining` |
| `_SlidingWindowCounter` | class (`__slots__`) | `__init__(window_size, max_requests)`, `consume() → (allowed, retry_after)`, `_advance_windows(now)`, properties `remaining`, `reset_time` |
| `_BucketStore` | class | `__init__(cleanup_interval)`, `get_or_create(key, factory)`, `_cleanup(now)` — lazy expiry-based eviction |
| `RateLimitRule` | class (`__slots__`) | `__init__(limit, window, algorithm, key_func, burst, scope, methods)`, `matches(request) → bool` |
| `RateLimitMiddleware` | class | `__init__(rules, default_limit, default_window, response_format, include_headers, exempt_paths)`, `__call__(request, ctx, next_handler)`, `_create_bucket(rule)`, `_rate_limited_response(rule, bucket, retry_after)`, `_apply_headers(response, rule, bucket)` |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `ip_key_extractor(request)` | Extract client IP as rate key |
| `api_key_extractor(request)` | Extract API key / Bearer token (truncated to 32 chars) |
| `user_key_extractor(request)` | Extract user ID from auth state |

---

### 5.5 `aquilia/middleware_ext/request_scope.py` — ~170 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `typing`, `aquilia.di.Container` |
| **Design Patterns** | Request-scoped DI container (child container per request) |
| **Security** | Proper isolation — each request gets its own DI scope; containers are disposed in `finally` blocks |

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `RequestScopeMiddleware` | ASGI middleware | `__init__(app, runtime)`, `__call__(scope, receive, send)` — creates child container per HTTP request, stores in `scope["state"]["di_container"]`, disposes in `finally` |
| `SimplifiedRequestScopeMiddleware` | class | `__init__(runtime)`, `__call__(request, call_next)` — higher-level version with request/response objects |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `create_request_scope_middleware(runtime)` | Factory function |

---

### 5.6 `aquilia/middleware_ext/security.py` — 1216 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `hashlib`, `ipaddress`, `os`, `re`, `secrets`, `time`, `collections.OrderedDict`, `typing`, `aquilia.request.Request`, `aquilia.response.Response`, `aquilia.faults.domains` (security faults) |
| **Design Patterns** | **LRU caching** (`_OriginMatcher`), **Builder** (`CSPPolicy` fluent API), **Synchronizer Token + Double Submit Cookie** (CSRF), **CIDR network matching** (ProxyFix), Factory methods (`CSPPolicy.strict()`, `CSPPolicy.relaxed()`) |
| **Security** | **This is the security-critical file. See details below.** |

#### ⚠️ Security-Relevant Code (Comprehensive)

| Component | Security Feature |
|-----------|-----------------|
| `CORSMiddleware` | RFC 6454/7231 compliant; `Vary: Origin` prevents cache poisoning; credential reflection (no `*` with credentials); fault integration via `CORSViolationFault` |
| `CSPMiddleware` | `secrets.token_urlsafe(16)` nonce generation per request; nonce injected into templates via `request.state["csp_nonce"]`; report-only mode |
| `CSRFMiddleware` | **Synchronizer Token** (session-backed) + **Double Submit Cookie** fallback (HMAC-SHA256 signed); `secrets.token_urlsafe(32)` tokens; **constant-time comparison** (`hmac.compare_digest`); SameSite cookie; token rotation; AJAX trust (`X-Requested-With`) |
| `HSTSMiddleware` | `Strict-Transport-Security` with `includeSubDomains` and `preload` |
| `HTTPSRedirectMiddleware` | Forces HTTPS; excludes localhost and configurable paths/hosts |
| `ProxyFixMiddleware` | **CIDR-based trusted proxy validation** (`ipaddress.ip_network`); only processes `X-Forwarded-*` headers from trusted sources; prevents IP spoofing |
| `SecurityHeadersMiddleware` | `X-Content-Type-Options: nosniff`; `X-Frame-Options: DENY`; `X-XSS-Protection: 0`; `Referrer-Policy`; `Permissions-Policy`; `Cross-Origin-Opener-Policy`; `Cross-Origin-Embedder-Policy`; `Cross-Origin-Resource-Policy`; removes `Server` header |

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `_OriginMatcher` | class (`__slots__`) | `__init__(origins, cache_size=512)`, `matches(origin) → bool`, `_evaluate(origin)`, property `is_wildcard`; LRU cache for compiled regex patterns |
| `CORSMiddleware` | class | `__init__(allow_origins, allow_methods, allow_headers, expose_headers, allow_credentials, max_age, allow_origin_regex)`, `__call__(request, ctx, next_handler)`, `_preflight(origin, request, allowed)`, `_apply_cors_headers(response, origin, allowed)`, `_set_origin_header(headers, origin)` |
| `CSPPolicy` | class (`__slots__`) | `default_src()`, `script_src()`, `style_src()`, `img_src()`, `font_src()`, `connect_src()`, `media_src()`, `object_src()`, `frame_src()`, `frame_ancestors()`, `base_uri()`, `form_action()`, `worker_src()`, `child_src()`, `manifest_src()`, `upgrade_insecure_requests()`, `block_all_mixed_content()`, `report_uri()`, `report_to()`, `directive()`, `build(nonce)` → CSP header string; classmethods: `strict()`, `relaxed()` |
| `CSPMiddleware` | class | `__init__(policy, report_only, nonce)`, `__call__(request, ctx, next_handler)` |
| `HSTSMiddleware` | class | `__init__(max_age, include_subdomains, preload)`, `__call__(request, ctx, next_handler)` |
| `HTTPSRedirectMiddleware` | class | `__init__(redirect_status, exclude_paths, exclude_hosts)`, `__call__(request, ctx, next_handler)`, `_get_scheme(request)`, `_get_host(request)` |
| `ProxyFixMiddleware` | class | `__init__(trusted_proxies, x_for, x_proto, x_host, x_port)`, `__call__(request, ctx, next_handler)`, `_get_remote_addr(request)`, `_is_trusted(ip_str)` |
| `SecurityHeadersMiddleware` | class | `__init__(frame_options, referrer_policy, permissions_policy, cross_origin_opener_policy, ...)`, `__call__(request, ctx, next_handler)` |
| `CSRFError` | `CSRFViolationFault` | `__init__(reason)` — integrates with Aquilia fault system |
| `CSRFMiddleware` | class | `__init__(secret_key, token_length, header_name, field_name, cookie_name, ..., trust_ajax, rotate_token, failure_status)`, `_generate_token()`, `_sign_token(token)`, `_verify_signed_token(signed)`, `_get_session_token(request)`, `_set_session_token(request, token)`, `_get_cookie_token(request)`, `_set_cookie_token(response, token)`, `_get_submitted_token(request)`, `_is_exempt(request)`, `_validate_token(stored, submitted)`, `__call__(request, ctx, next_handler)` |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `csrf_token_func(request)` | Extract CSRF token for template integration |
| `csrf_exempt(request)` | Mark request as CSRF-exempt |

---

### 5.7 `aquilia/middleware_ext/session_middleware.py` — ~190 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `logging`, `typing`, `aquilia.middleware.Handler`, `aquilia.request.Request`, `aquilia.response.Response`, `aquilia.di.RequestCtx`, `aquilia.sessions` |
| **Design Patterns** | Lifecycle management (resolve → process → commit), DI integration (session registered as request-scoped instance), Null Object (`OptionalSessionMiddleware`) |
| **Security** | **Session rotation on privilege change (login/logout) prevents session fixation; concurrency checking** |

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `SessionMiddleware` | class | `__init__(session_engine)`, `__call__(request, ctx, next_handler)` — resolves session, registers in DI, detects privilege changes (login/logout) for automatic rotation, commits session |
| `OptionalSessionMiddleware` | class | `__init__(session_engine=None)`, `__call__(...)` — gracefully handles missing session engine |

#### Standalone Functions

| Function | Description |
|----------|-------------|
| `create_session_middleware(session_engine, optional)` | Factory function |

---

### 5.8 `aquilia/middleware_ext/static.py` — 604 lines

| Item | Detail |
|------|--------|
| **Key Imports** | `hashlib`, `mimetypes`, `os`, `pathlib`, `time`, `collections.OrderedDict`, `datetime`, `email.utils`, `typing`, `aquilia.request.Request`, `aquilia.response.Response` |
| **Design Patterns** | **Radix Trie** (O(k) URL prefix matching), **LRU Cache** (in-memory file cache), Content negotiation (pre-compressed variants) |
| **Security** | **Directory traversal prevention via `Path.resolve()` + `relative_to()` check; file extension whitelist; file size limits** |

#### Constants
- `_EXTRA_MIME_TYPES` — additional MIME types beyond stdlib (woff2, webp, avif, wasm, etc.)

#### Classes

| Class | Type | Methods |
|-------|------|---------|
| `_RadixNode` | class (`__slots__`) | `prefix`, `children`, `directory` |
| `_RadixTrie` | class | `__init__()`, `insert(url_prefix, directory)`, `lookup(path) → (directory, relative_path)`, `_common_prefix(a, b)` |
| `_LRUFileCache` | class (`__slots__`) | `__init__(capacity_bytes, max_file_size)`, `get(key)`, `put(key, content, etag, content_type, mtime)`, `invalidate(key)` |
| `StaticMiddleware` | class | `__init__(directories, cache_max_age, immutable, etag, gzip, brotli, max_file_size, memory_cache, memory_cache_size, allowed_extensions, index_file, html5_history, extra_directories)`, `__call__(request, ctx, next_handler)`, `_matched_prefix(path)`, `_serve_file(request, directory, relative_path)`, `_negotiate_encoding(original, accept_encoding)`, `_detect_content_type(path)`, `_compute_etag(path, stat)`, `_etag_matches(client_header, etag)`, `_build_cache_headers(etag, stat)`, `_build_headers(...)`, `_handle_range(content, range_header, ...)`, `url_for_static(path)` |

#### Key Features
- **ETag**: Weak ETag from inode + mtime + size (MD5, `usedforsecurity=False`)
- **Conditional responses**: `If-None-Match` and `If-Modified-Since` → 304
- **Range requests**: `Range: bytes=start-end` → 206 Partial Content
- **Pre-compressed**: `.br` (Brotli) and `.gz` (gzip) detection
- **Fallback directories**: Module static dirs searched in order
- **HTML5 History API**: SPA routing fallback to `index.html`

---

## Summary Statistics

| Directory | Files | Total Lines | Classes | Standalone Functions | Security-Critical |
|-----------|-------|-------------|---------|---------------------|-------------------|
| `discovery/` | 2 | ~726 | 8 | 0 | AST-only (safe) |
| `faults/` | 11 | ~3,050 | ~25 + 37 faults | ~15 | SHA-256 hashing, info masking |
| `i18n/` | 11 | ~3,960 | ~20 | ~35 | SHA-256 catalog fingerprint |
| `mail/` | 14 | ~4,350 | ~25 | ~15 | TLS/SSL, write-only secrets, email validation, SHA-256 digests |
| `middleware_ext/` | 8 | ~3,150 | ~25 | ~8 | **CORS, CSP, CSRF, HSTS, HTTPS redirect, proxy fix, security headers, session fixation prevention, directory traversal prevention, rate limiting** |
| **Total** | **46** | **~15,236** | **~140** | **~73** | |

---

## Cross-Cutting Design Patterns

| Pattern | Occurrences |
|---------|-------------|
| Chain of Responsibility | `FaultHandler` chain, `ChainLocaleResolver`, `CompositeHandler` |
| Strategy | Locale resolvers, mail providers, log formatters, rate-limit algorithms |
| Factory | `create_i18n_service`, `create_mail_service`, `build_resolver`, `_create_provider`, `create_session_middleware` |
| Composite | `CompositeHandler`, `MergedCatalog`, `ChainLocaleResolver` |
| Proxy / Lazy | `LazyString`, `LazyPluralString` |
| Builder | `CSPPolicy` fluent API, `EmailMessage`, Blueprint config validation |
| Pipeline | Discovery engine, Fault engine lifecycle phases, Session middleware lifecycle |
| Monkey-patching | Fault integrations (DI, registry, routing, models) |
| Singleton | `MailService`, `FaultEngine` (default), i18n lazy context |
| Value Object | `Locale`, `FaultContext`, `Attachment`, `MailEnvelope`, `ProviderResult` |
| Null Object | `ConsoleProvider`, `OptionalSessionMiddleware` |
