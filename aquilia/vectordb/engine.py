"""
AquilaVectorDB — Async engine wrapper around ``elips.Engine``.

One :class:`VectorEngine` owns one elips database directory. Every blocking
native call is dispatched through :class:`~aquilia.vectordb.pool.VectorPool`, so
the surface is ``async`` without lying about it: elips releases the GIL in its
hot paths, which is what makes the offload buy real concurrency.

Writer serialization
--------------------

elips takes a single writer lock per database directory. Two coroutines issuing
concurrent ``write`` calls therefore contend inside C++, where the loser blocks a
*pool thread* rather than yielding. An ``asyncio.Lock`` around mutating calls
moves that queueing into Python, where waiting is free and ordering is fair. Read
paths take no lock and run fully parallel.

Vocabulary mapping
------------------

Aquilia's config vocabulary is not elips': ``metric`` is ``cosine|l2|dot`` here
and ``cosine|euclidean|dot_product`` there; ``index`` is ``flat|hnsw|ivf`` here
and ``exact|graph`` there. The translation lives in :data:`_METRICS` and
:data:`_INDEXES` so config stays stable across elips releases.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from functools import partial
from typing import TYPE_CHECKING, Any

from aquilia.vectordb._compat import require_elips, translate
from aquilia.vectordb.configs import VectorStoreConfig
from aquilia.vectordb.faults import VectorConfigFault, VectorStoreFault
from aquilia.vectordb.manager import _normalize_key
from aquilia.vectordb.pool import VectorPool

if TYPE_CHECKING:
    from aquilia.vectordb.gpu import GpuInfo

logger = logging.getLogger("aquilia.vectordb.engine")

#: Aquilia metric name → elips metric name.
_METRICS = {"cosine": "cosine", "l2": "euclidean", "dot": "dot_product"}

# ---------------------------------------------------------------------------
# Query observability gate
# ---------------------------------------------------------------------------
# Mirrors ``aquilia.db.engine._QUERY_INSPECTION``, and for the same reason: a
# diagnostic must cost nothing when it is off. Every native call flows through
# :meth:`VectorEngine.read` / :meth:`VectorEngine.write`, so an unconditional
# span build would tax the hot path of a subsystem whose whole point is latency.
# Disabled, the cost is one global load and a branch.
_VECTOR_INSPECTION: bool = False


def enable_vector_inspection(enabled: bool = True) -> None:
    """
    Turn per-operation inspector recording on or off process-wide.

    Called by the inspector collector at startup, not per request: re-deciding
    per call would reintroduce the overhead the flag exists to remove.

    Args:
        enabled: Whether to record a span per vector operation.
    """
    global _VECTOR_INSPECTION
    _VECTOR_INSPECTION = enabled


def vector_inspection_enabled() -> bool:
    """Whether per-operation inspector recording is currently active."""
    return _VECTOR_INSPECTION


#: Aquilia index name → elips index backend.
#: elips exposes ``exact`` (brute force) and ``graph`` (HNSW-family). ``ivf`` has
#: no distinct backend, so it maps to ``graph`` and :meth:`VectorEngine._open_sync`
#: warns; mapping it to ``exact`` instead would silently turn an approximate-index
#: request into a full scan. IVF-specific tuning (``nlist``, ``nprobe``) has no
#: effect — ``index_options`` carries HNSW graph parameters only.
_INDEXES = {"flat": "exact", "hnsw": "graph", "ivf": "graph"}


class VectorEngine:
    """
    Async handle on one elips database.

    Args:
        config: The store configuration.
        pool: Thread pool for blocking calls. A private pool is created when
            omitted, so direct use in tests needs no wiring.

    Example::

        engine = VectorEngine(VectorStoreConfig(alias="docs", path="./v", dimension=4))
        await engine.connect()
        col = await engine.collection("docs")
        await engine.close()
    """

    __slots__ = (
        "_config",
        "_pool",
        "_engine",
        "_lock",
        "_gpu_info",
        "_collections",
        "_connected",
        "_embedder",
        "_text_embedder",
        "_txn_owner",
    )

    def __init__(self, config: VectorStoreConfig, pool: VectorPool | None = None) -> None:
        self._config = config
        self._pool = pool or VectorPool()
        self._engine: Any | None = None
        self._lock = asyncio.Lock()
        self._gpu_info: GpuInfo | None = None
        self._collections: dict[str, Any] = {}
        self._connected = False
        self._embedder: Any | None = None
        self._text_embedder: Any | None = None
        self._txn_owner: asyncio.Task[Any] | None = None

    # ── Properties ───────────────────────────────────────────────────────

    @property
    def config(self) -> VectorStoreConfig:
        """The store configuration."""
        return self._config

    @property
    def alias(self) -> str:
        """The store alias."""
        return self._config.alias

    @property
    def connected(self) -> bool:
        """Whether the database is open."""
        return self._connected

    @property
    def gpu_info(self) -> GpuInfo | None:
        """GPU snapshot captured at connect time, or ``None`` before connect."""
        return self._gpu_info

    @property
    def pool(self) -> VectorPool:
        """The thread pool backing this engine."""
        return self._pool

    @property
    def text_embedder(self) -> Any | None:
        """
        The Python-side embedder for this store, or ``None``.

        Present only for ``EmbedderOptions(provider="uri")``, where vectors are
        computed in Python before the write. A ``provider="local"`` store embeds
        inside C++ instead, and reports ``None`` here — the two are mutually
        exclusive by construction, so a caller seeing ``None`` knows the engine
        handles text itself rather than that text is unsupported.
        """
        return self._text_embedder

    @property
    def embeds_server_side(self) -> bool:
        """Whether the engine embeds text itself, without a Python round trip."""
        return self._embedder is not None

    @property
    def can_embed(self) -> bool:
        """Whether this store can turn text into vectors by any route."""
        return self._embedder is not None or self._text_embedder is not None

    @property
    def raw(self) -> Any:
        """
        The underlying ``elips.Engine``.

        Raises:
            VectorStoreFault: When not connected.
        """
        if self._engine is None:
            raise VectorStoreFault(
                store=self._config.alias,
                operation="access",
                reason="engine is not connected; call connect() first",
            )
        return self._engine

    # ── Lifecycle ────────────────────────────────────────────────────────

    async def connect(self) -> None:
        """
        Open the elips database.

        Resolves GPU policy, builds the embedder, creates the directory when
        ``create_if_missing``, and opens the engine. Idempotent.

        Raises:
            VectorNotInstalledFault: When ``elips`` is missing.
            VectorGpuUnavailableFault: When ``require_gpu`` cannot be satisfied.
            VectorConfigFault: On an invalid or conflicting store config.
            VectorStoreFault: When the database cannot be opened.
        """
        if self._connected:
            return

        async with self._lock:
            if self._connected:
                return

            require_elips()

            from aquilia.vectordb.gpu import build_config, resolve

            # Resolve policy before touching the filesystem so a require_gpu
            # violation fails without leaving a half-created directory behind.
            self._gpu_info = resolve(self._config.gpu, store=self._config.alias)
            gpu_config = build_config(self._config.gpu, store=self._config.alias)

            self._embedder = await self._build_embedder()
            self._text_embedder = await self._build_text_embedder()
            self._engine = await self._pool.run(partial(self._open_sync, gpu_config))
            self._connected = True

            logger.info(
                "Vector store %r opened at %s (dim=%d metric=%s index=%s gpu=%s embedder=%s)",
                self._config.alias,
                self._config.path,
                self._config.dimension,
                self._config.metric,
                self._config.index,
                "on" if gpu_config is not None else "off",
                self._embedder_label(),
            )

    def _embedder_label(self) -> str:
        """Describe the active embedding route, for the boot log line."""
        if self._text_embedder is not None:
            return f"{self._text_embedder.provider}/{self._text_embedder.model} (python)"
        if self._embedder is not None:
            return "elips (native)"
        return "none"

    async def _build_text_embedder(self) -> Any | None:
        """
        Build the Python-side embedder, verifying it matches the store.

        The dimension check happens here, at open, rather than on first write.
        An embedder producing 768-dimension vectors against a 384-dimension
        store fails on every single write; discovering that at boot costs one
        probe embedding and turns a recurring runtime error into a
        configuration error with both numbers in it.

        Raises:
            VectorConfigFault: When the embedder's dimension disagrees with the
                store's.
        """
        spec = self._config.embedder
        if spec is None or spec.provider != "uri":
            return None

        embedder = spec.build()
        if embedder is None:
            return None

        try:
            produced = await embedder.dimension()
        except Exception as exc:
            # A probe failure is not fatal on its own: a cloud provider may be
            # briefly unreachable at boot while the store is still usable for
            # vector-supplied writes and searches.
            logger.warning(
                "Store %r: could not probe embedder %s dimension at open (%s); it will be checked on first use",
                self._config.alias,
                spec.uri,
                exc,
            )
            return embedder

        if produced != self._config.dimension:
            raise VectorConfigFault(
                reason=(
                    f"embedder {spec.uri!r} produces {produced}-dimension vectors but store "
                    f"{self._config.alias!r} is configured for {self._config.dimension}. "
                    f"Set dimension={produced} on the store, or choose an embedder that "
                    f"matches."
                ),
                store=self._config.alias,
            )

        return embedder

    def _open_sync(self, gpu_config: Any | None) -> Any:
        """
        Blocking half of :meth:`connect`; runs in the pool.

        Builds an ``elips.Config`` explicitly rather than passing keyword
        arguments to ``elips.connect``. The two are equivalent — ``connect``
        composes the same builder internally — except for ``graph_params``,
        which it does not expose. Constructing the config here is what makes
        ``index_options`` (HNSW ``M``, ``ef_construction``, ``ef_search``,
        ``compaction_ratio``) actually reach the index instead of being
        silently dropped.
        """
        import os

        elips = require_elips()
        cfg = self._config
        path = cfg.path

        if path != ":memory:":
            if cfg.create_if_missing:
                os.makedirs(path, exist_ok=True)
            elif not os.path.isdir(path):
                raise VectorConfigFault(
                    reason=(
                        f"store path {path!r} does not exist and create_if_missing=False. "
                        f"Create it, or set create_if_missing=True."
                    ),
                    store=cfg.alias,
                )

        metric = _METRICS.get(cfg.metric)
        if metric is None:
            raise VectorConfigFault(
                reason=f"unsupported metric {cfg.metric!r}; expected one of {', '.join(_METRICS)}",
                store=cfg.alias,
            )

        index = _INDEXES.get(cfg.index)
        if index is None:
            raise VectorConfigFault(
                reason=f"unsupported index {cfg.index!r}; expected one of {', '.join(_INDEXES)}",
                store=cfg.alias,
            )

        if cfg.index == "ivf":
            # elips has two backends, `exact` and `graph`. There is no IVF one,
            # so an `ivf` request is served by HNSW. Saying so is the difference
            # between a documented approximation and a silent substitution.
            logger.warning(
                "Store %r requests index='ivf', which this elips build does not provide; "
                "using the HNSW graph index instead. IVF-specific tuning (nlist, nprobe) "
                "has no effect — use index='hnsw' with index_options to tune it explicitly.",
                cfg.alias,
            )

        config = (
            elips.Config()
            .dimension(cfg.dimension)
            .metric(metric)
            .index(index)
            .access_mode("read_only" if cfg.read_only else "read_write")
            # Without a configured embedder, do not auto-attach elips' built-in
            # one: it would bake an embedder into the database identity that the
            # workspace never asked for, and text writes would then start
            # succeeding by accident.
            .auto_text_embedder(self._embedder is not None)
        )

        graph_params = self._graph_params(elips, index)
        if graph_params is not None:
            config.graph_params(graph_params)

        # Quantization has to be declared at open: elips validates the codec
        # against on-disk state here, and Collection.compress() refuses to run
        # without one already configured.
        quant_params = cfg.quantization.to_native()
        if quant_params is not None:
            config.quantization(quant_params)

        if gpu_config is not None:
            config.gpu(gpu_config)

        self._apply_option_overrides(config)

        open_kwargs: dict[str, Any] = {}
        if self._embedder is not None:
            open_kwargs["embedder"] = self._embedder
            if cfg.embedder is not None and cfg.embedder.provider == "callable":
                open_kwargs["embedder_provider"] = "python"
                open_kwargs["embedder_model"] = cfg.embedder.fn or "callable"

        try:
            return elips.connect_with_config(path, config, **open_kwargs)
        except Exception as exc:
            raise translate(exc, store=cfg.alias, operation="connect") from exc

    #: ``index_options`` key → ``elips.GraphParams`` attribute. ``m`` is accepted
    #: alongside ``max_connections`` because every HNSW paper and neighbouring
    #: library spells that parameter ``M``.
    _GRAPH_PARAM_KEYS = {
        "m": "max_connections",
        "max_connections": "max_connections",
        "ef_construction": "ef_construction",
        "ef_search": "ef_search",
        "compaction_ratio": "compaction_ratio",
    }

    def _graph_params(self, elips: Any, index: str) -> Any | None:
        """
        Build ``elips.GraphParams`` from ``index_options``.

        Returns ``None`` when nothing is declared, or when the store uses the
        exact index — graph tuning on a brute-force scan has nothing to tune.

        Unrecognized keys are warned about rather than dropped silently: an
        ``index_options={"nlist": 100}`` that does nothing should say so, not
        look like it worked.
        """
        cfg = self._config
        if not cfg.index_options:
            return None

        if index != "graph":
            logger.warning(
                "Store %r declares index_options but uses index=%r, which takes no graph tuning; ignoring %s.",
                cfg.alias,
                cfg.index,
                ", ".join(sorted(cfg.index_options)),
            )
            return None

        params = elips.GraphParams()
        unknown: list[str] = []
        applied = False

        for key, value in cfg.index_options.items():
            attr = self._GRAPH_PARAM_KEYS.get(str(key).lower())
            if attr is None:
                unknown.append(str(key))
                continue
            try:
                setattr(params, attr, float(value) if attr == "compaction_ratio" else int(value))
                applied = True
            except (TypeError, ValueError) as exc:
                raise VectorConfigFault(
                    reason=f"index_options[{key!r}]={value!r} is not a valid {attr}: {exc}",
                    store=cfg.alias,
                ) from exc

        if unknown:
            logger.warning(
                "Store %r: ignoring unknown index_options %s. Supported: %s.",
                cfg.alias,
                ", ".join(sorted(unknown)),
                ", ".join(sorted(set(self._GRAPH_PARAM_KEYS))),
            )

        return params if applied else None

    def _apply_option_overrides(self, config: Any) -> None:
        """
        Apply the ``options`` escape hatch as ``elips.Config`` builder calls.

        ``options`` exists so a newer elips knob reachable from config does not
        need a framework release. Each key is looked up as a builder method and
        skipped with a warning when this build has none, which is the same
        forgiving contract the previous keyword-retry had — without opening the
        database twice to discover it.
        """
        for key, value in self._config.options.items():
            method = getattr(config, str(key), None)
            if not callable(method):
                logger.warning(
                    "Store %r: elips.Config has no option %r on this build; ignoring it.",
                    self._config.alias,
                    key,
                )
                continue
            try:
                method(value)
            except Exception as exc:
                raise VectorConfigFault(
                    reason=f"option {key!r}={value!r} was rejected by elips.Config: {exc}",
                    store=self._config.alias,
                ) from exc

    async def _build_embedder(self) -> Any | None:
        """
        Construct the native embedder described by the store config.

        Returns ``None`` for ``provider="uri"``: that embedder lives in Python
        and is reached through :attr:`text_embedder`, so nothing is attached to
        the database. Attaching one there *and* embedding in Python would give a
        store two vector spaces under one dimension, and no later check could
        tell which space a given record came from.
        """
        spec = self._config.embedder
        if spec is None:
            return None

        if spec.provider == "uri":
            return None

        elips = require_elips()

        if spec.provider == "local":
            local_cfg = getattr(elips, "LocalEmbedderConfig", None)
            if local_cfg is None:
                raise VectorConfigFault(
                    reason="this elips build has no LocalEmbedderConfig; use provider='callable'",
                    store=self._config.alias,
                )
            cfg = local_cfg()
            if spec.model:
                # Attribute name varies across elips releases; set whichever exists
                # rather than guessing one and crashing on an older build.
                for attr in ("model", "model_name", "name"):
                    if hasattr(cfg, attr):
                        setattr(cfg, attr, spec.model)
                        break
            return cfg

        if spec.provider == "callable":
            if not spec.fn:
                raise VectorConfigFault(
                    reason="embedder provider='callable' requires fn='module.path:callable'",
                    store=self._config.alias,
                )
            return _resolve_callable_embedder(spec.fn, self._config.alias)

        raise VectorConfigFault(
            reason=f"unknown embedder provider {spec.provider!r}",
            store=self._config.alias,
        )

    async def close(self) -> None:
        """
        Close the database, releasing the writer lock.

        Idempotent. Safe to call on a never-connected engine.
        """
        if not self._connected or self._engine is None:
            return

        async with self._lock:
            if self._engine is None:
                return
            engine = self._engine
            self._engine = None
            self._connected = False
            self._collections.clear()
            self._text_embedder = None
            try:
                await self._pool.run(engine.close)
            except Exception as exc:
                # Never propagate from close(): shutdown must proceed even if a
                # store is already gone, or one bad store blocks the rest.
                logger.warning("Error closing vector store %r: %s", self._config.alias, exc)

    # ── Collections ──────────────────────────────────────────────────────

    async def collection(self, name: str) -> Any:
        """
        Open (creating if needed) a collection, memoized per engine.

        Args:
            name: Collection name.

        Returns:
            The native ``elips.Collection``.
        """
        cached = self._collections.get(name)
        if cached is not None:
            return cached

        async with self._lock:
            cached = self._collections.get(name)
            if cached is not None:
                return cached
            try:
                col = await self._pool.run(self.raw.collection, name)
            except Exception as exc:
                raise translate(exc, store=self._config.alias, operation="collection", context=name) from exc
            self._collections[name] = col
            return col

    async def collection_names(self) -> list[str]:
        """List collection names in this store."""
        try:
            return list(await self._pool.run(self.raw.collection_names))
        except Exception as exc:
            raise translate(exc, store=self._config.alias, operation="collection_names") from exc

    # ── Dispatch helpers ─────────────────────────────────────────────────

    def _notify_inspector(
        self,
        operation: str,
        duration_ms: float,
        *,
        error: str = "",
        detail: dict[str, Any] | None = None,
    ) -> None:
        """
        Record one vector operation in the active trace.

        Callers must gate this on :data:`_VECTOR_INSPECTION`. Failure here is
        swallowed: a broken diagnostic must never break the query it measures.

        Args:
            operation: Native call name, used as the span label.
            duration_ms: Measured wall time of the native call.
            error: Fault code when the call failed, empty when it succeeded.
            detail: Extra span detail merged over the defaults.
        """
        try:
            from aquilia.inspector.trace import Lane, SpanStatus, current_trace

            trace = current_trace()
            if trace is None:
                return

            now_offset = (time.monotonic() - trace.started_monotonic) * 1000.0
            span_detail: dict[str, Any] = {
                "store": self._config.alias,
                "index": self._config.index,
                "metric": self._config.metric,
                "gpu": self._gpu_info.available if self._gpu_info is not None else False,
            }
            if error:
                span_detail["error"] = error
            if detail:
                span_detail.update(detail)

            trace.add_span(
                lane=Lane.VECTOR,
                label=f"{self._config.alias}.{operation}",
                start_offset_ms=max(0.0, now_offset - duration_ms),
                duration_ms=duration_ms,
                status=SpanStatus.ERROR if error else SpanStatus.OK,
                detail=span_detail,
            )
        except Exception:  # pragma: no cover - diagnostics must not break queries
            logger.debug("Inspector span for %r failed", operation, exc_info=True)

    async def read(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        """
        Run a non-mutating native call in the pool, without the writer lock.

        Args:
            fn: Bound native callable.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            The native return value.
        """
        call = partial(fn, *args, **kwargs) if kwargs else fn
        if not _VECTOR_INSPECTION:
            try:
                return await self._pool.run(call, *(() if kwargs else args))
            except Exception as exc:
                raise translate(exc, store=self._config.alias, operation=getattr(fn, "__name__", "read")) from exc

        operation = getattr(fn, "__name__", "read")
        started = time.monotonic()
        try:
            result = await self._pool.run(call, *(() if kwargs else args))
        except Exception as exc:
            fault = translate(exc, store=self._config.alias, operation=operation)
            self._notify_inspector(
                operation,
                (time.monotonic() - started) * 1000.0,
                error=getattr(fault, "code", type(fault).__name__),
            )
            raise fault from exc

        self._notify_inspector(
            operation,
            (time.monotonic() - started) * 1000.0,
            detail=_result_detail(result),
        )
        return result

    async def write(self, fn: Any, *args: Any, **kwargs: Any) -> Any:
        """
        Run a mutating native call under the writer lock.

        elips serializes writers itself; the lock keeps the queue in Python
        where waiting is cheap and ordering is fair.

        Args:
            fn: Bound native callable.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            The native return value.

        Raises:
            VectorStoreFault: When the store is read-only, or when called from
                inside this engine's own :meth:`transaction` block.
        """
        if self._config.read_only:
            raise VectorStoreFault(
                store=self._config.alias,
                operation=getattr(fn, "__name__", "write"),
                reason="store is opened read_only; writes are rejected",
            )

        # A transaction holds the writer lock for its whole block. asyncio.Lock
        # is not reentrant, so a write from the owning task would wait on a lock
        # only that same task can release — a permanent hang. Raise instead.
        if self._txn_owner is not None and self._txn_owner is asyncio.current_task():
            raise VectorStoreFault(
                store=self._config.alias,
                operation=getattr(fn, "__name__", "write"),
                reason=(
                    "cannot write through the engine while this task holds an open "
                    "transaction; stage the write with the transaction handle instead"
                ),
            )

        call = partial(fn, *args, **kwargs) if kwargs else fn
        operation = getattr(fn, "__name__", "write")
        async with self._lock:
            if not _VECTOR_INSPECTION:
                try:
                    return await self._pool.run(call, *(() if kwargs else args))
                except Exception as exc:
                    raise translate(exc, store=self._config.alias, operation=operation) from exc

            started = time.monotonic()
            try:
                result = await self._pool.run(call, *(() if kwargs else args))
            except Exception as exc:
                fault = translate(exc, store=self._config.alias, operation=operation)
                self._notify_inspector(
                    operation,
                    (time.monotonic() - started) * 1000.0,
                    error=getattr(fault, "code", type(fault).__name__),
                )
                raise fault from exc

            self._notify_inspector(
                operation,
                (time.monotonic() - started) * 1000.0,
                detail=_result_detail(result),
            )
            return result

    # ── Transactions ─────────────────────────────────────────────────────

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[VectorTransaction]:
        """
        Batch writes into one atomic, single-fsync commit.

        Commits on clean exit, rolls back on any exception. Held under the
        engine's writer lock for its whole duration — elips takes a single
        writer per database, so an interleaved write from another coroutine
        would deadlock against the open transaction rather than queue behind it.

        Yields:
            A :class:`VectorTransaction` scoped to this engine.

        Raises:
            VectorStoreFault: When the store is read-only, or the native
                transaction cannot be opened.

        Example::

            async with engine.transaction() as txn:
                for row in rows:
                    txn.place("documents", vector=row.vector, meta=row.meta)

        Notes:
            The native transaction surface is deliberately narrower than the
            normal write path: ``TransactionVault`` exposes only ``place`` and
            ``erase``, so text-embedding, document attachments, chunk lineage,
            and embedding provenance are **not** available inside one. Records
            needing those go through :meth:`VectorManager.add`, which is why
            this is offered as an explicit bulk-load tool rather than as the
            default path for every write.

            Every call is one round trip into the pool. Building the batch in
            Python and committing once is the point; a transaction wrapped
            around a single write costs more than it saves.
        """
        if self._config.read_only:
            raise VectorStoreFault(
                store=self._config.alias,
                operation="transaction",
                reason="store is opened read_only; writes are rejected",
            )

        async with self._lock:
            native_db = self.raw.native
            try:
                handle = await self._pool.run(native_db.begin_transaction)
            except Exception as exc:
                raise translate(exc, store=self._config.alias, operation="begin_transaction") from exc

            txn = VectorTransaction(handle, engine=self)
            self._txn_owner = asyncio.current_task()
            try:
                yield txn
            except Exception:
                # Roll back before re-raising so the writer lock is released
                # with the database in its pre-transaction state.
                txn._close()
                try:
                    await self._pool.run(handle.rollback)
                except Exception as rollback_exc:
                    logger.error(
                        "Vector transaction rollback failed on store %r: %s",
                        self._config.alias,
                        rollback_exc,
                    )
                raise
            else:
                txn._close()
                try:
                    await self._pool.run(handle.commit)
                except Exception as exc:
                    raise translate(exc, store=self._config.alias, operation="commit") from exc
            finally:
                self._txn_owner = None

    # ── Maintenance ──────────────────────────────────────────────────────

    async def checkpoint(self) -> None:
        """Flush pending writes durably."""
        await self.write(self.raw.checkpoint)

    async def compact(self) -> Any:
        """Compact storage, reclaiming space from deleted records."""
        return await self.write(self.raw.compact)

    async def vacuum(self) -> Any:
        """Vacuum the database."""
        return await self.write(self.raw.vacuum)

    async def pending_writes(self) -> int:
        """
        Number of write-ahead log records not yet checkpointed.

        elips' native ``pending_writes()`` returns the WAL records themselves;
        only the count is useful for health, and materializing the records to
        count them is what the native call already does.
        """
        records = await self.read(self.raw.pending_writes)
        return len(records) if records is not None else 0

    async def quantize(
        self,
        collection: str,
        *,
        codec: str | None = None,
        sample_size: int | None = None,
        pq_dim: int | None = None,
        pq_bits: int | None = None,
    ) -> dict[str, Any]:
        """
        Train a codebook over one collection and compress it in place.

        Args:
            collection: Collection name.
            codec: Codec to apply. Defaults to the store's configured one.
            sample_size: Reserved; elips samples the collection itself. Accepted
                so the CLI flag has somewhere to land and so a future elips that
                exposes the knob needs no signature change.
            pq_dim: Reserved, as ``sample_size``.
            pq_bits: Reserved, as ``sample_size``.

        Returns:
            ``{"collection", "codec", "compressed", "reason"}``. ``compressed``
            is ``False`` with a ``reason`` when there was nothing to do — an
            empty or already-compressed collection is a normal state, not a
            failure, and a maintenance sweep over many collections must not
            abort on one.

        Raises:
            VectorConfigFault: When the store configures no codec. Compression
                cannot be requested per-call: elips fixes the codec at open.
            VectorStoreFault: When the native compress call fails.
        """
        configured = self._config.quantization
        requested = codec or configured.codec

        if requested == "none" or not configured.enabled:
            raise VectorConfigFault(
                reason=(
                    f"store {self._config.alias!r} has no quantization codec configured, so "
                    f"there is no codebook to train. Set quantization={{'codec': "
                    f"{requested if requested != 'none' else 'pq'!r}}} on the store and reopen it."
                ),
                store=self._config.alias,
            )

        if codec and codec != configured.codec:
            raise VectorConfigFault(
                reason=(
                    f"cannot compress with {codec!r}: store {self._config.alias!r} was opened "
                    f"with codec {configured.codec!r}. elips fixes the codec at open, so change "
                    f"the store configuration and reopen rather than passing a different one here."
                ),
                store=self._config.alias,
            )

        handle = await self.collection(collection)

        try:
            await self.write(handle.compress)
        except Exception as exc:
            # "empty" and "already compressed" are both ConfigError from elips
            # and both mean "nothing to do", which is not a failure worth
            # aborting a multi-collection sweep over.
            message = str(exc).lower()
            if "empty" in message or "already" in message:
                logger.info("Collection %r not compressed: %s", collection, exc)
                return {
                    "collection": collection,
                    "codec": configured.codec,
                    "compressed": False,
                    "reason": str(exc),
                }
            raise translate(exc, store=self._config.alias, operation="compress", context=collection) from exc

        return {
            "collection": collection,
            "codec": configured.codec,
            "compressed": True,
            "reason": "",
        }

    async def stats(self) -> dict[str, Any]:
        """
        Return per-collection telemetry for this store.

        Never raises: a store that cannot answer reports ``ok=False`` with the
        reason, for the same reason :meth:`health` does — diagnostics must stay
        callable when things are broken.
        """
        info: dict[str, Any] = {
            "alias": self._config.alias,
            "path": self._config.path,
            "connected": self._connected,
            "dimension": self._config.dimension,
            "metric": self._config.metric,
            "index": self._config.index,
            "codec": self._config.quantization.codec,
            "embedder": self._embedder_label(),
            "pool": self._pool.stats(),
        }

        if not self._connected:
            info["ok"] = False
            info["error"] = "not connected"
            info["collections"] = []
            return info

        try:
            info["pending_writes"] = await self.pending_writes()
            collections: list[dict[str, Any]] = []

            for name in await self.collection_names():
                handle = await self.collection(name)
                native = await self.read(handle.health)
                collections.append(
                    {
                        "name": name,
                        "live": getattr(native, "live", None),
                        "tombstone_ratio": getattr(native, "tombstone_ratio", None),
                        "pending_removals": getattr(native, "pending_removals", None),
                        "dimension": getattr(native, "dimension", None),
                        "metric": str(getattr(native, "metric", "") or ""),
                        "codec": str(getattr(native, "codec", "") or ""),
                        "code_bytes": getattr(native, "code_bytes", None),
                        "read_only": getattr(native, "read_only", None),
                        "sealed": getattr(native, "sealed", None),
                    }
                )

            info["collections"] = collections
            info["total_records"] = sum(c["live"] or 0 for c in collections)
            info["ok"] = True
        except Exception as exc:
            info["ok"] = False
            info["error"] = str(exc)
            info.setdefault("collections", [])

        return info

    async def health(self) -> dict[str, Any]:
        """
        Return a health snapshot for this store.

        Never raises: a store that cannot answer reports ``ok=False`` with the
        reason, because health checks must stay callable when things are broken.
        """
        info: dict[str, Any] = {
            "alias": self._config.alias,
            "path": self._config.path,
            "connected": self._connected,
            "dimension": self._config.dimension,
            "metric": self._config.metric,
            "index": self._config.index,
            "read_only": self._config.read_only,
            "gpu": self._gpu_info.to_dict() if self._gpu_info else None,
            "pool": self._pool.stats(),
        }
        if not self._connected:
            info["ok"] = False
            info["error"] = "not connected"
            return info

        try:
            info["collections"] = await self.collection_names()
            info["pending_writes"] = await self.pending_writes()
            info["ok"] = True
        except Exception as exc:
            info["ok"] = False
            info["error"] = str(exc)
        return info

    def __repr__(self) -> str:
        state = "connected" if self._connected else "closed"
        return f"<VectorEngine {self._config.alias!r} {state} path={self._config.path!r}>"


def _resolve_callable_embedder(spec: str, store: str) -> Any:
    """
    Import a ``"module.path:callable"`` embedder.

    Trusted deployment configuration, never request data — the same trust level
    as a manifest's controller path.

    Raises:
        VectorConfigFault: When the path cannot be imported or is not callable.
    """
    import importlib

    target = spec.replace(":", ".") if ":" in spec else spec
    module_path, _, attr = target.rpartition(".")
    if not module_path:
        raise VectorConfigFault(
            reason=f"embedder fn {spec!r} must be a dotted path like 'my.module:embed'",
            store=store,
        )

    try:
        module = importlib.import_module(module_path)
    except ImportError as exc:
        raise VectorConfigFault(
            reason=f"cannot import embedder module {module_path!r}: {exc}",
            store=store,
        ) from exc

    fn = getattr(module, attr, None)
    if fn is None:
        raise VectorConfigFault(
            reason=f"module {module_path!r} has no attribute {attr!r}",
            store=store,
        )
    if not callable(fn):
        raise VectorConfigFault(reason=f"embedder {spec!r} is not callable", store=store)
    return fn


def _result_detail(result: Any) -> dict[str, Any] | None:
    """
    Summarize a native return value for an inspector span.

    Records a *count* and nothing else. A hit list holds records whose vectors
    are hundreds of floats each; putting them in a span would copy the result
    set into the trace buffer once per query. ``len()`` on a list is O(1) and
    answers the question the swimlane actually asks — how much came back.
    """
    if isinstance(result, (list, tuple)):
        return {"rows": len(result)}
    if isinstance(result, int):
        return {"rows": result}
    return None


class VectorTransaction:
    """
    A batched write scope yielded by :meth:`VectorEngine.transaction`.

    Buffers writes in the native transaction and commits them in one fsync.
    Not constructed directly and not reusable after its block exits.
    """

    __slots__ = ("_engine", "_handle", "_open", "_vaults")

    def __init__(self, handle: Any, *, engine: VectorEngine) -> None:
        self._handle = handle
        self._engine = engine
        self._vaults: dict[str, Any] = {}
        self._open = True

    async def place(
        self,
        collection: str,
        *,
        vector: Sequence[float],
        meta: dict[str, Any] | None = None,
        key: Any | None = None,
    ) -> str:
        """
        Stage one record.

        Args:
            collection: Target collection name.
            vector: Pre-computed embedding. Transactions have no embedder, so
                text must be embedded by the caller first.
            meta: Flat metadata mapping.
            key: Optional record key. Folded to a deterministic UUIDv5 the same
                way :class:`VectorManager` does, so a record written here stays
                addressable through the normal manager path.

        Returns:
            The stored record key.
        """
        vault = await self._vault(collection)
        payload = dict(meta or {})
        native_key = _normalize_key(key) if key is not None else None
        try:
            return await self._engine._pool.run(
                partial(vault.place, list(vector), payload, native_key),
            )
        except Exception as exc:
            raise translate(exc, store=self._engine.alias, operation="transaction.place") from exc

    async def erase(self, collection: str, key: Any) -> None:
        """Stage a deletion by record key."""
        vault = await self._vault(collection)
        try:
            await self._engine._pool.run(partial(vault.erase, _normalize_key(key)))
        except Exception as exc:
            raise translate(exc, store=self._engine.alias, operation="transaction.erase") from exc

    async def _vault(self, collection: str) -> Any:
        """Resolve and cache the transaction vault for ``collection``."""
        if not self._open:
            raise VectorStoreFault(
                store=self._engine.alias,
                operation="transaction",
                reason="transaction is already closed; open a new one",
            )
        cached = self._vaults.get(collection)
        if cached is not None:
            return cached
        try:
            vault = await self._engine._pool.run(partial(self._handle.vault, collection))
        except Exception as exc:
            raise translate(exc, store=self._engine.alias, operation="transaction.vault") from exc
        self._vaults[collection] = vault
        return vault

    def _close(self) -> None:
        """Mark the scope spent so a leaked reference fails loudly."""
        self._open = False
        self._vaults.clear()


__all__ = ["VectorEngine", "VectorTransaction"]
