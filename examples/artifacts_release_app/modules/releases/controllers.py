from aquilia.controller import POST, Controller, RequestCtx
from aquilia.response import Response

from .services import ReleaseArtifactService


class ReleaseController(Controller):
    prefix = "/"
    tags = ["releases"]

    def __init__(self, service: ReleaseArtifactService | None = None):
        self.service = service or ReleaseArtifactService()

    @POST("/")
    async def create(self, ctx: RequestCtx):
        data = await ctx.json()
        return Response.json(self.service.create_release(data["name"], data["version"], data["payload"]), status=201)
