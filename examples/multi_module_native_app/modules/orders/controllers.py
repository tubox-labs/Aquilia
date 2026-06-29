from aquilia import GET, POST, Controller, RequestCtx, Response
from aquilia.auth import authenticated

from .blueprints import CreateOrderBlueprint
from .services import OrdersService


class OrdersController(Controller):
    prefix = "/"
    tags = ["orders"]

    def __init__(self, service: OrdersService | None = None):
        self.service = service or OrdersService()

    @GET("/")
    @authenticated
    async def list_orders(self, ctx: RequestCtx):
        return Response.json({"items": await self.service.list_orders()})

    @POST("/", status_code=201)
    @authenticated
    async def create_order(self, ctx: RequestCtx):
        blueprint = CreateOrderBlueprint(data=await ctx.json())
        await blueprint.is_sealed_async()
        return Response.json(await self.service.create_order(blueprint.validated_data), status=201)

    @GET("/<order_id:str>")
    @authenticated
    async def get_order(self, ctx: RequestCtx, order_id: str):
        return Response.json(await self.service.get_order(order_id))
