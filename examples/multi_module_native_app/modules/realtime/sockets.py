from aquilia.sockets import AckEvent, Connection, Event, OnConnect, Socket, SocketController, Subscribe

from .services import RealtimeService


@Socket("/ws/orders/:tenant", allowed_origins=["*"], message_rate_limit=30)
class OrderEventsSocket(SocketController):
    namespace = "orders"

    def __init__(self, service: RealtimeService | None = None):
        self.service = service or RealtimeService()

    @OnConnect()
    async def connect(self, conn: Connection):
        tenant = conn.scope.path_params.get("tenant", "public")
        await conn.join(f"tenant:{tenant}")
        await conn.send_event("connected", {"tenant": tenant, "connection_id": conn.id})

    @Subscribe("order.watch")
    async def watch_order(self, conn: Connection, payload: dict):
        room = f"order:{payload['order_id']}"
        await conn.join(room)
        await conn.send_event("order.watching", {"room": room})

    @Event("order.note", ack=True)
    async def note(self, conn: Connection, payload: dict):
        event = await self.service.event_payload("order.note", payload)
        await self.publish_room(f"order:{payload['order_id']}", "order.note", event)
        return {"published": True}

    @AckEvent("ping")
    async def ping(self, conn: Connection, payload: dict):
        return {"pong": True}
