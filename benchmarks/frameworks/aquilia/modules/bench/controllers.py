from __future__ import annotations

import asyncio
import random

from aquilia import GET, POST, Controller, RequestCtx, Response
from aquilia.controller.validation import validate_body
from aquilia.db import AquiliaDatabase
from benchmarks.frameworks.shared import LARGE_PAYLOAD, UserProfileContract, jinja_env

from .services import TopService


class BenchmarkController(Controller):
    prefix = ""
    tags = ["benchmark"]
    instantiation_mode = "singleton"

    def __init__(self, top: TopService, db: AquiliaDatabase):
        self.top = top
        self.db = db

    @GET("/health")
    async def health(self, ctx: RequestCtx):
        return Response.text("ok")

    @GET("/plaintext")
    async def plaintext(self, ctx: RequestCtx):
        return Response.text("Hello, World!")

    @GET("/json")
    async def json_endpoint(self, ctx: RequestCtx):
        return Response.json({"message": "Hello, World!"})

    @GET("/json/large")
    async def json_large(self, ctx: RequestCtx):
        return Response.json(LARGE_PAYLOAD)

    @GET("/db")
    async def db_single(self, ctx: RequestCtx):
        row_id = random.randint(1, 10000)
        row = await self.db.fetch_one("SELECT id, randomNumber FROM world WHERE id = ?", [row_id])
        return Response.json({"id": row["id"], "randomNumber": row["randomNumber"]})

    @GET("/queries")
    async def db_queries(self, ctx: RequestCtx):
        queries = ctx.request.query_param("queries", "1") or "1"
        try:
            q_val = int(queries)
        except ValueError:
            q_val = 1
        q_val = max(1, min(500, q_val))

        results = []
        for _ in range(q_val):
            row_id = random.randint(1, 10000)
            row = await self.db.fetch_one("SELECT id, randomNumber FROM world WHERE id = ?", [row_id])
            results.append({"id": row["id"], "randomNumber": row["randomNumber"]})
        return Response.json(results)

    @GET("/updates")
    async def db_updates(self, ctx: RequestCtx):
        queries = ctx.request.query_param("queries", "1") or "1"
        try:
            q_val = int(queries)
        except ValueError:
            q_val = 1
        q_val = max(1, min(500, q_val))

        results = []
        # Run updates inside transaction block
        async with self.db.transaction():
            for _ in range(q_val):
                row_id = random.randint(1, 10000)
                new_num = random.randint(1, 10000)
                row = await self.db.fetch_one("SELECT id, randomNumber FROM world WHERE id = ?", [row_id])
                await self.db.execute("UPDATE world SET randomNumber = ? WHERE id = ?", [new_num, row_id])
                results.append({"id": row_id, "randomNumber": new_num})
        return Response.json(results)

    @GET("/fortunes")
    async def fortunes(self, ctx: RequestCtx):
        rows = await self.db.fetch_all("SELECT id, message FROM fortune")
        fortunes_list = [{"id": r["id"], "message": r["message"]} for r in rows]

        fortunes_list.append({"id": 0, "message": "Additional fortune added at runtime."})
        fortunes_list.sort(key=lambda x: x["message"])

        template = jinja_env.get_template("fortunes.html")
        rendered = template.render(fortunes=fortunes_list)
        return Response.html(rendered)

    CACHE_STORE = {i: random.randint(1, 10000) for i in range(1, 10001)}

    @GET("/cached")
    async def cached_test(self, ctx: RequestCtx):
        queries = ctx.request.query_param("queries", "1") or "1"
        try:
            q_val = int(queries)
        except ValueError:
            q_val = 1
        q_val = max(1, min(500, q_val))

        results = []
        for _ in range(q_val):
            row_id = random.randint(1, 10000)
            val = self.CACHE_STORE.get(row_id)
            if val is None:
                row = await self.db.fetch_one("SELECT randomNumber FROM world WHERE id = ?", [row_id])
                val = row["randomNumber"]
                self.CACHE_STORE[row_id] = val
            results.append({"id": row_id, "randomNumber": val})
        return Response.json(results)

    @POST("/validation/contract")
    @validate_body(UserProfileContract)
    async def validation_contract(self, ctx: RequestCtx, body: UserProfileContract):
        # body is the validated and casted contract instance
        return Response.json({"ok": True, "username": body.username})

    @GET("/route/static")
    async def route_static(self, ctx: RequestCtx):
        return Response.json({"route": "static"})

    @GET("/route/params/<user_id:int>/orders/<order_id:int>")
    async def route_params(self, ctx: RequestCtx, user_id: int, order_id: int):
        return Response.json({"user_id": user_id, "order_id": order_id})

    @GET("/di")
    async def di_chain(self, ctx: RequestCtx):
        return Response.json({"value": self.top.value()})

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

    @GET("/response/stream")
    async def response_stream(self, ctx: RequestCtx):
        async def chunk_stream():
            for idx in range(32):
                yield f"chunk-{idx:03d}:{'x' * 1000}\n"
                await asyncio.sleep(0)

        return Response.stream(chunk_stream(), media_type="application/octet-stream")


# Define filler helper to register 500 routes
def _build_filler_handler(slot: int):
    async def _filler(self, ctx: RequestCtx):
        return Response.json({"slot": slot})

    _filler.__name__ = f"route_filler_{slot}"
    return GET(f"/route/filler/r{slot}")(_filler)


for _slot in range(500):
    setattr(BenchmarkController, f"route_filler_{_slot}", _build_filler_handler(_slot))
