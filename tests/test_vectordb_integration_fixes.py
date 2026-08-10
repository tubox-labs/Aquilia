"""
Regression tests for the vectordb ↔ Aquilia integration fixes.

Each test pins a defect where documented behaviour was silently absent — the
kind that a passing suite did not catch because nothing exercised the path.
"""

from __future__ import annotations

import asyncio
import tempfile
import time

import pytest

from aquilia.vectordb.configs import (
    GpuOptions,
    QuantizationConfig,
    VectorStoreConfig,
    normalize_stores,
)
from aquilia.vectordb.engine import VectorEngine, enable_vector_inspection
from aquilia.vectordb.faults import VectorConfigFault, VectorFault, VectorStoreFault


def _store(**kwargs) -> VectorStoreConfig:
    kwargs.setdefault("alias", "t")
    kwargs.setdefault("path", tempfile.mkdtemp())
    kwargs.setdefault("dimension", 4)
    return VectorStoreConfig(**kwargs)


# ---------------------------------------------------------------------------
# Config normalization
# ---------------------------------------------------------------------------


def test_gpu_options_accepts_bare_policy_string():
    """``gpu="prefer_gpu"`` is the pyconfig spelling; it used to raise."""
    assert GpuOptions.from_dict("prefer_gpu").policy == "prefer_gpu"
    assert GpuOptions.from_dict(None).policy == "cpu_only"
    assert GpuOptions.from_dict({"policy": "require_gpu"}).policy == "require_gpu"


def test_gpu_options_rejects_unknown_policy_as_fault():
    with pytest.raises(VectorConfigFault):
        GpuOptions.from_dict("turbo")


def test_pyconfig_shorthand_produces_a_store():
    """A flat block with a dimension and no ``stores`` is the single-store form.

    This previously normalized to zero stores, so the subsystem opened nothing
    and still reported healthy.
    """
    stores = normalize_stores({"enabled": True, "dimension": 384, "path": "/tmp/v", "default": "main", "stores": []})
    assert len(stores) == 1
    assert stores[0]["alias"] == "main"
    assert stores[0]["dimension"] == 384
    assert stores[0]["path"].endswith("/main")


def test_normalize_stores_handles_every_producer_shape():
    """List, dict, bare-int dict, and shorthand all reach VectorStoreConfig."""
    as_list = normalize_stores({"stores": [{"alias": "a", "dimension": 8}], "path": "/tmp/v"})
    as_dict = normalize_stores({"stores": {"b": {"dimension": 8}}, "path": "/tmp/v"})
    as_int = normalize_stores({"stores": {"c": 8}, "path": "/tmp/v"})

    for entries in (as_list, as_dict, as_int):
        cfg = VectorStoreConfig.from_dict(entries[0])
        assert cfg.dimension == 8

    assert normalize_stores({"enabled": True, "stores": []}) == []


def test_store_inherits_block_level_settings():
    stores = normalize_stores(
        {
            "dimension": 16,
            "gpu": "prefer_gpu",
            "auto_create": False,
            "stores": {"x": {}},
            "path": "/tmp/v",
        }
    )
    cfg = VectorStoreConfig.from_dict(stores[0])
    assert cfg.dimension == 16
    assert cfg.gpu.policy == "prefer_gpu"
    assert cfg.create_if_missing is False


# ---------------------------------------------------------------------------
# Query knobs
# ---------------------------------------------------------------------------


async def test_ef_search_and_gpu_do_not_break_search():
    """``.ef_search()``/``.gpu()`` forwarded kwargs elips rejects — 100% TypeError.

    They are advisory now: the chain records them, the native call does not
    receive them, and the query returns results.
    """
    from aquilia.vectordb import PayloadField, VectorField, VectorModel
    from aquilia.vectordb.registry import VectorRegistry

    class Knob(VectorModel):
        key: str | None = None
        embedding: list[float] = VectorField(dimension=4)
        n: int = PayloadField(default=0)

        class Meta:
            store = "knobs"
            collection = "knobs"
            dimension = 4

    VectorRegistry.configure([{"alias": "knobs", "path": tempfile.mkdtemp(), "dimension": 4}], default="knobs")
    try:
        await VectorRegistry.connect_all()
        await Knob.vectors.add(Knob(embedding=[1.0, 0.0, 0.0, 0.0], n=1))

        hits = await Knob.vectors.query().ef_search(64).gpu(True).search(vector=[1.0, 0.0, 0.0, 0.0])
        assert len(hits) == 1

        plan = await Knob.vectors.query().ef_search(64).explain()
        assert plan["ef_search"] == 64
    finally:
        await VectorRegistry.shutdown()
        VectorRegistry.reset()


