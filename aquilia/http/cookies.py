"""
AquilaHTTP — Cookie Jar.

Cookie management with domain/path matching, expiration,
and persistence support.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from http.cookies import SimpleCookie
from typing import Any
from urllib.parse import urlparse

logger = logging.getLogger("aquilia.http.cookies")


@dataclass
class Cookie:
    """
    HTTP Cookie representation.

    Attributes:
        name: Cookie name.
        value: Cookie value.
        domain: Domain the cookie applies to.
        path: Path the cookie applies to.
        expires: Expiration timestamp (seconds since epoch).
        max_age: Max-Age in seconds.
        secure: Only send over HTTPS.
        http_only: Not accessible via JavaScript.
        same_site: SameSite attribute (Strict, Lax, None).
    """

    name: str
    value: str
    domain: str = ""
    path: str = "/"
    expires: float | None = None
    max_age: int | None = None
    secure: bool = False
    http_only: bool = False
    same_site: str = ""

    @property
    def is_expired(self) -> bool:
        """Check if cookie has expired."""
        if self.max_age is not None:
            # max_age takes precedence over expires
            return False  # Need creation time to check this

        if self.expires is not None:
            return time.time() > self.expires

        return False

    @property
    def is_session(self) -> bool:
        """Check if this is a session cookie (no expiry)."""
        return self.expires is None and self.max_age is None

    def matches_domain(self, request_domain: str) -> bool:
        """Check if cookie matches the request domain."""
        if not self.domain:
            return True

        cookie_domain = self.domain.lower().lstrip(".")
        request_domain = request_domain.lower()

        # Exact match
        if request_domain == cookie_domain:
            return True

        # Subdomain match (cookie domain starts with .)
        if self.domain.startswith("."):
            return request_domain.endswith("." + cookie_domain) or request_domain == cookie_domain

        return False

    def matches_path(self, request_path: str) -> bool:
        """Check if cookie matches the request path."""
        if not self.path or self.path == "/":
            return True

        cookie_path = self.path.rstrip("/")
        request_path = request_path or "/"

        # Exact match
        if request_path == cookie_path:
            return True

        # Path prefix match
        if request_path.startswith(cookie_path + "/"):
            return True

        return False

    def matches(self, url: str) -> bool:
        """Check if cookie matches the URL."""
        parsed = urlparse(url)
        domain = parsed.netloc.split(":")[0]  # Remove port
        path = parsed.path or "/"

        # Check secure
        if self.secure and parsed.scheme != "https":
            return False

        # Check domain and path
        return self.matches_domain(domain) and self.matches_path(path)

    def to_header_value(self) -> str:
        """Format as cookie header value (name=value)."""
        return f"{self.name}={self.value}"

    def to_set_cookie(self) -> str:
        """Format as Set-Cookie header value."""
        parts = [f"{self.name}={self.value}"]

        if self.domain:
            parts.append(f"Domain={self.domain}")
        if self.path:
            parts.append(f"Path={self.path}")
        if self.expires is not None:
            from email.utils import formatdate

            parts.append(f"Expires={formatdate(self.expires, usegmt=True)}")
        if self.max_age is not None:
            parts.append(f"Max-Age={self.max_age}")
        if self.secure:
            parts.append("Secure")
        if self.http_only:
            parts.append("HttpOnly")
        if self.same_site:
            parts.append(f"SameSite={self.same_site}")

        return "; ".join(parts)

    @classmethod
    def from_set_cookie(cls, header: str, request_url: str = "") -> Cookie:
        """
        Parse a Set-Cookie header.

        Args:
            header: Set-Cookie header value.
            request_url: Request URL for domain inference.

        Returns:
            Cookie instance.
        """
        # Parse using SimpleCookie
        cookie: SimpleCookie[str] = SimpleCookie()
        cookie.load(header)

        # Get the first (and should be only) morsel
        for name, morsel in cookie.items():
            domain = morsel.get("domain", "")
            path = morsel.get("path", "/")
            secure = morsel.get("secure", False)
            http_only = morsel.get("httponly", False)
            same_site = morsel.get("samesite", "")

            # Parse expires
            expires = None
            expires_str = morsel.get("expires", "")
            if expires_str:
                try:
                    from email.utils import parsedate_to_datetime

                    dt = parsedate_to_datetime(expires_str)
                    expires = dt.timestamp()
                except (TypeError, ValueError):
                    pass

            # Parse max-age
            max_age = None
            max_age_str = morsel.get("max-age", "")
            if max_age_str:
                try:
                    max_age = int(max_age_str)
                except ValueError:
                    pass

            # Infer domain from request URL if not set
            if not domain and request_url:
                parsed = urlparse(request_url)
                domain = parsed.netloc.split(":")[0]

            return cls(
                name=name,
                value=morsel.value,
                domain=domain,
                path=path or "/",
                expires=expires,
                max_age=max_age,
                secure=bool(secure),
                http_only=bool(http_only),
                same_site=same_site,
            )

        # Fallback: manual parsing for malformed cookies
        parts = header.split(";")
        if not parts:
            raise ValueError(f"Invalid Set-Cookie header: {header}")

        name_value = parts[0].strip()
        if "=" not in name_value:
            raise ValueError(f"Invalid cookie name=value: {name_value}")

        name, value = name_value.split("=", 1)
        return cls(name=name.strip(), value=value.strip())


class CookieJar:
    """
    Thread-safe cookie storage.

    Manages cookies with automatic expiration and domain matching.
    """

    __slots__ = ("_cookies", "_ignore_expired")

    def __init__(self, ignore_expired: bool = True):
        self._cookies: dict[str, Cookie] = {}
        self._ignore_expired = ignore_expired

    def _cookie_key(self, cookie: Cookie) -> str:
        """Generate unique key for a cookie."""
        return f"{cookie.domain}:{cookie.path}:{cookie.name}"

    def set(self, cookie: Cookie) -> None:
        """
        Add or update a cookie.

        Args:
            cookie: Cookie to store.
        """
        key = self._cookie_key(cookie)

        # If max_age is 0 or negative, delete the cookie
        if cookie.max_age is not None and cookie.max_age <= 0:
            self._cookies.pop(key, None)
            return

        # If cookie is already expired, don't store it
        if cookie.is_expired and self._ignore_expired:
            return

        self._cookies[key] = cookie

    def set_from_response(
        self,
        headers: dict[str, str] | list[tuple[str, str]],
        request_url: str,
    ) -> list[Cookie]:
        """
        Extract and store cookies from response headers.

        Args:
            headers: Response headers.
            request_url: The request URL.

        Returns:
            List of cookies that were set.
        """
        cookies: list[Cookie] = []

        # Handle both dict and list of tuples
        if isinstance(headers, dict):
            items = headers.items()
        else:
            items = headers

        for name, value in items:
            if name.lower() == "set-cookie":
                try:
                    cookie = Cookie.from_set_cookie(value, request_url)
                    self.set(cookie)
                    cookies.append(cookie)
                except ValueError as e:
                    logger.warning(f"Failed to parse Set-Cookie: {e}")

        return cookies

    def get(self, name: str, domain: str = "", path: str = "/") -> Cookie | None:
        """
        Get a specific cookie.

        Args:
            name: Cookie name.
            domain: Domain to match.
            path: Path to match.

        Returns:
            Cookie if found and not expired.
        """
        for cookie in self._cookies.values():
            if cookie.name != name:
                continue

            if domain and not cookie.matches_domain(domain):
                continue

            if path and not cookie.matches_path(path):
                continue

            if cookie.is_expired and self._ignore_expired:
                continue

            return cookie

        return None

    def get_for_url(self, url: str) -> list[Cookie]:
        """
        Get all cookies that match a URL.

        Args:
            url: Request URL.

        Returns:
            List of matching cookies.
        """
        matching: list[Cookie] = []

        for cookie in self._cookies.values():
            if cookie.is_expired and self._ignore_expired:
                continue

            if cookie.matches(url):
                matching.append(cookie)

        # Sort by path specificity (longer paths first)
        matching.sort(key=lambda c: len(c.path), reverse=True)

        return matching

    def get_header(self, url: str) -> str | None:
        """
        Get Cookie header value for a URL.

        Args:
            url: Request URL.

        Returns:
            Cookie header value or None if no cookies match.
        """
        cookies = self.get_for_url(url)
        if not cookies:
            return None

        return "; ".join(c.to_header_value() for c in cookies)

    def delete(self, name: str, domain: str = "", path: str = "/") -> bool:
        """
        Delete a cookie.

        Args:
            name: Cookie name.
            domain: Domain to match.
            path: Path to match.

        Returns:
            True if cookie was deleted.
        """
        to_delete = []

        for key, cookie in self._cookies.items():
            if cookie.name != name:
                continue

            if domain and cookie.domain != domain:
                continue

            if path and cookie.path != path:
                continue

            to_delete.append(key)

        for key in to_delete:
            del self._cookies[key]

        return len(to_delete) > 0

    def clear(self, domain: str = "") -> int:
        """
        Clear cookies.

        Args:
            domain: If set, only clear cookies for this domain.

        Returns:
            Number of cookies cleared.
        """
        if not domain:
            count = len(self._cookies)
            self._cookies.clear()
            return count

        to_delete = [key for key, cookie in self._cookies.items() if cookie.matches_domain(domain)]

        for key in to_delete:
            del self._cookies[key]

        return len(to_delete)

    def cleanup_expired(self) -> int:
        """
        Remove expired cookies.

        Returns:
            Number of cookies removed.
        """
        to_delete = [key for key, cookie in self._cookies.items() if cookie.is_expired]

        for key in to_delete:
            del self._cookies[key]

        return len(to_delete)

    def all(self) -> list[Cookie]:
        """Get all non-expired cookies."""
        if self._ignore_expired:
            return [c for c in self._cookies.values() if not c.is_expired]
        return list(self._cookies.values())

    def to_dict(self) -> dict[str, str]:
        """Export cookies as simple dict."""
        return {c.name: c.value for c in self.all()}

    def __len__(self) -> int:
        return len(self.all())

    def __contains__(self, name: str) -> bool:
        return any(c.name == name for c in self.all())

    def __iter__(self):
        return iter(self.all())


class CookieInterceptor:
    """
    Interceptor that manages cookies automatically.

    Adds cookies to requests and stores cookies from responses.
    """

    __slots__ = ("_jar",)

    def __init__(self, jar: CookieJar | None = None):
        self._jar = jar or CookieJar()

    @property
    def jar(self) -> CookieJar:
        return self._jar

    async def intercept(
        self,
        request: Any,  # HTTPClientRequest
        next_handler: Any,  # Callable
    ) -> Any:  # HTTPClientResponse
        # Add cookies to request
        cookie_header = self._jar.get_header(request.url)
        if cookie_header:
            new_headers = dict(request.headers)
            existing = new_headers.get("Cookie", "")
            if existing:
                new_headers["Cookie"] = f"{existing}; {cookie_header}"
            else:
                new_headers["Cookie"] = cookie_header
            request = request.copy(headers=new_headers)

        # Execute request
        response = await next_handler(request)

        # Store cookies from response
        self._jar.set_from_response(response.headers, request.url)

        return response
