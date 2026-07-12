"""
Aquilia VectorDB faults -- structured fault hierarchy for the Elips-backed vector ORM.
"""

from __future__ import annotations

from typing import Any

from aquilia.faults.core import Fault, FaultDomain, Severity

__all__ = [
    "VectorFault",
    "VectorModelRegistrationFault",
    "VectorModelNotFoundFault",
    "VectorEngineFault",
    "VectorQueryFault",
    "DimensionMismatchFault",
    "EmbeddingFault",
    "VectorFieldValidationFault",
]

FaultDomain.VECTOR = FaultDomain.custom("vector", "Vector database (Elips) faults")


class VectorFault(Fault):
    """Base class for all vectordb faults."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        retryable: bool = False,
        public: bool = False,
        metadata: dict[str, Any] | None = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=FaultDomain.VECTOR,
            severity=severity,
            retryable=retryable,
            public=public,
            metadata=metadata,
        )


class VectorModelRegistrationFault(VectorFault):
    """VectorModel registration failed."""

    def __init__(self, model_name: str, reason: str, **kwargs):
        super().__init__(
            code="VECTOR_MODEL_REGISTRATION_FAILED",
            message=f"Failed to register vector model '{model_name}': {reason}",
            metadata={"model": model_name, "reason": reason, **kwargs.get("metadata", {})},
        )


class VectorModelNotFoundFault(VectorFault):
    """Record not found in an Elips vault."""

    def __init__(self, model_name: str, key: str | None = None, **kwargs):
        message = f"'{model_name}' record not found"
        if key is not None:
            message += f" for key={key!r}"
        super().__init__(
            code="VECTOR_RECORD_NOT_FOUND",
            message=message,
            metadata={"model": model_name, "key": key, **kwargs.get("metadata", {})},
        )


class VectorEngineFault(VectorFault):
    """Elips engine connection/lifecycle failure."""

    def __init__(self, reason: str, *, path: str = "", **kwargs):
        super().__init__(
            code="VECTOR_ENGINE_FAILED",
            message=f"Elips engine error: {reason}",
            severity=Severity.FATAL,
            metadata={"reason": reason, "path": path, **kwargs.get("metadata", {})},
        )


class VectorQueryFault(VectorFault):
    """Vector query execution failed."""

    def __init__(self, operation: str, reason: str, *, model: str = "unknown", **kwargs):
        super().__init__(
            code="VECTOR_QUERY_FAILED",
            message=f"Vector query on '{model}' ({operation}) failed: {reason}",
            metadata={"model": model, "operation": operation, "reason": reason, **kwargs.get("metadata", {})},
        )


class DimensionMismatchFault(VectorFault):
    """Embedding vector dimension does not match the configured dimension."""

    def __init__(self, expected: int, got: int, **kwargs):
        super().__init__(
            code="VECTOR_DIMENSION_MISMATCH",
            message=f"Embedding dimension mismatch: expected {expected}, got {got}",
            metadata={"expected": expected, "got": got, **kwargs.get("metadata", {})},
        )


class EmbeddingFault(VectorFault):
    """Embedding resolution/generation failed."""

    def __init__(self, field_name: str, reason: str, **kwargs):
        super().__init__(
            code="VECTOR_EMBEDDING_FAILED",
            message=f"Embedding field '{field_name}' failed: {reason}",
            metadata={"field": field_name, "reason": reason, **kwargs.get("metadata", {})},
        )


class VectorFieldValidationFault(VectorFault):
    """Field validation failed."""

    def __init__(self, field_name: str, reason: str, **kwargs):
        super().__init__(
            code="VECTOR_FIELD_VALIDATION_FAILED",
            message=f"Field '{field_name}': {reason}",
            metadata={"field": field_name, "reason": reason, **kwargs.get("metadata", {})},
        )
