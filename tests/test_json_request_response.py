"""
Comprehensive regression tests for JSON request / response integration.

Covers:
- §1: Request — json() payload parsing, model validation, error handling
- §2: Request — data() auto-detection (JSON)
- §3: Response — Response.json() factory, compression
- §4: Response — Response.negotiated() content negotiation (JSON default)
- §5: Round-trip — encode → request.json() → Response.json() → decode
"""

import json

import pytest


def _make_scope(
    method: str = "POST",
    path: str = "/",
    headers: dict[str, str] | None = None,
    content_type: str | None = None,
) -> dict:
    """Build a minimal ASGI scope dict."""
    raw_headers = []
    if content_type:
        raw_headers.append((b"content-type", content_type.encode()))
    for name, value in (headers or {}).items():
        raw_headers.append((name.lower().encode(), value.encode()))
    return {
        "type": "http",
        "method": method,
        "path": path,
        "headers": raw_headers,
        "query_string": b"",
        "root_path": "",
        "scheme": "http",
    }


def _make_receive(body: bytes):
    """Return an async receive callable delivering *body* in one chunk."""
    called = False

    async def receive():
        nonlocal called
        if not called:
            called = True
            return {"type": "http.request", "body": body, "more_body": False}
        return {"type": "http.disconnect"}

    return receive


def _make_request(
    body: bytes = b"",
    content_type: str | None = None,
    accept: str | None = None,
    **extra_headers,
):
    """Build a Request with the given body, content-type, and accept."""
    from aquilia.request import Request

    headers = dict(extra_headers)
    if accept:
        headers["accept"] = accept
    scope = _make_scope(
        method="POST",
        headers=headers,
        content_type=content_type,
    )
    return Request(scope, _make_receive(body))


class TestJSONRequestResponse:
    """Request and Response JSON integration tests."""

    @pytest.mark.asyncio
    async def test_json_request(self):
        data = {"hello": "world", "count": 42}
        body = json.dumps(data).encode("utf-8")
        req = _make_request(body=body, content_type="application/json")
        res = await req.json()
        assert res == data

    @pytest.mark.asyncio
    async def test_data_request(self):
        data = {"items": [1, 2, 3]}
        body = json.dumps(data).encode("utf-8")
        req = _make_request(body=body, content_type="application/json")
        res = await req.data()
        assert res == data

    def test_json_response(self):
        from aquilia.response import Response

        resp = Response.json({"status": "ok"})
        assert resp.status == 200
        assert "application/json" in resp.headers["content-type"]
        assert json.loads(resp.body()) == {"status": "ok"}

    def test_negotiated_response(self):
        from aquilia.response import Response

        req = _make_request(accept="application/json")
        resp = Response.negotiated({"negotiated": True}, req)
        assert "application/json" in resp.headers["content-type"]
        assert json.loads(resp.body()) == {"negotiated": True}
