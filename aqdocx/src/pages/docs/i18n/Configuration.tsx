import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Settings } from 'lucide-react'

export function I18nConfiguration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const box = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const subtle = isDark ? 'text-gray-400' : 'text-gray-600'

  const keys: Array<[string, string, string]> = [
    ['enabled', 'bool', 'Enable i18n boot wiring in AquiliaServer.'],
    ['default_locale', 'str', 'Default locale used when no resolver value is accepted.'],
    ['available_locales', 'list[str]', 'Allowed locale list for resolver and service checks.'],
    ['fallback_locale', 'str', 'Global fallback locale for lookup misses.'],
    ['catalog_dirs', 'list[str]', 'One or more locale roots (for example locales, modules/*/locales).'],
    ['catalog_format', 'str', 'Catalog preference: crous, json, or yaml metadata path.'],
    ['missing_key_strategy', 'str', 'return_key, return_empty, return_default, raise, or log_and_key.'],
    ['resolver_order', 'list[str]', 'Ordered resolver names: query, cookie, header, path, session.'],
    ['cookie_name', 'str', 'Cookie key for CookieLocaleResolver.'],
    ['query_param', 'str', 'Query key for QueryLocaleResolver.'],
    ['auto_reload', 'bool', 'Hot reload intent flag.'],
    ['auto_detect', 'bool', 'Auto-detection intent flag.'],
    ['path_prefix', 'bool', 'Path locale prefix intent flag.'],
  ]

  const defaults: Array<[string, string, string, string, string]> = [
    ['enabled', 'False', 'True', 'True', 'True'],
    ['catalog_format', 'crous', 'json', 'crous', 'json'],
    ['resolver_order', 'query,cookie,header', 'query,cookie,header', 'query,cookie,header', 'query,cookie,header'],
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Settings className="w-4 h-4" />
          i18n / Configuration
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            i18n Configuration
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${subtle}`}>
          i18n settings can be declared through workspace builders, typed integration objects, or raw runtime config.
          At server boot, all paths are normalized into I18nConfig.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Configuration Entry Points</h2>
        <CodeBlock language="python" filename="workspace.py">{`from aquilia.config_builders import Workspace, Integration
from aquilia.integrations.i18n import I18nIntegration

workspace = (
    Workspace("myapp")
    # Builder API
    .integrate(
        Integration.i18n(
            enabled=True,
            default_locale="en",
            available_locales=["en", "fr", "de", "ja"],
            fallback_locale="en",
            catalog_dirs=["locales", "modules/auth/locales"],
            catalog_format="crous",
            missing_key_strategy="log_and_key",
            resolver_order=["query", "cookie", "session", "header"],
            cookie_name="aq_locale",
            query_param="lang",
        )
    )

    # Typed integration object
    .integrate(
        I18nIntegration(
            enabled=True,
            default_locale="en",
            available_locales=["en", "fr"],
            catalog_dirs=["locales"],
        )
    )
)
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Runtime Precedence</h2>
        <CodeBlock language="python" filename="config_resolution.py">{`# Effective flow
# 1) user config in i18n or integrations.i18n
# 2) merged with ConfigLoader.get_i18n_config defaults
# 3) converted by I18nConfig.from_dict
# 4) consumed by create_i18n_service
`}</CodeBlock>
        <div className={box}>
          <p className={`text-sm ${subtle}`}>
            If enabled is false after merge, server setup skips i18n service creation, resolver chain construction,
            middleware insertion, and template global registration.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Key Reference</h2>
        <div className={box}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={isDark ? 'text-gray-400' : 'text-gray-500'}>
                  <th className="text-left pb-3 font-semibold">Key</th>
                  <th className="text-left pb-3 font-semibold">Type</th>
                  <th className="text-left pb-3 font-semibold">Description</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                {keys.map(([key, type, desc], i) => (
                  <tr key={i} className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-2 font-mono text-aquilia-500 text-xs pr-4">{key}</td>
                    <td className="py-2 font-mono text-xs pr-4">{type}</td>
                    <td className="py-2 text-xs">{desc}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Default Value Matrix</h2>
        <div className={box}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={isDark ? 'text-gray-400' : 'text-gray-500'}>
                  <th className="text-left pb-3 font-semibold">Key</th>
                  <th className="text-left pb-3 font-semibold">ConfigLoader</th>
                  <th className="text-left pb-3 font-semibold">Integration.i18n</th>
                  <th className="text-left pb-3 font-semibold">I18nConfig dataclass</th>
                  <th className="text-left pb-3 font-semibold">from_dict fallback</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                {defaults.map(([key, loader, integration, dataclassDefault, fromDict], i) => (
                  <tr key={i} className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-2 font-mono text-aquilia-500 text-xs pr-4">{key}</td>
                    <td className="py-2 font-mono text-xs pr-4">{loader}</td>
                    <td className="py-2 font-mono text-xs pr-4">{integration}</td>
                    <td className="py-2 font-mono text-xs pr-4">{dataclassDefault}</td>
                    <td className="py-2 font-mono text-xs">{fromDict}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Missing-Key Strategies</h2>
        <CodeBlock language="python" filename="aquilia/i18n/service.py::MissingKeyStrategy">{`return_key     # returns the dotted key
return_empty   # returns ""
return_default # returns default argument if present, else key
raise          # raises MissingTranslationFault
log_and_key    # logs warning and returns key
`}</CodeBlock>
        <div className={box}>
          <p className={`text-sm ${subtle}`}>
            Passing default to t(...) or tn(...) bypasses strategy logic and returns your explicit default value.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Production Example</h2>
        <CodeBlock language="python" filename="workspace.py">{`Workspace("myapp").integrate(
    Integration.i18n(
        enabled=True,
        default_locale="en",
        available_locales=["en", "fr", "de", "ja"],
        fallback_locale="en",
        catalog_dirs=["locales", "modules/auth/locales"],
        catalog_format="crous",
        missing_key_strategy="log_and_key",
        resolver_order=["query", "cookie", "session", "header"],
        cookie_name="aq_locale",
        query_param="lang",
        auto_reload=False,
    )
)
`}</CodeBlock>
      </section>

      <NextSteps
        items={[
          { text: 'i18n Architecture', link: '/docs/i18n/architecture' },
          { text: 'i18n Integration', link: '/docs/i18n/integration' },
          { text: 'i18n CLI Reference', link: '/docs/i18n/cli' },
          { text: 'i18n Edge Cases', link: '/docs/i18n/edge-cases' },
        ]}
      />
    </div>
  )
}
