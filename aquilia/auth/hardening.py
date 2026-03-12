"""
AquilAuth - Security Hardening Utilities

Provides additional security layers:
- CSRF token generation and validation
- Security headers middleware
- Request fingerprinting for session binding
- Constant-time comparison utilities
- Token binding and proof-of-possession
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from dataclasses import dataclass
from typing import Any

# ============================================================================
# Constant-time Utilities
# ============================================================================


def constant_time_compare(a: str | bytes, b: str | bytes) -> bool:
    """
    Compare two strings/bytes in constant time to prevent timing attacks.

    Uses hmac.compare_digest under the hood.
    """
    if isinstance(a, str):
        a = a.encode("utf-8")
    if isinstance(b, str):
        b = b.encode("utf-8")
    return hmac.compare_digest(a, b)


# ============================================================================
# CSRF Protection
# ============================================================================


class CSRFProtection:
    """
    CSRF token generation and validation.

    Uses double-submit cookie pattern with HMAC signing.
    """

    def __init__(
        self,
        secret: str | None = None,
        token_length: int = 32,
        max_age: int = 3600,  # 1 hour
        header_name: str = "X-CSRF-Token",
        cookie_name: str = "csrf_token",
        safe_methods: frozenset[str] = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"}),
    ):
        self._secret = (secret or os.environ.get("CSRF_SECRET") or secrets.token_hex(32)).encode()
        self._token_length = token_length
        self._max_age = max_age
        self.header_name = header_name
        self.cookie_name = cookie_name
        self.safe_methods = safe_methods

    def generate_token(self) -> str:
        """Generate a new CSRF token."""
        nonce = secrets.token_hex(self._token_length)
        timestamp = str(int(time.time()))
        payload = f"{nonce}:{timestamp}"
        signature = hmac.new(self._secret, payload.encode(), hashlib.sha256).hexdigest()
        return f"{payload}:{signature}"

    def validate_token(self, token: str) -> bool:
        """Validate a CSRF token."""
        if not token or ":" not in token:
            return False

        parts = token.split(":")
        if len(parts) != 3:
            return False

        nonce, timestamp_str, signature = parts

        # Verify signature
        payload = f"{nonce}:{timestamp_str}"
        expected = hmac.new(self._secret, payload.encode(), hashlib.sha256).hexdigest()

        if not constant_time_compare(signature, expected):
            return False

        # Verify expiry
        try:
            ts = int(timestamp_str)
            if time.time() - ts > self._max_age:
                return False
        except (ValueError, OverflowError):
            return False

        return True

    def requires_validation(self, method: str) -> bool:
        """Check if the HTTP method requires CSRF validation."""
        return method.upper() not in self.safe_methods


# ============================================================================
# Request Fingerprinting
# ============================================================================


@dataclass(frozen=True, slots=True)
class RequestFingerprint:
    """
    Fingerprint a request for session binding.

    Binds sessions to client characteristics to detect hijacking.
    """

    ip_hash: str
    ua_hash: str
    accept_hash: str

    @classmethod
    def from_request(cls, request: Any) -> RequestFingerprint:
        """Create fingerprint from a request object."""
        # IP
        ip = ""
        if hasattr(request, "client") and request.client:
            ip = request.client[0] if isinstance(request.client, tuple) else str(request.client)

        # User-Agent
        ua = ""
        accept_lang = ""
        if hasattr(request, "headers"):
            headers = request.headers
            if hasattr(headers, "get"):
                ua = headers.get("user-agent", "")
                accept_lang = headers.get("accept-language", "")

        return cls(
            ip_hash=hashlib.sha256(ip.encode()).hexdigest()[:16],
            ua_hash=hashlib.sha256(ua.encode()).hexdigest()[:16],
            accept_hash=hashlib.sha256(accept_lang.encode()).hexdigest()[:8],
        )

    def matches(self, other: RequestFingerprint, strict: bool = False) -> bool:
        """
        Check if another fingerprint matches this one.

        Args:
            other: Fingerprint to compare
            strict: If True, all fields must match.
                    If False, 2/3 must match (allows IP change).
        """
        matches = sum(
            [
                constant_time_compare(self.ip_hash, other.ip_hash),
                constant_time_compare(self.ua_hash, other.ua_hash),
                constant_time_compare(self.accept_hash, other.accept_hash),
            ]
        )

        if strict:
            return matches == 3
        return matches >= 2

    def to_string(self) -> str:
        """Serialize to storable string."""
        return f"{self.ip_hash}:{self.ua_hash}:{self.accept_hash}"

    @classmethod
    def from_string(cls, s: str) -> RequestFingerprint | None:
        """Deserialize from string."""
        parts = s.split(":")
        if len(parts) != 3:
            return None
        return cls(ip_hash=parts[0], ua_hash=parts[1], accept_hash=parts[2])


# ============================================================================
# Security Headers
# ============================================================================


@dataclass
class SecurityHeaders:
    """
    Configurable security headers for HTTP responses.

    Implements OWASP recommended headers.
    """

    # Content Security Policy
    content_security_policy: str = "default-src 'self'"

    # Strict Transport Security (HSTS)
    strict_transport_security: str = "max-age=31536000; includeSubDomains"

    # X-Content-Type-Options
    x_content_type_options: str = "nosniff"

    # X-Frame-Options
    x_frame_options: str = "DENY"

    # Referrer-Policy
    referrer_policy: str = "strict-origin-when-cross-origin"

    # Permissions-Policy
    permissions_policy: str = "geolocation=(), camera=(), microphone=()"

    # Cross-Origin policies
    cross_origin_opener_policy: str = "same-origin"
    cross_origin_embedder_policy: str = "require-corp"
    cross_origin_resource_policy: str = "same-origin"

    # Cache-Control for sensitive responses
    cache_control: str = "no-store, no-cache, must-revalidate"

    # Pragma (legacy cache control)
    pragma: str = "no-cache"

    def apply(self, response: Any) -> Any:
        """Apply security headers to a response object."""
        headers = {
            "Content-Security-Policy": self.content_security_policy,
            "Strict-Transport-Security": self.strict_transport_security,
            "X-Content-Type-Options": self.x_content_type_options,
            "X-Frame-Options": self.x_frame_options,
            "Referrer-Policy": self.referrer_policy,
            "Permissions-Policy": self.permissions_policy,
            "Cross-Origin-Opener-Policy": self.cross_origin_opener_policy,
            "Cross-Origin-Resource-Policy": self.cross_origin_resource_policy,
            "Cache-Control": self.cache_control,
            "Pragma": self.pragma,
        }

        if self.cross_origin_embedder_policy:
            headers["Cross-Origin-Embedder-Policy"] = self.cross_origin_embedder_policy

        if (
            hasattr(response, "headers")
            and hasattr(response.headers, "update")
            or hasattr(response, "headers")
            and isinstance(response.headers, dict)
        ):
            response.headers.update(headers)

        return response

    def to_dict(self) -> dict[str, str]:
        """Return headers as a dictionary."""
        return {
            "Content-Security-Policy": self.content_security_policy,
            "Strict-Transport-Security": self.strict_transport_security,
            "X-Content-Type-Options": self.x_content_type_options,
            "X-Frame-Options": self.x_frame_options,
            "Referrer-Policy": self.referrer_policy,
            "Permissions-Policy": self.permissions_policy,
            "Cross-Origin-Opener-Policy": self.cross_origin_opener_policy,
            "Cross-Origin-Resource-Policy": self.cross_origin_resource_policy,
            "Cache-Control": self.cache_control,
            "Pragma": self.pragma,
        }


# ============================================================================
# Token Binding
# ============================================================================


class TokenBinder:
    """
    Binds tokens to client characteristics for proof-of-possession.

    Prevents token theft by requiring the token to be used from
    the same client that originally obtained it.
    """

    def __init__(self, secret: str | None = None):
        self._secret = (secret or os.environ.get("TOKEN_BIND_SECRET") or secrets.token_hex(32)).encode()

    def create_binding(self, token: str, fingerprint: RequestFingerprint) -> str:
        """
        Create a binding hash for a token + fingerprint combination.

        Store this alongside the token to verify later.
        """
        binding_input = f"{token}:{fingerprint.to_string()}"
        return hmac.new(self._secret, binding_input.encode(), hashlib.sha256).hexdigest()

    def verify_binding(
        self,
        token: str,
        fingerprint: RequestFingerprint,
        expected_binding: str,
    ) -> bool:
        """
        Verify that a token is being used from the expected client.
        """
        actual = self.create_binding(token, fingerprint)
        return constant_time_compare(actual, expected_binding)


# ============================================================================
# Secure Token Generation
# ============================================================================


def generate_secure_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token."""
    return secrets.token_urlsafe(length)


def generate_opaque_id(prefix: str = "aq") -> str:
    """Generate an opaque identifier with prefix."""
    return f"{prefix}_{secrets.token_hex(16)}"


def hash_token(token: str) -> str:
    """Hash a token for storage (one-way)."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_sensitive(value: str, salt: str = "") -> str:
    """Hash sensitive data with optional salt."""
    data = f"{salt}:{value}" if salt else value
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


# ============================================================================
# Exports
# ============================================================================


__all__ = [
    "constant_time_compare",
    "CSRFProtection",
    "RequestFingerprint",
    "SecurityHeaders",
    "TokenBinder",
    "generate_secure_token",
    "generate_opaque_id",
    "hash_token",
    "hash_sensitive",
]
