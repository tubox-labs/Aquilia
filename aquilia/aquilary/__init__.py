"""
Aquilary - Manifest-driven App Registry for Aquilia

Production-grade registry system that:
- Safely discovers and validates manifests (no import-time side effects)
- Builds deterministic app loading order (dependency-aware)
- Produces scoped runtime registries with fingerprints
- Integrates with DI/effects/router/middleware
- Supports dev hot-reload and freeze mode for deploys
"""

from aquilia._version import __version__  # noqa: F401 — re-exported
from aquilia.aquilary.core import (
    AppContext,
    Aquilary,
    AquilaryRegistry,
    RegistryFingerprint,
    RegistryMode,
    RuntimeRegistry,
)
from aquilia.aquilary.errors import (
    ConfigValidationError,
    CrossAppUsageError,
    DependencyCycleError,
    DuplicateAppError,
    ErrorSpan,
    FrozenManifestMismatchError,
    HotReloadError,
    ManifestValidationError,
    RegistryError,
    RouteConflictError,
)
from aquilia.aquilary.fingerprint import FingerprintGenerator
from aquilia.aquilary.graph import DependencyGraph, GraphNode
from aquilia.aquilary.loader import ManifestLoader, ManifestSource
from aquilia.aquilary.validator import RegistryValidator, ValidationReport

__all__ = [
    # Core
    "Aquilary",
    "AquilaryRegistry",
    "RuntimeRegistry",
    "AppContext",
    "RegistryMode",
    # Errors
    "RegistryError",
    "DependencyCycleError",
    "RouteConflictError",
    "ConfigValidationError",
    "CrossAppUsageError",
    "ManifestValidationError",
    "DuplicateAppError",
    "FrozenManifestMismatchError",
    "HotReloadError",
    "ErrorSpan",
    # Fingerprint
    "FingerprintGenerator",
    "RegistryFingerprint",
    # Loader
    "ManifestLoader",
    "ManifestSource",
    # Validator
    "RegistryValidator",
    "ValidationReport",
    # Graph
    "DependencyGraph",
    "GraphNode",
]
