# Aquilia — Codebase Structure

> Complete directory-by-directory guide to the Aquilia framework source.

---

## Root Structure

```
aquilia/
├── __init__.py              # Public API surface (~300+ re-exported symbols)
├── _datastructures.py       # Core HTTP data structures (MultiDict, Headers, URL, Cookie)
├── _uploads.py              # File upload handling (streaming, disk, memory)
├── asgi.py                  # ASGI protocol adapter
├── config.py                # Layered configuration system
├── config_builders.py       # Fluent workspace configuration builders (4,661 lines)
├── effects.py               # Typed effect system (Effect-TS inspired)
├── engine.py                # Runtime primitives (EngineState, RuntimeStats, RequestContext)
├── flow.py                  # Guard → Transform → Handler → Hook pipeline
├── health.py                # Centralized subsystem health tracking
├── lifecycle.py             # Startup/shutdown lifecycle coordination
├── manifest.py              # Declarative module manifest system
├── middleware.py             # Core middleware (RequestID, ErrorHandler, Timing, Timeout, CORS, Gzip)
├── request.py               # Production-grade ASGI request wrapper (1,970 lines)
├── response.py              # HTTP response builder with SSE, file serving, signed cookies (1,841 lines)
└── server.py                # Central orchestrator — the nervous system (3,358 lines)
```

---

## Directory Guide

### `admin/` — Admin Panel (18 files, ~10,600 lines)

Django-admin-inspired auto-generated CRUD interface.

| File | Purpose |
|------|---------|
| `audit.py` | Immutable audit trail with binary persistence |
| `blueprints.py` | Admin-specific serialization rules |
| `controller.py` | 80+ HTTP routes (dashboard, CRUD, ORM, monitoring, Docker, K8s) |
| `di_providers.py` | DI wiring for admin components |
| `error_tracker.py` | Error grouping by SHA-256 fingerprint with trends |
| `export.py` | CSV, JSON, XML, Excel export backends |
| `faults.py` | Admin-specific fault classes |
| `filters.py` | Boolean, choice, date-range, related-model filters |
| `hooks.py` | Lifecycle hooks (before/after save/delete, soft-delete, versioning, timestamps) |
| `inlines.py` | Related model inline editing |
| `models.py` | AdminUser, AdminGroup, Permission models (Argon2id hashing) |
| `options.py` | ModelAdmin declarative configuration |
| `permissions.py` | 3-tier permission system (SUPERADMIN/STAFF/VIEWER) |
| `query_inspector.py` | Slow query detection, N+1 detection |
| `registry.py` | Model registration and autodiscovery |
| `site.py` | AdminSite singleton (6,347 lines) |
| `widgets.py` | Form widgets (text, select, date, chart, code, file) |

### `aquilary/` — Module Registry & Build System (9 files, ~4,100 lines)

The Aquilary is the module registry that manages application manifests.

| File | Purpose |
|------|---------|
| `cli.py` | CLI commands for manifest management |
| `core.py` | AppContext, RuntimeRegistry, Aquilary — 5-phase build pipeline |
| `errors.py` | Structured error classes with code locations |
| `fingerprint.py` | SHA-256 deterministic fingerprinting for CI/CD gating |
| `graph.py` | Dependency graph with Kahn's topological sort and Tarjan's SCC |
| `injection.py` | Type annotation → DI resolution mapping |
| `loader.py` | ManifestSource (file/DSL/builder), ManifestLoader |
| `validation.py` | 5-phase validation: structure → deps → namespace → routes → cross-app |

### `artifacts/` — Content-Addressed Artifact System (6 files, ~1,800 lines)

Immutable, content-addressed build artifacts with SHA-256 integrity.

| File | Purpose |
|------|---------|
| `builder.py` | Fluent ArtifactBuilder API |
| `core.py` | 11 artifact kinds (config, code, model, template, migration, etc.) |
| `kinds.py` | Typed artifact wrappers with kind-specific validation |
| `reader.py` | Artifact deserialization and schema inspection |
| `store.py` | Abstract + Memory + Filesystem stores (atomic writes, CROUS binary) |

### `auth/` — Authentication & Authorization (22 files, ~8,800 lines)

Complete security subsystem.

