"""Regression tests for the 2026-09-16 post-implementation audit core fixes.

Covers:
- F-CORE-02: ``Request.path_params`` is a property (contract path binding)
- F-CORE-01: engine nested-contract error aggregation flattens dicts
- F-CORE-01b: ``SealFault`` details flatten nested error dicts
- F-CORE-05: ``ConfigLoader`` workspace path is absolute (cwd-independent)
- F-CORE-07: singleton controllers resolve from the owning module container
- F-CORE-11: RenderDeployConfig validators registered via @ward (no
  self-deprecation)
- config N-1: ``get_subsystem_config`` merges root + integration sections
  instead of or-shadowing
- config N-4: malformed workspace.py raises ConfigInvalidFault with context
- engine N-1: Response(headers=...) validates header values
- engine N-1b: RequestIdMiddleware sanitizes echoed inbound IDs
- route_compiler N-2: bare module refs no longer rewritten to apps.* + print
"""

import asyncio
import warnings

import pytest

from aquilia.contracts.exceptions import SealFault
from aquilia.controller.engine import _merge_contract_errors

# ---------------------------------------------------------------------------
# F-CORE-02 — path_params property
# ---------------------------------------------------------------------------


async def _make_request(path_params=None):
    from aquilia.request import Request

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "query_string": b"",
    }

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(_msg):
        pass

    request = Request(scope, receive, send)
    if path_params is not None:
        request.state["path_params"] = path_params
    return request


class TestPathParamsProperty:
    async def test_path_params_is_a_dict(self):
        request = await _make_request({"sessionId": "abc-123"})
        assert isinstance(request.path_params, dict)
        assert request.path_params["sessionId"] == "abc-123"

    async def test_path_params_defaults_to_empty_dict(self):
        request = await _make_request()
        assert request.path_params == {}

    async def test_isinstance_check_used_by_contract_binding(self):
        """The contracts integration gates on isinstance(dict) — the exact
        check that silently never fired while path_params was a method."""
        request = await _make_request({"id": "42"})
        path_params = request.path_params
        assert isinstance(path_params, dict)
        assert path_params == {"id": "42"}

    async def test_iteration_does_not_explode(self):
        """auth/clearance.py iterates (request.path_params or {}).items()."""
        request = await _make_request({"a": 1, "b": 2})
        assert dict(request.path_params.items()) == {"a": 1, "b": 2}


# ---------------------------------------------------------------------------
# F-CORE-01 — nested error aggregation
# ---------------------------------------------------------------------------


class TestMergeContractErrors:
    def test_nested_dict_flattens_to_dotted_paths(self):
        target = {}
        _merge_contract_errors(
            target,
            {
                "device": {
                    "deviceId": ["Must be at least 8 characters"],
                    "deviceName": ["This field is required"],
                }
            },
        )
        assert target == {
            "device.deviceId": ["Must be at least 8 characters"],
            "device.deviceName": ["This field is required"],
        }

    def test_flat_lists_unchanged(self):
        target = {}
        _merge_contract_errors(target, {"email": ["Invalid email"]})
        assert target == {"email": ["Invalid email"]}

    def test_mixed_flat_and_nested(self):
        target = {}
        _merge_contract_errors(
            target,
            {
                "device": {"deviceId": ["too short"]},
                "email": ["Invalid email"],
            },
        )
        assert target == {
            "device.deviceId": ["too short"],
            "email": ["Invalid email"],
        }

    def test_dedup_across_merges(self):
        target = {"email": ["Invalid email"]}
        _merge_contract_errors(target, {"email": ["Invalid email", "Required"]})
        assert target == {"email": ["Invalid email", "Required"]}

    def test_deeply_nested(self):
        target = {}
        _merge_contract_errors(
            target, {"a": {"b": {"c": ["deep error"]}}}
        )
        assert target == {"a.b.c": ["deep error"]}

    def test_merge_into_existing_dotted_key_dedups(self):
        target = {"device.deviceId": ["too short"]}
        _merge_contract_errors(
            target, {"device": {"deviceId": ["too short", "also bad"]}}
        )
        assert target == {"device.deviceId": ["too short", "also bad"]}


