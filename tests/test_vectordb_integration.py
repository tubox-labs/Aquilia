"""
Vector database configuration, subsystem, and interop tests.

Configuration and manifest wiring is exercised without elips; the interop and
subsystem sections skip when it is absent.
"""

from __future__ import annotations

from typing import Annotated

import pytest

from aquilia.config import ConfigLoader
from aquilia.integrations import VectorDatabaseIntegration
from aquilia.integrations.integration import Integration
from aquilia.manifest import AppManifest, ComponentKind
from aquilia.vectordb import (
    Dimension,
    EmbedderOptions,
    GpuOptions,
    Key,
    Payload,
    Text,
    VectorModel,
    VectorStoreConfig,
    is_available,
)
from aquilia.vectordb.interop import Link
from aquilia.workspace import Workspace

DIM = 8


# ── Config dataclasses ───────────────────────────────────────────────────────


def test_store_config_round_trips_through_dict():
    cfg = VectorStoreConfig(alias="docs", path="./v", dimension=16, metric="l2", index="hnsw")
    assert VectorStoreConfig.from_dict(cfg.to_dict()) == cfg


def test_unknown_keys_are_preserved_as_options():
    """A newer elips knob must reach the engine without a framework release."""
    cfg = VectorStoreConfig.from_dict({"alias": "a", "dimension": 8, "future_knob": 7})
    assert cfg.options["future_knob"] == 7


def test_invalid_dimension_rejected():
    with pytest.raises(ValueError):
        VectorStoreConfig(dimension=0)


def test_invalid_metric_rejected():
    with pytest.raises(ValueError):
        VectorStoreConfig(metric="nope")


def test_gpu_options_round_trip():
    gpu = GpuOptions(policy="prefer_gpu", device=1, fallback="warn")
    assert GpuOptions.from_dict(gpu.to_dict()) == gpu


def test_embedder_options_round_trip():
    emb = EmbedderOptions(provider="callable", fn="mod:fn", batch_size=8)
    assert EmbedderOptions.from_dict(emb.to_dict()) == emb


def test_embedder_options_from_none_is_none():
    assert EmbedderOptions.from_dict(None) is None


# ── Integration ──────────────────────────────────────────────────────────────


def test_integration_flattens_stores_to_a_list():
    payload = VectorDatabaseIntegration(
        path="./vecs",
        stores={"default": {"dimension": 384}, "images": {"dimension": 512}},
    ).to_dict()

    assert payload["_integration_type"] == "vectordb"
    aliases = {s["alias"] for s in payload["stores"]}
    assert aliases == {"default", "images"}


def test_integration_derives_per_store_paths():
    payload = VectorDatabaseIntegration(path="./vecs", stores={"default": {"dimension": 8}}).to_dict()
    assert payload["stores"][0]["path"].replace("\\", "/").endswith("vecs/default")


def test_explicit_store_path_is_not_overridden():
    payload = VectorDatabaseIntegration(
        path="./vecs", stores={"default": {"dimension": 8, "path": "/abs/elsewhere"}}
    ).to_dict()
    assert payload["stores"][0]["path"] == "/abs/elsewhere"


def test_integration_level_gpu_cascades_to_stores():
    payload = VectorDatabaseIntegration(
        stores={"a": {"dimension": 8}, "b": {"dimension": 8, "gpu": {"policy": "cpu_only"}}},
        gpu=GpuOptions(policy="prefer_gpu"),
    ).to_dict()

    by_alias = {s["alias"]: s for s in payload["stores"]}
    assert by_alias["a"]["gpu"]["policy"] == "prefer_gpu"
    # An explicit store-level setting wins over the cascade.
    assert by_alias["b"]["gpu"]["policy"] == "cpu_only"


def test_integration_builder_matches_dataclass():
    built = Integration.vectordb(stores={"default": {"dimension": 8}})
    assert built["_integration_type"] == "vectordb"
    assert built["stores"][0]["alias"] == "default"


# ── Workspace ────────────────────────────────────────────────────────────────


