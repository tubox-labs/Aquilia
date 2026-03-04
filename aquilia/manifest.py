"""
AppManifest - Production-grade, data-driven application manifest system.

No import-time side effects, fully serializable and inspectable.
Provides precise control over middleware, sessions, DI, lifecycle, and error handling.

Architecture v2:
- ComponentRef: Universal typed reference for all component kinds
- ComponentKind: Enum for component classification
- exports/imports: Cross-module provider visibility
- auto_discover: Convention-over-configuration file scanning
- guards/pipes/interceptors: First-class request pipeline components
"""

from typing import Any, Callable, Optional, Type, List, Tuple, Dict, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import timedelta
import hashlib
import json
import warnings


# ============================================================================
# Component Classification (v2)
# ============================================================================

class ComponentKind(str, Enum):
    """Classification of framework components for auto-discovery."""
    CONTROLLER = "controller"
    SERVICE = "service"
    MIDDLEWARE = "middleware"
    GUARD = "guard"
    PIPE = "pipe"
    INTERCEPTOR = "interceptor"
    EFFECT = "effect"
    MODEL = "model"
    FAULT_HANDLER = "fault_handler"
    SOCKET_CONTROLLER = "socket_controller"
    SERIALIZER = "serializer"


@dataclass
class ComponentRef:
    """
    Universal typed reference to any framework component.

    Provides a unified format for referencing controllers, services,
    middleware, guards, pipes, interceptors, and models.
    Replaces the inconsistent mix of bare strings and config dataclasses.

    Examples:
        ComponentRef("modules.users.controllers:UsersController", ComponentKind.CONTROLLER)
        ComponentRef("modules.auth.guards:JWTGuard", ComponentKind.GUARD, metadata={"priority": 10})
    """
    class_path: str              # "module.path:ClassName"
    kind: ComponentKind          # Component classification
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if ":" not in self.class_path:
            raise ValueError(
                f"ComponentRef class_path must be 'module.path:ClassName', "
                f"got '{self.class_path}'"
            )

    @property
    def module_path(self) -> str:
        """Extract the module path (before ':')."""
        return self.class_path.split(":", 1)[0]

    @property
    def class_name(self) -> str:
        """Extract the class name (after ':')."""
        return self.class_path.split(":", 1)[1]

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "class_path": self.class_path,
            "kind": self.kind.value,
            "metadata": self.metadata,
        }


class ServiceScope(str, Enum):
    """Service lifecycle scope."""
    SINGLETON = "singleton"      # App-level single instance
    APP = "app"                  # Module-level single instance
    REQUEST = "request"          # New instance per request
    TRANSIENT = "transient"      # Always new instance
    POOLED = "pooled"            # Object pool
    EPHEMERAL = "ephemeral"      # Fastest, no lifecycle


@dataclass
class LifecycleConfig:
    """Lifecycle hook configuration."""
    on_startup: Optional[str] = None      # "path.to.module:function"
    on_shutdown: Optional[str] = None     # "path.to.module:function"
    depends_on: List[str] = field(default_factory=list)  # Services to wait for
    startup_timeout: float = 30.0         # Timeout in seconds
    shutdown_timeout: float = 30.0        # Timeout in seconds
    error_strategy: str = "propagate"     # "propagate", "log", "ignore"
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "on_startup": self.on_startup,
            "on_shutdown": self.on_shutdown,
            "depends_on": self.depends_on,
            "startup_timeout": self.startup_timeout,
            "shutdown_timeout": self.shutdown_timeout,
            "error_strategy": self.error_strategy,
        }


@dataclass
class ServiceConfig:
    """Service registration configuration with complete DI support."""
    class_path: str                       # "path.to.module:ClassName"
    scope: ServiceScope = ServiceScope.APP  # Lifecycle scope
    
    # Auto-discovery
    auto_discover: bool = True            # Auto-wire dependencies
    
    # Lifecycle management
    lifecycle: Optional[LifecycleConfig] = None
    
    # Feature flags
    feature_flags: List[str] = field(default_factory=list)  # Conditional registration
    
    # DI alternatives
    aliases: List[str] = field(default_factory=list)  # Alternative injection names
    
    # Factory pattern
    factory: Optional[str] = None         # "path.to.module:factory_function"
    factory_args: Optional[Dict[str, Any]] = None  # Factory arguments
    
    # Configuration
    config: Optional[Dict[str, Any]] = None  # Constructor kwargs
    
    # Observability
    observable: bool = True               # Include in metrics/tracing
    required: bool = True                 # Fail if can't register
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "class_path": self.class_path,
            "scope": getattr(self.scope, "value", str(self.scope)),
            "auto_discover": self.auto_discover,
            "aliases": self.aliases,
            "factory": self.factory,
            "config": self.config or {},
        }