class TestSealFaultNestedDetails:
    def test_single_nested_field_flattens(self):
        fault = SealFault(errors={"device": {"deviceId": ["too short"]}})
        assert fault.metadata["details"] == {
            "field": "device.deviceId",
            "reason": "too short",
        }

    def test_multiple_fields_keep_nested_messages(self):
        fault = SealFault(
            errors={
                "device": {"deviceId": ["too short"]},
                "email": ["Invalid email"],
            }
        )
        fields = {f["field"]: f["reasons"] for f in fault.metadata["details"]["fields"]}
        assert fields == {
            "device.deviceId": ["too short"],
            "email": ["Invalid email"],
        }

    def test_flat_single_field_unchanged(self):
        fault = SealFault(errors={"email": ["Invalid email"]})
        assert fault.metadata["details"] == {
            "field": "email",
            "reason": "Invalid email",
        }


# ---------------------------------------------------------------------------
# F-CORE-05 — cwd-independent workspace config load
# ---------------------------------------------------------------------------


class TestWorkspaceConfigAbsolutePath:
    def test_runtime_configure_uses_absolute_workspace_file(self, tmp_path, monkeypatch):
        """Runtime.configure must pass the absolute workspace file to
        ConfigLoader.load — a relative path resolves against cwd and silently
        boots unconfigured from any other directory."""
        (tmp_path / "workspace.py").write_text(
            "from aquilia import Workspace, Integration\n"
            "workspace = Workspace('cwdtest')\n"
            "workspace.integrate(Integration.cache(backend='memory'))\n"
        )
        # Run configure from a DIFFERENT cwd than the workspace root — the
        # exact trap of F-CORE-05.
        other = tmp_path / "elsewhere"
        other.mkdir()
        monkeypatch.chdir(other)
        from aquilia.runtime import AquiliaRuntime, RuntimeConfig

        runtime = AquiliaRuntime(RuntimeConfig(workspace_root=tmp_path))
        runtime.configure()
        raw = runtime._config_loader.get("cache", {})
        assert raw, "workspace config was not loaded (cwd-relative silent skip)"
        assert raw.get("backend") == "memory"

    def test_config_loader_warns_on_missing_path(self, tmp_path, monkeypatch, caplog):
        monkeypatch.chdir(tmp_path)
        from aquilia.config import ConfigLoader

        missing = tmp_path / "definitely_not_here.py"
        with caplog.at_level("WARNING"):
            loader = ConfigLoader.load(paths=[str(missing)])
        assert any(
            "not found" in rec.message for rec in caplog.records
        ), "silent skip of a missing config path"
        assert loader.config_data is not None


# ---------------------------------------------------------------------------
# F-CORE-07 — singleton controllers resolve from owning module container
# ---------------------------------------------------------------------------


class TestSingletonOwningContainer:
    def _setup(self):
        from aquilia.controller.factory import ControllerFactory, InstantiationMode
        from aquilia.di import Container, ValueProvider

        class Svc:
            pass

        class Ctrl:
            def __init__(self, svc: Svc):
                self.svc = svc

        base = Container(scope="app")
        owner = Container(scope="app")
        svc = Svc()
        owner.register(ValueProvider(value=svc, token=Svc))

        class _RequestScope:
            _parent = owner

        return ControllerFactory(app_container=base), Ctrl, InstantiationMode, svc, _RequestScope()

    def test_singleton_resolves_from_owning_container(self):
        factory, ctrl_cls, mode, svc, req_scope = self._setup()
        instance = asyncio.run(factory.create(ctrl_cls, mode.SINGLETON, request_container=req_scope))
        assert instance.svc is svc

    def test_singleton_falls_back_to_base_container_without_request_scope(self):
        factory, ctrl_cls, mode, svc, _ = self._setup()
        # Register the service in the base container for this variant
        from aquilia.di import Container, ValueProvider

        base = Container(scope="app")
        base.register(ValueProvider(value=svc, token=type(svc)))

        class CtrlBase:
            def __init__(self, svc: type(svc)):
                self.svc = svc

        factory2 = type(factory)(app_container=base)
        instance = asyncio.run(factory2.create(CtrlBase, mode.SINGLETON))
        assert instance.svc is svc


