from aquilia import DELETE, GET, PATCH, POST, Controller, RequestCtx, Response

from .contracts import ProjectCreateContract, ProjectUpdateContract
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
        contract = ProjectCreateContract(data=await ctx.json())
        await contract.is_sealed_async()
        return Response.json(await self.service.create_project(contract.validated_data), status=201)

    @GET("/<key:str>")
    async def get_project(self, ctx: RequestCtx, key: str):
        return Response.json(await self.service.get_project(key))

    @PATCH("/<key:str>")
    async def update_project(self, ctx: RequestCtx, key: str):
        contract = ProjectUpdateContract(data=await ctx.json())
        await contract.is_sealed_async()
        return Response.json(await self.service.update_project(key, contract.validated_data))

    @DELETE("/<key:str>")
    async def archive_project(self, ctx: RequestCtx, key: str):
        return Response.json(await self.service.archive_project(key))

    @POST("/<key:str>/restore")
    async def restore_project(self, ctx: RequestCtx, key: str):
        return Response.json(await self.service.restore_project(key))