| File | Purpose |
|------|---------|
| `core.py` | Identity, Credentials, PasswordHash, APIKey, OAuth2Client, MFAEnrollment |
| `tokens.py` | JWT-like token management with RS256/ES256/EdDSA + key rotation |
| `passwords.py` | Argon2id hashing + PBKDF2 fallback, HIBP breach checking |
| `guards.py` | Flow pipeline security guards (Bearer, API Key, Authorization, Scope, Role) |
| `authorization.py` | RBAC + ABAC + OAuth2 Scopes unified engine |
| `manager.py` | AuthManager — rate-limited authentication coordinator |
| `clearance.py` | 5-tier clearance system (level/entitlements/conditions/compartments) |
| `faults.py` | 40+ structured auth faults |
| `hardening.py` | CSRF, session fingerprinting, security headers, token binding |
| `mfa.py` | TOTP (RFC 6238), WebAuthn/FIDO2, backup codes |
| `oauth2.py` | OAuth 2.0 server (authorization code + PKCE, client credentials, device flow) |
| `audit.py` | OWASP-compliant audit trail with multi-store fan-out |
| `artifacts.py` | Signed security artifacts (RSA PKCS1v15) |
| `stores.py` | In-memory identity, credential, token stores |
| `policy.py` | Declarative policy DSL with `@rule` decorator |
| `sessions.py` | Auth-aware session management (rotation on privilege change) |
| `providers.py` | DI provider declarations for all auth components |
| `integration_guards.py` | Controller-compatible guard wrappers |
| `middleware.py` | Unified auth middleware (session → token → identity → DI) |
| `session_manager.py` | Standalone session lifecycle (create, rotate, extend, delete) |

### `blueprints/` — Data Contract System (8 files, ~4,200 lines)

Not serializers — first-class framework primitives.

| File | Purpose |
|------|---------|
| `core.py` | Blueprint metaclass — 6-source facet merging, ProjectionRegistry |
| `derivation.py` | Type annotation → Facet auto-derivation |
| `facets.py` | 25+ facet types with cast/seal/mold lifecycle |
| `faults.py` | Blueprint-specific faults (cast, validation, write, projection, depth) |
| `lens.py` | Relational views with depth control and cycle detection |
| `projections.py` | Named field subsets (SQL view analogy) |
| `schema.py` | JSON Schema / OpenAPI generation from Blueprints |
| `integration.py` | Controller auto-binding (request → Blueprint → response) |

### `build/` — Build Pipeline (5 files, ~2,650 lines)

Incremental compilation with content-hash caching.

| File | Purpose |
|------|---------|
| `bundler.py` | CROUS binary artifact bundling |
| `checker.py` | Pre-flight static analysis (4-phase) |
| `pipeline.py` | 5-phase build orchestrator (1,634 lines) |
| `resolver.py` | Pre-built artifact loading and verification |

### `cache/` — Caching Subsystem (14 files, ~3,600 lines)

Three-tier caching with stampede prevention.

| File | Purpose |
|------|---------|
| `base.py` | CacheEntry, CacheStats, CacheConfig, CacheBackend ABC |
| `decorators.py` | `@cached`, `@cache_result`, `@invalidate_cache` |
| `factory.py` | Backend factory from config |
| `faults.py` | 8 cache-specific faults |
| `keys.py` | ColonKeyBuilder, HashedKeyBuilder strategies |
| `middleware.py` | HTTP response caching with stale-while-revalidate |
| `serializers.py` | JSON, Pickle, Msgpack serialization strategies |
| `service.py` | CacheService — high-level API with stampede prevention |
| `backends/memory.py` | In-memory with 5 eviction policies |
| `backends/redis.py` | Redis-backed distributed cache |
| `backends/tiered.py` | L1/L2 composite cache |
| `backends/null.py` | Null object (no-op) implementation |

### `cli/` — Command-Line Interface (~19,000+ lines)

The `aq` command-line tool.

| Area | Commands |
|------|----------|
| **Core** | `init`, `run`, `serve`, `validate`, `test` |
| **Modules** | `add`, `discover`, `manifest` |
| **Build** | `compile`, `freeze`, `inspect`, `deploy` |
| **Data** | `model`, `migrate` |
| **I18n** | `i18n` extraction/compilation |
| **MLOps** | `mlops` model management |
| **Cache** | `cache` stats/clear |
| **Mail** | `mail` configuration |
| **WebSocket** | `ws` management |
| **Diagnostics** | `diagnose`, `analytics` |

### `controller/` — Controller System (12 files, ~6,600 lines)

MVC controller layer.

