"""
AquilaVectorDB — Typed store configuration.

Frozen dataclasses describing a vector store, plus GPU and embedder policy.
Each carries ``to_dict()`` so the same objects travel through
``Workspace.vectordb()``, ``Integration.vectordb()``, ``AquilaConfig.VectorDB``,
and ``ConfigLoader.get_vectordb_config()`` without a second representation.

Nothing here imports ``elips``. Translation into native ``elips.Config`` /
``elips.GpuConfig`` objects happens in :mod:`aquilia.vectordb.engine` and
:mod:`aquilia.vectordb.gpu`, at bind time — so a workspace can be *described*
on a machine that has neither elips nor a GPU installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Metric = Literal["cosine", "l2", "dot"]
IndexKind = Literal["flat", "hnsw", "ivf"]
GpuPolicyName = Literal["cpu_only", "prefer_gpu", "require_gpu"]
FallbackPolicy = Literal["allow", "warn", "require"]


@dataclass(frozen=True)
class GpuOptions:
    """
    GPU acceleration policy for a vector store.

    Args:
        policy: ``"cpu_only"`` never touches the GPU. ``"prefer_gpu"`` uses it
            when a device is present and silently runs on CPU otherwise.
            ``"require_gpu"`` refuses to boot without a usable device.
        device: Device ordinal to bind. ``None`` lets elips choose.
        fallback: What to do when a *query* runs on CPU despite the policy
            asking for GPU. elips falls back per-query even under
            ``require_gpu``, so:

            * ``"allow"`` — accept it silently (default; same API, possibly slower).
            * ``"warn"``  — log once per collection.
            * ``"require"`` — raise ``VectorGpuFault``. Costs an
              ``explain_seek`` per query, which is why it is opt-in.
        memory_budget_mb: Advisory device-memory ceiling, when elips honours one.

    Example::

        GpuOptions(policy="prefer_gpu", fallback="warn")
    """

    policy: GpuPolicyName = "cpu_only"
    device: int | None = None
    fallback: FallbackPolicy = "allow"
    memory_budget_mb: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "policy": self.policy,
            "device": self.device,
            "fallback": self.fallback,
            "memory_budget_mb": self.memory_budget_mb,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | GpuOptions | str | None) -> GpuOptions:
        """
        Build from a dict, a bare policy name, or an existing instance.

        A bare string is read as the policy, so ``gpu="prefer_gpu"`` works
        wherever the full dataclass does — matching how
        :meth:`EmbedderOptions.from_dict` accepts a bare URI and
        :meth:`QuantizationConfig.from_dict` a bare codec. The pyconfig
        ``VectorDB.gpu`` field is exactly that spelling.

        Raises:
            VectorConfigFault: When a bare string is not a known policy.
        """
        if data is None:
            return cls()
        if isinstance(data, GpuOptions):
            return data
        if isinstance(data, str):
            valid = ("cpu_only", "prefer_gpu", "require_gpu")
            if data not in valid:
                from aquilia.vectordb.faults import VectorConfigFault

                raise VectorConfigFault(
                    reason=f"unknown GPU policy {data!r}; expected one of {', '.join(valid)}",
                )
            return cls(policy=data)  # type: ignore[arg-type]
        known = {"policy", "device", "fallback", "memory_budget_mb"}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass(frozen=True)
class EmbedderOptions:
    """
    Server-side embedding configuration.

    When set, models with a ``TextField`` or ``Text()`` slot may be written
    without an explicit vector: elips embeds from the text on write and from
    the query string on search.

    The embedder is part of a persisted database's identity. Changing it against
    an existing directory makes stored vectors incomparable to new ones, so boot
    pre-checks the fingerprint and raises ``VectorEmbedderMismatchFault`` rather
    than letting search quality quietly collapse.

    Args:
        provider: How the embedder is obtained.

            * ``"uri"`` — resolve ``uri`` through
              :func:`aquilia.vectordb.embedders.resolve_embedder`. Vectors are
              computed in Python and written explicitly. This is the form the
              embedder ecosystem (§3.3) uses.
            * ``"local"`` — elips' built-in C++ embedder, attached to the
              database so the engine embeds server-side.
            * ``"callable"`` — the dotted path in ``fn``.
        model: Local model identifier passed to elips, for ``provider="local"``.
        uri: Embedder URI for ``provider="uri"``, e.g.
            ``"sentence-transformers/all-MiniLM-L6-v2"`` or
            ``"openai/text-embedding-3-small"``.
        fn: Dotted path to a callable ``(list[str]) -> list[list[float]]``,
            used when ``provider="callable"``. Resolved at bind time and
            imported verbatim — trusted deployment input, never request data.
        batch_size: Texts per embed call.
        normalize: Whether to L2-normalize returned vectors. Leave ``True``
            with ``cosine``.
        device: Compute device for local model backends (``"cpu"``, ``"cuda"``,
            ``"mps"``). ``None`` lets the backend choose.
        api_key: API key for hosted providers. Prefer leaving this unset and
            supplying the provider's environment variable, so the key does not
            sit in a config file that gets committed.
        dimension: Declared vector length. Discovered by probing when omitted.
        prompt_template: Applied to stored text before embedding, for
            asymmetric models (``"passage: {text}"``).

    Example::

        EmbedderOptions(provider="uri", uri="sentence-transformers/all-MiniLM-L6-v2")
        EmbedderOptions(provider="local", model="default")
    """

    provider: Literal["local", "callable", "uri"] = "local"
    model: str | None = None
    uri: str | None = None
    fn: str | None = None
    batch_size: int = 32
    normalize: bool = True
    device: str | None = None
    api_key: str | None = None
    dimension: int | None = None
    prompt_template: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "provider": self.provider,
            "model": self.model,
            "uri": self.uri,
            "fn": self.fn,
            "batch_size": self.batch_size,
            "normalize": self.normalize,
            "device": self.device,
            "api_key": self.api_key,
            "dimension": self.dimension,
            "prompt_template": self.prompt_template,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | EmbedderOptions | None) -> EmbedderOptions | None:
        """
        Build from a dict, passing through an existing instance.

        A bare string is accepted and read as a URI, so
        ``embedder="openai/text-embedding-3-small"`` works wherever the full
        dataclass does — that is the spelling the plan's pyconfig examples use.
        """
        if data is None:
            return None
        if isinstance(data, EmbedderOptions):
            return data
        if isinstance(data, str):
            return cls(provider="uri", uri=data)
        known = {
            "provider",
            "model",
            "uri",
            "fn",
            "batch_size",
            "normalize",
            "device",
            "api_key",
            "dimension",
            "prompt_template",
        }
        return cls(**{k: v for k, v in data.items() if k in known})

    def build(self) -> Any:
        """
        Construct the Python-side embedder this configuration names.

        Returns:
            A :class:`~aquilia.vectordb.embedders.BaseEmbedder`, or ``None`` for
            ``provider="local"`` — that one is attached to the engine and embeds
            inside C++, so there is no Python object to call.

        Raises:
            VectorConfigFault: When the configuration is incomplete.
        """
        from aquilia.vectordb.embedders import resolve_embedder
        from aquilia.vectordb.faults import VectorConfigFault

        shared: dict[str, Any] = {
            "batch_size": self.batch_size,
            "normalize": self.normalize,
            "prompt_template": self.prompt_template,
        }
        if self.dimension:
            shared["dimension"] = self.dimension

        if self.provider == "uri":
            if not self.uri:
                raise VectorConfigFault(reason="embedder provider='uri' requires uri='provider/model'")
            if self.device:
                shared["device"] = self.device
            if self.api_key:
                shared["api_key"] = self.api_key
            return resolve_embedder(self.uri, **shared)

        if self.provider == "callable":
            if not self.fn:
                raise VectorConfigFault(reason="embedder provider='callable' requires fn='module.path:callable'")
            from aquilia.vectordb.embedders import CallableEmbedder

            return CallableEmbedder(self.fn, **shared)

        return None


@dataclass(frozen=True)
class QuantizationConfig:
    """
    Vector compression policy for a store.

    Quantization trades recall for memory. ``sq8`` keeps one byte per dimension
    (~4x smaller); ``pq``/``opq`` keep a short code per vector (~8-32x smaller,
    with ``opq`` applying a learned rotation first for better accuracy at the
    same code size).

    The codec must be declared **at connect time**, not at compress time: elips
    validates it against the on-disk state when the database opens, and
    ``Collection.compress()`` refuses to run without one. That is why this lives
    on the store config rather than being a parameter to a compress call.

    Compression is still a separate, explicit step. Product quantization cannot
    encode the first record — a codebook has to be learned from real vectors —
    so a freshly-created store holds full-precision vectors until
    ``aq vectordb compress`` (or :meth:`VectorManager.quantize`) trains one.

    Args:
        codec: ``"none"``, ``"sq8"``, ``"pq"``, or ``"opq"``.
        pq_dim: Sub-quantizer count for ``pq``/``opq``. ``0`` lets elips derive
            one from the dimension.
        pq_bits: Bits per sub-quantizer code, 4-8. More bits means better recall
            and a larger code.
        train_iters: k-means iterations when training the codebook.
        opq_iters: Rotation-refinement iterations, ``opq`` only.
        sample_size: Vectors sampled to train the codebook. The whole collection
            is used when it holds fewer.

    Example::

        QuantizationConfig(codec="pq", pq_bits=8, sample_size=50_000)
    """

    codec: Literal["none", "sq8", "pq", "opq"] = "none"
    pq_dim: int = 0
    pq_bits: int = 8
    train_iters: int = 10
    opq_iters: int = 4
    sample_size: int = 10_000

    def __post_init__(self) -> None:
        if self.codec not in ("none", "sq8", "pq", "opq"):
            raise ValueError(f"QuantizationConfig(codec=...) must be 'none', 'sq8', 'pq', or 'opq', got {self.codec!r}")
        if not 4 <= self.pq_bits <= 8:
            raise ValueError(f"QuantizationConfig(pq_bits=...) must be between 4 and 8, got {self.pq_bits}")
        if self.sample_size < 1:
            raise ValueError(f"QuantizationConfig(sample_size=...) must be positive, got {self.sample_size}")

    @property
    def enabled(self) -> bool:
        """Whether this configuration asks for any compression."""
        return self.codec != "none"

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "codec": self.codec,
            "pq_dim": self.pq_dim,
            "pq_bits": self.pq_bits,
            "train_iters": self.train_iters,
            "opq_iters": self.opq_iters,
            "sample_size": self.sample_size,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | QuantizationConfig | str | None) -> QuantizationConfig:
        """
        Build from a dict, a bare codec name, or an existing instance.

        A bare string is read as the codec, so ``quantization="sq8"`` works
        wherever the full dataclass does.
        """
        if data is None:
            return cls()
        if isinstance(data, QuantizationConfig):
            return data
        if isinstance(data, str):
            return cls(codec=data)  # type: ignore[arg-type]
        known = {"codec", "pq_dim", "pq_bits", "train_iters", "opq_iters", "sample_size"}
        return cls(**{k: v for k, v in data.items() if k in known})

    def to_native(self) -> Any:
        """
        Build the native ``elips.QuantParams`` this configuration describes.

        Returns:
            A configured ``QuantParams``, or ``None`` when the codec is
            ``"none"`` — elips wants the argument omitted entirely rather than
            set to a no-op codec.
        """
        if not self.enabled:
            return None

        from aquilia.vectordb._compat import require_elips

        elips = require_elips()
        params = elips.QuantParams()
        # `codec` takes the name as a plain string; the `elips.Codec` enum is a
        # separate read-side type and assigning a member here is a TypeError.
        params.codec = self.codec
        if self.pq_dim:
            params.pq_dim = self.pq_dim
        params.pq_bits = self.pq_bits
        params.train_iters = self.train_iters
        params.opq_iters = self.opq_iters
        return params


@dataclass(frozen=True)
class VectorStoreConfig:
    """
    Configuration for one vector store (one elips database directory).

    A store maps 1:1 to an ``elips.Engine`` and therefore to one on-disk
    directory holding one writer lock. ``dimension`` and ``metric`` are
    database-global in elips, so every model bound to this store must agree on
    them; a disagreement is a ``VectorSchemaFault`` at bind time.

    Args:
        alias: Name models reference via ``Meta.store``.
        path: Database directory. Created on first open when
            ``create_if_missing``.
        dimension: Vector length for every collection in this store.
        metric: Similarity metric. Changing it against an existing directory is
            an elips ``ConfigError`` — it invalidates the built index.
        index: Index kind. ``"flat"`` is exact; ``"hnsw"``/``"ivf"`` are
            approximate and take their tuning from ``index_options``.
        index_options: Index-specific knobs passed through to elips
            (e.g. ``{"m": 16, "ef_construction": 200}``).
        create_if_missing: Create the directory when absent. Set ``False`` in
            production to make a missing store a boot failure instead of a
            silently empty one.
        read_only: Open without taking the writer lock. Lets several processes
            share one store for search; writes raise.
        gpu: GPU policy for this store.
        embedder: Server-side embedder, when text-first writes are used.
        pool_size: Reserved. elips is single-writer per directory, so the
            engine is a single handle guarded by an async lock rather than a
            pool; the field exists so a future multi-handle read path does not
            need a config change.
        options: Escape hatch forwarded verbatim to ``elips.Config``.

    Example::

        VectorStoreConfig(
            alias="docs",
            path="./data/vectors/docs",
            dimension=768,
            metric="cosine",
            index="hnsw",
            index_options={"m": 16, "ef_construction": 200},
        )
    """

    alias: str = "default"
    path: str = "./data/vectors"
    dimension: int = 768
    metric: Metric = "cosine"
    index: IndexKind = "flat"
    index_options: dict[str, Any] = field(default_factory=dict)
    create_if_missing: bool = True
    read_only: bool = False
    gpu: GpuOptions = field(default_factory=GpuOptions)
    embedder: EmbedderOptions | None = None
    quantization: QuantizationConfig = field(default_factory=QuantizationConfig)
    pool_size: int = 1
    options: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.dimension, int) or self.dimension <= 0:
            raise ValueError(f"VectorStoreConfig(dimension=...) must be a positive int, got {self.dimension!r}")
        if self.metric not in ("cosine", "l2", "dot"):
            raise ValueError(f"VectorStoreConfig(metric=...) must be 'cosine', 'l2', or 'dot', got {self.metric!r}")

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a plain dict."""
        return {
            "alias": self.alias,
            "path": self.path,
            "dimension": self.dimension,
            "metric": self.metric,
            "index": self.index,
            "index_options": dict(self.index_options),
            "create_if_missing": self.create_if_missing,
            "read_only": self.read_only,
            "gpu": self.gpu.to_dict(),
            "embedder": self.embedder.to_dict() if self.embedder else None,
            "quantization": self.quantization.to_dict(),
            "pool_size": self.pool_size,
            "options": dict(self.options),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | VectorStoreConfig) -> VectorStoreConfig:
        """
        Build from a plain dict, tolerating unknown keys.

        Unknown keys are folded into ``options`` rather than dropped, so a newer
        elips knob set in config reaches the engine without a framework release.
        """
        if isinstance(data, VectorStoreConfig):
            return data

        known = {
            "alias",
            "path",
            "dimension",
            "metric",
            "index",
            "index_options",
            "create_if_missing",
            "read_only",
            "pool_size",
        }
        kwargs: dict[str, Any] = {k: v for k, v in data.items() if k in known}
        structured = {"gpu", "embedder", "quantization", "options", "default"}
        extra = {k: v for k, v in data.items() if k not in known | structured}

        options = dict(data.get("options") or {})
        options.update(extra)

        return cls(
            **kwargs,
            gpu=GpuOptions.from_dict(data.get("gpu")),
            embedder=EmbedderOptions.from_dict(data.get("embedder")),
            quantization=QuantizationConfig.from_dict(data.get("quantization")),
            options=options,
        )


