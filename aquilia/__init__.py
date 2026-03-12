"""
Aquilia - Production-ready async Python web framework

Complete integration of:
- Aquilary: Manifest-driven app registry with dependency resolution
- Flow: Typed flow-first routing with composable pipelines
- DI: Scoped dependency injection with lifecycle management
- Sessions: Cryptographic session management with policies
- Auth: OAuth2/OIDC, MFA, RBAC/ABAC authorization
- Faults: Structured error handling with fault domains
- Middleware: Composable middleware with effect awareness
- Patterns: Auto-fix, retry, circuit breaker patterns

Everything deeply integrated for seamless developer experience.
"""

from aquilia._version import __version__  # noqa: F401 — re-exported

# Request data structures
from ._datastructures import (
    URL,
    Headers,
    MultiDict,
    ParsedContentType,
    Range,
)

# Upload handling
from ._uploads import (
    FormData,
    LocalUploadStore,
    UploadFile,
    UploadStore,
)

# ============================================================================
# Aquilary Registry (Replaces Legacy Registry)
# ============================================================================
from .aquilary import (
    AppContext,
    Aquilary,
    AquilaryRegistry,
    DependencyCycleError,
    ManifestValidationError,
    RegistryError,
    RegistryFingerprint,
    RegistryMode,
    RouteConflictError,
    RuntimeRegistry,
)

# ============================================================================
# Artifact System
# ============================================================================
from .artifacts import (
    Artifact,
    ArtifactBuilder,
    ArtifactEnvelope,
    ArtifactIntegrity,
    ArtifactKind,
    ArtifactProvenance,
    ArtifactReader,
    ArtifactStore,
    BundleArtifact,
    CodeArtifact,
    ConfigArtifact,
    DIGraphArtifact,
    FilesystemArtifactStore,
    MemoryArtifactStore,
    MigrationArtifact,
    ModelArtifact,
    RegistryArtifact,
    RouteArtifact,
    TemplateArtifact,
    register_artifact_kind,
)

# Audit Trail
from .auth.audit import (
    AuditEvent,
    AuditEventType,
    AuditSeverity,
    AuditTrail,
    MemoryAuditStore,
)
from .auth.authz import ABACEngine, AuthzEngine, RBACEngine

# Clearance System (Unique Aquilia declarative access control)
from .auth.clearance import (
    AccessLevel,
    Clearance,
    ClearanceEngine,
    ClearanceGuard,
    ClearanceVerdict,
    exempt,
    grant,
    is_owner_or_admin,
    is_same_tenant,
    is_verified,
    within_quota,
)

# ============================================================================
# Auth System (Complete Integration)
# ============================================================================
from .auth.core import (
    Identity,
    IdentityStatus,
    TokenClaims,
)

# Security Hardening
from .auth.hardening import (
    CSRFProtection,
    RequestFingerprint,
    SecurityHeaders,
    TokenBinder,
    constant_time_compare,
    generate_secure_token,
)
from .auth.hashing import PasswordHasher

# Auth Integration
from .auth.integration.aquila_sessions import (
    AuthPrincipal,
    SessionAuthBridge,
    api_session_policy,
    bind_identity,
    user_session_policy,
)
from .auth.integration.di_providers import (
    AuthConfig,
    create_auth_container,
    register_auth_providers,
)

# Flow guards -- re-enabled with FlowPipeline integration
from .auth.integration.flow_guards import (
    ControllerGuardAdapter,
    FlowGuard,
    RequireAuthGuard,
    RequirePermissionGuard,
    RequirePolicyGuard,
    RequireRolesGuard,
    RequireScopesGuard,
    require_auth,
    require_permission,
    require_roles,
    require_scopes,
)
from .auth.integration.middleware import (
    AquilAuthMiddleware,
    create_auth_middleware_stack,
)
from .auth.manager import AuthManager
from .auth.tokens import KeyRing, TokenManager

# ============================================================================
# Blueprints (Model ↔ World Contracts)
# ============================================================================
from .blueprints import (
    Blueprint,
    # Exceptions
    BlueprintFault,
    BlueprintMeta,
    BoolFacet,
    CastFault,
    ChoiceFacet,
    # Special Facets
    Computed,
    Constant,
    DateFacet,
    DateTimeFacet,
    DecimalFacet,
    DictFacet,
    DurationFacet,
    EmailFacet,
    # Facets
    Facet,
    FileFacet,
    FloatFacet,
    Hidden,
    ImprintFault,
    Inject,
    IntFacet,
    IPFacet,
    JSONFacet,
    # Lenses
    Lens,
    ListFacet,
    ProjectionFault,
    ReadOnly,
    SealFault,
    SlugFacet,
    TextFacet,
    TimeFacet,
    URLFacet,
    UUIDFacet,
    WriteOnly,
    bind_blueprint_to_request,
    generate_component_schemas,
    # Schema
    generate_schema,
    # Integration
    is_blueprint_class,
    render_blueprint_response,
)

