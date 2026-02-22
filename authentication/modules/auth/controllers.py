"""
Auth module controllers (request handlers).

This file defines the HTTP endpoints for the auth module
using the modern Controller architecture with pattern-based routing.
"""

from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response
from .faults import AuthNotFoundFault
from .services import AuthService
from .serializer import RegisterInputModel, UserOutputModel


class AuthController(Controller):
    prefix = "/"
    tags = ["auth"]

    def __init__(self, service: AuthService):
        self.service = service

    @GET("/<name:str>")
    async def list_auth(self, name: str):
        return Response.json({"name": name })

    @POST("/")
    async def create_auth(self, ctx: RequestCtx, data: RegisterInputModel):
        user = await self.service.register(data = data)
        return Response.json(UserOutputModel(instance = user).data, status = 201)
 