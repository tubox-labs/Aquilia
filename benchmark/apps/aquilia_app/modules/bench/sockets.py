from __future__ import annotations

from aquilia import Event, Socket, SocketController


@Socket("/ws/echo")
class BenchmarkSocket(SocketController):
    @Event("ping", ack=True)
    async def ping(self, conn, payload):
        return {
            "id": payload.get("id"),
            "echo": payload.get("payload"),
        }
