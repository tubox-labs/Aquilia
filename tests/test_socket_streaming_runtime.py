from __future__ import annotations

from dataclasses import dataclass

import pytest

from aquilia.sockets.controller import SocketController
from aquilia.sockets.envelope import MessageEnvelope, MessageType, StreamChunk
from aquilia.sockets.runtime import AquilaSockets, SocketRouter


@dataclass
class _Sent:
    events: list[tuple[str, dict]]
    json_payloads: list[dict]
    acks: list[tuple[str | None, dict]]
    envelopes: list[MessageEnvelope]


class _FakeConn:
    def __init__(self):
        self.sent = _Sent(events=[], json_payloads=[], acks=[], envelopes=[])

    async def send_event(self, event: str, payload: dict, ack: bool = False):  # noqa: ARG002
        self.sent.events.append((event, payload))

    async def send_json(self, data: dict):
        self.sent.json_payloads.append(data)

    async def send_ack(
        self, message_id: str | None, status: str = "ok", data: dict | None = None, error: str | None = None
    ):
        self.sent.acks.append((message_id, {"status": status, "data": data or {}, "error": error}))

    async def send_envelope(self, envelope: MessageEnvelope):
        self.sent.envelopes.append(envelope)


class _StreamingController(SocketController):
    async def stream_async(self, conn, payload):  # noqa: ARG002
        async def _gen():
            yield {"seq": 1}
            yield StreamChunk(data="two", meta={"seq": 2})

        return _gen()

    async def stream_sync(self, conn, payload):  # noqa: ARG002
        return iter([b"abc", {"done": True}])


_StreamingController.stream_async.__socket_handler__ = {
    "event": "stream.async",
    "type": "event",
    "ack": False,
    "schema": None,
}

_StreamingController.stream_sync.__socket_handler__ = {
    "event": "stream.sync",
    "type": "event",
    "ack": False,
    "schema": None,
}


@pytest.mark.asyncio
async def test_dispatch_event_streams_async_chunks_and_end_event():
    runtime = AquilaSockets(SocketRouter())
    conn = _FakeConn()
    controller = _StreamingController()

    envelope = MessageEnvelope(type=MessageType.EVENT, event="stream.async", payload={})
    await runtime._dispatch_event(conn, controller, envelope)

    assert conn.sent.events[0] == ("stream.async.chunk", {"seq": 1})
    assert conn.sent.events[1] == ("stream.async.chunk", {"text": "two", "seq": 2})
    assert conn.sent.events[-1] == ("stream.async.end", {"chunks": 2})


@pytest.mark.asyncio
async def test_dispatch_event_streams_sync_chunks_with_base64_for_bytes():
    runtime = AquilaSockets(SocketRouter())
    conn = _FakeConn()
    controller = _StreamingController()

    envelope = MessageEnvelope(type=MessageType.EVENT, event="stream.sync", payload={})
    await runtime._dispatch_event(conn, controller, envelope)

    assert conn.sent.events[0] == (
        "stream.sync.chunk",
        {"data_b64": "YWJj", "encoding": "base64"},
    )
    assert conn.sent.events[1] == ("stream.sync.chunk", {"done": True})
    assert conn.sent.events[-1] == ("stream.sync.end", {"chunks": 2})


@pytest.mark.asyncio
async def test_dispatch_event_stream_respects_client_ack_request():
    runtime = AquilaSockets(SocketRouter())
    conn = _FakeConn()
    controller = _StreamingController()

    envelope = MessageEnvelope(type=MessageType.EVENT, event="stream.async", payload={}, ack=True)
    await runtime._dispatch_event(conn, controller, envelope)

    assert conn.sent.acks == [
        (
            envelope.id,
            {
                "status": "ok",
                "data": {"streamed": True, "chunks": 2},
                "error": None,
            },
        )
    ]
