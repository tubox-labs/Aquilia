import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { BookOpen } from 'lucide-react'

export function I18nAPIReference() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderSubtle = isDark ? 'border-white/5' : 'border-gray-100'

  const localeSymbols: Array<[string, string]> = [
    ['Locale', 'BCP 47 locale dataclass with tag, language_tag, and fallback_chain helpers.'],
    ['parse_locale(tag)', 'Parse and validate locale tags.'],
    ['normalize_locale(tag)', 'Normalize locale string or return None if invalid.'],
    ['match_locale(requested, available)', 'Find the best available Locale match.'],
    ['parse_accept_language(header)', 'Parse weighted Accept-Language headers.'],
    ['negotiate_locale(header, available, default)', 'Negotiate the best locale from request headers.'],
    ['LOCALE_PATTERN', 'Regex pattern used for BCP 47 validation.'],
  ]

  const catalogSymbols: Array<[string, string]> = [
    ['TranslationCatalog', 'Abstract catalog contract describing key and locale listings.'],
    ['MemoryCatalog', 'In-memory nested dictionary catalog.'],
    ['FileCatalog', 'Filesystem catalog backend supporting JSON/YAML.'],
    ['SurpCatalog', 'SURP-first binary catalog backend.'],
    ['NamespacedCatalog', 'Prefixes catalog keys by namespace.'],
    ['MergedCatalog', 'Layer multiple catalogs in ordered lookup sequence.'],
    ['has_surp()', 'Returns whether optional surp package is importable.'],
  ]

  const formatterSymbols: Array<[string, string]> = [
    ['MessageFormatter', 'Formatter class used by service for ICU-like string interpolation.'],
    ['format_message', 'Format pattern with placeholder behavior.'],
    ['format_number', 'Locale-aware number formatting.'],
    ['format_decimal', 'Decimal formatting helper.'],
    ['format_percent', 'Percent formatting helper.'],
    ['format_currency', 'Currency formatting helper with symbol and locale conventions.'],
    ['format_ordinal', 'Ordinal helper.'],
    ['format_date', 'Date formatting helper.'],
    ['format_time', 'Time formatting helper.'],
    ['format_datetime', 'Date+time combined formatter.'],
  ]

  const serviceSymbols: Array<[string, string]> = [
    ['MissingKeyStrategy', 'Enum with return_key, return_empty, return_default, raise, log_and_key.'],
    ['I18nConfig', 'Typed i18n configuration model.'],
    ['I18nService.t', 'Translate single key with fallback chain and formatting kwargs.'],
    ['I18nService.tn', 'Plural-aware translation path with count injection.'],
    ['I18nService.tp', 'Parameterized translation alias.'],
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
      <div className="overflow-x-auto">
        <table className="w-full text-sm text-left border-collapse">
          <thead>
            <tr className={`border-b ${borderSubtle} ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              <th className="pb-3 font-semibold pr-4">Symbol</th>
              <th className="pb-3 font-semibold">Description</th>
            </tr>
          </thead>
          <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
            {items.map(([name, desc], i) => (
              <tr key={i} className={`border-b ${borderSubtle} hover:bg-aquilia-50/[0.02]`}>
                <td className="py-2.5 font-mono text-aquilia-500 text-xs pr-4">
                  {name.startsWith('I18nService') ? (
                    name
                  ) : (
                    <DocTerm id={`i18n.${name.split('(')[0].split(' / ')[0]}`}>{name}</DocTerm>
                  )}
                </td>
                <td className="py-2.5 text-xs">{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
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
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Module-level symbol map for Aquilia i18n including locale utilities, catalog backends,
          formatting surface, runtime middleware, template wiring, DI hooks, and fault types.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Top-Level Exports</h2>
        <CodeBlock language="python" filename="aquilia/i18n/__init__.py" highlightLines={[2, 3, 5, 6]}>{`from aquilia.i18n import (
    Locale, parse_locale, normalize_locale, parse_accept_language, negotiate_locale,
    TranslationCatalog, MemoryCatalog, FileCatalog, SurpCatalog, NamespacedCatalog, MergedCatalog,
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
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 space-y-2">
          <p>• <code className="text-aquilia-500">parse_locale</code> validates and normalizes locale tags and may raise config-domain validation faults.</p>
          <p>• <DocTerm id="i18n.I18nService">I18nService.t</DocTerm>/tn can raise MissingTranslationFault when missing_key_strategy is set to raise.</p>
          <p>• <DocTerm id="i18n.I18nMiddleware">I18nMiddleware</DocTerm> writes resolved locale information into the request state, and cleans up ContextVars in a finally block.</p>
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
