from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, UploadFile, WebSocket
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, StreamingResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocketDisconnect

from benchmark.apps.shared_payload import LARGE_PAYLOAD, SAMPLE_TEXT_PATH, build_stream_chunk

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


class PathScopedNoopMiddleware(BaseHTTPMiddleware):
    """Apply predictable middleware work only on /middleware routes."""

    def __init__(self, app, layers: int = 5, path_prefix: str = "/middleware"):
        super().__init__(app)
        self.layers = layers
        self.path_prefix = path_prefix

    async def dispatch(self, request, call_next):
        if request.url.path.startswith(self.path_prefix):
            count = 0
            for _ in range(self.layers):
                count += 1
            request.state.noop_layers = count
        return await call_next(request)


app = FastAPI(title="FastAPI Benchmark App", version="1.0.0")
app.add_middleware(PathScopedNoopMiddleware, layers=5)


@app.exception_handler(RuntimeError)
async def runtime_error_handler(request: Request, exc: RuntimeError):
    return JSONResponse(status_code=500, content={"error": "internal", "detail": str(exc)})


@app.get("/health", response_class=PlainTextResponse)
async def health() -> str:
    return "ok"


@app.get("/json/simple")
async def json_simple() -> dict[str, Any]:
    return {"ok": True, "framework": "fastapi", "value": 42}


@app.get("/json/large")
async def json_large() -> dict[str, Any]:
    return LARGE_PAYLOAD


def dep_leaf() -> int:
    return 21


def dep_mid(leaf: int = Depends(dep_leaf)) -> int:
    return leaf + 11


def dep_top(mid: int = Depends(dep_mid)) -> int:
    return mid * 2


@app.get("/di")
async def di_chain(result: int = Depends(dep_top)) -> dict[str, int]:
    return {"value": result}


@app.get("/middleware/noop")
async def middleware_noop() -> dict[str, Any]:
    return {"ok": True}


@app.get("/route/static")
async def route_static() -> dict[str, str]:
    return {"route": "static"}


@app.get("/route/params/{user_id}/orders/{order_id}")
async def route_params(user_id: int, order_id: int) -> dict[str, int]:
    return {"user_id": user_id, "order_id": order_id}


@app.post("/body/json")
async def body_json(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "keys": len(payload.keys()),
        "size": len(str(payload)),
    }


@app.post("/body/form")
async def body_form(name: str = Form(...), category: str = Form(...), quantity: int = Form(...)) -> dict[str, Any]:
    return {
        "name": name,
        "category": category,
        "quantity": quantity,
    }


@app.post("/body/multipart")
async def body_multipart(file: UploadFile = File(...)) -> dict[str, Any]:  # noqa: B008
    content = await file.read()
    return {
        "filename": file.filename,
        "size": len(content),
    }


@app.get("/response/text", response_class=PlainTextResponse)
async def response_text() -> str:
    return "benchmark-text-response"


@app.get("/response/stream")
async def response_stream() -> StreamingResponse:
    async def chunk_stream():
        for idx in range(32):
            yield build_stream_chunk(idx)
            await asyncio.sleep(0)

    return StreamingResponse(chunk_stream(), media_type="application/octet-stream")


@app.get("/response/file")
async def response_file() -> FileResponse:
    return FileResponse(SAMPLE_TEXT_PATH, media_type="text/plain")


@app.get("/error/handled")
async def error_handled() -> dict[str, str]:
    raise HTTPException(status_code=400, detail="handled benchmark error")


@app.get("/error/unhandled")
async def error_unhandled() -> dict[str, str]:
    raise RuntimeError("unhandled benchmark error")


@app.get("/compute/async")
async def compute_async(delay_ms: float = 5.0) -> dict[str, float]:
    await asyncio.sleep(max(0.0, delay_ms) / 1000.0)
    return {"delay_ms": delay_ms}


@app.websocket("/ws/echo")
async def ws_echo(ws: WebSocket):
    await ws.accept()
    try:
        while True:
            payload = await ws.receive_json()
            await ws.send_json(
                {
                    "id": payload.get("id"),
                    "echo": payload.get("payload"),
                }
            )
    except WebSocketDisconnect:
        return


def _register_filler_routes(count: int = 200) -> None:
    for slot in range(count):
        path = f"/route/filler/r{slot}"

        async def filler(slot: int = slot) -> dict[str, int]:
            return {"slot": slot}

        app.add_api_route(path, filler, methods=["GET"])


_register_filler_routes()
app.mount("/static", app=StaticFiles(directory=ASSETS_DIR), name="static")
