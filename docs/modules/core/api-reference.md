# Core API Reference

This page is generated from the current Python source using the AST. It lists public classes, public methods, public module-level functions, constants, exports, and source files.

## Source Inventory

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/__init__.py` | 1581 | 0 | 0 | Aquilia - Production-ready async Python web framework |
| `aquilia/_datastructures.py` | 440 | 5 | 2 | Core data structures for Aquilia Request handling. |
| `aquilia/_uploads.py` | 431 | 4 | 2 | Upload file handling for Aquilia Request. |
| `aquilia/_version.py` | 26 | 0 | 0 | Single source of truth for the Aquilia framework version. |
| `aquilia/asgi.py` | 641 | 1 | 0 | ASGI adapter -- Bridges the ASGI protocol to Aquilia's request / response system. Supports HTTP, WebSocket, and Lifespan events. |
| `aquilia/config.py` | 969 | 4 | 0 | Config system - Layered typed configuration with validation. Supports dataclass/pydantic-like behavior with merge precedence. |
| `aquilia/config_builders.py` | 5650 | 6 | 0 | Fluent Configuration Builders for Aquilia. |
| `aquilia/dotenv.py` | 898 | 2 | 6 | Aquilia Native Dotenv Loader (``aquilia.dotenv``) ================================================= |
| `aquilia/effects.py` | 794 | 21 | 0 | Effect System -- Typed Capabilities with Providers and Layers. |
| `aquilia/engine.py` | 295 | 3 | 1 | Engine -- Core runtime primitives for the Aquilia request lifecycle. |
| `aquilia/entrypoint.py` | 206 | 0 | 1 | Aquilia ASGI Entrypoint — Zero-Config Production Application Factory. |
| `aquilia/flow.py` | 1622 | 10 | 8 | Aquilia Flow -- Typed Pipeline System with Effect Integration. |
| `aquilia/health.py` | 162 | 3 | 0 | Health Registry -- Centralized subsystem health tracking. |
| `aquilia/lifecycle.py` | 363 | 5 | 1 | Lifecycle Coordinator - Orchestrates startup and shutdown hooks. |
| `aquilia/manifest.py` | 663 | 14 | 0 | AppManifest - Production-grade, data-driven application manifest system. |
| `aquilia/middleware.py` | 648 | 8 | 0 | Middleware system - Composable, async-first middleware with effect awareness. |
| `aquilia/pyconfig.py` | 1644 | 4 | 2 | Aquilia Python-Native Configuration System  (``aquilia.pyconfig``) ================================================================== |
| `aquilia/request.py` | 1998 | 11 | 0 | Request - Production-grade ASGI request wrapper. |
| `aquilia/response.py` | 2037 | 14 | 14 | Response - Production-grade HTTP response builder with streaming support. |
| `aquilia/runtime.py` | 721 | 3 | 0 | AquiliaRuntime — Structured ASGI Bootstrap Lifecycle Manager. |
| `aquilia/server.py` | 4001 | 1 | 0 | AquiliaServer - Main server orchestrating all components with lifecycle management. |
| `aquilia/signing.py` | 1532 | 13 | 9 | Aquilia Signing Engine  (``aquilia.signing``) ============================================= |

## Public Exports

`AMDLFile`, `AMDLParseError`, `AMDLParseFault`, `APIKeySigner`, `ActivationLinkSigner`, `AdminAction`, `AdminActionFault`, `AdminAudit`, `AdminAuditLog`, `AdminAuthenticationFault`, `AdminAuthorizationFault`, `AdminContainers`, `AdminController`, `AdminFault`, `AdminGuard`, `AdminIntegration`, `AdminModelNotFoundFault`, `AdminModules`, `AdminMonitoring`, `AdminPermission`, `AdminPods`, `AdminRecordNotFoundFault`, `AdminRole`, `AdminSecurity`, `AdminSidebar`, `AdminSite`, `AdminValidationFault`, `Algorithm`, `ApiVersion`, `AppContext`, `AppManifest`, `AquilAuthMiddleware`, `AquilaConfig`, `AquilaSockets`, `Aquilary`, `AquilaryRegistry`, `AquiliaDatabase`, `AquiliaRuntime`, `AquiliaServer`, `AquiliaTestCase`, `ArrayField`, `Artifact`, `ArtifactBuilder`, `ArtifactEnvelope`, `ArtifactIntegrity`, `ArtifactKind`, `ArtifactProvenance`, `ArtifactReader`, `ArtifactStore`, `AuthConfig`, `AuthIntegration`, `AuthManager`, `AuthPrincipal`, `AuthzEngine`, `AutoField`, `AzureBlobConfig`, `AzureBlobStorage`, `BackgroundTask`, `BadRequest`, `BadSignature`, `BaseFilterBackend`, `BigAutoField`, `BigIntegerField`, `BinaryField`, `Contract`, `ContractFault`, `ContractMeta`, `BoolFacet`, `BooleanField`, `BundleArtifact`, `CORSMiddleware`, `SURP_MEDIA_TYPE`, `CSPMiddleware`, `CSPPolicy`, `CSRFError`, `CSRFMiddleware`, `CSRFSigner`, `CacheBackend`, `CacheBackendFault`, `CacheCapacityFault`, `CacheConfig`, `CacheConfigFault`, `CacheConnectionFault`, `CacheEffect`, `CacheEntry`, `CacheFault`, `CacheHealthFault`, `CacheIntegration`, `CacheKeySigner`, `CacheMiddleware`, `CacheMissFault`, `CacheProvider`, `CacheSerializationFault`, `CacheService`, `CacheStampedeFault`, `CacheStats`, `CallableBackgroundTask`, `CartState`, `CastFault`, `CatalogLoadFault`, `ChannelResolver`, `CharField`, `ChoiceFacet`, `ClassProvider`, `ClientDisconnectError`, `CodeArtifact`, `CompiledPattern`, `CompositeBackend`, `CompositeConfig`, `CompositeResolver`, `CompositeStorage`, `Computed`, `Config`, `ConfigArtifact`, `ConfigLoader`, `ConfigValue`, `ConsoleProvider`, `Constant`, `Container`, `ContentNegotiator`, `Controller`, `ControllerFactory`, `ControllerGuardAdapter`, `ControllerMetadata`, `CookieSigner`, `CookieTransport`, `CorsIntegration`, `Created`, `CspIntegration`, `CsrfIntegration`, `CursorPagination`, `DBTx`, `DBTxProvider`, `DELETE`, `DIGraphArtifact`, `DIRegistry`, `DatabaseConfig`, `DatabaseConnectionFault`, `DatabaseError`, `DatabaseIntegration`, `DateFacet`, `DateField`, `DateTimeFacet`, `DateTimeField`, `DebugPageRenderer`, `DecimalFacet`, `DecimalField`, `DefaultKeyBuilder`, `DiIntegration`, `DictFacet`, `DotEnv`, `DotEnvLoader`, `DurationFacet`, `DurationField`, `Effect`, `EffectKind`, `EffectProvider`, `EffectRegistry`, `EffectScope`, `EmailFacet`, `EmailField`, `EmailMessage`, `EmailMultiAlternatives`, `Env`, `EnvCastType`, `EnvCaster`, `EnvelopeStatus`, `Event`, `EvictionPolicy`, `Facet`, `FactoryProvider`, `Fault`, `FaultContext`, `FaultEngine`, `FaultHandler`, `FaultHandlingIntegration`, `Field`, `FieldType`, `FieldValidationError`, `FileCatalog`, `FileFacet`, `FileField`, `FilePathField`, `FileProvider`, `FilesystemArtifactStore`, `FilterSet`, `FloatFacet`, `FloatField`, `FlowContext`, `FlowError`, `FlowGuard`, `FlowNode`, `FlowNodeType`, `FlowPipeline`, `FlowResult`, `FlowStatus`, `Forbidden`, `ForeignKey`, `FormData`, `GCSConfig`, `GCSStorage`, `GET`, `GeneratedField`, `GenericIPAddressField`, `HEAD`, `HLSManifestError`, `HLSSegment`, `HLSVariant`, `HSTSMiddleware`, `HStoreField`, `HTMLRenderer`, `HTTPEffect`, `HTTPProvider`, `HTTPSRedirectMiddleware`, `Handler`, `HashKeyBuilder`, `HeaderResolver`, `Headers`, `Hidden`, `HmacSignerBackend`, `HookNode`, `I18nConfig`, `I18nFault`, `I18nIntegration`, `I18nMiddleware`, `I18nService`, `IMailProvider`, `IPFacet`, `Identity`, `ImageField`, `ImprintFault`, `Index`, `Inject`, `InstantiationMode`, `IntFacet`, `IntegerField`, `Integration`, `IntegrationConfig`, `InternalError`, `InvalidHeaderError`, `InvalidLocaleFault`, `InvalidVersionError`, `JSONFacet`, `JSONField`, `JSONRenderer`, `Job`, `JobResult`, `JobState`, `JsonCacheSerializer`, `KeyRing`, `Layer`, `LayerComposition`, `LazyString`, `LegacyIndexNode`, `Lens`, `LifecycleCoordinator`, `LifecycleManager`, `LimitOffsetPagination`, `LinkKind`, `LinkNode`, `ListFacet`, `LiveServerTestCase`, `LocalConfig`, `LocalStorage`, `LocalUploadStore`, `Locale`, `LoggingIntegration`, `MLOpsIntegration`, `MailAuth`, `MailConfig`, `MailConfigFault`, `MailEnvelope`, `MailFault`, `MailIntegration`, `MailRateLimitFault`, `MailSendFault`, `MailService`, `MailSuppressedFault`, `MailTemplateFault`, `MailValidationFault`, `ManyToManyField`, `MediaChunk`, `MediaTypeResolver`, `MemoryArtifactStore`, `MemoryBackend`, `MemoryCatalog`, `MemoryConfig`, `MemoryStorage`, `MergedCatalog`, `MessageFormatter`, `MetaNode`, `Middleware`, `MiddlewareChain`, `MiddlewareEntry`, `MiddlewareStack`, `MigrationArtifact`, `MigrationConflictFault`, `MigrationFault`, `MigrationOps`, `MigrationRunner`, `MissingTranslationFault`, `MissingVersionError`, `Model`, `ModelAdmin`, `ModelArtifact`, `ModelFault`, `ModelMeta`, `ModelNode`, `ModelNotFoundFault`, `ModelProxy`, `ModelRegistrationFault`, `ModelRegistry`, `Module`, `ModuleConfig`, `MultiDict`, `NamespacedCatalog`, `NoContent`, `NoPagination`, `NotFound`, `NoteNode`, `NullBackend`, `OPTIONS`, `Ok`, `OnConnect`, `OnDisconnect`, `OneToOneField`, `OpenAPIIntegration`, `OrderingFilter`, `PATCH`, `POST`, `PRIORITY_AUTH`, `PRIORITY_CLEANUP`, `PRIORITY_CRITICAL`, `PRIORITY_DEFAULT`, `PRIORITY_ENRICH`, `PRIORITY_LOG`, `PRIORITY_TRANSFORM`, `PRIORITY_VALIDATE`, `PUT`, `PackageScanner`, `PageNumberPagination`, `ParsedContentType`, `PasswordHasher`, `PatternCompiler`, `PatternMatcher`, `PatternTypeRegistry`, `PatternsIntegration`, `PickleCacheSerializer`, `PlainTextRenderer`, `PluralCategory`, `PluralRuleFault`, `PositiveIntegerField`, `PositiveSmallIntegerField`, `Priority`, `ProjectionFault`, `Provider`, `ProviderMeta`, `ProviderResult`, `ProviderResultStatus`, `ProxyFixMiddleware`, `PyConfigLoader`, `Q`, `QueryFault`, `QueryParamResolver`, `QueueEffect`, `QueueProvider`, `Range`, `RangeNotSatisfiableError`, `RateLimitIntegration`, `RateLimitMiddleware`, `RateLimitRule`, `ReadOnly`, `RecoveryStrategy`, `RedisBackend`, `RegistryArtifact`, `RegistryIntegration`, `RegistryMode`, `RenderIntegration`, `Request`, `RequestCtx`, `RequireAuthGuard`, `RequirePermissionGuard`, `RequirePolicyGuard`, `RequireRolesGuard`, `RequireScopesGuard`, `Response`, `ResponseStreamError`, `RotatingSigner`, `RouteArtifact`, `RoutingIntegration`, `RuntimeConfig`, `RuntimePhase`, `RuntimeRegistry`, `S3Config`, `S3Storage`, `SFTPConfig`, `SFTPStorage`, `SchemaFault`, `SealFault`, `SearchFilter`, `Secret`, `SecurityHeadersMiddleware`, `SendGridProvider`, `SerializersIntegration`, `ServerSentEvent`, `SesProvider`, `Session`, `SessionAuthBridge`, `SessionContext`, `SessionEngine`, `SessionField`, `SessionGuard`, `SessionID`, `SessionIntegration`, `SessionMemoryStore`, `SessionPolicy`, `SessionPrincipal`, `SessionSigner`, `SessionState`, `SignatureExpired`, `SignatureMalformed`, `Signer`, `SignerBackend`, `SigningConfig`, `SigningError`, `SimpleTestCase`, `SlotNode`, `SlugFacet`, `SlugField`, `SmallIntegerField`, `SmtpProvider`, `Socket`, `SocketController`, `SocketGuard`, `SocketRouter`, `StaticFilesIntegration`, `StaticMiddleware`, `StorageBackend`, `StorageConfig`, `StorageEffect`, `StorageEffectProvider`, `StorageError`, `StorageFile`, `StorageIntegration`, `StorageMetadata`, `StorageProvider`, `StorageRegistry`, `StorageSubsystem`, `SunsetPolicy`, `SunsetRegistry`, `TaskBackend`, `TaskManager`, `TaskPriority`, `TasksIntegration`, `TemplateArtifact`, `TemplateEngine`, `TemplateMessage`, `TemplateMiddleware`, `TemplateRenderError`, `TemplatesIntegration`, `TestClient`, `TestServer`, `TextFacet`, `TextField`, `TimeFacet`, `TimeField`, `TimestampSigner`, `TokenManager`, `TransactionTestCase`, `TranslationCatalog`, `TransportPolicy`, `URL`, `URLFacet`, `URLField`, `URLPathResolver`, `UUIDFacet`, `UUIDField`, `Unauthorized`, `UniqueConstraint`, `UnsupportedAlgorithmError`, `UnsupportedVersionError`, `UploadFile`, `UploadStore`, `UserPreferencesState`, `VERSION_ANY`, `VERSION_NEUTRAL`, `ValueProvider`, `VerifiedEmailGuard`, `VersionChannel`, `VersionConfig`, `VersionError`, `VersionGraph`, `VersionMiddleware`, `VersionNegotiator`, `VersionStatus`, `VersionStrategy`, `VersionSunsetError`, `VersioningIntegration`, `WS`, `Worker`, `Workspace`, `WriteOnly`, `XMLRenderer`, `YAMLRenderer`, `api_session_policy`, `app`, `asend_mail`, `authenticated`, `autodiscover`, `b64_decode`, `b64_encode`, `bind_contract_to_request`, `bind_identity`, `cache_aside`, `cached`, `check_not_modified`, `configure_database`, `configure_signing`, `constant_time_compare`, `create_app`, `create_auth_container`, `create_auth_middleware_stack`, `create_i18n_service`, `csrf_exempt`, `csrf_token_func`, `derive_key`, `dotenv_values`, `dumps`, `ensure_dotenv_loaded`, `extract_controller_metadata`, `factory`, `find_dotenv`, `format_currency`, `format_date`, `format_datetime`, `format_message`, `format_number`, `format_ordinal`, `format_percent`, `format_time`, `from_pipeline_list`, `generate_component_schemas`, `generate_etag`, `generate_etag_from_file`, `generate_migration_file`, `generate_schema`, `get_database`, `get_default_cache_service`, `get_required_effects`, `guard`, `handler`, `has_surp`, `hook`, `inject`, `invalidate`, `is_contract_class`, `is_dotenv_loaded`, `lazy_t`, `lazy_tn`, `load_dotenv`, `loads`, `make_signer`, `make_timestamp_signer`, `match_locale`, `negotiate_locale`, `normalize_locale`, `not_modified_response`, `override_settings`, `parse_amdl`, `parse_amdl_directory`, `parse_amdl_file`, `parse_locale`, `pipeline`, `register`, `register_artifact_kind`, `register_auth_providers`, `render_contract_response`, `render_debug_exception_page`, `render_http_error_page`, `render_welcome_page`, `require_auth`, `require_permission`, `require_roles`, `require_scopes`, `requires`, `requires_surp`, `reset_dotenv_state`, `route`, `section`, `select_plural`, `send_mail`, `server`, `service`, `session`, `set_database`, `set_default_cache_service`, `signing_dumps`, `signing_loads`, `stateful`, `task`, `transform`, `user_session_policy`, `version`, `version_neutral`, `version_range`

## Public Class Summary

| Class | Source | Bases | Summary |
| --- | --- | --- | --- |
| `MultiDict` | `aquilia/_datastructures.py` | MutableMapping[str, list[str]] | Dictionary that supports multiple values per key. |
| `Headers` | `aquilia/_datastructures.py` | object | Case-insensitive header access with raw preservation. |
| `URL` | `aquilia/_datastructures.py` | object | Parsed URL representation. |
| `ParsedContentType` | `aquilia/_datastructures.py` | object | Parsed Content-Type header. |
| `Range` | `aquilia/_datastructures.py` | object | Parsed HTTP Range header. |
| `UploadFile` | `aquilia/_uploads.py` | object | Uploaded file representation. |
| `FormData` | `aquilia/_uploads.py` | object | Parsed form data containing both fields and files. |
| `UploadStore` | `aquilia/_uploads.py` | Protocol | Protocol for upload storage backends. |
| `LocalUploadStore` | `aquilia/_uploads.py` | object | Local filesystem upload store. |
| `ASGIAdapter` | `aquilia/asgi.py` | object | ASGI application adapter. Converts ASGI events to Aquilia Request/Response. Uses controller-based routing exclusively. |
| `NestedNamespace` | `aquilia/config.py` | object | A namespace that supports nested attribute access for app configs. Enables syntax like: config.apps.auth.secret_key |
| `Config` | `aquilia/config.py` | object | Base class for typed configuration classes. |
| `ConfigError` | `aquilia/config.py` | Exception | Raised when configuration validation fails. |
| `ConfigLoader` | `aquilia/config.py` | object | Loads and merges configuration from multiple sources with precedence: CLI args > Environment variables > .env files > config files > defaults |
| `RuntimeConfig` | `aquilia/config_builders.py` | object | Runtime configuration. |
| `ModuleConfig` | `aquilia/config_builders.py` | object | Module configuration -- workspace-level orchestration metadata. |
| `Module` | `aquilia/config_builders.py` | object | Fluent module builder -- workspace-level orchestration only. |
| `AuthConfig` | `aquilia/config_builders.py` | object | Authentication configuration. |
| `Integration` | `aquilia/config_builders.py` | object | Integration configuration builders. |
| `Workspace` | `aquilia/config_builders.py` | object | Fluent workspace builder. |
| `DotEnv` | `aquilia/dotenv.py` | object | Native dotenv file parser and loader. |
| `DotEnvLoader` | `aquilia/dotenv.py` | object | Singleton loader that ensures .env files are loaded exactly once. |
| `EffectKind` | `aquilia/effects.py` | Enum | Categories of effects. |
| `Effect` | `aquilia/effects.py` | Generic[T] | Effect token representing a capability. |
| `EffectProvider` | `aquilia/effects.py` | ABC | Base class for effect providers. |
| `DBTx` | `aquilia/effects.py` | Effect | Database transaction effect. |
| `CacheEffect` | `aquilia/effects.py` | Effect | Cache effect. |
| `QueueEffect` | `aquilia/effects.py` | Effect | Queue/message publish effect. |
| `HTTPEffect` | `aquilia/effects.py` | Effect | HTTP client effect for outbound requests. |
| `StorageEffect` | `aquilia/effects.py` | Effect | File/blob storage effect. |
| `DBTxProvider` | `aquilia/effects.py` | EffectProvider | Database transaction provider. |
| `CacheProvider` | `aquilia/effects.py` | EffectProvider | Cache effect provider backed by the real CacheService. |
| `QueueProvider` | `aquilia/effects.py` | EffectProvider | Queue/message publish effect provider. |
| `TaskQueueProvider` | `aquilia/effects.py` | EffectProvider | Task queue effect provider backed by AquilaTasks TaskManager. |
| `HTTPProvider` | `aquilia/effects.py` | EffectProvider | HTTP client effect provider for outbound requests. |
| `StorageProvider` | `aquilia/effects.py` | EffectProvider | File/blob storage effect provider. |
| `CacheServiceHandle` | `aquilia/effects.py` | object | Handle wrapping real CacheService for a given namespace. |
| `CacheHandle` | `aquilia/effects.py` | object | Handle for cache operations in a namespace. |
| `QueueHandle` | `aquilia/effects.py` | object | Handle for queue operations on a topic. |
| `TaskQueueHandle` | `aquilia/effects.py` | object | Handle for enqueuing background tasks via the TaskManager. |
| `HTTPHandle` | `aquilia/effects.py` | object | Handle for outbound HTTP requests. |
| `StorageHandle` | `aquilia/effects.py` | object | Handle for file/blob storage operations. |
| `EffectRegistry` | `aquilia/effects.py` | object | Registry for effect providers. |
| `LifecycleHook` | `aquilia/engine.py` | Enum | Named lifecycle points that subsystems can subscribe to. |
| `EngineMetrics` | `aquilia/engine.py` | object | Lightweight in-process metrics for the Aquilia engine. |
| `RequestCtx` | `aquilia/engine.py` | object | Per-request execution context. |
| `FlowNodeType` | `aquilia/flow.py` | str, Enum | Types of nodes in a flow pipeline. |
| `FlowStatus` | `aquilia/flow.py` | str, Enum | Pipeline execution outcome. |
| `FlowContext` | `aquilia/flow.py` | object | Typed execution context threaded through the entire flow pipeline. |
| `FlowNode` | `aquilia/flow.py` | object | A typed unit in a flow pipeline. |
| `FlowResult` | `aquilia/flow.py` | object | Result of a flow pipeline execution. |
| `FlowError` | `aquilia/flow.py` | Exception | Raised when a flow pipeline encounters an unrecoverable error. |
| `Layer` | `aquilia/flow.py` | object | Composable effect layer -- separates effect construction from usage. |
| `LayerComposition` | `aquilia/flow.py` | object | A composition of multiple layers, resolved in dependency order. |
| `FlowPipeline` | `aquilia/flow.py` | object | Composable, typed request pipeline with automatic effect management. |
| `EffectScope` | `aquilia/flow.py` | object | Async context manager that acquires and releases effects. |
| `SubsystemStatus` | `aquilia/health.py` | str, Enum | Status of a subsystem. |
| `HealthStatus` | `aquilia/health.py` | object | Health status for a single subsystem. |
| `HealthRegistry` | `aquilia/health.py` | object | Centralized health tracking for all subsystems. |
| `LifecyclePhase` | `aquilia/lifecycle.py` | Enum | Lifecycle phases. |
| `LifecycleEvent` | `aquilia/lifecycle.py` | object | Event emitted during lifecycle transitions. |
| `LifecycleError` | `aquilia/lifecycle.py` | Exception | Raised when lifecycle operation fails. |
| `LifecycleCoordinator` | `aquilia/lifecycle.py` | object | Coordinates application lifecycle across multiple apps. |
| `LifecycleManager` | `aquilia/lifecycle.py` | object | High-level lifecycle manager with context manager support. |
| `ComponentKind` | `aquilia/manifest.py` | str, Enum | Classification of framework components for auto-discovery. |
| `ComponentRef` | `aquilia/manifest.py` | object | Universal typed reference to any framework component. |
| `ServiceScope` | `aquilia/manifest.py` | str, Enum | Service lifecycle scope. |
| `LifecycleConfig` | `aquilia/manifest.py` | object | Lifecycle hook configuration. |
| `ServiceConfig` | `aquilia/manifest.py` | object | Service registration configuration with complete DI support. |
| `MiddlewareConfig` | `aquilia/manifest.py` | object | Middleware registration configuration. |
| `SessionConfig` | `aquilia/manifest.py` | object | Session management configuration. |
| `FaultHandlerConfig` | `aquilia/manifest.py` | object | Fault handler configuration. |
| `FaultHandlingConfig` | `aquilia/manifest.py` | object | Fault/error handling configuration. |
| `FeatureConfig` | `aquilia/manifest.py` | object | Feature flag configuration. |
| `BackgroundTaskConfig` | `aquilia/manifest.py` | object | Per-module background task configuration. |
| `TemplateConfig` | `aquilia/manifest.py` | object | Template engine configuration. |
| `DatabaseConfig` | `aquilia/manifest.py` | object | DEPRECATED: Manifest-level database configuration. |
| `AppManifest` | `aquilia/manifest.py` | object | Production-grade application manifest for complete app configuration. |
| `MiddlewareDescriptor` | `aquilia/middleware.py` | object | Descriptor for middleware registration. |
| `MiddlewareStack` | `aquilia/middleware.py` | object | Manages middleware stack with deterministic ordering. Order: Global < App < Controller < Route, then by priority. |
| `RequestIdMiddleware` | `aquilia/middleware.py` | object | Adds unique request ID to each request. |
| `ExceptionMiddleware` | `aquilia/middleware.py` | object | Catches exceptions and converts them to error responses. |
| `LoggingMiddleware` | `aquilia/middleware.py` | object | Logs request/response with timing. |
| `TimeoutMiddleware` | `aquilia/middleware.py` | object | Enforces request timeout. |
| `CORSMiddleware` | `aquilia/middleware.py` | object | Handles CORS headers. |
| `CompressionMiddleware` | `aquilia/middleware.py` | object | Compresses response bodies. |
| `Secret` | `aquilia/pyconfig.py` | object | A configuration field that holds a sensitive value (password, API key …). |
| `Env` | `aquilia/pyconfig.py` | object | Bind a configuration field to an environment variable. |
| `AquilaConfig` | `aquilia/pyconfig.py` | object | Base class for Aquilia Python-native configuration. |
| `PyConfigLoader` | `aquilia/pyconfig.py` | object | Load an ``AquilaConfig`` subclass from a Python source file. |
| `RequestFault` | `aquilia/request.py` | Fault | Base class for request-related faults. |
| `BadRequest` | `aquilia/request.py` | RequestFault | Malformed request (400). |
| `PayloadTooLarge` | `aquilia/request.py` | RequestFault | Request payload exceeds limits (413). |
| `UnsupportedMediaType` | `aquilia/request.py` | RequestFault | Unsupported Content-Type (415). |
| `ClientDisconnect` | `aquilia/request.py` | RequestFault | Client disconnected during request (499). |
| `InvalidJSON` | `aquilia/request.py` | RequestFault | Invalid JSON payload (400). |
| `InvalidSurp` | `aquilia/request.py` | RequestFault | Invalid SURP binary payload (400). |
| `SurpUnavailable` | `aquilia/request.py` | RequestFault | SURP library not installed (500-level). |
| `InvalidHeader` | `aquilia/request.py` | RequestFault | Invalid header format (400). |
| `MultipartParseError` | `aquilia/request.py` | RequestFault | Multipart parsing failed (400). |
| `Request` | `aquilia/request.py` | object | Production-grade request object for Aquilia. |
| `BackgroundTask` | `aquilia/response.py` | Protocol | Protocol for background tasks executed after response is sent. |
| `CallableBackgroundTask` | `aquilia/response.py` | object | Simple callable-based background task. |
| `ServerSentEvent` | `aquilia/response.py` | object | Server-Sent Event data structure. |
| `MediaChunk` | `aquilia/response.py` | object | Type-safe media chunk container for streaming payloads. |
| `HLSSegment` | `aquilia/response.py` | object | Single media segment entry in an HLS media playlist. |
| `HLSVariant` | `aquilia/response.py` | object | Variant stream descriptor for an HLS master playlist. |
| `CookieSigner` | `aquilia/response.py` | object | Cookie signer with HMAC-based signing and key rotation support. |
| `ResponseStreamError` | `aquilia/response.py` | Fault | Error during response streaming. |
| `TemplateRenderError` | `aquilia/response.py` | Fault | Template rendering error during response. |
| `InvalidHeaderError` | `aquilia/response.py` | Fault | Invalid header name or value (injection attempt). |
| `ClientDisconnectError` | `aquilia/response.py` | Fault | Client disconnected during response send. |
| `RangeNotSatisfiableError` | `aquilia/response.py` | Fault | Invalid Range header (416 response). |
| `HLSManifestError` | `aquilia/response.py` | Fault | Invalid HLS manifest payload or helper usage. |
| `Response` | `aquilia/response.py` | object | Production-grade HTTP response with ASGI 3 streaming support. |
| `RuntimePhase` | `aquilia/runtime.py` | str, Enum | Lifecycle phase of an :class:`AquiliaRuntime` instance. |
| `RuntimeConfig` | `aquilia/runtime.py` | object | Immutable configuration for an :class:`AquiliaRuntime` instance. |
| `AquiliaRuntime` | `aquilia/runtime.py` | object | Structured ASGI bootstrap lifecycle manager. |
| `AquiliaServer` | `aquilia/server.py` | object | Main Aquilia server that orchestrates all components with lifecycle management. |
| `SignerBackend` | `aquilia/signing.py` | ABC | Abstract backend that produces and verifies raw byte signatures. |
| `HmacSignerBackend` | `aquilia/signing.py` | SignerBackend | Default signing backend — HMAC with a configurable digest. |
| `AsymmetricSignerBackend` | `aquilia/signing.py` | SignerBackend | Asymmetric signing backend using the ``cryptography`` package. |
| `Signer` | `aquilia/signing.py` | object | Simple HMAC-based data signer. |
| `TimestampSigner` | `aquilia/signing.py` | Signer | Signer that embeds a UTC timestamp in the signed value. |
| `RotatingSigner` | `aquilia/signing.py` | object | A signer that supports transparent key rotation. |
| `SessionSigner` | `aquilia/signing.py` | TimestampSigner | Timestamped signer for Aquilia session cookies. |
| `CSRFSigner` | `aquilia/signing.py` | Signer | Signer for CSRF tokens. |
| `ActivationLinkSigner` | `aquilia/signing.py` | TimestampSigner | Timestamped signer for one-time activation / password-reset URLs. |
| `CacheKeySigner` | `aquilia/signing.py` | Signer | Signer for cache key integrity verification. |
| `CookieSigner` | `aquilia/signing.py` | TimestampSigner | Timestamped signer for signed HTTP cookies (non-session). |
| `APIKeySigner` | `aquilia/signing.py` | TimestampSigner | Timestamped signer for short-lived API access keys / signed URLs. |
| `SigningConfig` | `aquilia/signing.py` | object | Runtime signing configuration. |

## Public Function Summary

| Function | Source | Signature | Summary |
| --- | --- | --- | --- |
| `parse_date_header` | `aquilia/_datastructures.py` | `def parse_date_header(date_str: str \| None)` | Parse HTTP date header. |
| `parse_authorization_header` | `aquilia/_datastructures.py` | `def parse_authorization_header(auth_header: str \| None)` | Parse Authorization header. |
| `create_upload_file_from_bytes` | `aquilia/_uploads.py` | `def create_upload_file_from_bytes(filename: str, content: bytes, content_type: str='application/octet-stream')` | Create an UploadFile from bytes (in-memory). |
| `create_upload_file_from_path` | `aquilia/_uploads.py` | `def create_upload_file_from_path(filename: str, file_path: Path, content_type: str='application/octet-stream')` | Create an UploadFile from a disk path. |
| `find_dotenv` | `aquilia/dotenv.py` | `def find_dotenv(filename: str='.env', raise_error: bool=False, usecwd: bool=False)` | Search for a .env file. |
| `load_dotenv` | `aquilia/dotenv.py` | `def load_dotenv(dotenv_path: str \| Path \| None=None, *, override: bool=False, interpolate: bool=True, encoding: str='utf-8')` | Load a .env file into os.environ. |
| `dotenv_values` | `aquilia/dotenv.py` | `def dotenv_values(dotenv_path: str \| Path \| None=None, *, interpolate: bool=True, encoding: str='utf-8')` | Parse a .env file and return values WITHOUT loading into os.environ. |
| `ensure_dotenv_loaded` | `aquilia/dotenv.py` | `def ensure_dotenv_loaded(path: str \| Path \| None=None, *, auto_load: bool \| None=None)` | Ensure dotenv is loaded (idempotent). |
| `is_dotenv_loaded` | `aquilia/dotenv.py` | `def is_dotenv_loaded()` | Check if dotenv has been loaded. |
| `reset_dotenv_state` | `aquilia/dotenv.py` | `def reset_dotenv_state()` | Reset dotenv loaded state. |
| `get_engine_metrics` | `aquilia/engine.py` | `def get_engine_metrics()` | Return the process-level engine metrics singleton. |
| `create_app` | `aquilia/entrypoint.py` | `def create_app(workspace_root: Path \| None=None, mode: str \| None=None)` | Create the ASGI application from workspace configuration. |
| `requires` | `aquilia/flow.py` | `def requires(*effect_names: str)` | Decorator declaring effect dependencies on a handler or flow node. |
| `get_required_effects` | `aquilia/flow.py` | `def get_required_effects(func: Callable)` | Extract declared effect requirements from a callable. |
| `pipeline` | `aquilia/flow.py` | `def pipeline(name: str='pipeline', *, timeout: float \| None=None)` | Create a new FlowPipeline. |
| `guard` | `aquilia/flow.py` | `def guard(fn: Callable, *, name: str \| None=None, priority: int=PRIORITY_AUTH, effects: list[str] \| None=None)` | Create a guard FlowNode. |
| `transform` | `aquilia/flow.py` | `def transform(fn: Callable, *, name: str \| None=None, priority: int=PRIORITY_TRANSFORM, effects: list[str] \| None=None)` | Create a transform FlowNode. |
| `handler` | `aquilia/flow.py` | `def handler(fn: Callable, *, name: str \| None=None, priority: int=PRIORITY_DEFAULT, effects: list[str] \| None=None)` | Create a handler FlowNode. |
| `hook` | `aquilia/flow.py` | `def hook(fn: Callable, *, name: str \| None=None, priority: int=PRIORITY_LOG, effects: list[str] \| None=None)` | Create a hook FlowNode. |
| `from_pipeline_list` | `aquilia/flow.py` | `def from_pipeline_list(nodes: Sequence[Any], *, name: str='controller_pipeline')` | Convert a controller-style pipeline list to a FlowPipeline. |
| `create_lifecycle_coordinator` | `aquilia/lifecycle.py` | `def create_lifecycle_coordinator(runtime: Any, config: Any=None)` | Factory function to create lifecycle coordinator. |
| `reset_dotenv_state` | `aquilia/pyconfig.py` | `def reset_dotenv_state()` | Reset the dotenv loading state. |
| `section` | `aquilia/pyconfig.py` | `def section(cls: type)` | Mark a nested class as a config *section*. |
| `has_surp` | `aquilia/response.py` | `def has_surp()` | Return ``True`` if the ``surp`` library is importable. |
| `Ok` | `aquilia/response.py` | `def Ok(content: Any=None, **kwargs)` | 200 OK response. |
| `Created` | `aquilia/response.py` | `def Created(content: Any=None, location: str \| None=None, **kwargs)` | 201 Created response. |
| `NoContent` | `aquilia/response.py` | `def NoContent()` | 204 No Content response. |
| `BadRequest` | `aquilia/response.py` | `def BadRequest(message: str='Bad Request', **kwargs)` | 400 Bad Request response. |
| `Unauthorized` | `aquilia/response.py` | `def Unauthorized(message: str='Unauthorized', **kwargs)` | 401 Unauthorized response. |
| `Forbidden` | `aquilia/response.py` | `def Forbidden(message: str='Forbidden', **kwargs)` | 403 Forbidden response. |
| `NotFound` | `aquilia/response.py` | `def NotFound(message: str='Not Found', **kwargs)` | 404 Not Found response. |
| `InternalError` | `aquilia/response.py` | `def InternalError(message: str='Internal Server Error', **kwargs)` | 500 Internal Server Error response. |
| `generate_etag` | `aquilia/response.py` | `def generate_etag(content: bytes, weak: bool=False)` | Generate ETag from content. |
| `generate_etag_from_file` | `aquilia/response.py` | `def generate_etag_from_file(path: PathLike, weak: bool=True)` | Generate ETag from file metadata. |
| `check_not_modified` | `aquilia/response.py` | `def check_not_modified(request: Any, etag: str \| None=None, last_modified: datetime \| None=None)` | Check if response should be 304 Not Modified. |
| `not_modified_response` | `aquilia/response.py` | `def not_modified_response(etag: str \| None=None)` | Create 304 Not Modified response. |
| `requires_surp` | `aquilia/response.py` | `def requires_surp(func: Callable)` | Mark a handler as preferring SURP binary responses. |
| `b64_encode` | `aquilia/signing.py` | `def b64_encode(data: bytes)` | URL-safe, no-padding Base64 encode. |
| `b64_decode` | `aquilia/signing.py` | `def b64_decode(data: str \| bytes)` | URL-safe, no-padding Base64 decode. |
| `constant_time_compare` | `aquilia/signing.py` | `def constant_time_compare(a: bytes \| str, b: bytes \| str)` | Compare two values in constant time to prevent timing attacks. |
| `derive_key` | `aquilia/signing.py` | `def derive_key(secret: str \| bytes, salt: str, algorithm: str='HS256')` | Derive a signing sub-key from *secret* and *salt* using HKDF-lite. |
| `dumps` | `aquilia/signing.py` | `def dumps(obj: Any, *, secret: str \| bytes \| None=None, salt: str='aquilia.signing.dumps', algorithm: str='HS256', compress: bool=False, max_age: float \| int \| timedelta \| None=None, timestamp: bool=True)` | Serialise *obj* to a signed URL-safe string. |
| `loads` | `aquilia/signing.py` | `def loads(token: str, *, secret: str \| bytes \| None=None, salt: str='aquilia.signing.dumps', algorithm: str='HS256', max_age: float \| int \| timedelta \| None=None)` | Verify and deserialise a token produced by :func:`dumps`. |
| `configure` | `aquilia/signing.py` | `def configure(secret: str \| bytes, *, fallback_secrets: Sequence[str \| bytes] \| None=None, algorithm: str='HS256', salt: str='aquilia.signing')` | Configure the global signing secret used by module-level helpers. |
| `make_signer` | `aquilia/signing.py` | `def make_signer(secret: str \| bytes \| None=None, *, salt: str='aquilia.signing', algorithm: str \| None=None)` | Create a :class:`Signer` with the given (or global) settings. |
| `make_timestamp_signer` | `aquilia/signing.py` | `def make_timestamp_signer(secret: str \| bytes \| None=None, *, salt: str='aquilia.signing.ts', algorithm: str \| None=None)` | Create a :class:`TimestampSigner` with the given (or global) settings. |

## Constants And Module Flags

| Name | Source | Value or Type |
| --- | --- | --- |
| `VERSION` | `aquilia/_version.py` | `tuple[int, int, int]` |
| `WORKSPACE_VERSION` | `aquilia/_version.py` | `str` |
| `_VAR_NAME_PATTERN` | `aquilia/dotenv.py` | `Final` |
| `_INTERPOLATE_BRACES` | `aquilia/dotenv.py` | `Final` |
| `_INTERPOLATE_SIMPLE` | `aquilia/dotenv.py` | `Final` |
| `T` | `aquilia/effects.py` | `TypeVar('T')` |
| `T` | `aquilia/flow.py` | `TypeVar('T')` |
| `R` | `aquilia/flow.py` | `TypeVar('R')` |
| `E` | `aquilia/flow.py` | `TypeVar('E')` |
| `PRIORITY_CRITICAL` | `aquilia/flow.py` | `10` |
| `PRIORITY_AUTH` | `aquilia/flow.py` | `20` |
| `PRIORITY_VALIDATE` | `aquilia/flow.py` | `30` |
| `PRIORITY_TRANSFORM` | `aquilia/flow.py` | `40` |
| `PRIORITY_DEFAULT` | `aquilia/flow.py` | `50` |
| `PRIORITY_ENRICH` | `aquilia/flow.py` | `60` |
| `PRIORITY_LOG` | `aquilia/flow.py` | `70` |
| `PRIORITY_CLEANUP` | `aquilia/flow.py` | `80` |
| `_FD_SECURITY` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.SECURITY)` |
| `_FD_IO` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.IO)` |
| `_FD_ROUTING` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.ROUTING)` |
| `_FD_EFFECT` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.EFFECT)` |
| `_FD_MODEL` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.MODEL)` |
| `_FD_CACHE` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.CACHE)` |
| `_FD_CONFIG` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.CONFIG)` |
| `_FD_REGISTRY` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.REGISTRY)` |
| `_FD_DI` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.DI)` |
| `_FD_FLOW` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.FLOW)` |
| `_FD_SYSTEM` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.SYSTEM)` |
| `_FD_STORAGE` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.STORAGE)` |
| `_FD_TASKS` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.TASKS)` |
| `_FD_TEMPLATE` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.TEMPLATE)` |
| `_FD_HTTP` | `aquilia/middleware.py` | `cast(FaultDomain, FaultDomain.HTTP)` |
| `_FAST_SKIP_NAMES` | `aquilia/middleware.py` | `frozenset({'LoggingMiddleware', 'TimeoutMiddleware'})` |
| `_FALLBACK_500_HTML` | `aquilia/middleware.py` | `'<!DOCTYPE html><html><head><meta charset="utf-8"><title>500 Internal Server Error</title><style>body{font-family:system-ui,sans-serif;background:#000;color:#ededed;display:flex;justify-content:center;align-items:center;height:100vh;margin:0;}.c{text-align:center;}.s{font-size:72px;font-weight:700;color:#ef4444;}p{color:#888;}</style></head><body><div class="c"><div class="s">500</div><h1>Internal Server Error</h1><p>An unexpected error occurred.</p></div></body></html>'` |
| `T` | `aquilia/pyconfig.py` | `TypeVar('T')` |
| `SURP_MEDIA_TYPE` | `aquilia/request.py` | `'application/x-surp'` |
| `SURP_MEDIA_TYPES` | `aquilia/request.py` | `frozenset({'application/x-surp', 'application/surp', 'application/vnd.surp'})` |
| `T` | `aquilia/request.py` | `TypeVar('T')` |
| `_FD_IO` | `aquilia/request.py` | `cast(FaultDomain, FaultDomain.IO)` |
| `_FD_SECURITY` | `aquilia/request.py` | `cast(FaultDomain, FaultDomain.SECURITY)` |
| `SURP_MEDIA_TYPE` | `aquilia/response.py` | `'application/x-surp'` |
| `_PHASE_ORDER` | `aquilia/runtime.py` | `dict[RuntimePhase, int]` |
| `_HMAC_ALGORITHMS` | `aquilia/signing.py` | `frozenset[str]` |
| `_ASYMMETRIC_ALGORITHMS` | `aquilia/signing.py` | `frozenset[str]` |
| `_ALL_ALGORITHMS` | `aquilia/signing.py` | `frozenset[str]` |
| `_HMAC_DIGEST_MAP` | `aquilia/signing.py` | `dict[str, str]` |
| `_SEP` | `aquilia/signing.py` | `':'` |
| `_MIN_KEY_BYTES` | `aquilia/signing.py` | `32` |
| `_EPOCH` | `aquilia/signing.py` | `int(datetime(2020, 1, 1, tzinfo=timezone.utc).timestamp() * 1000000)` |
| `_TS_FORMAT_V1` | `aquilia/signing.py` | `1` |
| `_GLOBAL_SECRETS` | `aquilia/signing.py` | `list[str \| bytes]` |
| `_GLOBAL_ALGORITHM` | `aquilia/signing.py` | `str` |
| `_GLOBAL_SALT` | `aquilia/signing.py` | `str` |

## Detailed Classes And Methods

### `MultiDict`

- Source: `aquilia/_datastructures.py`
- Bases: `MutableMapping[str, list[str]]`
- Summary: Dictionary that supports multiple values per key.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get` | `def get(self, key: str, default: Any=None)` | Get first value for a key. |
| `get_all` | `def get_all(self, key: str)` | Get all values for a key. |
| `add` | `def add(self, key: str, value: str)` | Add a value to a key (appends to list). |
| `items_list` | `def items_list(self)` | Return all items as flat list of tuples. |
| `to_dict` | `def to_dict(self, multi: bool=False)` | Convert to regular dict. |

