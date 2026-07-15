"""
aquilia.devplatform.core.protocol — Low-level ASGI connection state machine.

Wraps raw ASGI (scope, receive, send) triples with ADP instrumentation:
- Precise monotonic timing at ingress/egress
- Connection tracking via RuntimeStateStore
- RequestRecord population and commit on completion
- Passes execution to the wrapped Aquilia application unchanged

Design:
  ASGIHTTPConnection  — handles http scope
  ASGIWebSocketConnection — handles websocket scope
  ADPProtocolHandler  — top-level dispatcher (lifespan / http / websocket)
"""

from __future__ import annotations

import time
import traceback
from typing import Any

from aquilia._datastructures import Headers
from aquilia.devplatform.config import AquiliaDevelopmentConfig
from aquilia.devplatform.core.runtime import RuntimeStateStore
from aquilia.devplatform.core.state import RequestRecord, new_trace_id

_REDACTED_HEADER_KEYS = frozenset(
    {"authorization", "cookie", "set-cookie", "x-api-key", "x-auth-token", "x-session-id"}
)

_SENSITIVE_PREFIXES = ("bearer ", "basic ", "token ")

_BODY_PREVIEW_MAX_BYTES = 2048


def _is_client_disconnect(exc: BaseException) -> bool:
    """True for expected client-side disconnects (see h11_transport)."""
    if isinstance(exc, (ConnectionError, BrokenPipeError)):
        return True
    return getattr(exc, "code", None) == "CLIENT_DISCONNECT"


def _redact_headers(raw_headers: list[tuple[bytes, bytes]]) -> dict[str, str]:
    """Convert raw ASGI headers to a dict, redacting sensitive values.

    Uses ``aquilia._datastructures.Headers`` for case-insensitive lookup
    semantics instead of manual ``.lower()`` key comparisons.
    """
    headers = Headers(raw=raw_headers)
    out: dict[str, str] = {}
    for name, value in headers.items():
        key = name.lower()
        out[key] = "***REDACTED***" if key in _REDACTED_HEADER_KEYS else value
    return out


def _parse_query_string(raw: bytes) -> dict[str, list[str]]:
    """Parse a raw ASGI ``query_string`` into a multi-valued dict."""
    from urllib.parse import parse_qs

    text = raw.decode("latin-1", errors="replace")
    if not text:
        return {}
    return parse_qs(text, keep_blank_values=True)


def redact_body_preview(body: bytes, limit: int = _BODY_PREVIEW_MAX_BYTES) -> str | None:
    """
    Return a size-capped, best-effort UTF-8 preview of a request body with
    Bearer/Basic/Token-prefixed values scrubbed.

    Returns ``None`` for an empty body. Truncates at ``limit`` bytes before
    decoding to avoid slicing multi-byte UTF-8 sequences awkwardly (the
    trailing partial character, if any, is simply dropped via ``errors="ignore"``).
    """
    if not body:
        return None
    text = body[:limit].decode("utf-8", errors="ignore")
    lowered = text.lower()
    for prefix in _SENSITIVE_PREFIXES:
        idx = lowered.find(prefix)
        if idx != -1:
            text = text[: idx + len(prefix)] + "***REDACTED***"
            break
    if len(body) > limit:
        text += "…"
    return text


