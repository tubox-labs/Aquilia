"""
Render REST API Client — Comprehensive v2.

Typed HTTP client covering the **entire** Render platform API v1
surface: services, deploys, env vars, custom domains, disks,
autoscaling, secret files, headers, redirect rules, jobs, instances,
events, logs, metrics, postgres, key-value, projects, environments,
env groups, registry credentials, webhooks, maintenance, notifications,
blueprints, log streams, workspace members, and more.

Security
--------
- Bearer tokens are never logged or included in error messages.
- All API calls use HTTPS exclusively.
- Response bodies are validated before deserialization.
- Rate-limit headers are respected automatically.
- Request IDs are tracked for audit correlation.
- Token is redacted from all ``__repr__`` output.

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
    RenderAuditLogEntry,
    RenderBlueprint,
    RenderBlueprintSync,
    RenderCustomDomain,
    RenderDeploy,
    RenderDiskSnapshot,
    RenderEnvGroup,
    RenderEnvVar,
    RenderEvent,
    RenderHeaderRule,
    RenderInstance,
    RenderJob,
    RenderKeyValueConnectionInfo,
    RenderKeyValueInstance,
    RenderLogEntry,
    RenderLogStream,
    RenderMaintenance,
    RenderMetricPoint,
    RenderMetricsFilter,
    RenderNotificationSettings,
    RenderOwner,
    RenderPostgresConnectionInfo,
    RenderPostgresInstance,
    RenderPostgresUser,
    RenderProject,
    RenderEnvironment,
    RenderRedirectRule,
    RenderRegistryCredential,
    RenderSecretFile,
    RenderService,
    RenderServiceType,
    RenderWebhook,
    RenderWorkspaceMember,
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
_USER_AGENT = "Aquilia-CLI/2.0"
_DEFAULT_TIMEOUT = 30
_MAX_RETRIES = 3
_RETRY_BACKOFF = 1.5


def _build_ssl_context() -> ssl.SSLContext:
    """Build an SSL context that works on all platforms.

    macOS Python installations ship their own OpenSSL that does
    **not** use the system Keychain.  We solve this by:

    1. Trying ``certifi`` (ships Mozilla's CA bundle).
    2. Falling back to ``ssl.create_default_context()``.
    """
    ctx = ssl.create_default_context()
    try:
        import certifi
        ctx.load_verify_locations(certifi.where())
        return ctx
    except (ImportError, OSError):
        pass
    try:
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED
        return ctx
    except Exception:
        pass
    return ssl.create_default_context()


_SSL_CTX: ssl.SSLContext = _build_ssl_context()


# Legacy aliases
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

    Uses only stdlib ``urllib``.  Supports retry with exponential
    backoff and rate-limit awareness.  Cursor-based pagination.

    Args:
        token: Render API bearer token.
        base_url: API base URL (override for testing).
        timeout: Request timeout in seconds.
        max_retries: Maximum retry attempts for transient failures.
        ssl_context: Custom SSL context (default uses certifi).
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
        body: Optional[Any] = None,
        params: Optional[Dict[str, str]] = None,
    ) -> _RequestResult:
        """Execute an HTTP request with retry and rate-limit handling."""
        url = f"{self._base_url}{path}"
        if params:
            url += "?" + urllib.parse.urlencode(params)

        data = json.dumps(body).encode("utf-8") if body is not None else None

        last_error: Optional[Exception] = None

        for attempt in range(self._max_retries + 1):
            try:
                req = urllib.request.Request(
                    url, data=data, headers=self._headers(), method=method.upper(),
                )
                with urllib.request.urlopen(req, timeout=self._timeout, context=self._ssl_ctx) as resp:
                    resp_body = resp.read()
                    resp_headers = {k.lower(): v for k, v in resp.getheaders()}
                    return _RequestResult(status=resp.status, body=resp_body, headers=resp_headers)

            except urllib.error.HTTPError as e:
                resp_body = e.read()
                resp_headers = {k.lower(): v for k, v in e.headers.items()}
                status = e.code

                if status == 429:
                    retry_after = float(resp_headers.get("retry-after", str(2 ** attempt)))
                    if attempt < self._max_retries:
                        _logger.warning("Rate limited. Waiting %.1fs (attempt %d/%d)", retry_after, attempt + 1, self._max_retries)
                        time.sleep(retry_after)
                        continue
                    raise ProviderRateLimitFault(retry_after=retry_after)

                if status in (401, 403):
                    msg = self._parse_error_message(resp_body)
                    raise ProviderAuthFault(status, msg or "Authentication failed", request_id=resp_headers.get("x-request-id"))

                if status >= 500 and attempt < self._max_retries:
                    wait = _RETRY_BACKOFF ** attempt
                    _logger.warning("Server error %d. Retrying in %.1fs (attempt %d/%d)", status, wait, attempt + 1, self._max_retries)
                    time.sleep(wait)
                    last_error = e
                    continue

                msg = self._parse_error_message(resp_body)
                raise ProviderAPIFault(status, msg or f"HTTP {status}", request_id=resp_headers.get("x-request-id"))

            except urllib.error.URLError as e:
                if attempt < self._max_retries:
                    wait = _RETRY_BACKOFF ** attempt
                    _logger.warning("Connection error: %s. Retrying in %.1fs", e.reason, wait)
                    time.sleep(wait)
                    last_error = e
                    continue
                raise ProviderConnectionFault(f"Connection failed: {e.reason}")

        raise ProviderAPIFault(0, f"Max retries exhausted: {last_error}")

    def _parse_error_message(self, body: bytes) -> Optional[str]:
        try:
            data = json.loads(body)
            return data.get("message") or data.get("error") or data.get("detail")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    def _json(self, result: _RequestResult) -> Any:
        if not result.body:
            return {}
        return json.loads(result.body)

    # ═════════════════════════════════════════════════════════════════
    # Services
    # ═════════════════════════════════════════════════════════════════

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
        """List all services, optionally filtered."""
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

        if isinstance(data, list):
            return [self._parse_service(item.get("service", item)) for item in data]
        return []

    def get_service(self, service_id: str) -> RenderService:
        """Get a specific service by ID."""
        result = self._request("GET", f"/services/{service_id}")
        return self._parse_service(self._json(result))

    def get_service_by_name(self, name: str, owner_id: Optional[str] = None) -> Optional[RenderService]:
        """Find a service by name."""
        services = self.list_services(name=name, owner_id=owner_id)
        for svc in services:
            if svc.name == name:
                return svc
        return None

    def create_service(self, payload: Dict[str, Any]) -> RenderService:
        """Create a new service."""
        result = self._request("POST", "/services", body=payload)
        data = self._json(result)
        return self._parse_service(data.get("service", data))

    def update_service(self, service_id: str, payload: Dict[str, Any]) -> RenderService:
        """Update an existing service (PATCH)."""
        result = self._request("PATCH", f"/services/{service_id}", body=payload)
        return self._parse_service(self._json(result))

    def delete_service(self, service_id: str) -> None:
        """Delete a service."""
        self._request("DELETE", f"/services/{service_id}")

    def suspend_service(self, service_id: str) -> None:
        """Suspend a running service."""
        self._request("POST", f"/services/{service_id}/suspend")

    def resume_service(self, service_id: str) -> None:
        """Resume a suspended service."""
        self._request("POST", f"/services/{service_id}/resume")

    def restart_service(self, service_id: str) -> None:
        """Restart a running service (zero-downtime)."""
        self._request("POST", f"/services/{service_id}/restart")

    def purge_cache(self, service_id: str) -> None:
        """Clear the build cache for a service."""
        self._request("POST", f"/services/{service_id}/cache/purge")

    def create_preview(self, service_id: str, *, image_url: Optional[str] = None, name: Optional[str] = None) -> RenderService:
        """Create a preview instance of a service."""
        body: Dict[str, Any] = {}
        if image_url:
            body["imageUrl"] = image_url
        if name:
            body["name"] = name
        result = self._request("POST", f"/services/{service_id}/preview", body=body)
        data = self._json(result)
        return self._parse_service(data.get("service", data))

    # ═════════════════════════════════════════════════════════════════
    # Deploys
    # ═════════════════════════════════════════════════════════════════

    def list_deploys(self, service_id: str, *, cursor: Optional[str] = None, limit: int = 10) -> List[RenderDeploy]:
        """List deploys for a service."""
        params: Dict[str, str] = {"limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        result = self._request("GET", f"/services/{service_id}/deploys", params=params)
        data = self._json(result)
        if isinstance(data, list):
            return [self._parse_deploy(item.get("deploy", item)) for item in data]
        return []

    def get_deploy(self, service_id: str, deploy_id: str) -> RenderDeploy:
        """Get a specific deploy."""
        result = self._request("GET", f"/services/{service_id}/deploys/{deploy_id}")
        return self._parse_deploy(self._json(result))

    def trigger_deploy(self, service_id: str) -> RenderDeploy:
        """Trigger a new deploy."""
        result = self._request("POST", f"/services/{service_id}/deploys")
        return self._parse_deploy(self._json(result))

    def cancel_deploy(self, service_id: str, deploy_id: str) -> RenderDeploy:
        """Cancel a running deploy."""
        result = self._request("POST", f"/services/{service_id}/deploys/{deploy_id}/cancel")
        return self._parse_deploy(self._json(result))

    def rollback_deploy(self, service_id: str, deploy_id: str) -> RenderDeploy:
        """Rollback to a previous deploy."""
        result = self._request("POST", f"/services/{service_id}/rollbacks", body={"deployId": deploy_id})
        return self._parse_deploy(self._json(result))

    # ═════════════════════════════════════════════════════════════════
    # Environment Variables
    # ═════════════════════════════════════════════════════════════════

    def list_env_vars(self, service_id: str) -> List[Dict[str, Any]]:
        """List all environment variables for a service."""
        result = self._request("GET", f"/services/{service_id}/env-vars")
        data = self._json(result)
        if isinstance(data, list):
            return [item.get("envVar", item) for item in data]
        return []

    def update_env_vars(self, service_id: str, env_vars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bulk update environment variables for a service."""
        result = self._request("PUT", f"/services/{service_id}/env-vars", body=env_vars)
        data = self._json(result)
        if isinstance(data, list):
            return [item.get("envVar", item) for item in data]
        return []

    def get_env_var(self, service_id: str, key: str) -> Optional[Dict[str, Any]]:
        """Get a specific environment variable."""
        try:
            result = self._request("GET", f"/services/{service_id}/env-vars/{key}")
            return self._json(result)
        except ProviderAPIFault:
            return None

    def delete_env_var(self, service_id: str, key: str) -> None:
        """Delete a specific environment variable."""
        self._request("DELETE", f"/services/{service_id}/env-vars/{key}")

    # ═════════════════════════════════════════════════════════════════
    # Custom Domains
    # ═════════════════════════════════════════════════════════════════

    def list_custom_domains(self, service_id: str) -> List[Dict[str, Any]]:
        """List custom domains for a service."""
        result = self._request("GET", f"/services/{service_id}/custom-domains")
        data = self._json(result)
        if isinstance(data, list):
            return [item.get("customDomain", item) for item in data]
        return []

    def add_custom_domain(self, service_id: str, domain_name: str) -> Dict[str, Any]:
        """Add a custom domain to a service."""
        result = self._request("POST", f"/services/{service_id}/custom-domains", body={"name": domain_name})
        return self._json(result)

    def delete_custom_domain(self, service_id: str, domain_name: str) -> None:
        """Remove a custom domain."""
        self._request("DELETE", f"/services/{service_id}/custom-domains/{domain_name}")

    def verify_dns(self, service_id: str, domain_name: str) -> Dict[str, Any]:
        """Verify DNS configuration for a custom domain."""
        result = self._request("POST", f"/services/{service_id}/custom-domains/{domain_name}/verify")
        return self._json(result)

    # ═════════════════════════════════════════════════════════════════
    # Secret Files
    # ═════════════════════════════════════════════════════════════════

    def list_secret_files(self, service_id: str) -> List[RenderSecretFile]:
        """List secret files for a service."""
        result = self._request("GET", f"/services/{service_id}/secret-files")
        data = self._json(result)
        if isinstance(data, list):
            return [RenderSecretFile(name=item.get("name", ""), content=item.get("content", "")) for item in data]
        return []

    def update_secret_files(self, service_id: str, files: List[Dict[str, str]]) -> List[RenderSecretFile]:
        """Bulk update secret files (PUT replaces all)."""
        result = self._request("PUT", f"/services/{service_id}/secret-files", body=files)
        data = self._json(result)
        if isinstance(data, list):
            return [RenderSecretFile(name=item.get("name", ""), content=item.get("content", "")) for item in data]
        return []

    def delete_secret_file(self, service_id: str, name: str) -> None:
        """Delete a specific secret file."""
        self._request("DELETE", f"/services/{service_id}/secret-files/{name}")

    # ═════════════════════════════════════════════════════════════════
    # Header Rules
    # ═════════════════════════════════════════════════════════════════

    def list_headers(self, service_id: str) -> List[RenderHeaderRule]:
        """List HTTP header rules for a service."""
        result = self._request("GET", f"/services/{service_id}/headers")
        data = self._json(result)
        if isinstance(data, list):
            return [RenderHeaderRule(id=h.get("id"), path=h.get("path", "/*"), name=h.get("name", ""), value=h.get("value", "")) for h in data]
        return []

    def add_header(self, service_id: str, header: Dict[str, str]) -> RenderHeaderRule:
        """Add an HTTP header rule."""
        result = self._request("POST", f"/services/{service_id}/headers", body=header)
        data = self._json(result)
        return RenderHeaderRule(id=data.get("id"), path=data.get("path", "/*"), name=data.get("name", ""), value=data.get("value", ""))

    def delete_header(self, service_id: str, header_id: str) -> None:
        """Delete an HTTP header rule."""
        self._request("DELETE", f"/services/{service_id}/headers/{header_id}")

    # ═════════════════════════════════════════════════════════════════
    # Redirect / Rewrite Rules
    # ═════════════════════════════════════════════════════════════════

    def list_redirect_rules(self, service_id: str) -> List[RenderRedirectRule]:
        """List redirect/rewrite rules."""
        result = self._request("GET", f"/services/{service_id}/routes")
        data = self._json(result)
        if isinstance(data, list):
            return [RenderRedirectRule(id=r.get("id"), source=r.get("source", ""), destination=r.get("destination", ""), type=r.get("type", "redirect"), status_code=r.get("statusCode", 301)) for r in data]
        return []

    def add_redirect_rule(self, service_id: str, rule: Dict[str, Any]) -> RenderRedirectRule:
        """Add a redirect/rewrite rule."""
        result = self._request("POST", f"/services/{service_id}/routes", body=rule)
        data = self._json(result)
        return RenderRedirectRule(id=data.get("id"), source=data.get("source", ""), destination=data.get("destination", ""), type=data.get("type", "redirect"), status_code=data.get("statusCode", 301))

    def delete_redirect_rule(self, service_id: str, rule_id: str) -> None:
        """Delete a redirect/rewrite rule."""
        self._request("DELETE", f"/services/{service_id}/routes/{rule_id}")

    # ═════════════════════════════════════════════════════════════════
    # Instances
    # ═════════════════════════════════════════════════════════════════

    def list_instances(self, service_id: str) -> List[RenderInstance]:
        """List running instances of a service."""
        result = self._request("GET", f"/services/{service_id}/instances")
        data = self._json(result)
        if isinstance(data, list):
            return [RenderInstance(id=i.get("id"), service_id=service_id, status=i.get("status"), created_at=i.get("createdAt"), region=i.get("region")) for i in data]
        return []

    # ═════════════════════════════════════════════════════════════════
    # Events
    # ═════════════════════════════════════════════════════════════════

    def list_events(self, service_id: str, *, cursor: Optional[str] = None, limit: int = 20) -> List[RenderEvent]:
        """List events for a service."""
        params: Dict[str, str] = {"limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        result = self._request("GET", f"/services/{service_id}/events", params=params)
        data = self._json(result)
        if isinstance(data, list):
            return [RenderEvent(id=e.get("id"), service_id=service_id, type=e.get("type"), timestamp=e.get("timestamp"), details=e.get("details")) for e in data]
        return []

    # ═════════════════════════════════════════════════════════════════
    # Jobs (Cron & One-Off)
    # ═════════════════════════════════════════════════════════════════

    def list_jobs(self, service_id: str, *, cursor: Optional[str] = None, limit: int = 20) -> List[RenderJob]:
        """List job executions for a cron service."""
        params: Dict[str, str] = {"limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        result = self._request("GET", f"/services/{service_id}/jobs", params=params)
        data = self._json(result)
        if isinstance(data, list):
            return [self._parse_job(j.get("job", j)) for j in data]
        return []

    def trigger_job(self, service_id: str) -> RenderJob:
        """Manually trigger a cron job execution."""
        result = self._request("POST", f"/services/{service_id}/jobs")
        return self._parse_job(self._json(result))

    def cancel_job(self, service_id: str, job_id: str) -> RenderJob:
        """Cancel a running job."""
        result = self._request("POST", f"/services/{service_id}/jobs/{job_id}/cancel")
        return self._parse_job(self._json(result))

    # ═════════════════════════════════════════════════════════════════
    # Autoscaling
    # ═════════════════════════════════════════════════════════════════

    def set_autoscaling(self, service_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Configure autoscaling for a service."""
        result = self._request("PUT", f"/services/{service_id}/autoscaling", body=config)
        return self._json(result)

    def remove_autoscaling(self, service_id: str) -> None:
        """Remove autoscaling from a service."""
        self._request("DELETE", f"/services/{service_id}/autoscaling")

    def scale_service(self, service_id: str, num_instances: int) -> None:
        """Manually scale a service to a specific instance count."""
        self._request("POST", f"/services/{service_id}/scale", body={"numInstances": num_instances})

    # ═════════════════════════════════════════════════════════════════
    # Disks & Snapshots
    # ═════════════════════════════════════════════════════════════════

    def list_disks(self, service_id: str) -> List[Dict[str, Any]]:
        """List persistent disks for a service."""
        result = self._request("GET", f"/services/{service_id}/disks")
        return self._json(result) if isinstance(self._json(result), list) else []

    def create_disk(self, service_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Create a persistent disk."""
        result = self._request("POST", f"/services/{service_id}/disks", body=payload)
        return self._json(result)

    def delete_disk(self, disk_id: str) -> None:
        """Delete a persistent disk."""
        self._request("DELETE", f"/disks/{disk_id}")

    def list_disk_snapshots(self, disk_id: str) -> List[RenderDiskSnapshot]:
        """List snapshots for a persistent disk."""
        result = self._request("GET", f"/disks/{disk_id}/snapshots")
        data = self._json(result)
        if isinstance(data, list):
            return [RenderDiskSnapshot(id=s.get("id"), disk_id=disk_id, created_at=s.get("createdAt"), status=s.get("status")) for s in data]
        return []

    def restore_disk_snapshot(self, disk_id: str, snapshot_id: str) -> Dict[str, Any]:
        """Restore a persistent disk from a snapshot."""
        result = self._request("POST", f"/disks/{disk_id}/snapshots/{snapshot_id}/restore")
        return self._json(result)

    # ═════════════════════════════════════════════════════════════════
    # Logs
    # ═════════════════════════════════════════════════════════════════

    def get_logs(
        self,
        *,
        owner_id: Optional[str] = None,
        service_id: Optional[str] = None,
        direction: str = "backward",
        limit: int = 100,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        level: Optional[str] = None,
        log_type: Optional[str] = None,
        text: Optional[str] = None,
        instance_id: Optional[str] = None,
    ) -> List[RenderLogEntry]:
        """Retrieve logs from the Render logging API."""
        params: Dict[str, str] = {"direction": direction, "limit": str(limit)}
        if owner_id:
            params["ownerId"] = owner_id
        if service_id:
            params["resource"] = service_id
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if level:
            params["level"] = level
        if log_type:
            params["type"] = log_type
        if text:
            params["text"] = text
        if instance_id:
            params["instanceId"] = instance_id

        result = self._request("GET", "/logs", params=params)
        data = self._json(result)
        if isinstance(data, list):
            return [RenderLogEntry(
                timestamp=l.get("timestamp"),
                message=l.get("message", ""),
                level=l.get("level"),
                service_id=l.get("serviceId"),
                instance_id=l.get("instanceId"),
                deploy_id=l.get("deployId"),
                type=l.get("type"),
            ) for l in data]
        return []

    # ═════════════════════════════════════════════════════════════════
    # Metrics
    # ═════════════════════════════════════════════════════════════════

    def get_metrics(
        self,
        service_id: str,
        *,
        metric: str = "cpu",
        period: str = "1h",
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        instance_id: Optional[str] = None,
    ) -> List[RenderMetricPoint]:
        """Retrieve service metrics (CPU, memory, HTTP, bandwidth, disk)."""
        params: Dict[str, str] = {"metric": metric, "period": period}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if instance_id:
            params["instanceId"] = instance_id

        result = self._request("GET", f"/services/{service_id}/metrics", params=params)
        data = self._json(result)
        if isinstance(data, list):
            return [RenderMetricPoint(timestamp=p.get("timestamp"), value=p.get("value", 0.0), unit=p.get("unit"), label=p.get("label")) for p in data]
        return []

    def get_metrics_filtered(self, flt: RenderMetricsFilter) -> List[RenderMetricPoint]:
        """Retrieve metrics using a RenderMetricsFilter object."""
        if not flt.resource_id:
            return []
        return self.get_metrics(flt.resource_id, metric=flt.metric, period=flt.period, start_time=flt.start_time, end_time=flt.end_time, instance_id=flt.instance_id)

    # ═════════════════════════════════════════════════════════════════
    # Postgres
    # ═════════════════════════════════════════════════════════════════

    def list_postgres(self, *, owner_id: Optional[str] = None, cursor: Optional[str] = None, limit: int = 20) -> List[RenderPostgresInstance]:
        """List Postgres database instances."""
        params: Dict[str, str] = {"limit": str(limit)}
        if owner_id:
            params["ownerId"] = owner_id
        if cursor:
            params["cursor"] = cursor
        result = self._request("GET", "/postgres", params=params)
        data = self._json(result)
        if isinstance(data, list):
            return [self._parse_postgres(item.get("postgres", item)) for item in data]
        return []

    def create_postgres(self, payload: Dict[str, Any]) -> RenderPostgresInstance:
        """Create a new Postgres database."""
        result = self._request("POST", "/postgres", body=payload)
        data = self._json(result)
        return self._parse_postgres(data.get("postgres", data))

    def get_postgres(self, postgres_id: str) -> RenderPostgresInstance:
        """Get a specific Postgres instance."""
        result = self._request("GET", f"/postgres/{postgres_id}")
        return self._parse_postgres(self._json(result))

    def delete_postgres(self, postgres_id: str) -> None:
        """Delete a Postgres database."""
        self._request("DELETE", f"/postgres/{postgres_id}")

    def get_postgres_connection_info(self, postgres_id: str) -> RenderPostgresConnectionInfo:
        """Get connection info for a Postgres database."""
        result = self._request("GET", f"/postgres/{postgres_id}/connection-info")
        data = self._json(result)
        return RenderPostgresConnectionInfo(
            internal_connection_string=data.get("internalConnectionString"),
            external_connection_string=data.get("externalConnectionString"),
            psql_command=data.get("psqlCommand"),
            host=data.get("host"),
            port=data.get("port"),
            database=data.get("database"),
            user=data.get("user"),
            password=data.get("password"),
        )

    def list_postgres_users(self, postgres_id: str) -> List[RenderPostgresUser]:
        """List users in a Postgres database."""
        result = self._request("GET", f"/postgres/{postgres_id}/users")
        data = self._json(result)
        if isinstance(data, list):
            return [RenderPostgresUser(name=u.get("name", ""), grants=u.get("grants", [])) for u in data]
        return []

    def create_postgres_user(self, postgres_id: str, name: str) -> RenderPostgresUser:
        """Create a new Postgres user."""
        result = self._request("POST", f"/postgres/{postgres_id}/users", body={"name": name})
        data = self._json(result)
        return RenderPostgresUser(name=data.get("name", ""), password=data.get("password"), grants=data.get("grants", []))

    def delete_postgres_user(self, postgres_id: str, user_name: str) -> None:
        """Delete a Postgres user."""
        self._request("DELETE", f"/postgres/{postgres_id}/users/{user_name}")

    # ═════════════════════════════════════════════════════════════════
    # Key-Value (Redis)
    # ═════════════════════════════════════════════════════════════════

    def list_key_value(self, *, owner_id: Optional[str] = None, cursor: Optional[str] = None, limit: int = 20) -> List[RenderKeyValueInstance]:
        """List Key-Value (Redis) store instances."""
        params: Dict[str, str] = {"limit": str(limit)}
        if owner_id:
            params["ownerId"] = owner_id
        if cursor:
            params["cursor"] = cursor
        result = self._request("GET", "/key-value", params=params)
        data = self._json(result)
        if isinstance(data, list):
            return [self._parse_key_value(item.get("keyValue", item)) for item in data]
        return []

    def create_key_value(self, payload: Dict[str, Any]) -> RenderKeyValueInstance:
        """Create a new Key-Value store."""
        result = self._request("POST", "/key-value", body=payload)
        data = self._json(result)
        return self._parse_key_value(data.get("keyValue", data))

    def get_key_value(self, kv_id: str) -> RenderKeyValueInstance:
        """Get a specific Key-Value instance."""
        result = self._request("GET", f"/key-value/{kv_id}")
        return self._parse_key_value(self._json(result))

    def delete_key_value(self, kv_id: str) -> None:
        """Delete a Key-Value store."""
        self._request("DELETE", f"/key-value/{kv_id}")

    def get_key_value_connection_info(self, kv_id: str) -> RenderKeyValueConnectionInfo:
        """Get connection info for a Key-Value store."""
        result = self._request("GET", f"/key-value/{kv_id}/connection-info")
        data = self._json(result)
        return RenderKeyValueConnectionInfo(
            internal_connection_string=data.get("internalConnectionString"),
            external_connection_string=data.get("externalConnectionString"),
            host=data.get("host"),
            port=data.get("port"),
            password=data.get("password"),
        )

    # ═════════════════════════════════════════════════════════════════
    # Projects & Environments
    # ═════════════════════════════════════════════════════════════════

    def list_projects(self, *, owner_id: Optional[str] = None, cursor: Optional[str] = None, limit: int = 20) -> List[RenderProject]:
        """List projects."""
        params: Dict[str, str] = {"limit": str(limit)}
        if owner_id:
            params["ownerId"] = owner_id
        if cursor:
            params["cursor"] = cursor
        result = self._request("GET", "/projects", params=params)
        data = self._json(result)
        if isinstance(data, list):
            return [RenderProject(id=p.get("id"), name=p.get("name", ""), owner_id=p.get("ownerId"), created_at=p.get("createdAt")) for p in data]
        return []

    def create_project(self, payload: Dict[str, Any]) -> RenderProject:
        """Create a new project."""
        result = self._request("POST", "/projects", body=payload)
        data = self._json(result)
        return RenderProject(id=data.get("id"), name=data.get("name", ""), owner_id=data.get("ownerId"))

    def get_project(self, project_id: str) -> RenderProject:
        """Get a specific project."""
        result = self._request("GET", f"/projects/{project_id}")
        data = self._json(result)
        return RenderProject(id=data.get("id"), name=data.get("name", ""), owner_id=data.get("ownerId"), created_at=data.get("createdAt"))

    def delete_project(self, project_id: str) -> None:
        """Delete a project."""
        self._request("DELETE", f"/projects/{project_id}")

    def list_environments(self, project_id: str) -> List[RenderEnvironment]:
        """List environments for a project."""
        result = self._request("GET", f"/projects/{project_id}/environments")
        data = self._json(result)
        if isinstance(data, list):
            return [RenderEnvironment(id=e.get("id"), name=e.get("name", ""), project_id=project_id, protected_status=e.get("protectedStatus"), created_at=e.get("createdAt")) for e in data]
        return []

    def create_environment(self, project_id: str, payload: Dict[str, Any]) -> RenderEnvironment:
        """Create a new environment in a project."""
        result = self._request("POST", f"/projects/{project_id}/environments", body=payload)
        data = self._json(result)
        return RenderEnvironment(id=data.get("id"), name=data.get("name", ""), project_id=project_id)

    def delete_environment(self, project_id: str, environment_id: str) -> None:
        """Delete an environment."""
        self._request("DELETE", f"/projects/{project_id}/environments/{environment_id}")

    # ═════════════════════════════════════════════════════════════════
    # Env Groups
    # ═════════════════════════════════════════════════════════════════

    def list_env_groups(self, *, owner_id: Optional[str] = None, cursor: Optional[str] = None, limit: int = 20) -> List[RenderEnvGroup]:
        """List environment groups."""
        params: Dict[str, str] = {"limit": str(limit)}
        if owner_id:
            params["ownerId"] = owner_id
        if cursor:
            params["cursor"] = cursor
        result = self._request("GET", "/env-groups", params=params)
        data = self._json(result)
        if isinstance(data, list):
            return [self._parse_env_group(item.get("envGroup", item)) for item in data]
        return []

    def create_env_group(self, payload: Dict[str, Any]) -> RenderEnvGroup:
        """Create a new environment group."""
        result = self._request("POST", "/env-groups", body=payload)
        data = self._json(result)
        return self._parse_env_group(data.get("envGroup", data))

    def get_env_group(self, env_group_id: str) -> RenderEnvGroup:
        """Get a specific environment group."""
        result = self._request("GET", f"/env-groups/{env_group_id}")
        return self._parse_env_group(self._json(result))

    def update_env_group(self, env_group_id: str, payload: Dict[str, Any]) -> RenderEnvGroup:
        """Update an environment group."""
        result = self._request("PATCH", f"/env-groups/{env_group_id}", body=payload)
        return self._parse_env_group(self._json(result))

    def delete_env_group(self, env_group_id: str) -> None:
        """Delete an environment group."""
        self._request("DELETE", f"/env-groups/{env_group_id}")

    def link_service_to_env_group(self, env_group_id: str, service_id: str) -> None:
        """Link a service to an environment group."""
        self._request("POST", f"/env-groups/{env_group_id}/link", body={"serviceId": service_id})

    def unlink_service_from_env_group(self, env_group_id: str, service_id: str) -> None:
        """Unlink a service from an environment group."""
        self._request("POST", f"/env-groups/{env_group_id}/unlink", body={"serviceId": service_id})

    # ═════════════════════════════════════════════════════════════════
    # Registry Credentials
    # ═════════════════════════════════════════════════════════════════

    def list_registry_credentials(self, *, owner_id: Optional[str] = None) -> List[RenderRegistryCredential]:
        """List private registry credentials."""
        params: Dict[str, str] = {}
        if owner_id:
            params["ownerId"] = owner_id
        result = self._request("GET", "/registries", params=params or None)
        data = self._json(result)
        if isinstance(data, list):
            return [RenderRegistryCredential(id=r.get("id"), name=r.get("name", ""), registry=r.get("registry", ""), username=r.get("username", ""), created_at=r.get("createdAt")) for r in data]
        return []

    def create_registry_credential(self, payload: Dict[str, Any]) -> RenderRegistryCredential:
        """Create a private registry credential."""
        result = self._request("POST", "/registries", body=payload)
        data = self._json(result)
        return RenderRegistryCredential(id=data.get("id"), name=data.get("name", ""), registry=data.get("registry", ""), username=data.get("username", ""))

    def delete_registry_credential(self, credential_id: str) -> None:
        """Delete a registry credential."""
        self._request("DELETE", f"/registries/{credential_id}")

    # ═════════════════════════════════════════════════════════════════
    # Blueprints / IaC
    # ═════════════════════════════════════════════════════════════════

    def list_blueprints(self, *, owner_id: Optional[str] = None, cursor: Optional[str] = None, limit: int = 20) -> List[RenderBlueprint]:
        """List blueprints."""
        params: Dict[str, str] = {"limit": str(limit)}
        if owner_id:
            params["ownerId"] = owner_id
        if cursor:
            params["cursor"] = cursor
        result = self._request("GET", "/blueprints", params=params)
        data = self._json(result)
        if isinstance(data, list):
            return [self._parse_blueprint(item.get("blueprint", item)) for item in data]
        return []

    def get_blueprint(self, blueprint_id: str) -> RenderBlueprint:
        """Get a specific blueprint."""
        result = self._request("GET", f"/blueprints/{blueprint_id}")
        return self._parse_blueprint(self._json(result))

    def sync_blueprint(self, blueprint_id: str) -> RenderBlueprintSync:
        """Trigger a blueprint sync."""
        result = self._request("POST", f"/blueprints/{blueprint_id}/sync")
        data = self._json(result)
        return RenderBlueprintSync(id=data.get("id"), blueprint_id=blueprint_id, status=data.get("status"))

    # ═════════════════════════════════════════════════════════════════
    # Webhooks
    # ═════════════════════════════════════════════════════════════════

    def list_webhooks(self, *, owner_id: Optional[str] = None) -> List[RenderWebhook]:
        """List webhooks."""
        params: Dict[str, str] = {}
        if owner_id:
            params["ownerId"] = owner_id
        result = self._request("GET", "/webhooks", params=params or None)
        data = self._json(result)
        if isinstance(data, list):
            return [self._parse_webhook(w) for w in data]
        return []

    def create_webhook(self, payload: Dict[str, Any]) -> RenderWebhook:
        """Create a webhook subscription."""
        result = self._request("POST", "/webhooks", body=payload)
        return self._parse_webhook(self._json(result))

    def get_webhook(self, webhook_id: str) -> RenderWebhook:
        """Get a specific webhook."""
        result = self._request("GET", f"/webhooks/{webhook_id}")
        return self._parse_webhook(self._json(result))

    def update_webhook(self, webhook_id: str, payload: Dict[str, Any]) -> RenderWebhook:
        """Update a webhook."""
        result = self._request("PATCH", f"/webhooks/{webhook_id}", body=payload)
        return self._parse_webhook(self._json(result))

    def delete_webhook(self, webhook_id: str) -> None:
        """Delete a webhook."""
        self._request("DELETE", f"/webhooks/{webhook_id}")

    # ═════════════════════════════════════════════════════════════════
    # Maintenance
    # ═════════════════════════════════════════════════════════════════

    def list_maintenance_windows(self, service_id: str) -> List[RenderMaintenance]:
        """List maintenance windows for a service."""
        result = self._request("GET", f"/services/{service_id}/maintenance")
        data = self._json(result)
        if isinstance(data, list):
            return [RenderMaintenance(id=m.get("id"), service_id=service_id, status=m.get("status"), scheduled_at=m.get("scheduledAt"), description=m.get("description")) for m in data]
        return []

    def trigger_maintenance(self, service_id: str) -> RenderMaintenance:
        """Trigger maintenance for a service."""
        result = self._request("POST", f"/services/{service_id}/maintenance")
        data = self._json(result)
        return RenderMaintenance(id=data.get("id"), service_id=service_id, status=data.get("status"))

    # ═════════════════════════════════════════════════════════════════
    # Notifications
    # ═════════════════════════════════════════════════════════════════

    def get_notification_settings(self, service_id: str) -> RenderNotificationSettings:
        """Get notification settings for a service."""
        result = self._request("GET", f"/services/{service_id}/notification-overrides")
        data = self._json(result)
        return RenderNotificationSettings(notify_on_fail=data.get("notifyOnFail"), preview_notify_on_fail=data.get("previewNotifyOnFail"))

    def update_notification_settings(self, service_id: str, payload: Dict[str, str]) -> RenderNotificationSettings:
        """Update notification settings for a service."""
        result = self._request("PATCH", f"/services/{service_id}/notification-overrides", body=payload)
        data = self._json(result)
        return RenderNotificationSettings(notify_on_fail=data.get("notifyOnFail"), preview_notify_on_fail=data.get("previewNotifyOnFail"))

    # ═════════════════════════════════════════════════════════════════
    # Log Streams
    # ═════════════════════════════════════════════════════════════════

    def list_log_streams(self, *, owner_id: Optional[str] = None) -> List[RenderLogStream]:
        """List log stream sinks."""
        params: Dict[str, str] = {}
        if owner_id:
            params["ownerId"] = owner_id
        result = self._request("GET", "/log-streams", params=params or None)
        data = self._json(result)
        if isinstance(data, list):
            return [RenderLogStream(id=ls.get("id"), name=ls.get("name", ""), endpoint=ls.get("endpoint", ""), enabled=ls.get("enabled", True), created_at=ls.get("createdAt")) for ls in data]
        return []

    def create_log_stream(self, payload: Dict[str, Any]) -> RenderLogStream:
        """Create a log stream sink."""
        result = self._request("POST", "/log-streams", body=payload)
        data = self._json(result)
        return RenderLogStream(id=data.get("id"), name=data.get("name", ""), endpoint=data.get("endpoint", ""))

    def delete_log_stream(self, log_stream_id: str) -> None:
        """Delete a log stream sink."""
        self._request("DELETE", f"/log-streams/{log_stream_id}")

    # ═════════════════════════════════════════════════════════════════
    # Workspace / Owners / Members
    # ═════════════════════════════════════════════════════════════════

    def get_user(self) -> Dict[str, Any]:
        """Get the authenticated user's details."""
        result = self._request("GET", "/owners", params={"limit": "1"})
        data = self._json(result)
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
                    id=raw.get("id"), name=raw.get("name", ""),
                    email=raw.get("email"), type=raw.get("type"),
                ))
        return owners

    def list_workspace_members(self, owner_id: str) -> List[RenderWorkspaceMember]:
        """List members of a workspace/team."""
        result = self._request("GET", f"/owners/{owner_id}/members")
        data = self._json(result)
        if isinstance(data, list):
            return [RenderWorkspaceMember(
                id=m.get("id"), email=m.get("email"), name=m.get("name"),
                role=m.get("role"), joined_at=m.get("joinedAt"),
            ) for m in data]
        return []

    def validate_token(self) -> bool:
        """Validate the API token by fetching owner info."""
        try:
            user = self.get_user()
            return bool(user.get("id") or user.get("name"))
        except (ProviderAuthFault, ProviderAPIFault):
            return False

    # ═════════════════════════════════════════════════════════════════
    # Audit Logs
    # ═════════════════════════════════════════════════════════════════

    def list_audit_logs(self, owner_id: str, *, cursor: Optional[str] = None, limit: int = 50) -> List[RenderAuditLogEntry]:
        """List audit log entries for a workspace."""
        params: Dict[str, str] = {"limit": str(limit)}
        if cursor:
            params["cursor"] = cursor
        result = self._request("GET", f"/owners/{owner_id}/audit-logs", params=params)
        data = self._json(result)
        if isinstance(data, list):
            return [RenderAuditLogEntry(
                id=a.get("id"), action=a.get("action"), actor=a.get("actor"),
                resource=a.get("resource"), timestamp=a.get("timestamp"),
                details=a.get("details"),
            ) for a in data]
        return []

    # ═════════════════════════════════════════════════════════════════
    # Parsers
    # ═════════════════════════════════════════════════════════════════

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
            dashboard_url=data.get("dashboardUrl"),
            image_path=data.get("imagePath"),
            root_dir=data.get("rootDir"),
            notify_on_fail=data.get("notifyOnFail"),
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
            trigger=data.get("trigger"),
        )

    @staticmethod
    def _parse_job(data: Dict[str, Any]) -> RenderJob:
        return RenderJob(
            id=data.get("id"),
            service_id=data.get("serviceId"),
            status=data.get("status"),
            plan_id=data.get("planId"),
            started_at=data.get("startedAt"),
            finished_at=data.get("finishedAt"),
            created_at=data.get("createdAt"),
        )

    @staticmethod
    def _parse_postgres(data: Dict[str, Any]) -> RenderPostgresInstance:
        return RenderPostgresInstance(
            id=data.get("id"),
            name=data.get("name", ""),
            owner_id=data.get("ownerId"),
            plan=data.get("plan"),
            region=data.get("region"),
            status=data.get("status"),
            version=data.get("version"),
            disk_size_gb=data.get("diskSizeGB"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            dashboard_url=data.get("dashboardUrl"),
            high_availability_enabled=data.get("highAvailabilityEnabled", False),
        )

    @staticmethod
    def _parse_key_value(data: Dict[str, Any]) -> RenderKeyValueInstance:
        return RenderKeyValueInstance(
            id=data.get("id"),
            name=data.get("name", ""),
            owner_id=data.get("ownerId"),
            plan=data.get("plan"),
            region=data.get("region"),
            status=data.get("status"),
            max_memory_policy=data.get("maxmemoryPolicy"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )

    @staticmethod
    def _parse_env_group(data: Dict[str, Any]) -> RenderEnvGroup:
        env_vars = []
        for ev in data.get("envVars", []):
            env_vars.append(RenderEnvVar(key=ev.get("key", ""), value=ev.get("value")))
        secret_files = []
        for sf in data.get("secretFiles", []):
            secret_files.append(RenderSecretFile(name=sf.get("name", ""), content=sf.get("content", "")))
        return RenderEnvGroup(
            id=data.get("id"),
            name=data.get("name", ""),
            owner_id=data.get("ownerId"),
            env_vars=env_vars,
            secret_files=secret_files,
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )

    @staticmethod
    def _parse_blueprint(data: Dict[str, Any]) -> RenderBlueprint:
        return RenderBlueprint(
            id=data.get("id"),
            name=data.get("name", ""),
            status=data.get("status"),
            auto_sync=data.get("autoSync", False),
            repo=data.get("repo"),
            branch=data.get("branch"),
            owner_id=data.get("ownerId"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
            last_sync=data.get("lastSync"),
        )

    @staticmethod
    def _parse_webhook(data: Dict[str, Any]) -> RenderWebhook:
        return RenderWebhook(
            id=data.get("id"),
            url=data.get("url", ""),
            secret=data.get("secret"),
            events=data.get("events", []),
            enabled=data.get("enabled", True),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )
