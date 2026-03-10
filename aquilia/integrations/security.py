"""
Security integrations — CORS, CSP, Rate-Limit, CSRF.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CorsIntegration:
    """
    Typed CORS middleware configuration.

    Example::

        CorsIntegration(
            allow_origins=["https://example.com"],
            allow_credentials=True,
        )
    """

    _integration_type: str = field(default="cors", init=False, repr=False)

    allow_origins: List[str] = field(default_factory=lambda: ["*"])
    allow_methods: List[str] = field(
        default_factory=lambda: ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
    )
    allow_headers: List[str] = field(
        default_factory=lambda: [
            "accept", "accept-language", "content-language",
            "content-type", "authorization", "x-requested-with",
        ]
    )
    expose_headers: List[str] = field(default_factory=list)
    allow_credentials: bool = False
    max_age: int = 600
    allow_origin_regex: Optional[str] = None
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_integration_type": "cors",
            "enabled": self.enabled,
            "allow_origins": self.allow_origins,
            "allow_methods": self.allow_methods,
            "allow_headers": self.allow_headers,
            "expose_headers": self.expose_headers,
            "allow_credentials": self.allow_credentials,
            "max_age": self.max_age,
            "allow_origin_regex": self.allow_origin_regex,
        }


@dataclass
class CspIntegration:
    """
    Typed Content-Security-Policy configuration.

    Example::

        CspIntegration(
            policy={"default-src": ["'self'"]},
            nonce=True,
        )
    """

    _integration_type: str = field(default="csp", init=False, repr=False)

    policy: Optional[Dict[str, List[str]]] = None
    report_only: bool = False
    nonce: bool = True
    preset: str = "strict"
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_integration_type": "csp",
            "enabled": self.enabled,
            "policy": self.policy,
            "report_only": self.report_only,
            "nonce": self.nonce,
            "preset": self.preset,
        }


@dataclass
class RateLimitIntegration:
    """
    Typed rate limiting configuration.

    Example::

        RateLimitIntegration(limit=200, window=60, burst=50)
    """

    _integration_type: str = field(default="rate_limit", init=False, repr=False)

    limit: int = 100
    window: int = 60
    algorithm: str = "sliding_window"
    per_user: bool = False
    burst: Optional[int] = None
    exempt_paths: List[str] = field(
        default_factory=lambda: ["/health", "/healthz", "/ready"]
    )
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_integration_type": "rate_limit",
            "enabled": self.enabled,
            "limit": self.limit,
            "window": self.window,
            "algorithm": self.algorithm,
            "per_user": self.per_user,
            "burst": self.burst,
            "exempt_paths": self.exempt_paths,
        }


@dataclass
class CsrfIntegration:
    """
    Typed CSRF protection configuration.

    Example::

        CsrfIntegration(
            secret_key="my-secret",
            exempt_paths=["/api/webhooks"],
        )
    """

    _integration_type: str = field(default="csrf", init=False, repr=False)

    secret_key: str = ""
    token_length: int = 32
    header_name: str = "X-CSRF-Token"
    field_name: str = "_csrf_token"
    cookie_name: str = "_csrf_cookie"
    cookie_path: str = "/"
    cookie_domain: Optional[str] = None
    cookie_secure: bool = True
    cookie_samesite: str = "Lax"
    cookie_httponly: bool = False
    cookie_max_age: int = 3600
    safe_methods: List[str] = field(
        default_factory=lambda: ["GET", "HEAD", "OPTIONS", "TRACE"]
    )
    exempt_paths: List[str] = field(default_factory=list)
    exempt_content_types: List[str] = field(default_factory=list)
    trust_ajax: bool = True
    rotate_token: bool = False
    failure_status: int = 403
    enabled: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "_integration_type": "csrf",
            "enabled": self.enabled,
            "secret_key": self.secret_key,
            "token_length": self.token_length,
            "header_name": self.header_name,
            "field_name": self.field_name,
            "cookie_name": self.cookie_name,
            "cookie_path": self.cookie_path,
            "cookie_domain": self.cookie_domain,
            "cookie_secure": self.cookie_secure,
            "cookie_samesite": self.cookie_samesite,
            "cookie_httponly": self.cookie_httponly,
            "cookie_max_age": self.cookie_max_age,
            "safe_methods": self.safe_methods,
            "exempt_paths": self.exempt_paths,
            "exempt_content_types": self.exempt_content_types,
            "trust_ajax": self.trust_ajax,
            "rotate_token": self.rotate_token,
            "failure_status": self.failure_status,
        }
