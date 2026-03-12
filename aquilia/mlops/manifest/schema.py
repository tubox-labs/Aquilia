"""
Manifest Schema Validation for MLOps configuration.

Validates manifest entries at startup to catch configuration errors
before any model loading occurs.
"""

from __future__ import annotations

import logging

from .config import MLOpsManifestConfig, ModelManifestEntry

logger = logging.getLogger("aquilia.mlops.manifest.schema")


class ManifestValidationError(ValueError):
    """Raised when manifest validation fails."""

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__(
            f"Manifest validation failed ({len(errors)} error(s)):\n" + "\n".join(f"  - {e}" for e in errors)
        )


def validate_manifest_config(config: MLOpsManifestConfig) -> list[str]:
    """
    Validate a parsed manifest config.

    Returns a list of error messages (empty if valid).
    """
    errors: list[str] = []

    # Validate global settings
    if config.default_workers < 1:
        errors.append(f"default_workers must be >= 1, got {config.default_workers}")

    if config.default_batch_size < 1:
        errors.append(f"default_batch_size must be >= 1, got {config.default_batch_size}")

    if config.default_max_batch_latency_ms <= 0:
        errors.append(f"default_max_batch_latency_ms must be > 0, got {config.default_max_batch_latency_ms}")

    # Validate each model entry
    seen_names: dict[str, str] = {}  # name:version → class_path
    for entry in config.models:
        errors.extend(_validate_model_entry(entry, seen_names))

    if errors:
        logger.error("Manifest validation failed: %d error(s)", len(errors))

    return errors


def _validate_model_entry(
    entry: ModelManifestEntry,
    seen: dict[str, str],
) -> list[str]:
    """Validate a single model manifest entry."""
    errors: list[str] = []
    prefix = f"models.{entry.name}"

    # Name validation
    if not entry.name:
        errors.append(f"{prefix}: model name cannot be empty")
        return errors  # can't validate further without a name

    if not entry.name.replace("-", "").replace("_", "").isalnum():
        errors.append(f"{prefix}: model name must be alphanumeric (with dashes/underscores)")

    # Duplicate check
    key = f"{entry.name}:{entry.version}"
    if key in seen:
        errors.append(f"{prefix}: duplicate model entry '{key}' (also defined as {seen[key]})")
    else:
        seen[key] = entry.class_path

    # Class path validation
    if not entry.class_path:
        errors.append(f"{prefix}: 'class' is required (dotted path to model class)")
    elif "." not in entry.class_path:
        errors.append(
            f"{prefix}: 'class' must be a fully qualified dotted path "
            f"(e.g. 'myapp.models.MyModel'), got '{entry.class_path}'"
        )

    # Numeric bounds
    if entry.batch_size < 1:
        errors.append(f"{prefix}: batch_size must be >= 1, got {entry.batch_size}")

    if entry.max_batch_latency_ms <= 0:
        errors.append(f"{prefix}: max_batch_latency_ms must be > 0, got {entry.max_batch_latency_ms}")

    if entry.workers < 1:
        errors.append(f"{prefix}: workers must be >= 1, got {entry.workers}")

    if entry.timeout_ms <= 0:
        errors.append(f"{prefix}: timeout_ms must be > 0, got {entry.timeout_ms}")

    if entry.warmup_requests < 0:
        errors.append(f"{prefix}: warmup_requests must be >= 0, got {entry.warmup_requests}")

    # Device validation
    valid_devices = {"auto", "cpu", "mps"}
    if entry.device not in valid_devices and not entry.device.startswith("cuda:") and entry.device != "cuda":
        errors.append(f"{prefix}: invalid device '{entry.device}'. Must be one of {valid_devices} or 'cuda:N'")

    return errors


def validate_and_raise(config: MLOpsManifestConfig) -> None:
    """Validate and raise ``ManifestValidationError`` if invalid."""
    errors = validate_manifest_config(config)
    if errors:
        raise ManifestValidationError(errors)
