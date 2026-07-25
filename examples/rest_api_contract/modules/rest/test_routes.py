"""
Test routes for rest module - Additional test endpoints.
"""

from aquilia import Controller, GET, POST, RequestCtx, Response


class TestRestController(Controller):
    """Test endpoints for rest module verification."""

    prefix = "/test-rest"
    tags = ["test", "rest"]

    @GET("/hello")
    async def hello(self, ctx: RequestCtx):
        """Simple hello world test endpoint."""
        return Response.json({
            "message": "Hello from {self.name}!",
            "status": "success",
            "module": "rest",
            "controller": "TestRestController"
        })

    @GET("/echo/<message:str>")
    async def echo(self, ctx: RequestCtx, message: str):
        """Echo back a message with path parameter."""
        return Response.json({
            "echo": message,
            "length": len(message),
            "type": "path_param",
            "module": "rest"
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
                "module": "rest"
            })
        except Exception as e:
            return Response.json({
                "error": str(e),
                "status": "failed"
            }, status=400)

    @GET("/health")
    async def health(self, ctx: RequestCtx):
        """Health check endpoint for rest module."""
        return Response.json({
            "status": "healthy",
            "module": "rest",
            "controller": "TestRestController"
        })