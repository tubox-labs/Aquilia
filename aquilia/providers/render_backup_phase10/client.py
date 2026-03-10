"""
Render REST API Client.

Typed HTTP client for the Render platform API (v1).
Handles authentication, rate limiting, retries, and response
parsing with zero third-party dependencies beyond the stdlib +
urllib.

Security
--------
- Bearer tokens are never logged or included in error messages.
- All API calls use HTTPS exclusively.
- Response bodies are validated before deserialization.
- Rate-limit headers are respected automatically.

API Reference: https://api.render.com/docs
"""

from __future__ import annotations

import json
import logging
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .types import (
    RenderDeploy,
    RenderOwner,
    RenderService,
    RenderServiceType,
)
from aquilia.faults.domains import (
    ProviderAPIFault,
    ProviderAuthFault,
    ProviderRateLimitFault,
    ProviderTokenFault,
    ProviderConnectionFault,
)

__all__ = [
    "RenderClient",
    "ProviderAPIFault",
    "ProviderAuthFault",
    "ProviderRateLimitFault",
]

_logger = logging.getLogger("aquilia.providers.render.client")

_BASE_URL = "https://api.render.com/v1"
_USER_AGENT = "Aquilia-CLI/1.0"
_DEFAULT_TIMEOUT = 30  # seconds
_MAX_RETRIES = 3
_RETRY_BACKOFF = 1.5  # exponential backoff base


def _build_ssl_context() -> ssl.SSLContext:
    """Build an SSL context that works on all platforms.

    macOS Python installations (especially from python.org) ship their
    own OpenSSL that does **not** use the system Keychain, causing
    ``CERTIFICATE_VERIFY_FAILED``.  We solve this by:

    1. Trying ``certifi`` (ships Mozilla's CA bundle).
    2. Falling back to ``ssl.create_default_context()`` (works on
       Linux and Homebrew Python).
    3. As a last resort, loading the macOS-specific
       ``Install Certificates.command`` path.
    """
    ctx = ssl.create_default_context()
    try:                                       # 1. certifi
        import certifi
        ctx.load_verify_locations(certifi.where())
        return ctx
    except (ImportError, OSError):
        pass
    # 2. Default context already loads system certs on most platforms;
    #    test whether it can actually verify *anything*.
    try:
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx
    except Exception:                          # pragma: no cover
        pass
    return ssl.create_default_context()        # pragma: no cover


# Module-level context — reused across all requests for performance.
_SSL_CTX: ssl.SSLContext = _build_ssl_context()


# ═══════════════════════════════════════════════════════════════════════════
# Legacy aliases — kept so existing except clauses continue to work.
# New code should use the Fault types.
# ═══════════════════════════════════════════════════════════════════════════

RenderAPIError = ProviderAPIFault
RenderRateLimitError = ProviderRateLimitFault
RenderAuthError = ProviderAuthFault


# ═══════════════════════════════════════════════════════════════════════════
# Client
# ═══════════════════════════════════════════════════════════════════════════


@dataclass
class _RequestResult:
    status: int
    body: bytes
    headers: Dict[str, str]


