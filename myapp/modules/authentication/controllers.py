"""
Authentication module controllers (request handlers).

This file defines the HTTP endpoints for the authentication module
using the modern Controller architecture with pattern-based routing.
"""

from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response
from .faults import AuthenticationNotFoundFault
from .services import AuthenticationService


class AuthenticationController(Controller):
    """
    Controller for authentication endpoints.

    Provides RESTful CRUD operations for authentication.
    """
    prefix = "/"
    tags = ["authentication"]

    def __init__(self, service: "AuthenticationService" = None):
        # Instantiate service directly if not injected
        self.service = service or AuthenticationService()

    @GET("/")
    async def list_authentication(self, ctx: RequestCtx):
        """
        List all authentication.

        Example:
            GET /authentication/ -> {"items": [...], "total": 0}
        """
        items = await self.service.get_all()

        return Response.json({
            "items": items,
            "total": len(items)
        })

    @POST("/")
    async def create_authentication(self, ctx: RequestCtx):
        """
        Create a new authentication.

        Example:
            POST /authentication/
            Body: {"name": "Example"}
            -> {"id": 1, "name": "Example"}
        """
        data = await ctx.json()
        item = await self.service.create(data)
        return Response.json({"context": ctx.request.headers, **item}, status=201)

    @GET("/<id:int>")
    async def get_authentication(self, ctx: RequestCtx, id: int):
        """
        Get a authentication by ID.

        Example:
            GET /authentication/1 -> {"id": 1, "name": "Example"}
        """
        item = await self.service.get_by_id(id)
        if not item:
            raise AuthenticationNotFoundFault(item_id=id)

        return Response.json(item)

    @PUT("/<id:int>")
    async def update_authentication(self, ctx: RequestCtx, id: int):
        """
        Update a authentication by ID.

        Example:
            PUT /authentication/1
            Body: {"name": "Updated"}
            -> {"id": 1, "name": "Updated"}
        """
        data = await ctx.json()
        item = await self.service.update(id, data)
        if not item:
            raise AuthenticationNotFoundFault(item_id=id)

        return Response.json(item)

    @DELETE("/<id:int>")
    async def delete_authentication(self, ctx: RequestCtx, id: int):
        """
        Delete a authentication by ID.

        Example:
            DELETE /authentication/1 -> 204 No Content
        """
        deleted = await self.service.delete(id)
        if not deleted:
            raise AuthenticationNotFoundFault(item_id=id)

        return Response(status=204)