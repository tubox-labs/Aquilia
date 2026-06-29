import contextlib
import time
from collections.abc import Iterator

from .trace import SpanStatus, current_trace

_CUSTOM_LANES = {}


def register_lane(key: str, display_name: str) -> None:
    _CUSTOM_LANES[key] = display_name


@contextlib.contextmanager
def span(lane: str, label: str, detail: dict = None) -> Iterator[None]:
    trace = current_trace()
    if trace is None:
        yield
        return
    t0 = time.monotonic()
    status = SpanStatus.OK
    err = None
    try:
        yield
    except Exception as e:
        status = SpanStatus.ERROR
        err = e
        raise
    finally:
        dt = (time.monotonic() - t0) * 1000.0
        extra = dict(detail or {})
        if err:
            extra["error"] = str(err)
        trace.add_span(
            lane=lane,
            label=label,
            start_offset_ms=(t0 - trace.started_monotonic) * 1000.0,
            duration_ms=dt,
            status=status,
            detail=extra,
        )
