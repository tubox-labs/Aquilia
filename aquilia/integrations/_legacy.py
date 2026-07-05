"""
Legacy Integration class — backward compatibility shim.

This module exists solely so that existing code using
Integration.mail(...), Integration.admin(...),
etc. continues to work after config_builders.py was removed.

New code should use the typed dataclasses from
aquilia.integrations directly instead.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aquilia.integrations.mail import ConsoleProvider as _MailConsoleProvider
from aquilia.integrations.mail import FileProvider as _MailFileProvider
from aquilia.integrations.mail import MailAuth as _MailAuthImpl
from aquilia.integrations.mail import SendGridProvider as _MailSendGridProvider
from aquilia.integrations.mail import SesProvider as _MailSesProvider
from aquilia.integrations.mail import SmtpProvider as _MailSmtpProvider

# Note: AuthConfig is imported lazily inside the auth() method to
# avoid a circular import with aquilia.workspace.


class Integration:
    """Integration configuration builders."""

    # MailAuth is re-exported from aquilia.mail.auth -- the single
    # canonical declaration of these credential fields (also used by
    # MailIntegration). No separate field list is kept here.
    MailAuth = _MailAuthImpl

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

        Each is a thin wrapper around the matching ``aquilia.mail.providers``
        class -- field names/defaults live there, not here.
        """

        SMTP = _MailSmtpProvider
        SES = _MailSesProvider
        SendGrid = _MailSendGridProvider
        Console = _MailConsoleProvider
        File = _MailFileProvider

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
            # Lazy import to avoid circular dependency with aquilia.workspace
            from aquilia.workspace import AuthConfig

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
        Configure database integration.

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
            model_paths: Explicit model file paths
            scan_dirs: Directories to scan for model files
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
            if entry.get("alias") in (None, "default"):
                entry["alias"] = alias
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

            def source(self, *paths: str) -> Builder:
                """Add template search paths."""
                current = self.get("search_paths", [])
                if current == ["templates"]:  # Replace default
                    current = []
                self["search_paths"] = current + list(paths)
                return self

            def scan_modules(self) -> Builder:
                """Enable module auto-discovery."""
                # This is implicit in server logic but good for intent
                return self

            def cached(self, strategy: str = "memory") -> Builder:
                """Enable bytecode caching."""
                self["cache"] = strategy
                return self

            def secure(self, strict: bool = True) -> Builder:
                """Enable sandbox with security policy."""
                self["sandbox"] = True
                self["sandbox_policy"] = "strict" if strict else "permissive"
                return self

            def unsafe_dev_mode(self) -> Builder:
                """Disable sandbox/caching for development."""
                self["sandbox"] = False
                self["cache"] = "none"
                return self

            def precompile(self) -> Builder:
                """Enable startup precompilation."""
                self["precompile"] = True
                return self

        @classmethod
        def source(cls, *paths: str) -> Builder:
            """Start builder with source paths."""
            return cls.Builder().source(*paths)

        @classmethod
        def defaults(cls) -> Builder:
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
            )
        """

        __slots__ = (
            "_dashboard",
            "_orm",
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
            "_storage",
            "_mailer",
            "_api_keys",
            "_preferences",
            "_provider",
        )

        def __init__(self, **kwargs) -> None:
            self._dashboard: bool = True
            self._orm: bool = True
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
            self._storage: bool = False  # disabled by default
            self._mailer: bool = False  # disabled by default
            self._api_keys: bool = True
            self._preferences: bool = True
            self._provider: bool = False  # disabled by default

            for k, v in kwargs.items():
                clean_k = k
                if clean_k.startswith("enable_"):
                    clean_k = clean_k[7:]
                if not clean_k.startswith("_"):
                    clean_k = f"_{clean_k}"
                if hasattr(self, clean_k):
                    setattr(self, clean_k, bool(v))

        # ── Dashboard ──
        def enable_dashboard(self) -> Integration.AdminModules:
            """Show the Dashboard page."""
            self._dashboard = True
            return self

        def disable_dashboard(self) -> Integration.AdminModules:
            """Hide the Dashboard page."""
            self._dashboard = False
            return self

        # ── ORM ──
        def enable_orm(self) -> Integration.AdminModules:
            """Show the ORM Models page."""
            self._orm = True
            return self

        def disable_orm(self) -> Integration.AdminModules:
            """Hide the ORM Models page."""
            self._orm = False
            return self

        # ── Migrations ──
        def enable_migrations(self) -> Integration.AdminModules:
            """Show the Migrations page."""
            self._migrations = True
            return self

        def disable_migrations(self) -> Integration.AdminModules:
            """Hide the Migrations page."""
            self._migrations = False
            return self

        # ── Config ──
        def enable_config(self) -> Integration.AdminModules:
            """Show the Configuration page."""
            self._config = True
            return self

        def disable_config(self) -> Integration.AdminModules:
            """Hide the Configuration page."""
            self._config = False
            return self

        # ── Workspace ──
        def enable_workspace(self) -> Integration.AdminModules:
            """Show the Workspace page."""
            self._workspace = True
            return self

        def disable_workspace(self) -> Integration.AdminModules:
            """Hide the Workspace page."""
            self._workspace = False
            return self

        # ── Permissions ──
        def enable_permissions(self) -> Integration.AdminModules:
            """Show the Permissions page."""
            self._permissions = True
            return self

        def disable_permissions(self) -> Integration.AdminModules:
            """Hide the Permissions page."""
            self._permissions = False
            return self

        # ── Monitoring (disabled by default) ──
        def enable_monitoring(self) -> Integration.AdminModules:
            """Show the Monitoring page. Disabled by default -- opt in."""
            self._monitoring = True
            return self

        def disable_monitoring(self) -> Integration.AdminModules:
            """Hide the Monitoring page."""
            self._monitoring = False
            return self

        # ── Admin Users ──
        def enable_admin_users(self) -> Integration.AdminModules:
            """Show the Admin Users page."""
            self._admin_users = True
            return self

        def disable_admin_users(self) -> Integration.AdminModules:
            """Hide the Admin Users page."""
            self._admin_users = False
            return self

        # ── Profile ──
        def enable_profile(self) -> Integration.AdminModules:
            """Show the Profile page."""
            self._profile = True
            return self

        def disable_profile(self) -> Integration.AdminModules:
            """Hide the Profile page."""
            self._profile = False
            return self

        # ── Containers ──
        def enable_containers(self) -> Integration.AdminModules:
            """Show the Containers page (Docker containers, compose, images)."""
            self._containers = True
            return self

        def disable_containers(self) -> Integration.AdminModules:
            """Hide the Containers page."""
            self._containers = False
            return self

        # ── Pods ──
        def enable_pods(self) -> Integration.AdminModules:
            """Show the Pods page (Kubernetes pods, deployments, services)."""
            self._pods = True
            return self

        def disable_pods(self) -> Integration.AdminModules:
            """Hide the Pods page."""
            self._pods = False
            return self

        # ── Audit (disabled by default) ──
        def enable_audit(self) -> Integration.AdminModules:
            """Show the Audit Log page. Disabled by default -- opt in."""
            self._audit = True
            return self

        def disable_audit(self) -> Integration.AdminModules:
            """Hide the Audit Log page."""
            self._audit = False
            return self

        # ── Query Inspector (disabled by default) ──
        def enable_query_inspector(self) -> Integration.AdminModules:
            """Show the Query Inspector page (SQL profiling, N+1 detection). Disabled by default -- opt in."""
            self._query_inspector = True
            return self

        def disable_query_inspector(self) -> Integration.AdminModules:
            """Hide the Query Inspector page."""
            self._query_inspector = False
            return self

        # ── Background Tasks (disabled by default) ──
        def enable_tasks(self) -> Integration.AdminModules:
            """Show the Background Tasks page. Disabled by default -- opt in."""
            self._tasks = True
            return self

        def disable_tasks(self) -> Integration.AdminModules:
            """Hide the Background Tasks page."""
            self._tasks = False
            return self

        # ── Error Monitoring (disabled by default) ──
        def enable_errors(self) -> Integration.AdminModules:
            """Show the Error Monitoring page. Disabled by default -- opt in."""
            self._errors = True
            return self

        def disable_errors(self) -> Integration.AdminModules:
            """Hide the Error Monitoring page."""
            self._errors = False
            return self

        # ── Testing (disabled by default) ──
        def enable_testing(self) -> Integration.AdminModules:
            """Show the Testing page (test runner, coverage, assertions). Disabled by default -- opt in."""
            self._testing = True
            return self

        def disable_testing(self) -> Integration.AdminModules:
            """Hide the Testing page."""
            self._testing = False
            return self

        # ── Storage (disabled by default) ──
        def enable_storage(self) -> Integration.AdminModules:
            """Show the Storage page (file browser, backend analytics, health). Disabled by default -- opt in."""
            self._storage = True
            return self

        def disable_storage(self) -> Integration.AdminModules:
            """Hide the Storage page."""
            self._storage = False
            return self

        # ── Mailer (disabled by default) ──
        def enable_mailer(self) -> Integration.AdminModules:
            """Show the Mailer page (providers, config, templates, send test). Disabled by default -- opt in."""
            self._mailer = True
            return self

        def disable_mailer(self) -> Integration.AdminModules:
            """Hide the Mailer page."""
            self._mailer = False
            return self

        # ── Provider & Deployment (disabled by default) ──
        def enable_provider(self) -> Integration.AdminModules:
            """Show the Provider & Deployment page (Render, services, deploys, credentials). Disabled by default -- opt in."""
            self._provider = True
            return self

        def disable_provider(self) -> Integration.AdminModules:
            """Hide the Provider & Deployment page."""
            self._provider = False
            return self

        # ── API Keys ──
        def enable_api_keys(self) -> Integration.AdminModules:
            """Show the API Keys page."""
            self._api_keys = True
            return self

        def disable_api_keys(self) -> Integration.AdminModules:
            """Hide the API Keys page."""
            self._api_keys = False
            return self

        # ── Preferences ──
        def enable_preferences(self) -> Integration.AdminModules:
            """Show the Preferences page."""
            self._preferences = True
            return self

        def disable_preferences(self) -> Integration.AdminModules:
            """Hide the Preferences page."""
            self._preferences = False
            return self

        # ── Convenience ──
        def enable_all(self) -> Integration.AdminModules:
            """Enable every admin module (including monitoring & audit)."""
            for attr in self.__slots__:
                setattr(self, attr, True)
            return self

        def disable_all(self) -> Integration.AdminModules:
            """Disable every admin module."""
            for attr in self.__slots__:
                setattr(self, attr, False)
            return self

        def to_dict(self) -> dict[str, bool]:
            """Serialize to a dict consumed by AdminConfig."""
            return {
                "dashboard": self._dashboard,
                "orm": self._orm,
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

        def enable(self) -> Integration.AdminAudit:
            """Enable audit logging."""
            self._enabled = True
            return self

        def disable(self) -> Integration.AdminAudit:
            """Disable audit logging entirely."""
            self._enabled = False
            return self

        def max_entries(self, n: int) -> Integration.AdminAudit:
            """Set the maximum number of audit entries (FIFO eviction)."""
            self._max_entries = max(100, int(n))
            return self

        def log_logins(self, enabled: bool = True) -> Integration.AdminAudit:
            """Record LOGIN / LOGOUT / LOGIN_FAILED events."""
            self._log_logins = enabled
            return self

        def no_log_logins(self) -> Integration.AdminAudit:
            """Skip LOGIN / LOGOUT / LOGIN_FAILED events."""
            self._log_logins = False
            return self

        def log_views(self, enabled: bool = True) -> Integration.AdminAudit:
            """Record VIEW / LIST events."""
            self._log_views = enabled
            return self

        def no_log_views(self) -> Integration.AdminAudit:
            """Skip VIEW / LIST events."""
            self._log_views = False
            return self

        def log_searches(self, enabled: bool = True) -> Integration.AdminAudit:
            """Record SEARCH events."""
            self._log_searches = enabled
            return self

        def no_log_searches(self) -> Integration.AdminAudit:
            """Skip SEARCH events."""
            self._log_searches = False
            return self

        def exclude_actions(self, *actions: str) -> Integration.AdminAudit:
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

        def enable(self) -> Integration.AdminMonitoring:
            """Enable monitoring dashboard."""
            self._enabled = True
            return self

        def disable(self) -> Integration.AdminMonitoring:
            """Disable monitoring dashboard."""
            self._enabled = False
            return self

        def metrics(self, *names: str) -> Integration.AdminMonitoring:
            """
            Set which metric sections to collect.

            Valid values: ``"cpu"``, ``"memory"``, ``"disk"``,
            ``"network"``, ``"process"``, ``"python"``, ``"system"``,
            ``"health_checks"``.

            Pass no arguments to collect all metrics.
            """
            self._metrics = list(names) if names else list(self._ALL_METRICS)
            return self

        def all_metrics(self) -> Integration.AdminMonitoring:
            """Collect every available metric."""
            self._metrics = list(self._ALL_METRICS)
            return self

        def refresh_interval(self, seconds: int) -> Integration.AdminMonitoring:
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

        def show_overview(self) -> Integration.AdminSidebar:
            """Show the Overview section."""
            self._overview = True
            return self

        def hide_overview(self) -> Integration.AdminSidebar:
            """Hide the Overview section."""
            self._overview = False
            return self

        def show_data(self) -> Integration.AdminSidebar:
            """Show the Data section (ORM, Migrations)."""
            self._data = True
            return self

        def hide_data(self) -> Integration.AdminSidebar:
            """Hide the Data section."""
            self._data = False
            return self

        def show_system(self) -> Integration.AdminSidebar:
            """Show the System section (Monitoring, Workspace, Config)."""
            self._system = True
            return self

        def hide_system(self) -> Integration.AdminSidebar:
            """Hide the System section."""
            self._system = False
            return self

        def show_infrastructure(self) -> Integration.AdminSidebar:
            """Show the Infrastructure section (Containers, Pods)."""
            self._infrastructure = True
            return self

        def hide_infrastructure(self) -> Integration.AdminSidebar:
            """Hide the Infrastructure section."""
            self._infrastructure = False
            return self

        def show_security(self) -> Integration.AdminSidebar:
            """Show the Security section (Permissions, Audit, Admin Users)."""
            self._security = True
            return self

        def hide_security(self) -> Integration.AdminSidebar:
            """Hide the Security section."""
            self._security = False
            return self

        def show_models(self) -> Integration.AdminSidebar:
            """Show the Models section (per-model links)."""
            self._models = True
            return self

        def hide_models(self) -> Integration.AdminSidebar:
            """Hide the Models section."""
            self._models = False
            return self

        def show_devtools(self) -> Integration.AdminSidebar:
            """Show the DevTools section (Query Inspector, Tasks, Errors)."""
            self._devtools = True
            return self

        def hide_devtools(self) -> Integration.AdminSidebar:
            """Hide the DevTools section."""
            self._devtools = False
            return self

        def show_all(self) -> Integration.AdminSidebar:
            """Show every sidebar section."""
            for attr in self.__slots__:
                setattr(self, attr, True)
            return self

        def hide_all(self) -> Integration.AdminSidebar:
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

        def docker_host(self, host: str) -> Integration.AdminContainers:
            """Set Docker host (e.g. ``unix:///var/run/docker.sock`` or ``tcp://host:2375``)."""
            self._docker_host = host
            return self

        def docker_socket(self, path: str) -> Integration.AdminContainers:
            """Shorthand for ``docker_host('unix://<path>')``."""
            self._docker_host = f"unix://{path}"
            return self

        def allowed_actions(self, *actions: str) -> Integration.AdminContainers:
            """Set which container lifecycle actions are permitted."""
            self._allowed_actions = list(actions)
            return self

        def deny_actions(self, *actions: str) -> Integration.AdminContainers:
            """Deny specific actions (subtracted from allowed)."""
            self._denied_actions = list(actions)
            return self

        def log_tail(self, lines: int) -> Integration.AdminContainers:
            """Default number of log lines to fetch (default 200)."""
            self._log_tail = max(10, int(lines))
            return self

        def log_since(self, since: str) -> Integration.AdminContainers:
            """Default ``--since`` value for log fetching (e.g. ``'1h'``, ``'30m'``)."""
            self._log_since = since
            return self

        def refresh_interval(self, seconds: int) -> Integration.AdminContainers:
            """Auto-refresh interval for container metrics (min 5s)."""
            self._refresh_interval = max(5, int(seconds))
            return self

        def compose_files(self, *files: str) -> Integration.AdminContainers:
            """Explicit compose file paths to discover."""
            self._compose_files = list(files)
            return self

        def compose_project_dir(self, path: str) -> Integration.AdminContainers:
            """Set the compose project directory."""
            self._compose_project_dir = path
            return self

        def show_system_containers(self, enabled: bool = True) -> Integration.AdminContainers:
            """Show Docker system / infra containers (hidden by default)."""
            self._show_system_containers = enabled
            return self

        def enable_exec(self, enabled: bool = True) -> Integration.AdminContainers:
            """Allow ``docker exec`` from the admin UI."""
            self._enable_exec = enabled
            return self

        def disable_exec(self) -> Integration.AdminContainers:
            """Disable ``docker exec`` in the admin UI."""
            self._enable_exec = False
            return self

        def enable_prune(self, enabled: bool = True) -> Integration.AdminContainers:
            """Allow ``docker system prune`` from the admin UI."""
            self._enable_prune = enabled
            return self

        def disable_prune(self) -> Integration.AdminContainers:
            """Disable prune operations."""
            self._enable_prune = False
            return self

        def enable_build(self, enabled: bool = True) -> Integration.AdminContainers:
            """Allow ``docker build`` / ``compose build`` from the admin UI."""
            self._enable_build = enabled
            return self

        def disable_build(self) -> Integration.AdminContainers:
            """Disable build operations."""
            self._enable_build = False
            return self

        def enable_export(self, enabled: bool = True) -> Integration.AdminContainers:
            """Allow container filesystem export."""
            self._enable_export = enabled
            return self

        def disable_export(self) -> Integration.AdminContainers:
            """Disable container export."""
            self._enable_export = False
            return self

        def enable_image_actions(self, enabled: bool = True) -> Integration.AdminContainers:
            """Allow image pull / remove / tag operations."""
            self._enable_image_actions = enabled
            return self

        def disable_image_actions(self) -> Integration.AdminContainers:
            """Disable image operations."""
            self._enable_image_actions = False
            return self

        def enable_volume_actions(self, enabled: bool = True) -> Integration.AdminContainers:
            """Allow volume create / remove operations."""
            self._enable_volume_actions = enabled
            return self

        def disable_volume_actions(self) -> Integration.AdminContainers:
            """Disable volume operations."""
            self._enable_volume_actions = False
            return self

        def enable_network_actions(self, enabled: bool = True) -> Integration.AdminContainers:
            """Allow network create / remove operations."""
            self._enable_network_actions = enabled
            return self

        def disable_network_actions(self) -> Integration.AdminContainers:
            """Disable network operations."""
            self._enable_network_actions = False
            return self

        def read_only(self) -> Integration.AdminContainers:
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

        def kubeconfig(self, path: str) -> Integration.AdminPods:
            """Set path to kubeconfig file."""
            self._kubeconfig = path
            return self

        def namespace(self, ns: str) -> Integration.AdminPods:
            """Set the target Kubernetes namespace (default ``"default"``)."""
            self._namespace = ns
            return self

        def all_namespaces(self) -> Integration.AdminPods:
            """Query all namespaces."""
            self._namespace = "*"
            return self

        def contexts(self, *names: str) -> Integration.AdminPods:
            """Set allowed kubectl contexts."""
            self._contexts = list(names)
            return self

        def resources(self, *types: str) -> Integration.AdminPods:
            """Set which K8s resource types to display."""
            self._resources = list(types) if types else list(self._ALL_RESOURCES)
            return self

        def all_resources(self) -> Integration.AdminPods:
            """Display every supported K8s resource type."""
            self._resources = list(self._ALL_RESOURCES)
            return self

        def manifest_dirs(self, *dirs: str) -> Integration.AdminPods:
            """Set directories to scan for K8s manifest files."""
            self._manifest_dirs = list(dirs)
            return self

        def manifest_patterns(self, *patterns: str) -> Integration.AdminPods:
            """Set glob patterns for manifest files (default ``*.yaml``, ``*.yml``)."""
            self._manifest_patterns = list(patterns)
            return self

        def refresh_interval(self, seconds: int) -> Integration.AdminPods:
            """Auto-refresh interval for pod metrics (min 5s)."""
            self._refresh_interval = max(5, int(seconds))
            return self

        def log_tail(self, lines: int) -> Integration.AdminPods:
            """Default number of log lines to fetch."""
            self._log_tail = max(10, int(lines))
            return self

        def enable_logs(self, enabled: bool = True) -> Integration.AdminPods:
            """Allow pod log viewing."""
            self._enable_logs = enabled
            return self

        def enable_exec(self, enabled: bool = True) -> Integration.AdminPods:
            """Allow ``kubectl exec`` from the admin UI."""
            self._enable_exec = enabled
            return self

        def disable_exec(self) -> Integration.AdminPods:
            """Disable ``kubectl exec``."""
            self._enable_exec = False
            return self

        def enable_delete(self, enabled: bool = True) -> Integration.AdminPods:
            """Allow resource deletion."""
            self._enable_delete = enabled
            return self

        def disable_delete(self) -> Integration.AdminPods:
            """Disable resource deletion."""
            self._enable_delete = False
            return self

        def enable_scale(self, enabled: bool = True) -> Integration.AdminPods:
            """Allow deployment scaling."""
            self._enable_scale = enabled
            return self

        def disable_scale(self) -> Integration.AdminPods:
            """Disable deployment scaling."""
            self._enable_scale = False
            return self

        def enable_restart(self, enabled: bool = True) -> Integration.AdminPods:
            """Allow deployment rollout restart."""
            self._enable_restart = enabled
            return self

        def disable_restart(self) -> Integration.AdminPods:
            """Disable rollout restart."""
            self._enable_restart = False
            return self

        def enable_apply(self, enabled: bool = True) -> Integration.AdminPods:
            """Allow ``kubectl apply -f`` from the admin UI."""
            self._enable_apply = enabled
            return self

        def disable_apply(self) -> Integration.AdminPods:
            """Disable ``kubectl apply``."""
            self._enable_apply = False
            return self

        def read_only(self) -> Integration.AdminPods:
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

        def csrf_enabled(self, enabled: bool = True) -> Integration.AdminSecurity:
            """Enable or disable CSRF protection."""
            self._csrf_enabled = enabled
            return self

        def no_csrf(self) -> Integration.AdminSecurity:
            """Disable CSRF protection (NOT recommended for production)."""
            self._csrf_enabled = False
            return self

        def csrf_max_age(self, seconds: int) -> Integration.AdminSecurity:
            """Set CSRF token max age in seconds (default: 7200 = 2h)."""
            self._csrf_max_age = max(60, int(seconds))
            return self

        def csrf_token_length(self, length: int) -> Integration.AdminSecurity:
            """Set CSRF token random nonce length (default: 32)."""
            self._csrf_token_length = max(16, int(length))
            return self

        # ── Rate Limiting ─────────────────────────────────────────────

        def rate_limit_enabled(self, enabled: bool = True) -> Integration.AdminSecurity:
            """Enable or disable login rate limiting."""
            self._rate_limit_enabled = enabled
            return self

        def no_rate_limit(self) -> Integration.AdminSecurity:
            """Disable rate limiting (NOT recommended for production)."""
            self._rate_limit_enabled = False
            return self

        def rate_limit_max_attempts(self, n: int) -> Integration.AdminSecurity:
            """Max login attempts before lockout (default: 5)."""
            self._rate_limit_max_attempts = max(1, int(n))
            return self

        def rate_limit_window(self, seconds: int) -> Integration.AdminSecurity:
            """Rate limit window in seconds (default: 900 = 15min)."""
            self._rate_limit_window = max(10, int(seconds))
            return self

        def sensitive_op_limit(self, n: int) -> Integration.AdminSecurity:
            """Max sensitive operations per window (default: 30)."""
            self._sensitive_op_limit = max(1, int(n))
            return self

        def sensitive_op_window(self, seconds: int) -> Integration.AdminSecurity:
            """Sensitive operation window in seconds (default: 300 = 5min)."""
            self._sensitive_op_window = max(10, int(seconds))
            return self

        # ── Progressive Lockout ───────────────────────────────────────

        def progressive_lockout(self, enabled: bool = True) -> Integration.AdminSecurity:
            """Enable progressive lockout (escalating durations)."""
            self._progressive_lockout = enabled
            return self

        def lockout_tiers(self, tiers: list[list[int]]) -> Integration.AdminSecurity:
            """
            Set custom lockout tiers.

            Each tier is ``[failure_threshold, lockout_seconds]``.

            Default::

                [[5, 300], [10, 900], [20, 3600], [50, 86400]]
            """
            self._lockout_tiers = tiers
            return self

        # ── Password Policy ───────────────────────────────────────────

        def password_min_length(self, n: int) -> Integration.AdminSecurity:
            """Set minimum password length (default: 10)."""
            self._password_min_length = max(4, int(n))
            return self

        def password_max_length(self, n: int) -> Integration.AdminSecurity:
            """Set maximum password length (default: 128)."""
            self._password_max_length = max(32, int(n))
            return self

        def password_require_upper(self, required: bool = True) -> Integration.AdminSecurity:
            """Require at least one uppercase letter."""
            self._password_require_upper = required
            return self

        def password_require_lower(self, required: bool = True) -> Integration.AdminSecurity:
            """Require at least one lowercase letter."""
            self._password_require_lower = required
            return self

        def password_require_digit(self, required: bool = True) -> Integration.AdminSecurity:
            """Require at least one digit."""
            self._password_require_digit = required
            return self

        def password_require_special(self, required: bool = True) -> Integration.AdminSecurity:
            """Require at least one special character."""
            self._password_require_special = required
            return self

        def relaxed_password_policy(self) -> Integration.AdminSecurity:
            """Use relaxed password policy (length-only, min 8)."""
            self._password_min_length = 8
            self._password_require_upper = False
            self._password_require_lower = False
            self._password_require_digit = False
            self._password_require_special = False
            return self

        def strict_password_policy(self) -> Integration.AdminSecurity:
            """Use strict password policy (min 12, all character classes)."""
            self._password_min_length = 12
            self._password_require_upper = True
            self._password_require_lower = True
            self._password_require_digit = True
            self._password_require_special = True
            return self

        # ── Security Headers ──────────────────────────────────────────

        def security_headers_enabled(self, enabled: bool = True) -> Integration.AdminSecurity:
            """Enable or disable security header injection."""
            self._security_headers_enabled = enabled
            return self

        def no_security_headers(self) -> Integration.AdminSecurity:
            """Disable security headers."""
            self._security_headers_enabled = False
            return self

        def csp_template(self, template: str) -> Integration.AdminSecurity:
            """
            Set custom Content-Security-Policy template.

            Use ``{nonce}`` placeholder for per-request nonce injection.

            Default::

                "default-src 'self'; script-src 'self' {nonce}; ..."
            """
            self._csp_template = template
            return self

        def frame_options(self, value: str) -> Integration.AdminSecurity:
            """Set X-Frame-Options header (default: DENY)."""
            self._frame_options = value
            return self

        def permissions_policy(self, policy: str) -> Integration.AdminSecurity:
            """Set Permissions-Policy header."""
            self._permissions_policy = policy
            return self

        # ── Session ───────────────────────────────────────────────────

        def session_fixation_protection(self, enabled: bool = True) -> Integration.AdminSecurity:
            """Enable session fixation protection (regenerate session on login)."""
            self._session_fixation_protection = enabled
            return self

        # ── Event Tracking ────────────────────────────────────────────

        def event_tracker_max_events(self, n: int) -> Integration.AdminSecurity:
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
        modules: Optional[Integration.AdminModules] = None,
        audit: Optional[Integration.AdminAudit] = None,
        monitoring: Optional[Integration.AdminMonitoring] = None,
        sidebar: Optional[Integration.AdminSidebar] = None,
        containers: Optional[Integration.AdminContainers] = None,
        pods: Optional[Integration.AdminPods] = None,
        security: Optional[Integration.AdminSecurity] = None,
        # ── Legacy flat params (backward compat) ─────────────────
        enable_audit: bool | None = None,
        audit_max_entries: int = 10_000,
        enable_dashboard: bool | None = None,
        enable_orm: bool | None = None,
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
            ) -> Chain:
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
        def chain(cls) -> Chain:
            """Create an empty middleware chain."""
            return cls.Chain()

        @classmethod
        def defaults(cls) -> Chain:
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
        def production(cls) -> Chain:
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
        def minimal(cls) -> Chain:
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
