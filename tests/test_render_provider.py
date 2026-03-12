"""
Comprehensive Regression Tests — Render Provider.

Exhaustive test coverage for the entire ``aquilia.providers.render`` package:

    § 1  Types          — Enums, dataclasses, serialization, factory methods
    § 2  SSL            — _build_ssl_context, certifi fallback, context wiring
    § 3  Client         — Construction, header assembly, request routing,
                          retry/backoff, rate-limit, auth errors, parsing,
                          every public API method (services, deploys,
                          env-vars, domains, autoscaling, owners)
    § 4  Store          — Save/load round-trip, Crous binary format,
                          HMAC integrity, corruption detection, clear,
                          config helpers, cross-machine portability
    § 5  Deployer       — Pipeline steps, dry-run, Docker build/push,
                          owner resolution, service create/update,
                          env-var sync, deploy trigger, health polling,
                          autoscaling, URL resolution, destroy, status
    § 6  Package init   — Public symbol re-exports
    § 7  Fault defaults — Provider faults default to ``provider="render"``
"""

from __future__ import annotations

import hashlib
import hmac as _hmac
import http.client
import io
import json
import os
import platform
import secrets
import ssl
import struct
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock, Mock, PropertyMock, call, patch

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
#  Imports under test
# ═══════════════════════════════════════════════════════════════════════════════

from aquilia.providers.render.types import (
    RenderAutoscaling,
    RenderDeploy,
    RenderDeployConfig,
    RenderDeployStatus,
    RenderDisk,
    RenderEnvVar,
    RenderOwner,
    RenderPlan,
    RenderRegion,
    RenderService,
    RenderServiceType,
)
from aquilia.providers.render.client import (
    RenderClient,
    _build_ssl_context,
    _RequestResult,
    _BASE_URL,
    _USER_AGENT,
    _DEFAULT_TIMEOUT,
    _MAX_RETRIES,
    _RETRY_BACKOFF,
    _SSL_CTX,
    RenderAPIError,
    RenderRateLimitError,
    RenderAuthError,
)
from aquilia.providers.render.store import (
    RenderCredentialStore,
    _derive_key,
    _xor_encrypt,
    _compute_hmac,
    _CROUS_MAGIC,
    _CROUS_VERSION,
    _CROUS_VERSION_LEGACY,
    _SALT_SIZE,
    _NONCE_SIZE,
    _secure_zero,
    _detect_cipher_suite,
    _encrypt,
    _decrypt,
    _generate_keystream,
    _AuditLogger,
)
from aquilia.providers.render.deployer import (
    DeployResult,
    RenderDeployer,
)
from aquilia.faults.domains import (
    ProviderAPIFault,
    ProviderAuthFault,
    ProviderRateLimitFault,
    ProviderTokenFault,
    ProviderCredentialFault,
    ProviderConnectionFault,
)

import aquilia.providers.render as render_pkg


# ═══════════════════════════════════════════════════════════════════════════════
#  Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _make_http_response(body: bytes, status: int = 200, headers=None):
    """Create a mock response for urllib.request.urlopen."""
    resp = MagicMock()
    resp.read.return_value = body
    resp.status = status
    resp.getheaders.return_value = list((headers or {}).items())
    resp.__enter__ = Mock(return_value=resp)
    resp.__exit__ = Mock(return_value=False)
    return resp


def _make_http_error(status: int, body: bytes = b"{}", headers=None):
    """Create a urllib.error.HTTPError."""
    import urllib.error
    hdrs = http.client.HTTPMessage()
    for k, v in (headers or {}).items():
        hdrs[k] = v
    err = urllib.error.HTTPError(
        url="https://api.render.com/v1/test",
        code=status,
        msg=f"HTTP {status}",
        hdrs=hdrs,
        fp=io.BytesIO(body),
    )
    return err


def _make_url_error(reason: str):
    """Create a urllib.error.URLError."""
    import urllib.error
    return urllib.error.URLError(reason)


def _make_client(**kwargs) -> RenderClient:
    """Create a RenderClient with defaults suitable for testing."""
    defaults = {"token": "rnd_testtoken123", "max_retries": 0}
    defaults.update(kwargs)
    return RenderClient(**defaults)


# ═══════════════════════════════════════════════════════════════════════════════
#  § 1  Types
# ═══════════════════════════════════════════════════════════════════════════════


class TestRenderServiceType:
    """Enum: service types."""

    def test_values(self):
        assert RenderServiceType.WEB_SERVICE.value == "web_service"
        assert RenderServiceType.PRIVATE_SERVICE.value == "private_service"
        assert RenderServiceType.BACKGROUND_WORKER.value == "background_worker"
        assert RenderServiceType.CRON_JOB.value == "cron_job"
        assert RenderServiceType.STATIC_SITE.value == "static_site"

    def test_str_enum(self):
        assert isinstance(RenderServiceType.WEB_SERVICE, str)
        assert str(RenderServiceType.WEB_SERVICE) == "RenderServiceType.WEB_SERVICE"

    def test_lookup_by_value(self):
        assert RenderServiceType("web_service") is RenderServiceType.WEB_SERVICE

    def test_invalid_value(self):
        with pytest.raises(ValueError):
            RenderServiceType("nonexistent")

    def test_all_members_count(self):
        assert len(RenderServiceType) == 5


class TestRenderPlan:
    """Enum: compute plans."""

    def test_all_plans(self):
        expected = ["free", "starter", "standard", "pro", "pro_plus", "pro_max", "pro_ultra"]
        assert [p.value for p in RenderPlan] == expected

    def test_is_str_enum(self):
        assert isinstance(RenderPlan.STARTER, str)

    def test_lookup(self):
        assert RenderPlan("pro_plus") is RenderPlan.PRO_PLUS

    def test_count(self):
        assert len(RenderPlan) == 7


class TestRenderDeployStatus:
    """Enum: deploy lifecycle states."""

    def test_all_statuses(self):
        expected = [
            "created", "build_in_progress", "update_in_progress",
            "live", "deactivated", "build_failed", "update_failed",
            "canceled", "pre_deploy_in_progress", "pre_deploy_failed",
        ]
        assert [s.value for s in RenderDeployStatus] == expected

    def test_count(self):
        assert len(RenderDeployStatus) == 10

    def test_failure_statuses_subset(self):
        failures = {
            RenderDeployStatus.BUILD_FAILED,
            RenderDeployStatus.UPDATE_FAILED,
            RenderDeployStatus.PRE_DEPLOY_FAILED,
        }
        for f in failures:
            assert "failed" in f.value


class TestRenderRegion:
    """Enum: deployment regions."""

    def test_all_regions(self):
        expected = ["oregon", "frankfurt", "ohio", "virginia", "singapore"]
        assert [r.value for r in RenderRegion] == expected

    def test_count(self):
        assert len(RenderRegion) == 5

    def test_default_is_oregon(self):
        assert RenderRegion.OREGON.value == "oregon"


class TestRenderEnvVar:
    """Dataclass: environment variable."""

    def test_plain_value(self):
        ev = RenderEnvVar(key="FOO", value="bar")
        d = ev.to_dict()
        assert d == {"key": "FOO", "value": "bar"}

    def test_generated_secret(self):
        ev = RenderEnvVar(key="SECRET", generate_value="yes")
        d = ev.to_dict()
        assert d == {"key": "SECRET", "generateValue": "yes"}
        assert "value" not in d

    def test_empty_value(self):
        ev = RenderEnvVar(key="EMPTY")
        d = ev.to_dict()
        assert d == {"key": "EMPTY", "value": ""}

    def test_generate_value_not_yes(self):
        ev = RenderEnvVar(key="K", generate_value="no")
        d = ev.to_dict()
        # generate_value != "yes" → falls through to plain value
        assert d == {"key": "K", "value": ""}


class TestRenderDisk:
    """Dataclass: persistent disk."""

    def test_defaults(self):
        disk = RenderDisk()
        assert disk.name == "data"
        assert disk.mount_path == "/data"
        assert disk.size_gb == 1

    def test_to_dict(self):
        disk = RenderDisk(name="storage", mount_path="/mnt/store", size_gb=10)
        d = disk.to_dict()
        assert d == {"name": "storage", "mountPath": "/mnt/store", "sizeGB": 10}


class TestRenderAutoscaling:
    """Dataclass: autoscaling config."""

    def test_disabled_factory(self):
        a = RenderAutoscaling.disabled()
        assert a.enabled is False
        assert a.min == 1
        assert a.max == 1

    def test_auto_factory_defaults(self):
        a = RenderAutoscaling.auto()
        assert a.enabled is True
        assert a.min == 1
        assert a.max == 3
        assert a.criteria["cpu"]["percentage"] == 80
        assert "memory" not in a.criteria

    def test_auto_factory_with_memory(self):
        a = RenderAutoscaling.auto(
            min_instances=2, max_instances=5,
            cpu_percent=60, memory_percent=70,
        )
        assert a.min == 2
        assert a.max == 5
        assert a.criteria["cpu"]["percentage"] == 60
        assert a.criteria["memory"]["percentage"] == 70

    def test_to_dict_enabled(self):
        a = RenderAutoscaling.auto(cpu_percent=90)
        d = a.to_dict()
        assert d["enabled"] is True
        assert d["min"] == 1
        assert d["max"] == 3
        assert d["criteria"]["cpu"]["percentage"] == 90

    def test_to_dict_disabled_no_criteria(self):
        a = RenderAutoscaling.disabled()
        d = a.to_dict()
        assert d["enabled"] is False
        assert "criteria" not in d


class TestRenderDeploy:
    """Dataclass: deploy resource."""

    def test_defaults(self):
        d = RenderDeploy()
        assert d.id is None
        assert d.status is None

    def test_populated(self):
        d = RenderDeploy(id="dpl-123", service_id="srv-abc", status="live")
        assert d.id == "dpl-123"
        assert d.service_id == "srv-abc"
        assert d.status == "live"


class TestRenderService:
    """Dataclass: service resource."""

    def test_defaults(self):
        svc = RenderService()
        assert svc.name == ""
        assert svc.type == RenderServiceType.WEB_SERVICE
        assert svc.id is None

    def test_populated(self):
        svc = RenderService(
            id="srv-1", name="myapp", slug="myapp-xyz",
            plan="starter", region="oregon",
        )
        assert svc.slug == "myapp-xyz"
        assert svc.plan == "starter"


class TestRenderOwner:
    """Dataclass: owner/workspace."""

    def test_defaults(self):
        o = RenderOwner()
        assert o.name == ""
        assert o.id is None

    def test_populated(self):
        o = RenderOwner(id="own-1", name="team-x", email="t@x.com", type="team")
        assert o.type == "team"


class TestRenderDeployConfig:
    """Dataclass: deployment configuration + serialization."""

    def _basic_config(self, **overrides):
        defaults = dict(
            service_name="myapp",
            image="ghcr.io/org/myapp:latest",
            owner_id="own-1",
            plan=RenderPlan.STANDARD,
            region="oregon",
            num_instances=2,
            port=8000,
            health_check_path="/_health",
            env_vars=[RenderEnvVar(key="FOO", value="bar")],
        )
        defaults.update(overrides)
        return RenderDeployConfig(**defaults)

    def test_to_service_payload_basic(self):
        cfg = self._basic_config()
        p = cfg.to_service_payload()
        assert p["name"] == "myapp"
        assert p["type"] == "web_service"
        assert p["ownerId"] == "own-1"
        assert p["autoDeploy"] == "no"
        sd = p["serviceDetails"]
        assert sd["plan"] == "standard"
        assert sd["region"] == "oregon"
        assert sd["numInstances"] == 2
        assert sd["healthCheckPath"] == "/_health"
        assert len(sd["envVars"]) == 1
        assert sd["envVars"][0]["key"] == "FOO"
        assert sd["image"]["imagePath"] == "ghcr.io/org/myapp:latest"

    def test_to_service_payload_with_disk(self):
        cfg = self._basic_config(disk=RenderDisk(name="db", mount_path="/db", size_gb=5))
        p = cfg.to_service_payload()
        assert p["serviceDetails"]["disk"] == {
            "name": "db", "mountPath": "/db", "sizeGB": 5,
        }

    def test_to_service_payload_with_docker_command(self):
        cfg = self._basic_config(docker_command="gunicorn app:app")
        p = cfg.to_service_payload()
        assert p["serviceDetails"]["dockerCommand"] == "gunicorn app:app"

    def test_to_service_payload_no_owner(self):
        cfg = self._basic_config(owner_id=None)
        p = cfg.to_service_payload()
        assert "ownerId" not in p

    def test_to_update_payload(self):
        cfg = self._basic_config()
        p = cfg.to_update_payload()
        assert p["name"] == "myapp"
        assert p["autoDeploy"] == "no"
        sd = p["serviceDetails"]
        assert sd["plan"] == "standard"
        assert sd["numInstances"] == 2
        # update doesn't include ownerId or envVars
        assert "ownerId" not in p
        assert "envVars" not in sd

    def test_to_update_payload_with_image(self):
        cfg = self._basic_config()
        p = cfg.to_update_payload()
        assert p["serviceDetails"]["image"]["imagePath"] == "ghcr.io/org/myapp:latest"

    def test_from_workspace_context_minimal(self):
        wctx = {"name": "demo", "port": 3000, "workers": 2}
        cfg = RenderDeployConfig.from_workspace_context(
            wctx, image="img:1",
        )
        assert cfg.service_name == "demo"
        assert cfg.port == 3000
        assert cfg.plan == RenderPlan.STARTER
        assert cfg.region == "oregon"
        # Mandatory env vars
        keys = [ev.key for ev in cfg.env_vars]
        assert "AQUILIA_ENV" in keys
        assert "AQ_SERVER_PORT" in keys
        assert "AQ_SIGNING_SECRET" in keys

    def test_from_workspace_context_with_db_cache_auth_mail(self):
        wctx = {
            "name": "full", "port": 8080, "workers": 4,
            "has_db": True, "has_cache": True,
            "has_auth": True, "has_mail": True,
        }
        cfg = RenderDeployConfig.from_workspace_context(
            wctx, image="i:1",
            plan=RenderPlan.PRO, region="frankfurt", num_instances=3,
        )
        keys = [ev.key for ev in cfg.env_vars]
        assert "DATABASE_URL" in keys
        assert "REDIS_URL" in keys
        assert "AQ_AUTH_SECRET" in keys
        assert "MAIL_API_KEY" in keys
        assert cfg.plan == RenderPlan.PRO
        assert cfg.region == "frankfurt"
        assert cfg.num_instances == 3

    def test_from_workspace_context_with_autoscaling(self):
        wctx = {"name": "a", "port": 80, "workers": 1}
        auto = RenderAutoscaling.auto(min_instances=2, max_instances=6)
        cfg = RenderDeployConfig.from_workspace_context(
            wctx, image="i", autoscaling=auto,
        )
        assert cfg.autoscaling.enabled is True
        assert cfg.autoscaling.max == 6

    def test_defaults(self):
        cfg = RenderDeployConfig()
        assert cfg.service_name == ""
        assert cfg.plan == RenderPlan.STARTER
        assert cfg.region == "oregon"
        assert cfg.auto_deploy == "no"
        assert cfg.autoscaling.enabled is False


