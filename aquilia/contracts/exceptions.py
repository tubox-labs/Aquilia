"""
Aquilia Contract Exceptions -- Fault-domain-integrated error hierarchy.

All Contract errors participate in Aquilia's fault domain system,
producing structured error responses with field→message mapping.
"""

from __future__ import annotations

from typing import Any

from ..faults.core import Fault, FaultDomain, Severity

# ── Fault Domain ─────────────────────────────────────────────────────────

CONTRACT = FaultDomain(
    name="CONTRACT",
    description="Contract contract violations -- casting, sealing, imprinting",
)


# ── Base ─────────────────────────────────────────────────────────────────


class ContractFault(Fault):
    """Base fault for all Contract errors."""

    domain = CONTRACT
    severity = Severity.ERROR
    code = "BP000"
    public = True

    def __init__(
        self,
        message: str = "Contract validation failed",
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


class CastFault(ContractFault):
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


class SealFault(ContractFault):
    """Raised when a validation seal is broken."""

    code = "BP200"

    def __init__(
        self,
        message: str = "Contract validation failed",
        *,
        errors: dict[str, list[str]] | None = None,
        code: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        # Flatten errors for details if possible
        details = None
        if errors:
            # If only one field failed, show that field and its reason
            if len(errors) == 1:
                field, reasons = next(iter(errors.items()))
                details = {"field": field, "reason": reasons[0] if reasons else "Validation failed"}
            else:
                # Multiple fields: show all
                details = {"fields": [{"field": f, "reasons": rs} for f, rs in errors.items()]}
        meta = dict(metadata or {})
        if details:
            meta["details"] = details
        super().__init__(message=message, errors=errors, code=code, metadata=meta)


class ImprintFault(ContractFault):
    """Raised when a write (imprint) operation fails."""

    code = "BP300"


class ProjectionFault(ContractFault):
    """Raised when an invalid projection is requested."""

    code = "BP400"

    def __init__(self, projection: str, available: list[str]):
        super().__init__(
            message=f"Unknown projection '{projection}'. Available: {available}",
            metadata={"requested": projection, "available": available},
        )


class LensDepthFault(ContractFault):
    """Raised when Lens traversal exceeds maximum depth."""

    code = "BP500"

    def __init__(self, path: str, max_depth: int):
        super().__init__(
            message=f"Lens depth exceeded at '{path}' (max={max_depth})",
            metadata={"path": path, "max_depth": max_depth},
        )


class LensCycleFault(ContractFault):
    """Raised when a circular Lens reference is detected."""

    code = "BP501"

    def __init__(self, cycle_path: list[str]):
        super().__init__(
            message=f"Circular Lens reference detected: {' → '.join(cycle_path)}",
            metadata={"cycle": cycle_path},
        )


class LensUnresolvedFault(ContractFault):
    """
    Raised when a to-many :class:`~aquilia.contracts.lenses.Lens` receives an
    un-awaited related manager or queryset.

    Serialization is synchronous, so it cannot await the ORM. The relation must
    be prefetched (``prefetch_related``) or materialized to a list before the
    Contract renders it.

    Args:
        field: Name of the Lens facet that could not be resolved.

    Examples:
        >>> order = await Order.objects.prefetch_related("items").get(pk=1)
        >>> OrderContract(instance=order).data  # resolves cleanly

    Notes:
        This replaces an earlier behaviour that returned ``[]`` for unresolved
        relations. An empty list is indistinguishable from a genuinely empty
        relation, which silently produced wrong API responses — including, in
        the worst case, an empty permission list read as "no permissions".

    See Also:
        :class:`LensDepthFault`, :class:`LensCycleFault`
    """

    code = "BP503"

    def __init__(self, field: str):
        super().__init__(
            message=(
                f"Lens '{field}' received an unresolved async manager. "
                f"Prefetch the relation (e.g. prefetch_related('{field}')) or "
                f"assign an awaited list before serializing."
            ),
            errors={field: ["Related collection was not resolved before serialization"]},
            metadata={"field": field},
        )
        self.field = field


#: Maximum nesting depth for inbound nested-Contract validation.
#:
#: Deeply nested payloads are a denial-of-service vector: JSON allows
#: arbitrary nesting in a few kilobytes, and each level costs a Python stack
#: frame. Exceeding this limit produces a structured
#: :class:`NestingDepthFault` (a clean 4xx) instead of an uncaught
#: ``RecursionError`` that would abort the request coroutine mid-stack.
#:
#: Lives here rather than on a Facet class so both the annotation layer and
#: the compiled :class:`~aquilia.contracts.sigil.Sigil` can reference one
#: authoritative value without an import cycle.
MAX_NESTING_DEPTH: int = 32


class NestingDepthFault(ContractFault):
    """
    Raised when inbound nested-Contract validation exceeds its depth limit.

    Complements :class:`LensDepthFault`, which guards the *outbound*
    (serialization) direction. This fault guards the *inbound* direction and
    is the graceful failure mode for maliciously or accidentally
    deeply-nested request bodies.

    Args:
        field: Name of the facet at which the limit was reached.
        max_depth: The limit that was exceeded.

    Examples:
        >>> class Node(Contract):
        ...     label: str
        ...     child: "Node" = None
        >>> deep = {"label": "x"}
        >>> for _ in range(100):
        ...     deep = {"label": "x", "child": deep}
        >>> bp = Node(data=deep)
        >>> bp.is_sealed()
        False
        >>> "child" in bp.errors
        True

    See Also:
        :data:`MAX_NESTING_DEPTH`, :class:`LensDepthFault`
    """

    code = "BP502"

    def __init__(self, field: str, max_depth: int):
        super().__init__(
            message=f"Nested Contract depth exceeds maximum of {max_depth} at '{field}'",
            errors={field: [f"Nested Contract depth exceeds maximum of {max_depth}"]},
            metadata={"field": field, "max_depth": max_depth},
        )
        self.field = field
        self.max_depth = max_depth


class ContractAsyncMismatchFault(ContractFault, RuntimeError):
    """Raised when an async-only contract/field operation is called synchronously."""

    code = "BP201"

    def __init__(self, message: str, **kwargs):
        ContractFault.__init__(self, message=message, **kwargs)
        RuntimeError.__init__(self, message)


class StubGenerationFault(ContractFault):
    """
    Raised when a ``.pyi`` stub cannot be generated for a module.

    A developer-tooling fault, not a request-path one: it surfaces from
    ``aq contracts stubs``, never from serving traffic. It is therefore not
    public — its message names local module paths.

    Args:
        message: What could not be stubbed and why.

    See Also:
        :mod:`aquilia.contracts.stubs`
    """

    code = "BP600"
    public = False
    severity = Severity.WARN