class ASGIHTTPConnection:
    """
    Instruments a single HTTP request-response cycle.

    Wraps the ASGI (scope, receive, send) without altering their semantics.
    Populates a RequestRecord and commits it to RuntimeStateStore on completion.
    """

    __slots__ = (
        "scope",
        "receive",
        "send",
        "_config",
        "_runtime",
        "_trace_id",
        "_ingress_mono",
        "_record",
        "_status_code",
        "_response_headers",
        "_response_body_size",
        "_body_preview_captured",
    )

    def __init__(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
        config: AquiliaDevelopmentConfig,
        runtime: RuntimeStateStore,
    ) -> None:
        self.scope = scope
        self.receive = receive
        self.send = send
        self._config = config
        self._runtime = runtime

        self._trace_id = new_trace_id()
        self._ingress_mono = time.monotonic()
        self._status_code: int = 0
        self._response_headers: dict[str, str] = {}
        self._response_body_size: int = 0
        self._body_preview_captured = False

        # Build initial record
        client = scope.get("client")
        client_addr = f"{client[0]}:{client[1]}" if client else None
        raw_headers: list[tuple[bytes, bytes]] = scope.get("headers", [])
        query_params = _parse_query_string(scope.get("query_string", b""))

        self._record = RequestRecord(
            trace_id=self._trace_id,
            method=scope.get("method", "GET").upper(),
            path=scope.get("path", "/"),
            status_code=0,
            duration_ms=0.0,
            request_headers=_redact_headers(raw_headers),
            query_params=query_params,
            client_addr=client_addr,
        )

    async def _instrumented_receive(self) -> dict[str, Any]:
        """Intercept ASGI receive frames to capture a redacted body preview."""
        message = await self.receive()
        if not self._body_preview_captured and message.get("type") == "http.request":
            body = message.get("body", b"")
            if body:
                self._record.request_body_preview = redact_body_preview(body)
            self._body_preview_captured = True
        return message

    async def _instrumented_send(self, message: dict[str, Any]) -> None:
        """Intercept ASGI send frames to capture status code and body size."""
        msg_type = message.get("type", "")
        if msg_type == "http.response.start":
            self._status_code = message.get("status", 0)
            raw_resp_headers: list[tuple[bytes, bytes]] = message.get("headers", [])
            self._response_headers = _redact_headers(raw_resp_headers)
        elif msg_type == "http.response.body":
            body = message.get("body", b"")
            self._response_body_size += len(body)
        await self.send(message)

    async def execute(self, app: Any) -> None:
        """
        Run the Aquilia app for this connection, then commit telemetry.

        Wraps execution in a cProfile session when profiling is requested
        (config.profiler_enabled globally, or an X-Aquilia-Profile request
        header per-request) — see aquilia.devplatform.profiler.engine.
        """
        self._runtime.connection_opened()
        exc_type = exc_message = None
        stack_frames: list[dict[str, Any]] = []

        profiler = self._make_profiler_if_requested()

        try:
            if profiler is not None:
                profiler.start()
            await app(self.scope, self._instrumented_receive, self._instrumented_send)
        except Exception as exc:
            exc_type = type(exc).__name__
            exc_message = str(exc)
            stack_frames = [
                {
                    "filename": frame.filename,
                    "lineno": frame.lineno,
                    "name": frame.name,
                    "line": frame.line,
                }
                for frame in traceback.extract_tb(exc.__traceback__)
            ]
            # A client disconnect is not an application failure — don't
            # synthesize a 500 (which would elevate the request line to ERROR).
            if self._status_code == 0 and not _is_client_disconnect(exc):
                self._status_code = 500
            raise
        finally:
            egress_mono = time.monotonic()
            duration_ms = (egress_mono - self._ingress_mono) * 1000.0

            self._record.status_code = self._status_code or 0
            self._record.duration_ms = duration_ms
            self._record.response_headers = self._response_headers
            self._record.exception_type = exc_type
            self._record.exception_message = exc_message
            self._record.stack_frames = stack_frames
            if profiler is not None:
                self._record.profile_stats = profiler.stop()

            self._analyze_sql()

            self._runtime.record_request(self._record)
            self._runtime.connection_closed()
            self._emit_inspector_event()

    def _emit_inspector_event(self) -> None:
        """Surface this completed request as a structured Inspector event.

        Routed through the ADP log router's ring buffer (never straight to
        stdout), so it shows up in the Inspector console and access history
        without polluting the dashboard. Best-effort: failures are swallowed.
        """
        try:
            import logging

            from aquilia.devplatform.logging import get_router

            rec = self._record
            level = (
                logging.ERROR
                if rec.status_code >= 500
                else (logging.WARNING if rec.status_code >= 400 else logging.INFO)
            )
            detail = f"{rec.method} {rec.path} {rec.status_code} {rec.duration_ms:.1f}ms"
            if rec.exception_type:
                detail += f" [{rec.exception_type}]"
            get_router().log_event(
                detail,
                level=level,
                kind="request",
                logger_name="aquilia.devplatform.request",
                meta={
                    "method": rec.method,
                    "path": rec.path,
                    "status": rec.status_code,
                    "duration_ms": rec.duration_ms,
                    "exception_type": rec.exception_type,
                },
            )
        except Exception:
            pass

    def _analyze_sql(self) -> None:
        """
        Feed this request's completed ``Lane.DATABASE`` spans into
        ``SQLQueryAnalyzer`` for N+1/duplicate-query detection.

        Reads spans off the current Inspector trace — populated by
        ``aquilia.db.engine.AquiliaDatabase._notify_inspector()`` — rather
        than importing ``aquilia.db`` directly, keeping devplatform an
        observer of core, never a dependency of it.
        """
        if not self._config.n_plus_one_detection:
            return
        try:
            from aquilia.devplatform.diagnostics.sql import RequestSQLAccumulator, SQLQueryAnalyzer
            from aquilia.inspector.trace import Lane, current_trace

            trace = current_trace()
            if trace is None:
                return

            accumulator = RequestSQLAccumulator()
            analyzer = SQLQueryAnalyzer.get_instance()
            for span in trace.spans:
                if span.lane != Lane.DATABASE:
                    continue
                params = span.detail.get("params") if span.detail else None
                accumulator.record(span.label, params, span.duration_ms)
                analyzer.on_query(span.label, params, span.duration_ms)

            n1_warnings, dup_warnings = accumulator.analyze()
            self._record.n_plus_one_warnings = [w.to_dict() for w in n1_warnings] + [w.to_dict() for w in dup_warnings]
        except ImportError:
            pass
        except Exception as exc:
            from aquilia.devplatform.faults import InspectorFault, report_fault

            report_fault(InspectorFault(f"SQL analysis failed: {exc}"), app=self._runtime.app)

    def _make_profiler_if_requested(self) -> Any:
        """Return a cProfilingRunner if this request should be profiled, else None."""
        if not self._config.profiler_enabled:
            request_headers = self._record.request_headers
            if request_headers.get("x-aquilia-profile", "").lower() not in ("true", "1", "yes"):
                return None
        try:
            from aquilia.devplatform.profiler.engine import cProfilingRunner

            return cProfilingRunner()
        except ImportError:
            return None

    @property
    def record(self) -> RequestRecord:
        return self._record

    @property
    def trace_id(self) -> str:
        return self._trace_id


