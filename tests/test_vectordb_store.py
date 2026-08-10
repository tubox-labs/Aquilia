"""
Vector engine, query, and manager tests — these run against real elips.

Skipped wholesale when elips is not installed, which is the same contract the
subsystem itself honours.
"""

from __future__ import annotations

from typing import Annotated

import pytest

from aquilia.vectordb import (
    VF,
    Dimension,
    Key,
    Payload,
    Score,
    Text,
    VectorModel,
    VectorStoreConfig,
    is_available,
)
from aquilia.vectordb.engine import VectorEngine
from aquilia.vectordb.faults import (
    VectorDimensionFault,
    VectorLookupFault,
    VectorMultipleFoundFault,
    VectorNotFoundFault,
    VectorQueryFault,
    VectorStoreFault,
)
from aquilia.vectordb.registry import VectorRegistry

pytestmark = pytest.mark.skipif(not is_available(), reason="elips is not installed")

DIM = 8


def vec(seed: float) -> list[float]:
    """A deterministic vector that varies with the seed."""
    return [seed] + [0.0] * (DIM - 1)


class Note(VectorModel):
    key: Annotated[str, Key()]
    embedding: Annotated[list[float], Dimension(DIM)]
    body: Annotated[str, Text()]
    views: Annotated[int, Payload(indexed=True)]
    starred: Annotated[bool, Payload()]
    score: Annotated[float, Score()]

    class Meta:
        collection = "notes"


@pytest.fixture
async def notes(tmp_path):
    """A registry configured with one temp store, torn down after each test."""
    VectorRegistry.configure([VectorStoreConfig(alias="default", path=str(tmp_path / "db"), dimension=DIM)])
    try:
        yield Note.vectors
    finally:
        await VectorRegistry.shutdown()
        VectorRegistry._stores = {}
        VectorRegistry._engines = {}
        VectorRegistry._pool = None


async def seed(mgr, *specs):
    """Write ``(key_seed, views, starred)`` triples and return the assigned keys."""
    records = [Note(embedding=vec(s), body=f"note {s}", views=v, starred=st) for s, v, st in specs]
    await mgr.add_many(records)
    return [r.key for r in records]


# ── Engine lifecycle ─────────────────────────────────────────────────────────


async def test_engine_connects_and_closes(tmp_path):
    engine = VectorEngine(VectorStoreConfig(alias="t", path=str(tmp_path / "db"), dimension=DIM))
    assert engine.connected is False
    await engine.connect()
    assert engine.connected is True
    await engine.close()
    assert engine.connected is False


async def test_connect_is_idempotent(tmp_path):
    engine = VectorEngine(VectorStoreConfig(alias="t", path=str(tmp_path / "db"), dimension=DIM))
    await engine.connect()
    await engine.connect()
    assert engine.connected is True
    await engine.close()


async def test_raw_before_connect_fails_loudly(tmp_path):
    engine = VectorEngine(VectorStoreConfig(alias="t", path=str(tmp_path / "db"), dimension=DIM))
    with pytest.raises(VectorStoreFault) as exc:
        _ = engine.raw
    assert exc.value.code == "VECTOR_STORE_ERROR"


async def test_missing_path_without_create_fails(tmp_path):
    engine = VectorEngine(
        VectorStoreConfig(
            alias="t",
            path=str(tmp_path / "absent"),
            dimension=DIM,
            create_if_missing=False,
        )
    )
    with pytest.raises(Exception) as exc:
        await engine.connect()
    assert exc.value.code == "VECTOR_CONFIG_INVALID"


async def test_read_only_store_rejects_writes(tmp_path):
    path = str(tmp_path / "db")
    writable = VectorEngine(VectorStoreConfig(alias="w", path=path, dimension=DIM))
    await writable.connect()
    await writable.close()

    engine = VectorEngine(VectorStoreConfig(alias="ro", path=path, dimension=DIM, read_only=True))
    await engine.connect()
    collection = await engine.collection("notes")
    with pytest.raises(VectorStoreFault) as exc:
        await engine.write(collection.write, vector=vec(1.0), meta={})
    assert "read_only" in exc.value.message
    await engine.close()


