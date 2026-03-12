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

from dataclasses import dataclass, field
from typing import Any, Optional

# Typed integration protocol (lazy import to avoid circular deps)
try:
    from aquilia.integrations._protocol import IntegrationConfig as _IntegrationConfig
except ImportError:  # pragma: no cover
    _IntegrationConfig = None  # type: ignore[assignment,misc]


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

    # v2: Module encapsulation
    imports: list[str] = field(default_factory=list)  # modules this module depends on
    exports: list[str] = field(default_factory=list)  # services/components exposed to importers

    # Lifecycle hooks
    on_startup: str | None = None
    on_shutdown: str | None = None

    # Database configuration (per-module override)
    database: dict[str, Any] | None = None

    # Discovery configuration
    auto_discover: bool = True  # Default to True for convenience

    def to_dict(self) -> dict[str, Any]:
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

    def register_providers(self, *providers: dict[str, Any]) -> "Module":
        """DEPRECATED -- declare providers in modules/*/manifest.py instead."""
        import warnings

        warnings.warn(
            "Module.register_providers() is deprecated. Declare providers in modules/<name>/manifest.py.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self

    def register_routes(self, *routes: dict[str, Any]) -> "Module":
        """DEPRECATED -- declare routes via controllers in modules/*/manifest.py instead."""
        import warnings

        warnings.warn(
            "Module.register_routes() is deprecated. Use controller decorators (@GET, @POST, etc.) instead.",
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
        url: str | None = None,
        *,
        config: Any | None = None,
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


@dataclass
class AuthConfig:
    """Authentication configuration."""

    enabled: bool = True
    store_type: str = "memory"
    secret_key: str | None = None  # MUST be set explicitly; no insecure default
    algorithm: str = "HS256"
    issuer: str = "aquilia"
    audience: str = "aquilia-app"
    access_token_ttl_minutes: int = 60
    refresh_token_ttl_days: int = 30
    require_auth_by_default: bool = False

    def to_dict(self) -> dict[str, Any]:
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
            },
        }


