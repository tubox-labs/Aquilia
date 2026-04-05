"""
Lazy Strings — Deferred translation resolution.

Provides ``LazyString`` objects that look and behave like normal strings
but delay translation lookup until they are actually *used* (stringified,
concatenated, formatted, etc.).

This is essential for module-level translation constants that are defined
at import time — before the i18n service or request locale are available::

    from aquilia.i18n import lazy_t

    # Defined at module level (no service or locale yet)
    WELCOME_MSG = lazy_t("messages.welcome")
    ERROR_MSG = lazy_t("errors.generic", default="An error occurred")

    # Later, at request time, when converted to str:
    str(WELCOME_MSG)  # → resolves via the active I18nService + locale

Thread-safety: ``LazyString`` is immutable and safe for concurrent reads.
"""

from __future__ import annotations

from contextvars import ContextVar
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .service import I18nService


# Request/task-local references set by I18nMiddleware or DI.
_service_ref: ContextVar[I18nService | None] = ContextVar("aquilia_i18n_lazy_service", default=None)
_locale_ref: ContextVar[str | None] = ContextVar("aquilia_i18n_lazy_locale", default=None)


def set_lazy_context(service: I18nService, locale: str | None = None) -> None:
    """
    Set the global i18n context for lazy string resolution.

    Called by the i18n middleware at the start of each request.

    Args:
        service: Active I18nService
        locale: Current request locale
    """
    _service_ref.set(service)
    _locale_ref.set(locale)


def clear_lazy_context() -> None:
    """Clear the lazy context (called at request cleanup)."""
    _service_ref.set(None)
    _locale_ref.set(None)


class LazyString:
    """
    A string-like object that defers translation until stringification.

    Implements the full ``str`` protocol so it can be used anywhere a
    string is expected: formatting, concatenation, comparison, hashing, etc.

    Args:
        key: Translation key (dot-notated)
        default: Fallback if key not found
        locale: Override locale (None = use request locale)
        kwargs: Named interpolation arguments
        service: Explicit service reference (None = use global)
    """

    __slots__ = ("_key", "_default", "_locale", "_kwargs", "_service")

    def __init__(
        self,
        key: str,
        *,
        default: str | None = None,
        locale: str | None = None,
        service: I18nService | None = None,
        **kwargs: Any,
    ):
        self._key = key
        self._default = default
        self._locale = locale
        self._kwargs = kwargs
        self._service = service

    def _resolve(self) -> str:
        """Resolve the translation."""
        svc = self._service or _service_ref.get()
        if svc is None:
            # No service available — return key or default
            return self._default or self._key

        locale = self._locale or _locale_ref.get()
        return svc.t(self._key, locale=locale, default=self._default, **self._kwargs)

    # ── str Protocol ─────────────────────────────────────────────────

    def __str__(self) -> str:
        return self._resolve()

    def __repr__(self) -> str:
        return f"LazyString('{self._key}')"

    def __len__(self) -> int:
        return len(str(self))

    def __contains__(self, item: str) -> bool:
        return item in str(self)

    def __iter__(self):
        return iter(str(self))

    def __getitem__(self, index):
        return str(self)[index]

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, LazyString):
            return str(self) == str(other)
        return str(self) == other

    def __ne__(self, other: Any) -> bool:
        return not self.__eq__(other)

    def __lt__(self, other: Any) -> bool:
        return str(self) < str(other)

    def __le__(self, other: Any) -> bool:
        return str(self) <= str(other)

    def __gt__(self, other: Any) -> bool:
        return str(self) > str(other)

    def __ge__(self, other: Any) -> bool:
        return str(self) >= str(other)

    def __hash__(self) -> int:
        return hash(str(self))

    def __add__(self, other: str) -> str:
        return str(self) + other

    def __radd__(self, other: str) -> str:
        return other + str(self)

    def __mod__(self, args: Any) -> str:
        return str(self) % args

    def __format__(self, format_spec: str) -> str:
        return format(str(self), format_spec)

    def __bool__(self) -> bool:
        return bool(str(self))

    # ── str Methods (delegated) ──────────────────────────────────────

    def upper(self) -> str:
        return str(self).upper()

    def lower(self) -> str:
        return str(self).lower()

    def strip(self, chars: str | None = None) -> str:
        return str(self).strip(chars)

    def split(self, sep: str | None = None, maxsplit: int = -1) -> list[str]:
        return str(self).split(sep, maxsplit)

    def replace(self, old: str, new: str, count: int = -1) -> str:
        return str(self).replace(old, new, count)

    def startswith(self, prefix: str, *args) -> bool:
        return str(self).startswith(prefix, *args)

    def endswith(self, suffix: str, *args) -> bool:
        return str(self).endswith(suffix, *args)

    def encode(self, encoding: str = "utf-8", errors: str = "strict") -> bytes:
        return str(self).encode(encoding, errors)

    def join(self, iterable) -> str:
        return str(self).join(iterable)

    def format(self, *args, **kwargs) -> str:
        return str(self).format(*args, **kwargs)

    def format_map(self, mapping) -> str:
        return str(self).format_map(mapping)


class LazyPluralString(LazyString):
    """
    Lazy string with plural support.

    Defers plural resolution until stringification.

    Args:
        key: Translation key
        count: Plural count
        default: Fallback
        locale: Override locale
        kwargs: Interpolation arguments
        service: Explicit service reference
    """

    __slots__ = ("_count",)

    def __init__(
        self,
        key: str,
        count: int | float,
        *,
        default: str | None = None,
        locale: str | None = None,
        service: I18nService | None = None,
        **kwargs: Any,
    ):
        super().__init__(key, default=default, locale=locale, service=service, **kwargs)
        self._count = count

    def _resolve(self) -> str:
        svc = self._service or _service_ref.get()
        if svc is None:
            return self._default or self._key

        locale = self._locale or _locale_ref.get()
        return svc.tn(self._key, self._count, locale=locale, default=self._default, **self._kwargs)

    def __repr__(self) -> str:
        return f"LazyPluralString('{self._key}', count={self._count})"


def lazy_t(
    key: str,
    *,
    default: str | None = None,
    locale: str | None = None,
    service: I18nService | None = None,
    **kwargs: Any,
) -> LazyString:
    """
    Create a lazy translation string.

    Can be used at module level before the i18n service is initialized::

        from aquilia.i18n import lazy_t

        TITLE = lazy_t("pages.home.title")
        ERROR = lazy_t("errors.generic", default="Something went wrong")

    Args:
        key: Translation key
        default: Fallback value
        locale: Override locale
        service: Explicit service reference
        **kwargs: Interpolation arguments

    Returns:
        LazyString instance
    """
    return LazyString(key, default=default, locale=locale, service=service, **kwargs)


def lazy_tn(
    key: str,
    count: int | float,
    *,
    default: str | None = None,
    locale: str | None = None,
    service: I18nService | None = None,
    **kwargs: Any,
) -> LazyPluralString:
    """
    Create a lazy plural translation string.

    Args:
        key: Translation key
        count: Plural count
        default: Fallback value
        locale: Override locale
        service: Explicit service reference
        **kwargs: Interpolation arguments

    Returns:
        LazyPluralString instance
    """
    return LazyPluralString(key, count, default=default, locale=locale, service=service, **kwargs)
