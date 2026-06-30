from __future__ import annotations

import json
import sqlite3
from abc import ABC, abstractmethod
from collections import deque
from typing import Any

from .config import InspectorConfig
from .trace import ExceptionNode, RequestTrace, ResponseSummary, Span


class TraceStore(ABC):
    """Abstract interface for storing and retrieving RequestTraces."""

    @abstractmethod
    def save(self, trace: RequestTrace) -> None:
        """Persist a trace in the store."""
        pass

    @abstractmethod
    def get(self, trace_id: str) -> RequestTrace | None:
        """Retrieve a specific trace by ID."""
        pass

    @abstractmethod
    def list_recent(self, limit: int = 100) -> list[RequestTrace]:
        """List the most recent traces, newest first."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Clear all traces from the store."""
        pass


class MemoryTraceStore(TraceStore):
    """In-memory ring-buffer trace store."""

    def __init__(self, config: InspectorConfig):
        self._max_traces = config.max_traces
        self._traces: deque[RequestTrace] = deque(maxlen=self._max_traces)
        self._by_id: dict[str, RequestTrace] = {}

    def save(self, trace: RequestTrace) -> None:
        if len(self._traces) == self._traces.maxlen:
            evicted = self._traces[0]
            self._by_id.pop(evicted.trace_id, None)
        self._traces.append(trace)
        self._by_id[trace.trace_id] = trace

    def get(self, trace_id: str) -> RequestTrace | None:
        return self._by_id.get(trace_id)

    def list_recent(self, limit: int = 100) -> list[RequestTrace]:
        recent = list(self._traces)
        recent.reverse()
        return recent[:limit]

    def clear(self) -> None:
        self._traces.clear()
        self._by_id.clear()


class SQLiteTraceStore(TraceStore):
    """SQLite-backed trace store for persistent tracing."""

    def __init__(self, config: InspectorConfig):
        self._db_path = config.store_path
        self._max_traces = config.max_traces
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    CREATE TABLE IF NOT EXISTS traces (
                        trace_id TEXT PRIMARY KEY,
                        timestamp REAL,
                        data TEXT
                    )
                    """
                )
                conn.commit()
        finally:
            conn.close()

    def save(self, trace: RequestTrace) -> None:
        serialized = json.dumps(trace.to_dict())
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    "INSERT OR REPLACE INTO traces (trace_id, timestamp, data) VALUES (?, ?, ?)",
                    (trace.trace_id, trace.started_at, serialized),
                )
                # Enforce capacity limit
                conn.execute(
                    """
                    DELETE FROM traces WHERE trace_id NOT IN (
                        SELECT trace_id FROM traces ORDER BY timestamp DESC LIMIT ?
                    )
                    """,
                    (self._max_traces,),
                )
                conn.commit()
        finally:
            conn.close()

    def get(self, trace_id: str) -> RequestTrace | None:
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute("SELECT data FROM traces WHERE trace_id = ?", (trace_id,))
                row = cursor.fetchone()
                if row is None:
                    return None
                return self._reconstruct_trace(json.loads(row["data"]))
        finally:
            conn.close()

    def list_recent(self, limit: int = 100) -> list[RequestTrace]:
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute("SELECT data FROM traces ORDER BY timestamp DESC LIMIT ?", (limit,))
                rows = cursor.fetchall()
                return [self._reconstruct_trace(json.loads(row["data"])) for row in rows]
        finally:
            conn.close()

    def clear(self) -> None:
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("DELETE FROM traces")
                conn.commit()
        finally:
            conn.close()

    def _reconstruct_trace(self, data: dict[str, Any]) -> RequestTrace:
        spans_data = data.get("spans", [])
        spans = []
        for s in spans_data:
            spans.append(
                Span(
                    id=s.get("id"),
                    lane=s.get("lane"),
                    label=s.get("label"),
                    start_offset_ms=s.get("start_offset_ms"),
                    duration_ms=s.get("duration_ms"),
                    status=s.get("status"),
                    detail=s.get("detail"),
                    parent_id=s.get("parent_id"),
                    source=s.get("source"),
                )
            )

        exc_data = data.get("exception")
        exception = None
        if exc_data:
            exception = ExceptionNode(
                exception_type=exc_data.get("exception_type"),
                message=exc_data.get("message"),
                fault_code=exc_data.get("fault_code"),
                fault_domain=exc_data.get("fault_domain"),
                fingerprint=exc_data.get("fingerprint"),
                stack_frames=exc_data.get("stack_frames"),
            )

        resp_data = data.get("response")
        response = None
        if resp_data:
            response = ResponseSummary(
                status=resp_data.get("status"),
                size_bytes=resp_data.get("size_bytes"),
                content_type=resp_data.get("content_type"),
                preview=resp_data.get("preview"),
            )

        return RequestTrace(
            trace_id=data.get("trace_id"),
            method=data.get("method"),
            path=data.get("path"),
            route_pattern=data.get("route_pattern"),
            started_at=data.get("started_at", 0.0),
            started_monotonic=data.get("started_monotonic", 0.0),
            finished_monotonic=data.get("finished_monotonic"),
            status_code=data.get("status_code"),
            request_headers=data.get("request_headers", {}),
            request_body_preview=data.get("request_body_preview"),
            query_params=data.get("query_params", {}),
            path_params=data.get("path_params", {}),
            client_addr=data.get("client_addr"),
            spans=spans,
            exception=exception,
            response=response,
            app_name=data.get("app_name"),
            n_plus_one=data.get("n_plus_one", []),
            profile_stats=data.get("profile_stats"),
            otel_trace_id=data.get("otel_trace_id"),
            otel_span_id=data.get("otel_span_id"),
        )
