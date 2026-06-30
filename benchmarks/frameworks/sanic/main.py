from __future__ import annotations

import asyncio
import os
import random

from sanic import Sanic, Websocket
from sanic.response import html, json, text

from benchmarks.frameworks.shared import (
    LARGE_PAYLOAD,
    UserProfileModel,
    get_db_connection,
    jinja_env,
)

app = Sanic("Sanic-Benchmark")

# Dynamic Middleware
layers_count = int(os.environ.get("MIDDLEWARE_LAYERS", "0"))
for i in range(layers_count):

    @app.middleware("request")
    async def dummy_middleware(request, layer_id=i):
        # minor work
        request.ctx.layer_id = layer_id


@app.get("/health")
async def health(request):
    return text("ok")


@app.get("/plaintext")
async def plaintext(request):
    return text("Hello, World!")


@app.get("/json")
async def json_endpoint(request):
    return json({"message": "Hello, World!"})


@app.get("/json/large")
async def json_large(request):
    return json(LARGE_PAYLOAD)


@app.get("/db")
async def db_single(request):
    async with await get_db_connection() as db:
        row_id = random.randint(1, 10000)
        async with db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,)) as cursor:
            row = await cursor.fetchone()
            return json({"id": row["id"], "randomNumber": row["randomNumber"]})


@app.get("/queries")
async def db_queries(request):
    queries = request.args.get("queries", "1")
    try:
        q_val = int(queries)
    except ValueError:
        q_val = 1
    q_val = max(1, min(500, q_val))

    results = []
    async with await get_db_connection() as db:
        for _ in range(q_val):
            row_id = random.randint(1, 10000)
            async with db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,)) as cursor:
                row = await cursor.fetchone()
                results.append({"id": row["id"], "randomNumber": row["randomNumber"]})
    return json(results)


@app.get("/updates")
async def db_updates(request):
    queries = request.args.get("queries", "1")
    try:
        q_val = int(queries)
    except ValueError:
        q_val = 1
    q_val = max(1, min(500, q_val))

    results = []
    async with await get_db_connection() as db:
        for _ in range(q_val):
            row_id = random.randint(1, 10000)
            new_num = random.randint(1, 10000)
            async with db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,)) as cursor:
                row = await cursor.fetchone()
            await db.execute("UPDATE world SET randomNumber = ? WHERE id = ?", (new_num, row_id))
            results.append({"id": row_id, "randomNumber": new_num})
        await db.commit()
    return json(results)


@app.get("/fortunes")
async def fortunes(request):
    async with await get_db_connection() as db, db.execute("SELECT id, message FROM fortune") as cursor:
        rows = await cursor.fetchall()
        fortunes_list = [{"id": r["id"], "message": r["message"]} for r in rows]

    fortunes_list.append({"id": 0, "message": "Additional fortune added at runtime."})
    fortunes_list.sort(key=lambda x: x["message"])

    template = jinja_env.get_template("fortunes.html")
    rendered = template.render(fortunes=fortunes_list)
    return html(rendered)


CACHE_STORE = {i: random.randint(1, 10000) for i in range(1, 10001)}


@app.get("/cached")
async def cached_test(request):
    queries = request.args.get("queries", "1")
    try:
        q_val = int(queries)
    except ValueError:
        q_val = 1
    q_val = max(1, min(500, q_val))

    results = []
    for _ in range(q_val):
        row_id = random.randint(1, 10000)
        val = CACHE_STORE.get(row_id)
        if val is None:
            async with await get_db_connection() as db:
                async with db.execute("SELECT randomNumber FROM world WHERE id = ?", (row_id,)) as cursor:
                    row = await cursor.fetchone()
                    val = row["randomNumber"]
                    CACHE_STORE[row_id] = val
        results.append({"id": row_id, "randomNumber": val})
    return json(results)


@app.post("/validation/pydantic")
async def validation_pydantic(request):
    payload = UserProfileModel.model_validate(request.json)
    return json({"ok": True, "username": payload.username})


@app.get("/route/static")
async def route_static(request):
    return json({"route": "static"})


@app.get("/route/params/<user_id:int>/orders/<order_id:int>")
async def route_params(request, user_id: int, order_id: int):
    return json({"user_id": user_id, "order_id": order_id})


# Dependency Injection Simulation
@app.get("/di")
async def di_chain(request):
    return json({"value": (21 + 11) * 2})


@app.post("/body/multipart")
async def body_multipart(request):
    upload_file = request.files.get("file")
    if upload_file:
        return json({"filename": upload_file.name, "size": len(upload_file.body)})
    return json({"filename": "unknown", "size": 0})


@app.get("/response/stream")
async def response_stream(request):
    async def chunk_stream(response):
        for idx in range(32):
            await response.write(f"chunk-{idx:03d}:{'x' * 1000}\n")
            await asyncio.sleep(0)

    return app.response_like(chunk_stream, content_type="application/octet-stream")


@app.websocket("/ws/echo")
async def ws_echo(request, ws: Websocket):
    try:
        while True:
            msg = await ws.recv()
            payload = json.loads(msg)
            await ws.send(json.dumps({"id": payload.get("id"), "echo": payload.get("payload")}))
    except Exception:
        pass


# Filler routes to benchmark large route tables
for slot in range(500):

    @app.get(f"/route/filler/r{slot}", name=f"filler_{slot}")
    async def filler(request, slot_id=slot):
        return json({"slot": slot_id})
