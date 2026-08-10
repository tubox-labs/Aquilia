"""
Unified field architecture, dual-syntax expressions, EQL, embedders, chunking.

Covers the parts of the vectordb implementation plan that are declaration-time
or pure-Python, so they run without ``elips`` installed. The store-backed
behaviour they feed into lives in ``test_vectordb_pipeline.py``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

import pytest

from aquilia.vectordb import (
    VF,
    Dimension,
    Field,
    FieldExpression,
    Key,
    KeyField,
    LinkField,
    NumericConstraints,
    PayloadField,
    ScoreField,
    StringConstraints,
    Text,
    TextField,
    VectorField,
    VectorModel,
)
from aquilia.vectordb.chunking import (
    Chunk,
    RecursiveCharacterChunker,
    SentenceChunker,
    is_chunk_key,
    parent_key_of,
)
from aquilia.vectordb.embedders import (
    CallableEmbedder,
    EmbeddingLineage,
    FastEmbedder,
    LocalEmbedder,
    OllamaEmbedder,
    OpenAIEmbedder,
    SentenceTransformersEmbedder,
    resolve_embedder,
)
from aquilia.vectordb.eql import parse_eql
from aquilia.vectordb.faults import (
    VectorChunkingFault,
    VectorEmbedderFault,
    VectorEQLFault,
    VectorQueryFault,
    VectorSchemaFault,
    VectorValidationFault,
)
from aquilia.vectordb.filters import FilterCompiler

DIM = 8


# ── Style 1: direct field assignment (§2.4) ──────────────────────────────────


class Document(VectorModel):
    key: str = KeyField(prefix="doc_")
    body: str = TextField(embed=True, min_length=1, max_length=8192)
    vector: list[float] = VectorField(dimension=DIM)
    source: str = Field(default="web", indexed=True, min_length=1, max_length=256)
    views: int = Field(default=0, ge=0)
    score: float | None = ScoreField()
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Meta:
        collection = "fields_documents"
        dimension = DIM


def test_assigned_fields_route_to_slots():
    schema = Document._vfields
    assert schema.key_attr == "key"
    assert schema.text_attr == "body"
    assert schema.vector_attr == "vector"
    assert schema.score_attr == "score"
    assert schema.dimension == DIM


def test_assigned_fields_become_payloads():
    payloads = Document._vfields.payloads
    # `body` is both the text slot and a retrievable payload.
    assert set(payloads) == {"body", "source", "views", "created_at"}
    assert payloads["source"].indexed is True


def test_field_defaults_apply_on_construction():
    doc = Document(body="hello")
    assert doc.source == "web"
    assert doc.views == 0
    assert isinstance(doc.created_at, datetime)


def test_default_factory_runs_per_instance():
    """A shared mutable default would make two records alias one object."""
    first = Document(body="a")
    second = Document(body="b")
    assert first.created_at is not second.created_at


def test_key_field_prefix_shapes_generated_keys():
    generated = Document._vfields.key_field.generate()
    assert generated.startswith("doc_")


def test_autogenerate_false_rejects_an_unkeyed_save():
    class Manual(VectorModel):
        key: str = KeyField(autogenerate=False)
        body: str = TextField()

        class Meta:
            collection = "manual_keys"
            dimension = DIM

    import asyncio

    with pytest.raises(VectorValidationFault):
        asyncio.run(Manual(body="x").save())


# ── Style 2: Annotated syntax (§2.4) ─────────────────────────────────────────


class AnnotatedDoc(VectorModel):
    key: Annotated[str, KeyField(prefix="a_")]
    body: Annotated[str, TextField(embed=True, min_length=1)]
    vector: Annotated[list[float], VectorField(dimension=DIM)]
    source: Annotated[str, Field(indexed=True, max_length=256)] = "web"
    views: Annotated[int, Field(ge=0, le=150)] = 0

    class Meta:
        collection = "annotated_documents"


def test_annotated_fields_route_identically():
    schema = AnnotatedDoc._vfields
    assert (schema.key_attr, schema.text_attr, schema.vector_attr) == ("key", "body", "vector")
    assert schema.dimension == DIM


def test_annotated_assignment_supplies_the_default():
    doc = AnnotatedDoc(body="x")
    assert doc.source == "web"
    assert doc.views == 0


def test_declaring_a_field_twice_is_rejected():
    """Assigned and Annotated declarations disagree with no principled winner."""
    with pytest.raises(VectorSchemaFault, match="declares a field twice"):

        class Doubled(VectorModel):
            key: Annotated[str, KeyField()] = KeyField()
            body: str = TextField()

            class Meta:
                collection = "doubled"
                dimension = DIM


def test_legacy_markers_still_work_alongside_fields():
    """§6 Phase 1 requires the legacy syntax to keep working unchanged."""

    class Legacy(VectorModel):
        key: Annotated[str, Key()]
        body: Annotated[str, Text()]
        embedding: Annotated[list[float], Dimension(DIM)]

        class Meta:
            collection = "legacy_markers"

    schema = Legacy._vfields
    assert (schema.key_attr, schema.text_attr, schema.vector_attr) == ("key", "body", "embedding")
    assert schema.fields == {}


# ── Constraints (§2.3) ───────────────────────────────────────────────────────


def test_numeric_constraints_reject_out_of_range():
    doc = Document(body="x", views=-1)
    with pytest.raises(VectorValidationFault):
        doc.validate()


def test_string_constraints_reject_too_long():
    doc = Document(body="x", source="s" * 300)
    with pytest.raises(VectorValidationFault):
        doc.validate()


def test_exclusive_bounds_differ_from_inclusive():
    class Bounded(VectorModel):
        key: str = KeyField()
        body: str = TextField()
        ratio: float = Field(default=0.5, gt=0.0, lt=1.0)

        class Meta:
            collection = "bounded"
            dimension = DIM

    Bounded(body="x", ratio=0.5).validate()
    with pytest.raises(VectorValidationFault):
        Bounded(body="x", ratio=0.0).validate()
    with pytest.raises(VectorValidationFault):
        Bounded(body="x", ratio=1.0).validate()


def test_multiple_of_uses_decimal_arithmetic():
    """0.3 % 0.1 is non-zero in binary float; the validator must not be fooled."""

    class Stepped(VectorModel):
        key: str = KeyField()
        body: str = TextField()
        amount: float = Field(default=0.0, multiple_of=0.1)

        class Meta:
            collection = "stepped"
            dimension = DIM

    Stepped(body="x", amount=0.3).validate()
    with pytest.raises(VectorValidationFault):
        Stepped(body="x", amount=0.25).validate()


def test_constraint_containers_merge_with_keywords():
    field = Field(constraints=StringConstraints(min_length=2, max_length=64), max_length=32)
    # A keyword narrows the shared bundle rather than being overridden by it.
    assert field.string_constraints.max_length == 32
    assert field.string_constraints.min_length == 2


def test_numeric_container_populates_unset_rules():
    field = Field(constraints=NumericConstraints(ge=0, le=150))
    assert field.constraint_kwargs() == {"ge": 0, "le": 150}


def test_strip_whitespace_normalizes_before_validation():
    class Trimmed(VectorModel):
        key: str = KeyField()
        body: str = TextField()
        label: str = Field(default="", min_length=1, strip_whitespace=True)

        class Meta:
            collection = "trimmed"
            dimension = DIM

    record = Trimmed(body="x", label="  hello  ")
    record.validate()
    assert record.label == "hello"

    with pytest.raises(VectorValidationFault):
        Trimmed(body="x", label="   ").validate()


def test_default_and_default_factory_are_mutually_exclusive():
    with pytest.raises(ValueError, match="one or the other"):
        Field(default=1, default_factory=lambda: 2)


def test_alias_overrides_the_storage_key():
    class Aliased(VectorModel):
        key: str = KeyField()
        body: str = TextField()
        slug: str = Field(default="", alias="url_slug")

        class Meta:
            collection = "aliased"
            dimension = DIM

    assert Aliased._vfields.payloads["slug"].key == "url_slug"
    assert "url_slug" in Aliased._vfields.payload_keys


# ── Dual-syntax expressions (§4.2) ───────────────────────────────────────────


def test_comparison_operators_build_expressions():
    assert isinstance(Document.views >= 10, FieldExpression)
    for expr, op in (
        (Document.views == 1, "eq"),
        (Document.views != 1, "ne"),
        (Document.views >= 1, "gte"),
        (Document.views > 1, "gt"),
        (Document.views <= 1, "lte"),
        (Document.views < 1, "lt"),
    ):
        assert expr.op == op
        assert expr.attr == "views"


def test_fluent_helpers_build_expressions():
    assert Document.source.in_(["web", "api"]).op == "in"
    assert Document.source.contains("rel").op == "contains"
    assert Document.source.startswith("AQ").op == "startswith"
    assert Document.source.endswith(".md").op == "endswith"
    assert Document.views.between(10, 100).value == (10, 100)


def test_expressions_compose_into_trees():
    tree = ((Document.views >= 10) & (Document.source == "web")) | ~(Document.source == "draft")
    assert isinstance(tree, VF)


def test_expression_truthiness_raises():
    """`if Doc.views >= 10:` is a filter that was never applied."""
    with pytest.raises(VectorQueryFault, match="no boolean value"):
        bool(Document.views >= 10)


def test_instance_access_returns_the_value_not_the_field():
    doc = Document(body="x", views=42)
    assert doc.views == 42
    assert isinstance(Document.views, PayloadField)


def _compile(*nodes, **lookups):
    return FilterCompiler(Document._vfields).compile(tuple(nodes), lookups)


def test_all_three_syntaxes_compile_to_the_same_filter():
    """§4.2.3: keyword, expression, and EQL forms are interchangeable."""
    from aquilia.vectordb.expressions import to_vf

    keyword = _compile(**{"source": "docs", "views__gte": 10})
    expression = _compile(to_vf(Document.source == "docs") & to_vf(Document.views >= 10))
    eql = _compile(to_vf("source = 'docs' AND views >= 10"))

    payloads = [
        {"source": "docs", "views": 10},
        {"source": "docs", "views": 9},
        {"source": "web", "views": 50},
    ]
    for payload in payloads:
        verdicts = {
            keyword.native.matches(payload),
            expression.native.matches(payload),
            eql.native.matches(payload),
        }
        assert len(verdicts) == 1, f"syntaxes disagreed on {payload}"


# ── EQL (§4.3) ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "source",
    [
        "source = 'docs'",
        "views >= 10 AND source = 'web'",
        "NOT (views < 10 OR source = 'draft')",
        "source IN ['web', 'api']",
        "source CONTAINS 'rel'",
        "source STARTSWITH 'AQ'",
        "source ENDSWITH '.md'",
        "views != 3",
        "source NOT IN ['spam']",
    ],
)
def test_eql_parses_supported_forms(source):
    assert isinstance(parse_eql(source), VF)


@pytest.mark.parametrize(
    "source",
    ["", "   ", "views >=", "views ?? 3", "views = 1 AND", "(views = 1", "views = 1)", "= 5"],
)
def test_eql_rejects_malformed_input(source):
    with pytest.raises(VectorEQLFault):
        parse_eql(source)


def test_eql_fault_carries_a_position():
    with pytest.raises(VectorEQLFault) as caught:
        parse_eql("views ?? 3")
    assert caught.value.metadata["position"] == 6


def test_eql_does_not_evaluate_python():
    """The parser is hand-written precisely so this is inert text."""
    with pytest.raises(VectorEQLFault):
        parse_eql("__import__('os').system('true')")


def test_eql_boolean_and_null_literals():
    assert parse_eql("draft = true").lookups == {"draft__exact": True}
    assert parse_eql("draft = false").lookups == {"draft__exact": False}
    assert parse_eql("score IS NULL").lookups == {"score__isnull": True}
    assert parse_eql("score IS NOT NULL").lookups == {"score__isnull": False}


def test_eql_keywords_are_case_insensitive():
    assert parse_eql("views >= 10 and source = 'x'").children
    assert parse_eql("views >= 10 AND source = 'x'").children


def test_eql_accepts_both_list_bracket_styles():
    """`IN ('a','b')` is the spelling a SQL-literate user types first."""
    bracket = parse_eql("kind IN ['post', 'page']")
    paren = parse_eql("kind IN ('post', 'page')")
    assert bracket.lookups == paren.lookups == {"kind__in": ["post", "page"]}


def test_eql_between_consumes_its_own_and():
    """The AND inside BETWEEN is part of the operator, not a conjunction."""
    node = parse_eql("views BETWEEN 1 AND 5")
    assert node.lookups == {"views__range": (1, 5)}
    assert not node.children


def test_eql_between_composes_with_a_real_conjunction():
    node = parse_eql("views BETWEEN 1 AND 5 AND source = 'docs'")
    assert node.connector == VF.AND
    assert len(node.children) == 2


def test_eql_between_without_and_is_rejected():
    with pytest.raises(VectorEQLFault, match="expected AND"):
        parse_eql("views BETWEEN 1 5")


# ── Lineage filtering (§3.6.1) ───────────────────────────────────────────────


class _Lineage:
    def __init__(self, provider="", model="", revision=""):
        self.provider = provider
        self.model = model
        self.revision = revision


class _Record:
    def __init__(self, lineage):
        self.lineage = lineage


def test_lineage_lookups_compile_to_residuals():
    from aquilia.vectordb.filters import apply_residuals

    compiled = _compile(**{"lineage__model": "all-MiniLM-L6-v2"})
    # Provenance is not in the payload, so nothing pushes down.
    assert compiled.native is None
    assert len(compiled.residuals) == 1

    match = _Record(_Lineage(model="all-MiniLM-L6-v2"))
    miss = _Record(_Lineage(model="text-embedding-3-small"))
    none = _Record(None)

    kept = apply_residuals([match, miss, none], compiled.residuals)
    assert kept == [match]


def test_unknown_lineage_attribute_is_rejected():
    from aquilia.vectordb.faults import VectorLookupFault

    with pytest.raises(VectorLookupFault, match="unknown lineage attribute"):
        _compile(**{"lineage__nonsense": "x"})


def test_lineage_range_lookup_is_rejected():
    from aquilia.vectordb.faults import VectorLookupFault

    with pytest.raises(VectorLookupFault, match="not meaningful"):
        _compile(**{"lineage__model__gte": "x"})


# ── Embedders (§3.3) ─────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "uri,expected",
    [
        ("sentence-transformers/all-MiniLM-L6-v2", SentenceTransformersEmbedder),
        ("hf/all-MiniLM-L6-v2", SentenceTransformersEmbedder),
        ("openai/text-embedding-3-small", OpenAIEmbedder),
        ("fastembed/BAAI/bge-small-en-v1.5", FastEmbedder),
        ("ollama/nomic-embed-text", OllamaEmbedder),
        ("local:default", LocalEmbedder),
    ],
)
def test_embedder_uris_resolve_to_adapters(uri, expected):
    embedder = resolve_embedder(uri)
    assert isinstance(embedder, expected)
    assert not embedder.loaded, "resolution must not load the backend"


def test_embedder_uri_keeps_multi_segment_model_names():
    assert resolve_embedder("fastembed/BAAI/bge-small-en-v1.5").model == "BAAI/bge-small-en-v1.5"


def test_unknown_embedder_provider_is_rejected():
    with pytest.raises(VectorEmbedderFault, match="unknown embedder provider"):
        resolve_embedder("nope/model")


def test_callable_resolves_to_the_callable_adapter():
    assert isinstance(resolve_embedder(lambda texts: [[0.0]] * len(texts)), CallableEmbedder)


def test_embedder_instance_passes_through():
    original = CallableEmbedder(lambda texts: [[0.0]] * len(texts))
    assert resolve_embedder(original) is original


async def test_embedder_normalizes_to_unit_length():
    embedder = CallableEmbedder(lambda texts: [[3.0, 4.0] for _ in texts])
    vectors = await embedder.embed(["a"])
    assert pytest.approx(sum(x * x for x in vectors[0]) ** 0.5) == 1.0


async def test_embedder_can_skip_normalization():
    embedder = CallableEmbedder(lambda texts: [[3.0, 4.0] for _ in texts], normalize=False)
    assert await embedder.embed(["a"]) == [[3.0, 4.0]]


async def test_misaligned_batch_is_rejected():
    """A short batch would silently attach vectors to the wrong records."""
    embedder = CallableEmbedder(lambda texts: [[1.0, 0.0]])
    with pytest.raises(VectorEmbedderFault, match="misaligned"):
        await embedder.embed(["a", "b"])


async def test_dimension_is_discovered_by_probing():
    embedder = CallableEmbedder(lambda texts: [[0.0] * 5 for _ in texts])
    assert await embedder.dimension() == 5


async def test_prompt_template_wraps_stored_text():
    seen: list[str] = []

    def capture(texts):
        seen.extend(texts)
        return [[1.0] for _ in texts]

    embedder = CallableEmbedder(capture, prompt_template="passage: {text}")
    await embedder.embed(["hello"])
    assert seen == ["passage: hello"]


async def test_batching_respects_batch_size():
    batches: list[int] = []

    def capture(texts):
        batches.append(len(texts))
        return [[1.0] for _ in texts]

    await CallableEmbedder(capture, batch_size=2).embed(["a", "b", "c", "d", "e"])
    assert batches == [2, 2, 1]


def test_fingerprint_distinguishes_vector_spaces():
    a = CallableEmbedder(lambda t: [[0.0]], name="a", dimension=8)
    b = CallableEmbedder(lambda t: [[0.0]], name="b", dimension=8)
    c = CallableEmbedder(lambda t: [[0.0]], name="a", dimension=16)
    assert a.fingerprint != b.fingerprint
    assert a.fingerprint != c.fingerprint


def test_lineage_records_provenance():
    lineage = CallableEmbedder(lambda t: [[0.0]], name="m", dimension=4).lineage()
    assert isinstance(lineage, EmbeddingLineage)
    assert lineage.provider == "callable"
    assert lineage.model == "m"
    assert lineage.attributes["dimension"] == "4"


async def test_missing_backend_names_the_install():
    with pytest.raises(VectorEmbedderFault, match="pip install"):
        await resolve_embedder("sentence-transformers/all-MiniLM-L6-v2").embed(["x"])


# ── Chunking (§3.5) ──────────────────────────────────────────────────────────


def test_short_text_yields_one_chunk():
    chunks = RecursiveCharacterChunker(chunk_size=500).split("short")
    assert len(chunks) == 1
    assert chunks[0].text == "short"
    assert (chunks[0].char_start, chunks[0].char_end) == (0, 5)


def test_empty_text_yields_no_chunks():
    assert RecursiveCharacterChunker().split("") == []


def test_chunks_cover_the_source_in_order():
    text = "Aquilia is a framework. " * 40
    chunks = RecursiveCharacterChunker(chunk_size=100, chunk_overlap=20).split(text)

    assert len(chunks) > 1
    assert [c.ordinal for c in chunks] == list(range(len(chunks)))
    for chunk in chunks:
        assert text[chunk.char_start : chunk.char_end] == chunk.text
    assert chunks[0].char_start == 0
    assert chunks[-1].char_end == len(text)


def test_chunker_prefers_paragraph_boundaries():
    text = "First paragraph here.\n\n" + ("x" * 60)
    chunks = RecursiveCharacterChunker(chunk_size=40, chunk_overlap=0).split(text)
    assert chunks[0].text.strip() == "First paragraph here."


def test_overlap_repeats_text_between_chunks():
    text = "abcdefghij" * 20
    chunks = RecursiveCharacterChunker(chunk_size=50, chunk_overlap=10).split(text)
    assert chunks[1].char_start < chunks[0].char_end


def test_overlap_must_be_smaller_than_size():
    """Equal values advance zero characters per step — an infinite loop."""
    with pytest.raises(VectorChunkingFault, match="never terminate"):
        RecursiveCharacterChunker(chunk_size=100, chunk_overlap=100)


def test_non_positive_chunk_size_is_rejected():
    with pytest.raises(VectorChunkingFault):
        RecursiveCharacterChunker(chunk_size=0)


def test_sentence_chunker_never_splits_a_sentence():
    text = "One here. Two there. Three everywhere. Four somewhere."
    for chunk in SentenceChunker(chunk_size=25, chunk_overlap=0).split(text):
        assert chunk.text.strip()
        assert chunk.text.strip()[-1] in ".!?"


def test_sentence_chunker_emits_an_oversized_sentence_whole():
    text = "x" * 200 + "."
    chunks = SentenceChunker(chunk_size=50, chunk_overlap=0).split(text)
    assert len(chunks) == 1


def test_chunk_keys_derive_from_the_parent():
    chunk = Chunk(text="t", ordinal=3, char_start=0, char_end=1)
    assert chunk.key_for("article_101") == "article_101#chunk:3"


def test_parent_key_round_trips():
    assert parent_key_of("article_101#chunk:3") == "article_101"
    assert parent_key_of("article_101") is None
    assert is_chunk_key("article_101#chunk:0")
    assert not is_chunk_key("article_101")


def test_text_field_chunk_size_builds_a_chunker():
    field = TextField(chunk_size=200, chunk_overlap=20)
    chunker = field.resolve_chunker()
    assert isinstance(chunker, RecursiveCharacterChunker)
    assert chunker.chunk_size == 200


def test_text_field_without_chunking_resolves_to_none():
    assert TextField().resolve_chunker() is None


def test_chunk_size_and_chunker_are_mutually_exclusive():
    with pytest.raises(ValueError, match="one or the other"):
        TextField(chunk_size=100, chunker=RecursiveCharacterChunker())


# ── LinkField (§2.2) ─────────────────────────────────────────────────────────


def test_link_field_registers_as_a_link_and_a_payload():
    class Linked(VectorModel):
        key: str = KeyField()
        body: str = TextField()
        author_id: int = LinkField("mymod:User", on_delete="detach")

        class Meta:
            collection = "linked_fields"
            dimension = DIM

    assert "author_id" in Linked._vlinks
    assert Linked._vfields.link_attrs == frozenset({"author_id"})
    # A link is an ordinary payload too — that is how the key reaches storage.
    assert "author_id" in Linked._vfields.payloads
