"""Scan-mode (metadata filter) queryset behavior."""

from __future__ import annotations

import pytest

from aquilia.vectordb.query import VF


@pytest.fixture
async def seeded(Article):
    await Article.create(title="Blog A", author="Alice", year=2025, score=0.9, active=True, content="a")
    await Article.create(title="Blog B", author="Bob", year=2020, score=0.2, active=True, content="b")
    await Article.create(title="Blog C", author="Alice", year=2023, score=0.5, active=False, content="c")
    return Article


@pytest.mark.asyncio
async def test_filter_equality(seeded):
    results = await seeded.objects.filter(author="Alice").all()
    assert {r.title for r in results} == {"Blog A", "Blog C"}


@pytest.mark.asyncio
async def test_filter_gte(seeded):
    results = await seeded.objects.filter(year__gte=2023).all()
    assert {r.title for r in results} == {"Blog A", "Blog C"}


@pytest.mark.asyncio
async def test_filter_lte(seeded):
    results = await seeded.objects.filter(score__lte=0.5).all()
    assert {r.title for r in results} == {"Blog B", "Blog C"}


@pytest.mark.asyncio
async def test_filter_gt(seeded):
    results = await seeded.objects.filter(year__gt=2023).all()
    assert {r.title for r in results} == {"Blog A"}


@pytest.mark.asyncio
async def test_filter_lt(seeded):
    results = await seeded.objects.filter(score__lt=0.5).all()
    assert {r.title for r in results} == {"Blog B"}


@pytest.mark.asyncio
async def test_filter_ne(seeded):
    results = await seeded.objects.filter(author__ne="Alice").all()
    assert {r.title for r in results} == {"Blog B"}


@pytest.mark.asyncio
async def test_filter_in(seeded):
    results = await seeded.objects.filter(author__in=["Alice", "Bob"]).all()
    assert len(results) == 3


@pytest.mark.asyncio
async def test_filter_contains(seeded):
    results = await seeded.objects.filter(title__contains="Blog").all()
    assert len(results) == 3


@pytest.mark.asyncio
async def test_exclude(seeded):
    results = await seeded.objects.exclude(author="Alice").all()
    assert {r.title for r in results} == {"Blog B"}


@pytest.mark.asyncio
async def test_filter_chained_and(seeded):
    results = await seeded.objects.filter(active=True).filter(author="Alice").all()
    assert {r.title for r in results} == {"Blog A"}


@pytest.mark.asyncio
async def test_vf_and_composition(seeded):
    q = VF(active=True) & VF(author="Alice")
    results = await seeded.objects.filter(q).all()
    assert {r.title for r in results} == {"Blog A"}


@pytest.mark.asyncio
async def test_vf_or_composition(seeded):
    q = VF(author="Alice") | VF(author="Bob")
    results = await seeded.objects.filter(q).all()
    assert len(results) == 3


@pytest.mark.asyncio
async def test_vf_not_composition(seeded):
    q = ~VF(author="Alice")
    results = await seeded.objects.filter(q).all()
    assert {r.title for r in results} == {"Blog B"}


@pytest.mark.asyncio
async def test_limit_offset(seeded):
    results = await seeded.objects.filter(active=True).limit(1).offset(0).all()
    assert len(results) == 1


@pytest.mark.asyncio
async def test_count_no_filter(seeded):
    assert await seeded.objects.count() == 3


@pytest.mark.asyncio
async def test_count_with_filter(seeded):
    assert await seeded.objects.filter(active=True).count() == 2


@pytest.mark.asyncio
async def test_first_returns_none_on_empty(seeded):
    assert await seeded.objects.filter(author="Nobody").first() is None


@pytest.mark.asyncio
async def test_one_raises_on_empty(seeded):
    from aquilia.vectordb.faults import VectorQueryFault

    with pytest.raises(VectorQueryFault):
        await seeded.objects.filter(author="Nobody").one()


@pytest.mark.asyncio
async def test_one_raises_on_multiple(seeded):
    from aquilia.vectordb.faults import VectorQueryFault

    with pytest.raises(VectorQueryFault):
        await seeded.objects.filter(author="Alice").one()


@pytest.mark.asyncio
async def test_delete_queryset(seeded):
    deleted = await seeded.objects.filter(year__lt=2023).delete()
    assert deleted == 1
    assert await seeded.objects.count() == 2


@pytest.mark.asyncio
async def test_none_returns_empty(seeded):
    assert await seeded.objects.none().all() == []


@pytest.mark.asyncio
async def test_async_iter(seeded):
    titles = set()
    async for article in seeded.objects.filter(active=True):
        titles.add(article.title)
    assert titles == {"Blog A", "Blog B"}
