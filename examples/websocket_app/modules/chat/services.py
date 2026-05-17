from collections import defaultdict


class ChatPresenceService:
    def __init__(self):
        self._rooms: dict[str, set[str]] = defaultdict(set)

    async def join(self, room: str, connection_id: str) -> dict:
        self._rooms[room].add(connection_id)
        return {"room": room, "members": sorted(self._rooms[room])}

    async def leave(self, room: str, connection_id: str) -> dict:
        self._rooms[room].discard(connection_id)
        return {"room": room, "members": sorted(self._rooms[room])}

    async def snapshot(self) -> dict:
        return {room: sorted(members) for room, members in self._rooms.items()}
