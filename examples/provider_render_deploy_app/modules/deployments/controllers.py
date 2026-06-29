from aquilia.controller import POST, Controller, RequestCtx
from aquilia.response import Response

from .services import RenderDeploymentPlanner


class DeploymentsController(Controller):
    prefix = "/"
    tags = ["deployments"]

    def __init__(self, service: RenderDeploymentPlanner | None = None):
        self.service = service or RenderDeploymentPlanner()

    @POST("/render/dry-run")
    async def render_dry_run(self, ctx: RequestCtx):
        data = await ctx.json()
        return Response.json(self.service.dry_run(data.get("env", {})))
