"""
I18nIntegration — typed internationalization configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class I18nIntegration:
    """
    Typed i18n (internationalization) configuration.

    Example::

        I18nIntegration(
            default_locale="en",
            available_locales=["en", "fr", "de"],
        )
    """

    _integration_type: str = field(default="i18n", init=False, repr=False)

    default_locale: str = "en"
    available_locales: list[str] = field(default_factory=lambda: ["en"])
    fallback_locale: str = "en"
    catalog_dirs: list[str] = field(default_factory=lambda: ["locales"])
    catalog_format: str = "json"
    missing_key_strategy: str = "log_and_key"
    auto_reload: bool = False
    auto_detect: bool = True
    cookie_name: str = "aq_locale"
    query_param: str = "lang"
    path_prefix: bool = False
    resolver_order: list[str] = field(default_factory=lambda: ["query", "cookie", "header"])
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "_integration_type": "i18n",
            "enabled": self.enabled,
            "default_locale": self.default_locale,
            "available_locales": self.available_locales,
            "fallback_locale": self.fallback_locale,
            "catalog_dirs": self.catalog_dirs,
            "catalog_format": self.catalog_format,
            "missing_key_strategy": self.missing_key_strategy,
            "auto_reload": self.auto_reload,
            "auto_detect": self.auto_detect,
            "cookie_name": self.cookie_name,
            "query_param": self.query_param,
            "path_prefix": self.path_prefix,
            "resolver_order": self.resolver_order,
        }
