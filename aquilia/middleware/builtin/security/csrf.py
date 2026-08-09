"""Cross-Site Request Forgery protection.

Implements the Synchronizer Token Pattern backed by server-side sessions, with
a Double Submit Cookie fallback when no session is available. Runs after
authentication, since the session it reads is established there.
"""

from __future__ import annotations

import secrets
from typing import TYPE_CHECKING

from aquilia.faults.domains import CSRFViolationFault
from aquilia.middleware.core.base import Middleware
from aquilia.middleware.core.types import RequestHandler

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from aquilia.response import Response

Handler = RequestHandler


class CSRFError(CSRFViolationFault):
    """
    CSRF validation fault -- raised when CSRF protection detects a violation.

    Inherits from CSRFViolationFault (aquilia.faults.domains) to integrate
    with the Aquilia fault handling pipeline. This is a proper Fault, not
    a bare Exception.

    Attributes:
        reason: Human-readable description of the violation
        code: "CSRF_VIOLATION" (stable machine-readable identifier)
        domain: FaultDomain.SECURITY
        severity: Severity.WARN
        public: True (safe to expose to client)
    """

    def __init__(self, reason: str = "CSRF validation failed", **kwargs):
        self.reason = reason
        super().__init__(reason=reason, **kwargs)


class CSRFMiddleware(Middleware):
    """
    Production-grade CSRF (Cross-Site Request Forgery) protection middleware.

    Implements a **Synchronizer Token Pattern** backed by server-side sessions,
    with a **Double Submit Cookie** fallback when sessions are unavailable.

    Protection Flow:
        1. On every request, generate or retrieve the CSRF token from the session
           (or a signed cookie as fallback).
        2. For **state-changing** methods (POST, PUT, PATCH, DELETE), validate
           the submitted token against the stored token.
        3. Token can be submitted via:
           - HTTP header  (default: ``X-CSRF-Token``)
           - Form field   (default: ``_csrf_token``)
           - Custom header for AJAX (``X-Requested-With: XMLHttpRequest`` bypasses
             when ``trust_ajax`` is enabled, as same-origin policy prevents
             cross-origin custom headers)
        4. On validation failure, return **403 Forbidden**.
        5. Token is injected into ``request.state["csrf_token"]`` for template access.

    Token Storage Priority:
        1. Session (``request.state["session"]``) -- preferred, most secure.
        2. Double-submit cookie (``_csrf_cookie``) -- fallback when sessions are
           unavailable. Uses HMAC-signed tokens for integrity.

    Security Features:
        - Per-session token (regenerated on session rotation / login)
        - HMAC-signed cookie fallback (tamper-proof)
        - Configurable safe methods, exempt paths, exempt content types
        - Optional AJAX trust (``X-Requested-With`` header)
        - Constant-time comparison to prevent timing attacks
        - Token rotation support (new token after each validation -- optional)
        - SameSite cookie attribute for defense-in-depth

    Args:
        secret_key: Secret key for HMAC signing (required for cookie fallback).
                    If not provided, a random key is generated per-process
                    (tokens won't survive restarts without sessions).
        token_length: Length of the raw token in bytes (default 32 → 43 chars base64).
        header_name: HTTP header name for token submission.
        field_name: Form field name for token submission.
        cookie_name: Cookie name for double-submit fallback.
        cookie_path: Path attribute for the CSRF cookie.
        cookie_domain: Domain attribute for the CSRF cookie.
        cookie_secure: Secure flag for the CSRF cookie.
        cookie_samesite: SameSite attribute (``Lax``, ``Strict``, ``None``).
        cookie_httponly: HttpOnly flag for CSRF cookie (False allows JS access
                        for SPA/AJAX workflows).
        cookie_max_age: Max-Age for the CSRF cookie in seconds.
        safe_methods: HTTP methods that don't require CSRF validation.
        exempt_paths: URL paths exempt from CSRF checks (e.g. API webhooks).
        exempt_content_types: Content types exempt from CSRF (e.g. ``application/json``
                             for API-only endpoints behind token auth).
        trust_ajax: Trust ``X-Requested-With: XMLHttpRequest`` as proof of
                    same-origin (browser same-origin policy prevents custom headers
                    from cross-origin requests).
        rotate_token: Generate a new token after each successful validation
                     (one-time-use tokens -- stronger but may break back-button).
        failure_status: HTTP status code on CSRF failure (default 403).

    Example::

        csrf = CSRFMiddleware(secret_key="my-secret-key")
        app.middleware_stack.add(csrf, scope="global", priority=10, name="csrf")

        # In templates:
        # <input type="hidden" name="_csrf_token" value="{{ csrf_token }}">

        # In AJAX:
        # fetch('/api/data', {
        #     method: 'POST',
        #     headers: { 'X-CSRF-Token': csrfToken }
        # })
    """

    _SAFE_METHODS_DEFAULT: frozenset[str] = frozenset({"GET", "HEAD", "OPTIONS", "TRACE"})
    _SESSION_KEY: str = "_csrf_token"

    def __init__(
        self,
        secret_key: str | None = None,
        token_length: int = 32,
        header_name: str = "X-CSRF-Token",
        field_name: str = "_csrf_token",
        cookie_name: str = "_csrf_cookie",
        cookie_path: str = "/",
        cookie_domain: str | None = None,
        cookie_secure: bool = False,
        cookie_samesite: str = "Lax",
        cookie_httponly: bool = False,
        cookie_max_age: int = 3600,
        safe_methods: frozenset[str] | None = None,
        exempt_paths: list[str] | None = None,
        exempt_content_types: list[str] | None = None,
        trust_ajax: bool = True,
        rotate_token: bool = False,
        failure_status: int = 403,
    ):
        from aquilia.signing import CSRFSigner

        self._csrf_signer = CSRFSigner(
            secret=secret_key or secrets.token_urlsafe(32),
        )
        self._token_length = token_length
        self._header_name = header_name.lower()
        self._field_name = field_name
        self._cookie_name = cookie_name
        self._cookie_path = cookie_path
        self._cookie_domain = cookie_domain
        self._cookie_secure = cookie_secure
        self._cookie_samesite = cookie_samesite
        self._cookie_httponly = cookie_httponly
        self._cookie_max_age = cookie_max_age
        self._safe_methods = safe_methods or self._SAFE_METHODS_DEFAULT
        self._exempt_paths: set[str] = set(exempt_paths or [])
        self._exempt_content_types: set[str] = set(ct.lower() for ct in (exempt_content_types or []))
        self._trust_ajax = trust_ajax
        self._rotate_token = rotate_token
        self._failure_status = failure_status

    # ── Token Generation ─────────────────────────────────────────────────

    def _generate_token(self) -> str:
        """Generate a cryptographically secure CSRF token."""
        return secrets.token_urlsafe(self._token_length)

    def _sign_token(self, token: str) -> str:
        """Sign a token using the Aquilia signing subsystem (CSRFSigner)."""
        return self._csrf_signer.sign(token)

    def _verify_signed_token(self, signed: str) -> str | None:
        """Verify a signed token. Returns the token if valid, None otherwise."""
        from aquilia.signing import BadSignature, SignatureMalformed

        try:
            return self._csrf_signer.unsign(signed)
        except (BadSignature, SignatureMalformed):
            return None

    # ── Token Storage (Session + Cookie Fallback) ────────────────────────

    def _get_session_token(self, request: Request) -> str | None:
        """Get the stored CSRF token from the session."""
        session = request.state.get("session")
        if session is not None:
            # Session objects support dict-like access
            if hasattr(session, "get"):
                return session.get(self._SESSION_KEY)
            elif hasattr(session, "__getitem__"):
                try:
                    return session[self._SESSION_KEY]
                except (KeyError, IndexError):
                    return None
        return None

    def _set_session_token(self, request: Request, token: str) -> None:
        """Store CSRF token in the session."""
        session = request.state.get("session")
        if session is not None and hasattr(session, "__setitem__"):
            session[self._SESSION_KEY] = token

    def _get_cookie_token(self, request: Request) -> str | None:
        """Get the CSRF token from the double-submit cookie."""
        cookie_value = None
        # Try cookies dict
        if hasattr(request, "cookies") and isinstance(request.cookies, dict):
            cookie_value = request.cookies.get(self._cookie_name)
        # Fallback: parse Cookie header manually
        if cookie_value is None:
            cookie_header = request.header("cookie")
            if cookie_header:
                for pair in cookie_header.split(";"):
                    pair = pair.strip()
                    if pair.startswith(f"{self._cookie_name}="):
                        cookie_value = pair[len(self._cookie_name) + 1 :]
                        break
        if cookie_value:
            return self._verify_signed_token(cookie_value)
        return None

    def _set_cookie_token(self, response: Response, token: str) -> None:
        """Set the CSRF token as a signed double-submit cookie."""
        signed = self._sign_token(token)
        parts = [f"{self._cookie_name}={signed}"]
        parts.append(f"Path={self._cookie_path}")
        if self._cookie_domain:
            parts.append(f"Domain={self._cookie_domain}")
        parts.append(f"Max-Age={self._cookie_max_age}")
        parts.append(f"SameSite={self._cookie_samesite}")
        if self._cookie_secure:
            parts.append("Secure")
        if self._cookie_httponly:
            parts.append("HttpOnly")
        cookie_str = "; ".join(parts)
        # Append to existing Set-Cookie headers (don't overwrite)
        existing = response.headers.get("set-cookie", "")
        if existing:
            response.headers["set-cookie"] = f"{existing}, {cookie_str}"
        else:
            response.headers["set-cookie"] = cookie_str

    # ── Token Extraction from Request ────────────────────────────────────

    def _get_submitted_token(self, request: Request) -> str | None:
        """
        Extract the submitted CSRF token from the request.

        Checks in order:
        1. HTTP header (X-CSRF-Token)
        2. Form field (_csrf_token) -- from request body/state
        3. Query parameter (_csrf_token) -- last resort
        """
        # 1. Header
        token = request.header(self._header_name)
        if token:
            return token

        # 2. Form body (stored by body parser in request.state)
        form_data = request.state.get("form_data") or request.state.get("body")
        if isinstance(form_data, dict):
            token = form_data.get(self._field_name)
            if token:
                return token

        # 3. Parsed body (controllers often parse body into request.state)
        parsed_body = request.state.get("parsed_body")
        if isinstance(parsed_body, dict):
            token = parsed_body.get(self._field_name)
            if token:
                return token

        return None

    # ── Exemption Checks ─────────────────────────────────────────────────

    def _is_exempt(self, request: Request) -> bool:
        """Check if the request is exempt from CSRF validation."""
        # Safe methods don't need CSRF protection
        if request.method.upper() in self._safe_methods:
            return True

        # Explicit path exemptions
        if request.path in self._exempt_paths:
            return True

        # Prefix-based path exemption (for API routes etc.)
        for exempt in self._exempt_paths:
            if exempt.endswith("*") and request.path.startswith(exempt[:-1]):
                return True

        # Content-type exemption (e.g. application/json for pure APIs)
        if self._exempt_content_types:
            content_type = request.header("content-type").lower().split(";")[0].strip()
            if content_type in self._exempt_content_types:
                return True

        # Route-level opt-out via request.state
        if request.state.get("csrf_exempt"):
            return True

        # Trust AJAX requests (X-Requested-With can't be set cross-origin)
        if self._trust_ajax:
            xhr = request.header("x-requested-with")
            if xhr and xhr.lower() == "xmlhttprequest":
                return True

        return False

    # ── Validation ───────────────────────────────────────────────────────

    def _validate_token(self, stored: str, submitted: str) -> bool:
        """Constant-time comparison of CSRF tokens."""
        from aquilia.signing import constant_time_compare

        return constant_time_compare(stored, submitted)

    # ── Main Handler ─────────────────────────────────────────────────────

    async def __call__(self, request: Request, ctx: RequestCtx, next_handler: Handler) -> Response:
        """CSRF protection middleware handler."""
        from aquilia.response import Response

        # ── Step 1: Retrieve or generate token ───────────────────────────
        token = self._get_session_token(request)
        token_source = "session"

        if token is None:
            token = self._get_cookie_token(request)
            token_source = "cookie" if token else "new"

        if token is None:
            token = self._generate_token()
            token_source = "new"

        # Store in session if available
        if token_source in ("new", "cookie"):
            self._set_session_token(request, token)

        # ── Step 2: Inject into request state ────────────────────────────
        request.state["csrf_token"] = token
        request.state["csrf_token_field"] = self._field_name
        request.state["csrf_token_header"] = self._header_name

        # ── Step 3: Validate on unsafe methods ───────────────────────────
        if not self._is_exempt(request):
            submitted = self._get_submitted_token(request)

            if submitted is None:
                fault = CSRFError("CSRF token missing")
                resp = Response(
                    b'{"error": "CSRF token missing", "code": "CSRF_VIOLATION"}',
                    status=self._failure_status,
                    headers={
                        "content-type": "application/json",
                        "x-fault-code": fault.code,
                    },
                )
                resp._fault = fault
                return resp

            if not self._validate_token(token, submitted):
                fault = CSRFError("CSRF token invalid")
                resp = Response(
                    b'{"error": "CSRF token invalid", "code": "CSRF_VIOLATION"}',
                    status=self._failure_status,
                    headers={
                        "content-type": "application/json",
                        "x-fault-code": fault.code,
                    },
                )
                resp._fault = fault
                return resp

            # Optional: rotate token after successful validation
            if self._rotate_token:
                token = self._generate_token()
                self._set_session_token(request, token)
                request.state["csrf_token"] = token

        # ── Step 4: Process request ──────────────────────────────────────
        response = await next_handler(request, ctx)

        # ── Step 5: Always set cookie (double-submit defense-in-depth) ───
        self._set_cookie_token(response, token)

        return response


def csrf_token_func(request: Request) -> str:
    """
    Extract the CSRF token from request state.

    This function is designed to be passed to TemplateMiddleware as
    the ``csrf_token_func`` parameter, bridging CSRFMiddleware tokens
    into template context.

    Usage::

        template_mw = TemplateMiddleware(
            csrf_token_func=csrf_token_func,
        )
    """
    return request.state.get("csrf_token", "")


def csrf_exempt(request: Request) -> None:
    """
    Mark a request as exempt from CSRF validation.

    Call this in a controller or guard to skip CSRF checks for
    a specific request (e.g. API webhooks with signature verification).

    Usage::

        async def webhook_handler(request, ctx):
            csrf_exempt(request)
            # ... process webhook
    """
    request.state["csrf_exempt"] = True


__all__ = ["CSRFMiddleware", "CSRFError", "csrf_token_func", "csrf_exempt"]
