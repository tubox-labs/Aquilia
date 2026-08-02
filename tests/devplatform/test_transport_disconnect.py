"""Regression tests for h11 transport error classification.

Guards the fix where a browser refresh/abort (ConnectionResetError from
writer.drain) was logged at ERROR as "Unhandled error in ASGI app" and
double-logged via the run() DEBUG path. Expected client disconnects must be
DEBUG-only; genuine app exceptions must still be ERROR + 500.
"""

from __future__ import annotations

import asyncio
import logging

from aquilia.devplatform.core.h11_transport import H11Connection, _is_expected_disconnect
from aquilia.response import ClientDisconnectError, ResponseStreamError


class _FakeReader:
    """Feeds a canned HTTP/1.1 request once, then EOF."""

    def __init__(self, data: bytes) -> None:
        self._chunks = [data]

    async def read(self, _n: int) -> bytes:
        return self._chunks.pop(0) if self._chunks else b""


class _FakeWriter:
    def __init__(self, *, drain_exc: Exception | None = None) -> None:
        self._drain_exc = drain_exc
        self.closed = False

    def get_extra_info(self, _key):
        return ("127.0.0.1", 5555)

    def write(self, _data: bytes) -> None:
        pass

    async def drain(self) -> None:
        if self._drain_exc is not None:
            raise self._drain_exc

    def close(self) -> None:
        self.closed = True


_REQUEST = b"GET / HTTP/1.1\r\nHost: x\r\n\r\n"


def _app_that_streams():
    async def app(scope, receive, send):
        await receive()
        await send({"type": "http.response.start", "status": 200, "headers": []})
        await send({"type": "http.response.body", "body": b"chunk", "more_body": False})

    return app


def _app_that_raises(exc: Exception):
    async def app(scope, receive, send):
        await receive()
        raise exc

    return app


class TestDisconnectClassification:
    def test_helper_matches_connection_errors(self):
        assert _is_expected_disconnect(ConnectionResetError())
        assert _is_expected_disconnect(BrokenPipeError())
        assert _is_expected_disconnect(asyncio.CancelledError())
        assert _is_expected_disconnect(ClientDisconnectError(message="x"))

    def test_helper_rejects_stream_error_and_app_bugs(self):
        # A genuine streaming bug is NOT a disconnect.
        assert not _is_expected_disconnect(ResponseStreamError(message="boom"))
        assert not _is_expected_disconnect(ValueError("app bug"))

    async def test_drain_reset_is_debug_not_error(self, caplog):
        """Browser abort → drain raises ConnectionResetError → no ERROR log."""
        writer = _FakeWriter(drain_exc=ConnectionResetError("Connection lost"))
        conn = H11Connection(_FakeReader(_REQUEST), writer, _app_that_streams(), ("127.0.0.1", 8000))
        with caplog.at_level(logging.DEBUG, logger="aquilia.devplatform.h11_transport"):
            await conn.run()
        errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert not errors, f"unexpected error logs: {[r.getMessage() for r in errors]}"
        assert writer.closed

    async def test_client_disconnect_error_is_quiet(self, caplog):
        writer = _FakeWriter()
        app = _app_that_raises(ClientDisconnectError(message="Client disconnected"))
        conn = H11Connection(_FakeReader(_REQUEST), writer, app, ("127.0.0.1", 8000))
        with caplog.at_level(logging.DEBUG, logger="aquilia.devplatform.h11_transport"):
            await conn.run()
        assert not [r for r in caplog.records if r.levelno >= logging.ERROR]

    async def test_real_app_exception_still_errors(self, caplog):
        """A genuine bug must still surface as ERROR + a 500 attempt."""
        writer = _FakeWriter()
        conn = H11Connection(_FakeReader(_REQUEST), writer, _app_that_raises(ValueError("boom")), ("127.0.0.1", 8000))
        with caplog.at_level(logging.DEBUG, logger="aquilia.devplatform.h11_transport"):
            await conn.run()
        errors = [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert errors, "genuine app exception should log at ERROR"
        assert any("Unhandled error" in r.getMessage() for r in errors)

    async def test_sse_disconnect_does_not_emit_protocol_error(self, caplog):
        """After an SSE disconnect mid-body, the keep-alive loop must break.

        Regression: previously run() called start_next_cycle() on a connection
        stuck in SEND_BODY, raising h11 LocalProtocolError ("not in a reusable
        state") — a spurious second log line plus a doomed 400 write.
        """

        async def sse_app(scope, receive, send):
            await receive()
            await send({"type": "http.response.start", "status": 200, "headers": []})
            # Streaming chunk, then the client vanishes.
            await send({"type": "http.response.body", "body": b"data: 1\n\n", "more_body": True})
            raise ConnectionResetError("Connection lost")

        writer = _FakeWriter()
        conn = H11Connection(_FakeReader(_REQUEST), writer, sse_app, ("127.0.0.1", 8000))
        with caplog.at_level(logging.DEBUG, logger="aquilia.devplatform.h11_transport"):
            await conn.run()
        msgs = [r.getMessage() for r in caplog.records]
        assert not any("not in a reusable state" in m for m in msgs), msgs
        assert not any("protocol error" in m.lower() for m in msgs), msgs
        assert not [r for r in caplog.records if r.levelno >= logging.ERROR]
        assert writer.closed
