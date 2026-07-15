"""
aquilia.devplatform.core.websocket — WebSocket connection registry and tracker.

Keeps a live map of active WebSocket connections keyed by connection ID.
Reports aggregate frame counts and disconnect reason codes to RuntimeStateStore.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field

from aquilia.devplatform.core._base import SingletonMixin


@dataclass
class WebSocketEntry:
    """Metadata record for a single active WebSocket connection."""

    connection_id: str
    path: str
    client_addr: str | None
    connected_at: float = field(default_factory=time.time)
    inbound_frames: int = 0
    outbound_frames: int = 0
    subscribed_channels: list[str] = field(default_factory=list)
    disconnect_code: int | None = None
    disconnect_reason: str | None = None

    @property
    def duration_s(self) -> float:
        return time.time() - self.connected_at


class WebSocketTracker(SingletonMixin):
    """
    Thread-safe registry of active WebSocket connections.

    Singleton — obtain via WebSocketTracker.get_instance().
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._connections: dict[str, WebSocketEntry] = {}
        self._total_connected: int = 0
        self._total_disconnected: int = 0

    def register(self, entry: WebSocketEntry) -> None:
        with self._lock:
            self._connections[entry.connection_id] = entry
            self._total_connected += 1

    def unregister(
        self,
        connection_id: str,
        code: int | None = None,
        reason: str | None = None,
    ) -> None:
        with self._lock:
            entry = self._connections.pop(connection_id, None)
            if entry:
                entry.disconnect_code = code
                entry.disconnect_reason = reason
                self._total_disconnected += 1

    def record_inbound_frame(self, connection_id: str) -> None:
        with self._lock:
            if connection_id in self._connections:
                self._connections[connection_id].inbound_frames += 1

    def record_outbound_frame(self, connection_id: str) -> None:
        with self._lock:
            if connection_id in self._connections:
                self._connections[connection_id].outbound_frames += 1

    def subscribe_channel(self, connection_id: str, channel: str) -> None:
        with self._lock:
            if connection_id in self._connections:
                self._connections[connection_id].subscribed_channels.append(channel)

    def get_active_connections(self) -> list[WebSocketEntry]:
        with self._lock:
            return list(self._connections.values())

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._connections)

    @property
    def total_connected(self) -> int:
        return self._total_connected

    @property
    def total_disconnected(self) -> int:
        return self._total_disconnected
