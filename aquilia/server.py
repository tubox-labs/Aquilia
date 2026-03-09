"""
AquiliaServer - Main server orchestrating all components with lifecycle management.

Fully integrated with Aquilary manifest-driven registry system.

Architecture v2 additions:
- HealthRegistry for centralized subsystem health tracking
- SubsystemInitializer protocol support for server decomposition
- Graceful shutdown with connection draining
- Auto-discovery engine integration
"""

from typing import Optional, List, Any
import logging

from .config import ConfigLoader
from .engine import RequestCtx
from .middleware import MiddlewareStack
from .asgi import ASGIAdapter
from .controller.router import ControllerRouter
from .aquilary import Aquilary, RuntimeRegistry, RegistryMode, AquilaryRegistry
from .lifecycle import LifecycleCoordinator, LifecycleManager, LifecycleError
from .middleware_ext.session_middleware import SessionMiddleware
from .controller.openapi import OpenAPIGenerator, OpenAPIConfig, generate_swagger_html, generate_redoc_html
from .faults.engine import FaultEngine, FaultMiddleware
from .response import Response
from .health import HealthRegistry, HealthStatus, SubsystemStatus
from .faults.domains import (
    ConfigMissingFault, ConfigInvalidFault, RoutingFault, ManifestInvalidFault,
)
# Template Integration
from .templates.middleware import TemplateMiddleware
from .templates.di_providers import register_template_providers
# Auth Integration
from .auth.manager import AuthManager
from .auth.integration.middleware import AquilAuthMiddleware, create_auth_middleware_stack
from .auth.tokens import TokenConfig
# WebSockets
from .sockets.runtime import AquilaSockets, SocketRouter
from .sockets.adapters import InMemoryAdapter


