from aquilia import POST, Controller, RequestCtx, Response
from aquilia.auth import authenticated

from .services import NotificationService


class NotificationsController(Controller):
    prefix = "/"
    tags = ["notifications"]

    def __init__(self, service: NotificationService | None = None):
        self.service = service or NotificationService()

    @POST("/receipts")
    @authenticated
    async def send_receipt(self, ctx: RequestCtx):
        data = await ctx.json()
        job_id = await self.service.send_receipt(email=data["email"], order_id=data["order_id"])
        return Response.json({"job_id": job_id}, status=202)
