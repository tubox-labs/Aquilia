"""Workspace generator."""

from pathlib import Path
from typing import Optional
import textwrap


class WorkspaceGenerator:
    """Generate Aquilia workspace structure."""
    
    def __init__(
        self,
        name: str,
        path: Path,
        minimal: bool = False,
        template: Optional[str] = None,
        *,
        include_docker: bool = True,
        include_readme: bool = True,
        include_makefile: bool = True,
        include_tests: bool = True,
        include_gitignore: bool = True,
        include_license: Optional[str] = None,
    ):
        self.name = name
        self.path = path
        self.minimal = minimal
        self.template = template
        self.include_docker = include_docker
        self.include_readme = include_readme
        self.include_makefile = include_makefile
        self.include_tests = include_tests
        self.include_gitignore = include_gitignore
        self.include_license = include_license
    
    def generate(self) -> None:
        """Generate workspace structure."""
        self.path.mkdir(parents=True, exist_ok=True)
        
        # Create directory structure
        self._create_directories()
        
        # Create manifest files
        self._create_workspace_manifest()
        
        # Create starter page
        self._create_starter_page()
        
        # Template files (--template flag or full mode)
        if self.template:
            self._create_template_files()
        
        # Create additional files (industry-standard project structure)
        if self.include_gitignore:
            self._create_gitignore()
        self._create_env_example()
        self._create_editorconfig()
        self._create_requirements()
        if self.include_tests:
            self._create_tests_dir()
        if not self.minimal:
            if self.include_readme:
                self._create_readme()
            if self.include_makefile:
                self._create_makefile()
            if self.include_docker:
                self._create_deployment_files()
        if self.include_license:
            self._create_license_file()
        
        # Create starter locale files (i18n readiness)
        self._create_locale_files()
    
    def _create_directories(self) -> None:
        """Create workspace directories."""
        dirs = ['modules']
        
        if not self.minimal:
            dirs.extend(['artifacts'])
        
        # Always create locales directory for i18n readiness
        dirs.extend(['locales', 'locales/en'])
        
        if self.template:
            dirs.extend([
                'templates',
                'templates/includes',
                'assets',
                'assets/css',
                'assets/js',
            ])
        
        for dir_name in dirs:
            (self.path / dir_name).mkdir(parents=True, exist_ok=True)
    
    def _extract_field(self, content: str, pattern: str, default: str) -> str:
        """Extract a single field from manifest content."""
        import re
        match = re.search(pattern, content)
        return match.group(1) if match else default
    
    def _extract_list(self, content: str, pattern: str, default: list = None) -> list:
        """Extract a list field from manifest content."""
        import re
        if default is None:
            default = []
        match = re.search(pattern, content, re.DOTALL)
        if not match:
            return default
        
        list_content = match.group(1)
        # Extract quoted strings from the list
        items = re.findall(r'"([^"]+)"', list_content)
        return items if items else default
    
    def generate_workspace_module_config(self, discovered_modules: dict) -> str:
        """
        Generate workspace module configuration as pointers to per-module manifests.
        
        In the Manifest-First Architecture, workspace.py declares **which**
        modules exist and their orchestration metadata (route prefix, tags,
        dependencies). All component declarations (controllers, services,
        middleware, etc.) live exclusively in each module's ``manifest.py``.
        
        Args:
            discovered_modules: Dictionary of discovered module data
            
        Returns:
            String containing workspace module configuration (pointers only)
        """
        lines = []
        
        for mod_name, mod_data in discovered_modules.items():
            # Generate module configuration -- pointer only
            version = mod_data.get('version', '0.1.0')
            description = mod_data.get('description', f'{mod_name.capitalize()} module')
            route_prefix = mod_data.get('route_prefix', f'/{mod_name}')
            tags = mod_data.get('tags', [])
            depends_on = mod_data.get('depends_on', [])
            
            # Build slim module config (orchestration metadata only)
            base_config = f'Module("{mod_name}", version="{version}", description="{description}")'
            
            # Add route prefix
            config_chain = f'{base_config}\n        .route_prefix("{route_prefix}")'
            
            # Add tags
            if tags:
                tags_str = ', '.join(f'"{tag}"' for tag in tags)
                config_chain += f'\n        .tags({tags_str})'
            
            # Add dependencies
            if depends_on:
                deps_str = ', '.join(f'"{dep}"' for dep in depends_on)
                config_chain += f'\n        .depends_on({deps_str})'
            
            # .module at same level as .integrate (4 spaces)
            module_line = f'    .module({config_chain})'
            lines.append(module_line)
        
        # Separate each .module() block with a blank line for readability
        return '\n\n'.join(lines)
    
    def update_workspace_config(self, workspace_path: Path, discovered_modules: dict) -> None:
        """
        Update workspace.py with auto-discovered module configurations.
        
        Safely strips existing .module() blocks and re-inserts them
        before the integrations section, preserving all other content.
        
        Args:
            workspace_path: Path to workspace.py file
            discovered_modules: Dictionary of discovered module data
        """
        if not workspace_path.exists():
            return
        
        content = workspace_path.read_text(encoding="utf-8")
        
        # Generate new module configuration
        new_config = self.generate_workspace_module_config(discovered_modules)
        
        import re
        
        # --- Phase 1: Strip all existing .module() blocks ---
        lines = content.split('\n')
        new_lines = []
        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.lstrip()
            
            # Only match lines where .module( is at the START of meaningful content
            # (possibly preceded by whitespace). This avoids matching lines where
            # .module( appears embedded inside a comment.
            if stripped.startswith('.module('):
                # Skip the entire multi-line .module(...) block
                paren_depth = 0
                while i < len(lines):
                    paren_depth += lines[i].count('(') - lines[i].count(')')
                    i += 1
                    if paren_depth <= 0:
                        break
            else:
                new_lines.append(line)
                i += 1
        
        content = '\n'.join(new_lines)
        
        # --- Phase 2: Remove any existing "# ---- Modules" section header ---
        content = re.sub(r'\n\s*# -+ Modules -+\n', '\n', content)
        
        # --- Phase 3: Find the insertion point ---
        # Strategy: insert modules BEFORE the integrations section.
        # Look for known markers in order of preference:
        #   1. "# ---- Integrations" (our own marker)
        #   2. Any comment line containing "Integrations"
        #   3. First .integrate( call
        
        insertion_re = re.search(
            r'^(\s*# -+ Integrations)',
            content,
            re.MULTILINE,
        )
        if not insertion_re:
            insertion_re = re.search(
                r'^(\s*#.*Integrations)',
                content,
                re.MULTILINE,
            )
        if not insertion_re:
            insertion_re = re.search(
                r'^(\s*\.integrate\()',
                content,
                re.MULTILINE,
            )
        
        if insertion_re:
            pos = insertion_re.start()
            # Build the modules section with its own header
            modules_section = (
                '\n    # ---- Modules '
                + '-' * 57
                + '\n\n'
                + new_config
                + '\n\n'
            )
            content = content[:pos] + modules_section + content[pos:]
        
        # --- Phase 4: Clean up excessive blank lines ---
        content = re.sub(r'\n{3,}', '\n\n', content)
        
        # --- Phase 5: Validate syntax before writing ---
        import ast
        try:
            ast.parse(content)
        except SyntaxError as exc:
            print(
                f"  \u26a0\ufe0f  Generated workspace.py has syntax error "
                f"(line {exc.lineno}): {exc.msg} -- skipping write"
            )
            return
        
        # Write back
        workspace_path.write_text(content, encoding="utf-8")
        print(f"\u2705 Updated workspace.py with {len(discovered_modules)} module configurations")

    def _discover_modules(self) -> dict:
        """Enhanced module discovery with intelligent classification.
        
        Architecture v2: Uses AutoDiscoveryEngine (AST-based) as primary
        scanner, with EnhancedDiscovery as fallback for legacy workspaces.
        """
        modules_dir = self.path / 'modules'
        discovered_modules = {}
        
        if not modules_dir.exists():
            return discovered_modules
        
        # v2: Try AST-based auto-discovery engine first
        ast_results = {}
        try:
            from aquilia.discovery.engine import AutoDiscoveryEngine
            engine = AutoDiscoveryEngine(modules_dir)
            ast_results = engine.discover_all()
        except Exception:
            pass
        
        # Legacy discovery as fallback
        try:
            from aquilia.cli.discovery_utils import EnhancedDiscovery
            discovery = EnhancedDiscovery(verbose=False)
        except Exception:
            discovery = None
        
        # Find all module directories with manifest.py
        module_dirs = [d for d in modules_dir.iterdir() 
                      if d.is_dir() and (d / 'manifest.py').exists()]
        
        # Parse all manifests
        for mod_dir in module_dirs:
            mod_name = mod_dir.name
            try:
                manifest_content = (mod_dir / 'manifest.py').read_text(encoding="utf-8")
                
                # Extract all module metadata
                version = self._extract_field(manifest_content, r'version="([^"]+)"', "0.1.0")
                description = self._extract_field(manifest_content, r'description="([^"]+)"', mod_name.capitalize())
                route_prefix = self._extract_field(manifest_content, r'route_prefix="([^"]+)"', f"/{mod_name}")
                author = self._extract_field(manifest_content, r'author="([^"]+)"', "")
                tags = self._extract_list(manifest_content, r'tags=\[(.*?)\]', [])
                base_path = self._extract_field(manifest_content, r'base_path="([^"]+)"', f"modules.{mod_name}")
                depends_on = self._extract_list(manifest_content, r'depends_on=\[(.*?)\]', [])
                # v2: also extract imports field
                imports_list = self._extract_list(manifest_content, r'imports=\s*\[(.*?)\]', [])
                if imports_list:
                    depends_on = imports_list  # v2 imports supersede legacy depends_on
                
                # Extract current manifest declarations (baseline)
                manifest_services_list = self._extract_list(manifest_content, r'services=\s*\[(.*?)\]', [])
                manifest_controllers_list = self._extract_list(manifest_content, r'controllers=\s*\[(.*?)\]', [])
                manifest_middleware_list = self._extract_list(manifest_content, r'middleware=\s*\[(.*?)\]', [])
                manifest_socket_controllers_list = self._extract_list(manifest_content, r'socket_controllers=\s*\[(.*?)\]', [])
                # v2: Extract new component types
                manifest_guards_list = self._extract_list(manifest_content, r'guards=\s*\[(.*?)\]', [])
                manifest_pipes_list = self._extract_list(manifest_content, r'pipes=\s*\[(.*?)\]', [])
                manifest_interceptors_list = self._extract_list(manifest_content, r'interceptors=\s*\[(.*?)\]', [])
                manifest_exports_list = self._extract_list(manifest_content, r'exports=\s*\[(.*?)\]', [])

                # v2: Merge AST-discovered components with manifest declarations
                if mod_name in ast_results:
                    result = ast_results[mod_name]
                    # AST engine provides more accurate classification
                    controllers_list = [c.name for c in result.controllers] or manifest_controllers_list
                    services_list = [c.name for c in result.services] or manifest_services_list
                    guards_list = [c.name for c in result.guards] or manifest_guards_list
                    pipes_list = [c.name for c in result.pipes] or manifest_pipes_list
                    interceptors_list = [c.name for c in result.interceptors] or manifest_interceptors_list
                    socket_controllers_list = manifest_socket_controllers_list  # AST engine doesn't scan sockets yet
                else:
                    # Fallback: try EnhancedDiscovery
                    services_list = manifest_services_list
                    controllers_list = manifest_controllers_list
                    socket_controllers_list = manifest_socket_controllers_list
                    guards_list = manifest_guards_list
                    pipes_list = manifest_pipes_list
                    interceptors_list = manifest_interceptors_list
                    
                    if discovery:
                        try:
                            result = discovery.discover_module_controllers_and_services(
                                base_path, mod_name
                            )
                            if len(result) == 3:
                                discovered_controllers, discovered_services, discovered_sockets = result
                            else:
                                discovered_controllers, discovered_services = result
                                discovered_sockets = []
                            
                            services_list = discovered_services if discovered_services else manifest_services_list
                            controllers_list = discovered_controllers if discovered_controllers else manifest_controllers_list
                            socket_controllers_list = discovered_sockets if discovered_sockets else manifest_socket_controllers_list
                        except Exception:
                            pass
                
                # Check for actual declarations/discoveries
                has_services = len(services_list) > 0
                has_controllers = len(controllers_list) > 0
                has_sockets = len(socket_controllers_list) > 0
                has_middleware = len(manifest_middleware_list) > 0
                has_guards = len(guards_list) > 0
                has_pipes = len(pipes_list) > 0
                has_interceptors = len(interceptors_list) > 0
                
                discovered_modules[mod_name] = {
                    'name': mod_name,
                    'path': mod_dir,
                    'version': version,
                    'description': description,
                    'route_prefix': route_prefix,
                    'author': author,
                    'tags': tags,
                    'base_path': base_path,
                    'depends_on': depends_on,
                    'has_services': has_services,
                    'has_controllers': has_controllers,
                    'has_sockets': has_sockets,
                    'has_middleware': has_middleware,
                    'has_guards': has_guards,
                    'has_pipes': has_pipes,
                    'has_interceptors': has_interceptors,
                    'services_list': services_list,
                    'controllers_list': controllers_list,
                    'socket_controllers_list': socket_controllers_list,
                    'middleware_list': manifest_middleware_list,
                    'guards_list': guards_list,
                    'pipes_list': pipes_list,
                    'interceptors_list': interceptors_list,
                    'exports_list': manifest_exports_list,
                    'services_count': len(services_list),
                    'controllers_count': len(controllers_list),
                    'socket_controllers_count': len(socket_controllers_list),
                    'middleware_count': len(manifest_middleware_list),
                    'guards_count': len(guards_list),
                    'pipes_count': len(pipes_list),
                    'interceptors_count': len(interceptors_list),
                    'manifest_path': mod_dir / 'manifest.py',
                }
            except Exception:
                # Silently skip modules with parsing errors
                pass
        
        return discovered_modules
    
    def _resolve_dependencies(self, modules: dict) -> list:
        """Topologically sort modules based on dependencies (Kahn's algorithm)."""
        if not modules:
            return []
        
        # Build dependency graph
        graph = {name: mod.get('depends_on', []) for name, mod in modules.items()}
        in_degree = {name: 0 for name in modules}
        
        # Calculate in-degrees
        for name in modules:
            for dep in graph.get(name, []):
                if dep in in_degree:
                    in_degree[name] += 1
        
        # Process nodes with no dependencies
        sorted_modules = []
        queue = [name for name, degree in in_degree.items() if degree == 0]
        
        while queue:
            node = queue.pop(0)
            sorted_modules.append(node)
            
            # Reduce in-degree for dependent modules
            for name in modules:
                if node in graph.get(name, []):
                    in_degree[name] -= 1
                    if in_degree[name] == 0:
                        queue.append(name)
        
        # Return sorted modules, fall back to alphabetical if cycles detected
        return sorted_modules if len(sorted_modules) == len(modules) else sorted(modules.keys())
    
    def _validate_modules(self, modules: dict) -> dict:
        """Validate modules and detect conflicts."""
        validation = {
            'valid': True,
            'warnings': [],
            'errors': [],
        }
        
        route_prefixes = {}
        for name, mod in modules.items():
            route = mod['route_prefix']
            if route in route_prefixes:
                validation['warnings'].append(
                    f"Route prefix conflict: '{route}' used by both '{name}' and '{route_prefixes[route]}'"
                )
            else:
                route_prefixes[route] = name
            
            # Check for missing dependencies
            for dep in mod.get('depends_on', []):
                if dep not in modules:
                    validation['errors'].append(
                        f"Module '{name}' depends on '{dep}' which is not installed"
                    )
                    validation['valid'] = False
        
        return validation
    
    def _create_workspace_manifest(self) -> None:
        """Create aquilia.py configuration (Python-based, production-grade).

        When ``self.minimal`` is True, generates a lean workspace with just
        the bare essentials: DI, routing, fault handling, and patterns --
        no sessions, no security middleware, no telemetry, no templates,
        no static files.
        """
        if self.minimal:
            self._create_minimal_workspace_manifest()
            return

        # Discover all modules with enhanced detection
        discovered = self._discover_modules()
        module_registrations = ""
        
        if discovered:
            # Validate modules
            validation = self._validate_modules(discovered)
            
            # Resolve dependencies and get sorted order
            sorted_names = self._resolve_dependencies(discovered)
            
            module_lines = []
            for mod_name in sorted_names:
                mod = discovered[mod_name]
                
                # Build slim module registration -- pointer only
                # Component declarations (controllers, services, etc.) live in manifest.py
                
                base_config = f'Module("{mod["name"]}", version="{mod["version"]}", description="{mod["description"]}")'
                
                # Add route prefix
                config_chain = f'{base_config}\n        .route_prefix("{mod["route_prefix"]}")'
                
                # Add tags
                if mod.get('tags'):
                    tags_part = ", ".join(f'"{t}"' for t in mod['tags'])
                    config_chain += f'\n        .tags({tags_part})'
                
                # Add dependencies
                if mod.get('depends_on'):
                    deps_part = ", ".join(f'"{d}"' for d in mod['depends_on'])
                    config_chain += f'\n        .depends_on({deps_part})'
                
                # .module(Module(...) on same line, then chain methods indented
                module_line = f'.module({config_chain}\n    ))'
                module_lines.append(module_line)
            
            if module_lines:
                # Indent each module block with 4 spaces
                module_registrations = "\n" + "\n".join("    " + line.replace("\n", "\n    ") for line in module_lines)
        
        content = textwrap.dedent(f'''\
            """
            Aquilia Workspace Configuration - Production Grade
            Generated by: aq init workspace {self.name}

            Single-file workspace configuration.
            Everything — structure, modules, integrations, and operational
            settings (server, auth, DB) — lives in this one file.

            - Type-safe with full IDE support
            - Version-controlled and shared across team
            - Observable via introspection
            - Environment layering via AquilaConfig subclasses

            Override order: BaseEnv → <AQ_ENV>Env → environment variables
            """

            from aquilia import Workspace, Module, Integration
            from aquilia.config_builders import AquilaConfig, Secret, Env


            # ── Environment Configuration ────────────────────────────────────
            # Operational settings (server, auth, DB, mail) as Python classes.
            # Activate: AQ_ENV=dev (default) | AQ_ENV=prod

            class BaseEnv(AquilaConfig):
                """Shared defaults — every environment inherits these."""
                env = "dev"

                class server(AquilaConfig.Server):
                    host    = "127.0.0.1"
                    port    = 8000
                    workers = 1
                    reload  = False

                    # ── Timeouts ───────────────────────────────────────────
                    # timeout_keep_alive = 5        # seconds to keep idle connections open
                    # timeout_worker_healthcheck = 30  # seconds before worker considered unresponsive
                    # timeout_graceful_shutdown = 30 # seconds to wait on shutdown

                    # ── Limits ─────────────────────────────────────────────
                    # backlog            = 2048      # TCP connection backlog
                    # limit_concurrency  = None      # max concurrent connections
                    # limit_max_requests = None      # restart worker after N requests

                    # ── Proxy / Headers ───────────────────────────────────
                    # proxy_headers      = True      # trust X-Forwarded-* headers
                    # forwarded_allow_ips = "*"      # IPs allowed to set proxy headers
                    # root_path          = ""        # ASGI root_path for reverse proxies

                    # ── WebSocket ─────────────────────────────────────────
                    # ws_max_size        = 16_777_216  # max WebSocket message (16 MiB)
                    # ws_ping_interval   = 20.0        # ping every N seconds
                    # ws_ping_timeout    = 20.0        # close if pong not received

                    # ── TLS / SSL ─────────────────────────────────────────
                    # ssl_certfile       = "/etc/certs/cert.pem"
                    # ssl_keyfile        = "/etc/certs/key.pem"
                    # ssl_ca_certs       = None

                    # ── Protocol Implementation ───────────────────────────
                    # http = "auto"        # "auto" | "h11" | "httptools"
                    # ws   = "auto"        # "auto" | "wsproto" | "websockets" | "none"
                    # loop = "auto"        # "auto" | "asyncio" | "uvloop"

                class auth(AquilaConfig.Auth):
                    secret_key      = Secret(env="AQ_SECRET_KEY", default="change-me-in-prod")
                    password_hasher = AquilaConfig.PasswordHasher(algorithm="argon2id")


            class DevEnv(BaseEnv):
                """Development — hot-reload, debug pages, single worker."""
                env = "dev"

                class server(BaseEnv.server):
                    debug   = True
                    reload  = True
                    workers = 1


            class ProdEnv(BaseEnv):
                """Production — multi-worker, no reload, no debug."""
                env = "prod"

                class server(BaseEnv.server):
                    host               = Env("AQ_HOST", default="0.0.0.0")
                    port               = Env("AQ_PORT", default=8000, cast=int)
                    workers            = Env("AQ_WORKERS", default=4, cast=int)
                    reload             = False
                    access_log         = False
                    timeout_keep_alive = 30
                    limit_max_requests = 10_000   # auto-restart workers after 10k requests
                    proxy_headers      = True     # trust X-Forwarded-* from load balancer

                class auth(BaseEnv.auth):
                    secret_key = Secret(env="AQ_SECRET_KEY", required=True)


            # ── Workspace Structure ──────────────────────────────────────────

            workspace = (
                Workspace(
                    name="{self.name}",
                    version="1.0.0",
                    description="Aquilia workspace",
                )
                # Wire environment config (resolved by AQ_ENV at runtime)
                .env_config(BaseEnv)

                # Starter module -- registered here so the server does not need
                # to hard-code it. Delete this line (and starter.py) once you
                # add your own modules with a GET "/" route.
                .starter("starter")
{"" if not module_registrations else chr(10) + "    # Auto-detected modules" + module_registrations}
                # Add modules here with explicit configuration:
                # .module(Module("auth", version="1.0.0", description="Authentication module").route_prefix("/api/v1/auth").depends_on("core"))
                # .module(Module("users", version="1.0.0", description="User management").route_prefix("/api/v1/users").depends_on("auth", "core"))

                # Middleware chain -- controls which middleware runs and in what order.
                # Presets: defaults() (dev), production(), minimal()
                # Custom: Integration.middleware.chain().use("aquilia.middleware.ExceptionMiddleware", priority=1).use(...)
                .middleware(Integration.middleware.defaults())

                # Integrations - Configure core systems
                .integrate(Integration.di(auto_wire=True, manifest_validation=True))
                .integrate(Integration.registry(
                    mode="auto",  # "dev", "prod", "auto" (env-based)
                    fingerprint_verification=True,
                ))
                .integrate(Integration.routing(
                    strict_matching=True,
                    version_support=True,
                    compression=True,
                ))
                .integrate(Integration.fault_handling(
                    default_strategy="propagate",
                    metrics_enabled=True,
                ))
                .integrate(Integration.patterns())

                # Database - Configure the ORM backend
                .integrate(Integration.database(
                    url="sqlite:///db.sqlite3",       # SQLite (dev)
                    # url="postgresql://user:pass@localhost:5432/{self.name}",  # PostgreSQL
                    pool_size=5,
                    echo=False,
                    auto_migrate=False,
                ))

                # Cache - In-memory by default, switch to Redis for production
                .integrate(Integration.cache(
                    backend="memory",
                    default_ttl=300,
                    max_size=1024,
                    key_prefix="{self.name}:",
                ))
                
                # Templates - Fluent configuration
                .integrate(
                    Integration.templates
                    .source("templates")
                    .scan_modules()
                    .cached("memory")
                    .secure()
                )

                # Static Files - Serve static assets (CSS, JS, images)
                .integrate(Integration.static_files(
                    directories={{"/static": "static"}},
                    cache_max_age=86400,
                    etag=True,
                ))

                # Sessions (uncomment to enable session management)
                # .sessions(
                #     policies=[
                #         SessionPolicy(
                #             name="default",
                #             ttl=timedelta(days=7),
                #             idle_timeout=timedelta(hours=1),
                #             absolute_timeout=timedelta(days=30),
                #             rotate_on_use=False,
                #             rotate_on_privilege_change=True,
                #             fingerprint_binding=False,
                #             scope="user",
                #             persistence=PersistencePolicy(
                #                 enabled=True,
                #                 store_name="default",
                #                 write_through=True,
                #                 compress=False,
                #             ),
                #             concurrency=ConcurrencyPolicy(
                #                 max_sessions_per_principal=5,
                #                 behavior_on_limit="evict_oldest",
                #             ),
                #             transport=TransportPolicy(
                #                 cookie_name="{self.name}_session",
                #                 cookie_secure=False,
                #                 cookie_httponly=True,
                #                 cookie_samesite="lax",
                #             ),
                #         ),
                #     ],
                # )

                # Security (uncomment to enable security middleware)
                # Fine-grained: use Integration.cors(), Integration.csp(),
                # Integration.rate_limit() with .integrate().
                # .security(
                #     cors_enabled=False,
                #     csrf_protection=False,
                #     helmet_enabled=True,
                #     rate_limiting=False,
                # )

                # Telemetry (uncomment to enable observability)
                # .telemetry(
                #     tracing_enabled=False,
                #     metrics_enabled=True,
                #     logging_enabled=True,
                # )

                # Admin Dashboard (uncomment to enable admin at /admin/)
                # Requires: aq admin createsuperuser
                # .integrate(Integration.admin(
                #     url_prefix="/admin",
                #     site_title="{self.name} Admin",
                #     auto_discover=True,
                # ))
            )


            # Export for CLI/server
            __all__ = ["workspace"]
        ''').strip()

        (self.path / 'workspace.py').write_text(content, encoding="utf-8")

    def _create_minimal_workspace_manifest(self) -> None:
        """Create a minimal workspace.py -- just enough to run.

        No sessions, no security, no telemetry, no templates, no static
        files. Users can add integrations later with ``aq add module``
        or by editing workspace.py directly.

        Environment config (AquilaConfig) is inlined directly in this
        file — no separate ``config/env.py``.
        """
        content = textwrap.dedent(f'''\
            """
            Aquilia Workspace -- {self.name} (minimal)
            Generated by: aq init workspace {self.name} --minimal
            """

            from aquilia import Workspace, Module, Integration
            from aquilia.config_builders import AquilaConfig, Secret, Env
            from datetime import timedelta
            from aquilia.sessions import SessionPolicy, TransportPolicy
            from aquilia.sessions import PersistencePolicy, ConcurrencyPolicy


            # ── Environment Configuration ────────────────────────────────────────

            class BaseEnv(AquilaConfig):
                """Shared defaults — every environment inherits these."""
                env = "dev"

                class server(AquilaConfig.Server):
                    host    = "127.0.0.1"
                    port    = 8000
                    workers = 1
                    reload  = False
                    # See AquilaConfig.Server for all options:
                    # timeout_keep_alive, backlog, limit_concurrency,
                    # limit_max_requests, proxy_headers, root_path,
                    # ws_max_size, ssl_certfile, ssl_keyfile, loop, http, ...


            # ── Workspace Structure ──────────────────────────────────────────────

            workspace = (
                Workspace(
                    name="{self.name}",
                    version="1.0.0",
                    description="{self.name} workspace",
                )
                # Wire environment config (resolved by AQ_ENV at runtime)
                .env_config(BaseEnv)

                # Starter module -- remove once you add GET /
                .starter("starter")

                # Middleware chain -- presets: defaults(), production(), minimal()
                .middleware(Integration.middleware.minimal())

                # Integrations -- core only
                .integrate(Integration.di(auto_wire=True))
                .integrate(Integration.routing(strict_matching=True))
                .integrate(Integration.fault_handling(default_strategy="propagate"))
                .integrate(Integration.patterns())

                # Database
                .integrate(Integration.database(url="sqlite:///db.sqlite3"))

                # Add modules:
                #   .module(Module("users").route_prefix("/users"))

                # Sessions
                .sessions(
                    policies=[
                        SessionPolicy(
                            name="default",
                            ttl=timedelta(days=7),
                            idle_timeout=timedelta(hours=1),
                            absolute_timeout=timedelta(days=30),
                            rotate_on_use=False,
                            rotate_on_privilege_change=True,
                            fingerprint_binding=False,
                            scope="user",
                            persistence=PersistencePolicy(
                                enabled=True,
                                store_name="default",
                                write_through=True,
                                compress=False,
                            ),
                            concurrency=ConcurrencyPolicy(
                                max_sessions_per_principal=5,
                                behavior_on_limit="evict_oldest",
                            ),
                            transport=TransportPolicy(
                                cookie_name="{self.name}_session",
                                cookie_secure=False,
                                cookie_httponly=True,
                                cookie_samesite="lax",
                            ),
                        ),
                    ],
                )
            )


            __all__ = ["workspace"]
        ''').strip()

        (self.path / 'workspace.py').write_text(content, encoding="utf-8")

    def _create_config_files(self) -> None:
        """No-op — environment config is now inlined in workspace.py.

        Kept for backward compatibility with subclasses that may call
        ``super()._create_config_files()``.
        """
        pass

    def _create_starter_page(self) -> None:
        """Create a starter welcome controller that renders the Aquilia welcome page.

        This gives new workspaces a default landing page visible at ``/``.
        The page is only shown when ``debug=True`` -- in production it
        should be replaced by real routes.
        """
        # Create the starter controller file in the workspace root
        content = textwrap.dedent('''\
            """
            Aquilia Starter Page -- shown at / when debug=True.

            Replace this controller with your own routes.
            Delete this file once you have real endpoints.
            """

            from aquilia import Controller, GET, RequestCtx, Response


            class StarterController(Controller):
                """Default welcome page controller.

                Renders the built-in Aquilia welcome page using MongoDB Atlas
                colors with dark/light mode support.

                Remove this controller once you've added your own modules.
                """
                prefix = "/"
                tags = ["starter"]

                @GET("/")
                async def welcome(self, ctx: RequestCtx):
                    """Render the Aquilia welcome page."""
                    from aquilia.debug.pages import render_welcome_page
                    try:
                        from aquilia import __version__
                        version = __version__
                    except Exception:
                        version = ""

                    html = render_welcome_page(aquilia_version=version)
                    return Response(
                        content=html.encode("utf-8"),
                        status=200,
                        headers={"content-type": "text/html; charset=utf-8"},
                    )
        ''')

        (self.path / 'starter.py').write_text(content, encoding="utf-8")

    # ------------------------------------------------------------------
    # Scaffold files: models, cache, auth, templates
    # ------------------------------------------------------------------

    def _create_models_dir(self) -> None:
        """Create models/{workspace_name}.py with a basic Aquilia ORM model."""
        models_dir = self.path / 'models'
        models_dir.mkdir(exist_ok=True)

        model_name = self.name.capitalize()
        table_name = self.name.lower()

        init_content = textwrap.dedent(f'''\
            """
            {self.name} workspace models.

            Import your models here so they are registered with the ORM
            when the workspace boots.
            """

            from .{self.name} import *  # noqa: F401,F403
        ''').strip()

        model_content = textwrap.dedent(f'''\
            """
            {model_name} models -- Aquilia ORM.

            Define your database models here. Models are auto-discovered
            when ``auto_discover=True`` in the workspace or module manifest.

            Usage:
                from models.{self.name} import {model_name}Item

                # Create
                item = await {model_name}Item.objects.create(name="Example")

                # Query
                items = await {model_name}Item.objects.all()
                item  = await {model_name}Item.objects.get(id=1)

                # Filter
                active = await {model_name}Item.objects.filter(active=True)
            """

            from aquilia.models import Model
            from aquilia.models.fields import (
                AutoField,
                CharField,
                TextField,
                BooleanField,
                DateTimeField,
            )


            class {model_name}Item(Model):
                """Example model for the {self.name} workspace."""

                table = "{table_name}_items"

                id = AutoField(primary_key=True)
                name = CharField(max_length=255)
                description = TextField(blank=True, default="")
                active = BooleanField(default=True)
                created_at = DateTimeField(auto_now_add=True)
                updated_at = DateTimeField(auto_now=True)

                class Meta:
                    ordering = ["-created_at"]

                def __repr__(self):
                    return f"<{model_name}Item id={{self.id}} name={{self.name!r}}>"
        ''').strip()

        (models_dir / '__init__.py').write_text(init_content, encoding="utf-8")
        (models_dir / f'{self.name}.py').write_text(model_content, encoding="utf-8")

    # ------------------------------------------------------------------
    # Industry-standard project files
    # ------------------------------------------------------------------

    def _create_env_example(self) -> None:
        """Create .env.example with documented environment variables."""
        content = textwrap.dedent(f"""\
            # ──────────────────────────────────────────────────────────────────
            # {self.name} -- Environment Variables
            # ──────────────────────────────────────────────────────────────────
            # Copy this file to .env and fill in your values:
            #   cp .env.example .env
            #
            # NEVER commit .env to version control.
            # ──────────────────────────────────────────────────────────────────

            # ── Server ────────────────────────────────────────────────────────
            AQUILIA_MODE=dev                       # dev | prod | test
            AQUILIA_HOST=127.0.0.1
            AQUILIA_PORT=8000
            AQUILIA_WORKERS=1                      # Set to CPU count in prod
            AQUILIA_DEBUG=true                      # false in prod

            # ── Database ──────────────────────────────────────────────────────
            DATABASE_URL=sqlite:///db.sqlite3
            # DATABASE_URL=postgresql://user:password@localhost:5432/{self.name}
            # DATABASE_URL=mysql://user:password@localhost:3306/{self.name}

            # ── Security ──────────────────────────────────────────────────────
            SECRET_KEY=change-me-in-production
            # JWT_SECRET_KEY=
            # ALLOWED_HOSTS=localhost,127.0.0.1

            # ── Cache ─────────────────────────────────────────────────────────
            CACHE_BACKEND=memory                   # memory | redis
            # REDIS_URL=redis://localhost:6379/0

            # ── Mail ──────────────────────────────────────────────────────────
            # MAIL_PROVIDER=console                # console | smtp
            # SMTP_HOST=smtp.example.com
            # SMTP_PORT=587
            # SMTP_USER=
            # SMTP_PASSWORD=
            # MAIL_FROM=noreply@example.com

            # ── Logging ───────────────────────────────────────────────────────
            LOG_LEVEL=INFO                         # DEBUG | INFO | WARNING | ERROR
        """)

        (self.path / '.env.example').write_text(content, encoding="utf-8")

    def _create_editorconfig(self) -> None:
        """Create .editorconfig for consistent coding style across editors."""
        content = textwrap.dedent("""\
            # https://editorconfig.org
            root = true

            [*]
            charset = utf-8
            end_of_line = lf
            indent_style = space
            indent_size = 4
            insert_final_newline = true
            trim_trailing_whitespace = true

            [*.{yml,yaml}]
            indent_size = 2

            [*.{json,js,ts,jsx,tsx}]
            indent_size = 2

            [*.md]
            trim_trailing_whitespace = false

            [Makefile]
            indent_style = tab
        """)

        (self.path / '.editorconfig').write_text(content, encoding="utf-8")

    def _create_requirements(self) -> None:
        """Create requirements.txt with pinned Aquilia dependency."""
        content = textwrap.dedent("""\
            # ── Core ──────────────────────────────────────────────────────────
            aquilia>=1.0.0

            # ── Database drivers (uncomment as needed) ────────────────────────
            # SQLite is built-in via aquilia.sqlite (no extra dependency needed)
            # asyncpg>=0.29.0           # PostgreSQL
            # aiomysql>=0.2.0           # MySQL / MariaDB

            # ── Cache backends (uncomment as needed) ──────────────────────────
            # redis>=5.0.0              # Redis cache / sessions

            # ── Production server ─────────────────────────────────────────────
            # gunicorn>=22.0.0          # WSGI/ASGI process manager
            # uvicorn[standard]>=0.30.0 # ASGI server (included with Aquilia)
        """)

        (self.path / 'requirements.txt').write_text(content, encoding="utf-8")

    def _create_tests_dir(self) -> None:
        """Create tests/ directory with conftest.py and example tests using aquilia.testing."""
        tests_dir = self.path / 'tests'
        tests_dir.mkdir(exist_ok=True)

        # __init__.py
        (tests_dir / '__init__.py').write_text("", encoding="utf-8")

        # conftest.py -- registers Aquilia fixtures + any workspace-level overrides
        conftest = textwrap.dedent(f'''\
            """
            Shared test configuration for {self.name}.

            Registers all Aquilia testing fixtures (TestServer, TestClient,
            MockFaultEngine, MockEffectRegistry, etc.) and provides
            workspace-level overrides.

            Run tests with:
                aq test
            Or directly:
                pytest tests/ -v
            """

            import pytest

            # Register all built-in Aquilia fixtures:
            #   test_server, test_client, ws_client, fault_engine,
            #   effect_registry, di_container, identity_factory,
            #   mail_outbox, test_request, test_scope, settings_override
            from aquilia.testing.fixtures import aquilia_fixtures
            aquilia_fixtures()


            # ── Workspace-level overrides ─────────────────────────────────────

            @pytest.fixture
            def app_settings():
                """
                Base settings applied to every test server in this workspace.
                Override per-test via the ``settings_override`` fixture or
                by setting ``settings = {{...}}`` on an :class:`AquiliaTestCase`.
                """
                return {{
                    "debug": True,
                    "runtime": {{"mode": "test"}},
                }}
        ''')

        (tests_dir / 'conftest.py').write_text(conftest, encoding="utf-8")

        # Smoke tests -- SimpleTestCase (no server) + AquiliaTestCase (full stack)
        test_smoke = textwrap.dedent(f'''\
            """
            Smoke tests for {self.name} workspace.

            Demonstrates both testing styles available in aquilia.testing:
            - SimpleTestCase  -- pure unit tests, no server overhead
            - AquiliaTestCase -- full async test case with live TestServer
            - pytest fixtures -- functional style via aquilia_fixtures()
            """

            import aquilia
            from aquilia.testing import (
                AquiliaTestCase,
                SimpleTestCase,
                TestClient,
            )


            # ── Unit-style tests (no server) ──────────────────────────────────

            class TestWorkspace(SimpleTestCase):
                """Verify the workspace boots without errors."""

                def test_aquilia_importable(self):
                    """Aquilia framework must be importable."""
                    self.assertIsNotNone(aquilia.__version__)

                def test_aquilia_version_is_string(self):
                    self.assertIsInstance(aquilia.__version__, str)


            # ── Integration-style tests (full server lifecycle) ───────────────

            class TestSmoke(AquiliaTestCase):
                """
                End-to-end smoke tests against a live TestServer.

                ``self.client`` is a :class:`TestClient` pre-wired to the server.
                Add your manifests via ``manifests = [my_manifest]``.
                """

                settings = {{"debug": True}}

                async def test_health_endpoint(self):
                    """Built-in /health endpoint must return 200."""
                    resp = await self.client.get("/health")
                    self.assert_status(resp, 200)

                async def test_response_is_json(self):
                    """Health response should be valid JSON."""
                    resp = await self.client.get("/health")
                    self.assert_json(resp)


            # ── Pytest-fixture style tests ────────────────────────────────────

            async def test_health_with_fixture(test_client):
                """
                Same smoke test using the ``test_client`` pytest fixture.

                Registered automatically by ``aquilia_fixtures()`` in conftest.py.
                """
                resp = await test_client.get("/health")
                assert resp.status_code == 200


            async def test_fault_engine_captures(test_server, fault_engine):
                """MockFaultEngine records faults for assertion in tests."""
                fault_engine.raise_on_next("not_found", message="Resource missing")
                assert fault_engine.has_pending()


            async def test_settings_override(test_client, settings_override):
                """settings_override context manager lets you flip config mid-test."""
                with settings_override(debug=False):
                    resp = await test_client.get("/health")
                    assert resp.status_code == 200
        ''')

        (tests_dir / 'test_smoke.py').write_text(test_smoke, encoding="utf-8")

    def _create_makefile(self) -> None:
        """Create Makefile with common development commands."""
        content = textwrap.dedent(f"""\
            .PHONY: run dev test lint format migrate clean help

            # ── Variables ─────────────────────────────────────────────────────
            PYTHON ?= python
            APP    ?= {self.name}

            # ── Development ───────────────────────────────────────────────────

            help: ## Show this help message
            \t@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \\
            \t\tawk 'BEGIN {{FS = ":.*?## "}}; {{printf "\\033[36m%-20s\\033[0m %s\\n", $$1, $$2}}'

            run: ## Start development server with hot-reload
            \taq run

            dev: ## Start development server (alias for run)
            \taq run --mode=dev

            prod: ## Start production server
            \taq run --mode=prod

            # ── Testing ───────────────────────────────────────────────────────

            test: ## Run all tests
            \taq test

            test-cov: ## Run tests with coverage
            \taq test --coverage

            # ── Database ──────────────────────────────────────────────────────

            migrate: ## Apply database migrations
            \taq db migrate

            makemigrations: ## Generate new migration
            \taq db makemigrations

            # ── Code Quality ──────────────────────────────────────────────────

            lint: ## Run linter
            \t$(PYTHON) -m ruff check .

            format: ## Auto-format code
            \t$(PYTHON) -m ruff format .

            # ── Build & Deploy ────────────────────────────────────────────────

            compile: ## Compile workspace artifacts
            \taq compile

            freeze: ## Freeze artifacts for deployment
            \taq freeze

            docker-build: ## Build Docker image
            \tdocker build -t $(APP) .

            docker-run: ## Run in Docker container
            \tdocker compose up

            # ── Housekeeping ──────────────────────────────────────────────────

            clean: ## Remove build artifacts and caches
            \tfind . -type d -name __pycache__ -exec rm -rf {{}} + 2>/dev/null || true
            \tfind . -type d -name .pytest_cache -exec rm -rf {{}} + 2>/dev/null || true
            \trm -rf artifacts/ .ruff_cache/ .mypy_cache/ htmlcov/ .coverage
            \t@echo "Cleaned."

            doctor: ## Diagnose workspace issues
            \taq doctor
        """)

        (self.path / 'Makefile').write_text(content, encoding="utf-8")

    def _create_template_files(self) -> None:
        """Create template scaffold files for --template flag.

        Generates:
        - templates/includes/base.html   (Jinja2 base layout)
        - templates/index.html           (extends base)
        - assets/css/style.css           (basic styles)
        - assets/js/app.js               (basic JS)
        """
        # --- base.html (Jinja2 include layout) ---
        base_html = textwrap.dedent(f'''\
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8" />
                <meta name="viewport" content="width=device-width, initial-scale=1.0" />
                <title>{{% block title %}}{self.name.capitalize()}{{% endblock %}}</title>
                <link rel="stylesheet" href="/static/css/style.css" />
                {{% block head %}}{{% endblock %}}
            </head>
            <body>
                <header>
                    {{% block header %}}
                    <nav>
                        <a href="/">{self.name.capitalize()}</a>
                    </nav>
                    {{% endblock %}}
                </header>

                <main>
                    {{% block content %}}{{% endblock %}}
                </main>

                <footer>
                    {{% block footer %}}
                    <p>&copy; {{{{ year }}}} {self.name.capitalize()}. Powered by Aquilia.</p>
                    {{% endblock %}}
                </footer>

                <script src="/static/js/app.js"></script>
                {{% block scripts %}}{{% endblock %}}
            </body>
            </html>
        ''').strip()

        # --- index.html (extends base) ---
        index_html = textwrap.dedent(f'''\
            {{% extends "includes/base.html" %}}

            {{% block title %}}Home -- {self.name.capitalize()}{{% endblock %}}

            {{% block content %}}
            <section class="hero">
                <h1>Welcome to {self.name.capitalize()}</h1>
                <p>Your Aquilia workspace is ready.</p>
            </section>
            {{% endblock %}}
        ''').strip()

        # --- style.css ---
        style_css = textwrap.dedent('''\
            /* Aquilia workspace styles */
            *, *::before, *::after {
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }

            :root {
                --color-bg: #ffffff;
                --color-text: #1a1a2e;
                --color-primary: #00ed64;
                --color-accent: #001e2b;
                --font-sans: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
            }

            body {
                font-family: var(--font-sans);
                color: var(--color-text);
                background: var(--color-bg);
                line-height: 1.6;
            }

            header nav {
                padding: 1rem 2rem;
                background: var(--color-accent);
            }

            header nav a {
                color: var(--color-primary);
                text-decoration: none;
                font-weight: 700;
                font-size: 1.25rem;
            }

            main {
                max-width: 960px;
                margin: 2rem auto;
                padding: 0 1rem;
            }

            .hero {
                text-align: center;
                padding: 4rem 1rem;
            }

            .hero h1 {
                font-size: 2.5rem;
                margin-bottom: 0.5rem;
            }

            footer {
                text-align: center;
                padding: 2rem 1rem;
                color: #888;
                font-size: 0.875rem;
            }
        ''').strip()

        # --- app.js ---
        app_js = textwrap.dedent('''\
            /**
             * Aquilia workspace JavaScript.
             *
             * This file is loaded on every page via the base template.
             * Add your client-side logic here.
             */

            document.addEventListener("DOMContentLoaded", () => {
                console.log("Aquilia workspace ready.");
            });
        ''').strip()

        templates_dir = self.path / 'templates'
        includes_dir = templates_dir / 'includes'
        css_dir = self.path / 'assets' / 'css'
        js_dir = self.path / 'assets' / 'js'

        templates_dir.mkdir(exist_ok=True)
        includes_dir.mkdir(exist_ok=True)
        css_dir.mkdir(parents=True, exist_ok=True)
        js_dir.mkdir(parents=True, exist_ok=True)

        (includes_dir / 'base.html').write_text(base_html, encoding="utf-8")
        (templates_dir / 'index.html').write_text(index_html, encoding="utf-8")
        (css_dir / 'style.css').write_text(style_css, encoding="utf-8")
        (js_dir / 'app.js').write_text(app_js, encoding="utf-8")

    def _create_gitignore(self) -> None:
        """Create .gitignore file."""
        content = textwrap.dedent("""
            # Python
            __pycache__/
            *.py[cod]
            *$py.class
            *.so
            .Python
            env/
            venv/
            .venv/
            ENV/
            dist/
            *.egg-info/
            *.egg

            # Aquilia
            artifacts/
            *.crous

            # Environment & secrets
            .env
            .env.*
            !.env.example

            # Testing & coverage
            .pytest_cache/
            htmlcov/
            .coverage
            .coverage.*
            coverage.xml

            # Linting & type-checking
            .ruff_cache/
            .mypy_cache/

            # IDE
            .vscode/
            .idea/
            *.swp
            *.swo

            # OS
            .DS_Store
            Thumbs.db

            # Logs
            *.log
        """).strip()

        (self.path / '.gitignore').write_text(content, encoding="utf-8")
    
    def _create_readme(self) -> None:
        """Create README.md file."""
        content = textwrap.dedent(f"""
            # {self.name}

            Aquilia workspace generated with `aq init workspace {self.name}`.

            ## Project Structure

            ```
            {self.name}/
            ├── workspace.py          # Workspace config (structure + env config)
            ├── starter.py            # Welcome-page controller
            ├── requirements.txt      # Python dependencies
            ├── .env.example          # Environment variable template
            ├── .editorconfig         # Editor style consistency
            ├── .gitignore
            ├── Makefile              # Common dev commands
            ├── Dockerfile
            ├── .dockerignore
            ├── docker-compose.yml
            ├── models/
            │   └── example.py        # Example model
            ├── modules/              # Application modules
            └── tests/
                ├── conftest.py       # Shared fixtures
                └── test_smoke.py     # Smoke tests
            ```

            ## Getting Started

            ```bash
            # 1. Set up environment
            cp .env.example .env      # Copy & fill in your values
            pip install -r requirements.txt

            # 2. Add a module
            aq add module users

            # 3. Start dev server
            make run                  # or: aq run
            ```

            ## Configuration

            Aquilia uses a **single-file** configuration model:

            | File              | Purpose                              | Committed? |
            |-------------------|--------------------------------------|------------|
            | `workspace.py`    | Structure + env config (AquilaConfig)| Yes     |
            | `.env`            | Secrets, database URLs               | No      |

            Config merge order: `BaseEnv` → `<AQ_ENV>Env` → environment variables.

            ## Useful Commands

            ```bash
            make help             # Show all available make targets
            make run              # Start dev server
            make test             # Run tests
            make lint             # Lint with ruff
            make format           # Auto-format with ruff
            make docker-build     # Build Docker image
            ```

            | CLI Command            | Description                          |
            |------------------------|--------------------------------------|
            | `aq add module <name>` | Scaffold a new module                |
            | `aq run`               | Start development server             |
            | `aq run --mode=prod`   | Start production server              |
            | `aq compile`           | Compile workspace artifacts          |
            | `aq freeze`            | Freeze artifacts for deployment      |
            | `aq validate`          | Validate workspace configuration     |
            | `aq doctor`            | Diagnose workspace issues            |
            | `aq inspect routes`    | Show compiled route table            |

            ## Documentation

            See Aquilia documentation for complete guides.
        """).strip()

        (self.path / 'README.md').write_text(content, encoding="utf-8")

    def _create_license_file(self) -> None:
        """Create a LICENSE file based on the selected license type."""
        import datetime
        year = datetime.datetime.now().year

        if self.include_license == 'MIT':
            content = textwrap.dedent(f"""\
                MIT License

                Copyright (c) {year} {self.name}

                Permission is hereby granted, free of charge, to any person obtaining a copy
                of this software and associated documentation files (the "Software"), to deal
                in the Software without restriction, including without limitation the rights
                to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
                copies of the Software, and to permit persons to whom the Software is
                furnished to do so, subject to the following conditions:

                The above copyright notice and this permission notice shall be included in all
                copies or substantial portions of the Software.

                THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
                IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
                FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
                AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
                LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
                OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
                SOFTWARE.
            """)
        elif self.include_license == 'Apache-2.0':
            content = textwrap.dedent(f"""\
                Copyright {year} {self.name}

                Licensed under the Apache License, Version 2.0 (the "License");
                you may not use this file except in compliance with the License.
                You may obtain a copy of the License at

                    http://www.apache.org/licenses/LICENSE-2.0

                Unless required by applicable law or agreed to in writing, software
                distributed under the License is distributed on an "AS IS" BASIS,
                WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
                See the License for the specific language governing permissions and
                limitations under the License.
            """)
        elif self.include_license == 'BSD-3':
            content = textwrap.dedent(f"""\
                BSD 3-Clause License

                Copyright (c) {year}, {self.name}
                All rights reserved.

                Redistribution and use in source and binary forms, with or without
                modification, are permitted provided that the following conditions are met:

                1. Redistributions of source code must retain the above copyright notice, this
                   list of conditions and the following disclaimer.

                2. Redistributions in binary form must reproduce the above copyright notice,
                   this list of conditions and the following disclaimer in the documentation
                   and/or other materials provided with the distribution.

                3. Neither the name of the copyright holder nor the names of its
                   contributors may be used to endorse or promote products derived from
                   this software without specific prior written permission.

                THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
                AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
                IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
                DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
                FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
                DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
                SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
                CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
                OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
                OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
            """)
        else:
            return  # Unknown license -- skip

        (self.path / 'LICENSE').write_text(content, encoding="utf-8")

    def _create_deployment_files(self) -> None:
        """Create default Docker and docker-compose files for the workspace.

        These are generated as part of ``aq init workspace`` so that new
        workspaces are immediately deployable.
        """
        from .deployment import (
            WorkspaceIntrospector,
            DockerfileGenerator,
            ComposeGenerator,
        )

        try:
            wctx = WorkspaceIntrospector(self.path).introspect()
            docker_gen = DockerfileGenerator(wctx)
            compose_gen = ComposeGenerator(wctx)

            (self.path / 'Dockerfile').write_text(docker_gen.generate_dockerfile(), encoding="utf-8")
            (self.path / '.dockerignore').write_text(docker_gen.generate_dockerignore(), encoding="utf-8")
            (self.path / 'docker-compose.yml').write_text(
                compose_gen.generate_compose(include_monitoring=False)
            , encoding="utf-8")
        except Exception:
            # Non-fatal -- the workspace is still usable without these files
            pass

    def _create_locale_files(self) -> None:
        """Create starter i18n locale files for the workspace.

        Generates ``locales/en/messages.json`` with a minimal set of
        example translations so new workspaces are i18n-ready from
        day one.
        """
        import json

        locales_dir = self.path / 'locales' / 'en'
        locales_dir.mkdir(parents=True, exist_ok=True)

        messages_file = locales_dir / 'messages.json'
        if messages_file.exists():
            return

        starter = {
            "welcome": "Welcome to {app_name}!",
            "goodbye": "Goodbye!",
            "greeting": "Hello, {name}!",
            "items_count": {
                "one": "{count} item",
                "other": "{count} items",
            },
            "errors": {
                "not_found": "Page not found",
                "server_error": "Internal server error",
                "unauthorized": "Please sign in to continue",
                "forbidden": "You don't have permission to access this",
            },
        }

        messages_file.write_text(
            json.dumps(starter, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
