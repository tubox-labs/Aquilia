from aquilia import DELETE, GET, PATCH, POST, Controller, RequestCtx, Response

from .blueprints import ProjectCreateBlueprint, ProjectUpdateBlueprint
from .services import ProjectsService


class ProjectsController(Controller):
    prefix = "/"
    tags = ["projects"]

    def __init__(self, service: ProjectsService | None = None):
        self.service = service or ProjectsService()

    @GET("/")
    async def list_projects(self, ctx: RequestCtx):
        include_archived = (ctx.query_param("archived", "false") or "false").lower() == "true"
        return Response.json({"items": await self.service.list_projects(include_archived=include_archived)})

    @POST("/", status_code=201)
    async def create_project(self, ctx: RequestCtx):
        blueprint = ProjectCreateBlueprint(data=await ctx.json())
        await blueprint.is_sealed_async()
        return Response.json(await self.service.create_project(blueprint.validated_data), status=201)

    @GET("/<key:str>")
    async def get_project(self, ctx: RequestCtx, key: str):
        return Response.json(await self.service.get_project(key))

    @PATCH("/<key:str>")
    async def update_project(self, ctx: RequestCtx, key: str):
        blueprint = ProjectUpdateBlueprint(data=await ctx.json())
        await blueprint.is_sealed_async()
        return Response.json(await self.service.update_project(key, blueprint.validated_data))

    @DELETE("/<key:str>")
    async def archive_project(self, ctx: RequestCtx, key: str):
        return Response.json(await self.service.archive_project(key))

    @POST("/<key:str>/restore")
    async def restore_project(self, ctx: RequestCtx, key: str):
        return Response.json(await self.service.restore_project(key))
