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

__version__ = "1.0.1"

# ============================================================================
# Core Framework
# ============================================================================

from .manifest import AppManifest, DatabaseConfig, ComponentRef, ComponentKind, BackgroundTaskConfig
from .config import Config, ConfigLoader
from .config_builders import Workspace, Module, Integration
from .request import Request
from .response import Response
from .server import AquiliaServer
from .health import HealthRegistry, HealthStatus, SubsystemStatus

# Request data structures
from ._datastructures import (
    MultiDict,
    Headers,
    URL,
    ParsedContentType,
    Range,
)

# Upload handling
from ._uploads import (
    UploadFile,
    FormData,
    UploadStore,
    LocalUploadStore,
)

# Storage system (production-grade, async-first)
from .storage import (
    StorageBackend,
    StorageFile,
    StorageMetadata,
    StorageRegistry,
    StorageError,
    StorageSubsystem,
    StorageEffectProvider,
    LocalStorage,
    MemoryStorage,
    S3Storage,
    GCSStorage,
    AzureBlobStorage,
    SFTPStorage,
    CompositeStorage,
    StorageConfig,
    LocalConfig,
    MemoryConfig,
    S3Config,
    GCSConfig,
    AzureBlobConfig,
    SFTPConfig,
    CompositeConfig,
)

# ============================================================================
# Aquilary Registry (Replaces Legacy Registry)
# ============================================================================

from .aquilary import (
    Aquilary,
    AquilaryRegistry,
    RuntimeRegistry,
    AppContext,
    RegistryMode,
    RegistryFingerprint,
    RegistryError,
    DependencyCycleError,
    RouteConflictError,
    ManifestValidationError,
)

# ============================================================================
# Controller System (NEW - First-class controllers)
# ============================================================================

from .controller import (
    Controller,
    RequestCtx,
    ExceptionFilter,
    Interceptor,
    Throttle,
    GET, POST, PUT, PATCH, DELETE,
    HEAD, OPTIONS, TRACE, WS,
    route,
    VALID_HTTP_METHODS,
    ControllerMetadata,
    RouteMetadata,
    ParameterMetadata,
    extract_controller_metadata,
    ControllerFactory,
    InstantiationMode,
    OpenAPIGenerator,
    OpenAPIConfig,
    # Filtering & Search
    FilterSet,
    SearchFilter,
    OrderingFilter,
    BaseFilterBackend,
    # Pagination
    PageNumberPagination,
    LimitOffsetPagination,
    CursorPagination,
    NoPagination,
    # Content Negotiation & Rendering
    JSONRenderer,
    XMLRenderer,
    YAMLRenderer,
    PlainTextRenderer,
    HTMLRenderer,
    ContentNegotiator,
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
    Container,
    Registry as DIRegistry,
    Provider,
    ProviderMeta,
    ClassProvider,
    FactoryProvider,
    ValueProvider,
    service,
    factory,
    inject,
    Inject,
    # Annotation-driven DI (steroids)
    Dep,
    Header as DIHeader,
    Query as DIQuery,
    Body as DIBody,
    RequestDAG,
)

# ============================================================================
# Sessions System
# ============================================================================

from .sessions import (
    Session,
    SessionID,
    SessionPolicy,
    SessionEngine,
    SessionPrincipal,
    MemoryStore as SessionMemoryStore,
    CookieTransport,
    TransportPolicy,
    SessionFault,
    SessionExpiredFault,
)

# Session decorators and state (NEW - Unique Aquilia syntax)
from .sessions.decorators import (
    session,
    authenticated,
    stateful,
    SessionRequiredFault,
    AuthenticationRequiredFault,
)

from .sessions.state import (
    SessionState,
    Field as SessionField,
    CartState,
    UserPreferencesState,
)

# Session guards & context managers (merged from enhanced.py into decorators)
from .sessions.decorators import (
    SessionContext,
    SessionGuard,
    requires,
    AdminGuard,
    VerifiedEmailGuard,
)

# ============================================================================
# Auth System (Complete Integration)
# ============================================================================

