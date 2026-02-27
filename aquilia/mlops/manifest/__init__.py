"""
Aquilia MLOps Manifest Configuration.

Parses the ``[mlops]`` section from Aquilia workspace config.
"""

from .config import MLOpsManifestConfig, ModelManifestEntry, parse_mlops_config
from .schema import validate_manifest_config

__all__ = [
    "MLOpsManifestConfig",
    "ModelManifestEntry",
    "parse_mlops_config",
    "validate_manifest_config",
]
