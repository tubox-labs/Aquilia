"""
Aquilia Blueprint Exceptions -- Fault-domain-integrated error hierarchy.

All Blueprint errors participate in Aquilia's fault domain system,
producing structured error responses with field→message mapping.
"""

from __future__ import annotations

from typing import Any

from ..faults.core import Fault, FaultDomain, Severity

# ── Fault Domain ─────────────────────────────────────────────────────────

BLUEPRINT = FaultDomain(
    name="BLUEPRINT",
    description="Blueprint contract violations -- casting, sealing, imprinting",
)


# ── Base ─────────────────────────────────────────────────────────────────


class BlueprintFault(Fault):
    """Base fault for all Blueprint errors."""

    domain = BLUEPRINT
    severity = Severity.ERROR
    code = "BP000"
    public = True

    def __init__(
        self,
        message: str = "Blueprint validation failed",
        *,
        errors: dict[str, list[str]] | None = None,
        code: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        self.field_errors: dict[str, list[str]] = errors or {}
        super().__init__(
            message=message,
            code=code or self.__class__.code,
            metadata={**(metadata or {}), "field_errors": self.field_errors},
        )

    def as_response_body(self) -> dict[str, Any]:
        """Structured error payload for API responses."""
        body: dict[str, Any] = {
            "fault": self.code,
            "message": str(self),
        }
        if self.field_errors:
            body["errors"] = self.field_errors
        return body


# ── Specific Faults ──────────────────────────────────────────────────────


class CastFault(BlueprintFault):
    """Raised when incoming data cannot be cast to the expected type."""

    code = "BP100"

    def __init__(
        self,
        field: str,
        message: str = "Invalid value",
        *,
        metadata: dict[str, Any] | None = None,
    ):
        super().__init__(
            message=f"Cast failed for '{field}': {message}",
            errors={field: [message]},
            metadata=metadata,
        )
        self.field = field


class SealFault(BlueprintFault):
    """Raised when a validation seal is broken."""
    code = "BP200"

    def __init__(self, message: str = "Blueprint validation failed", *, errors: dict[str, list[str]] | None = None, code: str | None = None, metadata: dict[str, Any] | None = None):
        # Flatten errors for details if possible
        details = None
        if errors:
            # If only one field failed, show that field and its reason
            if len(errors) == 1:
                field, reasons = next(iter(errors.items()))
                details = {"field": field, "reason": reasons[0] if reasons else "Validation failed"}
            else:
                # Multiple fields: show all
                details = {"fields": [
                    {"field": f, "reasons": rs} for f, rs in errors.items()
                ]}
        meta = dict(metadata or {})
        if details:
            meta["details"] = details
        super().__init__(message=message, errors=errors, code=code, metadata=meta)


class ImprintFault(BlueprintFault):
    """Raised when a write (imprint) operation fails."""

    code = "BP300"


class ProjectionFault(BlueprintFault):
    """Raised when an invalid projection is requested."""

    code = "BP400"

    def __init__(self, projection: str, available: list[str]):
        super().__init__(
            message=f"Unknown projection '{projection}'. Available: {available}",
            metadata={"requested": projection, "available": available},
        )


class LensDepthFault(BlueprintFault):
    """Raised when Lens traversal exceeds maximum depth."""

    code = "BP500"

    def __init__(self, path: str, max_depth: int):
        super().__init__(
            message=f"Lens depth exceeded at '{path}' (max={max_depth})",
            metadata={"path": path, "max_depth": max_depth},
        )


class LensCycleFault(BlueprintFault):
    """Raised when a circular Lens reference is detected."""

    code = "BP501"

    def __init__(self, cycle_path: list[str]):
        super().__init__(
            message=f"Circular Lens reference detected: {' → '.join(cycle_path)}",
            metadata={"cycle": cycle_path},
        )