# ============================================================================
# Cache System
# ============================================================================
from .cache import (
    # Core types
    CacheBackend,
    CacheBackendFault,
    CacheCapacityFault,
    CacheConfig,
    CacheConfigFault,
    CacheConnectionFault,
    CacheEntry,
    # Faults
    CacheFault,
    CacheHealthFault,
    # Middleware
    CacheMiddleware,
    CacheMissFault,
    CacheSerializationFault,
    # Service
    CacheService,
    CacheStampedeFault,
    CacheStats,
    CompositeBackend,
    # Key builders
    DefaultKeyBuilder,
    EvictionPolicy,
    HashKeyBuilder,
    # Serializers
    JsonCacheSerializer,
    # Backends
    MemoryBackend,
    NullBackend,
    PickleCacheSerializer,
    RedisBackend,
    cache_aside,
    # Decorators
    cached,
    get_default_cache_service,
    invalidate,
    set_default_cache_service,
)
from .config import Config, ConfigLoader
from .config_builders import Integration, Module, Workspace

# ============================================================================
# Controller System (NEW - First-class controllers)
# ============================================================================
from .controller import (
    DELETE,
    GET,
    HEAD,
    OPTIONS,
    PATCH,
    POST,
    PUT,
    TRACE,
    VALID_HTTP_METHODS,
    WS,
    BaseFilterBackend,
    ContentNegotiator,
    Controller,
    ControllerFactory,
    ControllerMetadata,
    CursorPagination,
    ExceptionFilter,
    # Filtering & Search
    FilterSet,
    HTMLRenderer,
    InstantiationMode,
    Interceptor,
    # Content Negotiation & Rendering
    JSONRenderer,
    LimitOffsetPagination,
    NoPagination,
    OpenAPIConfig,
    OpenAPIGenerator,
    OrderingFilter,
    # Pagination
    PageNumberPagination,
    ParameterMetadata,
    PlainTextRenderer,
    RequestCtx,
    RouteMetadata,
    SearchFilter,
    Throttle,
    XMLRenderer,
    YAMLRenderer,
    extract_controller_metadata,
    route,
)
from .db import (
    AquiliaDatabase,
    DatabaseError,
    configure_database,
    get_database,
    set_database,
)

# ============================================================================
# Debug Pages
# ============================================================================
from .debug import (
    DebugPageRenderer,
    render_debug_exception_page,
    render_http_error_page,
    render_welcome_page,
)
from .di import (
    Body as DIBody,
)

# ============================================================================
# Engine
# ============================================================================
# Note: RequestCtx is imported from .controller above; do not re-import
# from .engine to avoid shadowing.
# ============================================================================
# DI System (Complete)
# ============================================================================
from .di import (
    ClassProvider,
    Container,
    # Annotation-driven DI (steroids)
    Dep,
    FactoryProvider,
    Inject,
    Provider,
    ProviderMeta,
    RequestDAG,
    ValueProvider,
    factory,
    inject,
    service,
)
from .di import (
    Header as DIHeader,
)
from .di import (
    Query as DIQuery,
)
from .di import (
    Registry as DIRegistry,
)

# ============================================================================
# Discovery
# ============================================================================
from .discovery import PackageScanner

# ============================================================================
# Effects & Patterns
# ============================================================================
from .effects import (
    CacheEffect,
    CacheProvider,
    DBTx,
    DBTxProvider,
    Effect,
    EffectKind,
    EffectProvider,
    EffectRegistry,
    HTTPEffect,
    HTTPProvider,
    QueueEffect,
    QueueProvider,
    StorageEffect,
    StorageProvider,
)

# ============================================================================
# Faults System
# ============================================================================
from .faults import (
    AMDLParseFault,
    DatabaseConnectionFault,
    Fault,
    FaultContext,
    FaultEngine,
    FaultHandler,
    MigrationConflictFault,
    MigrationFault,
    # Model faults
    ModelFault,
    ModelNotFoundFault,
    ModelRegistrationFault,
    QueryFault,
    RecoveryStrategy,
    SchemaFault,
)

