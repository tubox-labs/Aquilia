import time

from aquilia.di.diagnostics import DIEvent, DIEventType

from .trace import Lane, SpanStatus, current_trace


class InspectorDiagnosticListener:
    """Implements aquilia.di.diagnostics.DiagnosticListener (duck-typed Protocol)."""

    def on_event(self, event: DIEvent) -> None:
        if event.type not in (DIEventType.RESOLUTION_SUCCESS, DIEventType.RESOLUTION_FAILURE):
            return  # registration/lifecycle events are noisy and not request-scoped; skip
        trace = current_trace()
        if trace is None:
            return
        duration_ms = (event.duration or 0.0) * 1000.0
        now_offset_ms = (time.monotonic() - trace.started_monotonic) * 1000.0
        label = event.provider_name or str(event.token)
        trace.add_span(
            Lane.DEPENDENCY,
            label,
            start_offset_ms=max(0.0, now_offset_ms - duration_ms),
            duration_ms=duration_ms,
            status=SpanStatus.ERROR if event.type is DIEventType.RESOLUTION_FAILURE else SpanStatus.OK,
            detail={"error": str(event.error)} if event.error else {},
        )
