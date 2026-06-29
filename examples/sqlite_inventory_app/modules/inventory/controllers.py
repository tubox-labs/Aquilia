from aquilia.controller import GET, POST, Controller, RequestCtx
from aquilia.response import Response

from .services import InventorySqliteService


class InventoryController(Controller):
    prefix = "/"
    tags = ["inventory"]

    def __init__(self, service: InventorySqliteService | None = None):
        self.service = service or InventorySqliteService("runtime/inventory.db")

    @POST("/items")
    async def upsert(self, ctx: RequestCtx):
        data = await ctx.json()
        return Response.json(await self.service.upsert_item(data["sku"], data["name"], int(data["quantity"])))

    @GET("/items/<sku:str>")
    async def get_item(self, ctx: RequestCtx, sku: str):
        return Response.json(await self.service.get_item(sku))