from .auth.core import (
    Identity,
    IdentityStatus,
    TokenClaims,
)

from .auth.manager import AuthManager
from .auth.tokens import TokenManager, KeyRing
from .auth.hashing import PasswordHasher
from .auth.authz import AuthzEngine, RBACEngine, ABACEngine

# Auth Integration
from .auth.integration.aquila_sessions import (
    AuthPrincipal,
    SessionAuthBridge,
    bind_identity,
    user_session_policy,
    api_session_policy,
)

from .auth.integration.di_providers import (
    register_auth_providers,
    create_auth_container,
    AuthConfig,
)

from .auth.integration.middleware import (
    AquilAuthMiddleware,
    create_auth_middleware_stack,
)

# Flow guards -- re-enabled with FlowPipeline integration
from .auth.integration.flow_guards import (
    FlowGuard,
    RequireAuthGuard,
    RequireScopesGuard,
    RequireRolesGuard,
    RequirePermissionGuard,
    RequirePolicyGuard,
    ControllerGuardAdapter,
    require_auth,
    require_scopes,
    require_roles,
    require_permission,
)

# Clearance System (Unique Aquilia declarative access control)
from .auth.clearance import (
    AccessLevel,
    Clearance,
    ClearanceVerdict,
    ClearanceEngine,
    ClearanceGuard,
    grant,
    exempt,
    is_verified,
    is_owner_or_admin,
    within_quota,
    is_same_tenant,
)