async def test_health_reports_store_shape(tmp_path):
    engine = VectorEngine(VectorStoreConfig(alias="t", path=str(tmp_path / "db"), dimension=DIM))
    await engine.connect()
    health = await engine.health()
    assert health["ok"] is True
    assert health["dimension"] == DIM
    assert health["alias"] == "t"
    await engine.close()


async def test_health_of_closed_engine_is_not_ok(tmp_path):
    """A health check has to stay callable when the thing is broken."""
    engine = VectorEngine(VectorStoreConfig(alias="t", path=str(tmp_path / "db"), dimension=DIM))
    health = await engine.health()
    assert health["ok"] is False
    assert health["error"] == "not connected"


# ── Writes and reads ─────────────────────────────────────────────────────────


async def test_save_assigns_a_key(notes):
    note = Note(embedding=vec(1.0), body="hello", views=3, starred=True)
    assert note.key is None
    await note.save()
    assert note.key is not None


async def test_save_then_get_round_trips(notes):
    note = Note(embedding=vec(1.0), body="hello", views=3, starred=True)
    await note.save()

    got = await notes.get(note.key)
    assert isinstance(got, Note)
    assert got.body == "hello"
    assert got.views == 3
    assert got.starred is True


async def test_get_missing_returns_none(notes):
    assert await notes.get("11111111-1111-4111-8111-111111111111") is None


async def test_natural_keys_are_normalized_consistently(notes):
    """A non-UUID key is folded to a stable UUID on every path, not just writes."""
    note = Note(key="posts:1", embedding=vec(1.0), body="x", views=1, starred=False)
    await note.save()

    assert await notes.get("posts:1") is not None
    assert await notes.remove("posts:1") is True
    assert await notes.count() == 0


async def test_resaving_the_same_key_overwrites(notes):
    """Deterministic keys make mirroring idempotent."""
    await Note(key="posts:1", embedding=vec(1.0), body="first", views=1, starred=False).save()
    await Note(key="posts:1", embedding=vec(1.0), body="second", views=2, starred=False).save()

    assert await notes.count() == 1
    assert (await notes.get("posts:1")).body == "second"


async def test_add_validates_before_writing(notes):
    bad = Note(embedding=[0.0, 1.0], body="x", views=1, starred=False)
    with pytest.raises(Exception) as exc:
        await notes.add(bad)
    assert exc.value.code == "VECTOR_VALIDATION_FAILED"
    assert await notes.count() == 0


async def test_delete_instance_removes(notes):
    note = Note(embedding=vec(1.0), body="x", views=1, starred=False)
    await note.save()
    assert await note.delete_instance() is True
    assert await notes.count() == 0


async def test_refresh_reloads_from_storage(notes):
    note = Note(embedding=vec(1.0), body="original", views=1, starred=False)
    await note.save()

    note.body = "local edit"
    await note.refresh()
    assert note.body == "original"


async def test_refresh_of_deleted_record_raises(notes):
    note = Note(embedding=vec(1.0), body="x", views=1, starred=False)
    await note.save()
    await notes.remove(note.key)
    with pytest.raises(VectorNotFoundFault):
        await note.refresh()


async def test_get_many_skips_missing(notes):
    note = Note(embedding=vec(1.0), body="x", views=1, starred=False)
    await note.save()
    found = await notes.get_many([note.key, "11111111-1111-4111-8111-111111111111"])
    assert [n.key for n in found] == [note.key]


async def test_add_many_assigns_all_keys(notes):
    keys = await seed(notes, (1.0, 1, True), (0.5, 2, False), (0.1, 3, True))
    assert all(k is not None for k in keys)
    assert await notes.count() == 3


# ── Search ───────────────────────────────────────────────────────────────────


async def test_search_orders_by_similarity(notes):
    await seed(notes, (1.0, 1, False), (-1.0, 2, False))
    hits = await notes.query().search(vector=vec(1.0), limit=2)
    assert hits[0].score >= hits[1].score
    assert hits[0].record.views == 1


async def test_hit_proxies_record_attributes(notes):
    await seed(notes, (1.0, 7, True))
    hit = (await notes.query().search(vector=vec(1.0), limit=1))[0]
    assert hit.views == 7
    assert hit.record.views == 7


