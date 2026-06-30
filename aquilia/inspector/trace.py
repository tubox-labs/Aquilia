from __future__ import annotations

import time
from contextvars import ContextVar, Token
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Lane(str, Enum):
    PARSE = "parse"
    ROUTE = "route"
    MIDDLEWARE = "middleware"
    DEPENDENCY = "dependency"
    VALIDATION = "validation"
    DATABASE = "database"
    EXTERNAL_HTTP = "external_http"
    EFFECT = "effect"
    HANDLER = "handler"
    SERIALIZE = "serialize"
    EXCEPTION = "exception"


class SpanStatus(str, Enum):
    OK = "ok"
    WARNING = "warning"
    ERROR = "error"


@dataclass(slots=True)
class Span:
    id: str
    lane: Lane | str
    label: str
    start_offset_ms: float
    duration_ms: float
    status: SpanStatus = SpanStatus.OK
    detail: dict[str, Any] = field(default_factory=dict)
    parent_id: str | None = None
    source: str | None = None  # "file.py:123"


@dataclass(slots=True)
class ExceptionNode:
    exception_type: str
    message: str
    fault_code: str | None
    fault_domain: str | None
    fingerprint: str | None  # cross-links aquilia.admin.error_tracker.ErrorRecord.fingerprint
    stack_frames: list[dict[str, Any]]


@dataclass(slots=True)
class ResponseSummary:
    status: int
    size_bytes: int
    content_type: str
    preview: str | None  # redacted, truncated to config.max_body_bytes


@dataclass(slots=True)
class RequestTrace:
    trace_id: str
    method: str
    path: str
    route_pattern: str | None
    started_at: float  # time.time() wall clock, for display
    started_monotonic: float  # time.monotonic(), for duration math
    finished_monotonic: float | None = None
    status_code: int | None = None
    request_headers: dict[str, str] = field(default_factory=dict)  # pre-redacted
    request_body_preview: str | None = None  # pre-redacted, size-capped
    query_params: dict[str, list[str]] = field(default_factory=dict)
    path_params: dict[str, Any] = field(default_factory=dict)
    client_addr: str | None = None
    spans: list[Span] = field(default_factory=list)
    exception: ExceptionNode | None = None
    response: ResponseSummary | None = None
    app_name: str | None = None
    n_plus_one: list[Any] = field(default_factory=list)

    @property
    def duration_ms(self) -> float:
        end = self.finished_monotonic or time.monotonic()
        return (end - self.started_monotonic) * 1000.0

    def add_span(self, lane: Lane | str, label: str, start_offset_ms: float, duration_ms: float, **kw: Any) -> Span:
        span = Span(
            id=f"{self.trace_id}-{len(self.spans):04d}",
            lane=lane,
            label=label,
            start_offset_ms=start_offset_ms,
            duration_ms=duration_ms,
            **kw,
        )
        self.spans.append(span)
        return span

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "method": self.method,
            "path": self.path,
            "route_pattern": self.route_pattern,
            "started_at": self.started_at,
            "duration_ms": self.duration_ms,
            "status_code": self.status_code,
            "request_headers": self.request_headers,
            "request_body_preview": self.request_body_preview,
            "query_params": self.query_params,
            "path_params": self.path_params,
            "client_addr": self.client_addr,
            "spans": [
                {
                    "id": s.id,
                    "lane": s.lane.value if isinstance(s.lane, Lane) else s.lane,
                    "label": s.label,
                    "start_offset_ms": s.start_offset_ms,
                    "duration_ms": s.duration_ms,
                    "status": s.status.value,
                    "detail": s.detail,
                    "parent_id": s.parent_id,
                    "source": s.source,
                }
                for s in self.spans
            ],
            "exception": {
                "exception_type": self.exception.exception_type,
                "message": self.exception.message,
                "fault_code": self.exception.fault_code,
                "fault_domain": self.exception.fault_domain,
                "fingerprint": self.exception.fingerprint,
                "stack_frames": self.exception.stack_frames,
            }
            if self.exception
            else None,
            "response": {
                "status": self.response.status,
                "size_bytes": self.response.size_bytes,
                "content_type": self.response.content_type,
                "preview": self.response.preview,
            }
            if self.response
            else None,
            "app_name": self.app_name,
            "n_plus_one": [d.to_dict() if hasattr(d, "to_dict") else d for d in self.n_plus_one],
        }


_CURRENT_TRACE: ContextVar[RequestTrace | None] = ContextVar("aquilia_inspector_trace", default=None)


def _set_current_trace(trace: RequestTrace) -> Token[RequestTrace | None]:
    return _CURRENT_TRACE.set(trace)


def _reset_current_trace(token: Token[RequestTrace | None]) -> None:
    _CURRENT_TRACE.reset(token)


def current_trace() -> RequestTrace | None:
    """Public accessor — safe to call from anywhere (DI listeners, DB engine, HTTP client)."""
    return _CURRENT_TRACE.get()


def current_trace_id() -> str | None:
    t = _CURRENT_TRACE.get()
    return t.trace_id if t else None
