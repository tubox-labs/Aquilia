"""Vector search (search mode): near, near_text, hybrid, explain."""

from __future__ import annotations

import pytest

from aquilia.vectordb.faults import VectorQueryFault
from aquilia.vectordb.query import VectorHit


@pytest.fixture
async def seeded(Article):
    await Article.create(title="Alpha", year=2025, embedding=[1.0, 0.0, 0.0, 0.0], content="alpha doc")
    await Article.create(title="Beta", year=2020, embedding=[0.0, 1.0, 0.0, 0.0], content="beta doc")
    await Article.create(title="Gamma", year=2025, embedding=[0.9, 0.1, 0.0, 0.0], content="gamma doc")
    return Article


@pytest.mark.asyncio
async def test_near_returns_vector_hits(seeded):
    hits = await seeded.objects.near([1.0, 0.0, 0.0, 0.0], top=2).all()
    assert len(hits) == 2
    assert all(isinstance(h, VectorHit) for h in hits)


@pytest.mark.asyncio
async def test_near_hit_has_distance(seeded):
    hits = await seeded.objects.near([1.0, 0.0, 0.0, 0.0], top=1).all()
    assert isinstance(hits[0].distance, float)


@pytest.mark.asyncio
async def test_near_hit_proxies_model_attrs(seeded):
    hits = await seeded.objects.near([1.0, 0.0, 0.0, 0.0], top=1).all()
    assert hits[0].title == "Alpha"
    assert hits[0].key is not None


@pytest.mark.asyncio
async def test_near_with_filter(seeded):
    hits = await seeded.objects.near([1.0, 0.0, 0.0, 0.0], top=5).filter(year__gte=2025).all()
    assert all(h.year == 2025 for h in hits)


@pytest.mark.asyncio
async def test_near_text(seeded):
    hits = await seeded.objects.near_text("alpha", top=2).all()
    assert all(isinstance(h, VectorHit) for h in hits)


@pytest.mark.asyncio
async def test_hybrid(seeded):
    hits = await seeded.objects.hybrid([1.0, 0.0, 0.0, 0.0], "alpha", top=2, lexical_weight=0.3).all()
    assert len(hits) <= 2


@pytest.mark.asyncio
async def test_max_distance(seeded):
    hits = await seeded.objects.near([1.0, 0.0, 0.0, 0.0], top=5, max_distance=0.001).all()
    assert isinstance(hits, list)


@pytest.mark.asyncio
async def test_limit_on_search_mode_raises(seeded):
    with pytest.raises(VectorQueryFault):
        seeded.objects.near([1.0, 0.0, 0.0, 0.0]).limit(2)


@pytest.mark.asyncio
async def test_delete_on_search_mode_raises(seeded):
    with pytest.raises(VectorQueryFault):
        await seeded.objects.near([1.0, 0.0, 0.0, 0.0]).delete()


@pytest.mark.asyncio
async def test_explain_returns_string(seeded):
    plan = await seeded.objects.near([1.0, 0.0, 0.0, 0.0], top=2).explain()
    assert isinstance(plan, str)


@pytest.mark.asyncio
async def test_explain_on_scan_mode_raises(seeded):
    with pytest.raises(VectorQueryFault):
        await seeded.objects.filter(year__gte=2020).explain()
