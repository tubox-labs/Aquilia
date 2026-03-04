"""
Tubox module faults (error handling).

Faults define domain-specific errors and their recovery strategies.
They are automatically registered with the fault handling system.
"""

from aquilia.faults import Fault, FaultDomain, Severity, RecoveryStrategy


# Define fault domain for this module
TUBOX = FaultDomain.custom(
    "TUBOX",
    "Tubox module faults",
)


class TuboxNotFoundFault(Fault):
    """
    Raised when a Tubox is not found.

    Recovery: Return 404 response
    """

    domain = TUBOX
    severity = Severity.INFO
    code = "TUBOX_NOT_FOUND"

    def __init__(self, item_id: int):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message=f"Tubox with id {item_id} not found",
            metadata={"item_id": item_id},
            retryable=False,
        )


class TuboxValidationFault(Fault):
    """
    Raised when Tubox data validation fails.

    Recovery: Return 400 response with validation errors
    """

    domain = TUBOX
    severity = Severity.INFO
    code = "TUBOX_VALIDATION_ERROR"

    def __init__(self, errors: dict):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message="Validation failed",
            metadata={"errors": errors},
            retryable=False,
        )


class TuboxOperationFault(Fault):
    """
    Raised when a Tubox operation fails.

    Recovery: Retry with exponential backoff
    """

    domain = TUBOX
    severity = Severity.WARN
    code = "TUBOX_OPERATION_FAILED"

    def __init__(self, operation: str, reason: str):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message=f"Operation '{operation}' failed: {reason}",
            metadata={"operation": operation, "reason": reason},
            retryable=True,
        )