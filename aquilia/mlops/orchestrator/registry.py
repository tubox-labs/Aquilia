"""
Model Registry -- in-memory metadata-only registry for ML models.

The registry tracks model metadata (name, version, class, config) without
eagerly loading any model into memory.  Loading is the ``ModelLoader``'s
responsibility and only happens on first request or explicit warmup.

Thread-safe via ``asyncio.Lock`` for all mutations.

Usage::

    registry = ModelRegistry()
    registry.register("sentiment", SentimentModel, version="v1", config={...})
    entry = registry.get("sentiment")
    entries = registry.list_models()
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type

from ..runtime.base import ModelState

logger = logging.getLogger("aquilia.mlops.orchestrator.registry")


@dataclass
class ModelConfig:
    """Per-model configuration (from manifest or decorator)."""
    device: str = "auto"
    batch_size: int = 16
    max_batch_latency_ms: float = 50.0
    warmup_requests: int = 0
    workers: int = 4
    timeout_ms: float = 30000.0
    artifacts_dir: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ModelConfig":
        return cls(
            device=d.get("device", "auto"),
            batch_size=d.get("batch_size", 16),
            max_batch_latency_ms=d.get("max_batch_latency_ms", 50.0),
            warmup_requests=d.get("warmup_requests", 0),
            workers=d.get("workers", 4),
            timeout_ms=d.get("timeout_ms", 30000.0),
            artifacts_dir=d.get("artifacts_dir", ""),
            metadata=d.get("metadata", {}),
        )


@dataclass
class ModelEntry:
    """
    Registry entry for a single model version.

    Tracks metadata, config, and lifecycle state without holding any
    loaded model reference (that's the loader's job).
    """
    name: str
    version: str
    model_class: Any                          # The model class (AquiliaModel subclass or callable)
    config: ModelConfig = field(default_factory=ModelConfig)
    state: ModelState = ModelState.UNLOADED
    registered_at: float = field(default_factory=time.time)
    supports_streaming: bool = False
    tags: List[str] = field(default_factory=list)

    @property
    def key(self) -> str:
        """Unique key for this model version."""
        return f"{self.name}:{self.version}"

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for API responses."""
        return {
            "name": self.name,
            "version": self.version,
            "state": self.state.value,
            "supports_streaming": self.supports_streaming,
            "registered_at": self.registered_at,
            "tags": self.tags,
            "config": {
                "device": self.config.device,
                "batch_size": self.config.batch_size,
                "max_batch_latency_ms": self.config.max_batch_latency_ms,
                "warmup_requests": self.config.warmup_requests,
                "workers": self.config.workers,
            },
        }


class ModelRegistry:
    """
    In-memory metadata-only model registry.

    Models are registered with their class and configuration but are NOT
    loaded into memory.  The ``ModelLoader`` handles lazy loading on
    first request.
    """

    def __init__(self) -> None:
        self._entries: Dict[str, ModelEntry] = {}   # key = "name:version"
        self._active: Dict[str, str] = {}           # model_name → active version
        self._lock = asyncio.Lock()

    # ── Registration ─────────────────────────────────────────────────

    async def register(
        self,
        name: str,
        model_class: Any,
        version: str = "v1",
        config: Optional[Dict[str, Any]] = None,
        supports_streaming: bool = False,
        tags: Optional[List[str]] = None,
        set_active: bool = True,
    ) -> ModelEntry:
        """
        Register a model (metadata only -- no loading).

        Args:
            name: Model identifier (e.g. "sentiment").
            model_class: The model class or callable.
            version: Model version string (e.g. "v1", "v2.1").
            config: Model configuration dict.
            supports_streaming: Whether the model supports streaming inference.
            tags: Optional tags for categorization.
            set_active: If True, set this version as the active version.

        Returns:
            The created ``ModelEntry``.
        """
        entry = ModelEntry(
            name=name,
            version=version,
            model_class=model_class,
            config=ModelConfig.from_dict(config or {}),
            supports_streaming=supports_streaming,
            tags=tags or [],
        )

        async with self._lock:
            self._entries[entry.key] = entry
            if set_active or name not in self._active:
                self._active[name] = version

        return entry

    def register_sync(
        self,
        name: str,
        model_class: Any,
        version: str = "v1",
        config: Optional[Dict[str, Any]] = None,
        supports_streaming: bool = False,
        tags: Optional[List[str]] = None,
        set_active: bool = True,
    ) -> ModelEntry:
        """Synchronous registration (for use at import time via decorators)."""
        entry = ModelEntry(
            name=name,
            version=version,
            model_class=model_class,
            config=ModelConfig.from_dict(config or {}),
            supports_streaming=supports_streaming,
            tags=tags or [],
        )
        self._entries[entry.key] = entry
        if set_active or name not in self._active:
            self._active[name] = version
        return entry

    # ── Lookup ───────────────────────────────────────────────────────

    def get(self, name: str, version: Optional[str] = None) -> Optional[ModelEntry]:
        """
        Get a model entry by name and optional version.

        If ``version`` is None, returns the active version.
        """
        if version is None:
            version = self._active.get(name)
            if version is None:
                return None
        return self._entries.get(f"{name}:{version}")

    def get_active_version(self, name: str) -> Optional[str]:
        """Get the active version for a model."""
        return self._active.get(name)

    def list_models(self) -> List[str]:
        """List all unique model names."""
        return list(self._active.keys())

    def list_versions(self, name: str) -> List[str]:
        """List all versions of a model."""
        return [
            entry.version
            for entry in self._entries.values()
            if entry.name == name
        ]

    def list_entries(self) -> List[ModelEntry]:
        """List all model entries."""
        return list(self._entries.values())

    def has(self, name: str, version: Optional[str] = None) -> bool:
        """Check if a model (and optionally a specific version) is registered."""
        if version:
            return f"{name}:{version}" in self._entries
        return name in self._active

    # ── State Updates ────────────────────────────────────────────────

    def update_state(self, name: str, version: str, state: ModelState) -> None:
        """Update the lifecycle state of a model entry."""
        entry = self._entries.get(f"{name}:{version}")
        if entry:
            entry.state = state

    async def set_active_version(self, name: str, version: str) -> bool:
        """Set the active version for a model."""
        key = f"{name}:{version}"
        if key not in self._entries:
            return False
        async with self._lock:
            self._active[name] = version
        return True

    # ── Removal ──────────────────────────────────────────────────────

    async def unregister(self, name: str, version: str) -> bool:
        """Remove a model version from the registry."""
        key = f"{name}:{version}"
        async with self._lock:
            if key not in self._entries:
                return False
            del self._entries[key]
            if self._active.get(name) == version:
                # Set another version as active, or remove
                remaining = self.list_versions(name)
                if remaining:
                    self._active[name] = remaining[-1]
                else:
                    del self._active[name]
        return True

    def summary(self) -> Dict[str, Any]:
        """Summary for health/debug endpoints."""
        return {
            "total_models": len(self._active),
            "total_versions": len(self._entries),
            "models": {
                name: {
                    "active_version": self._active[name],
                    "versions": self.list_versions(name),
                }
                for name in self._active
            },
        }