class Integration:
    """Integration configuration builders."""

    class MailAuth:
        """
        Nested config class for mail provider authentication credentials.

        Groups all credential data into one typed object instead of scattering
        ``username``, ``password``, ``api_key`` etc. as flat provider dict keys.

        Pass an instance to ``Integration.mail(auth=...)`` for a global default,
        or embed one inside a provider dict as ``"auth": Integration.MailAuth.plain(...)``.

        Supported authentication methods
        ---------------------------------
        ``plain``   -- SMTP AUTH PLAIN / LOGIN  (username + password)
        ``oauth2``  -- OAuth2 bearer token      (client_id, secret, token_url)
        ``api_key`` -- API-key providers         (SendGrid, Mailgun, etc.)
        ``aws_ses`` -- AWS SES                  (access_key_id, secret, region)
        ``ntlm``    -- Windows NTLM             (username + password + domain)
        ``none``    -- Anonymous / open relay

        Examples::

            # SMTP plain auth
            Integration.MailAuth.plain("user@example.com", "s3cr3t")

            # SendGrid / Mailgun API key
            Integration.MailAuth.api_key(env="SENDGRID_API_KEY")

            # AWS SES
            Integration.MailAuth.aws_ses(
                access_key_id="AKIA...",
                secret_access_key_env="AWS_SECRET_ACCESS_KEY",
                region="eu-west-1",
            )

            # OAuth2 (e.g. Gmail / Microsoft 365)
            Integration.MailAuth.oauth2(
                client_id="abc",
                client_secret_env="OAUTH_CLIENT_SECRET",
                token_url="https://oauth2.googleapis.com/token",
                scope="https://mail.google.com/",
            )
        """

        METHOD_PLAIN = "plain"
        METHOD_OAUTH2 = "oauth2"
        METHOD_API_KEY = "api_key"
        METHOD_AWS_SES = "aws_ses"
        METHOD_NTLM = "ntlm"
        METHOD_NONE = "none"

        def __init__(
            self,
            method: str = "plain",
            # ── plain / NTLM ──────────────────────────────────────────────
            username: str | None = None,
            password: str | None = None,
            password_env: str | None = None,
            domain: str | None = None,  # NTLM domain
            # ── API key (SendGrid, Mailgun, Postmark …) ──────────────────
            api_key: str | None = None,
            api_key_env: str | None = None,
            # ── AWS SES ──────────────────────────────────────────────────
            aws_access_key_id: str | None = None,
            aws_access_key_id_env: str | None = None,
            aws_secret_access_key: str | None = None,
            aws_secret_access_key_env: str | None = None,
            aws_region: str | None = None,
            aws_session_token: str | None = None,
            # ── OAuth2 ───────────────────────────────────────────────────
            access_token: str | None = None,
            refresh_token: str | None = None,
            token_url: str | None = None,
            client_id: str | None = None,
            client_secret: str | None = None,
            client_secret_env: str | None = None,
            scope: str | None = None,
        ) -> None:
            self._method = method
            self._username = username
            self._password = password
            self._password_env = password_env
            self._domain = domain
            self._api_key = api_key
            self._api_key_env = api_key_env
            self._aws_access_key_id = aws_access_key_id
            self._aws_access_key_id_env = aws_access_key_id_env
            self._aws_secret_access_key = aws_secret_access_key
            self._aws_secret_access_key_env = aws_secret_access_key_env
            self._aws_region = aws_region
            self._aws_session_token = aws_session_token
            self._access_token = access_token
            self._refresh_token = refresh_token
            self._token_url = token_url
            self._client_id = client_id
            self._client_secret = client_secret
            self._client_secret_env = client_secret_env
            self._scope = scope

        # ── Convenience constructors ──────────────────────────────────────

        @classmethod
        def plain(
            cls,
            username: str,
            password: str | None = None,
            *,
            password_env: str | None = None,
        ) -> "Integration.MailAuth":
            """SMTP AUTH PLAIN / LOGIN."""
            return cls(
                method="plain",
                username=username,
                password=password,
                password_env=password_env,
            )

        @classmethod
        def api_key(
            cls,
            key: str | None = None,
            *,
            env: str | None = None,
        ) -> "Integration.MailAuth":
            """API-key auth for SendGrid, Mailgun, Postmark, etc."""
            return cls(method="api_key", api_key=key, api_key_env=env)

        @classmethod
        def aws_ses(
            cls,
            access_key_id: str | None = None,
            secret_access_key: str | None = None,
            region: str = "us-east-1",
            session_token: str | None = None,
            *,
            access_key_id_env: str | None = None,
            secret_access_key_env: str | None = None,
        ) -> "Integration.MailAuth":
            """AWS SES credentials."""
            return cls(
                method="aws_ses",
                aws_access_key_id=access_key_id,
                aws_access_key_id_env=access_key_id_env,
                aws_secret_access_key=secret_access_key,
                aws_secret_access_key_env=secret_access_key_env,
                aws_region=region,
                aws_session_token=session_token,
            )

        @classmethod
        def oauth2(
            cls,
            client_id: str,
            client_secret: str | None = None,
            *,
            client_secret_env: str | None = None,
            token_url: str,
            scope: str | None = None,
            access_token: str | None = None,
            refresh_token: str | None = None,
        ) -> "Integration.MailAuth":
            """OAuth2 bearer-token auth (Gmail, Microsoft 365, etc.)."""
            return cls(
                method="oauth2",
                client_id=client_id,
                client_secret=client_secret,
                client_secret_env=client_secret_env,
                token_url=token_url,
                scope=scope,
                access_token=access_token,
                refresh_token=refresh_token,
            )

        @classmethod
        def ntlm(
            cls,
            username: str,
            password: str | None = None,
            domain: str | None = None,
            *,
            password_env: str | None = None,
        ) -> "Integration.MailAuth":
            """Windows NTLM authentication."""
            return cls(
                method="ntlm",
                username=username,
                password=password,
                password_env=password_env,
                domain=domain,
            )

        @classmethod
        def anonymous(cls) -> "Integration.MailAuth":
            """No authentication -- open relay."""
            return cls(method="none")

        # ── Serialisation ─────────────────────────────────────────────────

        def to_dict(self) -> dict[str, Any]:
            """Serialise to the dict format consumed by MailConfig / providers."""
            d: dict[str, Any] = {"method": self._method}
            # Plain / NTLM
            if self._username is not None:
                d["username"] = self._username
            if self._password is not None:
                d["password"] = self._password
            if self._password_env is not None:
                d["password_env"] = self._password_env
            if self._domain is not None:
                d["domain"] = self._domain
            # API key
            if self._api_key is not None:
                d["api_key"] = self._api_key
            if self._api_key_env is not None:
                d["api_key_env"] = self._api_key_env
            # AWS SES
            if self._aws_access_key_id is not None:
                d["aws_access_key_id"] = self._aws_access_key_id
            if self._aws_access_key_id_env is not None:
                d["aws_access_key_id_env"] = self._aws_access_key_id_env
            if self._aws_secret_access_key is not None:
                d["aws_secret_access_key"] = self._aws_secret_access_key
            if self._aws_secret_access_key_env is not None:
                d["aws_secret_access_key_env"] = self._aws_secret_access_key_env
            if self._aws_region is not None:
                d["aws_region"] = self._aws_region
            if self._aws_session_token is not None:
                d["aws_session_token"] = self._aws_session_token
            # OAuth2
            if self._access_token is not None:
                d["access_token"] = self._access_token
            if self._refresh_token is not None:
                d["refresh_token"] = self._refresh_token
            if self._token_url is not None:
                d["token_url"] = self._token_url
            if self._client_id is not None:
                d["client_id"] = self._client_id
            if self._client_secret is not None:
                d["client_secret"] = self._client_secret
            if self._client_secret_env is not None:
                d["client_secret_env"] = self._client_secret_env
            if self._scope is not None:
                d["scope"] = self._scope
            return d

        def __repr__(self) -> str:  # pragma: no cover
            return f"Integration.MailAuth(method={self._method!r}, username={self._username!r})"

    class MailProvider:
        """
        Typed nested builder classes for every built-in mail provider.

        Instead of writing raw dicts in ``Integration.mail(providers=[...])``,
        use these classes for IDE auto-complete, validation, and clarity::

            .integrate(Integration.mail(
                default_from="noreply@myapp.com",
                auth=Integration.MailAuth.plain("user", password_env="SMTP_PASS"),
                providers=[
                    Integration.MailProvider.SMTP(
                        name="primary",
                        host="smtp.myapp.com",
                        port=587,
                    ),
                ],
            ))

        Every class exposes a ``to_dict()`` method so they are directly
        usable anywhere a provider dict is expected.  They also accept an
        ``auth=`` kwarg (``Integration.MailAuth`` instance) to attach
        per-provider credentials that override the global auth.

        Available providers
        -------------------
        ``Integration.MailProvider.SMTP``      -- SMTP / STARTTLS
        ``Integration.MailProvider.SES``       -- AWS Simple Email Service
        ``Integration.MailProvider.SendGrid``  -- SendGrid Web API v3
        ``Integration.MailProvider.Console``   -- stdout (development)
        ``Integration.MailProvider.File``      -- .eml files on disk (testing / audit)
        """

        # ── Base ─────────────────────────────────────────────────────────

        class _Base:
            """Shared serialisation logic for all provider builders."""

            _provider_type: str = ""

            def __init__(
                self,
                name: str,
                *,
                priority: int = 10,
                enabled: bool = True,
                rate_limit_per_min: int = 600,
                auth: Any | None = None,
            ) -> None:
                self._name = name
                self._priority = priority
                self._enabled = enabled
                self._rate_limit = rate_limit_per_min
                self._auth = auth
                self._extra: dict[str, Any] = {}

            def _base_dict(self) -> dict[str, Any]:
                d: dict[str, Any] = {
                    "name": self._name,
                    "type": self._provider_type,
                    "priority": self._priority,
                    "enabled": self._enabled,
                    "rate_limit_per_min": self._rate_limit,
                }
                if self._auth is not None:
                    d["auth"] = self._auth.to_dict() if hasattr(self._auth, "to_dict") else self._auth
                d.update(self._extra)
                return d

            def to_dict(self) -> dict[str, Any]:  # pragma: no cover
                return self._base_dict()

            def __repr__(self) -> str:  # pragma: no cover
                return (
                    f"Integration.MailProvider.{type(self).__name__}"
                    f"(name={self._name!r}, host={getattr(self, '_host', None)!r})"
                )

        # ── SMTP ─────────────────────────────────────────────────────────

        class SMTP(_Base):
            """
            SMTP / STARTTLS provider builder.

            Maps directly to ``SMTPProvider.__init__`` parameters.

            Example::

                Integration.MailProvider.SMTP(
                    name="primary",
                    host="smtp.myapp.com",
                    port=587,
                    use_tls=True,
                    auth=Integration.MailAuth.plain(
                        "noreply@myapp.com",
                        password_env="SMTP_PASSWORD",
                    ),
                )
            """

            _provider_type = "smtp"

            def __init__(
                self,
                name: str = "smtp",
                host: str = "localhost",
                port: int = 587,
                *,
                use_tls: bool = True,
                use_ssl: bool = False,
                timeout: float = 30.0,
                # Connection pool
                pool_size: int = 3,
                pool_recycle: float = 300.0,
                # TLS / cert options
                validate_certs: bool = True,
                client_cert: str | None = None,
                client_key: str | None = None,
                source_address: str | None = None,
                local_hostname: str | None = None,
                # Shared
                priority: int = 10,
                enabled: bool = True,
                rate_limit_per_min: int = 600,
                auth: Any | None = None,
            ) -> None:
                super().__init__(
                    name,
                    priority=priority,
                    enabled=enabled,
                    rate_limit_per_min=rate_limit_per_min,
                    auth=auth,
                )
                self._host = host
                self._port = port
                self._use_tls = use_tls
                self._use_ssl = use_ssl
                self._timeout = timeout
                self._pool_size = pool_size
                self._pool_recycle = pool_recycle
                self._validate_certs = validate_certs
                self._client_cert = client_cert
                self._client_key = client_key
                self._source_address = source_address
                self._local_hostname = local_hostname

            def to_dict(self) -> dict[str, Any]:
                d = self._base_dict()
                d.update(
                    {
                        "host": self._host,
                        "port": self._port,
                        "use_tls": self._use_tls,
                        "use_ssl": self._use_ssl,
                        "timeout": self._timeout,
                        "pool_size": self._pool_size,
                        "pool_recycle": self._pool_recycle,
                        "validate_certs": self._validate_certs,
                    }
                )
                if self._client_cert is not None:
                    d["client_cert"] = self._client_cert
                if self._client_key is not None:
                    d["client_key"] = self._client_key
                if self._source_address is not None:
                    d["source_address"] = self._source_address
                if self._local_hostname is not None:
                    d["local_hostname"] = self._local_hostname
                return d

        # ── SES ──────────────────────────────────────────────────────────

        class SES(_Base):
            """
            AWS Simple Email Service provider builder.

            Credentials are best supplied via ``auth=Integration.MailAuth.aws_ses(...)``
            or via the environment / IAM role (recommended for production).

            Example::

                Integration.MailProvider.SES(
                    name="ses-prod",
                    region="eu-west-1",
                    configuration_set="my-config",
                    auth=Integration.MailAuth.aws_ses(
                        access_key_id_env="AWS_ACCESS_KEY_ID",
                        secret_access_key_env="AWS_SECRET_ACCESS_KEY",
                    ),
                )
            """

            _provider_type = "ses"

            def __init__(
                self,
                name: str = "ses",
                region: str = "us-east-1",
                *,
                configuration_set: str | None = None,
                source_arn: str | None = None,
                return_path: str | None = None,
                tags: dict[str, str] | None = None,
                use_raw: bool = True,
                endpoint_url: str | None = None,
                # Shared
                priority: int = 10,
                enabled: bool = True,
                rate_limit_per_min: int = 600,
                auth: Any | None = None,
            ) -> None:
                super().__init__(
                    name,
                    priority=priority,
                    enabled=enabled,
                    rate_limit_per_min=rate_limit_per_min,
                    auth=auth,
                )
                self._region = region
                self._configuration_set = configuration_set
                self._source_arn = source_arn
                self._return_path = return_path
                self._tags = tags or {}
                self._use_raw = use_raw
                self._endpoint_url = endpoint_url

            def to_dict(self) -> dict[str, Any]:
                d = self._base_dict()
                d["region"] = self._region
                d["use_raw"] = self._use_raw
                if self._configuration_set is not None:
                    d["configuration_set"] = self._configuration_set
                if self._source_arn is not None:
                    d["source_arn"] = self._source_arn
                if self._return_path is not None:
                    d["return_path"] = self._return_path
                if self._tags:
                    d["tags"] = self._tags
                if self._endpoint_url is not None:
                    d["endpoint_url"] = self._endpoint_url
                return d

        # ── SendGrid ─────────────────────────────────────────────────────

        class SendGrid(_Base):
            """
            SendGrid Web API v3 provider builder.

            Example::

                Integration.MailProvider.SendGrid(
                    name="sendgrid-prod",
                    auth=Integration.MailAuth.api_key(env="SENDGRID_API_KEY"),
                    sandbox_mode=False,
                    click_tracking=True,
                )
            """

            _provider_type = "sendgrid"

            def __init__(
                self,
                name: str = "sendgrid",
                *,
                sandbox_mode: bool = False,
                click_tracking: bool = True,
                open_tracking: bool = True,
                categories: list[str] | None = None,
                asm_group_id: int | None = None,
                ip_pool_name: str | None = None,
                template_id: str | None = None,
                api_base_url: str = "https://api.sendgrid.com",
                timeout: float = 30.0,
                # Shared
                priority: int = 10,
                enabled: bool = True,
                rate_limit_per_min: int = 600,
                auth: Any | None = None,
            ) -> None:
                super().__init__(
                    name,
                    priority=priority,
                    enabled=enabled,
                    rate_limit_per_min=rate_limit_per_min,
                    auth=auth,
                )
                self._sandbox_mode = sandbox_mode
                self._click_tracking = click_tracking
                self._open_tracking = open_tracking
                self._categories = categories or []
                self._asm_group_id = asm_group_id
                self._ip_pool_name = ip_pool_name
                self._template_id = template_id
                self._api_base_url = api_base_url
                self._timeout = timeout

            def to_dict(self) -> dict[str, Any]:
                d = self._base_dict()
                d.update(
                    {
                        "sandbox_mode": self._sandbox_mode,
                        "click_tracking": self._click_tracking,
                        "open_tracking": self._open_tracking,
                        "api_base_url": self._api_base_url,
                        "timeout": self._timeout,
                    }
                )
                if self._categories:
                    d["categories"] = self._categories
                if self._asm_group_id is not None:
                    d["asm_group_id"] = self._asm_group_id
                if self._ip_pool_name is not None:
                    d["ip_pool_name"] = self._ip_pool_name
                if self._template_id is not None:
                    d["template_id"] = self._template_id
                return d

        # ── Console ──────────────────────────────────────────────────────

        class Console(_Base):
            """
            Console / stdout provider builder (development only).

            Prints a formatted representation of each email to the log
            instead of actually sending it.

            Example::

                Integration.MailProvider.Console(name="dev-console")
            """

            _provider_type = "console"

            def __init__(
                self,
                name: str = "console",
                *,
                priority: int = 100,
                enabled: bool = True,
                rate_limit_per_min: int = 10000,
                auth: Any | None = None,
            ) -> None:
                super().__init__(
                    name,
                    priority=priority,
                    enabled=enabled,
                    rate_limit_per_min=rate_limit_per_min,
                    auth=auth,
                )

            def to_dict(self) -> dict[str, Any]:
                return self._base_dict()

        # ── File ─────────────────────────────────────────────────────────

        class File(_Base):
            """
            File / .eml provider builder (testing & audit).

            Writes each outgoing email as an RFC 2822 ``.eml`` file.
            Useful for integration tests and CI pipelines.

            Example::

                Integration.MailProvider.File(
                    name="file-test",
                    output_dir="/tmp/mail_out",
                    max_files=500,
                )
            """

            _provider_type = "file"

            def __init__(
                self,
                name: str = "file",
                output_dir: str = "/tmp/aquilia_mail",
                *,
                max_files: int = 10000,
                write_index: bool = True,
                include_metadata: bool = True,
                file_extension: str = ".eml",
                priority: int = 90,
                enabled: bool = True,
                rate_limit_per_min: int = 10000,
                auth: Any | None = None,
            ) -> None:
                super().__init__(
                    name,
                    priority=priority,
                    enabled=enabled,
                    rate_limit_per_min=rate_limit_per_min,
                    auth=auth,
                )
                self._output_dir = output_dir
                self._max_files = max_files
                self._write_index = write_index
                self._include_metadata = include_metadata
                self._file_extension = file_extension

            def to_dict(self) -> dict[str, Any]:
                d = self._base_dict()
                d.update(
                    {
                        "output_dir": self._output_dir,
                        "max_files": self._max_files,
                        "write_index": self._write_index,
                        "include_metadata": self._include_metadata,
                        "file_extension": self._file_extension,
                    }
                )
                return d

    @staticmethod
    def auth(
        config: AuthConfig | None = None,
        enabled: bool = True,
        store_type: str = "memory",
        secret_key: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
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
                },
            }

        # Apply kwargs overrides (deep merge logic simplified for common top-level overrides)
        # Note: A real deep merge might be better but for now we trust the structure
        conf_dict.update(kwargs)

        return conf_dict

    @staticmethod
    def sessions(
        policy: Any | None = None, store: Any | None = None, transport: Any | None = None, **kwargs
    ) -> dict[str, Any]:
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
        from aquilia.sessions import CookieTransport, MemoryStore, SessionPolicy

        # Smart policy creation with Aquilia's unique builders
        if policy is None:
            policy = SessionPolicy.for_web_users().with_smart_defaults()

        # Smart store selection
        if store is None:
            store = MemoryStore.optimized_for_development()

        # Smart transport with security defaults
        if transport is None:
            if hasattr(policy, "transport") and policy.transport:
                transport = CookieTransport.from_policy(policy.transport)
            else:
                transport = CookieTransport.with_aquilia_defaults()

        return {
            "enabled": True,
            "policy": policy,
            "store": store,
            "transport": transport,
            "aquilia_syntax_version": "2.0",  # Mark as enhanced syntax
            **kwargs,
        }

    @staticmethod
    def di(auto_wire: bool = True, **kwargs) -> dict[str, Any]:
        """Configure dependency injection."""
        return {"enabled": True, "auto_wire": auto_wire, **kwargs}

    @staticmethod
    def database(
        url: str | None = None,
        *,
        config: Any | None = None,
        auto_connect: bool = True,
        auto_create: bool = True,
        auto_migrate: bool = False,
        migrations_dir: str = "migrations",
        pool_size: int = 5,
        echo: bool = False,
        model_paths: list[str] | None = None,
        scan_dirs: list[str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
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
            result.update(
                {
                    "auto_connect": auto_connect,
                    "auto_create": auto_create,
                    "auto_migrate": auto_migrate,
                    "migrations_dir": migrations_dir,
                    "pool_size": pool_size,
                    "echo": echo,
                    "model_paths": model_paths or [],
                    "scan_dirs": scan_dirs or ["models"],
                }
            )
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
        def web_app(**overrides) -> dict[str, Any]:
            """Optimized for web applications with users."""
            from aquilia.sessions import CookieTransport, MemoryStore, SessionPolicy

            policy = SessionPolicy.for_web_users().lasting(days=7).idle_timeout(hours=2).web_defaults().build()
            store = MemoryStore.web_optimized()
            transport = CookieTransport.for_web_browsers()

            return {
                "enabled": True,
                "policy": policy,
                "store": store,
                "transport": transport,
                "aquilia_syntax_version": "2.0",
                **overrides,
            }

        @staticmethod
        def api_service(**overrides) -> dict[str, Any]:
            """Optimized for API services with token-based auth."""
            from aquilia.sessions import HeaderTransport, MemoryStore, SessionPolicy

            policy = SessionPolicy.for_api_tokens().lasting(hours=1).no_idle_timeout().api_defaults().build()
            store = MemoryStore.api_optimized()
            transport = HeaderTransport.for_rest_apis()

            return {
                "enabled": True,
                "policy": policy,
                "store": store,
                "transport": transport,
                "aquilia_syntax_version": "2.0",
                **overrides,
            }

        @staticmethod
        def mobile_app(**overrides) -> dict[str, Any]:
            """Optimized for mobile applications with long-lived sessions."""
            from aquilia.sessions import CookieTransport, MemoryStore, SessionPolicy

            policy = SessionPolicy.for_mobile_users().lasting(days=90).idle_timeout(days=30).mobile_defaults().build()
            store = MemoryStore.mobile_optimized()
            transport = CookieTransport.for_mobile_webviews()

            return {
                "enabled": True,
                "policy": policy,
                "store": store,
                "transport": transport,
                "aquilia_syntax_version": "2.0",
                **overrides,
            }

    @staticmethod
    def storage(
        default: str = "default",
        backends: dict[str, Any] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Configure file storage backends.

        Accepts a dict of named backends (keyed by alias).
        Each value can be a StorageConfig instance or a plain dict
        with a ``backend`` key.

        Args:
            default: Alias of the default backend.
            backends: ``{alias: config_dict_or_StorageConfig, ...}``
            **kwargs: Additional storage options.

        Returns:
            Storage configuration dictionary.

        Examples::

            # Local only:
            .integrate(Integration.storage(
                backends={"default": {"backend": "local", "root": "./uploads"}},
            ))

            # Multi-backend:
            from aquilia.storage import LocalConfig, S3Config
            .integrate(Integration.storage(
                default="cdn",
                backends={
                    "local": LocalConfig(root="./uploads"),
                    "cdn": S3Config(bucket="my-cdn", region="us-east-1"),
                },
            ))
        """
        backend_list = []
        for alias, cfg in (backends or {}).items():
            if hasattr(cfg, "to_dict"):
                entry = cfg.to_dict()
            elif isinstance(cfg, dict):
                entry = dict(cfg)
            else:
                entry = {"backend": str(cfg)}
            entry.setdefault("alias", alias)
            if alias == default:
                entry["default"] = True
            backend_list.append(entry)

        return {
            "_integration_type": "storage",
            "enabled": True,
            "default": default,
            "backends": backend_list,
            **kwargs,
        }

    @staticmethod
    def registry(**kwargs) -> dict[str, Any]:
        """Configure registry."""
        return {"enabled": True, **kwargs}

    @staticmethod
    def routing(strict_matching: bool = True, **kwargs) -> dict[str, Any]:
        """Configure routing."""
        return {"enabled": True, "strict_matching": strict_matching, **kwargs}

    @staticmethod
    def fault_handling(default_strategy: str = "propagate", **kwargs) -> dict[str, Any]:
        """Configure fault handling."""
        return {"enabled": True, "default_strategy": default_strategy, **kwargs}

    class templates:
        """
        Fluent template configuration builder.

        Unique Syntax:
            Integration.templates.source("...").secure().cached()
        """

        class Builder(dict):
            """Fluent builder inheriting from dict for compatibility."""

            def __init__(self, defaults: dict | None = None):
                super().__init__(
                    defaults
                    or {
                        "enabled": True,
                        "search_paths": ["templates"],
                        "cache": "memory",
                        "sandbox": True,
                        "precompile": False,
                    }
                )

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
    ) -> dict[str, Any]:
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
        scheduler_tick: float = 15.0,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Configure the background task subsystem.

        Provides an async-native task queue with priority scheduling,
        retry with exponential backoff, dead-letter handling, and
        admin dashboard integration.

        Tasks are dispatched in two industry-standard ways:

        1. **On-demand** — from controllers/services via
           ``await my_task.delay(...)`` or ``manager.enqueue(...)``.
        2. **Periodic** — automatically by the scheduler loop for
           tasks decorated with ``@task(schedule=every(...))`` or
           ``@task(schedule=cron(...))``.

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
            scheduler_tick: Seconds between scheduler loop ticks
                for periodic task evaluation (default: 15s).
            **kwargs: Additional overrides.

        Returns:
            Tasks configuration dictionary.

        Examples::

            # Default in-memory task queue
            .integrate(Integration.tasks())

            # Custom worker pool with fast scheduler
            .integrate(Integration.tasks(
                num_workers=8,
                default_timeout=600,
                max_retries=5,
                scheduler_tick=10.0,
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
            "scheduler_tick": scheduler_tick,
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

        __slots__ = (
            "_dashboard",
            "_orm",
            "_build",
            "_migrations",
            "_config",
            "_workspace",
            "_permissions",
            "_monitoring",
            "_admin_users",
            "_profile",
            "_audit",
            "_containers",
            "_pods",
            "_query_inspector",
            "_tasks",
            "_errors",
            "_testing",
            "_mlops",
            "_storage",
            "_mailer",
            "_api_keys",
            "_preferences",
            "_provider",
        )

        def __init__(self) -> None:
            self._dashboard: bool = True
            self._orm: bool = True
            self._build: bool = True
            self._migrations: bool = True
            self._config: bool = True
            self._workspace: bool = True
            self._permissions: bool = True
            self._monitoring: bool = False  # disabled by default
            self._admin_users: bool = True
            self._profile: bool = True
            self._audit: bool = False  # disabled by default
            self._containers: bool = False  # disabled by default
            self._pods: bool = False  # disabled by default
            self._query_inspector: bool = False  # disabled by default
            self._tasks: bool = False  # disabled by default
            self._errors: bool = False  # disabled by default
            self._testing: bool = False  # disabled by default
            self._mlops: bool = False  # disabled by default
            self._storage: bool = False  # disabled by default
            self._mailer: bool = False  # disabled by default
            self._api_keys: bool = True
            self._preferences: bool = True
            self._provider: bool = False  # disabled by default

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

        # ── Testing (disabled by default) ──
        def enable_testing(self) -> "Integration.AdminModules":
            """Show the Testing page (test runner, coverage, assertions). Disabled by default -- opt in."""
            self._testing = True
            return self

        def disable_testing(self) -> "Integration.AdminModules":
            """Hide the Testing page."""
            self._testing = False
            return self

        # ── MLOps (disabled by default) ──
        def enable_mlops(self) -> "Integration.AdminModules":
            """Show the MLOps page (model registry, serving, drift, rollouts). Disabled by default -- opt in."""
            self._mlops = True
            return self

        def disable_mlops(self) -> "Integration.AdminModules":
            """Hide the MLOps page."""
            self._mlops = False
            return self

        # ── Storage (disabled by default) ──
        def enable_storage(self) -> "Integration.AdminModules":
            """Show the Storage page (file browser, backend analytics, health). Disabled by default -- opt in."""
            self._storage = True
            return self

        def disable_storage(self) -> "Integration.AdminModules":
            """Hide the Storage page."""
            self._storage = False
            return self

        # ── Mailer (disabled by default) ──
        def enable_mailer(self) -> "Integration.AdminModules":
            """Show the Mailer page (providers, config, templates, send test). Disabled by default -- opt in."""
            self._mailer = True
            return self

        def disable_mailer(self) -> "Integration.AdminModules":
            """Hide the Mailer page."""
            self._mailer = False
            return self

        # ── Provider & Deployment (disabled by default) ──
        def enable_provider(self) -> "Integration.AdminModules":
            """Show the Provider & Deployment page (Render, services, deploys, credentials). Disabled by default -- opt in."""
            self._provider = True
            return self

        def disable_provider(self) -> "Integration.AdminModules":
            """Hide the Provider & Deployment page."""
            self._provider = False
            return self

        # ── API Keys ──
        def enable_api_keys(self) -> "Integration.AdminModules":
            """Show the API Keys page."""
            self._api_keys = True
            return self

        def disable_api_keys(self) -> "Integration.AdminModules":
            """Hide the API Keys page."""
            self._api_keys = False
            return self

        # ── Preferences ──
        def enable_preferences(self) -> "Integration.AdminModules":
            """Show the Preferences page."""
            self._preferences = True
            return self

        def disable_preferences(self) -> "Integration.AdminModules":
            """Hide the Preferences page."""
            self._preferences = False
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

        def to_dict(self) -> dict[str, bool]:
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
                "testing": self._testing,
                "mlops": self._mlops,
                "storage": self._storage,
                "mailer": self._mailer,
                "api_keys": self._api_keys,
                "preferences": self._preferences,
                "provider": self._provider,
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

        __slots__ = ("_enabled", "_max_entries", "_log_logins", "_log_views", "_log_searches", "_excluded_actions")

        def __init__(self) -> None:
            self._enabled: bool = False  # disabled by default
            self._max_entries: int = 10_000
            self._log_logins: bool = True
            self._log_views: bool = True
            self._log_searches: bool = True
            self._excluded_actions: list[str] = []

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

        def to_dict(self) -> dict[str, Any]:
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
            "cpu",
            "memory",
            "disk",
            "network",
            "process",
            "python",
            "system",
            "health_checks",
        ]

        __slots__ = ("_enabled", "_metrics", "_refresh_interval")

        def __init__(self) -> None:
            self._enabled: bool = False  # disabled by default
            self._metrics: list[str] = list(self._ALL_METRICS)
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

        def to_dict(self) -> dict[str, Any]:
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

        def to_dict(self) -> dict[str, bool]:
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
            "_docker_host",
            "_allowed_actions",
            "_denied_actions",
            "_log_tail",
            "_log_since",
            "_refresh_interval",
            "_compose_files",
            "_compose_project_dir",
            "_show_system_containers",
            "_enable_exec",
            "_enable_prune",
            "_enable_build",
            "_enable_export",
            "_enable_image_actions",
            "_enable_volume_actions",
            "_enable_network_actions",
        )

        _ALL_ACTIONS = [
            "start",
            "stop",
            "restart",
            "pause",
            "unpause",
            "kill",
            "rm",
            "logs",
            "inspect",
            "exec",
            "export",
        ]

        def __init__(self) -> None:
            self._docker_host: str | None = None  # None = auto-detect
            self._allowed_actions: list[str] = list(self._ALL_ACTIONS)
            self._denied_actions: list[str] = []
            self._log_tail: int = 200
            self._log_since: str = ""
            self._refresh_interval: int = 15
            self._compose_files: list[str] = []
            self._compose_project_dir: str | None = None
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

        def to_dict(self) -> dict[str, Any]:
            """Serialize to a dict consumed by AdminConfig."""
            effective_actions = [a for a in self._allowed_actions if a not in self._denied_actions]
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
            "pods",
            "deployments",
            "services",
            "ingresses",
            "configmaps",
            "secrets",
            "namespaces",
            "events",
            "daemonsets",
            "statefulsets",
            "jobs",
            "cronjobs",
            "persistentvolumeclaims",
            "nodes",
        ]

        __slots__ = (
            "_kubeconfig",
            "_namespace",
            "_contexts",
            "_resources",
            "_manifest_dirs",
            "_manifest_patterns",
            "_refresh_interval",
            "_enable_logs",
            "_enable_exec",
            "_enable_delete",
            "_enable_scale",
            "_enable_restart",
            "_enable_apply",
            "_log_tail",
        )

        def __init__(self) -> None:
            self._kubeconfig: str | None = None  # None = auto-detect
            self._namespace: str = "default"
            self._contexts: list[str] = []
            self._resources: list[str] = list(self._ALL_RESOURCES)
            self._manifest_dirs: list[str] = ["k8s"]
            self._manifest_patterns: list[str] = ["*.yaml", "*.yml"]
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

        def to_dict(self) -> dict[str, Any]:
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

    class AdminSecurity:
        """
        Fluent builder for admin security configuration.

        Controls CSRF protection, rate limiting, password policies,
        security headers, session fixation protection, and progressive
        lockout for the admin dashboard.

        **Enabled by default** with sensible defaults (OWASP compliant).

        Example::

            security = (
                Integration.AdminSecurity()
                .csrf_enabled()
                .csrf_max_age(7200)
                .rate_limit_max_attempts(5)
                .rate_limit_window(900)
                .password_min_length(12)
                .password_require_special()
                .security_headers_enabled()
                .session_fixation_protection()
            )
        """

        __slots__ = (
            "_csrf_enabled",
            "_csrf_max_age",
            "_csrf_token_length",
            "_rate_limit_enabled",
            "_rate_limit_max_attempts",
            "_rate_limit_window",
            "_sensitive_op_limit",
            "_sensitive_op_window",
            "_progressive_lockout",
            "_lockout_tiers",
            "_password_min_length",
            "_password_max_length",
            "_password_require_upper",
            "_password_require_lower",
            "_password_require_digit",
            "_password_require_special",
            "_security_headers_enabled",
            "_csp_template",
            "_frame_options",
            "_permissions_policy",
            "_session_fixation_protection",
            "_event_tracker_max_events",
        )

        def __init__(self) -> None:
            # CSRF defaults
            self._csrf_enabled: bool = True
            self._csrf_max_age: int = 7200  # 2 hours
            self._csrf_token_length: int = 32
            # Rate limiting defaults
            self._rate_limit_enabled: bool = True
            self._rate_limit_max_attempts: int = 5
            self._rate_limit_window: int = 900  # 15 minutes
            self._sensitive_op_limit: int = 30
            self._sensitive_op_window: int = 300  # 5 minutes
            # Progressive lockout
            self._progressive_lockout: bool = True
            self._lockout_tiers: list[list[int]] | None = None  # [[threshold, duration], ...]
            # Password policy defaults
            self._password_min_length: int = 10
            self._password_max_length: int = 128
            self._password_require_upper: bool = True
            self._password_require_lower: bool = True
            self._password_require_digit: bool = True
            self._password_require_special: bool = True
            # Security headers defaults
            self._security_headers_enabled: bool = True
            self._csp_template: str | None = None
            self._frame_options: str = "DENY"
            self._permissions_policy: str | None = None
            # Session
            self._session_fixation_protection: bool = True
            # Event tracking
            self._event_tracker_max_events: int = 1000

        # ── CSRF ──────────────────────────────────────────────────────

        def csrf_enabled(self, enabled: bool = True) -> "Integration.AdminSecurity":
            """Enable or disable CSRF protection."""
            self._csrf_enabled = enabled
            return self

        def no_csrf(self) -> "Integration.AdminSecurity":
            """Disable CSRF protection (NOT recommended for production)."""
            self._csrf_enabled = False
            return self

        def csrf_max_age(self, seconds: int) -> "Integration.AdminSecurity":
            """Set CSRF token max age in seconds (default: 7200 = 2h)."""
            self._csrf_max_age = max(60, int(seconds))
            return self

        def csrf_token_length(self, length: int) -> "Integration.AdminSecurity":
            """Set CSRF token random nonce length (default: 32)."""
            self._csrf_token_length = max(16, int(length))
            return self

        # ── Rate Limiting ─────────────────────────────────────────────

        def rate_limit_enabled(self, enabled: bool = True) -> "Integration.AdminSecurity":
            """Enable or disable login rate limiting."""
            self._rate_limit_enabled = enabled
            return self

        def no_rate_limit(self) -> "Integration.AdminSecurity":
            """Disable rate limiting (NOT recommended for production)."""
            self._rate_limit_enabled = False
            return self

        def rate_limit_max_attempts(self, n: int) -> "Integration.AdminSecurity":
            """Max login attempts before lockout (default: 5)."""
            self._rate_limit_max_attempts = max(1, int(n))
            return self

        def rate_limit_window(self, seconds: int) -> "Integration.AdminSecurity":
            """Rate limit window in seconds (default: 900 = 15min)."""
            self._rate_limit_window = max(10, int(seconds))
            return self

        def sensitive_op_limit(self, n: int) -> "Integration.AdminSecurity":
            """Max sensitive operations per window (default: 30)."""
            self._sensitive_op_limit = max(1, int(n))
            return self

        def sensitive_op_window(self, seconds: int) -> "Integration.AdminSecurity":
            """Sensitive operation window in seconds (default: 300 = 5min)."""
            self._sensitive_op_window = max(10, int(seconds))
            return self

        # ── Progressive Lockout ───────────────────────────────────────

        def progressive_lockout(self, enabled: bool = True) -> "Integration.AdminSecurity":
            """Enable progressive lockout (escalating durations)."""
            self._progressive_lockout = enabled
            return self

        def lockout_tiers(self, tiers: list[list[int]]) -> "Integration.AdminSecurity":
            """
            Set custom lockout tiers.

            Each tier is ``[failure_threshold, lockout_seconds]``.

            Default::

                [[5, 300], [10, 900], [20, 3600], [50, 86400]]
            """
            self._lockout_tiers = tiers
            return self

        # ── Password Policy ───────────────────────────────────────────

        def password_min_length(self, n: int) -> "Integration.AdminSecurity":
            """Set minimum password length (default: 10)."""
            self._password_min_length = max(4, int(n))
            return self

        def password_max_length(self, n: int) -> "Integration.AdminSecurity":
            """Set maximum password length (default: 128)."""
            self._password_max_length = max(32, int(n))
            return self

        def password_require_upper(self, required: bool = True) -> "Integration.AdminSecurity":
            """Require at least one uppercase letter."""
            self._password_require_upper = required
            return self

        def password_require_lower(self, required: bool = True) -> "Integration.AdminSecurity":
            """Require at least one lowercase letter."""
            self._password_require_lower = required
            return self

        def password_require_digit(self, required: bool = True) -> "Integration.AdminSecurity":
            """Require at least one digit."""
            self._password_require_digit = required
            return self

        def password_require_special(self, required: bool = True) -> "Integration.AdminSecurity":
            """Require at least one special character."""
            self._password_require_special = required
            return self

        def relaxed_password_policy(self) -> "Integration.AdminSecurity":
            """Use relaxed password policy (length-only, min 8)."""
            self._password_min_length = 8
            self._password_require_upper = False
            self._password_require_lower = False
            self._password_require_digit = False
            self._password_require_special = False
            return self

        def strict_password_policy(self) -> "Integration.AdminSecurity":
            """Use strict password policy (min 12, all character classes)."""
            self._password_min_length = 12
            self._password_require_upper = True
            self._password_require_lower = True
            self._password_require_digit = True
            self._password_require_special = True
            return self

        # ── Security Headers ──────────────────────────────────────────

        def security_headers_enabled(self, enabled: bool = True) -> "Integration.AdminSecurity":
            """Enable or disable security header injection."""
            self._security_headers_enabled = enabled
            return self

        def no_security_headers(self) -> "Integration.AdminSecurity":
            """Disable security headers."""
            self._security_headers_enabled = False
            return self

        def csp_template(self, template: str) -> "Integration.AdminSecurity":
            """
            Set custom Content-Security-Policy template.

            Use ``{nonce}`` placeholder for per-request nonce injection.

            Default::

                "default-src 'self'; script-src 'self' {nonce}; ..."
            """
            self._csp_template = template
            return self

        def frame_options(self, value: str) -> "Integration.AdminSecurity":
            """Set X-Frame-Options header (default: DENY)."""
            self._frame_options = value
            return self

        def permissions_policy(self, policy: str) -> "Integration.AdminSecurity":
            """Set Permissions-Policy header."""
            self._permissions_policy = policy
            return self

        # ── Session ───────────────────────────────────────────────────

        def session_fixation_protection(self, enabled: bool = True) -> "Integration.AdminSecurity":
            """Enable session fixation protection (regenerate session on login)."""
            self._session_fixation_protection = enabled
            return self

        # ── Event Tracking ────────────────────────────────────────────

        def event_tracker_max_events(self, n: int) -> "Integration.AdminSecurity":
            """Set max security events in the FIFO buffer (default: 1000)."""
            self._event_tracker_max_events = max(100, int(n))
            return self

        # ── Serialization ─────────────────────────────────────────────

        def to_dict(self) -> dict[str, Any]:
            """Serialize to a dict consumed by AdminConfig / AdminSecurityPolicy."""
            result: dict[str, Any] = {
                "csrf": {
                    "enabled": self._csrf_enabled,
                    "max_age": self._csrf_max_age,
                    "token_length": self._csrf_token_length,
                },
                "rate_limit": {
                    "enabled": self._rate_limit_enabled,
                    "max_login_attempts": self._rate_limit_max_attempts,
                    "login_window": self._rate_limit_window,
                    "sensitive_op_limit": self._sensitive_op_limit,
                    "sensitive_op_window": self._sensitive_op_window,
                    "progressive_lockout": self._progressive_lockout,
                },
                "password": {
                    "min_length": self._password_min_length,
                    "max_length": self._password_max_length,
                    "require_upper": self._password_require_upper,
                    "require_lower": self._password_require_lower,
                    "require_digit": self._password_require_digit,
                    "require_special": self._password_require_special,
                },
                "headers": {
                    "enabled": self._security_headers_enabled,
                    "frame_options": self._frame_options,
                },
                "session_fixation_protection": self._session_fixation_protection,
                "event_tracker_max_events": self._event_tracker_max_events,
            }
            if self._lockout_tiers is not None:
                result["rate_limit"]["lockout_tiers"] = self._lockout_tiers
            if self._csp_template is not None:
                result["headers"]["csp_template"] = self._csp_template
            if self._permissions_policy is not None:
                result["headers"]["permissions_policy"] = self._permissions_policy
            return result

        def __repr__(self) -> str:
            parts = []
            if self._csrf_enabled:
                parts.append("csrf")
            if self._rate_limit_enabled:
                parts.append("rate_limit")
            if self._security_headers_enabled:
                parts.append("headers")
            return f"AdminSecurity({', '.join(parts) or 'minimal'})"

    @staticmethod
    def admin(
        url_prefix: str = "/admin",
        site_title: str = "Aquilia Admin",
        site_header: str = "Aquilia Administration",
        auto_discover: bool = True,
        login_url: str | None = None,
        list_per_page: int = 25,
        theme: str = "auto",
        # ── Nested builder objects (IDE-friendly) ─────────────────
        modules: Optional["Integration.AdminModules"] = None,
        audit: Optional["Integration.AdminAudit"] = None,
        monitoring: Optional["Integration.AdminMonitoring"] = None,
        sidebar: Optional["Integration.AdminSidebar"] = None,
        containers: Optional["Integration.AdminContainers"] = None,
        pods: Optional["Integration.AdminPods"] = None,
        security: Optional["Integration.AdminSecurity"] = None,
        # ── Legacy flat params (backward compat) ─────────────────
        enable_audit: bool | None = None,
        audit_max_entries: int = 10_000,
        enable_dashboard: bool | None = None,
        enable_orm: bool | None = None,
        enable_build: bool | None = None,
        enable_migrations: bool | None = None,
        enable_config: bool | None = None,
        enable_workspace: bool | None = None,
        enable_permissions: bool | None = None,
        enable_monitoring: bool | None = None,
        enable_admin_users: bool | None = None,
        enable_containers: bool | None = None,
        enable_pods: bool | None = None,
        enable_profile: bool | None = None,
        audit_log_logins: bool | None = None,
        audit_log_views: bool | None = None,
        audit_log_searches: bool | None = None,
        enable_api_keys: bool | None = None,
        enable_preferences: bool | None = None,
        audit_excluded_actions: list[str] | None = None,
        monitoring_metrics: list[str] | None = None,
        monitoring_refresh_interval: int | None = None,
        sidebar_sections: dict[str, bool] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
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
            "cpu",
            "memory",
            "disk",
            "network",
            "process",
            "python",
            "system",
            "health_checks",
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
                "testing": kwargs.pop("enable_testing", False),
                "mlops": kwargs.pop("enable_mlops", False),
                "storage": kwargs.pop("enable_storage", False),
                "mailer": kwargs.pop("enable_mailer", False),
                "api_keys": enable_api_keys if enable_api_keys is not None else True,
                "preferences": enable_preferences if enable_preferences is not None else True,
                "provider": kwargs.pop("enable_provider", False),
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
        if audit is not None or modules is None and enable_audit is not None:
            mod_dict["audit"] = bool(audit_dict.get("enabled", mod_dict.get("audit", False)))

        # ── Resolve monitoring ───────────────────────────────────────
        if monitoring is not None:
            mon_dict = monitoring.to_dict()
        else:
            _mon_enabled = enable_monitoring if enable_monitoring is not None else False
            mon_dict = {
                "enabled": _mon_enabled,
                "metrics": list(monitoring_metrics) if monitoring_metrics else list(_all_metrics),
                "refresh_interval": max(5, int(monitoring_refresh_interval))
                if monitoring_refresh_interval is not None
                else 30,
            }

        # Keep module monitoring flag in sync
        # Only override if the monitoring builder was explicitly provided,
        # or if legacy flat enable_monitoring was given AND no modules builder.
        if monitoring is not None or modules is None and enable_monitoring is not None:
            mod_dict["monitoring"] = bool(mon_dict.get("enabled", mod_dict.get("monitoring", False)))

        # ── Resolve sidebar ──────────────────────────────────────────
        if sidebar is not None:
            sidebar_dict = sidebar.to_dict()
        else:
            _default_sidebar = {
                "overview": True,
                "data": True,
                "system": True,
                "infrastructure": True,
                "security": True,
                "models": True,
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
                    "start",
                    "stop",
                    "restart",
                    "pause",
                    "unpause",
                    "kill",
                    "rm",
                    "logs",
                    "inspect",
                    "exec",
                    "export",
                ],
                "log_tail": 200,
                "log_since": "",
                "refresh_interval": 15,
                "compose_files": [],
                "compose_project_dir": None,
                "show_system_containers": False,
                "capabilities": {
                    "exec": True,
                    "prune": True,
                    "build": True,
                    "export": True,
                    "image_actions": True,
                    "volume_actions": True,
                    "network_actions": True,
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
                    "pods",
                    "deployments",
                    "services",
                    "ingresses",
                    "configmaps",
                    "secrets",
                    "namespaces",
                    "events",
                    "daemonsets",
                    "statefulsets",
                    "jobs",
                    "cronjobs",
                    "persistentvolumeclaims",
                    "nodes",
                ],
                "manifest_dirs": ["k8s"],
                "manifest_patterns": ["*.yaml", "*.yml"],
                "refresh_interval": 15,
                "log_tail": 200,
                "capabilities": {
                    "logs": True,
                    "exec": True,
                    "delete": True,
                    "scale": True,
                    "restart": True,
                    "apply": True,
                },
            }

        # ── Resolve security config ───────────────────────────────
        if security is not None:
            security_dict = security.to_dict()
        else:
            security_dict = {
                "csrf": {
                    "enabled": True,
                    "max_age": 7200,
                    "token_length": 32,
                },
                "rate_limit": {
                    "enabled": True,
                    "max_login_attempts": 5,
                    "login_window": 900,
                    "sensitive_op_limit": 30,
                    "sensitive_op_window": 300,
                    "progressive_lockout": True,
                },
                "password": {
                    "min_length": 10,
                    "max_length": 128,
                    "require_upper": True,
                    "require_lower": True,
                    "require_digit": True,
                    "require_special": True,
                },
                "headers": {
                    "enabled": True,
                    "frame_options": "DENY",
                },
                "session_fixation_protection": True,
                "event_tracker_max_events": 1000,
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
            "security_config": security_dict,
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
            name: str | None = None
            kwargs: dict[str, Any] = field(default_factory=dict)

            def to_dict(self) -> dict[str, Any]:
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
                name: str | None = None,
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

            def to_list(self) -> list[dict[str, Any]]:
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
                .use("aquilia.middleware.ExceptionMiddleware", priority=1, debug=False)
                .use("aquilia.middleware.RequestIdMiddleware", priority=10)
                .use("aquilia.middleware.CompressionMiddleware", priority=15, minimum_size=500)
                .use("aquilia.middleware.TimeoutMiddleware", priority=18, timeout_seconds=30.0)
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
    def patterns(**kwargs) -> dict[str, Any]:
        """Configure patterns."""
        return {"enabled": True, **kwargs}

    @staticmethod
    def static_files(
        directories: dict[str, str] | None = None,
        cache_max_age: int = 86400,
        immutable: bool = False,
        etag: bool = True,
        gzip: bool = True,
        brotli: bool = True,
        memory_cache: bool = True,
        html5_history: bool = False,
        **kwargs,
    ) -> dict[str, Any]:
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
        allow_origins: list[str] | None = None,
        allow_methods: list[str] | None = None,
        allow_headers: list[str] | None = None,
        expose_headers: list[str] | None = None,
        allow_credentials: bool = False,
        max_age: int = 600,
        allow_origin_regex: str | None = None,
        **kwargs,
    ) -> dict[str, Any]:
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
            "allow_headers": allow_headers
            or ["accept", "accept-language", "content-language", "content-type", "authorization", "x-requested-with"],
            "expose_headers": expose_headers or [],
            "allow_credentials": allow_credentials,
            "max_age": max_age,
            "allow_origin_regex": allow_origin_regex,
            **kwargs,
        }

    @staticmethod
    def csp(
        policy: dict[str, list[str]] | None = None,
        report_only: bool = False,
        nonce: bool = True,
        preset: str = "strict",
        **kwargs,
    ) -> dict[str, Any]:
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
        burst: int | None = None,
        exempt_paths: list[str] | None = None,
        **kwargs,
    ) -> dict[str, Any]:
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
        servers: list[dict[str, str]] | None = None,
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
        swagger_ui_config: dict[str, Any] | None = None,
        enabled: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
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
        cookie_domain: str | None = None,
        cookie_secure: bool = True,
        cookie_samesite: str = "Lax",
        cookie_httponly: bool = False,
        cookie_max_age: int = 3600,
        safe_methods: list[str] | None = None,
        exempt_paths: list[str] | None = None,
        exempt_content_types: list[str] | None = None,
        trust_ajax: bool = True,
        rotate_token: bool = False,
        failure_status: int = 403,
        enabled: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
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
        skip_paths: list[str] | None = None,
        include_headers: bool = False,
        include_query: bool = True,
        include_user_agent: bool = False,
        log_request_body: bool = False,
        log_response_body: bool = False,
        colorize: bool = True,
        enabled: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
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
        default_reply_to: str | None = None,
        subject_prefix: str = "",
        providers: list[dict[str, Any]] | None = None,
        auth: Any | None = None,
        console_backend: bool = False,
        preview_mode: bool = False,
        template_dirs: list[str] | None = None,
        retry_max_attempts: int = 5,
        retry_base_delay: float = 1.0,
        rate_limit_global: int = 1000,
        rate_limit_per_domain: int = 100,
        dkim_enabled: bool = False,
        dkim_domain: str | None = None,
        dkim_selector: str = "aquilia",
        require_tls: bool = True,
        pii_redaction: bool = False,
        metrics_enabled: bool = True,
        tracing_enabled: bool = False,
        enabled: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
        """
        Configure AquilaMail -- the production-ready async mail subsystem.

        Args:
            default_from: Default sender address.
            default_reply_to: Default reply-to address.
            subject_prefix: Prefix prepended to all subjects.
            providers: List of provider config dicts (may include a per-provider
                ``"auth"`` key containing an ``Integration.MailAuth`` or dict).
            auth: Global default authentication credentials shared by all
                providers that do not define their own.  Pass an
                ``Integration.MailAuth`` instance or a plain dict.
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

            # SMTP with typed provider builder
            .integrate(Integration.mail(
                default_from="noreply@myapp.com",
                auth=Integration.MailAuth.plain(
                    "noreply@myapp.com",
                    password_env="SMTP_PASSWORD",
                ),
                providers=[
                    Integration.MailProvider.SMTP(
                        name="primary",
                        host="smtp.myapp.com",
                        port=587,
                        use_tls=True,
                    ),
                ],
            ))

            # SendGrid
            .integrate(Integration.mail(
                default_from="noreply@myapp.com",
                providers=[
                    Integration.MailProvider.SendGrid(
                        name="sendgrid-prod",
                        auth=Integration.MailAuth.api_key(env="SENDGRID_API_KEY"),
                        click_tracking=True,
                    ),
                ],
            ))

            # AWS SES
            .integrate(Integration.mail(
                default_from="noreply@myapp.com",
                providers=[
                    Integration.MailProvider.SES(
                        name="ses-prod",
                        region="eu-west-1",
                        configuration_set="my-config",
                        auth=Integration.MailAuth.aws_ses(
                            access_key_id_env="AWS_ACCESS_KEY_ID",
                            secret_access_key_env="AWS_SECRET_ACCESS_KEY",
                        ),
                    ),
                ],
            ))

            # Dev / test
            .integrate(Integration.mail(
                default_from="dev@localhost",
                console_backend=True,
                providers=[
                    Integration.MailProvider.Console(),
                    Integration.MailProvider.File(output_dir="/tmp/mail"),
                ],
            ))
        """
        # Normalise auth → plain dict so it is JSON-serialisable downstream
        auth_dict: dict[str, Any] | None = None
        if auth is not None:
            if hasattr(auth, "to_dict"):
                auth_dict = auth.to_dict()
            elif isinstance(auth, dict):
                auth_dict = auth

        # Normalise per-provider auth entries too
        # Also accept Integration.MailProvider.* instances directly,
        # or a single provider object instead of a list.
        if providers is not None and hasattr(providers, "to_dict") and not isinstance(providers, (list, tuple)):
            providers = [providers]
        normalised_providers: list[dict[str, Any]] = []
        for p in providers or []:
            if hasattr(p, "to_dict"):
                # Integration.MailProvider.SMTP / SES / SendGrid / Console / File
                p = p.to_dict()
            elif isinstance(p, dict) and hasattr(p.get("auth"), "to_dict"):
                p = {**p, "auth": p["auth"].to_dict()}
            normalised_providers.append(p)

        return {
            "_integration_type": "mail",
            "enabled": enabled,
            "default_from": default_from,
            "default_reply_to": default_reply_to,
            "subject_prefix": subject_prefix,
            "providers": normalised_providers,
            "auth": auth_dict,
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
        hmac_secret: str | None = None,
        signing_private_key: str | None = None,
        signing_public_key: str | None = None,
        encryption_key: Any | None = None,
        plugin_auto_discover: bool = True,
        scaling_policy: dict[str, Any] | None = None,
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
    ) -> dict[str, Any]:
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
        available_locales: list[str] | None = None,
        fallback_locale: str = "en",
        catalog_dirs: list[str] | None = None,
        catalog_format: str = "json",
        missing_key_strategy: str = "log_and_key",
        auto_reload: bool = False,
        auto_detect: bool = True,
        cookie_name: str = "aq_locale",
        query_param: str = "lang",
        path_prefix: bool = False,
        resolver_order: list[str] | None = None,
        enabled: bool = True,
        **kwargs,
    ) -> dict[str, Any]:
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
    ) -> dict[str, Any]:
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

    # ═══════════════════════════════════════════════════════════════════
    # Render PaaS Deployment Configuration
    # ═══════════════════════════════════════════════════════════════════
    # NOTE: Render deployment config has moved to pyconfig.py
    # (AquilaConfig.Render section).  Use the pyconfig DSL:
    #
    #   class render(AquilaConfig.Render):
    #       region        = "frankfurt"
    #       plan          = "standard"
    #       num_instances = 2
    #
    # The Integration.render() helper and Integration.RenderConfig builder
    # are kept for backward compatibility but delegate to the same
    # configuration path.

    @staticmethod
    def render(
        service_name: str | None = None,
        region: str = "oregon",
        plan: str = "starter",
        num_instances: int = 1,
        image: str | None = None,
        health_path: str = "/_health",
        auto_deploy: str = "no",
        **kwargs,
    ) -> dict[str, Any]:
        """
        Configure Render PaaS deployment.

        Defines how the workspace should be deployed to Render when
        running ``aq deploy render``.  Settings here serve as defaults
        that can be overridden via CLI flags.

        Args:
            service_name: Render service name (default: workspace name).
            region: Deployment region (oregon, frankfurt, ohio, virginia, singapore).
            plan: Compute plan (free, starter, standard, pro, pro_plus, ...).
            num_instances: Number of running instances.
            image: Docker image reference (registry/name:tag).
            health_path: Health check endpoint path.
            auto_deploy: Auto-deploy on image push ("yes" or "no").
            **kwargs: Additional deployment options.

        Returns:
            Render deployment configuration dictionary.

        Examples::

            # Basic deployment
            .integrate(Integration.render(
                region="frankfurt",
                plan="standard",
            ))

            # Production with multiple instances
            .integrate(Integration.render(
                service_name="my-api-prod",
                region="oregon",
                plan="pro",
                num_instances=3,
                image="ghcr.io/myorg/my-api:latest",
            ))

            # High-performance
            .integrate(Integration.render(
                plan="pro_plus",
                num_instances=4,
            ))
        """
        config: dict[str, Any] = {
            "_integration_type": "render",
            "enabled": True,
            "region": region,
            "plan": plan,
            "num_instances": num_instances,
            "health_path": health_path,
            "auto_deploy": auto_deploy,
            **kwargs,
        }
        if service_name:
            config["service_name"] = service_name
        if image:
            config["image"] = image
        return config

    @staticmethod
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
        **kwargs,
    ) -> dict[str, Any]:
        """
        Configure API versioning integration.

        Aquilia's Epoch-Based Versioning supports multiple strategies:
        URL path, header, query param, media type, channel, and composite.

        Features:
        - Multi-strategy resolution with fallback chains
        - Version channels (stable, preview, legacy, canary)
        - Sunset lifecycle with RFC 8594/9745 headers
        - Version negotiation (exact, compatible, best_match, nearest)
        - Version-neutral endpoints
        - Compile-time version graph

        Args:
            strategy: Version extraction strategy.
                "url" — from URL path segment (``/v2/users``)
                "header" — from HTTP header (``X-API-Version: 2``)
                "query" — from query parameter (``?api_version=2``)
                "media_type" — from Accept header (``Accept: application/json; version=2``)
                "channel" — from channel header (``X-API-Channel: stable``)
                "composite" — try all strategies with fallback
            versions: List of supported version strings.
            default_version: Fallback version when not specified.
            require_version: If True, reject requests without a version.
            header_name: Header name for header-based versioning.
            query_param: Query parameter name for query-based versioning.
            url_prefix: URL segment prefix (default "v").
            url_segment_index: URL path segment index (0-based).
            strip_version_from_path: Remove version from URL for routing.
            media_type_param: Parameter name in Accept header.
            channels: Channel → version mapping (e.g. {"stable": "2.0"}).
            channel_header: Header for channel-based resolution.
            channel_query_param: Query param for channel-based resolution.
            negotiation_mode: Version negotiation strategy.
                "exact" — exact match only
                "compatible" — backward-compatible match (same major)
                "best_match" — intelligent best-fit selection
                "nearest" — closest registered version
                "latest" — always use latest
            sunset_policy: SunsetPolicy instance for deprecation handling.
            sunset_schedules: Per-version sunset schedule dicts.
            include_version_header: Add X-API-Version to responses.
            response_header_name: Response header name for version.
            include_supported_versions_header: Add supported versions header.
            neutral_paths: Paths that skip version resolution.
            enabled: Enable/disable versioning.
            **kwargs: Extra config passed through.

        Returns:
            Config dict with ``_integration_type: "versioning"``.

        Example::

            workspace = (
                Workspace("myapp")
                .integrate(Integration.versioning(
                    strategy="composite",
                    versions=["1.0", "2.0", "2.1"],
                    default_version="2.0",
                    channels={"stable": "2.0", "preview": "2.1"},
                    negotiation_mode="compatible",
                ))
            )
        """
        config: dict[str, Any] = {
            "_integration_type": "versioning",
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
            "media_type_param": media_type_param,
            "channels": channels or {},
            "channel_header": channel_header,
            "channel_query_param": channel_query_param,
            "negotiation_mode": negotiation_mode,
            "include_version_header": include_version_header,
            "response_header_name": response_header_name,
            "include_supported_versions_header": include_supported_versions_header,
            "neutral_paths": neutral_paths
            or [
                "/_health",
                "/openapi.json",
                "/docs",
                "/redoc",
            ],
            **kwargs,
        }
        if sunset_policy is not None:
            config["sunset_policy"] = sunset_policy
        if sunset_schedules:
            config["sunset_schedules"] = sunset_schedules
        return config


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
        self._mlops_config: dict[str, Any] | None = None
        self._cache_config: dict[str, Any] | None = None
        self._i18n_config: dict[str, Any] | None = None
        self._tasks_config: dict[str, Any] | None = None
        self._storage_config: dict[str, Any] | None = None
        self._render_config: dict[str, Any] | None = None
        self._starter: str | None = None
        self._middleware_chain: list[dict[str, Any]] | None = None
        self._on_startup: str | None = None
        self._on_shutdown: str | None = None
        self._env_config: AquilaConfig | None = None  # pyconfig bridge

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

    # ------------------------------------------------------------------
    # Python-native environment config bridge
    # ------------------------------------------------------------------

    def env_config(self, config_cls: "type | AquilaConfig") -> "Workspace":
        """
        Attach a :class:`~aquilia.pyconfig.AquilaConfig` subclass
        (or instance) as the operational environment config.

        This replaces the old ``config/base.yaml`` / ``config/dev.yaml``
        approach.  The *structural* config lives in ``workspace.py``
        (modules, integrations, DI, routing) while the *operational*
        config (server host/port, auth tokens, password hasher params,
        database URL, mail credentials, etc.) is defined in a
        class-based :class:`AquilaConfig` hierarchy.

        The environment is resolved at startup from ``AQ_ENV``.

        Args:
            config_cls: An :class:`AquilaConfig` **subclass** or
                        already-resolved **instance**.  If a class is
                        passed, ``.for_env(os.environ.get('AQ_ENV', 'dev'))``
                        is called automatically at :meth:`to_dict` time.

        Returns:
            Self for chaining.

        Example::

            class BaseEnv(AquilaConfig):
                class server(AquilaConfig.Server):
                    port = 8000

            workspace = (
                Workspace("myapp")
                .env_config(BaseEnv)  # resolved by AQ_ENV at runtime
                .module(...)
            )
        """
        self._env_config = config_cls
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

    def integrate(self, integration: "dict[str, Any] | Any") -> "Workspace":
        """
        Add an integration.

        Accepts either:

        * A plain ``dict`` (legacy) produced by ``Integration.xyz()``.
        * A typed :class:`IntegrationConfig` dataclass from
          ``aquilia.integrations`` (new API).  The object's
          ``.to_dict()`` is called automatically and the result is
          routed to the correct config slot.

        Examples::

            # Legacy dict API (still works)
            workspace.integrate(Integration.mail(...))

            # New typed API
            from aquilia.integrations import MailIntegration, SmtpProvider
            workspace.integrate(MailIntegration(
                default_from="hi@app.com",
                providers=[SmtpProvider(host="smtp.app.com")],
            ))
        """
        # ── NEW: typed IntegrationConfig protocol objects ────────────
        if _IntegrationConfig is not None and isinstance(integration, _IntegrationConfig):
            integration = integration.to_dict()

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
            # Generic integration
            for key, _value in integration.items():
                if key != "enabled":
                    self._integrations[key] = integration
                    break
        return self

    def sessions(self, policies: list[Any] | None = None, **kwargs) -> "Workspace":
        """
        Configure session management.

        Args:
            policies: List of SessionPolicy instances
            **kwargs: Additional session configuration
        """
        self._sessions_config = {"enabled": True, "policies": policies or [], **kwargs}
        return self

    def i18n(
        self,
        default_locale: str = "en",
        available_locales: list[str] | None = None,
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

    def storage(
        self,
        default: str = "default",
        backends: dict[str, Any] | None = None,
        **kwargs,
    ) -> "Workspace":
        """
        Configure file storage for the workspace.

        Shorthand for ``integrate(Integration.storage(...))``.

        Args:
            default: Alias of the default backend.
            backends: ``{alias: config_dict_or_StorageConfig, ...}``
            **kwargs: Additional storage configuration.

        Returns:
            Self for chaining.

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
        config = Integration.storage(
            default=default,
            backends=backends,
            **kwargs,
        )
        self._storage_config = config
        self._integrations["storage"] = config
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
            **kwargs,
        }
        return self

    def telemetry(
        self, tracing_enabled: bool = False, metrics_enabled: bool = True, logging_enabled: bool = True, **kwargs
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

    def to_dict(self) -> dict[str, Any]:
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

        # Merge env_config (pyconfig bridge) if provided
        if self._env_config is not None:
            import os

            env_cfg = self._env_config
            # If it's a class (not instance), resolve for current environment
            if isinstance(env_cfg, type):
                env_name = os.environ.get("AQ_ENV", "dev")
                try:
                    env_cfg = env_cfg.for_env(env_name)
                except Exception:
                    pass  # use base class as-is (includes Fault subclasses)
            # Merge the dict representation
            try:
                env_data = env_cfg.to_dict()
            except (TypeError, AttributeError):
                env_data = {}
            # server → runtime mapping
            if "server" in env_data:
                runtime_overlay = env_data.pop("server")
                config["runtime"].update(runtime_overlay)
            for key, val in env_data.items():
                if key in ("env",):
                    continue  # skip meta
                if key in config and isinstance(config[key], dict) and isinstance(val, dict):
                    config[key].update(val)
                else:
                    config[key] = val

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
        if self._storage_config:
            config["storage"] = self._storage_config
            config["integrations"]["storage"] = self._storage_config

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

# Re-export typed integration types for convenience in workspace.py
try:
    from aquilia.integrations import (
        AdminAudit as AdminAudit,
    )
    from aquilia.integrations import (
        AdminContainers as AdminContainers,
    )
    from aquilia.integrations import (
        AdminIntegration as AdminIntegration,
    )
    from aquilia.integrations import (
        AdminModules as AdminModules,
    )
    from aquilia.integrations import (
        AdminMonitoring as AdminMonitoring,
    )
    from aquilia.integrations import (
        AdminPods as AdminPods,
    )
    from aquilia.integrations import (
        AdminSecurity as AdminSecurity,
    )
    from aquilia.integrations import (
        AdminSidebar as AdminSidebar,
    )
    from aquilia.integrations import (
        AuthIntegration as AuthIntegration,
    )
    from aquilia.integrations import (
        CacheIntegration as CacheIntegration,
    )
    from aquilia.integrations import (
        ConsoleProvider as ConsoleProvider,
    )
    from aquilia.integrations import (
        CorsIntegration as CorsIntegration,
    )
    from aquilia.integrations import (
        CspIntegration as CspIntegration,
    )
    from aquilia.integrations import (
        CsrfIntegration as CsrfIntegration,
    )
    from aquilia.integrations import (
        DatabaseIntegration as DatabaseIntegration,
    )
    from aquilia.integrations import (
        DiIntegration as DiIntegration,
    )
    from aquilia.integrations import (
        FaultHandlingIntegration as FaultHandlingIntegration,
    )
    from aquilia.integrations import (
        FileProvider as FileProvider,
    )
    from aquilia.integrations import (
        I18nIntegration as I18nIntegration,
    )
    from aquilia.integrations import (  # noqa: E402
        IntegrationConfig as IntegrationConfig,
    )
    from aquilia.integrations import (
        LoggingIntegration as LoggingIntegration,
    )
    from aquilia.integrations import (
        MailAuth as MailAuth,
    )
    from aquilia.integrations import (
        MailIntegration as MailIntegration,
    )
    from aquilia.integrations import (
        MiddlewareChain as MiddlewareChain,
    )
    from aquilia.integrations import (
        MiddlewareEntry as MiddlewareEntry,
    )
    from aquilia.integrations import (
        MLOpsIntegration as MLOpsIntegration,
    )
    from aquilia.integrations import (
        OpenAPIIntegration as OpenAPIIntegration,
    )
    from aquilia.integrations import (
        PatternsIntegration as PatternsIntegration,
    )
    from aquilia.integrations import (
        RateLimitIntegration as RateLimitIntegration,
    )
    from aquilia.integrations import (
        RegistryIntegration as RegistryIntegration,
    )
    from aquilia.integrations import (
        RenderIntegration as RenderIntegration,
    )
    from aquilia.integrations import (
        RoutingIntegration as RoutingIntegration,
    )
    from aquilia.integrations import (
        SendGridProvider as SendGridProvider,
    )
    from aquilia.integrations import (
        SerializersIntegration as SerializersIntegration,
    )
    from aquilia.integrations import (
        SesProvider as SesProvider,
    )
    from aquilia.integrations import (
        SessionIntegration as SessionIntegration,
    )
    from aquilia.integrations import (
        SmtpProvider as SmtpProvider,
    )
    from aquilia.integrations import (
        StaticFilesIntegration as StaticFilesIntegration,
    )
    from aquilia.integrations import (
        StorageIntegration as StorageIntegration,
    )
    from aquilia.integrations import (
        TasksIntegration as TasksIntegration,
    )
    from aquilia.integrations import (
        TemplatesIntegration as TemplatesIntegration,
    )
    from aquilia.integrations import (
        VersioningIntegration as VersioningIntegration,
    )

    __all__ += [
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
    ]
except ImportError:
    pass

# Re-export pyconfig types for single-import convenience in workspace.py
try:
    from aquilia.pyconfig import (
        AquilaConfig,
        Env,
        Secret,
        section,
    )

    __all__ += ["AquilaConfig", "Secret", "Env", "section"]
except ImportError:
    pass

# Re-export config classes for convenient access
try:
    from aquilia.db.configs import (
        DatabaseConfig,
        MysqlConfig,
        OracleConfig,
        PostgresConfig,
        SqliteConfig,
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
