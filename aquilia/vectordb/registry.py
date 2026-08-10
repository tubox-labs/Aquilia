"""
AquilaVectorDB — Model and engine registry.

Two responsibilities:

1. **Model registration.** Every concrete ``VectorModel`` registers itself at
   class-creation time, so a module import is all discovery needs — the same
   contract ``ModelRegistry`` offers the SQL ORM.
2. **Engine grouping.** Stores are opened lazily, one ``VectorEngine`` per
   configured alias, and models are bound to the store named by
   ``Meta.store``.

The grouping rule
-----------------

elips holds ``dimension`` and ``metric`` **database-global**: they are set once
at ``connect()`` and every vault inherits them. Two models with different
dimensions therefore cannot share a directory — reopening with a different
dimension raises ``ConfigError``.

So binding validates each model against its store's configuration and fails
loudly on a mismatch, naming both sides. The alternative — coercing the model to
the store's dimension — would write vectors that search returns in the wrong
order, with nothing in the logs.

Collections within one store are independent, so any number of models may share
a store as long as they agree on ``(dimension, metric)``.
"""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from aquilia.vectordb.configs import VectorStoreConfig
from aquilia.vectordb.faults import VectorRegistryFault, VectorSchemaFault
from aquilia.vectordb.pool import VectorPool

if TYPE_CHECKING:
    from aquilia.vectordb.base import VectorModel
    from aquilia.vectordb.engine import VectorEngine

logger = logging.getLogger("aquilia.vectordb.registry")


