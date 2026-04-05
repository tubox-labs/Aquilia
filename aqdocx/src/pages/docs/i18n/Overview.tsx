import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Link } from 'react-router-dom'
import { Languages } from 'lucide-react'

export function I18nOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const box = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const subtle = isDark ? 'text-gray-400' : 'text-gray-600'

  const subsystems: Array<{ title: string; desc: string }> = [
    {
      title: 'Locale and negotiation',
      desc: 'BCP 47 parsing, normalization, and Accept-Language negotiation with resolver chaining.',
    },
    {
      title: 'Catalog backends',
      desc: 'MemoryCatalog, FileCatalog, and CrousCatalog with namespace and merged layering support.',
    },
    {
      title: 'Formatting and plurals',
      desc: 'Message formatting, CLDR-style plural categories, and locale-aware number/date/currency helpers.',
    },
    {
      title: 'Runtime integration',
      desc: 'Request middleware, template globals, DI provider registration, and lazy translation context.',
    },
    {
      title: 'CLI operations',
      desc: 'aq i18n init/check/inspect/extract/coverage/compile for full translation lifecycle management.',
    },
    {
      title: 'Fault model',
      desc: 'Structured i18n fault types plus predictable missing-key strategies in I18nService.',
    },
  ]

  const docsMap: Array<{ title: string; path: string; text: string }> = [
    {
      title: 'Architecture',
      path: '/docs/i18n/architecture',
      text: 'Boot flow, lookup pipeline, resolver chain, and subsystem boundaries.',
    },
    {
      title: 'Configuration',
      path: '/docs/i18n/configuration',
      text: 'All entry points, precedence behavior, defaults matrix, and recommended production setup.',
    },
    {
      title: 'Integration',
      path: '/docs/i18n/integration',
      text: 'Server, middleware, request state, templates, DI, sessions, and manual setup patterns.',
    },
    {
      title: 'API Reference',
      path: '/docs/i18n/api-reference',
      text: 'Module-level symbol map across locale, catalog, formatter, service, middleware, and more.',
    },
    {
      title: 'CLI Reference',
      path: '/docs/i18n/cli',
      text: 'Detailed command behavior for initialization, extraction, coverage, and CROUS compilation.',
    },
    {
      title: 'Edge Cases',
      path: '/docs/i18n/edge-cases',
      text: 'Validated edge behavior, known limitations, and practical production mitigations.',
    },
    {
      title: 'Troubleshooting',
      path: '/docs/i18n/troubleshooting',
      text: 'Symptom-driven diagnostics for locale selection, missing keys, and template mismatches.',
    },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Languages className="w-4 h-4" />
          Advanced / i18n
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Internationalization (i18n)
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${subtle}`}>
          Aquilia i18n is an async-native localization subsystem with locale negotiation, plural-aware
          translation lookup, flexible catalog backends, and first-class integration into middleware,
          templates, DI containers, and CLI workflows.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>What You Get</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {subsystems.map((item, i) => (
            <div key={i} className={box}>
              <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h3>
              <p className={`text-sm ${subtle}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Quick Start</h2>
        <CodeBlock language="python" filename="workspace.py">{`from aquilia.config_builders import Workspace, Integration

workspace = (
    Workspace("myapp")
    .integrate(
        Integration.i18n(
            enabled=True,
            default_locale="en",
            available_locales=["en", "fr", "de", "ja"],
            fallback_locale="en",
            catalog_dirs=["locales"],
            catalog_format="crous",
            resolver_order=["query", "cookie", "header"],
        )
    )
)
`}</CodeBlock>
        <CodeBlock language="bash" filename="Terminal">{`aq i18n init --locales en,fr,de,ja --directory locales --format json
aq i18n extract --source-dirs modules,templates --output locales/en/messages.json
aq i18n compile --directory locales`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Request State Contract</h2>
        <div className={box}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={isDark ? 'text-gray-400' : 'text-gray-500'}>
                  <th className="text-left pb-3 font-semibold">State Key</th>
                  <th className="text-left pb-3 font-semibold">Type</th>
                  <th className="text-left pb-3 font-semibold">Meaning</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                <tr className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <td className="py-2 font-mono text-aquilia-500 text-xs pr-4">locale</td>
                  <td className="py-2 font-mono text-xs pr-4">str</td>
                  <td className="py-2 text-xs">Resolved locale tag after resolver chain and availability checks.</td>
                </tr>
                <tr className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <td className="py-2 font-mono text-aquilia-500 text-xs pr-4">locale_obj</td>
                  <td className="py-2 font-mono text-xs pr-4">Locale</td>
                  <td className="py-2 text-xs">Parsed locale object from aquilia.i18n.locale.parse_locale.</td>
                </tr>
                <tr className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <td className="py-2 font-mono text-aquilia-500 text-xs pr-4">i18n</td>
                  <td className="py-2 font-mono text-xs pr-4">I18nService</td>
                  <td className="py-2 text-xs">Primary translation service for downstream handlers and templates.</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Documentation Map</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {docsMap.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`${box} hover:border-aquilia-500/50 transition-colors`}
            >
              <h3 className="font-bold mb-2 text-aquilia-500">{item.title}</h3>
              <p className={`text-sm ${subtle}`}>{item.text}</p>
            </Link>
          ))}
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'i18n Architecture', link: '/docs/i18n/architecture' },
          { text: 'i18n Configuration', link: '/docs/i18n/configuration' },
          { text: 'i18n Integration', link: '/docs/i18n/integration' },
          { text: 'i18n API Reference', link: '/docs/i18n/api-reference' },
        ]}
      />
    </div>
  )
}
