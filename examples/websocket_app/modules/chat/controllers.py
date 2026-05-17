from aquilia import Controller, GET, RequestCtx, Response

from .services import ChatPresenceService


class ChatController(Controller):
    prefix = "/"
    tags = ["chat"]

    def __init__(self, presence: ChatPresenceService | None = None):
        self.presence = presence or ChatPresenceService()

    @GET("/rooms")
    async def rooms(self, ctx: RequestCtx):
        return Response.json({"rooms": await self.presence.snapshot()})