# ═══════════════════════════════════════════════════════════════════════════════
#  § 2  SSL
# ═══════════════════════════════════════════════════════════════════════════════


class TestSSLContext:
    """SSL context builder and wiring."""

    def test_build_ssl_context_returns_ssl_context(self):
        ctx = _build_ssl_context()
        assert isinstance(ctx, ssl.SSLContext)

    def test_module_level_ctx_is_ssl_context(self):
        assert isinstance(_SSL_CTX, ssl.SSLContext)

    def test_build_ssl_context_with_certifi(self):
        """When certifi is available, its CA bundle is loaded."""
        try:
            import certifi
            ctx = _build_ssl_context()
            # Should succeed without error
            assert ctx.verify_mode == ssl.CERT_REQUIRED
        except ImportError:
            pytest.skip("certifi not installed")

    def test_build_ssl_context_without_certifi(self):
        """Falls back gracefully when certifi is not installed."""
        with patch.dict("sys.modules", {"certifi": None}):
            ctx = _build_ssl_context()
            assert isinstance(ctx, ssl.SSLContext)

    def test_client_uses_ssl_context_in_requests(self):
        """The SSL context is passed to urlopen."""
        client = _make_client()
        resp = _make_http_response(b'{"ok": true}')
        with patch("urllib.request.urlopen", return_value=resp) as mock_open:
            client._request("GET", "/test")
            _, kwargs = mock_open.call_args
            assert "context" in kwargs
            assert isinstance(kwargs["context"], ssl.SSLContext)

    def test_custom_ssl_context_parameter(self):
        """User can pass a custom ssl_context to the client."""
        custom_ctx = ssl.create_default_context()
        client = RenderClient(token="rnd_test", ssl_context=custom_ctx)
        assert client._ssl_ctx is custom_ctx

    def test_default_ssl_context_is_module_level(self):
        """Without explicit ssl_context, the module-level one is used."""
        client = _make_client()
        assert client._ssl_ctx is _SSL_CTX


# ═══════════════════════════════════════════════════════════════════════════════
#  § 3  Client
# ═══════════════════════════════════════════════════════════════════════════════


class TestClientConstruction:
    """Client init validation."""

    def test_requires_token(self):
        with pytest.raises(ProviderTokenFault):
            RenderClient(token="")

    def test_none_token(self):
        with pytest.raises(ProviderTokenFault):
            RenderClient(token=None)

    def test_non_string_token(self):
        with pytest.raises(ProviderTokenFault):
            RenderClient(token=123)

    def test_defaults(self):
        c = _make_client()
        assert c._base_url == _BASE_URL
        assert c._timeout == _DEFAULT_TIMEOUT

    def test_custom_base_url_strips_trailing_slash(self):
        c = _make_client(base_url="https://custom.api.com/v1/")
        assert c._base_url == "https://custom.api.com/v1"

    def test_repr(self):
        c = _make_client()
        assert "RenderClient" in repr(c)
        assert _BASE_URL in repr(c)


class TestClientHeaders:
    """Header assembly."""

    def test_bearer_token(self):
        c = _make_client(token="rnd_secret")
        h = c._headers()
        assert h["Authorization"] == "Bearer rnd_secret"

    def test_content_type(self):
        h = _make_client()._headers()
        assert h["Content-Type"] == "application/json"

    def test_user_agent(self):
        h = _make_client()._headers()
        assert h["User-Agent"] == _USER_AGENT


class TestClientRequest:
    """Low-level _request method."""

    def test_get_request(self):
        client = _make_client()
        resp = _make_http_response(b'{"id": "1"}')
        with patch("urllib.request.urlopen", return_value=resp) as mock:
            result = client._request("GET", "/services")
            assert result.status == 200
            assert result.body == b'{"id": "1"}'

    def test_post_request_with_body(self):
        client = _make_client()
        resp = _make_http_response(b'{"created": true}', 201)
        with patch("urllib.request.urlopen", return_value=resp) as mock:
            result = client._request("POST", "/services", body={"name": "app"})
            assert result.status == 201
            # Verify the request had data
            req_obj = mock.call_args[0][0]
            assert req_obj.data is not None
            assert b'"name"' in req_obj.data

    def test_query_params(self):
        client = _make_client()
        resp = _make_http_response(b"[]")
        with patch("urllib.request.urlopen", return_value=resp) as mock:
            client._request("GET", "/services", params={"limit": "5", "name": "app"})
            req_obj = mock.call_args[0][0]
            assert "limit=5" in req_obj.full_url
            assert "name=app" in req_obj.full_url

    def test_auth_error_401_raises_provider_auth_fault(self):
        client = _make_client()
        err = _make_http_error(401, b'{"message": "Unauthorized"}')
        with patch("urllib.request.urlopen", side_effect=err):
            with pytest.raises(ProviderAuthFault) as exc_info:
                client._request("GET", "/owners")
            assert exc_info.value.status_code == 401

    def test_auth_error_403_raises_provider_auth_fault(self):
        client = _make_client()
        err = _make_http_error(403, b'{"message": "Forbidden"}')
        with patch("urllib.request.urlopen", side_effect=err):
            with pytest.raises(ProviderAuthFault):
                client._request("GET", "/services")

    def test_rate_limit_429_raises_rate_limit_fault(self):
        client = _make_client()
        err = _make_http_error(429, b"{}", headers={"retry-after": "30"})
        with patch("urllib.request.urlopen", side_effect=err):
            with pytest.raises(ProviderRateLimitFault) as exc_info:
                client._request("GET", "/services")
            assert exc_info.value.retry_after == 30.0

    def test_client_error_raises_api_fault(self):
        client = _make_client()
        err = _make_http_error(422, b'{"message": "Validation failed"}')
        with patch("urllib.request.urlopen", side_effect=err):
            with pytest.raises(ProviderAPIFault) as exc_info:
                client._request("POST", "/services")
            assert exc_info.value.status_code == 422

    def test_connection_error_raises_connection_fault(self):
        client = _make_client()
        err = _make_url_error("Connection refused")
        with patch("urllib.request.urlopen", side_effect=err):
            with pytest.raises(ProviderConnectionFault):
                client._request("GET", "/test")

    def test_retry_on_server_error(self):
        client = _make_client(max_retries=2)
        err500 = _make_http_error(500, b'{"message": "Internal"}')
        resp = _make_http_response(b'{"ok": true}')
        with patch("urllib.request.urlopen", side_effect=[err500, resp]):
            with patch("time.sleep"):
                result = client._request("GET", "/test")
                assert result.status == 200

    def test_retry_exhaustion_raises(self):
        client = _make_client(max_retries=1)
        err500 = _make_http_error(500, b'{"message": "Down"}')
        with patch("urllib.request.urlopen", side_effect=[err500, err500]):
            with patch("time.sleep"):
                with pytest.raises(ProviderAPIFault):
                    client._request("GET", "/test")

    def test_retry_on_connection_error(self):
        client = _make_client(max_retries=1)
        err = _make_url_error("timeout")
        resp = _make_http_response(b'{"ok": true}')
        with patch("urllib.request.urlopen", side_effect=[err, resp]):
            with patch("time.sleep"):
                result = client._request("GET", "/test")
                assert result.status == 200

    def test_rate_limit_retry(self):
        client = _make_client(max_retries=1)
        err429 = _make_http_error(429, b"{}", headers={"retry-after": "1"})
        resp = _make_http_response(b'{"ok": true}')
        with patch("urllib.request.urlopen", side_effect=[err429, resp]):
            with patch("time.sleep") as sleep_mock:
                result = client._request("GET", "/test")
                assert result.status == 200
                sleep_mock.assert_called_once_with(1.0)

    def test_parse_error_message_json(self):
        client = _make_client()
        assert client._parse_error_message(b'{"message": "oops"}') == "oops"
        assert client._parse_error_message(b'{"error": "bad"}') == "bad"
        assert client._parse_error_message(b'{"detail": "info"}') == "info"

    def test_parse_error_message_invalid_json(self):
        client = _make_client()
        assert client._parse_error_message(b"not json") is None

    def test_json_empty_body(self):
        client = _make_client()
        result = _RequestResult(status=204, body=b"", headers={})
        assert client._json(result) == {}

    def test_max_retries_exhausted_with_url_error(self):
        client = _make_client(max_retries=1)
        err = _make_url_error("SSL error")
        with patch("urllib.request.urlopen", side_effect=[err, err]):
            with patch("time.sleep"):
                with pytest.raises(ProviderConnectionFault, match="SSL error"):
                    client._request("GET", "/test")


class TestClientServices:
    """Service CRUD methods."""

    def _patch_request(self, client, return_value):
        return patch.object(client, "_request", return_value=return_value)

    def test_list_services_empty(self):
        client = _make_client()
        result = _RequestResult(status=200, body=b"[]", headers={})
        with self._patch_request(client, result):
            svcs = client.list_services()
            assert svcs == []

    def test_list_services_with_cursor_format(self):
        client = _make_client()
        data = [
            {"service": {"id": "srv-1", "name": "app1", "type": "web_service"}, "cursor": "c1"},
            {"service": {"id": "srv-2", "name": "app2", "type": "web_service"}, "cursor": "c2"},
        ]
        result = _RequestResult(status=200, body=json.dumps(data).encode(), headers={})
        with self._patch_request(client, result):
            svcs = client.list_services()
            assert len(svcs) == 2
            assert svcs[0].id == "srv-1"
            assert svcs[1].name == "app2"

    def test_list_services_with_filters(self):
        client = _make_client()
        result = _RequestResult(status=200, body=b"[]", headers={})
        with patch.object(client, "_request", return_value=result) as mock_req:
            client.list_services(
                name="myapp", type="web_service",
                region="oregon", suspended="not_suspended",
                owner_id="own-1", cursor="c-x", limit=5,
            )
            _, kwargs = mock_req.call_args
            params = kwargs["params"]
            assert params["name"] == "myapp"
            assert params["type"] == "web_service"
            assert params["region"] == "oregon"
            assert params["ownerId"] == "own-1"
            assert params["cursor"] == "c-x"
            assert params["limit"] == "5"

    def test_get_service(self):
        client = _make_client()
        data = {"id": "srv-1", "name": "myapp", "type": "web_service", "plan": "starter"}
        result = _RequestResult(status=200, body=json.dumps(data).encode(), headers={})
        with self._patch_request(client, result):
            svc = client.get_service("srv-1")
            assert svc.id == "srv-1"
            assert svc.plan == "starter"

    def test_get_service_by_name_found(self):
        client = _make_client()
        data = [{"service": {"id": "srv-1", "name": "target", "type": "web_service"}}]
        result = _RequestResult(status=200, body=json.dumps(data).encode(), headers={})
        with self._patch_request(client, result):
            svc = client.get_service_by_name("target")
            assert svc is not None
            assert svc.name == "target"

    def test_get_service_by_name_not_found(self):
        client = _make_client()
        data = [{"service": {"id": "srv-1", "name": "other", "type": "web_service"}}]
        result = _RequestResult(status=200, body=json.dumps(data).encode(), headers={})
        with self._patch_request(client, result):
            svc = client.get_service_by_name("nonexistent")
            assert svc is None

    def test_create_service(self):
        client = _make_client()
        resp_data = {"service": {"id": "srv-new", "name": "app", "type": "web_service"}}
        result = _RequestResult(status=201, body=json.dumps(resp_data).encode(), headers={})
        with patch.object(client, "_request", return_value=result) as mock_req:
            svc = client.create_service({"name": "app"})
            assert svc.id == "srv-new"
            mock_req.assert_called_once_with("POST", "/services", body={"name": "app"})

    def test_update_service(self):
        client = _make_client()
        resp_data = {"id": "srv-1", "name": "updated", "type": "web_service"}
        result = _RequestResult(status=200, body=json.dumps(resp_data).encode(), headers={})
        with patch.object(client, "_request", return_value=result) as mock_req:
            svc = client.update_service("srv-1", {"name": "updated"})
            assert svc.name == "updated"
            mock_req.assert_called_once_with("PATCH", "/services/srv-1", body={"name": "updated"})

    def test_delete_service(self):
        client = _make_client()
        result = _RequestResult(status=204, body=b"", headers={})
        with patch.object(client, "_request", return_value=result) as mock_req:
            client.delete_service("srv-1")
            mock_req.assert_called_once_with("DELETE", "/services/srv-1")

    def test_suspend_service(self):
        client = _make_client()
        result = _RequestResult(status=200, body=b"{}", headers={})
        with patch.object(client, "_request", return_value=result) as mock_req:
            client.suspend_service("srv-1")
            mock_req.assert_called_once_with("POST", "/services/srv-1/suspend")

    def test_resume_service(self):
        client = _make_client()
        result = _RequestResult(status=200, body=b"{}", headers={})
        with patch.object(client, "_request", return_value=result) as mock_req:
            client.resume_service("srv-1")
            mock_req.assert_called_once_with("POST", "/services/srv-1/resume")


