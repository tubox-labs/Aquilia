from aquilia.controller import GET, POST, Controller, RequestCtx
from aquilia.response import Response

from .services import AdminOpsService, TicketRecord


class AdminOpsController(Controller):
    prefix = "/"
    tags = ["adminops"]

    def __init__(self, service: AdminOpsService | None = None):
        self.service = service or AdminOpsService()

    @GET("/dashboard")
    async def dashboard(self, ctx: RequestCtx):
        return Response.json(self.service.dashboard())

    @POST("/tickets")
    async def create_ticket(self, ctx: RequestCtx):
        data = await ctx.json()
        ticket = TicketRecord(
            key=data["key"],
            customer_email=data["customer_email"],
            subject=data["subject"],
            priority=data.get("priority", "normal"),
        )
        return Response.json(self.service.create_ticket(ticket), status=201)
