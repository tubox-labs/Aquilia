"""
AquilaTemplates — Fault Classes.

Typed, structured fault classes for the template engine system.
Replaces raw RuntimeError raises with first-class Aquilia Fault objects.

Domains:
    TEMPLATE — Template engine, rendering, and security faults.
"""

from __future__ import annotations

from typing import Any

from aquilia.faults.core import Fault, FaultDomain, Severity

# ============================================================================
# Domain
# ============================================================================

TEMPLATE_DOMAIN = FaultDomain.custom("template", "Template engine faults")


# ============================================================================
# Base
# ============================================================================


class TemplateFault(Fault):
    """Base fault for the template subsystem."""

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
            domain=TEMPLATE_DOMAIN,
            severity=severity,
            retryable=retryable,
            public=public,
            metadata=metadata,
        )


# ============================================================================
# Concrete Faults
# ============================================================================


class TemplateEngineUnavailableFault(TemplateFault):
    """
    Template engine not available.

    Raised when a mixin or integration tries to render a template but
    no TemplateEngine instance has been configured / injected.
    """

    def __init__(self, **kwargs):
        super().__init__(
            code="TEMPLATE_ENGINE_UNAVAILABLE",
            message="Template engine not available",
            severity=Severity.ERROR,
            retryable=False,
            metadata=kwargs.get("metadata", {}),
        )


class TemplateCacheIntegrityFault(TemplateFault):
    """
    Bytecode cache integrity check failed.

    Raised when a cached template artifact fails HMAC verification,
    indicating possible tampering or corruption.
    """

    def __init__(self, cache_file: str, **kwargs):
        super().__init__(
            code="TEMPLATE_CACHE_INTEGRITY",
            message=f"Bytecode cache integrity check failed: {cache_file}",
            severity=Severity.WARN,
            retryable=False,
            metadata={"cache_file": cache_file, **kwargs.get("metadata", {})},
        )


class TemplateSanitizationWarning(TemplateFault):
    """
    HTML sanitization used regex-based implementation.

    Advisory fault (INFO severity) logged when the built-in regex
    sanitizer is used instead of a proper library like bleach.
    """

    def __init__(self, **kwargs):
        super().__init__(
            code="TEMPLATE_SANITIZE_REGEX",
            message=(
                "Using built-in regex HTML sanitizer which is NOT production-grade. "
                "Install 'bleach' for robust XSS protection."
            ),
            severity=Severity.INFO,
            retryable=False,
            metadata=kwargs.get("metadata", {}),
        )
