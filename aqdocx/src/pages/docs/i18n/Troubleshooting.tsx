import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { LifeBuoy } from 'lucide-react'

export function I18nTroubleshooting() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const box = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const subtle = isDark ? 'text-gray-400' : 'text-gray-600'

  const scenarios: Array<{ title: string; causes: string[]; fixes: string[] }> = [
    {
      title: 'Translations return keys instead of text',
      causes: [
        'i18n integration not enabled in effective config',
        'catalog directory missing or empty',
        'key namespace mismatch (messages.welcome vs welcome)',
      ],
      fixes: [
        'run aq i18n inspect and aq i18n check to confirm runtime config and files',
        'verify request.state["i18n"] and request.state["locale"] are present in handlers',
        'verify locale files and key paths match call sites',
      ],
    },
    {
      title: 'Wrong locale selected for requests',
      causes: [
        'resolver_order does not reflect intended precedence',
        'candidate locale is not in available_locales',
        'header resolver short-circuits before expected overrides',
      ],
      fixes: [
        'set resolver_order explicitly and keep it stable across environments',
        'normalize and validate locale sources against available_locales',
        'move header later if query/cookie/session overrides should win',
      ],
    },
    {
      title: 'Template output uses default locale unexpectedly',
      causes: [
        'request_locale global is not set in template rendering path',
        'helper calls do not pass explicit locale in edge rendering flows',
      ],
      fixes: [
        'set env.globals["request_locale"] from request.state locale before rendering',
        'pass locale= explicitly in critical template helper calls',
      ],
    },
    {
      title: 'YAML locale files are ignored',
      causes: [
        'service boot path uses FileCatalog default extension set in non-crous mode',
      ],
      fixes: [
        'prefer JSON catalog files in standard boot paths',
        'or build a custom catalog with explicit extension handling when needed',
      ],
    },
    {
      title: 'Intermittent locale mix-up with custom lazy usage',
      causes: [
        'custom middleware sets lazy context without guaranteed cleanup',
      ],
      fixes: [
        'always pair set_lazy_context and clear_lazy_context in try/finally',
        'prefer default I18nMiddleware where possible',
      ],
    },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <LifeBuoy className="w-4 h-4" />
          i18n / Troubleshooting
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Troubleshooting i18n
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${subtle}`}>
          Symptom-driven diagnostics for the most common i18n runtime issues.
          Start with config visibility, then validate resolver behavior, then verify catalog content.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Diagnostic Baseline</h2>
        <CodeBlock language="bash" filename="Terminal">{`aq i18n inspect
aq i18n check
aq i18n coverage --verbose`}</CodeBlock>
        <CodeBlock language="python" filename="handler_probe.py">{`@GET("/debug/i18n")
async def debug_i18n(self, ctx: RequestCtx):
    state = ctx.request.state
    return {
        "has_i18n": "i18n" in state,
        "locale": state.get("locale"),
        "available_locales": state["i18n"].available_locales() if "i18n" in state else [],
    }
`}</CodeBlock>
      </section>

      {scenarios.map((scenario, i) => (
        <section className="mb-16" key={i}>
          <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>{scenario.title}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className={box}>
              <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Likely Causes</h3>
              <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
                {scenario.causes.map((cause, idx) => (
                  <li key={idx}>{cause}</li>
                ))}
              </ul>
            </div>
            <div className={box}>
              <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Recommended Fixes</h3>
              <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
                {scenario.fixes.map((fix, idx) => (
                  <li key={idx}>{fix}</li>
                ))}
              </ul>
            </div>
          </div>
        </section>
      ))}

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Operational Guardrails</h2>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>Keep one canonical locale key naming convention across templates and controllers.</li>
            <li>Run extraction and coverage checks in CI to prevent silent key drift.</li>
            <li>Smoke test representative keys for each supported locale during startup validation.</li>
            <li>Avoid implicit defaults for resolver order in production; configure it explicitly.</li>
          </ul>
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'i18n Edge Cases', link: '/docs/i18n/edge-cases' },
          { text: 'i18n Configuration', link: '/docs/i18n/configuration' },
          { text: 'i18n CLI Reference', link: '/docs/i18n/cli' },
          { text: 'i18n API Reference', link: '/docs/i18n/api-reference' },
        ]}
      />
    </div>
  )
}