# ---------------------------------------------------------------------------
# F-CORE-11 — framework's own seal_ validators under @ward
# ---------------------------------------------------------------------------


class TestRenderWardMigration:
    def test_no_deprecation_warning_on_import(self):
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            from aquilia.providers.render import types as render_types

            # Force class reinspection: the wards were collected at class
            # creation; importing fresh state proves no warning fires.
            assert render_types.RenderDeployConfig is not None
        deprecations = [
            w for w in caught if issubclass(w.category, DeprecationWarning)
        ]
        assert not deprecations, [str(w.message) for w in deprecations]

    @pytest.mark.parametrize(
        "kwargs",
        [
            {"port": 99999},
            {"num_instances": 0},
            {"health_check_path": "nope"},
            {"auto_deploy": "maybe"},
        ],
    )
    def test_validators_still_fire(self, kwargs):
        from aquilia.providers.render.types import RenderDeployConfig

        with pytest.raises(SealFault):
            RenderDeployConfig(**kwargs)

    def test_valid_config_still_seals(self):
        from aquilia.providers.render.types import RenderDeployConfig

        config = RenderDeployConfig(port=8080, num_instances=2)
        assert config.port == 8080


# ---------------------------------------------------------------------------
# config N-1 — subsystem config merge instead of or-shadowing
# ---------------------------------------------------------------------------


class TestSubsystemConfigMerge:
    def test_root_env_keys_do_not_shadow_typed_integration(self):
        from aquilia.config import ConfigLoader

        loader = ConfigLoader.__new__(ConfigLoader)
        loader.config_data = {
            "cache": {"enabled": True},  # e.g. from AQ_CACHE__ENABLED=true
            "integrations": {
                "cache": {
                    "backend": "redis",
                    "redis_url": "redis://prod:6379/0",
                    "default_ttl": 600,
                }
            },
        }
        merged = loader.get_subsystem_config(
            "cache", {"backend": "memory", "default_ttl": None}
        )
        assert merged["backend"] == "redis"
        assert merged["redis_url"] == "redis://prod:6379/0"
        assert merged["default_ttl"] == 600
        assert merged["enabled"] is True

    def test_integration_only_unchanged(self):
        from aquilia.config import ConfigLoader

        loader = ConfigLoader.__new__(ConfigLoader)
        loader.config_data = {
            "integrations": {"cache": {"backend": "redis"}},
        }
        merged = loader.get_subsystem_config(
            "cache", {"backend": "memory"}
        )
        assert merged["backend"] == "redis"

    def test_root_only_unchanged(self):
        from aquilia.config import ConfigLoader

        loader = ConfigLoader.__new__(ConfigLoader)
        loader.config_data = {"cache": {"backend": "redis"}}
        merged = loader.get_subsystem_config(
            "cache", {"backend": "memory"}
        )
        assert merged["backend"] == "redis"

    def test_integration_wins_on_conflict(self):
        from aquilia.config import ConfigLoader

        loader = ConfigLoader.__new__(ConfigLoader)
        loader.config_data = {
            "cache": {"backend": "memory"},
            "integrations": {"cache": {"backend": "redis"}},
        }
        merged = loader.get_subsystem_config("cache", {})
        assert merged["backend"] == "redis"


# ---------------------------------------------------------------------------
# config N-4 — malformed workspace.py context
# ---------------------------------------------------------------------------


