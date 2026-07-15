"""
aquilia.devplatform.core.h11_transport — Native h11-based ASGI/1.1 transport.

Replaces the toy line-oriented HTTP parser previously in devserver.py with a
real HTTP/1.1 state machine (h11): keep-alive, chunked transfer-encoding,
pipelining, and malformed-request handling all come from h11 rather than a
partial hand-rolled reimplementation.

Scope: HTTP/1.1 only (matches ``--http h11``, the ADP default). WebSocket
upgrade requests are handed off to ``WebSocketConnection``
(``aquilia.devplatform.core.websocket_transport``) once h11 reports a
``SWITCHED_PROTOCOL`` event is imminent (Connection: Upgrade, Upgrade: websocket).

One ``H11Connection`` per TCP connection; h11's ``Connection`` state machine
natively supports keep-alive, so a single instance serves every request on
a persistent connection until the client or h11 closes it.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

import h11

logger = logging.getLogger("aquilia.devplatform.h11_transport")

_REQUEST_TIMEOUT = 10.0  # seconds to wait for a new request on a keep-alive connection
_HEADER_READ_TIMEOUT = 5.0

ASGIApp = Callable[[dict, Callable, Callable], Coroutine[Any, Any, None]]


class H11Connection:
    """
    Drives one TCP connection's worth of HTTP/1.1 traffic through h11,
    dispatching each request to the wrapped ASGI app.
    """

    __slots__ = (
        "reader",
        "writer",
        "app",
        "server_addr",
        "conn",
        "_client_addr",
        "_ws_upgrade_hook",
    )

    def __init__(
        self,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
        app: ASGIApp,
        server_addr: tuple[str, int],
        ws_upgrade_hook: Callable[..., Coroutine[Any, Any, None]] | None = None,
    ) -> None:
        self.reader = reader
        self.writer = writer
        self.app = app
        self.server_addr = server_addr
        self.conn = h11.Connection(h11.SERVER)
        peer = writer.get_extra_info("peername")
        self._client_addr = (peer[0], peer[1]) if peer else ("unknown", 0)
        self._ws_upgrade_hook = ws_upgrade_hook

    async def run(self) -> None:
        """Serve requests on this connection until it closes or errors."""
        try:
            while True:
                request = await self._read_request()
                if request is None:
                    break

                upgrade = _is_websocket_upgrade(request)
                if upgrade and self._ws_upgrade_hook is not None:
                    await self._ws_upgrade_hook(self, request)
                    break  # WS takes over the raw socket; h11 loop is done

                disconnected = await self._dispatch(request)
                if disconnected:
                    # Client vanished mid-response: h11 is stuck in SEND_BODY,
                    # so start_next_cycle() would raise LocalProtocolError
                    # ("not in a reusable state"). Nothing more to serve.
                    break

                if self.conn.our_state is h11.MUST_CLOSE or self.conn.their_state is h11.MUST_CLOSE:
                    break
                if self.conn.our_state is not h11.DONE or self.conn.their_state is not h11.DONE:
                    # Response didn't cleanly complete — cannot reuse the
                    # connection; close rather than force an invalid transition.
                    break
                self.conn.start_next_cycle()
        except (h11.RemoteProtocolError, h11.LocalProtocolError) as exc:
            logger.debug("HTTP protocol error: %s", exc)
            await self._send_error_response(400, b"Bad Request")
        except (asyncio.TimeoutError, ConnectionResetError, BrokenPipeError):
            pass
        except Exception as exc:
            logger.debug("Connection error: %s", exc)
        finally:
            try:
                self.writer.close()
            except Exception:
                pass

    async def _read_request(self) -> h11.Request | None:
        """Read and parse one request line + headers (no body) via h11."""
        timeout = _REQUEST_TIMEOUT
        while True:
            event = self.conn.next_event()
            if event is h11.NEED_DATA:
                try:
                    data = await asyncio.wait_for(self.reader.read(65536), timeout=timeout)
                except asyncio.TimeoutError:
                    return None
                if not data:
                    self.conn.receive_data(b"")
                    return None
                self.conn.receive_data(data)
                timeout = _HEADER_READ_TIMEOUT
                continue
            if isinstance(event, h11.Request):
                return event
            if isinstance(event, h11.ConnectionClosed) or event is h11.PAUSED:
                return None

    async def _read_body(self) -> bytes:
        """Drain the request body (h11 handles chunked/content-length transparently)."""
        chunks: list[bytes] = []
        while True:
            event = self.conn.next_event()
            if event is h11.NEED_DATA:
                data = await asyncio.wait_for(self.reader.read(65536), timeout=30.0)
                self.conn.receive_data(data or b"")
                continue
            if isinstance(event, h11.Data):
                chunks.append(bytes(event.data))
                continue
            if isinstance(event, h11.EndOfMessage):
                break
            if isinstance(event, h11.ConnectionClosed):
                break
        return b"".join(chunks)

    async def _dispatch(self, request: h11.Request) -> bool:
        """Run the ASGI app for one request.

        Returns ``True`` if the client disconnected mid-response (the caller
        must stop the keep-alive loop — h11 can't be reused from a partial
        SEND_BODY state), ``False`` on a normally-completed request.
        """
        body = await self._read_body()
        scope = _build_scope(request, body, self._client_addr, self.server_addr)

        body_sent = False

        async def receive() -> dict[str, Any]:
            nonlocal body_sent
            if not body_sent:
                body_sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        started = False

        async def send(message: dict[str, Any]) -> None:
            nonlocal started
            msg_type = message["type"]
            if msg_type == "http.response.start":
                started = True
                status = message.get("status", 200)
                headers = message.get("headers", [])
                resp = h11.Response(status_code=status, headers=headers)
                data = self.conn.send(resp)
                if data:
                    self.writer.write(data)
            elif msg_type == "http.response.body":
                body_chunk = message.get("body", b"")
                more = message.get("more_body", False)
                if body_chunk:
                    data = self.conn.send(h11.Data(data=body_chunk))
                    if data:
                        self.writer.write(data)
                if not more:
                    data = self.conn.send(h11.EndOfMessage())
                    if data:
                        self.writer.write(data)
                await self.writer.drain()

        try:
            await self.app(scope, receive, send)
        except Exception as exc:
            if _is_expected_disconnect(exc):
                # Browser refresh/abort/tab-close severed the socket mid-response.
                # This is not an application failure — log quietly and stop.
                logger.debug("Client disconnected during %s %s: %s", scope["method"], scope["path"], exc)
                return True
            logger.exception("Unhandled error in ASGI app for %s %s", scope["method"], scope["path"])
            if not started:
                await self._send_error_response(500, b"Internal Server Error")
            else:
                # Response already started — nothing safe to send, close the connection.
                raise
            return True
        if not started:
            logger.error("ASGI app for %s %s returned without sending a response", scope["method"], scope["path"])
            await self._send_error_response(500, b"Internal Server Error")
        return False

    async def _send_error_response(self, status: int, body: bytes) -> None:
        try:
            if self.conn.our_state in (h11.IDLE, h11.SEND_RESPONSE):
                resp = h11.Response(status_code=status, headers=[(b"content-length", str(len(body)).encode())])
                data = self.conn.send(resp)
                if data:
                    self.writer.write(data)
                data = self.conn.send(h11.Data(data=body))
                if data:
                    self.writer.write(data)
                data = self.conn.send(h11.EndOfMessage())
                if data:
                    self.writer.write(data)
                await self.writer.drain()
        except Exception:
            pass


def _is_websocket_upgrade(request: h11.Request) -> bool:
    headers = {k.lower(): v.lower() for k, v in request.headers}
    return headers.get(b"upgrade") == b"websocket" and b"upgrade" in headers.get(b"connection", b"")


def _is_expected_disconnect(exc: BaseException) -> bool:
    """Return True if ``exc`` is an expected client-side disconnect.

    Covers both the raw socket errors (``ConnectionError``/``BrokenPipeError``/
    ``CancelledError``) and Aquilia's structured ``ClientDisconnectError`` that
    ``aquilia.response`` raises when a browser refresh/abort severs the socket
    mid-response. A ``ResponseStreamError`` is a genuine app streaming bug and
    is deliberately *not* treated as a disconnect.
    """
    if isinstance(exc, (ConnectionError, BrokenPipeError, asyncio.CancelledError)):
        return True
    # Match by code without importing response at module load (avoids a cycle
    # and keeps the transport importable in isolation).
    return getattr(exc, "code", None) == "CLIENT_DISCONNECT"


def _build_scope(
    request: h11.Request,
    body: bytes,
    client: tuple[str, int],
    server: tuple[str, int],
) -> dict[str, Any]:
    raw_path, _, query_string = request.target.partition(b"?")
    return {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": request.http_version.decode("latin-1"),
        "method": request.method.decode("latin-1").upper(),
        "path": raw_path.decode("latin-1") or "/",
        "raw_path": raw_path,
        "query_string": query_string,
        "root_path": "",
        "headers": [(k, v) for k, v in request.headers],
        "client": client,
        "server": server,
        "state": {},
    }
