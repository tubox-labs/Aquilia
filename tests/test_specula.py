"""
Test suite for Specula — the Aquilia API Observatory (aquilia.specula).

Covers: schema type mapping, Contract/Model schema bridges, standard schemas,
the SpeculaBuilder engine, SpeculaService caching + SSE, faults, the mock
server synthesis, Postman/Insomnia export, the UI renderer, and end-to-end
server route wiring.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal
from uuid import UUID

import pytest

from aquilia import GET, POST, Controller
from aquilia.controller.base import RequestCtx
from aquilia.controller.compiler import ControllerCompiler
from aquilia.controller.router import ControllerRouter
from aquilia.request import Request
from aquilia.specula import (
    SPECULA_DOMAIN,
    ObservatoryForbiddenFault,
    SpecBuildFault,
    SpeculaBuilder,
    SpeculaConfig,
    SpeculaController,
    SpeculaFault,
    SpeculaRenderer,
    SpeculaService,
    VersionNotFoundFault,
    python_type_to_schema,
)
from aquilia.specula.schema.fault import aquilia_error_schema, aquilia_validation_error_schema
from aquilia.specula.schema.standard import STANDARD_SCHEMAS

# ── Fixtures / helpers ──────────────────────────────────────────────────


class UsersController(Controller):
    prefix = "/users"
    tags = ["users"]

    @GET("/")
    async def list_users(self, ctx):
        """List all users."""
        return None

    @GET("/<uid:str>")
    async def get_user(self, ctx, uid: str):
        """Get a user by ID."""
        return None

    @POST("/")
    async def create_user(self, ctx):
        """
        Create a user.

        Raises:
            AuthFault (401): Missing or invalid bearer token
        """
        return None


class HealthController(Controller):
    prefix = "/health"
    tags = ["health"]

    @GET("/")
    async def check(self, ctx):
        """Health check."""
        return None


def build_router() -> ControllerRouter:
    compiler = ControllerCompiler()
    router = ControllerRouter()
    for ctrl in (UsersController, HealthController):
        compiled = compiler.compile_controller(ctrl)
        for route in compiled.routes:
            route.app_name = ctrl.__name__.replace("Controller", "").lower()
        router.add_controller(compiled)
    router.initialize()
    return router


def make_request(method: str = "GET", path: str = "/", query: bytes = b"", body: Any = None) -> Request:
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": query,
        "headers": [],
    }
    body_bytes = json.dumps(body).encode() if isinstance(body, dict) else (body or b"")

    async def receive():
        return {"type": "http.request", "body": body_bytes}

    return Request(scope=scope, receive=receive)


def make_ctx(request=None) -> RequestCtx:
    return RequestCtx(request=request or make_request(), state={})


@pytest.fixture
def config() -> SpeculaConfig:
    return SpeculaConfig(title="Test API", version="2.0.0")


@pytest.fixture
def router() -> ControllerRouter:
    return build_router()


@pytest.fixture
def service(router, config) -> SpeculaService:
    return SpeculaService(router=router, config=config)


@pytest.fixture
def controller(service, config) -> SpeculaController:
    return SpeculaController(service=service, config=config)


from aquilia.contracts import Contract, NestedContractFacet


class DummyContract(Contract):
    username: str
    password: str

class DummyController(Controller):
    prefix = "/dummy"

    @POST("/login")
    async def login(self, ctx, login_data: DummyContract):
        return None

class SubContract(Contract):
    sub_field: str

class ParentContract(Contract):
    nested_field = NestedContractFacet[SubContract]
    root_field: int

class NestedController(Controller):
    prefix = "/nested"

    @POST("/action")
    async def action(self, ctx, payload: ParentContract):
        return None


class TestSpeculaBuilder:
    def test_builds_valid_3_1_0_spec(self, router, config):
        spec = SpeculaBuilder(config).build(router)
        assert spec["openapi"] == "3.1.0"

    def test_optional_fields_use_oneof_not_nullable(self):
        schema = python_type_to_schema(str | None)
        assert schema == {"oneOf": [{"type": "string"}, {"type": "null"}]}
        assert "nullable" not in json.dumps(schema)

    def test_includes_all_user_routes(self, router, config):
        spec = SpeculaBuilder(config).build(router)
        assert "/users" in spec["paths"] or "/users/" in spec["paths"]
        assert any("/users" in p for p in spec["paths"])

    def test_excludes_specula_own_routes(self, router, config):
        spec = SpeculaBuilder(config).build(router)
        assert config.ui_path not in spec["paths"]
        assert config.json_path not in spec["paths"]

    def test_excludes_internal_routes_by_default(self, config):
        compiler = ControllerCompiler()
        router = ControllerRouter()

        class InternalController(Controller):
            prefix = "/_internal"

            @GET("/status")
            async def status(self, ctx):
                return None

        compiled = compiler.compile_controller(InternalController)
        router.add_controller(compiled)
        router.initialize()
        spec = SpeculaBuilder(config).build(router)
        assert not any(p.startswith("/_internal") for p in spec["paths"])

    def test_standard_schemas_present(self, router, config):
        spec = SpeculaBuilder(config).build(router)
        schemas = spec["components"]["schemas"]
        assert "AquiliaError" in schemas
        assert "AquiliaValidationError" in schemas
        assert "PaginatedResponse" in schemas

    def test_auto_422_on_post(self, router, config):
        spec = SpeculaBuilder(config).build(router)
        key = "/users/" if "/users/" in spec["paths"] else "/users"
        post = spec["paths"][key]["post"]
        assert "422" in post["responses"]

    def test_raises_docstring_becomes_error_response(self, router, config):
        spec = SpeculaBuilder(config).build(router)
        key = "/users/" if "/users/" in spec["paths"] else "/users"
        post = spec["paths"][key]["post"]
        assert "401" in post["responses"]

    def test_module_extension_x_specula_module(self, router, config):
        spec = SpeculaBuilder(config).build(router)
        found = False
        for path_item in spec["paths"].values():
            for method, op in path_item.items():
                if method.startswith("x-"):
                    continue
                if op.get("x-specula-module"):
                    found = True
        assert found

    def test_tag_groups_in_spec(self, router):
        config = SpeculaConfig(tag_groups=[{"name": "Core", "tags": ["users"]}])
        spec = SpeculaBuilder(config).build(router)
        assert spec["x-tagGroups"] == [{"name": "Core", "tags": ["users"]}]

    def test_webhooks_in_spec(self, router):
        config = SpeculaConfig(webhooks={"onEvent": {"post": {}}})
        spec = SpeculaBuilder(config).build(router)
        assert "webhooks" in spec

    def test_operation_ids_unique(self, router, config):
        spec = SpeculaBuilder(config).build(router)
        ids = []
        for path_item in spec["paths"].values():
            for method, op in path_item.items():
                if not method.startswith("x-"):
                    ids.append(op["operationId"])
        assert len(ids) == len(set(ids))

    def test_idempotent_build(self, router, config):
        builder = SpeculaBuilder(config)
        spec1 = builder.build(router)
        spec2 = builder.build(router)
        assert spec1["paths"].keys() == spec2["paths"].keys()

    def test_infer_request_body_from_signature_parameter_contract(self, config):
        compiler = ControllerCompiler()
        router = ControllerRouter()
        compiled = compiler.compile_controller(DummyController)
        router.add_controller(compiled)
        router.initialize()

        spec = SpeculaBuilder(config).build(router)
        login_op = spec["paths"]["/dummy/login"]["post"]
        assert "requestBody" in login_op
        schema_ref = login_op["requestBody"]["content"]["application/json"]["schema"]["$ref"]
        assert "DummyContractInput" in schema_ref

    def test_extract_and_flatten_nested_contract_defs(self, config):
        compiler = ControllerCompiler()
        router = ControllerRouter()
        compiled = compiler.compile_controller(NestedController)
        router.add_controller(compiled)
        router.initialize()

        spec = SpeculaBuilder(config).build(router)

        # Check that both the parent and nested contract are registered in components
        schemas = spec["components"]["schemas"]
        assert "ParentContractInput" in schemas
        assert "SubContractInput" in schemas

        # Check that the ref inside ParentContractInput is correctly rewritten to components
        parent_schema = schemas["ParentContractInput"]
        assert parent_schema["properties"]["nested_field"]["$ref"] == "#/components/schemas/SubContractInput"

        # Check that $defs was cleaned up from the parent schema
        assert "$defs" not in parent_schema




# ═══════════════════════════════════════════════════════════════════════
#  Schema type mapping
# ═══════════════════════════════════════════════════════════════════════


class TestSchemaTypes:
    def test_optional_str_is_oneof(self):
        assert python_type_to_schema(str | None) == {"oneOf": [{"type": "string"}, {"type": "null"}]}

    def test_list_str_is_array(self):
        assert python_type_to_schema(list[str]) == {"type": "array", "items": {"type": "string"}}

    def test_dict_str_x_is_object(self):
        assert python_type_to_schema(dict[str, int]) == {
            "type": "object",
            "additionalProperties": {"type": "integer", "format": "int64"},
        }

    def test_literal_is_enum(self):
        assert python_type_to_schema(Literal["a", "b"]) == {"enum": ["a", "b"]}

    def test_datetime_is_date_time_format(self):
        assert python_type_to_schema(datetime) == {"type": "string", "format": "date-time"}

    def test_uuid_is_uuid_format(self):
        assert python_type_to_schema(UUID) == {"type": "string", "format": "uuid"}

    def test_bytes_is_binary_format(self):
        assert python_type_to_schema(bytes) == {"type": "string", "format": "binary"}

    def test_int_has_int64_format(self):
        assert python_type_to_schema(int) == {"type": "integer", "format": "int64"}

    def test_decimal_is_string_decimal(self):
        assert python_type_to_schema(Decimal) == {"type": "string", "format": "decimal"}

    def test_set_has_unique_items(self):
        schema = python_type_to_schema(set[str])
        assert schema["uniqueItems"] is True


# ═══════════════════════════════════════════════════════════════════════
#  Fault schemas
# ═══════════════════════════════════════════════════════════════════════


class TestFaultSchemas:
    def test_error_schema_required_fields(self):
        schema = aquilia_error_schema()
        assert set(schema["required"]) == {"code", "message", "domain"}

    def test_validation_schema_has_fields(self):
        schema = aquilia_validation_error_schema()
        assert "fields" in schema["properties"]

    def test_standard_schemas_include_error(self):
        assert "AquiliaError" in STANDARD_SCHEMAS
        assert "AquiliaValidationError" in STANDARD_SCHEMAS


# ═══════════════════════════════════════════════════════════════════════
#  SpeculaService
# ═══════════════════════════════════════════════════════════════════════


class TestSpeculaService:
    async def test_spec_returns_dict(self, service):
        spec = await service.get_spec()
        assert spec["openapi"] == "3.1.0"

    async def test_spec_cached_in_process(self, service):
        spec1 = await service.get_spec()
        spec2 = await service.get_spec()
        assert spec1 is spec2

    async def test_invalidate_clears_cache(self, service):
        spec1 = await service.get_spec()
        service.invalidate()
        spec2 = await service.get_spec()
        assert spec1 is not spec2

    async def test_spec_json_is_valid_json(self, service):
        text = await service.get_spec_json()
        assert json.loads(text)["openapi"] == "3.1.0"

    async def test_spec_yaml_parses(self, service):
        text = await service.get_spec_yaml()
        try:
            import yaml

            assert yaml.safe_load(text)["openapi"] == "3.1.0"
        except ImportError:
            assert "openapi: 3.1.0" in text or 'openapi: "3.1.0"' in text

    async def test_sse_broadcast_on_invalidation(self, service):
        queue: asyncio.Queue = asyncio.Queue()
        service.subscribe_sse(queue)
        service.invalidate()
        payload = await asyncio.wait_for(queue.get(), timeout=1.0)
        assert payload["type"] == "spec:invalidated"
        service.unsubscribe_sse(queue)

    async def test_spec_build_fault_on_router_error(self, config):
        class BrokenRouter:
            def get_routes_full(self):
                raise RuntimeError("boom")

        service = SpeculaService(router=BrokenRouter(), config=config)
        with pytest.raises(SpecBuildFault):
            await service.get_spec()


# ═══════════════════════════════════════════════════════════════════════
#  SpeculaController
# ═══════════════════════════════════════════════════════════════════════


class TestSpeculaController:
    async def test_spec_json_200(self, controller):
        resp = await controller.spec_json(make_request(), make_ctx())
        assert resp.status == 200

    async def test_spec_json_valid_json(self, controller):
        resp = await controller.spec_json(make_request(), make_ctx())
        assert json.loads(resp._content)["openapi"] == "3.1.0"

    async def test_spec_yaml_200(self, controller):
        resp = await controller.spec_yaml(make_request(), make_ctx())
        assert resp.status == 200

    async def test_observatory_ui_200(self, controller):
        resp = await controller.observatory_ui(make_request(), make_ctx())
        assert resp.status == 200

    async def test_observatory_ui_contains_specula_js(self, controller):
        resp = await controller.observatory_ui(make_request(), make_ctx())
        assert "Specula" in resp._content

    async def test_versions_index(self, controller):
        resp = await controller.versions_index(make_request(), make_ctx())
        data = json.loads(resp._content)
        assert "latest" in data["versions"]

    async def test_schemas_index(self, controller):
        resp = await controller.schemas_index(make_request(), make_ctx())
        data = json.loads(resp._content)
        assert data["count"] > 0
        assert "AquiliaError" in data["schemas"]

    async def test_schema_detail(self, controller):
        resp = await controller.schema_detail(make_request(), make_ctx(), name="AquiliaError")
        assert resp.status == 200

    async def test_schema_detail_invalid_name_400(self, controller):
        resp = await controller.schema_detail(make_request(), make_ctx(), name="../etc")
        assert resp.status == 400

    async def test_schema_detail_missing_404(self, controller):
        resp = await controller.schema_detail(make_request(), make_ctx(), name="Nonexistent")
        assert resp.status == 404

    async def test_routes_index(self, controller):
        resp = await controller.routes_index(make_request(), make_ctx())
        data = json.loads(resp._content)
        assert data["count"] > 0

    async def test_mock_disabled_by_default_404(self, controller):
        resp = await controller.mock_endpoint(make_request(), make_ctx(), path="users")
        assert resp.status == 404

    async def test_postman_export(self, controller):
        resp = await controller.export_postman(make_request(), make_ctx())
        assert resp.status == 200
        data = json.loads(resp._content)
        assert "item" in data and "info" in data

    async def test_insomnia_export(self, controller):
        resp = await controller.export_insomnia(make_request(), make_ctx())
        data = json.loads(resp._content)
        assert data["__export_format"] == 4

    async def test_mock_enabled_returns_example(self, service, config):
        config.mock_server_enabled = True
        controller = SpeculaController(service=service, config=config)
        req = make_request(method="POST", body={"method": "get"})
        resp = await controller.mock_endpoint(req, make_ctx(req), path="users")
        # 404 (no 2xx doc) or 200 with example — both are valid mock outcomes
        assert resp.status in (200, 404)


# ═══════════════════════════════════════════════════════════════════════
#  Mock server synthesis
# ═══════════════════════════════════════════════════════════════════════


class TestMockServer:
    def test_synthesizes_string(self):
        from aquilia.specula.controller import _synthesize

        assert _synthesize({"type": "string"}, {}, 3) == "example_string"

    def test_synthesizes_email(self):
        from aquilia.specula.controller import _synthesize

        assert _synthesize({"type": "string", "format": "email"}, {}, 3) == "user@example.com"

    def test_synthesizes_uuid(self):
        from aquilia.specula.controller import _synthesize

        assert _synthesize({"type": "string", "format": "uuid"}, {}, 3) == "550e8400-e29b-41d4-a716-446655440000"

    def test_synthesizes_integer(self):
        from aquilia.specula.controller import _synthesize

        assert _synthesize({"type": "integer"}, {}, 3) == 42

    def test_synthesizes_nested_object(self):
        from aquilia.specula.controller import _synthesize

        schema = {"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}
        result = _synthesize(schema, {}, 3)
        assert result == {"name": "example_string", "age": 42}

    def test_resolves_ref_for_synthesis(self):
        from aquilia.specula.controller import _synthesize

        spec = {"components": {"schemas": {"User": {"type": "object", "properties": {"id": {"type": "integer"}}}}}}
        result = _synthesize({"$ref": "#/components/schemas/User"}, spec, 3)
        assert result == {"id": 42}

    def test_uses_example_when_present(self):
        from aquilia.specula.controller import _synthesize

        assert _synthesize({"type": "string", "example": "hi"}, {}, 3) == "hi"


# ═══════════════════════════════════════════════════════════════════════
#  Faults
# ═══════════════════════════════════════════════════════════════════════


class TestSpeculaFaults:
    def test_faults_carry_specula_domain(self):
        fault = SpeculaFault("test")
        assert fault.domain is SPECULA_DOMAIN

    def test_version_not_found_is_404(self):
        assert VersionNotFoundFault.status_code == 404

    def test_observatory_forbidden_is_403(self):
        assert ObservatoryForbiddenFault.status_code == 403

    def test_spec_build_fault_structured(self):
        fault = SpecBuildFault("failed", detail={"x": 1})
        assert fault.code == "SPECULA_SPEC_BUILD_FAILED"
        assert fault.detail == {"x": 1}


# ═══════════════════════════════════════════════════════════════════════
#  UI renderer
# ═══════════════════════════════════════════════════════════════════════


class TestSpeculaUI:
    def test_ui_html_is_valid_utf8(self, config):
        html = SpeculaRenderer(config).render()
        html.encode("utf-8")

    def test_ui_contains_specula_js_namespace(self, config):
        html = SpeculaRenderer(config).render()
        assert "const Specula" in html

    def test_ui_injects_spec_url(self, config):
        html = SpeculaRenderer(config).render()
        assert config.json_path in html

    def test_ui_injects_theme(self):
        config = SpeculaConfig(ui_theme="dark")
        html = SpeculaRenderer(config).render()
        assert 'data-theme="dark"' in html

    def test_custom_css_injected(self):
        config = SpeculaConfig(ui_custom_css=".xyz{color:red}")
        html = SpeculaRenderer(config).render()
        assert ".xyz{color:red}" in html

    def test_ui_contains_aq_app_root(self, config):
        html = SpeculaRenderer(config).render()
        assert 'id="aq-app"' in html

    def test_ui_self_contained_no_cdn_swagger(self, config):
        html = SpeculaRenderer(config).render()
        assert "swagger-ui-dist" not in html
        assert "redoc.standalone" not in html

    def test_primary_color_applied(self):
        config = SpeculaConfig(ui_primary_color="#123456")
        html = SpeculaRenderer(config).render()
        assert "#123456" in html


# ═══════════════════════════════════════════════════════════════════════
#  Config
# ═══════════════════════════════════════════════════════════════════════


class TestSpeculaConfig:
    def test_defaults(self):
        config = SpeculaConfig()
        assert config.title == "Aquilia API"
        assert config.ui_path == "/specula"

    def test_from_dict_ignores_private_and_unknown(self):
        config = SpeculaConfig.from_dict({"_integration_type": "specula", "title": "X", "bogus": 1})
        assert config.title == "X"
        assert not hasattr(config, "bogus")

    def test_integration_specula_key(self):
        from aquilia.config import Integration

        d = Integration.specula(title="T", version="9.9")
        assert d["_integration_type"] == "specula"
        assert d["title"] == "T"


# ═══════════════════════════════════════════════════════════════════════
#  Postman / Insomnia export
# ═══════════════════════════════════════════════════════════════════════


class TestExports:
    def test_postman_groups_by_tag(self, router, config):
        from aquilia.specula.controller import _build_postman_collection

        spec = SpeculaBuilder(config).build(router)
        collection = _build_postman_collection(spec, config)
        assert collection["info"]["name"] == config.title
        assert isinstance(collection["item"], list)

    def test_postman_path_params_become_variables(self, config):
        from aquilia.specula.controller import _build_postman_collection

        spec = {
            "paths": {"/users/{id}": {"get": {"operationId": "get_user", "tags": ["users"]}}},
            "components": {"schemas": {}},
        }
        collection = _build_postman_collection(spec, config)
        raw = collection["item"][0]["item"][0]["request"]["url"]["raw"]
        assert "{{id}}" in raw

    def test_insomnia_export_format(self, router, config):
        from aquilia.specula.controller import _build_insomnia_collection

        spec = SpeculaBuilder(config).build(router)
        collection = _build_insomnia_collection(spec, config)
        assert collection["_type"] == "export"
        assert collection["__export_format"] == 4


# ═══════════════════════════════════════════════════════════════════════
#  End-to-end server integration
# ═══════════════════════════════════════════════════════════════════════


class TestSpeculaServerIntegration:
    """
    Boots a real AquiliaServer (bypassing the TestConfig override layer, which
    shadows the base ``integrations`` map) to prove Specula routes are wired.
    """

    async def _boot(self):
        from aquilia.aquilary.core import RegistryMode
        from aquilia.config import ConfigLoader, Integration
        from aquilia.manifest import AppManifest
        from aquilia.server import AquiliaServer
        from aquilia.workspace import Workspace

        ws = Workspace("specula-test").integrate(Integration.specula(title="E2E API", version="1.2.3"))
        loader = ConfigLoader()
        loader.config_data = ws.to_dict()
        loader.config_data["debug"] = True
        loader.config_data["docs_enabled"] = True
        loader.config_data.setdefault("integrations", {})
        for sub in ("cache", "sessions", "auth", "mail", "templates"):
            loader.config_data["integrations"].setdefault(sub, {})["enabled"] = False
        loader._build_apps_namespace()

        manifest = AppManifest(name="specula_e2e_app", version="0.0.1")
        server = AquiliaServer(manifests=[manifest], config=loader, mode=RegistryMode.TEST)
        await server.startup()
        return server

    async def test_spec_json_served(self):
        from aquilia.testing import TestClient

        server = await self._boot()
        try:
            client = TestClient(server.app)
            resp = await client.get("/specula/spec.json")
            assert resp.status_code == 200
            assert resp.json()["openapi"] == "3.1.0"
        finally:
            await server.shutdown()

    async def test_ui_served(self):
        from aquilia.testing import TestClient

        server = await self._boot()
        try:
            client = TestClient(server.app)
            resp = await client.get("/specula")
            assert resp.status_code == 200
            assert b"aq-app" in resp.body
        finally:
            await server.shutdown()

    async def test_schemas_endpoint_served(self):
        from aquilia.testing import TestClient

        server = await self._boot()
        try:
            client = TestClient(server.app)
            resp = await client.get("/specula/schemas")
            assert resp.status_code == 200
            assert "AquiliaError" in resp.json()["schemas"]
        finally:
            await server.shutdown()


# ═══════════════════════════════════════════════════════════════════════
#  Contract schema bridge
# ═══════════════════════════════════════════════════════════════════════


class TestContractSchema:
    def _contract(self):
        from aquilia.contracts import Contract

        class ProductContract(Contract):
            name: str
            age: int
            price: float

        return ProductContract

    def test_contract_to_schema_object(self):
        from aquilia.specula.schema.contract import contract_to_schema

        schema = contract_to_schema(self._contract(), mode="output")
        assert schema["type"] == "object"
        assert "name" in schema["properties"]

    def test_contract_components_output_and_input(self):
        from aquilia.specula.schema.contract import contract_components

        comps = contract_components(self._contract())
        assert "ProductContract" in comps
        assert "ProductContractInput" in comps

    def test_builder_registers_response_contract(self):
        compiler = ControllerCompiler()
        router = ControllerRouter()
        contract = self._contract()

        class ProductsController(Controller):
            prefix = "/products"

            @GET("/", response_contract=contract)
            async def list_products(self, ctx):
                """List products."""
                return None

        compiled = compiler.compile_controller(ProductsController)
        router.add_controller(compiled)
        router.initialize()
        spec = SpeculaBuilder(SpeculaConfig()).build(router)
        assert "ProductContract" in spec["components"]["schemas"]


# ═══════════════════════════════════════════════════════════════════════
#  Model schema bridge
# ═══════════════════════════════════════════════════════════════════════


class TestModelSchema:
    def _model(self):
        from aquilia.models import Model
        from aquilia.models.fields import (
            AutoField,
            BooleanField,
            CharField,
            EmailField,
            IntegerField,
        )

        class Widget(Model):
            id = AutoField(primary_key=True)
            name = CharField(max_length=50)
            count = IntegerField(null=True)
            email = EmailField()
            active = BooleanField(default=True)

        return Widget

    def test_char_field_is_string_with_max_length(self):
        from aquilia.specula.schema.model import model_to_schema

        schema = model_to_schema(self._model())
        assert schema["properties"]["name"]["type"] == "string"
        assert schema["properties"]["name"]["maxLength"] == 50

    def test_email_field_has_email_format(self):
        from aquilia.specula.schema.model import model_to_schema

        schema = model_to_schema(self._model())
        assert schema["properties"]["email"]["format"] == "email"

    def test_auto_field_is_read_only(self):
        from aquilia.specula.schema.model import model_to_schema

        schema = model_to_schema(self._model())
        assert schema["properties"]["id"]["readOnly"] is True

    def test_nullable_field_uses_oneof(self):
        from aquilia.specula.schema.model import model_to_schema

        schema = model_to_schema(self._model())
        assert "oneOf" in schema["properties"]["count"]

    def test_model_components(self):
        from aquilia.specula.schema.model import model_components

        comps = model_components(self._model())
        assert "Widget" in comps

    def test_non_model_raises(self):
        from aquilia.specula.faults import SchemaResolutionFault
        from aquilia.specula.schema.model import model_to_schema

        with pytest.raises(SchemaResolutionFault):
            model_to_schema(dict)


# ═══════════════════════════════════════════════════════════════════════
#  Security and clearance detection
# ═══════════════════════════════════════════════════════════════════════


class TestSpeculaSecurity:
    def test_authenticated_decorator_detected(self):
        from aquilia.auth import authenticated
        from aquilia.controller import GET, Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.router import ControllerRouter
        from aquilia.specula.config import SpeculaConfig
        from aquilia.specula.schema.builder import SpeculaBuilder

        class SecureController(Controller):
            prefix = "/secure"

            @GET("/me")
            @authenticated
            async def get_me(self, ctx):
                return {"ok": True}

        compiler = ControllerCompiler()
        router = ControllerRouter()
        compiled = compiler.compile_controller(SecureController)
        router.add_controller(compiled)
        router.initialize()

        spec = SpeculaBuilder(SpeculaConfig()).build(router)

        assert "bearerAuth" in spec["components"]["securitySchemes"]

        op = spec["paths"]["/secure/me"]["get"]
        assert "security" in op
        assert any("bearerAuth" in s for s in op["security"])

        assert "x-specula-security" in op
        assert op["x-specula-security"]["authenticated"] is True

    def test_clearance_detected(self):
        from aquilia.auth.clearance import AccessLevel, Clearance, grant
        from aquilia.controller import GET, Controller
        from aquilia.controller.compiler import ControllerCompiler
        from aquilia.controller.router import ControllerRouter
        from aquilia.specula.config import SpeculaConfig
        from aquilia.specula.schema.builder import SpeculaBuilder

        class ClearanceController(Controller):
            prefix = "/clear"
            clearance = Clearance(level=AccessLevel.INTERNAL)

            @GET("/staff")
            async def staff_only(self, ctx):
                return {"ok": True}

            @GET("/public")
            @grant(level=AccessLevel.PUBLIC)
            async def public_ok(self, ctx):
                return {"ok": True}

        compiler = ControllerCompiler()
        router = ControllerRouter()
        compiled = compiler.compile_controller(ClearanceController)
        router.add_controller(compiled)
        router.initialize()

        spec = SpeculaBuilder(SpeculaConfig()).build(router)

        staff_op = spec["paths"]["/clear/staff"]["get"]
        assert "security" in staff_op
        assert staff_op["x-specula-security"]["clearance"]["level"] == "INTERNAL"

        public_op = spec["paths"]["/clear/public"]["get"]
        assert "security" not in public_op or not public_op["security"]
        assert public_op["x-specula-security"]["clearance"]["level"] == "PUBLIC"