async def test_search_requires_exactly_one_query(notes):
    with pytest.raises(VectorQueryFault):
        await notes.query().search()
    with pytest.raises(VectorQueryFault):
        await notes.query().search(text="x", vector=vec(1.0))


async def test_search_rejects_wrong_dimension(notes):
    with pytest.raises(VectorDimensionFault):
        await notes.query().search(vector=[0.0, 1.0])


async def test_search_without_embedder_rejects_text(notes):
    with pytest.raises(Exception) as exc:
        await notes.query().search(text="anything")
    assert exc.value.code == "VECTOR_EMBEDDER_UNAVAILABLE"


async def test_search_rejects_offset(notes):
    """Top-k has no stable offset; paging by it would re-rank between pages."""
    with pytest.raises(VectorQueryFault):
        await notes.query().offset(5).search(vector=vec(1.0))


async def test_search_applies_filters(notes):
    await seed(notes, (1.0, 10, True), (0.9, 1, False))
    hits = await notes.query().filter(starred=True).search(vector=vec(1.0), limit=5)
    assert [h.record.views for h in hits] == [10]


# ── Filtering ────────────────────────────────────────────────────────────────


async def test_filter_exact(notes):
    await seed(notes, (1.0, 10, True), (0.9, 20, False))
    assert len(await notes.query().filter(views=10).all()) == 1


async def test_filter_range(notes):
    await seed(notes, (1.0, 5, False), (0.9, 50, False))
    found = await notes.query().filter(views__gte=10).all()
    assert [n.views for n in found] == [50]


async def test_filter_in(notes):
    await seed(notes, (1.0, 5, False), (0.9, 50, False), (0.8, 99, False))
    found = await notes.query().filter(views__in=[5, 99]).all()
    assert sorted(n.views for n in found) == [5, 99]


async def test_filter_empty_in_matches_nothing(notes):
    await seed(notes, (1.0, 5, False))
    assert await notes.query().filter(views__in=[]).all() == []


async def test_filter_or_node(notes):
    await seed(notes, (1.0, 5, False), (0.9, 50, False), (0.8, 99, False))
    found = await notes.query().filter(VF(views=5) | VF(views=99)).all()
    assert sorted(n.views for n in found) == [5, 99]


async def test_filter_and_node(notes):
    await seed(notes, (1.0, 5, True), (0.9, 5, False))
    found = await notes.query().filter(VF(views=5) & VF(starred=True)).all()
    assert len(found) == 1


async def test_exclude_negates(notes):
    await seed(notes, (1.0, 5, False), (0.9, 50, False))
    found = await notes.query().exclude(views=5).all()
    assert [n.views for n in found] == [50]


async def test_filter_contains_substring(notes):
    await seed(notes, (1.0, 5, False))
    assert len(await notes.query().filter(body__contains="note").all()) == 1
    assert len(await notes.query().filter(body__contains="zzz").all()) == 0


async def test_filter_startswith_is_anchored(notes):
    """Push-down is containment; anchoring is applied as a residual."""
    await seed(notes, (1.0, 5, False))
    assert len(await notes.query().filter(body__startswith="note").all()) == 1
    assert len(await notes.query().filter(body__startswith="ote").all()) == 0


async def test_filter_rejects_unknown_attribute(notes):
    with pytest.raises(VectorLookupFault) as exc:
        await notes.query().filter(nope=1).all()
    assert "nope" in exc.value.message


async def test_filter_rejects_unknown_lookup(notes):
    with pytest.raises(VectorLookupFault):
        await notes.query().filter(views__sideways=1).all()


async def test_filter_rejects_isnull(notes):
    """elips has no null concept, so isnull has no faithful translation."""
    with pytest.raises(VectorLookupFault) as exc:
        await notes.query().filter(views__isnull=True).all()
    assert exc.value.code == "VECTOR_LOOKUP_UNSUPPORTED"


# ── Query semantics ──────────────────────────────────────────────────────────


async def test_query_is_immutable(notes):
    base = notes.query()
    narrowed = base.filter(views=1)
    assert base is not narrowed
    assert base._lookups == {}


async def test_bool_raises_with_guidance(notes):
    query = notes.query()
    with pytest.raises(VectorQueryFault) as exc:
        bool(query)
    assert "exists()" in exc.value.message