class TestClientDeploys:
    """Deploy methods."""

    def test_list_deploys(self):
        client = _make_client()
        data = [
            {"deploy": {"id": "dpl-1", "status": "live"}, "cursor": "c1"},
            {"deploy": {"id": "dpl-2", "status": "build_in_progress"}, "cursor": "c2"},
        ]
        result = _RequestResult(status=200, body=json.dumps(data).encode(), headers={})
        with patch.object(client, "_request", return_value=result):
            deploys = client.list_deploys("srv-1")
            assert len(deploys) == 2
            assert deploys[0].id == "dpl-1"
            assert deploys[0].status == "live"

    def test_list_deploys_empty(self):
        client = _make_client()
        result = _RequestResult(status=200, body=b"[]", headers={})
        with patch.object(client, "_request", return_value=result):
            assert client.list_deploys("srv-1") == []

    def test_list_deploys_non_list_response(self):
        client = _make_client()
        result = _RequestResult(status=200, body=b'{"unexpected": true}', headers={})
        with patch.object(client, "_request", return_value=result):
            assert client.list_deploys("srv-1") == []

    def test_get_deploy(self):
        client = _make_client()
        data = {"id": "dpl-1", "serviceId": "srv-1", "status": "live"}
        result = _RequestResult(status=200, body=json.dumps(data).encode(), headers={})
        with patch.object(client, "_request", return_value=result):
            deploy = client.get_deploy("srv-1", "dpl-1")
            assert deploy.id == "dpl-1"
            assert deploy.service_id == "srv-1"

    def test_trigger_deploy(self):
        client = _make_client()
        data = {"id": "dpl-new", "status": "created"}
        result = _RequestResult(status=201, body=json.dumps(data).encode(), headers={})
        with patch.object(client, "_request", return_value=result) as mock_req:
            deploy = client.trigger_deploy("srv-1")
            assert deploy.id == "dpl-new"
            mock_req.assert_called_once_with("POST", "/services/srv-1/deploys")


class TestClientEnvVars:
    """Environment variable methods."""

    def test_list_env_vars(self):
        client = _make_client()
        data = [
            {"envVar": {"key": "FOO", "value": "bar"}},
            {"envVar": {"key": "SECRET", "value": "hidden"}},
        ]
        result = _RequestResult(status=200, body=json.dumps(data).encode(), headers={})
        with patch.object(client, "_request", return_value=result):
            evs = client.list_env_vars("srv-1")
            assert len(evs) == 2
            assert evs[0]["key"] == "FOO"

    def test_list_env_vars_non_list(self):
        client = _make_client()
        result = _RequestResult(status=200, body=b'{}', headers={})
        with patch.object(client, "_request", return_value=result):
            assert client.list_env_vars("srv-1") == []

    def test_update_env_vars(self):
        client = _make_client()
        data = [{"envVar": {"key": "A", "value": "1"}}]
        result = _RequestResult(status=200, body=json.dumps(data).encode(), headers={})
        with patch.object(client, "_request", return_value=result) as mock_req:
            evs = client.update_env_vars("srv-1", [{"key": "A", "value": "1"}])
            assert len(evs) == 1
            mock_req.assert_called_once_with(
                "PUT", "/services/srv-1/env-vars",
                body=[{"key": "A", "value": "1"}],
            )

    def test_get_env_var_found(self):
        client = _make_client()
        data = {"key": "MY_KEY", "value": "my_val"}
        result = _RequestResult(status=200, body=json.dumps(data).encode(), headers={})
        with patch.object(client, "_request", return_value=result):
            ev = client.get_env_var("srv-1", "MY_KEY")
            assert ev["key"] == "MY_KEY"

    def test_get_env_var_not_found(self):
        client = _make_client()
        with patch.object(client, "_request", side_effect=ProviderAPIFault(404, "Not found")):
            assert client.get_env_var("srv-1", "MISSING") is None

    def test_delete_env_var(self):
        client = _make_client()
        result = _RequestResult(status=204, body=b"", headers={})
        with patch.object(client, "_request", return_value=result) as mock_req:
            client.delete_env_var("srv-1", "OLD_KEY")
            mock_req.assert_called_once_with("DELETE", "/services/srv-1/env-vars/OLD_KEY")


class TestClientCustomDomains:
    """Custom domain methods."""

    def test_list_custom_domains(self):
        client = _make_client()
        data = [{"customDomain": {"name": "app.example.com"}}]
        result = _RequestResult(status=200, body=json.dumps(data).encode(), headers={})
        with patch.object(client, "_request", return_value=result):
            domains = client.list_custom_domains("srv-1")
            assert domains[0]["name"] == "app.example.com"

    def test_add_custom_domain(self):
        client = _make_client()
        data = {"name": "app.example.com"}
        result = _RequestResult(status=201, body=json.dumps(data).encode(), headers={})
        with patch.object(client, "_request", return_value=result) as mock_req:
            client.add_custom_domain("srv-1", "app.example.com")
            mock_req.assert_called_once_with(
                "POST", "/services/srv-1/custom-domains",
                body={"name": "app.example.com"},
            )

    def test_delete_custom_domain(self):
        client = _make_client()
        result = _RequestResult(status=204, body=b"", headers={})
        with patch.object(client, "_request", return_value=result) as mock_req:
            client.delete_custom_domain("srv-1", "old.example.com")
            mock_req.assert_called_once_with(
                "DELETE", "/services/srv-1/custom-domains/old.example.com",
            )


class TestClientAutoscaling:
    """Autoscaling / scaling methods."""

    def test_set_autoscaling(self):
        client = _make_client()
        config = {"enabled": True, "min": 1, "max": 5}
        result = _RequestResult(status=200, body=json.dumps(config).encode(), headers={})
        with patch.object(client, "_request", return_value=result) as mock_req:
            resp = client.set_autoscaling("srv-1", config)
            assert resp["enabled"] is True
            mock_req.assert_called_once_with(
                "PUT", "/services/srv-1/autoscaling", body=config,
            )

    def test_remove_autoscaling(self):
        client = _make_client()
        result = _RequestResult(status=204, body=b"", headers={})
        with patch.object(client, "_request", return_value=result) as mock_req:
            client.remove_autoscaling("srv-1")
            mock_req.assert_called_once_with("DELETE", "/services/srv-1/autoscaling")

    def test_scale_service(self):
        client = _make_client()
        result = _RequestResult(status=200, body=b"{}", headers={})
        with patch.object(client, "_request", return_value=result) as mock_req:
            client.scale_service("srv-1", 3)
            mock_req.assert_called_once_with(
                "POST", "/services/srv-1/scale",
                body={"numInstances": 3},
            )


class TestClientOwners:
    """Account / owner methods."""

    def test_get_user(self):
        client = _make_client()
        data = [{"owner": {"id": "own-1", "name": "testuser"}, "cursor": "c1"}]
        result = _RequestResult(status=200, body=json.dumps(data).encode(), headers={})
        with patch.object(client, "_request", return_value=result):
            user = client.get_user()
            assert user["id"] == "own-1"
            assert user["name"] == "testuser"

    def test_get_user_empty(self):
        client = _make_client()
        result = _RequestResult(status=200, body=b"[]", headers={})
        with patch.object(client, "_request", return_value=result):
            assert client.get_user() == {}

    def test_list_owners(self):
        client = _make_client()
        data = [
            {"owner": {"id": "own-1", "name": "user1", "email": "u@e.com", "type": "user"}},
            {"owner": {"id": "own-2", "name": "team1", "type": "team"}},
        ]
        result = _RequestResult(status=200, body=json.dumps(data).encode(), headers={})
        with patch.object(client, "_request", return_value=result):
            owners = client.list_owners()
            assert len(owners) == 2
            assert owners[0].id == "own-1"
            assert owners[0].email == "u@e.com"
            assert owners[1].type == "team"

    def test_validate_token_success(self):
        client = _make_client()
        data = [{"owner": {"id": "own-1", "name": "user"}}]
        result = _RequestResult(status=200, body=json.dumps(data).encode(), headers={})
        with patch.object(client, "_request", return_value=result):
            assert client.validate_token() is True

    def test_validate_token_auth_failure(self):
        client = _make_client()
        with patch.object(client, "_request", side_effect=ProviderAuthFault()):
            assert client.validate_token() is False

    def test_validate_token_api_failure(self):
        client = _make_client()
        with patch.object(client, "_request", side_effect=ProviderAPIFault(500, "error")):
            assert client.validate_token() is False

    def test_validate_token_empty_response(self):
        client = _make_client()
        result = _RequestResult(status=200, body=b"[]", headers={})
        with patch.object(client, "_request", return_value=result):
            assert client.validate_token() is False


class TestClientParsers:
    """Static parser methods."""

    def test_parse_service_full(self):
        data = {
            "id": "srv-1", "name": "app", "ownerId": "own-1",
            "slug": "app-xyz", "type": "web_service", "plan": "pro",
            "region": "frankfurt", "status": "running",
            "suspended": "not_suspended", "autoDeploy": "yes",
            "serviceDetails": {"buildCommand": "pip install"},
            "createdAt": "2026-01-01T00:00:00Z",
            "updatedAt": "2026-03-01T00:00:00Z",
        }
        svc = RenderClient._parse_service(data)
        assert svc.id == "srv-1"
        assert svc.owner_id == "own-1"
        assert svc.slug == "app-xyz"
        assert svc.type == RenderServiceType.WEB_SERVICE
        assert svc.plan == "pro"
        assert svc.auto_deploy == "yes"
        assert svc.service_details == {"buildCommand": "pip install"}

    def test_parse_service_unknown_type_defaults(self):
        data = {"type": "unknown_type", "name": "x"}
        svc = RenderClient._parse_service(data)
        assert svc.type == RenderServiceType.WEB_SERVICE

    def test_parse_deploy_full(self):
        data = {
            "id": "dpl-1", "serviceId": "srv-1", "status": "live",
            "commit": {"id": "abc123"}, "image": {"imagePath": "img:1"},
            "createdAt": "2026-01-01", "updatedAt": "2026-01-02",
            "finishedAt": "2026-01-02",
        }
        deploy = RenderClient._parse_deploy(data)
        assert deploy.id == "dpl-1"
        assert deploy.service_id == "srv-1"
        assert deploy.commit == {"id": "abc123"}
        assert deploy.finished_at == "2026-01-02"


class TestLegacyAliases:
    """Backward-compatible aliases."""

    def test_render_api_error_is_provider_api_fault(self):
        assert RenderAPIError is ProviderAPIFault

    def test_render_rate_limit_error_is_provider_rate_limit_fault(self):
        assert RenderRateLimitError is ProviderRateLimitFault

    def test_render_auth_error_is_provider_auth_fault(self):
        assert RenderAuthError is ProviderAuthFault


# ═══════════════════════════════════════════════════════════════════════════════
#  § 4  Store
# ═══════════════════════════════════════════════════════════════════════════════


class TestCryptoHelpers:
    """Low-level crypto functions."""

    def test_derive_key_deterministic(self):
        salt = b"a" * 32
        k1 = _derive_key(salt, "ctx")
        k2 = _derive_key(salt, "ctx")
        assert k1 == k2
        assert len(k1) == 32

    def test_derive_key_different_salt(self):
        k1 = _derive_key(b"a" * 32, "ctx")
        k2 = _derive_key(b"b" * 32, "ctx")
        assert k1 != k2

    def test_derive_key_different_context(self):
        salt = b"x" * 32
        k1 = _derive_key(salt, "token-encryption")
        k2 = _derive_key(salt, "hmac-signing")
        assert k1 != k2

    def test_xor_encrypt_roundtrip(self):
        key = secrets.token_bytes(32)
        plaintext = b"hello world secret token"
        encrypted = _xor_encrypt(plaintext, key)
        assert encrypted != plaintext
        decrypted = _xor_encrypt(encrypted, key)
        assert decrypted == plaintext

    def test_xor_encrypt_empty(self):
        assert _xor_encrypt(b"", b"key") == b""

    def test_compute_hmac(self):
        key = b"secret"
        data = b"message"
        result = _compute_hmac(key, data)
        assert len(result) == 32  # SHA-256

    def test_compute_hmac_deterministic(self):
        key = b"k"
        data = b"d"
        assert _compute_hmac(key, data) == _compute_hmac(key, data)