# ============================================================================
# Flow Pipeline System
# ============================================================================
from .flow import (
    PRIORITY_AUTH,
    PRIORITY_CLEANUP,
    # Priority constants
    PRIORITY_CRITICAL,
    PRIORITY_DEFAULT,
    PRIORITY_ENRICH,
    PRIORITY_LOG,
    PRIORITY_TRANSFORM,
    PRIORITY_VALIDATE,
    # Effect scope
    EffectScope,
    FlowContext,
    FlowError,
    # Core types
    FlowNode,
    FlowNodeType,
    FlowPipeline,
    FlowResult,
    FlowStatus,
    # Layer system (Effect-TS pattern)
    Layer,
    LayerComposition,
    from_pipeline_list,
    get_required_effects,
    guard,
    handler,
    hook,
    # Factory functions
    pipeline,
    # Decorators
    requires,
    transform,
)
from .health import HealthRegistry, HealthStatus, SubsystemStatus

# ============================================================================
# I18n (Internationalization)
# ============================================================================
from .i18n import (
    CatalogLoadFault,
    FileCatalog,
    I18nConfig,
    # Faults
    I18nFault,
    # Middleware
    I18nMiddleware,
    # Service
    I18nService,
    InvalidLocaleFault,
    # Lazy
    LazyString,
    # Locale
    Locale,
    MemoryCatalog,
    MergedCatalog,
    # Formatting
    MessageFormatter,
    MissingTranslationFault,
    NamespacedCatalog,
    # Plural
    PluralCategory,
    PluralRuleFault,
    # Catalog
    TranslationCatalog,
    create_i18n_service,
    format_currency,
    format_date,
    format_datetime,
    format_message,
    format_number,
    format_ordinal,
    format_percent,
    format_time,
    lazy_t,
    lazy_tn,
    match_locale,
    negotiate_locale,
    normalize_locale,
    parse_locale,
    select_plural,
)

# ── Typed integration configs (new API) ───────────────────────────────
from .integrations import (
    AdminAudit,
    AdminContainers,
    AdminIntegration,
    AdminModules,
    AdminMonitoring,
    AdminPods,
    AdminSecurity,
    AdminSidebar,
    AuthIntegration,
    CacheIntegration,
    ConsoleProvider,
    CorsIntegration,
    CspIntegration,
    CsrfIntegration,
    DatabaseIntegration,
    DiIntegration,
    FaultHandlingIntegration,
    FileProvider,
    I18nIntegration,
    IntegrationConfig,
    LoggingIntegration,
    MailAuth,
    MailIntegration,
    MiddlewareChain,
    MiddlewareEntry,
    MLOpsIntegration,
    OpenAPIIntegration,
    PatternsIntegration,
    RateLimitIntegration,
    RegistryIntegration,
    RenderIntegration,
    RoutingIntegration,
    SendGridProvider,
    SerializersIntegration,
    SesProvider,
    SessionIntegration,
    SmtpProvider,
    StaticFilesIntegration,
    StorageIntegration,
    TasksIntegration,
    TemplatesIntegration,
    VersioningIntegration,
)

# ============================================================================
# Lifecycle
# ============================================================================
from .lifecycle import (
    LifecycleCoordinator,
    LifecycleError,
    LifecycleManager,
    LifecyclePhase,
)

# ============================================================================
# Mail (AquilaMail)
# ============================================================================
from .mail import (
    # Message types
    EmailMessage,
    EmailMultiAlternatives,
    EnvelopeStatus,
    # Providers
    IMailProvider,
    # Config
    MailConfig,
    MailConfigFault,
    # Envelope
    MailEnvelope,
    # Faults
    MailFault,
    MailRateLimitFault,
    MailSendFault,
    MailSuppressedFault,
    MailTemplateFault,
    MailValidationFault,
    Priority,
    ProviderResult,
    ProviderResultStatus,
    TemplateMessage,
    asend_mail,
    # Convenience API
    send_mail,
)
from .mail.service import MailService

# ============================================================================
# Core Framework
# ============================================================================
from .manifest import AppManifest, BackgroundTaskConfig, ComponentKind, ComponentRef, DatabaseConfig

# ============================================================================
# Middleware System
# ============================================================================
from .middleware import (
    Handler,
    LoggingMiddleware,
    Middleware,
    MiddlewareStack,
    RequestIdMiddleware,
)
from .middleware_ext.rate_limit import (
    RateLimitMiddleware,
    RateLimitRule,
)

