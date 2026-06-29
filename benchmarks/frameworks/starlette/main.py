from __future__ import annotations

import asyncio
import os
import random
import json
from starlette.applications import Starlette
from starlette.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse
from starlette.routing import Route, WebSocketRoute
from starlette.middleware import Middleware
from starlette.websockets import WebSocket, WebSocketDisconnect

from benchmarks.frameworks.shared import (
    DB_PATH, LARGE_PAYLOAD, SAMPLE_TEXT_PATH,
    UserProfileModel, get_db_connection, jinja_env
)

async def health(request):
    return PlainTextResponse("ok")

async def plaintext(request):
    return PlainTextResponse("Hello, World!")

async def json_endpoint(request):
    return JSONResponse({"message": "Hello, World!"})

async def json_large(request):
    return JSONResponse(LARGE_PAYLOAD)

async def db_single(request):
    async with await get_db_connection() as db:
        row_id = random.randint(1, 10000)
        async with db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,)) as cursor:
            row = await cursor.fetchone()
            return JSONResponse({"id": row["id"], "randomNumber": row["randomNumber"]})

async def db_queries(request):
    queries = request.query_params.get("queries", "1")
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
    return JSONResponse(results)

async def db_updates(request):
    queries = request.query_params.get("queries", "1")
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
    return JSONResponse(results)

async def fortunes(request):
    async with await get_db_connection() as db:
        async with db.execute("SELECT id, message FROM fortune") as cursor:
            rows = await cursor.fetchall()
            fortunes_list = [{"id": r["id"], "message": r["message"]} for r in rows]
    
    fortunes_list.append({"id": 0, "message": "Additional fortune added at runtime."})
    fortunes_list.sort(key=lambda x: x["message"])
    
    template = jinja_env.get_template("fortunes.html")
    rendered = template.render(fortunes=fortunes_list)
    return HTMLResponse(content=rendered)

CACHE_STORE = {i: random.randint(1, 10000) for i in range(1, 10001)}

async def cached_test(request):
    queries = request.query_params.get("queries", "1")
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
    return JSONResponse(results)

async def validation_pydantic(request):
    body_bytes = await request.body()
    data = json.loads(body_bytes)
    payload = UserProfileModel.model_validate(data)
    return JSONResponse({"ok": True, "username": payload.username})

async def route_static(request):
    return JSONResponse({"route": "static"})

async def route_params(request):
    user_id = int(request.path_params["user_id"])
    order_id = int(request.path_params["order_id"])
    return JSONResponse({"user_id": user_id, "order_id": order_id})

# Simulated Dependency Injection
def dep_resolve():
    leaf = 21
    mid = leaf + 11
    top = mid * 2
    return top

async def di_chain(request):
    res = dep_resolve()
    return JSONResponse({"value": res})

async def body_multipart(request):
    async with request.form() as form:
        upload_file = form["file"]
        content = await upload_file.read()
        return JSONResponse({"filename": upload_file.filename, "size": len(content)})

async def response_stream(request):
    async def chunk_stream():
        for idx in range(32):
            yield f"chunk-{idx:03d}:{'x'*1000}\n"
            await asyncio.sleep(0)
    return StreamingResponse(chunk_stream(), media_type="application/octet-stream")

async def ws_echo(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            payload = await ws.receive_json()
            await ws.send_json({
                "id": payload.get("id"),
                "echo": payload.get("payload")
            })
    except WebSocketDisconnect:
        pass

# Define Base routes
routes = [
    Route("/health", health),
    Route("/plaintext", plaintext),
    Route("/json", json_endpoint),
    Route("/json/large", json_large),
    Route("/db", db_single),
    Route("/queries", db_queries),
    Route("/updates", db_updates),
    Route("/fortunes", fortunes),
    Route("/cached", cached_test),
    Route("/validation/pydantic", validation_pydantic, methods=["POST"]),
    Route("/route/static", route_static),
    Route("/route/params/{user_id:int}/orders/{order_id:int}", route_params),
    Route("/di", di_chain),
    Route("/body/multipart", body_multipart, methods=["POST"]),
    Route("/response/stream", response_stream),
    WebSocketRoute("/ws/echo", ws_echo),
]

# Filler routes to benchmark large route tables
for slot in range(500):
    routes.append(Route(f"/route/filler/r{slot}", lambda r, s=slot: JSONResponse({"slot": s})))

# Custom Middleware class to dynamic wrap
class DummyMiddleware:
    def __init__(self, app, layer_id):
        self.app = app
        self.layer_id = layer_id
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http":
            # simulate minor work
            scope["starlette_layer"] = self.layer_id
        await self.app(scope, receive, send)

layers_count = int(os.environ.get("MIDDLEWARE_LAYERS", "0"))
middleware_stack = []
for i in range(layers_count):
    middleware_stack.append(Middleware(DummyMiddleware, layer_id=i))

app = Starlette(routes=routes, middleware=middleware_stack)
