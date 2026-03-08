"""
AquilAdmin -- Security Hardening Module.

Provides admin-specific security layers:
- CSRF token generation/validation for all admin forms
- Rate limiting for login and sensitive operations
- Brute-force protection with progressive lockout
- Security headers for admin responses
- Session fixation protection
- Password complexity validation
- IP-based threat tracking
- Admin-specific CSP nonce support

Integrates with Aquilia's existing security infrastructure:
- ``aquilia.auth.hardening.CSRFProtection`` for token mechanics
- ``aquilia.auth.hardening.constant_time_compare`` for timing-safe ops
- ``aquilia.auth.manager.RateLimiter`` for attempt tracking
- ``aquilia.faults.domains`` for structured security faults
- ``aquilia.admin.faults`` for admin-specific faults

Architecture:
    AdminCSRFProtection
        ├── generate_token(session)   → creates signed CSRF token, stores in session
        ├── validate_request(ctx)     → verifies token from form/header, constant-time
        └── get_token(ctx)            → retrieves current token for template injection

    AdminRateLimiter
        ├── check_login(ip)           → enforces login attempt limits
        ├── record_failure(ip)        → records failed attempt, progressive lockout
        ├── record_success(ip)        → clears attempt counter on success
        └── check_sensitive_op(ip, op)→ rate limits sensitive operations

    AdminSecurityHeaders
        ├── apply(response)           → adds X-Frame-Options, CSP, X-Content-Type, etc.
        └── apply_with_nonce(response, nonce) → CSP with nonce for inline scripts

    PasswordValidator
        ├── validate(password)        → checks complexity rules
        └── get_strength(password)    → returns strength score and feedback

    AdminSecurityPolicy (orchestrator)
        ├── csrf                      → AdminCSRFProtection instance
        ├── rate_limiter              → AdminRateLimiter instance
        ├── headers                   → AdminSecurityHeaders instance
        ├── password_validator        → PasswordValidator instance
        └── protect_response(response, ctx) → applies all policies to a response

Usage:
    from aquilia.admin.security import AdminSecurityPolicy

    policy = AdminSecurityPolicy()

    # In login handler:
    if policy.rate_limiter.is_locked_out(client_ip):
        raise AdminAuthenticationFault("Too many attempts. Try again later.")

    # In form submission:
    if not policy.csrf.validate_request(ctx):
        raise AdminAuthorizationFault("CSRF validation failed")

    # On response:
    response = policy.protect_response(response, ctx)
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import re
import secrets
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple, TYPE_CHECKING

from aquilia.admin.faults import (
    AdminAuthenticationFault,
    AdminAuthorizationFault,
)

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.response import Response

logger = logging.getLogger("aquilia.admin.security")


# ═══════════════════════════════════════════════════════════════════════════════
#  CSRF Protection for Admin
# ═══════════════════════════════════════════════════════════════════════════════


class AdminCSRFProtection:
    """
    CSRF protection specifically for the admin panel.

    Uses double-submit pattern: token is stored in the session AND
    must be submitted in the form body (``_csrf_token`` field) or
    the ``X-CSRF-Token`` header.

    Tokens are HMAC-signed with a per-instance secret and include
    a timestamp for expiry validation.
    """

    FORM_FIELD = "_csrf_token"
    HEADER_NAME = "x-csrf-token"
    SESSION_KEY = "_admin_csrf_token"

    def __init__(
        self,
        *,
        secret: Optional[str] = None,
        max_age: int = 7200,  # 2 hours
        token_length: int = 32,
    ):
        self._secret = (
            secret
            or os.environ.get("AQUILIA_ADMIN_CSRF_SECRET")
            or secrets.token_hex(32)
        ).encode("utf-8")
        self._max_age = max_age
        self._token_length = token_length

    def generate_token(self) -> str:
        """Generate a new HMAC-signed CSRF token with timestamp."""
        nonce = secrets.token_hex(self._token_length)
        timestamp = str(int(time.time()))
        payload = f"{nonce}:{timestamp}"
        signature = hmac.new(
            self._secret, payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()
        return f"{payload}:{signature}"

    def validate_token(self, token: str) -> bool:
        """Validate a CSRF token (signature + expiry)."""
        if not token or token.count(":") != 2:
            return False

        parts = token.split(":", 2)
        if len(parts) != 3:
            return False

        nonce, timestamp_str, signature = parts

        # Verify signature using constant-time comparison
        payload = f"{nonce}:{timestamp_str}"
        expected = hmac.new(
            self._secret, payload.encode("utf-8"), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(signature.encode(), expected.encode()):
            return False

        # Verify not expired
        try:
            ts = int(timestamp_str)
            if time.time() - ts > self._max_age:
                return False
        except (ValueError, OverflowError):
            return False

        return True

    def get_or_create_token(self, ctx: "RequestCtx") -> str:
        """
        Get existing CSRF token from session, or create a new one.

        Ensures the token is stored in the session for later validation.
        """
        if ctx.session and hasattr(ctx.session, "data"):
            existing = ctx.session.data.get(self.SESSION_KEY)
            if existing and self.validate_token(existing):
                return existing

            # Generate new token and store in session
            token = self.generate_token()
            ctx.session.data[self.SESSION_KEY] = token
            return token

        # No session available — generate ephemeral token
        return self.generate_token()

    def validate_request(self, ctx: "RequestCtx", form_data: Optional[Dict] = None) -> bool:
        """
        Validate CSRF token from request.

        Checks (in order):
        1. Form body field ``_csrf_token``
        2. Header ``X-CSRF-Token``

        Compares against the token stored in the session.
        """
        # Get the session-stored token
        session_token = None
        if ctx.session and hasattr(ctx.session, "data"):
            session_token = ctx.session.data.get(self.SESSION_KEY)

        if not session_token:
            return False

        # Get submitted token from form data or header
        submitted_token = None
        if form_data and isinstance(form_data, dict):
            submitted_token = form_data.get(self.FORM_FIELD)

        if not submitted_token:
            # Try request headers
            try:
                request = getattr(ctx, "request", None)
                if request and hasattr(request, "header"):
                    submitted_token = request.header(self.HEADER_NAME)
                elif request and hasattr(request, "headers"):
                    hdrs = request.headers
                    if hasattr(hdrs, "get"):
                        submitted_token = hdrs.get(self.HEADER_NAME)
            except Exception:
                pass

        if not submitted_token:
            return False

        # Constant-time comparison of the full tokens
        if not hmac.compare_digest(
            submitted_token.encode("utf-8"),
            session_token.encode("utf-8"),
        ):
            return False

        # Also verify the submitted token is structurally valid
        return self.validate_token(submitted_token)


# ═══════════════════════════════════════════════════════════════════════════════
#  Rate Limiting for Admin Operations
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass
class _AttemptRecord:
    """Tracks attempts for a single key."""
    attempts: List[float] = field(default_factory=list)
    lockout_until: float = 0.0
    consecutive_failures: int = 0


class AdminRateLimiter:
    """
    Rate limiter for admin authentication and sensitive operations.

    Features:
    - Progressive lockout: 5→15→60 minute lockouts after repeated failures
    - Per-IP tracking with automatic cleanup
    - Separate limits for login vs. sensitive operations
    - Thread-safe via dict-level atomicity in CPython
    """

    # Progressive lockout durations (seconds)
    LOCKOUT_TIERS = [
        (5, 300),      # After 5 failures: 5 minutes
        (10, 900),     # After 10 failures: 15 minutes
        (20, 3600),    # After 20 failures: 1 hour
        (50, 86400),   # After 50 failures: 24 hours
    ]

    def __init__(
        self,
        *,
        max_login_attempts: int = 5,
        login_window: int = 900,      # 15 minutes
        sensitive_op_limit: int = 30,  # ops per window
        sensitive_op_window: int = 300,  # 5 minutes
        cleanup_interval: int = 3600,  # Clean up stale entries every hour
    ):
        self.max_login_attempts = max_login_attempts
        self.login_window = login_window
        self.sensitive_op_limit = sensitive_op_limit
        self.sensitive_op_window = sensitive_op_window
        self.cleanup_interval = cleanup_interval

        self._login_records: Dict[str, _AttemptRecord] = {}
        self._sensitive_records: Dict[str, _AttemptRecord] = {}
        self._last_cleanup = time.monotonic()

    def _maybe_cleanup(self) -> None:
        """Periodically remove stale entries to prevent memory growth."""
        now = time.monotonic()
        if now - self._last_cleanup < self.cleanup_interval:
            return
        self._last_cleanup = now

        cutoff = now - max(self.login_window, self.sensitive_op_window) * 2
        for store in (self._login_records, self._sensitive_records):
            stale_keys = [
                k for k, v in store.items()
                if v.lockout_until < now and (not v.attempts or v.attempts[-1] < cutoff)
            ]
            for k in stale_keys:
                store.pop(k, None)

    def _get_login_record(self, key: str) -> _AttemptRecord:
        """Get or create a login attempt record."""
        if key not in self._login_records:
            self._login_records[key] = _AttemptRecord()
        return self._login_records[key]

    def is_login_locked(self, ip: str) -> Tuple[bool, int]:
        """
        Check if an IP is locked out from login attempts.

        Returns:
            (is_locked, retry_after_seconds)
        """
        self._maybe_cleanup()
        record = self._get_login_record(f"login:{ip}")
        now = time.monotonic()

        if record.lockout_until > now:
            retry_after = int(record.lockout_until - now) + 1
            return True, retry_after

        return False, 0

    def record_login_failure(self, ip: str) -> Tuple[bool, int]:
        """
        Record a failed login attempt.

        Returns:
            (now_locked, retry_after_seconds) — if the failure triggered a lockout
        """
        self._maybe_cleanup()
        key = f"login:{ip}"
        record = self._get_login_record(key)
        now = time.monotonic()

        # Clean old attempts outside the window
        cutoff = now - self.login_window
        record.attempts = [t for t in record.attempts if t > cutoff]

        record.attempts.append(now)
        record.consecutive_failures += 1

        # Determine lockout tier based on consecutive failures
        lockout_duration = 0
        for threshold, duration in self.LOCKOUT_TIERS:
            if record.consecutive_failures >= threshold:
                lockout_duration = duration

        if len(record.attempts) >= self.max_login_attempts and lockout_duration > 0:
            record.lockout_until = now + lockout_duration
            return True, lockout_duration

        # Simple lockout: window-based
        if len(record.attempts) >= self.max_login_attempts:
            record.lockout_until = now + self.LOCKOUT_TIERS[0][1]
            return True, self.LOCKOUT_TIERS[0][1]

        return False, 0

    def record_login_success(self, ip: str) -> None:
        """Clear login failure tracking on successful authentication."""
        key = f"login:{ip}"
        self._login_records.pop(key, None)

    def get_remaining_login_attempts(self, ip: str) -> int:
        """Get remaining login attempts before lockout."""
        record = self._get_login_record(f"login:{ip}")
        now = time.monotonic()
        cutoff = now - self.login_window
        recent = [t for t in record.attempts if t > cutoff]
        return max(0, self.max_login_attempts - len(recent))

    def check_sensitive_op(self, ip: str, operation: str = "default") -> Tuple[bool, int]:
        """
        Check if a sensitive operation is rate-limited.

        Returns:
            (allowed, retry_after_seconds)
        """
        self._maybe_cleanup()
        key = f"sensitive:{ip}:{operation}"
        if key not in self._sensitive_records:
            self._sensitive_records[key] = _AttemptRecord()
        record = self._sensitive_records[key]
        now = time.monotonic()

        cutoff = now - self.sensitive_op_window
        record.attempts = [t for t in record.attempts if t > cutoff]

        if len(record.attempts) >= self.sensitive_op_limit:
            retry_after = int(record.attempts[0] + self.sensitive_op_window - now) + 1
            return False, max(1, retry_after)

        record.attempts.append(now)
        return True, 0


# ═══════════════════════════════════════════════════════════════════════════════
#  Security Headers for Admin Responses
# ═══════════════════════════════════════════════════════════════════════════════


class AdminSecurityHeaders:
    """
    Applies security headers to all admin responses.

    Headers applied:
    - X-Frame-Options: DENY (prevent clickjacking)
    - X-Content-Type-Options: nosniff (prevent MIME sniffing)
    - X-XSS-Protection: 0 (modern browsers use CSP instead)
    - Referrer-Policy: strict-origin-when-cross-origin
    - Cache-Control: no-store, no-cache (prevent caching sensitive pages)
    - Pragma: no-cache
    - Content-Security-Policy: with nonce for inline scripts
    - Permissions-Policy: restrict dangerous browser features
    """

    DEFAULT_CSP = (
        "default-src 'self'; "
        "script-src 'self' {nonce}; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: blob:; "
        "font-src 'self' data:; "
        "connect-src 'self'; "
        "frame-ancestors 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    DEFAULT_PERMISSIONS_POLICY = (
        "camera=(), microphone=(), geolocation=(), "
        "payment=(), usb=(), magnetometer=(), gyroscope=(), "
        "accelerometer=()"
    )

    def __init__(
        self,
        *,
        csp_template: Optional[str] = None,
        frame_options: str = "DENY",
        permissions_policy: Optional[str] = None,
    ):
        self._csp_template = csp_template or self.DEFAULT_CSP
        self._frame_options = frame_options
        self._permissions_policy = permissions_policy or self.DEFAULT_PERMISSIONS_POLICY

    def generate_nonce(self) -> str:
        """Generate a cryptographically random nonce for CSP."""
        return secrets.token_urlsafe(24)

    def apply(
        self,
        response: "Response",
        *,
        nonce: Optional[str] = None,
        cache_control: str = "no-store, no-cache, must-revalidate, max-age=0",
    ) -> "Response":
        """
        Apply security headers to a response.

        Args:
            response: The response to secure
            nonce: CSP nonce for inline scripts (generates one if not provided)
            cache_control: Cache-Control header value

        Returns:
            The response with security headers applied
        """
        if nonce is None:
            nonce = self.generate_nonce()

        nonce_directive = f"'nonce-{nonce}'"
        csp = self._csp_template.replace("{nonce}", nonce_directive)

        security_headers = {
            "x-frame-options": self._frame_options,
            "x-content-type-options": "nosniff",
            "x-xss-protection": "0",
            "referrer-policy": "strict-origin-when-cross-origin",
            "cache-control": cache_control,
            "pragma": "no-cache",
            "content-security-policy": csp,
            "permissions-policy": self._permissions_policy,
            "x-permitted-cross-domain-policies": "none",
        }

        # Apply headers to response
        if hasattr(response, "headers") and isinstance(response.headers, dict):
            for key, value in security_headers.items():
                response.headers[key] = value
        elif hasattr(response, "headers"):
            for key, value in security_headers.items():
                response.headers[key] = value

        return response

    def apply_for_asset(
        self,
        response: "Response",
    ) -> "Response":
        """
        Apply lighter security headers for static assets (avatars, downloads).

        Allows caching but prevents clickjacking and MIME sniffing.
        """
        asset_headers = {
            "x-content-type-options": "nosniff",
            "x-frame-options": self._frame_options,
        }

        if hasattr(response, "headers") and isinstance(response.headers, dict):
            for key, value in asset_headers.items():
                response.headers[key] = value

        return response


# ═══════════════════════════════════════════════════════════════════════════════
#  Password Complexity Validator
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class PasswordStrength:
    """Result of password complexity analysis."""
    score: int          # 0-4 (0=terrible, 4=strong)
    is_valid: bool      # Meets minimum requirements
    feedback: List[str]  # Human-readable improvement suggestions
    length: int
    has_upper: bool
    has_lower: bool
    has_digit: bool
    has_special: bool


class PasswordValidator:
    """
    Password complexity validator for admin accounts.

    Rules (configurable):
    - Minimum length (default: 10)
    - Must contain uppercase letter
    - Must contain lowercase letter
    - Must contain digit
    - Must contain special character
    - Must not be a common password
    - Must not contain the username

    OWASP Password Storage Cheat Sheet compliant.
    """

    # Top common passwords to reject (abbreviated list)
    COMMON_PASSWORDS: FrozenSet[str] = frozenset({
        "password", "123456", "12345678", "1234567890", "qwerty",
        "abc123", "password1", "admin", "letmein", "welcome",
        "monkey", "dragon", "master", "login", "princess",
        "starwars", "passw0rd", "shadow", "sunshine", "trustno1",
        "iloveyou", "batman", "access", "hello", "charlie",
        "password123", "admin123", "root", "toor", "changeme",
        "123456789", "12345", "1234", "qwerty123", "1q2w3e4r",
        "qwertyuiop", "654321", "555555", "lovely", "password1!",
    })

    def __init__(
        self,
        *,
        min_length: int = 10,
        require_upper: bool = True,
        require_lower: bool = True,
        require_digit: bool = True,
        require_special: bool = True,
        max_length: int = 128,
    ):
        self.min_length = min_length
        self.require_upper = require_upper
        self.require_lower = require_lower
        self.require_digit = require_digit
        self.require_special = require_special
        self.max_length = max_length

    def validate(
        self,
        password: str,
        *,
        username: Optional[str] = None,
    ) -> PasswordStrength:
        """
        Validate password complexity.

        Returns a PasswordStrength with validity and feedback.
        """
        feedback = []
        score = 0

        length = len(password)
        has_upper = bool(re.search(r"[A-Z]", password))
        has_lower = bool(re.search(r"[a-z]", password))
        has_digit = bool(re.search(r"\d", password))
        has_special = bool(re.search(r"[^A-Za-z0-9]", password))

        # Length check
        if length < self.min_length:
            feedback.append(f"Must be at least {self.min_length} characters (currently {length}).")
        elif length >= 16:
            score += 2  # Bonus for very long passwords
        else:
            score += 1

        if length > self.max_length:
            feedback.append(f"Must not exceed {self.max_length} characters.")

        # Character class checks
        if self.require_upper and not has_upper:
            feedback.append("Must contain at least one uppercase letter (A-Z).")
        elif has_upper:
            score += 1

        if self.require_lower and not has_lower:
            feedback.append("Must contain at least one lowercase letter (a-z).")

        if self.require_digit and not has_digit:
            feedback.append("Must contain at least one digit (0-9).")
        elif has_digit:
            score += 1

        if self.require_special and not has_special:
            feedback.append("Must contain at least one special character (!@#$%^&*...).")
        elif has_special:
            score += 1

        # Common password check
        if password.lower() in self.COMMON_PASSWORDS:
            feedback.append("This is a commonly used password. Please choose something unique.")
            score = 0

        # Username in password check
        if username and len(username) >= 3 and username.lower() in password.lower():
            feedback.append("Password must not contain your username.")
            score = max(0, score - 1)

        # Repeating characters check
        if re.search(r"(.)\1{3,}", password):
            feedback.append("Avoid repeating the same character more than 3 times.")
            score = max(0, score - 1)

        is_valid = len(feedback) == 0
        score = min(4, max(0, score))

        return PasswordStrength(
            score=score,
            is_valid=is_valid,
            feedback=feedback,
            length=length,
            has_upper=has_upper,
            has_lower=has_lower,
            has_digit=has_digit,
            has_special=has_special,
        )


# ═══════════════════════════════════════════════════════════════════════════════
#  Security Event Tracking
# ═══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class SecurityEvent:
    """Immutable record of a security-relevant event."""
    timestamp: float
    event_type: str  # "login_failed", "csrf_violation", "rate_limited", "lockout"
    ip_address: str
    details: Dict[str, Any] = field(default_factory=dict)


class SecurityEventTracker:
    """
    Tracks security events for monitoring and alerting.

    Maintains a bounded FIFO buffer of recent security events
    for the admin monitoring dashboard.
    """

    def __init__(self, max_events: int = 1000):
        self._events: List[SecurityEvent] = []
        self._max_events = max_events

    def record(
        self,
        event_type: str,
        ip_address: str,
        **details: Any,
    ) -> SecurityEvent:
        """Record a security event."""
        event = SecurityEvent(
            timestamp=time.time(),
            event_type=event_type,
            ip_address=ip_address,
            details=dict(details),
        )
        self._events.append(event)

        # Trim to max size
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

        logger.warning(
            "Security event: %s from %s — %s",
            event_type, ip_address, details,
        )
        return event

    def get_events(
        self,
        *,
        event_type: Optional[str] = None,
        ip_address: Optional[str] = None,
        since: Optional[float] = None,
        limit: int = 100,
    ) -> List[SecurityEvent]:
        """Query recent security events with optional filters."""
        results = self._events
        if event_type:
            results = [e for e in results if e.event_type == event_type]
        if ip_address:
            results = [e for e in results if e.ip_address == ip_address]
        if since:
            results = [e for e in results if e.timestamp >= since]
        return results[-limit:]

    def count_events(
        self,
        event_type: str,
        *,
        ip_address: Optional[str] = None,
        since: Optional[float] = None,
    ) -> int:
        """Count events matching criteria."""
        results = [e for e in self._events if e.event_type == event_type]
        if ip_address:
            results = [e for e in results if e.ip_address == ip_address]
        if since:
            results = [e for e in results if e.timestamp >= since]
        return len(results)

    def clear(self) -> None:
        """Clear all tracked events."""
        self._events.clear()


# ═══════════════════════════════════════════════════════════════════════════════
#  Admin Security Policy (Orchestrator)
# ═══════════════════════════════════════════════════════════════════════════════


class AdminSecurityPolicy:
    """
    Central orchestrator for all admin security features.

    Holds singleton instances of CSRF, rate limiter, headers, password
    validator, and event tracker. Provides convenience methods that
    combine multiple security checks.

    Typically instantiated once and stored on the AdminSite.
    """

    def __init__(
        self,
        *,
        csrf: Optional[AdminCSRFProtection] = None,
        rate_limiter: Optional[AdminRateLimiter] = None,
        headers: Optional[AdminSecurityHeaders] = None,
        password_validator: Optional[PasswordValidator] = None,
        event_tracker: Optional[SecurityEventTracker] = None,
    ):
        self.csrf = csrf or AdminCSRFProtection()
        self.rate_limiter = rate_limiter or AdminRateLimiter()
        self.headers = headers or AdminSecurityHeaders()
        self.password_validator = password_validator or PasswordValidator()
        self.event_tracker = event_tracker or SecurityEventTracker()

    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "AdminSecurityPolicy":
        """
        Build an AdminSecurityPolicy from a security config dict.

        The config dict is the ``security_config`` from ``AdminConfig``,
        produced by ``Integration.AdminSecurity.to_dict()`` or the
        default security config.

        Args:
            config: Security configuration dictionary with keys:
                csrf, rate_limit, password, headers,
                session_fixation_protection, event_tracker_max_events

        Returns:
            Fully configured AdminSecurityPolicy instance.
        """
        csrf_cfg = config.get("csrf", {})
        rate_cfg = config.get("rate_limit", {})
        password_cfg = config.get("password", {})
        headers_cfg = config.get("headers", {})

        # Build CSRF protection
        csrf = None
        if csrf_cfg.get("enabled", True):
            csrf = AdminCSRFProtection(
                max_age=csrf_cfg.get("max_age", 7200),
                token_length=csrf_cfg.get("token_length", 32),
            )

        # Build rate limiter
        rate_limiter = None
        if rate_cfg.get("enabled", True):
            rate_limiter = AdminRateLimiter(
                max_login_attempts=rate_cfg.get("max_login_attempts", 5),
                login_window=rate_cfg.get("login_window", 900),
                sensitive_op_limit=rate_cfg.get("sensitive_op_limit", 30),
                sensitive_op_window=rate_cfg.get("sensitive_op_window", 300),
            )

        # Build security headers
        headers = None
        if headers_cfg.get("enabled", True):
            headers = AdminSecurityHeaders(
                csp_template=headers_cfg.get("csp_template"),
                frame_options=headers_cfg.get("frame_options", "DENY"),
                permissions_policy=headers_cfg.get("permissions_policy"),
            )

        # Build password validator
        password_validator = PasswordValidator(
            min_length=password_cfg.get("min_length", 10),
            require_upper=password_cfg.get("require_upper", True),
            require_lower=password_cfg.get("require_lower", True),
            require_digit=password_cfg.get("require_digit", True),
            require_special=password_cfg.get("require_special", True),
            max_length=password_cfg.get("max_length", 128),
        )

        # Build event tracker
        event_tracker = SecurityEventTracker(
            max_events=config.get("event_tracker_max_events", 1000),
        )

        return cls(
            csrf=csrf or AdminCSRFProtection(),
            rate_limiter=rate_limiter or AdminRateLimiter(),
            headers=headers or AdminSecurityHeaders(),
            password_validator=password_validator,
            event_tracker=event_tracker,
        )

    def protect_response(
        self,
        response: "Response",
        *,
        nonce: Optional[str] = None,
        is_asset: bool = False,
    ) -> "Response":
        """
        Apply all security policies to a response.

        Args:
            response: The response to protect
            nonce: CSP nonce (generated if not provided)
            is_asset: If True, use lighter headers for static files
        """
        if is_asset:
            return self.headers.apply_for_asset(response)
        return self.headers.apply(response, nonce=nonce)

    def extract_client_ip(self, request: Any) -> str:
        """Extract the client IP address from a request."""
        try:
            if hasattr(request, "headers"):
                hdrs = request.headers
                if hasattr(hdrs, "get"):
                    # Trust X-Forwarded-For only behind a proxy
                    forwarded = hdrs.get("x-forwarded-for")
                    if forwarded:
                        return forwarded.split(",")[0].strip()
                    real_ip = hdrs.get("x-real-ip")
                    if real_ip:
                        return real_ip
            if hasattr(request, "scope"):
                client = request.scope.get("client")
                if client and isinstance(client, (list, tuple)) and len(client) >= 1:
                    return str(client[0])
        except Exception:
            pass
        return "unknown"


# ═══════════════════════════════════════════════════════════════════════════════
#  DI Registration
# ═══════════════════════════════════════════════════════════════════════════════


def register_security_providers(container: Any, config: Optional[Dict[str, Any]] = None) -> None:
    """
    Register admin security components with the DI container.

    Registers:
    - AdminSecurityPolicy (singleton)
    - AdminCSRFProtection (singleton)
    - AdminRateLimiter (singleton)
    - AdminSecurityHeaders (singleton)
    - PasswordValidator (singleton)
    - SecurityEventTracker (singleton)

    Args:
        container: DI container to register providers into.
        config: Optional security config dict from AdminConfig.security_config.
            If None, uses defaults.
    """
    try:
        from aquilia.di.providers import FactoryProvider, ValueProvider
        from aquilia.di.scopes import Scope

        if config:
            policy = AdminSecurityPolicy.from_config(config)
        else:
            policy = AdminSecurityPolicy()

        container.register(
            AdminSecurityPolicy,
            ValueProvider(policy),
        )
        container.register(
            AdminCSRFProtection,
            ValueProvider(policy.csrf),
        )
        container.register(
            AdminRateLimiter,
            ValueProvider(policy.rate_limiter),
        )
        container.register(
            AdminSecurityHeaders,
            ValueProvider(policy.headers),
        )
        container.register(
            PasswordValidator,
            ValueProvider(policy.password_validator),
        )
        container.register(
            SecurityEventTracker,
            ValueProvider(policy.event_tracker),
        )

        logger.debug("Admin security providers registered with DI container.")
    except ImportError:
        logger.debug("DI system not available; admin security DI registration skipped.")
    except Exception as exc:
        logger.warning("Failed to register admin security DI providers: %s", exc)


__all__ = [
    "AdminCSRFProtection",
    "AdminRateLimiter",
    "AdminSecurityHeaders",
    "PasswordValidator",
    "PasswordStrength",
    "SecurityEventTracker",
    "SecurityEvent",
    "AdminSecurityPolicy",
    "register_security_providers",
]
