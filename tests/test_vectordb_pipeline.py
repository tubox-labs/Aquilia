"""
Store-backed pipeline tests — ingest, lineage, chunking, and search.

These open a real ``elips`` database in a temp directory, so they exercise the
native write/read path rather than a mock. Skipped when ``elips`` is absent,
which keeps the suite green on an install that did not ask for vector support.
"""

from __future__ import annotations

import pytest

from aquilia.vectordb import is_available

pytestmark = pytest.mark.skipif(not is_available(), reason="elips is not installed")

from aquilia.vectordb import (  # noqa: E402
    Field,
    KeyField,
    TextField,
    VectorField,
    VectorModel,
)
from aquilia.vectordb.configs import QuantizationConfig, VectorStoreConfig  # noqa: E402
from aquilia.vectordb.embedders import CallableEmbedder  # noqa: E402
from aquilia.vectordb.faults import VectorConfigFault, VectorEmbedderFault  # noqa: E402
from aquilia.vectordb.registry import VectorRegistry  # noqa: E402

DIM = 8


def _hashing_embed(texts: list[str]) -> list[list[float]]:
    """Deterministic bag-of-characters embedding, adequate for ranking assertions."""
    vectors = []
    for text in texts:
        vector = [0.0] * DIM
        for char in text.lower():
            vector[ord(char) % DIM] += 1.0
        vectors.append(vector)
    return vectors


class Doc(VectorModel):
    key: str = KeyField(prefix="doc_")
    body: str = TextField(embed=True)
    vector: list[float] = VectorField(dimension=DIM)
    source: str = Field(default="web", indexed=True)
    views: int = Field(default=0, ge=0)

    class Meta:
        collection = "pipeline_docs"
        dimension = DIM


class Article(VectorModel):
    key: str = KeyField()
    content: str = TextField(embed=True, chunk_size=60, chunk_overlap=10)
    vector: list[float] = VectorField(dimension=DIM)
    topic: str = Field(default="general")

    class Meta:
        collection = "pipeline_articles"
        dimension = DIM


@pytest.fixture
async def store(tmp_path):
    """Open an isolated store with a Python-side embedder attached."""
    VectorRegistry.configure(
        [VectorStoreConfig(alias="default", path=str(tmp_path / "vectors"), dimension=DIM, metric="cosine")]
    )
    engine = await VectorRegistry.engine("default")
    engine._text_embedder = CallableEmbedder(_hashing_embed, name="hashing", dimension=DIM)
    try:
        yield engine
    finally:
        await VectorRegistry.shutdown()
        VectorRegistry.reset()


# ── Automated ingest (§3.4) ──────────────────────────────────────────────────


async def test_save_embeds_text_without_an_explicit_vector(store):
    doc = Doc(body="aquilia vector database release", source="release", views=10)
    await doc.save()

    assert doc.key is not None
    fetched = await Doc.vectors.get(doc.key)
    assert fetched.source == "release"
    assert fetched.views == 10


async def test_save_records_embedding_lineage(store):
    doc = Doc(body="provenance is recorded on write")
    await doc.save()

    fetched = await Doc.vectors.get(doc.key)
    assert fetched.lineage is not None
    assert fetched.lineage.provider == "callable"
    assert fetched.lineage.model == "hashing"


async def test_explicit_vector_is_not_overwritten(store):
    supplied = [1.0] + [0.0] * (DIM - 1)
    doc = Doc(body="text present but vector wins", vector=list(supplied))
    await doc.save()

    fetched = await Doc.vectors.query().with_vectors().filter(Doc.key == doc.key).first()
    assert fetched.vector == pytest.approx(supplied)


async def test_text_without_an_embedder_fails_loudly(tmp_path):
    """A store with no embedder must refuse, not write an unvectorized record."""
    VectorRegistry.configure(
        [VectorStoreConfig(alias="default", path=str(tmp_path / "bare"), dimension=DIM, metric="cosine")]
    )
    try:
        with pytest.raises(VectorEmbedderFault, match="no embedder"):
            await Doc(body="nothing can embed this").save()
    finally:
        await VectorRegistry.shutdown()
        VectorRegistry.reset()


async def test_add_many_batches_the_embedding(store):
    docs = [Doc(body=f"document number {n}", views=n) for n in range(5)]
    await Doc.vectors.add_many(docs)

    assert all(d.key is not None for d in docs)
    assert await Doc.vectors.count() == 5


# ── Search (§3.4.2) ──────────────────────────────────────────────────────────


async def test_search_ranks_by_similarity(store):
    await Doc(body="aquilia framework vector search", source="docs").save()
    await Doc(body="tomato pasta cooking recipe", source="food").save()

    hits = await Doc.vectors.query().search("aquilia framework vector", limit=2)
    assert hits
    assert hits[0].record.source == "docs"
    assert hits[0].score >= hits[-1].score


async def test_search_applies_metadata_filters(store):
    await Doc(body="alpha release", source="docs").save()
    await Doc(body="alpha release", source="blog").save()

    hits = await Doc.vectors.query().filter(source="blog").search("alpha release", limit=5)
    assert {h.record.source for h in hits} == {"blog"}


