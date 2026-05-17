from aquilia.controller import Controller, GET, RequestCtx
from aquilia.response import Response

from .services import ContentLocalizationService


class ContentController(Controller):
    prefix = "/"
    tags = ["content"]

    def __init__(self, service: ContentLocalizationService | None = None):
        self.service = service or ContentLocalizationService()

    @GET("/landing")
    async def landing(self, ctx: RequestCtx):
        return Response.json(
            self.service.landing_copy(
                accept_language=ctx.headers.get("accept-language", ""),
                name=ctx.query_param("name", "World") or "World",
                count=int(ctx.query_param("count", "1") or "1"),
            )
        )
