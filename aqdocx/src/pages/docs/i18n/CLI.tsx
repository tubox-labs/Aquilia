import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Terminal } from 'lucide-react'

export function I18nCLI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const box = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const subtle = isDark ? 'text-gray-400' : 'text-gray-600'

  const commands: Array<[string, string]> = [
    ['aq i18n init', 'Initialize locale directory structure and starter message files.'],
    ['aq i18n check', 'Validate runtime i18n config and inspect locale directory presence.'],
    ['aq i18n inspect', 'Print effective i18n config JSON.'],
    ['aq i18n extract', 'Extract translation keys from Python and template sources.'],
    ['aq i18n coverage', 'Compute locale coverage against default locale key set.'],
    ['aq i18n compile', 'Compile JSON catalogs to CROUS artifacts for faster runtime loading.'],
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
        <p className={`text-lg leading-relaxed ${subtle}`}>
          The aq i18n command group covers catalog initialization, validation, extraction, coverage measurement,
          and CROUS compilation. Commands are registered in the CLI entrypoint and implemented in
          aquilia/cli/commands/i18n.py.
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
                  <th className="text-left pb-3 font-semibold">Purpose</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                {commands.map(([name, desc], i) => (
                  <tr key={i} className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-2 font-mono text-aquilia-500 text-xs pr-4">{name}</td>
                    <td className="py-2 text-xs">{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq i18n init</h2>
        <CodeBlock language="bash" filename="Terminal">{`aq i18n init --locales en,fr,de --directory locales --format json
aq i18n init --locales en --directory translations --format yaml`}</CodeBlock>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>Bootstraps locale folders and starter files such as locales/en/messages.json.</li>
            <li>Supports json, yaml, and crous command paths (with crous dependency checks).</li>
            <li>Skips files that already exist and only creates missing locale assets.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq i18n check and inspect</h2>
        <CodeBlock language="bash" filename="Terminal">{`aq i18n check
aq i18n check --verbose
aq i18n inspect`}</CodeBlock>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>check validates enabled/default/fallback/resolver settings and catalog directory presence.</li>
            <li>inspect prints effective configuration JSON using workspace-first load behavior.</li>
            <li>both commands rely on workspace.py workspace object when present, otherwise ConfigLoader fallback.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq i18n extract</h2>
        <CodeBlock language="bash" filename="Terminal">{`aq i18n extract --source-dirs modules,templates --output locales/en/messages.json
aq i18n extract --source-dirs modules,controllers --output locales/en/messages.json --no-merge`}</CodeBlock>
        <div className={box}>
          <p className={`text-sm ${subtle}`}>
            Extraction scans translation calls in Python and template files, expands dotted keys to nested JSON,
            and can merge with existing catalog values unless no-merge is provided.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq i18n coverage</h2>
        <CodeBlock language="bash" filename="Terminal">{`aq i18n coverage
aq i18n coverage --verbose`}</CodeBlock>
        <div className={box}>
          <p className={`text-sm ${subtle}`}>
            Coverage compares each locale key set against the default locale key set and prints percentages.
            Verbose mode includes missing key samples for each locale.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>aq i18n compile</h2>
        <CodeBlock language="bash" filename="Terminal">{`aq i18n compile
aq i18n compile --directory locales
aq i18n compile --directory locales --output artifacts/locales`}</CodeBlock>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>Compiles JSON catalogs into CROUS files for faster startup and lookups.</li>
            <li>Uses CrousCatalog compile path under the hood.</li>
            <li>Requires crous package; command reports clear dependency error when absent.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Typical Workflow</h2>
        <CodeBlock language="bash" filename="Terminal">{`# 1) bootstrap locales
aq i18n init --locales en,fr,de --format json

# 2) extract keys from source
aq i18n extract --source-dirs modules,templates --output locales/en/messages.json

# 3) fill translations for sibling locales

# 4) verify coverage
aq i18n coverage --verbose

# 5) compile for deployment
aq i18n compile --directory locales`}</CodeBlock>
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