| File | Purpose |
|------|---------|
| `base.py` | Controller base class with lifecycle hooks, rate limiting, interceptors |
| `compiler.py` | Translates controllers into compiled route structures |
| `decorators.py` | `@Get`, `@Post`, `@Put`, `@Delete`, `@Patch`, `@Head`, `@Options`, `@Sse`, `@Route` |
| `executor.py` | 12-phase request execution engine (1,266 lines) |
| `factory.py` | DI-aware controller instantiation with scope validation |
| `filters.py` | Declarative query filtering (Django-inspired FilterSet) |
| `metadata.py` | Static metadata extraction from controllers |
| `openapi.py` | OpenAPI 3.1.0 spec generation with multi-strategy inference |
| `pagination.py` | Offset, Limit-Offset, Cursor/Keyset pagination |
| `renderers.py` | JSON, HTML, XML, YAML, MessagePack, CSV, plaintext renderers |
| `router.py` | Two-tier router (O(1) static + O(k) dynamic) |

### `db/` — Database Layer (8 files, ~2,900 lines)

Multi-backend async database abstraction.

| File | Purpose |
|------|---------|
| `config.py` | SQLiteConfig, PostgreSQLConfig, MySQLConfig, OracleConfig |
| `database.py` | Database engine with retry, transactions, savepoints |
| `base.py` | DatabaseAdapter ABC — 20+ abstract methods |
| `adapters/sqlite.py` | aiosqlite adapter |
| `adapters/postgres.py` | asyncpg adapter with `RETURNING` auto-inject |
| `adapters/mysql.py` | aiomysql adapter with dialect translation |
| `adapters/oracle.py` | oracledb adapter with thin mode |

### `debug/` — Debug Tools (2 files, ~1,100 lines)

Development-only debug pages.

| File | Purpose |
|------|---------|
| `pages.py` | Self-contained HTML error pages, traceback pages, welcome page (all CSS/JS inlined) |

### `di/` — Dependency Injection Container (14 files, ~4,500 lines)

Hierarchical IoC container.

