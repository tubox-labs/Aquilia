import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Shield } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function TemplatesSecurity() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderMuted = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto px-4 py-2">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Shield className="w-4 h-4" />
          Templates / Security
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono">Template Security Sandbox</span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          AquilaTemplates enforces restricted sandboxing by default. The <DocTerm id="templates.TemplateSandbox">TemplateSandbox</DocTerm> class and its accompanying <DocTerm id="templates.TemplateSandbox">SandboxPolicy</DocTerm> prevent templates from executing arbitrary Python scripts or calling unauthorized object methods.
        </p>
      </div>

      {/* SandboxPolicy Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          SandboxPolicy Options
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          Define sandbox policies by initializing <DocTerm id="templates.TemplateSandbox">SandboxPolicy</DocTerm> with custom whitelists, or use the pre-configured classmethod presets:
        </p>
        <CodeBlock
          language="python"
          filename="security_policy.py"
          highlightLines={[4, 5, 8, 12, 13, 14]}
        >{`from aquilia.templates import SandboxPolicy, TemplateSandbox

# 1. Custom Whitelist Security Policy
policy = SandboxPolicy(
    allow_unsafe_filters=False,
    allow_unsafe_tests=False,
    allow_unsafe_globals=False,
    allowed_filters={"abs", "capitalize", "escape", "length"},
    allowed_tests={"defined", "undefined", "even", "odd"},
    allowed_globals={"range", "namespace", "csrf_token"},
    autoescape=True,
    autoescape_extensions=["html", "htm", "xml", "xhtml"],
    max_recursion_depth=50
)

sandbox = TemplateSandbox(policy=policy, immutable=True)`}</CodeBlock>
      </section>

      {/* Preset Policies */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Standard Policy Presets
        </h2>
        <div className="space-y-6">
          <div className="pl-4 border-l-2 border-aquilia-500/20">
            <h4 className={`text-sm font-semibold mb-1 font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
              SandboxPolicy.strict() (Default)
            </h4>
            <p className={`text-xs ${textMuted}`}>
              Blocks all unsafe actions, filters, tests, and globals. Allows only whitelisted operations. Perfect for production environments rendering user-submitted templates.
            </p>
          </div>
          <div className="pl-4 border-l-2 border-aquilia-500/20">
            <h4 className={`text-sm font-semibold mb-1 font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
              SandboxPolicy.permissive()
            </h4>
            <p className={`text-xs ${textMuted}`}>
              Expands the allowed filters and tests list (adding operations like tojson and xmlattr) to aid in diagnostic reporting and development-level debugging.
            </p>
          </div>
        </div>
      </section>

      {/* Security Whitelists */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Sandbox Whitelist References
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          The following standard features are whitelisted out-of-the-box by the default strict policy:
        </p>
        <div className="space-y-6">
          {[
            { category: 'Allowed Globals', items: 'range, dict, lipsum, cycler, joiner, namespace, url_for, static, media, csrf_token' },
            { category: 'Allowed Filters', items: 'abs, attr, default, escape, filesizeformat, first, int, float, join, last, length, map, max, min, replace, reverse, round, safe, select, slice, sort, string, trim, truncate, upper, lower, urlencode, format_date, format_currency, pluralize, sanitize_html' },
            { category: 'Allowed Tests', items: 'defined, undefined, boolean, callable, divisibleby, eq, ne, even, odd, false, true, ge, le, gt, lt, in, iterable, mapping, sequence, string, sameas' }
          ].map((item, i) => (
            <div key={i} className="py-4 border-b border-white/5 last:border-0">
              <span className={`font-semibold text-xs block mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.category}</span>
              <p className={`font-mono text-xs text-aquilia-400 leading-relaxed break-all`}>
                {item.items}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* Auto-Escaping & XSS */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Auto-Escaping & XSS Prevention
        </h2>
        <p className={`text-sm mb-4 ${textMuted}`}>
          To safeguard templates against Cross-Site Scripting (XSS), the environment automatically escapes standard variables matching the <code className="text-aquilia-400">autoescape_extensions</code> set:
        </p>
        <CodeBlock
          language="html"
          filename="templates/xss_prevention.html"
          highlightLines={[2, 5, 8]}
        >{`{# 1. Automatic Escaping (converts HTML characters to entities) #}
<p>{{ user.biography }}</p>

{# 2. Explicit Safe Escape (ONLY use for verified database outputs) #}
<p>{{ user.raw_html_bio | safe }}</p>

{# 3. Inline HTML Sanitizer Filter #}
<p>{{ user.untrusted_input | sanitize_html }}`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/templates/loaders" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Loaders
        </Link>
        <Link to="/docs/mail" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Mail <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'Mail Service Overview', link: '/docs/mail' },
          { text: 'Mail Templates & Syntax', link: '/docs/mail/templates' },
          { text: 'Developer Integration Guide', link: '/docs/developer-guide' },
        ]}
      />
    </div>
  )
}