# ---------------------------------------------------------------------------
# Graph tuning
# ---------------------------------------------------------------------------


async def test_index_options_reach_the_graph_index():
    """``index_options`` was accepted, stored, and never forwarded to elips."""
    engine = VectorEngine(_store(index="hnsw", index_options={"m": 24, "ef_construction": 200, "ef_search": 128}))
    await engine.connect()
    try:
        params = engine.raw.config.graph_params_val
        assert params.max_connections == 24
        assert params.ef_construction == 200
        assert params.ef_search == 128
    finally:
        await engine.close()


async def test_quantization_still_applies_through_the_config_builder():
    """Guards the connect() → connect_with_config() rewrite."""
    engine = VectorEngine(_store(quantization=QuantizationConfig(codec="sq8")))
    await engine.connect()
    try:
        assert engine.raw.config.quantization_val.codec == "sq8"
    finally:
        await engine.close()


async def test_ivf_index_warns_that_it_maps_to_graph(caplog):
    engine = VectorEngine(_store(index="ivf"))
    with caplog.at_level("WARNING"):
        await engine.connect()
    await engine.close()
    assert "ivf" in caplog.text and "HNSW" in caplog.text


async def test_unknown_index_option_warns_rather_than_silently_dropping(caplog):
    engine = VectorEngine(_store(index="hnsw", index_options={"nlist": 100}))
    with caplog.at_level("WARNING"):
        await engine.connect()
    await engine.close()
    assert "nlist" in caplog.text


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


async def test_transaction_commits_as_a_unit():
    engine = VectorEngine(_store())
    await engine.connect()
    try:
        collection = await engine.collection("things")
        async with engine.transaction() as txn:
            for i in range(5):
                await txn.place("things", vector=[float(i), 0, 0, 1], meta={"i": i}, key=f"row:{i}")
        assert await engine.read(collection.count) == 5
    finally:
        await engine.close()


async def test_transaction_rolls_back_on_exception():
    engine = VectorEngine(_store())
    await engine.connect()
    try:
        collection = await engine.collection("things")
        await engine.write(collection.write, vector=[1.0, 0, 0, 0], meta={})
        before = await engine.read(collection.count)

        with pytest.raises(RuntimeError):
            async with engine.transaction() as txn:
                await txn.place("things", vector=[9.0, 0, 0, 1], meta={"i": 99})
                raise RuntimeError("boom")

        assert await engine.read(collection.count) == before
    finally:
        await engine.close()


async def test_transaction_keys_are_manager_addressable():
    """A natural key staged in a transaction folds the same way a save() does."""
    from aquilia.vectordb.manager import _normalize_key

    engine = VectorEngine(_store())
    await engine.connect()
    try:
        collection = await engine.collection("things")
        async with engine.transaction() as txn:
            await txn.place("things", vector=[1.0, 0, 0, 0], meta={"i": 3}, key="row:3")

        found = await engine.read(collection.pull, [_normalize_key("row:3")])
        assert found and dict(found[0].meta)["i"] == 3
    finally:
        await engine.close()


async def test_engine_write_inside_transaction_raises_instead_of_deadlocking():
    """The writer lock is not reentrant; this used to hang forever."""
    engine = VectorEngine(_store())
    await engine.connect()
    try:
        collection = await engine.collection("things")
        with pytest.raises(VectorStoreFault, match="open transaction"):
            async with engine.transaction() as txn:
                await txn.place("things", vector=[1.0, 0, 0, 0], meta={})
                await asyncio.wait_for(engine.write(collection.rebuild), timeout=5.0)
    finally:
        await engine.close()


async def test_transaction_handle_is_spent_after_the_block():
    engine = VectorEngine(_store())
    await engine.connect()
    try:
        async with engine.transaction() as txn:
            pass
        with pytest.raises(VectorStoreFault, match="already closed"):
            await txn.place("things", vector=[1.0, 0, 0, 0], meta={})
    finally:
        await engine.close()


async def test_read_only_store_refuses_transactions():
    path = tempfile.mkdtemp()
    writer = VectorEngine(_store(path=path))
    await writer.connect()
    await writer.close()

    reader = VectorEngine(_store(path=path, read_only=True))
    await reader.connect()
    try:
        with pytest.raises(VectorStoreFault, match="read_only"):
            async with reader.transaction():
                pass
    finally:
        await reader.close()


