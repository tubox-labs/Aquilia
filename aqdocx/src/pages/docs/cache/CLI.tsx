import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Terminal } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CacheCLI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const box = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const subtle = isDark ? 'text-gray-400' : 'text-gray-600'

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
        <p className={`text-lg leading-relaxed ${subtle}`}>
          Aquilia exposes cache management via the <code className="text-aquilia-500">aq cache</code> command group.
          Commands are registered in <code className="text-aquilia-500">aquilia/cli/__main__.py</code> and implemented in
          <code className="text-aquilia-500 mx-1">aquilia/cli/commands/cache.py</code>.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Command Surface</h2>
        <div className={box}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={isDark ? 'text-gray-400' : 'text-gray-500'}>
                  <th className="text-left pb-3 font-semibold">Command</th>
                  <th className="text-left pb-3 font-semibold">Description</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                {commands.map(([cmd, desc], i) => (
                  <tr key={i} className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-2 font-mono text-aquilia-500 text-xs pr-4">{cmd}</td>
                    <td className="py-2 text-xs">{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq cache check</h2>
        <p className={`mb-4 ${subtle}`}>
          Loads cache config and prints key settings (backend, TTL, serializer, key prefix, and backend-specific details).
          For redis backend it attempts a synchronous PING using the redis package.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`aq cache check
aq cache check -v`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq cache inspect</h2>
        <p className={`mb-4 ${subtle}`}>
          Outputs cache configuration as JSON. It first attempts to load from workspace.py and falls back to ConfigLoader defaults.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`aq cache inspect
aq cache inspect -v`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq cache stats</h2>
        <p className={`mb-4 ${subtle}`}>
          Builds a temporary CacheService and initializes it, then attempts to retrieve stats.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`aq cache stats
aq cache stats -v`}</CodeBlock>
        <div className={box}>
          <p className={`text-sm ${subtle}`}>
            Current implementation note: stats command checks for <code className="text-aquilia-500">svc.info()</code>.
            <code className="text-aquilia-500">CacheService</code> exposes <code className="text-aquilia-500">stats()</code>,
            not <code className="text-aquilia-500">info()</code>, so output may be empty.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq cache clear</h2>
        <p className={`mb-4 ${subtle}`}>
          Creates a temporary CacheService from config, initializes it, clears all entries or a single namespace,
          then shuts down the temporary service.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# Clear all keys
aq cache clear

# Clear one namespace
aq cache clear --namespace http`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Config Loading Logic</h2>
        <CodeBlock language="python" filename="aquilia/cli/commands/cache.py">{`def _load_cache_config() -> dict:
    # 1) workspace.py -> workspace.to_dict() -> cache or integrations.cache
    # 2) fallback ConfigLoader().get_cache_config()
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Operational Caveats</h2>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>check command currently expects nested redis/middleware blocks in some output paths, while canonical cache config is mostly flat.</li>
            <li>stats command may return no data because it probes for info() instead of calling stats().</li>
            <li>These commands inspect local config and local connectivity; they do not attach to an already-running app process cache instance.</li>
          </ul>
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
