import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Box, Layers, Zap, ShieldCheck, GitBranch, ArrowRight, Cpu, Sparkles } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function DIOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Cpu className="w-4 h-4 animate-pulse" />
          Core Subsystems / Dependency Injection
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Dependency Injection Overview
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Aquilia's DI subsystem acts as the central nervous system of your web application. It integrates manifests, hierarchical scopes, request lifecycles, and controller resolution into a single O(1) lookup path completing in under 3&micro;s.
        </p>
      </div>

      {/* Architecture Section */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          System Architecture
        </h2>
        <div className="flex items-center justify-center py-6">
          <img src="/architecture/di.svg" alt="Dependency Injection Architecture" className="max-w-full h-auto max-h-[360px]" />
        </div>
      </section>

      {/* Premium Concept Grid (No boxes, elegant glass containers with left borders) */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Sparkles className="w-5 h-5 text-aquilia-500" />
          Core Pillars
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[
            { icon: <Layers className="w-5 h-5" />, title: 'Manifest-Driven Registration', desc: 'Services are declared in app manifests. The Registry loads all manifests, builds the dependency graph, runs Tarjan\'s cycle detection, validates cross-app boundaries, then builds the Container.' },
            { icon: <Zap className="w-5 h-5" />, title: 'Async-First Resolution', desc: 'resolve_async() is the primary hot path. Token-to-key conversion is inlined and cached in _type_key_cache. Cached lookups complete in under 3µs. Singleton/app scopes delegate to the parent container.' },
            { icon: <ShieldCheck className="w-5 h-5" />, title: 'Scope Hierarchy Validation', desc: 'Six scope levels form a hierarchy: singleton > app > request > transient > pooled > ephemeral. The ScopeValidator prevents shorter-lived providers from being injected into longer-lived consumers.' },
            { icon: <GitBranch className="w-5 h-5" />, title: 'Per-Request DAG', desc: 'Dependencies declared natively in route handlers via Dep() form a per-request Directed Acyclic Graph. Shared sub-dependencies are deduplicated and resolved exactly once per request. Independent branches resolve concurrently.' },
            { icon: <Box className="w-5 h-5" />, title: 'Annotation-Driven Inject', desc: 'Inspired by FastAPI, use generic typing like Annotated[DB, Dep(get_db)] to seamlessly wire sub-dependencies inline, avoiding the need for boilerplate provider factory registration.' },
            { icon: <GitBranch className="w-5 h-5" />, title: 'Hierarchical Containers', desc: 'create_request_scope() creates a lightweight child container that shares the parent\'s _providers dict by reference but has its own _cache and a _NullLifecycle. Singleton lookups bubble up to the parent automatically.' },
            { icon: <ShieldCheck className="w-5 h-5" />, title: 'Typed Settings', desc: 'One immutable DISettings object holds every runtime knob — scope enforcement, parallel resolution, diagnostics, pool bounds — configured declaratively via the di section of workspace.py. Invalid values raise DIConfigFault at boot.' },
            { icon: <Box className="w-5 h-5" />, title: 'Interceptors & Plugins', desc: 'Provider interceptors wrap instantiation with around-advice (AOP) via intercept(). DIPlugin hooks extend registry construction to auto-register providers and observe container builds — both failure-isolated.' },
            { icon: <Zap className="w-5 h-5" />, title: 'Conditional Providers', desc: 'Gate registration on the environment or config with @service(when=...) or @conditional(...). The Spring @Profile / @ConditionalOnProperty equivalent — a bad predicate skips the service, never crashing boot.' },
          ].map((card, i) => (
            <div key={i} className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 hover:border-aquilia-500/20 p-6 backdrop-blur-sm transition-all duration-300 hover:translate-y-[-2px] hover:shadow-lg shadow-black/40">
              <div className="absolute top-0 bottom-0 left-0 w-1 bg-gradient-to-b from-aquilia-500 to-transparent opacity-50 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="flex items-center gap-3 mb-3">
                <div className="text-aquilia-500">{card.icon}</div>
                <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{card.title}</h3>
              </div>
              <p className={`text-sm leading-relaxed ${subtleText}`}>{card.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Module Map */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Module Map</h2>
        <p className={`mb-4 ${subtleText}`}>
          The DI system lives under <code className="text-aquilia-500">aquilia/di/</code> and is composed of these modules:
        </p>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Module</th>
                <th className="py-4 px-6 text-left font-semibold">Contents</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['__init__.py', 'Public API surface — re-exports everything consumers need.'],
                ['core.py', 'ProviderMeta, ResolveCtx, Provider protocol, Container, Registry, _NullLifecycleType.'],
                ['providers.py', 'ClassProvider, FactoryProvider, ValueProvider, PoolProvider, AliasProvider, LazyProxyProvider, ScopedProvider, ContractProvider.'],
                ['scopes.py', 'ServiceScopeLiteral (canonical string-literal type), deprecated ServiceScope enum, Scope dataclass, SCOPES dict, ScopeValidator.'],
                ['decorators.py', 'Inject, inject(), service(), factory(), provides(), auto_inject(), conditional(), ConditionContext, should_register().'],
                ['dep.py', 'Dep descriptor for inline parameter injection. HTTP extractors: Header, Query, Body, Cookie, Path.'],
                ['request_dag.py', 'Thin compatibility shim over container.resolve_dep() — the unified per-request resolution engine now lives in core.py.'],
                ['settings.py', 'DISettings (typed runtime config), DIConfigFault, configure_di(), get_di_settings(), reset_di_settings().'],
                ['interceptors.py', 'ProviderInterceptor protocol, InterceptingProvider, InterceptContext, intercept() — provider-level AOP.'],
                ['plugins.py', 'DIPlugin base, register_plugin(), unregister_plugin(), get_plugins(), clear_plugins().'],
                ['lifecycle.py', 'DisposalStrategy, LifecycleHook, Lifecycle, LifecycleContext.'],
                ['diagnostics.py', 'DIEventType, DIEvent, DiagnosticListener protocol, ConsoleDiagnosticListener, DIDiagnostics.'],
                ['graph.py', 'DependencyGraph — Tarjan\'s SCC detection, Kahn\'s topological sort, DOT export, tree view.'],
                ['errors.py', (
                  <span>
                    <DocTerm id="di.provider_not_found_error" className="!text-xs">DIError</DocTerm> subclasses: {['ProviderNotFoundError', 'DependencyCycleError', 'ScopeViolationError', 'AmbiguousProviderError', 'ManifestValidationError', 'CrossAppDependencyError', 'CircularDependencyError', 'MissingDependencyError'].map((err, idx) => (
                      <span key={err}>
                        <DocTerm id={`di.${err.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`).replace(/^_/, '')}`} className="!text-xs">
                          {err}
                        </DocTerm>
                        {idx < 7 ? ', ' : '.'}
                      </span>
                    ))}
                  </span>
                )],
                ['testing.py', 'MockProvider, TestRegistry, override_container(), pytest fixtures (di_container, request_container, mock_provider).'],
                ['compat.py', 'RequestCtx legacy wrapper, get_request_container(), set_request_container(), reset_request_container(), request_container_scope() — ContextVar bridge.'],
                ['cli.py', (
                  <span>
                    CLI commands:{' '}
                    {['aq di-check', 'aq di-tree', 'aq di-graph', 'aq di-profile', 'aq di-manifest'].map((cmd, idx) => (
                      <span key={cmd}>
                        <DocTerm id={`di.cli.${cmd.split(' ')[1].replace(/-/g, '_')}`} className="!text-xs">
                          {cmd}
                        </DocTerm>
                        {idx < 4 ? ', ' : '.'}
                      </span>
                    ))}
                  </span>
                )],
              ].map(([mod, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-aquilia-500 text-xs">{mod}</td>
                  <td className={`py-3.5 px-6 ${subtleText}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Registration Flow */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Registration Flow</h2>
        <p className={`mb-6 ${subtleText}`}>
          The <code className="text-aquilia-500">Registry.from_manifests()</code> pipeline processes manifests through four sequential phases before building the container:
        </p>
        <div className="space-y-4 mb-8">
          {[
            { phase: 'Phase 1', title: 'Load Manifest Services', desc: 'Iterate each manifest\'s services list. Create Provider instances (ClassProvider for classes, FactoryProvider for factories). Attach ProviderMeta with scope, tags, module, line number.' },
            { phase: 'Phase 2', title: 'Build Dependency Graph', desc: 'For each provider, extract constructor dependencies via inspect.signature(). Add nodes and edges to DependencyGraph.adj_list. Supports Annotated[Type, Inject(tag="...")] for tagged lookups.' },
            { phase: 'Phase 3', title: 'Detect Cycles (Tarjan\'s)', desc: <span>Run Tarjan\'s strongly-connected-component algorithm. Filter out trivial SCCs (single node, no self-loop). Raise <DocTerm id="di.dependency_cycle_error" className="!text-xs">DependencyCycleError</DocTerm> with cycle trace and locations. Suggest allow_lazy=True or interface extraction.</span> },
            { phase: 'Phase 4', title: 'Validate Cross-App Dependencies', desc: <span>When enforce_cross_app=True, verify that every inter-app dependency is declared in the consumer manifest\'s depends_on list. Raise <DocTerm id="di.cross_app_dependency_error" className="!text-xs">CrossAppDependencyError</DocTerm> with fix suggestion if violated.</span> },
          ].map((p, i) => (
            <div key={i} className="flex gap-4 relative pl-8 before:absolute before:left-3 before:top-8 before:bottom-0 before:w-0.5 before:bg-white/5 last:before:hidden">
              <div className="absolute left-0 flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-full bg-aquilia-500/20 text-aquilia-500 text-xs font-bold ring-4 ring-aquilia-500/10">
                {i + 1}
              </div>
              <div className="pb-4">
                <h4 className={`font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{p.title}</h4>
                <p className={`text-sm ${subtleText}`}>{p.desc}</p>
              </div>
            </div>
          ))}
        </div>

        <CodeBlock language="python" filename="Registry Pipeline">{`from aquilia.di import Registry

# Typically called by the engine during startup:
registry = Registry.from_manifests(
    manifests=[users_manifest, orders_manifest, payments_manifest],
    config=app_config,
    enforce_cross_app=True,  # Strict in production
)

# Build the root container
container = registry.build_container()
await container.startup()  # Run lifecycle hooks`}</CodeBlock>
      </section>

      {/* Resolution Hot Path */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Resolution Hot Path</h2>
        <p className={`mb-4 ${subtleText}`}>
          <code className="text-aquilia-500">resolve_async()</code> is the primary resolution method called on every request. It is optimized for &lt;3&micro;s cached lookups with an inlined token-to-key conversion path:
        </p>
        <CodeBlock language="python" filename="Hot Path Internals">{`# Simplified view of resolve_async internals:
async def resolve_async(self, token, *, tag=None, optional=False):
    # 1. Inline token_to_key (avoid function-call overhead)
    #    Uses _type_key_cache (dict) for O(1) type → string lookup
    key = self._type_key_cache.get(token) or self._token_to_key(token)
    
    # 2. Check cache first — O(1) dict lookup
    cache_key = f"{key}:{tag}" if tag else key
    cached = self._cache.get(cache_key)
    if cached is not _SENTINEL:
        return cached  # <3µs return path
    
    # 3. Scope delegation: singleton/app → parent container
    if provider.meta.scope in ("singleton", "app") and self._parent:
        return await self._parent.resolve_async(token, tag=tag)
    
    # 4. Instantiate via provider
    ctx = ResolveCtx(container=self, stack=[], cache={})
    instance = await provider.instantiate(ctx)
    
    # 5. Cache if scope is cacheable
    if self._should_cache(provider.meta.scope):
        self._cache[cache_key] = instance
        self._register_finalizer(instance)
    
    return instance`}</CodeBlock>
      </section>

      {/* Quick Start with Constructor Injection */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Usage inside Web Framework</h2>
        <p className={`mb-6 ${subtleText}`}>
          Aquilia promotes clean separation of concerns. Do not manually pull dependencies from the request container. Instead, use <strong>Constructor Injection</strong> to automatically wire services, repositories, and models.
        </p>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Define and Annotate Services</h3>
        <CodeBlock language="python" filename="services.py">{`from aquilia.di import service, Inject
from typing import Annotated

@service(scope="app")
class UserRepository:
    def __init__(self, db: DatabasePool):
        self.db = db
    
    async def find(self, user_id: str):
        return await self.db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)

@service(scope="request")
class UserService:
    def __init__(
        self,
        repo: UserRepository,
        cache: Annotated[CacheBackend, Inject(tag="redis")],
    ):
        self.repo = repo
        self.cache = cache
        
    async def get_user(self, user_id: str):
        # Auto-delegates DB querying to repo
        return await self.repo.find(user_id)`}</CodeBlock>

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Constructor Injection in Web Controllers</h3>
        <p className={`mb-4 text-sm ${subtleText}`}>
          The ControllerFactory uses parameter type hints to resolve and inject services directly into the constructor.
        </p>
        <CodeBlock language="python" filename="controller.py">{`from aquilia import Controller, get
from myapp.services import UserService

class UserController(Controller):
    prefix = "/users"
    
    # RECOMMENDED: Constructor Injection
    # Resolved and instantiated by ControllerFactory on each request:
    def __init__(self, user_service: UserService):
        self.user_service = user_service
        
    @get("/{user_id}")
    async def get_user(self, ctx):
        # Use constructor injected service directly
        user = await self.user_service.get_user(ctx.request.params["user_id"])
        return ctx.json(user)`}</CodeBlock>

        <div className="border-l-4 border-amber-500 bg-amber-500/5 pl-4 py-3 rounded-r-xl my-6">
          <h4 className="font-semibold text-sm text-amber-500 mb-1">Anti-Pattern Warning</h4>
          <p className="text-xs text-amber-500/90 leading-relaxed">
            Do NOT resolve dependencies dynamically inside routes via <code className="text-xs">await ctx.container.resolve_async(UserService)</code>. This hides dependencies, makes unit testing complex, and prevents compile-time dependency cycle and scope validation checks. Always prefer Constructor Injection.
          </p>
        </div>
      </section>

      {/* Provider Types Summary */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Provider Types at a Glance</h2>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Provider</th>
                <th className="py-4 px-6 text-left font-semibold">Use Case</th>
                <th className="py-4 px-6 text-left font-semibold">Async Init</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['ClassProvider', 'Default — instantiates class, auto-resolves __init__ dependencies via inspect.signature + type hints', 'Yes (async_init())'],
                ['FactoryProvider', 'Custom creation logic — calls sync/async factory function, auto-resolves factory parameters', 'Yes'],
                ['ValueProvider', 'Pre-built constants — returns the exact same instance every time', 'No'],
                ['PoolProvider', 'Object pools — asyncio.Queue-based, FIFO/LIFO ordering, max_size limit, release() back to pool', 'Yes'],
                ['AliasProvider', 'Token aliasing — delegates resolution to another token', 'Delegated'],
                ['LazyProxyProvider', 'Cycle breaking — creates a dynamic proxy class that defers __getattr__ and __call__ to the real instance', 'Lazy'],
                ['ScopedProvider', 'Scope override — wraps any inner provider with a different scope', 'Delegated'],
                ['ContractProvider', 'Request-body contracts — automatically binds contract facets to the incoming request payload with validation and mold casting', 'Yes'],
              ].map(([name, desc, async_], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6">
                    <DocTerm id={`di.${name.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`).replace(/^_/, '')}`}>
                      {name}
                    </DocTerm>
                  </td>
                  <td className={`py-3.5 px-6 ${subtleText}`}>{desc}</td>
                  <td className={`py-3.5 px-6 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{async_}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Error Types */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Error Taxonomy</h2>
        <p className={`mb-4 ${subtleText}`}>
          All DI errors inherit from <code className="text-aquilia-500">DIError</code> and include rich diagnostic messages with file locations, candidate lists, and suggested fixes:
        </p>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Error</th>
                <th className="py-4 px-6 text-left font-semibold">Trigger</th>
                <th className="py-4 px-6 text-left font-semibold">Suggested Fix</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['ProviderNotFoundError', 'resolve() called for unregistered token', 'Register provider or add Inject(tag=...) to disambiguate'],
                ['DependencyCycleError', 'Tarjan\'s detects a cycle during registry build', 'Use allow_lazy=True, extract interface, or restructure'],
                ['ScopeViolationError', 'Request-scoped injected into singleton', 'Align scopes or use factory pattern to defer instantiation'],
                ['AmbiguousProviderError', 'Multiple providers match token without tag', 'Add Inject(tag=...) or remove duplicate registration'],
                ['ManifestValidationError', 'Manifest fails structural validation', 'Fix manifest\'s services list or configuration'],
                ['CrossAppDependencyError', 'Inter-app dependency not in depends_on', 'Add provider app to consumer\'s depends_on list'],
                ['CircularDependencyError', 'Circular dependency in service graph', 'Use lazy injection, extract interface, or use events'],
                ['MissingDependencyError', 'Required dependency not in container', 'Register dependency or make it Optional[T]'],
              ].map(([name, trigger, fix], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6">
                    <DocTerm id={`di.${name.replace(/[A-Z]/g, letter => `_${letter.toLowerCase()}`).replace(/^_/, '')}`} className="!text-red-400 hover:!text-red-300 !border-red-400/30 hover:!border-red-300/60 font-mono text-xs">
                      {name}
                    </DocTerm>
                  </td>
                  <td className={`py-3.5 px-6 ${subtleText}`}>{trigger}</td>
                  <td className={`py-3.5 px-6 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{fix}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="border-l-4 border-aquilia-500 bg-aquilia-500/5 pl-4 py-3 rounded-r-xl mt-6">
          <p className="text-xs text-aquilia-500/90 leading-relaxed">
            <strong>Structured faults at boot.</strong> The DI layer now raises structured <code className="text-xs">DIFault</code>s rather than bare <code className="text-xs">ValueError</code>s. A manifest declaring an unknown <code className="text-xs">scope</code> fails fast with <code className="text-xs">INVALID_SERVICE_SCOPE</code> (always fatal, lists the valid scopes). When <code className="text-xs">strict_service_registration</code> is on, a service that fails to register raises <code className="text-xs">SERVICE_REGISTRATION_FAILED</code> and aborts boot; otherwise it logs a warning and continues. Invalid <code className="text-xs">di</code> config raises <code className="text-xs">DI_CONFIG_INVALID</code>.
          </p>
        </div>
      </section>

      {/* CLI Tooling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>CLI Tooling</h2>
        <p className={`mb-4 ${subtleText}`}>
          The DI system provides five CLI commands for validation, visualization, and profiling:
        </p>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Command</th>
                <th className="py-4 px-6 text-left font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['aq di-check --settings settings.py', 'Static validation — checks resolvability, cycles, scope violations, cross-app deps.'],
                ['aq di-tree --settings settings.py', 'Renders the dependency tree (text format). Supports --root token and --out file.'],
                ['aq di-graph --settings settings.py --out graph.dot', 'Exports the dependency graph as Graphviz DOT. Visualize with: dot -Tpng graph.dot -o graph.png.'],
                ['aq di-profile --settings settings.py --bench resolve', 'Benchmarks cached resolution latency (avg, median, P95). Validates the <3µs target.'],
                ['aq di-manifest --settings settings.py --out di_manifest.json', 'Generates a JSON manifest for LSP integration (hover info, autocomplete, navigation).'],
              ].map(([cmd, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6">
                    <DocTerm id={`di.cli.${cmd.split(' ')[1].replace(/-/g, '_')}`} className={`${isDark ? '!text-green-400 hover:!text-green-300 !border-green-400/30 hover:!border-green-300/60 font-mono text-xs' : '!text-green-700 hover:!text-green-600 !border-green-700/30 hover:!border-green-600/60 font-mono text-xs'}`}>
                      {cmd}
                    </DocTerm>
                  </td>
                  <td className={`py-3.5 px-6 ${subtleText}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Explore the docs */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Explore the DI Docs</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            ['Container', '/docs/di/container', 'Registration, resolution, hierarchical containers, hot-swap.'],
            ['Providers', '/docs/di/providers', 'Class, Factory, Value, Pool, Alias, LazyProxy, Scoped, Contract.'],
            ['Scopes', '/docs/di/scopes', 'Lifetimes, caching, captive-dependency rules, enforcement.'],
            ['Decorators', '/docs/di/decorators', '@service, @factory, @provides, conditional providers, Inject.'],
            ['RequestDAG', '/docs/di/request-dag', 'Inline Dep() injection, dedup, parallel resolution, teardown.'],
            ['HTTP Extractors', '/docs/di/extractors', 'Header, Query, Cookie, Path, Body with auto-coercion.'],
            ['Lifecycle', '/docs/di/lifecycle', 'Startup/shutdown hooks, disposal strategies, finalizers.'],
            ['Advanced', '/docs/di/advanced', 'DISettings, interceptors, plugins, cross-app links, testing.'],
            ['Patterns & Recipes', '/docs/di/patterns', '15 production recipes from basic wiring to large apps.'],
            ['Errors & Troubleshooting', '/docs/di/troubleshooting', 'Full fault taxonomy and a debugging playbook.'],
          ].map(([label, path, desc], i) => (
            <Link key={i} to={path} className="group rounded-2xl bg-white/5 border border-white/5 hover:border-aquilia-500/30 p-5 backdrop-blur-sm transition-all duration-200 hover:translate-y-[-2px]">
              <div className="flex items-center gap-2 mb-1">
                <span className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'} group-hover:text-aquilia-500 transition-colors`}>{label}</span>
                <ArrowRight className="w-3.5 h-3.5 text-aquilia-500 opacity-0 group-hover:opacity-100 transition-opacity" />
              </div>
              <p className={`text-xs ${subtleText}`}>{desc}</p>
            </Link>
          ))}
        </div>
      </section>

      {/* Navigation */}
      <div className={`mt-16 pt-8 border-t flex justify-between ${isDark ? 'border-white/5' : 'border-gray-200'}`}>
        <span />
        <Link to="/docs/di/container" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          Container <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}