### `Headers`

- Source: `aquilia/_datastructures.py`
- Bases: `object`
- Summary: Case-insensitive header access with raw preservation.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `raw` | `list[tuple[bytes, bytes]]` | `field(default_factory=list)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get` | `def get(self, name: str, default: str \| None=None)` | Get first value for header (case-insensitive). |
| `get_all` | `def get_all(self, name: str)` | Get all values for header (case-insensitive). |
| `has` | `def has(self, name: str)` | Check if header exists. |
| `items` | `def items(self)` | Iterate over all headers. |
| `keys` | `def keys(self)` | Iterate over header names. |
| `values` | `def values(self)` | Iterate over header values. |

### `URL`

- Source: `aquilia/_datastructures.py`
- Bases: `object`
- Summary: Parsed URL representation.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `scheme` | `str` | `` |
| `host` | `str` | `` |
| `port` | `int \| None` | `None` |
| `path` | `str` | `'/'` |
| `query` | `str` | `''` |
| `fragment` | `str` | `''` |
| `username` | `str \| None` | `None` |
| `password` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `parse` | `def parse(cls, url: str)` | Parse URL string into components. |
| `netloc` | `def netloc(self)` | Build netloc string. |
| `replace` | `def replace(self, **kwargs)` | Create new URL with replaced components. |
| `with_query` | `def with_query(self, **params)` | Create new URL with updated query parameters. |

