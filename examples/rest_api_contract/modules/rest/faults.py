"""
Structured Faults for rest Module.
"""

from typing import Any
from aquilia.faults import Fault, FaultDomain, Severity

REST_DOMAIN = FaultDomain.custom("rest", "REST domain faults")


class RestModuleFault(Fault):
    """Base fault for rest module operations."""

    domain = REST_DOMAIN
    severity = Severity.WARN
    public = True

    def __init__(
        self,
        message: str | None = None,
        code: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            domain=self.domain,
            severity=self.severity,
            public=True,
            metadata=metadata,
            **kwargs,
        )


class RestNotFoundFault(RestModuleFault):
    """Fault raised when a rest article is not found."""

    code = "rest.not_found"
    message = "Requested rest article was not found"
    status = 404

    def __init__(self, item_id: str | None = None, **kwargs: Any) -> None:
        meta = kwargs.pop("metadata", None) or {}
        if item_id:
            meta["item_id"] = item_id
        super().__init__(metadata=meta, **kwargs)