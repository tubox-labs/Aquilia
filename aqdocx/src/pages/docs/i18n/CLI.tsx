import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Terminal } from 'lucide-react'

export function I18nCLI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderSubtle = isDark ? 'border-white/5' : 'border-gray-100'

  const commands: Array<[string, string]> = [
    ['aq i18n init', 'Initialize locale directory structure and starter message files.'],
    ['aq i18n check', 'Validate runtime i18n config and inspect locale directory presence.'],
    ['aq i18n inspect', 'Print effective i18n config JSON.'],
    ['aq i18n extract', 'Extract translation keys from Python and template sources.'],
    ['aq i18n coverage', 'Compute locale coverage against default locale key set.'],
    ['aq i18n compile', 'Compile JSON catalogs to SURP artifacts for faster runtime loading.'],
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Terminal className="w-4 h-4" />
          i18n / CLI
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            i18n CLI Reference
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          The <code className="text-aquilia-500">aq i18n</code> command group covers catalog initialization, validation, extraction, coverage measurement,
          and SURP compilation. Commands are registered in the CLI entrypoint and implemented in
          <code className="text-aquilia-500">aquilia/cli/commands/i18n.py</code>.
        </p>
      </div>

      {/* Command Surface */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Command Surface</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className={`border-b ${borderSubtle} ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <th className="pb-3 font-semibold pr-4">Command</th>
                <th className="pb-3 font-semibold">Purpose</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
              {commands.map(([name, desc], i) => (
                <tr key={i} className={`border-b ${borderSubtle} hover:bg-aquilia-50/[0.02]`}>
                  <td className="py-2.5 font-mono text-aquilia-500 text-xs pr-4">{name}</td>
                  <td className="py-2.5 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* aq i18n init */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq i18n init</h2>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[1]}>{`aq i18n init --locales en,fr,de --directory locales --format json
aq i18n init --locales en --directory translations --format yaml`}</CodeBlock>
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 space-y-2 mt-4">
          <p>• Bootstraps locale folders and starter files such as <code className="text-aquilia-500">locales/en/messages.json</code>.</p>
          <p>• Skips files that already exist and only creates missing locale assets.</p>
        </div>
      </section>

      {/* aq i18n check and inspect */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq i18n check and inspect</h2>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[1, 3]}>{`aq i18n check
aq i18n check --verbose
aq i18n inspect`}</CodeBlock>
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 space-y-2 mt-4">
          <p>• <code className="text-aquilia-500">check</code> validates enabled, default, fallback and resolver settings.</p>
          <p>• <code className="text-aquilia-500">inspect</code> prints effective configuration JSON using workspace-first load behavior.</p>
        </div>
      </section>

      {/* aq i18n extract */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq i18n extract</h2>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[1]}>{`aq i18n extract --source-dirs modules,templates --output locales/en/messages.json
aq i18n extract --source-dirs modules,controllers --output locales/en/messages.json --no-merge`}</CodeBlock>
        <p className={`mt-4 text-sm ${textMuted}`}>
          Extraction scans translation calls in Python and template files, expands dotted keys to nested JSON, and merges with existing values.
        </p>
      </section>

      {/* aq i18n coverage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq i18n coverage</h2>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[1]}>{`aq i18n coverage
aq i18n coverage --verbose`}</CodeBlock>
      </section>

      {/* aq i18n compile */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq i18n compile</h2>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[1]}>{`aq i18n compile
aq i18n compile --directory locales
aq i18n compile --directory locales --output artifacts/locales`}</CodeBlock>
      </section>

      <NextSteps
        items={[
          { text: 'i18n Configuration', link: '/docs/i18n/configuration' },
          { text: 'i18n Integration', link: '/docs/i18n/integration' },
          { text: 'i18n API Reference', link: '/docs/i18n/api-reference' },
          { text: 'i18n Troubleshooting', link: '/docs/i18n/troubleshooting' },
        ]}
      />
    </div>
  )
}
