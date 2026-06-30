from __future__ import annotations

import time
from typing import Any

from aquilia.controller.base import RequestCtx
from aquilia.middleware import Middleware
from aquilia.request import Request
from aquilia.response import Response
from aquilia.typing.middleware import RequestHandler

from .collector import get_collector
from .config import InspectorConfig
from .redaction import redact_body, redact_body_keys_recursive, redact_headers
from .trace import (
    ExceptionNode,
    RequestTrace,
    ResponseSummary,
    _reset_current_trace,
    _set_current_trace,
)


def _safe_client_addr(request: Request) -> str | None:
    try:
        client = request.client
        if client and hasattr(client, "host"):
            return str(client.host)
        if isinstance(client, (list, tuple)) and len(client) > 0:
            return str(client[0])
        return str(client)
    except Exception:
        return None


def _is_capturable_method(method: str) -> bool:
    return method in ("POST", "PUT", "PATCH", "DELETE", "GET")


async def _safe_body_preview(request: Request, config: InspectorConfig) -> str | None:
    try:
        body_bytes = await request.body()
        if not body_bytes:
            return None
        content_type = request.headers.get("content-type")
        redacted = redact_body(body_bytes, content_type, config)
        if not redacted:
            return None
        if len(redacted) > config.max_body_bytes:
            return redacted[: config.max_body_bytes] + f"...truncated ({len(body_bytes)} bytes total)"
        return redacted
    except Exception:
        return None


def _is_stream_content(content: Any) -> bool:
    return hasattr(content, "__aiter__") or (
        hasattr(content, "__iter__") and not isinstance(content, (bytes, str, dict, list))
    )


def _summarize_response(response: Response, config: InspectorConfig) -> ResponseSummary:
    content_type = response.headers.get("content-type", "")
    preview = None
    size_bytes = 0

    if not _is_stream_content(response._content):
        try:
            body_bytes = response._encode_body(response._content)
            size_bytes = len(body_bytes)
            if config.capture_response_body:
                redacted = redact_body(body_bytes, content_type, config)
                if redacted:
                    if len(redacted) > config.max_body_bytes:
                        preview = redacted[: config.max_body_bytes] + f"...truncated ({size_bytes} bytes total)"
                    else:
                        preview = redacted
        except Exception:
            pass
    else:
        preview = "***STREAMING_RESPONSE***"
        cl = response.headers.get("content-length")
        if cl:
            try:
                size_bytes = int(cl)
            except Exception:
                pass

    return ResponseSummary(
        status=response.status,
        size_bytes=size_bytes,
        content_type=content_type,
        preview=preview,
    )


def _exception_to_node(exc: Exception) -> ExceptionNode:
    import hashlib

    code = getattr(exc, "code", "UNHANDLED_EXCEPTION")
    domain = getattr(exc, "domain", "system")
    domain_str = str(domain)

    # Fetch app/route context
    app = None
    route = None
    if hasattr(exc, "app"):
        app = exc.app
    if hasattr(exc, "route"):
        route = exc.route

    fp_data = f"{code}:{domain_str}:{app or ''}:{route or ''}"
    fingerprint = hashlib.sha256(fp_data.encode()).hexdigest()[:16]

    # Stack trace extraction
    frames = []
    tb = exc.__traceback__
    while tb:
        frame = tb.tb_frame
        code_obj = frame.f_code
        frames.append(
            {
                "filename": code_obj.co_filename,
                "lineno": tb.tb_lineno,
                "name": code_obj.co_name,
            }
        )
        tb = tb.tb_next

    return ExceptionNode(
        exception_type=type(exc).__name__,
        message=str(exc),
        fault_code=code,
        fault_domain=domain_str,
        fingerprint=fingerprint,
        stack_frames=frames,
    )