# Audit Trail
from .auth.audit import (
    AuditEventType,
    AuditSeverity,
    AuditEvent,
    AuditTrail,
    MemoryAuditStore,
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

# ============================================================================
# Cache System
# ============================================================================

from .cache import (
    # Core types
    CacheBackend,
    CacheEntry,
    CacheStats,
    CacheConfig,
    EvictionPolicy,
    # Backends
    MemoryBackend,
    RedisBackend,
    CompositeBackend,
    NullBackend,
    # Service
    CacheService,
    # Decorators
    cached,
    cache_aside,
    invalidate,
    set_default_cache_service,
    get_default_cache_service,
    # Faults
    CacheFault,
    CacheMissFault,
    CacheConnectionFault,
    CacheSerializationFault,
    CacheCapacityFault,
    CacheBackendFault,
    CacheConfigFault,
    CacheStampedeFault,
    CacheHealthFault,
    # Middleware
    CacheMiddleware,
    # Key builders
    DefaultKeyBuilder,
    HashKeyBuilder,
    # Serializers
    JsonCacheSerializer,
    PickleCacheSerializer,
)

# ============================================================================
# I18n (Internationalization)
# ============================================================================

from .i18n import (
    # Locale
    Locale,
    parse_locale,
    normalize_locale,
    match_locale,
    negotiate_locale,
    # Catalog
    TranslationCatalog,
    MemoryCatalog,
    FileCatalog,
    NamespacedCatalog,
    MergedCatalog,
    # Plural
    PluralCategory,
    select_plural,
    # Formatting
    MessageFormatter,
    format_message,
    format_number,
    format_currency,
    format_date,
    format_time,
    format_datetime,
    format_percent,
    format_ordinal,
    # Service
    I18nService,
    I18nConfig,
    create_i18n_service,
    # Lazy
    LazyString,
    lazy_t,
    lazy_tn,
    # Middleware
    I18nMiddleware,
    # Faults
    I18nFault,
    MissingTranslationFault,
    InvalidLocaleFault,
    CatalogLoadFault,
    PluralRuleFault,
)

# ============================================================================
# Faults System
# ============================================================================

from .faults import (
    Fault,
    FaultContext,
    FaultEngine,
    FaultHandler,
    RecoveryStrategy,
    # Model faults
    ModelFault,
    AMDLParseFault,
    ModelNotFoundFault,
    ModelRegistrationFault,
    MigrationFault,
    MigrationConflictFault,
    QueryFault,
    DatabaseConnectionFault,
    SchemaFault,
)

# ============================================================================
# Middleware System
# ============================================================================

from .middleware import (
    Middleware,
    Handler,
    MiddlewareStack,
    RequestIdMiddleware,
    LoggingMiddleware,
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
from .middleware_ext.rate_limit import (
    RateLimitMiddleware,
    RateLimitRule,
)
from .middleware_ext.static import StaticMiddleware

# ============================================================================
# Debug Pages
# ============================================================================

from .debug import (
    DebugPageRenderer,
    render_debug_exception_page,
    render_http_error_page,
    render_welcome_page,
)

# ============================================================================
# Effects & Patterns
# ============================================================================

from .effects import (
    Effect,
    EffectKind,
    EffectProvider,
    EffectRegistry,
    DBTx,
    CacheEffect,
    QueueEffect,
    HTTPEffect,
    StorageEffect,
    DBTxProvider,
    CacheProvider,
    QueueProvider,
    HTTPProvider,
    StorageProvider,
)

# ============================================================================
# Flow Pipeline System
# ============================================================================

from .flow import (
    # Core types
    FlowNode,
    FlowNodeType,
    FlowContext,
    FlowPipeline,
    FlowResult,
    FlowStatus,
    FlowError,
    # Layer system (Effect-TS pattern)
    Layer,
    LayerComposition,
    # Effect scope
    EffectScope,
    # Decorators
    requires,
    get_required_effects,
    # Factory functions
    pipeline,
    guard,
    transform,
    handler,
    hook,
    from_pipeline_list,
    # Priority constants
    PRIORITY_CRITICAL,
    PRIORITY_AUTH,
    PRIORITY_VALIDATE,
    PRIORITY_TRANSFORM,
    PRIORITY_DEFAULT,
    PRIORITY_ENRICH,
    PRIORITY_LOG,
    PRIORITY_CLEANUP,
)

# ============================================================================
# Sockets (WebSockets)
# ============================================================================

from .sockets import (
    SocketController,
    Socket,
    OnConnect,
    OnDisconnect,
    Event,
    AquilaSockets,
    SocketRouter,
    SocketGuard,
)

# ============================================================================
# Templates
# ============================================================================

from .templates import (
    TemplateEngine,
    TemplateMiddleware,
)

# ============================================================================
# Mail (AquilaMail)
# ============================================================================

from .mail import (
    # Message types
    EmailMessage,
    EmailMultiAlternatives,
    TemplateMessage,
    # Convenience API
    send_mail,
    asend_mail,
    # Envelope
    MailEnvelope,
    EnvelopeStatus,
    Priority,
    # Config
    MailConfig,
    # Providers
    IMailProvider,
    ProviderResult,
    ProviderResultStatus,
    # Faults
    MailFault,
    MailSendFault,
    MailTemplateFault,
    MailConfigFault,
    MailSuppressedFault,
    MailRateLimitFault,
    MailValidationFault,
)

from .mail.service import MailService

# ============================================================================
# Tasks (Background Jobs)
# ============================================================================

from .tasks import (
    TaskManager,
    TaskBackend,
    MemoryBackend,
    Job,
    JobState,
    Priority as TaskPriority,
    JobResult,
    Worker,
    task,
)

# ============================================================================
# Patterns
# ============================================================================

from .patterns import (
    PatternCompiler,
    PatternMatcher,
    CompiledPattern,
    TypeRegistry as PatternTypeRegistry,
)

# ============================================================================
# Discovery
# ============================================================================

from .discovery import PackageScanner

# ============================================================================
# Blueprints (Model ↔ World Contracts)
# ============================================================================

from .blueprints import (
    Blueprint,
    BlueprintMeta,
    # Facets
    Facet,
    TextFacet,
    IntFacet,
    FloatFacet,
    DecimalFacet,
    BoolFacet,
    DateFacet,
    TimeFacet,
    DateTimeFacet,
    DurationFacet,
    UUIDFacet,
    EmailFacet,
    URLFacet,
    SlugFacet,
    IPFacet,
    ListFacet,
    DictFacet,
    JSONFacet,
    FileFacet,
    ChoiceFacet,
    # Special Facets
    Computed,
    Constant,
    WriteOnly,
    ReadOnly,
    Hidden,
    Inject,
    # Lenses
    Lens,
    # Exceptions
    BlueprintFault,
    CastFault,
    SealFault,
    ImprintFault,
    ProjectionFault,
    # Schema
    generate_schema,
    generate_component_schemas,
    # Integration
    is_blueprint_class,
    render_blueprint_response,
    bind_blueprint_to_request,
)



# ============================================================================
# Lifecycle
# ============================================================================

from .lifecycle import (
    LifecycleCoordinator,
    LifecycleManager,
    LifecyclePhase,
    LifecycleError,
)

# ============================================================================
# Model System (Pure Python ORM)
# ============================================================================

from .models import (
    # New pure-Python model system
    Model,
    ModelMeta,
    ModelRegistry,
    Q,
    # Fields
    Field,
    FieldValidationError,
    Index,
    UniqueConstraint,
    AutoField,
    BigAutoField,
    IntegerField,
    BigIntegerField,
    SmallIntegerField,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    FloatField,
    DecimalField,
    CharField,
    TextField,
    SlugField,
    EmailField,
    URLField,
    UUIDField,
    FilePathField,
    DateField,
    TimeField,
    DateTimeField,
    DurationField,
    BooleanField,
    BinaryField,
    JSONField,
    ForeignKey,
    OneToOneField,
    ManyToManyField,
    GenericIPAddressField,
    FileField,
    ImageField,
    ArrayField,
    HStoreField,
    GeneratedField,
    # Legacy AMDL (backward compat)
    ModelNode,
    SlotNode,
    LinkNode,
    IndexNode as LegacyIndexNode,
    HookNode,
    MetaNode,
    NoteNode,
    AMDLFile,
    FieldType,
    LinkKind,
    parse_amdl,
    parse_amdl_file,
    parse_amdl_directory,
    AMDLParseError,
    ModelProxy,
    # Migrations
    MigrationRunner,
    MigrationOps,
    generate_migration_file,
)

from .db import (
    AquiliaDatabase,
    configure_database,
    get_database,
    set_database,
    DatabaseError,
)

# ============================================================================
# Artifact System
# ============================================================================

from .artifacts import (
    Artifact,
    ArtifactEnvelope,
    ArtifactKind,
    ArtifactProvenance,
    ArtifactIntegrity,
    register_artifact_kind,
    ArtifactBuilder,
    ArtifactStore,
    MemoryArtifactStore,
    FilesystemArtifactStore,
    ArtifactReader,
    CodeArtifact,
    ModelArtifact,
    ConfigArtifact,
    TemplateArtifact,
    MigrationArtifact,
    RegistryArtifact,
    RouteArtifact,
    DIGraphArtifact,
    BundleArtifact,
)

# ============================================================================
# Testing Framework
# ============================================================================

try:
    from .testing import (
        TestClient,
        TestServer,
        create_test_server,
        override_settings,
        AquiliaTestCase,
        SimpleTestCase,
        TransactionTestCase,
        LiveServerTestCase,
    )
except ImportError:
    # Testing framework is optional and requires pytest
    pass

# ============================================================================
# Admin System (AquilAdmin -- auto-detecting admin)
# ============================================================================

from .admin import (
    AdminSite,
    ModelAdmin,
    register,
    autodiscover,
    AdminController,
    AdminPermission,
    AdminRole,
    AdminAuditLog,
    AdminAction,
    AdminUser,
    AdminGroup,
    ContentType,
    AdminLogEntry,
    AdminSession,
    AdminUserBlueprint,
    AdminGroupBlueprint,
    AdminPermissionBlueprint,
    ContentTypeBlueprint,
    AdminLogEntryBlueprint,
    AdminSessionBlueprint,
    AdminFault,
    AdminAuthenticationFault,
    AdminAuthorizationFault,
    AdminModelNotFoundFault,
    AdminRecordNotFoundFault,
    AdminValidationFault,
    AdminActionFault,
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
    "GET", "POST", "PUT", "PATCH", "DELETE",
    "HEAD", "OPTIONS", "WS",
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
