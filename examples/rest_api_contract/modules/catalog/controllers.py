from aquilia import DELETE, GET, PATCH, POST, Controller, RequestCtx, Response

from .contracts import ProductCreateContract, ProductUpdateContract
from .services import CatalogService


class CatalogController(Controller):
    prefix = "/"
    tags = ["catalog"]

    def __init__(self, service: CatalogService | None = None):
        self.service = service or CatalogService()

    @GET("/health")
    async def health(self, ctx: RequestCtx):
        return Response.json({"module": "catalog", "status": "ok", "path": ctx.path})

    @GET("/products")
    async def list_products(self, ctx: RequestCtx):
        active_raw = ctx.query_param("active", "true")
        active = None if active_raw == "all" else active_raw.lower() != "false"
        limit = min(int(ctx.query_param("limit", "50") or "50"), 100)
        offset = max(int(ctx.query_param("offset", "0") or "0"), 0)
        payload = await self.service.list_products(
            q=ctx.query_param("q"),
            active=active,
            limit=limit,
            offset=offset,
        )
        return Response.json(payload)

    @POST("/products", status_code=201)
    async def create_product(self, ctx: RequestCtx):
        contract = ProductCreateContract(data=await ctx.json())
        await contract.is_sealed_async()
        product = await self.service.create_product(contract.validated_data)
        return Response.json(product, status=201)

    @GET("/products/<sku:str>")
    async def get_product(self, ctx: RequestCtx, sku: str):
        return Response.json(await self.service.get_product(sku))

    @PATCH("/products/<sku:str>")
    async def update_product(self, ctx: RequestCtx, sku: str):
        contract = ProductUpdateContract(data=await ctx.json())
        await contract.is_sealed_async()
        return Response.json(await self.service.update_product(sku, contract.validated_data))

    @DELETE("/products/<sku:str>")
    async def delete_product(self, ctx: RequestCtx, sku: str):
        return Response.json(await self.service.deactivate_product(sku))
