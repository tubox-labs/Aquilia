"""
AquilaHTTP — Authentication Interceptors.

Interceptors for various authentication schemes:
- Basic Auth
- Bearer Token
- API Key
- OAuth 2.0
- AWS Signature v4
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from .interceptors import HTTPInterceptor
from .request import HTTPClientRequest
from .response import HTTPClientResponse

logger = logging.getLogger("aquilia.http.auth")


class AuthInterceptor(HTTPInterceptor, ABC):
    """
    Base class for authentication interceptors.

    Subclasses implement specific auth schemes.
    """

    @abstractmethod
    def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str] | None:
        """
        Generate authentication header.

        Args:
            request: The request being authenticated.

        Returns:
            (header_name, header_value) tuple, or None if no auth needed.
        """
        ...

    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse:
        """Apply authentication header to request."""
        auth = self.get_auth_header(request)

        if auth:
            name, value = auth
            new_headers = dict(request.headers)
            new_headers[name] = value
            request = request.copy(headers=new_headers)

        return await next_handler(request)


class BasicAuth(AuthInterceptor):
    """
    HTTP Basic Authentication.

    Encodes username:password in Base64.
    """

    __slots__ = ("_username", "_password")

    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password

    def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str]:
        credentials = f"{self._username}:{self._password}".encode()
        encoded = base64.b64encode(credentials).decode("ascii")
        return ("Authorization", f"Basic {encoded}")


class BearerAuth(AuthInterceptor):
    """
    Bearer Token Authentication.

    Adds Authorization: Bearer <token> header.
    """

    __slots__ = ("_token", "_token_getter")

    def __init__(
        self,
        token: str | None = None,
        token_getter: Callable[[], str] | None = None,
    ):
        """
        Initialize Bearer auth.

        Args:
            token: Static token.
            token_getter: Function that returns the current token.
        """
        if token is None and token_getter is None:
            raise ValueError("Either token or token_getter must be provided")

        self._token = token
        self._token_getter = token_getter

    def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str]:
        token = self._token or (self._token_getter() if self._token_getter else "")
        return ("Authorization", f"Bearer {token}")


class APIKeyAuth(AuthInterceptor):
    """
    API Key Authentication.

    Adds API key as header or query parameter.
    """

    __slots__ = ("_key", "_header_name", "_in_query")

    def __init__(
        self,
        key: str,
        header_name: str = "X-API-Key",
        in_query: bool = False,
    ):
        """
        Initialize API Key auth.

        Args:
            key: The API key.
            header_name: Header name (or query param name if in_query=True).
            in_query: If True, add key as query parameter.
        """
        self._key = key
        self._header_name = header_name
        self._in_query = in_query

    def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str] | None:
        if self._in_query:
            # Will be handled in intercept
            return None
        return (self._header_name, self._key)

    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse:
        if self._in_query:
            # Add to query string
            from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

            parsed = urlparse(request.url)
            params = parse_qsl(parsed.query)
            params.append((self._header_name, self._key))
            new_query = urlencode(params)
            new_url = urlunparse(
                (
                    parsed.scheme,
                    parsed.netloc,
                    parsed.path,
                    parsed.params,
                    new_query,
                    parsed.fragment,
                )
            )
            request = request.copy(url=new_url)
        else:
            auth = self.get_auth_header(request)
            if auth:
                new_headers = dict(request.headers)
                new_headers[auth[0]] = auth[1]
                request = request.copy(headers=new_headers)

        return await next_handler(request)


class DigestAuth(AuthInterceptor):
    """
    HTTP Digest Authentication.

    Implements RFC 7616 Digest Access Authentication.
    """

    __slots__ = ("_username", "_password", "_nonce_count")

    def __init__(self, username: str, password: str):
        self._username = username
        self._password = password
        self._nonce_count = 0

    def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str] | None:
        # Digest auth requires a challenge from the server first
        # This is handled in intercept
        return None

    def _compute_digest(
        self,
        method: str,
        uri: str,
        realm: str,
        nonce: str,
        qop: str = "",
        nc: str = "",
        cnonce: str = "",
    ) -> str:
        """Compute digest response."""
        # HA1 = MD5(username:realm:password)
        ha1 = hashlib.md5(f"{self._username}:{realm}:{self._password}".encode()).hexdigest()

        # HA2 = MD5(method:uri)
        ha2 = hashlib.md5(f"{method}:{uri}".encode()).hexdigest()

        # Response
        if qop:
            response = hashlib.md5(f"{ha1}:{nonce}:{nc}:{cnonce}:{qop}:{ha2}".encode()).hexdigest()
        else:
            response = hashlib.md5(f"{ha1}:{nonce}:{ha2}".encode()).hexdigest()

        return response

    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse:
        import secrets

        # First request without auth
        response = await next_handler(request)

        # Check for 401 with WWW-Authenticate: Digest
        if response.status_code != 401:
            return response

        auth_header = response.get_header("WWW-Authenticate", "")
        if not auth_header.lower().startswith("digest"):
            return response

        # Parse challenge
        import re

        params: dict[str, str] = {}
        for match in re.finditer(r'(\w+)=["\']?([^"\',]+)["\']?', auth_header):
            params[match.group(1).lower()] = match.group(2)

        realm = params.get("realm", "")
        nonce = params.get("nonce", "")
        qop = params.get("qop", "")
        opaque = params.get("opaque", "")

        # Increment nonce count
        self._nonce_count += 1
        nc = f"{self._nonce_count:08x}"
        cnonce = secrets.token_hex(8)

        # Compute response
        from urllib.parse import urlparse

        parsed = urlparse(request.url)
        uri = parsed.path or "/"
        if parsed.query:
            uri += f"?{parsed.query}"

        digest_response = self._compute_digest(
            method=request.method.value,
            uri=uri,
            realm=realm,
            nonce=nonce,
            qop=qop.split(",")[0] if qop else "",
            nc=nc,
            cnonce=cnonce,
        )

        # Build Authorization header
        auth_parts = [
            f'username="{self._username}"',
            f'realm="{realm}"',
            f'nonce="{nonce}"',
            f'uri="{uri}"',
            f'response="{digest_response}"',
        ]
        if qop:
            auth_parts.extend(
                [
                    f"qop={qop.split(',')[0]}",
                    f"nc={nc}",
                    f'cnonce="{cnonce}"',
                ]
            )
        if opaque:
            auth_parts.append(f'opaque="{opaque}"')

        auth_value = "Digest " + ", ".join(auth_parts)

        # Retry with auth
        new_headers = dict(request.headers)
        new_headers["Authorization"] = auth_value
        request = request.copy(headers=new_headers)

        return await next_handler(request)


@dataclass
class OAuth2Token:
    """OAuth 2.0 token."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None
    created_at: float = 0.0

    def __post_init__(self):
        if self.created_at == 0.0:
            self.created_at = time.time()

    @property
    def is_expired(self) -> bool:
        if self.expires_in is None:
            return False
        return time.time() > (self.created_at + self.expires_in)


