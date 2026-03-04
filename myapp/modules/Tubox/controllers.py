"""
Tubox module controllers (request handlers).

This file defines the HTTP endpoints for the Tubox module
using the modern Controller architecture with pattern-based routing.
"""

from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response
from .faults import TuboxNotFoundFault
from .services import TuboxService


class TuboxController(Controller):
    """
    Controller for Tubox endpoints.

    Provides RESTful CRUD operations for Tubox.
    """
    prefix = "/"
    tags = ["Tubox"]

    def __init__(self, service: "TuboxService" = None):
        # Instantiate service directly if not injected
        self.service = service or TuboxService()

    @GET("/")
    async def list_Tubox(self, ctx: RequestCtx):
        """
        List all Tubox.

        Example:
            GET /Tubox/ -> {"items": [...], "total": 0}
        """
        items = await self.service.get_all()

        return Response.json({
            "items": items,
            "total": len(items)
        })

    @POST("/")
    async def create_Tubox(self, ctx: RequestCtx):
        """
        Create a new Tubox.

        Example:
            POST /Tubox/
            Body: {"name": "Example"}
            -> {"id": 1, "name": "Example"}
        """
        data = await ctx.json()
        item = await self.service.create(data)
        return Response.json(item, status=201)

    @GET("/<id:int>")
    async def get_Tubox(self, ctx: RequestCtx, id: int):
        """
        Get a Tubox by ID.

        Example:
            GET /Tubox/1 -> {"id": 1, "name": "Example"}
        """
        item = await self.service.get_by_id(id)
        if not item:
            raise TuboxNotFoundFault(item_id=id)

        return Response.json(item)

    @PUT("/<id:int>")
    async def update_Tubox(self, ctx: RequestCtx, id: int):
        """
        Update a Tubox by ID.

        Example:
            PUT /Tubox/1
            Body: {"name": "Updated"}
            -> {"id": 1, "name": "Updated"}
        """
        data = await ctx.json()
        item = await self.service.update(id, data)
        if not item:
            raise TuboxNotFoundFault(item_id=id)

        return Response.json(item)

    @DELETE("/<id:int>")
    async def delete_Tubox(self, ctx: RequestCtx, id: int):
        """
        Delete a Tubox by ID.

        Example:
            DELETE /Tubox/1 -> 204 No Content
        """
        deleted = await self.service.delete(id)
        if not deleted:
            raise TuboxNotFoundFault(item_id=id)

        return Response(status=204)