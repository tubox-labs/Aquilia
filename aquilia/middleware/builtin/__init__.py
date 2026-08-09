"""Framework-owned middleware implementations.

These depend on :mod:`aquilia.middleware.core` only — never on
:mod:`aquilia.middleware.stack`. That direction is what lets the stack import
built-ins without a cycle.
"""

from aquilia.middleware.builtin.compression import CompressionMiddleware
from aquilia.middleware.builtin.effects import EffectMiddleware, FlowContextMiddleware
from aquilia.middleware.builtin.exceptions import ExceptionMiddleware
from aquilia.middleware.builtin.logging import (
    CombinedLogFormatter,
    DevLogFormatter,
    LoggingMiddleware,
    StructuredLogFormatter,
)
from aquilia.middleware.builtin.rate_limit import (
    RateLimitMiddleware,
    RateLimitRule,
    api_key_extractor,
    ip_key_extractor,
    user_key_extractor,
)
from aquilia.middleware.builtin.request_id import RequestIdMiddleware
from aquilia.middleware.builtin.request_scope import (
    RequestScopeMiddleware,
    SimplifiedRequestScopeMiddleware,
)
from aquilia.middleware.builtin.security import (
    CORSMiddleware,
    CSPMiddleware,
    CSPPolicy,
    CSRFError,
    CSRFMiddleware,
    HSTSMiddleware,
    HTTPSRedirectMiddleware,
    ProxyFixMiddleware,
    SecurityHeadersMiddleware,
    csrf_exempt,
    csrf_token_func,
)
from aquilia.middleware.builtin.session import SessionMiddleware
from aquilia.middleware.builtin.static import StaticMiddleware
from aquilia.middleware.builtin.timeout import TimeoutMiddleware

__all__ = [
    # Core
    "ExceptionMiddleware",
    "RequestIdMiddleware",
    "TimeoutMiddleware",
    "CompressionMiddleware",
    "RequestScopeMiddleware",
    "SimplifiedRequestScopeMiddleware",
    "SessionMiddleware",
    # Security
    "CORSMiddleware",
    "CSPMiddleware",
    "CSPPolicy",
    "CSRFError",
    "CSRFMiddleware",
    "HSTSMiddleware",
    "HTTPSRedirectMiddleware",
    "ProxyFixMiddleware",
    "SecurityHeadersMiddleware",
    "csrf_exempt",
    "csrf_token_func",
    # Rate limiting
    "RateLimitMiddleware",
    "RateLimitRule",
    "ip_key_extractor",
    "api_key_extractor",
    "user_key_extractor",
    # Static files
    "StaticMiddleware",
    # Logging
    "LoggingMiddleware",
    "CombinedLogFormatter",
    "StructuredLogFormatter",
    "DevLogFormatter",
    # Effects
    "EffectMiddleware",
    "FlowContextMiddleware",
]