async def test_prompt_template_is_applied_to_the_query(store):
    seen: list[str] = []

    def capture(texts):
        seen.extend(texts)
        return _hashing_embed(texts)

    store._text_embedder = CallableEmbedder(capture, name="capture", dimension=DIM)
    await Doc(body="indexed document").save()
    seen.clear()

    await Doc.vectors.query().search("a question", prompt_template="query: {text}")
    assert seen == ["query: a question"]


async def test_min_score_filters_weak_hits(store):
    await Doc(body="exactly this text").save()
    hits = await Doc.vectors.query().min_score(0.999).search("completely unrelated words")
    assert hits == []


async def test_explain_reports_the_plan(store):
    await Doc(body="planned").save()
    plan = await Doc.vectors.query().explain()
    assert "strategy" in plan
    assert "full_scan" in plan


# ── records() / rows() (§1.2) ────────────────────────────────────────────────


async def test_records_is_the_vector_native_terminal(store):
    await Doc(body="one", source="a").save()
    await Doc(body="two", source="b").save()

    records = await Doc.vectors.query().filter(source="a").records()
    assert [r.source for r in records] == ["a"]


async def test_rows_still_works_but_warns(store):
    await Doc(body="legacy caller").save()

    with pytest.deprecated_call():
        records = await Doc.vectors.query().rows()
    assert len(records) == 1


# ── Lineage filtering (§3.6.1) ───────────────────────────────────────────────


async def test_lineage_lookup_matches_written_records(store):
    await Doc(body="written by the hashing embedder").save()

    matched = await Doc.vectors.query().filter(lineage__model="hashing").records()
    missed = await Doc.vectors.query().filter(lineage__model="some-other-model").records()

    assert len(matched) == 1
    assert missed == []


# ── Chunking (§3.5) ──────────────────────────────────────────────────────────


async def test_long_text_fans_out_into_chunk_records(store):
    body = "Aquilia is a manifest-first framework. " * 6
    article = Article(key="article_101", content=body, topic="framework")
    await article.save()

    # One parent plus its chunks.
    assert await Article.vectors.count() > 1


async def test_chunk_records_carry_placement(store):
    body = "Aquilia is a manifest-first framework. " * 6
    await Article(key="article_202", content=body).save()

    hits = await Article.vectors.query().search("manifest framework", limit=5)
    chunked = [h for h in hits if h.record.chunk is not None]

    assert chunked, "expected at least one chunk hit"
    for hit in chunked:
        chunk = hit.record.chunk
        assert chunk.ordinal >= 0
        assert chunk.char_end > chunk.char_start
        assert chunk.document_key


async def test_short_text_is_not_chunked(store):
    await Article(key="article_303", content="Too short to split.").save()
    assert await Article.vectors.count() == 1


# ── Quantization (§1.1 item 3) ───────────────────────────────────────────────


async def test_quantize_requires_a_configured_codec(store):
    await Doc(body="uncompressed").save()
    with pytest.raises(VectorConfigFault, match="no quantization codec"):
        await Doc.vectors.quantize()


async def test_quantization_config_reaches_the_engine(tmp_path):
    config = VectorStoreConfig(
        alias="default",
        path=str(tmp_path / "quantized"),
        dimension=DIM,
        metric="cosine",
        quantization=QuantizationConfig(codec="sq8"),
    )
    VectorRegistry.configure([config])
    try:
        engine = await VectorRegistry.engine("default")
        assert engine.config.quantization.codec == "sq8"
        assert engine.config.quantization.enabled
    finally:
        await VectorRegistry.shutdown()
        VectorRegistry.reset()


def test_quantization_config_rejects_a_bad_codec():
    with pytest.raises(ValueError, match="must be 'none'"):
        QuantizationConfig(codec="lzma")


def test_quantization_config_rejects_out_of_range_bits():
    with pytest.raises(ValueError, match="between 4 and 8"):
        QuantizationConfig(codec="pq", pq_bits=12)


# ── Telemetry (§1.1 item 8) ──────────────────────────────────────────────────


async def test_stats_reports_per_collection_counts(store):
    await Doc(body="counted").save()

    stats = await store.stats()
    assert stats["ok"] is True
    assert stats["alias"] == "default"

    names = {c["name"] for c in stats["collections"]}
    assert "pipeline_docs" in names


async def test_pending_writes_is_exposed(store):
    await Doc(body="written").save()
    assert isinstance(await Doc.vectors.pending_writes(), int)


async def test_rebuild_runs_against_a_live_collection(store):
    await Doc(body="indexed").save()
    await Doc.vectors.rebuild()
    assert await Doc.vectors.count() == 1


# ── Dimension guard (§4 embedders) ───────────────────────────────────────────


async def test_embedder_dimension_mismatch_fails_at_open(tmp_path):
    """Discovering this at boot beats failing on every single write."""
    from aquilia.vectordb.configs import EmbedderOptions

    VectorRegistry.configure(
        [
            VectorStoreConfig(
                alias="default",
                path=str(tmp_path / "mismatch"),
                dimension=DIM,
                metric="cosine",
                embedder=EmbedderOptions(provider="uri", uri="local:default", dimension=DIM * 2),
            )
        ]
    )
    try:
        with pytest.raises(VectorConfigFault, match="dimension"):
            await VectorRegistry.engine("default")
    finally:
        await VectorRegistry.shutdown()
        VectorRegistry.reset()
