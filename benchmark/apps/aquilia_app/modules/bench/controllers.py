from __future__ import annotations

import asyncio
from pathlib import Path

from aquilia import GET, POST, Controller, RequestCtx, Response
from aquilia.faults.domains import BadRequestFault
from benchmark.apps.shared_payload import LARGE_PAYLOAD, build_stream_chunk

from .services import TopService

SAMPLE_TEXT_PATH = Path(__file__).resolve().parents[2] / "static" / "sample.txt"


class BenchmarkController(Controller):
    prefix = ""
    tags = ["benchmark"]

    def __init__(self, top: TopService):
        self.top = top

    @GET("/health")
    async def health(self, ctx: RequestCtx):
        return Response.text("ok")

    @GET("/json/simple")
    async def json_simple(self, ctx: RequestCtx):
        return Response.json({"ok": True, "framework": "aquilia", "value": 42})

    @GET("/json/large")
    async def json_large(self, ctx: RequestCtx):
        return Response.json(LARGE_PAYLOAD)

    @GET("/di")
    async def di_chain(self, ctx: RequestCtx):
        return Response.json({"value": self.top.value()})

    @GET("/middleware/noop")
    async def middleware_noop(self, ctx: RequestCtx):
        return Response.json(
            {
                "ok": True,
                "layers": int(ctx.state.get("noop_layers", 0)),
            }
        )

    @GET("/route/static")
    async def route_static(self, ctx: RequestCtx):
        return Response.json({"route": "static"})

    @GET("/route/params/<user_id:int>/orders/<order_id:int>")
    async def route_params(self, ctx: RequestCtx, user_id: int, order_id: int):
        return Response.json({"user_id": user_id, "order_id": order_id})

    @POST("/body/json")
    async def body_json(self, ctx: RequestCtx):
        payload = await ctx.request.json(strict=False)
        if not isinstance(payload, dict):
            payload = {"value": payload}
        return Response.json({"keys": len(payload.keys()), "size": len(str(payload))})

    @POST("/body/form")
    async def body_form(self, ctx: RequestCtx):
        form = await ctx.request.form()
        quantity_raw = form.get_field("quantity", "0") or "0"
        return Response.json(
            {
                "name": form.get_field("name", ""),
                "category": form.get_field("category", ""),
                "quantity": int(quantity_raw),
            }
        )

    @POST("/body/multipart")
    async def body_multipart(self, ctx: RequestCtx):
        form = await ctx.request.multipart()
        uploaded = form.get_file("file")
        size = 0
        filename = ""

        if uploaded is not None:
            filename = uploaded.filename
            size = len(await uploaded.read())

        await form.cleanup()
        return Response.json({"filename": filename, "size": size})

    @GET("/response/text")
    async def response_text(self, ctx: RequestCtx):
        return Response.text("benchmark-text-response")

    @GET("/response/stream")
    async def response_stream(self, ctx: RequestCtx):
        async def chunk_stream():
            for idx in range(32):
                yield build_stream_chunk(idx)
                await asyncio.sleep(0)

        return Response.stream(chunk_stream(), media_type="application/octet-stream")

    @GET("/response/file")
    async def response_file(self, ctx: RequestCtx):
        return Response.file(SAMPLE_TEXT_PATH)

    @GET("/static/sample.txt")
    async def static_sample(self, ctx: RequestCtx):
        return Response.file(SAMPLE_TEXT_PATH)

    @GET("/error/handled")
    async def error_handled(self, ctx: RequestCtx):
        raise BadRequestFault("handled benchmark fault")

    @GET("/error/unhandled")
    async def error_unhandled(self, ctx: RequestCtx):
        raise RuntimeError("unhandled benchmark error")

    @GET("/compute/async")
    async def compute_async(self, ctx: RequestCtx):
        delay_raw = ctx.request.query_param("delay_ms", "5") or "5"
        delay_ms = max(0.0, float(delay_raw))
        await asyncio.sleep(delay_ms / 1000.0)
        return Response.json({"delay_ms": delay_ms})


def _build_filler_handler(slot: int):
    async def _filler(self, ctx: RequestCtx):
        return Response.json({"slot": slot})

    _filler.__name__ = f"route_filler_{slot}"
    return GET(f"/route/filler/r{slot}")(_filler)


for _slot in range(200):
    setattr(BenchmarkController, f"route_filler_{_slot}", _build_filler_handler(_slot))
