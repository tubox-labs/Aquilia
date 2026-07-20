import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { ArrowLeft, ArrowRight, ShieldAlert } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function DITroubleshooting() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'
  const head = isDark ? 'text-white' : 'text-gray-900'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <ShieldAlert className="w-4 h-4" />
          Dependency Injection / Errors &amp; Troubleshooting
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${head} mb-4`}>
          Errors, Faults &amp; Troubleshooting
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Every DI failure raises a structured fault, not a bare exception. This page is the complete taxonomy — what each error means, when it fires, and how to fix it.
        </p>
      </div>

      {/* Fault hierarchy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>The Fault Hierarchy</h2>
        <p className={`mb-4 ${subtleText}`}>
          All DI errors descend from <code className="text-aquilia-500">DIFault</code> (domain <code className="text-aquilia-500">DI</code>, severity <code className="text-aquilia-500">ERROR</code>, non-retryable, non-public). Registration/graph errors live in <code className="text-aquilia-500">aquilia.di.errors</code> and subclass <code className="text-aquilia-500">DIError</code>; runtime resolution failures raise <code className="text-aquilia-500">DIResolutionFault</code>. Because they are faults, the Fault Engine renders them as structured responses automatically.
        </p>
        <CodeBlock language="text" filename="Hierarchy">{`Fault
