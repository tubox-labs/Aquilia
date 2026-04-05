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


def _register_with_value_provider(
    container: Any,
    *,
    token: type | str,
    value: Any,
    scope: str,
    name: str,
) -> None:
    """Register a constant value using Aquilia's Provider-based DI API."""
    from aquilia.di.providers import ValueProvider

    provider = ValueProvider(
        value=value,
        token=token,
        scope=scope,
        name=name,
    )

    try:
        container.register(provider)
    except Exception as exc:
        # Some containers may already have this token registered;
        # treat duplicate registration as non-fatal.
        msg = str(exc)
        if "already registered" in msg or "PROVIDER_ALREADY_REGISTERED" in msg:
            return
        raise


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
            # Aquilia Container.register expects a Provider, not token/value args.
            _register_with_value_provider(
                container,
                token=I18nService,
                value=service,
                scope="app",
                name="i18n_service",
            )
            _register_with_value_provider(
                container,
                token=I18nConfig,
                value=cfg,
                scope="app",
                name="i18n_config",
            )
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

    try:
        locale_obj = parse_locale(locale)
    except Exception:
        locale_obj = None

    try:
        if hasattr(container, "register_value"):
            if locale_obj is not None:
                container.register_value(Locale, locale_obj)
            container.register_value("locale", locale)
        elif hasattr(container, "register"):
            if locale_obj is not None:
                _register_with_value_provider(
                    container,
                    token=Locale,
                    value=locale_obj,
                    scope="request",
                    name="request_locale_obj",
                )
            _register_with_value_provider(
                container,
                token="locale",
                value=locale,
                scope="request",
                name="request_locale",
            )
        elif hasattr(container, "set"):
            if locale_obj is not None:
                container.set(Locale, locale_obj)
            container.set("locale", locale)
        elif isinstance(container, dict):
            if locale_obj is not None:
                container[Locale] = locale_obj
            container["locale"] = locale
    except Exception:
        pass