# ---------------------------------------------------------------------------
# Inspector spans
# ---------------------------------------------------------------------------


async def test_inspector_spans_are_free_when_disabled_and_emitted_when_on():
    from aquilia.inspector.trace import _CURRENT_TRACE, Lane, RequestTrace

    engine = VectorEngine(_store())
    await engine.connect()
    collection = await engine.collection("d")

    trace = RequestTrace(
        trace_id="t1",
        method="GET",
        path="/x",
        route_pattern="/x",
        started_at=time.time(),
        started_monotonic=time.monotonic(),
    )
    token = _CURRENT_TRACE.set(trace)
    # The gate is process-global and any test that builds an InspectorCollector
    # turns it on, so assert from an explicitly-set state rather than the
    # module default.
    enable_vector_inspection(False)
    try:
        await engine.write(collection.write, vector=[1.0, 0, 0, 0], meta={"a": 1})
        assert trace.spans == []

        enable_vector_inspection(True)
        try:
            await engine.write(collection.write, vector=[0, 1.0, 0, 0], meta={"a": 2})
            await engine.read(collection.probe, [1.0, 0, 0, 0], top=5)
        finally:
            enable_vector_inspection(False)

        assert [s.lane for s in trace.spans] == [Lane.VECTOR, Lane.VECTOR]
        probe_span = trace.spans[-1]
        assert probe_span.detail["store"] == "t"
        assert probe_span.detail["rows"] == 2
    finally:
        _CURRENT_TRACE.reset(token)
        await engine.close()


async def test_inspector_span_records_the_fault_code_on_failure():
    from aquilia.inspector.trace import _CURRENT_TRACE, RequestTrace, SpanStatus

    engine = VectorEngine(_store())
    await engine.connect()
    collection = await engine.collection("d")

    trace = RequestTrace(
        trace_id="t2",
        method="GET",
        path="/x",
        route_pattern="/x",
        started_at=time.time(),
        started_monotonic=time.monotonic(),
    )
    token = _CURRENT_TRACE.set(trace)
    enable_vector_inspection(True)
    try:
        with pytest.raises(VectorFault):
            await engine.read(collection.pull, ["not-a-uuid"])
        assert trace.spans[-1].status is SpanStatus.ERROR
        assert trace.spans[-1].detail["error"]
    finally:
        enable_vector_inspection(False)
        _CURRENT_TRACE.reset(token)
        await engine.close()


# ---------------------------------------------------------------------------
# Embedding cache
# ---------------------------------------------------------------------------


class _CountingEmbedder:
    """Counts backend calls, so cache behaviour is observable."""

    def __new__(cls, **kwargs):
        from aquilia.vectordb.embedders import BaseEmbedder

        class Impl(BaseEmbedder):
            provider = "test"
            calls = 0

            def load(self) -> None:
                pass

            def _embed_sync(self, texts):
                Impl.calls += len(texts)
                return [[float(len(t)), 1.0] for t in texts]

        return Impl("m", normalize=False, **kwargs)


async def test_embedding_cache_dedupes_within_and_across_calls():
    embedder = _CountingEmbedder(cache_size=8)
    impl = type(embedder)

    first = await embedder.embed(["x", "yy", "x"])
    assert impl.calls == 2  # "x" embedded once despite appearing twice
    assert first == [[1.0, 1.0], [2.0, 1.0], [1.0, 1.0]]

    second = await embedder.embed(["x", "zzz"])
    assert impl.calls == 3  # only "zzz" is new
    assert second == [[1.0, 1.0], [3.0, 1.0]]

    # Order follows the input, not the cache or the backend batch.
    assert await embedder.embed(["zzz", "x", "yy"]) == [[3.0, 1.0], [1.0, 1.0], [2.0, 1.0]]
    assert impl.calls == 3


async def test_embedding_cache_is_bounded_and_disablable():
    embedder = _CountingEmbedder(cache_size=3)
    await embedder.embed(["a", "b", "c", "d", "e"])
    assert embedder.cache_stats()["size"] == 3

    off = _CountingEmbedder(cache_size=0)
    impl = type(off)
    impl.calls = 0
    await off.embed(["k"])
    await off.embed(["k"])
    assert impl.calls == 2
    assert off.cache_stats()["size"] == 0


async def test_embedding_cache_handles_empty_input():
    embedder = _CountingEmbedder(cache_size=4)
    assert await embedder.embed([]) == []