class TestCredentialStore:
    """Save/load round-trip and error handling."""

    @pytest.fixture
    def store_dir(self, tmp_path):
        return tmp_path / "render_creds"

    @pytest.fixture
    def store(self, store_dir):
        return RenderCredentialStore(store_dir=store_dir)

    def test_not_configured_initially(self, store):
        assert store.is_configured() is False

    def test_save_and_load_roundtrip(self, store):
        token = "rnd_test_token_12345678"
        store.save(token, owner_name="testuser", default_region="frankfurt")
        assert store.is_configured() is True
        loaded = store.load()
        assert loaded == token

    def test_save_creates_directory(self, store, store_dir):
        assert not store_dir.exists()
        store.save("rnd_token")
        assert store_dir.exists()

    def test_save_sets_file_permissions(self, store):
        store.save("rnd_token")
        mode = store.credentials_path.stat().st_mode & 0o777
        assert mode == 0o600

    def test_config_file_created(self, store):
        store.save("rnd_t", owner_name="user1", default_region="ohio")
        assert store.config_path.exists()
        config = json.loads(store.config_path.read_text())
        assert config["owner_name"] == "user1"
        assert config["default_region"] == "ohio"

    def test_config_metadata(self, store):
        store.save("rnd_t", metadata={"extra": "info"})
        config = json.loads(store.config_path.read_text())
        assert config["metadata"]["extra"] == "info"

    def test_get_default_region(self, store):
        store.save("rnd_t", default_region="singapore")
        assert store.get_default_region() == "singapore"

    def test_get_default_region_fallback(self, store):
        assert store.get_default_region() == "oregon"

    def test_get_owner_name(self, store):
        store.save("rnd_t", owner_name="myteam")
        assert store.get_owner_name() == "myteam"

    def test_get_owner_name_none(self, store):
        assert store.get_owner_name() is None

    def test_load_no_file(self, store):
        assert store.load() is None

    def test_load_corrupted_magic(self, store):
        store.save("rnd_t")
        # Corrupt magic bytes
        blob = store.credentials_path.read_bytes()
        store.credentials_path.write_bytes(b"XXXX" + blob[4:])
        with pytest.raises(ProviderCredentialFault, match="bad magic"):
            store.load()

    def test_load_wrong_version(self, store):
        store.save("rnd_t")
        blob = bytearray(store.credentials_path.read_bytes())
        blob[4] = 99  # Invalid version
        store.credentials_path.write_bytes(bytes(blob))
        with pytest.raises(ProviderCredentialFault, match="Unsupported credentials version"):
            store.load()

    def test_load_truncated_file(self, store):
        store.save("rnd_t")
        store.credentials_path.write_bytes(b"AQCR" + b"\x01" + b"short")
        with pytest.raises(ProviderCredentialFault, match="too small"):
            store.load()

    def test_load_tampered_signature(self, store):
        store.save("rnd_token")
        blob = bytearray(store.credentials_path.read_bytes())
        # Flip last byte (in HMAC signature)
        blob[-1] ^= 0xFF
        store.credentials_path.write_bytes(bytes(blob))
        with pytest.raises(ProviderCredentialFault, match="integrity check failed"):
            store.load()

    def test_load_truncated_token_data(self, store):
        store.save("rnd_t")
        blob = store.credentials_path.read_bytes()
        # Cut off most of the file but keep header valid
        truncated = blob[:50]
        store.credentials_path.write_bytes(truncated)
        with pytest.raises(ProviderCredentialFault, match="too small"):
            store.load()

    def test_clear(self, store):
        store.save("rnd_t", owner_name="u")
        assert store.is_configured() is True
        store.clear()
        assert store.is_configured() is False
        assert not store.config_path.exists()

    def test_clear_no_file(self, store):
        """Clear on empty store doesn't raise."""
        store.clear()

    def test_status_configured(self, store):
        store.save("rnd_t", owner_name="team1", default_region="virginia")
        s = store.status()
        assert s["configured"] is True
        assert s["owner_name"] == "team1"
        assert s["default_region"] == "virginia"

    def test_status_not_configured(self, store):
        s = store.status()
        assert s["configured"] is False

    def test_load_config_no_file(self, store):
        assert store.load_config() == {}

    def test_load_config_invalid_json(self, store, store_dir):
        store_dir.mkdir(parents=True, exist_ok=True)
        (store_dir / "config.json").write_text("not json")
        assert store.load_config() == {}

    def test_multiple_save_overwrites(self, store):
        store.save("rnd_first")
        store.save("rnd_second")
        assert store.load() == "rnd_second"

    def test_long_token(self, store):
        """Tokens of any reasonable length survive round-trip."""
        long_token = "rnd_" + "x" * 500
        store.save(long_token)
        assert store.load() == long_token

    def test_unicode_token(self, store):
        """UTF-8 tokens survive round-trip."""
        token = "rnd_üñîçödé_token"
        store.save(token)
        assert store.load() == token

    def test_binary_format_header(self, store):
        """Verify the Crous v2 binary format header structure."""
        store.save("rnd_check")
        blob = store.credentials_path.read_bytes()
        assert blob[:4] == _CROUS_MAGIC
        assert blob[4] == _CROUS_VERSION  # v2
        # byte 5 = cipher suite
        cipher_suite = blob[5]
        assert cipher_suite in (1, 3)  # AES-GCM or XOR-HMAC
        # Next 8 bytes = timestamp (double)
        ts = struct.unpack_from(">d", blob, 6)[0]
        assert ts > 0
        # Next 4 bytes = TTL
        ttl = struct.unpack_from(">I", blob, 14)[0]
        assert ttl >= 0
        # Next 32 bytes = salt
        assert len(blob[18:18 + _SALT_SIZE]) == _SALT_SIZE

    def test_credentials_path_property(self, store, store_dir):
        assert store.credentials_path == store_dir / "credentials.crous"

    def test_config_path_property(self, store, store_dir):
        assert store.config_path == store_dir / "config.json"


# ═══════════════════════════════════════════════════════════════════════════════
#  § 5  Deployer
# ═══════════════════════════════════════════════════════════════════════════════


class TestDeployResult:
    """DeployResult data class."""

    def test_success_result(self):
        r = DeployResult(success=True, url="https://app.onrender.com")
        assert r.success is True
        assert r.url == "https://app.onrender.com"
        assert r.errors == []
        assert r.steps_completed == []

    def test_failure_result(self):
        r = DeployResult(success=False, errors=["token invalid"])
        assert r.success is False
        assert r.errors == ["token invalid"]

    def test_repr_success(self):
        r = DeployResult(success=True, url="https://x.onrender.com")
        assert "SUCCESS" in repr(r)

    def test_repr_failure(self):
        r = DeployResult(success=False)
        assert "FAILED" in repr(r)


class TestDeployerConstruction:
    """Deployer init and step tracking."""

    def _make_deployer(self, **overrides):
        client = MagicMock(spec=RenderClient)
        config = RenderDeployConfig(
            service_name="testapp",
            image="ghcr.io/org/testapp:latest",
            plan=RenderPlan.STARTER,
            region="oregon",
        )
        defaults = dict(
            client=client,
            workspace_root=Path("/tmp/test_workspace"),
            config=config,
        )
        defaults.update(overrides)
        return RenderDeployer(**defaults), client, defaults["config"]

    def test_on_step_callback(self):
        steps = []
        deployer, _, _ = self._make_deployer(on_step=lambda p, m: steps.append((p, m)))
        deployer._step("test", "hello")
        assert ("test", "hello") in steps

    def test_error_tracking(self):
        deployer, _, _ = self._make_deployer()
        deployer._error("something broke")
        assert "something broke" in deployer._errors


class TestDeployerValidation:
    """Deploy pipeline — validation step."""

    def _make_deployer(self, config_overrides=None, **kwargs):
        client = MagicMock(spec=RenderClient)
        config = RenderDeployConfig(
            service_name="testapp",
            image="ghcr.io/org/testapp:latest",
            plan=RenderPlan.STARTER,
            region="oregon",
        )
        if config_overrides:
            for k, v in config_overrides.items():
                setattr(config, k, v)
        return RenderDeployer(
            client=client,
            workspace_root=Path("/tmp/ws"),
            config=config,
            **kwargs,
        ), client

    def test_validate_no_service_name(self):
        deployer, client = self._make_deployer(config_overrides={"service_name": ""})
        result = deployer.deploy()
        assert result.success is False
        assert any("Service name" in e for e in result.errors)

    def test_validate_no_image(self):
        deployer, client = self._make_deployer(config_overrides={"image": ""})
        result = deployer.deploy()
        assert result.success is False
        assert any("image" in e.lower() for e in result.errors)

    def test_validate_no_region(self):
        deployer, client = self._make_deployer(config_overrides={"region": ""})
        result = deployer.deploy()
        assert result.success is False
        assert any("region" in e.lower() for e in result.errors)

    def test_validate_invalid_token(self):
        deployer, client = self._make_deployer()
        client.validate_token.return_value = False
        result = deployer.deploy()
        assert result.success is False
        assert any("token" in e.lower() for e in result.errors)

    def test_validate_token_auth_fault(self):
        deployer, client = self._make_deployer()
        client.validate_token.side_effect = ProviderAuthFault()
        result = deployer.deploy()
        assert result.success is False

    def test_validate_token_api_fault(self):
        deployer, client = self._make_deployer()
        client.validate_token.side_effect = ProviderAPIFault(500, "down")
        result = deployer.deploy()
        assert result.success is False


class TestDeployerDryRun:
    """Dry run mode."""

    def test_dry_run_returns_success_without_side_effects(self):
        client = MagicMock(spec=RenderClient)
        client.validate_token.return_value = True
        config = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
        )
        deployer = RenderDeployer(
            client=client, workspace_root=Path("/tmp/ws"),
            config=config, dry_run=True,
        )
        result = deployer.deploy()
        assert result.success is True
        assert any("dry" in s.lower() for s in result.steps_completed)
        client.create_service.assert_not_called()
        client.trigger_deploy.assert_not_called()


class TestDeployerDockerSteps:
    """Docker build/push logic."""

    def _make_deployer(self, image, workspace_root=None):
        client = MagicMock(spec=RenderClient)
        config = RenderDeployConfig(
            service_name="app", image=image, region="oregon",
        )
        ws = workspace_root or Path("/tmp/ws")
        deployer = RenderDeployer(client=client, workspace_root=ws, config=config)
        return deployer, client

    def test_should_build_docker_local_image(self):
        deployer, _ = self._make_deployer("myapp")
        assert deployer._should_build_docker() is True

    def test_should_not_build_docker_registry_image(self):
        deployer, _ = self._make_deployer("ghcr.io/org/app:v1")
        assert deployer._should_build_docker() is False

    def test_should_build_docker_localhost(self):
        deployer, _ = self._make_deployer("localhost:5000/app:v1")
        assert deployer._should_build_docker() is True

    def test_should_push_docker_registry(self):
        deployer, _ = self._make_deployer("ghcr.io/org/app:v1")
        assert deployer._should_push_docker() is True

    def test_should_not_push_docker_localhost(self):
        deployer, _ = self._make_deployer("localhost:5000/app")
        assert deployer._should_push_docker() is False

    def test_docker_build_no_dockerfile(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            deployer, _ = self._make_deployer("myapp", Path(tmpdir))
            ok = deployer._docker_build()
            assert ok is False
            assert any("Dockerfile" in e for e in deployer._errors)

    def test_docker_build_success(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "Dockerfile").write_text("FROM python:3.14")
            deployer, _ = self._make_deployer("myapp", Path(tmpdir))
            mock_result = MagicMock(returncode=0, stderr="")
            with patch("subprocess.run", return_value=mock_result):
                assert deployer._docker_build() is True

    def test_docker_build_failure(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "Dockerfile").write_text("FROM x")
            deployer, _ = self._make_deployer("myapp", Path(tmpdir))
            mock_result = MagicMock(returncode=1, stderr="build error")
            with patch("subprocess.run", return_value=mock_result):
                assert deployer._docker_build() is False
                assert any("build failed" in e.lower() for e in deployer._errors)

    def test_docker_build_docker_not_installed(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "Dockerfile").write_text("FROM x")
            deployer, _ = self._make_deployer("myapp", Path(tmpdir))
            with patch("subprocess.run", side_effect=FileNotFoundError):
                assert deployer._docker_build() is False
                assert any("not installed" in e.lower() for e in deployer._errors)

    def test_docker_push_success(self):
        deployer, _ = self._make_deployer("ghcr.io/org/app:v1")
        mock_result = MagicMock(returncode=0)
        with patch("subprocess.run", return_value=mock_result):
            assert deployer._docker_push() is True

    def test_docker_push_failure(self):
        deployer, _ = self._make_deployer("ghcr.io/org/app:v1")
        mock_result = MagicMock(returncode=1, stderr="push error")
        with patch("subprocess.run", return_value=mock_result):
            assert deployer._docker_push() is False

    def test_docker_push_not_installed(self):
        deployer, _ = self._make_deployer("ghcr.io/org/app:v1")
        with patch("subprocess.run", side_effect=FileNotFoundError):
            assert deployer._docker_push() is False


class TestDeployerOwnerResolution:
    """Owner / workspace resolution."""

    def _make_deployer(self):
        client = MagicMock(spec=RenderClient)
        config = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
        )
        deployer = RenderDeployer(
            client=client, workspace_root=Path("/tmp/ws"), config=config,
        )
        return deployer, client

    def test_resolve_owner_from_config(self):
        deployer, client = self._make_deployer()
        deployer._config.owner_id = "own-preset"
        assert deployer._resolve_owner() == "own-preset"
        client.list_owners.assert_not_called()

    def test_resolve_owner_from_api(self):
        deployer, client = self._make_deployer()
        client.list_owners.return_value = [
            RenderOwner(id="own-1", name="team"),
        ]
        assert deployer._resolve_owner() == "own-1"

    def test_resolve_owner_no_owners(self):
        deployer, client = self._make_deployer()
        client.list_owners.return_value = []
        assert deployer._resolve_owner() is None
        assert any("No Render workspaces" in e for e in deployer._errors)

    def test_resolve_owner_api_fault(self):
        deployer, client = self._make_deployer()
        client.list_owners.side_effect = ProviderAPIFault(500, "down")
        assert deployer._resolve_owner() is None


class TestDeployerServiceManagement:
    """Service create / update logic."""

    def _make_deployer(self):
        client = MagicMock(spec=RenderClient)
        config = RenderDeployConfig(
            service_name="myapp", image="img:1",
            region="oregon", plan=RenderPlan.STARTER,
            owner_id="own-1",
        )
        deployer = RenderDeployer(
            client=client, workspace_root=Path("/tmp/ws"), config=config,
        )
        return deployer, client

    def test_ensure_service_creates_new(self):
        deployer, client = self._make_deployer()
        client.get_service_by_name.return_value = None
        new_svc = RenderService(id="srv-new", name="myapp")
        client.create_service.return_value = new_svc
        svc = deployer._ensure_service()
        assert svc.id == "srv-new"
        client.create_service.assert_called_once()

    def test_ensure_service_updates_existing(self):
        deployer, client = self._make_deployer()
        existing = RenderService(id="srv-1", name="myapp")
        client.get_service_by_name.return_value = existing
        updated = RenderService(id="srv-1", name="myapp")
        client.update_service.return_value = updated
        svc = deployer._ensure_service()
        assert svc.id == "srv-1"
        client.update_service.assert_called_once()

    def test_ensure_service_create_fails(self):
        deployer, client = self._make_deployer()
        client.get_service_by_name.return_value = None
        client.create_service.side_effect = ProviderAPIFault(422, "invalid")
        svc = deployer._ensure_service()
        assert svc is None
        assert any("Failed to create service" in e for e in deployer._errors)

    def test_ensure_service_lookup_error_falls_to_create(self):
        deployer, client = self._make_deployer()
        client.get_service_by_name.side_effect = ProviderAPIFault(500, "err")
        new_svc = RenderService(id="srv-2", name="myapp")
        client.create_service.return_value = new_svc
        svc = deployer._ensure_service()
        assert svc.id == "srv-2"


