import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { BookOpen } from 'lucide-react'

export function I18nAPIReference() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const box = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const subtle = isDark ? 'text-gray-400' : 'text-gray-600'

  const localeSymbols: Array<[string, string]> = [
    ['Locale', 'BCP 47 locale dataclass with tag/language_tag/fallback_chain/matches helpers.'],
    ['parse_locale(tag)', 'Parse and validate locale tags.'],
    ['normalize_locale(tag)', 'Normalize locale string or return None if invalid.'],
    ['match_locale(requested, available)', 'Find best available Locale match.'],
    ['parse_accept_language(header)', 'Parse weighted Accept-Language values.'],
    ['negotiate_locale(header, available, default)', 'Negotiate best locale from request header values.'],
    ['LOCALE_PATTERN', 'Regex pattern used for BCP 47 validation shape.'],
  ]

  const catalogSymbols: Array<[string, string]> = [
    ['TranslationCatalog', 'Abstract catalog contract: get, get_plural, has, locales, keys.'],
    ['MemoryCatalog', 'In-memory nested dict backend with deep merge support.'],
    ['FileCatalog', 'Filesystem catalog backend (JSON-first by default).'],
    ['CrousCatalog', 'CROUS-first backend with JSON/YAML fallback and compile support.'],
    ['NamespacedCatalog', 'Prefixes keys by namespace for module isolation.'],
    ['MergedCatalog', 'Layer multiple catalogs in ordered lookup sequence.'],
    ['has_crous()', 'Returns whether optional crous package is importable.'],
  ]

  const formatterSymbols: Array<[string, string]> = [
    ['MessageFormatter', 'Formatter class used by service for interpolation and formatting.'],
    ['format_message', 'Format pattern with ICU-like placeholder behavior.'],
    ['format_number', 'Locale-aware number formatting.'],
    ['format_decimal', 'Decimal formatting helper.'],
    ['format_percent', 'Percent formatting helper.'],
    ['format_currency', 'Currency formatting helper with symbol and locale conventions.'],
    ['format_ordinal', 'Ordinal helper (language-sensitive where implemented).'],
    ['format_date', 'Date formatting helper by style.'],
    ['format_time', 'Time formatting helper by style.'],
    ['format_datetime', 'Date+time combined formatter.'],
  ]

  const serviceSymbols: Array<[string, string]> = [
    ['MissingKeyStrategy', 'Enum with return_key, return_empty, return_default, raise, log_and_key.'],
    ['I18nConfig', 'Typed i18n configuration model with from_dict/to_dict helpers.'],
    ['I18nService.t', 'Translate single key with fallback chain and optional formatting kwargs.'],
    ['I18nService.tn', 'Plural-aware translation path with count injection.'],
    ['I18nService.tp', 'Parameterized alias to t for API symmetry.'],
    ['I18nService.has', 'Check key availability for locale.'],
    ['I18nService.available_locales', 'Return configured locales list.'],
    ['I18nService.negotiate', 'Header locale negotiation helper.'],
    ['I18nService.locale', 'Return Locale object from tag/default locale.'],
    ['I18nService.reload_catalogs', 'Rebuild catalog stack from config.'],
    ['create_i18n_service', 'Factory accepting dict or I18nConfig.'],
  ]

  const runtimeSymbols: Array<[string, string]> = [
    ['LazyString / LazyPluralString', 'Deferred translation objects resolved at string-use time.'],
    ['lazy_t / lazy_tn', 'Lazy translation factories for module-level constants.'],
    ['set_lazy_context / clear_lazy_context', 'ContextVar-backed lazy context lifecycle hooks.'],
    ['LocaleResolver', 'Resolver abstract type for request locale extraction.'],
    ['HeaderLocaleResolver', 'Resolve locale from Accept-Language.'],
    ['CookieLocaleResolver', 'Resolve locale from cookie value.'],
    ['QueryLocaleResolver', 'Resolve locale from query param.'],
    ['PathLocaleResolver', 'Resolve locale from URL path prefix.'],
    ['SessionLocaleResolver', 'Resolve locale from request session data.'],
    ['ChainLocaleResolver', 'Ordered resolver composition with fail-soft behavior.'],
    ['I18nMiddleware', 'Injects locale, locale_obj, and i18n service into request state.'],
    ['build_resolver', 'Build resolver chain from config resolver_order.'],
  ]

  const integrationSymbols: Array<[string, string]> = [
    ['register_i18n_template_globals', 'Attach template globals/filters for translation and format helpers.'],
    ['I18nTemplateExtension', 'Template extension descriptor applying global/filter registration.'],
    ['register_i18n_providers', 'Register I18nService and I18nConfig in app DI container.'],
    ['register_i18n_request_providers', 'Optional request-scope locale registration helper.'],
    ['I18nFault', 'Base i18n fault type.'],
    ['MissingTranslationFault', 'Raised for missing keys with raise strategy.'],
    ['InvalidLocaleFault', 'Fault class for invalid locale contexts.'],
    ['CatalogLoadFault', 'Fault class for catalog loading failures.'],
    ['PluralRuleFault', 'Fault class for plural rule failures.'],
    ['I18nIntegration', 'Typed integration dataclass in aquilia/integrations/i18n.py.'],
  ]

  const renderTable = (title: string, items: Array<[string, string]>) => (
    <section className="mb-16" key={title}>
      <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>{title}</h2>
      <div className={box}>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'text-gray-400' : 'text-gray-500'}>
                <th className="text-left pb-3 font-semibold">Symbol</th>
                <th className="text-left pb-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
              {items.map(([name, desc], i) => (
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
  )

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <BookOpen className="w-4 h-4" />
          i18n / API Reference
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            i18n API Reference
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${subtle}`}>
          Module-level symbol map for Aquilia i18n including locale utilities, catalog backends,
          formatting surface, runtime middleware, template wiring, DI hooks, and fault types.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Top-Level Exports</h2>
        <CodeBlock language="python" filename="aquilia/i18n/__init__.py">{`from aquilia.i18n import (
    Locale, parse_locale, normalize_locale, parse_accept_language, negotiate_locale,
    TranslationCatalog, MemoryCatalog, FileCatalog, CrousCatalog, NamespacedCatalog, MergedCatalog,
    PluralCategory, get_plural_rule, select_plural,
    MessageFormatter, format_message, format_number, format_currency, format_date,
    I18nConfig, I18nService, create_i18n_service,
    LazyString, lazy_t, lazy_tn,
    I18nMiddleware, ChainLocaleResolver,
    register_i18n_template_globals, I18nTemplateExtension,
    register_i18n_providers,
    I18nFault, MissingTranslationFault,
)
`}</CodeBlock>
      </section>

      {renderTable('Locale APIs', localeSymbols)}
      {renderTable('Catalog APIs', catalogSymbols)}
      {renderTable('Formatter APIs', formatterSymbols)}
      {renderTable('Service APIs', serviceSymbols)}
      {renderTable('Runtime and Middleware APIs', runtimeSymbols)}
      {renderTable('Integration and Fault APIs', integrationSymbols)}

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Behavior Map</h2>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>parse_locale validates and normalizes locale tags and may raise config-domain validation faults.</li>
            <li>I18nService.t/tn can raise MissingTranslationFault when missing_key_strategy is raise.</li>
            <li>reload_catalogs rebuilds active catalog stack from current config and replaces service catalog reference.</li>
            <li>I18nMiddleware writes request state and guarantees lazy context cleanup in a finally block.</li>
            <li>register_i18n_providers mutates the DI container and is intentionally tolerant of container API variation.</li>
          </ul>
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'i18n Integration', link: '/docs/i18n/integration' },
          { text: 'i18n CLI Reference', link: '/docs/i18n/cli' },
          { text: 'i18n Edge Cases', link: '/docs/i18n/edge-cases' },
          { text: 'i18n Troubleshooting', link: '/docs/i18n/troubleshooting' },
        ]}
      />
    </div>
  )
}
