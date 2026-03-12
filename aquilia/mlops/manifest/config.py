"""
Manifest Config -- parse ``[mlops]`` config from Aquilia workspace config.

Supports both inline configuration and reference-based model definitions
using dotted class paths.

Example aquilia.toml::

    [mlops]
    enabled = true
    default_device = "auto"
    default_workers = 4

    [mlops.models.sentiment]
    class = "myapp.models.SentimentModel"
    version = "v1"
    device = "cuda:0"
    batch_size = 32
    max_batch_latency_ms = 50
    warmup_requests = 3

    [mlops.models.embedding]
    class = "myapp.models.EmbeddingModel"
    version = "v2"
    device = "auto"
    batch_size = 64
"""

from __future__ import annotations

import importlib
import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger("aquilia.mlops.manifest.config")


@dataclass
class ModelManifestEntry:
    """Configuration for a single model from the manifest."""

    name: str
    class_path: str  # dotted path: "myapp.models.SentimentModel"
    version: str = "v1"
    device: str = "auto"
    batch_size: int = 16
    max_batch_latency_ms: float = 50.0
    warmup_requests: int = 0
    workers: int = 4
    timeout_ms: float = 30000.0
    artifacts_dir: str = ""
    supports_streaming: bool = False
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def resolve_class(self) -> Any:
        """Import and return the model class from its dotted path."""
        module_path, _, class_name = self.class_path.rpartition(".")
        if not module_path:
            from aquilia.faults.domains import ConfigInvalidFault

            raise ConfigInvalidFault(
                key="mlops.model.class_path",
                reason=(
                    f"Invalid class path '{self.class_path}' for model '{self.name}'. "
                    f"Must be a fully qualified dotted path like 'myapp.models.MyModel'"
                ),
            )
        try:
            module = importlib.import_module(module_path)
            cls = getattr(module, class_name)
            return cls
        except (ImportError, AttributeError) as exc:
            raise ImportError(f"Cannot import model class '{self.class_path}' for model '{self.name}': {exc}") from exc

    def to_config_dict(self) -> dict[str, Any]:
        """Convert to a config dict for ModelRegistry.register()."""
        return {
            "device": self.device,
            "batch_size": self.batch_size,
            "max_batch_latency_ms": self.max_batch_latency_ms,
            "warmup_requests": self.warmup_requests,
            "workers": self.workers,
            "timeout_ms": self.timeout_ms,
            "artifacts_dir": self.artifacts_dir,
            "metadata": self.metadata,
        }


@dataclass
class MLOpsManifestConfig:
    """
    Parsed ``[mlops]`` configuration from Aquilia workspace config.

    Contains global defaults and per-model entries.
    """

    enabled: bool = True
    default_device: str = "auto"
    default_workers: int = 4
    default_batch_size: int = 16
    default_max_batch_latency_ms: float = 50.0
    default_timeout_ms: float = 30000.0
    route_prefix: str = "/mlops"
    models: list[ModelManifestEntry] = field(default_factory=list)


def parse_mlops_config(config: dict[str, Any]) -> MLOpsManifestConfig:
    """
    Parse an ``[mlops]`` config dict into ``MLOpsManifestConfig``.

    Applies global defaults to model entries where values are not
    explicitly set.

    Args:
        config: The raw config dict from the ``[mlops]`` section.

    Returns:
        A ``MLOpsManifestConfig`` with all defaults resolved.
    """
    manifest = MLOpsManifestConfig(
        enabled=config.get("enabled", True),
        default_device=config.get("default_device", "auto"),
        default_workers=config.get("default_workers", 4),
        default_batch_size=config.get("default_batch_size", 16),
        default_max_batch_latency_ms=config.get("default_max_batch_latency_ms", 50.0),
        default_timeout_ms=config.get("default_timeout_ms", 30000.0),
        route_prefix=config.get("route_prefix", "/mlops"),
    )

    # Parse model entries
    models_config = config.get("models", {})
    if isinstance(models_config, dict):
        for model_name, model_cfg in models_config.items():
            if not isinstance(model_cfg, dict):
                continue

            entry = ModelManifestEntry(
                name=model_name,
                class_path=model_cfg.get("class", ""),
                version=model_cfg.get("version", "v1"),
                device=model_cfg.get("device", manifest.default_device),
                batch_size=model_cfg.get("batch_size", manifest.default_batch_size),
                max_batch_latency_ms=model_cfg.get(
                    "max_batch_latency_ms",
                    manifest.default_max_batch_latency_ms,
                ),
                warmup_requests=model_cfg.get("warmup_requests", 0),
                workers=model_cfg.get("workers", manifest.default_workers),
                timeout_ms=model_cfg.get("timeout_ms", manifest.default_timeout_ms),
                artifacts_dir=model_cfg.get("artifacts_dir", ""),
                supports_streaming=model_cfg.get("supports_streaming", False),
                tags=model_cfg.get("tags", []),
                metadata=model_cfg.get("metadata", {}),
            )
            manifest.models.append(entry)

    return manifest
