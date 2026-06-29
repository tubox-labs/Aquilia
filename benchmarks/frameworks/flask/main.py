from __future__ import annotations

import os
import random
import sqlite3
import time
from flask import Flask, request, jsonify, make_response
from asgiref.wsgi import WsgiToAsgi

from benchmarks.frameworks.shared import (
    DB_PATH, LARGE_PAYLOAD, SAMPLE_TEXT_PATH,
    UserProfileDataclass, jinja_env
)

app = Flask("Flask-Benchmark")

# Dynamic Middleware
layers_count = int(os.environ.get("MIDDLEWARE_LAYERS", "0"))
for i in range(layers_count):
    @app.before_request
    def dummy_before(layer_id=i):
        # minor work
        pass

@app.route("/health")
def health():
    return "ok"

@app.route("/plaintext")
def plaintext():
    return "Hello, World!"

@app.route("/json")
def json_endpoint():
    return jsonify({"message": "Hello, World!"})

@app.route("/json/large")
def json_large():
    return jsonify(LARGE_PAYLOAD)

def get_sync_db():
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn

@app.route("/db")
def db_single():
    with get_sync_db() as db:
        row_id = random.randint(1, 10000)
        cursor = db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,))
        row = cursor.fetchone()
        return jsonify({"id": row["id"], "randomNumber": row["randomNumber"]})

@app.route("/queries")
def db_queries():
    queries = request.args.get("queries", "1")
    try:
        q_val = int(queries)
    except ValueError:
        q_val = 1
    q_val = max(1, min(500, q_val))

    results = []
    with get_sync_db() as db:
        for _ in range(q_val):
            row_id = random.randint(1, 10000)
            cursor = db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,))
            row = cursor.fetchone()
            results.append({"id": row["id"], "randomNumber": row["randomNumber"]})
    return jsonify(results)

@app.route("/updates")
def db_updates():
    queries = request.args.get("queries", "1")
    try:
        q_val = int(queries)
    except ValueError:
        q_val = 1
    q_val = max(1, min(500, q_val))

    results = []
    with get_sync_db() as db:
        for _ in range(q_val):
            row_id = random.randint(1, 10000)
            new_num = random.randint(1, 10000)
            cursor = db.execute("SELECT id, randomNumber FROM world WHERE id = ?", (row_id,))
            row = cursor.fetchone()
            db.execute("UPDATE world SET randomNumber = ? WHERE id = ?", (new_num, row_id))
            results.append({"id": row_id, "randomNumber": new_num})
        db.commit()
    return jsonify(results)

@app.route("/fortunes")
def fortunes():
    with get_sync_db() as db:
        cursor = db.execute("SELECT id, message FROM fortune")
        rows = cursor.fetchall()
        fortunes_list = [{"id": r["id"], "message": r["message"]} for r in rows]
    
    fortunes_list.append({"id": 0, "message": "Additional fortune added at runtime."})
    fortunes_list.sort(key=lambda x: x["message"])
    
    template = jinja_env.get_template("fortunes.html")
    rendered = template.render(fortunes=fortunes_list)
    return make_response(rendered)

CACHE_STORE = {i: random.randint(1, 10000) for i in range(1, 10001)}

@app.route("/cached")
def cached_test():
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
            with get_sync_db() as db:
                cursor = db.execute("SELECT randomNumber FROM world WHERE id = ?", (row_id,))
                row = cursor.fetchone()
                val = row["randomNumber"]
                CACHE_STORE[row_id] = val
        results.append({"id": row_id, "randomNumber": val})
    return jsonify(results)

@app.route("/validation/dataclass", methods=["POST"])
def validation_dataclass():
    data = request.get_json()
    payload = UserProfileDataclass.from_dict(data)
    return jsonify({"ok": True, "username": payload.username})

@app.route("/route/static")
def route_static():
    return jsonify({"route": "static"})

@app.route("/route/params/<int:user_id>/orders/<int:order_id>")
def route_params(user_id: int, order_id: int):
    return jsonify({"user_id": user_id, "order_id": order_id})

# Dependency Injection Simulation
@app.route("/di")
def di_chain():
    return jsonify({"value": (21 + 11) * 2})

@app.route("/body/multipart", methods=["POST"])
def body_multipart():
    upload_file = request.files.get("file")
    if upload_file:
        content = upload_file.read()
        return jsonify({"filename": upload_file.filename, "size": len(content)})
    return jsonify({"filename": "unknown", "size": 0})

@app.route("/response/stream")
def response_stream():
    def chunk_stream():
        for idx in range(32):
            yield f"chunk-{idx:03d}:{'x'*1000}\n"
            # Since this is sync generator, sleep for a tiny bit
            time.sleep(0.001)
    return make_response(chunk_stream())

# WebSocket is not supported for Flask WSGI in standard ASGI adapter
# without extra socket extensions.

# Filler routes to benchmark large route tables
for slot in range(500):
    @app.route(f"/route/filler/r{slot}", endpoint=f"filler_{slot}")
    def filler(slot_id=slot):
        return jsonify({"slot": slot_id})

# Adapt Flask WSGI app to ASGI using asgiref
asgi_app = WsgiToAsgi(app)
