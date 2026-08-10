"""
AquilaVectorDB — Embedder adapters.

Turns text into vectors (§3.3 of the implementation plan). One protocol,
several backends, and a URI syntax that names a backend without importing it::

    "sentence-transformers/all-MiniLM-L6-v2"   local HuggingFace model
    "openai/text-embedding-3-small"            cloud API
    "fastembed/BAAI/bge-small-en-v1.5"         ONNX, CPU-optimised
    "ollama/nomic-embed-text"                  local Ollama daemon
    "local:default"                            elips' built-in C++ embedder

Every provider is an optional dependency
----------------------------------------

Nothing here imports ``sentence_transformers``, ``openai``, or any other
provider at module scope. The import happens inside :meth:`BaseEmbedder.load`,
on first use, and a missing package surfaces as
:class:`~aquilia.vectordb.faults.VectorEmbedderFault` naming the exact
``pip install`` to run — not as a ``ModuleNotFoundError`` from four frames deep
inside a save.

Blocking work is offloaded
--------------------------

A local transformer model is CPU-bound Python and a cloud API is network-bound;
both would stall the event loop if called inline. Sync backends run through
:class:`~aquilia.vectordb.pool.VectorPool` (the same pool elips calls use);
natively-async backends are awaited directly. :meth:`BaseEmbedder.embed`
presents one async surface over both, so the ingest pipeline never branches on
which kind it holds.

Identity is part of the store
-----------------------------

An embedder's :attr:`~BaseEmbedder.fingerprint` identifies the vector space it
produces. Two models that embed the same text differently produce vectors that
must never be compared, so the fingerprint is recorded in each record's
lineage and checked at boot — see
:class:`~aquilia.vectordb.faults.VectorEmbedderMismatchFault`.
"""

from __future__ import annotations

import hashlib
import logging
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, ClassVar, Protocol, runtime_checkable

from aquilia.vectordb.faults import VectorEmbedderFault

logger = logging.getLogger("aquilia.vectordb.embedders")

#: Texts per provider call when the caller does not say otherwise. Bounded
#: because a cloud provider rejects oversized batches and a local model's peak
#: memory scales with the batch.
DEFAULT_BATCH_SIZE = 32

#: Texts an embedder remembers, per instance. Embedding is deterministic for a
#: fixed model, so a repeat text is a pure waste of a network round trip or a
#: transformer forward pass — the same query string recurring across requests is
#: the common case for search. Bounded because vectors are large: 1000 entries
#: of a 1536-dimension model is roughly 6 MB, which is a cache, not a leak.
#: Set ``cache_size=0`` to disable.
DEFAULT_CACHE_SIZE = 1000


@dataclass(frozen=True, slots=True)
class EmbeddingLineage:
    """
    Provenance for one embedding.

    Recorded alongside every vector written through an embedder, so a record can
    always answer "which model produced this, and is it still the one we use?".
    Mirrors the native ``elips.EmbeddingLineage`` fields exactly, which is what
    lets it round-trip through storage without translation.

    Attributes:
        provider: Backend family, e.g. ``"sentence-transformers"``.
        model: Model identifier, e.g. ``"all-MiniLM-L6-v2"``.
        revision: Model revision or version pin. Empty when unpinned.
        attributes: Free-form extras — ``dimension``, ``fingerprint``, backend.
    """

    provider: str
    model: str
    revision: str = ""
    attributes: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize for health output and CLI reporting."""
        return {
            "provider": self.provider,
            "model": self.model,
            "revision": self.revision,
            "attributes": dict(self.attributes),
        }

    @classmethod
    def from_native(cls, native: Any) -> EmbeddingLineage | None:
        """Build from an ``elips.EmbeddingLineage``, or ``None`` when absent."""
        if native is None:
            return None
        return cls(
            provider=str(getattr(native, "provider", "") or ""),
            model=str(getattr(native, "model", "") or ""),
            revision=str(getattr(native, "revision", "") or ""),
            attributes={str(k): str(v) for k, v in dict(getattr(native, "attributes", {}) or {}).items()},
        )


@runtime_checkable
class Embedder(Protocol):
    """
    Structural contract every embedder satisfies.

    Declared as a ``Protocol`` so a project can supply its own embedder without
    subclassing anything — anything with these three members is accepted.
    """

    provider: str
    model: str

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Return one vector per input text, in order."""
        ...


