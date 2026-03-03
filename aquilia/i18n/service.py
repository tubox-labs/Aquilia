"""
I18n Service — Central orchestrator for all translation operations.

The ``I18nService`` is the single entry point for:
- Translating keys with fallback chains
- Plural-aware translations
- Parameterized message formatting
- Locale validation and normalization
- Missing-key strategy enforcement

It composes a ``TranslationCatalog``, the ``MessageFormatter``, and the
plural rule engine into one cohesive API.

Configuration is expressed via ``I18nConfig`` which maps 1-to-1 with
``Integration.i18n()`` and ``ConfigLoader.get_i18n_config()``.

Example::

    config = I18nConfig(
        default_locale="en",
        available_locales=["en", "fr", "de", "ja"],
        fallback_locale="en",
        catalog_dirs=["locales"],
    )
    service = create_i18n_service(config)

    # Simple translation
    service.t("messages.welcome", locale="fr")  # "Bienvenue"

    # Plural-aware
    service.tn("items.count", count=5, locale="en")  # "5 items"

    # Parameterized
    service.t("greetings.hello", locale="en", name="World")  # "Hello, World!"
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from .catalog import FileCatalog, MemoryCatalog, MergedCatalog, TranslationCatalog
from .formatter import MessageFormatter
from .locale import Locale, negotiate_locale, normalize_locale, parse_locale
from .plural import PluralCategory, select_plural

logger = logging.getLogger("aquilia.i18n.service")


class MissingKeyStrategy(str, Enum):
    """What to do when a translation key is not found."""

    RETURN_KEY = "return_key"          # Return the dotted key as-is
    RETURN_EMPTY = "return_empty"      # Return empty string
    RETURN_DEFAULT = "return_default"  # Return the ``default`` argument
    RAISE = "raise"                    # Raise MissingTranslationFault
    LOG_AND_KEY = "log_and_key"        # Log a warning and return the key


@dataclass
class I18nConfig:
    """
    Configuration for the i18n service.

    Maps 1-to-1 with the dict returned by ``Integration.i18n()`` and
    ``ConfigLoader.get_i18n_config()``.
    """

    enabled: bool = True

    # Locale settings
    default_locale: str = "en"
    available_locales: List[str] = field(default_factory=lambda: ["en"])
    fallback_locale: str = "en"

    # Catalog settings
    catalog_dirs: List[str] = field(default_factory=lambda: ["locales"])
    catalog_format: str = "json"  # "json" or "yaml"

    # Behaviour
    missing_key_strategy: str = "log_and_key"
    auto_reload: bool = False  # Hot-reload catalogs on file change

    # Middleware settings
    auto_detect: bool = True  # Auto-detect locale from Accept-Language
    cookie_name: str = "aq_locale"
    query_param: str = "lang"
    path_prefix: bool = False  # /en/about, /fr/about

    # Resolver chain order
    resolver_order: List[str] = field(
        default_factory=lambda: ["query", "cookie", "header"]
    )

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "I18nConfig":
        """Create config from a dictionary (e.g. from ConfigLoader)."""
        return cls(
            enabled=data.get("enabled", True),
            default_locale=data.get("default_locale", "en"),
            available_locales=data.get("available_locales", ["en"]),
            fallback_locale=data.get("fallback_locale", "en"),
            catalog_dirs=data.get("catalog_dirs", ["locales"]),
            catalog_format=data.get("catalog_format", "json"),
            missing_key_strategy=data.get("missing_key_strategy", "log_and_key"),
            auto_reload=data.get("auto_reload", False),
            auto_detect=data.get("auto_detect", True),
            cookie_name=data.get("cookie_name", "aq_locale"),
            query_param=data.get("query_param", "lang"),
            path_prefix=data.get("path_prefix", False),
            resolver_order=data.get("resolver_order", ["query", "cookie", "header"]),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for ConfigLoader round-tripping."""
        return {
            "enabled": self.enabled,
            "default_locale": self.default_locale,
            "available_locales": list(self.available_locales),
            "fallback_locale": self.fallback_locale,
            "catalog_dirs": list(self.catalog_dirs),
            "catalog_format": self.catalog_format,
            "missing_key_strategy": self.missing_key_strategy,
            "auto_reload": self.auto_reload,
            "auto_detect": self.auto_detect,
            "cookie_name": self.cookie_name,
            "query_param": self.query_param,
            "path_prefix": self.path_prefix,
            "resolver_order": list(self.resolver_order),
        }


