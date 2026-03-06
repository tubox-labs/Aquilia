"""
Auth module controllers (request handlers).

This file defines the HTTP endpoints for the auth module
using the modern Controller architecture with pattern-based routing.
"""

from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response
from .faults import AuthNotFoundFault
from .services import AuthService


class AuthController(Controller):
    """
    Controller for auth endpoints.

    Provides RESTful CRUD operations for auth.
    """
    prefix = "/"
    tags = ["auth"]

    def __init__(self, service: "AuthService" = None):
        # Instantiate service directly if not injected
        self.service = service or AuthService()

    @GET("/")
    async def list_auth(self, ctx: RequestCtx):
        """
        List all auth.

        Example:
            GET /auth/ -> {"items": [...], "total": 0}
        """
        items = await self.service.get_all()

        raise AuthNotFoundFault(1)

    @POST("/")
    async def create_auth(self, ctx: RequestCtx):
        """
        Create a new auth.

        Example:
            POST /auth/
            Body: {"name": "Example"}
            -> {"id": 1, "name": "Example"}
        """
        data = await ctx.json()
        item = await self.service.create(data)
        return Response.json(item, status=201)

    @GET("/<id:int>")
    async def get_auth(self, ctx: RequestCtx, id: int):
        """
        Get a auth by ID.

        Example:
            GET /auth/1 -> {"id": 1, "name": "Example"}
        """
        item = await self.service.get_by_id(id)
        if not item:
            raise AuthNotFoundFault(item_id=id)

        return Response.json(item)

    @PUT("/<id:int>")
    async def update_auth(self, ctx: RequestCtx, id: int):
        """
        Update a auth by ID.

        Example:
            PUT /auth/1
            Body: {"name": "Updated"}
            -> {"id": 1, "name": "Updated"}
        """
        data = await ctx.json()
        item = await self.service.update(id, data)
        if not item:
            raise AuthNotFoundFault(item_id=id)

        return Response.json(item)

    @DELETE("/<id:int>")
    async def delete_auth(self, ctx: RequestCtx, id: int):
        """
        Delete a auth by ID.

        Example:
            DELETE /auth/1 -> 204 No Content
        """
        deleted = await self.service.delete(id)
        if not deleted:
            raise AuthNotFoundFault(item_id=id)

        return Response(status=204)