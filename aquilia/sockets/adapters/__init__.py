"""
Adapters Package - WebSocket scaling adapters
"""

from aquilia.sockets.adapters.base import Adapter, RoomInfo
from aquilia.sockets.adapters.inmemory import InMemoryAdapter
from aquilia.sockets.adapters.redis import RedisAdapter

__all__ = [
    "Adapter",
    "RoomInfo",
    "InMemoryAdapter",
    "RedisAdapter",
]