└── DIFault                       (code varies; domain=DI)
    ├── DIError                   ("DI_ERROR")
    │   ├── ProviderNotFoundError     ("PROVIDER_NOT_FOUND")
    │   ├── DependencyCycleError      ("DEPENDENCY_CYCLE")
    │   ├── ScopeViolationError       ("SCOPE_VIOLATION")
    │   ├── AmbiguousProviderError    ("AMBIGUOUS_PROVIDER")
    │   ├── ManifestValidationError   ("MANIFEST_VALIDATION_FAILED")
    │   ├── CrossAppDependencyError   ("CROSS_APP_DEPENDENCY")
    │   ├── CircularDependencyError   ("CIRCULAR_DEPENDENCY")
    │   └── MissingDependencyError    ("MISSING_DEPENDENCY")
    ├── DIResolutionFault         ("DI_RESOLUTION_FAILED")
    └── DIConfigFault             ("DI_CONFIG_INVALID")`}</CodeBlock>
        <div className="border-l-4 border-aquilia-500 bg-aquilia-500/5 pl-4 py-3 rounded-r-xl my-6">
          <p className="text-xs text-aquilia-500/90 leading-relaxed">
            Exported from <code className="text-xs">aquilia.di</code>: <code className="text-xs">DIError</code>, <code className="text-xs">ProviderNotFoundError</code>, <code className="text-xs">DependencyCycleError</code>, <code className="text-xs">ScopeViolationError</code>, <code className="text-xs">AmbiguousProviderError</code>. The graph-build errors (<code className="text-xs">MissingDependencyError</code>, <code className="text-xs">CircularDependencyError</code>, <code className="text-xs">CrossAppDependencyError</code>, <code className="text-xs">ManifestValidationError</code>) exist in <code className="text-xs">aquilia.di.errors</code> but aren't re-exported — import them from there if you catch them directly.
          </p>
        </div>
      </section>

      {/* Error catalog */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${head}`}>Error Catalog</h2>
        <div className="space-y-8">
          {[
            {
              name: 'ProviderNotFoundError',
              code: 'PROVIDER_NOT_FOUND',
              when: 'You resolve a token that has no registered provider (and optional=False). The message lists similar registered keys as candidates.',
              fix: 'Register the provider (list it in the manifest or container.register(...)). If it is genuinely optional, use Optional[T] or Inject(optional=True). If a tagged provider exists, add the matching Inject(tag=...).',
            },
            {
              name: 'AmbiguousProviderError',
              code: 'AMBIGUOUS_PROVIDER',
              when: 'Multiple providers match one token and no tag was supplied to pick one.',
              fix: 'Tag each provider at registration and select one with Inject(tag="..."), or remove the duplicate registration.',
            },
            {
              name: 'ScopeViolationError',
              code: 'SCOPE_VIOLATION',
              when: 'A shorter-lived provider (request/ephemeral) is injected into a longer-lived consumer (singleton/app) — a captive dependency. Only raised when scope_enforcement="raise" (otherwise logged as a warning).',
              fix: 'Align scopes (make the consumer request-scoped), or resolve the short-lived dependency lazily inside a method via the request container instead of capturing it in the constructor.',
            },
            {
              name: 'MissingDependencyError',
              code: 'MISSING_DEPENDENCY',
              when: 'Graph build (Registry.from_manifests) finds a service whose constructor needs a token that no provider supplies. Includes the service source location when available.',
              fix: 'Register the missing dependency, or give the constructor parameter a default / Optional[T] so it is not required.',
            },
            {
              name: 'CircularDependencyError',
              code: 'CIRCULAR_DEPENDENCY',
              when: 'Tarjan\'s SCC detection finds a construction cycle across providers during graph build. Reports every cycle with source locations.',
              fix: 'Break the cycle: extract an interface, introduce an event/mediator, or use a LazyProxyProvider (allow_lazy) for one edge.',
            },
            {
              name: 'DependencyCycleError',
              code: 'DEPENDENCY_CYCLE',
              when: 'A cycle is hit at resolution time — including one that spans a cross-app dependency link (A→B→A) that static graph analysis could not see.',
              fix: 'Same remedies as CircularDependencyError. For cross-app cycles, rethink the depends_on topology so it forms a DAG.',
            },
            {
              name: 'CrossAppDependencyError',
              code: 'CROSS_APP_DEPENDENCY',
              when: 'A service depends on another app\'s provider without declaring that app in its manifest depends_on. Raised at boot.',
              fix: 'Add the provider app to the consumer manifest\'s depends_on list.',
            },
            {
              name: 'ManifestValidationError',
              code: 'MANIFEST_VALIDATION_FAILED',
              when: 'A manifest fails structural validation (malformed services list or configuration).',
              fix: 'Fix the manifest\'s services entries / configuration per the listed errors.',
            },
            {
              name: 'DIResolutionFault',
              code: 'DI_RESOLUTION_FAILED',
              when: 'A runtime resolution failure not covered above — a Dep() circular dependency, a pool exhausted past its acquire_timeout or max_waiters, a non-generator passed where a generator Dep was expected, or resolve() called from inside a running event loop.',
              fix: 'Read the reason string — it names the provider and cause. For pools, raise max_size / max_waiters. For "in a running loop", await resolve_async() instead of the sync resolve().',
            },
            {
              name: 'DIConfigFault',
              code: 'DI_CONFIG_INVALID',
              when: 'An invalid value in the di config block (bad scope_enforcement, disposal_strategy, non-positive timeout, pool_max_waiters < 1, etc). Raised at boot when DISettings is constructed.',
              fix: 'Correct the offending field in your workspace.py di block. The message names the field, the bad value, and the allowed set.',
            },
          ].map((e, i) => (
            <div key={i} className="border-l-2 border-red-500/30 pl-6">
              <div className="flex flex-wrap items-center gap-3 mb-2">
                <h3 className={`text-lg font-bold ${head}`}><code className="text-red-400">{e.name}</code></h3>
                <span className="font-mono text-xs text-yellow-500 bg-yellow-500/10 px-2 py-0.5 rounded">{e.code}</span>
              </div>
              <p className={`text-sm mb-1 ${subtleText}`}><strong className={head}>When:</strong> {e.when}</p>
              <p className={`text-sm ${subtleText}`}><strong className={head}>Fix:</strong> {e.fix}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Boot-time validation faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Boot-Time Registration Faults</h2>
        <p className={`mb-4 ${subtleText}`}>
          The runtime raises structured <code className="text-aquilia-500">DIFault</code>s while wiring services from manifests:
        </p>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Code</th>
                <th className="py-4 px-6 text-left font-semibold">Cause</th>
                <th className="py-4 px-6 text-left font-semibold">Behavior</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['INVALID_SERVICE_SCOPE', 'A manifest declares an unknown scope (typo like "singelton").', 'Always fatal. Lists the valid scopes.'],
                ['SERVICE_REGISTRATION_FAILED', 'A service fails to import/construct at registration.', 'Fatal only when strict_service_registration=True; otherwise logged and skipped.'],
                ['PROVIDER_ALREADY_REGISTERED', 'A genuine local re-registration of the same token+tag.', 'Raised. Shadowing an inherited parent provider is allowed and does not raise.'],
                ['DI_INVALID_PLUGIN', 'register_plugin() called with a non-DIPlugin object.', 'Raised immediately.'],
                ['DI_NO_INTERCEPTORS', 'intercept()/InterceptingProvider given an empty interceptor list.', 'Raised at construction.'],
              ].map(([code, cause, behavior], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-xs text-yellow-500 whitespace-nowrap">{code}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{cause}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{behavior}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Handling faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Catching DI Faults</h2>
        <CodeBlock language="python" filename="Targeted handling">{`from aquilia.di import (
    ProviderNotFoundError, ScopeViolationError, DependencyCycleError, DIError,
)

try:
    svc = await container.resolve_async(SomeService)
except ProviderNotFoundError as e:
    log.error("Missing provider: token=%s candidates=%s", e.token, e.candidates)
except ScopeViolationError as e:
    log.error("Captive dep: %s(%s) -> %s(%s)",
              e.provider_token, e.provider_scope, e.consumer_token, e.consumer_scope)
except DIError as e:                 # catch-all for the DI domain
    log.error("DI failure [%s]: %s", e.code, e.message)`}</CodeBlock>
      </section>

      {/* Troubleshooting playbook */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Troubleshooting Playbook</h2>
        <div className="space-y-4 text-sm">
          {[
            ['"No provider found" but I registered it', 'The token key is module.qualname. If two classes share a name across modules, or the class is imported under a different path, the keys differ. Register/resolve by the same type object, or use a string token consistently. Run aq di-tree to see registered keys.'],
            ['A singleton sees stale request data', 'You captured a request-scoped object in a singleton constructor. Move that dependency to a method call resolved from the request container, or make the consumer request-scoped. Turn on scope_enforcement="raise" to catch it at the source.'],
            ['Cycle only fails in production', 'Cross-app link cycles surface at resolution, not graph build. Map your depends_on edges — they must form a DAG. aq di-graph exports a DOT you can render to spot the loop.'],
            ['Sync resolve() raises "in a running loop"', 'Container.resolve() and lazy proxies refuse to drive the async path from inside an event loop (deadlock guard). In async code, always await resolve_async().'],
            ['Pool times out under load', 'The pool hit max_size with a full waiter queue. Raise max_size, raise/adjust max_waiters, or increase acquire_timeout_seconds — but first check whether instances are being released (use the acquire() context manager).'],
            ['Parallel resolution changed behavior', 'With parallel_resolution=True, independent constructor deps resolve concurrently on forked resolution contexts. In-flight dedup preserves singleton/app/request identity. If a provider has hidden ordering assumptions, keep it sequential.'],
          ].map(([q, a], i) => (
            <div key={i} className="rounded-xl border border-white/5 bg-white/5 p-4">
              <p className={`font-semibold mb-1 ${head}`}>{q}</p>
              <p className={subtleText}>{a}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Validate in CI */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${head}`}>Validate Before You Ship</h2>
        <p className={`mb-4 ${subtleText}`}>
          Catch DI misconfiguration in CI, before it reaches production:
        </p>
        <CodeBlock language="bash" filename="CI step">{`# Fail the build on cycles, missing providers, undeclared cross-app deps
aq di-check --settings workspace.py --verbose

# Visualize the graph for review
aq di-graph --settings workspace.py --out di-graph.dot

# Inspect the resolution tree from a root
aq di-tree --settings workspace.py --root modules.api.services:ApiService`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`mt-16 pt-8 border-t flex justify-between ${isDark ? 'border-white/5' : 'border-gray-200'}`}>
        <Link to="/docs/di/patterns" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> Patterns &amp; Recipes
        </Link>
        <Link to="/docs/models" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          Models <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