class OAuth2Auth(AuthInterceptor):
    """
    OAuth 2.0 Bearer Token Authentication.

    Supports automatic token refresh.
    """

    __slots__ = ("_token", "_refresh_callback")

    def __init__(
        self,
        token: OAuth2Token,
        refresh_callback: Callable[[OAuth2Token], Awaitable[OAuth2Token]] | None = None,
    ):
        """
        Initialize OAuth2 auth.

        Args:
            token: Initial OAuth2 token.
            refresh_callback: Async callback to refresh expired tokens.
        """
        self._token = token
        self._refresh_callback = refresh_callback

    @property
    def token(self) -> OAuth2Token:
        return self._token

    def set_token(self, token: OAuth2Token) -> None:
        self._token = token

    def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str]:
        return ("Authorization", f"{self._token.token_type} {self._token.access_token}")

    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse:
        # Check if token needs refresh
        if self._token.is_expired and self._refresh_callback:
            try:
                self._token = await self._refresh_callback(self._token)
                logger.debug("OAuth2 token refreshed")
            except Exception as e:
                logger.error(f"Failed to refresh OAuth2 token: {e}")

        # Apply auth header
        auth = self.get_auth_header(request)
        new_headers = dict(request.headers)
        new_headers[auth[0]] = auth[1]
        request = request.copy(headers=new_headers)

        response = await next_handler(request)

        # Handle 401 - try refresh
        if response.status_code == 401 and self._refresh_callback:
            try:
                self._token = await self._refresh_callback(self._token)
                logger.debug("OAuth2 token refreshed after 401")

                # Retry with new token
                auth = self.get_auth_header(request)
                new_headers = dict(request.headers)
                new_headers[auth[0]] = auth[1]
                request = request.copy(headers=new_headers)

                return await next_handler(request)
            except Exception as e:
                logger.error(f"Failed to refresh OAuth2 token: {e}")

        return response