class BaseEmbedder:
    """
    Base class for embedder adapters.

    Subclasses implement :meth:`load` (acquire the client or model) and one of
    :meth:`_embed_sync` or :meth:`_embed_async`. Everything else — batching,
    pool offload, dimension discovery, lineage, fingerprinting — is shared.

    Args:
        model: Model identifier for the backend.
        batch_size: Texts per provider call.
        normalize: L2-normalize returned vectors. Leave on with ``cosine``,
            where an unnormalized vector makes distances incomparable between
            records of differing magnitude.
        dimension: Vector length, when known ahead of loading. Discovered by
            embedding a probe string when omitted.
        prompt_template: Applied to *stored* text before embedding, for
            asymmetric models (``"passage: {text}"`` for E5). The query-side
            counterpart is ``VectorQuery.prompt()``.
    """

    #: Backend family name, recorded in lineage. Subclasses override.
    provider: ClassVar[str] = "base"

    #: Package to install when the backend is missing, for the fault message.
    install_hint: ClassVar[str] = ""

    def __init__(
        self,
        model: str,
        *,
        batch_size: int = DEFAULT_BATCH_SIZE,
        normalize: bool = True,
        dimension: int | None = None,
        prompt_template: str | None = None,
        cache_size: int = DEFAULT_CACHE_SIZE,
    ) -> None:
        self.model = model
        self.batch_size = max(1, int(batch_size))
        self.normalize = bool(normalize)
        self._dimension = dimension
        self.prompt_template = prompt_template
        self._client: Any = None
        self._loaded = False
        self._cache_size = max(0, int(cache_size))
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._cache_hits = 0
        self._cache_misses = 0

    # ── Lifecycle ────────────────────────────────────────────────────────

    def load(self) -> None:
        """
        Acquire the underlying model or client.

        Called on first use, inside the thread pool. Subclasses import their
        provider package here — never at module scope — so an unused backend
        costs nothing and a missing one fails with an actionable message.
        """
        raise NotImplementedError

    def _ensure_loaded(self) -> None:
        """Load once, idempotently."""
        if not self._loaded:
            self.load()
            self._loaded = True

    @property
    def loaded(self) -> bool:
        """Whether the backend has been initialized."""
        return self._loaded

    # ── Embedding ────────────────────────────────────────────────────────

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Blocking embed. Implemented by synchronous backends."""
        raise NotImplementedError

    async def _embed_async(self, texts: list[str]) -> list[list[float]]:
        """
        Native async embed. Implemented by network backends.

        Defaults to running :meth:`_embed_sync` in the vector thread pool, which
        is what makes a sync backend usable from the async pipeline without the
        caller knowing which kind it holds.
        """
        from aquilia.vectordb.registry import VectorRegistry

        def run() -> list[list[float]]:
            self._ensure_loaded()
            return self._embed_sync(texts)

        return await VectorRegistry.pool().run(run)

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """
        Embed a list of texts.

        Args:
            texts: Input strings.

        Returns:
            One vector per input, in the same order.

        Raises:
            VectorEmbedderFault: When the backend is unavailable, or returns a
                different number of vectors than texts given — which would
                otherwise misalign every vector against the wrong record, a
                corruption no later check could detect.

        Notes:
            Cached per prepared text, so only the misses reach the backend. A
            partially-cached batch sends just its misses and reassembles the
            result in input order — which is the common shape for a search
            workload where one popular query recurs among novel ones.
        """
        if not texts:
            return []

        prepared = [self._apply_template(t) for t in texts]

        # Resolve what is already known, and collect the rest. `pending` maps a
        # unique missing text to the output slots waiting on it, so a batch
        # repeating one string embeds it once.
        out: list[list[float] | None] = [None] * len(prepared)
        pending: dict[str, list[int]] = {}

        for index, text in enumerate(prepared):
            hit = self._cache_get(text)
            if hit is not None:
                out[index] = list(hit)
            else:
                pending.setdefault(text, []).append(index)

        misses = list(pending)
        for start in range(0, len(misses), self.batch_size):
            chunk = misses[start : start + self.batch_size]
            try:
                vectors = await self._embed_async(chunk)
            except VectorEmbedderFault:
                raise
            except Exception as exc:
                raise VectorEmbedderFault(
                    reason=f"{self.provider}/{self.model} failed to embed a batch of {len(chunk)}: {exc}",
                ) from exc

            if len(vectors) != len(chunk):
                raise VectorEmbedderFault(
                    reason=(
                        f"{self.provider}/{self.model} returned {len(vectors)} vectors for "
                        f"{len(chunk)} texts. Vectors would be misaligned against records."
                    ),
                )

            for text, raw in zip(chunk, vectors, strict=True):
                vector = self._normalize(list(map(float, raw)))
                self._cache_put(text, vector)
                for slot in pending[text]:
                    out[slot] = list(vector)

        # Every slot is filled: each was either a cache hit or a member of
        # `pending`, and every pending key was covered by a chunk.
        return [vector for vector in out if vector is not None]

    # ── Cache ────────────────────────────────────────────────────────────

    def _cache_get(self, text: str) -> list[float] | None:
        """Return a cached vector for ``text``, marking it most-recently used."""
        if self._cache_size == 0:
            return None
        hit = self._cache.get(text)
        if hit is None:
            self._cache_misses += 1
            return None
        self._cache.move_to_end(text)
        self._cache_hits += 1
        return hit

    def _cache_put(self, text: str, vector: list[float]) -> None:
        """Store a vector, evicting the least-recently used entry when full."""
        if self._cache_size == 0:
            return
        self._cache[text] = vector
        self._cache.move_to_end(text)
        while len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    def cache_stats(self) -> dict[str, int]:
        """Return hit/miss counters and current occupancy, for diagnostics."""
        return {
            "hits": self._cache_hits,
            "misses": self._cache_misses,
            "size": len(self._cache),
            "capacity": self._cache_size,
        }

    def clear_cache(self) -> None:
        """Drop every cached vector. Counters are left intact."""
        self._cache.clear()

    async def embed_one(self, text: str) -> list[float]:
        """Embed a single string."""
        vectors = await self.embed([text])
        return vectors[0]

    def _apply_template(self, text: str) -> str:
        """Wrap stored text in the document-side prompt template, if any."""
        return self.prompt_template.format(text=text) if self.prompt_template else text

    def _normalize(self, vector: list[float]) -> list[float]:
        """L2-normalize when configured; a zero vector is returned unchanged."""
        if not self.normalize:
            return vector
        magnitude = sum(x * x for x in vector) ** 0.5
        if magnitude == 0.0:
            return vector
        return [x / magnitude for x in vector]

    # ── Identity ─────────────────────────────────────────────────────────

    async def dimension(self) -> int:
        """
        Return the vector length this embedder produces.

        Discovered by embedding a probe string when not declared, then cached —
        most backends only reveal their dimension once a model is loaded, and
        guessing it wrong misconfigures the whole store.
        """
        if self._dimension is None:
            probe = await self.embed_one("dimension probe")
            self._dimension = len(probe)
        return self._dimension

    @property
    def fingerprint(self) -> str:
        """
        Stable identifier for the vector space this embedder produces.

        Two embedders sharing a fingerprint produce comparable vectors; two that
        differ do not, whatever their dimensions happen to be. Recorded in
        lineage and checked at boot against the store's manifest.
        """
        material = f"{self.provider}:{self.model}:{self._dimension or 0}:{int(self.normalize)}"
        return hashlib.blake2b(material.encode("utf-8"), digest_size=8).hexdigest()

    def lineage(self) -> EmbeddingLineage:
        """Return the provenance record for vectors this embedder produces."""
        return EmbeddingLineage(
            provider=self.provider,
            model=self.model,
            revision="",
            attributes={
                "fingerprint": self.fingerprint,
                "dimension": str(self._dimension or 0),
                "normalized": str(self.normalize).lower(),
            },
        )

    def _missing(self, exc: Exception) -> VectorEmbedderFault:
        """Build the fault for an absent provider package."""
        hint = f" Install it with: pip install {self.install_hint}" if self.install_hint else ""
        return VectorEmbedderFault(
            reason=f"the {self.provider!r} embedder backend is not installed ({exc}).{hint}",
        )

    def __repr__(self) -> str:
        state = "loaded" if self._loaded else "lazy"
        return f"<{type(self).__name__} {self.provider}/{self.model} {state}>"


# ============================================================================
# Adapters
# ============================================================================


class SentenceTransformersEmbedder(BaseEmbedder):
    """
    Local HuggingFace embeddings via ``sentence-transformers``.

    The default choice for self-hosted semantic search: no network, no API key,
    and quality that is competitive with cloud models at 384–768 dimensions.

    Args:
        model: HuggingFace model id, e.g. ``"all-MiniLM-L6-v2"``.
        device: ``"cpu"``, ``"cuda"``, ``"mps"``, or ``None`` to auto-select.

    Example::

        SentenceTransformersEmbedder("all-MiniLM-L6-v2", device="cpu")
    """

    provider = "sentence-transformers"
    install_hint = "sentence-transformers"

    def __init__(self, model: str = "all-MiniLM-L6-v2", *, device: str | None = None, **kwargs: Any) -> None:
        super().__init__(model, **kwargs)
        self.device = device

    def load(self) -> None:
        """Load the model onto the configured device."""
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise self._missing(exc) from exc

        self._client = SentenceTransformer(self.model, device=self.device)
        if self._dimension is None:
            declared = self._client.get_sentence_embedding_dimension()
            if declared:
                self._dimension = int(declared)

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Encode a batch, letting the library handle its own batching."""
        # normalize_embeddings stays False: BaseEmbedder normalizes uniformly
        # across every backend, so one code path decides magnitude.
        vectors = self._client.encode(texts, convert_to_numpy=True, normalize_embeddings=False)
        return [list(map(float, v)) for v in vectors]


