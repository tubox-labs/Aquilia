# I18n Architecture

## Design Goals

Aquilia i18n is built around these goals:

- Async-safe request integration through middleware and request state
- Explicit, typed configuration (`I18nConfig`)
- Catalog backend flexibility (memory, file, CROUS)
- Stable translation lookup semantics (`t`, `tn`, `tp`)
- Zero required external runtime dependencies (optional extras for YAML/CROUS)

## Boot and Wiring Flow

When the server starts and i18n is enabled:

1. `ConfigLoader.get_i18n_config()` produces merged runtime config.
2. `I18nConfig.from_dict()` converts dict config to typed config.
3. `create_i18n_service()` builds `I18nService` and catalog backend.
4. `register_i18n_providers()` injects app-scoped providers into DI containers.
5. `build_resolver()` constructs ordered locale resolvers.
6. `I18nMiddleware` is added to middleware stack (priority 24).
7. `register_i18n_template_globals()` is applied if template engine exists.

Primary orchestrator: `aquilia/server.py::_setup_i18n`.

## Core Components

| Component | Location | Responsibility |
|---|---|---|
| Locale model and parsing | `aquilia/i18n/locale.py` | BCP 47 parsing, normalization, matching, negotiation |
| Plural rules | `aquilia/i18n/plural.py` | CLDR-style category selection (`zero/one/two/few/many/other`) |
| Catalog abstraction | `aquilia/i18n/catalog.py` | Key retrieval, plural retrieval, locale/key enumeration |
| Message formatting | `aquilia/i18n/formatter.py` | ICU-like interpolation plus number/date/currency helpers |
| Service orchestration | `aquilia/i18n/service.py` | Translation API, fallback chain, strategy handling |
| Request integration | `aquilia/i18n/middleware.py` | Locale resolution and request state injection |
| Template integration | `aquilia/i18n/template_integration.py` | Jinja globals and filters |
| Template context helper | `aquilia/templates/context.py` | Optional `_`/`gettext` context injection fallback |
| DI integration | `aquilia/i18n/di_integration.py` | App and request provider registration |
| Fault types | `aquilia/i18n/faults.py` | i18n-domain fault hierarchy |
| CLI tooling | `aquilia/cli/commands/i18n.py` | Catalog lifecycle and extraction operations |

## Translation Lookup Pipeline

### `I18nService.t(key, locale, default, **kwargs)`

Lookup order:

1. Exact locale key lookup (`catalog.get(key, locale)`).
2. Parsed locale fallback chain (`fr-CA -> fr`, etc.).
3. Global fallback locale (`config.fallback_locale`) if different.
4. Missing-key strategy handling.

Formatting:

- If kwargs are present and text resolved, formatter interpolation runs.
- Formatting is ICU-like but intentionally lightweight.

### `I18nService.tn(key, count, locale, default, **kwargs)`

1. Determine plural category from language via `select_plural`.
2. Attempt `catalog.get_plural(key, locale, category)`.
3. Fallback to non-plural `t` lookup if plural branch missing.
4. Inject `count` into kwargs and format resolved string.

## Locale Resolution Pipeline

Resolver chain is ordered by `resolver_order` and short-circuits on first match:

- `QueryLocaleResolver`
- `CookieLocaleResolver`
- `HeaderLocaleResolver`
- `PathLocaleResolver`
- `SessionLocaleResolver`

`ChainLocaleResolver.resolve()` catches resolver exceptions and continues.

`I18nMiddleware` then:

1. Starts with default locale.
2. Applies resolver result if available and allowed by `service.is_available`.
3. Parses locale object (`parse_locale`).
4. Writes request state:
   - `locale`
   - `locale_obj`
   - `i18n`
5. Sets lazy-translation context for request duration.

## Catalog Build Pipeline

`I18nService._build_catalog()` chooses backend per `catalog_format`:

- `crous` -> `CrousCatalog`
- otherwise -> `FileCatalog`

Multiple `catalog_dirs` are layered with `MergedCatalog` preserving order.

Backend details:

- `MemoryCatalog`: in-memory nested dict lookups with deep merge support.
- `FileCatalog`: lazy loads JSON trees by default, with optional YAML support when configured; filenames become namespaces.
- `CrousCatalog`: prefers `.crous`, supports JSON fallback and optional auto-compile.

## Fault and Exception Behavior

The subsystem includes typed i18n faults (`I18nFault` subclasses), but not every invalid-path branch raises them today.

Key behavior:

- Missing translation can raise `MissingTranslationFault` when strategy is `raise`.
- Locale parsing currently raises `ConfigInvalidFault` from `aquilia.faults.domains`.
- Some failure points are fail-soft and log warnings instead of raising.

See `edge-cases-and-limitations.md` for exact caveats.

## Boundaries and Integration Contracts

- i18n does not authenticate or authorize users.
- i18n may read session data only through `SessionLocaleResolver` if configured.
- i18n does not own persistence for user locale preferences; it consumes request/session/cookie/query/header signals.
- Template and controller layers should treat `I18nService` as the canonical translation API.
