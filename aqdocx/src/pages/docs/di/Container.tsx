import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { ArrowLeft, ArrowRight, Layers } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function DIContainer() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Layers className="w-4 h-4" />
          Dependency Injection / Container
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          DI Container
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          The <code className="text-aquilia-500">Container</code> is the central state engine for resolved services. It manages provider lifecycle transitions, caches instances by scope, and delegates queries up hierarchical container chains.
        </p>
      </div>

      {/* Internal Structure Table */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Internal Structure</h2>
        <p className={`mb-4 ${subtleText}`}>
          The Container uses <code className="text-aquilia-500">__slots__</code> with 8 attributes for direct memory allocation, bypassing class dictionary lookups entirely:
        </p>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Slot</th>
                <th className="py-4 px-6 text-left font-semibold">Type</th>
                <th className="py-4 px-6 text-left font-semibold">Purpose</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['_providers', 'dict[str, Provider]', 'Token → Provider mapping. Shared by reference with child containers.'],
                ['_cache', 'dict[str, Any]', 'Cache key → resolved instance. Each container gets its own cache.'],
                ['_scope', 'str', 'Container scope ("app", "request", etc). Determines cache behavior.'],
                ['_parent', 'Container | None', 'Parent container for scope delegation. Singleton/app lookups bubble up.'],
                ['_finalizers', 'list[Callable]', 'LIFO finalizer stack — shutdown() drains in reverse order.'],
                ['_resolve_plans', 'dict', 'Cached resolution plans for hot-path optimization.'],
                ['_diagnostics', 'DIDiagnostics', 'Event emitter for tracing registrations and resolutions.'],
                ['_lifecycle', 'Lifecycle', 'Manages on_startup/on_shutdown hooks and disposal strategy.'],
              ].map(([slot, type_, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-aquilia-500 text-xs">{slot}</td>
                  <td className="py-3.5 px-6 font-mono text-xs text-yellow-500">{type_}</td>
                  <td className={`py-3.5 px-6 ${subtleText}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Creating Containers */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Creating Containers</h2>
        <CodeBlock language="python" filename="Container Initialization">{`from aquilia.di.core import Container

# Root app container (created by Registry.build_container() internally)
container = Container(scope="app")

# With explicit parent (for manual hierarchies)
request_container = Container(scope="request", parent=container)

# Preferred: use the factory method for request scoping
request_container = container.create_request_scope()
# → Creates child with shared _providers (by reference), fresh _cache,
#   and _NullLifecycle (no-op lifecycle for lightweight request containers)`}</CodeBlock>

        <div className="border-l-4 border-aquilia-500 bg-aquilia-500/5 pl-4 py-3 rounded-r-xl my-6">
          <p className={`text-sm ${isDark ? 'text-aquilia-400' : 'text-aquilia-800'}`}>
            <strong>Note:</strong> In production web workflows, you almost never create containers manually. The <code className="text-green-500 font-semibold">Registry.build_container()</code> method builds the root container, and the ASGI server middleware executes <code className="text-green-500 font-semibold">create_request_scope()</code> on every incoming request automatically.
          </p>
        </div>
      </section>

      {/* API Reference */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>API Reference</h2>

        {/* register */}
        <div className="mb-12 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">register(provider, *, tag=None)</code></h3>
          <p className={`mb-4 text-sm ${subtleText}`}>
            Register a <code className="text-aquilia-500">Provider</code> instance. A genuine local re-registration of the same token+tag raises a <code className="text-aquilia-500">DIFault</code>, but a child container may <strong>shadow</strong> a provider inherited from its parent. Fires the <code className="text-aquilia-500">on_provider_registered</code> plugin hook.
          </p>
          <CodeBlock language="python">{`from aquilia.di import ClassProvider

provider = ClassProvider(UserService, scope="request")
container.register(provider)

# With a tag for disambiguation
container.register(redis_provider, tag="redis")`}</CodeBlock>
        </div>

        {/* bind */}
        <div className="mb-12 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">bind(interface, implementation, *, scope="app", tag=None)</code></h3>
          <p className={`mb-4 text-sm ${subtleText}`}>
            Bind an interface type to a concrete implementation. Creates a <code className="text-aquilia-500">ClassProvider</code> internally.
          </p>
          <CodeBlock language="python">{`from abc import ABC, abstractmethod
from aquilia.controller import Controller, get

class IUserRepo(ABC):
    @abstractmethod
    async def find(self, id: str): ...

class PostgresUserRepo(IUserRepo):
    def __init__(self, pool: DatabasePool):
        self.pool = pool
    
    async def find(self, id: str):
        return await self.pool.fetch_one("SELECT * FROM users WHERE id=$1", id)

# Bind interface → implementation
container.bind(IUserRepo, PostgresUserRepo, scope="app")

# Web Controllers resolve this automatically via constructor injection:
class UserController(Controller):
    prefix = "/users"

    def __init__(self, repo: IUserRepo): # Resolved to PostgresUserRepo
        self.repo = repo

    @get("/{id}")
    async def get_user(self, ctx):
        user = await self.repo.find(ctx.request.params["id"])
        return ctx.json(user)`}</CodeBlock>
        </div>

        {/* resolve_async */}
        <div className="mb-12 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">await resolve_async(token, *, tag=None, optional=False)</code></h3>
          <p className={`mb-4 text-sm ${subtleText}`}>
            <strong>Primary async resolution path.</strong> Optimized for &lt;3&micro;s cached lookups with O(1) cache check and parent container delegation. Pass <code className="text-aquilia-500">optional=True</code> to get <code className="text-aquilia-500">None</code> instead of <code className="text-aquilia-500">ProviderNotFoundError</code> when unregistered.
          </p>
          <CodeBlock language="python">{`# Standard resolution
user_svc = await container.resolve_async(UserService)

# Tagged resolution
redis = await container.resolve_async(CacheBackend, tag="redis")

# Optional — None if not registered
tracer = await container.resolve_async(Tracer, optional=True)`}</CodeBlock>
        </div>

        {/* resolve (sync) */}
        <div className="mb-12 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">resolve(token, *, tag=None, optional=False)</code></h3>
          <p className={`mb-4 text-sm ${subtleText}`}>
            Synchronous resolution for non-async call sites. Drives the async path on a persistent per-thread event loop. <strong>Raises <code className="text-aquilia-500">DIResolutionFault</code> if called from inside a running event loop</strong> — in async code, always use <code className="text-aquilia-500">resolve_async</code>.
          </p>
        </div>

        {/* register_instance */}
        <div className="mb-12 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">await register_instance(token, instance, scope="request", tag=None)</code></h3>
          <p className={`mb-4 text-sm ${subtleText}`}>
            Register a pre-built object (wraps it in a <code className="text-aquilia-500">ValueProvider</code>). Used for request-scoped objects created outside DI — the ASGI layer registers the current <code className="text-aquilia-500">Request</code> this way. Always replaces any existing entry for the token.
          </p>
          <CodeBlock language="python">{`session = await engine.open_session(request)
await container.register_instance(Session, session, scope="request")`}</CodeBlock>
        </div>

        {/* is_registered */}
        <div className="mb-12 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">is_registered(token, tag=None)</code></h3>
          <p className={`mb-4 text-sm ${subtleText}`}>
            Returns <code className="text-aquilia-500">True</code> if a provider is registered for the token (checks this container and its parent chain).
          </p>
        </div>

        {/* create_request_scope */}
        <div className="mb-12 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">create_request_scope()</code></h3>
          <p className={`mb-4 text-sm ${subtleText}`}>
            Create a lightweight child container for request-scoped isolation. The child shares the parent's providers but has isolated caches and finalizers.
          </p>
        </div>

        {/* create_child */}
        <div className="mb-12 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">create_child(scope="app", *, own_lifecycle=True)</code></h3>
          <p className={`mb-4 text-sm ${subtleText}`}>
            Generic hierarchical child container (copy-on-write provider dict; parent singletons resolved once at the owning level). Use for per-tenant or multi-level scope trees.
          </p>
        </div>

        {/* add_dependency_link */}
        <div className="mb-12 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">add_dependency_link(app_name, container)</code></h3>
          <p className={`mb-4 text-sm ${subtleText}`}>
            Runtime counterpart to a manifest's <code className="text-aquilia-500">depends_on</code>. When a token is missing locally and up the parent chain, resolution falls through to the linked sibling app container. Wired automatically by the runtime; undeclared cross-app deps still raise <code className="text-aquilia-500">ProviderNotFoundError</code>, and link cycles raise <code className="text-aquilia-500">DependencyCycleError</code>.
          </p>
        </div>

        {/* replace_provider */}
        <div className="mb-12 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">await replace_provider(token, provider, *, tag=None)</code></h3>
          <p className={`mb-4 text-sm ${subtleText}`}>
            Production-safe atomic hot-swap of a provider (copy-on-write safe, evicts the cached instance). Distinct from the test-only <code className="text-aquilia-500">override_container</code>. Emits a <code className="text-aquilia-500">REGISTRATION</code> diagnostic event.
          </p>
        </div>

        {/* shutdown */}
        <div className="mb-12 border-l-2 border-white/5 pl-6">
          <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code className="text-aquilia-500 text-lg">shutdown()</code></h3>
          <p className={`mb-4 text-sm ${subtleText}`}>
            Runs inline <code className="text-aquilia-500">Dep()</code> generator teardowns (LIFO) first, then drains finalizers in LIFO order (clean up database connections or file handlers), runs lifecycle shutdown hooks, and clears the instance cache.
          </p>
        </div>
      </section>

      {/* Caching Behavior by Scope */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Caching Behavior by Scope</h2>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Scope</th>
                <th className="py-4 px-6 text-left font-semibold">Cached?</th>
                <th className="py-4 px-6 text-left font-semibold">Where Cached</th>
                <th className="py-4 px-6 text-left font-semibold">Behavior</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['singleton', 'Yes', 'Parent (root)', 'One instance for the entire process. Delegates to parent.'],
                ['app', 'Yes', 'Parent (root)', 'Same as singleton — cached at app level. Delegates to parent.'],
                ['request', 'Yes', 'Child', 'One instance per request container. Cleared on request shutdown.'],
                ['transient', 'No', '—', 'New instance on every resolve_async() call.'],
                ['pooled', 'Yes', 'Pool queue', 'Managed by PoolProvider\'s asyncio.Queue. acquire/release.'],
                ['ephemeral', 'No', '—', 'Like transient but with request→ephemeral parent hierarchy.'],
              ].map(([scope, cached, where, behavior], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-aquilia-500 text-xs">{scope}</td>
                  <td className="py-3.5 px-6 font-semibold">{cached}</td>
                  <td className="py-3.5 px-6 text-xs">{where}</td>
                  <td className={`py-3.5 px-6 ${subtleText}`}>{behavior}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className={`mt-16 pt-8 border-t flex justify-between ${isDark ? 'border-white/5' : 'border-gray-200'}`}>
        <Link to="/docs/di/overview" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> DI Overview
        </Link>
        <Link to="/docs/di/providers" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          Providers <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}
