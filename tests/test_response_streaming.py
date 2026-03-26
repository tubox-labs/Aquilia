from __future__ import annotations

from types import SimpleNamespace

from aquilia.asgi import ASGIAdapter
from aquilia.middleware import CompressionMiddleware
from aquilia.response import Response


class _DummyRouter:
    def match_sync(self, path, method, api_version=None):
        return None

    def get_allowed_methods(self, path):
        return []


class _DummyStack:
    def build_handler(self, final_handler):
        return final_handler


async def test_asgi_adapter_passes_request_to_send_asgi():
    adapter = ASGIAdapter(
        controller_router=_DummyRouter(),
        controller_engine=SimpleNamespace(),
        middleware_stack=_DummyStack(),
    )

    captured = {}

    class _DummyResponse:
        async def send_asgi(self, send, request=None):
            captured["request"] = request

    async def _handler(request, ctx):
        return _DummyResponse()

    adapter._cached_middleware_chain = _handler

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/",
        "headers": [],
        "query_string": b"",
    }

    async def _receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def _send(_msg):
        return None

    await adapter.handle_http(scope, _receive, _send)

    req = captured.get("request")
    assert req is not None
    assert req.method == "GET"
    assert req.path == "/"


async def test_file_range_request_streams_partial_content(tmp_path):
    f = tmp_path / "blob.bin"
    f.write_bytes(b"0123456789")

    resp = Response.file(str(f))
    request = SimpleNamespace(headers={"range": "bytes=2-5"})

    messages = []

    async def _send(msg):
        messages.append(msg)

    await resp.send_asgi(_send, request)

    start = messages[0]
    assert start["type"] == "http.response.start"
    assert start["status"] == 206

    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    assert body == b"2345"


async def test_sse_stream_emits_error_frame_on_midstream_failure():
    async def _broken_stream():
        yield b"data: ok\n\n"
        raise RuntimeError("boom")

    resp = Response.stream(_broken_stream(), media_type="text/event-stream; charset=utf-8")

    messages = []

    async def _send(msg):
        messages.append(msg)

    await resp.send_asgi(_send)

    body_chunks = [m.get("body", b"") for m in messages if m["type"] == "http.response.body"]
    assert any(b"data: ok" in chunk for chunk in body_chunks)
    assert any(b"event: error" in chunk for chunk in body_chunks)
    assert messages[-1]["type"] == "http.response.body"
    assert messages[-1]["more_body"] is False


async def test_compression_middleware_skips_sync_streaming_content():
    stream_iter = iter([b"alpha", b"beta"])
    response = Response.stream(stream_iter)

    mw = CompressionMiddleware(minimum_size=1)

    class _Req:
        def header(self, name, default=""):
            if name == "accept-encoding":
                return "gzip"
            return default

    async def _next(_req, _ctx):
        return response

    result = await mw(_Req(), SimpleNamespace(), _next)

    assert result is response
    assert result._content is stream_iter
    assert "content-encoding" not in result.headers