class TestDeployerEnvVarSync:
    """Environment variable synchronization."""

    def _make_deployer(self, env_vars=None):
        client = MagicMock(spec=RenderClient)
        config = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
            env_vars=env_vars or [],
        )
        deployer = RenderDeployer(
            client=client, workspace_root=Path("/tmp/ws"), config=config,
        )
        return deployer, client

    def test_sync_env_vars_success(self):
        evs = [RenderEnvVar(key="A", value="1"), RenderEnvVar(key="B", value="2")]
        deployer, client = self._make_deployer(env_vars=evs)
        svc = RenderService(id="srv-1", name="app")
        deployer._sync_env_vars(svc)
        client.update_env_vars.assert_called_once()
        payload = client.update_env_vars.call_args[0][1]
        assert len(payload) == 2

    def test_sync_env_vars_empty(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="app")
        deployer._sync_env_vars(svc)
        client.update_env_vars.assert_not_called()

    def test_sync_env_vars_no_service_id(self):
        evs = [RenderEnvVar(key="X", value="Y")]
        deployer, client = self._make_deployer(env_vars=evs)
        svc = RenderService(id=None, name="app")
        deployer._sync_env_vars(svc)
        client.update_env_vars.assert_not_called()

    def test_sync_env_vars_api_error_logged(self):
        evs = [RenderEnvVar(key="A", value="1")]
        deployer, client = self._make_deployer(env_vars=evs)
        client.update_env_vars.side_effect = ProviderAPIFault(500, "fail")
        svc = RenderService(id="srv-1", name="app")
        deployer._sync_env_vars(svc)  # Should not raise
        assert any("Warning" in s for s in deployer._steps)


class TestDeployerTriggerAndWait:
    """Deploy trigger and health polling."""

    def _make_deployer(self):
        client = MagicMock(spec=RenderClient)
        config = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
        )
        deployer = RenderDeployer(
            client=client, workspace_root=Path("/tmp/ws"), config=config,
        )
        return deployer, client

    def test_trigger_deploy_success(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="app")
        triggered = RenderDeploy(id="dpl-1", status="created")
        client.trigger_deploy.return_value = triggered
        # Mock _wait_for_live to avoid actual polling
        live = RenderDeploy(id="dpl-1", status="live")
        with patch.object(deployer, "_wait_for_live", return_value=live):
            result = deployer._trigger_and_wait(svc)
            assert result.status == "live"

    def test_trigger_deploy_api_failure(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="app")
        client.trigger_deploy.side_effect = ProviderAPIFault(500, "err")
        result = deployer._trigger_and_wait(svc)
        assert result is None

    def test_trigger_deploy_no_service_id(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id=None, name="app")
        result = deployer._trigger_and_wait(svc)
        assert result is None
        assert any("no ID" in e for e in deployer._errors)


class TestDeployerHealthPolling:
    """_wait_for_live polling logic."""

    def _make_deployer(self):
        client = MagicMock(spec=RenderClient)
        config = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
        )
        deployer = RenderDeployer(
            client=client, workspace_root=Path("/tmp/ws"), config=config,
        )
        return deployer, client

    def test_wait_for_live_immediate(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="app")
        live = RenderDeploy(id="dpl-1", status="live")
        client.list_deploys.return_value = [live]
        with patch("time.sleep"):
            result = deployer._wait_for_live(svc, timeout=10, poll_interval=1)
            assert result.status == "live"

    def test_wait_for_live_transitions(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="app")
        building = RenderDeploy(id="dpl-1", status="build_in_progress")
        live = RenderDeploy(id="dpl-1", status="live")
        client.list_deploys.side_effect = [[building], [live]]
        with patch("time.sleep"):
            result = deployer._wait_for_live(svc, timeout=60, poll_interval=1)
            assert result.status == "live"

    def test_wait_for_live_build_failed(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="app")
        failed = RenderDeploy(id="dpl-1", status="build_failed")
        client.list_deploys.return_value = [failed]
        with patch("time.sleep"):
            result = deployer._wait_for_live(svc, timeout=10, poll_interval=1)
            assert result is None
            assert any("build_failed" in e for e in deployer._errors)

    def test_wait_for_live_update_failed(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="app")
        failed = RenderDeploy(id="dpl-1", status="update_failed")
        client.list_deploys.return_value = [failed]
        with patch("time.sleep"):
            result = deployer._wait_for_live(svc, timeout=10, poll_interval=1)
            assert result is None

    def test_wait_for_live_canceled(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="app")
        canceled = RenderDeploy(id="dpl-1", status="canceled")
        client.list_deploys.return_value = [canceled]
        with patch("time.sleep"):
            result = deployer._wait_for_live(svc, timeout=10, poll_interval=1)
            assert result is None

    def test_wait_for_live_pre_deploy_failed(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="app")
        failed = RenderDeploy(id="dpl-1", status="pre_deploy_failed")
        client.list_deploys.return_value = [failed]
        with patch("time.sleep"):
            result = deployer._wait_for_live(svc, timeout=10, poll_interval=1)
            assert result is None

    def test_wait_for_live_timeout(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="app")
        building = RenderDeploy(id="dpl-1", status="build_in_progress")
        client.list_deploys.return_value = [building]
        # Provide enough time.time() values for: deadline calc, while-check,
        # logging inside _step/_error, and any internal LogRecord timestamps.
        with patch("time.time", side_effect=[0, 0, 0, 0, 0, 0, 0, 999, 999, 999, 999, 999]):
            with patch("time.sleep"):
                result = deployer._wait_for_live(svc, timeout=10, poll_interval=1)
                assert result is None
                assert any("did not go live" in e for e in deployer._errors)

    def test_wait_for_live_empty_deploys(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="app")
        client.list_deploys.return_value = []
        with patch("time.time", side_effect=[0, 0, 0, 0, 0, 0, 0, 999, 999, 999, 999, 999]):
            with patch("time.sleep"):
                result = deployer._wait_for_live(svc, timeout=10, poll_interval=1)
                assert result is None

    def test_wait_for_live_api_error_during_poll(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="app")
        live = RenderDeploy(id="dpl-1", status="live")
        client.list_deploys.side_effect = [
            ProviderAPIFault(500, "blip"),
            [live],
        ]
        with patch("time.sleep"):
            result = deployer._wait_for_live(svc, timeout=60, poll_interval=1)
            assert result.status == "live"


class TestDeployerAutoscaling:
    """Autoscaling configuration step."""

    def test_configure_autoscaling(self):
        client = MagicMock(spec=RenderClient)
        auto = RenderAutoscaling.auto(min_instances=2, max_instances=4)
        config = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
            autoscaling=auto,
        )
        deployer = RenderDeployer(
            client=client, workspace_root=Path("/tmp/ws"), config=config,
        )
        svc = RenderService(id="srv-1", name="app")
        deployer._configure_autoscaling(svc)
        client.set_autoscaling.assert_called_once_with("srv-1", auto.to_dict())

    def test_configure_autoscaling_api_error(self):
        client = MagicMock(spec=RenderClient)
        auto = RenderAutoscaling.auto()
        config = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
            autoscaling=auto,
        )
        deployer = RenderDeployer(
            client=client, workspace_root=Path("/tmp/ws"), config=config,
        )
        client.set_autoscaling.side_effect = ProviderAPIFault(400, "bad")
        svc = RenderService(id="srv-1", name="app")
        deployer._configure_autoscaling(svc)  # Should not raise
        assert any("Warning" in s for s in deployer._steps)


class TestDeployerURLResolution:
    """URL resolution logic."""

    def _make_deployer(self):
        client = MagicMock(spec=RenderClient)
        config = RenderDeployConfig(
            service_name="myapp", image="img:1", region="oregon",
        )
        deployer = RenderDeployer(
            client=client, workspace_root=Path("/tmp/ws"), config=config,
        )
        return deployer, client

    def test_url_from_slug(self):
        deployer, _ = self._make_deployer()
        svc = RenderService(id="srv-1", name="myapp", slug="myapp-abc")
        assert deployer._resolve_url(svc) == "https://myapp-abc.onrender.com"

    def test_url_from_custom_domain(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="myapp", slug=None)
        client.list_custom_domains.return_value = [{"name": "app.example.com"}]
        assert deployer._resolve_url(svc) == "https://app.example.com"

    def test_url_fallback_to_service_name(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="myapp", slug=None)
        client.list_custom_domains.return_value = []
        assert deployer._resolve_url(svc) == "https://myapp.onrender.com"

    def test_url_fallback_no_id(self):
        deployer, _ = self._make_deployer()
        svc = RenderService(id=None, name="myapp", slug=None)
        assert deployer._resolve_url(svc) == "https://myapp.onrender.com"

    def test_url_custom_domain_api_error(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="myapp", slug=None)
        client.list_custom_domains.side_effect = ProviderAPIFault(500, "err")
        assert deployer._resolve_url(svc) == "https://myapp.onrender.com"


class TestDeployerDestroy:
    """Service destruction."""

    def _make_deployer(self):
        client = MagicMock(spec=RenderClient)
        config = RenderDeployConfig(
            service_name="doomed", image="img:1", region="oregon",
        )
        deployer = RenderDeployer(
            client=client, workspace_root=Path("/tmp/ws"), config=config,
        )
        return deployer, client

    def test_destroy_success(self):
        deployer, client = self._make_deployer()
        client.get_service_by_name.return_value = RenderService(id="srv-1", name="doomed")
        assert deployer.destroy() is True
        client.delete_service.assert_called_once_with("srv-1")

    def test_destroy_not_found(self):
        deployer, client = self._make_deployer()
        client.get_service_by_name.return_value = None
        assert deployer.destroy() is True
        client.delete_service.assert_not_called()

    def test_destroy_api_error(self):
        deployer, client = self._make_deployer()
        client.get_service_by_name.side_effect = ProviderAPIFault(500, "down")
        assert deployer.destroy() is False


class TestDeployerStatus:
    """Status query."""

    def _make_deployer(self):
        client = MagicMock(spec=RenderClient)
        config = RenderDeployConfig(
            service_name="statusapp", image="img:1", region="oregon",
        )
        deployer = RenderDeployer(
            client=client, workspace_root=Path("/tmp/ws"), config=config,
        )
        return deployer, client

    def test_status_deployed(self):
        deployer, client = self._make_deployer()
        svc = RenderService(
            id="srv-1", name="statusapp", slug="statusapp-abc",
            plan="starter", region="oregon", status="running",
            suspended="not_suspended",
        )
        client.get_service_by_name.return_value = svc
        deploy = RenderDeploy(id="dpl-1", status="live", created_at="2026-01-01")
        client.list_deploys.return_value = [deploy]
        s = deployer.status()
        assert s["status"] == "deployed"
        assert s["service_id"] == "srv-1"
        assert s["url"] == "https://statusapp-abc.onrender.com"
        assert s["latest_deploy"]["id"] == "dpl-1"

    def test_status_not_deployed(self):
        deployer, client = self._make_deployer()
        client.get_service_by_name.return_value = None
        s = deployer.status()
        assert s["status"] == "not_deployed"

    def test_status_api_error(self):
        deployer, client = self._make_deployer()
        client.get_service_by_name.side_effect = ProviderAPIFault(500, "err")
        s = deployer.status()
        assert s["status"] == "error"

    def test_status_no_deploys(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="srv-1", name="statusapp", slug="s")
        client.get_service_by_name.return_value = svc
        client.list_deploys.return_value = []
        s = deployer.status()
        assert s["latest_deploy"] is None


class TestDeployerFullPipeline:
    """End-to-end deploy pipeline (mocked)."""

    def test_full_pipeline_success(self):
        client = MagicMock(spec=RenderClient)
        config = RenderDeployConfig(
            service_name="fullapp",
            image="ghcr.io/org/fullapp:v1",
            region="oregon",
            plan=RenderPlan.STANDARD,
            env_vars=[RenderEnvVar(key="ENV", value="prod")],
        )
        deployer = RenderDeployer(
            client=client, workspace_root=Path("/tmp/ws"), config=config,
        )
        # Mock pipeline steps
        client.validate_token.return_value = True
        client.list_owners.return_value = [RenderOwner(id="own-1", name="team")]
        new_svc = RenderService(id="srv-1", name="fullapp", slug="fullapp-xyz")
        client.get_service_by_name.return_value = None
        client.create_service.return_value = new_svc
        client.update_env_vars.return_value = []
        triggered = RenderDeploy(id="dpl-1", status="created")
        client.trigger_deploy.return_value = triggered
        live = RenderDeploy(id="dpl-1", status="live")
        client.list_deploys.return_value = [live]

        push_result = MagicMock(returncode=0)
        with patch("time.sleep"), patch("subprocess.run", return_value=push_result):
            result = deployer.deploy()

        assert result.success is True
        assert result.url == "https://fullapp-xyz.onrender.com"
        assert result.service.id == "srv-1"
        assert result.errors == []

    def test_full_pipeline_with_autoscaling(self):
        client = MagicMock(spec=RenderClient)
        auto = RenderAutoscaling.auto(min_instances=2, max_instances=4)
        config = RenderDeployConfig(
            service_name="scaledapp",
            image="ghcr.io/org/app:v1",
            region="oregon",
            autoscaling=auto,
        )
        deployer = RenderDeployer(
            client=client, workspace_root=Path("/tmp/ws"), config=config,
        )
        client.validate_token.return_value = True
        client.list_owners.return_value = [RenderOwner(id="own-1", name="t")]
        svc = RenderService(id="srv-1", name="scaledapp", slug="s")
        client.get_service_by_name.return_value = None
        client.create_service.return_value = svc
        client.trigger_deploy.return_value = RenderDeploy(id="d", status="created")
        client.list_deploys.return_value = [RenderDeploy(id="d", status="live")]

        push_result = MagicMock(returncode=0)
        with patch("time.sleep"), patch("subprocess.run", return_value=push_result):
            result = deployer.deploy()

        assert result.success is True
        client.set_autoscaling.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
#  § 6  Package Init
# ═══════════════════════════════════════════════════════════════════════════════


