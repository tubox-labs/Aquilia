"""
I18n DI Integration — Register i18n providers in Aquilia's DI container.

Registers:
- ``I18nService`` as a singleton (shared across the application)
- ``I18nConfig`` as a value provider (configuration object)

These providers allow controllers to receive i18n dependencies via
constructor injection::

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

Integration is automatic — the server calls ``register_i18n_providers()``
at startup when i18n is enabled.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .service import I18nConfig, I18nService

logger = logging.getLogger("aquilia.i18n.di")


def register_i18n_providers(
    container: Any,
    service: I18nService,
    config: I18nConfig | None = None,
) -> None:
    """
    Register i18n providers in a DI container.

    Registers:
    - ``I18nService`` → singleton (the shared service instance)
    - ``I18nConfig`` → value provider (frozen config object)

    Args:
        container: Aquilia DI Container or Registry
        service: Initialized I18nService
        config: I18nConfig (defaults to ``service.config``)
    """
    from .service import I18nConfig, I18nService

    cfg = config or service.config

    try:
        # Try Aquilia's DI API
        if hasattr(container, "register_value"):
            # Registry API
            container.register_value(I18nService, service)
            container.register_value(I18nConfig, cfg)
        elif hasattr(container, "register"):
            # Generic Container.register(type, instance)
            container.register(I18nService, service)
            container.register(I18nConfig, cfg)
        elif hasattr(container, "set"):
            # Simple dict-like container
            container.set(I18nService, service)
            container.set(I18nConfig, cfg)
        elif isinstance(container, dict):
            # Plain dict (testing)
            container[I18nService] = service
            container[I18nConfig] = cfg
        else:
            logger.warning(
                "Cannot register i18n providers — container type %s not recognized",
                type(container).__name__,
            )
    except Exception as e:
        logger.error("Failed to register i18n DI providers: %s", e, exc_info=True)


def register_i18n_request_providers(
    container: Any,
    locale: str,
    service: I18nService,
) -> None:
    """
    Register request-scoped i18n providers.

    Called per-request by the i18n middleware to provide the current
    locale as a DI-injectable value.

    Args:
        container: Request-scoped DI container
        locale: Resolved locale for this request
        service: I18nService reference
    """
    from .locale import Locale, parse_locale

    locale_obj = parse_locale(locale)

    try:
        if hasattr(container, "register_value"):
            container.register_value(Locale, locale_obj)
            container.register_value("locale", locale)
        elif hasattr(container, "register"):
            container.register(Locale, locale_obj)
        elif hasattr(container, "set"):
            container.set(Locale, locale_obj)
            container.set("locale", locale)
        elif isinstance(container, dict):
            container[Locale] = locale_obj
            container["locale"] = locale
    except Exception:
        pass
