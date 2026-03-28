import sys
import types
from contextlib import asynccontextmanager
from typing import Any, cast

import pytest

from aquilia.aquilary.core import RegistryMode
from aquilia.config import ConfigLoader
from aquilia.faults.domains import ModelNotFoundFault, ModelRegistrationFault
from aquilia.manifest import AppManifest, DatabaseConfig
from aquilia.models.base import ModelRegistry
from aquilia.server import AquiliaServer


class AuthenticationValidationFault(Exception):
    """Business-layer validation error used by regression tests."""


def _install_auth_models_module(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """Install a synthetic modules.authentication.models package in sys.modules."""
    modules_pkg = types.ModuleType("modules")
    modules_pkg.__path__ = []

    auth_pkg = types.ModuleType("modules.authentication")
    auth_pkg.__path__ = []

    models_mod = types.ModuleType("modules.authentication.models")

    code = """
from aquilia.models import Model
from aquilia.models.fields import AutoField, CharField, ForeignKey


class Authentication(Model):
    table = "authentications"
    id = AutoField(primary_key=True)
    provider = CharField(max_length=64)

    class Meta:
        app_label = "authentication"


class Users(Model):
    table = "users"
    id = AutoField(primary_key=True)
    username = CharField(max_length=128)

    class Meta:
        app_label = "authentication"


class Category(Model):
    table = "categories"
    id = AutoField(primary_key=True)
    name = CharField(max_length=128)

    class Meta:
        app_label = "authentication"


class Product(Model):
    table = "products"
    id = AutoField(primary_key=True)
    name = CharField(max_length=128)
    category = ForeignKey("Category")

    class Meta:
        app_label = "authentication"


class Review(Model):
    table = "reviews"
    id = AutoField(primary_key=True)
    body = CharField(max_length=255, default="")
    product = ForeignKey("Product")

    class Meta:
        app_label = "authentication"
"""
    exec(code, models_mod.__dict__)

    monkeypatch.setitem(sys.modules, "modules", modules_pkg)
    monkeypatch.setitem(sys.modules, "modules.authentication", auth_pkg)
    monkeypatch.setitem(sys.modules, "modules.authentication.models", models_mod)

    return models_mod


def _build_auth_manifest(tmp_path) -> AppManifest:
    db_path = tmp_path / "registry_validation.sqlite3"
    return AppManifest(
        name="authentication",
        version="1.0.0",
        models=[
            "modules.authentication.models:Authentication",
            "modules.authentication.models:Users",
            "modules.authentication.models:Category",
            "modules.authentication.models:Product",
            "modules.authentication.models:Review",
        ],
        database=DatabaseConfig(url=f"sqlite:///{db_path}", auto_create=True),
    )


@asynccontextmanager
async def _running_server(manifest: AppManifest):
    """Start an AquiliaServer with a minimal deterministic test config."""
    cfg = ConfigLoader()
    cfg.config_data = {
        "debug": True,
        "runtime": {"mode": "test"},
        "middleware_chain": [],
        "integrations": {
            "cache": {"enabled": False},
            "sessions": {"enabled": False},
            "auth": {"enabled": False},
            "mail": {"enabled": False},
            "templates": {"enabled": False},
        },
    }

    server = AquiliaServer(manifests=[manifest], config=cfg, mode=RegistryMode.TEST)
    await server.startup()
    try:
        yield server
    finally:
        await server.shutdown()


async def _create_product_with_category_validation(product_model, category_id: int, name: str):
    """Replicates product create service behavior expected by issue #35."""
    category_model = ModelRegistry.get("Category")
    if category_model is None:
        raise ModelNotFoundFault(model_name="Category")

    category = await category_model.get_or_none(pk=category_id)
    if category is None:
        raise AuthenticationValidationFault(f"Category {category_id} does not exist")

    category_any = cast(Any, category)
    return await product_model.objects.create(name=name, category_id=category_any.id)


@pytest.fixture(autouse=True)
def _reset_model_registry():
    ModelRegistry.reset()
    yield
    ModelRegistry.reset()


@pytest.mark.asyncio
async def test_clean_boot_registers_manifest_models_and_category(monkeypatch: pytest.MonkeyPatch, tmp_path):
    models_mod = _install_auth_models_module(monkeypatch)
    manifest = _build_auth_manifest(tmp_path)

    async with _running_server(manifest):
        # Deterministic startup inventory should include all manifest models.
        names = set(ModelRegistry.all_models().keys())
        assert {"Authentication", "Users", "Category", "Product", "Review"}.issubset(names)

        # Category must always be present to avoid MODEL_NOT_FOUND at runtime.
        assert ModelRegistry.get("Category") is models_mod.Category


@pytest.mark.asyncio
async def test_product_create_valid_category_id_succeeds(monkeypatch: pytest.MonkeyPatch, tmp_path):
    models_mod = _install_auth_models_module(monkeypatch)
    manifest = _build_auth_manifest(tmp_path)

    async with _running_server(manifest):
        category = await models_mod.Category.objects.create(name="Peripherals")
        product = await _create_product_with_category_validation(
            models_mod.Product,
            category_id=category.id,
            name="Mechanical Keyboard",
        )

        assert product.id is not None
        assert product.category == category.id


@pytest.mark.asyncio
async def test_product_create_invalid_category_id_returns_business_error_not_model_not_found(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    models_mod = _install_auth_models_module(monkeypatch)
    manifest = _build_auth_manifest(tmp_path)

    async with _running_server(manifest):
        with pytest.raises(AuthenticationValidationFault):
            await _create_product_with_category_validation(
                models_mod.Product,
                category_id=9999,
                name="Mouse",
            )


@pytest.mark.asyncio
async def test_startup_fails_fast_when_manifest_declared_model_missing(monkeypatch: pytest.MonkeyPatch, tmp_path):
    modules_pkg = types.ModuleType("modules")
    modules_pkg.__path__ = []
    auth_pkg = types.ModuleType("modules.authentication")
    auth_pkg.__path__ = []

    models_mod = types.ModuleType("modules.authentication.models")
    exec(
        """
from aquilia.models import Model
from aquilia.models.fields import AutoField

class Product(Model):
    table = "products"
    id = AutoField(primary_key=True)
""",
        models_mod.__dict__,
    )

    monkeypatch.setitem(sys.modules, "modules", modules_pkg)
    monkeypatch.setitem(sys.modules, "modules.authentication", auth_pkg)
    monkeypatch.setitem(sys.modules, "modules.authentication.models", models_mod)

    db_path = tmp_path / "missing_model.sqlite3"
    manifest = AppManifest(
        name="authentication",
        version="1.0.0",
        models=[
            "modules.authentication.models:Product",
            "modules.authentication.models:Category",
        ],
        database=DatabaseConfig(url=f"sqlite:///{db_path}", auto_create=True),
    )

    with pytest.raises(ModelRegistrationFault) as exc_info:
        async with _running_server(manifest):
            pass

    assert exc_info.value.code == "MODEL_REGISTRATION_FAILED"
    assert "Category" in str(exc_info.value)


@pytest.mark.asyncio
async def test_registry_bootstrap_not_dependent_on_current_working_directory(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path,
):
    # Simulate launches where cwd is not workspace root.
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AQUILIA_WORKSPACE", raising=False)

    _install_auth_models_module(monkeypatch)
    manifest = _build_auth_manifest(tmp_path)

    async with _running_server(manifest):
        assert ModelRegistry.get("Category") is not None
        assert ModelRegistry.get("Product") is not None


@pytest.mark.asyncio
async def test_reload_keeps_registry_complete_for_declared_models(monkeypatch: pytest.MonkeyPatch, tmp_path):
    _install_auth_models_module(monkeypatch)
    manifest = _build_auth_manifest(tmp_path)

    cfg = ConfigLoader()
    cfg.config_data = {
        "debug": True,
        "runtime": {"mode": "test"},
        "middleware_chain": [],
    }
    server = AquiliaServer(manifests=[manifest], config=cfg, mode=RegistryMode.TEST)
    await server.startup()
    try:
        before = set(ModelRegistry.all_models().keys())
        assert {"Category", "Product", "Review"}.issubset(before)
    finally:
        await server.shutdown()

    # Simulate dev reload/restart via a fresh server process instance.
    cfg2 = ConfigLoader()
    cfg2.config_data = {
        "debug": True,
        "runtime": {"mode": "test"},
        "middleware_chain": [],
    }
    server2 = AquiliaServer(manifests=[manifest], config=cfg2, mode=RegistryMode.TEST)
    await server2.startup()
    try:
        after = set(ModelRegistry.all_models().keys())
        assert {"Category", "Product", "Review"}.issubset(after)
    finally:
        await server2.shutdown()
