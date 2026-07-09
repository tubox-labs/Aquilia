import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { AlertTriangle } from 'lucide-react'

export function I18nEdgeCases() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderSubtle = isDark ? 'border-white/5' : 'border-gray-100'

  const validated: string[] = [
    'Deep dotted keys resolve correctly (for example a.b.c.d).',
    'Numeric translation values are returned as strings.',
    'Empty string translations are valid values, not implicit misses.',
    'Unicode content is preserved across memory and SURP-backed catalogs.',
    'parse_accept_language clamps q values into the 0..1 range.',
    'Plural edges are validated for complex languages such as Russian boundaries (11-14, 21, etc.).',
    'English ordinal output handles teen suffix exceptions (11th, 12th, 13th).',
    'Lazy context is task-local with ContextVar usage and does not bleed across concurrent tasks.',
  ]

  const limitations: string[] = [
    'Template locale resolution reads env.globals["request_locale"] first; automatic setting can depend on render path.',
    'register_i18n_request_providers exists but is not auto-invoked by default server middleware wiring.',
    'auto_detect, path_prefix, and auto_reload are currently intent/config fields with limited direct runtime branching.',
    'Header resolver comments and real behavior can diverge in override expectations.',
    'Service non-surp catalog build path defaults to FileCatalog JSON extensions unless customized.',
    'Fault usage is not fully uniform across all invalid-locale branches.',
    'negotiate_locale exception handling can be narrower than parser fault surface in malformed cases.',
    'Default values differ across config entry points and can surprise manual constructions.',
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <AlertTriangle className="w-4 h-4" />
          i18n / Edge Cases
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Edge Cases and Limitations
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          This page captures behavior verified by tests plus practical implementation gaps that matter in production.
          Use it as a deployment hardening checklist.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Validated Behaviors</h2>
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 space-y-2">
          {validated.map((item, i) => (
            <p key={i}>• {item}</p>
          ))}
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Current Gaps and Caveats</h2>
        <div className="border-l-2 border-amber-500/30 pl-4 py-1 text-sm text-zinc-500 space-y-2">
          {limitations.map((item, i) => (
            <p key={i}>• {item}</p>
          ))}
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Recommended Mitigations</h2>
        <CodeBlock language="python" filename="hardening_checklist.py" highlightLines={[2, 8, 14]}>{`# 1) Keep resolver order explicit in production config
Integration.i18n(resolver_order=["query", "cookie", "session", "header"])

# 2) Prefer request.state locale in controllers
locale = request.state.get("locale", "en")

# 3) Pair lazy context set/clear in custom middleware via try/finally
from aquilia.i18n import set_lazy_context, clear_lazy_context
set_lazy_context(service, locale)
try:
    # Handle request
    pass
finally:
    clear_lazy_context()
`}</CodeBlock>
      </section>

      <NextSteps
        items={[
          { text: 'i18n Troubleshooting', link: '/docs/i18n/troubleshooting' },
          { text: 'i18n Configuration', link: '/docs/i18n/configuration' },
          { text: 'i18n Integration', link: '/docs/i18n/integration' },
          { text: 'i18n API Reference', link: '/docs/i18n/api-reference' },
        ]}
      />
    </div>
  )
}
