"""
Aquilia VectorDB configuration -- typed connection settings for Elips.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

__all__ = ["ElipsConfig"]


@dataclass
class ElipsConfig:
    """
    Connection configuration for an Elips vector database engine.

    Passed to ``ElipsEngine(config)``. ``to_connect_kwargs()`` produces the
    keyword arguments handed to ``elips.connect(path, **kwargs)``.
    """

    path: str = ":memory:"
    dimension: int = 0
    metric: Literal["cosine", "euclidean", "dot_product"] = "cosine"
    index: Literal["graph", "exact"] = "graph"
    access_mode: Literal["read_write", "read_only"] = "read_write"
    segmented_storage: bool = True
    metadata_acceleration: bool = True
    embedder: Callable | None = None
    use_default_text_embedder: bool = True
    max_workers: int = 4
    auto_connect: bool = True
    options: dict[str, Any] = field(default_factory=dict)

    def to_connect_kwargs(self) -> dict[str, Any]:
        """Build the keyword arguments for ``elips.connect(path, **kwargs)``."""
        kwargs: dict[str, Any] = {
            "dimension": self.dimension,
            "metric": self.metric,
            "index": self.index,
            "access_mode": self.access_mode,
            "segmented_storage": self.segmented_storage,
            "metadata_acceleration": self.metadata_acceleration,
            "use_default_text_embedder": self.use_default_text_embedder,
        }
        if self.embedder is not None:
            kwargs["embedder"] = self.embedder
        kwargs.update(self.options)
        return kwargs
