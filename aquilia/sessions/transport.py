"""
AquilaSessions - Transport adapters.

Handles session ID extraction and injection across different transports:
- CookieTransport: HTTP cookies (most common)
- HeaderTransport: Custom headers (APIs, mobile apps)
"""

from __future__ import annotations

from typing import Protocol, TYPE_CHECKING
from datetime import datetime, timezone

if TYPE_CHECKING:
    from aquilia.request import Request
    from aquilia.response import Response
    from .core import Session, SessionID
    from .policy import TransportPolicy


# ============================================================================
# SessionTransport Protocol
# ============================================================================

class SessionTransport(Protocol):
    """
    Abstract transport interface for session ID delivery.
    
    Transports are responsible ONLY for:
    - Extracting session ID from requests
    - Injecting session ID into responses
    - Clearing session ID from responses
    """
    
    def extract(self, request: Request) -> str | None: ...
    def inject(self, response: Response, session: Session) -> None: ...
    def clear(self, response: Response) -> None: ...


# ============================================================================
# CookieTransport - HTTP Cookies
# ============================================================================

class CookieTransport:
    """
    Cookie-based session transport.
    
    Features:
    - HttpOnly flag (XSS protection)
    - Secure flag (HTTPS only)
    - SameSite policy (CSRF protection)
    - Configurable path and domain
    - Expiry based on session TTL
    """
    
    def __init__(self, policy: TransportPolicy):
        self.policy = policy
        self.cookie_name = policy.cookie_name
    
    def extract(self, request: Request) -> str | None:
        """Extract session ID from cookie."""
        cookie_header = request.header("cookie")
        if not cookie_header:
            return None
        cookies = self._parse_cookies(cookie_header)
        return cookies.get(self.cookie_name)
    
    def inject(self, response: Response, session: Session) -> None:
        """Inject session ID as cookie via response.set_cookie()."""
        session_id = str(session.id)
        
        # Safely compute max_age (fix: was unbound when expires_at is None)
        max_age = None
        if session.expires_at:
            now = datetime.now(timezone.utc)
            computed = int((session.expires_at - now).total_seconds())
            max_age = max(computed, 0)
        
        response.set_cookie(
            name=self.cookie_name,
            value=session_id,
            max_age=max_age,
            path=self.policy.cookie_path,
            domain=self.policy.cookie_domain,
            secure=self.policy.cookie_secure,
            httponly=self.policy.cookie_httponly,
            samesite=self.policy.cookie_samesite,
        )
    
    def clear(self, response: Response) -> None:
        """Clear session cookie (logout)."""
        if hasattr(response, 'delete_cookie'):
            response.delete_cookie(
                key=self.cookie_name,
                path=self.policy.cookie_path,
                domain=self.policy.cookie_domain,
            )
        else:
            # Fallback: set expired cookie
            response.set_cookie(
                name=self.cookie_name,
                value="deleted",
                max_age=0,
                path=self.policy.cookie_path,
                domain=self.policy.cookie_domain,
                secure=self.policy.cookie_secure,
                httponly=self.policy.cookie_httponly,
                samesite=self.policy.cookie_samesite,
            )
    
    @staticmethod
    def _parse_cookies(cookie_header: str) -> dict[str, str]:
        """Parse cookie header into dict."""
        cookies = {}
        for part in cookie_header.split(";"):
            part = part.strip()
            if "=" in part:
                name, value = part.split("=", 1)
                cookies[name.strip()] = value.strip()
        return cookies
    
    # ========================================================================
    # Factory Methods
    # ========================================================================
    
    @classmethod
    def for_web_browsers(cls) -> 'CookieTransport':
        from .policy import TransportPolicy
        policy = TransportPolicy(
            adapter="cookie",
            cookie_name="aquilia_web_session",
            cookie_httponly=True,
            cookie_secure=True,
            cookie_samesite="strict",
            cookie_path="/",
        )
        return cls(policy)
    
    @classmethod  
    def for_spa_applications(cls) -> 'CookieTransport':
        from .policy import TransportPolicy
        policy = TransportPolicy(
            adapter="cookie",
            cookie_name="aquilia_spa_session", 
            cookie_httponly=True,
            cookie_secure=True,
            cookie_samesite="lax",
            cookie_path="/",
        )
        return cls(policy)
    
    @classmethod
    def for_mobile_webviews(cls) -> 'CookieTransport':
        from .policy import TransportPolicy
        policy = TransportPolicy(
            adapter="cookie",
            cookie_name="aquilia_mobile_session",
            cookie_httponly=True,
            cookie_secure=True,
            cookie_samesite="none", 
            cookie_path="/",
        )
        return cls(policy)
    
    @classmethod
    def with_aquilia_defaults(cls) -> 'CookieTransport':
        from .policy import TransportPolicy
        policy = TransportPolicy(
            adapter="cookie",
            cookie_name="aquilia_session",
            cookie_httponly=True,
            cookie_secure=True,
            cookie_samesite="lax",
            cookie_path="/",
        )
        return cls(policy)


# ============================================================================
# HeaderTransport - Custom Header
# ============================================================================

class HeaderTransport:
    """
    Header-based session transport for APIs and mobile apps.
    """
    
    def __init__(self, policy: TransportPolicy):
        self.policy = policy
        self.header_name = policy.header_name
    
    def extract(self, request: Request) -> str | None:
        return request.header(self.header_name)
    
    def inject(self, response: Response, session: Session) -> None:
        session_id = str(session.id)
        response.headers[self.header_name] = session_id
    
    def clear(self, response: Response) -> None:
        if self.header_name in response.headers:
            del response.headers[self.header_name]
    
    # ========================================================================
    # Factory Methods
    # ========================================================================
    
    @classmethod
    def for_rest_apis(cls) -> 'HeaderTransport':
        from .policy import TransportPolicy
        policy = TransportPolicy(adapter="header", header_name="X-Session-ID")
        return cls(policy)
    
    @classmethod
    def for_graphql_apis(cls) -> 'HeaderTransport':
        from .policy import TransportPolicy
        policy = TransportPolicy(adapter="header", header_name="X-GraphQL-Session")
        return cls(policy)
    
    @classmethod
    def for_mobile_apis(cls) -> 'HeaderTransport':
        from .policy import TransportPolicy
        policy = TransportPolicy(adapter="header", header_name="X-Mobile-Session")
        return cls(policy)
    
    @classmethod
    def for_microservices(cls) -> 'HeaderTransport':
        from .policy import TransportPolicy
        policy = TransportPolicy(adapter="header", header_name="X-Service-Session")
        return cls(policy)
    
    @classmethod
    def with_aquilia_defaults(cls) -> 'HeaderTransport':
        from .policy import TransportPolicy
        policy = TransportPolicy(adapter="header", header_name="X-Aquilia-Session")
        return cls(policy)


# ============================================================================
# Transport Factory
# ============================================================================

def create_transport(policy: TransportPolicy) -> CookieTransport | HeaderTransport:
    """Create transport adapter from policy."""
    if policy.adapter == "cookie":
        return CookieTransport(policy)
    elif policy.adapter == "header":
        return HeaderTransport(policy)
    elif policy.adapter == "token":
        raise NotImplementedError("Token transport not yet implemented")
    else:
        raise ValueError(f"Unsupported transport adapter: {policy.adapter}")
