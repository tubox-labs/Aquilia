from __future__ import annotations

import asyncio
import os
import random
from typing import Any

from litestar import Litestar, WebSocket, get, post, websocket
from litestar.datastructures import UploadFile
from litestar.enums import MediaType
from litestar.response import Stream

from benchmarks.frameworks.shared import (
    LARGE_PAYLOAD,
    UserProfileModel,
    get_db_connection,
    jinja_env,
)


@get("/health", media_type=MediaType.TEXT)
def health() -> str:
    return "ok"


@get("/plaintext", media_type=MediaType.TEXT)
def plaintext() -> str:
    return "Hello, World!"


@get("/json")
def json_endpoint() -> dict[str, str]:
    return {"message": "Hello, World!"}


@get("/json/large")
def json_large() -> dict[str, Any]:
    return LARGE_PAYLOAD


@get("/db")
async def db_single() -> dict[str, Any]:
    async with await get_db_connection() as db:
        row_id = random.randint(1, 10000)
        async with db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,)) as cursor:
            row = await cursor.fetchone()
            return {"id": row["id"], "randomNumber": row["randomNumber"]}


@get("/queries")
async def db_queries(queries: str = "1") -> list[dict[str, Any]]:
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


@get("/updates")
async def db_updates(queries: str = "1") -> list[dict[str, Any]]:
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
    return results


@get("/fortunes", media_type=MediaType.HTML)
async def fortunes() -> str:
    async with await get_db_connection() as db, db.execute("SELECT id, message FROM fortune") as cursor:
        rows = await cursor.fetchall()
        fortunes_list = [{"id": r["id"], "message": r["message"]} for r in rows]

    fortunes_list.append({"id": 0, "message": "Additional fortune added at runtime."})
    fortunes_list.sort(key=lambda x: x["message"])

    template = jinja_env.get_template("fortunes.html")
    rendered = template.render(fortunes=fortunes_list)
    return rendered


CACHE_STORE = {i: random.randint(1, 10000) for i in range(1, 10001)}


@get("/cached")
async def cached_test(queries: str = "1") -> list[dict[str, Any]]:
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
    return results


@post("/validation/pydantic")
def validation_pydantic(data: UserProfileModel) -> dict[str, Any]:
    return {"ok": True, "username": data.username}


@get("/route/static")
def route_static() -> dict[str, str]:
    return {"route": "static"}


@get("/route/params/{user_id:int}/orders/{order_id:int}")
def route_params(user_id: int, order_id: int) -> dict[str, int]:
    return {"user_id": user_id, "order_id": order_id}


# Dependency Injection Simulation
def dep_resolve():
    return (21 + 11) * 2


@get("/di")
def di_chain() -> dict[str, int]:
    return {"value": dep_resolve()}


@post("/body/multipart")
async def body_multipart(data: dict[str, Any]) -> dict[str, Any]:
    upload_file = data.get("file")
    if isinstance(upload_file, UploadFile):
        content = await upload_file.read()
        return {"filename": upload_file.filename, "size": len(content)}
    return {"filename": "unknown", "size": 0}


@get("/response/stream")
def response_stream() -> Stream:
    async def chunk_stream():
        for idx in range(32):
            yield f"chunk-{idx:03d}:{'x' * 1000}\n"
            await asyncio.sleep(0)

    return Stream(chunk_stream())


@websocket("/ws/echo")
async def ws_echo(socket: WebSocket) -> None:
    await socket.accept()
    while True:
        payload = await socket.receive_json()
        await socket.send_json({"id": payload.get("id"), "echo": payload.get("payload")})


# Setup app handlers
route_handlers = [
    health,
    plaintext,
    json_endpoint,
    json_large,
    db_single,
    db_queries,
    db_updates,
    fortunes,
    cached_test,
    validation_pydantic,
    route_static,
    route_params,
    di_chain,
    body_multipart,
    response_stream,
    ws_echo,
]

# Register filler routes
for slot in range(500):
    # Dynamic handler builder
    exec(f"""
@get("/route/filler/r{slot}")
def filler_{slot}() -> dict[str, int]:
    return {{"slot": {slot}}}
route_handlers.append(filler_{slot})
""")


# Custom Middleware wrapper
class LitestarDummyMiddleware:
    def __init__(self, app: Any, layer_id: int) -> None:
        self.app = app
        self.layer_id = layer_id

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] == "http":
            scope["litestar_layer"] = self.layer_id
        await self.app(scope, receive, send)


layers_count = int(os.environ.get("MIDDLEWARE_LAYERS", "0"))
middleware_stack = []
for i in range(layers_count):
    middleware_stack.append(lambda app, layer_id=i: LitestarDummyMiddleware(app, layer_id))

app = Litestar(route_handlers=route_handlers, middleware=middleware_stack)