| File | Purpose |
|------|---------|
| `container.py` | Core Container with scope hierarchy, cycle detection (Tarjan's SCC) |
| `decorators.py` | `@injectable`, `@factory`, `@provides`, `@auto_inject` |
| `descriptors.py` | `Dep`, `Header`, `Query`, `Body` injection descriptors |
| `diagnostics.py` | Observer-based DI event tracking |
| `errors.py` | Rich error hierarchy with suggested fixes |
| `graph.py` | Dependency graph analysis (Tarjan, Kahn, DOT export) |
| `lifecycle.py` | LIFO/FIFO/parallel disposal strategies |
| `providers.py` | ClassProvider, FactoryProvider, ValueProvider, PooledProvider, AliasProvider, LazyProvider, ScopedProvider, BlueprintProvider |
| `resolver.py` | Per-request DAG resolver with parallelization and generator teardown |
| `scopes.py` | SINGLETON, APP, REQUEST, TRANSIENT, POOLED, EPHEMERAL scope definitions |
| `tools.py` | CLI commands for DI debugging |
| `request_context.py` | ContextVar-based request container |
| `testing.py` | MockProvider, TestContainer, override fixtures |

### `discovery/` — Auto-Discovery (2 files, ~730 lines)

AST-based module scanning.

| File | Purpose |
|------|---------|
| `engine.py` | FileScanner → ASTClassifier → ManifestDiffer → ManifestWriter pipeline |

### `faults/` — Fault System (11 files, ~3,050 lines)

Structured error handling.

| File | Purpose |
|------|---------|
| `core.py` | Fault base class, FaultDomain, Severity, FaultContext |
| `engine.py` | FaultEngine with Chain of Responsibility handler pipeline |
| `handlers.py` | Built-in handlers (logging, response, recovery) |
| `registry.py` | Scoped fault handler registries |
| `integration.py` | Monkey-patches for DI, routing, registry, models |

### `i18n/` — Internationalization (11 files, ~3,960 lines)

| File | Purpose |
|------|---------|
| `locale.py` | BCP 47 locale parsing and validation |
| `plurals.py` | CLDR plural rules for 50+ languages |
| `messages.py` | ICU MessageFormat parser |
| `catalog.py` | Memory, File, CROUS, Namespaced, Merged catalog backends |
| `middleware.py` | 6 locale resolver strategies (header, cookie, URL, session, query, default) |
| `integration.py` | DI + template integration |

### `mail/` — Mail Subsystem (14 files, ~4,350 lines)

| File | Purpose |
|------|---------|
| `message.py` | MailMessage with attachment, inline, HTML/text body |
| `envelope.py` | MailEnvelope with SHA-256 content digest and delivery tracking |
| `composer.py` | Fluent mail composition API |
| `dispatcher.py` | Priority-ordered multi-provider dispatch |
| `providers/` | SMTP, SES, SendGrid, Console, File providers |
| `templates.py` | Template engine integration |

### `middleware_ext/` — Security Middleware (8 files, ~3,150 lines)

**Most security-critical module.**

| File | Purpose |
|------|---------|
| `cors.py` | CORS with LRU-cached origin matching |
| `csp.py` | Content Security Policy with per-request nonce |
| `csrf.py` | Synchronizer Token + HMAC-signed Double Submit Cookie |
| `hsts.py` | HTTP Strict Transport Security |
| `https_redirect.py` | HTTPS enforcement redirect |
| `proxy_fix.py` | CIDR-based trusted proxy validation |
| `security_headers.py` | Helmet-style OWASP headers |
| `rate_limit.py` | Token Bucket + Sliding Window rate limiting |
| `static.py` | Static file serving with radix trie, ETag, range requests |
| `session.py` | Session middleware with privilege change rotation |
| `di.py` | Request-scoped DI container middleware |

### `mlops/` — ML Operations Platform (69 files, ~14,200 lines)

Complete ML model serving platform.

| Area | Components |
|------|-----------|
| **Core** | BaseModel, decorator registration, inference pipeline |
| **Runtime** | Python, ONNX, Triton, TorchServe, BentoML backends |
| **Serving** | Adaptive batching, canary routing, health probes |
| **Registry** | SQLite-backed registry with S3/filesystem storage |
| **Monitoring** | Drift detection (PSI, KS, embedding), metrics, logging |
| **Deployment** | Auto-scaling, bin-packing placement, rollout management |
| **Security** | RBAC, Fernet encryption, HMAC/RSA signing |
| **Plugins** | Plugin host with marketplace support |
| **Explainability** | SHAP, LIME integrations |
| **Privacy** | PII scanning, differential privacy |

### `models/` — Pure-Python ORM (33 files, ~16,700 lines)

| File | Purpose |
|------|---------|
| `base.py` | Model base class — async CRUD, validation, serialization |
| `fields.py` | 50+ field types (2,234 lines) |
| `query.py` | Immutable QuerySet builder (1,582 lines) |
| `manager.py` | Manager/QuerySet descriptor |
| `metaclass.py` | Model metaclass — field collection, auto-PK, registration |
| `expressions.py` | Composable SQL expressions (F, Q, Case, When) |
| `aggregates.py` | SQL aggregate functions (Sum, Avg, Count, etc.) |
| `signals.py` | Model lifecycle signals (pre/post save/delete) |
| `sql_builders.py` | Parameterized SQL builder API |
| `transactions.py` | Async transaction context manager with savepoints |
| `registry.py` | Global model registry with topological table creation |
| `schema.py` | Schema snapshot/diff engine with rename heuristics |
| `constraints.py` | CHECK, EXCLUDE constraints |
| `deletion.py` | CASCADE, SET_NULL, PROTECT, RESTRICT behaviors |
| `migration/dsl.py` | Migration DSL (reversible operations) |
| `migration/generator.py` | Auto-migration generation from diffs |
| `migration/runner.py` | Transactional migration execution |
| `migration/legacy.py` | Legacy AMDL migration builder |
| `parser.py` | AMDL single-pass parser |
| `runtime.py` | AMDL dynamic proxy classes |

### `patterns/` — URL Pattern Language (14 files, ~2,800 lines)

| File | Purpose |
|------|---------|
| `ast.py` | Pattern AST nodes |
| `parser.py` | Recursive descent parser with tokenizer |
| `compiler.py` | AST → compiled regex with optimization |
| `matcher.py` | Pattern matching engine |
| `specificity.py` | CSS-like specificity scoring |
| `cache.py` | Compiled pattern cache |
| `autofix.py` | Auto-fix/quick-fix engine for pattern errors |
| `grammar.py` | EBNF grammar specification |
| `openapi.py` | OpenAPI path generation from patterns |
| `lsp/` | Language Server Protocol support for IDE integration |

### `sessions/` — Session Management (9 files, ~3,060 lines)

| File | Purpose |
|------|---------|
| `data.py` | Session entity with capabilities and metadata |
| `policy.py` | Session policy (TTL, renewal, idle timeout, security) |
| `engine.py` | Session orchestrator (create, rotate, extend, delete) |
| `stores.py` | Memory and Redis session stores |
| `transports.py` | Cookie and header transport |
| `integration.py` | DI wiring, guards, decorators |
| `faults.py` | 16 session-specific faults |
| `descriptors.py` | Typed session state descriptors |

### `sockets/` — WebSocket Subsystem (14 files, ~3,570 lines)

| File | Purpose |
|------|---------|
| `controller.py` | Declarative WebSocket controller base |
| `connection.py` | Connection entity with state machine |
| `decorators.py` | `@on_connect`, `@on_message`, `@on_disconnect`, `@on_error` |
| `messages.py` | Envelope pattern with codec/serialization |
| `compiler.py` | Build-time socket controller compilation |
| `runtime.py` | WebSocket event loop and router |
| `adapters/` | In-memory and Redis pub/sub backends |
| `guards.py` | WebSocket security guards |
| `faults.py` | Socket-specific faults |
| `middleware.py` | WebSocket middleware chain |

### `storage/` — File Storage (13 files, ~3,070 lines)

| File | Purpose |
|------|---------|
| `base.py` | StorageBackend ABC (15 abstract methods) |
| `config.py` | Backend-specific configuration objects |
| `backends/` | Filesystem, Memory, S3, GCS, Azure, FTP, Composite |
| `registry.py` | Named backend registry with health checking |
| `subsystem.py` | Storage lifecycle manager |
| `effects.py` | Effect system integration |

### `subsystems/` — Subsystem Framework (3 files, ~586 lines)

| File | Purpose |
|------|---------|
| `base.py` | BaseSubsystem ABC with timeout-guarded initialization |
| `effects.py` | Auto-discovery and wiring of effect providers |

### `tasks/` — Background Tasks (6 files, ~1,700 lines)

| File | Purpose |
|------|---------|
| `core.py` | JobState, Priority, TaskDescriptor, TaskResult |
| `manager.py` | TaskManager with worker pool, retry, dead letter |
| `decorators.py` | `@task` decorator with `delay()`, `send()`, `bind()` |
| `scheduler.py` | Cron and interval scheduling |
| `worker.py` | Background worker event loop |

### `templates/` — Jinja2 Integration (14 files, ~4,380 lines)

| File | Purpose |
|------|---------|
| `engine.py` | Core Jinja2 wrapper with async streaming |
| `loader.py` | Multi-directory loader with module prefixes |
| `cache.py` | Memory, Filesystem, Redis bytecode cache |
| `manager.py` | Template compilation and linting |
| `middleware.py` | Per-request template context injection |
| `context.py` | URL helpers, static helper, CSP nonce, CSRF token |
| `security.py` | Sandboxed execution with whitelist policy |
| `di.py` | DI provider declarations |
| `auth.py` | Auth-aware template helpers and guards |
| `sessions.py` | Session-aware template helpers with flash messages |
| `manifests.py` | Manifest-driven template discovery |
| `cli.py` | Template CLI commands (compile, lint, inspect) |

### `testing/` — Testing Framework (15 files, ~3,960 lines)

| File | Purpose |
|------|---------|
| `assertions.py` | 50+ custom assertions for HTTP, JSON, DI, cache, mail |
| `cases.py` | AquiliaTestCase, AsyncTestCase, TransactionalTestCase, LiveServerTestCase |
| `client.py` | TestClient (HTTP) and WebSocketTestClient |
| `config.py` | Test configuration with dot-notation override |
| `di.py` | MockProvider, SpyProvider, TestContainer |
| `flow.py` | MockEffectProvider, MockFlowContext |
| `faults.py` | FaultCapture for testing fault emission |
| `identity.py` | IdentityFactory and AuthTestMixin |
| `cache.py` | MockCacheService and CacheTestMixin |
| `mail.py` | MockMailProvider and MailTestMixin |
| `server.py` | Lightweight test server lifecycle |
| `fixtures.py` | pytest fixtures for all subsystems |
| `factories.py` | Test data factory functions |

### `utils/` — Utilities (4 files, ~314 lines)

| File | Purpose |
|------|---------|
| `attrdict.py` | Dict with attribute-style access |
| `discovery.py` | Auto-discover controllers/services from packages |
| `paths.py` | Safe URL path joining |