class OpenAIEmbedder(BaseEmbedder):
    """
    Cloud embeddings via the OpenAI API.

    Args:
        model: Embedding model, e.g. ``"text-embedding-3-small"``.
        api_key: API key. Falls back to ``OPENAI_API_KEY``.
        base_url: Override for an OpenAI-compatible gateway.
        dimensions: Request truncated vectors, supported by ``text-embedding-3-*``.

    Notes:
        Natively async — the client is awaited rather than offloaded, since the
        work is network-bound and a thread would only add a hop.

        Text leaves the process. That is inherent to a hosted embedder, but it
        is worth stating plainly: every indexed document is sent to OpenAI.
    """

    provider = "openai"
    install_hint = "openai"

    def __init__(
        self,
        model: str = "text-embedding-3-small",
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        dimensions: int | None = None,
        **kwargs: Any,
    ) -> None:
        kwargs.setdefault("dimension", dimensions)
        kwargs.setdefault("batch_size", 100)
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self.base_url = base_url
        self.dimensions = dimensions

    def load(self) -> None:
        """Construct the async client."""
        try:
            from openai import AsyncOpenAI
        except ImportError as exc:
            raise self._missing(exc) from exc

        import os

        key = self.api_key or os.environ.get("OPENAI_API_KEY")
        if not key:
            raise VectorEmbedderFault(
                reason=(
                    "the 'openai' embedder needs an API key. Pass api_key=, or set "
                    "the OPENAI_API_KEY environment variable."
                ),
            )

        kwargs: dict[str, Any] = {"api_key": key}
        if self.base_url:
            kwargs["base_url"] = self.base_url
        self._client = AsyncOpenAI(**kwargs)

    async def _embed_async(self, texts: list[str]) -> list[list[float]]:
        """Call the embeddings endpoint directly on the event loop."""
        self._ensure_loaded()

        kwargs: dict[str, Any] = {"model": self.model, "input": texts}
        if self.dimensions:
            kwargs["dimensions"] = self.dimensions

        response = await self._client.embeddings.create(**kwargs)
        # Sort by index: the API documents order but does not guarantee it, and
        # a reordered batch would silently attach vectors to the wrong records.
        ordered = sorted(response.data, key=lambda item: item.index)
        return [list(map(float, item.embedding)) for item in ordered]


