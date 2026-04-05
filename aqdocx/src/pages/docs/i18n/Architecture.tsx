import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Network } from 'lucide-react'

export function I18nArchitecture() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const box = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const subtle = isDark ? 'text-gray-400' : 'text-gray-600'

  const components: Array<[string, string, string]> = [
    ['Locale model', 'aquilia/i18n/locale.py', 'BCP 47 parsing, normalization, fallback chain, and negotiation.'],
    ['Plural rules', 'aquilia/i18n/plural.py', 'CLDR category selection for language-specific plural logic.'],
    ['Catalogs', 'aquilia/i18n/catalog.py', 'Memory, file, CROUS, namespaced, and merged translation backends.'],
    ['Formatter', 'aquilia/i18n/formatter.py', 'Message interpolation plus number/date/currency/percent helpers.'],
    ['Service', 'aquilia/i18n/service.py', 'Translation API, fallback chain, missing-key strategy, and catalog build.'],
    ['Middleware', 'aquilia/i18n/middleware.py', 'Resolver chain execution and request state injection.'],
    ['Template integration', 'aquilia/i18n/template_integration.py', 'Registers globals and filters for translation and formatting.'],
    ['DI integration', 'aquilia/i18n/di_integration.py', 'Registers app and optional request-scoped i18n providers.'],
    ['CLI', 'aquilia/cli/commands/i18n.py', 'Catalog bootstrap, extraction, coverage, and compilation operations.'],
  ]

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Network className="w-4 h-4" />
          i18n / Architecture
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            i18n Runtime Architecture
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${subtle}`}>
          Aquilia i18n bootstraps during server startup and then runs as a request-aware translation pipeline.
          The architecture combines config, catalog loading, locale resolution, formatting, and fault-aware lookup.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Boot Sequence</h2>
        <CodeBlock language="python" filename="aquilia/server.py::_setup_i18n">{`# 1) Load merged runtime config
raw_i18n = config_loader.get_i18n_config()

# 2) Convert to typed config
cfg = I18nConfig.from_dict(raw_i18n)

# 3) Build i18n service + catalog backend
service = create_i18n_service(cfg)

# 4) Register app-scoped DI values
register_i18n_providers(container, service, cfg)

# 5) Build locale resolver chain
resolver = build_resolver(cfg)

# 6) Add request middleware
middleware_stack.add(I18nMiddleware(service, resolver), priority=24)

# 7) Register template globals when env exists
register_i18n_template_globals(template_env, service)
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Subsystem Map</h2>
        <div className={box}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={isDark ? 'text-gray-400' : 'text-gray-500'}>
                  <th className="text-left pb-3 font-semibold">Component</th>
                  <th className="text-left pb-3 font-semibold">Location</th>
                  <th className="text-left pb-3 font-semibold">Role</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                {components.map(([name, file, role], i) => (
                  <tr key={i} className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-2 font-mono text-aquilia-500 text-xs pr-4">{name}</td>
                    <td className="py-2 font-mono text-xs pr-4">{file}</td>
                    <td className="py-2 text-xs">{role}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Translation Lookup Pipeline</h2>
        <CodeBlock language="python" filename="aquilia/i18n/service.py::I18nService._resolve">{`# t(key, locale) lookup order
1. catalog.get(key, exact_locale)
2. locale fallback chain (for example fr-CA -> fr)
3. catalog.get(key, fallback_locale)
4. missing-key strategy (_handle_missing)

# tn(key, count, locale) adds plural selection
category = select_plural(lang, count)
value = catalog.get_plural(key, locale, category)
if not value:
    value = _resolve(key, locale)
value = formatter.format(value, locale=locale, count=count, **kwargs)
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Locale Resolution Pipeline</h2>
        <CodeBlock language="python" filename="aquilia/i18n/middleware.py::I18nMiddleware.__call__">{`locale = config.default_locale

resolved = chain_resolver.resolve(request)
if resolved and service.is_available(resolved):
    locale = resolved

request.state["locale"] = locale
request.state["locale_obj"] = parse_locale(locale)
request.state["i18n"] = service

set_lazy_context(service, locale)
try:
    return await next_handler(request, ctx)
finally:
    clear_lazy_context()
`}</CodeBlock>
        <div className={box}>
          <p className={`text-sm ${subtle}`}>
            Resolver order is fully configuration-driven through resolver_order. ChainLocaleResolver is fail-soft and
            continues when individual resolvers throw.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Catalog Build Strategy</h2>
        <CodeBlock language="python" filename="aquilia/i18n/service.py::_build_catalog">{`if config.catalog_format == "crous":
    backend = CrousCatalog([catalog_dir])
else:
    backend = FileCatalog([catalog_dir])

if multiple_dirs:
    catalog = MergedCatalog([backend1, backend2, ...])
`}</CodeBlock>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>CrousCatalog can read CROUS artifacts and JSON/YAML fallback sources.</li>
            <li>Non-crous service boot path uses FileCatalog defaults, which are JSON-focused by default.</li>
            <li>When no catalog directory exists, service falls back to empty MemoryCatalog with warning log.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Boundaries and Contracts</h2>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>i18n owns translation lookup, not identity or authorization decisions.</li>
            <li>i18n may consume request/session hints for locale resolution but does not persist user preference itself.</li>
            <li>controllers and templates should treat I18nService as the canonical translation API.</li>
            <li>lazy translation context is request/task-local and cleaned in middleware finally blocks.</li>
          </ul>
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'i18n Configuration', link: '/docs/i18n/configuration' },
          { text: 'i18n Integration', link: '/docs/i18n/integration' },
          { text: 'i18n API Reference', link: '/docs/i18n/api-reference' },
          { text: 'i18n Edge Cases', link: '/docs/i18n/edge-cases' },
        ]}
      />
    </div>
  )
}
