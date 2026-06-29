from aquilia.controller import GET, Controller, RequestCtx
from aquilia.response import Response
from aquilia.versioning import version as api_version
from aquilia.versioning import version_neutral

from .services import PublicCatalogService


class PublicCatalogController(Controller):
    prefix = "/"
    tags = ["public"]
    version = "1.0"

    def __init__(self, service: PublicCatalogService | None = None):
        self.service = service or PublicCatalogService()

    @GET("/catalog")
    @api_version(["1.0", "2.0"])
    async def catalog(self, ctx: RequestCtx):
        return Response.json(self.service.catalog_payload(ctx.headers.get("x-api-version")))

    @GET("/health")
    @version_neutral
    async def health(self, ctx: RequestCtx):
        return Response.json({"status": "ok"})