class I18nService:
    """
    Central i18n orchestrator.

    Thread-safe, composable, and designed for request-scoped locale
    resolution. Typically created once at startup and shared across
    the application via DI.

    Args:
        config: I18nConfig instance
        catalog: Pre-built catalog (optional — will auto-build from config if None)

    Attributes:
        config: Active I18nConfig
        catalog: Active TranslationCatalog
        formatter: MessageFormatter instance
    """

    def __init__(
        self,
        config: I18nConfig,
        catalog: Optional[TranslationCatalog] = None,
    ):
        self.config = config
        self.formatter = MessageFormatter(config.default_locale)
        self._missing_strategy = MissingKeyStrategy(config.missing_key_strategy)

        # Build catalog if not provided
        if catalog is not None:
            self.catalog = catalog
        else:
            self.catalog = self._build_catalog()

        logger.info(
            "I18nService initialized — default=%s available=%s fallback=%s",
            config.default_locale,
            config.available_locales,
            config.fallback_locale,
        )

    # ── Public API ───────────────────────────────────────────────────

    def t(
        self,
        key: str,
        *,
        locale: Optional[str] = None,
        default: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Translate a key.

        Resolves the key through the catalog's fallback chain and
        optionally formats the result with named arguments.

        Args:
            key: Dot-notated translation key (e.g. ``"messages.welcome"``)
            locale: Target locale (defaults to ``config.default_locale``)
            default: Fallback if key not found (overrides strategy)
            **kwargs: Named arguments for message interpolation

        Returns:
            Translated and formatted string
        """
        loc = locale or self.config.default_locale
        result = self._resolve(key, loc, default=default)

        if kwargs and result:
            result = self.formatter.format(result, locale=loc, **kwargs)

        return result

    def tn(
        self,
        key: str,
        count: Union[int, float],
        *,
        locale: Optional[str] = None,
        default: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Translate a key with plural selection.

        Selects the correct plural form based on CLDR rules for the locale.

        Args:
            key: Translation key pointing to a plural dict or singular string
            count: The count for plural selection
            locale: Target locale
            default: Fallback
            **kwargs: Additional interpolation arguments

        Returns:
            Pluralized, formatted string
        """
        loc = locale or self.config.default_locale
        lang = loc.split("-")[0]
        category = select_plural(lang, count)

        # Try plural lookup first
        result = self.catalog.get_plural(key, loc, category, default=None)

        if result is None:
            # Fall back to non-plural lookup
            result = self._resolve(key, loc, default=default)

        if result is None:
            return self._handle_missing(key, loc, default)

        # Always inject count into kwargs for # substitution
        kwargs["count"] = count
        result = self.formatter.format(result, locale=loc, **kwargs)
        return result

    def tp(
        self,
        key: str,
        *,
        locale: Optional[str] = None,
        default: Optional[str] = None,
        **kwargs: Any,
    ) -> str:
        """
        Translate with explicit parameterized formatting.

        Alias for ``t()`` — exists for API symmetry with template helpers
        (``_p()``).
        """
        return self.t(key, locale=locale, default=default, **kwargs)

    def has(self, key: str, locale: Optional[str] = None) -> bool:
        """Check if a key exists for the given locale."""
        loc = locale or self.config.default_locale
        return self.catalog.has(key, loc)

    def available_locales(self) -> List[str]:
        """Return the list of configured available locales."""
        return list(self.config.available_locales)

    def is_available(self, locale: str) -> bool:
        """Check if a locale is in the available list."""
        normalized = normalize_locale(locale) or locale
        return normalized in self.config.available_locales or locale in self.config.available_locales

    def negotiate(self, accept_language: str) -> str:
        """
        Negotiate locale from an Accept-Language header.

        Args:
            accept_language: Raw Accept-Language header value

        Returns:
            Best matching locale tag, or the default locale
        """
        return negotiate_locale(
            accept_language,
            self.config.available_locales,
            self.config.default_locale,
        )

    def locale(self, tag: Optional[str] = None) -> Locale:
        """
        Get a ``Locale`` object for the given tag.

        Args:
            tag: BCP 47 tag (defaults to ``config.default_locale``)

        Returns:
            Parsed ``Locale`` dataclass
        """
        tag = tag or self.config.default_locale
        parsed = parse_locale(tag)
        if parsed is None:
            return parse_locale(self.config.default_locale) or Locale(language="en")
        return parsed

    def reload_catalogs(self) -> None:
        """Force reload all file-based catalogs."""
        self.catalog = self._build_catalog()
        logger.info("I18n catalogs reloaded")

    # ── Internal ─────────────────────────────────────────────────────

    def _resolve(
        self,
        key: str,
        locale: str,
        *,
        default: Optional[str] = None,
    ) -> str:
        """Resolve a key through the catalog with locale fallback chain."""
        # Try the exact locale
        result = self.catalog.get(key, locale)
        if result is not None:
            return result

        # Try fallback chain: fr-CA → fr → fallback_locale
        parsed = parse_locale(locale)
        if parsed:
            for tag in parsed.fallback_chain:
                if tag == locale:
                    continue  # Already tried
                result = self.catalog.get(key, tag)
                if result is not None:
                    return result

        # Try the fallback locale
        if locale != self.config.fallback_locale:
            result = self.catalog.get(key, self.config.fallback_locale)
            if result is not None:
                return result

        return self._handle_missing(key, locale, default)

    def _handle_missing(
        self,
        key: str,
        locale: str,
        default: Optional[str] = None,
    ) -> str:
        """Apply missing key strategy."""
        if default is not None:
            return default

        strategy = self._missing_strategy

        if strategy == MissingKeyStrategy.RETURN_KEY:
            return key
        elif strategy == MissingKeyStrategy.RETURN_EMPTY:
            return ""
        elif strategy == MissingKeyStrategy.RETURN_DEFAULT:
            return default or key
        elif strategy == MissingKeyStrategy.RAISE:
            from .faults import MissingTranslationFault
            raise MissingTranslationFault(key, locale)
        elif strategy == MissingKeyStrategy.LOG_AND_KEY:
            logger.warning("Missing translation: key='%s' locale='%s'", key, locale)
            return key

        return key

    def _build_catalog(self) -> TranslationCatalog:
        """Build a catalog from the config's catalog_dirs."""
        catalogs: list[TranslationCatalog] = []

        for catalog_dir in self.config.catalog_dirs:
            path = Path(catalog_dir)
            if path.exists() and path.is_dir():
                catalogs.append(FileCatalog(path))
            else:
                logger.debug("Catalog directory not found: %s", catalog_dir)

        if not catalogs:
            logger.warning(
                "No i18n catalog directories found (%s) — using empty catalog",
                self.config.catalog_dirs,
            )
            return MemoryCatalog({})

        if len(catalogs) == 1:
            return catalogs[0]

        return MergedCatalog(catalogs)


def create_i18n_service(
    config: Optional[Union[I18nConfig, Dict[str, Any]]] = None,
    catalog: Optional[TranslationCatalog] = None,
) -> I18nService:
    """
    Factory function for creating an ``I18nService``.

    Accepts either an ``I18nConfig`` object or a raw dict
    (as returned by ``ConfigLoader.get_i18n_config()``).

    Args:
        config: Configuration (dict or I18nConfig)
        catalog: Pre-built catalog (optional)

    Returns:
        Configured ``I18nService`` instance
    """
    if config is None:
        cfg = I18nConfig()
    elif isinstance(config, dict):
        cfg = I18nConfig.from_dict(config)
    else:
        cfg = config

    return I18nService(cfg, catalog=catalog)
