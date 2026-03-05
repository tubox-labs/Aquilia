"""
AquilAdmin — Error Tracker.

Built-in error monitoring system that hooks into AquilaFaults to provide:
- Error history with full stack traces
- Error grouping by fingerprint
- Error frequency & trend analysis
- Per-route / per-app error breakdown
- Admin panel integration

Integrates with FaultEngine via on_fault() listener.
"""

from __future__ import annotations

import traceback as tb_mod
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ErrorRecord:
    """Captured error with full context."""

    id: str = ""
    code: str = ""          # Fault code
    message: str = ""
    domain: str = ""        # Fault domain (MODEL, FLOW, SECURITY, etc.)
    severity: str = "ERROR"
    trace_id: str = ""
    fingerprint: str = ""

    # Context
    app: str = ""
    route: str = ""
    request_id: str = ""

    # Stack trace
    exception_type: str = ""
    exception_message: str = ""
    stack_trace: str = ""
    stack_frames: List[Dict[str, Any]] = field(default_factory=list)

    # Timing
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "message": self.message,
            "domain": self.domain,
            "severity": self.severity,
            "trace_id": self.trace_id,
            "fingerprint": self.fingerprint,
            "app": self.app,
            "route": self.route,
            "request_id": self.request_id,
            "exception_type": self.exception_type,
            "exception_message": self.exception_message,
            "stack_trace": self.stack_trace,
            "stack_frames": self.stack_frames,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ErrorGroup:
    """Aggregated error group (same fingerprint)."""

    fingerprint: str = ""
    code: str = ""
    message: str = ""
    domain: str = ""
    count: int = 0
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    occurrences: List[str] = field(default_factory=list)  # List of error IDs
    routes: set = field(default_factory=set)
    apps: set = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fingerprint": self.fingerprint,
            "code": self.code,
            "message": self.message,
            "domain": self.domain,
            "count": self.count,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "occurrences": len(self.occurrences),
            "routes": sorted(self.routes),
            "apps": sorted(self.apps),
        }


