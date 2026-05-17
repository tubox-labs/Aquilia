from __future__ import annotations

from typing import Any

from aquilia.i18n import I18nConfig, I18nService, MemoryCatalog, negotiate_locale


TRANSLATIONS = {
    "en": {
        "messages": {
            "welcome": "Welcome, {name}!",
            "items": {"one": "{count} item", "other": "{count} items"},
            "checkout": "Checkout",
        }
    },
    "es": {
        "messages": {
            "welcome": "Bienvenido, {name}!",
            "items": {"one": "{count} articulo", "other": "{count} articulos"},
            "checkout": "Pagar",
        }
    },
    "fr": {
        "messages": {
            "welcome": "Bienvenue, {name}!",
            "items": {"one": "{count} article", "other": "{count} articles"},
            "checkout": "Paiement",
        }
    },
}


class ContentLocalizationService:
    def __init__(self, i18n: I18nService | None = None) -> None:
        config = I18nConfig(
            default_locale="en",
            available_locales=["en", "es", "fr"],
            fallback_locale="en",
            missing_key_strategy="return_key",
        )
        self.i18n = i18n or I18nService(config, MemoryCatalog(TRANSLATIONS))

    def landing_copy(self, *, accept_language: str = "", name: str = "World", count: int = 1) -> dict[str, Any]:
        locale = negotiate_locale(accept_language, self.i18n.config.available_locales, self.i18n.config.default_locale)
        return {
            "locale": locale,
            "welcome": self.i18n.t("messages.welcome", locale=locale, name=name),
            "items": self.i18n.tn("messages.items", count, locale=locale),
            "cta": self.i18n.t("messages.checkout", locale=locale),
        }

    def missing_key(self, key: str, locale: str = "en") -> str:
        return self.i18n.t(key, locale=locale)