#: Keys that describe a whole ``vectordb`` block rather than one store, and so
#: are never copied down onto a synthesized store entry as-is.
_BLOCK_ONLY_KEYS = frozenset(
    {"_integration_type", "enabled", "stores", "default", "pool_threads", "auto_create", "path"}
)

#: Block-level keys that *are* inherited by each store, under a different name
#: where the two vocabularies differ.
_INHERITED_KEYS: tuple[tuple[str, str], ...] = (
    ("dimension", "dimension"),
    ("metric", "metric"),
    ("index", "index"),
    ("index_options", "index_options"),
    ("gpu", "gpu"),
    ("embedder", "embedder"),
    ("quantization", "quantization"),
    ("auto_create", "create_if_missing"),
    ("read_only", "read_only"),
)


def normalize_stores(block: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Flatten a ``vectordb`` config block into a list of store entries.

    One normalizer for every producer of that block, because there are four and
    they do not agree on shape:

    * :meth:`~aquilia.integrations.vectordb.VectorDatabaseIntegration.to_dict`
      emits ``stores`` as a list of entries that each carry an ``alias``.
    * ``Workspace.vectordb(stores={...})`` emits the same, via the integration.
    * :class:`~aquilia.pyconfig.AquilaConfig.VectorDB` emits a *flat* block with
      ``stores=None`` and the store settings inline — the single-store shorthand.
    * A hand-written config file may use ``{alias: config}``.

    Before this existed, the pyconfig shorthand produced no stores at all: the
    subsystem read ``stores=None``, logged "declares no stores", and reported
    HEALTHY having opened nothing.

    Args:
        block: The ``vectordb`` configuration block.

    Returns:
        Store entries, each carrying at least ``alias`` and ``path``. Empty when
        the block declares neither explicit stores nor a usable shorthand.
    """
    import os

    declared = block.get("stores")
    default_alias = str(block.get("default", "default") or "default")
    prefix = str(block.get("path", "./.aquilia/vectors") or "./.aquilia/vectors")

    entries: list[dict[str, Any]] = []

    # An *empty* stores list or dict is "not declared", not "declared as none":
    # ConfigLoader.get_vectordb_config() supplies ``stores: []`` as a default, and
    # treating that as an explicit empty declaration would shadow the single-store
    # shorthand below and silently open nothing.
    if isinstance(declared, dict) and declared:
        for alias, cfg in declared.items():
            if hasattr(cfg, "to_dict"):
                entry = cfg.to_dict()
            elif isinstance(cfg, dict):
                entry = dict(cfg)
            else:
                # `{"default": 384}` — a bare int is the dimension.
                entry = {"dimension": int(cfg)}
            entry.setdefault("alias", alias)
            entries.append(entry)
    elif isinstance(declared, (list, tuple)) and declared:
        for cfg in declared:
            entry = cfg.to_dict() if hasattr(cfg, "to_dict") else dict(cfg)
            entry.setdefault("alias", default_alias)
            entries.append(entry)
    elif block.get("dimension"):
        # Single-store shorthand: the block itself describes one store. This is
        # the pyconfig `VectorDB` path.
        entries.append({"alias": default_alias})

    for entry in entries:
        for block_key, store_key in _INHERITED_KEYS:
            value = block.get(block_key)
            if value is not None and store_key not in entry:
                entry[store_key] = value.to_dict() if hasattr(value, "to_dict") else value
        if not entry.get("path"):
            entry["path"] = os.path.join(prefix, str(entry["alias"]))

    return entries


__all__ = [
    "EmbedderOptions",
    "FallbackPolicy",
    "GpuOptions",
    "GpuPolicyName",
    "IndexKind",
    "Metric",
    "QuantizationConfig",
    "VectorStoreConfig",
    "normalize_stores",
]
