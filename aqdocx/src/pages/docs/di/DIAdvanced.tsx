import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Cpu } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function DIAdvanced() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Cpu className="w-4 h-4" />
          Dependency Injection / Advanced
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Advanced DI &amp; Testing Overrides
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Customize the resolution graph dynamically, swap providers at runtime during tests, and configure complex factory pipelines.
        </p>
      </div>

      {/* Advanced Decorators Reference */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Decorators Cheat Sheet</h2>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Decorator</th>
                <th className="py-4 px-6 text-left font-semibold">Scope</th>
                <th className="py-4 px-6 text-left font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                { d: '@service', s: 'app', desc: 'Class-based provider, instantiated once per app and cached.' },
                { d: '@service(scope="request")', s: 'request', desc: 'Per-request instance, cleared on request teardown.' },
                { d: '@service(scope="transient")', s: 'transient', desc: 'New instance generated on every resolution call.' },
                { d: '@service(when=predicate)', s: 'any', desc: 'Conditional registration gated on a ConditionContext predicate.' },
                { d: '@factory', s: 'configurable', desc: 'Decorator mapping functions as service providers.' },
                { d: '@provides(Token)', s: 'n/a', desc: 'Defines a custom provider function inside another service.' },
                { d: '@auto_inject', s: 'n/a', desc: 'Scan annotations and auto-resolve constructor arguments.' },
              ].map((row, i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-aquilia-500 text-xs">{row.d}</td>
                  <td className="py-3.5 px-6 font-mono text-xs text-yellow-500">{row.s}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{row.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* DI Settings */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>DI Settings</h2>
        <p className={`mb-4 ${subtleText}`}>
          Every runtime knob for the container lives in one typed, immutable <code className="text-aquilia-500">DISettings</code> object. Configure it declaratively through the <code className="text-aquilia-500">di</code> section of your <code className="text-aquilia-500">workspace.py</code> — the server reads it at boot and calls <code className="text-aquilia-500">configure_di()</code> for you.
        </p>
        <CodeBlock language="python" filename="workspace.py — di config block">{`from aquilia import AquilaConfig

class BaseEnv(AquilaConfig):
    class di(AquilaConfig.DI):
        scope_enforcement   = "warn"     # "warn" | "raise" | "off"
        parallel_resolution = False

class DevEnv(BaseEnv):
    class di(BaseEnv.di):
        diagnostics_enabled = True       # trace every resolution in dev

class ProdEnv(BaseEnv):
    class di(BaseEnv.di):
        scope_enforcement   = "raise"    # fail-fast on captive deps
        parallel_resolution = True       # resolve independent deps concurrently
        pool_max_waiters    = 256        # fast-fail an exhausted pool`}</CodeBlock>

        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mt-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Setting</th>
                <th className="py-4 px-6 text-left font-semibold">Default</th>
                <th className="py-4 px-6 text-left font-semibold">Purpose</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['scope_enforcement', '"warn"', 'Captive-dependency handling: "warn" logs, "raise" raises ScopeViolationError, "off" skips.'],
                ['parallel_resolution', 'False', 'Resolve independent constructor deps concurrently via asyncio.gather.'],
                ['diagnostics_enabled', 'False', 'Emit RESOLUTION_START/SUCCESS/FAILURE diagnostic events per resolve.'],
                ['disposal_strategy', '"lifo"', 'Finalizer ordering: "lifo" | "fifo" | "parallel".'],
                ['hook_timeout_seconds', '30.0', 'Per-hook timeout for startup/shutdown lifecycle hooks.'],
                ['pool_acquire_timeout_seconds', '30.0', 'Default pool acquire timeout.'],
                ['pool_max_waiters', 'None', 'Cap on concurrent waiters against an exhausted pool (None = unbounded).'],
                ['type_key_cache_max', '8192', 'Upper bound on the global type→key cache before a wholesale flush.'],
                ['enable_conditional_providers', 'True', 'Honour @conditional / when= predicates during registration.'],
                ['enable_plugins', 'True', 'Run registered DIPlugin hooks during registry build.'],
                ['strict_service_registration', 'False', 'Fail-fast at boot when a service fails to register, instead of warning.'],
              ].map(([name, def_, purpose], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-aquilia-500 text-xs whitespace-nowrap">{name}</td>
                  <td className="py-3.5 px-6 font-mono text-xs text-yellow-500">{def_}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{purpose}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className={`mb-4 mt-6 ${subtleText}`}>
          In tests or scripts you can configure the container directly. Invalid values raise <code className="text-aquilia-500">DIConfigFault</code> at construction, so bad config surfaces at boot rather than at first resolution:
        </p>
        <CodeBlock language="python" filename="Direct configuration (tests)">{`from aquilia.di import DISettings, configure_di, get_di_settings, reset_di_settings

configure_di(DISettings(scope_enforcement="raise", parallel_resolution=True))

assert get_di_settings().strict_scopes is True

# Test teardown — restore permissive defaults
reset_di_settings()`}</CodeBlock>
      </section>

      {/* Interceptors */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Provider Interceptors</h2>
        <p className={`mb-4 ${subtleText}`}>
          Interceptors wrap a provider's <strong>instantiation</strong> with around-advice (AOP) — logging, timing, tracing, caching — without touching the service class. Wrap any provider with <code className="text-aquilia-500">intercept()</code>. Interceptors run in registration order, first = outermost; call <code className="text-aquilia-500">nxt()</code> to proceed, or skip it to short-circuit with your own object.
        </p>
        <CodeBlock language="python" filename="Timing interceptor">{`from aquilia.di import ProviderInterceptor, intercept, ClassProvider

class TimingInterceptor(ProviderInterceptor):
    async def around_instantiate(self, ctx, nxt):
        import time
        start = time.perf_counter()
        obj = await nxt()               # proceed to real instantiation
        elapsed = time.perf_counter() - start
        print(f"built {ctx.meta.name} in {elapsed*1e6:.1f}us")
        return obj

# Wrap a provider — interceptors run first=outermost
provider = intercept(ClassProvider(UserService, scope="app"), TimingInterceptor())
container.register(provider)`}</CodeBlock>
        <div className="border-l-4 border-aquilia-500 bg-aquilia-500/5 pl-4 py-3 rounded-r-xl my-6">
          <p className="text-xs text-aquilia-500/90 leading-relaxed">
            <code className="text-xs">intercept(P, A, B)</code> yields the chain <code className="text-xs">A(in) → B(in) → B(out) → A(out)</code>. The wrapped <code className="text-xs">InterceptingProvider</code> mirrors the inner provider's token, scope, and tags. Wrapping with an empty interceptor list raises <code className="text-xs">DIFault</code> (<code className="text-xs">DI_NO_INTERCEPTORS</code>).
          </p>
        </div>
      </section>

      {/* Plugins */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>DI Plugins</h2>
        <p className={`mb-4 ${subtleText}`}>
          A <code className="text-aquilia-500">DIPlugin</code> hooks into registry construction to auto-register providers, observe registrations, or inspect built containers — ideal for cross-cutting concerns like auto-wiring repositories. Register once with <code className="text-aquilia-500">register_plugin()</code>; hooks fire during boot when <code className="text-aquilia-500">enable_plugins</code> is on (default).
        </p>
        <CodeBlock language="python" filename="Auto-registration plugin">{`from aquilia.di import DIPlugin, register_plugin, ClassProvider

class RepositoryPlugin(DIPlugin):
    name = "repository-autoreg"          # stable id — re-registering replaces

    def on_registry_build(self, registry):
        # Runs after manifests load, before the graph is built
        registry.add_provider(ClassProvider(UserRepository, scope="app"))

    def on_provider_registered(self, container, provider):
        ...   # fires per register() call

    def on_container_built(self, container):
        ...   # fires once each app container is built

register_plugin(RepositoryPlugin())`}</CodeBlock>
        <div className="border-l-4 border-aquilia-500 bg-aquilia-500/5 pl-4 py-3 rounded-r-xl my-6">
          <p className="text-xs text-aquilia-500/90 leading-relaxed">
            <strong>Failure-isolated:</strong> a plugin hook that raises is logged and skipped — it never crashes boot. Manage the registry with <code className="text-xs">unregister_plugin(name)</code>, <code className="text-xs">get_plugins()</code>, and <code className="text-xs">clear_plugins()</code> (test teardown). Plugins are deduplicated by <code className="text-xs">.name</code>.
          </p>
        </div>
      </section>

      {/* Cross-app & hot-swap */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Cross-App Links &amp; Runtime Swaps</h2>
        <p className={`mb-4 ${subtleText}`}>
          When a module declares <code className="text-aquilia-500">depends_on</code> in its manifest, the runtime wires a dependency link between the two app containers via <code className="text-aquilia-500">add_dependency_link()</code>. A token missing locally (and up the parent chain) falls through to the linked sibling app; the owning container instantiates and caches its own singletons exactly once. Undeclared cross-app dependencies still raise <code className="text-aquilia-500">ProviderNotFoundError</code>, and link cycles raise <code className="text-aquilia-500">DependencyCycleError</code> instead of deadlocking.
        </p>
        <CodeBlock language="python" filename="Production-safe hot-swap">{`# Atomically replace a provider at runtime (copy-on-write safe, evicts the
# cached instance). Distinct from the test-only override_container helper.
await container.replace_provider(EmailService, ClassProvider(SmtpEmailService, scope="app"))

# Generic hierarchical child (per-tenant trees, multi-level scopes)
child = container.create_child(scope="app", own_lifecycle=True)`}</CodeBlock>
      </section>

      {/* Test Overrides */}
      <section className="mb-16 border-l-2 border-aquilia-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>TestRegistry Overrides</h2>
        <p className={`mb-4 ${subtleText}`}>
          Swap components with mock implementations during unit or integration testing:
        </p>
        <CodeBlock language="python" filename="test_registry.py">{`from aquilia.di import TestRegistry, MockProvider

# Create a test registry delegating to production setup
test_reg = TestRegistry(base=production_registry)

# Override with custom value or MockProvider
test_reg.override(EmailService, MockProvider(
    send=AsyncMock(return_value=True)
))

# Override database connection pools with mock mocks
test_reg.override(DatabasePool, value=FakeDbPool())`}</CodeBlock>
      </section>

      {/* Pytest Fixtures */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Pytest Fixtures</h2>
        <p className={`mb-4 ${subtleText}`}>
          Use the built-in context overrides helper to automatically mock out components during test execution:
        </p>
        <CodeBlock language="python" filename="test_controller.py">{`import pytest
from aquilia.di.testing import override_container

@pytest.mark.asyncio
async def test_user_creation(client, app_container):
    # Override UserService inside the app DI container temporarily:
    mock_service = MagicMock()
    
    with override_container(app_container, {UserService: mock_service}):
        response = await client.post("/users", json={"name": "Alice"})
        assert response.status_code == 201
        mock_service.create.assert_called_once()`}</CodeBlock>
      </section>

      {/* Nav */}
      <div className="flex justify-between items-center mt-16 pt-8 border-t border-white/5">
        <Link to="/docs/di/scopes" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition">
          <ArrowLeft className="w-4 h-4" /> Scopes
        </Link>
        <Link to="/docs/models" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition">
          Models <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}