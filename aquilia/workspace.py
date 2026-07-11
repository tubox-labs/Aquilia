"""
Aquilia Workspace Configuration & Orchestration System.

This module provides the core fluent builders and orchestration configuration data structures
that define the application's global deployment parameters.

Architecture (Manifest-First Design)
------------------------------------
In Aquilia, workspace.py is the primary coordinator and orchestration layer:
- **Global Orchestration**: Configures mode, server binding details, telemetry, security headers,
  global databases, background workers, and mail/cache servers.
- **Module Pointers**: Registers active application modules by defining pointers (`Module`).
  Internals of the modules (controllers, services) remain in each module's `manifest.py`.
- **Integrations**: Binds third-party integrations (e.g. databases, caches, mailing services)
  to the workspace, passing credentials, connection limits, and provider specifics.

Registration & Discovery Flow
-----------------------------
1. **Workspace Definition**: The developer builds the `Workspace` configuration in the project's
   root configuration module (typically `workspace.py`).
2. **Integration Hooking**: Integrations like `MailIntegration` or `DatabaseIntegration` are
   bound to the workspace using the fluent `.integrate()` method.
3. **Module Registration**: Individual application modules are added via `.module(Module("name"))`.
4. **Bootstrapping**: The framework scans the workspace, loads individual module manifests,
   auto-discovers annotated components within convention folders, resolves environment settings,
   and injects everything into the dependency injection container.

Resolution & Configuration Handling
-----------------------------------
All integration arguments are recursively evaluated during serialization or bootstrap.
`Env`, `Secret`, and `PyConfig` instances (e.g. `ProdEnv.mail.email_user`) are automatically resolved
to primitive values (strings, integers) prior to instantiating provider objects.

Common Usage Patterns
---------------------
Creating a basic development workspace:

```python
from aquilia.workspace import Workspace, Module

workspace = (
    Workspace("my-app", version="1.0.0")
    .runtime(mode="dev", port=8000)
    .module(Module("auth"))
    .module(Module("users").route_prefix("/users").depends_on("auth"))
)
```

Advanced Usage Patterns
-----------------------
Creating a production-grade workspace with database, caching, and template engine configuration:

```python
from aquilia.workspace import Workspace, Module
from aquilia.integrations import DatabaseIntegration, SQLiteProvider, MailIntegration, SMTPProvider
from aquilia.pyconfig import Env, Secret

workspace = (
    Workspace("billing-platform", version="1.0.0")
    .runtime(mode="prod", host="0.0.0.0", port=8080)
    .database(
        url=Env("DATABASE_URL"),
        auto_migrate=True,
    )
    .integrate(
        MailIntegration(
            default_from="noreply@billing.com",
            providers=[
                SMTPProvider(
                    host=Env("SMTP_HOST"),
                    port=Env("SMTP_PORT", cast=int),
                    username=Env("SMTP_USER"),
                    password=Secret("SMTP_PASS")
                )
            ]
        )
    )
    .module(
        Module("billing")
        .route_prefix("/api/v1/billing")
        .tags("billing", "payments")
    )
)
```
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aquilia.integrations._protocol import IntegrationConfig

# ──────────────────────────────────────────────────────────────────────
# Dataclasses
# ──────────────────────────────────────────────────────────────────────


@dataclass
class RuntimeConfig:
    """
    Global server runtime configuration.

    Defines execution mode (development vs production), network bindings, reload policies,
    and concurrent ASGI workers.

    Parameters:
        mode: Execution environment. Typically `"dev"`, `"test"`, or `"prod"`. Defaults to `"dev"`.
        host: IP address or hostname to bind the ASGI server to. Defaults to `"127.0.0.1"`.
        port: Network port to bind the ASGI server to. Defaults to `8000`.
        reload: If `True`, restarts the server automatically when source files change (dev only). Defaults to `True`.
        workers: Number of child worker processes to spawn. Defaults to `1`.

    Examples:
        ```python
        config = RuntimeConfig(
            mode="prod",
            host="0.0.0.0",
            port=443,
            workers=4
        )
        ```
    """

    mode: str = "dev"
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True
    workers: int = 1


@dataclass
class ModuleConfig:
    """
    Workspace-level module orchestration metadata.

    A pointer configuration mapping how a module is bound into the workspace. It specifies
    routing prefixes, cross-module dependencies, custom lifecycle hooks, database configurations,
    and auto-discovery scanning toggles.

    In the Manifest-First Architecture, `ModuleConfig` represents the orchestration pointer
    registered in `workspace.py`, while component-level details (controllers, services) reside
    in the module's own `manifest.py`.

    Parameters:
        name: Unique module folder and registration name.
        version: Module version. Defaults to `"0.1.0"`.
        description: Brief module summary.
        fault_domain: Custom fault domain for exception translation. Defaults to uppercase `name`.
        route_prefix: Base HTTP path prefix for module controller routes. Defaults to `"/{name}"`.
        depends_on: List of other module names that must start up before this module.
        tags: Categorization tags.
        imports: List of module names whose exported services are visible to this module.
        exports: List of service class names exported to other importing modules.
        on_startup: Optional dotted path string to startup hook function.
        on_shutdown: Optional dotted path string to shutdown hook function.
        database: Optional dictionary overriding the global database configuration for this module.
        auto_discover: If `True` (default), scans the module directory for convention components.

    Examples:
        ```python
        config = ModuleConfig(
            name="users",
            route_prefix="/api/users",
            depends_on=["auth"]
        )
        ```
    """

    name: str
    version: str = "0.1.0"
    description: str = ""
    fault_domain: str | None = None
    route_prefix: str | None = None
    depends_on: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    imports: list[str] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)

    on_startup: str | None = None
    on_shutdown: str | None = None

    database: dict[str, Any] | None = None

    auto_discover: bool = True

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
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


# ──────────────────────────────────────────────────────────────────────
# Module -- fluent builder
# ──────────────────────────────────────────────────────────────────────


class Module:
    """
    Fluent builder class to configure a workspace module pointer.

    Defines routing prefixes, module boundaries (imports/exports), database connections,
    and hooks for a specific module within the workspace configuration.

    Examples:
        Basic usage:
        ```python
        module = Module("billing").route_prefix("/billing").depends_on("auth")
        ```

        Advanced custom database setup:
        ```python
        module = (
            Module("analytics")
            .database(url="postgresql://db/analytics_prod")
            .auto_discover(False)
        )
        ```
    """

    def __init__(self, name: str, version: str = "0.1.0", description: str = ""):
        """
        Initialize the Module fluent builder.

        Parameters:
            name: Unique module directory and registry name.
            version: Semantic version of the module. Defaults to `"0.1.0"`.
            description: Concise module description.
        """
        self._config = ModuleConfig(
            name=name,
            version=version,
            description=description,
            auto_discover=True,
        )

    def auto_discover(self, enabled: bool = True) -> Module:
        """
        Toggle convention-based auto-discovery scanning for this module.

        Parameters:
            enabled: If `True` (default), the framework scans folders matching convention
                names (e.g. controllers, services, models) during bootstrap.

        Returns:
            The current `Module` builder instance for chaining.
        """
        self._config.auto_discover = enabled
        return self

    def fault_domain(self, domain: str) -> Module:
        """
        Configure a custom fault domain name for exceptions originating in this module.

        Parameters:
            domain: Target fault domain name.

        Returns:
            The current `Module` builder instance for chaining.
        """
        self._config.fault_domain = domain
        return self

    def route_prefix(self, prefix: str) -> Module:
        """
        Set the base HTTP path prefix for all routes defined in this module.

        Parameters:
            prefix: URL path prefix (e.g. `"/users"`).

        Returns:
            The current `Module` builder instance for chaining.
        """
        self._config.route_prefix = prefix
        return self

    def depends_on(self, *modules: str) -> Module:
        """
        Declare bootstrap dependencies for this module.

        Guarantees that the listed modules complete their startup sequence before
        this module starts.

        Parameters:
            *modules: Variadic list of module names.

        Returns:
            The current `Module` builder instance for chaining.
        """
        self._config.depends_on = list(modules)
        return self

    def imports(self, *modules: str) -> Module:
        """
        Define module imports to allow accessing exported services.

        Parameters:
            *modules: Variadic list of module names to import.

        Returns:
            The current `Module` builder instance for chaining.
        """
        self._config.imports = list(modules)
        self._config.depends_on = list(modules)
        return self

    def exports(self, *components: str) -> Module:
        """
        Expose internal module services to other importing modules.

        Parameters:
            *components: Variadic list of service class name strings (e.g. `"UsersService"`).

        Returns:
            The current `Module` builder instance for chaining.
        """
        self._config.exports = list(components)
        return self

    def tags(self, *module_tags: str) -> Module:
        """
        Assign metadata tags to this module.

        Parameters:
            *module_tags: Variadic list of string tags.

        Returns:
            The current `Module` builder instance for chaining.
        """
        self._config.tags = list(module_tags)
        return self

    # ── Legacy registration methods (DEPRECATED) ───────────────────

    def register_controllers(self, *controllers: str) -> Module:
        """
        DEPRECATED: Register controllers. Declare them in AppManifest instead.
        """
        import warnings

        warnings.warn(
            "Module.register_controllers() is deprecated. "
            "Declare controllers in modules/<name>/manifest.py → AppManifest(controllers=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_services(self, *services: str) -> Module:
        """
        DEPRECATED: Register services. Declare them in AppManifest instead.
        """
        import warnings

        warnings.warn(
            "Module.register_services() is deprecated. "
            "Declare services in modules/<name>/manifest.py → AppManifest(services=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_providers(self, *providers: dict[str, Any]) -> Module:
        """
        DEPRECATED: Register providers. Declare them in AppManifest instead.
        """
        import warnings

        warnings.warn(
            "Module.register_providers() is deprecated. Declare providers in modules/<name>/manifest.py.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_routes(self, *routes: dict[str, Any]) -> Module:
        """
        DEPRECATED: Register routes. Declare them in controllers instead.
        """
        import warnings

        warnings.warn(
            "Module.register_routes() is deprecated. Use controller decorators (@GET, @POST, etc.) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_sockets(self, *sockets: str) -> Module:
        """
        DEPRECATED: Register sockets. Declare them in AppManifest instead.
        """
        import warnings

        warnings.warn(
            "Module.register_sockets() is deprecated. "
            "Declare socket_controllers in modules/<name>/manifest.py → AppManifest(socket_controllers=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_middlewares(self, *middlewares: str) -> Module:
        """
        DEPRECATED: Register middleware. Declare them in AppManifest instead.
        """
        import warnings

        warnings.warn(
            "Module.register_middlewares() is deprecated. "
            "Declare middleware in modules/<name>/manifest.py → AppManifest(middleware=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_models(self, *models: str) -> Module:
        """
        DEPRECATED: Register database models. Declare them in AppManifest instead.
        """
        import warnings

        warnings.warn(
            "Module.register_models() is deprecated. "
            "Declare models in modules/<name>/manifest.py → AppManifest(models=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_serializers(self, *serializers: str) -> Module:
        """
        DEPRECATED: Register serializers. Declare them in AppManifest instead.
        """
        import warnings

        warnings.warn(
            "Module.register_serializers() is deprecated. "
            "Declare serializers in modules/<name>/manifest.py → AppManifest(serializers=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def on_startup(self, hook: str) -> Module:
        """
        Register a custom startup hook callable.

        Parameters:
            hook: Dotted path to the callable function (e.g. `"modules.users.hooks:on_startup"`).

        Returns:
            The current `Module` builder instance for chaining.
        """
        self._config.on_startup = hook
        return self

    def on_shutdown(self, hook: str) -> Module:
        """
        Register a custom shutdown hook callable.

        Parameters:
            hook: Dotted path to the callable function (e.g. `"modules.users.hooks:on_shutdown"`).

        Returns:
            The current `Module` builder instance for chaining.
        """
        self._config.on_shutdown = hook
        return self

    def database(
        self,
        url: str | None = None,
        *,
        config: Any | None = None,
        auto_connect: bool = True,
        auto_create: bool = True,
        auto_migrate: bool = False,
        migrations_dir: str = "migrations",
        **kwargs,
    ) -> Module:
        """
        Configure a custom database connection specifically for this module.

        Parameters:
            url: Database connection string URL.
            config: Optional config object to extract connection parameters from.
            auto_connect: Connect automatically during bootstrap.
            auto_create: Create schema tables automatically if missing.
            auto_migrate: Execute pending migration scripts.
            migrations_dir: Folder containing migration files.
            **kwargs: Extra database connection keyword arguments.

        Returns:
            The current `Module` builder instance for chaining.
        """
        if config is not None:
            db_dict = config.to_dict()
            db_dict.update(
                {
                    "auto_connect": auto_connect,
                    "auto_create": auto_create,
                    "auto_migrate": auto_migrate,
                    "migrations_dir": migrations_dir,
                }
            )
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
        """
        Build and finalize the module configuration block.

        Returns:
            The constructed `ModuleConfig` metadata instance.
        """
        return self._config


# ──────────────────────────────────────────────────────────────────────
# AuthConfig
# ──────────────────────────────────────────────────────────────────────


@dataclass
class AuthConfig:
    """
    Global authentication configuration parameters.

    Defines token storage backend, cryptographic hashing algorithms, TTLs, issuer,
    audience, and default security guards for the workspace.

    Parameters:
        enabled: If `True` (default), enables authentication middleware.
        store_type: Token storage backend. Must be `"memory"`, `"redis"`, `"database"`, or `"custom"`.
        secret_key: Cryptographic key used to sign and verify JSON Web Tokens (JWT).
        algorithm: Hashing algorithm for tokens (e.g. `"HS256"`).
        issuer: Token issuer claim (`iss`). Defaults to `"aquilia"`.
        audience: Token audience claim (`aud`). Defaults to `"aquilia-app"`.
        access_token_ttl_minutes: Lifespan of access tokens in minutes. Defaults to `60`.
        refresh_token_ttl_days: Lifespan of refresh tokens in days. Defaults to `30`.
        require_auth_by_default: If `True`, all controller routes require authentication unless marked public.

    Examples:
        ```python
        config = AuthConfig(
            secret_key="my-super-secret-key",
            store_type="redis",
            require_auth_by_default=True
        )
        ```
    """

    enabled: bool = True
    store_type: str = "memory"
    secret_key: str | None = None
    algorithm: str = "HS256"
    issuer: str = "aquilia"
    audience: str = "aquilia-app"
    access_token_ttl_minutes: int = 60
    refresh_token_ttl_days: int = 30
    require_auth_by_default: bool = False

    def to_dict(self) -> dict[str, Any]:
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
            },
        }


# ──────────────────────────────────────────────────────────────────────
# Workspace
# ──────────────────────────────────────────────────────────────────────


class Workspace:
    """
    Fluent builder class to configure the application workspace.

    Workspace serves as the centralized root configuration, defining runtime bindings,
    global databases, security policies, background tasks, telemetry tracking, and
    registering pointers to application modules.

    Examples:
        Basic usage:
        ```python
        from aquilia.workspace import Workspace, Module

        workspace = (
            Workspace("my-service", version="1.0.0")
            .runtime(mode="dev", port=3000)
            .module(Module("users"))
        )
        ```

        Advanced workspace with security, telemetry, and mail integrations:
        ```python
        workspace = (
            Workspace("billing-service")
            .runtime(mode="prod", port=8080)
            .telemetry(metrics_enabled=True)
            .security(cors_enabled=True)
            .integrate(
                MailIntegration(
                    default_from="support@service.com",
                    providers=[SMTPProvider(host="smtp.service.com")]
                )
            )
        )
        ```
    """

    def __init__(self, name: str, version: str = "0.1.0", description: str = ""):
        self._name = name
        self._version = version
        self._description = description
        self._runtime = RuntimeConfig()
        self._modules: list[ModuleConfig] = []
        self._integrations: dict[str, dict[str, Any]] = {}
        self._sessions_config: dict[str, Any] | None = None
        self._security_config: dict[str, Any] | None = None
        self._telemetry_config: dict[str, Any] | None = None
        self._database_config: dict[str, Any] | None = None
        self._mail_config: dict[str, Any] | None = None
        self._cache_config: dict[str, Any] | None = None
        self._i18n_config: dict[str, Any] | None = None
        self._tasks_config: dict[str, Any] | None = None
        self._storage_config: dict[str, Any] | None = None
        self._render_config: dict[str, Any] | None = None
        self._inspector_config: dict[str, Any] | None = None
        self._starter: str | None = None
        self._middleware_chain: list[dict[str, Any]] | None = None
        self._on_startup: str | None = None
        self._on_shutdown: str | None = None
        self._env_config: Any | None = None

    def on_startup(self, hook: str) -> Workspace:
        self._on_startup = hook
        return self

    def on_shutdown(self, hook: str) -> Workspace:
        self._on_shutdown = hook
        return self

    def env_config(self, config_cls: type | Any) -> Workspace:
        self._env_config = config_cls
        return self

    def starter(self, module_name: str) -> Workspace:
        self._starter = module_name
        return self

    def middleware(self, chain: Any) -> Workspace:
        """
        Configure the middleware chain for this workspace.

        Accepts any chain object that implements ``to_list()``, e.g.
        ``MiddlewareChain`` from ``aquilia.integrations``.

        Example::

            from aquilia.integrations import MiddlewareChain

            workspace = (
                Workspace("myapp")
                .middleware(
                    MiddlewareChain()
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
    ) -> Workspace:
        self._runtime = RuntimeConfig(
            mode=mode,
            host=host,
            port=port,
            reload=reload,
            workers=workers,
        )
        return self

    def module(self, module: Module) -> Workspace:
        self._modules.append(module.build())
        return self

    def integrate(self, integration: dict[str, Any] | IntegrationConfig | Any) -> Workspace:
        """
        Add an integration.

        Accepts either:

        * A plain ``dict`` (legacy).
        * A typed :class:`IntegrationConfig` dataclass from
          ``aquilia.integrations`` (new API).  The object's
          ``.to_dict()`` is called automatically and the result is
          routed to the correct config slot.

        Examples::

            # New typed API
            from aquilia.integrations import MailIntegration, SmtpProvider
            workspace.integrate(MailIntegration(
                default_from="hi@app.com",
                providers=[SmtpProvider(host="smtp.app.com")],
            ))
        """
        # ── Typed IntegrationConfig protocol objects ──────────────────
        if isinstance(integration, IntegrationConfig):
            integration = integration.to_dict()

        from aquilia.integrations.utils import resolve_config_value

        integration = resolve_config_value(integration)

        integration_type = integration.get("_integration_type")
        if integration_type:
            self._integrations[integration_type] = integration
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
            elif integration_type == "cache":
                self._integrations["cache"] = integration
                self._cache_config = integration
            elif integration_type == "i18n":
                self._integrations["i18n"] = integration
                self._i18n_config = integration
            elif integration_type == "tasks":
                self._integrations["tasks"] = integration
                self._tasks_config = integration
            elif integration_type == "storage":
                self._integrations["storage"] = integration
                self._storage_config = integration
            elif integration_type == "render":
                self._integrations["render"] = integration
                self._render_config = integration
            elif integration_type == "database":
                self._integrations["database"] = integration
                self._database_config = integration
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
            for key, _value in integration.items():
                if key != "enabled":
                    self._integrations[key] = integration
                    break
        return self

    def inspector(self, enabled: bool = True, **kwargs) -> Workspace:
        """
        Configure request inspector.

        Example::

            workspace = (
                Workspace("myapp")
                .inspector(enabled=True, ring_buffer_size=50)
            )
        """
        self._inspector_config = {"enabled": enabled, **kwargs}
        self._integrations["inspector"] = self._inspector_config
        return self

    def sessions(self, policies: list[Any] | None = None, **kwargs) -> Workspace:
        self._sessions_config = {"enabled": True, "policies": policies or [], **kwargs}
        return self

    def i18n(
        self,
        default_locale: str = "en",
        available_locales: list[str] | None = None,
        **kwargs,
    ) -> Workspace:
        """
        Configure internationalization.

        Shorthand for ``integrate(I18nIntegration(...))``.

        Example::

            workspace = (
                Workspace("myapp")
                .i18n(
                    default_locale="en",
                    available_locales=["en", "fr", "de", "ja"],
                )
            )
        """
        from aquilia.integrations.i18n import I18nIntegration

        cfg = I18nIntegration(
            default_locale=default_locale,
            available_locales=available_locales or [default_locale],
        ).to_dict()
        cfg.update(kwargs)
        self._i18n_config = cfg
        self._integrations["i18n"] = cfg
        return self

    def tasks(
        self,
        num_workers: int = 4,
        backend: str = "memory",
        **kwargs,
    ) -> Workspace:
        """
        Configure background tasks.

        Shorthand for ``integrate(TasksIntegration(...))``.

        Example::

            workspace = (
                Workspace("myapp")
                .tasks(num_workers=8, max_retries=5)
            )
        """
        from aquilia.integrations.tasks import TasksIntegration

        cfg = TasksIntegration(
            num_workers=num_workers,
            backend=backend,
            **{k: v for k, v in kwargs.items() if k in TasksIntegration.__dataclass_fields__},
        ).to_dict()
        extra = {k: v for k, v in kwargs.items() if k not in TasksIntegration.__dataclass_fields__}
        cfg.update(extra)
        self._tasks_config = cfg
        self._integrations["tasks"] = cfg
        return self

    def storage(
        self,
        default: str = "default",
        backends: dict[str, Any] | None = None,
        **kwargs,
    ) -> Workspace:
        """
        Configure file storage for the workspace.

        Shorthand for ``integrate(StorageIntegration(...))``.

        Example::

            from aquilia.storage import LocalConfig, S3Config

            workspace = (
                Workspace("myapp")
                .storage(
                    default="local",
                    backends={
                        "local": LocalConfig(root="./uploads"),
                        "cdn": S3Config(bucket="cdn-bucket", region="us-east-1"),
                    },
                )
            )
        """
        from aquilia.integrations.storage import StorageIntegration

        cfg = StorageIntegration(default=default, backends=backends, **kwargs).to_dict()
        self._storage_config = cfg
        self._integrations["storage"] = cfg
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
        **kwargs,
    ) -> Workspace:
        self._security_config = {
            "enabled": True,
            "cors_enabled": cors_enabled,
            "csrf_protection": csrf_protection,
            "helmet_enabled": helmet_enabled,
            "rate_limiting": rate_limiting,
            "https_redirect": https_redirect,
            "hsts": hsts,
            "proxy_fix": proxy_fix,
            **kwargs,
        }
        return self

    def telemetry(
        self, tracing_enabled: bool = False, metrics_enabled: bool = True, logging_enabled: bool = True, **kwargs
    ) -> Workspace:
        self._telemetry_config = {
            "enabled": True,
            "tracing_enabled": tracing_enabled,
            "metrics_enabled": metrics_enabled,
            "logging_enabled": logging_enabled,
            **kwargs,
        }
        return self

    def database(
        self,
        url: str | None = None,
        *,
        config: Any | None = None,
        auto_connect: bool = True,
        auto_create: bool = True,
        auto_migrate: bool = False,
        migrations_dir: str = "migrations",
        **kwargs,
    ) -> Workspace:
        if config is not None:
            self._database_config = config.to_dict()
            self._database_config.update(
                {
                    "auto_connect": auto_connect,
                    "auto_create": auto_create,
                    "auto_migrate": auto_migrate,
                    "migrations_dir": migrations_dir,
                }
            )
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

    def to_dict(self) -> dict[str, Any]:
        """
        Convert workspace to dictionary format compatible with ConfigLoader.

        Returns:
            Configuration dictionary
        """
        config: dict[str, Any] = {
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

        if self._env_config is not None:
            import os

            env_cfg = self._env_config
            if isinstance(env_cfg, type):
                # Load .env BEFORE reading AQ_ENV — otherwise a .env that
                # sets AQ_ENV=prod will be invisible and DevEnv wins.
                from aquilia.pyconfig import _ensure_dotenv_loaded

                _ensure_dotenv_loaded(config_cls=env_cfg)

                env_name = os.environ.get("AQUILIA_ENV") or os.environ.get("AQ_ENV", "dev")
                try:
                    env_cfg = env_cfg.for_env(env_name)
                except Exception:
                    pass
            try:
                env_data = env_cfg.to_dict()
            except (TypeError, AttributeError):
                env_data = {}
            if "server" in env_data:
                runtime_overlay = env_data.pop("server")
                config["runtime"].update(runtime_overlay)
            for key, val in env_data.items():
                if key in ("env",):
                    continue
                if key in config and isinstance(config[key], dict) and isinstance(val, dict):
                    config[key].update(val)
                else:
                    config[key] = val

        if self._sessions_config:
            config["sessions"] = self._sessions_config
            if "integrations" not in config:
                config["integrations"] = {}
            config["integrations"]["sessions"] = self._sessions_config
        if self._security_config:
            config["security"] = self._security_config
        if self._telemetry_config:
            config["telemetry"] = self._telemetry_config
        if self._database_config:
            config["database"] = self._database_config
            config["integrations"]["database"] = self._database_config
        if self._mail_config:
            config["mail"] = self._mail_config
            config["integrations"]["mail"] = self._mail_config
        if self._cache_config:
            config["cache"] = self._cache_config
            config["integrations"]["cache"] = self._cache_config
        if self._i18n_config:
            config["i18n"] = self._i18n_config
            config["integrations"]["i18n"] = self._i18n_config
        if self._tasks_config:
            config["tasks"] = self._tasks_config
            config["integrations"]["tasks"] = self._tasks_config
        if self._storage_config:
            config["storage"] = self._storage_config
            config["integrations"]["storage"] = self._storage_config
        if self._inspector_config:
            config["inspector"] = self._inspector_config
            if "integrations" not in config:
                config["integrations"] = {}
            config["integrations"]["inspector"] = self._inspector_config

        from aquilia.integrations.utils import resolve_config_value

        return resolve_config_value(config)

    def __repr__(self) -> str:
        return f"Workspace(name='{self._name}', version='{self._version}', modules={len(self._modules)})"