class ErrorTracker:
    """
    Central error tracking system.

    Captures errors from FaultEngine and provides:
    - Error history with full stack traces
    - Error grouping and deduplication
    - Frequency analysis
    - Admin dashboard integration

    Usage::

        tracker = ErrorTracker()

        # Hook into FaultEngine
        fault_engine.on_fault(tracker.capture)

        # Or manually record
        tracker.record_error(
            code="VALIDATION_ERROR",
            message="Field 'email' is required",
            domain="MODEL",
            ...
        )

        # Query
        stats = tracker.get_stats()
        errors = tracker.get_recent_errors(limit=50)
    """

    def __init__(
        self,
        *,
        max_errors: int = 1000,
        max_groups: int = 200,
    ):
        self._errors: deque[ErrorRecord] = deque(maxlen=max_errors)
        self._groups: Dict[str, ErrorGroup] = {}
        self._max_groups = max_groups
        self._counter = 0

        # Aggregate counters
        self._total_errors = 0
        self._by_domain: Dict[str, int] = defaultdict(int)
        self._by_severity: Dict[str, int] = defaultdict(int)
        self._by_route: Dict[str, int] = defaultdict(int)
        self._by_code: Dict[str, int] = defaultdict(int)
        self._started_at = datetime.now(timezone.utc)

        # Hourly distribution (last 24 hours)
        self._hourly: Dict[str, int] = defaultdict(int)

        # ── Enhanced analytics (Phase 30) ────────────────────────────
        # 5-minute bucketed trend for high-resolution charts
        self._five_min: Dict[str, int] = defaultdict(int)
        # Per-domain hourly breakdown for stacked area charts
        self._domain_hourly: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        # Severity over time (hourly)
        self._severity_hourly: Dict[str, Dict[str, int]] = defaultdict(
            lambda: defaultdict(int)
        )
        # Resolution tracking
        self._resolved: Dict[str, datetime] = {}  # fingerprint -> resolved_at
        self._total_resolved = 0

    def capture(self, fault_context) -> None:
        """
        FaultEngine listener callback.

        Automatically called by FaultEngine.on_fault() when a fault occurs.
        Extracts all relevant data from the FaultContext.

        Args:
            fault_context: FaultContext from the fault engine
        """
        self._counter += 1

        # Extract stack trace
        stack_trace = ""
        stack_frames: List[Dict[str, Any]] = []
        if hasattr(fault_context, "stack") and fault_context.stack:
            for frame in fault_context.stack:
                frame_dict = {
                    "filename": getattr(frame, "filename", str(frame)),
                    "lineno": getattr(frame, "lineno", 0),
                    "name": getattr(frame, "name", ""),
                    "line": getattr(frame, "line", ""),
                }
                stack_frames.append(frame_dict)
            try:
                stack_trace = "".join(
                    tb_mod.format_list(fault_context.stack)
                )
            except Exception:
                stack_trace = str(fault_context.stack)

        # Extract cause info
        exception_type = ""
        exception_message = ""
        if hasattr(fault_context, "cause") and fault_context.cause:
            exception_type = type(fault_context.cause).__name__
            exception_message = str(fault_context.cause)

        fault = fault_context.fault
        record = ErrorRecord(
            id=f"err-{self._counter:06d}",
            code=getattr(fault, "code", "UNKNOWN"),
            message=getattr(fault, "message", str(fault)),
            domain=getattr(fault.domain, "value", str(getattr(fault, "domain", "UNKNOWN"))) if hasattr(fault, "domain") else "UNKNOWN",
            severity=getattr(fault.severity, "value", str(getattr(fault, "severity", "ERROR"))) if hasattr(fault, "severity") else "ERROR",
            trace_id=getattr(fault_context, "trace_id", ""),
            fingerprint=fault_context.fingerprint() if hasattr(fault_context, "fingerprint") else "",
            app=getattr(fault_context, "app", "") or "",
            route=getattr(fault_context, "route", "") or "",
            request_id=getattr(fault_context, "request_id", "") or "",
            exception_type=exception_type,
            exception_message=exception_message,
            stack_trace=stack_trace,
            stack_frames=stack_frames,
            timestamp=getattr(fault_context, "timestamp", datetime.now(timezone.utc)),
            metadata=getattr(fault_context, "metadata", {}),
        )

        self._record(record)

    def record_error(
        self,
        *,
        code: str = "UNKNOWN",
        message: str = "",
        domain: str = "SYSTEM",
        severity: str = "ERROR",
        app: str = "",
        route: str = "",
        request_id: str = "",
        exception_type: str = "",
        exception_message: str = "",
        stack_trace: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ErrorRecord:
        """
        Manually record an error.

        Args:
            code: Error code
            message: Human-readable message
            domain: Fault domain
            severity: Severity level
            app: App name
            route: Route pattern
            request_id: Request ID
            exception_type: Exception class name
            exception_message: Exception message
            stack_trace: Full stack trace string
            metadata: Extra metadata

        Returns:
            The created ErrorRecord
        """
        self._counter += 1
        import hashlib as _hashlib
        fp_data = f"{code}:{domain}:{app}:{route}"
        fingerprint = _hashlib.sha256(fp_data.encode()).hexdigest()[:16]

        record = ErrorRecord(
            id=f"err-{self._counter:06d}",
            code=code,
            message=message,
            domain=domain,
            severity=severity,
            fingerprint=fingerprint,
            app=app,
            route=route,
            request_id=request_id,
            exception_type=exception_type,
            exception_message=exception_message,
            stack_trace=stack_trace,
            metadata=metadata or {},
        )

        self._record(record)
        return record

    def _record(self, record: ErrorRecord) -> None:
        """Internal: store error and update aggregates."""
        self._errors.append(record)
        self._total_errors += 1
        self._by_domain[record.domain] += 1
        self._by_severity[record.severity] += 1
        if record.route:
            self._by_route[record.route] += 1
        self._by_code[record.code] += 1

        # Hourly distribution
        hour_key = record.timestamp.strftime("%Y-%m-%d %H:00")
        self._hourly[hour_key] += 1

        # ── Enhanced analytics (Phase 30) ────────────────────────────
        # 5-minute bucket
        minute = (record.timestamp.minute // 5) * 5
        five_min_key = record.timestamp.strftime(f"%Y-%m-%d %H:{minute:02d}")
        self._five_min[five_min_key] += 1

        # Per-domain hourly
        self._domain_hourly[record.domain][hour_key] += 1

        # Per-severity hourly
        self._severity_hourly[record.severity][hour_key] += 1

        # Update group
        fp = record.fingerprint
        if fp:
            if fp not in self._groups:
                if len(self._groups) >= self._max_groups:
                    # Evict oldest group
                    oldest_key = min(self._groups, key=lambda k: self._groups[k].last_seen or datetime.min.replace(tzinfo=timezone.utc))
                    del self._groups[oldest_key]
                self._groups[fp] = ErrorGroup(
                    fingerprint=fp,
                    code=record.code,
                    message=record.message,
                    domain=record.domain,
                    first_seen=record.timestamp,
                )
            group = self._groups[fp]
            group.count += 1
            group.last_seen = record.timestamp
            group.occurrences.append(record.id)
            if record.route:
                group.routes.add(record.route)
            if record.app:
                group.apps.add(record.app)

    # ========================================================================
    # Query API
    # ========================================================================

    def get_recent_errors(self, limit: int = 50) -> List[ErrorRecord]:
        """Get most recent errors."""
        errors = list(self._errors)
        return errors[-limit:]

    def get_error(self, error_id: str) -> Optional[ErrorRecord]:
        """Get a specific error by ID."""
        for err in self._errors:
            if err.id == error_id:
                return err
        return None

    def get_groups(self, limit: int = 50) -> List[ErrorGroup]:
        """Get error groups sorted by count descending."""
        groups = sorted(self._groups.values(), key=lambda g: g.count, reverse=True)
        return groups[:limit]

    def get_errors_by_route(self, route: str, limit: int = 50) -> List[ErrorRecord]:
        """Get errors for a specific route."""
        return [e for e in list(self._errors) if e.route == route][-limit:]

    def get_errors_by_domain(self, domain: str, limit: int = 50) -> List[ErrorRecord]:
        """Get errors for a specific domain."""
        return [e for e in list(self._errors) if e.domain == domain][-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive error statistics with chart-ready data."""
        errors = list(self._errors)
        groups = self.get_groups(20)

        from datetime import timedelta

        # Recent errors (last hour)
        now = datetime.now(timezone.utc)
        errors_last_hour = sum(
            1 for e in errors
            if (now - e.timestamp).total_seconds() < 3600
        )
        errors_last_24h = sum(
            1 for e in errors
            if (now - e.timestamp).total_seconds() < 86400
        )

        # Error rate
        elapsed = (now - self._started_at).total_seconds() or 1
        error_rate = self._total_errors / elapsed

        # Top routes
        top_routes = sorted(
            self._by_route.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # Top error codes
        top_codes = sorted(
            self._by_code.items(), key=lambda x: x[1], reverse=True
        )[:10]

        # ── Chart data: Hourly trend (last 24h) ─────────────────────
        hourly_trend = []
        hourly_labels = []
        hourly_values = []
        for i in range(24):
            hour = (now - timedelta(hours=23 - i)).strftime("%Y-%m-%d %H:00")
            count = self._hourly.get(hour, 0)
            hourly_trend.append({"hour": hour, "count": count})
            hourly_labels.append(hour[-5:])  # "HH:00"
            hourly_values.append(count)

        # ── Chart data: 5-min trend (last 2 hours, 24 buckets) ──────
        five_min_labels = []
        five_min_values = []
        for i in range(24):
            t = now - timedelta(minutes=(23 - i) * 5)
            minute = (t.minute // 5) * 5
            key = t.strftime(f"%Y-%m-%d %H:{minute:02d}")
            five_min_labels.append(t.strftime("%H:%M"))
            five_min_values.append(self._five_min.get(key, 0))

        # ── Chart data: Severity doughnut ────────────────────────────
        severity_labels = list(self._by_severity.keys()) if self._by_severity else ["No Data"]
        severity_values = list(self._by_severity.values()) if self._by_severity else [0]

        # ── Chart data: Domain polar area ────────────────────────────
        domain_labels = list(self._by_domain.keys()) if self._by_domain else ["No Data"]
        domain_values = list(self._by_domain.values()) if self._by_domain else [0]

        # ── Chart data: Top error codes horizontal bar ───────────────
        top_codes_labels = [c["code"] for c in [{"code": c, "count": n} for c, n in top_codes]][:8]
        top_codes_values = [c["count"] for c in [{"code": c, "count": n} for c, n in top_codes]][:8]

        # ── Chart data: Domain stacked area (hourly, last 24h) ──────
        domain_series = {}
        all_domains = sorted(self._domain_hourly.keys())
        for domain in all_domains[:6]:  # Max 6 domains for readability
            series = []
            for i in range(24):
                hour = (now - timedelta(hours=23 - i)).strftime("%Y-%m-%d %H:00")
                series.append(self._domain_hourly[domain].get(hour, 0))
            domain_series[domain] = series

        # ── Chart data: Severity timeline (hourly stacked) ──────────
        severity_series = {}
        all_severities = sorted(self._severity_hourly.keys())
        for sev in all_severities:
            series = []
            for i in range(24):
                hour = (now - timedelta(hours=23 - i)).strftime("%Y-%m-%d %H:00")
                series.append(self._severity_hourly[sev].get(hour, 0))
            severity_series[sev] = series

        # ── Resolution stats ────────────────────────────────────────
        unresolved_count = sum(
            1 for g in self._groups.values()
            if g.fingerprint not in self._resolved
        )

        # ── MTTR (Mean Time To Resolve) ─────────────────────────────
        mttr_ms = 0.0
        resolved_with_time = []
        for fp, resolved_at in self._resolved.items():
            group = self._groups.get(fp)
            if group and group.first_seen:
                delta = (resolved_at - group.first_seen).total_seconds()
                resolved_with_time.append(delta)
        if resolved_with_time:
            mttr_ms = sum(resolved_with_time) / len(resolved_with_time)

        # ── Error velocity (errors per 5 min, last 30 min) ──────────
        velocity_points = []
        for i in range(6):
            t = now - timedelta(minutes=(5 - i) * 5)
            minute = (t.minute // 5) * 5
            key = t.strftime(f"%Y-%m-%d %H:{minute:02d}")
            velocity_points.append(self._five_min.get(key, 0))

        return {
            "total_errors": self._total_errors,
            "errors_last_hour": errors_last_hour,
            "errors_last_24h": errors_last_24h,
            "error_rate_per_min": round(error_rate * 60, 2),
            "unique_errors": len(self._groups),
            "unresolved_count": unresolved_count,
            "resolved_count": self._total_resolved,
            "mttr_seconds": round(mttr_ms, 1),
            "by_domain": dict(self._by_domain),
            "by_severity": dict(self._by_severity),
            "top_routes": [{"route": r, "count": c} for r, c in top_routes],
            "top_codes": [{"code": c, "count": n} for c, n in top_codes],
            "recent_errors": [e.to_dict() for e in self.get_recent_errors(30)],
            "error_groups": [g.to_dict() for g in groups],
            "hourly_trend": hourly_trend,
            # ── Chart.js ready data ─────────────────────────────────
            "charts": {
                "hourly": {
                    "labels": hourly_labels,
                    "values": hourly_values,
                },
                "five_min": {
                    "labels": five_min_labels,
                    "values": five_min_values,
                },
                "severity_doughnut": {
                    "labels": severity_labels,
                    "values": severity_values,
                },
                "domain_polar": {
                    "labels": domain_labels,
                    "values": domain_values,
                },
                "top_codes_bar": {
                    "labels": top_codes_labels,
                    "values": top_codes_values,
                },
                "domain_stacked": {
                    "labels": hourly_labels,
                    "series": domain_series,
                },
                "severity_timeline": {
                    "labels": hourly_labels,
                    "series": severity_series,
                },
                "velocity": velocity_points,
            },
        }

    def resolve_error(self, fingerprint: str) -> bool:
        """Mark an error group as resolved."""
        if fingerprint in self._groups and fingerprint not in self._resolved:
            self._resolved[fingerprint] = datetime.now(timezone.utc)
            self._total_resolved += 1
            return True
        return False

    def clear(self) -> None:
        """Clear all tracked errors."""
        self._errors.clear()
        self._groups.clear()
        self._total_errors = 0
        self._by_domain.clear()
        self._by_severity.clear()
        self._by_route.clear()
        self._by_code.clear()
        self._hourly.clear()
        self._five_min.clear()
        self._domain_hourly.clear()
        self._severity_hourly.clear()
        self._resolved.clear()
        self._total_resolved = 0
        self._counter = 0


# ============================================================================
# Global instance
# ============================================================================

_default_tracker: Optional[ErrorTracker] = None


def get_error_tracker() -> ErrorTracker:
    """Get or create the global ErrorTracker instance."""
    global _default_tracker
    if _default_tracker is None:
        _default_tracker = ErrorTracker()
    return _default_tracker
