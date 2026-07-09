import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Link } from 'react-router-dom'
import { Languages, ArrowRight } from 'lucide-react'

export function I18nOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderSubtle = isDark ? 'border-white/5' : 'border-gray-100'

  const subsystems: Array<{ title: string; desc: string | React.ReactNode }> = [
    {
      title: 'Locale and negotiation',
      desc: 'BCP 47 parsing, normalization, and Accept-Language negotiation with resolver chaining.',
    },
    {
      title: 'Catalog backends',
      desc: 'MemoryCatalog, FileCatalog, and SurpCatalog with namespace and merged layering support.',
    },
    {
      title: 'Formatting and plurals',
      desc: <>Message formatting, CLDR-style plural categories, and locale-aware number/date/currency helpers in <DocTerm id="i18n.I18nService">I18nService</DocTerm>.</>,
    },
    {
      title: 'Runtime integration',
      desc: <>Request middleware (<DocTerm id="i18n.I18nMiddleware">I18nMiddleware</DocTerm>), template globals, DI provider registration, and lazy translation context.</>,
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
      text: 'Detailed command behavior for initialization, extraction, coverage, and SURP compilation.',
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
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Aquilia i18n is an async-native localization subsystem with locale negotiation, plural-aware
          translation lookup, flexible catalog backends, and first-class integration into middleware,
          templates, DI containers, and CLI workflows.
        </p>
      </div>

      {/* What You Get */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>What You Get</h2>
        <div className="space-y-6">
          {subsystems.map((item, i) => (
            <div key={i} className="border-l-2 border-aquilia-500/20 pl-4 py-1">
              <h3 className={`font-mono text-sm font-bold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h3>
              <p className={`text-sm ${textMuted}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Workspace-Level Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Workspace-Level Integration</h2>
        <p className={`mb-4 ${textMuted}`}>
          Initialize i18n globally in your workspace configuration. You can configure available locales, directory paths, catalog formats, and the locale resolver preference chain.
        </p>
        <CodeBlock language="python" filename="workspace.py" highlightLines={[6, 11]}>{`from aquilia import Workspace
from aquilia.integrations.i18n import I18nIntegration

workspace = (
    Workspace("localized-app")
    .integrate(I18nIntegration(
        default_locale="en",
        available_locales=["en", "es", "fr", "ja"],
        catalog_dirs=["locales"],
        resolver_order=["query", "cookie", "header"],
    ))
)
`}</CodeBlock>
      </section>

      {/* Manifest & Module Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Manifest & Module Integration</h2>
        <p className={`mb-4 ${textMuted}`}>
          Controllers and services declared in the <code className="text-aquilia-500">AppManifest</code> can request the <DocTerm id="i18n.I18nService">I18nService</DocTerm> via constructor dependency injection. You can also define module-level constants using lazy translation utilities.
        </p>
        <CodeBlock language="python" filename="modules/billing/controllers.py" highlightLines={[8, 12, 17]}>{`from aquilia import Controller, GET, RequestCtx
from aquilia.i18n import I18nService, lazy_t

# Constant resolved lazily when the request locale is available
BILLING_HEADER = lazy_t("billing.invoice_header")

class BillingController(Controller):
    def __init__(self, i18n: I18nService):
        self.i18n = i18n

    @GET("/invoice")
    async def get_invoice(self, ctx: RequestCtx):
        locale = ctx.request.state.get("locale", "en")
        
        message = self.i18n.t(
            "billing.invoice_ready",
            locale=locale,
            amount="$45.00"
        )
        return {"header": str(BILLING_HEADER), "message": message}
`}</CodeBlock>
      </section>

      {/* Request State Contract */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Request State Contract</h2>
        <div className="overflow-x-auto">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className={`border-b ${borderSubtle} ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
                <th className="pb-3 font-semibold pr-4">State Key</th>
                <th className="pb-3 font-semibold pr-4">Type</th>
                <th className="pb-3 font-semibold">Meaning</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
              <tr className={`border-b ${borderSubtle} hover:bg-aquilia-50/[0.02]`}>
                <td className="py-2.5 font-mono text-aquilia-500 text-xs pr-4">locale</td>
                <td className="py-2.5 font-mono text-xs pr-4 text-zinc-500">str</td>
                <td className="py-2.5 text-xs">Resolved BCP 47 locale tag after negotiating candidate headers/cookies.</td>
              </tr>
              <tr className={`border-b ${borderSubtle} hover:bg-aquilia-50/[0.02]`}>
                <td className="py-2.5 font-mono text-aquilia-500 text-xs pr-4">locale_obj</td>
                <td className="py-2.5 font-mono text-xs pr-4 text-zinc-500">Locale</td>
                <td className="py-2.5 text-xs">Parsed Locale model with validation, normalization, and fallback properties.</td>
              </tr>
              <tr className={`border-b ${borderSubtle} hover:bg-aquilia-50/[0.02]`}>
                <td className="py-2.5 font-mono text-aquilia-500 text-xs pr-4">i18n</td>
                <td className="py-2.5 font-mono text-xs pr-4 text-zinc-500">I18nService</td>
                <td className="py-2.5 text-xs">Primary translation and formatting service registry bound to the active request context.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Documentation Map */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Documentation Map</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {docsMap.map((item) => (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center justify-between px-4 py-3 rounded-xl border transition-colors ${
                isDark
                  ? 'border-white/5 bg-zinc-950/40 text-gray-200 hover:border-aquilia-500/60 hover:bg-zinc-900/50'
                  : 'border-gray-200 bg-white text-gray-700 hover:border-aquilia-500/60 hover:bg-gray-50'
              }`}
            >
              <div>
                <span className="text-sm font-medium block text-aquilia-500">{item.title}</span>
                <span className="text-xs text-zinc-500 block mt-0.5">{item.text}</span>
              </div>
              <ArrowRight className="w-4 h-4 text-aquilia-500 flex-shrink-0" />
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
