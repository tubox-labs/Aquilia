"""
Socket Controller - Base class for WebSocket controllers

Provides controller abstraction with:
- Lifecycle hooks (on_connect, on_disconnect)
- Message handling (event handlers)
- Room management (publish_room, broadcast)
- DI integration
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .adapters.base import Adapter
    from .connection import Connection

logger = logging.getLogger("aquilia.sockets.controller")


class SocketController:
    """
    Base class for WebSocket controllers.

    Controllers handle WebSocket connections with:
    - Constructor DI injection
    - Lifecycle hooks (@OnConnect, @OnDisconnect)
    - Message handlers (@Event, @AckEvent)
    - Room subscription handlers (@Subscribe, @Unsubscribe)
    - Guards (@Guard)

    Example:
        from aquilia.sockets import (
            SocketController, Socket, OnConnect, Event,
            Connection, Schema
        )
        from aquilia.di import Inject

        @Socket("/chat/:namespace")
        class ChatSocket(SocketController):
            def __init__(self, presence=Inject(tag="presence")):
                self.presence = presence

            @OnConnect()
            async def on_connect(self, conn: Connection):
                await conn.send_event("system.welcome", {
                    "msg": f"Welcome {conn.identity.id}"
                })

            @Event("message.send", schema=Schema({
                "room": str,
                "text": str
            }))
            async def handle_message(self, conn: Connection, payload):
                room = payload["room"]
                await self.publish_room(room, "message.receive", {
                    "from": conn.identity.id,
                    "text": payload["text"]
                })
    """

    # Class-level configuration (overridable)
    namespace: str | None = None
    adapter: Adapter | None = None

    def __init__(self):
        """
        Initialize controller.

        Override in subclasses for DI injection:
            def __init__(self, service=Inject()):
                self.service = service
        """
        pass

    # Publishing & Broadcasting

    async def publish_room(
        self,
        room: str,
        event: str,
        payload: dict[str, Any],
        *,
        namespace: str | None = None,
        exclude_connection: str | None = None,
    ):
        """
        Publish message to all connections in a room.

        Uses adapter for cross-worker fanout.

        Args:
            room: Room identifier
            event: Event name
            payload: Event data
            namespace: Optional namespace override
            exclude_connection: Optional connection ID to exclude
        """
        from .envelope import MessageEnvelope, MessageType

        ns = namespace or self.namespace
        if not ns:
            logger.warning("Cannot publish_room: namespace not set")
            return

        if not self.adapter:
            logger.warning("Cannot publish_room: adapter not set")
            return

        envelope = MessageEnvelope(
            type=MessageType.EVENT,
            event=event,
            payload=payload,
        )

        await self.adapter.publish(
            namespace=ns,
            room=room,
            envelope=envelope,
            exclude_connection=exclude_connection,
        )

    async def broadcast(
        self,
        event: str,
        payload: dict[str, Any],
        *,
        namespace: str | None = None,
        exclude_connection: str | None = None,
    ):
        """
        Broadcast message to all connections in namespace.

        Args:
            event: Event name
            payload: Event data
            namespace: Optional namespace override
            exclude_connection: Optional connection ID to exclude
        """
        from .envelope import MessageEnvelope, MessageType

        ns = namespace or self.namespace
        if not ns:
            logger.warning("Cannot broadcast: namespace not set")
            return

        if not self.adapter:
            logger.warning("Cannot broadcast: adapter not set")
            return

        envelope = MessageEnvelope(
            type=MessageType.EVENT,
            event=event,
            payload=payload,
        )

        await self.adapter.broadcast(
            namespace=ns,
            envelope=envelope,
            exclude_connection=exclude_connection,
        )

    # Lifecycle hooks (override in subclasses with decorators)

    async def on_connect(self, conn: Connection):
        """
        Called when connection is established.

        Override with @OnConnect() decorator:
            @OnConnect()
            async def on_connect(self, conn: Connection):
                ...
        """
        pass

    async def on_disconnect(self, conn: Connection, reason: str | None = None):
        """
        Called when connection is closed.

        Override with @OnDisconnect() decorator:
            @OnDisconnect()
            async def on_disconnect(self, conn: Connection, reason: Optional[str]):
                ...
        """
        pass

    # Helper methods

    def get_room_members(self, room: str, namespace: str | None = None) -> set[str]:
        """
        Get connection IDs in a room.

        Args:
            room: Room identifier
            namespace: Optional namespace override

        Returns:
            Set of connection IDs
        """
        ns = namespace or self.namespace
        if not ns or not self.adapter:
            return set()

        # This would be implemented by adapter
        # For now, return empty set
        return set()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(namespace={self.namespace})"
