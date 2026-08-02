"""
aquilia.devplatform.core.websocket_transport — Native RFC 6455 WebSocket transport.

Stdlib-only (hashlib/base64/struct) — no ``websockets``/``wsproto`` dependency
for the default ``--ws auto`` path. Those remain available as opt-in engines
(``--ws websockets`` / ``--ws wsproto``) once a measured need justifies adding
the dependency; the native implementation covers the ASGI websocket contract
(connect/receive/send/disconnect, text/binary frames, close codes) without it.

Handshake: H11Connection detects the Upgrade: websocket request and hands the
raw socket to ``serve_websocket`` here, which completes the RFC 6455 handshake
directly (bypassing h11 — the connection stops being HTTP/1.1 the instant the
upgrade response is sent) and then drives the ASGI websocket scope.
"""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import struct
import uuid
from collections.abc import Callable, Coroutine
from typing import Any

from aquilia.devplatform.core.websocket import WebSocketEntry, WebSocketTracker

logger = logging.getLogger("aquilia.devplatform.websocket_transport")

_WS_GUID = b"258EAFA5-E914-47DA-95CA-C5AB0DC85B11"

_OPCODE_CONTINUATION = 0x0
_OPCODE_TEXT = 0x1
_OPCODE_BINARY = 0x2
_OPCODE_CLOSE = 0x8
_OPCODE_PING = 0x9
_OPCODE_PONG = 0xA

#: Maximum accepted single-frame payload size. Rejects the connection before
#: reading the payload if the declared length exceeds this — without a cap,
#: an attacker-controlled 64-bit length prefix (RFC 6455's 127 marker) drives
#: an unbounded ``readexactly()`` allocation (DoS).
_MAX_FRAME_SIZE = 16 * 1024 * 1024  # 16 MiB

ASGIApp = Callable[[dict, Callable, Callable], Coroutine[Any, Any, None]]


def _accept_key(client_key: bytes) -> str:
    digest = hashlib.sha1(client_key + _WS_GUID).digest()
    return base64.b64encode(digest).decode("ascii")


