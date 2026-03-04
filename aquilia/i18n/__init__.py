"""
AquilaI18n — Industry-grade Internationalization & Localization for Aquilia.

A production-ready, async-aware i18n system tightly integrated into every
layer of the Aquilia ecosystem:

- **BCP 47** locale tags with IANA subtag validation
- **CLDR-based** plural rules (zero / one / two / few / many / other)
- **ICU MessageFormat**-inspired interpolation with named arguments
- **Accept-Language** content-negotiation middleware
- **Request-scoped** locale via middleware → DI → controllers → templates
- **Catalog-based** translations from JSON, YAML, or Python dicts
- **Namespace isolation** per module (``users.welcome``, ``auth.errors.invalid``)
- **Fallback chains** (``fr-CA`` → ``fr`` → default locale)
- **Template integration** — ``_()`` / ``_n()`` / ``_p()`` / ``format_number()`` etc.
- **DI integration** — inject ``I18nService`` or ``Locale`` into controllers
- **Config builder** — ``Integration.i18n()`` + ``Workspace.i18n()``
- **CLI tooling** — ``aq i18n init`` / ``extract`` / ``compile`` / ``check``
- **Lazy strings** for module-level translation constants
- **Number / date / currency formatting** with locale rules

Architecture follows Aquilia conventions:
- Catalog files live in ``locales/`` at workspace root or per-module
- Each locale gets a directory: ``locales/en/``, ``locales/fr/``, etc.
- Translation files are namespaced JSON: ``locales/en/messages.json``
- Plural rules ship built-in for 200+ languages (CLDR v44 data)
- Zero external dependencies (no babel, no gettext)

Example::

    from aquilia import Controller, GET
    from aquilia.i18n import I18nService, Locale

    class GreetController(Controller):
        prefix = "/greet"

        def __init__(self, i18n: I18nService):
            self.i18n = i18n

        @GET("/")
        async def hello(self, ctx):
            locale = ctx.request.state.get("locale", "en")
            msg = self.i18n.t("messages.welcome", locale=locale, name="World")
            return {"message": msg}
"""

__version__ = "1.0.0"

from .locale import (
    Locale,
    parse_locale,
    normalize_locale,
    match_locale,
    parse_accept_language,
    negotiate_locale,
    LOCALE_PATTERN,
)

from .catalog import (
    TranslationCatalog,
    MemoryCatalog,
    FileCatalog,
    CrousCatalog,
    NamespacedCatalog,
    MergedCatalog,
    has_crous,
)

from .plural import (
    PluralCategory,
    PluralRule,
    get_plural_rule,
    select_plural,
    CLDR_PLURAL_RULES,
)

from .formatter import (
    MessageFormatter,
    format_message,
    format_number,
    format_currency,
    format_date,
    format_time,
    format_datetime,
    format_percent,
    format_decimal,
    format_ordinal,
)

from .service import (
    I18nService,
    I18nConfig,
    create_i18n_service,
)

from .lazy import (
    LazyString,
    lazy_t,
    lazy_tn,
)

from .middleware import (
    I18nMiddleware,
    LocaleResolver,
    HeaderLocaleResolver,
    CookieLocaleResolver,
    QueryLocaleResolver,
    PathLocaleResolver,
    SessionLocaleResolver,
    ChainLocaleResolver,
)

from .faults import (
    I18nFault,
    MissingTranslationFault,
    InvalidLocaleFault,
    CatalogLoadFault,
    PluralRuleFault,
)

from .template_integration import (
    register_i18n_template_globals,
    I18nTemplateExtension,
)

from .di_integration import (
    register_i18n_providers,
)

__all__ = [
    # Locale
    "Locale",
    "parse_locale",
    "normalize_locale",
    "match_locale",
    "parse_accept_language",
    "negotiate_locale",

    # Catalog
    "TranslationCatalog",
    "MemoryCatalog",
    "FileCatalog",
    "CrousCatalog",
    "NamespacedCatalog",
    "MergedCatalog",
    "has_crous",

    # Plural rules
    "PluralCategory",
    "PluralRule",
    "get_plural_rule",
    "select_plural",
    "CLDR_PLURAL_RULES",

    # Formatting
    "MessageFormatter",
    "format_message",
    "format_number",
    "format_currency",
    "format_date",
    "format_time",
    "format_datetime",
    "format_percent",
    "format_decimal",
    "format_ordinal",

    # Service
    "I18nService",
    "I18nConfig",
    "create_i18n_service",

    # Lazy strings
    "LazyString",
    "lazy_t",
    "lazy_tn",

    # Middleware
    "I18nMiddleware",
    "LocaleResolver",
    "HeaderLocaleResolver",
    "CookieLocaleResolver",
    "QueryLocaleResolver",
    "PathLocaleResolver",
    "SessionLocaleResolver",
    "ChainLocaleResolver",

    # Faults
    "I18nFault",
    "MissingTranslationFault",
    "InvalidLocaleFault",
    "CatalogLoadFault",
    "PluralRuleFault",

    # Template integration
    "register_i18n_template_globals",
    "I18nTemplateExtension",

    # DI integration
    "register_i18n_providers",
]