class FastEmbedder(BaseEmbedder):
    """
    CPU-optimised ONNX embeddings via ``fastembed``.

    Quantized ONNX models with no PyTorch dependency — a good fit for
    containers where a torch install would dominate the image.

    Args:
        model: FastEmbed model id, e.g. ``"BAAI/bge-small-en-v1.5"``.
        cache_dir: Where to cache downloaded model artifacts.
    """

    provider = "fastembed"
    install_hint = "fastembed"

    def __init__(self, model: str = "BAAI/bge-small-en-v1.5", *, cache_dir: str | None = None, **kwargs: Any) -> None:
        super().__init__(model, **kwargs)
        self.cache_dir = cache_dir

    def load(self) -> None:
        """Construct the ONNX embedding model."""
        try:
            from fastembed import TextEmbedding
        except ImportError as exc:
            raise self._missing(exc) from exc

        kwargs: dict[str, Any] = {"model_name": self.model}
        if self.cache_dir:
            kwargs["cache_dir"] = self.cache_dir
        self._client = TextEmbedding(**kwargs)

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Drain the generator fastembed returns."""
        return [list(map(float, v)) for v in self._client.embed(texts)]


class OllamaEmbedder(BaseEmbedder):
    """
    Local embeddings via an Ollama daemon.

    Args:
        model: Ollama model tag, e.g. ``"nomic-embed-text"``.
        host: Daemon base URL.
        timeout: Per-request timeout in seconds.

    Notes:
        Uses Aquilia's own async HTTP client rather than the ``ollama`` package:
        the endpoint is one POST, and reusing the framework's client means the
        embedder inherits its retry, pooling, and timeout behaviour instead of
        carrying a second HTTP stack.
    """

    provider = "ollama"
    install_hint = ""

    def __init__(
        self,
        model: str = "nomic-embed-text",
        *,
        host: str = "http://localhost:11434",
        timeout: float = 60.0,
        **kwargs: Any,
    ) -> None:
        super().__init__(model, **kwargs)
        self.host = host.rstrip("/")
        self.timeout = timeout

    def load(self) -> None:
        """Nothing to acquire — each call is a stateless POST."""
        self._client = None

    async def _embed_async(self, texts: list[str]) -> list[list[float]]:
        """POST each text to ``/api/embeddings``."""
        from aquilia.http import AsyncHTTPClient

        vectors: list[list[float]] = []
        async with AsyncHTTPClient(timeout=self.timeout, raise_for_status=True) as client:
            for text in texts:
                response = await client.post(
                    f"{self.host}/api/embeddings",
                    json={"model": self.model, "prompt": text},
                )
                payload = await response.json()
                embedding = payload.get("embedding")
                if not embedding:
                    raise VectorEmbedderFault(
                        reason=(
                            f"ollama returned no embedding for model {self.model!r}. "
                            f"Is it pulled? Try: ollama pull {self.model}"
                        ),
                    )
                vectors.append(list(map(float, embedding)))
        return vectors


class LocalEmbedder(BaseEmbedder):
    """
    elips' built-in C++ feature-hashing embedder.

    Zero dependencies and no model download: deterministic random projection over
    character n-grams and word bigrams, computed inside the extension. Useful for
    tests, offline development, and lexical-ish retrieval where a transformer is
    more machinery than the task needs.

    Args:
        model: ``"default"`` (3–5 char n-grams, 4 projections) or ``"compact"``
            (3–4 char n-grams, 2 projections).
        dimension: Output length. Required — the C++ embedder projects into
            whatever space it is told to.

    Notes:
        Quality is well below a trained transformer. It is a real embedder for
        the cases above, not a stand-in for semantic search at scale.
    """

    provider = "elips-local"
    install_hint = "'aquilia[vectordb]'"

    def __init__(self, model: str = "default", *, dimension: int = 384, **kwargs: Any) -> None:
        kwargs.setdefault("dimension", dimension)
        super().__init__(model, **kwargs)

    def load(self) -> None:
        """Build the native ``LocalEmbedderConfig``."""
        from aquilia.vectordb._compat import require_elips

        elips = require_elips()
        config_cls = getattr(elips, "LocalEmbedderConfig", None)
        if config_cls is None:
            raise VectorEmbedderFault(
                reason="this elips build has no LocalEmbedderConfig; use a different embedder provider",
            )

        config = config_cls()
        config.model = self.model
        if self._dimension:
            config.dimension = int(self._dimension)
        self._client = config

    def native_config(self) -> Any:
        """
        Return the native config for handing to ``elips.connect(embedder=...)``.

        This embedder is unique in being resolvable *inside* the engine: elips
        computes the vectors itself, outside the vault lock. The Python-side
        :meth:`embed` exists so the same object still satisfies the protocol.
        """
        self._ensure_loaded()
        return self._client

    def _embed_sync(self, texts: list[str]) -> list[list[float]]:
        """Embed through the native describe/embed path."""
        from aquilia.vectordb._compat import require_elips

        elips = require_elips()
        embedder = getattr(elips, "LocalTextEmbedder", None)
        if embedder is None:
            raise VectorEmbedderFault(
                reason=(
                    "this elips build does not expose LocalTextEmbedder to Python. "
                    "Attach it to the store instead of embedding client-side: "
                    "EmbedderOptions(provider='local')."
                ),
            )
        instance = embedder(self._client)
        return [list(map(float, instance.embed(text))) for text in texts]


class CallableEmbedder(BaseEmbedder):
    """
    Adapter around a plain callable.

    The escape hatch for a project-specific model. The callable takes a list of
    strings and returns a list of vectors; it may be sync or async.

    Args:
        fn: The embedding callable, or a ``"module:callable"`` path.
        name: Model name recorded in lineage.
    """

    provider = "callable"

    def __init__(self, fn: Any, *, name: str = "callable", **kwargs: Any) -> None:
        super().__init__(name, **kwargs)
        self._fn = fn

    def load(self) -> None:
        """Resolve a dotted path into the callable it names."""
        if callable(self._fn):
            self._client = self._fn
            return

        from aquilia.vectordb.engine import _resolve_callable_embedder

        self._client = _resolve_callable_embedder(str(self._fn), "embedder")

    async def _embed_async(self, texts: list[str]) -> list[list[float]]:
        """Call the function, awaiting it when it is a coroutine function."""
        import inspect

        self._ensure_loaded()
        result = self._client(texts)
        if inspect.isawaitable(result):
            result = await result
        return [list(map(float, v)) for v in result]


# ============================================================================
# URI resolution
# ============================================================================

#: URI scheme → adapter class. Ordered longest-prefix-first at match time.
PROVIDERS: dict[str, type[BaseEmbedder]] = {
    "sentence-transformers": SentenceTransformersEmbedder,
    "st": SentenceTransformersEmbedder,
    "huggingface": SentenceTransformersEmbedder,
    "hf": SentenceTransformersEmbedder,
    "openai": OpenAIEmbedder,
    "fastembed": FastEmbedder,
    "ollama": OllamaEmbedder,
    "local": LocalEmbedder,
    "elips-local": LocalEmbedder,
}


def resolve_embedder(spec: Any, **kwargs: Any) -> BaseEmbedder:
    """
    Build an embedder from a URI, a callable, or an existing instance.

    Accepted forms:

    ==================================  ====================================
    ``"sentence-transformers/all-..."``  :class:`SentenceTransformersEmbedder`
    ``"openai/text-embedding-3-small"``  :class:`OpenAIEmbedder`
    ``"fastembed/BAAI/bge-small..."``    :class:`FastEmbedder`
    ``"ollama/nomic-embed-text"``        :class:`OllamaEmbedder`
    ``"local:default"``                  :class:`LocalEmbedder`
    a callable                           :class:`CallableEmbedder`
    a :class:`BaseEmbedder`              returned unchanged
    ==================================  ====================================

    Args:
        spec: The embedder specification.
        **kwargs: Forwarded to the adapter — ``batch_size``, ``normalize``,
            ``dimension``, ``device``, ``api_key``, ...

    Returns:
        A ready (but not yet loaded) embedder.

    Raises:
        VectorEmbedderFault: On an unknown provider or an unusable spec.

    Example::

        embedder = resolve_embedder("openai/text-embedding-3-small", dimension=512)
    """
    if isinstance(spec, BaseEmbedder):
        return spec

    if callable(spec):
        return CallableEmbedder(spec, **kwargs)

    if not isinstance(spec, str) or not spec.strip():
        raise VectorEmbedderFault(
            reason=(
                f"cannot resolve an embedder from {type(spec).__name__}. Give a URI "
                f"like 'sentence-transformers/all-MiniLM-L6-v2', a callable, or a "
                f"BaseEmbedder instance."
            ),
        )

    text = spec.strip()

    # `local:model` uses a colon; every other provider uses a slash. Both are
    # accepted for all providers, since the distinction carries no meaning and
    # guessing wrong is a needless failure.
    if ":" in text and "//" not in text:
        scheme, _, remainder = text.partition(":")
    else:
        scheme, _, remainder = text.partition("/")

    adapter = PROVIDERS.get(scheme.lower())
    if adapter is None:
        known = ", ".join(sorted(set(PROVIDERS)))
        raise VectorEmbedderFault(
            reason=f"unknown embedder provider {scheme!r} in {spec!r}. Known providers: {known}",
        )

    model = remainder.strip()
    if model:
        return adapter(model, **kwargs)
    return adapter(**kwargs)


__all__ = [
    "DEFAULT_BATCH_SIZE",
    "PROVIDERS",
    "BaseEmbedder",
    "CallableEmbedder",
    "Embedder",
    "EmbeddingLineage",
    "FastEmbedder",
    "LocalEmbedder",
    "OllamaEmbedder",
    "OpenAIEmbedder",
    "SentenceTransformersEmbedder",
    "resolve_embedder",
]
