"""Deprecated re-export package for extended middleware.

The canonical location is :mod:`aquilia.middleware.builtin`. This package
survives so user projects whose ``workspace.py`` resolves dotted strings like
``"aquilia.middleware_ext.SecurityHeadersMiddleware"`` keep booting — but
access now warns, so the migration is visible instead of silent.

Will be removed in 2.0.
"""

from __future__ import annotations

import warnings
from typing import Any

# name -> (module, attribute) under the new layout.
_MAP: dict[str, tuple[str, str]] = {
    "EffectMiddleware": ("aquilia.middleware.builtin.effects", "EffectMiddleware"),
    "FlowContextMiddleware": ("aquilia.middleware.builtin.effects", "FlowContextMiddleware"),
    "LoggingMiddleware": ("aquilia.middleware.builtin.logging", "LoggingMiddleware"),
    "EnhancedLoggingMiddleware": ("aquilia.middleware.builtin.logging", "LoggingMiddleware"),
    "CombinedLogFormatter": ("aquilia.middleware.builtin.logging", "CombinedLogFormatter"),
    "StructuredLogFormatter": ("aquilia.middleware.builtin.logging", "StructuredLogFormatter"),
    "DevLogFormatter": ("aquilia.middleware.builtin.logging", "DevLogFormatter"),
    "RateLimitMiddleware": ("aquilia.middleware.builtin.rate_limit", "RateLimitMiddleware"),
    "RateLimitRule": ("aquilia.middleware.builtin.rate_limit", "RateLimitRule"),
    "api_key_extractor": ("aquilia.middleware.builtin.rate_limit", "api_key_extractor"),
    "ip_key_extractor": ("aquilia.middleware.builtin.rate_limit", "ip_key_extractor"),
    "user_key_extractor": ("aquilia.middleware.builtin.rate_limit", "user_key_extractor"),
    "RequestScopeMiddleware": ("aquilia.middleware.builtin.request_scope", "RequestScopeMiddleware"),
    "SimplifiedRequestScopeMiddleware": (
        "aquilia.middleware.builtin.request_scope",
        "SimplifiedRequestScopeMiddleware",
    ),
    "SessionMiddleware": ("aquilia.middleware.builtin.session", "SessionMiddleware"),
    "StaticMiddleware": ("aquilia.middleware.builtin.static", "StaticMiddleware"),
    "CORSMiddleware": ("aquilia.middleware.builtin.security.cors", "CORSMiddleware"),
    "CSPMiddleware": ("aquilia.middleware.builtin.security.csp", "CSPMiddleware"),
    "CSPPolicy": ("aquilia.middleware.builtin.security.csp", "CSPPolicy"),
    "CSRFError": ("aquilia.middleware.builtin.security.csrf", "CSRFError"),
    "CSRFMiddleware": ("aquilia.middleware.builtin.security.csrf", "CSRFMiddleware"),
    "HSTSMiddleware": ("aquilia.middleware.builtin.security.hsts", "HSTSMiddleware"),
    "HTTPSRedirectMiddleware": (
        "aquilia.middleware.builtin.security.https_redirect",
        "HTTPSRedirectMiddleware",
    ),
    "ProxyFixMiddleware": ("aquilia.middleware.builtin.security.proxy_fix", "ProxyFixMiddleware"),
    "SecurityHeadersMiddleware": (
        "aquilia.middleware.builtin.security.headers",
        "SecurityHeadersMiddleware",
    ),
    "csrf_exempt": ("aquilia.middleware.builtin.security.csrf", "csrf_exempt"),
    "csrf_token_func": ("aquilia.middleware.builtin.security.csrf", "csrf_token_func"),
}

__all__ = sorted(_MAP)

_WARNED = False


def _warn() -> None:
    """Warn once per process. Users cannot fix a shim they hit on every import."""
    global _WARNED
    if not _WARNED:
        _WARNED = True
        warnings.warn(
            "aquilia.middleware_ext is deprecated: middleware moved to "
            "aquilia.middleware.builtin. Update dotted-path references in "
            "workspace.py chains; this shim will be removed in 2.0.",
            DeprecationWarning,
            stacklevel=3,
        )


def __getattr__(name: str) -> Any:
    if name not in _MAP:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    _warn()
    import importlib

    module_path, attribute = _MAP[name]
    return getattr(importlib.import_module(module_path), attribute)


def __dir__() -> list[str]:
    return __all__