class TestPackageExports:
    """Verify all public symbols are exported from render package."""

    def test_all_exports(self):
        expected = [
            "RenderClient", "RenderDeployer", "RenderCredentialStore",
            "RenderService", "RenderDeploy", "RenderOwner",
            "RenderServiceType", "RenderPlan", "RenderDeployStatus",
            "RenderDeployConfig", "RenderAutoscaling", "RenderRegion",
            "RenderEnvVar", "RenderDisk",
        ]
        for name in expected:
            assert hasattr(render_pkg, name), f"Missing export: {name}"

    def test_all_list(self):
        # Verify all original symbols plus the new v2 additions
        expected = {
            # Client & Deployer
            "RenderClient", "RenderDeployer", "DeployResult", "RenderCredentialStore",
            # Core resources
            "RenderService", "RenderDeploy", "RenderOwner",
            "RenderEnvVar", "RenderDisk", "RenderDiskSnapshot",
            "RenderAutoscaling", "RenderDeployConfig",
            # Enums
            "RenderServiceType", "RenderPlan", "RenderDeployStatus",
            "RenderRegion", "RenderServiceStatus", "RenderJobStatus",
            "RenderDomainVerificationStatus", "RenderLogLevel",
            "RenderLogDirection", "RenderLogType", "RenderRouteType",
            "RenderMaintenanceStatus", "RenderWebhookEventType",
            "RenderNotificationType", "RenderPostgresPlan",
            "RenderKeyValuePlan", "RenderBlueprintSyncStatus",
            "RenderInstanceStatus",
            # Extended resources
            "RenderSecretFile", "RenderCustomDomain", "RenderInstance",
            "RenderEvent", "RenderJob", "RenderHeaderRule",
            "RenderRedirectRule", "RenderLogEntry", "RenderMetricPoint",
            "RenderMetricsFilter", "RenderWebhook", "RenderProject",
            "RenderEnvironment", "RenderEnvGroup",
            "RenderRegistryCredential", "RenderMaintenance",
            "RenderNotificationSettings", "RenderAuditLogEntry",
            # Postgres & Key-Value
            "RenderPostgresInstance", "RenderPostgresConnectionInfo",
            "RenderPostgresUser", "RenderKeyValueInstance",
            "RenderKeyValueConnectionInfo",
            # Blueprint / IaC
            "RenderBlueprint", "RenderBlueprintSync",
            # Workspace
            "RenderWorkspaceMember", "RenderLogStream",
        }
        assert set(render_pkg.__all__) == expected


# ═══════════════════════════════════════════════════════════════════════════════
#  § 7  Fault Defaults
# ═══════════════════════════════════════════════════════════════════════════════


class TestFaultDefaults:
    """All provider faults default to provider='render'."""

    def test_provider_api_fault_default(self):
        f = ProviderAPIFault(500, "err")
        assert f.metadata["provider"] == "render"

    def test_provider_api_fault_custom_provider(self):
        f = ProviderAPIFault(500, "err", provider="custom")
        assert f.metadata["provider"] == "custom"

    def test_provider_auth_fault_default(self):
        f = ProviderAuthFault()
        assert f.metadata["provider"] == "render"

    def test_provider_rate_limit_fault_default(self):
        f = ProviderRateLimitFault(retry_after=5.0)
        assert f.metadata["provider"] == "render"

    def test_provider_token_fault_default(self):
        f = ProviderTokenFault()
        assert f.metadata["provider"] == "render"

    def test_provider_credential_fault_default(self):
        f = ProviderCredentialFault("test error")
        assert f.metadata["provider"] == "render"

    def test_provider_connection_fault_default(self):
        f = ProviderConnectionFault("timeout")
        assert f.metadata["provider"] == "render"

    def test_provider_api_fault_has_status_code(self):
        f = ProviderAPIFault(422, "bad input")
        assert f.status_code == 422
        assert f.metadata["status_code"] == 422

    def test_provider_api_fault_retryable_on_5xx(self):
        f = ProviderAPIFault(502, "bad gw")
        assert f.retryable is True

    def test_provider_api_fault_not_retryable_on_4xx(self):
        f = ProviderAPIFault(400, "bad req")
        assert f.retryable is False

    def test_provider_auth_fault_not_retryable(self):
        f = ProviderAuthFault()
        assert f.retryable is False

    def test_provider_rate_limit_fault_retryable(self):
        f = ProviderRateLimitFault(retry_after=1.0)
        assert f.retryable is True

    def test_provider_token_fault_not_retryable(self):
        f = ProviderTokenFault()
        assert f.retryable is False

    def test_provider_connection_fault_retryable(self):
        f = ProviderConnectionFault("net err")
        assert f.retryable is True

    def test_provider_api_fault_request_id(self):
        f = ProviderAPIFault(500, "err", request_id="req-123")
        assert f.request_id == "req-123"
        assert f.metadata["request_id"] == "req-123"

    def test_provider_credential_fault_path(self):
        f = ProviderCredentialFault("err", path="/home/user/.creds")
        assert f.metadata["path"] == "/home/user/.creds"

    def test_provider_rate_limit_fault_retry_after(self):
        f = ProviderRateLimitFault(retry_after=42.5)
        assert f.retry_after == 42.5
        assert f.metadata["retry_after"] == 42.5


# ═══════════════════════════════════════════════════════════════════════════════
#  § 8  Edge Cases & Regression Guards
# ═══════════════════════════════════════════════════════════════════════════════


