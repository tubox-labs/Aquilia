"""CRUD operations: create, get, save, delete, refresh, bulk_create, get_or_create, to_dict."""

from __future__ import annotations

import pytest

from aquilia.vectordb.faults import VectorModelNotFoundFault, VectorQueryFault

# Elips record keys must be 32 hex digits (a UUID, hyphens optional on input --
# always normalized to hyphenated form on output).
EXPLICIT_KEY = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
MISSING_KEY = "deadbeefdeadbeefdeadbeefdeadbeef"


@pytest.mark.asyncio
async def test_create_returns_instance_with_key(Article):
    article = await Article.create(title="Hello World", author="Alice", year=2025, content="Some body text")
    assert isinstance(article.key, str)
    assert article.title == "Hello World"


@pytest.mark.asyncio
async def test_create_with_explicit_key(Article):
    article = await Article.create(key=EXPLICIT_KEY, title="Pinned", content="text")
    assert article.key.replace("-", "") == EXPLICIT_KEY


@pytest.mark.asyncio
async def test_get_by_key(Article):
    created = await Article.create(title="Findable", content="body")
    fetched = await Article.get(created.key)
    assert fetched.key == created.key
    assert fetched.title == "Findable"


@pytest.mark.asyncio
async def test_get_missing_raises_fault(Article):
    with pytest.raises(VectorModelNotFoundFault):
        await Article.get(MISSING_KEY)


@pytest.mark.asyncio
async def test_get_or_none_missing_returns_none(Article):
    assert await Article.get_or_none(MISSING_KEY) is None


@pytest.mark.asyncio
async def test_save_new_instance(Article):
    article = Article(title="Draft", content="text")
    assert article.key is None
    await article.save()
    assert article.key is not None


@pytest.mark.asyncio
async def test_save_existing_instance(Article):
    article = await Article.create(title="Original", content="text")
    article.title = "Updated"
    await article.save()
    fetched = await Article.get(article.key)
    assert fetched.title == "Updated"


@pytest.mark.asyncio
async def test_delete_clears_key(Article):
    article = await Article.create(title="Bye", content="text")
    await article.delete()
    assert article.key is None


@pytest.mark.asyncio
async def test_delete_unsaved_raises_fault(Article):
    article = Article(title="Unsaved", content="text")
    with pytest.raises(VectorQueryFault):
        await article.delete()


@pytest.mark.asyncio
async def test_refresh(Article):
    article = await Article.create(title="Before", content="text")
    twin = await Article.get(article.key)
    twin.title = "After"
    await twin.save()

    await article.refresh()
    assert article.title == "After"


@pytest.mark.asyncio
async def test_bulk_create(Article):
    articles = await Article.bulk_create(
        [
            Article(title="A", year=2024, content="a text"),
            Article(title="B", year=2025, content="b text"),
        ]
    )
    assert all(a.key for a in articles)


@pytest.mark.asyncio
async def test_get_or_create_creates(Article):
    fresh_key = "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
    article, created = await Article.get_or_create(key=fresh_key, defaults={"title": "New", "content": "text"})
    assert created is True
    assert article.key.replace("-", "") == fresh_key


@pytest.mark.asyncio
async def test_get_or_create_gets_existing(Article):
    existing_key = "cccccccccccccccccccccccccccccccc"
    existing = await Article.create(key=existing_key, title="Already Here", content="text")
    article, created = await Article.get_or_create(key=existing_key, defaults={"title": "Ignored"})
    assert created is False
    assert article.title == "Already Here"
    assert article.key == existing.key


@pytest.mark.asyncio
async def test_to_dict(Article):
    article = await Article.create(title="Dictify", author="Bob", year=2025, content="text")
    d = article.to_dict()
    assert d["key"] == article.key
    assert d["title"] == "Dictify"
    assert d["author"] == "Bob"
    assert d["content"] == "text"
    assert "embedding" in d
