from __future__ import annotations


class PathNoopMiddleware:
    """No-op middleware layer used to benchmark middleware stack cost."""

    def __init__(self, layer_id: int, path_prefix: str = "/middleware"):
        self.layer_id = layer_id
        self.path_prefix = path_prefix

    async def __call__(self, request, ctx, next_handler):
        if request.path.startswith(self.path_prefix):
            current = int(ctx.state.get("noop_layers", 0))
            ctx.state["noop_layers"] = current + 1
        return await next_handler(request, ctx)
