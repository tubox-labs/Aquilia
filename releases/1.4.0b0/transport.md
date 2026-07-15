# Transport Layer — v1.4.0b0

## HTTP: `H11Connection`

`aquilia/devplatform/core/h11_transport.py`

Replaces the previous hand-rolled line parser in `devserver.py` (which read
one request line + headers with `reader.readline()`, had no keep-alive
support, and closed the connection after every response). `H11Connection`
drives a real `h11.Connection(h11.SERVER)` state machine instead.

```python
class H11Connection:
    def __init__(self, reader, writer, app, server_addr, ws_upgrade_hook=None):
        self.conn = h11.Connection(h11.SERVER)
        ...

    async def run(self) -> None:
        while True:
            request = await self._read_request()
            if request is None:
                break
            if _is_websocket_upgrade(request) and self._ws_upgrade_hook:
                await self._ws_upgrade_hook(self, request)
                break
            await self._dispatch(request)
            if self.conn.our_state is h11.MUST_CLOSE or self.conn.their_state is h11.MUST_CLOSE:
                break
            self.conn.start_next_cycle()
```

What this buys over the previous parser:
- **Keep-alive and pipelining** — handled by `h11.Connection.start_next_cycle()`, not re-implemented.
- **Chunked transfer-encoding** on request bodies — `h11` parses `Transfer-Encoding: chunked` transparently; `_read_body()` just drains `h11.Data`/`h11.EndOfMessage` events.
- **Malformed request handling** — `h11.RemoteProtocolError`/`h11.LocalProtocolError` are caught and answered with `400 Bad Request` instead of the connection hanging or raising unhandled.
- **No response after an app crash** — `_dispatch()` sends `500 Internal Server Error` if the app raises (or returns) before calling `send({"type": "http.response.start", ...})`; if the app already started a response before raising, the exception propagates and the connection closes (nothing safe left to send).

`_dispatch()` builds the ASGI `http` scope directly from the parsed `h11.Request`:

```python
scope = {
    "type": "http",
    "asgi": {"version": "3.0", "spec_version": "2.3"},
    "http_version": request.http_version.decode("latin-1"),
    "method": request.method.decode("latin-1").upper(),
    "path": raw_path.decode("latin-1") or "/",
    "raw_path": raw_path,
    "query_string": query_string,
    "headers": [(k, v) for k, v in request.headers],
    "client": client,
    "server": server,
    "state": {},
}
```

## WebSocket: `serve_websocket`

`aquilia/devplatform/core/websocket_transport.py`

Stdlib-only RFC 6455 implementation — `hashlib`, `base64`, `struct` only. No
`websockets` or `wsproto` dependency for the default (`--ws auto`) path.

- **Handshake**: `_accept_key()` computes `base64(sha1(Sec-WebSocket-Key + "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"))` and `_WebSocketConnection.accept()` writes the `101 Switching Protocols` response directly to the socket (bypassing h11 entirely — the connection stops being HTTP/1.1 once the handshake completes).
- **Framing**: `_WebSocketConnection.read_frame()`/`_send_frame()` implement the RFC 6455 frame format (2/4/10-byte header variants for payload length, client-to-server masking, opcodes for text/binary/close/ping/pong). No message fragmentation reassembly — each frame maps to one ASGI message (adequate for typical request/response and streaming patterns; a client sending fragmented messages across multiple frames is not reassembled).
- **Frame-size limit (security)**: `read_frame()` rejects any frame whose declared payload length exceeds `_MAX_FRAME_SIZE` (16 MiB) *before* calling `readexactly()`, closing the connection with code 1009. Without this, an attacker-controlled 64-bit length prefix (the RFC 6455 `127` marker) drove an unbounded memory allocation — a DoS vector.
- **Connection tracking**: `serve_websocket()` registers each connection in `WebSocketTracker` (a `WebSocketEntry` with per-connection inbound/outbound frame counts), unregistering with the disconnect code on close.
- **ASGI bridge**: an `asyncio.Queue` feeds `websocket.connect` / `websocket.receive` / `websocket.disconnect` messages to the app; `send()` translates `websocket.accept` / `websocket.send` / `websocket.close` back into frames.

