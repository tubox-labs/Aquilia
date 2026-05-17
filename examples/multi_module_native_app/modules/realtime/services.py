class RealtimeService:
    async def event_payload(self, event: str, payload: dict) -> dict:
        return {"event": event, "payload": payload}
