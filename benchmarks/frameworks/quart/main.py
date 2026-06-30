from __future__ import annotations

import asyncio
import json
import os
import random

from quart import Quart, jsonify, request
from quart.wrappers import Response

from benchmarks.frameworks.shared import (
    LARGE_PAYLOAD,
    UserProfileModel,
    get_db_connection,
    jinja_env,
)

app = Quart(__name__)

# Dynamic Middleware
layers_count = int(os.environ.get("MIDDLEWARE_LAYERS", "0"))
for i in range(layers_count):

    @app.before_request
    async def dummy_before(layer_id=i):
        # minor work
        request.routing_exception = None


@app.route("/health")
async def health():
    return "ok"


@app.route("/plaintext")
async def plaintext():
    return "Hello, World!"


@app.route("/json")
async def json_endpoint():
    return jsonify({"message": "Hello, World!"})


@app.route("/json/large")
async def json_large():
    return jsonify(LARGE_PAYLOAD)


@app.route("/db")
async def db_single():
    async with await get_db_connection() as db:
        row_id = random.randint(1, 10000)
        async with db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,)) as cursor:
            row = await cursor.fetchone()
            return jsonify({"id": row["id"], "randomNumber": row["randomNumber"]})


@app.route("/queries")
async def db_queries():
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
    return jsonify(results)


@app.route("/updates")
async def db_updates():
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
    return jsonify(results)


@app.route("/fortunes")
async def fortunes():
    async with await get_db_connection() as db, db.execute("SELECT id, message FROM fortune") as cursor:
        rows = await cursor.fetchall()
        fortunes_list = [{"id": r["id"], "message": r["message"]} for r in rows]

    fortunes_list.append({"id": 0, "message": "Additional fortune added at runtime."})
    fortunes_list.sort(key=lambda x: x["message"])

    template = jinja_env.get_template("fortunes.html")
    rendered = template.render(fortunes=fortunes_list)
    return Response(rendered, mimetype="text/html")


CACHE_STORE = {i: random.randint(1, 10000) for i in range(1, 10001)}


@app.route("/cached")
async def cached_test():
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
    return jsonify(results)


@app.route("/validation/pydantic", methods=["POST"])
async def validation_pydantic():
    data = await request.get_json()
    payload = UserProfileModel.model_validate(data)
    return jsonify({"ok": True, "username": payload.username})


@app.route("/route/static")
async def route_static():
    return jsonify({"route": "static"})


@app.route("/route/params/<int:user_id>/orders/<int:order_id>")
async def route_params(user_id: int, order_id: int):
    return jsonify({"user_id": user_id, "order_id": order_id})


# Dependency Injection Simulation
@app.route("/di")
async def di_chain():
    return jsonify({"value": (21 + 11) * 2})


@app.route("/body/multipart", methods=["POST"])
async def body_multipart():
    files = await request.files
    upload_file = files.get("file")
    if upload_file:
        content = upload_file.read()
        return jsonify({"filename": upload_file.filename, "size": len(content)})
    return jsonify({"filename": "unknown", "size": 0})


@app.route("/response/stream")
async def response_stream():
    async def chunk_stream():
        for idx in range(32):
            yield f"chunk-{idx:03d}:{'x' * 1000}\n"
            await asyncio.sleep(0)

    return Response(chunk_stream(), mimetype="application/octet-stream")


# WebSocket Echo
@app.websocket("/ws/echo")
async def ws_echo():
    from quart import websocket

    try:
        while True:
            msg = await websocket.receive()
            payload = json.loads(msg)
            await websocket.send(json.dumps({"id": payload.get("id"), "echo": payload.get("payload")}))
    except Exception:
        pass


# Filler routes to benchmark large route tables
for slot in range(500):

    @app.route(f"/route/filler/r{slot}", endpoint=f"filler_{slot}")
    async def filler(slot_id=slot):
        return jsonify({"slot": slot_id})
