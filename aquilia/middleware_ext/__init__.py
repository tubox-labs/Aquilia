"""
Extended middleware components for Aquilia framework.

This module provides additional middleware beyond the core middleware.py:

Core:
- RequestScopeMiddleware: ASGI-level request-scoped DI container creation
- SimplifiedRequestScopeMiddleware: Higher-level request scope middleware
- SessionMiddleware: Session management middleware

Security:
- CORSMiddleware: Full RFC 6454/7231 CORS with regex/glob origin matching
- CSPMiddleware: Content-Security-Policy with per-request nonce
- CSRFMiddleware: Cross-Site Request Forgery protection (Synchronizer Token + Double Submit Cookie)
- HSTSMiddleware: HTTP Strict Transport Security
- HTTPSRedirectMiddleware: Force HTTPS with configurable exemptions
- ProxyFixMiddleware: Trusted-proxy X-Forwarded-* header correction
- SecurityHeadersMiddleware: Helmet-style catch-all security headers

Rate Limiting:
- RateLimitMiddleware: Token bucket + sliding window rate limiting

Static Files:
- StaticMiddleware: Production-grade static file serving (radix trie, ETag, range)

Logging:
- LoggingMiddleware: Structured access logging (CLF, JSON, dev)
"""

from aquilia.middleware_ext.effect_middleware import EffectMiddleware, FlowContextMiddleware
from aquilia.middleware_ext.logging import (
    CombinedLogFormatter,
    DevLogFormatter,
    LoggingMiddleware,
    StructuredLogFormatter,
)
from aquilia.middleware_ext.logging import LoggingMiddleware as EnhancedLoggingMiddleware
from aquilia.middleware_ext.rate_limit import (
    RateLimitMiddleware,
    RateLimitRule,
    api_key_extractor,
    ip_key_extractor,
    user_key_extractor,
)
from aquilia.middleware_ext.request_scope import RequestScopeMiddleware, SimplifiedRequestScopeMiddleware
from aquilia.middleware_ext.security import (
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
from aquilia.middleware_ext.session_middleware import SessionMiddleware
from aquilia.middleware_ext.static import StaticMiddleware

__all__ = [
    # Core
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
    # Rate Limiting
    "RateLimitMiddleware",
    "RateLimitRule",
    "ip_key_extractor",
    "api_key_extractor",
    "user_key_extractor",
    # Static Files
    "StaticMiddleware",
    # Logging
    "EnhancedLoggingMiddleware",
    "LoggingMiddleware",
    "CombinedLogFormatter",
    "StructuredLogFormatter",
    "DevLogFormatter",
    # Effect System
    "EffectMiddleware",
    "FlowContextMiddleware",
]
