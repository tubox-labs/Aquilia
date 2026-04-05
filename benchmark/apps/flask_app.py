from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from asgiref.wsgi import WsgiToAsgi
from flask import Flask, Response, jsonify, request, send_file, stream_with_context

from benchmark.apps.shared_payload import LARGE_PAYLOAD, SAMPLE_TEXT_PATH, build_stream_chunk

ASSETS_DIR = Path(__file__).resolve().parent / "assets"

app = Flask(__name__, static_folder=str(ASSETS_DIR), static_url_path="/static")


class LeafService:
    def value(self) -> int:
        return 21


class MidService:
    def __init__(self, leaf: LeafService):
        self.leaf = leaf

    def value(self) -> int:
        return self.leaf.value() + 11


class TopService:
    def __init__(self, mid: MidService):
        self.mid = mid

    def value(self) -> int:
        return self.mid.value() * 2


def _resolve_chain() -> TopService:
    leaf = LeafService()
    mid = MidService(leaf)
    return TopService(mid)


def _make_noop_layer() -> Any:
    def noop_layer() -> None:
        if request.path.startswith("/middleware"):
            current = int(request.environ.get("bench.noop_layers", 0))
            request.environ["bench.noop_layers"] = current + 1

    return noop_layer


for _ in range(5):
    app.before_request(_make_noop_layer())


@app.get("/health")
def health() -> Response:
    return Response("ok", mimetype="text/plain")


@app.get("/json/simple")
def json_simple() -> Response:
    return jsonify({"ok": True, "framework": "flask", "value": 42})


@app.get("/json/large")
def json_large() -> Response:
    return jsonify(LARGE_PAYLOAD)


@app.get("/di")
def di_chain() -> Response:
    service = _resolve_chain()
    return jsonify({"value": service.value()})


@app.get("/middleware/noop")
def middleware_noop() -> Response:
    return jsonify({"ok": True, "layers": int(request.environ.get("bench.noop_layers", 0))})


@app.get("/route/static")
def route_static() -> Response:
    return jsonify({"route": "static"})


@app.get("/route/params/<int:user_id>/orders/<int:order_id>")
def route_params(user_id: int, order_id: int) -> Response:
    return jsonify({"user_id": user_id, "order_id": order_id})


@app.post("/body/json")
def body_json() -> Response:
    payload = request.get_json(silent=True) or {}
    return jsonify({"keys": len(payload.keys()), "size": len(str(payload))})


@app.post("/body/form")
def body_form() -> Response:
    quantity = int(request.form.get("quantity", "0"))
    return jsonify(
        {
            "name": request.form.get("name", ""),
            "category": request.form.get("category", ""),
            "quantity": quantity,
        }
    )


@app.post("/body/multipart")
def body_multipart() -> Response:
    upload = request.files.get("file")
    if upload is None:
        return jsonify({"error": "file missing"}), 400

    content = upload.read()
    return jsonify({"filename": upload.filename, "size": len(content)})


@app.get("/response/text")
def response_text() -> Response:
    return Response("benchmark-text-response", mimetype="text/plain")


@app.get("/response/stream")
def response_stream() -> Response:
    @stream_with_context
    def generator():
        for idx in range(32):
            yield build_stream_chunk(idx)

    return Response(generator(), mimetype="application/octet-stream")


@app.get("/response/file")
def response_file() -> Response:
    return send_file(SAMPLE_TEXT_PATH, mimetype="text/plain")


@app.get("/error/handled")
def error_handled() -> Response:
    return jsonify({"error": "handled benchmark error"}), 400


@app.get("/error/unhandled")
def error_unhandled() -> Response:
    raise RuntimeError("unhandled benchmark error")


@app.get("/compute/async")
def compute_async() -> Response:
    delay_ms = float(request.args.get("delay_ms", "5"))
    time.sleep(max(0.0, delay_ms) / 1000.0)
    return jsonify({"delay_ms": delay_ms})


def _register_filler_routes(count: int = 200) -> None:
    for slot in range(count):
        path = f"/route/filler/r{slot}"

        def filler(slot: int = slot) -> Response:
            return jsonify({"slot": slot})

        app.add_url_rule(path, endpoint=f"filler_{slot}", view_func=filler, methods=["GET"])


_register_filler_routes()
asgi_app = WsgiToAsgi(app)
