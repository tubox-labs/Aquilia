"""
VectorDatabaseIntegration — typed vector store configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VectorDatabaseIntegration:
    """
    Typed vector database configuration.

    Declares the elips-backed stores a workspace uses. Store aliases are what
    ``VectorModel.Meta.store`` names.

    Example::

        VectorDatabaseIntegration(
            path="./.aquilia/vectors",
            stores={
                "default": {"dimension": 384, "metric": "cosine"},
                "images": {"dimension": 512, "metric": "l2", "index": "hnsw"},
            },
        )

    Notes:
        ``path`` is a directory prefix, not a URL: elips is embedded, so a store
        is a local directory holding one writer lock. Each store gets its own
        subdirectory under ``path`` unless it declares an absolute ``path`` of
        its own.

        Two stores cannot share a directory, and one store cannot serve two
        dimensions — elips holds dimension and metric database-global.
    """

    _integration_type: str = field(default="vectordb", init=False, repr=False)

    path: str = "./.aquilia/vectors"
    stores: dict[str, Any] | None = None
    default: str = "default"
    dimension: int | None = None
    metric: str | None = None
    index: str | None = None
    gpu: Any | None = None
    embedder: Any | None = None
    quantization: Any | None = None
    auto_create: bool = True
    read_only: bool = False
    pool_threads: int = 4
    enabled: bool = True

    def to_dict(self) -> dict[str, Any]:
        """
        Normalize into the shape the loader and subsystem consume.

        ``stores`` is flattened from ``{alias: config}`` into a list of entries
        each carrying its own ``alias``, matching ``StorageIntegration.to_dict``
        so ``Workspace._integrations["vectordb"]`` looks like every other
        subsystem's slot.

        Store-level settings win over the integration-level defaults: the outer
        values exist so the common case (one path, one GPU policy) is declared
        once, not so they override a store that was explicit.

        A workspace that declares no ``stores`` at all but does set
        ``dimension`` gets a single default store built from the outer values —
        that is the one-store shorthand the pyconfig ``VectorDB`` block uses.
        """
        import os

        store_list: list[dict[str, Any]] = []

        declared = dict(self.stores or {})
        if not declared and self.dimension:
            declared = {self.default: {}}

        for alias, cfg in declared.items():
            if hasattr(cfg, "to_dict"):
                entry = cfg.to_dict()
            elif isinstance(cfg, dict):
                entry = dict(cfg)
            else:
                entry = {"dimension": int(cfg)}

            entry.setdefault("alias", alias)

            if not entry.get("path"):
                entry["path"] = os.path.join(self.path, alias)

            for key, value in (
                ("dimension", self.dimension),
                ("metric", self.metric),
                ("index", self.index),
            ):
                if value is not None and key not in entry:
                    entry[key] = value

            for key, value in (
                ("gpu", self.gpu),
                ("embedder", self.embedder),
                ("quantization", self.quantization),
            ):
                if value is not None and key not in entry:
                    entry[key] = value.to_dict() if hasattr(value, "to_dict") else value

            entry.setdefault("create_if_missing", self.auto_create)
            entry.setdefault("read_only", self.read_only)

            store_list.append(entry)

        return {
            "_integration_type": "vectordb",
            "enabled": self.enabled,
            "path": self.path,
            "default": self.default,
            "stores": store_list,
            "auto_create": self.auto_create,
            "read_only": self.read_only,
            "pool_threads": self.pool_threads,
        }
