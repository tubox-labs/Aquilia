from aquilia.faults.core import Fault, FaultDomain, Severity

INSPECTOR_DOMAIN = FaultDomain.custom("inspector", "Request inspector / debugging faults")


class InspectorFault(Fault):
    """Base fault class for Request Inspector subsystem."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        severity: Severity = Severity.ERROR,
        retryable: bool = False,
        public: bool = False,
        metadata: dict | None = None,
    ):
        super().__init__(
            code=code,
            message=message,
            domain=INSPECTOR_DOMAIN,
            severity=severity,
            retryable=retryable,
            public=public,
            metadata=metadata,
        )


class InspectorConfigFault(InspectorFault):
    """Raised for bad InspectorConfig values."""

    pass


class InspectorReplayFault(InspectorFault):
    """Raised when trace is expired or replay is blocked."""

    pass


class InspectorCaptureFault(InspectorFault):
    """Internal capture error (caught defensively)."""

    pass


class InspectorExportFault(InspectorFault):
    """Raised for JSON export serialization failures."""

    pass