# Extended Middleware (Security, Rate Limiting, Static Files)
from .middleware_ext.security import (
    CORSMiddleware,
    CSPMiddleware,
    CSPPolicy,
    CSRFError,
    CSRFMiddleware,
    HSTSMiddleware,
    HTTPSRedirectMiddleware,
    ProxyFixMiddleware,
    SecurityHeadersMiddleware,
    csrf_exempt,
    csrf_token_func,
)
from .middleware_ext.static import StaticMiddleware

# ============================================================================
# Model System (Pure Python ORM)
# ============================================================================
from .models import (
    AMDLFile,
    AMDLParseError,
    ArrayField,
    AutoField,
    BigAutoField,
    BigIntegerField,
    BinaryField,
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    DurationField,
    EmailField,
    # Fields
    Field,
    FieldType,
    FieldValidationError,
    FileField,
    FilePathField,
    FloatField,
    ForeignKey,
    GeneratedField,
    GenericIPAddressField,
    HookNode,
    HStoreField,
    ImageField,
    Index,
    IntegerField,
    JSONField,
    LinkKind,
    LinkNode,
    ManyToManyField,
    MetaNode,
    MigrationOps,
    # Migrations
    MigrationRunner,
    # New pure-Python model system
    Model,
    ModelMeta,
    # Legacy AMDL (backward compat)
    ModelNode,
    ModelProxy,
    ModelRegistry,
    NoteNode,
    OneToOneField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    Q,
    SlotNode,
    SlugField,
    SmallIntegerField,
    TextField,
    TimeField,
    UniqueConstraint,
    URLField,
    UUIDField,
    generate_migration_file,
    parse_amdl,
    parse_amdl_directory,
    parse_amdl_file,
)
from .models import (
    IndexNode as LegacyIndexNode,
)

# ============================================================================
# Patterns
# ============================================================================
from .patterns import (
    CompiledPattern,
    PatternCompiler,
    PatternMatcher,
)
from .patterns import (
    TypeRegistry as PatternTypeRegistry,
)
from .request import Request
from .response import Response
from .server import AquiliaServer

# ============================================================================
# Sessions System
# ============================================================================
from .sessions import (
    CookieTransport,
    Session,
    SessionEngine,
    SessionExpiredFault,
    SessionFault,
    SessionID,
    SessionPolicy,
    SessionPrincipal,
    TransportPolicy,
)
from .sessions import (
    MemoryStore as SessionMemoryStore,
)

# Session decorators and state (NEW - Unique Aquilia syntax)
# Session guards & context managers (merged from enhanced.py into decorators)
from .sessions.decorators import (
    AdminGuard,
    AuthenticationRequiredFault,
    SessionContext,
    SessionGuard,
    SessionRequiredFault,
    VerifiedEmailGuard,
    authenticated,
    requires,
    session,
    stateful,
)
from .sessions.state import (
    CartState,
    SessionState,
    UserPreferencesState,
)
from .sessions.state import (
    Field as SessionField,
)

# ============================================================================
# Sockets (WebSockets)
# ============================================================================
from .sockets import (
    AquilaSockets,
    Event,
    OnConnect,
    OnDisconnect,
    Socket,
    SocketController,
    SocketGuard,
    SocketRouter,
)

# Storage system (production-grade, async-first)
from .storage import (
    AzureBlobConfig,
    AzureBlobStorage,
    CompositeConfig,
    CompositeStorage,
    GCSConfig,
    GCSStorage,
    LocalConfig,
    LocalStorage,
    MemoryConfig,
    MemoryStorage,
    S3Config,
    S3Storage,
    SFTPConfig,
    SFTPStorage,
    StorageBackend,
    StorageConfig,
    StorageEffectProvider,
    StorageError,
    StorageFile,
    StorageMetadata,
    StorageRegistry,
    StorageSubsystem,
)

# ============================================================================
# Tasks (Background Jobs)
# ============================================================================
from .tasks import (
    Job,
    JobResult,
    JobState,
    MemoryBackend,
    TaskBackend,
    TaskManager,
    Worker,
    task,
)
from .tasks import (
    Priority as TaskPriority,
)

# ============================================================================
# Templates
# ============================================================================
from .templates import (
    TemplateEngine,
    TemplateMiddleware,
)

# ============================================================================
# API Versioning System
# ============================================================================
from .versioning import (
    VERSION_ANY,
    VERSION_NEUTRAL,
    ApiVersion,
    ChannelResolver,
    CompositeResolver,
    # Resolvers
    HeaderResolver,
    InvalidVersionError,
    MediaTypeResolver,
    MissingVersionError,
    QueryParamResolver,
    SunsetPolicy,
    SunsetRegistry,
    UnsupportedVersionError,
    URLPathResolver,
    VersionChannel,
    VersionConfig,
    # Errors
    VersionError,
    VersionGraph,
    VersionMiddleware,
    VersionNegotiator,
    VersionStatus,
    VersionStrategy,
    VersionSunsetError,
    # Decorators
    version,
    version_neutral,
    version_range,
)

