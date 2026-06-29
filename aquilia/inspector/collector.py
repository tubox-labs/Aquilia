from collections import deque
from collections.abc import Callable

from .config import InspectorConfig
from .trace import RequestTrace


class InspectorCollector:
    def __init__(self, config: InspectorConfig):
        self._traces: deque[RequestTrace] = deque(maxlen=config.max_traces)
        self._by_id: dict[str, RequestTrace] = {}  # kept in sync; bounded by deque eviction
        self._config = config
        self._subscribers: list[Callable[[RequestTrace], None]] = []  # for SSE, see stream.py

    def commit(self, trace: RequestTrace) -> None:
        # Check if deque is at capacity before appending
        if len(self._traces) == self._traces.maxlen:
            evicted = self._traces[0]
            self._by_id.pop(evicted.trace_id, None)
        self._traces.append(trace)
        self._by_id[trace.trace_id] = trace

    def get(self, trace_id: str) -> RequestTrace | None:
        return self._by_id.get(trace_id)

    def list_recent(self, limit: int = 100) -> list[RequestTrace]:
        # Return recent traces in reverse order (newest first) up to limit
        recent = list(self._traces)
        recent.reverse()
        return recent[:limit]

    def clear(self) -> None:
        self._traces.clear()
        self._by_id.clear()

    def subscribe(self, callback: Callable[[RequestTrace], None]) -> None:
        self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[RequestTrace], None]) -> None:
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    def publish(self, trace: RequestTrace) -> None:
        for subscriber in list(self._subscribers):
            try:
                subscriber(trace)
            except Exception:
                pass


_COLLECTOR: InspectorCollector | None = None


def get_collector(config: InspectorConfig) -> InspectorCollector:
    global _COLLECTOR
    if _COLLECTOR is None:
        _COLLECTOR = InspectorCollector(config)
    return _COLLECTOR


def reset_global_collector() -> None:
    global _COLLECTOR
    _COLLECTOR = None
