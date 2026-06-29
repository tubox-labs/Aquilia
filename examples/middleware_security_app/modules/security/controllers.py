from aquilia.controller import GET, Controller, RequestCtx
from aquilia.response import Response

from .services import SecurityPolicyService


class SecurityController(Controller):
    prefix = "/"
    tags = ["security"]

    def __init__(self, service: SecurityPolicyService | None = None):
        self.service = service or SecurityPolicyService()

    @GET("/policy")
    async def policy(self, ctx: RequestCtx):
        return Response.json(self.service.classify_request(ctx.query_param("path", "/public") or "/public"))