class VectorRegistry:
    """
    Process-wide registry of vector models, stores, and live engines.

    Class-level state, mirroring ``aquilia.models.registry.ModelRegistry``:
    models self-register at import time, long before any server exists, so the
    registry cannot be instance-scoped without making discovery order matter.
    """

    _models: dict[str, type[VectorModel]] = {}
    _stores: dict[str, VectorStoreConfig] = {}
    _engines: dict[str, VectorEngine] = {}
    _pool: VectorPool | None = None
    _lock: asyncio.Lock | None = None
    _default_store: str = "default"

    # ── Model registration ───────────────────────────────────────────────

    @classmethod
    def register(cls, model_cls: type[VectorModel]) -> None:
        """
        Register a concrete vector model.

        Called by :class:`~aquilia.vectordb.metaclass.VectorModelMeta`.

        Args:
            model_cls: The model class.

        Raises:
            VectorSchemaFault: When a different class is already registered
                under this name *and* targets the same collection. Re-importing
                the same module (common under autoreload and in tests) rebinds
                silently; two genuinely different models colliding does not.
        """
        name = model_cls.__name__
        existing = cls._models.get(name)

        if existing is not None and existing is not model_cls:
            old_col = getattr(getattr(existing, "_voptions", None), "collection", None)
            new_col = getattr(getattr(model_cls, "_voptions", None), "collection", None)
            same_origin = existing.__module__ == model_cls.__module__
            if old_col == new_col and not same_origin:
                raise VectorSchemaFault(
                    model=name,
                    reason=(
                        f"another vector model named {name!r} is already registered for "
                        f"collection {new_col!r} (from {existing.__module__}). Rename one, "
                        f"or give them distinct Meta.collection values."
                    ),
                )

        cls._models[name] = model_cls

    @classmethod
    def get(cls, name: str) -> type[VectorModel] | None:
        """Return a registered model by class name, or ``None``."""
        return cls._models.get(name)

    @classmethod
    def all_models(cls) -> dict[str, type[VectorModel]]:
        """Return a copy of the registered-model mapping."""
        return dict(cls._models)

    @classmethod
    def models_for_store(cls, alias: str) -> list[type[VectorModel]]:
        """Return every model bound to the store ``alias``."""
        return [m for m in cls._models.values() if getattr(m._voptions, "store", "default") == alias]

    # ── Store configuration ──────────────────────────────────────────────

    @classmethod
    def configure(
        cls,
        stores: list[VectorStoreConfig] | list[dict[str, Any]],
        *,
        default: str = "default",
        pool_threads: int = 4,
    ) -> None:
        """
        Install store configuration.

        Called by the subsystem at boot. Replaces any previous configuration but
        does **not** close live engines — :meth:`shutdown` is the explicit way to
        do that, so a reconfigure cannot silently drop a writer lock that
        in-flight queries still hold.

        Args:
            stores: Store configurations, as dataclasses or plain dicts.
            default: Alias used by models that do not name a store.
            pool_threads: Worker count for the shared thread pool.
        """
        resolved: dict[str, VectorStoreConfig] = {}
        for entry in stores:
            config = VectorStoreConfig.from_dict(entry) if isinstance(entry, dict) else entry
            resolved[config.alias] = config

        cls._stores = resolved
        cls._default_store = default
        if cls._pool is None:
            cls._pool = VectorPool(max_workers=pool_threads)

    @classmethod
    def store_config(cls, alias: str) -> VectorStoreConfig:
        """
        Return the configuration for ``alias``.

        Raises:
            VectorRegistryFault: When the alias is not configured.
        """
        config = cls._stores.get(alias)
        if config is None:
            known = ", ".join(sorted(cls._stores)) or "(none configured)"
            raise VectorRegistryFault(
                reason=(
                    f"no vector store configured with alias {alias!r}. Configured stores: {known}. "
                    f"Add one with Workspace.vectordb(stores=...)."
                )
            )
        return config

    @classmethod
    def store_names(cls) -> list[str]:
        """Return configured store aliases."""
        return sorted(cls._stores)

    @classmethod
    def pool(cls) -> VectorPool:
        """Return the shared thread pool, creating it on first use."""
        if cls._pool is None:
            cls._pool = VectorPool()
        return cls._pool

    # ── Engine access ────────────────────────────────────────────────────

    @classmethod
    async def engine(cls, alias: str | None = None) -> VectorEngine:
        """
        Return the live engine for ``alias``, opening it on first use.

        Args:
            alias: Store alias. Defaults to the configured default store.

        Returns:
            The connected :class:`~aquilia.vectordb.engine.VectorEngine`.

        Raises:
            VectorRegistryFault: When the alias is not configured.
        """
        name = alias or cls._default_store

        engine = cls._engines.get(name)
        if engine is not None and engine.connected:
            return engine

        if cls._lock is None:
            cls._lock = asyncio.Lock()

        async with cls._lock:
            engine = cls._engines.get(name)
            if engine is not None and engine.connected:
                return engine

            from aquilia.vectordb.engine import VectorEngine

            config = cls.store_config(name)
            engine = VectorEngine(config, pool=cls.pool())
            await engine.connect()
            cls._engines[name] = engine
            return engine

    @classmethod
    async def engine_for(cls, model_cls: type[VectorModel]) -> VectorEngine:
        """
        Return the engine backing ``model_cls``, validating schema compatibility.

        Args:
            model_cls: The vector model.

        Returns:
            The connected engine for the model's store.

        Raises:
            VectorSchemaFault: When the model's dimension or metric disagrees
                with the store's — elips holds both database-global, so a
                mismatch cannot be reconciled at the collection level.
        """
        options = model_cls._voptions
        engine = await cls.engine(options.store)
        cls._validate_binding(model_cls, engine.config)
        return engine

    @classmethod
    def _validate_binding(cls, model_cls: type[VectorModel], config: VectorStoreConfig) -> None:
        """Check a model's declared shape against its store's configuration."""
        schema = model_cls._vfields
        options = model_cls._voptions

        if schema.dimension and schema.dimension != config.dimension:
            raise VectorSchemaFault(
                model=schema.model_name,
                reason=(
                    f"declares dimension {schema.dimension} but store {config.alias!r} is "
                    f"configured for {config.dimension}. elips holds dimension "
                    f"database-global, so they must match — change Meta.dimension, or "
                    f"bind this model to a different store."
                ),
            )

        # `metric` defaults to "cosine" on both sides, so only an explicit
        # disagreement is worth failing over.
        if options.metric != config.metric and options.metric != "cosine":
            raise VectorSchemaFault(
                model=schema.model_name,
                reason=(
                    f"declares metric {options.metric!r} but store {config.alias!r} uses "
                    f"{config.metric!r}. elips holds the metric database-global; a mismatch "
                    f"would rank results by a different distance than declared."
                ),
            )

        cls._warn_model_graph_knobs(model_cls, config)

    #: ``Meta`` attributes that describe graph-index tuning. elips fixes these
    #: per *database*, not per collection, so a model cannot own them.
    _MODEL_GRAPH_KNOBS = ("ef_search", "max_connections", "ef_construction", "compaction_ratio")

    #: Models already warned about, so a hot query path warns once per model.
    _WARNED_GRAPH_KNOBS: set[str] = set()

    @classmethod
    def _warn_model_graph_knobs(cls, model_cls: type[VectorModel], config: VectorStoreConfig) -> None:
        """
        Warn when a model declares graph tuning its store does not carry.

        ``Meta.ef_search`` and friends are parsed into
        :class:`~aquilia.vectordb.schema.VectorOptions` but cannot be honoured
        per model: elips builds one index per database, shared by every
        collection in it, so two models on one store would be asking for two
        different graphs. The knob belongs on the store's ``index_options``.

        Warned rather than raised — a model carrying an inherited ``Meta`` from
        a shared base should not fail to bind over a tuning hint.
        """
        options = model_cls._voptions
        declared = [knob for knob in cls._MODEL_GRAPH_KNOBS if getattr(options, knob, None) is not None]
        if not declared:
            return

        key = f"{model_cls.__module__}.{model_cls.__name__}"
        if key in cls._WARNED_GRAPH_KNOBS:
            return
        cls._WARNED_GRAPH_KNOBS.add(key)

        missing = [knob for knob in declared if knob not in config.index_options]
        if not missing:
            return

        logger.warning(
            "%s declares Meta.%s, but elips tunes the graph index per database rather than "
            "per collection, so a model cannot set it. Move it to store %r: "
            "index_options={%s}.",
            model_cls.__name__,
            ", Meta.".join(missing),
            config.alias,
            ", ".join(f"{knob!r}: {getattr(options, knob)!r}" for knob in missing),
        )

    # ── Lifecycle ────────────────────────────────────────────────────────

    @classmethod
    async def connect_all(cls) -> dict[str, VectorEngine]:
        """
        Open every configured store.

        Returns:
            ``{alias: engine}`` for the stores that opened.

        Raises:
            The first fault encountered. Stores already opened stay open; the
            subsystem tears them down on a failed boot.
        """
        for alias in cls.store_names():
            await cls.engine(alias)
        return dict(cls._engines)

    @classmethod
    async def shutdown(cls, *, timeout: float = 10.0) -> None:
        """
        Close every engine and drain the pool.

        Args:
            timeout: Seconds allowed for pool drain.

        Notes:
            Never raises. Shutdown must complete even when a store is already
            broken, or one bad store would strand the rest with their locks held.
        """
        engines = list(cls._engines.values())
        cls._engines.clear()

        for engine in engines:
            try:
                await engine.close()
            except Exception as exc:
                logger.warning("Error closing vector engine %r: %s", engine.alias, exc)

        if cls._pool is not None:
            try:
                await cls._pool.shutdown(timeout=timeout)
            except Exception as exc:
                logger.warning("Error shutting down vector pool: %s", exc)

    @classmethod
    async def health(cls) -> dict[str, Any]:
        """
        Aggregate health across configured stores.

        Returns:
            ``{"ok": bool, "stores": {alias: {...}}, "models": int}``. A store
            that is configured but not yet opened reports ``ok=False`` with
            ``"not connected"`` rather than being omitted.
        """
        stores: dict[str, Any] = {}
        for alias in cls.store_names():
            engine = cls._engines.get(alias)
            if engine is None:
                stores[alias] = {"alias": alias, "ok": False, "error": "not connected"}
                continue
            stores[alias] = await engine.health()

        return {
            "ok": bool(stores) and all(s.get("ok") for s in stores.values()),
            "stores": stores,
            "models": len(cls._models),
        }

    @classmethod
    def gpu_info(cls) -> dict[str, Any]:
        """Return the GPU capability snapshot, for health and ``aq vectordb gpu status``."""
        from aquilia.vectordb.gpu import probe

        return probe().to_dict()

    @classmethod
    def reset(cls) -> None:
        """
        Drop all registry state.

        For tests only. Does **not** close engines — call
        :meth:`shutdown` first, or the writer locks stay held for the life of
        the process.
        """
        cls._models.clear()
        cls._stores.clear()
        cls._engines.clear()
        cls._pool = None
        cls._lock = None
        cls._default_store = "default"


__all__ = ["VectorRegistry"]
