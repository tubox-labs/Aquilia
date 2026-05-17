from aquilia.controller import Controller, GET, RequestCtx
from aquilia.response import Response

from .services import PortalRenderService


class PortalController(Controller):
    prefix = "/"
    tags = ["portal"]

    def __init__(self, service: PortalRenderService | None = None):
        self.service = service or PortalRenderService()

    @GET("/dashboard")
    async def dashboard(self, ctx: RequestCtx):
        html = await self.service.render_dashboard({"name": "Acme", "balance": 1200.5, "alerts": ["Invoice due"]})
        return Response.html(html)
