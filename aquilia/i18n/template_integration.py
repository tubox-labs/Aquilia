"""
I18n Template Integration — Jinja2 globals, filters, and extensions.

Registers translation helpers into Aquilia's template engine so templates
can use i18n seamlessly::

    {{ _("messages.welcome") }}
    {{ _n("items.count", count=5) }}
    {{ _p("greetings.hello", name=user.name) }}
    {{ format_number(price, locale) }}
    {{ format_currency(amount, "USD", locale) }}
    {{ format_date(created_at, locale) }}

The helpers read the current locale from the template context (injected
by ``I18nMiddleware`` via ``request.state``).

Integration is automatic when i18n is enabled — the server wires it
into the template engine at startup.
"""

from __future__ import annotations

import logging
from datetime import date, datetime, time
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from jinja2 import Environment
    from .service import I18nService

logger = logging.getLogger("aquilia.i18n.templates")


def register_i18n_template_globals(
    env: "Environment",
    service: "I18nService",
) -> None:
    """
    Register i18n globals and filters on a Jinja2 Environment.

    This is called automatically by the server when i18n is enabled
    and a template engine is configured.

    After this call, templates have access to:

    **Globals:**
    - ``_(key, **kwargs)`` → translate
    - ``_n(key, count, **kwargs)`` → plural translate
    - ``_p(key, **kwargs)`` → parameterized translate (alias for ``_``)
    - ``gettext(key, **kwargs)`` → alias for ``_``
    - ``ngettext(key, count, **kwargs)`` → alias for ``_n``

    **Filters:**
    - ``|translate`` → ``{{ "messages.welcome"|translate }}``
    - ``|format_number`` → ``{{ 1234|format_number }}``
    - ``|format_currency(currency)`` → ``{{ price|format_currency("USD") }}``
    - ``|format_date`` → ``{{ created|format_date }}``
    - ``|format_time`` → ``{{ now|format_time }}``
    - ``|format_percent`` → ``{{ ratio|format_percent }}``

    Args:
        env: Jinja2 Environment instance
        service: I18nService instance
    """
    from .formatter import (
        format_currency,
        format_date,
        format_datetime,
        format_number,
        format_ordinal,
        format_percent,
        format_time,
    )

    # ── Globals ──────────────────────────────────────────────────────

    def _translate(key: str, **kwargs: Any) -> str:
        """Translate a key using the current request locale."""
        locale = kwargs.pop("locale", None) or _get_ctx_locale(env)
        return service.t(key, locale=locale, **kwargs)

    def _translate_plural(key: str, count: int | float = 0, **kwargs: Any) -> str:
        """Translate with plural selection."""
        locale = kwargs.pop("locale", None) or _get_ctx_locale(env)
        return service.tn(key, count, locale=locale, **kwargs)

    def _translate_param(key: str, **kwargs: Any) -> str:
        """Parameterized translate (alias for _)."""
        locale = kwargs.pop("locale", None) or _get_ctx_locale(env)
        return service.t(key, locale=locale, **kwargs)

    env.globals["_"] = _translate
    env.globals["_n"] = _translate_plural
    env.globals["_p"] = _translate_param
    env.globals["gettext"] = _translate
    env.globals["ngettext"] = _translate_plural
    env.globals["i18n_service"] = service

    # Expose formatting functions
    env.globals["format_number"] = format_number
    env.globals["format_currency"] = format_currency
    env.globals["format_date"] = format_date
    env.globals["format_time"] = format_time
    env.globals["format_datetime"] = format_datetime
    env.globals["format_percent"] = format_percent
    env.globals["format_ordinal"] = format_ordinal

    # ── Filters ──────────────────────────────────────────────────────

    def filter_translate(value: str, **kwargs: Any) -> str:
        locale = kwargs.pop("locale", None) or _get_ctx_locale(env)
        return service.t(value, locale=locale, **kwargs)

    def filter_format_number(value: Any, locale: Optional[str] = None, **kwargs) -> str:
        loc = locale or _get_ctx_locale(env)
        return format_number(value, loc, **kwargs)

    def filter_format_currency(value: Any, currency: str = "USD", locale: Optional[str] = None, **kwargs) -> str:
        loc = locale or _get_ctx_locale(env)
        return format_currency(value, currency, loc, **kwargs)

    def filter_format_date(value: Any, locale: Optional[str] = None, **kwargs) -> str:
        loc = locale or _get_ctx_locale(env)
        return format_date(value, loc, **kwargs)

    def filter_format_time(value: Any, locale: Optional[str] = None, **kwargs) -> str:
        loc = locale or _get_ctx_locale(env)
        return format_time(value, loc, **kwargs)

    def filter_format_percent(value: Any, locale: Optional[str] = None, **kwargs) -> str:
        loc = locale or _get_ctx_locale(env)
        return format_percent(value, loc, **kwargs)

    env.filters["translate"] = filter_translate
    env.filters["t"] = filter_translate
    env.filters["format_number"] = filter_format_number
    env.filters["format_currency"] = filter_format_currency
    env.filters["format_date"] = filter_format_date
    env.filters["format_time"] = filter_format_time
    env.filters["format_percent"] = filter_format_percent

    logger.debug("I18n template globals and filters registered")


class I18nTemplateExtension:
    """
    Lightweight template extension descriptor for Aquilia's template engine.

    This is NOT a Jinja2 Extension (which requires ``jinja2.ext.Extension``
    subclass). Instead, it is a descriptor that Aquilia's template engine
    recognizes and applies during setup.

    Usage::

        engine = TemplateEngine(
            loader=loader,
            extensions=[I18nTemplateExtension(i18n_service)],
        )

    When applied, it registers the same globals and filters as
    ``register_i18n_template_globals()``.
    """

    def __init__(self, service: "I18nService"):
        self.service = service

    def apply(self, env: "Environment") -> None:
        """Apply the i18n extension to the Jinja2 environment."""
        register_i18n_template_globals(env, self.service)

    def __repr__(self) -> str:
        return "I18nTemplateExtension()"


# ═══════════════════════════════════════════════════════════════════════════
# Internal Helpers
# ═══════════════════════════════════════════════════════════════════════════

def _get_ctx_locale(env: "Environment") -> str:
    """
    Get the current locale from template rendering context.

    Looks for ``locale`` in the Jinja2 global context (set by
    I18nMiddleware via request.state → template context).
    Falls back to ``"en"``.
    """
    # The template middleware injects `locale` into the context
    # It's available as a global that gets overridden per-request
    locale = env.globals.get("request_locale")
    if locale:
        return locale

    # Try to get from the i18n service default
    svc = env.globals.get("i18n_service")
    if svc and hasattr(svc, "config"):
        return svc.config.default_locale

    return "en"