Both `H11Connection` (HTTP) and `serve_websocket` (WebSocket) were verified
against a real local socket during development — request/response cycles,
keep-alive across two requests on one connection, error responses, and a full
RFC 6455 handshake + text-frame echo + close sequence.

## Config Fields

`aquilia/devplatform/config.py` — `AquiliaDevelopmentConfig`:

| Field | Type | Default | Env override |
|---|---|---|---|
| `host` | `str` | `"127.0.0.1"` | `AQ_DEV_HOST` |
| `port` | `int` | `8000` | `AQ_DEV_PORT` |
| `uds` | `str \| None` | `None` | `AQ_DEV_UDS` |
| `fd` | `int \| None` | `None` | `AQ_DEV_FD` |
| `http` | `"auto" \| "h11"` | `"h11"` | `AQ_DEV_HTTP` |
| `ws` | `"auto" \| "none"` | `"auto"` | `AQ_DEV_WS` |

Binding priority in `AquiliaDevelopmentServer.start()`: **UDS > inherited FD >
`host:port`**, in that order — set at most one.

**Socket hardening (1.4.0b0).**
- **UDS**: before binding, a stale *socket* file left by a crashed process is unlinked (fixing an otherwise-unhandled `EADDRINUSE`); a non-socket file at the path is refused (`StartupFault`) rather than clobbered. After bind the socket is `chmod`'d to `0o600` (owner-only).
- **Inherited FD**: bound via `socket.socket(fileno=fd)`, which infers family/type/proto from the descriptor — the old `socket.fromfd(fd, AF_INET, ...)` hardcoded IPv4 and broke `AF_UNIX`/`AF_INET6` passing. `AQ_DEV_FD=0` now correctly binds fd 0 (previously coerced to "unset").
- **Port-in-use**: detected via `errno.EADDRINUSE` (cross-platform) instead of the previous Linux-only `errno == 98` / substring match; reported as a `StartupFault`.

## CLI Flags

Added to `aq run` / `aq dev` (`aquilia/cli/__main__.py`):

```
--uds TEXT        Bind to a UNIX domain socket path instead of host:port
--fd INTEGER      Bind to an inherited file descriptor instead of host:port
--http [auto|h11] HTTP transport engine (default: h11 — native ADP transport)
--ws [auto|none]  WebSocket support (default: auto — native RFC 6455 transport)
```

Example:

```bash
aq dev --http h11 --ws auto          # default: native transport, native WS
aq dev --http auto                    # uvicorn as the HTTP transport
aq dev --uds /tmp/aquilia-dev.sock    # UNIX socket instead of TCP
```

## `--http auto` (uvicorn) Path

`_run_with_adp()` in `aquilia/cli/commands/run.py`: when `--http auto` is
selected (and uvicorn is importable), a `runtime/_adp_app.py` wrapper module
is generated that layers `ASGILifespanManager` + `ADPProtocolHandler` around
the workspace app, and `uvicorn.run()` serves it. ADP's own hot-reload
watcher still drives reload in this mode (`uvicorn.run(..., reload=False)` —
uvicorn's own reload subprocess mechanism is explicitly not used).

If `--http auto` is requested but `uvicorn` isn't importable, `_run_with_adp`
falls back to `h11` with a warning rather than failing.

## Resolution Order

Documented in `run_dev_server()`'s docstring and mirrored in
`_build_adp_config()`:

1. Explicit CLI flags (`--host`, `--port`, `--reload`, `--uds`, `--fd`, `--http`, `--ws`)
2. `AquilaConfig.Server` values from `workspace.py` (`adp_uds`, `adp_http`, `adp_ws` — read via `rt.get("adp_http", "h11")` etc.; these are not declared as formal dataclass fields on `AquilaConfig.Server`, but `AquilaConfig.to_dict()` serializes arbitrary class attributes, so setting them on a `Server` subclass works and was verified empirically)
3. Hardcoded fallback defaults (`http="h11"`, `ws="auto"`, no `uds`/`fd`)

```python
# workspace.py
from aquilia.pyconfig import AquilaConfig

class Server(AquilaConfig.Server):
    adp_http = "auto"     # picked up by _build_adp_config via rt.get("adp_http")
    adp_ws = "none"
    adp_uds = "/tmp/aquilia.sock"

class Config(AquilaConfig):
    server = Server
```
