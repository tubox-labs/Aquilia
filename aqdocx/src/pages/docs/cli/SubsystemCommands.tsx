import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Stethoscope } from 'lucide-react'

export function CLISubsystemCommands() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = "mb-16 scroll-mt-24"
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`
  const listClass = "space-y-4 pl-5 list-disc"
  const itemClass = `text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`

  return (
    <div className="max-w-4xl mx-auto pb-20">
      {/* Header */}
      <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Stethoscope className="w-4 h-4" />
          CLI / Subsystem Commands
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Subsystem Diagnostics
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The Aquilia CLI provides sub-commands to diagnose, inspect, and flush resources for specific modules: Cache, Mail, and i18n Translations.
        </p>
      </div>

      {/* Cache Subsystem */}
      <section id="cache-subsystem" className={sectionClass}>
        <h2 className={h2Class}>aq cache</h2>
        <p className={pClass}>
          Commands to introspect active cache adapters and clear keys:
        </p>
        <ul className={listClass}>
          <li className={itemClass}><strong>aq cache status:</strong> Logs the current cache hits/misses statistics, configured backend (Redis, Memcached, SQLite, Memory), and pool size.</li>
          <li className={itemClass}><strong>aq cache keys:</strong> Lists active keys. Supports pattern-based glob matching (e.g. <code className="text-aquilia-500">aq cache keys "users:*"</code>).</li>
          <li className={itemClass}><strong>aq cache clear:</strong> Flushes all active keys or matching patterns.</li>
        </ul>
        <CodeBlock language="bash" filename="Terminal">{`# Clear cached data matching pattern
aq cache clear --pattern="products:*"`}</CodeBlock>
      </section>

      {/* Mail Subsystem */}
      <section id="mail-subsystem" className={sectionClass}>
        <h2 className={h2Class}>aq mail</h2>
        <p className={pClass}>
          Validates mail configurations and tests connections to SMTP servers:
        </p>
        <ul className={listClass}>
          <li className={itemClass}><strong>aq mail status:</strong> Displays the mail provider settings (SMTP, SendGrid, Mailgun) and verifies active authentication credentials.</li>
          <li className={itemClass}><strong>aq mail send:</strong> Dispatches a test email to verify correct connection routing.</li>
        </ul>
        <CodeBlock language="bash" filename="Terminal">{`# Send a diagnostic test email
aq mail send --to=admin@my-domain.com --subject="Test" --body="OK"`}</CodeBlock>
      </section>

      {/* i18n Translations Subsystem */}
      <section id="i18n-subsystem" className={sectionClass}>
        <h2 className={h2Class}>aq i18n</h2>
        <p className={pClass}>
          Coordinates localization translation catalogs, scanning files and compiling formats:
        </p>
        <ul className={listClass}>
          <li className={itemClass}><strong>aq i18n extract:</strong> Scans controller routes, Jinja templates, and validation schemas, extracting translatable strings into `.pot` templates.</li>
          <li className={itemClass}><strong>aq i18n compile:</strong> Compiles human-readable `.po` localization catalogs into binary `.mo` catalog mappings for fast lookup.</li>
        </ul>
        <CodeBlock language="bash" filename="Terminal">{`# Compile language catalogs
aq i18n compile`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
