from aquilia.controller import Controller, DELETE, GET, RequestCtx
from aquilia.response import Response

from .services import EdgeGatewayService


class EdgeController(Controller):
    prefix = "/"
    tags = ["edge"]

    def __init__(self, service: EdgeGatewayService | None = None):
        self.service = service or EdgeGatewayService()

    @GET("/products/<sku:str>")
    async def product(self, ctx: RequestCtx, sku: str):
        return Response.json(await self.service.product_snapshot(sku))

    @DELETE("/products/<sku:str>/cache")
    async def purge(self, ctx: RequestCtx, sku: str):
        return Response.json({"deleted": await self.service.purge_product(sku)})
