"""
Health Registry -- Centralized subsystem health tracking.

Architecture v2: Provides health status reporting for all subsystems,
enabling graceful degradation and /health endpoint support.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional

logger = logging.getLogger("aquilia.health")


class SubsystemStatus(str, Enum):
    """Status of a subsystem."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"
    STARTING = "starting"
    STOPPED = "stopped"


@dataclass
class HealthStatus:
    """Health status for a single subsystem."""
    name: str
    status: SubsystemStatus = SubsystemStatus.UNKNOWN
    latency_ms: float = 0.0
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def to_dict(self) -> dict:
        """Serialize for JSON response."""
        return {
            "name": self.name,
            "status": self.status.value,
            "latency_ms": round(self.latency_ms, 2),
            "message": self.message,
            "checked_at": self.checked_at.isoformat(),
        }


class HealthRegistry:
    """
    Centralized health tracking for all subsystems.

    Subsystems register their health during startup and can update
    it at any time. The registry provides an aggregate health status
    suitable for load balancer health checks.
    """

    def __init__(self):
        self._statuses: Dict[str, HealthStatus] = {}
        self._checks: Dict[str, Callable[[], HealthStatus]] = {}

    def register(self, name: str, status: HealthStatus) -> None:
        """Register or update a subsystem's health status."""
        self._statuses[name] = status

    def register_check(self, name: str, check: Callable[[], HealthStatus]) -> None:
        """Register a health check function for periodic evaluation."""
        self._checks[name] = check

    def update(self, name: str, status: SubsystemStatus, message: str = "") -> None:
        """Update an existing subsystem's status."""
        if name in self._statuses:
            self._statuses[name].status = status
            self._statuses[name].message = message
            self._statuses[name].checked_at = datetime.now(timezone.utc)
        else:
            self._statuses[name] = HealthStatus(
                name=name, status=status, message=message
            )

    def get(self, name: str) -> Optional[HealthStatus]:
        """Get a specific subsystem's health status."""
        return self._statuses.get(name)

    @property
    def all_statuses(self) -> Dict[str, HealthStatus]:
        """Get all registered health statuses."""
        return dict(self._statuses)

    def overall(self) -> HealthStatus:
        """
        Compute aggregate health across all subsystems.

        Rules:
        - If any required subsystem is UNHEALTHY → overall UNHEALTHY
        - If any subsystem is DEGRADED → overall DEGRADED
        - Otherwise → HEALTHY
        """
        if not self._statuses:
            return HealthStatus(name="server", status=SubsystemStatus.UNKNOWN)

        has_degraded = False
        for s in self._statuses.values():
            if s.status == SubsystemStatus.UNHEALTHY:
                return HealthStatus(
                    name="server",
                    status=SubsystemStatus.UNHEALTHY,
                    message=f"Subsystem '{s.name}' is unhealthy: {s.message}",
                )
            if s.status == SubsystemStatus.DEGRADED:
                has_degraded = True

        if has_degraded:
            return HealthStatus(
                name="server",
                status=SubsystemStatus.DEGRADED,
                message="One or more subsystems are degraded",
            )

        return HealthStatus(
            name="server",
            status=SubsystemStatus.HEALTHY,
            message=f"All {len(self._statuses)} subsystems healthy",
        )

    def to_dict(self) -> dict:
        """Serialize full health report for /health endpoint."""
        overall = self.overall()
        return {
            "status": overall.status.value,
            "message": overall.message,
            "checked_at": overall.checked_at.isoformat(),
            "subsystems": {
                name: s.to_dict()
                for name, s in sorted(self._statuses.items())
            },
        }

    async def run_checks(self) -> Dict[str, HealthStatus]:
        """Run all registered health checks and update statuses."""
        import asyncio
        import inspect
        import time

        results = {}
        for name, check in self._checks.items():
            start = time.monotonic()
            try:
                if inspect.iscoroutinefunction(check):
                    status = await check()
                else:
                    status = check()
                status.latency_ms = (time.monotonic() - start) * 1000
            except Exception as e:
                status = HealthStatus(
                    name=name,
                    status=SubsystemStatus.UNHEALTHY,
                    message=str(e),
                    latency_ms=(time.monotonic() - start) * 1000,
                )
            self._statuses[name] = status
            results[name] = status

        return results