### `ParsedContentType`

- Source: `aquilia/_datastructures.py`
- Bases: `object`
- Summary: Parsed Content-Type header.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `media_type` | `str` | `` |
| `params` | `dict[str, str]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `parse` | `def parse(cls, content_type: str \| None)` | Parse Content-Type header. |
| `charset` | `def charset(self)` | Get charset parameter (default: utf-8). |
| `boundary` | `def boundary(self)` | Get boundary parameter (for multipart). |

### `Range`

- Source: `aquilia/_datastructures.py`
- Bases: `object`
- Summary: Parsed HTTP Range header.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `unit` | `str` | `'bytes'` |
| `ranges` | `list[tuple[int \| None, int \| None]]` | `field(default_factory=list)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `parse` | `def parse(cls, range_header: str \| None)` | Parse Range header. |

### `UploadFile`

- Source: `aquilia/_uploads.py`
- Bases: `object`
- Summary: Uploaded file representation.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `filename` | `str` | `` |
| `content_type` | `str` | `` |
| `size` | `int \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `read` | `async def read(self, size: int=-1)` | Read file content. |
| `stream` | `async def stream(self, chunk_size: int \| None=None)` | Stream file content in chunks. |
| `save` | `async def save(self, path: str \| Path, overwrite: bool=False)` | Save uploaded file to disk. |
| `close` | `async def close(self)` | Clean up temporary file if exists. |

### `FormData`

- Source: `aquilia/_uploads.py`
- Bases: `object`
- Summary: Parsed form data containing both fields and files.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `fields` | `MultiDict` | `field(default_factory=MultiDict)` |
| `files` | `dict[str, list[UploadFile]]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get` | `def get(self, name: str, default: FormValue \| None=None)` | Get field or file by name. |
| `get_field` | `def get_field(self, name: str, default: str \| None=None)` | Get form field value. |
| `get_all_fields` | `def get_all_fields(self, name: str)` | Get all values for a form field. |
| `get_file` | `def get_file(self, name: str)` | Get first uploaded file by name. |
| `get_all_files` | `def get_all_files(self, name: str)` | Get all uploaded files by name. |
| `cleanup` | `async def cleanup(self)` | Clean up all temporary upload files. |

### `UploadStore`

- Source: `aquilia/_uploads.py`
- Bases: `Protocol`
- Summary: Protocol for upload storage backends.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `write_chunk` | `async def write_chunk(self, upload_id: str, chunk: bytes)` | Write a chunk of uploaded data. |
| `finalize` | `async def finalize(self, upload_id: str, metadata: dict[str, Any] \| None=None)` | Finalize upload and return final path/identifier. |
| `abort` | `async def abort(self, upload_id: str)` | Abort upload and clean up partial data. |

### `LocalUploadStore`

- Source: `aquilia/_uploads.py`
- Bases: `object`
- Summary: Local filesystem upload store.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `write_chunk` | `async def write_chunk(self, upload_id: str, chunk: bytes)` | Write chunk to temporary file. |
| `finalize` | `async def finalize(self, upload_id: str, metadata: dict[str, Any] \| None=None)` | Finalize upload and move to final location. |
| `abort` | `async def abort(self, upload_id: str)` | Abort upload and remove temp file. |

### `ASGIAdapter`

- Source: `aquilia/asgi.py`
- Bases: `object`
- Summary: ASGI application adapter. Converts ASGI events to Aquilia Request/Response. Uses controller-based routing exclusively.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `handle_http` | `async def handle_http(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend)` | Handle HTTP request with optimized hot path. |
| `handle_websocket` | `async def handle_websocket(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend)` | Handle WebSocket connection. |
| `handle_lifespan` | `async def handle_lifespan(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend)` | Handle ASGI lifespan events. |

### `NestedNamespace`

- Source: `aquilia/config.py`
- Bases: `object`
- Summary: A namespace that supports nested attribute access for app configs. Enables syntax like: config.apps.auth.secret_key

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Return the underlying data dictionary. |
| `get` | `def get(self, key: str, default: Any=None)` |  |

### `Config`

- Source: `aquilia/config.py`
- Bases: `object`
- Summary: Base class for typed configuration classes.

### `ConfigError`

- Source: `aquilia/config.py`
- Bases: `Exception`
- Summary: Raised when configuration validation fails.

### `ConfigLoader`

- Source: `aquilia/config.py`
- Bases: `object`
- Summary: Loads and merges configuration from multiple sources with precedence: CLI args > Environment variables > .env files > config files > defaults

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `load` | `def load(cls, paths: list[str] \| None=None, env_prefix: str='AQ_', env_file: str \| None=None, overrides: dict[str, Any] \| None=None)` | Load configuration from multiple sources with proper merge strategy. |
| `get` | `def get(self, path: str, default: Any=None)` | Get config value by dot-separated path. |
| `get_app_config` | `def get_app_config(self, app_name: str, config_class: type[Config])` | Get and validate configuration for a specific app. |
| `to_dict` | `def to_dict(self)` | Export all config as dictionary. |
| `get_session_config` | `def get_session_config(self)` | Get session configuration with defaults. |
| `get_auth_config` | `def get_auth_config(self)` | Get auth configuration with defaults. |
| `get_template_config` | `def get_template_config(self)` | Get template configuration with defaults. |
| `get_security_config` | `def get_security_config(self)` | Get security configuration with defaults. |
| `get_static_config` | `def get_static_config(self)` | Get static files configuration with defaults. |
| `get_cache_config` | `def get_cache_config(self)` | Get cache configuration with defaults. |
| `get_i18n_config` | `def get_i18n_config(self)` | Get i18n (internationalization) configuration with defaults. |
| `get_mail_config` | `def get_mail_config(self)` | Get mail configuration with defaults. |
| `get_tasks_config` | `def get_tasks_config(self)` | Get background tasks configuration with defaults. |
| `get_database_config` | `def get_database_config(self)` | Get database configuration with defaults. |
| `get_storage_config` | `def get_storage_config(self)` | Get storage configuration with defaults. |
| `get_middleware_config` | `def get_middleware_config(self)` | Get middleware chain configuration. |
| `get_versioning_config` | `def get_versioning_config(self)` | Get API versioning configuration with defaults. |

### `RuntimeConfig`

- Source: `aquilia/config_builders.py`
- Bases: `object`
- Summary: Runtime configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `mode` | `str` | `'dev'` |
| `host` | `str` | `'127.0.0.1'` |
| `port` | `int` | `8000` |
| `reload` | `bool` | `True` |
| `workers` | `int` | `1` |

### `ModuleConfig`

- Source: `aquilia/config_builders.py`
- Bases: `object`
- Summary: Module configuration -- workspace-level orchestration metadata.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `version` | `str` | `'0.1.0'` |
| `description` | `str` | `''` |
| `fault_domain` | `str \| None` | `None` |
| `route_prefix` | `str \| None` | `None` |
| `depends_on` | `list[str]` | `field(default_factory=list)` |
| `tags` | `list[str]` | `field(default_factory=list)` |
| `imports` | `list[str]` | `field(default_factory=list)` |
| `exports` | `list[str]` | `field(default_factory=list)` |
| `on_startup` | `str \| None` | `None` |
| `on_shutdown` | `str \| None` | `None` |
| `database` | `dict[str, Any] \| None` | `None` |
| `auto_discover` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Convert to dictionary format. |

### `Module`

- Source: `aquilia/config_builders.py`
- Bases: `object`
- Summary: Fluent module builder -- workspace-level orchestration only.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `auto_discover` | `def auto_discover(self, enabled: bool=True)` | Configure auto-discovery behavior. |
| `fault_domain` | `def fault_domain(self, domain: str)` | Set fault domain. |
| `route_prefix` | `def route_prefix(self, prefix: str)` | Set route prefix. |
| `depends_on` | `def depends_on(self, *modules: str)` | Set module dependencies (legacy -- prefer imports()). |
| `imports` | `def imports(self, *modules: str)` | Declare module imports (v2 encapsulation). |
| `exports` | `def exports(self, *components: str)` | Declare exported components (v2 encapsulation). |
| `tags` | `def tags(self, *module_tags: str)` | Set module tags for organization and filtering. |
| `register_controllers` | `def register_controllers(self, *controllers: str)` | DEPRECATED -- declare controllers in modules/*/manifest.py instead. |
| `register_services` | `def register_services(self, *services: str)` | DEPRECATED -- declare services in modules/*/manifest.py instead. |
| `register_providers` | `def register_providers(self, *providers: dict[str, Any])` | DEPRECATED -- declare providers in modules/*/manifest.py instead. |
| `register_routes` | `def register_routes(self, *routes: dict[str, Any])` | DEPRECATED -- declare routes via controllers in modules/*/manifest.py instead. |
| `register_sockets` | `def register_sockets(self, *sockets: str)` | DEPRECATED -- declare socket controllers in modules/*/manifest.py instead. |
| `register_middlewares` | `def register_middlewares(self, *middlewares: str)` | DEPRECATED -- declare middleware in modules/*/manifest.py instead. |
| `register_models` | `def register_models(self, *models: str)` | DEPRECATED -- declare models in modules/*/manifest.py instead. |
| `register_serializers` | `def register_serializers(self, *serializers: str)` | DEPRECATED -- declare serializers in modules/*/manifest.py instead. |
| `on_startup` | `def on_startup(self, hook: str)` | Register a startup hook for this module. |
| `on_shutdown` | `def on_shutdown(self, hook: str)` | Register a shutdown hook for this module. |
| `database` | `def database(self, url: str \| None=None, *, config: Any \| None=None, auto_connect: bool=True, auto_create: bool=True, auto_migrate: bool=False, migrations_dir: str='migrations', **kwargs)` | Configure database for this module. |
| `build` | `def build(self)` | Build module configuration. |

### `AuthConfig`

- Source: `aquilia/config_builders.py`
- Bases: `object`
- Summary: Authentication configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `store_type` | `str` | `'memory'` |
| `secret_key` | `str \| None` | `None` |
| `algorithm` | `str` | `'HS256'` |
| `issuer` | `str` | `'aquilia'` |
| `audience` | `str` | `'aquilia-app'` |
| `access_token_ttl_minutes` | `int` | `60` |
| `refresh_token_ttl_days` | `int` | `30` |
| `require_auth_by_default` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Convert to dictionary format. |

### `Integration`

- Source: `aquilia/config_builders.py`
- Bases: `object`
- Summary: Integration configuration builders.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `auth` | `def auth(config: AuthConfig \| None=None, enabled: bool=True, store_type: str='memory', secret_key: str \| None=None, **kwargs)` | Configure authentication. |
| `sessions` | `def sessions(policy: Any \| None=None, store: Any \| None=None, transport: Any \| None=None, **kwargs)` | Configure session integration with Aquilia's unique fluent syntax. |
| `di` | `def di(auto_wire: bool=True, **kwargs)` | Configure dependency injection. |
| `database` | `def database(url: str \| None=None, *, config: Any \| None=None, auto_connect: bool=True, auto_create: bool=True, auto_migrate: bool=False, migrations_dir: str='migrations', pool_size: int=5, echo: bool=False, model_paths: list[str] \| None=None, scan_dirs: list[str] \| None=None, **kwargs)` | Configure database and AMDL model integration. |
| `storage` | `def storage(default: str='default', backends: dict[str, Any] \| None=None, **kwargs)` | Configure file storage backends. |
| `registry` | `def registry(**kwargs)` | Configure registry. |
| `routing` | `def routing(strict_matching: bool=True, **kwargs)` | Configure routing. |
| `fault_handling` | `def fault_handling(default_strategy: str='propagate', **kwargs)` | Configure fault handling. |
| `cache` | `def cache(backend: str='memory', default_ttl: int=300, max_size: int=10000, eviction_policy: str='lru', namespace: str='default', key_prefix: str='aq:', serializer: str='json', redis_url: str='redis://localhost:6379/0', redis_max_connections: int=10, l1_max_size: int=1000, l1_ttl: int=60, l2_backend: str='redis', middleware_enabled: bool=False, middleware_default_ttl: int=60, **kwargs)` | Configure the caching subsystem. |
| `tasks` | `def tasks(backend: str='memory', num_workers: int=4, default_queue: str='default', cleanup_interval: float=300.0, cleanup_max_age: float=3600.0, max_retries: int=3, retry_delay: float=1.0, retry_backoff: float=2.0, retry_max_delay: float=300.0, default_timeout: float=300.0, auto_start: bool=True, dead_letter_max: int=1000, scheduler_tick: float=15.0, **kwargs)` | Configure the background task subsystem. |
| `admin` | `def admin(url_prefix: str='/admin', site_title: str='Aquilia Admin', site_header: str='Aquilia Administration', auto_discover: bool=True, login_url: str \| None=None, list_per_page: int=25, theme: str='auto', modules: Optional['Integration.AdminModules']=None, audit: Optional['Integration.AdminAudit']=None, monitoring: Optional['Integration.AdminMonitoring']=None, sidebar: Optional['Integration.AdminSidebar']=None, containers: Optional['Integration.AdminContainers']=None, pods: Optional['Integration.AdminPods']=None, security: Optional['Integration.AdminSecurity']=None, enable_audit: bool \| None=None, audit_max_entries: int=10000, enable_dashboard: bool \| None=None, enable_orm: bool \| None=None, enable_migrations: bool \| None=None, enable_config: bool \| None=None, enable_workspace: bool \| None=None, enable_permissions: bool \| None=None, enable_monitoring: bool \| None=None, enable_admin_users: bool \| None=None, enable_containers: bool \| None=None, enable_pods: bool \| None=None, enable_profile: bool \| None=None, audit_log_logins: bool \| None=None, audit_log_views: bool \| None=None, audit_log_searches: bool \| None=None, enable_api_keys: bool \| None=None, enable_preferences: bool \| None=None, audit_excluded_actions: list[str] \| None=None, monitoring_metrics: list[str] \| None=None, monitoring_refresh_interval: int \| None=None, sidebar_sections: dict[str, bool] \| None=None, **kwargs)` | Configure the admin dashboard integration. |
| `patterns` | `def patterns(**kwargs)` | Configure patterns. |
| `static_files` | `def static_files(directories: dict[str, str] \| None=None, cache_max_age: int=86400, immutable: bool=False, etag: bool=True, gzip: bool=True, brotli: bool=True, memory_cache: bool=True, html5_history: bool=False, **kwargs)` | Configure static file serving middleware. |
| `cors` | `def cors(allow_origins: list[str] \| None=None, allow_methods: list[str] \| None=None, allow_headers: list[str] \| None=None, expose_headers: list[str] \| None=None, allow_credentials: bool=False, max_age: int=600, allow_origin_regex: str \| None=None, **kwargs)` | Configure CORS middleware. |
| `csp` | `def csp(policy: dict[str, list[str]] \| None=None, report_only: bool=False, nonce: bool=True, preset: str='strict', **kwargs)` | Configure Content-Security-Policy middleware. |
| `rate_limit` | `def rate_limit(limit: int=100, window: int=60, algorithm: str='sliding_window', per_user: bool=False, burst: int \| None=None, exempt_paths: list[str] \| None=None, **kwargs)` | Configure rate limiting middleware. |
| `openapi` | `def openapi(title: str='Aquilia API', version: str='1.0.0', description: str='', terms_of_service: str='', contact_name: str='', contact_email: str='', contact_url: str='', license_name: str='', license_url: str='', servers: list[dict[str, str]] \| None=None, docs_path: str='/docs', openapi_json_path: str='/openapi.json', redoc_path: str='/redoc', include_internal: bool=False, group_by_module: bool=True, infer_request_body: bool=True, infer_responses: bool=True, detect_security: bool=True, external_docs_url: str='', external_docs_description: str='', swagger_ui_theme: str='', swagger_ui_config: dict[str, Any] \| None=None, enabled: bool=True, **kwargs)` | Configure OpenAPI specification generation and interactive documentation. |
| `csrf` | `def csrf(secret_key: str='', token_length: int=32, header_name: str='X-CSRF-Token', field_name: str='_csrf_token', cookie_name: str='_csrf_cookie', cookie_path: str='/', cookie_domain: str \| None=None, cookie_secure: bool=True, cookie_samesite: str='Lax', cookie_httponly: bool=False, cookie_max_age: int=3600, safe_methods: list[str] \| None=None, exempt_paths: list[str] \| None=None, exempt_content_types: list[str] \| None=None, trust_ajax: bool=True, rotate_token: bool=False, failure_status: int=403, enabled: bool=True, **kwargs)` | Configure CSRF (Cross-Site Request Forgery) protection integration. |
| `logging` | `def logging(format: str='%(method)s %(path)s %(status)s %(duration_ms).1fms', level: str='INFO', slow_threshold_ms: float=1000.0, skip_paths: list[str] \| None=None, include_headers: bool=False, include_query: bool=True, include_user_agent: bool=False, log_request_body: bool=False, log_response_body: bool=False, colorize: bool=True, enabled: bool=True, **kwargs)` | Configure request/response logging integration. |
| `mail` | `def mail(default_from: str='noreply@localhost', default_reply_to: str \| None=None, subject_prefix: str='', providers: list[dict[str, Any]] \| None=None, auth: Any \| None=None, console_backend: bool=False, preview_mode: bool=False, template_dirs: list[str] \| None=None, retry_max_attempts: int=5, retry_base_delay: float=1.0, rate_limit_global: int=1000, rate_limit_per_domain: int=100, dkim_enabled: bool=False, dkim_domain: str \| None=None, dkim_selector: str='aquilia', require_tls: bool=True, pii_redaction: bool=False, metrics_enabled: bool=True, tracing_enabled: bool=False, enabled: bool=True, **kwargs)` | Configure AquilaMail -- the production-ready async mail subsystem. |
| `mlops` | `def mlops(*, enabled: bool=True, registry_db: str='registry.db', blob_root: str='.aquilia-store', storage_backend: str='filesystem', drift_method: str='psi', drift_threshold: float=0.2, drift_num_bins: int=10, max_batch_size: int=16, max_latency_ms: float=50.0, batching_strategy: str='hybrid', sample_rate: float=0.01, log_dir: str='prediction_logs', hmac_secret: str \| None=None, signing_private_key: str \| None=None, signing_public_key: str \| None=None, encryption_key: Any \| None=None, plugin_auto_discover: bool=True, scaling_policy: dict[str, Any] \| None=None, rollout_default_strategy: str='canary', auto_rollback: bool=True, metrics_model_name: str='', metrics_model_version: str='', cache_enabled: bool=True, cache_ttl: int=60, cache_namespace: str='mlops', artifact_store_dir: str='artifacts', fault_engine_debug: bool=False, **kwargs)` | Configure MLOps platform integration. |
| `i18n` | `def i18n(*, default_locale: str='en', available_locales: list[str] \| None=None, fallback_locale: str='en', catalog_dirs: list[str] \| None=None, catalog_format: str='json', missing_key_strategy: str='log_and_key', auto_reload: bool=False, auto_detect: bool=True, cookie_name: str='aq_locale', query_param: str='lang', path_prefix: bool=False, resolver_order: list[str] \| None=None, enabled: bool=True, **kwargs)` | Configure the i18n (internationalization) subsystem. |
| `serializers` | `def serializers(*, auto_discover: bool=True, strict_validation: bool=True, raise_on_error: bool=False, date_format: str='iso-8601', datetime_format: str='iso-8601', coerce_decimal_to_string: bool=True, compact_json: bool=True, enabled: bool=True, **kwargs)` | Configure global serializer settings. |
| `render` | `def render(service_name: str \| None=None, region: str='oregon', plan: str='starter', num_instances: int=1, image: str \| None=None, health_path: str='/_health', auto_deploy: str='no', **kwargs)` | Configure Render PaaS deployment. |
| `versioning` | `def versioning(strategy: str='header', versions: list[str] \| None=None, default_version: str \| None=None, require_version: bool=False, header_name: str='X-API-Version', query_param: str='api_version', url_prefix: str='v', url_segment_index: int=0, strip_version_from_path: bool=True, media_type_param: str='version', channels: dict[str, str] \| None=None, channel_header: str='X-API-Channel', channel_query_param: str='api_channel', negotiation_mode: str='exact', sunset_policy: Any \| None=None, sunset_schedules: dict[str, dict[str, Any]] \| None=None, include_version_header: bool=True, response_header_name: str='X-API-Version', include_supported_versions_header: bool=True, neutral_paths: list[str] \| None=None, enabled: bool=True, **kwargs)` | Configure API versioning integration. |

### `Workspace`

- Source: `aquilia/config_builders.py`
- Bases: `object`
- Summary: Fluent workspace builder.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `on_startup` | `def on_startup(self, hook: str)` | Register a workspace-level startup hook. |
| `on_shutdown` | `def on_shutdown(self, hook: str)` | Register a workspace-level shutdown hook. |
| `env_config` | `def env_config(self, config_cls: 'type \| AquilaConfig')` | Attach a :class:`~aquilia.pyconfig.AquilaConfig` subclass (or instance) as the operational environment config. |
| `starter` | `def starter(self, module_name: str)` | Register the starter controller module. |
| `middleware` | `def middleware(self, chain: 'Integration.middleware.Chain')` | Configure the middleware chain for this workspace. |
| `runtime` | `def runtime(self, mode: str='dev', host: str='127.0.0.1', port: int=8000, reload: bool=True, workers: int=1)` | Configure runtime settings. |
| `module` | `def module(self, module: Module)` | Add a module to the workspace. |
| `integrate` | `def integrate(self, integration: 'dict[str, Any] \| Any')` | Add an integration. |
| `sessions` | `def sessions(self, policies: list[Any] \| None=None, **kwargs)` | Configure session management. |
| `i18n` | `def i18n(self, default_locale: str='en', available_locales: list[str] \| None=None, **kwargs)` | Configure internationalization (shorthand for ``integrate(Integration.i18n(...))``). |
| `tasks` | `def tasks(self, num_workers: int=4, backend: str='memory', **kwargs)` | Configure background tasks (shorthand for ``integrate(Integration.tasks(...))``). |
| `storage` | `def storage(self, default: str='default', backends: dict[str, Any] \| None=None, **kwargs)` | Configure file storage for the workspace. |
| `security` | `def security(self, cors_enabled: bool=False, csrf_protection: bool=False, helmet_enabled: bool=True, rate_limiting: bool=False, https_redirect: bool=False, hsts: bool=True, proxy_fix: bool=False, **kwargs)` | Configure security features. |
| `telemetry` | `def telemetry(self, tracing_enabled: bool=False, metrics_enabled: bool=True, logging_enabled: bool=True, **kwargs)` | Configure telemetry and observability. |
| `database` | `def database(self, url: str \| None=None, *, config: Any \| None=None, auto_connect: bool=True, auto_create: bool=True, auto_migrate: bool=False, migrations_dir: str='migrations', **kwargs)` | Configure global database for the workspace. |
| `mlops` | `def mlops(self, enabled: bool=True, registry_db: str='registry.db', blob_root: str='.aquilia-store', drift_method: str='psi', drift_threshold: float=0.2, max_batch_size: int=16, max_latency_ms: float=50.0, plugin_auto_discover: bool=True, **kwargs)` | Configure MLOps platform for this workspace. |
| `to_dict` | `def to_dict(self)` | Convert workspace to dictionary format compatible with ConfigLoader. |

### `DotEnv`

- Source: `aquilia/dotenv.py`
- Bases: `object`
- Summary: Native dotenv file parser and loader.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `parse` | `def parse(cls, path: str \| Path, *, encoding: str='utf-8', interpolate: bool=True)` | Parse a .env file and return a dictionary of values. |
| `parse_string` | `def parse_string(cls, content: str, *, interpolate: bool=True)` | Parse dotenv-formatted string content. |
| `load` | `def load(cls, path: str \| Path \| None=None, *, override: bool=False, encoding: str='utf-8', interpolate: bool=True)` | Load environment variables from a .env file into os.environ. |

### `DotEnvLoader`

- Source: `aquilia/dotenv.py`
- Bases: `object`
- Summary: Singleton loader that ensures .env files are loaded exactly once.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `configure` | `def configure(cls, *, search_paths: list[str] \| None=None, auto_load: bool=True, override: bool=False, interpolate: bool=True)` | Configure the loader before loading. |
| `ensure_loaded` | `def ensure_loaded(cls, *, path: str \| Path \| None=None, search_paths: list[str] \| None=None)` | Ensure dotenv files are loaded (idempotent). |
| `is_loaded` | `def is_loaded(cls)` | Check if dotenv files have been loaded. |
| `loaded_files` | `def loaded_files(cls)` | Return list of files that were loaded. |
| `loaded_values` | `def loaded_values(cls)` | Return copy of all loaded values. |
| `reset` | `def reset(cls)` | Reset the loader state. |

### `EffectKind`

- Source: `aquilia/effects.py`
- Bases: `Enum`
- Summary: Categories of effects.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `DB` | `` | `'db'` |
| `CACHE` | `` | `'cache'` |
| `QUEUE` | `` | `'queue'` |
| `HTTP` | `` | `'http'` |
| `STORAGE` | `` | `'storage'` |
| `CUSTOM` | `` | `'custom'` |

### `Effect`

- Source: `aquilia/effects.py`
- Bases: `Generic[T]`
- Summary: Effect token representing a capability.

### `EffectProvider`

- Source: `aquilia/effects.py`
- Bases: `ABC`
- Summary: Base class for effect providers.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Initialize the provider (called once at startup). |
| `acquire` | `async def acquire(self, mode: str \| None=None)` | Acquire a resource for this effect (called per-request). |
| `release` | `async def release(self, resource: Any, success: bool=True)` | Release the resource (called at end of request). |
| `finalize` | `async def finalize(self)` | Finalize provider (called at shutdown). |
| `health_check` | `async def health_check(self)` | Check provider health. Override for custom health reporting. |

### `DBTx`

- Source: `aquilia/effects.py`
- Bases: `Effect`
- Summary: Database transaction effect.

### `CacheEffect`

- Source: `aquilia/effects.py`
- Bases: `Effect`
- Summary: Cache effect.

### `QueueEffect`

- Source: `aquilia/effects.py`
- Bases: `Effect`
- Summary: Queue/message publish effect.

### `HTTPEffect`

- Source: `aquilia/effects.py`
- Bases: `Effect`
- Summary: HTTP client effect for outbound requests.

### `StorageEffect`

- Source: `aquilia/effects.py`
- Bases: `Effect`
- Summary: File/blob storage effect.

### `DBTxProvider`

- Source: `aquilia/effects.py`
- Bases: `EffectProvider`
- Summary: Database transaction provider.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Initialize connection pool. |
| `acquire` | `async def acquire(self, mode: str \| None=None)` | Acquire database connection. |
| `release` | `async def release(self, resource: Any, success: bool=True)` | Release connection and commit/rollback transaction. |
| `health_check` | `async def health_check(self)` |  |

### `CacheProvider`

- Source: `aquilia/effects.py`
- Bases: `EffectProvider`
- Summary: Cache effect provider backed by the real CacheService.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Initialize cache backend. |
| `acquire` | `async def acquire(self, mode: str \| None=None)` | Get cache handle for namespace. |
| `release` | `async def release(self, resource: Any, success: bool=True)` | Nothing to release for cache. |
| `finalize` | `async def finalize(self)` | Shutdown underlying cache service. |
| `health_check` | `async def health_check(self)` |  |

### `QueueProvider`

- Source: `aquilia/effects.py`
- Bases: `EffectProvider`
- Summary: Queue/message publish effect provider.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` |  |
| `acquire` | `async def acquire(self, mode: str \| None=None)` | Return a queue handle for a topic/channel. |
| `release` | `async def release(self, resource: Any, success: bool=True)` |  |
| `finalize` | `async def finalize(self)` |  |
| `health_check` | `async def health_check(self)` |  |