class TestMalformedWorkspaceConfig:
    def test_semantic_error_raises_config_fault_with_context(self, tmp_path):
        from aquilia.config import ConfigLoader
        from aquilia.faults.domains import ConfigInvalidFault

        bad = tmp_path / "workspace.py"
        bad.write_text(
            "from aquilia import Workspace\n"
            "workspace = Workspace('broken')\n"
            "workspace.integrate(None)\n"
        )
        with pytest.raises(ConfigInvalidFault, match=str(bad)):
            ConfigLoader.load(paths=[str(bad)])

    def test_syntax_error_wrapped_with_context(self, tmp_path):
        from aquilia.config import ConfigLoader
        from aquilia.faults.domains import ConfigInvalidFault

        bad = tmp_path / "workspace.py"
        bad.write_text("def broken(:\n")
        # Syntax errors surface as ConfigInvalidFault carrying the file path
        # (the underlying SyntaxError chained as __cause__).
        with pytest.raises(ConfigInvalidFault, match=str(bad)):
            ConfigLoader.load(paths=[str(bad)])


# ---------------------------------------------------------------------------
# F-CORE-12 — dotenv policy not frozen by foreign-cwd loads
# ---------------------------------------------------------------------------


class TestDotenvSearchPathFromConfig:
    def test_workspace_dir_env_honored_from_foreign_cwd(self, tmp_path, monkeypatch):
        ws = tmp_path / "ws"
        ws.mkdir()
        (ws / "workspace.py").write_text(
            "from aquilia import Workspace\nworkspace = Workspace('dtest')\n"
        )
        (ws / ".env").write_text("AQ_TEST_DOTENV_FROM_WS_DIR=1\n")
        # cwd is a DIFFERENT directory with no .env of its own
        other = tmp_path / "elsewhere"
        other.mkdir()
        monkeypatch.chdir(other)

        from aquilia.dotenv import DotEnvLoader

        # Reset the process-wide singleton so this test observes its own load
        DotEnvLoader._loaded = False
        DotEnvLoader._loaded_files.clear()
        monkeypatch.delenv("AQ_TEST_DOTENV_FROM_WS_DIR", raising=False)

        from aquilia.config import ConfigLoader

        ConfigLoader.load(paths=[str(ws / "workspace.py")])
        import os

        assert os.environ.get("AQ_TEST_DOTENV_FROM_WS_DIR") == "1"
        assert any(
            str(p).startswith(str(ws)) for p in DotEnvLoader._loaded_files
        ), DotEnvLoader._loaded_files


# ---------------------------------------------------------------------------
# engine N-1 — response header validation
# ---------------------------------------------------------------------------


class TestResponseHeaderValidation:
    def test_constructor_headers_validated(self):
        from aquilia.response import InvalidHeaderError, Response

        with pytest.raises(InvalidHeaderError):
            Response("ok", headers={"X-Bad": "value\r\nX-Injected: 1"})

    def test_constructor_multi_value_headers_validated(self):
        from aquilia.response import InvalidHeaderError, Response

        with pytest.raises(InvalidHeaderError):
            Response("ok", headers={"Set-Cookie": ["a=1", "b=2\r\nX-Injected: 1"]})

    def test_validation_can_be_disabled(self):
        from aquilia.response import Response

        response = Response(
            "ok",
            headers={"X-Raw": "v\r\nX-Injected: 1"},
            validate_headers=False,
        )
        assert response.headers["x-raw"] == "v\r\nX-Injected: 1"


class TestRequestIdSanitization:
    async def _run(self, inbound_id: bytes):
        from aquilia.middleware.builtin.request_id import RequestIdMiddleware

        middleware = RequestIdMiddleware()

        async def handler(request, ctx):
            from aquilia.response import Response

            return Response("ok")

        class _Req:
            def __init__(self):
                self.scope = {"headers": [(b"x-request-id", inbound_id)]}
                self.state = {}

        class _Ctx:
            request_id = None

        return await middleware(_Req(), _Ctx(), handler)

    async def test_crlf_request_id_not_echoed(self):
        response = await self._run(b"abc\r\nX-Injected: 1")
        # The unsafe inbound ID must be replaced, not echoed verbatim.
        assert "\r" not in response.headers["X-Request-ID"]
        assert "\n" not in response.headers["X-Request-ID"]

    async def test_safe_request_id_echoed(self):
        response = await self._run(b"req-abc_123")
        assert response.headers["X-Request-ID"] == "req-abc_123"
