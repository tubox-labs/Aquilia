import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Terminal } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CacheCLI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const subtleBorder = isDark ? 'border-white/5' : 'border-gray-100'

  const commands: Array<[string, string]> = [
    ['aq cache check', 'Validate cache config and optionally test Redis connectivity.'],
    ['aq cache inspect', 'Print effective cache config as JSON.'],
    ['aq cache stats', 'Instantiate temporary cache service and attempt statistics output.'],
    ['aq cache clear', 'Clear all cache entries (or one namespace) using temporary cache service.'],
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Terminal className="w-4 h-4" />
          Cache / CLI
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Cache CLI
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Aquilia exposes cache management via the <code className="text-aquilia-500">aq cache</code> command group.
          Commands are registered in <code className="text-aquilia-500">aquilia/cli/__main__.py</code> and implemented in
          <code className="text-aquilia-500 mx-1">aquilia/cli/commands/cache.py</code>.
        </p>
      </div>

      {/* Command Surface */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Command Surface</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className={`border-b ${subtleBorder} ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <th className="pb-3 font-semibold pr-4">Command</th>
                <th className="pb-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
              {commands.map(([cmd, desc], i) => (
                <tr key={i} className={`border-b ${subtleBorder} hover:bg-aquilia-500/[0.02]`}>
                  <td className="py-2.5 font-mono text-aquilia-500 text-xs pr-4">{cmd}</td>
                  <td className="py-2.5 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* aq cache check */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq cache check</h2>
        <p className={`mb-4 ${textMuted}`}>
          Loads cache config and prints key settings (backend, TTL, serializer, key prefix, and backend-specific details).
          For the Redis backend, it attempts a synchronous ping query to verify network connectivity.
        </p>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[1]}>{`aq cache check
aq cache check -v`}</CodeBlock>
      </section>

      {/* aq cache inspect */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq cache inspect</h2>
        <p className={`mb-4 ${textMuted}`}>
          Outputs cache configuration as JSON. It first attempts to load from the workspace module and falls back to ConfigLoader defaults.
        </p>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[1]}>{`aq cache inspect
aq cache inspect -v`}</CodeBlock>
      </section>

      {/* aq cache stats */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq cache stats</h2>
        <p className={`mb-4 ${textMuted}`}>
          Builds a temporary <DocTerm id="cache.CacheService">CacheService</DocTerm> and initializes it, then attempts to retrieve and display statistics from the active cache backend.
        </p>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[1]}>{`aq cache stats
aq cache stats -v`}</CodeBlock>
        <div className="border-l-2 border-amber-500/40 pl-4 py-1 text-sm text-zinc-500 mt-4">
          <p>
            <strong>Warning:</strong> The stats command expects the backend cache service to expose an <code className="text-aquilia-500">info()</code> call. Because <DocTerm id="cache.CacheService">CacheService</DocTerm> uses <code className="text-aquilia-500">stats()</code>, this command output may be empty for some backends.
          </p>
        </div>
      </section>

      {/* aq cache clear */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq cache clear</h2>
        <p className={`mb-4 ${textMuted}`}>
          Creates a temporary <DocTerm id="cache.CacheService">CacheService</DocTerm> from config, initializes it, clears all entries or a single namespace,
          then shuts down the temporary service.
        </p>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[2, 5]}>{`# Clear all keys
aq cache clear

# Clear one namespace
aq cache clear --namespace http`}</CodeBlock>
      </section>

      {/* Config Loading Logic */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Config Loading Logic</h2>
        <CodeBlock language="python" filename="aquilia/cli/commands/cache.py" highlightLines={[2, 3]}>{`def _load_cache_config() -> dict:
    # 1) workspace.py -> workspace.to_dict() -> cache or integrations.cache
    # 2) fallback ConfigLoader().get_cache_config()
`}</CodeBlock>
      </section>

      {/* Operational Caveats */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Operational Caveats</h2>
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 space-y-2">
          <p>
            • The check command expects nested config structures in the validation output paths, while standard cache configuration variables are flat.
          </p>
          <p>
            • CLI commands run in their own ephemeral process context. They do not hook into or share the in-memory cache allocations of separate running application server instances.
          </p>
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'Cache Overview', link: '/docs/cache' },
          { text: 'Configuration', link: '/docs/cache/configuration' },
          { text: 'CacheService API', link: '/docs/cache/service' },
          { text: 'API Reference', link: '/docs/cache/api-reference' },
        ]}
      />
    </div>
  )
}
