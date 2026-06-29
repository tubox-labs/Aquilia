from aquilia import GET, Controller, RequestCtx, Response

from .services import OperationsService


class OperationsController(Controller):
    prefix = "/"
    tags = ["operations"]

    def __init__(self, service: OperationsService | None = None):
        self.service = service or OperationsService()

    @GET("/health")
    async def health(self, ctx: RequestCtx):
        return Response.json(await self.service.health())

    @GET("/ready")
    async def readiness(self, ctx: RequestCtx):
        return Response.json(await self.service.readiness())

    @GET("/metrics")
    async def metrics(self, ctx: RequestCtx):
        return Response.json(await self.service.runtime_metrics())
