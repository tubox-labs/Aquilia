import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Box, Layers, Zap, ShieldCheck, GitBranch, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function DIOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4"><Box className="w-4 h-4" />Dependency Injection</div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Dependency Injection Overview
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia ships with a production-grade dependency injection container — hierarchical scopes, async-first resolution, cycle detection via Tarjan's algorithm, manifest-driven registration, rich diagnostics, and cached lookups under 3&micro;s.
        </p>
      </div>

      {/* Architecture SVG */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>System Architecture</h2>
        <div className="w-full">
          <div className="flex items-center justify-center py-6">
            <img src="/architecture/di.svg" alt="Dependency Injection Architecture" className="max-w-full h-auto max-h-[360px]" />
          </div>
        </div>
      </section>

      {/* Key Concepts */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Key Concepts</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { icon: <Layers className="w-5 h-5" />, title: 'Manifest-Driven Registration', desc: 'Services are declared in app manifests. The Registry loads all manifests, builds the dependency graph, runs Tarjan\'s cycle detection, validates cross-app dependencies, then builds the Container.' },
            { icon: <Zap className="w-5 h-5" />, title: 'Async-First Resolution', desc: 'resolve_async() is the primary hot path. Token-to-key conversion is inlined and cached in _type_key_cache. Cached lookups complete in under 3µs. Singleton/app scopes delegate to the parent container.' },
            { icon: <ShieldCheck className="w-5 h-5" />, title: 'Scope Validation', desc: 'Six scope levels form a hierarchy: singleton > app > request > transient > pooled > ephemeral. The ScopeValidator prevents shorter-lived providers from being injected into longer-lived consumers.' },
            { icon: <GitBranch className="w-5 h-5" />, title: 'Per-Request DAG', desc: 'Dependencies declared natively in route handlers via Dep() form a per-request Directed Acyclic Graph. Shared sub-dependencies are deduplicated and resolved exactly once per request. Independent branches resolve concurrently.' },
            { icon: <Box className="w-5 h-5" />, title: 'Annotation-Driven Inject', desc: 'Inspired by FastAPI, use generic typing like Annotated[DB, Dep(get_db)] to seamlessly wire sub-dependencies inline, avoiding the need for boilerplate provider factory registration.' },
            { icon: <GitBranch className="w-5 h-5" />, title: 'Hierarchical Containers', desc: 'create_request_scope() creates a lightweight child container that shares the parent\'s _providers dict by reference but has its own _cache and a _NullLifecycle. Singleton lookups bubble up to the parent automatically.' },
          ].map((card, i) => (
            <div key={i} className={`p-5 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-white border-gray-200'}`}>
              <div className="flex items-center gap-3 mb-3">
                <div className="text-aquilia-500">{card.icon}</div>
                <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{card.title}</h3>
              </div>
              <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{card.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Module Map */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Module Map</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The DI system lives under <code className="text-aquilia-500">aquilia/di/</code> and is composed of 13 modules:
        </p>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead><tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <th className="text-left py-3 pr-4 text-aquilia-500">Module</th>
              <th className="text-left py-3">Contents</th>
            </tr></thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              {[
                ['__init__.py', 'Public API surface — re-exports everything consumers need.'],
                ['core.py', 'ProviderMeta, ResolveCtx, Provider protocol, Container, Registry, _NullLifecycleType.'],
                ['providers.py', 'ClassProvider, FactoryProvider, ValueProvider, PoolProvider, AliasProvider, LazyProxyProvider, ScopedProvider, SerializerProvider.'],
                ['scopes.py', 'ServiceScope enum (6 scopes), Scope dataclass, SCOPES dict, ScopeValidator.'],
                ['decorators.py', 'Inject, inject(), service(), factory(), provides(), auto_inject(), injectable.'],
                ['dep.py', 'Dep descriptor for inline parameter injection. HTTP extractors: Header, Query, Body.'],
                ['request_dag.py', 'Per-request Dependency Graph execution, deduplication, and caching.'],
                ['lifecycle.py', 'DisposalStrategy, LifecycleHook, Lifecycle, LifecycleContext.'],
                ['diagnostics.py', 'DIEventType, DIEvent, DiagnosticListener protocol, ConsoleDiagnosticListener, DIDiagnostics.'],
                ['graph.py', 'DependencyGraph — Tarjan\'s SCC detection, Kahn\'s topological sort, DOT export, tree view.'],
                ['errors.py', 'DIError, ProviderNotFoundError, DependencyCycleError, ScopeViolationError, AmbiguousProviderError, ManifestValidationError, CrossAppDependencyError, CircularDependencyError, MissingDependencyError.'],
                ['testing.py', 'MockProvider, TestRegistry, override_container(), pytest fixtures (di_container, request_container, mock_provider).'],
                ['compat.py', 'RequestCtx legacy wrapper, get_request_container(), set_request_container(), clear_request_container() — ContextVar bridge.'],
                ['cli.py', 'CLI commands: aq di-check, aq di-tree, aq di-graph, aq di-profile, aq di-manifest.'],
              ].map(([mod, desc], i) => (
                <tr key={i}>
                  <td className="py-3 pr-4"><code className="text-aquilia-500 text-xs">{mod}</code></td>
                  <td className={`py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Registration Flow */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Registration Flow</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">Registry.from_manifests()</code> pipeline processes manifests through four sequential phases before building the container:
        </p>
        <div className="space-y-4">
          {[
            { phase: 'Phase 1', title: 'Load Manifest Services', desc: 'Iterate each manifest\'s services list. Create Provider instances (ClassProvider for classes, FactoryProvider for factories). Attach ProviderMeta with scope, tags, module, line number.' },
            { phase: 'Phase 2', title: 'Build Dependency Graph', desc: 'For each provider, extract constructor dependencies via inspect.signature(). Add nodes and edges to DependencyGraph.adj_list. Supports Annotated[Type, Inject(tag="...")] for tagged lookups.' },
            { phase: 'Phase 3', title: 'Detect Cycles (Tarjan\'s)', desc: 'Run Tarjan\'s strongly-connected-component algorithm. Filter out trivial SCCs (single node, no self-loop). Raise DependencyCycleError with cycle trace and locations. Suggest allow_lazy=True or interface extraction.' },
            { phase: 'Phase 4', title: 'Validate Cross-App Dependencies', desc: 'When enforce_cross_app=True, verify that every inter-app dependency is declared in the consumer manifest\'s depends_on list. Raise CrossAppDependencyError with fix suggestion if violated.' },
          ].map((p, i) => (
            <div key={i} className="flex gap-4">
              <div className="flex-shrink-0">
                <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-aquilia-500/20 text-aquilia-500 text-xs font-bold">{i + 1}</span>
              </div>
              <div>
                <h4 className={`font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{p.title}</h4>
                <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{p.desc}</p>
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
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
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

      {/* Quick Start */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Quick Start</h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Declare Services with Decorators</h3>
        <CodeBlock language="python" filename="services.py">{`from aquilia.di import service, inject, Inject
from typing import Annotated

@service(scope="app")
class UserRepository:
    def __init__(self, db: DatabasePool):
        self.db = db
    
    async def find(self, user_id: int):
        return await self.db.fetch_one("SELECT * FROM users WHERE id = $1", user_id)

@service(scope="request")
class UserService:
    def __init__(
        self,
        repo: UserRepository,
        cache: Annotated[CacheBackend, Inject(tag="redis")],
    ):
        self.repo = repo
        self.cache = cache`}</CodeBlock>

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Register in Manifest</h3>
        <CodeBlock language="python" filename="manifest.py">{`from aquilia import Manifest

users = Manifest(
    name="users",
    services=[UserRepository, UserService, CacheBackend],
    depends_on=["database"],  # Cross-app dependency declaration
)`}</CodeBlock>

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. Resolve in Controllers</h3>
        <CodeBlock language="python" filename="controller.py">{`from aquilia.controller import Controller, get

class UserController(Controller):
    prefix = "/users"
    
    @get("/{user_id}")
    async def get_user(self, req):
        # Container auto-injected into request context
        user_svc = await req.container.resolve_async(UserService)
        return await user_svc.find(req.params["user_id"])`}</CodeBlock>
      </section>

      {/* Provider Types Summary */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Provider Types at a Glance</h2>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead><tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <th className="text-left py-3 pr-4 text-aquilia-500">Provider</th>
              <th className="text-left py-3 pr-4">Use Case</th>
              <th className="text-left py-3">Async Init</th>
            </tr></thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              {[
                ['ClassProvider', 'Default — instantiates class, auto-resolves __init__ dependencies via inspect.signature + type hints', 'Yes (async_init())'],
                ['FactoryProvider', 'Custom creation logic — calls sync/async factory function, auto-resolves factory parameters', 'Yes'],
                ['ValueProvider', 'Pre-built constants — returns the exact same instance every time', 'No'],
                ['PoolProvider', 'Object pools — asyncio.Queue-based, FIFO/LIFO ordering, max_size limit, release() back to pool', 'Yes'],
                ['AliasProvider', 'Token aliasing — delegates resolution to another token', 'Delegated'],
                ['LazyProxyProvider', 'Cycle breaking — creates a dynamic proxy class that defers __getattr__ and __call__ to the real instance', 'Lazy'],
                ['ScopedProvider', 'Scope override — wraps any inner provider with a different scope', 'Delegated'],
                ['SerializerProvider', 'Request-context serializers — auto-parses request body (JSON/form), builds context with request/container/identity', 'Yes'],
              ].map(([name, desc, async_], i) => (
                <tr key={i}>
                  <td className="py-3 pr-4"><code className="text-aquilia-500 text-xs">{name}</code></td>
                  <td className={`py-3 pr-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{desc}</td>
                  <td className={`py-3 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{async_}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Error Types */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Error Taxonomy</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          All DI errors inherit from <code className="text-aquilia-500">DIError</code> and include rich diagnostic messages with file locations, candidate lists, and suggested fixes:
        </p>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead><tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <th className="text-left py-3 pr-4 text-aquilia-500">Error</th>
              <th className="text-left py-3 pr-4">Trigger</th>
              <th className="text-left py-3">Suggested Fix</th>
            </tr></thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
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
                <tr key={i}>
                  <td className="py-3 pr-4"><code className="text-xs text-red-400">{name}</code></td>
                  <td className={`py-3 pr-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{trigger}</td>
                  <td className={`py-3 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{fix}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* CLI Tooling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>CLI Tooling</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The DI system provides five CLI commands for validation, visualization, and profiling:
        </p>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead><tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <th className="text-left py-3 pr-4 text-aquilia-500">Command</th>
              <th className="text-left py-3">Description</th>
            </tr></thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              {[
                ['aq di-check --settings settings.py', 'Static validation — checks resolvability, cycles, scope violations, cross-app deps.'],
                ['aq di-tree --settings settings.py', 'Renders the dependency tree (text format). Supports --root token and --out file.'],
                ['aq di-graph --settings settings.py --out graph.dot', 'Exports the dependency graph as Graphviz DOT. Visualize with: dot -Tpng graph.dot -o graph.png.'],
                ['aq di-profile --settings settings.py --bench resolve', 'Benchmarks cached resolution latency (avg, median, P95). Validates the <3µs target.'],
                ['aq di-manifest --settings settings.py --out di_manifest.json', 'Generates a JSON manifest for LSP integration (hover info, autocomplete, navigation).'],
              ].map(([cmd, desc], i) => (
                <tr key={i}>
                  <td className="py-3 pr-4"><code className={`text-xs ${isDark ? 'text-green-400' : 'text-green-700'}`}>{cmd}</code></td>
                  <td className={`py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Imports Reference */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Import Reference</h2>
        <CodeBlock language="python" filename="aquilia/di/__init__.py">{`# Core
from aquilia.di import Container, Registry, Provider, ProviderMeta, ResolveCtx

# Providers
from aquilia.di import (
    ClassProvider, FactoryProvider, ValueProvider,
    PoolProvider, AliasProvider, LazyProxyProvider,
    ScopedProvider, SerializerProvider,
)

# Inline Injection (Steroids)
from aquilia.di import Dep, RequestDAG, Header, Query, Body

# Scopes
from aquilia.di import ServiceScope, Scope, ScopeValidator

# Decorators
from aquilia.di import service, factory, inject, Inject, provides, auto_inject

# Lifecycle
from aquilia.di import Lifecycle, LifecycleHook, DisposalStrategy, LifecycleContext

# Graph
from aquilia.di import DependencyGraph

# Errors
from aquilia.di.errors import (
    DIError, ProviderNotFoundError, DependencyCycleError,
    ScopeViolationError, AmbiguousProviderError,
    ManifestValidationError, CrossAppDependencyError,
    CircularDependencyError, MissingDependencyError,
)

# Testing
from aquilia.di import TestRegistry, MockProvider
from aquilia.di.testing import override_container

# Legacy compat
from aquilia.di import RequestCtx
from aquilia.di.compat import get_request_container, set_request_container`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`mt-16 pt-8 border-t flex justify-between ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <span />
        <Link to="/docs/di/container" className="flex items-center gap-2 text-aquilia-500 hover:underline font-medium">
          Container <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}