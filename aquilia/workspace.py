"""
Aquilia Workspace Configuration.

Provides the ``Workspace`` and ``Module`` fluent builders together with
their supporting dataclasses (``RuntimeConfig``, ``ModuleConfig``,
``AuthConfig``).  These were previously housed in ``config_builders.py``
alongside the legacy ``Integration`` class; they now live in their own
clean, focused module.

Usage::

    from aquilia.workspace import Workspace, Module

    workspace = (
        Workspace("myapp", version="1.0.0")
        .runtime(mode="dev", port=8000)
        .module(
            Module("users")
            .route_prefix("/users")
            .depends_on("auth")
        )
        .integrate(CacheIntegration(backend="redis"))
    )
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

    def auto_discover(self, enabled: bool = True) -> Module:
        self._config.auto_discover = enabled
        return self

    def fault_domain(self, domain: str) -> Module:
        self._config.fault_domain = domain
        return self

    def route_prefix(self, prefix: str) -> Module:
        self._config.route_prefix = prefix
        return self

    def depends_on(self, *modules: str) -> Module:
        self._config.depends_on = list(modules)
        return self

    def imports(self, *modules: str) -> Module:
        self._config.imports = list(modules)
        self._config.depends_on = list(modules)
        return self

    def exports(self, *components: str) -> Module:
        self._config.exports = list(components)
        return self

    def tags(self, *module_tags: str) -> Module:
        self._config.tags = list(module_tags)
        return self

    # ── Legacy registration methods (DEPRECATED) ───────────────────

    def register_controllers(self, *controllers: str) -> Module:
        import warnings

        warnings.warn(
            "Module.register_controllers() is deprecated. "
            "Declare controllers in modules/<name>/manifest.py → AppManifest(controllers=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_services(self, *services: str) -> Module:
        import warnings

        warnings.warn(
            "Module.register_services() is deprecated. "
            "Declare services in modules/<name>/manifest.py → AppManifest(services=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_providers(self, *providers: dict[str, Any]) -> Module:
        import warnings

        warnings.warn(
            "Module.register_providers() is deprecated. Declare providers in modules/<name>/manifest.py.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_routes(self, *routes: dict[str, Any]) -> Module:
        import warnings

        warnings.warn(
            "Module.register_routes() is deprecated. Use controller decorators (@GET, @POST, etc.) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_sockets(self, *sockets: str) -> Module:
        import warnings

        warnings.warn(
            "Module.register_sockets() is deprecated. "
            "Declare socket_controllers in modules/<name>/manifest.py → AppManifest(socket_controllers=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_middlewares(self, *middlewares: str) -> Module:
        import warnings

        warnings.warn(
            "Module.register_middlewares() is deprecated. "
            "Declare middleware in modules/<name>/manifest.py → AppManifest(middleware=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_models(self, *models: str) -> Module:
        import warnings

        warnings.warn(
            "Module.register_models() is deprecated. "
            "Declare models in modules/<name>/manifest.py → AppManifest(models=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_serializers(self, *serializers: str) -> Module:
        import warnings

        warnings.warn(
            "Module.register_serializers() is deprecated. "
            "Declare serializers in modules/<name>/manifest.py → AppManifest(serializers=[...]).",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def on_startup(self, hook: str) -> Module:
        self._config.on_startup = hook
        return self

    def on_shutdown(self, hook: str) -> Module:
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
        """Build module configuration."""
        return self._config


# ──────────────────────────────────────────────────────────────────────
# AuthConfig
# ──────────────────────────────────────────────────────────────────────


@dataclass
class AuthConfig:
    """Authentication configuration."""

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
    """Fluent workspace builder."""

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

        return config

    def __repr__(self) -> str:
        return f"Workspace(name='{self._name}', version='{self._version}', modules={len(self._modules)})"
