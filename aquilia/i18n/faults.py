"""
I18n Faults — Typed fault signals for the i18n subsystem.

Integrates with Aquilia's fault system (``aquilia.faults``) so i18n errors
flow through the same pipelines, handlers, and observability as all other
framework faults.

Fault hierarchy::

    Fault
    └── I18nFault  (domain = I18N)
        ├── MissingTranslationFault   ← key not found in any catalog
        ├── InvalidLocaleFault        ← malformed BCP 47 tag
        ├── CatalogLoadFault          ← failed to read catalog file
        └── PluralRuleFault           ← invalid plural form / category
"""

from __future__ import annotations

from typing import Any

from aquilia.faults.core import Fault, FaultDomain, Severity

# ── Register I18N domain ────────────────────────────────────────────────
FaultDomain.I18N = FaultDomain("i18n", "Internationalization and localization faults")


class I18nFault(Fault):
    """
    Base fault for all i18n-related errors.

    Inherits from ``Fault`` so it participates in Aquilia's fault engine,
    handlers, and observability pipeline.
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        retryable: bool = False,
        public: bool = False,
        metadata: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=FaultDomain.I18N,
            severity=severity,
            retryable=retryable,
            public=public,
            metadata=metadata,
        )


class MissingTranslationFault(I18nFault):
    """
    Raised when a translation key cannot be found in any catalog.

    Attributes (via ``metadata``):
        key: The missing translation key
        locale: The requested locale
        fallback_chain: Locales tried before giving up
    """

    def __init__(
        self,
        key: str,
        locale: str,
        *,
        fallback_chain: list[str] | None = None,
        **kwargs,
    ):
        super().__init__(
            code="I18N_MISSING_TRANSLATION",
            message=f"Missing translation: key='{key}' locale='{locale}'",
            severity=Severity.WARN,
            public=False,
            metadata={
                "key": key,
                "locale": locale,
                "fallback_chain": fallback_chain or [],
                **kwargs,
            },
        )
        self.key = key
        self.locale = locale


class InvalidLocaleFault(I18nFault):
    """
    Raised when a locale tag cannot be parsed as valid BCP 47.

    Attributes (via ``metadata``):
        tag: The invalid locale string
        reason: Why parsing failed
    """

    def __init__(
        self,
        tag: str,
        reason: str = "Malformed BCP 47 locale tag",
        **kwargs,
    ):
        super().__init__(
            code="I18N_INVALID_LOCALE",
            message=f"Invalid locale tag '{tag}': {reason}",
            severity=Severity.WARN,
            public=True,
            metadata={
                "tag": tag,
                "reason": reason,
                **kwargs,
            },
        )
        self.tag = tag
        self.reason = reason


class CatalogLoadFault(I18nFault):
    """
    Raised when a translation catalog file cannot be loaded.

    Typically caused by missing files, invalid JSON/YAML, or permission errors.

    Attributes (via ``metadata``):
        path: File path that failed to load
        reason: Error description
    """

    def __init__(
        self,
        path: str,
        reason: str = "Failed to load catalog file",
        *,
        original_error: Exception | None = None,
        **kwargs,
    ):
        super().__init__(
            code="I18N_CATALOG_LOAD",
            message=f"Failed to load i18n catalog '{path}': {reason}",
            severity=Severity.ERROR,
            retryable=True,
            metadata={
                "path": path,
                "reason": reason,
                "original_error": str(original_error) if original_error else None,
                **kwargs,
            },
        )
        self.path = path


class PluralRuleFault(I18nFault):
    """
    Raised when plural form selection fails.

    Typically caused by invalid count values or unsupported plural categories.

    Attributes (via ``metadata``):
        language: Language code
        count: The problematic count value
        category: The invalid/unexpected category
    """

    def __init__(
        self,
        language: str,
        count: Any = None,
        category: str = "",
        reason: str = "Plural rule evaluation failed",
        **kwargs,
    ):
        super().__init__(
            code="I18N_PLURAL_RULE",
            message=f"Plural rule error for '{language}': {reason}",
            severity=Severity.WARN,
            metadata={
                "language": language,
                "count": count,
                "category": category,
                "reason": reason,
                **kwargs,
            },
        )
        self.language = language