@dataclass
class MiddlewareConfig:
    """Middleware registration configuration."""
    class_path: str                       # "path.to.module:ClassName"
    scope: str = "global"                 # "global", "app", "route"
    scope_target: Optional[str] = None    # For app:name or route:/pattern
    priority: int = 50                    # Lower = earlier execution
    
    # Conditional execution
    condition: Optional[Callable] = None  # Optional function returning bool
    
    # Configuration
    config: Optional[Dict[str, Any]] = None  # Constructor kwargs
    
    # Error handling
    on_error: str = "propagate"          # "propagate", "skip", "fallback"
    fallback: Optional[str] = None        # Fallback middleware path
    
    # Observability
    observable: bool = True               # Include in metrics
    log_requests: bool = False            # Log individual requests
    log_responses: bool = False           # Log individual responses
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "class_path": self.class_path,
            "scope": self.scope,
            "priority": self.priority,
            "config": self.config or {},
        }


@dataclass
class SessionConfig:
    """Session management configuration."""
    name: str                             # Session policy name
    enabled: bool = True                  # Enable/disable
    ttl: timedelta = field(default_factory=lambda: timedelta(days=7))  # Time to live
    idle_timeout: Optional[timedelta] = None  # Inactivity timeout
    renewal: Optional[timedelta] = None   # Renewal window
    
    # Transport layer
    transport: str = "cookie"             # "cookie", "header", "custom"
    transport_config: Optional[Dict[str, Any]] = None  # Transport-specific config
    
    # Cookie-specific settings (for transport="cookie")
    cookie_name: str = "session_id"
    cookie_domain: Optional[str] = None
    cookie_path: str = "/"
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: str = "Strict"       # "Strict", "Lax", "None"
    
    # Storage
    store: str = "memory"                 # "memory", "redis", "database", "custom"
    store_config: Optional[Dict[str, Any]] = None  # Store-specific config
    
    # Encryption
    encryption_enabled: bool = True
    encryption_key_env: str = "SESSION_ENCRYPTION_KEY"
    
    # Serialization
    serializer: str = "json"              # "json", "pickle", "msgpack"
    
    # Observability
    log_lifecycle: bool = False           # Log session create/destroy
    metrics_enabled: bool = True          # Collect metrics
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "ttl": str(self.ttl),
            "transport": self.transport,
            "store": self.store,
            "cookie_secure": self.cookie_secure,
            "cookie_httponly": self.cookie_httponly,
            "cookie_samesite": self.cookie_samesite,
        }


@dataclass
class FaultHandlerConfig:
    """Fault handler configuration."""
    domain: str                           # Fault domain (e.g., "AUTH", "VALIDATION")
    handler_path: str                     # "path.to.module:handler_function"
    recovery_strategy: str = "propagate"  # "propagate", "recover", "fallback"
    fallback_response: Optional[Dict[str, Any]] = None  # Fallback response


@dataclass
class FaultHandlingConfig:
    """Fault/error handling configuration."""
    default_domain: str = "APP"           # Default fault domain
    strategy: str = "propagate"           # "propagate", "recover", "fallback"
    handlers: List[FaultHandlerConfig] = field(default_factory=list)  # Domain handlers
    middlewares: List[MiddlewareConfig] = field(default_factory=list)  # Error middlewares
    metrics_enabled: bool = True          # Collect error metrics
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "default_domain": self.default_domain,
            "strategy": self.strategy,
            "handlers": [h.__dict__ for h in self.handlers],
            "metrics_enabled": self.metrics_enabled,
        }


@dataclass
class FeatureConfig:
    """Feature flag configuration."""
    name: str                             # Feature identifier
    enabled: bool = False                 # Default state
    conditions: Optional[Dict[str, Any]] = None  # Conditional rules
    services: List[str] = field(default_factory=list)  # Services to register
    controllers: List[str] = field(default_factory=list)  # Controllers to register
    middleware: List[MiddlewareConfig] = field(default_factory=list)  # Middleware
    routes: List[str] = field(default_factory=list)  # Routes to register
    
    # Observability
    log_usage: bool = True                # Log feature usage
    metrics_enabled: bool = True          # Collect metrics
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "conditions": self.conditions or {},
        }


@dataclass
class TemplateConfig:
    """Template engine configuration."""
    enabled: bool = True
    search_paths: List[str] = field(default_factory=list)
    precompile: bool = False
    cache: str = "memory"  # "memory", "crous", "none"
    sandbox: bool = True
    context_processors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "enabled": self.enabled,
            "search_paths": self.search_paths,
            "precompile": self.precompile,
            "cache": self.cache,
        }