def test_workspace_vectordb_shorthand():
    ws = Workspace("app").vectordb(stores={"default": {"dimension": 8}})
    config = ws.to_dict()
    assert config["vectordb"]["enabled"] is True
    assert config["integrations"]["vectordb"]["stores"][0]["alias"] == "default"


def test_workspace_without_vectordb_has_no_block():
    assert "vectordb" not in Workspace("app").to_dict()


def test_workspace_integrate_routes_typed_dataclass():
    ws = Workspace("app").integrate(VectorDatabaseIntegration(stores={"default": {"dimension": 8}}))
    assert ws.to_dict()["vectordb"]["stores"][0]["alias"] == "default"


# ── ConfigLoader ─────────────────────────────────────────────────────────────


def _loader(config: dict) -> ConfigLoader:
    """A loader primed with in-memory config, as the other suites do it."""
    loader = ConfigLoader()
    loader.config_data = config
    return loader


def test_loader_defaults_to_disabled():
    """An install with no vectordb block must behave exactly as before."""
    config = _loader({}).get_vectordb_config()
    assert config["enabled"] is False
    assert config["stores"] == []


def test_loader_reads_workspace_block():
    ws = Workspace("app").vectordb(stores={"default": {"dimension": 8}})
    config = _loader(ws.to_dict()).get_vectordb_config()
    assert config["enabled"] is True
    assert config["pool_threads"] == 4
    assert config["stores"][0]["dimension"] == 8


# ── Manifest ─────────────────────────────────────────────────────────────────


def test_component_kind_exists():
    assert ComponentKind.VECTOR_MODEL.value == "vector_model"


def test_manifest_carries_vector_models():
    manifest = AppManifest(name="blog", version="1.0.0", vector_models=["modules.blog.vector_models"])
    assert manifest.vector_models == ["modules.blog.vector_models"]
    assert manifest.to_dict()["vector_models"] == ["modules.blog.vector_models"]


def test_manifest_defaults_to_empty():
    assert AppManifest(name="blog", version="1.0.0").vector_models == []


def test_discover_patterns_include_vector_models():
    assert "vector_models" in AppManifest(name="blog", version="1.0.0").discover_patterns


# ── Subsystem ────────────────────────────────────────────────────────────────


elips_only = pytest.mark.skipif(not is_available(), reason="elips is not installed")


def _boot_context(config):
    from aquilia.subsystems.base import BootContext

    return BootContext(config=config, manifests=[])


async def test_subsystem_noops_without_config():
    """No vectordb block means no elips import and no store."""
    from aquilia.health import SubsystemStatus
    from aquilia.vectordb.subsystem import VectorDBSubsystem

    subsystem = VectorDBSubsystem()
    status = await subsystem.initialize(_boot_context({}))

    assert status.status == SubsystemStatus.HEALTHY
    assert subsystem.required is False


async def test_subsystem_noops_when_disabled():
    from aquilia.vectordb.subsystem import VectorDBSubsystem

    subsystem = VectorDBSubsystem()
    await subsystem.initialize(_boot_context({"vectordb": {"enabled": False}}))
    assert subsystem.required is False


@elips_only
async def test_subsystem_opens_declared_stores(tmp_path):
    from aquilia.health import SubsystemStatus
    from aquilia.vectordb.registry import VectorRegistry
    from aquilia.vectordb.subsystem import VectorDBSubsystem

    ctx = _boot_context(
        {
            "vectordb": {
                "enabled": True,
                "stores": [{"alias": "main", "path": str(tmp_path / "db"), "dimension": DIM}],
            }
        }
    )

    subsystem = VectorDBSubsystem()
    try:
        status = await subsystem.initialize(ctx)
        assert status.status == SubsystemStatus.HEALTHY
        # A configured store that failed to open must stop the boot, so the
        # usual optional-subsystem default is raised here.
        assert subsystem.required is True
        assert VectorRegistry.store_names() == ["main"]
        assert ctx.shared_state["vector_registry"] is VectorRegistry
        assert "vectordb.main" in ctx.health._statuses
    finally:
        await subsystem.shutdown()
        VectorRegistry._stores = {}
        VectorRegistry._engines = {}
        VectorRegistry._pool = None


