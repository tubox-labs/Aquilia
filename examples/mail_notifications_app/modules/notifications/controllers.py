from aquilia.controller import Controller, POST, RequestCtx
from aquilia.response import Response

from .services import NotificationService


class NotificationsController(Controller):
    prefix = "/"
    tags = ["notifications"]

    def __init__(self, service: NotificationService | None = None):
        self.service = service or NotificationService()

    @POST("/welcome")
    async def welcome(self, ctx: RequestCtx):
        data = await ctx.json()
        return Response.json(await self.service.send_welcome(data["email"], data["name"]), status=202)
