"""
AquiliaDevelopmentPlatform — Fault Classes.

Typed, structured fault classes for the Aquilia Native Development Platform
(ADP). Replaces raw ``ValueError``/``RuntimeError``/bare ``except Exception``
handling with first-class Aquilia ``Fault`` objects, consistent with the rest
of the framework (see ``aquilia/tasks/faults.py``, ``aquilia/storage/base.py``).

Domains:
    DEVPLATFORM — Dev server startup, hot-reload, diagnostics, plugin, and
    configuration faults.
"""

from __future__ import annotations

from typing import Any

from aquilia.faults.core import Fault, FaultDomain, Severity

# ============================================================================
# Domain
# ============================================================================

DEVPLATFORM_DOMAIN = FaultDomain.DEVPLATFORM


# ============================================================================
# Base
# ============================================================================


class DevPlatformFault(Fault):
    """Base fault for the Aquilia Native Development Platform."""

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
            domain=DEVPLATFORM_DOMAIN,
            severity=severity,
            retryable=retryable,
            public=public,
            metadata=metadata,
        )


# ============================================================================
# Concrete Faults
# ============================================================================


class StartupFault(DevPlatformFault):
    """
    Dev server failed to start.

    Raised when socket binding fails (UDS/FD/TCP), the ASGI lifespan
    startup sequence times out, or config validation fails at boot.
    """

    def __init__(self, reason: str, **kwargs: Any):
        super().__init__(
            code="DEVPLATFORM_STARTUP_FAILED",
            message=f"Aquilia Development Platform failed to start: {reason}",
            severity=Severity.FATAL,
            retryable=False,
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )


class ReloadFault(DevPlatformFault):
    """
    Hot-reload cycle failed.

    Raised when the file watcher, dependency graph analyzer, or module
    reload executor encounters an unrecoverable error during a reload cycle.
    """

    def __init__(self, reason: str, **kwargs: Any):
        super().__init__(
            code="DEVPLATFORM_RELOAD_FAILED",
            message=f"Hot-reload cycle failed: {reason}",
            severity=Severity.ERROR,
            retryable=True,
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )


class InspectorFault(DevPlatformFault):
    """
    Inspector/telemetry wiring failure.

    Raised when trace span emission, DI diagnostic listener registration,
    or fault-bridge forwarding to Inspector fails.
    """

    def __init__(self, reason: str, **kwargs: Any):
        super().__init__(
            code="DEVPLATFORM_INSPECTOR_FAILED",
            message=f"Inspector integration failed: {reason}",
            severity=Severity.WARN,
            retryable=True,
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )


class WorkerFault(DevPlatformFault):
    """
    Background worker/diagnostic thread failure.

    Raised when the memory-usage tracker thread, event-loop monitor, or
    other ADP background worker fails to start, stop, or run correctly.
    """

    def __init__(self, reason: str, **kwargs: Any):
        super().__init__(
            code="DEVPLATFORM_WORKER_FAILED",
            message=f"ADP background worker failed: {reason}",
            severity=Severity.WARN,
            retryable=True,
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )


class ConfigurationFault(DevPlatformFault):
    """
    Invalid ADP configuration.

    Raised when ``AquiliaDevelopmentConfig`` validation fails — e.g. an
    invalid ``http``/``ws``/``log_level`` literal, a negative threshold,
    or an unusable ``AQUILIA_WORKSPACE`` path.
    """

    def __init__(self, reason: str, **kwargs: Any):
        super().__init__(
            code="DEVPLATFORM_CONFIGURATION_INVALID",
            message=f"Invalid ADP configuration: {reason}",
            severity=Severity.FATAL,
            retryable=False,
            metadata={"reason": reason, **kwargs.get("metadata", {})},
        )


def report_fault(fault: DevPlatformFault, app: Any = None) -> None:
    """
    Report a non-fatal DevPlatformFault through the host app's FaultEngine.

    If the wrapped Aquilia application exposes a ``fault_engine``
    (``getattr(app, "fault_engine", None)``), the fault is routed through
    ``FaultEngine.process()`` — Inspector's fault-bridge listener is already
    registered there (see ``aquilia/inspector/fault_bridge.py``), so the
    fault surfaces in Inspector's exception lane automatically. Falls back
    to logging ``fault.to_dict()`` at the fault's severity when no
    FaultEngine is reachable (e.g. app not yet booted, or a bare ASGI app
    without one).
    """
    import logging

    logger = logging.getLogger("aquilia.devplatform.faults")

    engine = getattr(app, "fault_engine", None)
    if engine is not None and hasattr(engine, "process"):
        try:
            engine.process(fault)
            return
        except Exception:
            pass

    log_fn = {
        Severity.INFO: logger.info,
        Severity.WARN: logger.warning,
        Severity.ERROR: logger.error,
        Severity.FATAL: logger.critical,
    }.get(fault.severity, logger.error)
    log_fn("%s: %s", fault.code, fault.to_dict())
