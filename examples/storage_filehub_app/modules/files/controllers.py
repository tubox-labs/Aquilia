from aquilia.controller import Controller, GET, POST, RequestCtx
from aquilia.response import Response

from .services import FileHubService


class FileHubController(Controller):
    prefix = "/"
    tags = ["files"]

    def __init__(self, service: FileHubService | None = None):
        self.service = service or FileHubService()

    @GET("/inventory")
    async def inventory(self, ctx: RequestCtx):
        return Response.json(await self.service.inventory(ctx.query_param("alias", "documents") or "documents"))

    @POST("/documents")
    async def upload(self, ctx: RequestCtx):
        data = await ctx.json()
        result = await self.service.upload_document(
            data["name"],
            data["content"].encode("utf-8"),
            tenant=data.get("tenant", "default"),
            quarantine=bool(data.get("quarantine", False)),
        )
        return Response.json(result, status=201)
