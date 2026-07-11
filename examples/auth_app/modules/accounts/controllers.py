from aquilia import GET, POST, Controller, RequestCtx, Response
from aquilia.auth import AdminGuard, authenticated
from aquilia.auth.decorators import requires

from .contracts import LoginContract, RegisterContract
from .services import AccountsService


class AccountsController(Controller):
    prefix = "/"
    tags = ["accounts"]

    def __init__(self, service: AccountsService | None = None):
        self.service = service or AccountsService()

    @POST("/register", status_code=201)
    async def register(self, ctx: RequestCtx):
        contract = RegisterContract(data=await ctx.json())
        await contract.is_sealed_async()
        return Response.json(await self.service.register(contract.validated_data), status=201)

    @POST("/login")
    async def login(self, ctx: RequestCtx):
        contract = LoginContract(data=await ctx.json())
        await contract.is_sealed_async()
        return Response.json(await self.service.login(contract.validated_data))

    @GET("/me")
    @authenticated
    async def me(self, ctx: RequestCtx, user=None):
        identity = user or ctx.identity
        return Response.json({"identity": identity.to_dict() if hasattr(identity, "to_dict") else None})

    @GET("/admin/summary")
    @requires(AdminGuard())
    async def admin_summary(self, ctx: RequestCtx):
        return Response.json({"area": "admin", "status": "authorized"})
