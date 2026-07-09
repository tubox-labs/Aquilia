import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { LifeBuoy } from 'lucide-react'

export function I18nTroubleshooting() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderSubtle = isDark ? 'border-white/5' : 'border-gray-100'

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
        'move header resolver later if query/cookie/session overrides should win',
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
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Symptom-driven diagnostics for the most common i18n runtime issues.
          Start with config visibility, then validate resolver behavior, then verify catalog content.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Diagnostic Baseline</h2>
        <CodeBlock language="bash" filename="Terminal" highlightLines={[1, 2]}>{`aq i18n inspect
aq i18n check
aq i18n coverage --verbose`}</CodeBlock>
        <CodeBlock language="python" filename="handler_probe.py" highlightLines={[3, 4]}>{`@GET("/debug/i18n")
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
          <div className="space-y-6">
            <div>
              <h3 className={`font-mono text-sm font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Likely Causes</h3>
              <ul className={`list-disc pl-6 space-y-1 text-sm ${textMuted}`}>
                {scenario.causes.map((cause, idx) => (
                  <li key={idx}>{cause}</li>
                ))}
              </ul>
            </div>
            <div>
              <h3 className={`font-mono text-sm font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Recommended Fixes</h3>
              <ul className={`list-disc pl-6 space-y-1 text-sm ${textMuted}`}>
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
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 space-y-2">
          <p>• Keep one canonical locale key naming convention across templates and controllers.</p>
          <p>• Run extraction and coverage checks in CI to prevent silent key drift.</p>
          <p>• Smoke test representative keys for each supported locale during startup validation.</p>
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