@dataclass
class DatabaseConfig:
    """
    Database configuration for AMDL model system.
    
    Controls database connection, auto-creation, migration behaviour,
    and discovery of .amdl model files.
    """
    url: str = "sqlite:///db.sqlite3"     # Database URL
    auto_connect: bool = True             # Connect on startup
    auto_create: bool = True              # Create tables on startup
    auto_migrate: bool = False            # Run pending migrations on startup
    migrations_dir: str = "migrations"    # Migration files directory
    pool_size: int = 5                    # Connection pool size (future)
    echo: bool = False                    # Log SQL statements
    
    # Model discovery
    model_paths: List[str] = field(default_factory=list)  # Explicit .amdl paths
    scan_dirs: List[str] = field(default_factory=lambda: ["models"])  # Directories to scan
    
    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "url": self.url,
            "auto_connect": self.auto_connect,
            "auto_create": self.auto_create,
            "auto_migrate": self.auto_migrate,
            "migrations_dir": self.migrations_dir,
            "pool_size": self.pool_size,
            "echo": self.echo,
            "model_paths": self.model_paths,
            "scan_dirs": self.scan_dirs,
        }


@dataclass
class AppManifest:
    """
    Production-grade application manifest for complete app configuration.
    
    Architecture v2 additions:
    - exports/imports: Cross-module provider visibility
    - guards/pipes/interceptors: First-class request pipeline components
    - auto_discover: Convention-over-configuration file scanning
    - All component lists accept Union[str, ComponentRef] for flexibility
    
    Provides precise control over:
    - Services with DI scopes and lifecycle
    - Controllers with routing
    - Middleware with scoping and priority
    - Guards for authentication/authorization gates
    - Pipes for request data transformation/validation
    - Interceptors for cross-cutting concerns (logging, caching, etc.)
    - Sessions with policies and storage
    - Error handling with fault domains
    - Feature flags with conditional activation
    """
    
    # Identity
    name: str                             # Module name
    version: str                          # Semantic version
    description: str = ""                 # Module description
    author: str = ""                      # Module author
    
    # Component declarations -- all accept str or ComponentRef
    services: List[Union[str, ServiceConfig, ComponentRef]] = field(default_factory=list)
    controllers: List[Union[str, ComponentRef]] = field(default_factory=list)
    socket_controllers: List[Union[str, ComponentRef]] = field(default_factory=list)
    models: List[Union[str, ComponentRef]] = field(default_factory=list)
    serializers: List[Union[str, ComponentRef]] = field(default_factory=list)
    
    # v2: First-class request pipeline components
    guards: List[Union[str, ComponentRef]] = field(default_factory=list)
    pipes: List[Union[str, ComponentRef]] = field(default_factory=list)
    interceptors: List[Union[str, ComponentRef]] = field(default_factory=list)
    
    # Middleware configuration
    middleware: List[Union[str, MiddlewareConfig, ComponentRef]] = field(default_factory=list)
    
    # Routing
    route_prefix: str = "/"               # Route prefix for module
    base_path: Optional[str] = None       # Optional base path override
    
    # Lifecycle management
    lifecycle: Optional[LifecycleConfig] = None
    
    # Session management
    sessions: List[SessionConfig] = field(default_factory=list)
    
    # Template management
    templates: Optional[TemplateConfig] = None
    
    # Database and models
    database: Optional[DatabaseConfig] = None
    
    # Error handling
    faults: Optional[FaultHandlingConfig] = None
    
    # Feature flags
    features: List[FeatureConfig] = field(default_factory=list)
    
    # v2: Cross-module dependency management
    exports: List[str] = field(default_factory=list)       # Services visible to importing modules
    imports: List[str] = field(default_factory=list)        # Modules this module depends on
    
    # Legacy: still works but prefer 'imports'
    depends_on: List[str] = field(default_factory=list)
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    config_schema: Optional[Dict[str, Any]] = None  # JSON Schema for validation
    
    # v2: Auto-discovery control
    auto_discover: bool = True            # Enable convention-based component scanning
    discover_patterns: List[str] = field(default_factory=lambda: [
        "controllers", "services", "middleware", "guards", "models"
    ])
    
    # Legacy support (for backward compatibility -- will emit warnings)
    middlewares: List[Tuple[str, dict]] = field(default_factory=list)  # Old format
    default_fault_domain: Optional[str] = None  # Old format
    on_startup: Optional[Callable] = None  # Old format
    on_shutdown: Optional[Callable] = None  # Old format
    config: Optional[Type] = None  # Old format
    
    def __post_init__(self):
        """Validate and normalize manifest structure."""
        if not self.name:
            raise ValueError("Manifest must have a name")
        if not self.version:
            raise ValueError("Manifest must have a version")
        
        # Validate name format (alphanumeric + underscore)
        if not self.name.replace("_", "").isalnum():
            raise ValueError(f"Invalid app name '{self.name}': must be alphanumeric with underscores")
        
        # Convert legacy middleware format to new format if needed
        if self.middlewares and not self.middleware:
            warnings.warn(
                f"AppManifest({self.name!r}).middlewares is deprecated. "
                "Use 'middleware' with MiddlewareConfig objects instead.",
                DeprecationWarning, stacklevel=2,
            )
            for path, kwargs in self.middlewares:
                self.middleware.append(
                    MiddlewareConfig(
                        class_path=path,
                        config=kwargs or {}
                    )
                )
        
        # Convert legacy fault domain to new format if needed
        if self.default_fault_domain and not self.faults:
            warnings.warn(
                f"AppManifest({self.name!r}).default_fault_domain is deprecated. "
                "Use 'faults=FaultHandlingConfig(default_domain=...)' instead.",
                DeprecationWarning, stacklevel=2,
            )
            self.faults = FaultHandlingConfig(
                default_domain=self.default_fault_domain
            )
        
        # v2: Migrate depends_on → imports (with warning)
        if self.depends_on and not self.imports:
            warnings.warn(
                f"AppManifest({self.name!r}).depends_on is deprecated. "
                "Use 'imports' instead for cross-module dependencies.",
                DeprecationWarning, stacklevel=2,
            )
            self.imports = list(self.depends_on)
        
        # v2: Normalize string services to ServiceConfig
        normalized_services = []
        for s in self.services:
            if isinstance(s, str):
                normalized_services.append(ServiceConfig(class_path=s))
            elif isinstance(s, ComponentRef):
                normalized_services.append(ServiceConfig(
                    class_path=s.class_path,
                    config=s.metadata.get("config"),
                ))
            else:
                normalized_services.append(s)
        self.services = normalized_services
        
        # v2: Normalize string middleware to MiddlewareConfig
        normalized_mw = []
        for m in self.middleware:
            if isinstance(m, str):
                normalized_mw.append(MiddlewareConfig(class_path=m))
            elif isinstance(m, ComponentRef):
                normalized_mw.append(MiddlewareConfig(
                    class_path=m.class_path,
                    priority=m.metadata.get("priority", 50),
                    config=m.metadata.get("config"),
                ))
            else:
                normalized_mw.append(m)
        self.middleware = normalized_mw
    
    def to_dict(self) -> dict:
        """Serialize manifest to dictionary (for fingerprinting and inspection)."""
        
        def _ref_to_str(ref) -> str:
            """Convert any component reference to its class_path string."""
            if isinstance(ref, str):
                return ref
            if isinstance(ref, ComponentRef):
                return ref.class_path
            if hasattr(ref, "class_path"):
                return ref.class_path
            return str(ref)
        
        result = {
            "name": self.name,
            "version": self.version,
            "controllers": [_ref_to_str(c) for c in self.controllers],
            "socket_controllers": [_ref_to_str(c) for c in self.socket_controllers],
            "models": [_ref_to_str(m) for m in self.models],
            "serializers": [_ref_to_str(s) for s in self.serializers],
            "services": [s.to_dict() if hasattr(s, 'to_dict') else str(s) for s in self.services],
            "middleware": [m.to_dict() if hasattr(m, 'to_dict') else str(m) for m in self.middleware],
            "guards": [_ref_to_str(g) for g in self.guards],
            "pipes": [_ref_to_str(p) for p in self.pipes],
            "interceptors": [_ref_to_str(i) for i in self.interceptors],
            "exports": self.exports,
            "imports": self.imports,
            "depends_on": self.depends_on,
            "description": self.description,
            "author": self.author,
            "tags": self.tags,
            "auto_discover": self.auto_discover,
        }
        if self.database:
            result["database"] = self.database.to_dict()
        if self.faults:
            result["faults"] = self.faults.to_dict()
        if self.lifecycle:
            result["lifecycle"] = self.lifecycle.to_dict()
        return result
    
    def fingerprint(self) -> str:
        """Generate stable hash of manifest for reproducible deploys."""
        data = json.dumps(self.to_dict(), sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()[:16]


# Legacy ManifestLoader removed -- use aquilia.aquilary.ManifestLoader instead.
# The aquilary pipeline (loader → validator → graph → fingerprint → registry)
# is the canonical manifest processing system.