# ============================================================================
# Testing Framework
# ============================================================================

try:
    from .testing import (
        AquiliaTestCase,
        LiveServerTestCase,
        SimpleTestCase,
        TestClient,
        TestServer,
        TransactionTestCase,
        create_test_server,
        override_settings,
    )
except ImportError:
    # Testing framework is optional and requires pytest
    pass

# ============================================================================
# Signing Engine  (aquilia.signing — zero-dependency HMAC signing)
# ============================================================================

# ============================================================================
# Admin System (AquilAdmin -- auto-detecting admin)
# ============================================================================
from .admin import (
    AdminAction,
    AdminActionFault,
    AdminAuditLog,
    AdminAuthenticationFault,
    AdminAuthorizationFault,
    AdminController,
    AdminFault,
    AdminGroup,
    AdminGroupBlueprint,
    AdminLogEntry,
    AdminLogEntryBlueprint,
    AdminModelNotFoundFault,
    AdminPermission,
    AdminPermissionBlueprint,
    AdminRecordNotFoundFault,
    AdminRole,
    AdminSession,
    AdminSessionBlueprint,
    AdminSite,
    AdminUser,
    AdminUserBlueprint,
    AdminValidationFault,
    ContentType,
    ContentTypeBlueprint,
    ModelAdmin,
    autodiscover,
    register,
)
from .signing import (
    ActivationLinkSigner,
    APIKeySigner,
    BadSignature,
    CacheKeySigner,
    CookieSigner,
    CSRFSigner,
    HmacSignerBackend,
    RotatingSigner,
    # Specialised subsystem signers
    SessionSigner,
    SignatureExpired,
    SignatureMalformed,
    # Core signer classes
    Signer,
    # Backend protocol + default
    SignerBackend,
    # Configuration
    SigningConfig,
    # Exceptions
    SigningError,
    TimestampSigner,
    UnsupportedAlgorithmError,
    b64_decode,
    # Low-level primitives
    b64_encode,
    constant_time_compare,
    derive_key,
    make_signer,
    make_timestamp_signer,
)
from .signing import (
    configure as configure_signing,
)
from .signing import (
    # Structured payload helpers
    dumps as signing_dumps,
)
from .signing import (
    loads as signing_loads,
)

# ============================================================================
# Exports
# ============================================================================