async def test_len_raises_with_guidance(notes):
    query = notes.query()
    with pytest.raises(VectorQueryFault) as exc:
        len(query)
    assert "count()" in exc.value.message


async def test_manager_rejects_instance_access(notes):
    note = Note(embedding=vec(1.0), body="x", views=1, starred=False)
    with pytest.raises(VectorQueryFault):
        _ = note.vectors


async def test_count_matches_all(notes):
    await seed(notes, (1.0, 1, False), (0.9, 2, False), (0.8, 3, False))
    assert await notes.count() == 3
    assert await notes.query().filter(views__gte=2).count() == 2


async def test_limit_caps_results(notes):
    await seed(notes, *[(1.0 - i / 10, i, False) for i in range(5)])
    assert len(await notes.query().limit(2).all()) == 2


async def test_first_returns_none_when_empty(notes):
    assert await notes.query().first() is None


async def test_one_requires_exactly_one(notes):
    await seed(notes, (1.0, 1, False), (0.9, 2, False))
    with pytest.raises(VectorMultipleFoundFault):
        await notes.query().one()
    with pytest.raises(VectorNotFoundFault):
        await notes.query().filter(views=999).one()
    assert (await notes.query().filter(views=1).one()).views == 1


async def test_exists(notes):
    assert await notes.query().exists() is False
    await seed(notes, (1.0, 1, False))
    assert await notes.query().exists() is True


async def test_async_iteration(notes):
    await seed(notes, (1.0, 1, False), (0.9, 2, False))
    seen = [n.views async for n in notes.query()]
    assert sorted(seen) == [1, 2]


async def test_delete_requires_a_filter(notes):
    """An unfiltered delete would empty the collection, so it is refused."""
    await seed(notes, (1.0, 1, False))
    with pytest.raises(VectorQueryFault):
        await notes.query().delete()
    assert await notes.count() == 1


async def test_filtered_delete_removes_matching(notes):
    await seed(notes, (1.0, 1, False), (0.9, 50, False))
    assert await notes.query().filter(views__gte=10).delete() == 1
    assert await notes.count() == 1


async def test_explain_reports_the_plan(notes):
    await seed(notes, (1.0, 1, False))
    plan = await notes.query().filter(views=1).explain()
    assert "strategy" in plan
    assert "index_type" in plan


async def test_with_vectors_hydrates_the_vector(notes):
    note = Note(embedding=vec(0.5), body="x", views=1, starred=False)
    await note.save()

    plain = await notes.query().first()
    assert plain.embedding is None

    hydrated = await notes.query().with_vectors().first()
    assert hydrated.embedding is not None
    assert len(hydrated.embedding) == DIM


# ── Registry ─────────────────────────────────────────────────────────────────


async def test_dimension_mismatch_is_rejected_at_bind(tmp_path):
    class Wide(VectorModel):
        key: Annotated[str, Key()]
        embedding: Annotated[list[float], Dimension(128)]
        body: Annotated[str, Text()]

        class Meta:
            collection = "wide"

    VectorRegistry.configure([VectorStoreConfig(alias="default", path=str(tmp_path / "db"), dimension=DIM)])
    try:
        with pytest.raises(Exception) as exc:
            await Wide.vectors.count()
        assert exc.value.code == "VECTOR_SCHEMA_INVALID"
    finally:
        await VectorRegistry.shutdown()
        VectorRegistry._stores = {}
        VectorRegistry._engines = {}
        VectorRegistry._pool = None


async def test_unknown_store_alias_is_rejected(tmp_path):
    class Elsewhere(VectorModel):
        key: Annotated[str, Key()]
        embedding: Annotated[list[float], Dimension(DIM)]
        body: Annotated[str, Text()]

        class Meta:
            collection = "elsewhere"
            store = "nonexistent"

    VectorRegistry.configure([VectorStoreConfig(alias="default", path=str(tmp_path / "db"), dimension=DIM)])
    try:
        with pytest.raises(Exception) as exc:
            await Elsewhere.vectors.count()
        assert exc.value.code == "VECTOR_REGISTRY_ERROR"
    finally:
        await VectorRegistry.shutdown()
        VectorRegistry._stores = {}
        VectorRegistry._engines = {}
        VectorRegistry._pool = None
