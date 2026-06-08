"""Tests for Server-Sent Events support."""
import asyncio

import pytest

from aquilia.sse import SSEEvent, SSEResponse


class TestSSEEvent:
    def test_encode_basic(self):
        event = SSEEvent(data="hello")
        encoded = event.encode().decode()
        assert "data: hello" in encoded
        assert encoded.endswith("\n\n")

    def test_encode_named_event(self):
        event = SSEEvent(data="payload", event="update")
        encoded = event.encode().decode()
        assert "event: update" in encoded
        assert "data: payload" in encoded

    def test_encode_with_id(self):
        event = SSEEvent(data="x", id="42")
        encoded = event.encode().decode()
        assert "id: 42" in encoded

    def test_encode_with_retry(self):
        event = SSEEvent(data="x", retry=3000)
        encoded = event.encode().decode()
        assert "retry: 3000" in encoded

    def test_encode_multiline_data(self):
        event = SSEEvent(data="line1\nline2\nline3")
        encoded = event.encode().decode()
        assert encoded.count("data:") == 3

    def test_encode_empty_data(self):
        event = SSEEvent(data="")
        encoded = event.encode().decode()
        assert event.encode() == b"\n\n"


class TestSSEResponse:
    @pytest.mark.asyncio
    async def test_text_stream(self):
        async def gen():
            yield "hello"

        resp = SSEResponse.text(gen())
        messages = []

        async def mock_send(msg):
            messages.append(msg)

        async def mock_receive():
            await asyncio.sleep(100)

        await resp({"type": "http"}, mock_receive, mock_send)

        start = messages[0]
        assert start["type"] == "http.response.start"
        assert start["status"] == 200
        headers = dict(start["headers"])
        assert headers[b"content-type"] == b"text/event-stream; charset=utf-8"
        assert headers[b"cache-control"] == b"no-cache"

    @pytest.mark.asyncio
    async def test_json_stream(self):
        async def gen():
            yield {"value": 1}

        resp = SSEResponse.json(gen())
        messages = []

        async def mock_send(msg):
            messages.append(msg)

        async def mock_receive():
            await asyncio.sleep(100)

        await resp({"type": "http"}, mock_receive, mock_send)

        body_msg = messages[1]
        assert b"value" in body_msg["body"]
        assert "data:" in body_msg["body"].decode()

    @pytest.mark.asyncio
    async def test_basic_sse(self):
        async def gen():
            yield SSEEvent(data="a", event="update", id="1")

        resp = SSEResponse(gen())
        messages = []

        async def mock_send(msg):
            messages.append(msg)

        async def mock_receive():
            await asyncio.sleep(100)

        await resp({"type": "http"}, mock_receive, mock_send)

        body = messages[1]["body"].decode()
        assert "event: update" in body
        assert "id: 1" in body
        assert "data: a" in body