class AWSSignatureV4Auth(AuthInterceptor):
    """
    AWS Signature Version 4 Authentication.

    Signs requests for AWS services.
    """

    __slots__ = (
        "_access_key",
        "_secret_key",
        "_region",
        "_service",
        "_session_token",
    )

    def __init__(
        self,
        access_key: str,
        secret_key: str,
        region: str,
        service: str,
        session_token: str | None = None,
    ):
        self._access_key = access_key
        self._secret_key = secret_key
        self._region = region
        self._service = service
        self._session_token = session_token

    def get_auth_header(self, request: HTTPClientRequest) -> tuple[str, str] | None:
        # AWS SigV4 requires full request context
        return None

    def _sign(self, key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _get_signature_key(self, date_stamp: str) -> bytes:
        k_date = self._sign(f"AWS4{self._secret_key}".encode(), date_stamp)
        k_region = self._sign(k_date, self._region)
        k_service = self._sign(k_region, self._service)
        k_signing = self._sign(k_service, "aws4_request")
        return k_signing

    async def intercept(
        self,
        request: HTTPClientRequest,
        next_handler: Callable[[HTTPClientRequest], Awaitable[HTTPClientResponse]],
    ) -> HTTPClientResponse:
        from datetime import datetime, timezone
        from urllib.parse import quote, urlparse

        # Generate timestamps
        now = datetime.now(timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        # Parse URL
        parsed = urlparse(request.url)
        host = parsed.netloc
        canonical_uri = quote(parsed.path or "/", safe="/-_.~")
        canonical_querystring = parsed.query or ""

        # Build canonical headers
        headers = dict(request.headers)
        headers["host"] = host
        headers["x-amz-date"] = amz_date
        if self._session_token:
            headers["x-amz-security-token"] = self._session_token

        signed_headers = ";".join(sorted(k.lower() for k in headers.keys()))
        canonical_headers = "".join(
            f"{k.lower()}:{v.strip()}\n" for k, v in sorted(headers.items(), key=lambda x: x[0].lower())
        )

        # Payload hash
        payload = b""
        if isinstance(request.body, bytes):
            payload = request.body
        payload_hash = hashlib.sha256(payload).hexdigest()
        headers["x-amz-content-sha256"] = payload_hash

        # Canonical request
        canonical_request = "\n".join(
            [
                request.method.value,
                canonical_uri,
                canonical_querystring,
                canonical_headers,
                signed_headers,
                payload_hash,
            ]
        )

        # String to sign
        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self._region}/{self._service}/aws4_request"
        string_to_sign = "\n".join(
            [
                algorithm,
                amz_date,
                credential_scope,
                hashlib.sha256(canonical_request.encode("utf-8")).hexdigest(),
            ]
        )

        # Calculate signature
        signing_key = self._get_signature_key(date_stamp)
        signature = hmac.new(
            signing_key,
            string_to_sign.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        # Build Authorization header
        authorization = (
            f"{algorithm} "
            f"Credential={self._access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, "
            f"Signature={signature}"
        )

        headers["Authorization"] = authorization

        # Create new request with signed headers
        request = request.copy(headers=headers)

        return await next_handler(request)
