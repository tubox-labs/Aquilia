"""
Fluent Configuration Builders for Aquilia.

Provides a unique, type-safe, fluent API for configuring Aquilia workspaces.
Replaces YAML configuration with Python for better IDE support and validation.

Supports typed database config classes (SqliteConfig, PostgresConfig,
MysqlConfig, OracleConfig) alongside URL-based configuration for backward
compatibility.

Example:
    >>> from aquilia.db.configs import PostgresConfig
    >>> workspace = (
    ...     Workspace("myapp", version="0.1.0")
    ...     .runtime(mode="dev", port=8000)
    ...     .module(Module("users").route_prefix("/users"))
    ...     .integrate(Integration.database(
    ...         config=PostgresConfig(
    ...             host="localhost",
    ...             name="mydb",
    ...             user="admin",
    ...             password="secret",
    ...         )
    ...     ))
    ...     .integrate(Integration.sessions(...))
    ... )
"""

from typing import Optional, List, Any, Dict, Union
from dataclasses import dataclass, field
from datetime import timedelta


@dataclass
class RuntimeConfig:
    """Runtime configuration."""
    mode: str = "dev"
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    workers: int = 1


@dataclass
class ModuleConfig:
    """
    Module configuration -- workspace-level orchestration metadata.
    
    The Module in workspace.py is a **pointer** to the per-module manifest.
    Component declarations (controllers, services, middleware, models,
    serializers, socket_controllers) live exclusively in each module's
    ``manifest.py`` via ``AppManifest``.
    
    This dataclass holds only the orchestration concerns that the
    workspace needs to know about:
    - Identity (name, version)
    - Routing topology (route_prefix, depends_on)
    - Organisational metadata (tags, description, fault_domain)
    - Discovery behaviour (auto_discover)
    - Lifecycle hooks (on_startup, on_shutdown)
    - Per-module database override
    """
    name: str
    version: str = "0.1.0"
    description: str = ""
    fault_domain: Optional[str] = None
    route_prefix: Optional[str] = None
    depends_on: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # v2: Module encapsulation
    imports: List[str] = field(default_factory=list)   # modules this module depends on
    exports: List[str] = field(default_factory=list)   # services/components exposed to importers
    
    # Lifecycle hooks
    on_startup: Optional[str] = None
    on_shutdown: Optional[str] = None
    
    # Database configuration (per-module override)
    database: Optional[Dict[str, Any]] = None
    
    # Discovery configuration
    auto_discover: bool = True  # Default to True for convenience
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        result = {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "fault_domain": self.fault_domain or self.name.upper(),
            "route_prefix": self.route_prefix or f"/{self.name}",
            "depends_on": self.depends_on,
            "imports": self.imports,
            "exports": self.exports,
            "tags": self.tags,
            "on_startup": self.on_startup,
            "on_shutdown": self.on_shutdown,
            "auto_discover": self.auto_discover,
        }
        if self.database:
            result["database"] = self.database
        return result


