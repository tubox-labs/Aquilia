from aquilia.controller import GET, POST, Controller, RequestCtx
from aquilia.response import Response

from .services import MLOpsRegistryService


class MLOpsDemoController(Controller):
    prefix = "/"
    tags = ["mlops"]

    def __init__(self, service: MLOpsRegistryService | None = None):
        self.service = service or MLOpsRegistryService()

    @POST("/models/register")
    async def register(self, ctx: RequestCtx):
        data = await ctx.json()
        return Response.json(await self.service.register_model(data.get("version", "v1")), status=201)

    @GET("/plugins")
    async def plugins(self, ctx: RequestCtx):
        return Response.json({"plugins": self.service.plugin_inventory()})
