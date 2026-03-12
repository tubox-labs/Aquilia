"""
MLOpsIntegration — typed MLOps platform configuration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MLOpsIntegration:
    """
    Typed MLOps platform configuration.

    Example::

        MLOpsIntegration(
            registry_db="models.db",
            drift_method="psi",
            max_batch_size=32,
        )
    """

    _integration_type: str = field(default="mlops", init=False, repr=False)

    enabled: bool = True
    registry_db: str = "registry.db"
    blob_root: str = ".aquilia-store"
    storage_backend: str = "filesystem"
    drift_method: str = "psi"
    drift_threshold: float = 0.2
    drift_num_bins: int = 10
    max_batch_size: int = 16
    max_latency_ms: float = 50.0
    batching_strategy: str = "hybrid"
    sample_rate: float = 0.01
    log_dir: str = "prediction_logs"
    hmac_secret: str | None = None
    signing_private_key: str | None = None
    signing_public_key: str | None = None
    encryption_key: Any | None = None
    plugin_auto_discover: bool = True
    scaling_policy: dict[str, Any] | None = None
    rollout_default_strategy: str = "canary"
    auto_rollback: bool = True
    metrics_model_name: str = ""
    metrics_model_version: str = ""
    cache_enabled: bool = True
    cache_ttl: int = 60
    cache_namespace: str = "mlops"
    artifact_store_dir: str = "artifacts"
    fault_engine_debug: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "_integration_type": "mlops",
            "enabled": self.enabled,
            "registry": {
                "db_path": self.registry_db,
                "blob_root": self.blob_root,
                "storage_backend": self.storage_backend,
            },
            "serving": {
                "max_batch_size": self.max_batch_size,
                "max_latency_ms": self.max_latency_ms,
                "batching_strategy": self.batching_strategy,
            },
            "observe": {
                "drift_method": self.drift_method,
                "drift_threshold": self.drift_threshold,
                "drift_num_bins": self.drift_num_bins,
                "sample_rate": self.sample_rate,
                "log_dir": self.log_dir,
                "metrics_model_name": self.metrics_model_name,
                "metrics_model_version": self.metrics_model_version,
            },
            "release": {
                "rollout_default_strategy": self.rollout_default_strategy,
                "auto_rollback": self.auto_rollback,
            },
            "security": {
                "hmac_secret": self.hmac_secret,
                "signing_private_key": self.signing_private_key,
                "signing_public_key": self.signing_public_key,
                "encryption_key": self.encryption_key,
            },
            "plugins": {
                "auto_discover": self.plugin_auto_discover,
            },
            "scaling_policy": self.scaling_policy,
            "ecosystem": {
                "cache_enabled": self.cache_enabled,
                "cache_ttl": self.cache_ttl,
                "cache_namespace": self.cache_namespace,
                "artifact_store_dir": self.artifact_store_dir,
                "fault_engine_debug": self.fault_engine_debug,
            },
        }