class InspectorMiddleware(Middleware):
    def __init__(self, config: InspectorConfig):
        self._config = config
        self._collector = get_collector(config)

    async def __call__(self, request: Request, ctx: RequestCtx, next_handler: RequestHandler) -> Response:
        if request.path.startswith("/__aquilia__/") or request.path.startswith("/static/"):
            return await next_handler(request, ctx)

        # Probabilistic sampling
        if self._config.sampling_rate < 1.0:
            import random

            if random.random() > self._config.sampling_rate:
                return await next_handler(request, ctx)

        trace = RequestTrace(
            trace_id=ctx.request_id,
            method=request.method,
            path=request.path,
            route_pattern=request.state.get("route_pattern"),
            started_at=time.time(),
            started_monotonic=time.monotonic(),
            request_headers=redact_headers(dict(request.headers), self._config),
            query_params=redact_body_keys_recursive(
                {k: v for k, v in request.query_params.items()},
                self._config.redact_body_keys,
            ),
            path_params=dict(request.state.get("path_params") or {}),
            app_name=request.state.get("app_name"),
            client_addr=_safe_client_addr(request) if self._config.capture_client_addr else None,
        )

        if self._config.capture_request_body and _is_capturable_method(request.method):
            trace.request_body_preview = await _safe_body_preview(request, self._config)

        # OpenTelemetry correlation
        try:
            from opentelemetry import trace as otel_trace

            current_otel_span = otel_trace.get_current_span()
            if current_otel_span and current_otel_span.get_span_context().is_valid:
                span_context = current_otel_span.get_span_context()
                trace.otel_trace_id = f"{span_context.trace_id:032x}"
                trace.otel_span_id = f"{span_context.span_id:016x}"
        except Exception:
            pass

        token = _set_current_trace(trace)
        try:
            try:
                import sys

                from aquilia import __version__
                from aquilia.inspector.trace import Lane, SpanStatus

                trace.add_span(
                    lane=Lane.VERSIONS,
                    label="Resolve Framework Versions",
                    start_offset_ms=0.0,
                    duration_ms=0.1,
                    status=SpanStatus.OK,
                    detail={
                        "aquilia": __version__,
                        "python": sys.version,
                    },
                )
            except Exception:
                pass

            profile_enabled = False
            try:
                if request.headers.get("x-profile") == "true" or request.query_params.get("profile") == "true":
                    profile_enabled = True
            except Exception:
                pass

            if profile_enabled:
                import cProfile
                import io
                import pstats

                pr = cProfile.Profile()
                pr.enable()
                try:
                    response = await next_handler(request, ctx)
                    trace.status_code = response.status
                    trace.response = _summarize_response(response, self._config)
                    return response
                except Exception as exc:
                    trace.exception = trace.exception or _exception_to_node(exc)
                    raise
                finally:
                    pr.disable()
                    s = io.StringIO()
                    ps = pstats.Stats(pr, stream=s).sort_stats(pstats.SortKey.CUMULATIVE)
                    ps.print_stats(100)
                    trace.profile_stats = s.getvalue()
            else:
                try:
                    response = await next_handler(request, ctx)
                    trace.status_code = response.status
                    trace.response = _summarize_response(response, self._config)
                    return response
                except Exception as exc:
                    trace.exception = trace.exception or _exception_to_node(exc)
                    raise
        finally:
            try:
                from aquilia.inspector.trace import Lane, SpanStatus

                session = request.state.get("session")
                identity = request.state.get("identity")
                if session is not None or identity is not None:
                    detail = {}
                    if session is not None:
                        detail["session_id"] = str(session.id) if hasattr(session, "id") else str(session)
                        detail["session_scope"] = (
                            str(session.scope.value)
                            if hasattr(session, "scope") and hasattr(session.scope, "value")
                            else str(getattr(session, "scope", ""))
                        )
                    if identity is not None:
                        detail["user_id"] = getattr(identity, "id", None)
                        detail["identity_type"] = getattr(identity, "type", None)
                        detail["clearance"] = (
                            identity.get_attribute("clearance") if hasattr(identity, "get_attribute") else None
                        )
                        detail["roles"] = (
                            identity.get_attribute("roles", []) if hasattr(identity, "get_attribute") else []
                        )

                    trace.add_span(
                        lane="auth",
                        label="Authenticate Request",
                        start_offset_ms=0.0,
                        duration_ms=0.1,
                        status=SpanStatus.OK,
                        detail=detail,
                    )
            except Exception:
                pass

            try:
                from aquilia.inspector.trace import SpanStatus

                locale = request.state.get("locale")
                if locale is not None:
                    trace.add_span(
                        lane="i18n",
                        label="Resolve Locale",
                        start_offset_ms=0.0,
                        duration_ms=0.1,
                        status=SpanStatus.OK,
                        detail={"locale": locale},
                    )
            except Exception:
                pass

            trace.finished_monotonic = time.monotonic()
            _reset_current_trace(token)
            self._collector.commit(trace)
            self._collector.publish(trace)