### `TaskQueueProvider`

- Source: `aquilia/effects.py`
- Bases: `EffectProvider`
- Summary: Task queue effect provider backed by AquilaTasks TaskManager.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` |  |
| `acquire` | `async def acquire(self, mode: str \| None=None)` |  |
| `release` | `async def release(self, resource: Any, success: bool=True)` |  |
| `finalize` | `async def finalize(self)` |  |
| `health_check` | `async def health_check(self)` |  |

### `HTTPProvider`

- Source: `aquilia/effects.py`
- Bases: `EffectProvider`
- Summary: HTTP client effect provider for outbound requests.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` | Create HTTP client session. |
| `acquire` | `async def acquire(self, mode: str \| None=None)` | Return HTTP client handle. |
| `release` | `async def release(self, resource: Any, success: bool=True)` |  |
| `finalize` | `async def finalize(self)` |  |

### `StorageProvider`

- Source: `aquilia/effects.py`
- Bases: `EffectProvider`
- Summary: File/blob storage effect provider.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `initialize` | `async def initialize(self)` |  |
| `acquire` | `async def acquire(self, mode: str \| None=None)` |  |
| `release` | `async def release(self, resource: Any, success: bool=True)` |  |
| `health_check` | `async def health_check(self)` |  |

### `CacheServiceHandle`

