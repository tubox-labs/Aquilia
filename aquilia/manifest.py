"""
AppManifest - Production-grade, data-driven application manifest system for Aquilia.

This module provides the declarative metadata system used to describe the internal
capabilities, dependencies, and structure of individual application modules. By keeping
configuration declarative and decoupled from import-time execution, Aquilia prevents
circular dependency side effects during bootstrapping.

Architecture (Manifest-First Design)
------------------------------------
In Aquilia, application structure is split into two primary layers:
1. **Global Orchestration (workspace.py)**: Configures global network settings, databases,
   third-party integrations, and maps directory-level module pointers.
2. **Module internals (manifest.py)**: Each module provides an `AppManifest` acting as the
   definitive catalog of its controllers, services, middleware, models, database models,
   realtime socket controllers, and lifecycle hooks.

Registration & Discovery Flow
-----------------------------
During application initialization, the framework's scanner scans active modules:
- **Convention-based Auto-discovery**: When `auto_discover=True` (default), the framework
  scans convention directories (such as `/controllers`, `/services`, `/models`, etc.) matching
  defined patterns and registers components automatically.
- **Explicit Component Reference**: Components can also be explicitly declared using standard
  import path strings (e.g. `"modules.users.services:UsersService"`) or `ComponentRef` instances
  which offer metadata-based configuration.

Resolution & DI Visibility Flow
------------------------------
Cross-module dependency visibility is governed by module boundaries:
- **Imports**: Declares other modules that this module depends on.
- **Exports**: Controls visibility of internal dependency injection (DI) service providers
  to the rest of the application. Services not listed under `exports` remain private to
  the module.

Common Usage Patterns
---------------------
Declaring a basic module with convention-based discovery:

```python
from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="billing",
    version="1.2.0",
    description="Manages subscriptions and invoices",
    imports=["auth", "users"],
    auto_discover=True,
)
```

Advanced Usage Patterns
-----------------------
Declaring a complex module with custom DI service registration, priority middleware, and guards:

```python
from aquilia.manifest import AppManifest, ServiceConfig, MiddlewareConfig

manifest = AppManifest(
    name="billing",
    version="1.2.0",
    services=[
        ServiceConfig(
            class_path="modules.billing.services:PaymentService",
            scope="request",
            tag="stripe",
            config={"api_key_env": "STRIPE_API_KEY"},
        )
    ],
    middleware=[
        MiddlewareConfig(
            class_path="modules.billing.middleware:RateLimitMiddleware",
            priority=10,
            config={"limit": 60},
        )
    ],
    guards=[
        "modules.billing.guards:StripeSignatureGuard",
    ],
    exports=["modules.billing.services:PaymentService"],
)
```
"""

import hashlib
import json
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import timedelta
from enum import Enum
from typing import Any, Literal, cast

from .typing.manifest import ManifestMetadata

# ============================================================================
# Component Classification (v2)
# ============================================================================


class ComponentKind(str, Enum):
    """
    Classification of framework components for auto-discovery and registration.

    This enum defines all first-class component kinds supported by the Aquilia framework.
    It is used by `ComponentRef` and convention-based discovery to classify components and
    wire them correctly into the dependency injection container, routing engine, or middleware chain.

    Attributes:
        CONTROLLER: HTTP API controller managing route handlers.
        SERVICE: Dependency injection service containing business logic.
        MIDDLEWARE: ASGI or HTTP middleware in the request/response chain.
        GUARD: Security/authorization check executing before controllers.
        PIPE: Data transformation or validation layer for request payloads.
        INTERCEPTOR: Aspect-oriented hook wrapping controller execution.
        EFFECT: Contextual side-effect provider.
        MODEL: Database schema model class.
        FAULT_HANDLER: Exception translator for specific fault domains.
        SOCKET_CONTROLLER: Realtime WebSocket message controller.
        SERIALIZER: Data serialization/deserialization schema.
        TASK: Asynchronous background worker task.
        EVENT_HANDLER: Event listener in the pub/sub subsystem.
        INTEGRATION: Third-party service integration config.
        COMMAND: CLI command registered in the admin interface.
        VALIDATOR: Request parameter validator.
    """

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
    TASK = "task"
    EVENT_HANDLER = "event_handler"
    INTEGRATION = "integration"
    COMMAND = "command"
    VALIDATOR = "validator"


