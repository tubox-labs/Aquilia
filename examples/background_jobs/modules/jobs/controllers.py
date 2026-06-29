from aquilia import GET, POST, Controller, RequestCtx, Response
from aquilia.faults import NotFoundFault

from .services import JobsService


class JobsController(Controller):
    prefix = "/"
    tags = ["jobs"]

    def __init__(self, service: JobsService | None = None):
        self.service = service or JobsService()

    @POST("/welcome")
    async def enqueue_welcome(self, ctx: RequestCtx):
        data = await ctx.json()
        job_id = await self.service.send_welcome(email=data["email"], name=data.get("name", "friend"))
        return Response.json({"job_id": job_id}, status=202)

    @POST("/reports/daily")
    async def enqueue_report(self, ctx: RequestCtx):
        data = await ctx.json()
        job_id = await self.service.rebuild_report(date=data["date"])
        return Response.json({"job_id": job_id}, status=202)

    @GET("/<job_id:str>")
    async def status(self, ctx: RequestCtx, job_id: str):
        job = await self.service.job_status(job_id)
        if job is None:
            raise NotFoundFault(detail="Job was not found")
        return Response.json(job)

    @GET("/stats")
    async def stats(self, ctx: RequestCtx):
        return Response.json(await self.service.stats())
