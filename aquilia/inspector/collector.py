from collections import deque
from collections.abc import Callable

from .config import InspectorConfig
from .trace import RequestTrace


class InspectorCollector:
    def __init__(self, config: InspectorConfig):
        self._config = config
        from .store import MemoryTraceStore, SQLiteTraceStore
        if config.store == "sqlite":
            self.store = SQLiteTraceStore(config)
        else:
            self.store = MemoryTraceStore(config)
        self._subscribers: list[Callable[[RequestTrace], None]] = []  # for SSE, see stream.py
        from .stream import SSEStreamManager

        self.stream_manager = SSEStreamManager()
        self.subscribe(self.stream_manager.publish_trace)
        try:
            from aquilia.admin.query_inspector import get_query_inspector

            self.subscribe(get_query_inspector().on_trace_committed)
        except ImportError:
            pass

    def commit(self, trace: RequestTrace) -> None:
        self.store.save(trace)

    def get(self, trace_id: str) -> RequestTrace | None:
        return self.store.get(trace_id)

    def list_recent(self, limit: int = 100) -> list[RequestTrace]:
        return self.store.list_recent(limit)

    def clear(self) -> None:
        self.store.clear()

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
