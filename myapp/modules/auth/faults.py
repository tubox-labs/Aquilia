"""
Auth module faults (error handling).

Faults define domain-specific errors and their recovery strategies.
They are automatically registered with the fault handling system.
"""

from aquilia.faults import Fault, FaultDomain, Severity, RecoveryStrategy


# Define fault domain for this module
AUTH = FaultDomain.custom(
    "AUTH",
    "Auth module faults",
)


class AuthNotFoundFault(Fault):
    """
    Raised when a auth is not found.

    Recovery: Return 404 response
    """

    domain = AUTH
    severity = Severity.INFO
    code = "AUTH_NOT_FOUND"

    def __init__(self, item_id: int):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message=f"Auth with id {item_id} not found",
            metadata={"item_id": item_id},
            retryable=False,
        )


class AuthValidationFault(Fault):
    """
    Raised when auth data validation fails.

    Recovery: Return 400 response with validation errors
    """

    domain = AUTH
    severity = Severity.INFO
    code = "AUTH_VALIDATION_ERROR"

    def __init__(self, errors: dict):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message="Validation failed",
            metadata={"errors": errors},
            retryable=False,
        )


class AuthOperationFault(Fault):
    """
    Raised when a auth operation fails.

    Recovery: Retry with exponential backoff
    """

    domain = AUTH
    severity = Severity.WARN
    code = "AUTH_OPERATION_FAILED"

    def __init__(self, operation: str, reason: str):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message=f"Operation '{operation}' failed: {reason}",
            metadata={"operation": operation, "reason": reason},
            retryable=True,
        )