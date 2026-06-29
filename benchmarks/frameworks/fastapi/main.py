from __future__ import annotations

import asyncio
import os
import random
from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, StreamingResponse
from starlette.websockets import WebSocketDisconnect
from starlette.staticfiles import StaticFiles

from benchmarks.frameworks.shared import (
    DB_PATH, LARGE_PAYLOAD, SAMPLE_TEXT_PATH,
    UserProfileModel, VALIDATION_INPUT, get_db_connection, jinja_env
)

app = FastAPI(title="FastAPI Benchmark App")

# Dynamic Middleware Pipeline setup
layers_count = int(os.environ.get("MIDDLEWARE_LAYERS", "0"))
for i in range(layers_count):
    # We define inline middleware layers to simulate middleware overhead
    @app.middleware("http")
    async def dummy_middleware(request: Request, call_next, layer_id=i):
        # Do minor work
        request.state.last_layer = layer_id
        return await call_next(request)

@app.get("/health", response_class=PlainTextResponse)
async def health():
    return "ok"

@app.get("/plaintext", response_class=PlainTextResponse)
async def plaintext():
    return "Hello, World!"

@app.get("/json")
async def json_endpoint():
    return {"message": "Hello, World!"}

@app.get("/json/large")
async def json_large():
    return LARGE_PAYLOAD

@app.get("/db")
async def db_single():
    async with await get_db_connection() as db:
        row_id = random.randint(1, 10000)
        async with db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,)) as cursor:
            row = await cursor.fetchone()
            return {"id": row["id"], "randomNumber": row["randomNumber"]}

@app.get("/queries")
async def db_queries(queries: str = "1"):
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
    return results

@app.get("/updates")
async def db_updates(queries: str = "1"):
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
            # Read-modify-write
            async with db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,)) as cursor:
                row = await cursor.fetchone()
            await db.execute("UPDATE world SET randomNumber = ? WHERE id = ?", (new_num, row_id))
            results.append({"id": row_id, "randomNumber": new_num})
        await db.commit()
    return results

@app.get("/fortunes", response_class=HTMLResponse)
async def fortunes():
    async with await get_db_connection() as db:
        async with db.execute("SELECT id, message FROM fortune") as cursor:
            rows = await cursor.fetchall()
            fortunes_list = [{"id": r["id"], "message": r["message"]} for r in rows]
    
    fortunes_list.append({"id": 0, "message": "Additional fortune added at runtime."})
    fortunes_list.sort(key=lambda x: x["message"])
    
    template = jinja_env.get_template("fortunes.html")
    rendered = template.render(fortunes=fortunes_list)
    return HTMLResponse(content=rendered)

# Caching Test (using in-memory dict as cache store)
CACHE_STORE = {i: random.randint(1, 10000) for i in range(1, 10001)}

@app.get("/cached")
async def cached_test(queries: str = "1"):
    try:
        q_val = int(queries)
    except ValueError:
        q_val = 1
    q_val = max(1, min(500, q_val))
    
    results = []
    for _ in range(q_val):
        row_id = random.randint(1, 10000)
        # Check cache, fallback to db
        val = CACHE_STORE.get(row_id)
        if val is None:
            async with await get_db_connection() as db:
                async with db.execute("SELECT randomNumber FROM world WHERE id = ?", (row_id,)) as cursor:
                    row = await cursor.fetchone()
                    val = row["randomNumber"]
                    CACHE_STORE[row_id] = val
        results.append({"id": row_id, "randomNumber": val})
    return results

# Pydantic Validation Endpoint
@app.post("/validation/pydantic")
async def validation_pydantic(payload: UserProfileModel):
    return {"ok": True, "username": payload.username}

# Route Resolution dummy routes
def register_filler_routes(count: int = 500):
    for slot in range(count):
        path = f"/route/filler/r{slot}"
        @app.get(path)
        async def filler(slot_id=slot):
            return {"slot": slot_id}

register_filler_routes()

@app.get("/route/static")
async def route_static():
    return {"route": "static"}

@app.get("/route/params/{user_id}/orders/{order_id}")
async def route_params(user_id: int, order_id: int):
    return {"user_id": user_id, "order_id": order_id}

# Dependency Injection resolution path
def dep_leaf() -> int:
    return 21

def dep_mid(leaf: int = Depends(dep_leaf)) -> int:
    return leaf + 11

def dep_top(mid: int = Depends(dep_mid)) -> int:
    return mid * 2

@app.get("/di")
async def di_chain(result: int = Depends(dep_top)):
    return {"value": result}

# Multipart upload parsing
@app.post("/body/multipart")
async def body_multipart(file: UploadFile = File(...)):
    content = await file.read()
    return {"filename": file.filename, "size": len(content)}

# Response streaming
@app.get("/response/stream")
async def response_stream():
    async def chunk_stream():
        for idx in range(32):
            yield f"chunk-{idx:03d}:{'x'*1000}\n"
            await asyncio.sleep(0)
    return StreamingResponse(chunk_stream(), media_type="application/octet-stream")

# WebSocket Echo
@app.websocket("/ws/echo")
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