- Source: `aquilia/effects.py`
- Bases: `object`
- Summary: Handle wrapping real CacheService for a given namespace.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get` | `async def get(self, key: str)` |  |
| `set` | `async def set(self, key: str, value: Any, ttl: int \| None=None)` |  |
| `delete` | `async def delete(self, key: str)` |  |

### `CacheHandle`

- Source: `aquilia/effects.py`
- Bases: `object`
- Summary: Handle for cache operations in a namespace.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get` | `async def get(self, key: str)` | Get value from cache. |
| `set` | `async def set(self, key: str, value: Any, ttl: int \| None=None)` | Set value in cache. |
| `delete` | `async def delete(self, key: str)` | Delete value from cache. |

### `QueueHandle`

- Source: `aquilia/effects.py`
- Bases: `object`
- Summary: Handle for queue operations on a topic.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `publish` | `async def publish(self, payload: Any, *, headers: dict[str, str] \| None=None)` | Publish a message to the topic. |
| `publish_batch` | `async def publish_batch(self, payloads: Sequence[Any])` | Publish multiple messages. |

### `TaskQueueHandle`

- Source: `aquilia/effects.py`
- Bases: `object`
- Summary: Handle for enqueuing background tasks via the TaskManager.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `enqueue` | `async def enqueue(self, func, *args, **kwargs)` | Enqueue a task for background execution. |
| `publish` | `async def publish(self, payload: Any, *, headers: dict[str, str] \| None=None)` | Compatibility with QueueHandle -- enqueue payload as a task. |
| `publish_batch` | `async def publish_batch(self, payloads: Sequence[Any])` | Compatibility with QueueHandle. |

### `HTTPHandle`

- Source: `aquilia/effects.py`
- Bases: `object`
- Summary: Handle for outbound HTTP requests.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get` | `async def get(self, url: str, **kwargs)` |  |
| `post` | `async def post(self, url: str, *, json: Any=None, **kwargs)` |  |
| `put` | `async def put(self, url: str, *, json: Any=None, **kwargs)` |  |
| `delete` | `async def delete(self, url: str, **kwargs)` |  |

### `StorageHandle`

- Source: `aquilia/effects.py`
- Bases: `object`
- Summary: Handle for file/blob storage operations.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `read` | `async def read(self, key: str)` |  |
| `write` | `async def write(self, key: str, data: bytes)` |  |
| `delete` | `async def delete(self, key: str)` |  |
| `exists` | `async def exists(self, key: str)` |  |

### `EffectRegistry`

- Source: `aquilia/effects.py`
- Bases: `object`
- Summary: Registry for effect providers.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register` | `def register(self, effect_name: str, provider: EffectProvider)` | Register an effect provider. |
| `unregister` | `def unregister(self, effect_name: str)` | Unregister and return an effect provider. |
| `initialize_all` | `async def initialize_all(self)` | Initialize all registered providers (lifecycle startup hook). |
| `finalize_all` | `async def finalize_all(self)` | Finalize all providers (lifecycle shutdown hook). |
| `acquire` | `async def acquire(self, effect_name: str, mode: str \| None=None)` | Acquire a resource for the named effect. |
| `release` | `async def release(self, effect_name: str, resource: Any, *, success: bool=True)` | Release a resource for the named effect. |
| `startup` | `async def startup(self)` | DI lifecycle startup hook. |
| `shutdown` | `async def shutdown(self)` | DI lifecycle shutdown hook. |
| `has_effect` | `def has_effect(self, effect_name: str)` | Check if effect is available. |
| `get_provider` | `def get_provider(self, effect_name: str)` | Get provider for effect. |
| `health_check` | `async def health_check(self)` | Aggregate health from all providers. |
| `register_with_container` | `def register_with_container(self, container: 'Any')` | Register this EffectRegistry and all effect providers with a DI container. |
| `list_effects` | `def list_effects(self)` | Return all registered effect names. |
| `get_metrics` | `def get_metrics(self)` | Return per-effect metrics. |

### `LifecycleHook`

- Source: `aquilia/engine.py`
- Bases: `Enum`
- Summary: Named lifecycle points that subsystems can subscribe to.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `BEFORE_REQUEST` | `` | `auto()` |
| `AFTER_REQUEST` | `` | `auto()` |
| `ON_ERROR` | `` | `auto()` |
| `ON_STARTUP` | `` | `auto()` |
| `ON_SHUTDOWN` | `` | `auto()` |

### `EngineMetrics`

- Source: `aquilia/engine.py`
- Bases: `object`
- Summary: Lightweight in-process metrics for the Aquilia engine.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `request_started` | `def request_started(self)` |  |
| `request_finished` | `def request_finished(self, latency_ms: float)` |  |
| `request_errored` | `def request_errored(self)` |  |
| `mean_latency_ms` | `def mean_latency_ms(self)` |  |
| `snapshot` | `def snapshot(self)` | Return a JSON-serialisable snapshot of current metrics. |

### `RequestCtx`

- Source: `aquilia/engine.py`
- Bases: `object`
- Summary: Per-request execution context.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `resolve` | `async def resolve(self, name: str, optional: bool=False)` | Resolve a dependency from the request-scoped container. |
| `resolve_sync` | `def resolve_sync(self, name: str, optional: bool=False)` | Synchronous resolution -- only for sync-safe providers. |
| `get` | `def get(self, key: str, default: Any=None)` | Shorthand for ``ctx.state.get(key, default)``. |
| `set` | `def set(self, key: str, value: Any)` | Shorthand for ``ctx.state[key] = value``. |
| `elapsed_ms` | `def elapsed_ms(self)` | Milliseconds elapsed since this context was created. |
| `add_cleanup` | `def add_cleanup(self, callback: CleanupCallback)` | Register an async or sync callable to run on ``dispose()``. |
| `dispose` | `async def dispose(self)` | Dispose of the request context. |

### `FlowNodeType`

- Source: `aquilia/flow.py`
- Bases: `str, Enum`
- Summary: Types of nodes in a flow pipeline.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `GUARD` | `` | `'guard'` |
| `TRANSFORM` | `` | `'transform'` |
| `HANDLER` | `` | `'handler'` |
| `HOOK` | `` | `'hook'` |
| `EFFECT` | `` | `'effect'` |
| `MIDDLEWARE` | `` | `'middleware'` |

### `FlowStatus`

- Source: `aquilia/flow.py`
- Bases: `str, Enum`
- Summary: Pipeline execution outcome.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `SUCCESS` | `` | `'success'` |
| `GUARDED` | `` | `'guarded'` |
| `ERROR` | `` | `'error'` |
| `TIMEOUT` | `` | `'timeout'` |
| `CANCELLED` | `` | `'cancelled'` |

### `FlowContext`

