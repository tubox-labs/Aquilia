"""
aquilia.devplatform.core.state — Immutable telemetry data structures.

RequestRecord and TraceSpan are the primary carriers of per-request
telemetry data produced by the ADP instrumentation layer.

Design constraints:
- Slots used on inner classes for low-overhead allocation on hot paths.
- Records become logically immutable after being committed to the store.
- UUIDs are string-typed (already formatted) to avoid repeated formatting.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TraceSpan:
    """Single timing/operation span within a request trace."""

    span_id: str
    name: str
    lane: str  # matches aquilia.inspector.trace.Lane values
    start_time: float  # monotonic
    end_time: float  # monotonic

    parent_id: str | None = None
    status: str = "ok"  # "ok" | "warning" | "error"
    detail: dict[str, Any] = field(default_factory=dict)
    source: str | None = None  # "file.py:lineno"

    @property
    def duration_ms(self) -> float:
        return (self.end_time - self.start_time) * 1000.0


@dataclass
class SQLRecord:
    """Single SQL query captured during a request."""

    sql: str
    normalized_hash: str
    params: tuple[Any, ...] | list[Any] | None
    duration_ms: float
    explain_plan: str | None = None
    source_span_id: str | None = None


@dataclass
class RequestRecord:
    """Compiled, logically-immutable record of a completed HTTP request.

    Produced by the ADP instrumentation layer after each request completes.
    Committed to RuntimeStateStore.
    """

    trace_id: str
    method: str
    path: str
    status_code: int
    duration_ms: float

    # Headers (pre-redacted sensitive values)
    request_headers: dict[str, str] = field(default_factory=dict)
    response_headers: dict[str, str] = field(default_factory=dict)

    # Params
    query_params: dict[str, list[str]] = field(default_factory=dict)
    path_params: dict[str, Any] = field(default_factory=dict)

    # Body preview (size-capped, sensitive keys redacted)
    request_body_preview: str | None = None

    # Client
    client_addr: str | None = None

    # Timing
    started_at: float = field(default_factory=time.time)  # wall clock for display

    # Telemetry spans
    spans: list[TraceSpan] = field(default_factory=list)

    # SQL
    sql_records: list[SQLRecord] = field(default_factory=list)
    n_plus_one_warnings: list[dict[str, Any]] = field(default_factory=list)

    # Memory (RSS delta, bytes)
    memory_ingress_rss: int = 0
    memory_egress_rss: int = 0

    # Exception
    exception_type: str | None = None
    exception_message: str | None = None
    stack_frames: list[dict[str, Any]] = field(default_factory=list)

    # CPU profiling
    profile_stats: str | None = None

    # Route metadata
    route_pattern: str | None = None
    controller_class: str | None = None
    handler_name: str | None = None

    # Auth
    auth_type: str | None = None
    auth_principal_id: str | None = None

    # App name
    app_name: str | None = None

    @property
    def memory_delta_bytes(self) -> int:
        return self.memory_egress_rss - self.memory_ingress_rss

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "method": self.method,
            "path": self.path,
            "status_code": self.status_code,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at,
            "client_addr": self.client_addr,
            "route_pattern": self.route_pattern,
            "controller_class": self.controller_class,
            "handler_name": self.handler_name,
            "request_headers": self.request_headers,
            "response_headers": self.response_headers,
            "query_params": self.query_params,
            "path_params": self.path_params,
            "request_body_preview": self.request_body_preview,
            "app_name": self.app_name,
            "auth_type": self.auth_type,
            "auth_principal_id": self.auth_principal_id,
            "memory_delta_bytes": self.memory_delta_bytes,
            "n_plus_one_warnings": self.n_plus_one_warnings,
            "spans": [
                {
                    "span_id": s.span_id,
                    "name": s.name,
                    "lane": s.lane,
                    "duration_ms": s.duration_ms,
                    "status": s.status,
                    "detail": s.detail,
                    "parent_id": s.parent_id,
                    "source": s.source,
                }
                for s in self.spans
            ],
            "sql_records": [
                {
                    "sql": r.sql,
                    "duration_ms": r.duration_ms,
                    "explain_plan": r.explain_plan,
                }
                for r in self.sql_records
            ],
            "exception_type": self.exception_type,
            "exception_message": self.exception_message,
            "profile_stats": self.profile_stats,
        }


def new_trace_id() -> str:
    """Generate a fresh trace ID string."""
    return uuid.uuid4().hex