async def serve_websocket(
    h11_conn: Any,
    request: Any,
    app: ASGIApp,
) -> None:
    """
    Complete the WebSocket handshake on an already-accepted TCP connection
    and drive the ASGI websocket lifecycle until close.

    ``h11_conn`` is an ``H11Connection`` (for its reader/writer/server_addr) —
    the h11 state machine itself is discarded; RFC 6455 framing takes over.
    """
    reader = h11_conn.reader
    writer = h11_conn.writer
    headers = {k.lower(): v for k, v in request.headers}

    client_key = headers.get(b"sec-websocket-key")
    if client_key is None:
        writer.write(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\n\r\n")
        await writer.drain()
        writer.close()
        return

    raw_path, _, query_string = request.target.partition(b"?")
    scope = {
        "type": "websocket",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": request.http_version.decode("latin-1"),
        "path": raw_path.decode("latin-1") or "/",
        "raw_path": raw_path,
        "query_string": query_string,
        "root_path": "",
        "headers": [(k, v) for k, v in request.headers],
        "client": h11_conn._client_addr,
        "server": h11_conn.server_addr,
        "subprotocols": _parse_subprotocols(headers.get(b"sec-websocket-protocol")),
        "state": {},
    }

    conn = _WebSocketConnection(reader, writer, client_key)
    to_app: asyncio.Queue = asyncio.Queue()
    closed = asyncio.Event()
    close_code = 1000

    connection_id = uuid.uuid4().hex
    client_addr = h11_conn._client_addr
    tracker = WebSocketTracker.get_instance()
    tracker.register(
        WebSocketEntry(
            connection_id=connection_id,
            path=scope["path"],
            client_addr=f"{client_addr[0]}:{client_addr[1]}" if client_addr else None,
        )
    )

    async def receive() -> dict[str, Any]:
        return await to_app.get()

    async def send(message: dict[str, Any]) -> None:
        nonlocal close_code
        msg_type = message["type"]
        if msg_type == "websocket.accept":
            await conn.accept(message.get("subprotocol"))
        elif msg_type == "websocket.send":
            if message.get("text") is not None:
                await conn.send_text(message["text"])
            elif message.get("bytes") is not None:
                await conn.send_bytes(message["bytes"])
            tracker.record_outbound_frame(connection_id)
        elif msg_type == "websocket.close":
            close_code = message.get("code", 1000)
            await conn.close(close_code)
            closed.set()

    # Kick off the ASGI app with an initial "connect" message queued.
    await to_app.put({"type": "websocket.connect"})
    app_task = asyncio.create_task(app(scope, receive, send))

    disconnect_code = 1000
    disconnect_reason: str | None = None
    try:
        while not closed.is_set() and not app_task.done():
            frame = await conn.read_frame()
            if frame is None:
                disconnect_code = 1006
                await to_app.put({"type": "websocket.disconnect", "code": 1006})
                break
            opcode, payload = frame
            tracker.record_inbound_frame(connection_id)
            if opcode == _OPCODE_TEXT:
                await to_app.put({"type": "websocket.receive", "text": payload.decode("utf-8", errors="replace")})
            elif opcode == _OPCODE_BINARY:
                await to_app.put({"type": "websocket.receive", "bytes": payload})
            elif opcode == _OPCODE_CLOSE:
                code = 1000
                if len(payload) >= 2:
                    code = struct.unpack("!H", payload[:2])[0]
                await conn.close(code)
                disconnect_code = code
                await to_app.put({"type": "websocket.disconnect", "code": code})
                break
            elif opcode == _OPCODE_PING:
                await conn.send_pong(payload)
            # PONG: no action needed
    except (asyncio.IncompleteReadError, ConnectionResetError, BrokenPipeError):
        disconnect_code = 1006
        await to_app.put({"type": "websocket.disconnect", "code": 1006})
    except _FrameTooLargeError as exc:
        disconnect_code = 1009
        disconnect_reason = str(exc)
        await conn.close(1009)
        await to_app.put({"type": "websocket.disconnect", "code": 1009})
    finally:
        tracker.unregister(connection_id, code=disconnect_code, reason=disconnect_reason)
        if not app_task.done():
            try:
                await asyncio.wait_for(app_task, timeout=2.0)
            except asyncio.TimeoutError:
                app_task.cancel()
        try:
            writer.close()
        except Exception:
            pass


class _FrameTooLargeError(Exception):
    """Raised when a peer declares a frame payload larger than ``_MAX_FRAME_SIZE``."""


def _parse_subprotocols(raw: bytes | None) -> list[str]:
    if not raw:
        return []
    return [p.strip().decode("latin-1") for p in raw.split(b",")]


class _WebSocketConnection:
    """RFC 6455 frame reader/writer over an asyncio stream pair."""

    __slots__ = ("reader", "writer", "_client_key", "_accepted")

    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter, client_key: bytes) -> None:
        self.reader = reader
        self.writer = writer
        self._client_key = client_key
        self._accepted = False

    async def accept(self, subprotocol: str | None = None) -> None:
        accept_value = _accept_key(self._client_key)
        lines = [
            "HTTP/1.1 101 Switching Protocols",
            "Upgrade: websocket",
            "Connection: Upgrade",
            f"Sec-WebSocket-Accept: {accept_value}",
        ]
        if subprotocol:
            lines.append(f"Sec-WebSocket-Protocol: {subprotocol}")
        lines.append("\r\n")
        self.writer.write("\r\n".join(lines).encode("latin-1"))
        await self.writer.drain()
        self._accepted = True

    async def read_frame(self) -> tuple[int, bytes] | None:
        """Read one complete WebSocket frame (handles fragmentation minimally: no continuation reassembly beyond single-frame messages)."""
        try:
            header = await self.reader.readexactly(2)
        except (asyncio.IncompleteReadError, ConnectionResetError):
            return None

        b0, b1 = header[0], header[1]
        opcode = b0 & 0x0F
        masked = bool(b1 & 0x80)
        length = b1 & 0x7F

        if length == 126:
            ext = await self.reader.readexactly(2)
            length = struct.unpack("!H", ext)[0]
        elif length == 127:
            ext = await self.reader.readexactly(8)
            length = struct.unpack("!Q", ext)[0]

        if length > _MAX_FRAME_SIZE:
            raise _FrameTooLargeError(f"frame length {length} exceeds max {_MAX_FRAME_SIZE} bytes")

        mask_key = b""
        if masked:
            mask_key = await self.reader.readexactly(4)

        payload = await self.reader.readexactly(length) if length else b""
        if masked and mask_key:
            payload = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload))

        return opcode, payload

    async def _send_frame(self, opcode: int, payload: bytes) -> None:
        length = len(payload)
        header = bytearray()
        header.append(0x80 | opcode)  # FIN=1, no fragmentation
        if length < 126:
            header.append(length)
        elif length < 65536:
            header.append(126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(127)
            header.extend(struct.pack("!Q", length))
        self.writer.write(bytes(header) + payload)
        await self.writer.drain()

    async def send_text(self, text: str) -> None:
        await self._send_frame(_OPCODE_TEXT, text.encode("utf-8"))

    async def send_bytes(self, data: bytes) -> None:
        await self._send_frame(_OPCODE_BINARY, data)

    async def send_pong(self, payload: bytes = b"") -> None:
        await self._send_frame(_OPCODE_PONG, payload)

    async def close(self, code: int = 1000) -> None:
        try:
            await self._send_frame(_OPCODE_CLOSE, struct.pack("!H", code))
        except Exception:
            pass