- Source: `aquilia/flow.py`
- Bases: `object`
- Summary: Typed execution context threaded through the entire flow pipeline.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `get_effect` | `def get_effect(self, name: str)` | Get an acquired effect resource by name. |
| `has_effect` | `def has_effect(self, name: str)` | Check if an effect resource is currently acquired. |
| `get` | `def get(self, key: str, default: Any=None)` |  |
| `set` | `def set(self, key: str, value: Any)` |  |
| `add_cleanup` | `def add_cleanup(self, callback: Callable[[], Awaitable[None]])` | Register a cleanup callback (LIFO execution order). |
| `dispose` | `async def dispose(self)` | Run all cleanup callbacks in LIFO order. |
| `elapsed_ms` | `def elapsed_ms(self)` |  |
| `to_dict` | `def to_dict(self)` | Convert to dict for legacy FlowGuard compatibility. |

### `FlowNode`

- Source: `aquilia/flow.py`
- Bases: `object`
- Summary: A typed unit in a flow pipeline.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `type` | `FlowNodeType` | `` |
| `callable` | `Callable[..., Any]` | `` |
| `name` | `str` | `` |
| `priority` | `int` | `PRIORITY_DEFAULT` |
| `effects` | `list[str]` | `field(default_factory=list)` |
| `condition` | `Callable[[FlowContext], bool] \| None` | `None` |
| `timeout` | `float \| None` | `None` |

### `FlowResult`

- Source: `aquilia/flow.py`
- Bases: `object`
- Summary: Result of a flow pipeline execution.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `status` | `FlowStatus` | `` |
| `value` | `Any` | `None` |
| `context` | `FlowContext \| None` | `None` |
| `error` | `Exception \| None` | `None` |
| `guard` | `FlowNode \| None` | `None` |
| `timings` | `dict[str, float]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_success` | `def is_success(self)` |  |
| `is_guarded` | `def is_guarded(self)` |  |

### `FlowError`

- Source: `aquilia/flow.py`
- Bases: `Exception`
- Summary: Raised when a flow pipeline encounters an unrecoverable error.

### `Layer`

- Source: `aquilia/flow.py`
- Bases: `object`
- Summary: Composable effect layer -- separates effect construction from usage.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `factory` | `Callable[..., Any]` | `` |
| `deps` | `list[str]` | `field(default_factory=list)` |
| `scope` | `str` | `'app'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build` | `async def build(self, resolved_deps: dict[str, Any])` | Build the effect provider using resolved dependencies. |
| `merge` | `def merge(*layers: Layer)` | Merge multiple layers into a single composition. |
| `provide` | `def provide(layer: Layer, *providers: Layer)` | Provide dependencies for a layer from other layers. |

### `LayerComposition`

- Source: `aquilia/flow.py`
- Bases: `object`
- Summary: A composition of multiple layers, resolved in dependency order.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `layers` | `list[Layer]` | `` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `build_all` | `async def build_all(self, initial_deps: dict[str, Any] \| None=None)` | Build all layers in dependency order. |
| `register_with` | `async def register_with(self, registry: EffectRegistry, initial_deps: dict[str, Any] \| None=None)` | Build all layers and register providers with the registry. |

### `FlowPipeline`

- Source: `aquilia/flow.py`
- Bases: `object`
- Summary: Composable, typed request pipeline with automatic effect management.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `guard` | `def guard(self, callable_or_node: Callable \| FlowNode, *, name: str \| None=None, priority: int=PRIORITY_AUTH, effects: list[str] \| None=None, condition: Callable \| None=None)` | Add a guard node. Guards can short-circuit the pipeline. |
| `transform` | `def transform(self, callable_or_node: Callable \| FlowNode, *, name: str \| None=None, priority: int=PRIORITY_TRANSFORM, effects: list[str] \| None=None)` | Add a transform node. Transforms modify the context/request data. |
| `handler` | `def handler(self, callable_or_node: Callable \| FlowNode, *, name: str \| None=None, priority: int=PRIORITY_DEFAULT, effects: list[str] \| None=None)` | Set the handler node. The handler is the core business logic. |
| `hook` | `def hook(self, callable_or_node: Callable \| FlowNode, *, name: str \| None=None, priority: int=PRIORITY_LOG, effects: list[str] \| None=None)` | Add a post-handler hook. Hooks run after the handler. |
| `effect` | `def effect(self, callable_or_node: Callable \| FlowNode, *, name: str \| None=None, priority: int=PRIORITY_DEFAULT - 5, effects: list[str] \| None=None)` | Add an effect node. Effect nodes manage resource acquisition. |
| `middleware` | `def middleware(self, callable_or_node: Callable \| FlowNode, *, name: str \| None=None, priority: int=PRIORITY_CRITICAL)` | Add a middleware node. Middleware wraps the entire pipeline. |
| `add_node` | `def add_node(self, node: FlowNode)` | Add a pre-built FlowNode. |
| `add_nodes` | `def add_nodes(self, nodes: Sequence[FlowNode])` | Add multiple pre-built FlowNodes. |
| `compose` | `def compose(self, *other: FlowPipeline)` | Compose this pipeline with others. |
| `execute` | `async def execute(self, context: FlowContext, effect_registry: EffectRegistry \| None=None)` | Execute the pipeline. |
| `execute_with_timeout` | `async def execute_with_timeout(self, context: FlowContext, effect_registry: EffectRegistry \| None=None, timeout: float \| None=None)` | Execute pipeline with optional timeout. |
| `nodes` | `def nodes(self)` | Return a copy of the node list. |
| `required_effects` | `def required_effects(self)` | All effects required by this pipeline. |

### `EffectScope`

- Source: `aquilia/flow.py`
- Bases: `object`
- Summary: Async context manager that acquires and releases effects.

### `SubsystemStatus`

- Source: `aquilia/health.py`
- Bases: `str, Enum`
- Summary: Status of a subsystem.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `HEALTHY` | `` | `'healthy'` |
| `DEGRADED` | `` | `'degraded'` |
| `UNHEALTHY` | `` | `'unhealthy'` |
| `UNKNOWN` | `` | `'unknown'` |
| `STARTING` | `` | `'starting'` |
| `STOPPED` | `` | `'stopped'` |

### `HealthStatus`

- Source: `aquilia/health.py`
- Bases: `object`
- Summary: Health status for a single subsystem.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `status` | `SubsystemStatus` | `SubsystemStatus.UNKNOWN` |
| `latency_ms` | `float` | `0.0` |
| `message` | `str` | `''` |
| `details` | `dict[str, Any]` | `field(default_factory=dict)` |
| `checked_at` | `datetime` | `field(default_factory=lambda: datetime.now(timezone.utc))` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize for JSON response. |

### `HealthRegistry`

- Source: `aquilia/health.py`
- Bases: `object`
- Summary: Centralized health tracking for all subsystems.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `register` | `def register(self, name: str, status: HealthStatus)` | Register or update a subsystem's health status. |
| `register_check` | `def register_check(self, name: str, check: Callable[[], HealthStatus])` | Register a health check function for periodic evaluation. |
| `update` | `def update(self, name: str, status: SubsystemStatus, message: str='')` | Update an existing subsystem's status. |
| `get` | `def get(self, name: str)` | Get a specific subsystem's health status. |
| `all_statuses` | `def all_statuses(self)` | Get all registered health statuses. |
| `overall` | `def overall(self)` | Compute aggregate health across all subsystems. |
| `to_dict` | `def to_dict(self)` | Serialize full health report for /health endpoint. |
| `run_checks` | `async def run_checks(self)` | Run all registered health checks and update statuses. |

### `LifecyclePhase`

- Source: `aquilia/lifecycle.py`
- Bases: `Enum`
- Summary: Lifecycle phases.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `INIT` | `` | `'init'` |
| `STARTING` | `` | `'starting'` |
| `READY` | `` | `'ready'` |
| `STOPPING` | `` | `'stopping'` |
| `STOPPED` | `` | `'stopped'` |
| `ERROR` | `` | `'error'` |

### `LifecycleEvent`

- Source: `aquilia/lifecycle.py`
- Bases: `object`
- Summary: Event emitted during lifecycle transitions.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `phase` | `LifecyclePhase` | `` |
| `app_name` | `str \| None` | `None` |
| `message` | `str \| None` | `None` |
| `error` | `Exception \| None` | `None` |

### `LifecycleError`

- Source: `aquilia/lifecycle.py`
- Bases: `Exception`
- Summary: Raised when lifecycle operation fails.

### `LifecycleCoordinator`

- Source: `aquilia/lifecycle.py`
- Bases: `object`
- Summary: Coordinates application lifecycle across multiple apps.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `on_event` | `def on_event(self, handler: Callable[[LifecycleEvent], None])` | Register event handler. |
| `startup` | `async def startup(self)` | Execute startup hooks for all apps in dependency order. |
| `shutdown` | `async def shutdown(self)` | Execute shutdown hooks for all started apps in reverse order. |
| `restart` | `async def restart(self)` | Restart the application (shutdown then startup). |
| `get_status` | `def get_status(self)` | Get current lifecycle status. |

### `LifecycleManager`

- Source: `aquilia/lifecycle.py`
- Bases: `object`
- Summary: High-level lifecycle manager with context manager support.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `on_event` | `def on_event(self, handler: Callable[[LifecycleEvent], None])` | Register event handler. |

### `ComponentKind`

- Source: `aquilia/manifest.py`
- Bases: `str, Enum`
- Summary: Classification of framework components for auto-discovery.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CONTROLLER` | `` | `'controller'` |
| `SERVICE` | `` | `'service'` |
| `MIDDLEWARE` | `` | `'middleware'` |
| `GUARD` | `` | `'guard'` |
| `PIPE` | `` | `'pipe'` |
| `INTERCEPTOR` | `` | `'interceptor'` |
| `EFFECT` | `` | `'effect'` |
| `MODEL` | `` | `'model'` |
| `FAULT_HANDLER` | `` | `'fault_handler'` |
| `SOCKET_CONTROLLER` | `` | `'socket_controller'` |
| `SERIALIZER` | `` | `'serializer'` |

### `ComponentRef`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Summary: Universal typed reference to any framework component.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `class_path` | `str` | `` |
| `kind` | `ComponentKind` | `` |
| `metadata` | `ManifestMetadata` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `module_path` | `def module_path(self)` | Extract the module path (before ':'). |
| `class_name` | `def class_name(self)` | Extract the class name (after ':'). |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary. |

### `ServiceScope`

- Source: `aquilia/manifest.py`
- Bases: `str, Enum`
- Summary: Service lifecycle scope.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `SINGLETON` | `` | `'singleton'` |
| `APP` | `` | `'app'` |
| `REQUEST` | `` | `'request'` |
| `TRANSIENT` | `` | `'transient'` |
| `POOLED` | `` | `'pooled'` |
| `EPHEMERAL` | `` | `'ephemeral'` |

### `LifecycleConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Summary: Lifecycle hook configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `on_startup` | `str \| None` | `None` |
| `on_shutdown` | `str \| None` | `None` |
| `depends_on` | `list[str]` | `field(default_factory=list)` |
| `startup_timeout` | `float` | `30.0` |
| `shutdown_timeout` | `float` | `30.0` |
| `error_strategy` | `str` | `'propagate'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary. |

### `ServiceConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Summary: Service registration configuration with complete DI support.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `class_path` | `str` | `` |
| `scope` | `ServiceScope` | `ServiceScope.APP` |
| `auto_discover` | `bool` | `True` |
| `lifecycle` | `LifecycleConfig \| None` | `None` |
| `feature_flags` | `list[str]` | `field(default_factory=list)` |
| `aliases` | `list[str]` | `field(default_factory=list)` |
| `factory` | `str \| None` | `None` |
| `factory_args` | `dict[str, Any] \| None` | `None` |
| `config` | `dict[str, Any] \| None` | `None` |
| `observable` | `bool` | `True` |
| `required` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary. |

### `MiddlewareConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Summary: Middleware registration configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `class_path` | `str` | `` |
| `scope` | `str` | `'global'` |
| `scope_target` | `str \| None` | `None` |
| `priority` | `int` | `50` |
| `condition` | `Callable \| None` | `None` |
| `config` | `dict[str, Any] \| None` | `None` |
| `on_error` | `str` | `'propagate'` |
| `fallback` | `str \| None` | `None` |
| `observable` | `bool` | `True` |
| `log_requests` | `bool` | `False` |
| `log_responses` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary. |

### `SessionConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Summary: Session management configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `enabled` | `bool` | `True` |
| `ttl` | `timedelta` | `field(default_factory=lambda: timedelta(days=7))` |
| `idle_timeout` | `timedelta \| None` | `None` |
| `renewal` | `timedelta \| None` | `None` |
| `transport` | `str` | `'cookie'` |
| `transport_config` | `dict[str, Any] \| None` | `None` |
| `cookie_name` | `str` | `'session_id'` |
| `cookie_domain` | `str \| None` | `None` |
| `cookie_path` | `str` | `'/'` |
| `cookie_secure` | `bool` | `True` |
| `cookie_httponly` | `bool` | `True` |
| `cookie_samesite` | `str` | `'Strict'` |
| `store` | `str` | `'memory'` |
| `store_config` | `dict[str, Any] \| None` | `None` |
| `encryption_enabled` | `bool` | `True` |
| `encryption_key_env` | `str` | `'SESSION_ENCRYPTION_KEY'` |
| `serializer` | `str` | `'json'` |
| `log_lifecycle` | `bool` | `False` |
| `metrics_enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary. |

### `FaultHandlerConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Summary: Fault handler configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `domain` | `str` | `` |
| `handler_path` | `str` | `` |
| `recovery_strategy` | `str` | `'propagate'` |
| `fallback_response` | `dict[str, Any] \| None` | `None` |

