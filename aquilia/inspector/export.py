import json
import time

from .faults import InspectorExportFault
from .trace import ExceptionNode, RequestTrace, ResponseSummary, Span, SpanStatus


def export_trace_json(trace: RequestTrace) -> str:
    try:
        return json.dumps(trace.to_dict(), indent=2)
    except Exception as e:
        raise InspectorExportFault(
            code="EXPORT_SERIALIZATION_FAILED",
            message=f"Failed to serialize trace to JSON: {e}",
        )


def import_trace_json(json_str: str) -> RequestTrace:
    try:
        data = json.loads(json_str)
    except Exception as e:
        raise InspectorExportFault(
            code="IMPORT_PARSE_FAILED",
            message=f"Failed to parse trace JSON: {e}",
        )

    # Basic validations
    if "trace_id" not in data or not data["trace_id"]:
        raise InspectorExportFault(
            code="IMPORT_INVALID_TRACE",
            message="Imported trace is missing trace_id.",
        )

    # Reconstruct ExceptionNode
    exc_data = data.get("exception")
    exception_node = None
    if exc_data:
        exception_node = ExceptionNode(
            exception_type=exc_data["exception_type"],
            message=exc_data["message"],
            fault_code=exc_data["fault_code"],
            fault_domain=exc_data["fault_domain"],
            fingerprint=exc_data["fingerprint"],
            stack_frames=exc_data["stack_frames"],
        )

    # Reconstruct ResponseSummary
    resp_data = data.get("response")
    response_summary = None
    if resp_data:
        response_summary = ResponseSummary(
            status=resp_data["status"],
            size_bytes=resp_data["size_bytes"],
            content_type=resp_data["content_type"],
            preview=resp_data["preview"],
        )

    # Reconstruct Spans
    spans = []
    for s in data.get("spans", []):
        spans.append(
            Span(
                id=s["id"],
                lane=s["lane"],
                label=s["label"],
                start_offset_ms=s["start_offset_ms"],
                duration_ms=s["duration_ms"],
                status=SpanStatus(s["status"]),
                detail=s.get("detail", {}),
                parent_id=s.get("parent_id"),
                source=s.get("source"),
            )
        )

    trace = RequestTrace(
        trace_id=data["trace_id"],
        method=data["method"],
        path=data["path"],
        route_pattern=data.get("route_pattern"),
        started_at=data["started_at"],
        started_monotonic=time.monotonic() - (data.get("duration_ms", 0.0) / 1000.0),
        finished_monotonic=time.monotonic(),
        status_code=data.get("status_code"),
        request_headers=data.get("request_headers", {}),
        request_body_preview=data.get("request_body_preview"),
        query_params=data.get("query_params", {}),
        path_params=data.get("path_params", {}),
        client_addr=data.get("client_addr"),
        spans=spans,
        exception=exception_node,
        response=response_summary,
        app_name=data.get("app_name"),
    )
    return trace
