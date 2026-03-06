"""
Test routes for auth module - Additional test endpoints.
"""

from aquilia import Controller, GET, POST, RequestCtx, Response


class TestAuthController(Controller):
    """Test endpoints for auth module verification."""

    prefix = "/test-auth"
    tags = ["test", "auth"]

    @GET("/hello")
    async def hello(self, ctx: RequestCtx):
        """Simple hello world test endpoint."""
        return Response.json({
            "message": "Hello from {self.name}!",
            "status": "success",
            "module": "auth",
            "controller": "TestAuthController"
        })

    @GET("/echo/<message:str>")
    async def echo(self, ctx: RequestCtx, message: str):
        """Echo back a message with path parameter."""
        return Response.json({
            "echo": message,
            "length": len(message),
            "type": "path_param",
            "module": "auth"
        })

    @POST("/data")
    async def post_data(self, ctx: RequestCtx):
        """Test POST with JSON body."""
        try:
            data = await ctx.json()
            return Response.json({
                "received": data,
                "keys": list(data.keys()) if isinstance(data, dict) else None,
                "status": "processed",
                "module": "auth"
            })
        except Exception as e:
            return Response.json({
                "error": str(e),
                "status": "failed"
            }, status=400)

    @GET("/health")
    async def health(self, ctx: RequestCtx):
        """Health check endpoint for auth module."""
        return Response.json({
            "status": "healthy",
            "module": "auth",
            "controller": "TestAuthController"
        })