__all__ = [
    # Core
    "AquiliaServer",
    "AppManifest",
    "DatabaseConfig",
    "Config",
    "ConfigLoader",
    "Request",
    "Response",
    # Signing engine
    "SigningError",
    "BadSignature",
    "SignatureExpired",
    "SignatureMalformed",
    "UnsupportedAlgorithmError",
    "Signer",
    "TimestampSigner",
    "RotatingSigner",
    "signing_dumps",
    "signing_loads",
    "SignerBackend",
    "HmacSignerBackend",
    "SessionSigner",
    "CSRFSigner",
    "ActivationLinkSigner",
    "CacheKeySigner",
    "CookieSigner",
    "APIKeySigner",
    "SigningConfig",
    "configure_signing",
    "make_signer",
    "make_timestamp_signer",
    "b64_encode",
    "b64_decode",
    "constant_time_compare",
    "derive_key",
    # Request data structures
    "MultiDict",
    "Headers",
    "URL",
    "ParsedContentType",
    "Range",
    # Upload handling
    "UploadFile",
    "FormData",
    "UploadStore",
    "LocalUploadStore",
    # Storage system
    "StorageBackend",
    "StorageFile",
    "StorageMetadata",
    "StorageRegistry",
    "StorageError",
    "StorageSubsystem",
    "StorageEffectProvider",
    "LocalStorage",
    "MemoryStorage",
    "S3Storage",
    "GCSStorage",
    "AzureBlobStorage",
    "SFTPStorage",
    "CompositeStorage",
    "StorageConfig",
    "LocalConfig",
    "MemoryConfig",
    "S3Config",
    "GCSConfig",
    "AzureBlobConfig",
    "SFTPConfig",
    "CompositeConfig",
    # Aquilary
    "Aquilary",
    "AquilaryRegistry",
    "RuntimeRegistry",
    "AppContext",
    "RegistryMode",
    # Controller (NEW - First-class)
    "Controller",
    "RequestCtx",
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "HEAD",
    "OPTIONS",
    "WS",
    "route",
    "ControllerMetadata",
    "extract_controller_metadata",
    "ControllerFactory",
    "InstantiationMode",
    # Filtering & Search
    "FilterSet",
    "SearchFilter",
    "OrderingFilter",
    "BaseFilterBackend",
    # Pagination
    "PageNumberPagination",
    "LimitOffsetPagination",
    "CursorPagination",
    "NoPagination",
    # Content Negotiation & Rendering
    "JSONRenderer",
    "XMLRenderer",
    "YAMLRenderer",
    "PlainTextRenderer",
    "HTMLRenderer",
    "ContentNegotiator",
    # API Versioning
    "ApiVersion",
    "VersionChannel",
    "VersionStatus",
    "VERSION_NEUTRAL",
    "VERSION_ANY",
    "VersionStrategy",
    "VersionConfig",
    "VersionMiddleware",
    "SunsetPolicy",
    "SunsetRegistry",
    "VersionGraph",
    "VersionNegotiator",
    "HeaderResolver",
    "URLPathResolver",
    "QueryParamResolver",
    "MediaTypeResolver",
    "CompositeResolver",
    "ChannelResolver",
    "version",
    "version_neutral",
    "version_range",
    "VersionError",
    "InvalidVersionError",
    "UnsupportedVersionError",
    "VersionSunsetError",
    "MissingVersionError",
    # DI
    "Container",
    "DIRegistry",
    "Provider",
    "ProviderMeta",
    "ClassProvider",
    "FactoryProvider",
    "ValueProvider",
    "service",
    "factory",
    "inject",
    "Inject",
    # Sessions
    "Session",
    "SessionID",
    "SessionPolicy",
    "SessionEngine",
    "SessionPrincipal",
    "SessionMemoryStore",
    "CookieTransport",
    "TransportPolicy",
    # Session decorators (NEW - Unique syntax)
    "session",
    "authenticated",
    "stateful",
    "SessionState",
    "SessionField",
    "CartState",
    "UserPreferencesState",
    # Enhanced session features (NEW - Advanced patterns)
    "SessionContext",
    "SessionGuard",
    "requires",
    "AdminGuard",
    "VerifiedEmailGuard",
    # Config builders (NEW - Python config)
    "Workspace",
    "Module",
    "Integration",
    # Typed Integration configs (modern API)
    "IntegrationConfig",
    "AuthIntegration",
    "DatabaseIntegration",
    "SessionIntegration",
    "MailIntegration",
    "MailAuth",
    "SmtpProvider",
    "SesProvider",
    "SendGridProvider",
    "ConsoleProvider",
    "FileProvider",
    "AdminIntegration",
    "AdminModules",
    "AdminAudit",
    "AdminMonitoring",
    "AdminSidebar",
    "AdminContainers",
    "AdminPods",
    "AdminSecurity",
    "MiddlewareChain",
    "MiddlewareEntry",
    "CacheIntegration",
    "TasksIntegration",
    "StorageIntegration",
    "TemplatesIntegration",
    "CorsIntegration",
    "CspIntegration",
    "RateLimitIntegration",
    "CsrfIntegration",
    "OpenAPIIntegration",
    "I18nIntegration",
    "MLOpsIntegration",
    "VersioningIntegration",
    "RenderIntegration",
    "LoggingIntegration",
    "StaticFilesIntegration",
    "DiIntegration",
    "RoutingIntegration",
    "FaultHandlingIntegration",
    "PatternsIntegration",
    "RegistryIntegration",
    "SerializersIntegration",
    # Auth - Core
    "Identity",
    "AuthManager",
    "TokenManager",
    "KeyRing",
    "PasswordHasher",
    "AuthzEngine",
    # Auth - Integration
    "AuthPrincipal",
    "SessionAuthBridge",
    "bind_identity",
    "user_session_policy",
    "api_session_policy",
    "register_auth_providers",
    "create_auth_container",
    "AuthConfig",
    "AquilAuthMiddleware",
    "create_auth_middleware_stack",
    # Auth - Flow Guards
    "FlowGuard",
    "RequireAuthGuard",
    "RequireScopesGuard",
    "RequireRolesGuard",
    "RequirePermissionGuard",
    "RequirePolicyGuard",
    "ControllerGuardAdapter",
    "require_auth",
    "require_scopes",
    "require_roles",
    "require_permission",
    # Cache
    "CacheBackend",
    "CacheEntry",
    "CacheStats",
    "CacheConfig",
    "EvictionPolicy",
    "MemoryBackend",
    "RedisBackend",
    "CompositeBackend",
    "NullBackend",
    "CacheService",
    "cached",
    "cache_aside",
    "invalidate",
    "set_default_cache_service",
    "get_default_cache_service",
    "CacheFault",
    "CacheMissFault",
    "CacheConnectionFault",
    "CacheSerializationFault",
    "CacheCapacityFault",
    "CacheBackendFault",
    "CacheConfigFault",
    "CacheStampedeFault",
    "CacheHealthFault",
    "CacheMiddleware",
    "DefaultKeyBuilder",
    "HashKeyBuilder",
    "JsonCacheSerializer",
    "PickleCacheSerializer",
    # I18n
    "Locale",
    "parse_locale",
    "normalize_locale",
    "match_locale",
    "negotiate_locale",
    "TranslationCatalog",
    "MemoryCatalog",
    "FileCatalog",
    "NamespacedCatalog",
    "MergedCatalog",
    "PluralCategory",
    "select_plural",
    "MessageFormatter",
    "format_message",
    "format_number",
    "format_currency",
    "format_date",
    "format_time",
    "format_datetime",
    "format_percent",
    "format_ordinal",
    "I18nService",
    "I18nConfig",
    "create_i18n_service",
    "LazyString",
    "lazy_t",
    "lazy_tn",
    "I18nMiddleware",
    "I18nFault",
    "MissingTranslationFault",
    "InvalidLocaleFault",
    "CatalogLoadFault",
    "PluralRuleFault",
    # Faults
    "Fault",
    "FaultContext",
    "FaultEngine",
    "FaultHandler",
    "RecoveryStrategy",
    "ModelFault",
    "AMDLParseFault",
    "ModelNotFoundFault",
    "ModelRegistrationFault",
    "MigrationFault",
    "MigrationConflictFault",
    "QueryFault",
    "DatabaseConnectionFault",
    "SchemaFault",
    # Middleware
    "Middleware",
    "Handler",
    "MiddlewareStack",
    "CORSMiddleware",
    "CSPMiddleware",
    "CSPPolicy",
    "CSRFError",
    "CSRFMiddleware",
    "HSTSMiddleware",
    "HTTPSRedirectMiddleware",
    "ProxyFixMiddleware",
    "SecurityHeadersMiddleware",
    "csrf_exempt",
    "csrf_token_func",
    "RateLimitMiddleware",
    "RateLimitRule",
    "StaticMiddleware",
    # Debug Pages
    "DebugPageRenderer",
    "render_debug_exception_page",
    "render_http_error_page",
    "render_welcome_page",
    # Effects
    "Effect",
    "EffectKind",
    "EffectProvider",
    "EffectRegistry",
    "DBTx",
    "CacheEffect",
    "QueueEffect",
    "HTTPEffect",
    "StorageEffect",
    "DBTxProvider",
    "CacheProvider",
    "QueueProvider",
    "HTTPProvider",
    "StorageProvider",
    # Flow Pipeline System
    "FlowNode",
    "FlowNodeType",
    "FlowContext",
    "FlowPipeline",
    "FlowResult",
    "FlowStatus",
    "FlowError",
    "Layer",
    "LayerComposition",
    "EffectScope",
    "requires",
    "get_required_effects",
    "pipeline",
    "guard",
    "transform",
    "handler",
    "hook",
    "from_pipeline_list",
    "PRIORITY_CRITICAL",
    "PRIORITY_AUTH",
    "PRIORITY_VALIDATE",
    "PRIORITY_TRANSFORM",
    "PRIORITY_DEFAULT",
    "PRIORITY_ENRICH",
    "PRIORITY_LOG",
    "PRIORITY_CLEANUP",
    # Sockets (WebSockets)
    "SocketController",
    "Socket",
    "OnConnect",
    "OnDisconnect",
    "Event",
    "AquilaSockets",
    "SocketRouter",
    "SocketGuard",
    # Templates
    "TemplateEngine",
    "TemplateMiddleware",
    # Mail (AquilaMail)
    "EmailMessage",
    "EmailMultiAlternatives",
    "TemplateMessage",
    "send_mail",
    "asend_mail",
    "MailEnvelope",
    "EnvelopeStatus",
    "Priority",
    "MailConfig",
    "MailService",
    "IMailProvider",
    "ProviderResult",
    "ProviderResultStatus",
    "MailFault",
    "MailSendFault",
    "MailTemplateFault",
    "MailConfigFault",
    "MailSuppressedFault",
    "MailRateLimitFault",
    "MailValidationFault",
    # Tasks (Background Jobs)
    "TaskManager",
    "TaskBackend",
    "MemoryBackend",
    "Job",
    "JobState",
    "TaskPriority",
    "JobResult",
    "Worker",
    "task",
    # Patterns
    "PatternCompiler",
    "PatternMatcher",
    "CompiledPattern",
    "PatternTypeRegistry",
    # Discovery
    "PackageScanner",
    # Blueprints (Model ↔ World Contracts)
    "Blueprint",
    "BlueprintMeta",
    "Facet",
    "TextFacet",
    "IntFacet",
    "FloatFacet",
    "DecimalFacet",
    "BoolFacet",
    "DateFacet",
    "TimeFacet",
    "DateTimeFacet",
    "DurationFacet",
    "UUIDFacet",
    "EmailFacet",
    "URLFacet",
    "SlugFacet",
    "IPFacet",
    "ListFacet",
    "DictFacet",
    "JSONFacet",
    "FileFacet",
    "ChoiceFacet",
    "Computed",
    "Constant",
    "WriteOnly",
    "ReadOnly",
    "Hidden",
    "Inject",
    "Lens",
    "BlueprintFault",
    "CastFault",
    "SealFault",
    "ImprintFault",
    "ProjectionFault",
    "generate_schema",
    "generate_component_schemas",
    "is_blueprint_class",
    "render_blueprint_response",
    "bind_blueprint_to_request",
    # Lifecycle
    "LifecycleCoordinator",
    "LifecycleManager",
    # Model System (Pure Python ORM)
    "Model",
    "ModelMeta",
    "ModelRegistry",
    "Q",
    "Field",
    "FieldValidationError",
    "Index",
    "UniqueConstraint",
    "AutoField",
    "BigAutoField",
    "IntegerField",
    "BigIntegerField",
    "SmallIntegerField",
    "PositiveIntegerField",
    "PositiveSmallIntegerField",
    "FloatField",
    "DecimalField",
    "CharField",
    "TextField",
    "SlugField",
    "EmailField",
    "URLField",
    "UUIDField",
    "FilePathField",
    "DateField",
    "TimeField",
    "DateTimeField",
    "DurationField",
    "BooleanField",
    "BinaryField",
    "JSONField",
    "ForeignKey",
    "OneToOneField",
    "ManyToManyField",
    "GenericIPAddressField",
    "FileField",
    "ImageField",
    "ArrayField",
    "HStoreField",
    "GeneratedField",
    # Legacy AMDL (backward compat)
    "ModelNode",
    "SlotNode",
    "LinkNode",
    "LegacyIndexNode",
    "HookNode",
    "MetaNode",
    "NoteNode",
    "AMDLFile",
    "FieldType",
    "LinkKind",
    "parse_amdl",
    "parse_amdl_file",
    "parse_amdl_directory",
    "AMDLParseError",
    "ModelProxy",
    # Migrations
    "MigrationRunner",
    "MigrationOps",
    "generate_migration_file",
    # Database
    "AquiliaDatabase",
    "configure_database",
    "get_database",
    "set_database",
    "DatabaseError",
    # Artifacts
    "Artifact",
    "ArtifactEnvelope",
    "ArtifactKind",
    "ArtifactProvenance",
    "ArtifactIntegrity",
    "register_artifact_kind",
    "ArtifactBuilder",
    "ArtifactStore",
    "MemoryArtifactStore",
    "FilesystemArtifactStore",
    "ArtifactReader",
    "CodeArtifact",
    "ModelArtifact",
    "ConfigArtifact",
    "TemplateArtifact",
    "MigrationArtifact",
    "RegistryArtifact",
    "RouteArtifact",
    "DIGraphArtifact",
    "BundleArtifact",
    # Testing Framework
    "TestClient",
    "TestServer",
    "AquiliaTestCase",
    "SimpleTestCase",
    "TransactionTestCase",
    "LiveServerTestCase",
    "override_settings",
    # Admin System (AquilAdmin)
    "AdminSite",
    "ModelAdmin",
    "register",
    "autodiscover",
    "AdminController",
    "AdminPermission",
    "AdminRole",
    "AdminAuditLog",
    "AdminAction",
    "AdminFault",
    "AdminAuthenticationFault",
    "AdminAuthorizationFault",
    "AdminModelNotFoundFault",
    "AdminRecordNotFoundFault",
    "AdminValidationFault",
    "AdminActionFault",
]
