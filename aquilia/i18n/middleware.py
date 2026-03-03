"""
I18n Middleware — Request-scoped locale resolution & injection.

Provides locale resolution from multiple sources (header, cookie, query,
path, session) and injects the resolved locale + i18n service into the
request state for downstream consumption.

Architecture::

    Request
    ┌──────────────────────────────────┐
    │  Accept-Language: fr-CA, fr;q=0.9│
    │  Cookie: aq_locale=de            │
    │  ?lang=ja                        │
    └───────────┬──────────────────────┘
                │
                ▼
    ┌─────────────────────────┐
    │  ChainLocaleResolver    │
    │  ┌────────────────────┐ │
    │  │ QueryResolver      │─┤── ?lang=ja → "ja" ✓
    │  │ CookieResolver     │ │
    │  │ HeaderResolver     │ │
    │  └────────────────────┘ │
    └───────────┬─────────────┘
                │ locale = "ja"
                ▼
    ┌─────────────────────────┐
    │  I18nMiddleware          │
    │  request.state["locale"]│── "ja"
    │  request.state["i18n"]  │── I18nService
    └───────────┬─────────────┘
                │
                ▼
            Controller / Template

The resolver chain is configurable via ``I18nConfig.resolver_order``.

Usage in Aquilia middleware stack::

    # Automatic — wired by server.py when i18n is enabled
    # Manual:
    middleware_stack.add(
        I18nMiddleware(i18n_service, resolver),
        scope="global",
        priority=25,
        name="i18n",
    )
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Sequence, TYPE_CHECKING

from .locale import negotiate_locale, normalize_locale, parse_locale
from .lazy import set_lazy_context, clear_lazy_context

if TYPE_CHECKING:
    from .service import I18nService

logger = logging.getLogger("aquilia.i18n.middleware")


# ═══════════════════════════════════════════════════════════════════════════
# Locale Resolvers
# ═══════════════════════════════════════════════════════════════════════════

class LocaleResolver(ABC):
    """
    Abstract locale resolver.

    Each resolver inspects one source (header, cookie, query, path, session)
    and returns a locale string or ``None``.
    """

    @abstractmethod
    def resolve(self, request: Any) -> Optional[str]:
        """
        Attempt to resolve locale from the request.

        Args:
            request: Aquilia request object

        Returns:
            Locale string or None if this resolver cannot determine it
        """
        ...


class HeaderLocaleResolver(LocaleResolver):
    """
    Resolve locale from the ``Accept-Language`` HTTP header.

    Performs full RFC 4647 content negotiation against the available
    locales.
    """

    def __init__(self, available_locales: Sequence[str], default_locale: str = "en"):
        self.available_locales = list(available_locales)
        self.default_locale = default_locale

    def resolve(self, request: Any) -> Optional[str]:
        accept = _get_header(request, "accept-language")
        if not accept:
            return None

        result = negotiate_locale(accept, self.available_locales, self.default_locale)
        # Only return if negotiation picked something other than default
        # (to allow other resolvers to override)
        return result if result else None


class CookieLocaleResolver(LocaleResolver):
    """
    Resolve locale from a cookie.

    Cookie name defaults to ``aq_locale`` (configurable via I18nConfig).
    """

    def __init__(self, cookie_name: str = "aq_locale", available_locales: Optional[Sequence[str]] = None):
        self.cookie_name = cookie_name
        self.available_locales = set(available_locales) if available_locales else None

    def resolve(self, request: Any) -> Optional[str]:
        cookies = _get_cookies(request)
        value = cookies.get(self.cookie_name)
        if not value:
            return None

        normalized = normalize_locale(value)
        if normalized is None:
            return None

        # Validate against available locales if configured
        if self.available_locales and normalized not in self.available_locales:
            return None

        return normalized


class QueryLocaleResolver(LocaleResolver):
    """
    Resolve locale from a query parameter.

    Parameter name defaults to ``lang`` (configurable via I18nConfig).
    """

    def __init__(self, param_name: str = "lang", available_locales: Optional[Sequence[str]] = None):
        self.param_name = param_name
        self.available_locales = set(available_locales) if available_locales else None

    def resolve(self, request: Any) -> Optional[str]:
        params = _get_query_params(request)
        value = params.get(self.param_name)
        if not value:
            return None

        normalized = normalize_locale(value)
        if normalized is None:
            return None

        if self.available_locales and normalized not in self.available_locales:
            return None

        return normalized


class PathLocaleResolver(LocaleResolver):
    """
    Resolve locale from the URL path prefix.

    Matches paths like ``/en/about``, ``/fr-CA/help``.
    """

    def __init__(self, available_locales: Optional[Sequence[str]] = None):
        self.available_locales = set(available_locales) if available_locales else None

    def resolve(self, request: Any) -> Optional[str]:
        path = _get_path(request)
        if not path or path == "/":
            return None

        # Extract first path segment
        segments = path.strip("/").split("/")
        if not segments:
            return None

        candidate = segments[0]
        normalized = normalize_locale(candidate)
        if normalized is None:
            return None

        if self.available_locales and normalized not in self.available_locales:
            return None

        return normalized


class SessionLocaleResolver(LocaleResolver):
    """
    Resolve locale from the user's session.

    Reads ``request.state["session"]["locale"]`` if sessions are available.
    """

    def __init__(self, session_key: str = "locale", available_locales: Optional[Sequence[str]] = None):
        self.session_key = session_key
        self.available_locales = set(available_locales) if available_locales else None

    def resolve(self, request: Any) -> Optional[str]:
        state = _get_state(request)
        session = state.get("session")
        if not session:
            return None

        value = None
        if isinstance(session, dict):
            value = session.get(self.session_key)
        elif hasattr(session, "get"):
            value = session.get(self.session_key)

        if not value:
            return None

        normalized = normalize_locale(str(value))
        if normalized is None:
            return None

        if self.available_locales and normalized not in self.available_locales:
            return None

        return normalized


class ChainLocaleResolver(LocaleResolver):
    """
    Composite resolver that tries multiple resolvers in order.

    Returns the first non-None result. If all resolvers return None,
    returns None (the middleware will fall back to default locale).

    Args:
        resolvers: Ordered list of resolvers to try
    """

    def __init__(self, resolvers: Sequence[LocaleResolver]):
        self.resolvers = list(resolvers)

    def resolve(self, request: Any) -> Optional[str]:
        for resolver in self.resolvers:
            try:
                result = resolver.resolve(request)
                if result is not None:
                    return result
            except Exception as e:
                logger.debug("Locale resolver %s failed: %s", type(resolver).__name__, e)
                continue
        return None


# ═══════════════════════════════════════════════════════════════════════════
# I18n Middleware
# ═══════════════════════════════════════════════════════════════════════════

class I18nMiddleware:
    """
    Aquilia middleware that resolves locale and injects i18n into requests.

    After this middleware runs, every downstream handler/controller has:
    - ``request.state["locale"]`` → resolved locale string (e.g. ``"fr-CA"``)
    - ``request.state["locale_obj"]`` → parsed ``Locale`` dataclass
    - ``request.state["i18n"]`` → ``I18nService`` reference

    This is an ASGI-style callable middleware compatible with Aquilia's
    middleware stack.

    Args:
        service: The I18nService singleton
        resolver: Locale resolver (typically a ChainLocaleResolver)
    """

    def __init__(
        self,
        service: "I18nService",
        resolver: Optional[LocaleResolver] = None,
    ):
        self.service = service
        self.resolver = resolver

    async def __call__(self, request: Any, ctx: Any, next_handler: Callable) -> Any:
        """
        Resolve locale and inject i18n state.
        """
        locale = self.service.config.default_locale

        # Resolve locale from request
        if self.resolver:
            try:
                resolved = self.resolver.resolve(request)
                if resolved and self.service.is_available(resolved):
                    locale = resolved
            except Exception as e:
                logger.debug("Locale resolution failed, using default: %s", e)

        # Parse locale object
        locale_obj = parse_locale(locale)

        # Inject into request state
        state = _get_state(request)
        state["locale"] = locale
        state["locale_obj"] = locale_obj
        state["i18n"] = self.service

        # Set lazy string context for this request
        set_lazy_context(self.service, locale)

        try:
            response = await next_handler(request, ctx)
            return response
        finally:
            # Clean up lazy context
            clear_lazy_context()


# ═══════════════════════════════════════════════════════════════════════════
# Factory
# ═══════════════════════════════════════════════════════════════════════════

def build_resolver(config: Any) -> ChainLocaleResolver:
    """
    Build a ``ChainLocaleResolver`` from an ``I18nConfig``.

    The resolver order is determined by ``config.resolver_order``.

    Args:
        config: I18nConfig instance

    Returns:
        Configured ChainLocaleResolver
    """
    resolver_map = {
        "header": lambda: HeaderLocaleResolver(config.available_locales, config.default_locale),
        "cookie": lambda: CookieLocaleResolver(config.cookie_name, config.available_locales),
        "query": lambda: QueryLocaleResolver(config.query_param, config.available_locales),
        "path": lambda: PathLocaleResolver(config.available_locales),
        "session": lambda: SessionLocaleResolver(available_locales=config.available_locales),
    }

    resolvers: list[LocaleResolver] = []
    for name in config.resolver_order:
        factory = resolver_map.get(name)
        if factory:
            resolvers.append(factory())
        else:
            logger.warning("Unknown locale resolver: %s", name)

    return ChainLocaleResolver(resolvers)


# ═══════════════════════════════════════════════════════════════════════════
# Request Helpers (Aquilia-compatible request interface)
# ═══════════════════════════════════════════════════════════════════════════

def _get_header(request: Any, name: str) -> Optional[str]:
    """Get a header value from the request."""
    if hasattr(request, "headers"):
        headers = request.headers
        if isinstance(headers, dict):
            return headers.get(name) or headers.get(name.title())
        if hasattr(headers, "get"):
            return headers.get(name) or headers.get(name.title())
    return None


def _get_cookies(request: Any) -> Dict[str, str]:
    """Get cookies from the request."""
    if hasattr(request, "cookies"):
        cookies = request.cookies
        if isinstance(cookies, dict):
            return cookies
        if hasattr(cookies, "items"):
            return dict(cookies.items())
    return {}


def _get_query_params(request: Any) -> Dict[str, str]:
    """Get query parameters from the request."""
    if hasattr(request, "query_params"):
        qp = request.query_params
        if isinstance(qp, dict):
            return qp
        if hasattr(qp, "get"):
            # QueryParams-like object
            return {k: qp.get(k) for k in qp}
    return {}


def _get_path(request: Any) -> str:
    """Get the request path."""
    if hasattr(request, "url"):
        url = request.url
        if hasattr(url, "path"):
            return url.path
        return str(url)
    if hasattr(request, "path"):
        return request.path
    return "/"


def _get_state(request: Any) -> Dict[str, Any]:
    """Get the request state dict."""
    if hasattr(request, "state"):
        state = request.state
        if isinstance(state, dict):
            return state
        # Starlette-style state object
        if hasattr(state, "__dict__"):
            return state.__dict__
    return {}