@dataclass
class ComponentRef:
    """
    Universal typed reference to any framework component.

    Provides a unified format for referencing controllers, services, middleware,
    guards, pipes, interceptors, and models. Replaces the inconsistent mix of
    bare strings and configuration objects, enabling metadata passing at registration time.

    Parameters:
        class_path: Dotted module path and class name separated by a colon
            (e.g., `"modules.users.controllers:UsersController"`).
        kind: The classification of the component from `ComponentKind`.
        metadata: Arbitrary key-value metadata associated with the component,
            conforming to `ManifestMetadata`.

    Raises:
        ManifestInvalidFault: If the class_path is missing a colon `':'`.

    Examples:
        Basic usage:
        ```python
        ref = ComponentRef(
            class_path="modules.users.controllers:UsersController",
            kind=ComponentKind.CONTROLLER
        )
        ```

        With metadata:
        ```python
        ref = ComponentRef(
            class_path="modules.auth.guards:JWTGuard",
            kind=ComponentKind.GUARD,
            metadata={"priority": 10}
        )
        ```
    """

    class_path: str  # "module.path:ClassName"
    kind: ComponentKind  # Component classification
    metadata: ManifestMetadata = field(default_factory=dict)

    def __post_init__(self):
        if ":" not in self.class_path:
            from .faults.domains import ManifestInvalidFault

            raise ManifestInvalidFault(
                manifest_name="ComponentRef",
                errors=[f"class_path must be 'module.path:ClassName', got '{self.class_path}'"],
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


ServiceScopeLiteral = Literal["singleton", "app", "request", "transient", "pooled", "ephemeral"]


class ServiceScopeMeta(type(Enum)):
    def __getattribute__(cls, name):
        if name in ("SINGLETON", "APP", "REQUEST", "TRANSIENT", "POOLED", "EPHEMERAL"):
            warnings.warn(
                f"Using ServiceScope.{name} is deprecated. Use string literal '{name.lower()}' instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
        return super().__getattribute__(name)

    def __call__(cls, value, names=None, *args, **kwargs):
        if names is None:
            warnings.warn(
                "ServiceScope Enum is deprecated and will be removed in a future version. "
                "Use string literals (e.g. 'singleton', 'app') instead.",
                category=DeprecationWarning,
                stacklevel=2,
            )
        return super().__call__(value, names, *args, **kwargs)


class ServiceScope(str, Enum, metaclass=ServiceScopeMeta):
    """
    [DEPRECATED] Service lifecycle scopes for dependency injection.

    Defines the instantiation policy and lifespan of services resolved
    by the dependency injection (DI) container.

    Attributes:
        SINGLETON: Application-wide single instance shared across all requests.
        APP: Module-level single instance shared within the defining module.
        REQUEST: Instantiated once per incoming HTTP/WebSocket request and disposed after.
        TRANSIENT: Instantiated fresh every time the service is requested/injected.
        POOLED: Managed object pool of reusable instances.
        EPHEMERAL: High-performance transient instance without container tracking or hooks.
    """

    SINGLETON = "singleton"  # App-level single instance
    APP = "app"  # Module-level single instance
    REQUEST = "request"  # New instance per request
    TRANSIENT = "transient"  # Always new instance
    POOLED = "pooled"  # Object pool
    EPHEMERAL = "ephemeral"  # Fastest, no lifecycle


@dataclass
class LifecycleConfig:
    """
    Lifecycle hook configuration for modules and services.

    Allows registering custom startup and shutdown hooks, declaring dependency order,
    and managing timeouts/errors during the application boot process.

    Parameters:
        on_startup: Dotted path to the callable executed during application bootstrap
            (e.g., `"modules.users.hooks:init_db"`).
        on_shutdown: Dotted path to the callable executed during application shutdown
            (e.g., `"modules.users.hooks:close_db"`).
        depends_on: List of other module names that must complete startup before this one.
        startup_timeout: Maximum duration in seconds allowed for startup hook execution.
        shutdown_timeout: Maximum duration in seconds allowed for shutdown hook execution.
        error_strategy: Action taken if a hook fails. Must be `"propagate"`, `"log"`, or `"ignore"`.

    Examples:
        ```python
        config = LifecycleConfig(
            on_startup="modules.users.hooks:on_boot",
            on_shutdown="modules.users.hooks:on_close",
            depends_on=["auth"],
            startup_timeout=15.0,
        )
        ```
    """

    on_startup: str | None = None  # "path.to.module:function"
    on_shutdown: str | None = None  # "path.to.module:function"
    depends_on: list[str] = field(default_factory=list)  # Services to wait for
    startup_timeout: float = 30.0  # Timeout in seconds
    shutdown_timeout: float = 30.0  # Timeout in seconds
    error_strategy: str = "propagate"  # "propagate", "log", "ignore"

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
    """
    Service registration configuration with complete DI support.

    Declares explicit service parameters for registration in the dependency injection
    container, enabling custom scopes, aliases, factories, and conditional flag checks.

    Parameters:
        class_path: Dotted module path and class name separated by a colon
            (e.g., `"modules.users.services:UsersService"`).
        scope: Lifecycle scope policy of the service. Defaults to `"app"`.
        auto_discover: If `True`, automatically wires constructor dependencies.
        lifecycle: Optional custom lifecycle hooks specifically for this service.
        feature_flags: Service is only registered if all listed feature flags are active.
        aliases: Alternative token strings that resolve to this service instance.
        tag: Optional string identifier enabling named/tagged injection (`Inject(tag=...)`).
        factory: Dotted path to a factory function used to instantiate the service.
        factory_args: Dictionary of arguments passed directly to the factory function.
        config: Dictionary of keyword arguments passed directly to the constructor.
        observable: If `True`, publishes performance metrics and tracing spans.
        required: If `True` (default), bootstrap fails if this service cannot be registered.

    Examples:
        Configuration with custom arguments:
        ```python
        config = ServiceConfig(
            class_path="modules.users.services:UsersService",
            scope="singleton",
            config={"max_users": 1000}
        )
        ```

        Using a factory function:
        ```python
        config = ServiceConfig(
            class_path="modules.auth.services:AuthService",
            factory="modules.auth.factories:create_auth_service",
            factory_args={"env": "prod"}
        )
        ```
    """

    class_path: str  # "path.to.module:ClassName"
    scope: ServiceScopeLiteral | ServiceScope = "app"  # Lifecycle scope

    # Auto-discovery
    auto_discover: bool = True  # Auto-wire dependencies

    # Lifecycle management
    lifecycle: LifecycleConfig | None = None

    # Feature flags
    feature_flags: list[str] = field(default_factory=list)  # Conditional registration

    # DI alternatives
    aliases: list[str] = field(default_factory=list)  # Alternative injection names
    tag: str | None = None  # Explicit DI tag for Inject(tag=...) resolution

    # Factory pattern
    factory: str | None = None  # "path.to.module:factory_function"
    factory_args: dict[str, Any] | None = None  # Factory arguments

    # Configuration
    config: dict[str, Any] | None = None  # Constructor kwargs

    # Observability
    observable: bool = True  # Include in metrics/tracing
    required: bool = True  # Fail if can't register

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "class_path": self.class_path,
            "scope": getattr(self.scope, "value", str(self.scope)),
            "auto_discover": self.auto_discover,
            "aliases": self.aliases,
            "tag": self.tag,
            "factory": self.factory,
            "config": self.config or {},
        }


@dataclass
class MiddlewareConfig:
    """
    Middleware registration configuration.

    Declares a middleware component in the HTTP request/response pipeline, defining
    its path, execution priority, active scope, and conditional parameters.

    Parameters:
        class_path: Dotted module path and class name separated by a colon
            (e.g., `"modules.users.middleware:UsersMiddleware"`).
        scope: Target routing scope. Must be `"global"` (runs on all routes),
            `"app"` (runs on specific application routes), or `"route"` (runs on specific path patterns).
        scope_target: Optional target modifier for scope (e.g. specific application name or path pattern).
        priority: Execution priority order (lower executes earlier, default is `50`).
        condition: Optional callable returning a boolean to determine if the middleware should run.
        config: Dictionary of keyword arguments passed directly to the middleware constructor.
        on_error: Recovery action if middleware execution fails. Must be `"propagate"`, `"skip"`, or `"fallback"`.
        fallback: Optional dotted path to fallback middleware.
        observable: If `True`, records execution duration metrics.
        log_requests: If `True`, enables logging for incoming requests.
        log_responses: If `True`, enables logging for outgoing responses.

    Examples:
        ```python
        config = MiddlewareConfig(
            class_path="aquilia.middleware:LoggingMiddleware",
            scope="global",
            priority=10,
            config={"log_headers": True}
        )
        ```
    """

    class_path: str  # "path.to.module:ClassName"
    scope: str = "global"  # "global", "app", "route"
    scope_target: str | None = None  # For app:name or route:/pattern
    priority: int = 50  # Lower = earlier execution

    # Conditional execution
    condition: Callable | None = None  # Optional function returning bool

    # Configuration
    config: dict[str, Any] | None = None  # Constructor kwargs

    # Error handling
    on_error: str = "propagate"  # "propagate", "skip", "fallback"
    fallback: str | None = None  # Fallback middleware path

    # Observability
    observable: bool = True  # Include in metrics
    log_requests: bool = False  # Log individual requests
    log_responses: bool = False  # Log individual responses

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
    """
    Session management configuration.

    Defines cryptographic session policies, TTLs, transport methods (cookies or headers),
    and storage backends (memory, redis, etc.) for a module.

    Parameters:
        name: Unique session policy name.
        enabled: If `True` (default), enables session management for this module.
        ttl: Time-to-live duration for active sessions. Defaults to `7 days`.
        idle_timeout: Optional inactivity timeout duration.
        renewal: Optional session renewal/refresh window duration.
        transport: Protocol transport method. Must be `"cookie"`, `"header"`, or `"custom"`.
        transport_config: Optional dictionary of transport-specific parameters.
        cookie_name: Name of the session cookie. Defaults to `"session_id"`.
        cookie_domain: Optional domain limitation for the session cookie.
        cookie_path: URL path constraint for the session cookie. Defaults to `"/"`.
        cookie_secure: If `True` (default), cookie is only sent over HTTPS.
        cookie_httponly: If `True` (default), cookie is inaccessible to client-side scripts.
        cookie_samesite: CSRF protection policy. Must be `"Strict"`, `"Lax"`, or `"None"`.
        store: Storage engine type. Must be `"memory"`, `"redis"`, `"database"`, or `"custom"`.
        store_config: Optional dictionary of storage engine parameters.
        encryption_enabled: If `True`, session data is encrypted at rest/transit.
        encryption_key_env: Environment variable holding the cryptographic secret key.
        serializer: Session serialization format. Must be `"json"`, `"pickle"`, or `"msgpack"`.
        log_lifecycle: If `True`, logs session creation and destruction events.
        metrics_enabled: If `True`, collects session metrics.

    Examples:
        ```python
        config = SessionConfig(
            name="user_session",
            ttl=timedelta(days=1),
            cookie_secure=True,
            store="redis",
            store_config={"redis_url": "redis://localhost:6379/1"}
        )
        ```
    """

    name: str  # Session policy name
    enabled: bool = True  # Enable/disable
    ttl: timedelta = field(default_factory=lambda: timedelta(days=7))  # Time to live
    idle_timeout: timedelta | None = None  # Inactivity timeout
    renewal: timedelta | None = None  # Renewal window

    # Transport layer
    transport: str = "cookie"  # "cookie", "header", "custom"
    transport_config: dict[str, Any] | None = None  # Transport-specific config

    # Cookie-specific settings (for transport="cookie")
    cookie_name: str = "session_id"
    cookie_domain: str | None = None
    cookie_path: str = "/"
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: str = "Strict"  # "Strict", "Lax", "None"

    # Storage
    store: str = "memory"  # "memory", "redis", "database", "custom"
    store_config: dict[str, Any] | None = None  # Store-specific config

    # Encryption
    encryption_enabled: bool = True
    encryption_key_env: str = "SESSION_ENCRYPTION_KEY"

    # Serialization
    serializer: str = "json"  # "json", "pickle", "msgpack"

    # Observability
    log_lifecycle: bool = False  # Log session create/destroy
    metrics_enabled: bool = True  # Collect metrics

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
    """
    Fault handler configuration for specific exception domains.

    Maps a structured framework fault domain (e.g. `"AUTH"`, `"VALIDATION"`) to an
    exception handler callable, and defines error recovery strategies.

    Parameters:
        domain: Target fault domain name.
        handler_path: Dotted path to the handler function (e.g. `"modules.auth.handlers:on_auth_fault"`).
        recovery_strategy: Strategy to use. Must be `"propagate"`, `"recover"`, or `"fallback"`.
        fallback_response: Optional JSON-serializable dictionary returned on fallback.

    Examples:
        ```python
        handler = FaultHandlerConfig(
            domain="VALIDATION",
            handler_path="modules.users.handlers:handle_validation_error",
            recovery_strategy="recover"
        )
        ```
    """

    domain: str  # Fault domain (e.g., "AUTH", "VALIDATION")
    handler_path: str  # "path.to.module:handler_function"
    recovery_strategy: str = "propagate"  # "propagate", "recover", "fallback"
    fallback_response: dict[str, Any] | None = None  # Fallback response


@dataclass
class FaultHandlingConfig:
    """
    Module-level fault and error handling configuration.

    Aggregates fault domain handlers, exception translation middleware, and metrics.

    Parameters:
        default_domain: Fallback fault domain name when none is matched. Defaults to `"APP"`.
        strategy: Default recovery action if a handler is not defined. Defaults to `"propagate"`.
        handlers: List of explicit domain handlers using `FaultHandlerConfig`.
        middlewares: List of custom error middleware instances.
        metrics_enabled: If `True`, tracks error counts and rates.

    Examples:
        ```python
        config = FaultHandlingConfig(
            default_domain="BILLING",
            handlers=[
                FaultHandlerConfig(
                    domain="STRIPE",
                    handler_path="modules.billing.handlers:handle_stripe_error"
                )
            ]
        )
        ```
    """

    default_domain: str = "APP"  # Default fault domain
    strategy: str = "propagate"  # "propagate", "recover", "fallback"
    handlers: list[FaultHandlerConfig] = field(default_factory=list)  # Domain handlers
    middlewares: list[MiddlewareConfig] = field(default_factory=list)  # Error middlewares
    metrics_enabled: bool = True  # Collect error metrics

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
    """
    Feature flag configuration for conditional component activation.

    Allows wrapping services, controllers, middleware, and routes with a feature
    toggle, enabling dynamic module composition based on runtime conditions.

    Parameters:
        name: Unique feature flag identifier string.
        enabled: If `True`, the feature is enabled by default. Defaults to `False`.
        conditions: Dictionary of rules (e.g. env vars, customer tier) required to enable.
        services: List of service class path strings only registered when the feature is active.
        controllers: List of controller path strings only registered when feature is active.
        middleware: List of middleware configurations only active when feature is active.
        routes: List of routes only registered when feature is active.
        log_usage: If `True`, logs feature evaluation events.
        metrics_enabled: If `True`, collects usage metrics.

    Examples:
        ```python
        feature = FeatureConfig(
            name="beta-billing",
            enabled=False,
            conditions={"env": "staging"},
            services=["modules.billing.services:BetaBillingService"]
        )
        ```
    """

    name: str  # Feature identifier
    enabled: bool = False  # Default state
    conditions: dict[str, Any] | None = None  # Conditional rules
    services: list[str] = field(default_factory=list)  # Services to register
    controllers: list[str] = field(default_factory=list)  # Controllers to register
    middleware: list[MiddlewareConfig] = field(default_factory=list)  # Middleware
    routes: list[str] = field(default_factory=list)  # Routes to register

    # Observability
    log_usage: bool = True  # Log feature usage
    metrics_enabled: bool = True  # Collect metrics

    def to_dict(self) -> dict:
        """Serialize to dictionary."""
        return {
            "name": self.name,
            "enabled": self.enabled,
            "conditions": self.conditions or {},
        }


@dataclass
class BackgroundTaskConfig:
    """Per-module background task configuration.

    Declares background tasks owned by this module, their default
    queues, retry policies, and scheduling parameters.

    The tasks listed here are auto-registered with the
    :class:`TaskManager` during server startup.  The ``@task``
    decorator on the functions provides the runtime metadata;
    this config gives the manifest layer visibility into what
    tasks a module contributes.

    Example::

        background_tasks=BackgroundTaskConfig(
            tasks=[
                "modules.auth.tasks:cleanup_expired_sessions",
                "modules.auth.tasks:record_login_attempt",
            ],
            default_queue="auth",
            auto_discover=True,
        )
    """

    tasks: list[str] = field(default_factory=list)  # Dotted refs to @task functions
    default_queue: str = "default"  # Fallback queue for this module
    auto_discover: bool = True  # Scan tasks.py automatically
    enabled: bool = True  # Enable/disable module tasks

    def to_dict(self) -> dict:
        return {
            "tasks": self.tasks,
            "default_queue": self.default_queue,
            "auto_discover": self.auto_discover,
            "enabled": self.enabled,
        }


@dataclass
class TemplateConfig:
    """
    Jinja2-based template engine configuration for a module.

    Defines search paths, caching mechanisms, precompilation policies, and
    context processors for rendering HTML/text templates.

    Parameters:
        enabled: If `True` (default), enables template rendering for this module.
        search_paths: List of directory paths (relative to module root) containing templates.
        precompile: If `True`, compiles all templates at application boot time for faster response.
        cache: Caching backend. Must be `"memory"`, `"surp"`, or `"none"`.
        sandbox: If `True` (default), uses a secure sandboxed Jinja environment to prevent arbitrary code execution.
        context_processors: List of dotted path strings to callables returning template global context.

    Examples:
        ```python
        config = TemplateConfig(
            search_paths=["templates", "layouts"],
            cache="memory",
            sandbox=True
        )
        ```
    """

    enabled: bool = True
    search_paths: list[str] = field(default_factory=list)
    precompile: bool = False
    cache: str = "memory"  # "memory", "surp", "none"
    sandbox: bool = True
    context_processors: list[str] = field(default_factory=list)

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
    DEPRECATED: Manifest-level database configuration.

    This class is retained only for backward compatibility. Use `Workspace.database()`
    or `Integration.database()` inside `workspace.py` instead.

    Parameters:
        url: Database connection string.
        auto_connect: Connect on startup.
        auto_create: Automatically create database tables.
        auto_migrate: Automatically execute pending migrations.
        migrations_dir: Directory containing migration scripts.
        pool_size: Connection pool size.
        echo: Log generated SQL queries.
        model_paths: Explicit list of database model paths.
        scan_dirs: Directories scanned for model discovery.
    """

    url: str = "sqlite:///db.sqlite3"  # Database URL
    auto_connect: bool = True  # Connect on startup
    auto_create: bool = True  # Create tables on startup
    auto_migrate: bool = False  # Run pending migrations on startup
    migrations_dir: str = "migrations"  # Migration files directory
    pool_size: int = 5  # Connection pool size (future)
    echo: bool = False  # Log SQL statements

    # Model discovery
    model_paths: list[str] = field(default_factory=list)  # Explicit model paths
    scan_dirs: list[str] = field(default_factory=lambda: ["models"])  # Directories to scan

    def __post_init__(self) -> None:
        warnings.warn(
            "AppManifest.database / manifest.DatabaseConfig is deprecated and ignored at runtime. "
            "Configure database via Workspace.database() / Integration.database().",
            DeprecationWarning,
            stacklevel=2,
        )

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
class AppVersioningConfig:
    """
    Module-level versioning override configuration.

    Enables version negotiation, route prefixing, and deprecation scheduling
    specifically for API routes defined in this module.

    Parameters:
        strategy: Negotiation strategy. Must be `"header"`, `"url"`, `"query"`, `"media_type"`, `"channel"`, or `"composite"`.
        versions: List of supported version identifier strings (e.g. `["v1", "v2"]`).
        default_version: Version used when none is provided in the client request.
        require_version: If `True`, requests without version info are rejected with a fault.
        header_name: HTTP header name for versioning (used with strategy `"header"`). Defaults to `"X-API-Version"`.
        query_param: Query parameter name for versioning. Defaults to `"api_version"`.
        url_prefix: Prefix used for URL path segment versioning. Defaults to `"v"`.
        url_segment_index: Index of URL segment containing version. Defaults to `0`.
        strip_version_from_path: If `True`, removes version segment from request path before routing.
        url_position: Position of the version segment in URL. Must be `"before"` or `"after"`.
        expose_unversioned_alias: If `True`, exposes routes without a version prefix.
        media_type_param: Media type version parameter. Defaults to `"version"`.
        channels: Dictionary mapping channel names to versions.
        channel_header: HTTP header name for channel identifier.
        channel_query_param: Query parameter name for channel identifier.
        negotiation_mode: Negotiation behavior. Must be `"exact"`, `"compatible"`, `"best_match"`, or `"latest"`.
        sunset_policy: Optional sunset/deprecation policy metadata object.
        sunset_schedules: Dictionary containing sunset schedule dates per version.
        include_version_header: If `True`, includes version header in responses.
        response_header_name: Name of the response version header. Defaults to `"X-API-Version"`.
        include_supported_versions_header: If `True`, includes supported versions header in response.
        neutral_paths: List of route paths exempt from version requirements.
        enabled: If `True` (default), enables versioning for this module.
        auto_version_unmarked: If `True`, automatically versions routes without explicit decorator tags.
        position: Convenience alias for `url_position`.

    Examples:
        ```python
        config = AppVersioningConfig(
            strategy="url",
            versions=["v1", "v2"],
            default_version="v2",
            require_version=True
        )
        ```
    """

    strategy: str = "header"
    versions: list[str] = field(default_factory=list)
    default_version: str | None = None
    require_version: bool = False
    header_name: str = "X-API-Version"
    query_param: str = "api_version"
    url_prefix: str = "v"
    url_segment_index: int = 0
    strip_version_from_path: bool = True
    url_position: str = "before"
    expose_unversioned_alias: bool = False
    media_type_param: str = "version"
    channels: dict[str, str] = field(default_factory=dict)
    channel_header: str = "X-API-Channel"
    channel_query_param: str = "api_channel"
    negotiation_mode: str = "exact"
    sunset_policy: Any | None = None
    sunset_schedules: dict[str, dict[str, Any]] = field(default_factory=dict)
    include_version_header: bool = True
    response_header_name: str = "X-API-Version"
    include_supported_versions_header: bool = True
    neutral_paths: list[str] | None = None
    enabled: bool = True
    auto_version_unmarked: bool = False
    position: str | None = None  # Convenience alias for url_position

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dictionary."""
        pos = self.position or self.url_position
        config: dict[str, Any] = {
            "enabled": self.enabled,
            "strategy": self.strategy,
            "versions": self.versions,
            "default_version": self.default_version,
            "require_version": self.require_version,
            "header_name": self.header_name,
            "query_param": self.query_param,
            "url_prefix": self.url_prefix,
            "url_segment_index": self.url_segment_index,
            "strip_version_from_path": self.strip_version_from_path,
            "url_position": pos,
            "position": pos,
            "expose_unversioned_alias": self.expose_unversioned_alias,
            "media_type_param": self.media_type_param,
            "channels": self.channels,
            "channel_header": self.channel_header,
            "channel_query_param": self.channel_query_param,
            "negotiation_mode": self.negotiation_mode,
            "sunset_schedules": self.sunset_schedules,
            "include_version_header": self.include_version_header,
            "response_header_name": self.response_header_name,
            "include_supported_versions_header": self.include_supported_versions_header,
            "neutral_paths": self.neutral_paths,
            "auto_version_unmarked": self.auto_version_unmarked,
        }
        if self.sunset_policy is not None:
            config["sunset_policy"] = self.sunset_policy
        return config


def versioning(
    strategy: str = "header",
    versions: list[str] | None = None,
    default_version: str | None = None,
    require_version: bool = False,
    header_name: str = "X-API-Version",
    query_param: str = "api_version",
    url_prefix: str = "v",
    url_segment_index: int = 0,
    strip_version_from_path: bool = True,
    url_position: str = "before",
    expose_unversioned_alias: bool = False,
    media_type_param: str = "version",
    channels: dict[str, str] | None = None,
    channel_header: str = "X-API-Channel",
    channel_query_param: str = "api_channel",
    negotiation_mode: str = "exact",
    sunset_policy: Any | None = None,
    sunset_schedules: dict[str, dict[str, Any]] | None = None,
    include_version_header: bool = True,
    response_header_name: str = "X-API-Version",
    include_supported_versions_header: bool = True,
    neutral_paths: list[str] | None = None,
    enabled: bool = True,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Configure API versioning integration at the module manifest level.

    Helper function returning a dictionary structure matching `AppVersioningConfig`
    parameters, providing backward-compatible syntax for configuration blocks.

    Parameters:
        strategy: Negotiation strategy. Must be `"header"`, `"url"`, `"query"`, `"media_type"`, `"channel"`, or `"composite"`.
        versions: List of supported version identifier strings.
        default_version: Version used when none is provided in the client request.
        require_version: If `True`, requests without version info are rejected with a fault.
        header_name: HTTP header name for versioning. Defaults to `"X-API-Version"`.
        query_param: Query parameter name for versioning. Defaults to `"api_version"`.
        url_prefix: Prefix used for URL path segment versioning. Defaults to `"v"`.
        url_segment_index: Index of URL segment containing version. Defaults to `0`.
        strip_version_from_path: If `True`, removes version segment from request path.
        url_position: Position of the version segment in URL. Must be `"before"` or `"after"`.
        expose_unversioned_alias: If `True`, exposes routes without a version prefix.
        media_type_param: Media type version parameter. Defaults to `"version"`.
        channels: Dictionary mapping channel names to versions.
        channel_header: HTTP header name for channel identifier.
        channel_query_param: Query parameter name for channel identifier.
        negotiation_mode: Negotiation behavior. Must be `"exact"`, `"compatible"`, `"best_match"`, or `"latest"`.
        sunset_policy: Optional sunset/deprecation policy metadata object.
        sunset_schedules: Dictionary containing sunset schedule dates per version.
        include_version_header: If `True`, includes version header in responses.
        response_header_name: Name of the response version header. Defaults to `"X-API-Version"`.
        include_supported_versions_header: If `True`, includes supported versions header in response.
        neutral_paths: List of route paths exempt from version requirements.
        enabled: If `True` (default), enables versioning for this module.
        **kwargs: Extensible extra arguments.

    Returns:
        Dictionary containing all structured versioning settings.
    """
    config: dict[str, Any] = {
        "enabled": enabled,
        "strategy": strategy,
        "versions": versions or [],
        "default_version": default_version,
        "require_version": require_version,
        "header_name": header_name,
        "query_param": query_param,
        "url_prefix": url_prefix,
        "url_segment_index": url_segment_index,
        "strip_version_from_path": strip_version_from_path,
        "url_position": url_position,
        "expose_unversioned_alias": expose_unversioned_alias,
        "media_type_param": media_type_param,
        "channels": channels or {},
        "channel_header": channel_header,
        "channel_query_param": channel_query_param,
        "negotiation_mode": negotiation_mode,
        "include_version_header": include_version_header,
        "response_header_name": response_header_name,
        "include_supported_versions_header": include_supported_versions_header,
        "neutral_paths": neutral_paths,
        **kwargs,
    }
    if sunset_policy is not None:
        config["sunset_policy"] = sunset_policy
    if sunset_schedules:
        config["sunset_schedules"] = sunset_schedules
    return config


@dataclass
class AppManifest:
    """
    Production-grade application manifest for complete app configuration.

    The primary entry point for declaring a module's internal assets, wiring, and
    dependencies. It maps controllers, services, database models, background tasks,
    middleware, request pipeline guards, pipes, and interceptors.

    In the Manifest-First Design:
    1. Each module contains a `manifest.py` containing an `AppManifest` instance (by convention).
    2. During boot, the framework scans modules to load manifests and build a dependency graph.
    3. Manifest parameters are normalized, validated, and resolved at runtime.

    Parameters:
        name: Unique module identifier (alphanumeric with underscores).
        version: Semantic version of the module.
        description: Concise summary of what the module does.
        author: Developer/Owner email or name.
        services: List of services to register in the DI container.
            Can contain strings, `ServiceConfig` instances, or `ComponentRef` objects.
        controllers: List of HTTP controller classes or `ComponentRef` objects.
        socket_controllers: List of WebSocket controller classes or `ComponentRef` objects.
        models: List of model classes or `ComponentRef` objects.
        serializers: List of serializer classes or `ComponentRef` objects.
        guards: List of authorization guard class paths or `ComponentRef` objects.
        pipes: List of request data validation pipe class paths or `ComponentRef` objects.
        interceptors: List of aspect-oriented interceptor class paths or `ComponentRef` objects.
        middleware: List of middleware configs, class paths, or `ComponentRef` objects.
        route_prefix: DEPRECATED: Module route prefix (use `Module.route_prefix()` in `workspace.py`).
        base_path: Optional base directory override for file imports.
        lifecycle: Module startup/shutdown lifecycle configs (`LifecycleConfig`).
        sessions: List of session policy configurations (`SessionConfig`).
        templates: Jinja template engine configuration (`TemplateConfig`).
        database: DEPRECATED: Module database configuration. Use `Workspace.database()` instead.
        faults: Fault handling configuration (`FaultHandlingConfig`).
        background_tasks: Background task queue declarations (`BackgroundTaskConfig`).
        features: Feature toggle configurations (`FeatureConfig`).
        exports: List of service class names exported to importing modules.
        imports: List of module names this module depends on.
        depends_on: Legacy alias for `imports`.
        tags: List of organizational tags.
        versioning: Version negotiation parameters (`AppVersioningConfig`).
        config_schema: Optional JSON Schema dictionary to validate module configuration.
        auto_discover: If `True` (default), scans directories matching `discover_patterns`.
        discover_patterns: Folders to scan during auto-discovery.
        middlewares: Legacy middleware format.
        default_fault_domain: Legacy fault domain.
        on_startup: Legacy startup callable.
        on_shutdown: Legacy shutdown callable.
        config: Legacy config class.

    Raises:
        ManifestInvalidFault: If name or version is missing, or name is invalid.

    Examples:
        Declaring a billing module:
        ```python
        from aquilia.manifest import AppManifest, ServiceConfig

        manifest = AppManifest(
            name="billing",
            version="1.0.0",
            services=[
                ServiceConfig(
                    class_path="modules.billing.services:BillingService",
                    scope="singleton"
                )
            ],
            controllers=[
                "modules.billing.controllers:BillingController"
            ],
            imports=["auth", "users"],
            exports=["modules.billing.services:BillingService"]
        )
        ```
    """

    # Identity
    name: str  # Module name
    version: str  # Semantic version
    description: str = ""  # Module description
    author: str = ""  # Module author

    # Component declarations -- all accept str or ComponentRef
    services: list[str | ServiceConfig | ComponentRef] = field(default_factory=list)
    controllers: list[str | ComponentRef] = field(default_factory=list)
    socket_controllers: list[str | ComponentRef] = field(default_factory=list)
    models: list[str | ComponentRef] = field(default_factory=list)
    serializers: list[str | ComponentRef] = field(default_factory=list)

    # v2: First-class request pipeline components
    guards: list[str | ComponentRef] = field(default_factory=list)
    pipes: list[str | ComponentRef] = field(default_factory=list)
    interceptors: list[str | ComponentRef] = field(default_factory=list)

    # Middleware configuration
    middleware: list[str | MiddlewareConfig | ComponentRef] = field(default_factory=list)

    # Routing (DEPRECATED: use Module.route_prefix() in workspace.py)
    route_prefix: str = "/"  # Route prefix for module (deprecated - use workspace)
    base_path: str | None = None  # Optional base path override

    # Lifecycle management
    lifecycle: LifecycleConfig | None = None

    # Session management
    sessions: list[SessionConfig] = field(default_factory=list)

    # Template management
    templates: TemplateConfig | None = None

    # Database and models (DEPRECATED: ignored at runtime)
    database: DatabaseConfig | None = None

    # Error handling
    faults: FaultHandlingConfig | None = None

    # Background tasks
    background_tasks: BackgroundTaskConfig | None = None

    # Feature flags
    features: list[FeatureConfig] = field(default_factory=list)

    # v2: Cross-module dependency management
    exports: list[str] = field(default_factory=list)  # Services visible to importing modules
    imports: list[str] = field(default_factory=list)  # Modules this module depends on

    # Legacy: still works but prefer 'imports'
    depends_on: list[str] = field(default_factory=list)

    # Metadata
    tags: list[str] = field(default_factory=list)
    versioning: AppVersioningConfig | dict[str, Any] | None = None
    config_schema: dict[str, Any] | None = None  # JSON Schema for validation

    # v2: Auto-discovery control
    auto_discover: bool = True  # Enable convention-based component scanning
    discover_patterns: list[str] = field(
        default_factory=lambda: ["controllers", "services", "middleware", "guards", "models", "tasks"]
    )

    # Legacy support (for backward compatibility -- will emit warnings)
    middlewares: list[tuple[str, dict]] = field(default_factory=list)  # Old format
    default_fault_domain: str | None = None  # Old format
    on_startup: Callable | None = None  # Old format
    on_shutdown: Callable | None = None  # Old format
    config: type | None = None  # Old format

    def __post_init__(self):
        """Validate and normalize manifest structure."""
        from .faults.domains import ManifestInvalidFault

        if not self.name:
            raise ManifestInvalidFault(
                manifest_name="unknown",
                errors=["Manifest must have a name"],
            )
        if not self.version:
            raise ManifestInvalidFault(
                manifest_name=self.name,
                errors=["Manifest must have a version"],
            )

        # Validate name format (alphanumeric + underscore)
        if not self.name.replace("_", "").isalnum():
            raise ManifestInvalidFault(
                manifest_name=self.name,
                errors=[f"Invalid app name '{self.name}': must be alphanumeric with underscores"],
            )

        # Convert legacy middleware format to new format if needed
        if self.middlewares and not self.middleware:
            warnings.warn(
                f"AppManifest({self.name!r}).middlewares is deprecated. "
                "Use 'middleware' with MiddlewareConfig objects instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            for path, kwargs in self.middlewares:
                self.middleware.append(MiddlewareConfig(class_path=path, config=kwargs or {}))

        # Convert legacy fault domain to new format if needed
        if self.default_fault_domain and not self.faults:
            warnings.warn(
                f"AppManifest({self.name!r}).default_fault_domain is deprecated. "
                "Use 'faults=FaultHandlingConfig(default_domain=...)' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            self.faults = FaultHandlingConfig(default_domain=self.default_fault_domain)

        # v2: Migrate depends_on → imports (with warning)
        if self.depends_on and not self.imports:
            warnings.warn(
                f"AppManifest({self.name!r}).depends_on is deprecated. "
                "Use 'imports' instead for cross-module dependencies.",
                DeprecationWarning,
                stacklevel=2,
            )
            self.imports = list(self.depends_on)

        # v2: Deprecate route_prefix in manifest (should be in workspace.py)
        if self.route_prefix != "/":
            warnings.warn(
                f"AppManifest({self.name!r}).route_prefix is deprecated. "
                "Use Module.route_prefix() in workspace.py instead. "
                "The workspace value will take precedence at runtime.",
                DeprecationWarning,
                stacklevel=2,
            )

        # Deprecate manifest-level DB config and clear it so runtime behavior
        # is always driven by workspace/integration config.
        if self.database is not None:
            warnings.warn(
                f"AppManifest({self.name!r}).database is deprecated and ignored at runtime. "
                "Use Workspace.database() / Integration.database() instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            self.database = None

        # v2: Normalize string services to ServiceConfig
        normalized_services = []
        for s in self.services:
            if isinstance(s, str):
                normalized_services.append(ServiceConfig(class_path=s))
            elif isinstance(s, ComponentRef):
                normalized_services.append(
                    ServiceConfig(
                        class_path=s.class_path,
                        config=s.metadata.get("config"),
                    )
                )
            else:
                normalized_services.append(s)
        self.services = normalized_services

        # v2: Normalize string middleware to MiddlewareConfig
        normalized_mw = []
        for m in self.middleware:
            if isinstance(m, str):
                normalized_mw.append(MiddlewareConfig(class_path=m))
            elif isinstance(m, ComponentRef):
                normalized_mw.append(
                    MiddlewareConfig(
                        class_path=m.class_path,
                        priority=m.metadata.get("priority", 50),
                        config=m.metadata.get("config"),
                    )
                )
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
                return cast(str, ref.class_path)
            return str(ref)

        result = {
            "name": self.name,
            "version": self.version,
            "controllers": [_ref_to_str(c) for c in self.controllers],
            "socket_controllers": [_ref_to_str(c) for c in self.socket_controllers],
            "models": [_ref_to_str(m) for m in self.models],
            "serializers": [_ref_to_str(s) for s in self.serializers],
            "services": [s.to_dict() if hasattr(s, "to_dict") else str(s) for s in self.services],
            "middleware": [m.to_dict() if hasattr(m, "to_dict") else str(m) for m in self.middleware],
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
        if self.background_tasks:
            result["background_tasks"] = self.background_tasks.to_dict()
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