class Module:
    """
    Fluent module builder -- workspace-level orchestration only.
    
    The Module builder configures **how** a module fits into the workspace
    (routing, dependencies, tags, lifecycle). All component declarations
    (controllers, services, middleware, models, serializers) belong in the
    module's own ``manifest.py`` via ``AppManifest``.
    
    This separation follows the Manifest-First Architecture:
    - ``workspace.py`` → orchestration & integration config
    - ``modules/*/manifest.py`` → module internals (source of truth)
    
    Example::
    
        # workspace.py -- pointer only
        workspace = (
            Workspace("myapp")
            .module(
                Module("users", version="0.1.0")
                .route_prefix("/users")
                .depends_on("auth")
                .tags("core", "users")
            )
            .module(
                Module("auth", version="0.1.0")
                .route_prefix("/auth")
            )
        )
        
        # modules/users/manifest.py -- source of truth
        manifest = AppManifest(
            name="users",
            version="0.1.0",
            controllers=["modules.users.controllers:UsersController"],
            services=["modules.users.services:UsersService"],
            ...
        )
    """
    
    def __init__(self, name: str, version: str = "0.1.0", description: str = ""):
        self._config = ModuleConfig(
            name=name,
            version=version,
            description=description,
            auto_discover=True,
        )
    
    def auto_discover(self, enabled: bool = True) -> "Module":
        """
        Configure auto-discovery behavior.
        
        If enabled (default), the runtime will automatically scan:
        - .controllers for Controller subclasses
        - .services for Service classes
        
        Args:
            enabled: Whether to enable auto-discovery
        """
        self._config.auto_discover = enabled
        return self
    
    def fault_domain(self, domain: str) -> "Module":
        """Set fault domain."""
        self._config.fault_domain = domain
        return self
    
    def route_prefix(self, prefix: str) -> "Module":
        """Set route prefix."""
        self._config.route_prefix = prefix
        return self
    
    def depends_on(self, *modules: str) -> "Module":
        """Set module dependencies (legacy -- prefer imports())."""
        self._config.depends_on = list(modules)
        return self
    
    def imports(self, *modules: str) -> "Module":
        """
        Declare module imports (v2 encapsulation).
        
        Modules listed here expose their ``exports`` to this module.
        Supersedes ``depends_on()`` for dependency declaration.
        
        Args:
            *modules: Names of modules to import from.
        """
        self._config.imports = list(modules)
        # Keep depends_on in sync for backward compatibility
        self._config.depends_on = list(modules)
        return self
    
    def exports(self, *components: str) -> "Module":
        """
        Declare exported components (v2 encapsulation).
        
        Only exported services/components are visible to importing modules.
        Non-exported components are module-private.
        
        Args:
            *components: Import paths of components to export.
        """
        self._config.exports = list(components)
        return self
    
    def tags(self, *module_tags: str) -> "Module":
        """Set module tags for organization and filtering."""
        self._config.tags = list(module_tags)
        return self

    # ──────────────────────────────────────────────────────────────────────
    # Legacy registration methods (DEPRECATED)
    #
    # These methods are retained for backward compatibility but are no-ops
    # in the new architecture.  All component declarations belong in the
    # module's manifest.py.  The workspace.py Module builder is a pointer
    # only; the manifest is the source of truth.
    # ──────────────────────────────────────────────────────────────────────

    def register_controllers(self, *controllers: str) -> "Module":
        """DEPRECATED -- declare controllers in modules/*/manifest.py instead."""
        import warnings
        warnings.warn(
            "Module.register_controllers() is deprecated. "
            "Declare controllers in modules/<name>/manifest.py → AppManifest(controllers=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_services(self, *services: str) -> "Module":
        """DEPRECATED -- declare services in modules/*/manifest.py instead."""
        import warnings
        warnings.warn(
            "Module.register_services() is deprecated. "
            "Declare services in modules/<name>/manifest.py → AppManifest(services=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self
        
    def register_providers(self, *providers: Dict[str, Any]) -> "Module":
        """DEPRECATED -- declare providers in modules/*/manifest.py instead."""
        import warnings
        warnings.warn(
            "Module.register_providers() is deprecated. "
            "Declare providers in modules/<name>/manifest.py.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self
        
    def register_routes(self, *routes: Dict[str, Any]) -> "Module":
        """DEPRECATED -- declare routes via controllers in modules/*/manifest.py instead."""
        import warnings
        warnings.warn(
            "Module.register_routes() is deprecated. "
            "Use controller decorators (@GET, @POST, etc.) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_sockets(self, *sockets: str) -> "Module":
        """DEPRECATED -- declare socket controllers in modules/*/manifest.py instead."""
        import warnings
        warnings.warn(
            "Module.register_sockets() is deprecated. "
            "Declare socket_controllers in modules/<name>/manifest.py → AppManifest(socket_controllers=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_middlewares(self, *middlewares: str) -> "Module":
        """DEPRECATED -- declare middleware in modules/*/manifest.py instead."""
        import warnings
        warnings.warn(
            "Module.register_middlewares() is deprecated. "
            "Declare middleware in modules/<name>/manifest.py → AppManifest(middleware=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self
    
    def register_models(self, *models: str) -> "Module":
        """DEPRECATED -- declare models in modules/*/manifest.py instead."""
        import warnings
        warnings.warn(
            "Module.register_models() is deprecated. "
            "Declare models in modules/<name>/manifest.py → AppManifest(models=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self
    
    def register_serializers(self, *serializers: str) -> "Module":
        """DEPRECATED -- declare serializers in modules/*/manifest.py instead."""
        import warnings
        warnings.warn(
            "Module.register_serializers() is deprecated. "
            "Declare serializers in modules/<name>/manifest.py → AppManifest(serializers=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self
    
    def on_startup(self, hook: str) -> "Module":
        """
        Register a startup hook for this module.
        
        Args:
            hook: Import path to a callable in "module:func" format.
        """
        self._config.on_startup = hook
        return self
        
    def on_shutdown(self, hook: str) -> "Module":
        """
        Register a shutdown hook for this module.
        
        Args:
            hook: Import path to a callable in "module:func" format.
        """
        self._config.on_shutdown = hook
        return self
    
    def database(
        self,
        url: Optional[str] = None,
        *,
        config: Optional[Any] = None,
        auto_connect: bool = True,
        auto_create: bool = True,
        auto_migrate: bool = False,
        migrations_dir: str = "migrations",
        **kwargs,
    ) -> "Module":
        """
        Configure database for this module.
        
        Accepts either a URL string or a typed DatabaseConfig object.
        
        Args:
            url: Database URL (backward compatible)
            config: Typed DatabaseConfig (SqliteConfig, PostgresConfig,
                    MysqlConfig, OracleConfig). Takes precedence over url.
            auto_connect: Connect on startup
            auto_create: Create tables automatically
            auto_migrate: Run pending migrations on startup
            migrations_dir: Migration files directory
            **kwargs: Additional database options
        """
        if config is not None:
            # Use typed config object
            db_dict = config.to_dict()
            db_dict.update({
                "auto_connect": auto_connect,
                "auto_create": auto_create,
                "auto_migrate": auto_migrate,
                "migrations_dir": migrations_dir,
            })
            db_dict.update(kwargs)
            self._config.database = db_dict
        else:
            self._config.database = {
                "url": url or "sqlite:///db.sqlite3",
                "auto_connect": auto_connect,
                "auto_create": auto_create,
                "auto_migrate": auto_migrate,
                "migrations_dir": migrations_dir,
                **kwargs,
            }
        return self
    
    def build(self) -> ModuleConfig:
        """Build module configuration."""
        return self._config


@dataclass
class AuthConfig:
    """Authentication configuration."""
    enabled: bool = True
    store_type: str = "memory"
    secret_key: Optional[str] = None  # MUST be set explicitly; no insecure default
    algorithm: str = "HS256"
    issuer: str = "aquilia"
    audience: str = "aquilia-app"
    access_token_ttl_minutes: int = 60
    refresh_token_ttl_days: int = 30
    require_auth_by_default: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format."""
        return {
            "enabled": self.enabled,
            "store": {
                "type": self.store_type,
            },
            "tokens": {
                "secret_key": self.secret_key,
                "algorithm": self.algorithm,
                "issuer": self.issuer,
                "audience": self.audience,
                "access_token_ttl_minutes": self.access_token_ttl_minutes,
                "refresh_token_ttl_days": self.refresh_token_ttl_days,
            },
            "security": {
                "require_auth_by_default": self.require_auth_by_default,
            }
        }


class Integration:
    """Integration configuration builders."""
    
    @staticmethod
    def auth(
        config: Optional[AuthConfig] = None,
        enabled: bool = True,
        store_type: str = "memory",
        secret_key: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Configure authentication.
        
        Args:
            config: AuthConfig object (optional)
            enabled: Enable authentication
            store_type: Store type (memory, etc.)
            secret_key: Secret key for tokens
            **kwargs: Overrides
            
        Returns:
            Auth configuration dictionary
        """
        if config:
            # Use provided config object
            conf_dict = config.to_dict()
        else:
            # Build from arguments using defaults from AuthConfig
            defaults = AuthConfig()
            conf_dict = {
                "enabled": enabled,
                "store": {
                    "type": store_type,
                },
                "tokens": {
                    "secret_key": secret_key or defaults.secret_key,  # None if not provided
                    "algorithm": defaults.algorithm,
                    "issuer": defaults.issuer,
                    "audience": defaults.audience,
                    "access_token_ttl_minutes": defaults.access_token_ttl_minutes,
                    "refresh_token_ttl_days": defaults.refresh_token_ttl_days,
                },
                "security": {
                    "require_auth_by_default": defaults.require_auth_by_default,
                }
            }
            
        # Apply kwargs overrides (deep merge logic simplified for common top-level overrides)
        # Note: A real deep merge might be better but for now we trust the structure
        conf_dict.update(kwargs)
        
        return conf_dict

    
    @staticmethod
    def sessions(
        policy: Optional[Any] = None,
        store: Optional[Any] = None,
        transport: Optional[Any] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Configure session integration with Aquilia's unique fluent syntax.
        
        Unique Features:
        - Chained policy builders: SessionPolicy.for_users().lasting(days=7).rotating_on_auth()
        - Smart defaults: Auto-configures based on environment
        - Policy templates: .web_users(), .api_tokens(), .mobile_apps()
        
        Args:
            policy: SessionPolicy instance or policy builder
            store: Store instance or store config
            transport: Transport instance or transport config
            **kwargs: Additional session configuration
            
        Returns:
            Session configuration dictionary
            
        Examples:
            # Unique Aquilia syntax:
            .integrate(Integration.sessions(
                policy=SessionPolicy.for_web_users()
                    .lasting(days=14)
                    .idle_timeout(hours=2)
                    .rotating_on_privilege_change()
                    .scoped_to("tenant"),
                store=MemoryStore.with_capacity(50000),
                transport=CookieTransport.secure_defaults()
            ))
            
            # Template syntax:
            .integrate(Integration.sessions.web_app())
            .integrate(Integration.sessions.api_service())
            .integrate(Integration.sessions.mobile_app())
        """
        from aquilia.sessions import SessionPolicy, MemoryStore, CookieTransport, TransportPolicy
        
        # Smart policy creation with Aquilia's unique builders
        if policy is None:
            policy = SessionPolicy.for_web_users().with_smart_defaults()
        
        # Smart store selection
        if store is None:
            store = MemoryStore.optimized_for_development()
        
        # Smart transport with security defaults
        if transport is None:
            if hasattr(policy, 'transport') and policy.transport:
                transport = CookieTransport.from_policy(policy.transport)
            else:
                transport = CookieTransport.with_aquilia_defaults()
        
        return {
            "enabled": True,
            "policy": policy,
            "store": store,
            "transport": transport,
            "aquilia_syntax_version": "2.0",  # Mark as enhanced syntax
            **kwargs
        }
    
    @staticmethod
    def di(auto_wire: bool = True, **kwargs) -> Dict[str, Any]:
        """Configure dependency injection."""
        return {
            "enabled": True,
            "auto_wire": auto_wire,
            **kwargs
        }
    
    @staticmethod
    def database(
        url: Optional[str] = None,
        *,
        config: Optional[Any] = None,
        auto_connect: bool = True,
        auto_create: bool = True,
        auto_migrate: bool = False,
        migrations_dir: str = "migrations",
        pool_size: int = 5,
        echo: bool = False,
        model_paths: Optional[List[str]] = None,
        scan_dirs: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure database and AMDL model integration.
        
        Accepts either a URL string or a typed DatabaseConfig object for
        developer-friendly, IDE-assisted configuration.
        
        Args:
            url: Database URL (sqlite:///path, postgresql://..., etc.)
                 Ignored if config is provided.
            config: Typed DatabaseConfig object. Supported types:
                    - SqliteConfig
                    - PostgresConfig
                    - MysqlConfig
                    - OracleConfig
                    Takes precedence over url.
            auto_connect: Connect database on server startup
            auto_create: Automatically create tables from discovered models
            auto_migrate: Run pending migrations on startup
            migrations_dir: Directory for migration files
            pool_size: Connection pool size
            echo: Log SQL statements
            model_paths: Explicit .amdl file paths
            scan_dirs: Directories to scan for .amdl files
            **kwargs: Additional database options
        
        Returns:
            Database configuration dictionary
            
        Examples:
            # URL-based (backward compatible):
            .integrate(Integration.database(
                url="sqlite:///app.db",
                auto_create=True,
            ))
            
            # Config-based (recommended):
            from aquilia.db.configs import PostgresConfig
            .integrate(Integration.database(
                config=PostgresConfig(
                    host="localhost",
                    port=5432,
                    name="mydb",
                    user="admin",
                    password="secret",
                ),
                pool_size=10,
                auto_create=True,
                scan_dirs=["models", "modules/*/models"],
            ))
            
            # Oracle:
            from aquilia.db.configs import OracleConfig
            .integrate(Integration.database(
                config=OracleConfig(
                    host="oracle.example.com",
                    service_name="PROD",
                    user="app",
                    password="secret",
                ),
            ))
        """
        if config is not None:
            # Merge typed config with overrides
            result = config.to_dict()
            result.update({
                "auto_connect": auto_connect,
                "auto_create": auto_create,
                "auto_migrate": auto_migrate,
                "migrations_dir": migrations_dir,
                "pool_size": pool_size,
                "echo": echo,
                "model_paths": model_paths or [],
                "scan_dirs": scan_dirs or ["models"],
            })
            result.update(kwargs)
            return result
        
        return {
            "enabled": True,
            "url": url or "sqlite:///db.sqlite3",
            "auto_connect": auto_connect,
            "auto_create": auto_create,
            "auto_migrate": auto_migrate,
            "migrations_dir": migrations_dir,
            "pool_size": pool_size,
            "echo": echo,
            "model_paths": model_paths or [],
            "scan_dirs": scan_dirs or ["models"],
            **kwargs,
        }
    
    # ========================================================================
    # Unique Aquilia Session Templates
    # ========================================================================
    
    class sessions:
        """Unique Aquilia session configuration templates."""
        
        @staticmethod
        def web_app(**overrides) -> Dict[str, Any]:
            """Optimized for web applications with users."""
            from aquilia.sessions import SessionPolicy, MemoryStore, CookieTransport
            
            policy = SessionPolicy.for_web_users().lasting(days=7).idle_timeout(hours=2).web_defaults().build()
            store = MemoryStore.web_optimized()
            transport = CookieTransport.for_web_browsers()
            
            return {
                "enabled": True,
                "policy": policy,
                "store": store,
                "transport": transport,
                "aquilia_syntax_version": "2.0",
                **overrides
            }
        
        @staticmethod
        def api_service(**overrides) -> Dict[str, Any]:
            """Optimized for API services with token-based auth."""
            from aquilia.sessions import SessionPolicy, MemoryStore, HeaderTransport
            
            policy = SessionPolicy.for_api_tokens().lasting(hours=1).no_idle_timeout().api_defaults().build()
            store = MemoryStore.api_optimized()
            transport = HeaderTransport.for_rest_apis()
            
            return {
                "enabled": True,
                "policy": policy,
                "store": store,
                "transport": transport,
                "aquilia_syntax_version": "2.0",
                **overrides
            }
        
        @staticmethod  
        def mobile_app(**overrides) -> Dict[str, Any]:
            """Optimized for mobile applications with long-lived sessions."""
            from aquilia.sessions import SessionPolicy, MemoryStore, CookieTransport
            
            policy = SessionPolicy.for_mobile_users().lasting(days=90).idle_timeout(days=30).mobile_defaults().build()
            store = MemoryStore.mobile_optimized()
            transport = CookieTransport.for_mobile_webviews()
            
            return {
                "enabled": True,
                "policy": policy,
                "store": store,
                "transport": transport,
                "aquilia_syntax_version": "2.0",
                **overrides
            }
    
    @staticmethod
    def registry(**kwargs) -> Dict[str, Any]:
        """Configure registry."""
        return {
            "enabled": True,
            **kwargs
        }
    
    @staticmethod
    def routing(strict_matching: bool = True, **kwargs) -> Dict[str, Any]:
        """Configure routing."""
        return {
            "enabled": True,
            "strict_matching": strict_matching,
            **kwargs
        }
    
    @staticmethod
    def fault_handling(default_strategy: str = "propagate", **kwargs) -> Dict[str, Any]:
        """Configure fault handling."""
        return {
            "enabled": True,
            "default_strategy": default_strategy,
            **kwargs
        }
    
    class templates:
        """
        Fluent template configuration builder.
        
        Unique Syntax:
            Integration.templates.source("...").secure().cached()
        """
        
        class Builder(dict):
            """Fluent builder inheriting from dict for compatibility."""
            
            def __init__(self, defaults: Optional[Dict] = None):
                super().__init__(defaults or {
                    "enabled": True,
                    "search_paths": ["templates"],
                    "cache": "memory",
                    "sandbox": True,
                    "precompile": False,
                })
                
            def source(self, *paths: str) -> "Integration.templates.Builder":
                """Add template search paths."""
                current = self.get("search_paths", [])
                if current == ["templates"]:  # Replace default
                    current = []
                self["search_paths"] = current + list(paths)
                return self
                
            def scan_modules(self) -> "Integration.templates.Builder":
                """Enable module auto-discovery."""
                # This is implicit in server logic but good for intent
                return self
                
            def cached(self, strategy: str = "memory") -> "Integration.templates.Builder":
                """Enable bytecode caching."""
                self["cache"] = strategy
                return self
                
            def secure(self, strict: bool = True) -> "Integration.templates.Builder":
                """Enable sandbox with security policy."""
                self["sandbox"] = True
                self["sandbox_policy"] = "strict" if strict else "permissive"
                return self
                
            def unsafe_dev_mode(self) -> "Integration.templates.Builder":
                """Disable sandbox/caching for development."""
                self["sandbox"] = False
                self["cache"] = "none"
                return self
                
            def precompile(self) -> "Integration.templates.Builder":
                """Enable startup precompilation."""
                self["precompile"] = True
                return self
        
        @classmethod
        def source(cls, *paths: str) -> "Integration.templates.Builder":
            """Start builder with source paths."""
            return cls.Builder().source(*paths)
            
        @classmethod
        def defaults(cls) -> "Integration.templates.Builder":
            """Start with default configuration."""
            return cls.Builder()

    @staticmethod
    def cache(
        backend: str = "memory",
        default_ttl: int = 300,
        max_size: int = 10000,
        eviction_policy: str = "lru",
        namespace: str = "default",
        key_prefix: str = "aq:",
        serializer: str = "json",
        redis_url: str = "redis://localhost:6379/0",
        redis_max_connections: int = 10,
        l1_max_size: int = 1000,
        l1_ttl: int = 60,
        l2_backend: str = "redis",
        middleware_enabled: bool = False,
        middleware_default_ttl: int = 60,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure the caching subsystem.

        Supports memory (LRU/LFU), Redis, composite (L1+L2), and null
        backends with pluggable serialization and middleware.

        Args:
            backend: Backend type -- ``"memory"``, ``"redis"``,
                     ``"composite"``, or ``"null"``.
            default_ttl: Default time-to-live in seconds.
            max_size: Maximum entries for memory backend.
            eviction_policy: ``"lru"``, ``"lfu"``, ``"fifo"``, ``"ttl"``,
                             or ``"random"``.
            namespace: Default namespace for key isolation.
            key_prefix: Global key prefix.
            serializer: ``"json"``, ``"pickle"``, or ``"msgpack"``.
            redis_url: Redis connection URL.
            redis_max_connections: Redis connection pool size.
            l1_max_size: L1 (memory) size for composite backend.
            l1_ttl: L1 TTL for composite backend.
            l2_backend: L2 backend for composite (``"redis"``).
            middleware_enabled: Enable HTTP response caching middleware.
            middleware_default_ttl: Response cache TTL.
            **kwargs: Additional overrides.

        Returns:
            Cache configuration dictionary.

        Examples::

            # Simple in-memory LRU cache
            .integrate(Integration.cache())

            # Redis backend
            .integrate(Integration.cache(
                backend="redis",
                redis_url="redis://cache.internal:6379/0",
                default_ttl=600,
            ))

            # Two-level composite cache
            .integrate(Integration.cache(
                backend="composite",
                l1_max_size=500,
                l1_ttl=30,
                redis_url="redis://localhost:6379/0",
            ))
        """
        return {
            "_integration_type": "cache",
            "enabled": True,
            "backend": backend,
            "default_ttl": default_ttl,
            "max_size": max_size,
            "eviction_policy": eviction_policy,
            "namespace": namespace,
            "key_prefix": key_prefix,
            "serializer": serializer,
            "redis_url": redis_url,
            "redis_max_connections": redis_max_connections,
            "l1_max_size": l1_max_size,
            "l1_ttl": l1_ttl,
            "l2_backend": l2_backend,
            "middleware_enabled": middleware_enabled,
            "middleware_default_ttl": middleware_default_ttl,
            **kwargs,
        }

    @staticmethod
    def tasks(
        backend: str = "memory",
        num_workers: int = 4,
        default_queue: str = "default",
        cleanup_interval: float = 300.0,
        cleanup_max_age: float = 3600.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        retry_backoff: float = 2.0,
        retry_max_delay: float = 300.0,
        default_timeout: float = 300.0,
        auto_start: bool = True,
        dead_letter_max: int = 1000,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure the background task subsystem.

        Provides an async-native task queue with priority scheduling,
        retry with exponential backoff, dead-letter handling, and
        admin dashboard integration.

        Args:
            backend: Backend type -- ``"memory"`` (default) or
                     ``"redis"`` (future).
            num_workers: Number of concurrent worker coroutines.
            default_queue: Default queue name for tasks without
                           explicit queue assignment.
            cleanup_interval: Seconds between old job cleanup sweeps.
            cleanup_max_age: Max age (seconds) for terminal jobs
                             before cleanup removes them.
            max_retries: Default max retry attempts for tasks.
            retry_delay: Default base retry delay in seconds.
            retry_backoff: Exponential backoff multiplier.
            retry_max_delay: Maximum retry delay cap.
            default_timeout: Default task execution timeout.
            auto_start: Start workers automatically on server boot.
            dead_letter_max: Maximum dead-letter queue size.
            **kwargs: Additional overrides.

        Returns:
            Tasks configuration dictionary.

        Examples::

            # Default in-memory task queue
            .integrate(Integration.tasks())

            # Custom worker pool
            .integrate(Integration.tasks(
                num_workers=8,
                default_timeout=600,
                max_retries=5,
            ))
        """
        return {
            "_integration_type": "tasks",
            "enabled": True,
            "backend": backend,
            "num_workers": num_workers,
            "default_queue": default_queue,
            "cleanup_interval": cleanup_interval,
            "cleanup_max_age": cleanup_max_age,
            "max_retries": max_retries,
            "retry_delay": retry_delay,
            "retry_backoff": retry_backoff,
            "retry_max_delay": retry_max_delay,
            "default_timeout": default_timeout,
            "auto_start": auto_start,
            "dead_letter_max": dead_letter_max,
            **kwargs,
        }

    # ── Admin Nested Builder Classes ──────────────────────────────────
    #
    # IDE-friendly, type-safe configuration objects for the admin panel.
    # Each sub-config is a small fluent builder that produces a typed dict.
    # Developers get autocomplete, doc-strings, and compile-time safety.
    #
    # Usage::
    #
    #     .integrate(Integration.admin(
    #         site_title="MyApp Admin",
    #         modules=(
    #             Integration.AdminModules()
    #             .enable_dashboard()
    #             .enable_orm()
    #             .disable_build()
    #             .disable_migrations()
    #         ),
    #         audit=(
    #             Integration.AdminAudit()
    #             .enable()
    #             .log_logins()
    #             .exclude_actions("VIEW", "LIST")
    #         ),
    #         monitoring=(
    #             Integration.AdminMonitoring()
    #             .enable()
    #             .metrics("cpu", "memory", "system")
    #             .refresh_interval(15)
    #         ),
    #         sidebar=(
    #             Integration.AdminSidebar()
    #             .show_overview()
    #             .show_data()
    #             .hide_security()
    #         ),
    #     ))

    class AdminModules:
        """
        Fluent builder for admin module visibility.

        Controls which pages are visible in the admin panel.
        All modules default to enabled except monitoring and audit
        (which must be explicitly opted-in).

        Example::

            modules = (
                Integration.AdminModules()
                .enable_orm()
                .enable_monitoring()   # Opt-in
                .disable_build()
            )
        """

        __slots__ = ("_dashboard", "_orm", "_build", "_migrations",
                     "_config", "_workspace", "_permissions",
                     "_monitoring", "_admin_users", "_profile", "_audit",
                     "_containers", "_pods",
                     "_query_inspector", "_tasks", "_errors")

        def __init__(self) -> None:
            self._dashboard: bool = True
            self._orm: bool = True
            self._build: bool = True
            self._migrations: bool = True
            self._config: bool = True
            self._workspace: bool = True
            self._permissions: bool = True
            self._monitoring: bool = False   # disabled by default
            self._admin_users: bool = True
            self._profile: bool = True
            self._audit: bool = False         # disabled by default
            self._containers: bool = False    # disabled by default
            self._pods: bool = False           # disabled by default
            self._query_inspector: bool = False  # disabled by default
            self._tasks: bool = False             # disabled by default
            self._errors: bool = False            # disabled by default

        # ── Dashboard ──
        def enable_dashboard(self) -> "Integration.AdminModules":
            """Show the Dashboard page."""
            self._dashboard = True
            return self

        def disable_dashboard(self) -> "Integration.AdminModules":
            """Hide the Dashboard page."""
            self._dashboard = False
            return self

        # ── ORM ──
        def enable_orm(self) -> "Integration.AdminModules":
            """Show the ORM Models page."""
            self._orm = True
            return self

        def disable_orm(self) -> "Integration.AdminModules":
            """Hide the ORM Models page."""
            self._orm = False
            return self

        # ── Build ──
        def enable_build(self) -> "Integration.AdminModules":
            """Show the Build page."""
            self._build = True
            return self

        def disable_build(self) -> "Integration.AdminModules":
            """Hide the Build page."""
            self._build = False
            return self

        # ── Migrations ──
        def enable_migrations(self) -> "Integration.AdminModules":
            """Show the Migrations page."""
            self._migrations = True
            return self

        def disable_migrations(self) -> "Integration.AdminModules":
            """Hide the Migrations page."""
            self._migrations = False
            return self

        # ── Config ──
        def enable_config(self) -> "Integration.AdminModules":
            """Show the Configuration page."""
            self._config = True
            return self

        def disable_config(self) -> "Integration.AdminModules":
            """Hide the Configuration page."""
            self._config = False
            return self

        # ── Workspace ──
        def enable_workspace(self) -> "Integration.AdminModules":
            """Show the Workspace page."""
            self._workspace = True
            return self

        def disable_workspace(self) -> "Integration.AdminModules":
            """Hide the Workspace page."""
            self._workspace = False
            return self

        # ── Permissions ──
        def enable_permissions(self) -> "Integration.AdminModules":
            """Show the Permissions page."""
            self._permissions = True
            return self

        def disable_permissions(self) -> "Integration.AdminModules":
            """Hide the Permissions page."""
            self._permissions = False
            return self

        # ── Monitoring (disabled by default) ──
        def enable_monitoring(self) -> "Integration.AdminModules":
            """Show the Monitoring page. Disabled by default -- opt in."""
            self._monitoring = True
            return self

        def disable_monitoring(self) -> "Integration.AdminModules":
            """Hide the Monitoring page."""
            self._monitoring = False
            return self

        # ── Admin Users ──
        def enable_admin_users(self) -> "Integration.AdminModules":
            """Show the Admin Users page."""
            self._admin_users = True
            return self

        def disable_admin_users(self) -> "Integration.AdminModules":
            """Hide the Admin Users page."""
            self._admin_users = False
            return self

        # ── Profile ──
        def enable_profile(self) -> "Integration.AdminModules":
            """Show the Profile page."""
            self._profile = True
            return self

        def disable_profile(self) -> "Integration.AdminModules":
            """Hide the Profile page."""
            self._profile = False
            return self

        # ── Containers ──
        def enable_containers(self) -> "Integration.AdminModules":
            """Show the Containers page (Docker containers, compose, images)."""
            self._containers = True
            return self

        def disable_containers(self) -> "Integration.AdminModules":
            """Hide the Containers page."""
            self._containers = False
            return self

        # ── Pods ──
        def enable_pods(self) -> "Integration.AdminModules":
            """Show the Pods page (Kubernetes pods, deployments, services)."""
            self._pods = True
            return self

        def disable_pods(self) -> "Integration.AdminModules":
            """Hide the Pods page."""
            self._pods = False
            return self

        # ── Audit (disabled by default) ──
        def enable_audit(self) -> "Integration.AdminModules":
            """Show the Audit Log page. Disabled by default -- opt in."""
            self._audit = True
            return self

        def disable_audit(self) -> "Integration.AdminModules":
            """Hide the Audit Log page."""
            self._audit = False
            return self

        # ── Query Inspector (disabled by default) ──
        def enable_query_inspector(self) -> "Integration.AdminModules":
            """Show the Query Inspector page (SQL profiling, N+1 detection). Disabled by default -- opt in."""
            self._query_inspector = True
            return self

        def disable_query_inspector(self) -> "Integration.AdminModules":
            """Hide the Query Inspector page."""
            self._query_inspector = False
            return self

        # ── Background Tasks (disabled by default) ──
        def enable_tasks(self) -> "Integration.AdminModules":
            """Show the Background Tasks page. Disabled by default -- opt in."""
            self._tasks = True
            return self

        def disable_tasks(self) -> "Integration.AdminModules":
            """Hide the Background Tasks page."""
            self._tasks = False
            return self

        # ── Error Monitoring (disabled by default) ──
        def enable_errors(self) -> "Integration.AdminModules":
            """Show the Error Monitoring page. Disabled by default -- opt in."""
            self._errors = True
            return self

        def disable_errors(self) -> "Integration.AdminModules":
            """Hide the Error Monitoring page."""
            self._errors = False
            return self

        # ── Convenience ──
        def enable_all(self) -> "Integration.AdminModules":
            """Enable every admin module (including monitoring & audit)."""
            for attr in self.__slots__:
                setattr(self, attr, True)
            return self

        def disable_all(self) -> "Integration.AdminModules":
            """Disable every admin module."""
            for attr in self.__slots__:
                setattr(self, attr, False)
            return self

        def to_dict(self) -> Dict[str, bool]:
            """Serialize to a dict consumed by AdminConfig."""
            return {
                "dashboard": self._dashboard,
                "orm": self._orm,
                "build": self._build,
                "migrations": self._migrations,
                "config": self._config,
                "workspace": self._workspace,
                "permissions": self._permissions,
                "monitoring": self._monitoring,
                "admin_users": self._admin_users,
                "profile": self._profile,
                "audit": self._audit,
                "containers": self._containers,
                "pods": self._pods,
                "query_inspector": self._query_inspector,
                "tasks": self._tasks,
                "errors": self._errors,
            }

        def __repr__(self) -> str:
            enabled = [k for k, v in self.to_dict().items() if v]
            return f"AdminModules(enabled={enabled})"

    class AdminAudit:
        """
        Fluent builder for admin audit log configuration.

        Controls whether the audit trail is active, which action
        categories are recorded, and which specific actions are
        excluded.

        **Disabled by default** -- call ``.enable()`` to activate.

        Example::

            audit = (
                Integration.AdminAudit()
                .enable()
                .max_entries(50_000)
                .log_logins()
                .no_log_views()            # skip VIEW / LIST
                .exclude_actions("SEARCH")
            )
        """

        __slots__ = ("_enabled", "_max_entries", "_log_logins",
                     "_log_views", "_log_searches", "_excluded_actions")

        def __init__(self) -> None:
            self._enabled: bool = False      # disabled by default
            self._max_entries: int = 10_000
            self._log_logins: bool = True
            self._log_views: bool = True
            self._log_searches: bool = True
            self._excluded_actions: List[str] = []

        def enable(self) -> "Integration.AdminAudit":
            """Enable audit logging."""
            self._enabled = True
            return self

        def disable(self) -> "Integration.AdminAudit":
            """Disable audit logging entirely."""
            self._enabled = False
            return self

        def max_entries(self, n: int) -> "Integration.AdminAudit":
            """Set the maximum number of audit entries (FIFO eviction)."""
            self._max_entries = max(100, int(n))
            return self

        def log_logins(self, enabled: bool = True) -> "Integration.AdminAudit":
            """Record LOGIN / LOGOUT / LOGIN_FAILED events."""
            self._log_logins = enabled
            return self

        def no_log_logins(self) -> "Integration.AdminAudit":
            """Skip LOGIN / LOGOUT / LOGIN_FAILED events."""
            self._log_logins = False
            return self

        def log_views(self, enabled: bool = True) -> "Integration.AdminAudit":
            """Record VIEW / LIST events."""
            self._log_views = enabled
            return self

        def no_log_views(self) -> "Integration.AdminAudit":
            """Skip VIEW / LIST events."""
            self._log_views = False
            return self

        def log_searches(self, enabled: bool = True) -> "Integration.AdminAudit":
            """Record SEARCH events."""
            self._log_searches = enabled
            return self

        def no_log_searches(self) -> "Integration.AdminAudit":
            """Skip SEARCH events."""
            self._log_searches = False
            return self

        def exclude_actions(self, *actions: str) -> "Integration.AdminAudit":
            """
            Exclude specific actions from audit logging.

            Valid values: ``"LOGIN"``, ``"LOGOUT"``, ``"LOGIN_FAILED"``,
            ``"VIEW"``, ``"LIST"``, ``"CREATE"``, ``"UPDATE"``,
            ``"DELETE"``, ``"BULK_ACTION"``, ``"EXPORT"``,
            ``"SETTINGS_CHANGE"``, ``"SEARCH"``, ``"PERMISSION_CHANGE"``.
            """
            self._excluded_actions = list(actions)
            return self

        def to_dict(self) -> Dict[str, Any]:
            """Serialize to a dict consumed by AdminConfig."""
            return {
                "enabled": self._enabled,
                "max_entries": self._max_entries,
                "log_logins": self._log_logins,
                "log_views": self._log_views,
                "log_searches": self._log_searches,
                "excluded_actions": list(self._excluded_actions),
            }

        def __repr__(self) -> str:
            state = "enabled" if self._enabled else "disabled"
            return f"AdminAudit({state})"

    class AdminMonitoring:
        """
        Fluent builder for admin monitoring configuration.

        Controls whether real-time system metrics are collected and
        which metric categories are shown in the dashboard.

        **Disabled by default** -- call ``.enable()`` to activate.

        Example::

            monitoring = (
                Integration.AdminMonitoring()
                .enable()
                .metrics("cpu", "memory", "system")
                .refresh_interval(15)
            )
        """

        _ALL_METRICS = [
            "cpu", "memory", "disk", "network",
            "process", "python", "system", "health_checks",
        ]

        __slots__ = ("_enabled", "_metrics", "_refresh_interval")

        def __init__(self) -> None:
            self._enabled: bool = False      # disabled by default
            self._metrics: List[str] = list(self._ALL_METRICS)
            self._refresh_interval: int = 30

        def enable(self) -> "Integration.AdminMonitoring":
            """Enable monitoring dashboard."""
            self._enabled = True
            return self

        def disable(self) -> "Integration.AdminMonitoring":
            """Disable monitoring dashboard."""
            self._enabled = False
            return self

        def metrics(self, *names: str) -> "Integration.AdminMonitoring":
            """
            Set which metric sections to collect.

            Valid values: ``"cpu"``, ``"memory"``, ``"disk"``,
            ``"network"``, ``"process"``, ``"python"``, ``"system"``,
            ``"health_checks"``.

            Pass no arguments to collect all metrics.
            """
            self._metrics = list(names) if names else list(self._ALL_METRICS)
            return self

        def all_metrics(self) -> "Integration.AdminMonitoring":
            """Collect every available metric."""
            self._metrics = list(self._ALL_METRICS)
            return self

        def refresh_interval(self, seconds: int) -> "Integration.AdminMonitoring":
            """Auto-refresh interval for the monitoring dashboard (min 5s)."""
            self._refresh_interval = max(5, int(seconds))
            return self

        def to_dict(self) -> Dict[str, Any]:
            """Serialize to a dict consumed by AdminConfig."""
            return {
                "enabled": self._enabled,
                "metrics": list(self._metrics),
                "refresh_interval": self._refresh_interval,
            }

        def __repr__(self) -> str:
            state = "enabled" if self._enabled else "disabled"
            return f"AdminMonitoring({state}, metrics={self._metrics})"

    class AdminSidebar:
        """
        Fluent builder for admin sidebar section visibility.

        Controls which sidebar sections are rendered. Individual modules
        within a section can still be hidden via ``AdminModules``.

        Example::

            sidebar = (
                Integration.AdminSidebar()
                .show_overview()
                .show_data()
                .hide_security()
            )
        """

        __slots__ = ("_overview", "_data", "_system", "_infrastructure", "_security", "_models", "_devtools")

        def __init__(self) -> None:
            self._overview: bool = True
            self._data: bool = True
            self._system: bool = True
            self._infrastructure: bool = True
            self._security: bool = True
            self._models: bool = True
            self._devtools: bool = True

        def show_overview(self) -> "Integration.AdminSidebar":
            """Show the Overview section."""
            self._overview = True
            return self

        def hide_overview(self) -> "Integration.AdminSidebar":
            """Hide the Overview section."""
            self._overview = False
            return self

        def show_data(self) -> "Integration.AdminSidebar":
            """Show the Data section (ORM, Migrations)."""
            self._data = True
            return self

        def hide_data(self) -> "Integration.AdminSidebar":
            """Hide the Data section."""
            self._data = False
            return self

        def show_system(self) -> "Integration.AdminSidebar":
            """Show the System section (Monitoring, Workspace, Build, Config)."""
            self._system = True
            return self

        def hide_system(self) -> "Integration.AdminSidebar":
            """Hide the System section."""
            self._system = False
            return self

        def show_infrastructure(self) -> "Integration.AdminSidebar":
            """Show the Infrastructure section (Containers, Pods)."""
            self._infrastructure = True
            return self

        def hide_infrastructure(self) -> "Integration.AdminSidebar":
            """Hide the Infrastructure section."""
            self._infrastructure = False
            return self

        def show_security(self) -> "Integration.AdminSidebar":
            """Show the Security section (Permissions, Audit, Admin Users)."""
            self._security = True
            return self

        def hide_security(self) -> "Integration.AdminSidebar":
            """Hide the Security section."""
            self._security = False
            return self

        def show_models(self) -> "Integration.AdminSidebar":
            """Show the Models section (per-model links)."""
            self._models = True
            return self

        def hide_models(self) -> "Integration.AdminSidebar":
            """Hide the Models section."""
            self._models = False
            return self

        def show_devtools(self) -> "Integration.AdminSidebar":
            """Show the DevTools section (Query Inspector, Tasks, Errors)."""
            self._devtools = True
            return self

        def hide_devtools(self) -> "Integration.AdminSidebar":
            """Hide the DevTools section."""
            self._devtools = False
            return self

        def show_all(self) -> "Integration.AdminSidebar":
            """Show every sidebar section."""
            for attr in self.__slots__:
                setattr(self, attr, True)
            return self

        def hide_all(self) -> "Integration.AdminSidebar":
            """Hide every sidebar section."""
            for attr in self.__slots__:
                setattr(self, attr, False)
            return self

        def to_dict(self) -> Dict[str, bool]:
            """Serialize to a dict consumed by AdminConfig."""
            return {
                "overview": self._overview,
                "data": self._data,
                "system": self._system,
                "infrastructure": self._infrastructure,
                "security": self._security,
                "models": self._models,
                "devtools": self._devtools,
            }

        def __repr__(self) -> str:
            visible = [k for k, v in self.to_dict().items() if v]
            return f"AdminSidebar(visible={visible})"

    class AdminContainers:
        """
        Fluent builder for admin Containers (Docker) page configuration.

        Controls Docker integration behaviour: socket path, allowed
        lifecycle actions, log tail limits, auto-refresh intervals,
        and compose file discovery.

        **Disabled by default** — opt in via ``AdminModules.enable_containers()``.

        Example::

            containers = (
                Integration.AdminContainers()
                .docker_socket("/var/run/docker.sock")
                .allowed_actions("start", "stop", "restart", "logs")
                .log_tail(500)
                .refresh_interval(10)
                .compose_files("docker-compose.yml", "docker-compose.prod.yml")
            )
        """

        __slots__ = (
            "_docker_host", "_allowed_actions", "_denied_actions",
            "_log_tail", "_log_since", "_refresh_interval",
            "_compose_files", "_compose_project_dir",
            "_show_system_containers", "_enable_exec",
            "_enable_prune", "_enable_build", "_enable_export",
            "_enable_image_actions", "_enable_volume_actions",
            "_enable_network_actions",
        )

        _ALL_ACTIONS = [
            "start", "stop", "restart", "pause", "unpause",
            "kill", "rm", "logs", "inspect", "exec", "export",
        ]

        def __init__(self) -> None:
            self._docker_host: Optional[str] = None   # None = auto-detect
            self._allowed_actions: List[str] = list(self._ALL_ACTIONS)
            self._denied_actions: List[str] = []
            self._log_tail: int = 200
            self._log_since: str = ""
            self._refresh_interval: int = 15
            self._compose_files: List[str] = []
            self._compose_project_dir: Optional[str] = None
            self._show_system_containers: bool = False
            self._enable_exec: bool = True
            self._enable_prune: bool = True
            self._enable_build: bool = True
            self._enable_export: bool = True
            self._enable_image_actions: bool = True
            self._enable_volume_actions: bool = True
            self._enable_network_actions: bool = True

        def docker_host(self, host: str) -> "Integration.AdminContainers":
            """Set Docker host (e.g. ``unix:///var/run/docker.sock`` or ``tcp://host:2375``)."""
            self._docker_host = host
            return self

        def docker_socket(self, path: str) -> "Integration.AdminContainers":
            """Shorthand for ``docker_host('unix://<path>')``."""
            self._docker_host = f"unix://{path}"
            return self

        def allowed_actions(self, *actions: str) -> "Integration.AdminContainers":
            """Set which container lifecycle actions are permitted."""
            self._allowed_actions = list(actions)
            return self

        def deny_actions(self, *actions: str) -> "Integration.AdminContainers":
            """Deny specific actions (subtracted from allowed)."""
            self._denied_actions = list(actions)
            return self

        def log_tail(self, lines: int) -> "Integration.AdminContainers":
            """Default number of log lines to fetch (default 200)."""
            self._log_tail = max(10, int(lines))
            return self

        def log_since(self, since: str) -> "Integration.AdminContainers":
            """Default ``--since`` value for log fetching (e.g. ``'1h'``, ``'30m'``)."""
            self._log_since = since
            return self

        def refresh_interval(self, seconds: int) -> "Integration.AdminContainers":
            """Auto-refresh interval for container metrics (min 5s)."""
            self._refresh_interval = max(5, int(seconds))
            return self

        def compose_files(self, *files: str) -> "Integration.AdminContainers":
            """Explicit compose file paths to discover."""
            self._compose_files = list(files)
            return self

        def compose_project_dir(self, path: str) -> "Integration.AdminContainers":
            """Set the compose project directory."""
            self._compose_project_dir = path
            return self

        def show_system_containers(self, enabled: bool = True) -> "Integration.AdminContainers":
            """Show Docker system / infra containers (hidden by default)."""
            self._show_system_containers = enabled
            return self

        def enable_exec(self, enabled: bool = True) -> "Integration.AdminContainers":
            """Allow ``docker exec`` from the admin UI."""
            self._enable_exec = enabled
            return self

        def disable_exec(self) -> "Integration.AdminContainers":
            """Disable ``docker exec`` in the admin UI."""
            self._enable_exec = False
            return self

        def enable_prune(self, enabled: bool = True) -> "Integration.AdminContainers":
            """Allow ``docker system prune`` from the admin UI."""
            self._enable_prune = enabled
            return self

        def disable_prune(self) -> "Integration.AdminContainers":
            """Disable prune operations."""
            self._enable_prune = False
            return self

        def enable_build(self, enabled: bool = True) -> "Integration.AdminContainers":
            """Allow ``docker build`` / ``compose build`` from the admin UI."""
            self._enable_build = enabled
            return self

        def disable_build(self) -> "Integration.AdminContainers":
            """Disable build operations."""
            self._enable_build = False
            return self

        def enable_export(self, enabled: bool = True) -> "Integration.AdminContainers":
            """Allow container filesystem export."""
            self._enable_export = enabled
            return self

        def disable_export(self) -> "Integration.AdminContainers":
            """Disable container export."""
            self._enable_export = False
            return self

        def enable_image_actions(self, enabled: bool = True) -> "Integration.AdminContainers":
            """Allow image pull / remove / tag operations."""
            self._enable_image_actions = enabled
            return self

        def disable_image_actions(self) -> "Integration.AdminContainers":
            """Disable image operations."""
            self._enable_image_actions = False
            return self

        def enable_volume_actions(self, enabled: bool = True) -> "Integration.AdminContainers":
            """Allow volume create / remove operations."""
            self._enable_volume_actions = enabled
            return self

        def disable_volume_actions(self) -> "Integration.AdminContainers":
            """Disable volume operations."""
            self._enable_volume_actions = False
            return self

        def enable_network_actions(self, enabled: bool = True) -> "Integration.AdminContainers":
            """Allow network create / remove operations."""
            self._enable_network_actions = enabled
            return self

        def disable_network_actions(self) -> "Integration.AdminContainers":
            """Disable network operations."""
            self._enable_network_actions = False
            return self

        def read_only(self) -> "Integration.AdminContainers":
            """Convenience -- disable all mutating operations."""
            self._allowed_actions = ["logs", "inspect"]
            self._enable_exec = False
            self._enable_prune = False
            self._enable_build = False
            self._enable_export = False
            self._enable_image_actions = False
            self._enable_volume_actions = False
            self._enable_network_actions = False
            return self

        def to_dict(self) -> Dict[str, Any]:
            """Serialize to a dict consumed by AdminConfig."""
            effective_actions = [
                a for a in self._allowed_actions
                if a not in self._denied_actions
            ]
            return {
                "docker_host": self._docker_host,
                "allowed_actions": effective_actions,
                "log_tail": self._log_tail,
                "log_since": self._log_since,
                "refresh_interval": self._refresh_interval,
                "compose_files": self._compose_files,
                "compose_project_dir": self._compose_project_dir,
                "show_system_containers": self._show_system_containers,
                "capabilities": {
                    "exec": self._enable_exec,
                    "prune": self._enable_prune,
                    "build": self._enable_build,
                    "export": self._enable_export,
                    "image_actions": self._enable_image_actions,
                    "volume_actions": self._enable_volume_actions,
                    "network_actions": self._enable_network_actions,
                },
            }

        def __repr__(self) -> str:
            return f"AdminContainers(host={self._docker_host!r}, refresh={self._refresh_interval}s)"

    class AdminPods:
        """
        Fluent builder for admin Pods (Kubernetes) page configuration.

        Controls kubectl integration behaviour: kubeconfig path,
        target namespace, allowed resource types, refresh intervals,
        and manifest file discovery.

        **Disabled by default** — opt in via ``AdminModules.enable_pods()``.

        Example::

            pods = (
                Integration.AdminPods()
                .kubeconfig("~/.kube/config")
                .namespace("production")
                .contexts("gke-prod", "gke-staging")
                .resources("pods", "deployments", "services", "ingresses")
                .manifest_dirs("k8s", "deploy/k8s")
                .refresh_interval(15)
            )
        """

        _ALL_RESOURCES = [
            "pods", "deployments", "services", "ingresses",
            "configmaps", "secrets", "namespaces", "events",
            "daemonsets", "statefulsets", "jobs", "cronjobs",
            "persistentvolumeclaims", "nodes",
        ]

        __slots__ = (
            "_kubeconfig", "_namespace", "_contexts",
            "_resources", "_manifest_dirs", "_manifest_patterns",
            "_refresh_interval", "_enable_logs", "_enable_exec",
            "_enable_delete", "_enable_scale", "_enable_restart",
            "_enable_apply", "_log_tail",
        )

        def __init__(self) -> None:
            self._kubeconfig: Optional[str] = None   # None = auto-detect
            self._namespace: str = "default"
            self._contexts: List[str] = []
            self._resources: List[str] = list(self._ALL_RESOURCES)
            self._manifest_dirs: List[str] = ["k8s"]
            self._manifest_patterns: List[str] = ["*.yaml", "*.yml"]
            self._refresh_interval: int = 15
            self._enable_logs: bool = True
            self._enable_exec: bool = True
            self._enable_delete: bool = True
            self._enable_scale: bool = True
            self._enable_restart: bool = True
            self._enable_apply: bool = True
            self._log_tail: int = 200

        def kubeconfig(self, path: str) -> "Integration.AdminPods":
            """Set path to kubeconfig file."""
            self._kubeconfig = path
            return self

        def namespace(self, ns: str) -> "Integration.AdminPods":
            """Set the target Kubernetes namespace (default ``"default"``)."""
            self._namespace = ns
            return self

        def all_namespaces(self) -> "Integration.AdminPods":
            """Query all namespaces."""
            self._namespace = "*"
            return self

        def contexts(self, *names: str) -> "Integration.AdminPods":
            """Set allowed kubectl contexts."""
            self._contexts = list(names)
            return self

        def resources(self, *types: str) -> "Integration.AdminPods":
            """Set which K8s resource types to display."""
            self._resources = list(types) if types else list(self._ALL_RESOURCES)
            return self

        def all_resources(self) -> "Integration.AdminPods":
            """Display every supported K8s resource type."""
            self._resources = list(self._ALL_RESOURCES)
            return self

        def manifest_dirs(self, *dirs: str) -> "Integration.AdminPods":
            """Set directories to scan for K8s manifest files."""
            self._manifest_dirs = list(dirs)
            return self

        def manifest_patterns(self, *patterns: str) -> "Integration.AdminPods":
            """Set glob patterns for manifest files (default ``*.yaml``, ``*.yml``)."""
            self._manifest_patterns = list(patterns)
            return self

        def refresh_interval(self, seconds: int) -> "Integration.AdminPods":
            """Auto-refresh interval for pod metrics (min 5s)."""
            self._refresh_interval = max(5, int(seconds))
            return self

        def log_tail(self, lines: int) -> "Integration.AdminPods":
            """Default number of log lines to fetch."""
            self._log_tail = max(10, int(lines))
            return self

        def enable_logs(self, enabled: bool = True) -> "Integration.AdminPods":
            """Allow pod log viewing."""
            self._enable_logs = enabled
            return self

        def enable_exec(self, enabled: bool = True) -> "Integration.AdminPods":
            """Allow ``kubectl exec`` from the admin UI."""
            self._enable_exec = enabled
            return self

        def disable_exec(self) -> "Integration.AdminPods":
            """Disable ``kubectl exec``."""
            self._enable_exec = False
            return self

        def enable_delete(self, enabled: bool = True) -> "Integration.AdminPods":
            """Allow resource deletion."""
            self._enable_delete = enabled
            return self

        def disable_delete(self) -> "Integration.AdminPods":
            """Disable resource deletion."""
            self._enable_delete = False
            return self

        def enable_scale(self, enabled: bool = True) -> "Integration.AdminPods":
            """Allow deployment scaling."""
            self._enable_scale = enabled
            return self

        def disable_scale(self) -> "Integration.AdminPods":
            """Disable deployment scaling."""
            self._enable_scale = False
            return self

        def enable_restart(self, enabled: bool = True) -> "Integration.AdminPods":
            """Allow deployment rollout restart."""
            self._enable_restart = enabled
            return self

        def disable_restart(self) -> "Integration.AdminPods":
            """Disable rollout restart."""
            self._enable_restart = False
            return self

        def enable_apply(self, enabled: bool = True) -> "Integration.AdminPods":
            """Allow ``kubectl apply -f`` from the admin UI."""
            self._enable_apply = enabled
            return self

        def disable_apply(self) -> "Integration.AdminPods":
            """Disable ``kubectl apply``."""
            self._enable_apply = False
            return self

        def read_only(self) -> "Integration.AdminPods":
            """Convenience -- disable all mutating operations."""
            self._enable_exec = False
            self._enable_delete = False
            self._enable_scale = False
            self._enable_restart = False
            self._enable_apply = False
            return self

        def to_dict(self) -> Dict[str, Any]:
            """Serialize to a dict consumed by AdminConfig."""
            return {
                "kubeconfig": self._kubeconfig,
                "namespace": self._namespace,
                "contexts": self._contexts,
                "resources": self._resources,
                "manifest_dirs": self._manifest_dirs,
                "manifest_patterns": self._manifest_patterns,
                "refresh_interval": self._refresh_interval,
                "log_tail": self._log_tail,
                "capabilities": {
                    "logs": self._enable_logs,
                    "exec": self._enable_exec,
                    "delete": self._enable_delete,
                    "scale": self._enable_scale,
                    "restart": self._enable_restart,
                    "apply": self._enable_apply,
                },
            }

        def __repr__(self) -> str:
            return f"AdminPods(ns={self._namespace!r}, refresh={self._refresh_interval}s)"

    @staticmethod
    def admin(
        url_prefix: str = "/admin",
        site_title: str = "Aquilia Admin",
        site_header: str = "Aquilia Administration",
        auto_discover: bool = True,
        login_url: Optional[str] = None,
        list_per_page: int = 25,
        theme: str = "auto",
        # ── Nested builder objects (IDE-friendly) ─────────────────
        modules: Optional["Integration.AdminModules"] = None,
        audit: Optional["Integration.AdminAudit"] = None,
        monitoring: Optional["Integration.AdminMonitoring"] = None,
        sidebar: Optional["Integration.AdminSidebar"] = None,
        containers: Optional["Integration.AdminContainers"] = None,
        pods: Optional["Integration.AdminPods"] = None,
        # ── Legacy flat params (backward compat) ─────────────────
        enable_audit: Optional[bool] = None,
        audit_max_entries: int = 10_000,
        enable_dashboard: Optional[bool] = None,
        enable_orm: Optional[bool] = None,
        enable_build: Optional[bool] = None,
        enable_migrations: Optional[bool] = None,
        enable_config: Optional[bool] = None,
        enable_workspace: Optional[bool] = None,
        enable_permissions: Optional[bool] = None,
        enable_monitoring: Optional[bool] = None,
        enable_admin_users: Optional[bool] = None,
        enable_containers: Optional[bool] = None,
        enable_pods: Optional[bool] = None,
        enable_profile: Optional[bool] = None,
        audit_log_logins: Optional[bool] = None,
        audit_log_views: Optional[bool] = None,
        audit_log_searches: Optional[bool] = None,
        audit_excluded_actions: Optional[List[str]] = None,
        monitoring_metrics: Optional[List[str]] = None,
        monitoring_refresh_interval: Optional[int] = None,
        sidebar_sections: Optional[Dict[str, bool]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure the admin dashboard integration.

        Accepts either **nested builder objects** (preferred, IDE-friendly)
        or legacy flat keyword arguments for backward compatibility.
        When both are provided, the builder object wins.

        **Default change (v2):** ``monitoring`` and ``audit`` are
        **disabled** by default. Use the builder or set
        ``enable_monitoring=True`` / ``enable_audit=True`` to opt in.
        Pages for disabled features show a beautiful blurred overlay
        prompting the developer to enable the feature in config.

        Args:
            url_prefix: URL prefix for admin routes (default "/admin").
            site_title: Title shown in browser tab.
            site_header: Header text in the admin dashboard.
            auto_discover: Auto-register models from ModelRegistry.
            login_url: Custom login URL.
            list_per_page: Default rows per page in list views.
            theme: ``"auto"``, ``"dark"``, or ``"light"``.
            modules: ``AdminModules`` builder -- controls page visibility.
            audit: ``AdminAudit`` builder -- controls audit logging.
            monitoring: ``AdminMonitoring`` builder -- controls metrics.
            sidebar: ``AdminSidebar`` builder -- controls sidebar sections.

        Returns:
            Admin configuration dictionary.

        Example -- **builder syntax** (recommended)::

            .integrate(Integration.admin(
                site_title="MyApp Admin",
                modules=(
                    Integration.AdminModules()
                    .enable_orm()
                    .enable_monitoring()     # opt-in
                    .disable_build()
                ),
                audit=(
                    Integration.AdminAudit()
                    .enable()                # opt-in
                    .no_log_views()
                    .exclude_actions("SEARCH")
                ),
                monitoring=(
                    Integration.AdminMonitoring()
                    .enable()                # opt-in
                    .metrics("cpu", "memory", "system")
                    .refresh_interval(15)
                ),
            ))

        Example -- **flat syntax** (legacy / quick)::

            .integrate(Integration.admin(
                site_title="MyApp Admin",
                enable_monitoring=True,
                enable_audit=True,
                audit_log_views=False,
                monitoring_metrics=["cpu", "memory"],
            ))
        """
        _all_metrics = [
            "cpu", "memory", "disk", "network",
            "process", "python", "system", "health_checks",
        ]

        # ── Resolve modules ──────────────────────────────────────────
        if modules is not None:
            mod_dict = modules.to_dict()
        else:
            # Build from legacy flat params (defaults: monitoring & audit OFF)
            mod_dict = {
                "dashboard": enable_dashboard if enable_dashboard is not None else True,
                "orm": enable_orm if enable_orm is not None else True,
                "build": enable_build if enable_build is not None else True,
                "migrations": enable_migrations if enable_migrations is not None else True,
                "config": enable_config if enable_config is not None else True,
                "workspace": enable_workspace if enable_workspace is not None else True,
                "permissions": enable_permissions if enable_permissions is not None else True,
                "monitoring": enable_monitoring if enable_monitoring is not None else False,
                "admin_users": enable_admin_users if enable_admin_users is not None else True,
                "profile": enable_profile if enable_profile is not None else True,
                "audit": enable_audit if enable_audit is not None else False,
                "containers": enable_containers if enable_containers is not None else False,
                "pods": enable_pods if enable_pods is not None else False,
                "query_inspector": kwargs.pop("enable_query_inspector", False),
                "tasks": kwargs.pop("enable_tasks", False),
                "errors": kwargs.pop("enable_errors", False),
            }

        # ── Resolve audit ────────────────────────────────────────────
        if audit is not None:
            audit_dict = audit.to_dict()
        else:
            _aud_enabled = enable_audit if enable_audit is not None else False
            audit_dict = {
                "enabled": _aud_enabled,
                "max_entries": int(audit_max_entries),
                "log_logins": audit_log_logins if audit_log_logins is not None else True,
                "log_views": audit_log_views if audit_log_views is not None else True,
                "log_searches": audit_log_searches if audit_log_searches is not None else True,
                "excluded_actions": list(audit_excluded_actions or []),
            }

        # Keep module audit flag in sync with audit_config.enabled
        # Only override if the audit builder was explicitly provided,
        # or if legacy flat enable_audit was given AND no modules builder.
        if audit is not None:
            mod_dict["audit"] = bool(audit_dict.get("enabled", mod_dict.get("audit", False)))
        elif modules is None and enable_audit is not None:
            mod_dict["audit"] = bool(audit_dict.get("enabled", mod_dict.get("audit", False)))

        # ── Resolve monitoring ───────────────────────────────────────
        if monitoring is not None:
            mon_dict = monitoring.to_dict()
        else:
            _mon_enabled = enable_monitoring if enable_monitoring is not None else False
            mon_dict = {
                "enabled": _mon_enabled,
                "metrics": list(monitoring_metrics) if monitoring_metrics else list(_all_metrics),
                "refresh_interval": max(5, int(monitoring_refresh_interval)) if monitoring_refresh_interval is not None else 30,
            }

        # Keep module monitoring flag in sync
        # Only override if the monitoring builder was explicitly provided,
        # or if legacy flat enable_monitoring was given AND no modules builder.
        if monitoring is not None:
            mod_dict["monitoring"] = bool(mon_dict.get("enabled", mod_dict.get("monitoring", False)))
        elif modules is None and enable_monitoring is not None:
            mod_dict["monitoring"] = bool(mon_dict.get("enabled", mod_dict.get("monitoring", False)))

        # ── Resolve sidebar ──────────────────────────────────────────
        if sidebar is not None:
            sidebar_dict = sidebar.to_dict()
        else:
            _default_sidebar = {
                "overview": True, "data": True, "system": True,
                "infrastructure": True, "security": True, "models": True,
                "devtools": True,
            }
            sidebar_dict = {**_default_sidebar}
            if sidebar_sections:
                for k, v in sidebar_sections.items():
                    if k in sidebar_dict:
                        sidebar_dict[k] = bool(v)

        # ── Resolve containers config ─────────────────────────────
        if containers is not None:
            containers_dict = containers.to_dict()
        else:
            containers_dict = {
                "docker_host": None,
                "allowed_actions": [
                    "start", "stop", "restart", "pause", "unpause",
                    "kill", "rm", "logs", "inspect", "exec", "export",
                ],
                "log_tail": 200,
                "log_since": "",
                "refresh_interval": 15,
                "compose_files": [],
                "compose_project_dir": None,
                "show_system_containers": False,
                "capabilities": {
                    "exec": True, "prune": True, "build": True,
                    "export": True, "image_actions": True,
                    "volume_actions": True, "network_actions": True,
                },
            }

        # ── Resolve pods config ──────────────────────────────────────
        if pods is not None:
            pods_dict = pods.to_dict()
        else:
            pods_dict = {
                "kubeconfig": None,
                "namespace": "default",
                "contexts": [],
                "resources": [
                    "pods", "deployments", "services", "ingresses",
                    "configmaps", "secrets", "namespaces", "events",
                    "daemonsets", "statefulsets", "jobs", "cronjobs",
                    "persistentvolumeclaims", "nodes",
                ],
                "manifest_dirs": ["k8s"],
                "manifest_patterns": ["*.yaml", "*.yml"],
                "refresh_interval": 15,
                "log_tail": 200,
                "capabilities": {
                    "logs": True, "exec": True, "delete": True,
                    "scale": True, "restart": True, "apply": True,
                },
            }

        return {
            "_integration_type": "admin",
            "enabled": True,
            "url_prefix": url_prefix.rstrip("/"),
            "site_title": site_title,
            "site_header": site_header,
            "auto_discover": auto_discover,
            "login_url": login_url or f"{url_prefix.rstrip('/')}/login",
            "enable_audit": audit_dict.get("enabled", False),
            "audit_max_entries": audit_dict.get("max_entries", 10_000),
            "list_per_page": list_per_page,
            "theme": theme,
            "modules": mod_dict,
            "audit_config": audit_dict,
            "monitoring_config": mon_dict,
            "containers_config": containers_dict,
            "pods_config": pods_dict,
            "sidebar_sections": sidebar_dict,
            **kwargs,
        }

    # ── Middleware Chain Builder ──────────────────────────────────────
    #
    # Industry-grade middleware configuration via path-based resolution.
    # Middleware classes are referenced by their dotted import path
    # (e.g. ``aquilia.middleware.RequestIdMiddleware``) so workspace.py
    # never imports framework internals directly.
    #
    # Usage::
    #
    #     .middleware(
    #         Integration.middleware.chain()
    #         .use("aquilia.middleware.ExceptionMiddleware", priority=1, debug=True)
    #         .use("aquilia.middleware.RequestIdMiddleware", priority=10)
    #         .use("aquilia.middleware.LoggingMiddleware",   priority=20)
    #     )
    #
    #     # Or use preset chains:
    #     .middleware(Integration.middleware.defaults())
    #     .middleware(Integration.middleware.production())
    #

    class middleware:
        """
        Middleware configuration builder.

        Provides path-based middleware resolution so workspace.py declares
        *what* middleware to run without importing framework internals.

        Middleware paths follow the ``aquilia.middleware.<Class>`` or
        ``aquilia.middleware_ext.<module>.<Class>`` convention.  Custom
        middleware uses full dotted paths (``myapp.middleware.RateLimiter``).
        """

        @dataclass
        class Entry:
            """A single middleware entry in the chain."""
            path: str
            priority: int = 50
            scope: str = "global"
            name: Optional[str] = None
            kwargs: Dict[str, Any] = field(default_factory=dict)

            def to_dict(self) -> Dict[str, Any]:
                return {
                    "path": self.path,
                    "priority": self.priority,
                    "scope": self.scope,
                    "name": self.name or self.path.rsplit(".", 1)[-1],
                    "kwargs": self.kwargs,
                }

        class Chain(list):
            """
            Fluent middleware chain builder.

            Each ``.use()`` call appends a middleware entry.  The chain
            serializes to a list of dicts consumed by the server at boot.

            Example::

                chain = (
                    Integration.middleware.chain()
                    .use("aquilia.middleware.ExceptionMiddleware", priority=1, debug=True)
                    .use("aquilia.middleware.RequestIdMiddleware", priority=10)
                    .use("aquilia.middleware.LoggingMiddleware",   priority=20)
                    .use("myapp.middleware.TenantMiddleware",      priority=30, header="X-Tenant-ID")
                )
            """

            def use(
                self,
                path: str,
                *,
                priority: int = 50,
                scope: str = "global",
                name: Optional[str] = None,
                **kwargs,
            ) -> "Integration.middleware.Chain":
                """
                Append a middleware to the chain.

                Args:
                    path: Dotted import path to the middleware class.
                          Examples:
                          - ``aquilia.middleware.ExceptionMiddleware``
                          - ``aquilia.middleware.RequestIdMiddleware``
                          - ``aquilia.middleware.LoggingMiddleware``
                          - ``aquilia.middleware.TimeoutMiddleware``
                          - ``aquilia.middleware.CORSMiddleware``
                          - ``aquilia.middleware.CompressionMiddleware``
                          - ``myapp.middleware.CustomMiddleware``
                    priority: Execution order (lower = runs first).
                    scope: ``"global"`` or ``"app:<name>"``.
                    name: Display name for debugging / introspection.
                    **kwargs: Constructor arguments forwarded to the
                              middleware class's ``__init__``.

                Returns:
                    Self for chaining.
                """
                entry = Integration.middleware.Entry(
                    path=path,
                    priority=priority,
                    scope=scope,
                    name=name,
                    kwargs=kwargs,
                )
                self.append(entry)
                return self

            def to_list(self) -> List[Dict[str, Any]]:
                """Serialize the chain to a config-compatible list."""
                return [e.to_dict() for e in self]

        @classmethod
        def chain(cls) -> "Integration.middleware.Chain":
            """Create an empty middleware chain."""
            return cls.Chain()

        @classmethod
        def defaults(cls) -> "Integration.middleware.Chain":
            """
            Standard development middleware chain.

            Includes:
            - ExceptionMiddleware (priority 1) -- catches errors, renders debug pages
            - RequestIdMiddleware (priority 10) -- adds X-Request-ID header
            """
            return (
                cls.chain()
                .use("aquilia.middleware.ExceptionMiddleware", priority=1)
                .use("aquilia.middleware.RequestIdMiddleware", priority=10)
            )

        @classmethod
        def production(cls) -> "Integration.middleware.Chain":
            """
            Production-grade middleware chain.

            Includes:
            - ExceptionMiddleware   (priority 1) -- error handling (debug=False)
            - RequestIdMiddleware   (priority 10) -- request tracing
            - CompressionMiddleware (priority 15) -- gzip response compression
            - TimeoutMiddleware     (priority 18) -- 30s request timeout
            """
            return (
                cls.chain()
                .use("aquilia.middleware.ExceptionMiddleware",   priority=1, debug=False)
                .use("aquilia.middleware.RequestIdMiddleware",   priority=10)
                .use("aquilia.middleware.CompressionMiddleware", priority=15, minimum_size=500)
                .use("aquilia.middleware.TimeoutMiddleware",     priority=18, timeout_seconds=30.0)
            )

        @classmethod
        def minimal(cls) -> "Integration.middleware.Chain":
            """
            Minimal middleware chain -- just error handling.

            Includes:
            - ExceptionMiddleware (priority 1)
            - RequestIdMiddleware (priority 10)
            """
            return (
                cls.chain()
                .use("aquilia.middleware.ExceptionMiddleware", priority=1)
                .use("aquilia.middleware.RequestIdMiddleware", priority=10)
            )

    @staticmethod
    def patterns(**kwargs) -> Dict[str, Any]:
        """Configure patterns."""
        return {
            "enabled": True,
            **kwargs
        }

    @staticmethod
    def static_files(
        directories: Optional[Dict[str, str]] = None,
        cache_max_age: int = 86400,
        immutable: bool = False,
        etag: bool = True,
        gzip: bool = True,
        brotli: bool = True,
        memory_cache: bool = True,
        html5_history: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure static file serving middleware.

        Args:
            directories: Mapping of URL prefix → filesystem directory.
                         Example: {"/static": "static", "/media": "uploads"}
            cache_max_age: Cache-Control max-age in seconds (default 1 day).
            immutable: Set Cache-Control: immutable for fingerprinted assets.
            etag: Enable ETag generation.
            gzip: Serve pre-compressed .gz files.
            brotli: Serve pre-compressed .br files.
            memory_cache: Enable in-memory LRU file cache.
            html5_history: Serve index.html for SPA 404s.

        Returns:
            Static files configuration dictionary.

        Example::

            .integrate(Integration.static_files(
                directories={"/static": "static", "/media": "uploads"},
                cache_max_age=86400,
                etag=True,
            ))
        """
        return {
            "_integration_type": "static_files",
            "enabled": True,
            "directories": directories or {"/static": "static"},
            "cache_max_age": cache_max_age,
            "immutable": immutable,
            "etag": etag,
            "gzip": gzip,
            "brotli": brotli,
            "memory_cache": memory_cache,
            "html5_history": html5_history,
            **kwargs,
        }

    @staticmethod
    def cors(
        allow_origins: Optional[List[str]] = None,
        allow_methods: Optional[List[str]] = None,
        allow_headers: Optional[List[str]] = None,
        expose_headers: Optional[List[str]] = None,
        allow_credentials: bool = False,
        max_age: int = 600,
        allow_origin_regex: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure CORS middleware.

        Args:
            allow_origins: Allowed origins (supports globs like "*.example.com").
            allow_methods: Allowed HTTP methods.
            allow_headers: Allowed request headers.
            expose_headers: Headers exposed to the browser.
            allow_credentials: Allow cookies / Authorization header.
            max_age: Preflight cache duration (seconds).
            allow_origin_regex: Regex pattern for origin matching.

        Returns:
            CORS configuration dictionary.

        Example::

            .integrate(Integration.cors(
                allow_origins=["https://example.com", "*.staging.example.com"],
                allow_credentials=True,
                max_age=3600,
            ))
        """
        return {
            "_integration_type": "cors",
            "enabled": True,
            "allow_origins": allow_origins or ["*"],
            "allow_methods": allow_methods or ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"],
            "allow_headers": allow_headers or ["accept", "accept-language", "content-language", "content-type", "authorization", "x-requested-with"],
            "expose_headers": expose_headers or [],
            "allow_credentials": allow_credentials,
            "max_age": max_age,
            "allow_origin_regex": allow_origin_regex,
            **kwargs,
        }

    @staticmethod
    def csp(
        policy: Optional[Dict[str, List[str]]] = None,
        report_only: bool = False,
        nonce: bool = True,
        preset: str = "strict",
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure Content-Security-Policy middleware.

        Args:
            policy: CSP directives dict (e.g. {"default-src": ["'self'"]}).
            report_only: Use Content-Security-Policy-Report-Only header.
            nonce: Enable per-request nonce generation.
            preset: "strict" or "relaxed" (used when policy is None).

        Returns:
            CSP configuration dictionary.

        Example::

            .integrate(Integration.csp(
                policy={
                    "default-src": ["'self'"],
                    "script-src": ["'self'", "'nonce-{nonce}'"],
                    "style-src": ["'self'", "'unsafe-inline'"],
                },
                nonce=True,
            ))
        """
        return {
            "_integration_type": "csp",
            "enabled": True,
            "policy": policy,
            "report_only": report_only,
            "nonce": nonce,
            "preset": preset,
            **kwargs,
        }

    @staticmethod
    def rate_limit(
        limit: int = 100,
        window: int = 60,
        algorithm: str = "sliding_window",
        per_user: bool = False,
        burst: Optional[int] = None,
        exempt_paths: Optional[List[str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure rate limiting middleware.

        Args:
            limit: Maximum requests per window.
            window: Window size in seconds.
            algorithm: "sliding_window" or "token_bucket".
            per_user: Use user identity as key (requires auth).
            burst: Extra burst capacity (token_bucket only).
            exempt_paths: Paths to skip rate limiting.

        Returns:
            Rate limit configuration dictionary.

        Example::

            .integrate(Integration.rate_limit(
                limit=200,
                window=60,
                algorithm="token_bucket",
                burst=50,
            ))
        """
        return {
            "_integration_type": "rate_limit",
            "enabled": True,
            "limit": limit,
            "window": window,
            "algorithm": algorithm,
            "per_user": per_user,
            "burst": burst,
            "exempt_paths": exempt_paths or ["/health", "/healthz", "/ready"],
            **kwargs,
        }

    @staticmethod
    def openapi(
        title: str = "Aquilia API",
        version: str = "1.0.0",
        description: str = "",
        terms_of_service: str = "",
        contact_name: str = "",
        contact_email: str = "",
        contact_url: str = "",
        license_name: str = "",
        license_url: str = "",
        servers: Optional[List[Dict[str, str]]] = None,
        docs_path: str = "/docs",
        openapi_json_path: str = "/openapi.json",
        redoc_path: str = "/redoc",
        include_internal: bool = False,
        group_by_module: bool = True,
        infer_request_body: bool = True,
        infer_responses: bool = True,
        detect_security: bool = True,
        external_docs_url: str = "",
        external_docs_description: str = "",
        swagger_ui_theme: str = "",
        swagger_ui_config: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure OpenAPI specification generation and interactive documentation.

        Enables automatic API documentation from controller metadata, type hints,
        and docstrings. Serves Swagger UI at ``docs_path`` and ReDoc at ``redoc_path``.

        Args:
            title: API title shown in documentation.
            version: API version string.
            description: Markdown description for the API overview.
            terms_of_service: URL to Terms of Service.
            contact_name: Maintainer / team name.
            contact_email: Contact email address.
            contact_url: Contact URL.
            license_name: License name (e.g. "MIT", "Apache-2.0").
            license_url: URL to the full license text.
            servers: List of server dicts ``[{"url": "...", "description": "..."}]``.
            docs_path: URL path for Swagger UI (default ``/docs``).
            openapi_json_path: URL path for raw JSON spec (default ``/openapi.json``).
            redoc_path: URL path for ReDoc viewer (default ``/redoc``).
            include_internal: Include ``/_internal`` routes in the spec.
            group_by_module: Group tags by module.
            infer_request_body: Infer request bodies from source analysis.
            infer_responses: Infer response schemas from source analysis.
            detect_security: Auto-detect security schemes from pipeline guards.
            external_docs_url: URL to external documentation.
            external_docs_description: Description for external docs link.
            swagger_ui_theme: Swagger UI theme ("dark", "" for default).
            swagger_ui_config: Extra Swagger UI configuration overrides.
            enabled: Enable/disable OpenAPI routes entirely.

        Returns:
            OpenAPI configuration dictionary.

        Example::

            .integrate(Integration.openapi(
                title="My App API",
                version="2.0.0",
                description="Production API for My App",
                contact_name="Backend Team",
                contact_email="api@myapp.com",
                license_name="MIT",
                servers=[
                    {"url": "https://api.myapp.com", "description": "Production"},
                    {"url": "https://staging-api.myapp.com", "description": "Staging"},
                ],
                swagger_ui_theme="dark",
            ))
        """
        return {
            "_integration_type": "openapi",
            "enabled": enabled,
            "title": title,
            "version": version,
            "description": description,
            "terms_of_service": terms_of_service,
            "contact_name": contact_name,
            "contact_email": contact_email,
            "contact_url": contact_url,
            "license_name": license_name,
            "license_url": license_url,
            "servers": servers or [],
            "docs_path": docs_path,
            "openapi_json_path": openapi_json_path,
            "redoc_path": redoc_path,
            "include_internal": include_internal,
            "group_by_module": group_by_module,
            "infer_request_body": infer_request_body,
            "infer_responses": infer_responses,
            "detect_security": detect_security,
            "external_docs_url": external_docs_url,
            "external_docs_description": external_docs_description,
            "swagger_ui_theme": swagger_ui_theme,
            "swagger_ui_config": swagger_ui_config or {},
            **kwargs,
        }

    @staticmethod
    def csrf(
        secret_key: str = "",
        token_length: int = 32,
        header_name: str = "X-CSRF-Token",
        field_name: str = "_csrf_token",
        cookie_name: str = "_csrf_cookie",
        cookie_path: str = "/",
        cookie_domain: Optional[str] = None,
        cookie_secure: bool = True,
        cookie_samesite: str = "Lax",
        cookie_httponly: bool = False,
        cookie_max_age: int = 3600,
        safe_methods: Optional[List[str]] = None,
        exempt_paths: Optional[List[str]] = None,
        exempt_content_types: Optional[List[str]] = None,
        trust_ajax: bool = True,
        rotate_token: bool = False,
        failure_status: int = 403,
        enabled: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure CSRF (Cross-Site Request Forgery) protection integration.

        Produces a config dict consumed by ``CSRFMiddleware`` in
        ``aquilia.middleware_ext.security``.

        Args:
            secret_key: HMAC key for cookie-based token signing.
            token_length: Length of generated CSRF tokens in bytes.
            header_name: HTTP header name for token submission.
            field_name: Form field name for token submission.
            cookie_name: Cookie name for double-submit fallback.
            cookie_path: Cookie path attribute.
            cookie_domain: Cookie domain attribute (None = current domain).
            cookie_secure: Set Secure flag on cookie.
            cookie_samesite: SameSite attribute (Strict, Lax, None).
            cookie_httponly: Set HttpOnly flag on cookie.
            cookie_max_age: Cookie max-age in seconds.
            safe_methods: HTTP methods that skip CSRF validation.
            exempt_paths: URL paths exempt from CSRF checks.
            exempt_content_types: Content types exempt from CSRF checks.
            trust_ajax: Trust X-Requested-With header for AJAX requests.
            rotate_token: Generate new token after each successful validation.
            failure_status: HTTP status code returned on CSRF failure.
            enabled: Enable/disable CSRF protection.
            **kwargs: Extra config passed through.

        Returns:
            Config dict with ``_integration_type: "csrf"``.

        Example::

            app = Aquilia(
                integrations=[Integration.csrf(
                    secret_key="my-secret-key",
                    exempt_paths=["/api/webhooks", "/health"],
                    cookie_secure=True,
                    cookie_samesite="Strict",
                )]
            )
        """
        return {
            "_integration_type": "csrf",
            "enabled": enabled,
            "secret_key": secret_key,
            "token_length": token_length,
            "header_name": header_name,
            "field_name": field_name,
            "cookie_name": cookie_name,
            "cookie_path": cookie_path,
            "cookie_domain": cookie_domain,
            "cookie_secure": cookie_secure,
            "cookie_samesite": cookie_samesite,
            "cookie_httponly": cookie_httponly,
            "cookie_max_age": cookie_max_age,
            "safe_methods": safe_methods or ["GET", "HEAD", "OPTIONS", "TRACE"],
            "exempt_paths": exempt_paths or [],
            "exempt_content_types": exempt_content_types or [],
            "trust_ajax": trust_ajax,
            "rotate_token": rotate_token,
            "failure_status": failure_status,
            **kwargs,
        }

    @staticmethod
    def logging(
        format: str = "%(method)s %(path)s %(status)s %(duration_ms).1fms",
        level: str = "INFO",
        slow_threshold_ms: float = 1000.0,
        skip_paths: Optional[List[str]] = None,
        include_headers: bool = False,
        include_query: bool = True,
        include_user_agent: bool = False,
        log_request_body: bool = False,
        log_response_body: bool = False,
        colorize: bool = True,
        enabled: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure request/response logging integration.

        Produces a config dict consumed by ``LoggingMiddleware`` in
        ``aquilia.middleware_ext.logging``.

        Args:
            format: Log message format string.
            level: Default log level for normal requests.
            slow_threshold_ms: Threshold (ms) above which requests are flagged slow.
            skip_paths: URL paths to skip logging for (e.g. health checks).
            include_headers: Include request headers in log output.
            include_query: Include query string in log output.
            include_user_agent: Include User-Agent header in log output.
            log_request_body: Log request body (use with caution).
            log_response_body: Log response body (use with caution).
            colorize: Colorize log output (for development).
            enabled: Enable/disable request logging.
            **kwargs: Extra config passed through.

        Returns:
            Config dict with ``_integration_type: "logging"``.

        Example::

            app = Aquilia(
                integrations=[Integration.logging(
                    slow_threshold_ms=500,
                    skip_paths=["/health", "/metrics"],
                    include_headers=True,
                )]
            )
        """
        return {
            "_integration_type": "logging",
            "enabled": enabled,
            "format": format,
            "level": level,
            "slow_threshold_ms": slow_threshold_ms,
            "skip_paths": skip_paths or ["/health", "/healthz", "/ready", "/metrics"],
            "include_headers": include_headers,
            "include_query": include_query,
            "include_user_agent": include_user_agent,
            "log_request_body": log_request_body,
            "log_response_body": log_response_body,
            "colorize": colorize,
            **kwargs,
        }

    @staticmethod
    def mail(
        default_from: str = "noreply@localhost",
        default_reply_to: Optional[str] = None,
        subject_prefix: str = "",
        providers: Optional[List[Dict[str, Any]]] = None,
        console_backend: bool = False,
        preview_mode: bool = False,
        template_dirs: Optional[List[str]] = None,
        retry_max_attempts: int = 5,
        retry_base_delay: float = 1.0,
        rate_limit_global: int = 1000,
        rate_limit_per_domain: int = 100,
        dkim_enabled: bool = False,
        dkim_domain: Optional[str] = None,
        dkim_selector: str = "aquilia",
        require_tls: bool = True,
        pii_redaction: bool = False,
        metrics_enabled: bool = True,
        tracing_enabled: bool = False,
        enabled: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure AquilaMail -- the production-ready async mail subsystem.

        Args:
            default_from: Default sender address.
            default_reply_to: Default reply-to address.
            subject_prefix: Prefix prepended to all subjects.
            providers: List of provider config dicts.
            console_backend: Print mail to console instead of sending.
            preview_mode: Render-only, no delivery.
            template_dirs: ATS template search paths.
            retry_max_attempts: Max retry attempts for transient failures.
            retry_base_delay: Base delay (seconds) for exponential backoff.
            rate_limit_global: Global rate limit (messages/minute).
            rate_limit_per_domain: Per-domain rate limit (messages/minute).
            dkim_enabled: Enable DKIM signing.
            dkim_domain: DKIM signing domain.
            dkim_selector: DKIM selector.
            require_tls: Require TLS for SMTP connections.
            pii_redaction: Redact PII in logs.
            metrics_enabled: Enable mail metrics.
            tracing_enabled: Enable distributed tracing.
            enabled: Enable/disable the mail subsystem.
            **kwargs: Additional mail configuration.

        Returns:
            Mail configuration dictionary.

        Example::

            .integrate(Integration.mail(
                default_from="noreply@myapp.com",
                console_backend=True,  # dev mode
                providers=[
                    {"name": "smtp", "type": "smtp", "host": "smtp.example.com", "port": 587},
                ],
            ))
        """
        return {
            "_integration_type": "mail",
            "enabled": enabled,
            "default_from": default_from,
            "default_reply_to": default_reply_to,
            "subject_prefix": subject_prefix,
            "providers": providers or [],
            "console_backend": console_backend,
            "preview_mode": preview_mode,
            "templates": {
                "template_dirs": template_dirs or ["mail_templates"],
            },
            "retry": {
                "max_attempts": retry_max_attempts,
                "base_delay": retry_base_delay,
            },
            "rate_limit": {
                "global_per_minute": rate_limit_global,
                "per_domain_per_minute": rate_limit_per_domain,
            },
            "security": {
                "dkim_enabled": dkim_enabled,
                "dkim_domain": dkim_domain,
                "dkim_selector": dkim_selector,
                "require_tls": require_tls,
                "pii_redaction_enabled": pii_redaction,
            },
            "metrics_enabled": metrics_enabled,
            "tracing_enabled": tracing_enabled,
            **kwargs,
        }

    @staticmethod
    def mlops(
        *,
        enabled: bool = True,
        registry_db: str = "registry.db",
        blob_root: str = ".aquilia-store",
        storage_backend: str = "filesystem",
        drift_method: str = "psi",
        drift_threshold: float = 0.2,
        drift_num_bins: int = 10,
        max_batch_size: int = 16,
        max_latency_ms: float = 50.0,
        batching_strategy: str = "hybrid",
        sample_rate: float = 0.01,
        log_dir: str = "prediction_logs",
        hmac_secret: Optional[str] = None,
        signing_private_key: Optional[str] = None,
        signing_public_key: Optional[str] = None,
        encryption_key: Optional[Any] = None,
        plugin_auto_discover: bool = True,
        scaling_policy: Optional[Dict[str, Any]] = None,
        rollout_default_strategy: str = "canary",
        auto_rollback: bool = True,
        metrics_model_name: str = "",
        metrics_model_version: str = "",
        # Ecosystem integration
        cache_enabled: bool = True,
        cache_ttl: int = 60,
        cache_namespace: str = "mlops",
        artifact_store_dir: str = "artifacts",
        fault_engine_debug: bool = False,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure MLOps platform integration.

        Wires model packaging, registry, serving, observability, release
        management, scheduling, security, and plugins into the Aquilia
        framework via DI, lifecycle hooks, and middleware.

        Ecosystem wiring:
        - **CacheService** -- MLOps controller caches model metadata,
          registry listings, and capability introspections.
        - **FaultEngine** -- All MLOps exceptions flow through the engine
          with scoped handlers for observability and recovery.
        - **ArtifactStore** -- Model packs are managed via the Aquilia
          artifact system with content-addressed storage and integrity
          verification.
        - **Effects** -- Controller methods declare ``CacheEffect`` to
          participate in the effect middleware pipeline.

        Args:
            enabled: Enable/disable MLOps integration.
            registry_db: Path to the registry SQLite database.
            blob_root: Root directory for blob storage.
            storage_backend: ``"filesystem"`` or ``"s3"``.
            drift_method: ``"psi"``, ``"ks_test"``, or ``"distribution"``.
            drift_threshold: Drift score threshold for alerts.
            drift_num_bins: Number of histogram bins for PSI.
            max_batch_size: Dynamic batcher max batch size.
            max_latency_ms: Dynamic batcher max wait time (ms).
            batching_strategy: ``"size"``, ``"time"``, or ``"hybrid"``.
            sample_rate: Prediction logging sampling rate (0.0–1.0).
            log_dir: Directory for prediction log files.
            hmac_secret: HMAC secret for artifact signing.
            signing_private_key: Path to RSA private key for signing.
            signing_public_key: Path to RSA public key for verification.
            encryption_key: Fernet key for blob encryption at rest.
            plugin_auto_discover: Scan entry points for plugins.
            scaling_policy: Autoscaler policy dict.
            rollout_default_strategy: Default rollout strategy.
            auto_rollback: Enable automatic rollback on metric degradation.
            metrics_model_name: Default model name for metrics labels.
            metrics_model_version: Default model version for metrics labels.
            cache_enabled: Enable CacheService for MLOps caching.
            cache_ttl: Default cache TTL in seconds.
            cache_namespace: Cache namespace prefix.
            artifact_store_dir: Directory for artifact storage.
            fault_engine_debug: Enable FaultEngine debug mode.
            **kwargs: Additional MLOps configuration.

        Returns:
            MLOps configuration dictionary.

        Example::

            .integrate(Integration.mlops(
                registry_db="registry.db",
                drift_method="psi",
                drift_threshold=0.25,
                max_batch_size=32,
                plugin_auto_discover=True,
                cache_enabled=True,
                cache_ttl=120,
            ))
        """
        return {
            "_integration_type": "mlops",
            "enabled": enabled,
            "registry": {
                "db_path": registry_db,
                "blob_root": blob_root,
                "storage_backend": storage_backend,
            },
            "serving": {
                "max_batch_size": max_batch_size,
                "max_latency_ms": max_latency_ms,
                "batching_strategy": batching_strategy,
            },
            "observe": {
                "drift_method": drift_method,
                "drift_threshold": drift_threshold,
                "drift_num_bins": drift_num_bins,
                "sample_rate": sample_rate,
                "log_dir": log_dir,
                "metrics_model_name": metrics_model_name,
                "metrics_model_version": metrics_model_version,
            },
            "release": {
                "rollout_default_strategy": rollout_default_strategy,
                "auto_rollback": auto_rollback,
            },
            "security": {
                "hmac_secret": hmac_secret,
                "signing_private_key": signing_private_key,
                "signing_public_key": signing_public_key,
                "encryption_key": encryption_key,
            },
            "plugins": {
                "auto_discover": plugin_auto_discover,
            },
            "scaling_policy": scaling_policy,
            "ecosystem": {
                "cache_enabled": cache_enabled,
                "cache_ttl": cache_ttl,
                "cache_namespace": cache_namespace,
                "artifact_store_dir": artifact_store_dir,
                "fault_engine_debug": fault_engine_debug,
            },
            **kwargs,
        }

    @staticmethod
    def i18n(
        *,
        default_locale: str = "en",
        available_locales: Optional[List[str]] = None,
        fallback_locale: str = "en",
        catalog_dirs: Optional[List[str]] = None,
        catalog_format: str = "json",
        missing_key_strategy: str = "log_and_key",
        auto_reload: bool = False,
        auto_detect: bool = True,
        cookie_name: str = "aq_locale",
        query_param: str = "lang",
        path_prefix: bool = False,
        resolver_order: Optional[List[str]] = None,
        enabled: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure the i18n (internationalization) subsystem.

        Provides locale negotiation, translation catalogs, plural rules,
        message formatting, and template integration.

        Args:
            default_locale: Default BCP 47 locale tag.
            available_locales: List of supported locale tags.
            fallback_locale: Ultimate fallback locale.
            catalog_dirs: Directories to scan for translation files.
            catalog_format: ``"json"`` or ``"yaml"``.
            missing_key_strategy: How to handle missing keys —
                ``"return_key"``, ``"return_empty"``, ``"raise"``,
                ``"log_and_key"``.
            auto_reload: Hot-reload catalogs on file change.
            auto_detect: Auto-detect locale from Accept-Language.
            cookie_name: Cookie name for locale preference.
            query_param: Query parameter name for locale override.
            path_prefix: Enable path-based locale (``/en/about``).
            resolver_order: Locale resolver chain order.
            enabled: Enable/disable i18n.
            **kwargs: Additional configuration.

        Returns:
            I18n configuration dictionary.

        Examples::

            # Basic setup with English and French
            .integrate(Integration.i18n(
                default_locale="en",
                available_locales=["en", "fr", "de"],
            ))

            # Full production config
            .integrate(Integration.i18n(
                default_locale="en",
                available_locales=["en", "fr", "de", "ja", "zh"],
                fallback_locale="en",
                catalog_dirs=["locales", "modules/auth/locales"],
                missing_key_strategy="log_and_key",
                auto_detect=True,
                cookie_name="locale",
                resolver_order=["query", "cookie", "session", "header"],
            ))
        """
        return {
            "_integration_type": "i18n",
            "enabled": enabled,
            "default_locale": default_locale,
            "available_locales": available_locales or [default_locale],
            "fallback_locale": fallback_locale,
            "catalog_dirs": catalog_dirs or ["locales"],
            "catalog_format": catalog_format,
            "missing_key_strategy": missing_key_strategy,
            "auto_reload": auto_reload,
            "auto_detect": auto_detect,
            "cookie_name": cookie_name,
            "query_param": query_param,
            "path_prefix": path_prefix,
            "resolver_order": resolver_order or ["query", "cookie", "header"],
            **kwargs,
        }

    @staticmethod
    def serializers(
        *,
        auto_discover: bool = True,
        strict_validation: bool = True,
        raise_on_error: bool = False,
        date_format: str = "iso-8601",
        datetime_format: str = "iso-8601",
        coerce_decimal_to_string: bool = True,
        compact_json: bool = True,
        enabled: bool = True,
        **kwargs,
    ) -> Dict[str, Any]:
        """
        Configure global serializer settings.

        Args:
            auto_discover: Auto-discover serializers in modules.
            strict_validation: Reject unknown fields in input.
            raise_on_error: Raise ``ValidationFault`` instead of
                            returning errors dict.
            date_format: Default output format for DateField.
            datetime_format: Default output format for DateTimeField.
            coerce_decimal_to_string: Render Decimal as string (default).
            compact_json: Use compact JSON output (no indent).
            enabled: Enable/disable the serializer integration.
            **kwargs: Additional serializer configuration.

        Returns:
            Serializer integration configuration dictionary.

        Example::

            .integrate(Integration.serializers(
                strict_validation=True,
                raise_on_error=True,
                coerce_decimal_to_string=False,
            ))
        """
        return {
            "_integration_type": "serializers",
            "enabled": enabled,
            "auto_discover": auto_discover,
            "strict_validation": strict_validation,
            "raise_on_error": raise_on_error,
            "date_format": date_format,
            "datetime_format": datetime_format,
            "coerce_decimal_to_string": coerce_decimal_to_string,
            "compact_json": compact_json,
            **kwargs,
        }


class Workspace:
    """Fluent workspace builder."""
    
    def __init__(self, name: str, version: str = "0.1.0", description: str = ""):
        self._name = name
        self._version = version
        self._description = description
        self._runtime = RuntimeConfig()
        self._modules: List[ModuleConfig] = []
        self._integrations: Dict[str, Dict[str, Any]] = {}
        self._sessions_config: Optional[Dict[str, Any]] = None
        self._security_config: Optional[Dict[str, Any]] = None
        self._telemetry_config: Optional[Dict[str, Any]] = None
        self._database_config: Optional[Dict[str, Any]] = None
        self._mail_config: Optional[Dict[str, Any]] = None
        self._mlops_config: Optional[Dict[str, Any]] = None
        self._cache_config: Optional[Dict[str, Any]] = None
        self._i18n_config: Optional[Dict[str, Any]] = None
        self._tasks_config: Optional[Dict[str, Any]] = None
        self._starter: Optional[str] = None
        self._middleware_chain: Optional[List[Dict[str, Any]]] = None
        self._on_startup: Optional[str] = None
        self._on_shutdown: Optional[str] = None
    
    def on_startup(self, hook: str) -> "Workspace":
        """
        Register a workspace-level startup hook.
        
        Args:
            hook: Import path to a callable in "module:func" format.
        """
        self._on_startup = hook
        return self
        
    def on_shutdown(self, hook: str) -> "Workspace":
        """
        Register a workspace-level shutdown hook.
        
        Args:
            hook: Import path to a callable in "module:func" format.
        """
        self._on_shutdown = hook
        return self
    
    def starter(self, module_name: str) -> "Workspace":
        """
        Register the starter controller module.
        
        The starter controller provides the welcome page at ``/``
        for new workspaces. When registered via ``.starter()``, the
        server loads it from the workspace root instead of relying
        on hard-coded debug-mode logic.
        
        Delete the starter file and this line once your own modules
        provide a ``GET /`` route.
        
        Args:
            module_name: Python module name (e.g. ``"starter"``).
                         Resolved relative to the workspace root.
        """
        self._starter = module_name
        return self
    
    def middleware(self, chain: "Integration.middleware.Chain") -> "Workspace":
        """
        Configure the middleware chain for this workspace.

        Replaces the default hard-coded middleware stack with a
        user-controlled, path-based chain.  Each middleware is
        referenced by its dotted import path so workspace.py never
        needs to import framework internals.

        Args:
            chain: A middleware chain built via
                   ``Integration.middleware.chain()`` or one of the
                   presets (``defaults()``, ``production()``, ``minimal()``).

        Returns:
            Self for chaining.

        Example::

            workspace = (
                Workspace("myapp")
                .middleware(
                    Integration.middleware.chain()
                    .use("aquilia.middleware.ExceptionMiddleware", priority=1)
                    .use("aquilia.middleware.RequestIdMiddleware", priority=10)
                    .use("aquilia.middleware.LoggingMiddleware",   priority=20)
                )
            )
        """
        self._middleware_chain = chain.to_list()
        return self
    
    def runtime(
        self,
        mode: str = "dev",
        host: str = "127.0.0.1",
        port: int = 8000,
        reload: bool = True,
        workers: int = 1,
    ) -> "Workspace":
        """Configure runtime settings."""
        self._runtime = RuntimeConfig(
            mode=mode,
            host=host,
            port=port,
            reload=reload,
            workers=workers,
        )
        return self
    
    def module(self, module: Module) -> "Workspace":
        """Add a module to the workspace."""
        self._modules.append(module.build())
        return self
    
    def integrate(self, integration: Dict[str, Any]) -> "Workspace":
        """Add an integration."""
        # Check for explicit integration type marker
        integration_type = integration.get("_integration_type")
        if integration_type:
            self._integrations[integration_type] = integration
            # Wire specific types to their config slots
            if integration_type == "cors":
                if not self._security_config:
                    self._security_config = {"enabled": True}
                self._security_config["cors_enabled"] = True
                self._security_config["cors"] = integration
            elif integration_type == "csp":
                if not self._security_config:
                    self._security_config = {"enabled": True}
                self._security_config["csp"] = integration
            elif integration_type == "rate_limit":
                if not self._security_config:
                    self._security_config = {"enabled": True}
                self._security_config["rate_limiting"] = True
                self._security_config["rate_limit"] = integration
            elif integration_type == "static_files":
                self._integrations["static_files"] = integration
            elif integration_type == "openapi":
                self._integrations["openapi"] = integration
            elif integration_type == "mail":
                self._integrations["mail"] = integration
                self._mail_config = integration
            elif integration_type == "mlops":
                self._integrations["mlops"] = integration
                self._mlops_config = integration
            elif integration_type == "cache":
                self._integrations["cache"] = integration
                self._cache_config = integration
            elif integration_type == "i18n":
                self._integrations["i18n"] = integration
                self._i18n_config = integration
            elif integration_type == "tasks":
                self._integrations["tasks"] = integration
                self._tasks_config = integration
            return self

        # Determine integration type from keys (legacy detection)
        if "tokens" in integration and "security" in integration:
            self._integrations["auth"] = integration
        elif "policy" in integration or "store" in integration:
            self._integrations["sessions"] = integration
        elif "auto_wire" in integration:
            self._integrations["dependency_injection"] = integration
        elif "strict_matching" in integration:
            self._integrations["routing"] = integration
        elif "default_strategy" in integration:
            self._integrations["fault_handling"] = integration
        elif "search_paths" in integration and "cache" in integration:
            self._integrations["templates"] = integration
        elif "url" in integration and ("auto_create" in integration or "scan_dirs" in integration):
            self._integrations["database"] = integration
            self._database_config = integration
        else:
            # Generic integration
            for key, value in integration.items():
                if key != "enabled":
                    self._integrations[key] = integration
                    break
        return self
    
    def sessions(self, policies: Optional[List[Any]] = None, **kwargs) -> "Workspace":
        """
        Configure session management.
        
        Args:
            policies: List of SessionPolicy instances
            **kwargs: Additional session configuration
        """
        self._sessions_config = {
            "enabled": True,
            "policies": policies or [],
            **kwargs
        }
        return self
    
    def i18n(
        self,
        default_locale: str = "en",
        available_locales: Optional[List[str]] = None,
        **kwargs,
    ) -> "Workspace":
        """
        Configure internationalization (shorthand for ``integrate(Integration.i18n(...))``).

        Args:
            default_locale: Default BCP 47 locale tag.
            available_locales: List of supported locale tags.
            **kwargs: Additional i18n config (see ``Integration.i18n()``).

        Returns:
            Self for chaining.

        Example::

            workspace = (
                Workspace("myapp")
                .i18n(
                    default_locale="en",
                    available_locales=["en", "fr", "de", "ja"],
                )
            )
        """
        config = Integration.i18n(
            default_locale=default_locale,
            available_locales=available_locales,
            **kwargs,
        )
        self._i18n_config = config
        self._integrations["i18n"] = config
        return self

    def tasks(
        self,
        num_workers: int = 4,
        backend: str = "memory",
        **kwargs,
    ) -> "Workspace":
        """
        Configure background tasks (shorthand for ``integrate(Integration.tasks(...))``).

        Args:
            num_workers: Number of concurrent worker coroutines.
            backend: Backend type (``"memory"`` or ``"redis"``).
            **kwargs: Additional task config (see ``Integration.tasks()``).

        Returns:
            Self for chaining.

        Example::

            workspace = (
                Workspace("myapp")
                .tasks(num_workers=8, max_retries=5)
            )
        """
        config = Integration.tasks(
            num_workers=num_workers,
            backend=backend,
            **kwargs,
        )
        self._tasks_config = config
        self._integrations["tasks"] = config
        return self

    def security(
        self,
        cors_enabled: bool = False,
        csrf_protection: bool = False,
        helmet_enabled: bool = True,
        rate_limiting: bool = False,
        https_redirect: bool = False,
        hsts: bool = True,
        proxy_fix: bool = False,
        **kwargs
    ) -> "Workspace":
        """
        Configure security features.
        
        These flags control which security middleware are automatically
        added to the middleware stack during server startup.

        For fine-grained control, use Integration.cors(), Integration.csp(),
        Integration.rate_limit() instead (or in addition).
        
        Args:
            cors_enabled: Enable CORS middleware (default origins: *)
            csrf_protection: Enable CSRF protection
            helmet_enabled: Enable Helmet-style security headers
            rate_limiting: Enable rate limiting (100 req/min default)
            https_redirect: Enable HTTP→HTTPS redirect
            hsts: Enable HSTS header (Strict-Transport-Security)
            proxy_fix: Enable X-Forwarded-* header processing
            **kwargs: Additional security configuration
        """
        self._security_config = {
            "enabled": True,
            "cors_enabled": cors_enabled,
            "csrf_protection": csrf_protection,
            "helmet_enabled": helmet_enabled,
            "rate_limiting": rate_limiting,
            "https_redirect": https_redirect,
            "hsts": hsts,
            "proxy_fix": proxy_fix,
            **kwargs
        }
        return self
    
    def telemetry(
        self,
        tracing_enabled: bool = False,
        metrics_enabled: bool = True,
        logging_enabled: bool = True,
        **kwargs
    ) -> "Workspace":
        """
        Configure telemetry and observability.
        
        Args:
            tracing_enabled: Enable distributed tracing
            metrics_enabled: Enable metrics collection
            logging_enabled: Enable structured logging
            **kwargs: Additional telemetry configuration
        """
        self._telemetry_config = {
            "enabled": True,
            "tracing_enabled": tracing_enabled,
            "metrics_enabled": metrics_enabled,
            "logging_enabled": logging_enabled,
            **kwargs
        }
        return self
    
    def database(
        self,
        url: Optional[str] = None,
        *,
        config: Optional[Any] = None,
        auto_connect: bool = True,
        auto_create: bool = True,
        auto_migrate: bool = False,
        migrations_dir: str = "migrations",
        **kwargs,
    ) -> "Workspace":
        """
        Configure global database for the workspace.
        
        This sets the default database for all modules.
        Individual modules can override with Module.database().
        
        Accepts either a URL string or a typed DatabaseConfig object.
        
        Args:
            url: Database URL (backward compatible)
            config: Typed DatabaseConfig (SqliteConfig, PostgresConfig,
                    MysqlConfig, OracleConfig). Takes precedence over url.
            auto_connect: Connect on startup
            auto_create: Create tables on startup
            auto_migrate: Run pending migrations on startup
            migrations_dir: Migration files directory
            **kwargs: Additional database options
            
        Example:
            ```python
            from aquilia.db.configs import PostgresConfig
            
            workspace = (
                Workspace("myapp")
                .database(config=PostgresConfig(
                    host="localhost",
                    name="mydb",
                    user="admin",
                    password="secret",
                ))
                .module(Module("blog").register_models("models/blog.amdl"))
            )
            
            # Or with URL (backward compatible):
            workspace = (
                Workspace("myapp")
                .database(url="sqlite:///app.db", auto_create=True)
            )
            ```
        """
        if config is not None:
            self._database_config = config.to_dict()
            self._database_config.update({
                "auto_connect": auto_connect,
                "auto_create": auto_create,
                "auto_migrate": auto_migrate,
                "migrations_dir": migrations_dir,
            })
            self._database_config.update(kwargs)
        else:
            self._database_config = {
                "enabled": True,
                "url": url or "sqlite:///db.sqlite3",
                "auto_connect": auto_connect,
                "auto_create": auto_create,
                "auto_migrate": auto_migrate,
                "migrations_dir": migrations_dir,
                **kwargs,
            }
        return self
    
    def mlops(
        self,
        enabled: bool = True,
        registry_db: str = "registry.db",
        blob_root: str = ".aquilia-store",
        drift_method: str = "psi",
        drift_threshold: float = 0.2,
        max_batch_size: int = 16,
        max_latency_ms: float = 50.0,
        plugin_auto_discover: bool = True,
        **kwargs,
    ) -> "Workspace":
        """
        Configure MLOps platform for this workspace.

        Shorthand for ``.integrate(Integration.mlops(...))``.

        Args:
            enabled: Enable MLOps subsystem.
            registry_db: Path to registry database.
            blob_root: Root directory for blob storage.
            drift_method: Drift detection method.
            drift_threshold: Drift alert threshold.
            max_batch_size: Dynamic batcher max batch size.
            max_latency_ms: Dynamic batcher max wait (ms).
            plugin_auto_discover: Auto-discover plugins.
            **kwargs: Additional MLOps configuration.

        Example::

            workspace = (
                Workspace("ml-app")
                .mlops(
                    registry_db="models.db",
                    drift_method="psi",
                    max_batch_size=32,
                )
            )
        """
        config = Integration.mlops(
            enabled=enabled,
            registry_db=registry_db,
            blob_root=blob_root,
            drift_method=drift_method,
            drift_threshold=drift_threshold,
            max_batch_size=max_batch_size,
            max_latency_ms=max_latency_ms,
            plugin_auto_discover=plugin_auto_discover,
            **kwargs,
        )
        self._mlops_config = config
        self._integrations["mlops"] = config
        
        if enabled:
            # Auto-register MLOps lifecycle hooks if not already set
            if not self._on_startup:
                self.on_startup("aquilia.mlops.engine.lifecycle:mlops_on_startup")
            if not self._on_shutdown:
                self.on_shutdown("aquilia.mlops.engine.lifecycle:mlops_on_shutdown")
                
        return self
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert workspace to dictionary format compatible with ConfigLoader.
        
        Returns:
            Configuration dictionary
        """
        config = {
            "workspace": {
                "name": self._name,
                "version": self._version,
                "description": self._description,
            },
            "runtime": {
                "mode": self._runtime.mode,
                "host": self._runtime.host,
                "port": self._runtime.port,
                "reload": self._runtime.reload,
                "workers": self._runtime.workers,
            },
            "modules": [m.to_dict() for m in self._modules],
            "integrations": self._integrations,
            "middleware_chain": self._middleware_chain,
            "starter": self._starter,
            "on_startup": self._on_startup,
            "on_shutdown": self._on_shutdown,
        }
        
        # Add optional configurations
        if self._sessions_config:
            config["sessions"] = self._sessions_config
            # Also add to integrations for compatibility
            if "integrations" not in config:
                config["integrations"] = {}
            config["integrations"]["sessions"] = self._sessions_config
        if self._security_config:
            config["security"] = self._security_config
        if self._telemetry_config:
            config["telemetry"] = self._telemetry_config
        if self._database_config:
            config["database"] = self._database_config
            # Also add to integrations for compatibility
            config["integrations"]["database"] = self._database_config
        if self._mail_config:
            config["mail"] = self._mail_config
            config["integrations"]["mail"] = self._mail_config
        if self._mlops_config:
            config["mlops"] = self._mlops_config
            config["integrations"]["mlops"] = self._mlops_config
        if self._cache_config:
            config["cache"] = self._cache_config
            config["integrations"]["cache"] = self._cache_config
        if self._i18n_config:
            config["i18n"] = self._i18n_config
            config["integrations"]["i18n"] = self._i18n_config
        if self._tasks_config:
            config["tasks"] = self._tasks_config
            config["integrations"]["tasks"] = self._tasks_config
        
        return config
    
    def __repr__(self) -> str:
        return f"Workspace(name='{self._name}', version='{self._version}', modules={len(self._modules)})"


__all__ = [
    "Workspace",
    "Module",
    "Integration",
    "RuntimeConfig",
    "ModuleConfig",
    "AuthConfig",
]

# Re-export config classes for convenient access
try:
    from aquilia.db.configs import (
        DatabaseConfig,
        SqliteConfig,
        PostgresConfig,
        MysqlConfig,
        OracleConfig,
    )
    __all__ += [
        "DatabaseConfig",
        "SqliteConfig",
        "PostgresConfig",
        "MysqlConfig",
        "OracleConfig",
    ]
except ImportError:
    pass