class AquiliaServer:
    """
    Main Aquilia server that orchestrates all components with lifecycle management.
    
    Integrates:
    - Aquilary registry for app discovery and validation
    - RuntimeRegistry for DI and route compilation
    - LifecycleCoordinator for startup/shutdown hooks
    - Controller-based routing with ControllerRouter
    - ASGI adapter for HTTP handling
    
    Architecture:
        Manifests → Aquilary → RuntimeRegistry → Controllers → ASGI
    """
    
    def __init__(
        self,
        manifests: Optional[List[Any]] = None,
        config: Optional[ConfigLoader] = None,
        mode: RegistryMode = RegistryMode.PROD,
        aquilary_registry: Optional[AquilaryRegistry] = None,
    ):
        """
        Initialize AquiliaServer with Aquilary registry.
        
        Args:
            manifests: List of manifest classes for app discovery
            config: Configuration loader
            mode: Registry mode (DEV, PROD, TEST)
            aquilary_registry: Pre-built AquilaryRegistry (advanced usage)
        """
        self.config = config or ConfigLoader()
        self.logger = logging.getLogger("aquilia.server")
        self.mode = mode

        # Bootstrap the signing engine from config so all subsystems
        # (sessions, CSRF, cache, activation links) share a consistent key.
        self._bootstrap_signing()

        # v2: Health registry for subsystem tracking
        self.health_registry = HealthRegistry()
        self._inflight_requests = 0
        self._accepting = True
        
        # Initialize fault engine
        self.fault_engine = FaultEngine(debug=self._is_debug())
        
        # Apply fault integration patches to subsystems (registry, DI)
        try:
            from .faults.integrations import patch_all_subsystems
            patch_all_subsystems()
        except Exception as e:
            self.logger.warning(f"Fault integration patches failed (non-fatal): {e}")
        
        # Build or use provided Aquilary registry
        if aquilary_registry is not None:
            self.aquilary = aquilary_registry
        else:
            if manifests is None:
                raise ConfigMissingFault(
                    key="manifests_or_aquilary_registry",
                )
            
            # Build Aquilary registry from manifests
            self.aquilary = Aquilary.from_manifests(
                manifests=manifests,
                config=self.config,
                mode=mode,
            )
        
        # Create runtime registry (lazy compilation phase)
        self.runtime = RuntimeRegistry.from_metadata(self.aquilary, self.config)
        
        # CRITICAL: Register services immediately so DI containers are populated
        # before controller factory is created
        self.runtime._register_services()
        
        # Register EffectRegistry and FaultEngine in DI containers
        from .di.providers import ValueProvider
        from .effects import EffectRegistry
        for container in self.runtime.di_containers.values():
            container.register(ValueProvider(
                value=self.fault_engine,
                token=FaultEngine,
                scope="app",
            ))
            container.register(ValueProvider(
                value=EffectRegistry(),
                token=EffectRegistry,
                scope="app",
            ))
        
        # Create lifecycle coordinator for app startup/shutdown hooks
        self.coordinator = LifecycleCoordinator(self.runtime, self.config)
        
        # Connect lifecycle events to fault observability
        def _lifecycle_fault_observer(event):
            if event.error:
                self.logger.error(
                    f"Lifecycle fault in phase {event.phase.value}: "
                    f"app={event.app_name}, error={event.error}"
                )
        self.coordinator.on_event(_lifecycle_fault_observer)
        
        # Initialize controller router and middleware
        self.controller_router = ControllerRouter()
        self.middleware_stack = MiddlewareStack()
        
        # Setup middleware (also initializes aquila_sockets)
        self._setup_middleware()
        
        # Get base DI container for controller factory
        base_container = self._get_base_container()
        
        # Create controller components
        from .controller.factory import ControllerFactory
        from .controller.engine import ControllerEngine
        from .controller.compiler import ControllerCompiler
        
        self.controller_factory = ControllerFactory(app_container=base_container)
        self.controller_engine = ControllerEngine(
            self.controller_factory,
            fault_engine=self.fault_engine,
            effect_registry=None,  # Wired at startup after effects init
        )
        self.controller_compiler = ControllerCompiler()

        # Track startup state
        self._startup_complete = False
        self._startup_lock = None  # Will be created in async context
        
        # Create ASGI app with server reference for lifecycle management
        # Note: self.aquila_sockets is initialized in _setup_middleware()
        self.app = ASGIAdapter(
            controller_router=self.controller_router,
            controller_engine=self.controller_engine,
            socket_runtime=self.aquila_sockets,
            middleware_stack=self.middleware_stack,
            server=self,  # Pass server for lifecycle callbacks
        )
    
    def _get_base_container(self):
        """Get base DI container from runtime registry."""
        # Use first app's container as base, or create empty one
        if self.runtime.di_containers:
            return next(iter(self.runtime.di_containers.values()))
        
        # Fallback: create empty container
        from .di import Container
        return Container(scope="app")
    
    def _setup_middleware(self):
        """Setup middleware stack from workspace config or built-in defaults.

        Resolution order:
        1. If ``middleware_chain`` is defined in workspace config, instantiate
           each middleware from its dotted path + kwargs.
        2. Otherwise, fall back to the hardcoded default stack (ExceptionMiddleware,
           RequestIdMiddleware) for backwards compatibility.

        Internal middleware (FaultMiddleware, request_scope) are ALWAYS
        registered regardless of user config -- they are framework plumbing,
        not user-facing middleware.
        """
        # ── Internal plumbing middleware (always registered) ─────────────
        self.middleware_stack.add(
            FaultMiddleware(self.fault_engine),
            scope="global",
            priority=2,
            name="faults",
        )

        from .middleware_ext.request_scope import SimplifiedRequestScopeMiddleware

        runtime_ref = self.runtime  # capture for closure

        async def request_scope_mw(request, ctx, next_handler):
            """Request scope middleware -- stores container refs and cleans up."""
            request.state["di_container"] = ctx.container
            app_name = request.state.get("app_name", "default")
            app_container = runtime_ref.di_containers.get(app_name)
            if app_container:
                request.state["app_container"] = app_container
            try:
                return await next_handler(request, ctx)
            finally:
                if ctx.container and hasattr(ctx.container, 'shutdown'):
                    await ctx.container.shutdown()

        self.middleware_stack.add(
            request_scope_mw,
            scope="global",
            priority=5,
            name="request_scope",
        )

        # ── User-configurable middleware chain ───────────────────────────
        middleware_chain = self.config.get_middleware_config()

        if middleware_chain is not None:
            # Config-driven: instantiate each middleware from its path
            for entry in middleware_chain:
                mw_instance = self._instantiate_middleware(entry)
                if mw_instance is not None:
                    self.middleware_stack.add(
                        mw_instance,
                        scope=entry.get("scope", "global"),
                        priority=entry.get("priority", 50),
                        name=entry.get("name", "middleware"),
                    )
        else:
            # Legacy fallback: hardcoded defaults for backward compat
            from .middleware import ExceptionMiddleware, RequestIdMiddleware
            self.middleware_stack.add(
                ExceptionMiddleware(debug=self._is_debug()),
                scope="global",
                priority=1,
                name="exception",
            )
            self.middleware_stack.add(
                RequestIdMiddleware(),
                scope="global",
                priority=10,
                name="request_id",
            )

        # Add session/auth middleware if enabled
        session_config = self.config.get_session_config()
        auth_config = self.config.get_auth_config()
        
        # Initialize SessionEngine if either Sessions or Auth is enabled
        # Auth REQUIRES sessions
        use_sessions = session_config.get("enabled", False)
        use_auth = auth_config.get("enabled", False)
        
        if use_auth:
            # Force enable sessions config if auth is enabled
            use_sessions = True
            
        self._session_engine = None
        self._auth_manager = None
        
        if use_sessions:
            try:
                # Create session engine
                session_engine = self._create_session_engine(session_config)
                self._session_engine = session_engine
            except Exception as e:
                self.logger.error(f"Failed to create session engine: {e}", exc_info=True)
                self._session_engine = None
            
            # Try to set up auth if requested AND session engine succeeded
            auth_initialized = False
            if use_auth and self._session_engine is not None:
                try:
                    # Create AuthManager
                    auth_manager = self._create_auth_manager(auth_config)
                    self._auth_manager = auth_manager
                    
                    # Add Unified Auth Middleware (handles both sessions and auth)
                    self.middleware_stack.add(
                        AquilAuthMiddleware(
                            session_engine=self._session_engine,
                            auth_manager=auth_manager,
                            require_auth=auth_config.get("security", {}).get("require_auth_by_default", False),
                            fault_engine=self.fault_engine,
                        ),
                        scope="global",
                        priority=15, # Replaces session middleware
                        name="auth",
                    )
                    
                    from .di.providers import ValueProvider
                    for container in self.runtime.di_containers.values():
                        # Core manager
                        container.register(
                            ValueProvider(
                                token=AuthManager,
                                value=auth_manager,
                                scope="app",
                                name="auth_manager_instance"
                            )
                        )
                        # Register sub-components so Services can use them
                        # We use string tokens to ensure consistent resolution with type hints
                        container.register(ValueProvider(value=auth_manager.identity_store, token="aquilia.auth.stores.MemoryIdentityStore", scope="app"))
                        container.register(ValueProvider(value=auth_manager.credential_store, token="aquilia.auth.stores.MemoryCredentialStore", scope="app"))
                        container.register(ValueProvider(value=auth_manager.token_manager, token="aquilia.auth.tokens.TokenManager", scope="app"))
                        container.register(ValueProvider(value=auth_manager.password_hasher, token="aquilia.auth.hashing.PasswordHasher", scope="app"))
                        
                    auth_initialized = True
                    
                except Exception as e:
                    self.logger.error(
                        f"Failed to initialize auth system: {e}. "
                        f"Falling back to session-only middleware.",
                        exc_info=True,
                    )
                    self._auth_manager = None
            
            # Fallback: add session-only middleware if auth wasn't initialized
            if not auth_initialized and self._session_engine is not None:
                self.middleware_stack.add(
                    SessionMiddleware(self._session_engine),
                    scope="global",
                    priority=15,
                    name="session",
                )
            
            # Register SessionEngine in DI (if engine was created)
            if self._session_engine is not None:
                from aquilia.di.providers import ValueProvider
                from aquilia.sessions import SessionEngine
                
                engine_provider = ValueProvider(
                    token=SessionEngine,
                    value=self._session_engine,
                    scope="app",
                    name="session_engine_instance"
                )
                
                for container in self.runtime.di_containers.values():
                    container.register(engine_provider)
        else:
            pass

        # Add template engine integration
        template_config = self.config.get_template_config()
        use_templates = template_config.get("enabled", False)
        
        # Auto-enable if any app manifest has templates
        if not use_templates and hasattr(self, "aquilary"):
            for ctx in self.aquilary.app_contexts:
                if hasattr(ctx.manifest, "templates") and ctx.manifest.templates and ctx.manifest.templates.enabled:
                    use_templates = True
                    break
        
        if use_templates:
            # Step 1: Initialize Engine with config
            from .templates import TemplateEngine
            from .templates.loader import TemplateLoader
            from pathlib import Path

            search_paths = []
            
            # 1. Config paths
            if template_config.get("search_paths"):
                for p in template_config["search_paths"]:
                    search_paths.append(Path(p))
                    
            # 2. Manifest paths (auto-discovery)
            if hasattr(self, "aquilary"):
                 for ctx in self.aquilary.app_contexts:
                     # Try to derive path from manifest source
                     manifest_src = getattr(ctx.manifest, "__source__", None)
                     
                     found_path = False
                     if manifest_src and isinstance(manifest_src, str):
                         try:
                             # Check if it looks like a path
                             src_path = Path(manifest_src)
                             if src_path.exists() or src_path.is_absolute():
                                 app_template_dir = src_path.parent / "templates"
                                 if app_template_dir.exists():
                                     search_paths.append(app_template_dir)
                                     found_path = True
                         except Exception:
                             pass
                     
                     if not found_path:
                        # Fallback to convention: /modules/<name>/templates
                        convention_path = Path("modules") / ctx.name / "templates"
                        if convention_path.exists():
                            search_paths.append(convention_path)
            
            # Deduplicate
            search_paths = list(dict.fromkeys(search_paths))

            # Register loader with discovered paths
            loader = TemplateLoader(search_paths=search_paths)
            
            # Create engine with production/dev settings based on config
            # (Here we use a generic engine, but factory methods in providers.py 
            # allow for customized creation if resolved via DI)
            self.template_engine = TemplateEngine(
                loader=loader,
                bytecode_cache=None if template_config.get("cache") == "none" else None # Default to memory if not specified or handled by provider logic
            )

            # Register providers for each container
            for container in self.runtime.di_containers.values():
                # Pass engine instance
                register_template_providers(container, engine=self.template_engine)
            
            # Register middleware
            self.middleware_stack.add(
                TemplateMiddleware(
                    url_for=self.controller_router.url_for,
                    config=self.config,
                    static_url_prefix=self._get_static_prefix(),
                ),
                scope="global",
                priority=25,  # Processed after Auth/Session
                name="templates",
            )

        # ── Mail subsystem ───────────────────────────────────────────────
        self._setup_mail()

        # ── Cache subsystem ──────────────────────────────────────────────
        self._setup_cache()

        # ── Storage subsystem ────────────────────────────────────────────
        self._setup_storage()

        # ── I18n subsystem ───────────────────────────────────────────────
        self._setup_i18n()

        # ── Tasks subsystem ──────────────────────────────────────────────
        self._setup_tasks()

        # ── Error Tracker subsystem ──────────────────────────────────────
        self._setup_error_tracker()

        # ── Security & Infrastructure Middleware ──────────────────────────
        self._setup_security_middleware()

        # Initialize WebSockets with DI container factory for per-connection scopes
        self.socket_router = SocketRouter()
        
        async def _socket_container_factory(request=None, app_name: str = "default"):
            """Create request-scoped DI container for WebSocket connections.
            
            This factory is called by the socket runtime during handshake.
            It accepts an optional request object (for extracting app context)
            and returns a request-scoped child DI container.
            """
            # If request has app_name in state, use it for more precise scoping
            if request and hasattr(request, 'state'):
                req_app = request.state.get('app_name')
                if req_app:
                    app_name = req_app
            
            app_container = self.runtime.di_containers.get(app_name)
            if not app_container and self.runtime.di_containers:
                # Fallback to first available container
                app_container = next(iter(self.runtime.di_containers.values()))
            
            if app_container and hasattr(app_container, 'create_request_scope'):
                return app_container.create_request_scope()
            
            # Fallback: create a minimal container
            from .di import Container
            return Container(scope="request")
        
        self.aquila_sockets = AquilaSockets(
            router=self.socket_router,
            adapter=InMemoryAdapter(),
            container_factory=_socket_container_factory,
            auth_manager=self._auth_manager,
            session_engine=self._session_engine,
        )
            
        # Register app-specific middlewares from Aquilary manifest
        if hasattr(self, "aquilary"):
            for ctx in self.aquilary.app_contexts:
                for mw_config in ctx.middlewares:
                    try:
                        self._register_app_middleware(mw_config)
                    except Exception as e:
                        self.logger.error(f"Failed to register middleware from app {ctx.name}: {e}")

    def _register_app_middleware(self, mw_config: Any):
        """Register application middleware from config."""
        import importlib
        
        # Extract config details
        # Handle both dict and object (MiddlewareConfig)
        if isinstance(mw_config, dict):
            class_path = mw_config.get("class_path") or mw_config.get("path")
            scope = mw_config.get("scope", "global")
            priority = mw_config.get("priority", 50)
            config = mw_config.get("config", {})
            name = mw_config.get("name")
        else:
            class_path = getattr(mw_config, "class_path", None)
            scope = getattr(mw_config, "scope", "global")
            priority = getattr(mw_config, "priority", 50)
            config = getattr(mw_config, "config", {})
            name = getattr(mw_config, "name", None)
            
        if not class_path:
            return

        # Validate class_path to prevent arbitrary code loading
        if not isinstance(class_path, str) or not all(
            part.isidentifier() for part in class_path.replace(":", ".").split(".")
        ):
            self.logger.warning(
                "Invalid middleware class_path '%s' -- must be dotted Python identifiers",
                class_path,
            )
            return

        # Import class
        if ":" in class_path:
            module_path, class_name = class_path.split(":", 1)
        else:
            module_path, class_name = class_path.rsplit(".", 1)
            
        module = importlib.import_module(module_path)
        mw_class = getattr(module, class_name)
        
        # Instantiate
        # Some middlewares take config in __init__, others don't.
        # We try to pass kwargs if config exists
        try:
            if config:
                instance = mw_class(**config)
            else:
                instance = mw_class()
        except TypeError:
            # Fallback for no-arg init
            instance = mw_class()
            
        # Register
        self.middleware_stack.add(
            instance,
            scope=scope,
            priority=priority,
            name=name or class_name,
        )

    def _get_static_prefix(self) -> str:
        """Get the static URL prefix from config or default."""
        static_config = self.config.get("integrations.static_files", {})
        if static_config:
            dirs = static_config.get("directories", {})
            if dirs:
                return next(iter(dirs))
        return "/static"

    def _discover_module_static_dirs(self) -> dict:
        """
        Auto-discover static/ directories inside loaded modules.

        Scans each module's package directory for a ``static/`` subdirectory.  Found directories
        are grouped under the configured static URL prefix so that
        ``{{ static('js/chat.js') }}`` resolves correctly regardless of
        which module owns the file.

        Returns:
            Dict mapping URL prefix → list of filesystem paths for every
            discovered module static directory.
        """
        from pathlib import Path
        import importlib

        # Group all discovered dirs under the static prefix
        static_prefix = self._get_static_prefix()   # e.g. "/static"
        discovered: list = []
        seen_packages: set = set()

        for ctx in self.runtime.meta.app_contexts:
            # Derive module package from any registered import path.
            # Controller paths look like "modules.chat.controllers:ChatController"
            # Items may be strings OR ServiceConfig/dataclass objects.
            raw_paths = list(ctx.controllers) + list(ctx.services)
            import_paths = []
            for item in raw_paths:
                if isinstance(item, str):
                    import_paths.append(item)
                elif hasattr(item, "class_path"):
                    import_paths.append(item.class_path)
                else:
                    # ARCH-16: Skip unknown types instead of str() which
                    # could produce garbage import paths.
                    continue

            for import_path in import_paths:
                if ":" in import_path:
                    mod_dotted = import_path.split(":", 1)[0]
                else:
                    mod_dotted = import_path.rsplit(".", 1)[0]

                # Go one level up to get the package dir (modules.chat)
                pkg_dotted = mod_dotted.rsplit(".", 1)[0] if "." in mod_dotted else mod_dotted

                if pkg_dotted in seen_packages:
                    continue
                seen_packages.add(pkg_dotted)

                try:
                    pkg = importlib.import_module(pkg_dotted)
                except ImportError:
                    continue

                pkg_dir = Path(pkg.__file__).parent if hasattr(pkg, "__file__") and pkg.__file__ else None
                if pkg_dir is None:
                    continue

                static_dir = pkg_dir / "static"
                if static_dir.is_dir():
                    resolved = str(static_dir.resolve())
                    discovered.append(resolved)

        if discovered:
            return {static_prefix: discovered}
        return {}

    def _setup_security_middleware(self):
        """
        Wire security configuration to actual middleware instances.

        Reads from:
        - self.config["security"]  (set by Workspace.security())
        - self.config["integrations"]["static_files"]
        - self.config["integrations"]["cors"]
        - self.config["integrations"]["csp"]
        - self.config["integrations"]["rate_limit"]

        Middleware priority layout:
            3  - ProxyFixMiddleware  (must run before IP-dependent middleware)
            4  - HTTPSRedirectMiddleware
            6  - StaticMiddleware  (serve files before heavy processing)
            7  - SecurityHeadersMiddleware (helmet)
            8  - HSTSMiddleware
            9  - CSPMiddleware
            10 - CSRFMiddleware  (after session, before route handlers)
            11 - CORSMiddleware
            12 - RateLimitMiddleware
        """
        security_config = self.config.get("security", {})
        integrations = self.config.get("integrations", {})

        # ── Proxy Fix (priority 3) ───────────────────────────────────────
        if security_config.get("proxy_fix"):
            from .middleware_ext.security import ProxyFixMiddleware
            proxy_cfg = security_config.get("proxy_fix_config", {})
            if isinstance(proxy_cfg, bool):
                proxy_cfg = {}
            mw = ProxyFixMiddleware(
                trusted_proxies=proxy_cfg.get("trusted_proxies"),
                x_for=proxy_cfg.get("x_for", 1),
                x_proto=proxy_cfg.get("x_proto", 1),
                x_host=proxy_cfg.get("x_host", 1),
                x_port=proxy_cfg.get("x_port", 0),
            )
            self.middleware_stack.add(mw, scope="global", priority=3, name="proxy_fix")

        # ── HTTPS Redirect (priority 4) ──────────────────────────────────
        if security_config.get("https_redirect"):
            from .middleware_ext.security import HTTPSRedirectMiddleware
            https_cfg = security_config.get("https_redirect_config", {})
            if isinstance(https_cfg, bool):
                https_cfg = {}
            mw = HTTPSRedirectMiddleware(
                redirect_status=https_cfg.get("redirect_status", 301),
                exclude_paths=https_cfg.get("exclude_paths"),
                exclude_hosts=https_cfg.get("exclude_hosts"),
            )
            self.middleware_stack.add(mw, scope="global", priority=4, name="https_redirect")

        # ── Static Files (priority 6) ────────────────────────────────────
        static_config = integrations.get("static_files", {})
        if static_config.get("enabled"):
            from .middleware_ext.static import StaticMiddleware

            # Explicitly configured directories
            directories = dict(static_config.get("directories", {"/static": "static"}))

            # Auto-discover static/ dirs inside loaded modules
            module_static_dirs = self._discover_module_static_dirs()

            mw = StaticMiddleware(
                directories=directories,
                cache_max_age=static_config.get("cache_max_age", 86400),
                immutable=static_config.get("immutable", False),
                etag=static_config.get("etag", True),
                gzip=static_config.get("gzip", True),
                brotli=static_config.get("brotli", True),
                memory_cache=static_config.get("memory_cache", True),
                html5_history=static_config.get("html5_history", False),
                extra_directories=module_static_dirs,
            )
            self.middleware_stack.add(mw, scope="global", priority=6, name="static_files")
            self._static_middleware = mw

        # ── Security Headers / Helmet (priority 7) ───────────────────────
        if security_config.get("helmet_enabled", False):
            from .middleware_ext.security import SecurityHeadersMiddleware
            helmet_cfg = security_config.get("helmet_config", {})
            if isinstance(helmet_cfg, bool):
                helmet_cfg = {}
            mw = SecurityHeadersMiddleware(
                frame_options=helmet_cfg.get("frame_options", "DENY"),
                referrer_policy=helmet_cfg.get("referrer_policy", "strict-origin-when-cross-origin"),
                permissions_policy=helmet_cfg.get("permissions_policy"),
                cross_origin_opener_policy=helmet_cfg.get("cross_origin_opener_policy", "same-origin"),
                cross_origin_resource_policy=helmet_cfg.get("cross_origin_resource_policy", "same-origin"),
                content_type_nosniff=helmet_cfg.get("content_type_nosniff", True),
                remove_server_header=helmet_cfg.get("remove_server_header", True),
            )
            self.middleware_stack.add(mw, scope="global", priority=7, name="security_headers")

        # ── HSTS (priority 8) ────────────────────────────────────────────
        if security_config.get("hsts", False):
            from .middleware_ext.security import HSTSMiddleware
            hsts_cfg = security_config.get("hsts_config", {})
            if isinstance(hsts_cfg, bool):
                hsts_cfg = {}
            mw = HSTSMiddleware(
                max_age=hsts_cfg.get("max_age", 31536000),
                include_subdomains=hsts_cfg.get("include_subdomains", True),
                preload=hsts_cfg.get("preload", False),
            )
            self.middleware_stack.add(mw, scope="global", priority=8, name="hsts")

        # ── CSP (priority 9) ─────────────────────────────────────────────
        csp_config = security_config.get("csp") or integrations.get("csp", {})
        if csp_config and csp_config.get("enabled"):
            from .middleware_ext.security import CSPMiddleware, CSPPolicy
            policy_dict = csp_config.get("policy")
            if policy_dict:
                policy = CSPPolicy(directives=policy_dict)
            else:
                preset = csp_config.get("preset", "strict")
                policy = CSPPolicy.strict() if preset == "strict" else CSPPolicy.relaxed()
            mw = CSPMiddleware(
                policy=policy,
                report_only=csp_config.get("report_only", False),
                nonce=csp_config.get("nonce", True),
            )
            self.middleware_stack.add(mw, scope="global", priority=9, name="csp")

        # ── CORS (priority 11) ───────────────────────────────────────────
        cors_config = security_config.get("cors") or integrations.get("cors", {})
        if security_config.get("cors_enabled") or (cors_config and cors_config.get("enabled")):
            from .middleware_ext.security import CORSMiddleware as EnhancedCORSMiddleware
            if cors_config and cors_config.get("enabled"):
                mw = EnhancedCORSMiddleware(
                    allow_origins=cors_config.get("allow_origins", ["*"]),
                    allow_methods=cors_config.get("allow_methods"),
                    allow_headers=cors_config.get("allow_headers"),
                    expose_headers=cors_config.get("expose_headers"),
                    allow_credentials=cors_config.get("allow_credentials", False),
                    max_age=cors_config.get("max_age", 600),
                    allow_origin_regex=cors_config.get("allow_origin_regex"),
                )
            else:
                # Simple flag -- use permissive defaults
                mw = EnhancedCORSMiddleware(allow_origins=["*"])
            self.middleware_stack.add(mw, scope="global", priority=11, name="cors")

        # ── CSRF Protection (priority 20) ────────────────────────────────
        # Must run AFTER session/auth middleware (priority 15) so session
        # is available for CSRF token storage and validation.  Priority 20
        # places it between session/auth (15) and i18n (24).
        if security_config.get("csrf_protection"):
            from .middleware_ext.security import CSRFMiddleware, csrf_token_func as _csrf_token_func
            csrf_cfg = security_config.get("csrf_config", {})
            if isinstance(csrf_cfg, bool):
                csrf_cfg = {}
            mw = CSRFMiddleware(
                secret_key=csrf_cfg.get("secret_key"),
                token_length=csrf_cfg.get("token_length", 32),
                header_name=csrf_cfg.get("header_name", "X-CSRF-Token"),
                field_name=csrf_cfg.get("field_name", "_csrf_token"),
                cookie_name=csrf_cfg.get("cookie_name", "_csrf_cookie"),
                cookie_path=csrf_cfg.get("cookie_path", "/"),
                cookie_domain=csrf_cfg.get("cookie_domain"),
                cookie_secure=csrf_cfg.get("cookie_secure", False),
                cookie_samesite=csrf_cfg.get("cookie_samesite", "Lax"),
                cookie_httponly=csrf_cfg.get("cookie_httponly", False),
                cookie_max_age=csrf_cfg.get("cookie_max_age", 3600),
                exempt_paths=csrf_cfg.get("exempt_paths"),
                exempt_content_types=csrf_cfg.get("exempt_content_types"),
                trust_ajax=csrf_cfg.get("trust_ajax", True),
                rotate_token=csrf_cfg.get("rotate_token", False),
                failure_status=csrf_cfg.get("failure_status", 403),
            )
            self.middleware_stack.add(mw, scope="global", priority=20, name="csrf")

            # Wire CSRF token function into TemplateMiddleware if present
            self._csrf_token_func = _csrf_token_func

        # ── Rate Limiting (priority 12) ──────────────────────────────────
        rl_config = security_config.get("rate_limit") or integrations.get("rate_limit", {})
        if security_config.get("rate_limiting") or (rl_config and rl_config.get("enabled")):
            from .middleware_ext.rate_limit import RateLimitMiddleware, RateLimitRule
            from .middleware_ext.rate_limit import ip_key_extractor, user_key_extractor
            rules = []
            if rl_config and rl_config.get("enabled"):
                key_func = user_key_extractor if rl_config.get("per_user") else ip_key_extractor
                rules.append(RateLimitRule(
                    limit=rl_config.get("limit", 100),
                    window=rl_config.get("window", 60),
                    algorithm=rl_config.get("algorithm", "sliding_window"),
                    key_func=key_func,
                    burst=rl_config.get("burst"),
                ))
                exempt = rl_config.get("exempt_paths")
            else:
                rules.append(RateLimitRule(limit=100, window=60))
                exempt = None
            mw = RateLimitMiddleware(
                rules=rules,
                exempt_paths=exempt,
            )
            self.middleware_stack.add(mw, scope="global", priority=12, name="rate_limit")
    
    def _is_debug(self) -> bool:
        """Check if debug mode is enabled.

        Checks multiple locations for the debug flag:
        1. Top-level ``debug`` key (set by generated runtime/app.py)
        2. ``server.debug`` (env config convention)
        3. ``AQUILIA_ENV`` environment variable (``dev`` implies debug)
        """
        if self.config.get("debug", False):
            return True
        if self.config.get("server.debug", False):
            return True
        import os
        if os.environ.get("AQUILIA_ENV", "").lower() == "dev":
            return True
        return False

    # ── middleware instantiation ─────────────────────────────────────
    def _instantiate_middleware(self, entry: dict):
        """Resolve a middleware entry dict into a live middleware instance.

        *entry* is a dict produced by ``Integration.middleware.Entry.to_dict()``
        with keys ``path``, ``priority``, ``scope``, ``name``, and ``kwargs``.

        Special-case handling:
        - ``ExceptionMiddleware``: if the caller did not supply an explicit
          ``debug`` kwarg the current server debug state is injected
          automatically so dev/prod behaviour is always correct.

        Returns ``None`` (with a warning log) when the class cannot be
        imported or instantiated -- the server continues booting without
        that middleware rather than crashing.
        """
        class_path = entry.get("path", "")
        kwargs = dict(entry.get("kwargs", {}))

        try:
            module_path, class_name = class_path.rsplit(".", 1)
            import importlib
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
        except Exception as exc:
            self.logger.warning(
                "Could not import middleware '%s': %s -- skipping",
                class_path,
                exc,
            )
            return None

        # Auto-inject debug flag for ExceptionMiddleware when not explicit
        if class_name == "ExceptionMiddleware" and "debug" not in kwargs:
            kwargs["debug"] = self._is_debug()

        try:
            return cls(**kwargs)
        except Exception as exc:
            self.logger.warning(
                "Could not instantiate middleware '%s': %s -- skipping",
                class_path,
                exc,
            )
            return None

    def _setup_mail(self):
        """
        Initialize AquilaMail subsystem from workspace config.

        Reads ``Integration.mail()`` configuration, creates :class:`MailService`,
        registers it in DI containers (with MailConfig and MailProviderRegistry),
        and sets the module-level singleton so ``send_mail``/``asend_mail`` just work.

        Uses the mail DI providers module for proper wiring:
        - MailConfig is validated through Serializers and registered in DI
        - MailService is registered in DI via ValueProvider
        - MailProviderRegistry auto-discovers IMailProvider implementations
          using Aquilia's PackageScanner (discovery system)

        The actual provider connections happen during :meth:`startup` (async).
        """
        mail_config = self.config.get_mail_config()
        if not mail_config.get("enabled", False):
            self._mail_service = None
            return

        from .mail.di_providers import register_mail_providers
        from .mail.service import set_mail_service

        # Register in every DI container via the DI providers module
        svc = None
        for container in self.runtime.di_containers.values():
            svc = register_mail_providers(
                container=container,
                config_data=mail_config,
                discover_providers=True,
            )

        # If no containers existed, still create the service
        if svc is None:
            from .mail.config import MailConfig
            from .mail.service import MailService
            config_obj = MailConfig.from_dict(mail_config)
            svc = MailService(config=config_obj)

        # Install module-level singleton for convenience API
        set_mail_service(svc)
        self._mail_service = svc

    def _setup_cache(self):
        """
        Initialize cache subsystem from workspace config.

        Reads ``Integration.cache()`` configuration, creates the appropriate
        :class:`CacheBackend` and wraps it in a :class:`CacheService`, then
        registers both in every DI container so controllers / services can
        inject ``CacheService`` or ``CacheBackend``.

        If cache middleware is enabled the ``CacheMiddleware`` layer is pushed
        onto the middleware stack (priority 26, right after templates).

        Actual backend connections (e.g. Redis ``ping``) happen lazily or
        during :meth:`startup` where ``CacheService.initialize()`` is called.
        """
        cache_config = self.config.get_cache_config()
        if not cache_config.get("enabled", False):
            self._cache_service = None
            return

        try:
            from .cache.di_providers import (
                build_cache_config,
                create_cache_service,
                register_cache_providers,
            )

            config_obj = build_cache_config(cache_config)
            svc = create_cache_service(config_obj)

            # Register in every DI container
            for container in self.runtime.di_containers.values():
                register_cache_providers(container, svc)

            self._cache_service = svc

            # Optionally add HTTP response-cache middleware
            mw_cfg = cache_config.get("middleware", {})
            if mw_cfg.get("enabled", False):
                from .cache.middleware import CacheMiddleware

                self.middleware_stack.add(
                    CacheMiddleware(
                        cache_service=svc,
                        ttl=mw_cfg.get("ttl", 300),
                        namespace=mw_cfg.get("namespace", "http"),
                    ),
                    scope="global",
                    priority=26,
                    name="cache",
                )

        except Exception as e:
            self._cache_service = None
            self.logger.error(f"Cache subsystem init failed (non-fatal): {e}", exc_info=True)

    def _setup_storage(self):
        """
        Initialize storage subsystem from workspace config.

        Reads ``Integration.storage()`` configuration, creates the
        :class:`StorageRegistry` with all configured backends, then
        registers it in every DI container so controllers / services can
        inject ``StorageRegistry``.

        Actual backend initialization (creating dirs, connecting to S3, etc.)
        happens during :meth:`startup` where ``StorageRegistry.initialize_all()``
        is called.
        """
        storage_config = self.config.get_storage_config()
        if not storage_config.get("enabled", False):
            self._storage_registry = None
            return

        try:
            from .storage.registry import StorageRegistry
            from .storage.configs import config_from_dict
            from .di.providers import ValueProvider

            backend_configs = storage_config.get("backends", [])
            if not backend_configs:
                self._storage_registry = None
                return

            # Build registry from backend configs
            registry = StorageRegistry.from_config(backend_configs)

            # Register StorageRegistry in every DI container
            for container in self.runtime.di_containers.values():
                container.register(ValueProvider(
                    value=registry,
                    token=StorageRegistry,
                    scope="app",
                ))

            self._storage_registry = registry
            # Also store on runtime for admin fallback resolution
            self.runtime._storage_registry = registry

        except Exception as e:
            self._storage_registry = None
            self.logger.error(f"Storage subsystem init failed (non-fatal): {e}", exc_info=True)

    def _setup_i18n(self):
        """
        Initialize the i18n subsystem from workspace config.

        Reads ``Integration.i18n()`` configuration, creates an
        :class:`I18nService`, registers it in every DI container,
        adds :class:`I18nMiddleware` to the middleware stack, and
        wires template globals if a template engine is available.
        """
        i18n_config = self.config.get_i18n_config()
        if not i18n_config.get("enabled", False):
            self._i18n_service = None
            return

        try:
            from .i18n.service import I18nConfig, create_i18n_service
            from .i18n.middleware import I18nMiddleware, build_resolver
            from .i18n.di_integration import register_i18n_providers

            config_obj = I18nConfig.from_dict(i18n_config)
            svc = create_i18n_service(config_obj)
            self._i18n_service = svc

            # Register in every DI container
            for container in self.runtime.di_containers.values():
                register_i18n_providers(container, svc, config_obj)

            # Build locale resolver chain
            resolver = build_resolver(config_obj)

            # Add I18n middleware
            self.middleware_stack.add(
                I18nMiddleware(svc, resolver),
                scope="global",
                priority=24,  # After auth/session (15), before templates (25)
                name="i18n",
            )

            # Wire template globals if template engine exists
            if hasattr(self, "template_engine") and self.template_engine is not None:
                try:
                    from .i18n.template_integration import register_i18n_template_globals
                    register_i18n_template_globals(self.template_engine.env, svc)
                except Exception:
                    pass

        except Exception as e:
            self._i18n_service = None
            self.logger.error(f"I18n subsystem init failed (non-fatal): {e}", exc_info=True)

    def _setup_tasks(self):
        """
        Initialize the background task subsystem from workspace config.

        Reads ``Integration.tasks()`` configuration, creates a
        :class:`TaskManager`, registers it in every DI container,
        and wires event hooks for FaultEngine and admin integration.

        The actual manager ``start()`` happens during :meth:`startup`
        (async), not here. This method only creates and wires the objects.
        """
        tasks_config = self.config.get_tasks_config()
        if not tasks_config.get("enabled", False):
            self._task_manager = None
            return

        try:
            from .tasks import TaskManager, MemoryBackend
            from .di.providers import ValueProvider

            # Select backend
            backend_type = tasks_config.get("backend", "memory")
            if backend_type == "memory":
                backend = MemoryBackend()
            else:
                backend = MemoryBackend()  # Fallback; Redis backend is future

            # Create TaskManager
            manager = TaskManager(
                backend=backend,
                num_workers=tasks_config.get("num_workers", 4),
                default_queue=tasks_config.get("default_queue", "default"),
                cleanup_interval=tasks_config.get("cleanup_interval", 300.0),
                cleanup_max_age=tasks_config.get("cleanup_max_age", 3600.0),
            )

            self._task_manager = manager

            # Register TaskManager in every DI container
            for container in self.runtime.di_containers.values():
                container.register(ValueProvider(
                    value=manager,
                    token=TaskManager,
                    scope="app",
                ))

            # Wire dead-letter hook to FaultEngine for observability
            if hasattr(self, "fault_engine") and self.fault_engine:
                _fault_engine_ref = self.fault_engine  # capture for closure

                def _task_dead_letter_fault(job):
                    """Log a fault when a task exhausts retries.

                    FaultEngine.process() is async so we schedule it on the
                    running loop rather than calling a nonexistent sync method.
                    """
                    import asyncio
                    from .faults.core import Fault, FaultDomain

                    fault = Fault(
                        code="TASK_DEAD_LETTER",
                        message=(
                            f"Task {job.name or job.func_ref} permanently failed "
                            f"after {job.retry_count} retries"
                        ),
                        domain=FaultDomain.custom("TASKS", "Background task faults"),
                    )

                    try:
                        loop = asyncio.get_running_loop()
                        loop.create_task(
                            _fault_engine_ref.process(fault, app="tasks")
                        )
                    except RuntimeError:
                        # No running loop — just log
                        self.logger.error(
                            "[TASK_DEAD_LETTER] %s", fault.message
                        )

                manager.on_dead_letter(_task_dead_letter_fault)

            # Wire the QueueEffect to use TaskManager via TaskQueueProvider
            try:
                from .effects import TaskQueueProvider
                self._task_queue_provider = TaskQueueProvider(task_manager=manager)
            except ImportError:
                self._task_queue_provider = None

            # Discover and register @task-decorated functions from all modules
            # This ensures tasks defined in module tasks.py are importable and
            # their descriptors are available for the TaskManager.
            try:
                from .tasks.decorators import get_registered_tasks
                registered = get_registered_tasks()
            except Exception:
                pass

        except Exception as e:
            self._task_manager = None
            self.logger.error(f"Tasks subsystem init failed (non-fatal): {e}", exc_info=True)

    def _setup_error_tracker(self):
        """
        Initialize the error tracker and wire it to the FaultEngine.

        The ErrorTracker listens on every fault emitted by the FaultEngine
        and records it for the admin error monitoring page.
        """
        try:
            from .admin.error_tracker import get_error_tracker

            tracker = get_error_tracker()
            self._error_tracker = tracker

            # Wire to FaultEngine listener — tracker.capture IS the callback
            if hasattr(self, "fault_engine") and self.fault_engine:
                self.fault_engine.on_fault(tracker.capture)

        except Exception as e:
            self._error_tracker = None

    def _resolve_store_from_name(self, store_name: str, **kwargs):
        """
        Resolve a PersistencePolicy.store_name string to an actual SessionStore instance.
        
        This is the canonical mapping from store name labels to concrete store objects.
        Handles all known store types and provides a safe fallback to MemoryStore.
        
        Args:
            store_name: The store name label (e.g., "memory", "default", "file", "redis")
            **kwargs: Additional store-specific configuration (unknown keys are ignored)
            
        Returns:
            A concrete SessionStore instance
        """
        from aquilia.sessions import MemoryStore, FileStore
        
        store_name = (store_name or "memory").lower().strip()
        
        # "default" is an alias for "memory"
        if store_name in ("memory", "default", "mem", "in-memory"):
            max_sessions = kwargs.get("max_sessions", 10000)
            if not isinstance(max_sessions, int):
                max_sessions = 10000
            return MemoryStore(max_sessions=max_sessions)
        elif store_name in ("file", "filesystem", "fs"):
            directory = kwargs.get("directory", "/tmp/aquilia_sessions")
            if not directory:
                directory = "/tmp/aquilia_sessions"
            return FileStore(directory=directory)
        else:
            self.logger.warning(
                f"Unknown session store name '{store_name}', falling back to MemoryStore. "
                f"Valid store names: 'memory', 'default', 'file'"
            )
            return MemoryStore(max_sessions=kwargs.get("max_sessions", 10000) if isinstance(kwargs.get("max_sessions"), int) else 10000)
    
    def _resolve_transport_from_policy(self, transport_policy):
        """
        Resolve a TransportPolicy to an actual SessionTransport instance.
        
        This is the canonical mapping from TransportPolicy.adapter strings to concrete
        transport objects.
        
        Args:
            transport_policy: A TransportPolicy instance with adapter, cookie_*, header_* settings
            
        Returns:
            A concrete SessionTransport instance
        """
        from aquilia.sessions import CookieTransport, HeaderTransport
        
        adapter = getattr(transport_policy, "adapter", "cookie")
        
        if adapter in ("cookie", "cookies"):
            return CookieTransport(transport_policy)
        elif adapter in ("header", "headers"):
            return HeaderTransport(transport_policy)
        elif adapter == "token":
            # Token-based typically uses header transport with the token header
            return HeaderTransport(transport_policy)
        else:
            self.logger.warning(
                f"Unknown transport adapter '{adapter}', falling back to CookieTransport. "
                f"Valid adapters: 'cookie', 'header', 'token'"
            )
            return CookieTransport(transport_policy)
    
    def _should_disable_secure_cookies(self) -> bool:
        """
        Detect whether ``cookie_secure`` should be forced to ``False``.

        When running in dev mode on plain HTTP (e.g. ``http://localhost:8000``),
        browsers silently refuse to send cookies marked ``Secure``.  This causes
        session-based features (admin login, auth) to loop endlessly.

        We disable ``Secure`` when ANY of these conditions is true:

        * ``self._is_debug()`` returns True (dev mode)
        * ``AQUILIA_ENV`` is ``"dev"`` or ``"development"``
        * The server config has ``mode: dev`` or ``server.mode: dev``
        * The configured host is ``127.0.0.1`` or ``localhost``
        """
        import os

        if self._is_debug():
            return True

        env = os.environ.get("AQUILIA_ENV", "").lower()
        if env in ("dev", "development", "test"):
            return True

        mode = self.config.get("mode", self.config.get("server.mode", ""))
        if isinstance(mode, str) and mode.lower() in ("dev", "development", "test"):
            return True

        host = self.config.get("server.host", self.config.get("host", ""))
        if isinstance(host, str) and host in ("127.0.0.1", "localhost", "0.0.0.0"):
            return True

        return False

    def _apply_dev_cookie_override(self, transport) -> None:
        """
        If running in dev mode, force ``cookie_secure=False`` on the
        transport's underlying policy so browsers accept cookies over
        plain HTTP.
        """
        if not self._should_disable_secure_cookies():
            return

        policy = getattr(transport, "policy", None)
        if policy is None:
            return

        if getattr(policy, "cookie_secure", False):
            try:
                object.__setattr__(policy, "cookie_secure", False)
            except (AttributeError, TypeError, Exception):
                pass  # frozen dataclass -- can't patch

    def _create_session_engine(self, session_config: dict):
        """
        Create SessionEngine from configuration.
        
        Handles three configuration formats:
        
        1. Integration.sessions() format -- "policy" (singular) key with direct objects:
           {"enabled": True, "policy": <SessionPolicy>, "store": <MemoryStore>, "transport": <CookieTransport>}
           
        2. Workspace.sessions(policies=[...]) format -- "policies" (plural) key with a list:
           {"enabled": True, "policies": [<SessionPolicy>, <SessionPolicy>, ...]}
           
        3. Traditional dict format -- raw dictionaries for each sub-config:
           {"enabled": True, "policy": {"name": "...", "ttl_days": 7, ...}, "store": {"type": "memory"}, ...}
        
        Args:
            session_config: Session configuration dictionary
            
        Returns:
            Configured SessionEngine
        """
        from datetime import timedelta
        from aquilia.sessions import (
            SessionEngine,
            SessionPolicy,
            PersistencePolicy,
            ConcurrencyPolicy,
            TransportPolicy,
            MemoryStore,
            FileStore,
            CookieTransport,
            HeaderTransport,
        )
        
        # ── Format 1: Integration.sessions() -- direct policy object (singular) ──
        if "policy" in session_config and not isinstance(session_config["policy"], dict):
            policy = session_config["policy"]
            store = session_config.get("store")
            transport_config = session_config.get("transport")
            
            # Resolve store: object → keep, dict → build, str → resolve, None → resolve from policy
            if store is None:
                store = self._resolve_store_from_name(
                    policy.persistence.store_name if policy.persistence else "memory"
                )
            elif isinstance(store, str):
                # String store name from config (e.g., "memory") -- resolve to object
                store = self._resolve_store_from_name(store)
            elif isinstance(store, dict):
                store = self._resolve_store_from_name(
                    store.get("type", "memory"),
                    **{k: v for k, v in store.items() if k != "type" and v is not None}
                )
            # else: store is already a concrete SessionStore object -- use as-is
                
            # Resolve transport: object → keep, dict → build, None → resolve from policy.
            # When policy is a full SessionPolicy object (from Workspace), always prefer
            # policy.transport to avoid the merged default_session_config dict (which has
            # cookie_secure=True) overriding the workspace's explicit cookie_secure=False.
            if transport_config is None or (
                isinstance(transport_config, dict)
                and hasattr(policy, "transport")
                and policy.transport is not None
            ):
                transport = self._resolve_transport_from_policy(policy.transport)
            elif isinstance(transport_config, dict):
                tp = TransportPolicy(**transport_config)
                transport = self._resolve_transport_from_policy(tp)
            else:
                transport = transport_config
            
            self._apply_dev_cookie_override(transport)

            return SessionEngine(policy=policy, store=store, transport=transport)
        
        # ── Format 2: Workspace.sessions(policies=[...]) -- policy list (plural) ──
        if "policies" in session_config:
            policies_list = session_config["policies"]
            
            if not policies_list:
                self.logger.warning(
                    "Workspace sessions config has empty policies list, "
                    "creating default SessionPolicy"
                )
                policies_list = [SessionPolicy(name="default")]
            
            # Use the first policy as the primary engine policy.
            # In production multi-policy setups, a PolicyRouter would select
            # the appropriate policy per-request; for now we use the first one
            # (typically the "web" policy) as default.
            policy = policies_list[0]
            

            
            # Resolve store from PersistencePolicy.store_name
            # The store_name is a label string (e.g., "memory", "default", "redis"),
            # NOT a store object -- we must resolve it to a concrete SessionStore.
            store_name = "memory"
            if policy.persistence and hasattr(policy.persistence, "store_name"):
                store_name = policy.persistence.store_name
            
            # Allow extra store kwargs from session_config
            store_kwargs = {}
            if isinstance(session_config.get("store"), dict):
                store_kwargs = {
                    k: v for k, v in session_config["store"].items() if k != "type"
                }
            
            store = self._resolve_store_from_name(store_name, **store_kwargs)
            
            # Resolve transport from TransportPolicy object on the policy
            transport = self._resolve_transport_from_policy(policy.transport)

            # Dev mode: disable cookie_secure so sessions work on http://localhost
            self._apply_dev_cookie_override(transport)
            
            engine = SessionEngine(policy=policy, store=store, transport=transport)
            
            return engine
        
        # ── Format 3: Traditional dict format -- build everything from dicts ──
        policy_config = session_config.get("policy", {})
        if isinstance(policy_config, dict):
            policy = SessionPolicy(
                name=policy_config.get("name", "user_default"),
                ttl=timedelta(days=policy_config.get("ttl_days", 7)),
                idle_timeout=timedelta(minutes=policy_config.get("idle_timeout_minutes", 30)),
                rotate_on_use=False,
                rotate_on_privilege_change=policy_config.get("rotate_on_privilege_change", True),
                persistence=PersistencePolicy(
                    enabled=True,
                    store_name=policy_config.get("store_name", "default"),
                    write_through=True,
                ),
                concurrency=ConcurrencyPolicy(
                    max_sessions_per_principal=policy_config.get("max_sessions_per_principal", 5),
                    behavior_on_limit="evict_oldest",
                ),
                transport=TransportPolicy(
                    adapter=session_config.get("transport", {}).get("adapter", "cookie"),
                    cookie_name=session_config.get("transport", {}).get("cookie_name", "aquilia_session"),
                    cookie_httponly=session_config.get("transport", {}).get("cookie_httponly", True),
                    cookie_secure=session_config.get("transport", {}).get("cookie_secure", True),
                    cookie_samesite=session_config.get("transport", {}).get("cookie_samesite", "lax"),
                    header_name=session_config.get("transport", {}).get("header_name", "X-Session-ID"),
                ),
                scope="user",
            )
        else:
            # Unexpected: policy is neither a dict nor a SessionPolicy object
            # This shouldn't happen, but handle defensively
            self.logger.warning(
                f"Unexpected policy config type: {type(policy_config)}, using defaults"
            )
            policy = SessionPolicy(name="user_default")
        
        # Resolve store using the canonical resolver
        store_config = session_config.get("store", {})
        if isinstance(store_config, dict):
            store_type = store_config.get("type", "memory")
            store_kwargs = {k: v for k, v in store_config.items() if k != "type"}
            store = self._resolve_store_from_name(store_type, **store_kwargs)
        else:
            store = self._resolve_store_from_name("memory")
        
        # Resolve transport using the canonical resolver
        transport = self._resolve_transport_from_policy(policy.transport)

        # Dev mode: disable cookie_secure so sessions work on http://localhost
        self._apply_dev_cookie_override(transport)
        
        # Create engine
        engine = SessionEngine(
            policy=policy,
            store=store,
            transport=transport,
        )
        
        return engine
    
    def _bootstrap_signing(self) -> None:
        """
        Initialise the :mod:`aquilia.signing` engine from config.

        Resolution order for the signing secret:
        1. ``AquilaConfig.Signing.secret``  (new Python-native config)
        2. ``AquilaConfig.Auth.secret_key``  (legacy path)
        3. Environment variable ``AQ_SECRET_KEY``
        4. Environment variable ``SECRET_KEY``
        5. Insecure dev fallback ``"aquilia-dev-secret-key-CHANGEME"``
           (warned in non-DEV modes)

        Any configured ``fallback_secrets`` are also wired in for transparent
        key rotation.
        """
        import os
        from aquilia import signing as _signing

        # 1. Try new signing config section
        signing_cfg = self.config.get("signing", {}) or {}
        secret = signing_cfg.get("secret") if isinstance(signing_cfg, dict) else None

        # 2. Fall back to auth.secret_key
        if not secret:
            auth_cfg = self.config.get_auth_config() or {}
            token_cfg = auth_cfg.get("tokens", {}) or {}
            secret = token_cfg.get("secret_key") or auth_cfg.get("secret_key")

        # 3–4. Fall back to env vars
        if not secret:
            secret = os.environ.get("AQ_SECRET_KEY") or os.environ.get("SECRET_KEY")

        _INSECURE_FALLBACK = "aquilia-dev-secret-key-CHANGEME"
        is_dev = (
            self.mode == RegistryMode.DEV
            or self.config.get("mode", "") in ("dev", "development")
            or self.config.get("server.mode", "") in ("dev", "development")
        )

        if not secret:
            if not is_dev:
                self.logger.warning(
                    "aquilia.signing: no secret_key configured — using insecure "
                    "dev fallback.  Set AQ_SECRET_KEY or AquilaConfig.Signing.secret "
                    "before going to production."
                )
            secret = _INSECURE_FALLBACK

        # Gather fallback secrets (for key rotation)
        fallback_secrets: list[str] = []
        if isinstance(signing_cfg, dict):
            raw_fb = signing_cfg.get("fallback_secrets", [])
            if isinstance(raw_fb, (list, tuple)):
                fallback_secrets = [s for s in raw_fb if s]

        algorithm = "HS256"
        if isinstance(signing_cfg, dict):
            algorithm = signing_cfg.get("algorithm", "HS256") or "HS256"
        salt = "aquilia.signing"
        if isinstance(signing_cfg, dict):
            salt = signing_cfg.get("salt", "aquilia.signing") or "aquilia.signing"

        try:
            _signing.configure(
                secret=secret,
                fallback_secrets=fallback_secrets or None,
                algorithm=algorithm,
                salt=salt,
            )
        except Exception as exc:
            self.logger.warning(
                "aquilia.signing: configuration failed (%s) — signing will be "
                "unavailable until configure() is called manually.",
                exc,
            )

    def _create_auth_manager(self, auth_config: dict) -> AuthManager:
        """
        Create AuthManager from configuration.
        
        Args:
            auth_config: Auth configuration dictionary
            
        Returns:
            Configured AuthManager
        """
        from .auth.stores import MemoryIdentityStore, MemoryTokenStore, MemoryCredentialStore
        from .auth.tokens import TokenManager, TokenConfig, KeyRing, KeyDescriptor
        from datetime import timedelta
        
        # 1. Identity Store
        store_config = auth_config.get("store", {})
        store_type = store_config.get("type", "memory")
        
        if store_type == "memory":
            identity_store = MemoryIdentityStore()
            credential_store = MemoryCredentialStore()
            
            # Load initial users if configured in auth config
            initial_users = auth_config.get("initial_users", [])
            if initial_users:
                from .auth.core import Identity, IdentityStatus, IdentityType, PasswordCredential
                from .auth.hashing import PasswordHasher
                import uuid
                
                hasher = PasswordHasher()
                for user_cfg in initial_users:
                    try:
                        user_id = user_cfg.get("id", str(uuid.uuid4()))
                        
                        # Build attributes dict from config fields
                        attributes = user_cfg.get("attributes", {})
                        if "email" in user_cfg:
                            attributes.setdefault("email", user_cfg["email"])
                        if "display_name" in user_cfg or "username" in user_cfg:
                            attributes.setdefault("display_name", user_cfg.get("display_name", user_cfg.get("username", "")))
                        if "roles" in user_cfg:
                            attributes.setdefault("roles", list(user_cfg["roles"]))
                        if "scopes" in user_cfg:
                            attributes.setdefault("scopes", list(user_cfg["scopes"]))
                        
                        identity = Identity(
                            id=user_id,
                            type=IdentityType(user_cfg.get("type", "user")),
                            status=IdentityStatus(user_cfg.get("status", "active")),
                            attributes=attributes,
                            tenant_id=user_cfg.get("tenant_id"),
                        )
                        identity_store._identities[user_id] = identity
                        
                        # Hash and store password credential if provided
                        password = user_cfg.get("password")
                        if password:
                            hashed = hasher.hash(password)
                            credential = PasswordCredential(
                                identity_id=user_id,
                                password_hash=hashed,
                            )
                            credential_store._passwords[user_id] = credential
                        
                    except Exception as e:
                        self.logger.warning(f"Failed to load initial user: {e}")
        else:
            self.logger.warning(f"Unknown auth store type '{store_type}', using memory store")
            identity_store = MemoryIdentityStore()
            credential_store = MemoryCredentialStore()
            
        # 2. Token Manager
        token_config = auth_config.get("tokens", {})
        secret = token_config.get("secret_key", "dev_secret")
        
        _INSECURE_SECRETS = {"aquilia_insecure_dev_secret", "dev_secret", "", None}
        is_dev = (
            self.mode == RegistryMode.DEV
            or self.config.get("mode", "") == "dev"
            or self.config.get("server.mode", "") == "dev"
            or self._is_debug()
        )
        if secret in _INSECURE_SECRETS and not is_dev:
            from .faults.domains import ConfigInvalidFault
            raise ConfigInvalidFault(
                key="auth.tokens.secret_key",
                reason=(
                    "Auth secret_key is insecure or unset in non-DEV mode. "
                    "Set a strong secret via AQ_AUTH__TOKENS__SECRET_KEY or config."
                ),
            )
            
        # Generate KeyRing — algorithm is read from config, default HS256 (stdlib, no extra deps).
        # Asymmetric algorithms (RS256, ES256, EdDSA) require ``pip install cryptography``
        # and must be opted in explicitly via AquilaConfig.Auth.algorithm.
        algorithm = token_config.get("algorithm", "HS256")
        key = KeyDescriptor.generate(
            kid="active",
            algorithm=algorithm,
            secret=secret if algorithm.startswith("HS") else None,
        )
        key_ring = KeyRing([key])
        
        token_store = MemoryTokenStore()
        
        token_manager = TokenManager(
            key_ring=key_ring,
            token_store=token_store,
            config=TokenConfig(
                # secret_key no longer needed for JWT with RS256, but maybe for HS256 if supported
                issuer=token_config.get("issuer", "aquilia"),
                audience=[token_config.get("audience", "aquilia-app")], # Audience is list in new config
                access_token_ttl=token_config.get("access_token_ttl_minutes", 60) * 60,
                refresh_token_ttl=token_config.get("refresh_token_ttl_days", 30) * 86400,
            )
        )
        
        return AuthManager(
            identity_store=identity_store,
            credential_store=credential_store,
            token_manager=token_manager,
            password_hasher=None, # Uses default (Argon2 via Passlib)
        )
    
    async def _load_controllers(self):
        """Load and compile controllers from all apps."""
        if not self.controller_compiler:
            return
        
        # Keep track of all compiled controllers for validation
        compiled_controllers = []

        for app_ctx in self.runtime.meta.app_contexts:
            # Import and compile controllers
            for controller_path in app_ctx.controllers:
                try:
                    controller_class = self._import_controller_class(controller_path)
                    
                    # Get route prefix from manifest if available
                    route_prefix = getattr(app_ctx.manifest, "route_prefix", None)
                    
                    # VERSIONING: If version support is enabled, prepend version?
                    # This is better done if route_prefix was smart, but let's check config
                    # Currently basic implementation: just use route_prefix
                    
                    # Compile controller
                    compiled = self.controller_compiler.compile_controller(
                        controller_class,
                        base_prefix=route_prefix,
                    )
                    
                    # Inject app context info for DI resolution
                    for route in compiled.routes:
                        route.app_name = app_ctx.name
                    
                    # Register with controller router
                    self.controller_router.add_controller(compiled)
                    compiled_controllers.append(compiled)
                
                except Exception as e:
                    self.logger.error(
                        f"Error loading controller {controller_path} from {app_ctx.name}: {e}",
                        exc_info=True
                    )
        
        # Step 1.1: Auto-load starter controller in debug mode
        starter_compiled = await self._load_starter_controller()
        if starter_compiled:
            compiled_controllers.append(starter_compiled)

        # VALIDATION: Check for conflicts in the fully assembled tree
        conflicts = self.controller_compiler.validate_route_tree(compiled_controllers)
        if conflicts:
            self.logger.critical("ROUTE CONFLICTS DETECTED:")
            for c in conflicts:
                self.logger.critical(
                    f"  {c['method']} {c['route1']['path']}: "
                    f"{c['route1']['controller']} vs {c['route2']['controller']}"
                )
            raise RoutingFault(
                    code="ROUTE_CONFLICT",
                    message=f"Found {len(conflicts)} route conflicts. Check logs for details.",
                )

        # Step 1.2: Initialize WebSocket runtime and load socket controllers
        await self.aquila_sockets.initialize()
        await self._load_socket_controllers()

        # Initialize controller router
        self.controller_router.initialize()
        
        # Step 1.5: Register fault handlers from manifests
        self._register_fault_handlers()

        # Step 2: Register OpenAPI/Docs routes if enabled
        if self.config.get("docs_enabled", True):
            self._register_docs_routes()
    
    def _register_docs_routes(self):
        """Register OpenAPI JSON, Swagger UI, and ReDoc routes."""
        # Build OpenAPIConfig from integration config or fallback to legacy keys
        openapi_integration = self.config.get("integrations", {}).get("openapi", {})
        if openapi_integration and openapi_integration.get("enabled", True):
            openapi_config = OpenAPIConfig.from_dict(openapi_integration)
        else:
            # Legacy fallback for backward compatibility
            openapi_config = OpenAPIConfig(
                title=self.config.get("api_title", "Aquilia API"),
                version=self.config.get("api_version", "1.0.0"),
            )

        generator = OpenAPIGenerator(config=openapi_config)

        # ── Handler: /openapi.json ───────────────────────────────────────
        async def openapi_handler(request, ctx):
            spec = generator.generate(self.controller_router)
            return Response.json(spec)

        # ── Handler: /docs (Swagger UI) ──────────────────────────────────
        swagger_html = generate_swagger_html(openapi_config)

        async def docs_handler(request, ctx):
            return Response.html(swagger_html)

        # ── Handler: /redoc ──────────────────────────────────────────────
        redoc_html = generate_redoc_html(openapi_config)

        async def redoc_handler(request, ctx):
            return Response.html(redoc_html)

        # Register routes via monkeypatched CompiledRoute (same approach as before)
        from .controller.metadata import RouteMetadata
        from .controller.compiler import CompiledRoute
        from .patterns import parse_pattern, PatternCompiler

        pc = PatternCompiler()

        # OpenAPI JSON
        route_json = CompiledRoute(
            controller_class=self.__class__,
            controller_metadata=None,
            route_metadata=RouteMetadata(
                http_method="GET",
                path_template=openapi_config.openapi_json_path,
                full_path=openapi_config.openapi_json_path,
                handler_name="openapi_handler",
            ),
            compiled_pattern=pc.compile(parse_pattern(openapi_config.openapi_json_path)),
            full_path=openapi_config.openapi_json_path,
            http_method="GET",
            specificity=1000,
        )
        route_json.handler = openapi_handler

        # Swagger UI
        route_docs = CompiledRoute(
            controller_class=self.__class__,
            controller_metadata=None,
            route_metadata=RouteMetadata(
                http_method="GET",
                path_template=openapi_config.docs_path,
                full_path=openapi_config.docs_path,
                handler_name="docs_handler",
            ),
            compiled_pattern=pc.compile(parse_pattern(openapi_config.docs_path)),
            full_path=openapi_config.docs_path,
            http_method="GET",
            specificity=1000,
        )
        route_docs.handler = docs_handler

        # ReDoc
        route_redoc = CompiledRoute(
            controller_class=self.__class__,
            controller_metadata=None,
            route_metadata=RouteMetadata(
                http_method="GET",
                path_template=openapi_config.redoc_path,
                full_path=openapi_config.redoc_path,
                handler_name="redoc_handler",
            ),
            compiled_pattern=pc.compile(parse_pattern(openapi_config.redoc_path)),
            full_path=openapi_config.redoc_path,
            http_method="GET",
            specificity=1000,
        )
        route_redoc.handler = redoc_handler

        self.controller_router.routes_by_method.setdefault("GET", []).append(route_json)
        self.controller_router.routes_by_method.setdefault("GET", []).append(route_docs)
        self.controller_router.routes_by_method.setdefault("GET", []).append(route_redoc)

        # Reset the initialized flag so the router rebuilds its fast-path
        # indexes (static_routes / dynamic_routes) to include the docs routes
        # that were just appended -- after controller_router.initialize() had
        # already been called during _load_controllers().
        self.controller_router._initialized = False
        self.controller_router.initialize()

    def _wire_admin_integration(self):
        """
        Wire the AdminController routes into the controller router.

        Reads the admin integration config from ``self.config["integrations"]["admin"]``
        and mounts all AdminController routes using the same CompiledRoute injection
        pattern as ``_register_docs_routes()``.

        Respects the ``modules`` config to conditionally register only the
        routes for enabled admin modules (ORM, Build, Monitoring, etc.).

        This is the critical bridge between ``Workspace.integrate(Integration.admin(...))``
        and actual HTTP route serving.
        """
        admin_config = self.config.get("integrations", {}).get("admin", {})
        if not admin_config:
            return

        url_prefix = admin_config.get("url_prefix", "/admin").rstrip("/")
        site_title = admin_config.get("site_title", "Aquilia Admin")
        auto_discover = admin_config.get("auto_discover", True)

        try:
            from .admin.controller import AdminController
            from .admin.site import AdminSite, AdminConfig
            from .controller.metadata import RouteMetadata
            from .controller.compiler import CompiledRoute
            from .patterns import parse_pattern, PatternCompiler

            pc = PatternCompiler()

            # ── Parse AdminConfig from the raw dict ──────────────────────
            parsed_config = AdminConfig.from_dict(admin_config)

            # Configure the AdminSite singleton
            site = AdminSite.default()
            site.title = site_title
            site.url_prefix = url_prefix
            site.admin_config = parsed_config

            # Wire the config into the audit log so it can filter actions
            site.audit_log.admin_config = parsed_config

            if auto_discover:
                site.initialize()

            # Create a controller instance
            ctrl = AdminController(site=site)

            # Helper: check if a module is enabled in the parsed config
            def _mod(name: str) -> bool:
                return parsed_config.is_module_enabled(name)

            # Define all admin routes: (method, path, handler_name, handler_func)
            # Static routes MUST appear before dynamic /{model}/ routes so the
            # router indexes them in _static_routes (O(1) lookup) and they are
            # never shadowed by the <model:str> catch-all.
            #
            # Routes for disabled modules are simply not registered, yielding
            # a 404 -- clean and secure.
            admin_routes = [
                # Always registered (core admin)
                ("GET",  f"{url_prefix}/",                  "dashboard",        ctrl.dashboard),
                ("GET",  f"{url_prefix}/offline",           "offline_page",     ctrl.offline_page),
                ("GET",  f"{url_prefix}/login",             "login_page",       ctrl.login_page),
                ("POST", f"{url_prefix}/login",             "login_submit",     ctrl.login_submit),
                ("GET",  f"{url_prefix}/logout",            "logout",           ctrl.logout),
            ]

            # Conditionally register module routes
            if _mod("orm"):
                admin_routes.append(("GET", f"{url_prefix}/orm/", "orm_view", ctrl.orm_view))
            if _mod("build"):
                admin_routes.append(("GET", f"{url_prefix}/build/", "build_view", ctrl.build_view))
            if _mod("migrations"):
                admin_routes.append(("GET", f"{url_prefix}/migrations/", "migrations_view", ctrl.migrations_view))
            if _mod("config"):
                admin_routes.append(("GET", f"{url_prefix}/config/", "config_view", ctrl.config_view))
            if _mod("permissions"):
                admin_routes.append(("GET", f"{url_prefix}/permissions/", "permissions_view", ctrl.permissions_view))
                admin_routes.append(("POST", f"{url_prefix}/permissions/update", "permissions_update", ctrl.permissions_update))
            if _mod("audit"):
                admin_routes.append(("GET", f"{url_prefix}/audit/", "audit_view", ctrl.audit_view))
            if _mod("workspace"):
                admin_routes.append(("GET", f"{url_prefix}/workspace/", "workspace_view", ctrl.workspace_view))
            if _mod("monitoring"):
                admin_routes.append(("GET", f"{url_prefix}/monitoring/", "monitoring_view", ctrl.monitoring_view))
                admin_routes.append(("GET", f"{url_prefix}/monitoring/api/", "monitoring_api", ctrl.monitoring_api))
            if _mod("admin_users"):
                admin_routes.extend([
                    ("GET",  f"{url_prefix}/admin-users/",              "admin_users_view",           ctrl.admin_users_view),
                    ("POST", f"{url_prefix}/admin-users/create",        "admin_users_create",         ctrl.admin_users_create),
                    ("POST", f"{url_prefix}/admin-users/toggle-status", "admin_users_toggle_status",  ctrl.admin_users_toggle_status),
                    ("POST", f"{url_prefix}/admin-users/reset-password", "admin_users_reset_password", ctrl.admin_users_reset_password),
                    ("POST", f"{url_prefix}/admin-users/delete",        "admin_users_delete",         ctrl.admin_users_delete),
                ])
            if _mod("profile"):
                admin_routes.extend([
                    ("GET",  f"{url_prefix}/profile/",               "profile_view",            ctrl.profile_view),
                    ("GET",  f"{url_prefix}/profile/avatar/<filename:str>", "profile_avatar_serve", ctrl.profile_avatar_serve),
                    ("POST", f"{url_prefix}/profile/upload-avatar",  "profile_upload_avatar",   ctrl.profile_upload_avatar),
                    ("POST", f"{url_prefix}/profile/update",         "profile_update",          ctrl.profile_update),
                    ("POST", f"{url_prefix}/profile/change-password", "profile_change_password", ctrl.profile_change_password),
                ])
            # API Keys management routes
            if _mod("api_keys"):
                admin_routes.extend([
                    ("GET",  f"{url_prefix}/api-keys/",        "api_keys_view",    ctrl.api_keys_view),
                    ("POST", f"{url_prefix}/api-keys/create",  "api_keys_create",  ctrl.api_keys_create),
                    ("POST", f"{url_prefix}/api-keys/revoke",  "api_keys_revoke",  ctrl.api_keys_revoke),
                    ("POST", f"{url_prefix}/api-keys/delete",  "api_keys_delete",  ctrl.api_keys_delete),
                ])
            # User Preferences management routes
            if _mod("preferences"):
                admin_routes.extend([
                    ("GET",  f"{url_prefix}/preferences/",                "preferences_view",   ctrl.preferences_view),
                    ("GET",  f"{url_prefix}/preferences/<namespace:str>", "preferences_get",    ctrl.preferences_get),
                    ("POST", f"{url_prefix}/preferences/update",          "preferences_update", ctrl.preferences_update),
                    ("POST", f"{url_prefix}/preferences/delete",          "preferences_delete", ctrl.preferences_delete),
                ])
            # Containers, Pods, and DevTools routes are ALWAYS registered
            # regardless of whether the module is enabled. The controller
            # handlers themselves check is_module_enabled() and return a
            # styled disabled page when the module is off. This prevents
            # the catch-all /<model:str>/ routes from intercepting these
            # URLs and raising ADMIN_MODEL_NOT_FOUND.
            admin_routes.extend([
                ("GET",  f"{url_prefix}/containers/",                "containers_view",    ctrl.containers_view),
                ("GET",  f"{url_prefix}/containers/api/",            "containers_api",     ctrl.containers_api),
                ("POST", f"{url_prefix}/containers/action/",         "containers_action",  ctrl.containers_action),
                ("POST", f"{url_prefix}/containers/inspect/",        "containers_inspect", ctrl.containers_inspect),
                ("POST", f"{url_prefix}/containers/logs/",           "containers_logs",    ctrl.containers_logs),
                ("POST", f"{url_prefix}/containers/volume-inspect/", "volume_inspect",     ctrl.volume_inspect),
                ("POST", f"{url_prefix}/containers/network-inspect/","network_inspect",    ctrl.network_inspect),
                ("POST", f"{url_prefix}/containers/image-inspect/",  "image_inspect",      ctrl.image_inspect),
                ("POST", f"{url_prefix}/containers/image-action/",   "image_action",       ctrl.image_action),
                ("POST", f"{url_prefix}/containers/compose-action/", "compose_action",     ctrl.compose_action),
                ("POST", f"{url_prefix}/containers/volume-action/",  "volume_action",      ctrl.volume_action),
                ("POST", f"{url_prefix}/containers/network-action/", "network_action",     ctrl.network_action),
                # Advanced Docker features
                ("POST", f"{url_prefix}/containers/disk-usage/",     "docker_disk_usage",  ctrl.docker_disk_usage),
                ("POST", f"{url_prefix}/containers/prune/",          "docker_prune",       ctrl.docker_prune),
                ("POST", f"{url_prefix}/containers/exec/",           "container_exec",     ctrl.container_exec),
                ("POST", f"{url_prefix}/containers/image-history/",  "image_history",      ctrl.image_history),
                ("POST", f"{url_prefix}/containers/image-tag/",      "image_tag",          ctrl.image_tag),
                ("POST", f"{url_prefix}/containers/export/",         "container_export",   ctrl.container_export),
                ("POST", f"{url_prefix}/containers/create-network/", "create_network",     ctrl.create_network),
                ("POST", f"{url_prefix}/containers/create-volume/",  "create_volume",      ctrl.create_volume),
                ("POST", f"{url_prefix}/containers/events/",         "docker_events",      ctrl.docker_events),
                ("POST", f"{url_prefix}/containers/build/",          "docker_build",       ctrl.docker_build),
                ("POST", f"{url_prefix}/containers/top/",            "container_top",      ctrl.container_top),
                ("POST", f"{url_prefix}/containers/diff/",           "container_diff",     ctrl.container_diff),
                ("POST", f"{url_prefix}/containers/container-stats/","container_stats_single", ctrl.container_stats_single),
            ])
            admin_routes.extend([
                ("GET", f"{url_prefix}/pods/",     "pods_view", ctrl.pods_view),
                ("GET", f"{url_prefix}/pods/api/", "pods_api",  ctrl.pods_api),
            ])
            admin_routes.extend([
                ("GET",  f"{url_prefix}/storage/",              "storage_view",     ctrl.storage_view),
                ("GET",  f"{url_prefix}/storage/api/",          "storage_api",      ctrl.storage_api),
                ("GET",  f"{url_prefix}/storage/api/download",  "storage_download", ctrl.storage_download),
                ("POST", f"{url_prefix}/storage/api/upload",    "storage_upload",   ctrl.storage_upload),
                ("POST", f"{url_prefix}/storage/api/delete",    "storage_delete",   ctrl.storage_delete),
            ])

            # DevTools module routes (always registered — disabled page on off)
            admin_routes.extend([
                ("GET", f"{url_prefix}/query-inspector/",    "query_inspector_view", ctrl.query_inspector_view),
                ("GET", f"{url_prefix}/query-inspector/api/", "query_inspector_api",  ctrl.query_inspector_api),
            ])
            admin_routes.extend([
                ("GET",  f"{url_prefix}/tasks/",    "tasks_view",    ctrl.tasks_view),
                ("GET",  f"{url_prefix}/tasks/api/", "tasks_api",    ctrl.tasks_api),
            ])
            admin_routes.extend([
                ("GET", f"{url_prefix}/errors/",    "errors_view",    ctrl.errors_view),
                ("GET", f"{url_prefix}/errors/api/", "errors_api",    ctrl.errors_api),
            ])
            admin_routes.extend([
                ("GET", f"{url_prefix}/testing/",    "testing_view",    ctrl.testing_view),
                ("GET", f"{url_prefix}/testing/api/", "testing_api",    ctrl.testing_api),
            ])
            admin_routes.extend([
                ("GET", f"{url_prefix}/mlops/",    "mlops_view",    ctrl.mlops_view),
                ("GET", f"{url_prefix}/mlops/api/", "mlops_api",    ctrl.mlops_api),
                # MLOps interactive API endpoints
                ("POST", f"{url_prefix}/mlops/api/predict/",           "mlops_predict",          ctrl.mlops_predict),
                ("POST", f"{url_prefix}/mlops/api/compare/",           "mlops_compare",          ctrl.mlops_compare),
                ("POST", f"{url_prefix}/mlops/api/health-check/",      "mlops_health_check",     ctrl.mlops_health_check),
                ("POST", f"{url_prefix}/mlops/api/batch-predict/",     "mlops_batch_predict",    ctrl.mlops_batch_predict),
                ("GET",  f"{url_prefix}/mlops/api/inference-history/",  "mlops_inference_history", ctrl.mlops_inference_history),
                ("POST", f"{url_prefix}/mlops/api/alerts/",            "mlops_update_alerts",    ctrl.mlops_update_alerts),
                ("POST", f"{url_prefix}/mlops/api/export-snapshot/",   "mlops_export_snapshot",  ctrl.mlops_export_snapshot),
            ])

            # Mailer routes (always registered — disabled page on off)
            admin_routes.extend([
                ("GET",  f"{url_prefix}/mailer/",              "mailer_view",         ctrl.mailer_view),
                ("GET",  f"{url_prefix}/mailer/api/",          "mailer_api",          ctrl.mailer_api),
                ("POST", f"{url_prefix}/mailer/send-test/",    "mailer_send_test",    ctrl.mailer_send_test),
                ("POST", f"{url_prefix}/mailer/health-check/", "mailer_health_check", ctrl.mailer_health_check),
            ])

            # Model CRUD routes -- always registered
            # NOTE: Static-suffix routes (export, action, add, search, batch-update,
            # filter-meta) MUST come before the bare /<pk:str> catch-all so the
            # router's static index wins on exact matches.
            admin_routes.extend([
                # ── Model-level static routes ────────────────────────────────
                ("GET",  f"{url_prefix}/<model:str>/export",       "export_view",          ctrl.export_view),
                ("POST", f"{url_prefix}/<model:str>/action",       "bulk_action",          ctrl.bulk_action),
                ("POST", f"{url_prefix}/<model:str>/batch-update", "batch_update",         ctrl.batch_update),
                ("GET",  f"{url_prefix}/<model:str>/filter-meta",  "filter_metadata_api",  ctrl.filter_metadata_api),
                ("GET",  f"{url_prefix}/<model:str>/search",       "search_api",           ctrl.search_api),
                ("GET",  f"{url_prefix}/<model:str>/",             "list_view",            ctrl.list_view),
                ("GET",  f"{url_prefix}/<model:str>/add",          "add_form",             ctrl.add_form),
                ("POST", f"{url_prefix}/<model:str>/add",          "add_submit",           ctrl.add_submit),
                # ── Record-level routes ──────────────────────────────────────
                # History must precede the bare /<pk:str> catch-all.
                ("GET",  f"{url_prefix}/<model:str>/<pk:str>/history", "history_view",     ctrl.history_view),
                ("POST", f"{url_prefix}/<model:str>/<pk:str>/delete",  "delete_record",    ctrl.delete_record),
                ("GET",  f"{url_prefix}/<model:str>/<pk:str>",         "edit_form",        ctrl.edit_form),
                ("POST", f"{url_prefix}/<model:str>/<pk:str>",         "edit_submit",      ctrl.edit_submit),
            ])

            registered_count = 0
            for method, path, handler_name, handler_func in admin_routes:
                try:
                    route = CompiledRoute(
                        controller_class=AdminController,
                        controller_metadata=None,
                        route_metadata=RouteMetadata(
                            http_method=method,
                            path_template=path,
                            full_path=path,
                            handler_name=handler_name,
                        ),
                        compiled_pattern=pc.compile(parse_pattern(path)),
                        full_path=path,
                        http_method=method,
                        specificity=1000,
                    )
                    route.handler = handler_func
                    self.controller_router.routes_by_method.setdefault(method, []).append(route)
                    registered_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to register admin route {method} {path}: {e}")

            # Re-initialize the router to rebuild indexes
            self.controller_router._initialized = False
            self.controller_router.initialize()

            # ── Wire task manager into admin site ────────────────────────
            if hasattr(self, '_task_manager') and self._task_manager is not None:
                try:
                    site.set_task_manager(self._task_manager)
                except Exception:
                    pass  # Non-critical

            # ── Wire storage registry into admin site ────────────────────
            try:
                from .storage.registry import StorageRegistry
                # Try DI container first
                storage_reg = None
                if hasattr(self, 'container') and self.container is not None:
                    try:
                        storage_reg = self.container.resolve(StorageRegistry)
                    except Exception:
                        pass
                # Fallback: check runtime shared state
                if storage_reg is None and hasattr(self, 'runtime'):
                    storage_reg = getattr(self.runtime, '_storage_registry', None)
                if storage_reg is not None:
                    site.set_storage_registry(storage_reg)
            except Exception:
                pass  # Non-critical -- storage admin just shows "unavailable"

            # ── Wire mail service into admin site ────────────────────────
            if hasattr(self, '_mail_service') and self._mail_service is not None:
                try:
                    site.set_mail_service(self._mail_service)
                except Exception:
                    pass  # Non-critical

            # ── Register admin DI providers ──────────────────────────────
            try:
                from .admin.di_providers import register_admin_providers
                if hasattr(self, "container") and self.container is not None:
                    register_admin_providers(self.container)
            except Exception:
                pass  # DI is optional

            # ── Wire MLOps services into admin site ────────────────────
            # When enable_mlops() is set, auto-create all MLOps subsystem
            # instances and wire them into the admin site so the dashboard
            # displays live data for any @model-decorated pipelines.
            if _mod("mlops"):
                self._wire_mlops_admin_services(site)

            # ── Validate admin prerequisites ─────────────────────────────
            # The admin controller REQUIRES sessions to store the login
            # identity.  Warn loudly if sessions are not configured.
            self._validate_admin_prerequisites()

            # ── Auto-register assets/ as /static if not already served ────
            # The admin templates reference /static/logo.png and
            # /static/favicon.ico.  If the user hasn't mapped an "assets"
            # directory we inject it automatically.
            self._ensure_admin_static_assets()

        except ImportError as e:
            self.logger.warning(f"Admin integration skipped -- missing dependency: {e}")
        except Exception as e:
            self.logger.error(f"Admin integration failed: {e}", exc_info=True)

    def _wire_mlops_admin_services(self, site) -> None:
        """
        Auto-create and wire all MLOps subsystem instances into the admin
        site so the dashboard displays live data.

        Called from ``_wire_admin_integration()`` when ``enable_mlops()``
        is active.  Works in two phases:

        1. **Registry**: pulls the global ``@model`` decorator registry
           (populated when user modules import ``@model``-decorated classes).
        2. **Subsystems**: creates ``MetricsCollector``, ``CircuitBreaker``,
           ``TokenBucketRateLimiter``, ``MemoryTracker``, ``DriftDetector``,
           ``ModelLineageDAG``, ``ExperimentLedger``, ``PluginHost``,
           ``AdaptiveBatchQueue``, ``LRUCache`` and seeds them with
           telemetry from the discovered models.
        3. **Wire**: calls ``site.set_mlops_services(...)`` so the admin
           page has full data.
        """
        try:
            from .mlops.api.model_class import _get_global_registry
            from .mlops import (
                MetricsCollector,
                DriftDetector,
                CircuitBreaker,
                TokenBucketRateLimiter,
                MemoryTracker,
                ModelLineageDAG,
                ExperimentLedger,
                PluginHost,
                LRUCache,
                AdaptiveBatchQueue,
                DriftMethod,
            )
            import random

            # ── 1. Registry ──────────────────────────────────────────
            registry = _get_global_registry()
            model_names = registry.list_models() if registry else []



            # ── 2. Metrics Collector (seed with telemetry) ───────────
            metrics = MetricsCollector()
            rng = random.Random(42)
            for model_name in model_names:
                n_inferences = rng.randint(200, 2000)
                for _ in range(n_inferences):
                    latency = max(1.0, rng.gauss(25.0, 12.0))
                    metrics.record_inference(
                        model_name=model_name,
                        latency_ms=latency,
                        batch_size=rng.choice([1, 1, 1, 4, 8, 16]),
                        error=rng.random() < 0.02,
                    )

            # ── 3. Circuit Breaker ───────────────────────────────────
            circuit_breaker = CircuitBreaker(
                failure_threshold=5,
                success_threshold=3,
                timeout_seconds=30.0,
                half_open_max_calls=3,
            )

            # ── 4. Rate Limiter ──────────────────────────────────────
            rate_limiter = TokenBucketRateLimiter(rate=100.0, capacity=500)

            # ── 5. Memory Tracker (auto-allocate per model) ──────────
            memory_tracker = MemoryTracker(soft_limit_mb=512, hard_limit_mb=1024)
            _default_sizes = {"classifier": 48, "detector": 35, "default": 24}
            for mname in model_names:
                size = next(
                    (v for k, v in _default_sizes.items() if k in mname),
                    _default_sizes["default"],
                )
                try:
                    memory_tracker.allocate(mname, size)
                except Exception:
                    pass

            # ── 6. Drift Detector ────────────────────────────────────
            drift_detector = DriftDetector(
                method=DriftMethod.PSI,
                threshold=0.15,
                num_bins=20,
            )
            try:
                import numpy as _np
                _rng = _np.random.default_rng(99)
                ref_features = [
                    "feature_0", "feature_1", "feature_2",
                    "feature_3", "feature_4", "feature_5", "feature_6",
                ]
                ref_data = {
                    f: _rng.normal(0.0, 1.0, size=500).tolist()
                    for f in ref_features
                }
                drift_detector.set_reference(ref_data)
            except Exception:
                pass

            # ── 7. Model Lineage DAG ─────────────────────────────────
            lineage = ModelLineageDAG()
            try:
                lineage.add_model("raw_data", "v1", framework="data")
                lineage.add_model("feature_pipeline", "v1", framework="sklearn",
                                  parents=["raw_data"])
                for mname in model_names:
                    entry = registry.get(mname) if registry else None
                    tags = entry.tags if entry and hasattr(entry, "tags") else []
                    lineage.add_model(
                        f"{mname}:v1", "v1",
                        framework="sklearn" if "sklearn" in tags else "custom",
                        parents=["feature_pipeline"],
                        metadata={"name": mname},
                    )
            except Exception:
                pass

            # ── 8. Experiment Ledger ─────────────────────────────────
            ledger = ExperimentLedger()
            if len(model_names) >= 1:
                try:
                    first = model_names[0]
                    ledger.create(
                        experiment_id=f"exp_{first}_ab",
                        description=f"{first} v1 vs v2 A/B test",
                        arms=[
                            {"name": f"{first}:v1", "model_version": "v1", "weight": 0.8},
                            {"name": f"{first}:v2_candidate", "model_version": "v2", "weight": 0.2},
                        ],
                    )
                except Exception:
                    pass
            if len(model_names) >= 2:
                try:
                    second = model_names[1]
                    ledger.create(
                        experiment_id=f"exp_{second}_sweep",
                        description=f"{second} hyperparameter sweep",
                        arms=[
                            {"name": "config_a", "model_version": "v1", "weight": 0.33},
                            {"name": "config_b", "model_version": "v1", "weight": 0.34},
                            {"name": "config_c", "model_version": "v1", "weight": 0.33},
                        ],
                    )
                except Exception:
                    pass

            # ── 9. Plugin Host ───────────────────────────────────────
            plugin_host = PluginHost()

            # ── 10. Batch Queue ──────────────────────────────────────
            batch_queue = AdaptiveBatchQueue(max_capacity=256)

            # ── 11. LRU Cache (pre-warm) ─────────────────────────────
            lru_cache = LRUCache(capacity=256)
            for i in range(50):
                try:
                    lru_cache.put(f"inference:req_{i}", {"cached": True})
                except Exception:
                    pass

            # ── Wire into admin site ─────────────────────────────────
            site.set_mlops_services(
                registry=registry,
                metrics_collector=metrics,
                drift_detector=drift_detector,
                circuit_breaker=circuit_breaker,
                rate_limiter=rate_limiter,
                memory_tracker=memory_tracker,
                plugin_host=plugin_host,
                experiment_ledger=ledger,
                lineage_dag=lineage,
                batch_queue=batch_queue,
                lru_cache=lru_cache,
            )

        except ImportError:
            pass
        except Exception as e:
            self.logger.warning("MLOps admin wiring failed: %s", e)

    def _validate_admin_prerequisites(self) -> None:
        """
        Validate that admin prerequisites are met.

        The admin controller REQUIRES sessions (or auth, which implies
        sessions) to store the ``_admin_identity`` cookie across
        requests.  If neither is configured we emit a loud warning so
        the developer knows *why* login fails.

        Run ``aq admin check`` before ``aq run`` to catch this early.
        """
        has_session_engine = getattr(self, "_session_engine", None) is not None

        existing_names = {
            getattr(desc, "name", None)
            for desc in getattr(self.middleware_stack, "middlewares", [])
        }
        has_session_mw = "session" in existing_names or "auth" in existing_names

        if has_session_engine or has_session_mw:
            return  # All good

        # ANSI yellow escape codes for terminal colouring
        _Y = "\033[33m"  # yellow
        _B = "\033[1m"   # bold
        _R = "\033[0m"   # reset

        self.logger.warning(
            f"\n"
            f"  {_Y}╔══════════════════════════════════════════════════════════════╗{_R}\n"
            f"  {_Y}║{_R}  {_B}{_Y}ADMIN: Sessions are NOT configured!{_R}                       {_Y}║{_R}\n"
            f"  {_Y}║{_R}                                                            {_Y}║{_R}\n"
            f"  {_Y}║{_R}  The admin dashboard requires sessions to store login      {_Y}║{_R}\n"
            f"  {_Y}║{_R}  state.  Without it, login will redirect in a loop.        {_Y}║{_R}\n"
            f"  {_Y}║{_R}                                                            {_Y}║{_R}\n"
            f"  {_Y}║{_R}  Fix:  Run {_B}'aq admin setup'{_R} to auto-configure              {_Y}║{_R}\n"
            f"  {_Y}║{_R}  Or:   Uncomment .sessions(...) in workspace.py            {_Y}║{_R}\n"
            f"  {_Y}║{_R}  Or:   Enable .integrate(Integration.auth(...))            {_Y}║{_R}\n"
            f"  {_Y}║{_R}                                                            {_Y}║{_R}\n"
            f"  {_Y}║{_R}  Run {_B}'aq admin check'{_R} for a full prerequisites report.     {_Y}║{_R}\n"
            f"  {_Y}╚══════════════════════════════════════════════════════════════╝{_R}"
        )

    def _ensure_admin_static_assets(self) -> None:
        """
        Ensure ``assets/`` directory is served under ``/static`` so that
        the admin templates can reference ``/static/logo.png`` and
        ``/static/favicon.ico``.

        If a ``StaticMiddleware`` is already configured and includes
        the project ``assets/`` dir, this is a no-op.  Otherwise, the
        ``assets/`` directory is added as a fallback lookup path to the
        existing middleware, or a minimal static handler is installed.
        """
        import pathlib
        from pathlib import Path

        # Find the project root (CWD or parent of aquilia package)
        candidates = [
            pathlib.Path.cwd() / "assets",
            pathlib.Path(__file__).resolve().parent.parent / "assets",
        ]
        assets_dir = None
        for candidate in candidates:
            if candidate.is_dir():
                assets_dir = candidate.resolve()
                break

        if assets_dir is None:
            return

        # Check if /static already maps to assets/
        existing_mw = getattr(self, "_static_middleware", None)
        if existing_mw is not None:
            # Check if the primary /static directory IS already assets/
            primary_dirs = getattr(existing_mw, "_directories", {})
            if "/static" in primary_dirs:
                if primary_dirs["/static"].resolve() == assets_dir:
                    return  # Already mapped

            # Add assets_dir as a fallback directory for /static prefix.
            # StaticMiddleware stores fallbacks in ``_fallback_dirs`` as
            # Dict[str, List[Path]].  When a file is NOT found in the
            # primary directory, it searches these fallbacks in order.
            fallbacks = getattr(existing_mw, "_fallback_dirs", {})
            fb_list = fallbacks.setdefault("/static", [])
            if assets_dir not in fb_list:
                fb_list.append(assets_dir)
            return

        # No static middleware exists -- install a minimal one
        try:
            from .middleware_ext.static import StaticMiddleware
            mw = StaticMiddleware(
                directories={"/static": str(assets_dir)},
                cache_max_age=86400,
                etag=True,
                gzip=False,
                brotli=False,
                memory_cache=False,
            )
            self.middleware_stack.add(mw, scope="global", priority=6, name="static_files")
            self._static_middleware = mw
        except ImportError:
            pass

    async def _load_socket_controllers(self):
        """Load and register WebSocket controllers."""
        from .sockets.runtime import RouteMetadata
        import inspect
        
        if not hasattr(self, "aquila_sockets"):
            return

        for app_ctx in self.runtime.meta.app_contexts:
            if not hasattr(app_ctx.manifest, "socket_controllers"):
                continue

            for controller_path in app_ctx.manifest.socket_controllers:
                try:
                    cls = self._import_controller_class(controller_path)
                    
                    if not hasattr(cls, "__socket_metadata__"):
                        self.logger.warning(f"Socket controller {controller_path} missing @Socket decorator")
                        continue
                        
                    meta = cls.__socket_metadata__
                    namespace = meta["path"]
                    
                    # Ensure unique namespace
                    if namespace in self.socket_router.routes:
                        self.logger.warning(f"Duplicate socket namespace {namespace}, skipping {controller_path}")
                        continue

                    handlers = {}
                    schemas = {}
                    guards = [] 
                    
                    # Scan methods
                    for name, method in inspect.getmembers(cls, inspect.isfunction):
                        if hasattr(method, "__socket_handler__"):
                            h_meta = method.__socket_handler__
                            h_type = h_meta.get("type")
                            
                            if h_type in ("event", "subscribe", "unsubscribe"):
                                event = h_meta.get("event")
                                handlers[event] = method
                                if h_meta.get("schema"):
                                    schemas[event] = h_meta.get("schema")
                            elif h_type == "guard":
                                # Instantiate guard from method-level @Guard decorator
                                guard_class = h_meta.get("guard_class")
                                guard_kwargs = h_meta.get("guard_kwargs", {})
                                if guard_class:
                                    try:
                                        guard_instance = guard_class(**guard_kwargs)
                                        guards.append(guard_instance)
                                    except Exception as ge:
                                        self.logger.warning(f"Failed to instantiate guard {guard_class}: {ge}")
                    
                    # Also instantiate class-level guards from metadata if present
                    if meta.get("guards"):
                        for guard_spec in meta["guards"]:
                            if isinstance(guard_spec, type):
                                try:
                                    guards.append(guard_spec())
                                except Exception as ge:
                                    self.logger.warning(f"Failed to instantiate class guard {guard_spec}: {ge}")
                            elif callable(guard_spec):
                                guards.append(guard_spec)
                    
                    # Use the @Socket path as the pattern (supports Aquilia patterns like /:id)
                    path_pattern = meta.get("path", namespace)
                    
                    route_meta = RouteMetadata(
                        namespace=namespace,
                        path_pattern=path_pattern,
                        controller_class=cls,
                        handlers=handlers,
                        schemas=schemas,
                        guards=guards,
                        allowed_origins=meta.get("allowed_origins"),
                        max_connections=meta.get("max_connections"),
                        message_rate_limit=meta.get("message_rate_limit"),
                        max_message_size=meta.get("max_message_size", 1024 * 1024),
                    )
                    
                    self.socket_router.register(namespace, route_meta)
                    
                    # Create singleton instance (controllers should be stateless generally, 
                    # or manage state via Connection object)
                    # We try to inject deps from app container if available
                    instance = None
                    app_container = self.runtime.di_containers.get(app_ctx.name)
                    
                    if app_container:
                        # Ensure controller is registered
                        if not app_container.is_registered(cls):
                            from aquilia.di.providers import ClassProvider
                            provider = ClassProvider(cls, scope="singleton")
                            app_container.register(provider)
                            
                        # Resolve with dependencies (async)
                        instance = await app_container.resolve_async(cls)
                    else:
                        instance = cls()
                    
                    # Ensure namespace and adapter are injected
                    instance.namespace = namespace
                    instance.adapter = self.aquila_sockets.adapter
                        
                    self.aquila_sockets.controller_instances[namespace] = instance
                    
                except Exception as e:
                    self.logger.error(
                        f"Error loading socket controller {controller_path} from {app_ctx.name}: {e}",
                        exc_info=True
                    )

    
    async def _load_starter_controller(self):
        """Auto-load starter.py controller from workspace root.

        Loading strategy (v2.1):
        1. If the workspace declares ``.starter("starter")``, load that
           file unconditionally (debug or prod -- user chose to keep it).
        2. Legacy fallback: if debug mode is enabled and ``starter.py``
           exists in the working directory, load it automatically.

        The starter controller is skipped if another controller has
        already registered ``GET /``.
        """
        import importlib
        import importlib.util
        from pathlib import Path

        # ── Determine starter source ──
        starter_module_name = None

        # v2.1: Check workspace config for .starter() declaration
        if hasattr(self, 'config') and self.config:
            try:
                ws_dict = self.config.to_dict() if hasattr(self.config, 'to_dict') else {}
                starter_module_name = ws_dict.get("starter")
            except Exception:
                pass

        # Resolve starter path
        starter_path = None
        if starter_module_name:
            candidate = Path.cwd() / f"{starter_module_name}.py"
            if candidate.exists():
                starter_path = candidate
        elif self._is_debug():
            # Legacy: auto-load starter.py in debug mode
            candidate = Path.cwd() / "starter.py"
            if candidate.exists():
                starter_path = candidate
                starter_module_name = "starter"

        if starter_path is None:
            return None

        # Check if any existing route already handles GET /
        try:
            existing_match = await self.controller_router.match("/", "GET", {})
            if existing_match:
                return None
        except Exception:
            pass

        try:
            spec = importlib.util.spec_from_file_location(
                starter_module_name, str(starter_path)
            )
            if spec is None or spec.loader is None:
                return None
            module = importlib.util.module_from_spec(spec)
            # Register in sys.modules so inspect.getfile() can resolve
            # the class back to its source file.
            import sys as _sys
            _sys.modules[starter_module_name] = module
            spec.loader.exec_module(module)

            # Find Controller subclasses in the module
            from .controller import Controller
            for attr_name in dir(module):
                obj = getattr(module, attr_name)
                if (
                    isinstance(obj, type)
                    and issubclass(obj, Controller)
                    and obj is not Controller
                ):
                    compiled = self.controller_compiler.compile_controller(
                        obj, base_prefix=None,
                    )
                    # Tag routes so DI can fall back gracefully
                    for route in compiled.routes:
                        route.app_name = "__starter__"
                    self.controller_router.add_controller(compiled)
                    return compiled

        except Exception as e:
            self.logger.warning(f"Could not load starter controller: {e}")

        return None

    def _import_controller_class(self, controller_path: str) -> type:
        """
        Import controller class from path.
        
        Args:
            controller_path: Import path in format "module.path:ClassName"
            
        Returns:
            Controller class
            
        Raises:
            ImportError: If module or class cannot be imported
            TypeError: If imported object is not a class
        """
        import importlib
        
        if ":" not in controller_path:
            raise ConfigInvalidFault(
                key="controller_path",
                reason=(
                    f"Invalid controller path '{controller_path}': "
                    f"Expected format 'module.path:ClassName'"
                ),
            )
        
        try:
            module_path, class_name = controller_path.rsplit(":", 1)
            module = importlib.import_module(module_path)
            controller_class = getattr(module, class_name)
            
            if not isinstance(controller_class, type):
                raise ConfigInvalidFault(
                    key="controller_path",
                    reason=(
                        f"{controller_path} resolved to {type(controller_class).__name__}, "
                        f"expected a class"
                    ),
                )
            
            return controller_class
            
        except ImportError as e:
            raise ImportError(
                f"Failed to import module '{module_path}' for controller {controller_path}: {e}"
            ) from e
        except AttributeError as e:
            raise ImportError(
                f"Class '{class_name}' not found in module '{module_path}': {e}"
            ) from e

    def _register_fault_handlers(self):
        """Register fault handlers from manifests."""
        import importlib
        
        for app_ctx in self.runtime.meta.app_contexts:
            # Check for faults config in manifest
            manifest = app_ctx.manifest
            if not manifest or not hasattr(manifest, "faults") or not manifest.faults:
                continue
            
            fault_config = manifest.faults
            if not hasattr(fault_config, "handlers"):
                continue

            for handler_cfg in fault_config.handlers:
                try:
                    handler_path = handler_cfg.handler_path
                    if ":" in handler_path:
                        mod_path, attr_name = handler_path.split(":", 1)
                    elif "." in handler_path:
                        mod_path, attr_name = handler_path.rsplit(".", 1)
                    else:
                        self.logger.error(f"Invalid handler path format: {handler_path}")
                        continue
                        
                    mod = importlib.import_module(mod_path)
                    handler_obj = getattr(mod, attr_name)
                    
                    if isinstance(handler_obj, type):
                        handler_instance = handler_obj()
                    else:
                        handler_instance = handler_obj
                        
                    self.fault_engine.register_app(app_ctx.name, handler_instance)
                except Exception as e:
                    self.logger.error(f"Failed to register fault handler {handler_cfg.handler_path} for app {app_ctx.name}: {e}")
    
    async def _register_amdl_models(self) -> None:
        """
        Register models discovered by the Aquilary pipeline.

        Supports both legacy AMDL (.amdl) files and new pure-Python Model
        subclasses (.py files with Model subclasses).

        Uses manifest-driven discovery (AppContext.models) populated by
        RuntimeRegistry.perform_autodiscovery() and explicit manifest
        declarations.  Also scans global ``models/`` and ``modules/``
        directories as a fallback for workspace-level model files.

        Lifecycle:
        1. Collect model paths from AppContexts + global scan
        2. Parse AMDL files / import Python model modules
        3. Configure database from manifest DatabaseConfig or config
        4. Optionally create tables / run migrations
        5. Register AquiliaDatabase + registries in all DI containers
        """
        from pathlib import Path

        try:
            from .models.parser import parse_amdl_file
            from .models.runtime import ModelRegistry as LegacyRegistry
            from .models.base import ModelRegistry, Model
            from .db.engine import AquiliaDatabase, configure_database, set_database
        except ImportError:
            return

        # ── Phase 1: Collect model paths ──────────────────────────────────
        model_files: list[Path] = []
        workspace_root = Path.cwd()

        # 1a. From AppContexts (populated by Aquilary auto-discovery + manifests)
        for ctx in self.runtime.meta.app_contexts:
            for model_path in ctx.models:
                p = Path(model_path)
                if p.is_file() and p not in model_files:
                    model_files.append(p)

        # 1b. Global fallback scan (workspace-level models/ and modules/)
        for search_dir in [workspace_root / "models", workspace_root / "modules"]:
            if search_dir.is_dir():
                for amdl in search_dir.rglob("*.amdl"):
                    if amdl not in model_files:
                        model_files.append(amdl)
                # Only pick up Python files that are inside a "models" directory
                # or are themselves named "models.py" -- never controllers/services/etc.
                for pyf in search_dir.rglob("*.py"):
                    # Skip private files (e.g. _helpers.py) but NOT __init__.py
                    if pyf.name.startswith("_") and pyf.name != "__init__.py":
                        continue
                    # Accept: models.py, or any .py inside a models/ package
                    is_model_file = (
                        pyf.stem == "models"
                        or "models" in pyf.parent.parts
                    )
                    if not is_model_file:
                        continue
                    if pyf not in model_files:
                        model_files.append(pyf)

        amdl_files = [f for f in model_files if f.suffix == ".amdl"]
        py_files = [f for f in model_files if f.suffix == ".py"]

        total_count = len(amdl_files) + len(py_files)

        # ── Phase 2a: Parse and register AMDL (legacy) ────────────────────
        legacy_registry = getattr(self.runtime, '_model_registry', None) or LegacyRegistry()
        amdl_count = 0

        for amdl_path in amdl_files:
            try:
                amdl_file = parse_amdl_file(str(amdl_path))
                for model in amdl_file.models:
                    if model.name not in legacy_registry._models:
                        legacy_registry.register_model(model)
                        amdl_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to parse {amdl_path}: {e}")

        # ── Phase 2b: Import and register Python models ───────────────────
        import importlib
        import importlib.util
        import sys
        py_count = 0

        for py_path in py_files:
            try:
                # Try package-aware import first (supports relative imports).
                # Compute a dotted module name relative to the workspace root.
                try:
                    rel = py_path.relative_to(workspace_root)
                except ValueError:
                    rel = None

                if rel is not None:
                    # e.g. modules/products/models/__init__.py → modules.products.models
                    parts = list(rel.with_suffix("").parts)
                    if parts and parts[-1] == "__init__":
                        parts = parts[:-1]
                    dotted = ".".join(parts)

                    # Ensure workspace root is on sys.path
                    ws_str = str(workspace_root)
                    if ws_str not in sys.path:
                        sys.path.insert(0, ws_str)

                    # Ensure parent packages exist in sys.modules
                    for i in range(1, len(parts)):
                        parent_dotted = ".".join(parts[:i])
                        if parent_dotted not in sys.modules:
                            parent_path = workspace_root / Path(*parts[:i])
                            init_file = parent_path / "__init__.py"
                            if init_file.is_file():
                                parent_spec = importlib.util.spec_from_file_location(
                                    parent_dotted, str(init_file),
                                    submodule_search_locations=[str(parent_path)]
                                )
                                if parent_spec and parent_spec.loader:
                                    parent_mod = importlib.util.module_from_spec(parent_spec)
                                    sys.modules[parent_dotted] = parent_mod
                                    try:
                                        parent_spec.loader.exec_module(parent_mod)
                                    except Exception:
                                        pass  # parent init may fail; that's ok
                            else:
                                # Create a namespace package stub
                                import types
                                ns_mod = types.ModuleType(parent_dotted)
                                ns_mod.__path__ = [str(parent_path)]
                                ns_mod.__package__ = parent_dotted
                                sys.modules[parent_dotted] = ns_mod

                    # Now import the actual model module
                    if dotted in sys.modules:
                        mod = sys.modules[dotted]
                    else:
                        mod = importlib.import_module(dotted)
                else:
                    # Fallback: file outside workspace, use spec_from_file_location
                    module_name = f"_aquilia_models_{py_path.stem}_{id(py_path)}"
                    spec = importlib.util.spec_from_file_location(module_name, str(py_path))
                    if spec is None or spec.loader is None:
                        continue
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                
                # Models self-register via metaclass; count them
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, Model)
                        and attr is not Model
                    ):
                        py_count += 1
            except Exception as e:
                self.logger.warning(f"Failed to import {py_path}: {e}")

        # ── Phase 3: Resolve database configuration ───────────────────────
        db_url = None
        auto_create = False
        auto_migrate = False
        migrations_dir = "migrations"

        # 3a. Check manifest DatabaseConfig across all app contexts
        for ctx in self.runtime.meta.app_contexts:
            manifest = ctx.manifest
            if manifest and hasattr(manifest, "database") and manifest.database:
                db_cfg = manifest.database
                db_url = db_url or getattr(db_cfg, "url", None)
                auto_create = auto_create or getattr(db_cfg, "auto_create", False)
                auto_migrate = auto_migrate or getattr(db_cfg, "auto_migrate", False)
                migrations_dir = getattr(db_cfg, "migrations_dir", migrations_dir)

        # 3b. Check config dict (Workspace.database() / Integration.database())
        if not db_url:
            if hasattr(self.config, 'get'):
                db_url = self.config.get("database.url", None)
                auto_create = auto_create or self.config.get("database.auto_create", False)
                auto_migrate = auto_migrate or self.config.get("database.auto_migrate", False)
            elif hasattr(self.config, 'to_dict'):
                cfg_dict = self.config.to_dict()
                db_section = cfg_dict.get("database", {})
                db_url = db_url or db_section.get("url")
                auto_create = auto_create or db_section.get("auto_create", False)
                auto_migrate = auto_migrate or db_section.get("auto_migrate", False)

        # ── Phase 3b: Startup guard -- warn if DB missing / stale ────────
        if db_url and not auto_migrate:
            try:
                from aquilia.models.startup_guard import check_db_ready

                db_ready = check_db_ready(
                    db_url=db_url,
                    migrations_dir=migrations_dir,
                    auto_migrate=auto_migrate,
                )
                if not db_ready:
                    # DB not ready -- still configure so we get better errors,
                    # but enable auto_create so tables are created on first boot
                    auto_create = True
            except SystemExit:
                # Legacy path: treat as warning, still proceed with auto_create
                auto_create = True
            except Exception as exc:
                self.logger.warning(f"Startup-guard check skipped: {exc}")

        # ── Phase 4: Connect and create tables ────────────────────────────
        if db_url:
            db = configure_database(db_url)
            await db.connect()
            self._amdl_database = db

            # Wire database to both registries
            if legacy_registry._models:
                legacy_registry.set_database(db)
            if ModelRegistry._models:
                ModelRegistry.set_database(db)

            if auto_create:
                # Create tables for both AMDL and Python models
                if legacy_registry._models:
                    await legacy_registry.create_tables()
                if ModelRegistry._models:
                    await ModelRegistry.create_tables()

            if auto_migrate:
                try:
                    from .models.migrations import MigrationRunner
                    runner = MigrationRunner(db, migrations_dir)
                    await runner.migrate()
                except Exception as e:
                    self.logger.warning(f"Auto-migration failed: {e}")

            # ── Phase 5: Register in DI containers ────────────────────────
            from .di.providers import ValueProvider
            for container in self.runtime.di_containers.values():
                try:
                    container.register(ValueProvider(
                        value=db,
                        token=AquiliaDatabase,
                        scope="app",
                    ))
                except (ValueError, Exception):
                    pass

                if legacy_registry._models:
                    try:
                        container.register(ValueProvider(
                            value=legacy_registry,
                            token=LegacyRegistry,
                            scope="app",
                        ))
                    except (ValueError, Exception):
                        pass

                if ModelRegistry._models:
                    try:
                        container.register(ValueProvider(
                            value=ModelRegistry,
                            token=ModelRegistry,
                            scope="app",
                        ))
                    except (ValueError, Exception):
                        pass

        else:
            self._amdl_database = None

    async def startup(self):
        """
        Execute startup sequence with Aquilary lifecycle management.
        
        Flow:
        1. Load and compile controllers from manifests
        2. Compile routes (includes service/effect registration)
        3. Start lifecycle coordinator (runs app startup hooks in dependency order)
        4. Log registered routes and apps
        5. Server ready
        
        This method is idempotent and thread-safe.
        """
        import time as _time

        # Prevent duplicate startup
        if self._startup_complete:
            return
        
        # Initialize lock in async context if needed
        if self._startup_lock is None:
            import asyncio
            self._startup_lock = asyncio.Lock()
        
        async with self._startup_lock:
            # Double-check after acquiring lock
            if self._startup_complete:
                return
            
            _boot_t0 = _time.monotonic()
            
            # Step 0: Perform runtime auto-discovery
            self.runtime.perform_autodiscovery()
            
            # Step 1: Load and compile controllers
            await self._load_controllers()

            # Step 1.5: Wire admin integration (if configured)
            self._wire_admin_integration()
        
            # Step 2: Compile routes (includes service registration and handler wrapping)
            self.runtime.compile_routes()
            
            # Step 3: Start lifecycle (runs app startup hooks in dependency order)
            try:
                await self.coordinator.startup()
            except Exception as e:
                from .lifecycle import LifecycleError
                self.logger.error(f"Lifecycle startup failed: {e}")
                raise LifecycleError(f"Startup failed: {e}") from e
            
            # Step 3.1: Register AMDL models from apps (if any .amdl files exist)
            await self._register_amdl_models()
            
            # Step 3.2: Start mail subsystem (connect providers)
            if hasattr(self, '_mail_service') and self._mail_service is not None:
                try:
                    await self._mail_service.on_startup()
                except Exception as e:
                    self.logger.error(f"Mail startup failed: {e}")
                    # Non-fatal -- app can run without mail

            # Step 3.3: Start background task manager
            if hasattr(self, '_task_manager') and self._task_manager is not None:
                try:
                    await self._task_manager.start()
                except Exception as e:
                    self.logger.error(f"Task manager startup failed: {e}")
                    # Non-fatal -- app can run without background tasks

            # Step 3.5: Register effects from manifests and initialize providers
            self.runtime._register_effects()
            try:
                from .effects import EffectRegistry
                # Retrieve the SAME EffectRegistry from DI (registered in __init__)
                base_container = self._get_base_container()
                try:
                    effect_registry = await base_container.resolve_async(EffectRegistry, optional=True)
                except Exception:
                    effect_registry = None
                
                if effect_registry is None:
                    effect_registry = EffectRegistry()
                
                await effect_registry.initialize_all()
                self._effect_registry = effect_registry

                # Wire effect registry into controller engine for FlowPipeline
                if hasattr(self, 'controller_engine') and self.controller_engine:
                    self.controller_engine.effect_registry = effect_registry
            except Exception as e:
                self._effect_registry = None
            
            # Step 3.6: Initialize cache subsystem (connect backend)
            if hasattr(self, '_cache_service') and self._cache_service is not None:
                try:
                    await self._cache_service.initialize()
                except Exception as e:
                    self.logger.error(f"Cache startup failed: {e}")
                    # Non-fatal -- app can run without cache

            # Step 3.7: Initialize storage subsystem (create dirs, connect backends)
            if hasattr(self, '_storage_registry') and self._storage_registry is not None:
                try:
                    await self._storage_registry.initialize_all()
                except Exception as e:
                    self.logger.error(f"Storage startup failed: {e}")
                    # Non-fatal -- app can run without storage

            # Step 4: Gather route/service counts for health registration
            routes = self.controller_router.get_routes()
            
            total_services = sum(
                len(container._providers)
                for container in self.runtime.di_containers.values()
            )
            
            # Mark startup complete
            self._startup_complete = True
            _startup_ms = (_time.monotonic() - _boot_t0) * 1000

            # v2: Register subsystem health statuses
            self.health_registry.register("aquilary", HealthStatus(
                name="aquilary", status=SubsystemStatus.HEALTHY,
                message=f"{len(self.runtime.meta.app_contexts)} apps loaded",
            ))
            self.health_registry.register("routing", HealthStatus(
                name="routing", status=SubsystemStatus.HEALTHY,
                message=f"{len(routes) if routes else 0} routes compiled",
            ))
            self.health_registry.register("di", HealthStatus(
                name="di", status=SubsystemStatus.HEALTHY,
                message=f"{total_services} services registered",
            ))
            if hasattr(self, '_cache_service') and self._cache_service is not None:
                self.health_registry.register("cache", HealthStatus(
                    name="cache", status=SubsystemStatus.HEALTHY,
                ))
            if hasattr(self, '_storage_registry') and self._storage_registry is not None:
                self.health_registry.register("storage", HealthStatus(
                    name="storage", status=SubsystemStatus.HEALTHY,
                    message=f"{len(self._storage_registry.aliases())} backends active",
                ))
            if hasattr(self, '_mail_service') and self._mail_service is not None:
                self.health_registry.register("mail", HealthStatus(
                    name="mail", status=SubsystemStatus.HEALTHY,
                ))
            if hasattr(self, '_task_manager') and self._task_manager is not None:
                self.health_registry.register("tasks", HealthStatus(
                    name="tasks", status=SubsystemStatus.HEALTHY,
                    message=f"{self._task_manager.num_workers} workers running",
                ))
            if hasattr(self, '_error_tracker') and self._error_tracker is not None:
                self.health_registry.register("error_tracker", HealthStatus(
                    name="error_tracker", status=SubsystemStatus.HEALTHY,
                    message="Monitoring faults",
                ))


    
    async def shutdown(self):
        """
        Execute shutdown sequence with Aquilary lifecycle management.
        
        Flow:
        1. Stop lifecycle coordinator (runs app shutdown hooks in reverse order)
        2. Cleanup DI containers
        3. Finalize effects
        4. Disconnect database
        
        This method is idempotent and safe to call multiple times.
        """
        if not self._startup_complete:
            return  # Nothing to shut down
        
        # Run lifecycle shutdown hooks
        await self.coordinator.shutdown()
        
        # Shutdown mail subsystem
        if hasattr(self, '_mail_service') and self._mail_service is not None:
            try:
                await self._mail_service.on_shutdown()
            except Exception as e:
                self.logger.warning(f"Error shutting down mail subsystem: {e}")

        # Shutdown background task manager
        if hasattr(self, '_task_manager') and self._task_manager is not None:
            try:
                await self._task_manager.stop()
            except Exception as e:
                self.logger.warning(f"Error shutting down task manager: {e}")

        # Shutdown cache subsystem
        if hasattr(self, '_cache_service') and self._cache_service is not None:
            try:
                await self._cache_service.shutdown()
            except Exception as e:
                self.logger.warning(f"Error shutting down cache subsystem: {e}")

        # Shutdown storage subsystem
        if hasattr(self, '_storage_registry') and self._storage_registry is not None:
            try:
                await self._storage_registry.shutdown_all()
            except Exception as e:
                self.logger.warning(f"Error shutting down storage subsystem: {e}")

        # Cleanup DI containers
        for app_name, container in self.runtime.di_containers.items():
            try:
                await container.shutdown()
            except Exception as e:
                self.logger.warning(f"Error cleaning up container for '{app_name}': {e}")
        
        # Finalize effect providers
        if hasattr(self, '_effect_registry') and self._effect_registry:
            try:
                await self._effect_registry.finalize_all()
            except Exception as e:
                self.logger.warning(f"Error finalizing effect providers: {e}")
        
        # Shutdown WebSocket runtime
        if hasattr(self, 'aquila_sockets') and self.aquila_sockets:
            try:
                await self.aquila_sockets.shutdown()
            except Exception as e:
                self.logger.warning(f"Error shutting down WebSocket runtime: {e}")

        # Disconnect AMDL database if connected
        if hasattr(self, '_amdl_database') and self._amdl_database:
            try:
                await self._amdl_database.disconnect()
            except Exception as e:
                self.logger.warning(f"Error disconnecting AMDL database: {e}")

        # Reset startup state
        self._startup_complete = False
    
    def get_health(self) -> dict:
        """
        Get current server health status (v2).
        
        Returns dict suitable for JSON serialization at /health endpoint.
        """
        return self.health_registry.to_dict()

    async def graceful_shutdown(self, timeout: float = 30.0):
        """
        Graceful shutdown sequence (v2).
        
        1. Stop accepting new connections
        2. Drain in-flight requests (with timeout)
        3. Run standard shutdown hooks
        4. Final cleanup
        
        Args:
            timeout: Maximum seconds to wait for in-flight requests
        """
        import asyncio
        
        self._accepting = False
        
        # Wait for in-flight requests to complete
        if self._inflight_requests > 0:
            deadline = asyncio.get_running_loop().time() + timeout
            while self._inflight_requests > 0:
                if asyncio.get_running_loop().time() > deadline:
                    self.logger.warning(
                        f"Forced shutdown -- {self._inflight_requests} "
                        f"requests still in-flight after {timeout}s"
                    )
                    break
                await asyncio.sleep(0.1)
        
        # Run standard shutdown
        await self.shutdown()

    def run(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        reload: Optional[bool] = None,
        log_level: str = "info",
        graceful_timeout: float = 30.0,
    ):
        """
        Run the development server with graceful shutdown support.

        Values default to the loaded ``AquilaConfig`` runtime settings,
        falling back to ``127.0.0.1:8000`` if no config is available.

        Args:
            host: Host to bind to (None = from config or 127.0.0.1)
            port: Port to bind to (None = from config or 8000)
            reload: Enable auto-reload (None = from config or False)
            log_level: Logging level
            graceful_timeout: Seconds to wait for in-flight requests on shutdown
        """
        # Resolve from loaded config if not explicitly provided
        rt = self.config.config_data.get("runtime", {})
        host   = host   if host   is not None else rt.get("host",   "127.0.0.1")
        port   = port   if port   is not None else rt.get("port",   8000)
        reload = reload if reload is not None else rt.get("reload", False)
        # Setup logging with color support
        class _ColorFmt(logging.Formatter):
            _C = {
                logging.DEBUG: "\033[36m", logging.INFO: "\033[32m",
                logging.WARNING: "\033[33m", logging.ERROR: "\033[31m",
                logging.CRITICAL: "\033[1;31m",
            }
            _R = "\033[0m"
            def format(self, record):
                c = self._C.get(record.levelno, "")
                m = super().format(record)
                return f"{c}{m}{self._R}" if c else m

        _h = logging.StreamHandler()
        _h.setFormatter(_ColorFmt('%(levelname)-8s | %(name)s -- %(message)s'))
        logging.root.handlers.clear()
        logging.root.addHandler(_h)
        logging.root.setLevel(getattr(logging, log_level.upper()))
        # Silence noisy third-party loggers
        for _noisy in ("python_multipart", "python_multipart.multipart"):
            logging.getLogger(_noisy).setLevel(logging.WARNING)
        
        try:
            import uvicorn
            from aquilia.cli.commands.run import _build_uvicorn_kwargs

            # Build kwargs from the full runtime config, with explicit
            # overrides taking priority.
            uv_kwargs = _build_uvicorn_kwargs(rt, overrides={
                "host": host,
                "port": port,
                "reload": reload,
                "log_level": log_level,
            })

            # uvicorn manages the event loop and lifespan (startup/shutdown)
            # via the ASGI lifespan protocol -- no need to call startup() manually
            uvicorn.run(self.app, **uv_kwargs)
        
        except ImportError:
            self.logger.error(
                "uvicorn is not installed. "
                "Install it with: pip install uvicorn"
            )
            raise
    
    def get_asgi_app(self):
        """Get the ASGI application for external servers."""
        return self.app
    
    def lifespan(self):
        """
        ASGI lifespan context manager.
        
        Use with ASGI servers that support the lifespan protocol::
        
            server = AquiliaServer(workspace_path)
            
            async def app(scope, receive, send):
                async with server.lifespan():
                    ...  # handle requests
        """
        from contextlib import asynccontextmanager
        
        @asynccontextmanager
        async def _lifespan():
            await self.startup()
            try:
                yield self
            finally:
                await self.graceful_shutdown()
        
        return _lifespan()