class ASGIWebSocketConnection:
    """
    Tracks WebSocket connection lifecycle and frame counts.
    """

    __slots__ = ("scope", "receive", "send", "_runtime", "_in_frames", "_out_frames")

    def __init__(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
        runtime: RuntimeStateStore,
    ) -> None:
        self.scope = scope
        self.receive = receive
        self.send = send
        self._runtime = runtime
        self._in_frames: int = 0
        self._out_frames: int = 0

    async def _instrumented_receive(self) -> dict[str, Any]:
        msg = await self.receive()
        if msg.get("type") in ("websocket.receive", "websocket.disconnect"):
            self._in_frames += 1
        return msg

    async def _instrumented_send(self, message: dict[str, Any]) -> None:
        self._out_frames += 1
        await self.send(message)

    async def execute(self, app: Any) -> None:
        self._runtime.websocket_opened()
        try:
            await app(self.scope, self._instrumented_receive, self._instrumented_send)
        finally:
            self._runtime.websocket_closed()


class ADPProtocolHandler:
    """
    Top-level ASGI callable. Dispatches lifespan / http / websocket to
    the correct instrumented wrapper before handing off to the Aquilia app.
    """

    def __init__(
        self,
        app: Any,
        config: AquiliaDevelopmentConfig,
        runtime: RuntimeStateStore,
    ) -> None:
        self._app = app
        self._config = config
        self._runtime = runtime

    async def __call__(
        self,
        scope: dict[str, Any],
        receive: Any,
        send: Any,
    ) -> None:
        scope_type = scope.get("type", "")

        if scope_type == "http":
            conn = ASGIHTTPConnection(scope, receive, send, self._config, self._runtime)
            await conn.execute(self._app)

        elif scope_type == "websocket":
            ws_conn = ASGIWebSocketConnection(scope, receive, send, self._runtime)
            await ws_conn.execute(self._app)

        else:
            # lifespan or unknown — pass through directly
            await self._app(scope, receive, send)