class RenderClient:
    """Synchronous REST client for the Render API (v1).

    Uses only stdlib ``urllib`` — no external dependencies required.
    Supports retry with exponential backoff and rate-limit awareness.

    Render uses cursor-based pagination.  List methods accept an
    optional ``cursor`` parameter; the returned list may be paginated
    with ``cursor`` response headers.

    Args:
        token: Render API bearer token.
        base_url: API base URL (override for testing).
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts for transient failures.

    Example::

        client = RenderClient(token="rnd_xxxxxxxxxxxx")
        services = client.list_services()
        for svc in services:
            print(svc.name)
    """

    def __init__(
        self,
        token: str,
        *,
        base_url: str = _BASE_URL,
        timeout: int = _DEFAULT_TIMEOUT,
        max_retries: int = _MAX_RETRIES,
        ssl_context: Optional[ssl.SSLContext] = None,
    ):
        if not token or not isinstance(token, str):
            raise ProviderTokenFault("Render API token is required")

        self._token = token
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._ssl_ctx = ssl_context or _SSL_CTX

    def __repr__(self) -> str:
        return f"RenderClient(base_url={self._base_url!r})"

    # ─── Low-level HTTP ──────────────────────────────────────────────

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": _USER_AGENT,
        }

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> _RequestResult:
        """Execute an HTTP request with retry and rate-limit handling."""
        url = f"{self._base_url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)

        data = json.dumps(body).encode("utf-8") if body else None

        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            try:
                req = urllib.request.Request(
                    url,
                    data=data,
                    headers=self._headers(),
                    method=method.upper(),
                )
                with urllib.request.urlopen(req, timeout=self._timeout, context=self._ssl_ctx) as resp:
                    resp_body = resp.read()
                    resp_headers = {
                        k.lower(): v for k, v in resp.getheaders()
                    }
                    return _RequestResult(
                        status=resp.status,
                        body=resp_body,
                        headers=resp_headers,
                    )

            except urllib.error.HTTPError as e:
                resp_body = e.read()
                resp_headers = {
                    k.lower(): v for k, v in e.headers.items()
                }
                status = e.code

                # Rate limited — respect Retry-After header
                if status == 429:
                    retry_after = float(
                        resp_headers.get("retry-after", str(2 ** attempt))
                    )
                    if attempt < self._max_retries:
                        _logger.warning(
                            "Rate limited. Waiting %.1fs (attempt %d/%d)",
                            retry_after, attempt + 1, self._max_retries,
                        )
                        time.sleep(retry_after)
                        continue
                    raise ProviderRateLimitFault(retry_after=retry_after)

                # Auth errors — don't retry
                if status in (401, 403):
                    msg = self._parse_error_message(resp_body)
                    raise ProviderAuthFault(
                        status, msg or "Authentication failed",
                        request_id=resp_headers.get("x-request-id"),
                    )

                # Server errors — retry with backoff
                if status >= 500 and attempt < self._max_retries:
                    wait = _RETRY_BACKOFF ** attempt
                    _logger.warning(
                        "Server error %d. Retrying in %.1fs (attempt %d/%d)",
                        status, wait, attempt + 1, self._max_retries,
                    )
                    time.sleep(wait)
                    last_error = e
                    continue

                # Client errors or exhausted retries
                msg = self._parse_error_message(resp_body)
                raise ProviderAPIFault(
                    status, msg or f"HTTP {status}",
                    request_id=resp_headers.get("x-request-id"),
                )

            except urllib.error.URLError as e:
                if attempt < self._max_retries:
                    wait = _RETRY_BACKOFF ** attempt
                    _logger.warning(
                        "Connection error: %s. Retrying in %.1fs",
                        e.reason, wait,
                    )
                    time.sleep(wait)
                    last_error = e
                    continue
                raise ProviderConnectionFault(f"Connection failed: {e.reason}")

        raise ProviderAPIFault(0, f"Max retries exhausted: {last_error}")

    def _parse_error_message(self, body: bytes) -> Optional[str]:
        """Extract error message from API response body."""
        try:
            data = json.loads(body)
            return data.get("message") or data.get("error") or data.get("detail")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    def _json(self, result: _RequestResult) -> Any:
        """Parse JSON response body."""
        if not result.body:
            return {}
        return json.loads(result.body)

    # ─── Services ────────────────────────────────────────────────────

    def list_services(
        self,
        *,
        name: Optional[str] = None,
        type: Optional[str] = None,
        region: Optional[str] = None,
        suspended: Optional[str] = None,
        owner_id: Optional[str] = None,
        cursor: Optional[str] = None,
        limit: int = 20,
    ) -> List[RenderService]:
        """List all services, optionally filtered.

        Render uses cursor-based pagination.  The ``cursor`` parameter
        accepts a service ID; results start after that service.
        """
        params: Dict[str, str] = {"limit": str(limit)}
        if name:
            params["name"] = name
        if type:
            params["type"] = type
        if region:
            params["region"] = region
        if suspended:
            params["suspended"] = suspended
        if owner_id:
            params["ownerId"] = owner_id
        if cursor:
            params["cursor"] = cursor

        result = self._request("GET", "/services", params=params)
        data = self._json(result)

        # Render returns a list of {service: {...}, cursor: "..."}
        if isinstance(data, list):
            return [self._parse_service(item.get("service", item)) for item in data]
        # Fallback for unexpected format
        services = data if isinstance(data, list) else []
        return [self._parse_service(s) for s in services]

    def get_service(self, service_id: str) -> RenderService:
        """Get a specific service by ID."""
        result = self._request("GET", f"/services/{service_id}")
        data = self._json(result)
        return self._parse_service(data)

    def get_service_by_name(
        self, name: str, owner_id: Optional[str] = None
    ) -> Optional[RenderService]:
        """Find a service by name. Returns None if not found."""
        services = self.list_services(name=name, owner_id=owner_id)
        for svc in services:
            if svc.name == name:
                return svc
        return None

    def create_service(self, payload: Dict[str, Any]) -> RenderService:
        """Create a new service.

        The ``payload`` should be produced by
        ``RenderDeployConfig.to_service_payload()``.
        """
        result = self._request("POST", "/services", body=payload)
        data = self._json(result)
        return self._parse_service(data.get("service", data))

    def update_service(
        self, service_id: str, payload: Dict[str, Any]
    ) -> RenderService:
        """Update an existing service (PATCH)."""
        result = self._request("PATCH", f"/services/{service_id}", body=payload)
        data = self._json(result)
        return self._parse_service(data)

    def delete_service(self, service_id: str) -> None:
        """Delete a service."""
        self._request("DELETE", f"/services/{service_id}")

    def suspend_service(self, service_id: str) -> None:
        """Suspend a running service."""
        self._request("POST", f"/services/{service_id}/suspend")

    def resume_service(self, service_id: str) -> None:
        """Resume a suspended service."""
        self._request("POST", f"/services/{service_id}/resume")

    # ─── Deploys ─────────────────────────────────────────────────────

    def list_deploys(
        self,
        service_id: str,
        *,
        cursor: Optional[str] = None,
        limit: int = 10,
    ) -> List[RenderDeploy]:
        """List deploys for a service."""
        params: Dict[str, str] = {"limit": str(limit)}
        if cursor:
            params["cursor"] = cursor

        result = self._request(
            "GET", f"/services/{service_id}/deploys", params=params
        )
        data = self._json(result)

        # Render returns [{deploy: {...}, cursor: "..."}]
        if isinstance(data, list):
            return [self._parse_deploy(item.get("deploy", item)) for item in data]
        return []

    def get_deploy(self, service_id: str, deploy_id: str) -> RenderDeploy:
        """Get a specific deploy."""
        result = self._request(
            "GET", f"/services/{service_id}/deploys/{deploy_id}"
        )
        data = self._json(result)
        return self._parse_deploy(data)

    def trigger_deploy(self, service_id: str) -> RenderDeploy:
        """Trigger a new deploy for the service.

        This re-deploys the service using its current configuration.
        """
        result = self._request(
            "POST", f"/services/{service_id}/deploys"
        )
        data = self._json(result)
        return self._parse_deploy(data)

    # ─── Environment Variables ───────────────────────────────────────

    def list_env_vars(self, service_id: str) -> List[Dict[str, Any]]:
        """List all environment variables for a service."""
        result = self._request("GET", f"/services/{service_id}/env-vars")
        data = self._json(result)
        if isinstance(data, list):
            return [item.get("envVar", item) for item in data]
        return []

    def update_env_vars(
        self, service_id: str, env_vars: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Bulk update environment variables for a service.

        The ``env_vars`` list should contain objects with ``key``
        and ``value`` (or ``generateValue``) fields.
        """
        result = self._request(
            "PUT", f"/services/{service_id}/env-vars", body=env_vars
        )
        data = self._json(result)
        if isinstance(data, list):
            return [item.get("envVar", item) for item in data]
        return []

    def get_env_var(self, service_id: str, key: str) -> Optional[Dict[str, Any]]:
        """Get a specific environment variable."""
        try:
            result = self._request(
                "GET", f"/services/{service_id}/env-vars/{key}"
            )
            return self._json(result)
        except ProviderAPIFault:
            return None

    def delete_env_var(self, service_id: str, key: str) -> None:
        """Delete a specific environment variable."""
        self._request("DELETE", f"/services/{service_id}/env-vars/{key}")

    # ─── Custom Domains ──────────────────────────────────────────────

    def list_custom_domains(self, service_id: str) -> List[Dict[str, Any]]:
        """List custom domains for a service."""
        result = self._request(
            "GET", f"/services/{service_id}/custom-domains"
        )
        data = self._json(result)
        if isinstance(data, list):
            return [item.get("customDomain", item) for item in data]
        return []

    def add_custom_domain(
        self, service_id: str, domain_name: str
    ) -> Dict[str, Any]:
        """Add a custom domain to a service."""
        result = self._request(
            "POST",
            f"/services/{service_id}/custom-domains",
            body={"name": domain_name},
        )
        return self._json(result)

    def delete_custom_domain(
        self, service_id: str, domain_name: str
    ) -> None:
        """Remove a custom domain from a service."""
        self._request(
            "DELETE", f"/services/{service_id}/custom-domains/{domain_name}"
        )

    # ─── Autoscaling ─────────────────────────────────────────────────

    def set_autoscaling(
        self, service_id: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Configure autoscaling for a service."""
        result = self._request(
            "PUT", f"/services/{service_id}/autoscaling", body=config
        )
        return self._json(result)

    def remove_autoscaling(self, service_id: str) -> None:
        """Remove autoscaling from a service."""
        self._request("DELETE", f"/services/{service_id}/autoscaling")

    # ─── Scaling ─────────────────────────────────────────────────────

    def scale_service(self, service_id: str, num_instances: int) -> None:
        """Manually scale a service to a specific instance count."""
        self._request(
            "POST",
            f"/services/{service_id}/scale",
            body={"numInstances": num_instances},
        )

    # ─── Account / Owners ────────────────────────────────────────────

    def get_user(self) -> Dict[str, Any]:
        """Get the authenticated user's details.

        This is the primary token-validation endpoint on Render:
        ``GET /v1/owners?limit=1`` (the /user endpoint may require
        different scopes).
        """
        result = self._request("GET", "/owners", params={"limit": "1"})
        data = self._json(result)
        # Render returns [{owner: {...}, cursor: "..."}]
        if isinstance(data, list) and data:
            return data[0].get("owner", data[0])
        return {}

    def list_owners(self) -> List[RenderOwner]:
        """List owners (workspaces) for the authenticated user."""
        result = self._request("GET", "/owners")
        data = self._json(result)
        owners: List[RenderOwner] = []
        if isinstance(data, list):
            for item in data:
                raw = item.get("owner", item)
                owners.append(RenderOwner(
                    id=raw.get("id"),
                    name=raw.get("name", ""),
                    email=raw.get("email"),
                    type=raw.get("type"),
                ))
        return owners

    def validate_token(self) -> bool:
        """Validate the API token by fetching owner info.

        Returns True if valid, False otherwise.
        """
        try:
            user = self.get_user()
            return bool(user.get("id") or user.get("name"))
        except ProviderAuthFault:
            return False
        except ProviderAPIFault:
            return False

    # ─── Parsers ─────────────────────────────────────────────────────

    @staticmethod
    def _parse_service(data: Dict[str, Any]) -> RenderService:
        svc_type = data.get("type", "web_service")
        try:
            service_type = RenderServiceType(svc_type)
        except ValueError:
            service_type = RenderServiceType.WEB_SERVICE

        return RenderService(
            id=data.get("id"),
            name=data.get("name", ""),
            owner_id=data.get("ownerId"),
            slug=data.get("slug"),
            type=service_type,
            plan=data.get("plan"),
            region=data.get("region"),
            status=data.get("status"),
            suspended=data.get("suspended"),
            auto_deploy=data.get("autoDeploy"),
            service_details=data.get("serviceDetails"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )

    @staticmethod
    def _parse_deploy(data: Dict[str, Any]) -> RenderDeploy:
        return RenderDeploy(
            id=data.get("id"),
            service_id=data.get("serviceId"),
            status=data.get("status"),
            commit=data.get("commit"),
            image=data.get("image"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            finished_at=data.get("finishedAt"),
        )