### `FaultHandlingConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Summary: Fault/error handling configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `default_domain` | `str` | `'APP'` |
| `strategy` | `str` | `'propagate'` |
| `handlers` | `list[FaultHandlerConfig]` | `field(default_factory=list)` |
| `middlewares` | `list[MiddlewareConfig]` | `field(default_factory=list)` |
| `metrics_enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary. |

### `FeatureConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Summary: Feature flag configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `enabled` | `bool` | `False` |
| `conditions` | `dict[str, Any] \| None` | `None` |
| `services` | `list[str]` | `field(default_factory=list)` |
| `controllers` | `list[str]` | `field(default_factory=list)` |
| `middleware` | `list[MiddlewareConfig]` | `field(default_factory=list)` |
| `routes` | `list[str]` | `field(default_factory=list)` |
| `log_usage` | `bool` | `True` |
| `metrics_enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary. |

### `BackgroundTaskConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Summary: Per-module background task configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `tasks` | `list[str]` | `field(default_factory=list)` |
| `default_queue` | `str` | `'default'` |
| `auto_discover` | `bool` | `True` |
| `enabled` | `bool` | `True` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `TemplateConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Summary: Template engine configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `enabled` | `bool` | `True` |
| `search_paths` | `list[str]` | `field(default_factory=list)` |
| `precompile` | `bool` | `False` |
| `cache` | `str` | `'memory'` |
| `sandbox` | `bool` | `True` |
| `context_processors` | `list[str]` | `field(default_factory=list)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` |  |

### `DatabaseConfig`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Summary: DEPRECATED: Manifest-level database configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `url` | `str` | `'sqlite:///db.sqlite3'` |
| `auto_connect` | `bool` | `True` |
| `auto_create` | `bool` | `True` |
| `auto_migrate` | `bool` | `False` |
| `migrations_dir` | `str` | `'migrations'` |
| `pool_size` | `int` | `5` |
| `echo` | `bool` | `False` |
| `model_paths` | `list[str]` | `field(default_factory=list)` |
| `scan_dirs` | `list[str]` | `field(default_factory=lambda: ['models'])` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize to dictionary. |

### `AppManifest`

- Source: `aquilia/manifest.py`
- Bases: `object`
- Summary: Production-grade application manifest for complete app configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `name` | `str` | `` |
| `version` | `str` | `` |
| `description` | `str` | `''` |
| `author` | `str` | `''` |
| `services` | `list[str \| ServiceConfig \| ComponentRef]` | `field(default_factory=list)` |
| `controllers` | `list[str \| ComponentRef]` | `field(default_factory=list)` |
| `socket_controllers` | `list[str \| ComponentRef]` | `field(default_factory=list)` |
| `models` | `list[str \| ComponentRef]` | `field(default_factory=list)` |
| `serializers` | `list[str \| ComponentRef]` | `field(default_factory=list)` |
| `guards` | `list[str \| ComponentRef]` | `field(default_factory=list)` |
| `pipes` | `list[str \| ComponentRef]` | `field(default_factory=list)` |
| `interceptors` | `list[str \| ComponentRef]` | `field(default_factory=list)` |
| `middleware` | `list[str \| MiddlewareConfig \| ComponentRef]` | `field(default_factory=list)` |
| `route_prefix` | `str` | `'/'` |
| `base_path` | `str \| None` | `None` |
| `lifecycle` | `LifecycleConfig \| None` | `None` |
| `sessions` | `list[SessionConfig]` | `field(default_factory=list)` |
| `templates` | `TemplateConfig \| None` | `None` |
| `database` | `DatabaseConfig \| None` | `None` |
| `faults` | `FaultHandlingConfig \| None` | `None` |
| `background_tasks` | `BackgroundTaskConfig \| None` | `None` |
| `features` | `list[FeatureConfig]` | `field(default_factory=list)` |
| `exports` | `list[str]` | `field(default_factory=list)` |
| `imports` | `list[str]` | `field(default_factory=list)` |
| `depends_on` | `list[str]` | `field(default_factory=list)` |
| `tags` | `list[str]` | `field(default_factory=list)` |
| `config_schema` | `dict[str, Any] \| None` | `None` |
| `auto_discover` | `bool` | `True` |
| `discover_patterns` | `list[str]` | `field(default_factory=lambda: ['controllers', 'services', 'middleware', 'guards', 'models', 'tasks'])` |
| `middlewares` | `list[tuple[str, dict]]` | `field(default_factory=list)` |
| `default_fault_domain` | `str \| None` | `None` |
| `on_startup` | `Callable \| None` | `None` |
| `on_shutdown` | `Callable \| None` | `None` |
| `config` | `type \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(self)` | Serialize manifest to dictionary (for fingerprinting and inspection). |
| `fingerprint` | `def fingerprint(self)` | Generate stable hash of manifest for reproducible deploys. |

### `MiddlewareDescriptor`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Descriptor for middleware registration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `middleware` | `Middleware` | `` |
| `scope` | `str` | `` |
| `priority` | `int` | `` |
| `name` | `str` | `` |

### `MiddlewareStack`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Manages middleware stack with deterministic ordering. Order: Global < App < Controller < Route, then by priority.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `add` | `def add(self, middleware: Middleware, scope: str='global', priority: int=50, name: str \| None=None)` | Add middleware to stack. |
| `build_handler` | `def build_handler(self, final_handler: Handler)` | Build middleware chain wrapping the final handler. |
| `build_fast_handler` | `def build_fast_handler(self, final_handler: Handler)` | Build a *minimal* middleware chain for latency-sensitive routes. |

### `RequestIdMiddleware`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Adds unique request ID to each request.

### `ExceptionMiddleware`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Catches exceptions and converts them to error responses.

### `LoggingMiddleware`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Logs request/response with timing.

### `TimeoutMiddleware`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Enforces request timeout.

### `CORSMiddleware`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Handles CORS headers.

### `CompressionMiddleware`

- Source: `aquilia/middleware.py`
- Bases: `object`
- Summary: Compresses response bodies.

### `Secret`

- Source: `aquilia/pyconfig.py`
- Bases: `object`
- Summary: A configuration field that holds a sensitive value (password, API key …).

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `reveal` | `def reveal(self)` | Return the actual secret value (use deliberately). |
| `env_name` | `def env_name(self)` | Return the environment variable name, if any. |
| `is_required` | `def is_required(self)` | Return whether this secret is required. |

### `Env`

- Source: `aquilia/pyconfig.py`
- Bases: `object`
- Summary: Bind a configuration field to an environment variable.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `name` | `def name(self)` | Return the environment variable name. |
| `default` | `def default(self)` | Return the default value. |
| `is_required` | `def is_required(self)` | Return whether this env var is required. |
| `resolve` | `def resolve(self, *, use_cache: bool=False)` | Return the resolved value from the environment or default. |
| `invalidate_cache` | `def invalidate_cache(self)` | Invalidate the cached resolved value. |
| `disable_auto_load` | `def disable_auto_load(cls)` | Disable automatic .env loading. |
| `enable_auto_load` | `def enable_auto_load(cls)` | Enable automatic .env loading (default behavior). |

### `AquilaConfig`

- Source: `aquilia/pyconfig.py`
- Bases: `object`
- Summary: Base class for Aquilia Python-native configuration.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `env` | `str` | `'dev'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `to_dict` | `def to_dict(cls, *, use_cache: bool=True)` | Serialise this config class into a plain nested dict. |
| `invalidate_cache` | `def invalidate_cache(cls)` | Invalidate the cached config dict for this class. |
| `clear_all_caches` | `def clear_all_caches(cls)` | Clear all config class caches. |
| `to_loader` | `def to_loader(cls)` | Convert this Python config into a :class:`~aquilia.config.ConfigLoader`. |
| `get` | `def get(cls, path: str, default: Any=None)` | Dot-path accessor on the serialised config dict. |
| `for_env` | `def for_env(cls, env_name: str)` | Resolve the correct subclass for *env_name* from the subclass tree. |
| `from_env_var` | `def from_env_var(cls, var: str='AQ_ENV', default: str='dev')` | Read ``var`` from the environment and return the matching subclass. |

### `PyConfigLoader`

- Source: `aquilia/pyconfig.py`
- Bases: `object`
- Summary: Load an ``AquilaConfig`` subclass from a Python source file.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `from_file` | `def from_file(cls, path: str \| Path, *, env: str \| None=None, var: str='AQ_ENV', default_env: str='dev')` | Import a Python config file and resolve the right subclass. |
| `to_aquilia_loader` | `def to_aquilia_loader(self)` | Return a fully populated :class:`~aquilia.config.ConfigLoader`. |
| `config_class` | `def config_class(self)` | The resolved :class:`AquilaConfig` subclass. |

### `RequestFault`

- Source: `aquilia/request.py`
- Bases: `Fault`
- Summary: Base class for request-related faults.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `public` | `` | `True` |

### `BadRequest`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Malformed request (400).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'BAD_REQUEST'` |
| `message` | `` | `'Bad request'` |

### `PayloadTooLarge`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Request payload exceeds limits (413).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'PAYLOAD_TOO_LARGE'` |
| `message` | `` | `'Payload too large'` |

### `UnsupportedMediaType`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Unsupported Content-Type (415).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'UNSUPPORTED_MEDIA_TYPE'` |
| `message` | `` | `'Unsupported media type'` |

### `ClientDisconnect`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Client disconnected during request (499).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'CLIENT_DISCONNECT'` |
| `message` | `` | `'Client disconnected'` |

### `InvalidJSON`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Invalid JSON payload (400).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'INVALID_JSON'` |
| `message` | `` | `'Invalid JSON'` |

### `InvalidSurp`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Invalid SURP binary payload (400).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'INVALID_SURP'` |
| `message` | `` | `'Invalid SURP payload'` |

### `SurpUnavailable`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: SURP library not installed (500-level).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'SURP_UNAVAILABLE'` |
| `message` | `` | `'SURP serializer not available'` |
| `public` | `` | `False` |

### `InvalidHeader`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Invalid header format (400).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'INVALID_HEADER'` |
| `message` | `` | `'Invalid header'` |

### `MultipartParseError`

- Source: `aquilia/request.py`
- Bases: `RequestFault`
- Summary: Multipart parsing failed (400).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'MULTIPART_PARSE_ERROR'` |
| `message` | `` | `'Multipart parsing failed'` |

### `Request`

- Source: `aquilia/request.py`
- Bases: `object`
- Summary: Production-grade request object for Aquilia.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `method` | `def method(self)` | HTTP method (GET, POST, etc.). |
| `http_version` | `def http_version(self)` | HTTP version (e.g., '1.1', '2'). |
| `path` | `def path(self)` | Request path (decoded). |
| `raw_path` | `def raw_path(self)` | Raw request path (as bytes from ASGI). |
| `query_string` | `def query_string(self)` | Raw query string. |
| `client` | `def client(self)` | Client address (host, port). |
| `query_params` | `def query_params(self)` | Get parsed query parameters as MultiDict. |
| `query_param` | `def query_param(self, name: str, default: str \| None=None)` | Get single query parameter. |
| `headers` | `def headers(self)` | Get parsed headers. |
| `header` | `def header(self, name: str, default: str \| None=None)` | Get single header (case-insensitive). |
| `has_header` | `def has_header(self, name: str)` | Check if header exists. |
| `cookies` | `def cookies(self)` | Get parsed cookies. |
| `cookie` | `def cookie(self, name: str, default: str \| None=None)` | Get single cookie value. |
| `url` | `def url(self)` | Get full request URL. |
| `base_url` | `def base_url(self)` | Get base URL (scheme + host + root_path). |
| `url_for` | `def url_for(self, route_name: str, /, **params)` | Build URL for named route. |
| `client_ip` | `def client_ip(self)` | Get client IP address. |
| `content_type` | `def content_type(self)` | Get Content-Type header. |
| `content_length` | `def content_length(self)` | Get Content-Length header as int. |
| `is_json` | `def is_json(self)` | Check if request content type is JSON. |
| `is_surp` | `def is_surp(self)` | Check if request content type is SURP binary. |
| `accepts` | `def accepts(self, *media_types: str)` | Check if client accepts any of the given media types. |
| `accepts_surp` | `def accepts_surp(self)` | Check if the client accepts SURP binary responses. |
| `prefers_surp` | `def prefers_surp(self)` | Check if the client prefers SURP over JSON. |
| `best_response_format` | `def best_response_format(self)` | Negotiate the best response format between SURP and JSON. |
| `range` | `def range(self)` | Parse Range header. |
| `if_modified_since` | `def if_modified_since(self)` | Parse If-Modified-Since header. |
| `if_none_match` | `def if_none_match(self)` | Get If-None-Match header (ETag). |
| `auth_scheme` | `def auth_scheme(self)` | Get authorization scheme (e.g., 'Bearer', 'Basic'). |
| `auth_credentials` | `def auth_credentials(self)` | Get authorization credentials. |
| `is_disconnected` | `def is_disconnected(self)` | Check if client has disconnected. |
| `iter_bytes` | `async def iter_bytes(self, chunk_size: int \| None=None)` | Stream request body in chunks. |
| `iter_text` | `async def iter_text(self, encoding: str='utf-8', chunk_size: int \| None=None)` | Stream request body as text chunks. |
| `body` | `async def body(self)` | Read full request body (idempotent). |
| `text` | `async def text(self, encoding: str \| None=None)` | Read request body as text. |
| `readexactly` | `async def readexactly(self, n: int)` | Read exactly n bytes from request body. |
| `json` | `async def json(self, model: type[T] \| None=None, *, strict: bool=True)` | Parse request body as JSON. |
| `surp` | `async def surp(self, model: type[T] \| None=None, *, strict: bool=True)` | Parse request body as SURP binary format. |
| `data` | `async def data(self, model: type[T] \| None=None, *, strict: bool=True)` | Parse request body as JSON **or** SURP, auto-detected. |
| `form` | `async def form(self)` | Parse application/x-www-form-urlencoded form data. |
| `multipart` | `async def multipart(self)` | Parse multipart/form-data. |
| `files` | `async def files(self)` | Get uploaded files from multipart request. |
| `save_upload` | `async def save_upload(self, upload: UploadFile, dest: str \| PathLike, *, overwrite: bool=False)` | Save uploaded file to destination. |
| `stream_upload_to_store` | `async def stream_upload_to_store(self, upload: UploadFile, store: UploadStore)` | Stream upload to custom storage backend. |
| `identity` | `def identity(self)` | Get authenticated identity (set by AuthMiddleware). |
| `authenticated` | `def authenticated(self)` | Check if request is authenticated. |
| `require_identity` | `def require_identity(self)` | Get identity or raise AUTH_REQUIRED fault. |
| `has_role` | `def has_role(self, role: str)` | Check if identity has specific role. |
| `has_scope` | `def has_scope(self, scope: str)` | Check if identity has OAuth scope. |
| `session` | `def session(self)` | Get session (set by SessionMiddleware). |
| `session` | `def session(self, value)` | Set session in request state. |
| `require_session` | `def require_session(self)` | Get session or raise SESSION_REQUIRED fault. |
| `session_id` | `def session_id(self)` | Get session ID. |
| `container` | `def container(self)` | Get request-scoped DI container. |
| `resolve` | `async def resolve(self, service_type: type[T], *, optional: bool=False)` | Resolve service from DI container. |
| `inject` | `async def inject(self, **services)` | Inject multiple services by name. |
| `flash_messages` | `def flash_messages(self)` | Get and clear flash messages from session. |
| `is_authenticated` | `def is_authenticated(self)` | Check if request is authenticated. |
| `template_context` | `def template_context(self)` | Get template rendering context with auto-injected variables. |
| `add_template_context` | `def add_template_context(self, **kwargs)` | Add variables to template context. |
| `emit_effect` | `async def emit_effect(self, effect_name: str, **data)` | Emit effect for lifecycle hooks. |
| `get_effect` | `def get_effect(self, name: str)` | Get an acquired effect resource by name. |
| `has_effect` | `def has_effect(self, name: str)` | Check if an effect resource is currently acquired. |
| `effects` | `def effects(self)` | All currently acquired effect resources. |
| `flow_context` | `def flow_context(self)` | Get the FlowContext for this request, if available. |
| `before_response` | `async def before_response(self, callback: Callable[..., Awaitable[None]])` | Register callback to run before response is sent. |
| `after_response` | `async def after_response(self, callback: Callable[..., Awaitable[None]])` | Register callback to run after response is sent. |
| `fault_context` | `def fault_context(self)` | Get context for fault reporting. |
| `report_fault` | `async def report_fault(self, fault: Fault)` | Report fault through FaultEngine with request context. |
| `trace_id` | `def trace_id(self)` | Get trace ID for distributed tracing. |
| `request_id` | `def request_id(self)` | Get unique request ID. |
| `record_metric` | `def record_metric(self, name: str, value: float, **tags)` | Record metric for this request. |
| `cleanup` | `async def cleanup(self)` | Clean up temporary resources. |
| `path_params` | `def path_params(self)` | Get path parameters (set by router via state). |

### `BackgroundTask`

- Source: `aquilia/response.py`
- Bases: `Protocol`
- Summary: Protocol for background tasks executed after response is sent.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `run` | `async def run(self)` | Execute the background task. |

### `CallableBackgroundTask`

- Source: `aquilia/response.py`
- Bases: `object`
- Summary: Simple callable-based background task.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `func` | `Callable[[], Awaitable[None]]` | `` |
| `run_on_disconnect` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `run` | `async def run(self)` |  |

### `ServerSentEvent`

- Source: `aquilia/response.py`
- Bases: `object`
- Summary: Server-Sent Event data structure.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `data` | `str` | `` |
| `id` | `str \| None` | `None` |
| `event` | `str \| None` | `None` |
| `retry` | `int \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `encode` | `def encode(self)` | Encode SSE event according to spec. |

### `MediaChunk`

- Source: `aquilia/response.py`
- Bases: `object`
- Summary: Type-safe media chunk container for streaming payloads.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `data` | `bytes \| str` | `` |
| `content_type` | `str \| None` | `None` |
| `is_final` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `encode` | `def encode(self, encoding: str='utf-8')` |  |

### `HLSSegment`

- Source: `aquilia/response.py`
- Bases: `object`
- Summary: Single media segment entry in an HLS media playlist.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `uri` | `str` | `` |
| `duration` | `float` | `` |
| `title` | `str \| None` | `None` |
| `byte_range` | `str \| None` | `None` |
| `discontinuity` | `bool` | `False` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `render` | `def render(self)` |  |

### `HLSVariant`

- Source: `aquilia/response.py`
- Bases: `object`
- Summary: Variant stream descriptor for an HLS master playlist.
- Decorators: `dataclass(frozen=True, slots=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `uri` | `str` | `` |
| `bandwidth` | `int` | `` |
| `resolution` | `str \| None` | `None` |
| `codecs` | `str \| None` | `None` |
| `frame_rate` | `float \| None` | `None` |
| `audio` | `str \| None` | `None` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `render` | `def render(self)` |  |

### `CookieSigner`

- Source: `aquilia/response.py`
- Bases: `object`
- Summary: Cookie signer with HMAC-based signing and key rotation support.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sign` | `def sign(self, value: str)` | Sign a cookie value. |
| `unsign` | `def unsign(self, signed_value: str)` | Verify and unsign a cookie value. |

### `ResponseStreamError`