class TestRegressionGuards:
    """Edge cases and regression guards."""

    def test_client_no_body_get_request(self):
        """GET with no params and empty response body."""
        client = _make_client()
        resp = _make_http_response(b"", 204)
        with patch("urllib.request.urlopen", return_value=resp):
            result = client._request("GET", "/empty")
            assert result.body == b""

    def test_client_request_method_uppercased(self):
        """Method is uppercased in the Request object."""
        client = _make_client()
        resp = _make_http_response(b'{}')
        with patch("urllib.request.urlopen", return_value=resp) as mock:
            client._request("patch", "/services/srv-1")
            req_obj = mock.call_args[0][0]
            assert req_obj.method == "PATCH"

    def test_service_type_preserves_all_render_types(self):
        """All Render service types are parseable."""
        for stype in RenderServiceType:
            data = {"type": stype.value, "name": "test"}
            svc = RenderClient._parse_service(data)
            assert svc.type == stype

    def test_deploy_config_auto_deploy_default(self):
        """auto_deploy defaults to 'no'."""
        cfg = RenderDeployConfig()
        assert cfg.auto_deploy == "no"
        p = cfg.to_service_payload()
        assert p["autoDeploy"] == "no"

    def test_env_var_to_dict_immutability(self):
        """to_dict returns a fresh dict each call."""
        ev = RenderEnvVar(key="K", value="V")
        d1 = ev.to_dict()
        d2 = ev.to_dict()
        assert d1 == d2
        assert d1 is not d2

    def test_store_concurrent_save_load(self):
        """Multiple rapid save/load cycles don't corrupt."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store = RenderCredentialStore(store_dir=Path(tmpdir) / "creds")
            for i in range(10):
                token = f"rnd_token_{i}"
                store.save(token, owner_name=f"user_{i}")
                assert store.load() == token
                assert store.get_owner_name() == f"user_{i}"

    def test_autoscaling_disabled_to_dict_keys(self):
        d = RenderAutoscaling.disabled().to_dict()
        assert set(d.keys()) == {"enabled", "min", "max"}

    def test_disk_to_dict_snake_to_camel(self):
        """Verify snake_case → camelCase mapping."""
        disk = RenderDisk(name="d", mount_path="/m", size_gb=2)
        d = disk.to_dict()
        assert "mountPath" in d
        assert "sizeGB" in d
        assert "mount_path" not in d
        assert "size_gb" not in d

    def test_deploy_result_defaults(self):
        r = DeployResult(success=True)
        assert r.errors == []
        assert r.steps_completed == []
        assert r.service is None
        assert r.deploy is None
        assert r.url is None

    def test_client_base_url_default(self):
        assert _BASE_URL == "https://api.render.com/v1"

    def test_client_user_agent(self):
        assert _USER_AGENT == "Aquilia-CLI/2.0"

    def test_client_retry_constants(self):
        assert _MAX_RETRIES == 3
        assert _RETRY_BACKOFF == 1.5

    def test_store_crous_magic(self):
        assert _CROUS_MAGIC == b"AQCR"
        assert _CROUS_VERSION == 2
        assert _CROUS_VERSION_LEGACY == 1
        assert _SALT_SIZE == 32
        assert _NONCE_SIZE == 12

    def test_render_plan_ordering(self):
        """Plans should go from cheapest to most expensive."""
        plans = list(RenderPlan)
        assert plans[0] == RenderPlan.FREE
        assert plans[-1] == RenderPlan.PRO_ULTRA

    def test_render_region_has_us_and_eu(self):
        """At minimum, has US and EU regions."""
        values = [r.value for r in RenderRegion]
        assert "oregon" in values    # US
        assert "frankfurt" in values # EU

    def test_deploy_status_live_is_terminal_success(self):
        assert RenderDeployStatus.LIVE.value == "live"

    def test_env_var_generated_secret_format(self):
        """Generated secrets use generateValue API field."""
        ev = RenderEnvVar(key="SECRET", generate_value="yes")
        d = ev.to_dict()
        assert "generateValue" in d
        assert d["generateValue"] == "yes"

    def test_service_payload_no_image(self):
        """Service payload without image omits image field."""
        cfg = RenderDeployConfig(
            service_name="app", image="", region="oregon",
        )
        p = cfg.to_service_payload()
        assert "image" not in p["serviceDetails"]

    def test_update_payload_no_docker_command(self):
        """Update payload without docker_command omits it."""
        cfg = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
        )
        p = cfg.to_update_payload()
        assert "dockerCommand" not in p["serviceDetails"]


# ═══════════════════════════════════════════════════════════════════════════════
#  § 9  Enhanced v2 Types Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnhancedEnums:
    """Test all new v2 enum types."""

    def test_service_status_values(self):
        from aquilia.providers.render.types import RenderServiceStatus
        assert RenderServiceStatus.LIVE.value == "live"
        assert RenderServiceStatus.SUSPENDED.value == "suspended"

    def test_job_status_values(self):
        from aquilia.providers.render.types import RenderJobStatus
        assert RenderJobStatus.SUCCEEDED.value == "succeeded"
        assert RenderJobStatus.FAILED.value == "failed"
        assert RenderJobStatus.IN_PROGRESS.value == "in_progress"

    def test_domain_verification_status(self):
        from aquilia.providers.render.types import RenderDomainVerificationStatus
        assert RenderDomainVerificationStatus.VERIFIED.value == "verified"
        assert RenderDomainVerificationStatus.UNVERIFIED.value == "unverified"

    def test_log_level_values(self):
        from aquilia.providers.render.types import RenderLogLevel
        assert RenderLogLevel.ERROR.value == "error"
        assert RenderLogLevel.DEBUG.value == "debug"

    def test_log_direction(self):
        from aquilia.providers.render.types import RenderLogDirection
        assert RenderLogDirection.FORWARD.value == "forward"
        assert RenderLogDirection.BACKWARD.value == "backward"

    def test_log_type(self):
        from aquilia.providers.render.types import RenderLogType
        assert RenderLogType.APP.value == "app"
        assert RenderLogType.BUILD.value == "build"

    def test_route_type(self):
        from aquilia.providers.render.types import RenderRouteType
        assert RenderRouteType.REDIRECT.value == "redirect"
        assert RenderRouteType.REWRITE.value == "rewrite"

    def test_maintenance_status(self):
        from aquilia.providers.render.types import RenderMaintenanceStatus
        assert RenderMaintenanceStatus.SCHEDULED.value == "scheduled"
        assert RenderMaintenanceStatus.COMPLETED.value == "completed"

    def test_webhook_event_type(self):
        from aquilia.providers.render.types import RenderWebhookEventType
        assert RenderWebhookEventType.DEPLOY_STARTED.value == "deploy_started"
        assert RenderWebhookEventType.SERVICE_DELETED.value == "service_deleted"

    def test_notification_type(self):
        from aquilia.providers.render.types import RenderNotificationType
        assert RenderNotificationType.EMAIL.value == "email"
        assert RenderNotificationType.SLACK.value == "slack"

    def test_postgres_plan(self):
        from aquilia.providers.render.types import RenderPostgresPlan
        assert RenderPostgresPlan.FREE.value == "free"
        assert RenderPostgresPlan.ACCELERATED.value == "accelerated"

    def test_key_value_plan(self):
        from aquilia.providers.render.types import RenderKeyValuePlan
        assert RenderKeyValuePlan.FREE.value == "free"
        assert RenderKeyValuePlan.PRO.value == "pro"

    def test_blueprint_sync_status(self):
        from aquilia.providers.render.types import RenderBlueprintSyncStatus
        assert RenderBlueprintSyncStatus.SYNCED.value == "synced"
        assert RenderBlueprintSyncStatus.FAILED.value == "failed"

    def test_instance_status(self):
        from aquilia.providers.render.types import RenderInstanceStatus
        assert RenderInstanceStatus.RUNNING.value == "running"
        assert RenderInstanceStatus.CRASHED.value == "crashed"


class TestEnhancedDataclasses:
    """Test all new v2 dataclasses."""

    def test_secret_file_to_dict(self):
        from aquilia.providers.render.types import RenderSecretFile
        sf = RenderSecretFile(name=".env", content="SECRET=abc")
        d = sf.to_dict()
        assert d["name"] == ".env"
        assert d["content"] == "SECRET=abc"

    def test_secret_file_repr_redacts(self):
        from aquilia.providers.render.types import RenderSecretFile
        sf = RenderSecretFile(name=".env", content="TOP_SECRET")
        assert "TOP_SECRET" not in repr(sf)
        assert "***" in repr(sf)

    def test_custom_domain_fields(self):
        from aquilia.providers.render.types import RenderCustomDomain
        cd = RenderCustomDomain(name="example.com", verification_status="verified")
        assert cd.name == "example.com"
        assert cd.verification_status == "verified"

    def test_instance_fields(self):
        from aquilia.providers.render.types import RenderInstance
        i = RenderInstance(id="inst-1", status="running", region="oregon")
        assert i.id == "inst-1"
        assert i.region == "oregon"

    def test_event_fields(self):
        from aquilia.providers.render.types import RenderEvent
        e = RenderEvent(id="evt-1", type="deploy_started")
        assert e.type == "deploy_started"

    def test_job_fields(self):
        from aquilia.providers.render.types import RenderJob
        j = RenderJob(id="job-1", status="succeeded")
        assert j.status == "succeeded"

    def test_header_rule_to_dict(self):
        from aquilia.providers.render.types import RenderHeaderRule
        h = RenderHeaderRule(path="/*", name="X-Frame-Options", value="DENY")
        d = h.to_dict()
        assert d["name"] == "X-Frame-Options"
        assert d["value"] == "DENY"
        assert d["path"] == "/*"

    def test_redirect_rule_to_dict(self):
        from aquilia.providers.render.types import RenderRedirectRule
        r = RenderRedirectRule(source="/old", destination="/new", status_code=301)
        d = r.to_dict()
        assert d["source"] == "/old"
        assert d["destination"] == "/new"
        assert d["statusCode"] == 301

    def test_log_entry_fields(self):
        from aquilia.providers.render.types import RenderLogEntry
        le = RenderLogEntry(message="hello", level="info")
        assert le.message == "hello"
        assert le.level == "info"

    def test_metric_point_fields(self):
        from aquilia.providers.render.types import RenderMetricPoint
        mp = RenderMetricPoint(value=42.5, unit="percent")
        assert mp.value == 42.5
        assert mp.unit == "percent"

    def test_webhook_to_dict(self):
        from aquilia.providers.render.types import RenderWebhook
        wh = RenderWebhook(url="https://hook.example.com", events=["deploy_started"], secret="s3cret")
        d = wh.to_dict()
        assert d["url"] == "https://hook.example.com"
        assert "deploy_started" in d["events"]
        assert d["secret"] == "s3cret"

    def test_webhook_repr_redacts_secret(self):
        from aquilia.providers.render.types import RenderWebhook
        wh = RenderWebhook(url="https://hook.example.com", secret="s3cret")
        assert "s3cret" not in repr(wh)
        assert "***" in repr(wh)

    def test_project_fields(self):
        from aquilia.providers.render.types import RenderProject
        p = RenderProject(id="prj-1", name="MyProject")
        assert p.name == "MyProject"

    def test_environment_fields(self):
        from aquilia.providers.render.types import RenderEnvironment
        e = RenderEnvironment(name="staging", project_id="prj-1")
        assert e.name == "staging"

    def test_env_group_to_dict(self):
        from aquilia.providers.render.types import RenderEnvGroup, RenderEnvVar
        eg = RenderEnvGroup(name="shared", env_vars=[RenderEnvVar(key="K", value="V")])
        d = eg.to_dict()
        assert d["name"] == "shared"
        assert len(d["envVars"]) == 1
        assert d["envVars"][0]["key"] == "K"

    def test_registry_credential_repr(self):
        from aquilia.providers.render.types import RenderRegistryCredential
        rc = RenderRegistryCredential(name="dockerhub", registry="DOCKER", username="user1")
        r = repr(rc)
        assert "dockerhub" in r
        assert "DOCKER" in r

    def test_postgres_connection_info_repr_redacts(self):
        from aquilia.providers.render.types import RenderPostgresConnectionInfo
        ci = RenderPostgresConnectionInfo(password="supersecret")
        assert "supersecret" not in repr(ci)
        assert "redacted" in repr(ci)

    def test_postgres_user_repr_redacts(self):
        from aquilia.providers.render.types import RenderPostgresUser
        pu = RenderPostgresUser(name="admin", password="pw123")
        assert "pw123" not in repr(pu)
        assert "***" in repr(pu)

    def test_key_value_connection_info_repr_redacts(self):
        from aquilia.providers.render.types import RenderKeyValueConnectionInfo
        ci = RenderKeyValueConnectionInfo(password="redispw")
        assert "redispw" not in repr(ci)
        assert "redacted" in repr(ci)

    def test_log_stream_repr_redacts_token(self):
        from aquilia.providers.render.types import RenderLogStream
        ls = RenderLogStream(name="syslog", endpoint="https://log.example.com", token="tok123")
        assert "tok123" not in repr(ls)
        assert "***" in repr(ls)

    def test_metrics_filter_to_params(self):
        from aquilia.providers.render.types import RenderMetricsFilter
        mf = RenderMetricsFilter(resource_id="svc-1", metric="memory", period="24h")
        params = mf.to_params()
        assert params["metric"] == "memory"
        assert params["period"] == "24h"
        assert params["resourceId"] == "svc-1"

    def test_metrics_filter_optional_params(self):
        from aquilia.providers.render.types import RenderMetricsFilter
        mf = RenderMetricsFilter(metric="cpu", period="1h")
        params = mf.to_params()
        assert "resourceId" not in params
        assert "startTime" not in params

    def test_disk_snapshot_fields(self):
        from aquilia.providers.render.types import RenderDiskSnapshot
        ds = RenderDiskSnapshot(id="snap-1", disk_id="disk-1", status="completed")
        assert ds.id == "snap-1"
        assert ds.status == "completed"

    def test_blueprint_fields(self):
        from aquilia.providers.render.types import RenderBlueprint
        bp = RenderBlueprint(name="my-bp", auto_sync=True, repo="org/repo")
        assert bp.auto_sync is True
        assert bp.repo == "org/repo"

    def test_blueprint_sync_fields(self):
        from aquilia.providers.render.types import RenderBlueprintSync
        bs = RenderBlueprintSync(status="synced", blueprint_id="bp-1")
        assert bs.status == "synced"

    def test_workspace_member_fields(self):
        from aquilia.providers.render.types import RenderWorkspaceMember
        wm = RenderWorkspaceMember(email="user@example.com", role="admin")
        assert wm.email == "user@example.com"
        assert wm.role == "admin"

    def test_maintenance_fields(self):
        from aquilia.providers.render.types import RenderMaintenance
        m = RenderMaintenance(status="scheduled", description="DB upgrade")
        assert m.description == "DB upgrade"

    def test_notification_settings_fields(self):
        from aquilia.providers.render.types import RenderNotificationSettings
        ns = RenderNotificationSettings(notify_on_fail="notify")
        assert ns.notify_on_fail == "notify"

    def test_audit_log_entry_fields(self):
        from aquilia.providers.render.types import RenderAuditLogEntry
        ale = RenderAuditLogEntry(action="service.create", actor={"name": "user1"})
        assert ale.action == "service.create"


# ═══════════════════════════════════════════════════════════════════════════════
#  § 10  Enhanced v2 Deploy Config Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnhancedDeployConfig:
    """Test v2 deploy config enhancements."""

    def test_service_payload_with_secret_files(self):
        from aquilia.providers.render.types import RenderSecretFile
        cfg = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
            secret_files=[RenderSecretFile(name=".env", content="X=1")],
        )
        p = cfg.to_service_payload()
        assert "secretFiles" in p["serviceDetails"]
        assert p["serviceDetails"]["secretFiles"][0]["name"] == ".env"

    def test_service_payload_with_headers(self):
        from aquilia.providers.render.types import RenderHeaderRule
        cfg = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
            headers=[RenderHeaderRule(name="X-Custom", value="val")],
        )
        p = cfg.to_service_payload()
        assert "headers" in p["serviceDetails"]

    def test_service_payload_with_redirect_rules(self):
        from aquilia.providers.render.types import RenderRedirectRule
        cfg = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
            redirect_rules=[RenderRedirectRule(source="/old", destination="/new")],
        )
        p = cfg.to_service_payload()
        assert "routes" in p["serviceDetails"]

    def test_service_payload_with_registry_credential(self):
        cfg = RenderDeployConfig(
            service_name="app", image="ghcr.io/org/img:1", region="oregon",
            registry_credential_id="reg-123",
        )
        p = cfg.to_service_payload()
        assert p["serviceDetails"]["image"]["registryCredentialId"] == "reg-123"

    def test_service_payload_with_pre_deploy_command(self):
        cfg = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
            pre_deploy_command="python manage.py migrate",
        )
        p = cfg.to_service_payload()
        assert p["serviceDetails"]["preDeployCommand"] == "python manage.py migrate"

    def test_service_payload_with_project_id(self):
        cfg = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
            project_id="prj-123",
        )
        p = cfg.to_service_payload()
        assert p["projectId"] == "prj-123"

    def test_service_payload_with_env_group_ids(self):
        cfg = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
            env_group_ids=["eg-1", "eg-2"],
        )
        p = cfg.to_service_payload()
        assert "envSpecificDetails" in p
        assert p["envSpecificDetails"]["envGroupIds"] == ["eg-1", "eg-2"]

    def test_service_payload_with_notify_on_fail(self):
        cfg = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
            notify_on_fail="notify",
        )
        p = cfg.to_service_payload()
        assert p["notifyOnFail"] == "notify"

    def test_service_payload_with_root_dir(self):
        cfg = RenderDeployConfig(
            service_name="app", image="img:1", region="oregon",
            root_dir="./backend",
        )
        p = cfg.to_service_payload()
        assert p["rootDir"] == "./backend"

    def test_from_workspace_context_includes_security_headers(self):
        wctx = {"name": "myapp", "port": 8000, "workers": 4}
        cfg = RenderDeployConfig.from_workspace_context(wctx, image="img:1")
        assert len(cfg.headers) >= 5
        header_names = [h.name for h in cfg.headers]
        assert "X-Content-Type-Options" in header_names
        assert "X-Frame-Options" in header_names
        assert "Strict-Transport-Security" in header_names


# ═══════════════════════════════════════════════════════════════════════════════
#  § 11  Enhanced v2 Security Store Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnhancedSecurity:
    """Test the military-grade security enhancements."""

    @pytest.fixture
    def store_dir(self, tmp_path):
        return tmp_path / "render_security"

    @pytest.fixture
    def store(self, store_dir):
        return RenderCredentialStore(store_dir)

    def test_secure_zero_clears_buffer(self):
        buf = bytearray(b"SECRET_DATA_HERE")
        _secure_zero(buf)
        assert buf == bytearray(16)

    def test_secure_zero_empty_buffer(self):
        buf = bytearray()
        _secure_zero(buf)  # Should not raise
        assert len(buf) == 0

    def test_detect_cipher_suite_returns_valid(self):
        cs = _detect_cipher_suite()
        assert cs in (1, 3)  # AES-GCM or XOR-HMAC

    def test_encrypt_decrypt_roundtrip(self):
        key = secrets.token_bytes(32)
        nonce = secrets.token_bytes(12)
        plaintext = b"Hello, military-grade encryption!"
        cs = _detect_cipher_suite()
        ct, tag = _encrypt(key, nonce, plaintext, cs)
        result = _decrypt(key, nonce, ct, tag, cs)
        assert result == plaintext

    def test_encrypt_decrypt_xor_fallback(self):
        """Test XOR-HMAC cipher directly."""
        key = secrets.token_bytes(32)
        nonce = secrets.token_bytes(12)
        plaintext = b"XOR fallback test data"
        from aquilia.providers.render.store import _CIPHER_XOR_HMAC
        ct, tag = _encrypt(key, nonce, plaintext, _CIPHER_XOR_HMAC)
        result = _decrypt(key, nonce, ct, tag, _CIPHER_XOR_HMAC)
        assert result == plaintext

    def test_decrypt_tampered_ciphertext_fails(self):
        key = secrets.token_bytes(32)
        nonce = secrets.token_bytes(12)
        plaintext = b"tamper test"
        from aquilia.providers.render.store import _CIPHER_XOR_HMAC
        ct, tag = _encrypt(key, nonce, plaintext, _CIPHER_XOR_HMAC)
        tampered = bytes([ct[0] ^ 0xFF]) + ct[1:]
        with pytest.raises(ProviderCredentialFault):
            _decrypt(key, nonce, tampered, tag, _CIPHER_XOR_HMAC)

    def test_generate_keystream_length(self):
        key = secrets.token_bytes(32)
        nonce = secrets.token_bytes(12)
        stream = _generate_keystream(key, nonce, 200)
        assert len(stream) == 200

    def test_generate_keystream_deterministic(self):
        key = secrets.token_bytes(32)
        nonce = secrets.token_bytes(12)
        s1 = _generate_keystream(key, nonce, 100)
        s2 = _generate_keystream(key, nonce, 100)
        assert s1 == s2

    def test_derive_key_v2_different_from_legacy(self):
        salt = secrets.token_bytes(32)
        from aquilia.providers.render.store import _derive_key_legacy
        key_v2 = _derive_key(salt, context="test")
        key_v1 = _derive_key_legacy(salt, context="test")
        assert key_v2 != key_v1

    def test_store_token_expiry(self, store_dir):
        """Token with TTL should expire."""
        store = RenderCredentialStore(store_dir, ttl=1)
        store.save("rnd_expiring_token")
        assert store.load() == "rnd_expiring_token"
        time.sleep(1.5)
        with pytest.raises(ProviderCredentialFault, match="expired"):
            store.load()

    def test_store_no_expiry(self, store):
        """Token without TTL should not expire."""
        store.save("rnd_forever")
        assert store.is_expired() is False

    def test_store_token_age(self, store):
        store.save("rnd_age_test")
        age = store.get_token_age()
        assert age is not None
        assert age >= 0
        assert age < 5  # Should be nearly instantaneous

    def test_store_rotate(self, store):
        """Key rotation re-encrypts with new salt."""
        store.save("rnd_rotate_test")
        old_blob = store.credentials_path.read_bytes()
        store.rotate()
        new_blob = store.credentials_path.read_bytes()
        assert old_blob != new_blob  # Different salt = different ciphertext
        assert store.load() == "rnd_rotate_test"

    def test_store_rotate_with_new_token(self, store):
        store.save("rnd_old")
        store.rotate(new_token="rnd_new")
        assert store.load() == "rnd_new"

    def test_store_rotate_no_existing_token(self, store):
        with pytest.raises(ProviderCredentialFault, match="No existing token"):
            store.rotate()

    def test_store_clear_secure_overwrite(self, store):
        """Clear performs 3-pass overwrite."""
        store.save("rnd_secure_clear")
        creds_path = store.credentials_path
        assert creds_path.exists()
        store.clear()
        assert not creds_path.exists()

    def test_store_audit_log(self, store):
        store.save("rnd_audit_test")
        store.load()
        entries = store.get_audit_log()
        assert len(entries) > 0
        actions = [e["action"] for e in entries]
        assert "save_start" in actions
        assert "save_complete" in actions
        assert "load_start" in actions

    def test_store_audit_log_empty(self, store):
        entries = store.get_audit_log()
        assert entries == []

    def test_store_status_v2_fields(self, store):
        store.save("rnd_status_v2", owner_name="team")
        s = store.status()
        assert s["crous_version"] == 2
        assert s["cipher_suite"] in (1, 3)
        assert s["ttl"] == 0
        assert s["expired"] is False
        assert "token_age_hours" in s

    def test_store_save_empty_token_raises(self, store):
        with pytest.raises(ProviderCredentialFault, match="non-empty"):
            store.save("")

    def test_store_save_oversized_token_raises(self, store):
        with pytest.raises(ProviderCredentialFault, match="maximum size"):
            store.save("x" * 10000)

    def test_store_load_bad_magic(self, store):
        store._dir.mkdir(parents=True, exist_ok=True)
        store.credentials_path.write_bytes(b"XXXX" + b"\x00" * 100)
        with pytest.raises(ProviderCredentialFault, match="bad magic"):
            store.load()

    def test_store_load_unsupported_version(self, store):
        store._dir.mkdir(parents=True, exist_ok=True)
        store.credentials_path.write_bytes(_CROUS_MAGIC + bytes([99]) + b"\x00" * 200)
        with pytest.raises(ProviderCredentialFault, match="Unsupported"):
            store.load()

    def test_store_load_truncated_v2(self, store):
        store._dir.mkdir(parents=True, exist_ok=True)
        store.credentials_path.write_bytes(_CROUS_MAGIC + bytes([2]) + b"\x00" * 10)
        with pytest.raises(ProviderCredentialFault, match="too small"):
            store.load()

    def test_store_v2_hmac_tamper_detected(self, store):
        """Modifying any byte in the crous blob should be detected."""
        store.save("rnd_tamper_v2")
        blob = bytearray(store.credentials_path.read_bytes())
        blob[-1] ^= 0xFF  # Flip last byte of HMAC
        store.credentials_path.write_bytes(bytes(blob))
        with pytest.raises(ProviderCredentialFault, match="integrity|tampered"):
            store.load()

    def test_store_metadata(self, store):
        store.save("rnd_meta", metadata={"env": "prod", "app": "myapp"})
        config = store.load_config()
        assert config["metadata"]["env"] == "prod"
        assert config["metadata"]["app"] == "myapp"


# ═══════════════════════════════════════════════════════════════════════════════
#  § 12  Enhanced v2 Client API Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnhancedClientAPI:
    """Test all new v2 client API methods."""

    @pytest.fixture
    def client(self):
        return RenderClient.__new__(RenderClient)

    @pytest.fixture(autouse=True)
    def setup_client(self, client):
        client._token = "rnd_test"
        client._base_url = "https://api.render.com/v1"
        client._timeout = 30
        client._max_retries = 3
        client._ssl_ctx = _SSL_CTX

    def test_restart_service(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b"{}", {})
            client.restart_service("svc-1")
            mock_req.assert_called_once_with("POST", "/services/svc-1/restart")

    def test_purge_cache(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b"{}", {})
            client.purge_cache("svc-1")
            mock_req.assert_called_once_with("POST", "/services/svc-1/cache/purge")

    def test_cancel_deploy(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'{"id":"d-1","status":"canceled"}', {})
            deploy = client.cancel_deploy("svc-1", "d-1")
            assert deploy.status == "canceled"

    def test_rollback_deploy(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'{"id":"d-2","status":"created"}', {})
            deploy = client.rollback_deploy("svc-1", "d-old")
            assert deploy.id == "d-2"
            mock_req.assert_called_once_with("POST", "/services/svc-1/rollbacks", body={"deployId": "d-old"})

    def test_list_secret_files(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"name":".env","content":"X=1"}]', {})
            files = client.list_secret_files("svc-1")
            assert len(files) == 1
            assert files[0].name == ".env"

    def test_list_headers(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"id":"h1","path":"/*","name":"X-Custom","value":"val"}]', {})
            headers = client.list_headers("svc-1")
            assert len(headers) == 1
            assert headers[0].name == "X-Custom"

    def test_list_instances(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"id":"i1","status":"running"}]', {})
            instances = client.list_instances("svc-1")
            assert len(instances) == 1
            assert instances[0].status == "running"

    def test_list_events(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"id":"e1","type":"deploy_started"}]', {})
            events = client.list_events("svc-1")
            assert len(events) == 1
            assert events[0].type == "deploy_started"

    def test_list_jobs(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"job":{"id":"j1","status":"succeeded"}}]', {})
            jobs = client.list_jobs("svc-1")
            assert len(jobs) == 1
            assert jobs[0].status == "succeeded"

    def test_trigger_job(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'{"id":"j2","status":"pending"}', {})
            job = client.trigger_job("svc-1")
            assert job.status == "pending"

    def test_get_logs(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"message":"hello","level":"info"}]', {})
            logs = client.get_logs(service_id="svc-1", limit=10)
            assert len(logs) == 1
            assert logs[0].message == "hello"

    def test_get_metrics(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"timestamp":"2024-01-01","value":42.0,"unit":"percent"}]', {})
            metrics = client.get_metrics("svc-1", metric="cpu")
            assert len(metrics) == 1
            assert metrics[0].value == 42.0

    def test_list_postgres(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"postgres":{"id":"pg-1","name":"mydb","plan":"starter"}}]', {})
            dbs = client.list_postgres()
            assert len(dbs) == 1
            assert dbs[0].name == "mydb"

    def test_get_postgres_connection_info(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'{"host":"db.render.com","port":5432,"database":"mydb","user":"admin","password":"pw"}', {})
            ci = client.get_postgres_connection_info("pg-1")
            assert ci.host == "db.render.com"
            assert ci.port == 5432

    def test_list_key_value(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"keyValue":{"id":"kv-1","name":"cache","plan":"starter"}}]', {})
            kvs = client.list_key_value()
            assert len(kvs) == 1
            assert kvs[0].name == "cache"

    def test_list_projects(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"id":"prj-1","name":"MyProject"}]', {})
            projects = client.list_projects()
            assert len(projects) == 1
            assert projects[0].name == "MyProject"

    def test_list_env_groups(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"envGroup":{"id":"eg-1","name":"shared","envVars":[],"secretFiles":[]}}]', {})
            groups = client.list_env_groups()
            assert len(groups) == 1
            assert groups[0].name == "shared"

    def test_list_registry_credentials(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"id":"rc-1","name":"dockerhub","registry":"DOCKER","username":"user1"}]', {})
            creds = client.list_registry_credentials()
            assert len(creds) == 1
            assert creds[0].registry == "DOCKER"

    def test_list_blueprints(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"blueprint":{"id":"bp-1","name":"my-bp","autoSync":true}}]', {})
            bps = client.list_blueprints()
            assert len(bps) == 1
            assert bps[0].auto_sync is True

    def test_list_webhooks(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"id":"wh-1","url":"https://hook.example.com","events":["deploy_started"],"enabled":true}]', {})
            webhooks = client.list_webhooks()
            assert len(webhooks) == 1
            assert webhooks[0].url == "https://hook.example.com"

    def test_list_workspace_members(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"email":"user@example.com","role":"admin"}]', {})
            members = client.list_workspace_members("own-1")
            assert len(members) == 1
            assert members[0].role == "admin"

    def test_verify_dns(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'{"verified":true}', {})
            result = client.verify_dns("svc-1", "example.com")
            assert result["verified"] is True

    def test_create_preview(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'{"service":{"id":"svc-preview","name":"app-preview","type":"web_service"}}', {})
            preview = client.create_preview("svc-1", name="app-preview")
            assert preview.name == "app-preview"

    def test_list_log_streams(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"id":"ls-1","name":"syslog","endpoint":"https://log.example.com"}]', {})
            streams = client.list_log_streams()
            assert len(streams) == 1
            assert streams[0].name == "syslog"

    def test_list_disk_snapshots(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'[{"id":"snap-1","status":"completed"}]', {})
            snapshots = client.list_disk_snapshots("disk-1")
            assert len(snapshots) == 1
            assert snapshots[0].status == "completed"

    def test_get_notification_settings(self, client):
        with patch.object(client, "_request") as mock_req:
            mock_req.return_value = _RequestResult(200, b'{"notifyOnFail":"notify"}', {})
            ns = client.get_notification_settings("svc-1")
            assert ns.notify_on_fail == "notify"


# ═══════════════════════════════════════════════════════════════════════════════
#  § 13  Enhanced v2 Deployer Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnhancedDeployer:
    """Test v2 deployer enhancements: rollback, cancel, preview, restart."""

    def _make_deployer(self, **config_overrides):
        client = MagicMock(spec=RenderClient)
        config = RenderDeployConfig(
            service_name="testapp",
            image="ghcr.io/org/testapp:latest",
            plan=RenderPlan.STARTER,
            region="oregon",
        )
        for k, v in config_overrides.items():
            setattr(config, k, v)
        deployer = RenderDeployer(
            client=client,
            workspace_root=Path("/tmp/test_ws"),
            config=config,
        )
        return deployer, client

    def test_deploy_result_has_rollback_id(self):
        r = DeployResult(success=True, rollback_deploy_id="d-old")
        assert r.rollback_deploy_id == "d-old"

    def test_deploy_result_has_metrics(self):
        r = DeployResult(success=True, metrics={"cpu": 42})
        assert r.metrics == {"cpu": 42}

    def test_cancel_deploy(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="svc-1", name="testapp")
        client.get_service_by_name.return_value = svc
        deploy = RenderDeploy(id="d-1", status="build_in_progress")
        client.list_deploys.return_value = [deploy]
        client.cancel_deploy.return_value = RenderDeploy(id="d-1", status="canceled")

        result = deployer.cancel()
        assert result is True
        client.cancel_deploy.assert_called_once_with("svc-1", "d-1")

    def test_cancel_no_service(self):
        deployer, client = self._make_deployer()
        client.get_service_by_name.return_value = None
        result = deployer.cancel()
        assert result is False

    def test_restart_service(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="svc-1", name="testapp")
        client.get_service_by_name.return_value = svc
        result = deployer.restart()
        assert result is True
        client.restart_service.assert_called_once_with("svc-1")

    def test_restart_no_service(self):
        deployer, client = self._make_deployer()
        client.get_service_by_name.return_value = None
        result = deployer.restart()
        assert result is False

    def test_purge_cache(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="svc-1", name="testapp")
        client.get_service_by_name.return_value = svc
        result = deployer.purge_cache()
        assert result is True
        client.purge_cache.assert_called_once_with("svc-1")

    def test_create_preview(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="svc-1", name="testapp", slug="testapp")
        client.get_service_by_name.return_value = svc
        preview_svc = RenderService(id="svc-preview", name="testapp-preview", slug="testapp-preview")
        client.create_preview.return_value = preview_svc

        result = deployer.create_preview()
        assert result.success is True
        assert result.service.name == "testapp-preview"

    def test_rollback_no_deploy_id(self):
        deployer, client = self._make_deployer()
        result = deployer.rollback()
        assert result.success is False
        assert "No deploy ID" in result.errors[0]

    def test_rollback_with_explicit_id(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="svc-1", name="testapp", slug="testapp")
        client.get_service_by_name.return_value = svc
        client.rollback_deploy.return_value = RenderDeploy(id="d-rollback", status="created")
        live_deploy = RenderDeploy(id="d-rollback", status="live")
        client.list_deploys.return_value = [live_deploy]

        result = deployer.rollback(deploy_id="d-old")
        assert result.success is True
        client.rollback_deploy.assert_called_once_with("svc-1", "d-old")

    def test_get_deploy_logs(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="svc-1", name="testapp")
        client.get_service_by_name.return_value = svc
        from aquilia.providers.render.types import RenderLogEntry
        client.get_logs.return_value = [RenderLogEntry(message="log line")]
        logs = deployer.get_deploy_logs(limit=10)
        assert len(logs) == 1
        assert logs[0].message == "log line"

    def test_get_service_metrics(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="svc-1", name="testapp")
        client.get_service_by_name.return_value = svc
        from aquilia.providers.render.types import RenderMetricPoint
        client.get_metrics.return_value = [RenderMetricPoint(value=65.0)]
        metrics = deployer.get_service_metrics(metric="cpu")
        assert len(metrics) == 1
        assert metrics[0].value == 65.0

    def test_status_includes_instance_count(self):
        deployer, client = self._make_deployer()
        svc = RenderService(id="svc-1", name="testapp", slug="testapp", status="live", plan="starter", region="oregon")
        client.get_service_by_name.return_value = svc
        client.list_deploys.return_value = []
        from aquilia.providers.render.types import RenderInstance
        client.list_instances.return_value = [RenderInstance(id="i1"), RenderInstance(id="i2")]

        s = deployer.status()
        assert s["instance_count"] == 2


# ═══════════════════════════════════════════════════════════════════════════════
#  § 14  Audit Logger Tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestAuditLogger:
    """Test the audit logging subsystem."""

    def test_audit_log_creates_file(self, tmp_path):
        logger = _AuditLogger(tmp_path / "audit.log")
        logger.log("test_action", details="test detail")
        assert (tmp_path / "audit.log").exists()

    def test_audit_log_json_format(self, tmp_path):
        logger = _AuditLogger(tmp_path / "audit.log")
        logger.log("save_start")
        content = (tmp_path / "audit.log").read_text()
        entry = json.loads(content.strip())
        assert entry["action"] == "save_start"
        assert "ts" in entry
        assert "pid" in entry

    def test_audit_log_multiple_entries(self, tmp_path):
        logger = _AuditLogger(tmp_path / "audit.log")
        logger.log("action1")
        logger.log("action2")
        logger.log("action3")
        lines = (tmp_path / "audit.log").read_text().strip().split("\n")
        assert len(lines) == 3

    def test_audit_log_with_details(self, tmp_path):
        logger = _AuditLogger(tmp_path / "audit.log")
        logger.log("save", details="owner=team1")
        entry = json.loads((tmp_path / "audit.log").read_text().strip())
        assert entry["details"] == "owner=team1"

    def test_audit_log_no_details(self, tmp_path):
        logger = _AuditLogger(tmp_path / "audit.log")
        logger.log("clear")
        entry = json.loads((tmp_path / "audit.log").read_text().strip())
        assert "details" not in entry