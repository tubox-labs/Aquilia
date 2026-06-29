from __future__ import annotations

import asyncio
import os
import random
import json
import falcon
import falcon.asgi

from benchmarks.frameworks.shared import (
    DB_PATH, LARGE_PAYLOAD, SAMPLE_TEXT_PATH,
    UserProfileModel, get_db_connection, jinja_env
)

class HealthResource:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.text = "ok"

class PlaintextResource:
    async def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.text = "Hello, World!"

class JsonResource:
    async def on_get(self, req, resp):
        resp.media = {"message": "Hello, World!"}

class LargeJsonResource:
    async def on_get(self, req, resp):
        resp.media = LARGE_PAYLOAD

class DbSingleResource:
    async def on_get(self, req, resp):
        async with await get_db_connection() as db:
            row_id = random.randint(1, 10000)
            async with db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,)) as cursor:
                row = await cursor.fetchone()
                resp.media = {"id": row["id"], "randomNumber": row["randomNumber"]}

class DbQueriesResource:
    async def on_get(self, req, resp):
        queries = req.get_param("queries", default="1")
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
        resp.media = results

class DbUpdatesResource:
    async def on_get(self, req, resp):
        queries = req.get_param("queries", default="1")
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
        resp.media = results

class FortunesResource:
    async def on_get(self, req, resp):
        async with await get_db_connection() as db:
            async with db.execute("SELECT id, message FROM fortune") as cursor:
                rows = await cursor.fetchall()
                fortunes_list = [{"id": r["id"], "message": r["message"]} for r in rows]
        
        fortunes_list.append({"id": 0, "message": "Additional fortune added at runtime."})
        fortunes_list.sort(key=lambda x: x["message"])
        
        template = jinja_env.get_template("fortunes.html")
        rendered = template.render(fortunes=fortunes_list)
        resp.status = falcon.HTTP_200
        resp.content_type = falcon.MEDIA_HTML
        resp.text = rendered

CACHE_STORE = {i: random.randint(1, 10000) for i in range(1, 10001)}

class CachedResource:
    async def on_get(self, req, resp):
        queries = req.get_param("queries", default="1")
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
        resp.media = results

class ValidationResource:
    async def on_post(self, req, resp):
        data = await req.media
        payload = UserProfileModel.model_validate(data)
        resp.media = {"ok": True, "username": payload.username}

class RouteStaticResource:
    async def on_get(self, req, resp):
        resp.media = {"route": "static"}

class RouteParamsResource:
    async def on_get(self, req, resp, user_id, order_id):
        resp.media = {"user_id": int(user_id), "order_id": int(order_id)}

class DIResource:
    async def on_get(self, req, resp):
        resp.media = {"value": (21 + 11) * 2}

class MultipartResource:
    async def on_post(self, req, resp):
        # Read form parts manually
        form = await req.get_media()
        # Parse file from multipart
        filename = ""
        size = 0
        async for part in form:
            if part.name == "file":
                filename = part.filename
                # Read entire content of file stream
                content = await part.stream.read()
                size = len(content)
        resp.media = {"filename": filename, "size": size}

class ResponseStreamResource:
    async def on_get(self, req, resp):
        async def chunk_stream():
            for idx in range(32):
                yield f"chunk-{idx:03d}:{'x'*1000}\n".encode("utf-8")
                await asyncio.sleep(0)
        resp.status = falcon.HTTP_200
        resp.content_type = "application/octet-stream"
        resp.stream = chunk_stream()

class WsEchoResource:
    async def on_websocket(self, req, ws):
        await ws.accept()
        try:
            while True:
                msg = await ws.receive_media()
                await ws.send_media({
                    "id": msg.get("id"),
                    "echo": msg.get("payload")
                })
        except falcon.WebSocketDisconnected:
            pass

# Custom Middleware wrapper
class DummyMiddleware:
    def __init__(self, layer_id):
        self.layer_id = layer_id
    async def process_request(self, req, resp):
        # minor work
        req.context.layer_id = self.layer_id

layers_count = int(os.environ.get("MIDDLEWARE_LAYERS", "0"))
middleware_stack = []
for i in range(layers_count):
    middleware_stack.append(DummyMiddleware(layer_id=i))

app = falcon.asgi.App(middleware=middleware_stack)

app.add_route("/health", HealthResource())
app.add_route("/plaintext", PlaintextResource())
app.add_route("/json", JsonResource())
app.add_route("/json/large", LargeJsonResource())
app.add_route("/db", DbSingleResource())
app.add_route("/queries", DbQueriesResource())
app.add_route("/updates", DbUpdatesResource())
app.add_route("/fortunes", FortunesResource())
app.add_route("/cached", CachedResource())
app.add_route("/validation/pydantic", ValidationResource())
app.add_route("/route/static", RouteStaticResource())
app.add_route("/route/params/{user_id:int}/orders/{order_id:int}", RouteParamsResource())
app.add_route("/di", DIResource())
app.add_route("/body/multipart", MultipartResource())
app.add_route("/response/stream", ResponseStreamResource())
app.add_route("/ws/echo", WsEchoResource())

# Filler routes to benchmark large route tables
for slot in range(500):
    class FillerResource:
        def __init__(self, s):
            self.s = s
        async def on_get(self, req, resp):
            resp.media = {"slot": self.s}
    app.add_route(f"/route/filler/r{slot}", FillerResource(slot))