- Source: `aquilia/response.py`
- Bases: `Fault`
- Summary: Error during response streaming.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'RESPONSE_STREAM_ERROR'` |

### `TemplateRenderError`

- Source: `aquilia/response.py`
- Bases: `Fault`
- Summary: Template rendering error during response.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'TEMPLATE_RENDER_ERROR'` |
| `message` | `` | `'Template rendering failed'` |

### `InvalidHeaderError`

- Source: `aquilia/response.py`
- Bases: `Fault`
- Summary: Invalid header name or value (injection attempt).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'INVALID_HEADER'` |

### `ClientDisconnectError`

- Source: `aquilia/response.py`
- Bases: `Fault`
- Summary: Client disconnected during response send.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'CLIENT_DISCONNECT'` |

### `RangeNotSatisfiableError`

- Source: `aquilia/response.py`
- Bases: `Fault`
- Summary: Invalid Range header (416 response).

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'RANGE_NOT_SATISFIABLE'` |

### `HLSManifestError`

- Source: `aquilia/response.py`
- Bases: `Fault`
- Summary: Invalid HLS manifest payload or helper usage.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `code` | `` | `'HLS_MANIFEST_ERROR'` |

### `Response`

- Source: `aquilia/response.py`
- Bases: `object`
- Summary: Production-grade HTTP response with ASGI 3 streaming support.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `headers` | `def headers(self)` | Get response headers. |
| `json` | `def json(cls, obj: Any, status: int=200, *, encoder: Callable[[Any], str] \| None=None, headers: Mapping[str, str] \| None=None, **kwargs)` | Create JSON response. |
| `html` | `def html(cls, content: str, status: int=200, **kwargs)` | Create HTML response. |
| `text` | `def text(cls, content: str, status: int=200, **kwargs)` | Create plain text response. |
| `redirect` | `def redirect(cls, url: str, status: int=307, *, headers: dict[str, str] \| None=None)` | Create redirect response. |
| `stream` | `def stream(cls, iterator: AsyncIterator[bytes] \| Iterator[bytes], status: int=200, media_type: str='application/octet-stream', **kwargs)` | Create streaming response. |
| `media_stream` | `def media_stream(cls, chunks: AsyncIterator[MediaChunk] \| Iterator[MediaChunk], status: int=200, media_type: str='application/octet-stream', **kwargs)` | Create a type-safe media chunk streaming response. |
| `sse` | `def sse(cls, event_iter: AsyncIterator[ServerSentEvent], status: int=200, **kwargs)` | Create Server-Sent Events (SSE) response. |
| `surp` | `def surp(cls, obj: Any, status: int=200, *, headers: Mapping[str, str] \| None=None, compression: str \| None=None, dedup: bool=True, **kwargs)` | Create a SURP binary response. |
| `negotiated` | `def negotiated(cls, obj: Any, request: Any, status: int=200, *, headers: Mapping[str, str] \| None=None, **kwargs)` | Create a response with automatic content negotiation. |
| `file` | `def file(cls, path: PathLike, *, filename: str \| None=None, media_type: str \| None=None, status: int=200, use_sendfile: bool=True, chunk_size: int=64 * 1024, **kwargs)` | Create file download response. |
| `hls_playlist` | `def hls_playlist(cls, segments: Sequence[HLSSegment], *, target_duration: int \| None=None, media_sequence: int=0, version: int=3, endlist: bool=True, status: int=200, headers: Mapping[str, str] \| None=None)` | Create an HLS media playlist (.m3u8) response. |
| `hls_master_playlist` | `def hls_master_playlist(cls, variants: Sequence[HLSVariant], *, version: int=3, status: int=200, headers: Mapping[str, str] \| None=None)` | Create an HLS master playlist response. |
| `hls_segment` | `def hls_segment(cls, path: PathLike, *, status: int=200, chunk_size: int=64 * 1024, headers: Mapping[str, str] \| None=None)` | Create an HLS segment file response with media-aware defaults. |
| `render` | `async def render(cls, template_name: str, context: Mapping[str, Any] \| None=None, *, request: Any \| None=None, request_ctx: Any \| None=None, engine: Any \| None=None, status: int=200, headers: Mapping \| None=None, **response_kwargs)` | Render template with automatic context injection. |
| `commit_session` | `async def commit_session(self, request: Any)` | Commit session changes after response. |
| `execute_before_send_hooks` | `async def execute_before_send_hooks(self, request: Any)` | Execute before-response callbacks registered on request. |
| `execute_after_send_hooks` | `async def execute_after_send_hooks(self, request: Any)` | Execute after-response callbacks registered on request. |
| `record_response_metrics` | `def record_response_metrics(self, request: Any, duration_ms: float)` | Record response metrics. |
| `from_fault` | `def from_fault(cls, fault: Fault, *, include_details: bool=False, request: Any \| None=None)` | Create Response from Fault with appropriate status code. |
| `set_cookie` | `def set_cookie(self, name: str, value: str, *, max_age: int \| None=None, expires: datetime \| None=None, path: str='/', domain: str \| None=None, secure: bool=True, httponly: bool=True, samesite: str \| None='Lax', same_site_policy: str \| None=None, signed: bool=False, signer: CookieSigner \| None=None)` | Set a cookie. |
| `delete_cookie` | `def delete_cookie(self, name: str, path: str='/', domain: str \| None=None)` | Delete a cookie by setting Max-Age=0. |
| `set_header` | `def set_header(self, name: str, value: str)` | Set header (replaces existing). |
| `add_header` | `def add_header(self, name: str, value: str)` | Add header (supports multiple values). |
| `unset_header` | `def unset_header(self, name: str)` | Remove header. |
| `set_etag` | `def set_etag(self, etag: str, weak: bool=False)` | Set ETag header. |
| `set_last_modified` | `def set_last_modified(self, dt: datetime)` | Set Last-Modified header. |
| `cache_control` | `def cache_control(self, **directives)` | Set Cache-Control header. |
| `secure_headers` | `def secure_headers(self, *, hsts: bool=True, hsts_max_age: int=31536000, csp: str \| None=None, frame_options: str='DENY', content_type_options: bool=True, xss_protection: bool=True, referrer_policy: str='strict-origin-when-cross-origin')` | Set recommended security headers. |
| `send_asgi` | `async def send_asgi(self, send: Callable[[dict], Awaitable[None]], request: Any \| None=None)` | Send response via ASGI. |

### `RuntimePhase`

- Source: `aquilia/runtime.py`
- Bases: `str, Enum`
- Summary: Lifecycle phase of an :class:`AquiliaRuntime` instance.

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `CREATED` | `` | `'created'` |
| `CONFIGURING` | `` | `'configuring'` |
| `DISCOVERING` | `` | `'discovering'` |
| `BOOTSTRAPPING` | `` | `'bootstrapping'` |
| `READY` | `` | `'ready'` |
| `RUNNING` | `` | `'running'` |
| `SHUTTING_DOWN` | `` | `'shutting_down'` |
| `STOPPED` | `` | `'stopped'` |
| `FAILED` | `` | `'failed'` |

### `RuntimeConfig`

- Source: `aquilia/runtime.py`
- Bases: `object`
- Summary: Immutable configuration for an :class:`AquiliaRuntime` instance.
- Decorators: `dataclass(frozen=True)`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `workspace_root` | `Path` | `` |
| `mode` | `Literal['dev', 'test', 'prod']` | `'prod'` |
| `debug` | `bool \| None` | `None` |
| `config_overrides` | `dict[str, Any]` | `field(default_factory=dict)` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `is_dev` | `def is_dev(self)` | Whether the runtime is in development mode. |
| `workspace_file` | `def workspace_file(self)` | Path to ``workspace.py``. |
| `modules_dir` | `def modules_dir(self)` | Path to the ``modules/`` directory. |

### `AquiliaRuntime`

- Source: `aquilia/runtime.py`
- Bases: `object`
- Summary: Structured ASGI bootstrap lifecycle manager.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `phase` | `def phase(self)` | Current lifecycle phase. |
| `app` | `def app(self)` | The ASGI application callable. |
| `server` | `def server(self)` | The :class:`~aquilia.server.AquiliaServer` instance. |
| `workspace_name` | `def workspace_name(self)` | Workspace name extracted from ``workspace.py``. |
| `module_names` | `def module_names(self)` | List of discovered module names. |
| `configure` | `def configure(self)` | Bootstrap paths, environment variables, logging, and config. |
| `discover` | `def discover(self)` | Discover workspace name, module manifests, and workspace module configs. |
| `bootstrap` | `def bootstrap(self)` | Construct the :class:`~aquilia.server.AquiliaServer`. |
| `from_workspace` | `def from_workspace(cls, workspace_root: Path \| str \| None=None, mode: str \| None=None, *, config_overrides: dict[str, Any] \| None=None)` | Create a fully bootstrapped runtime from workspace configuration. |
| `create_app` | `def create_app(cls, workspace_root: Path \| str \| None=None, mode: str \| None=None, *, config_overrides: dict[str, Any] \| None=None)` | One-liner factory returning just the ASGI callable. |

### `AquiliaServer`

- Source: `aquilia/server.py`
- Bases: `object`
- Summary: Main Aquilia server that orchestrates all components with lifecycle management.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `startup` | `async def startup(self)` | Execute startup sequence with Aquilary lifecycle management. |
| `shutdown` | `async def shutdown(self)` | Execute shutdown sequence with Aquilary lifecycle management. |
| `get_health` | `def get_health(self)` | Get current server health status (v2). |
| `graceful_shutdown` | `async def graceful_shutdown(self, timeout: float=30.0)` | Graceful shutdown sequence (v2). |
| `run` | `def run(self, host: str \| None=None, port: int \| None=None, reload: bool \| None=None, log_level: str='info', graceful_timeout: float=30.0)` | Run the development server with graceful shutdown support. |
| `get_asgi_app` | `def get_asgi_app(self)` | Get the ASGI application for external servers. |
| `lifespan` | `def lifespan(self)` | ASGI lifespan context manager. |

### `SignerBackend`

- Source: `aquilia/signing.py`
- Bases: `ABC`
- Summary: Abstract backend that produces and verifies raw byte signatures.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sign` | `def sign(self, message: bytes)` | Return the signature for *message*. |
| `verify` | `def verify(self, message: bytes, signature: bytes)` | Return ``True`` if *signature* is valid for *message*. |
| `algorithm` | `def algorithm(self)` | The algorithm name (e.g. ``"HS256"``). |

### `HmacSignerBackend`

- Source: `aquilia/signing.py`
- Bases: `SignerBackend`
- Summary: Default signing backend — HMAC with a configurable digest.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `algorithm` | `def algorithm(self)` |  |
| `sign` | `def sign(self, message: bytes)` | Return HMAC-{digest} signature of *message*. |
| `verify` | `def verify(self, message: bytes, signature: bytes)` | Return ``True`` iff *signature* equals HMAC of *message* (constant-time). |

### `AsymmetricSignerBackend`

- Source: `aquilia/signing.py`
- Bases: `SignerBackend`
- Summary: Asymmetric signing backend using the ``cryptography`` package.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `algorithm` | `def algorithm(self)` |  |
| `sign` | `def sign(self, message: bytes)` |  |
| `verify` | `def verify(self, message: bytes, signature: bytes)` |  |

### `Signer`

- Source: `aquilia/signing.py`
- Bases: `object`
- Summary: Simple HMAC-based data signer.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sign` | `def sign(self, value: str, **kwargs: Any)` | Sign *value* and return ``"<value><sep><b64sig>"``. |
| `unsign` | `def unsign(self, signed_value: str, **kwargs: Any)` | Verify and return the original value from a signed token. |
| `sign_bytes` | `def sign_bytes(self, data: bytes)` | Sign raw *data* and return ``data + sep_byte + b64sig`` as bytes. |
| `unsign_bytes` | `def unsign_bytes(self, signed_data: bytes)` | Verify and return the original bytes from signed byte data. |
| `sign_object` | `def sign_object(self, obj: Any, **kwargs: Any)` | Serialise *obj* to JSON, sign, and return a URL-safe token. |
| `unsign_object` | `def unsign_object(self, token: str, **kwargs: Any)` | Verify *token* and deserialise the embedded JSON payload. |

### `TimestampSigner`

- Source: `aquilia/signing.py`
- Bases: `Signer`
- Summary: Signer that embeds a UTC timestamp in the signed value.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `sign` | `def sign(self, value: str, *, timestamp: datetime \| None=None, **kwargs: Any)` | Sign *value* with an embedded UTC timestamp. |
| `unsign` | `def unsign(self, signed_value: str, max_age: float \| int \| timedelta \| None=None, **kwargs: Any)` | Verify signature, optionally enforce ``max_age``, and return value. |
| `unsign_with_timestamp` | `def unsign_with_timestamp(self, signed_value: str, max_age: float \| int \| timedelta \| None=None)` | Verify signature and return ``(value, timestamp)`` tuple. |
| `sign_object` | `def sign_object(self, obj: Any, *, timestamp: datetime \| None=None, **kwargs: Any)` | Sign a JSON-serialisable object with an embedded timestamp. |
| `unsign_object` | `def unsign_object(self, token: str, max_age: float \| int \| timedelta \| None=None, **kwargs: Any)` | Verify and deserialise a JSON object from a timestamped token. |

### `RotatingSigner`

- Source: `aquilia/signing.py`
- Bases: `object`
- Summary: A signer that supports transparent key rotation.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `current_signer` | `def current_signer(self)` | The active signer (used for new :meth:`sign` calls). |
| `sign` | `def sign(self, value: str, **kwargs: Any)` | Sign *value* with the current (first) secret. |
| `unsign` | `def unsign(self, signed_value: str, max_age: float \| int \| timedelta \| None=None, **kwargs: Any)` | Try each secret in order; return the value verified by the first match. |
| `sign_object` | `def sign_object(self, obj: Any, **kwargs: Any)` | Sign a JSON-serialisable object with the current secret. |
| `unsign_object` | `def unsign_object(self, token: str, max_age: float \| int \| timedelta \| None=None)` | Verify and deserialise using each secret in order. |

### `SessionSigner`

- Source: `aquilia/signing.py`
- Bases: `TimestampSigner`
- Summary: Timestamped signer for Aquilia session cookies.

### `CSRFSigner`

- Source: `aquilia/signing.py`
- Bases: `Signer`
- Summary: Signer for CSRF tokens.

### `ActivationLinkSigner`

- Source: `aquilia/signing.py`
- Bases: `TimestampSigner`
- Summary: Timestamped signer for one-time activation / password-reset URLs.

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `unsign` | `def unsign(self, signed_value: str, max_age: float \| int \| timedelta \| None=None, **kwargs: Any)` | Unsign with a default 24-hour max_age unless overridden. |

### `CacheKeySigner`

- Source: `aquilia/signing.py`
- Bases: `Signer`
- Summary: Signer for cache key integrity verification.

### `CookieSigner`

- Source: `aquilia/signing.py`
- Bases: `TimestampSigner`
- Summary: Timestamped signer for signed HTTP cookies (non-session).

### `APIKeySigner`

- Source: `aquilia/signing.py`
- Bases: `TimestampSigner`
- Summary: Timestamped signer for short-lived API access keys / signed URLs.

### `SigningConfig`

- Source: `aquilia/signing.py`
- Bases: `object`
- Summary: Runtime signing configuration.
- Decorators: `dataclass`

Fields and class attributes:

| Name | Type | Default / Value |
| --- | --- | --- |
| `secret` | `str` | `''` |
| `fallback_secrets` | `list[str]` | `field(default_factory=list)` |
| `algorithm` | `str` | `'HS256'` |
| `salt` | `str` | `'aquilia.signing'` |
| `session_salt` | `str` | `'aquilia.sessions'` |
| `csrf_salt` | `str` | `'aquilia.csrf'` |
| `activation_salt` | `str` | `'aquilia.activation'` |
| `cache_salt` | `str` | `'aquilia.cache'` |

Methods:

| Method | Signature | Summary |
| --- | --- | --- |
| `apply` | `def apply(self)` | Apply this config to the global signing registry. |
| `make_session_signer` | `def make_session_signer(self)` |  |
| `make_csrf_signer` | `def make_csrf_signer(self)` |  |
| `make_activation_signer` | `def make_activation_signer(self)` |  |
| `make_cache_signer` | `def make_cache_signer(self)` |  |
| `make_cookie_signer` | `def make_cookie_signer(self)` |  |
| `make_api_key_signer` | `def make_api_key_signer(self)` |  |