# ── Interop ──────────────────────────────────────────────────────────────────


class Doc(VectorModel):
    key: Annotated[str, Key()]
    embedding: Annotated[list[float], Dimension(DIM)]
    body: Annotated[str, Text()]
    post_id: Annotated[int, Payload()]

    class Meta:
        collection = "interop_docs"


class Linked(VectorModel):
    """Declared at module scope: PEP 563 resolves annotations against module
    globals, so a marker imported inside a function body is invisible here."""

    key: Annotated[str, Key()]
    embedding: Annotated[list[float], Dimension(DIM)]
    body: Annotated[str, Text()]
    post_id: Annotated[int, Link("mymod:Post")]

    class Meta:
        collection = "linked"


def test_link_marker_is_recorded():
    assert "post_id" in Linked._vlinks
    assert Linked._vfields.link_attrs == frozenset({"post_id"})
    # A link is also an ordinary payload — that is how the FK reaches storage.
    assert "post_id" in Linked._vfields.payloads


def test_link_on_unstorable_type_is_rejected():
    from aquilia.vectordb.faults import VectorSchemaFault

    with pytest.raises(VectorSchemaFault):

        class BadLink(VectorModel):
            key: Annotated[str, Key()]
            embedding: Annotated[list[float], Dimension(DIM)]
            body: Annotated[str, Text()]
            ref: Annotated[dict, Link("mymod:Post")]


def test_mirror_requires_text_or_vector():
    from aquilia.vectordb.faults import VectorSchemaFault
    from aquilia.vectordb.interop import mirror

    with pytest.raises(VectorSchemaFault):
        mirror(into=Doc)


def test_mirror_key_is_deterministic():
    """Stable keys are what make a re-save overwrite instead of duplicating."""
    from aquilia.vectordb.interop import MirrorSpec

    class FakePost:
        _table_name = "posts"
        pk = 42

    spec = MirrorSpec(source=FakePost, target=Doc, text=lambda p: "x")
    # Keyed off the *target collection*, not the source SQL table: the vector
    # side owns the key space it writes into, so renaming the table must not
    # orphan every mirrored record.
    assert spec.build_key(FakePost()) == "interop_docs:42"
    assert spec.build_key(FakePost()) == spec.build_key(FakePost())


def test_mirror_key_ignores_sql_table_name():
    """§1.2: the ``_table_name`` fallback is gone — collection is the source."""
    from aquilia.vectordb.interop import MirrorSpec

    class Renamed:
        _table_name = "totally_different"
        pk = 7

    spec = MirrorSpec(source=Renamed, target=Doc, text=lambda p: "x")
    assert spec.build_key(Renamed()) == "interop_docs:7"


def test_mirror_when_predicate_gates_records():
    from aquilia.vectordb.interop import MirrorSpec

    class FakePost:
        _table_name = "posts"
        pk = 1
        published = False

    spec = MirrorSpec(source=FakePost, target=Doc, text=lambda p: "x", when=lambda p: p.published)
    assert spec.should_mirror(FakePost()) is False


def test_mirror_payload_resolves_callables_and_constants():
    from aquilia.vectordb.interop import MirrorSpec

    class FakePost:
        _table_name = "posts"
        pk = 7

    spec = MirrorSpec(
        source=FakePost,
        target=Doc,
        text=lambda p: "x",
        meta={"post_id": lambda p: p.pk, "kind": "post"},
    )
    payload = spec.build_payload(FakePost())
    assert payload == {"post_id": 7, "kind": "post"}


async def test_as_models_returns_empty_for_no_hits():
    from aquilia.vectordb.interop import as_models

    class FakeModel:
        pass

    assert await as_models([], FakeModel, via="post_id") == []


async def test_resolve_rejects_non_link_attribute():
    from aquilia.vectordb.faults import VectorSchemaFault
    from aquilia.vectordb.interop import resolve

    doc = Doc(key="k", embedding=[0.0] * DIM, body="x", post_id=1)
    with pytest.raises(VectorSchemaFault):
        await resolve(doc, "post_id")
