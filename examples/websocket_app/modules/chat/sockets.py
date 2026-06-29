from aquilia.sockets import (
    AckEvent,
    Connection,
    Event,
    OnConnect,
    OnDisconnect,
    Schema,
    Socket,
    SocketController,
    Subscribe,
    Unsubscribe,
)

from .services import ChatPresenceService


@Socket("/ws/chat/:room", allowed_origins=["*"], message_rate_limit=20, max_message_size=16384)
class ChatSocket(SocketController):
    namespace = "chat"

    def __init__(self, presence: ChatPresenceService | None = None):
        self.presence = presence or ChatPresenceService()

    @OnConnect()
    async def connected(self, conn: Connection):
        room = conn.scope.path_params.get("room", "lobby")
        await conn.join(room)
        await self.presence.join(room, conn.id)
        await conn.send_event("system.welcome", {"room": room, "connection_id": conn.id})

    @OnDisconnect()
    async def disconnected(self, conn: Connection, reason: str | None = None):
        for room in conn.rooms:
            await self.presence.leave(room, conn.id)

    @Subscribe("room.join", schema=Schema({"room": str}))
    async def join_room(self, conn: Connection, payload: dict):
        room = payload["room"]
        await conn.join(room)
        state = await self.presence.join(room, conn.id)
        await conn.send_event("room.joined", state)

    @Unsubscribe("room.leave", schema=Schema({"room": str}))
    async def leave_room(self, conn: Connection, payload: dict):
        room = payload["room"]
        await conn.leave(room)
        state = await self.presence.leave(room, conn.id)
        await conn.send_event("room.left", state)

    @Event("message.send", schema=Schema({"room": str, "text": str}), ack=True)
    async def send_message(self, conn: Connection, payload: dict):
        await self.publish_room(
            payload["room"],
            "message.received",
            {"from": conn.id, "text": payload["text"]},
            exclude_connection=None,
        )
        return {"delivered": True, "room": payload["room"]}

    @AckEvent("presence.snapshot")
    async def presence_snapshot(self, conn: Connection, payload: dict):
        return await self.presence.snapshot()
