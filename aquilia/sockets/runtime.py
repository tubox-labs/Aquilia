"""
WebSocket Runtime - ASGI integration and connection management

Integrates WebSocket controllers with Aquilia's ASGI adapter.
"""

from __future__ import annotations

import contextlib
import logging
import uuid
from collections.abc import AsyncIterator, Callable, Iterator
from dataclasses import dataclass
from typing import Any

from aquilia.auth.core import Identity
from aquilia.faults import Fault
from aquilia.request import Request
from aquilia.sessions.core import Session
from aquilia.sockets.adapters import Adapter, InMemoryAdapter
from aquilia.sockets.connection import Connection, ConnectionScope
from aquilia.sockets.controller import SocketController
from aquilia.sockets.envelope import JSONCodec, MessageEnvelope, StreamChunk
from aquilia.sockets.faults import WS_MESSAGE_INVALID, WS_PAYLOAD_TOO_LARGE, WS_UNSUPPORTED_EVENT
from aquilia.sockets.guards import SocketGuard
from aquilia.sockets.middleware import SocketCtx, SocketMiddlewareStack

logger = logging.getLogger("aquilia.sockets.runtime")

# Internal ctx.state key carrying the accept callable through the connect chain.
# The chain is folded once per namespace at startup, so per-connection callables
# cannot be captured in the closure and have to travel on the context.
_ACCEPT_KEY = "_ws_accept"

# RFC 6455 close codes used when a fault does not name one.
_CLOSE_UNSUPPORTED = 1003
_CLOSE_INTERNAL_ERROR = 1011


def _close_code(fault: Fault, default: int = _CLOSE_UNSUPPORTED) -> int:
    """Extract ``ws_close_code`` from a fault's metadata.

    Socket faults carry it in ``metadata`` (see ``aquilia/sockets/faults.py``),
    not as an attribute — reading it with ``getattr`` silently returns the
    default for every fault, which is how every close came back as 1003.
    """
    metadata = getattr(fault, "metadata", None)
    if isinstance(metadata, dict):
        code = metadata.get("ws_close_code")
        if isinstance(code, int):
            return code
    return default


@dataclass
class RouteMetadata:
    """Socket route metadata extracted from controller."""

    namespace: str
    path_pattern: str
    controller_class: type[SocketController]
    handlers: dict[str, Callable]  # event -> method
    schemas: dict[str, Any]  # event -> schema
    guards: list[SocketGuard]
    allowed_origins: list[str] | None
    max_connections: int | None
    message_rate_limit: int | None
    max_message_size: int
    app_name: str | None = None  # Owning app container (for per-app DI scoping)


class SocketRouter:
    """
    Router for WebSocket namespaces.

    Matches paths to controllers and manages routing.
    """

    def __init__(self):
        """Initialize socket router."""
        self.routes: dict[str, RouteMetadata] = {}  # namespace -> metadata
        self._compiled_patterns: dict[str, Any] = {}  # namespace -> CompiledPattern
        self._namespace_by_pattern: dict[str, str] = {}  # pattern.raw -> namespace
        try:
            from aquilia.patterns import PatternCompiler, PatternMatcher

            self._pattern_compiler = PatternCompiler()
            self._pattern_matcher = PatternMatcher()
            self._has_patterns = True
        except ImportError:
            self._pattern_compiler = None
            self._pattern_matcher = None
            self._has_patterns = False

    def register(
        self,
        namespace: str,
        metadata: RouteMetadata,
    ):
        """
        Register socket controller.

        Args:
            namespace: Namespace identifier
            metadata: Route metadata
        """
        if namespace in self.routes:
            logger.warning(f"Namespace {namespace} already registered, overwriting")

        self.routes[namespace] = metadata

        # Pre-compile pattern for fast matching
        if self._has_patterns and self._pattern_compiler:
            try:
                from aquilia.patterns import parse_pattern

                ast = parse_pattern(metadata.path_pattern)
                compiled = self._pattern_compiler.compile(ast)
                self._compiled_patterns[namespace] = compiled
                # PatternMatcher matches against the patterns registered on it,
                # so a compiled pattern that is never added can never match.
                self._pattern_matcher.add_pattern(compiled)
                self._namespace_by_pattern[compiled.raw] = namespace
            except Exception:
                logger.debug("Could not compile socket pattern %s", metadata.path_pattern, exc_info=True)

    async def match(self, path: str) -> tuple[str, RouteMetadata, dict[str, Any]] | None:
        """
        Match path to namespace.

        Args:
            path: Request path

        Returns:
            (namespace, metadata, path_params) or None
        """
        # Full pattern support (typed params, constraints, splats).
        if self._has_patterns and self._pattern_matcher and self._pattern_matcher.patterns:
            try:
                result = await self._pattern_matcher.match(path)
            except Exception:
                logger.debug("Socket pattern matching failed for %s", path, exc_info=True)
                result = None

            if result is not None:
                namespace = self._namespace_by_pattern.get(result.pattern.raw)
                if namespace is not None and namespace in self.routes:
                    return (namespace, self.routes[namespace], result.params or {})

        # Fallback: exact match, then basic ":param" matching. Reachable when the
        # patterns subsystem is unavailable, or when a route failed to compile.
        for namespace, metadata in self.routes.items():
            pattern = metadata.path_pattern

            # Simple static matching
            if pattern == path:
                return (namespace, metadata, {})

            # Basic param matching (e.g., /chat/:namespace)
            if ":" in pattern:
                parts = pattern.split("/")
                path_parts = path.split("/")

                if len(parts) == len(path_parts):
                    params = {}
                    match = True

                    for i, part in enumerate(parts):
                        if part.startswith(":"):
                            param_name = part[1:]
                            params[param_name] = path_parts[i]
                        elif part != path_parts[i]:
                            match = False
                            break

                    if match:
                        return (namespace, metadata, params)

        return None


class AquilaSockets:
    """
    Main WebSocket runtime.

    Manages:
    - Connection lifecycle
    - Message routing
    - Controller execution
    - DI integration
    """

    def __init__(
        self,
        router: SocketRouter,
        adapter: Adapter | None = None,
        container_factory: Callable | None = None,
        auth_manager: Any | None = None,
        session_engine: Any | None = None,
        middleware_stack: SocketMiddlewareStack | None = None,
    ):
        """
        Initialize WebSocket runtime.

        Args:
            router: Socket router
            adapter: Scaling adapter (default: InMemoryAdapter)
            container_factory: Factory for creating DI containers
            auth_manager: Auth manager for handshake auth
            session_engine: Session engine for session support
            middleware_stack: Socket middleware stack. Chains are folded once per
                namespace at startup and cached, mirroring the HTTP adapter's
                single cached chain.
        """
        self.router = router
        self.adapter = adapter or InMemoryAdapter()
        self.container_factory = container_factory
        self.auth_manager = auth_manager
        self.session_engine = session_engine
        self.middleware_stack = middleware_stack if middleware_stack is not None else SocketMiddlewareStack()

        self.connections: dict[str, Connection] = {}
        self.controller_instances: dict[str, SocketController] = {}

        self.codec = JSONCodec()
        self._initialized = False

        # namespace -> (connect_chain, message_chain, scoped_stack)
        self._chains: dict[str, tuple[Callable, Callable, SocketMiddlewareStack]] = {}

    # ── Middleware chains ────────────────────────────────────────────────

    def build_chains(self) -> None:
        """Fold the middleware chains for every registered namespace.

        Called once at startup after controllers are loaded. Building per
        namespace rather than per connection keeps the per-connection cost to a
        dict lookup, and lets ``namespace:`` scoped middleware be filtered out of
        chains it does not belong to instead of being tested per message.
        """
        self._chains.clear()

        for namespace in self.router.routes:
            scoped = self.middleware_stack.scoped(namespace)
            self._chains[namespace] = (
                scoped.build_connect_handler(self._final_connect),
                scoped.build_message_handler(self._final_dispatch),
                scoped,
            )

    def _chain_for(self, namespace: str) -> tuple[Callable, Callable, SocketMiddlewareStack]:
        """Chains for *namespace*, folding them on demand if startup did not.

        A namespace registered after ``build_chains()`` (a test constructing the
        runtime directly, say) still gets a correct chain rather than silently
        running with no middleware.
        """
        chain = self._chains.get(namespace)
        if chain is None:
            scoped = self.middleware_stack.scoped(namespace)
            chain = (
                scoped.build_connect_handler(self._final_connect),
                scoped.build_message_handler(self._final_dispatch),
                scoped,
            )
            self._chains[namespace] = chain
        return chain

    async def initialize(self):
        """Initialize runtime."""
        await self.adapter.initialize()
        if not self._chains:
            self.build_chains()
        self._initialized = True

    async def shutdown(self):
        """Shutdown runtime."""
        # Disconnect all connections
        for conn in list(self.connections.values()):
            await self._disconnect_connection(conn, "server shutdown")

        await self.adapter.shutdown()
        self._initialized = False

    async def handle_websocket(self, scope: dict, receive: callable, send: callable):
        """
        Handle WebSocket connection (ASGI entry point).

        Args:
            scope: ASGI scope
            receive: ASGI receive callable
            send: ASGI send callable
        """
        # Match route
        path = scope.get("path", "/")
        match_result = await self.router.match(path)

        if not match_result:
            # No route found - reject handshake
            await send(
                {
                    "type": "websocket.close",
                    "code": 1003,
                    "reason": "No matching WebSocket namespace",
                }
            )
            return

        namespace, route_metadata, path_params = match_result
        connect_chain, message_chain, scoped_stack = self._chain_for(namespace)

        # Perform handshake
        try:
            conn = await self._perform_handshake(
                scope,
                send,
                namespace,
                route_metadata,
                path_params,
            )
        except Fault as e:
            logger.warning(f"Handshake failed: {e.message}")
            await self._close(send, _close_code(e), e.message)
            return

        ctx = SocketCtx(conn, namespace)

        # The connect chain runs *before* websocket.accept, so a middleware that
        # rejects closes the handshake outright. Accepting and then immediately
        # closing is indistinguishable from a crash on the client side.
        async def _accept() -> None:
            await send({"type": "websocket.accept"})

        ctx.state[_ACCEPT_KEY] = _accept

        try:
            await connect_chain(ctx)
        except Fault as e:
            logger.warning(f"Socket connect rejected ({e.code}): {e.message}")
            await self._reject_connection(conn, send, _close_code(e), e.message)
            return
        except Exception as e:
            logger.error(f"Socket connect failed: {e}", exc_info=True)
            await self._reject_connection(conn, send, 1011, "internal error")
            return
        finally:
            ctx.state.pop(_ACCEPT_KEY, None)

        controller = self.controller_instances.get(namespace)

        # Message loop
        await self._message_loop(conn, ctx, route_metadata, message_chain, scoped_stack, receive, send)

    async def _final_connect(self, ctx: SocketCtx) -> None:
        """Innermost connect handler: accept the socket, then run ``@OnConnect``."""
        accept = ctx.state.pop(_ACCEPT_KEY, None)
        if accept is not None:
            await accept()

        ctx.connection.mark_connected()

        controller = self.controller_instances.get(ctx.namespace)
        if controller is not None:
            await self._call_on_connect(controller, ctx.connection)

    async def _reject_connection(
        self,
        conn: Connection,
        send: callable,
        code: int,
        reason: str,
    ) -> None:
        """Tear down a connection refused during the connect chain.

        Deliberately does not run the disconnect middleware fan-out: the
        connection never reached the connected state, so there is no symmetric
        teardown owed. Middleware that needs to compensate for a rejected
        handshake does so in its own ``on_connect`` exception path.
        """
        was_accepted = conn.is_connected
        conn.mark_closing()

        try:
            await conn.leave_all()
        except Exception:  # noqa: BLE001 — best-effort cleanup
            logger.debug("leave_all failed while rejecting connection", exc_info=True)

        if hasattr(self.adapter, "unregister_send_callback"):
            self.adapter.unregister_send_callback(conn.namespace, conn.connection_id)

        try:
            await self.adapter.unregister_connection(conn.namespace, conn.connection_id)
        except Exception:  # noqa: BLE001 — best-effort cleanup
            logger.debug("adapter unregister failed while rejecting connection", exc_info=True)

        self.connections.pop(conn.connection_id, None)
        conn.mark_closed()

        # An accepted socket is closed; one never accepted is refused. Both use
        # websocket.close, but only the accepted case has a live peer.
        await self._close(send, code, reason)
        if was_accepted:
            logger.debug("Connection %s closed after accept during connect chain", conn.connection_id)

    @staticmethod
    async def _close(send: callable, code: int, reason: str) -> None:
        await send(
            {
                "type": "websocket.close",
                "code": code,
                "reason": (reason or "")[:123],  # Max 123 bytes
            }
        )

    async def _perform_handshake(
        self,
        scope: dict,
        send: callable,
        namespace: str,
        route_metadata: RouteMetadata,
        path_params: dict[str, Any],
    ) -> Connection:
        """Perform WebSocket handshake."""
        # Create Request object for robust parsing

        # Mock receive that returns nothing (we don't read body in handshake)
        async def mock_receive():
            return {"type": "websocket.receive", "bytes": b""}

        # Create request with websocket scope
        # We temporarily treat it as HTTP-like for parsing helpers
        req = Request(scope, mock_receive)

        # Extract parsing results from Request
        headers = dict(req.headers)
        query_params = dict(req.query_params)

        conn_scope = ConnectionScope(
            namespace=namespace,
            path=req.path,
            path_params=path_params,
            query_params=query_params,
            headers=headers,
        )

        # Authenticate using the robust Request object
        identity, session = await self._authenticate_handshake(req)

        # Run guards
        for guard in route_metadata.guards:
            await guard.check_handshake(conn_scope, identity, session)

        # Check origin
        if route_metadata.allowed_origins:
            origin = headers.get("origin", "")
            if origin and origin not in route_metadata.allowed_origins:
                from aquilia.sockets.faults import WS_ORIGIN_NOT_ALLOWED

                raise WS_ORIGIN_NOT_ALLOWED(origin)

        # Create DI container
        container = None
        if self.container_factory:
            # Propagate the matched route's owning app so the factory scopes
            # the container to the correct per-app container (§6.6), instead
            # of always using the first-registered app.
            if route_metadata.app_name is not None:
                try:
                    if isinstance(req.state, dict):
                        req.state["app_name"] = route_metadata.app_name
                    else:
                        req.state.app_name = route_metadata.app_name
                except Exception:
                    pass
            # Pass request context if factory supports it
            try:
                container = await self.container_factory(req)
            except TypeError:
                container = await self.container_factory()

        # Create connection
        connection_id = str(uuid.uuid4())

        async def send_func(data: bytes):
            await send(
                {
                    "type": "websocket.send",
                    "text": data.decode("utf-8") if isinstance(data, bytes) else data,
                }
            )

        conn = Connection(
            connection_id=connection_id,
            namespace=namespace,
            scope=conn_scope,
            container=container,
            adapter=self.adapter,
            send_func=send_func,
            identity=identity,
            session=session,
        )

        # Register connection
        self.connections[connection_id] = conn

        # Register with adapter
        import os

        worker_id = f"{os.uname().nodename}:{os.getpid()}"
        await self.adapter.register_connection(
            namespace=namespace,
            connection_id=connection_id,
            worker_id=worker_id,
        )

        # Register send callback with adapter (for InMemoryAdapter)
        if hasattr(self.adapter, "register_send_callback"):
            self.adapter.register_send_callback(namespace, connection_id, send_func)

        return conn

    async def _authenticate_handshake(
        self,
        request: Request,
    ) -> tuple[Identity | None, Session | None]:
        """
        Authenticate handshake using Request object.

        Tries multiple auth methods:
        1. Authorization header (via Request helper)
        2. Query string token (?token=...)
        3. Session cookie (via SessionEngine)

        Returns:
            (identity, session) tuple
        """
        identity = None
        session = None

        # 1. Try Authorization header
        # Using Request's auth_scheme/auth_credentials
        scheme = request.auth_scheme()
        credentials = request.auth_credentials()

        if scheme and scheme.lower() == "bearer" and credentials and self.auth_manager:
            with contextlib.suppress(Exception):
                identity = await self.auth_manager.get_identity_from_token(credentials)

        # 2. Try query string token
        if not identity and self.auth_manager:
            token = request.query_param("token")
            if token:
                with contextlib.suppress(Exception):
                    identity = await self.auth_manager.get_identity_from_token(token)

        # 3. Try session cookie (Unified with HTTP flow)
        if self.session_engine:
            try:
                # Use SessionEngine to load session from request
                # This uses the same logic as SessionMiddleware
                # Note: Pass None for container as we prefer to register it later strictly
                session = await self.session_engine.resolve(request, None)

                if session and not identity:
                    # Extract identity from session
                    # We can use the standard session helper since we have a real Session object
                    if "identity_id" in session.data and self.auth_manager:
                        identity_id = session.data["identity_id"]
                        identity = await self.auth_manager.identity_store.get(identity_id)

            except Exception:
                pass

        return identity, session

    async def _call_on_connect(self, controller: SocketController, conn: Connection):
        """Call controller's on_connect handler."""
        # Find @OnConnect handler
        for _name, method in controller.__class__.__dict__.items():
            if hasattr(method, "__socket_handler__"):
                metadata = method.__socket_handler__
                if metadata.get("type") == "on_connect":
                    await method(controller, conn)
                    return

    async def _message_loop(
        self,
        conn: Connection,
        ctx: SocketCtx,
        route_metadata: RouteMetadata,
        message_chain: Callable,
        scoped_stack: SocketMiddlewareStack,
        receive: callable,
        send: callable,
    ):
        """Message receive loop."""
        max_size = route_metadata.max_message_size
        reason = "connection closed"

        try:
            while conn.is_connected:
                message = await receive()

                if message["type"] == "websocket.receive":
                    # Handle text or binary message
                    raw = message.get("bytes") or message.get("text")
                    if raw:
                        # Normalise to bytes for codec.decode()
                        data = raw.encode("utf-8") if isinstance(raw, str) else raw
                        conn.record_received(len(data))

                        # Frame size is checked against the raw bytes, before
                        # decode: you cannot safely decode a frame in order to
                        # discover it was too large to decode.
                        if max_size and len(data) > max_size:
                            await self._report_message_error(
                                conn,
                                None,
                                WS_PAYLOAD_TOO_LARGE(len(data), max_size),
                            )
                            continue

                        await self._handle_message(conn, ctx, message_chain, data)

                elif message["type"] == "websocket.disconnect":
                    # Client disconnected
                    code = message.get("code", 1000)
                    reason = f"client disconnect (code {code})"
                    await self._disconnect_connection(conn, reason, ctx=ctx, stack=scoped_stack)
                    return

        except Exception as e:
            logger.error(f"Message loop error: {e}", exc_info=True)
            await self._disconnect_connection(conn, f"error: {e}", ctx=ctx, stack=scoped_stack)
            return

        # Loop exited because the connection stopped being connected (a handler
        # called conn.disconnect()) rather than via a disconnect frame.
        await self._disconnect_connection(conn, reason, ctx=ctx, stack=scoped_stack)

    async def _handle_message(
        self,
        conn: Connection,
        ctx: SocketCtx,
        message_chain: Callable,
        data: bytes,
    ):
        """Decode one frame and run it through the message chain."""
        try:
            envelope = self.codec.decode(data)
        except Exception as e:
            # Decode happens before the chain, so SocketFaultMiddleware never
            # sees this and the reply has to be produced here. Previously this
            # was logged and the client was told nothing at all.
            logger.warning("Could not decode socket message: %s", e)
            await self._report_message_error(conn, None, WS_MESSAGE_INVALID(str(e)))
            return

        ctx.begin_message(envelope.event)
        try:
            result = await message_chain(envelope, ctx)

            # _final_dispatch always returns None and sends its own acks, so a
            # non-None result means a middleware short-circuited and this is its
            # reply to deliver.
            if result is not None:
                await self._send_short_circuit_reply(conn, envelope, result)

        except Fault as e:
            # Only reachable when SocketFaultMiddleware is not registered; it
            # normally converts faults into acks further in. Reported here so a
            # chain without it still tells the client something.
            logger.warning("Socket fault on '%s' (%s): %s", envelope.event, e.code, e.message)
            await self._report_message_error(conn, envelope, e)
        except Exception as e:
            logger.error("Message handling error on '%s': %s", envelope.event, e, exc_info=True)
            await self._report_message_error(conn, envelope, e)
        finally:
            ctx.end_message()

    async def _final_dispatch(self, envelope: MessageEnvelope, ctx: SocketCtx) -> dict | None:
        """Innermost message handler: route to the controller's event handler.

        Always returns ``None`` — ``_dispatch_event`` sends its own acks and
        stream chunks. That is what makes a non-``None`` chain result an
        unambiguous signal that a middleware short-circuited.
        """
        controller = self.controller_instances.get(ctx.namespace)
        if controller is None:
            return None

        await self._dispatch_event(ctx.connection, controller, envelope)
        return None

    async def _send_short_circuit_reply(
        self,
        conn: Connection,
        envelope: MessageEnvelope,
        payload: dict,
    ) -> None:
        """Deliver a payload returned by a middleware that skipped the handler.

        Status is ``ok`` because the middleware chose to return rather than
        raise; a middleware signalling failure raises a ``SocketFault``, which
        becomes an error ack instead.
        """
        if not conn.is_connected:
            return
        try:
            if envelope.id:
                await conn.send_ack(envelope.id, status="ok", data=payload)
            else:
                await conn.send_json(payload)
        except Exception:  # noqa: BLE001 — peer may already be gone
            logger.debug("Could not deliver short-circuit reply", exc_info=True)

    async def _report_message_error(
        self,
        conn: Connection,
        envelope: MessageEnvelope | None,
        error: Exception,
    ) -> None:
        """Tell the client a message failed.

        Fault codes and messages are safe to expose — they are authored strings
        with stable codes. An arbitrary exception's text is not, so it is
        replaced with a generic message.
        """
        if not conn.is_connected:
            return

        if isinstance(error, Fault):
            code, message = error.code, error.message
        else:
            code, message = "WS_INTERNAL_ERROR", "Internal server error"

        try:
            if envelope is not None and envelope.id:
                await conn.send_ack(envelope.id, status="error", error=message)
            else:
                await conn.send_event(
                    "error",
                    {
                        "code": code,
                        "message": message,
                        "event": envelope.event if envelope is not None else None,
                    },
                )
        except Exception:  # noqa: BLE001 — peer may already be gone
            logger.debug("Could not deliver socket error report", exc_info=True)

    async def _dispatch_event(
        self,
        conn: Connection,
        controller: SocketController,
        envelope: MessageEnvelope,
    ):
        """Dispatch event to controller handler."""
        event = envelope.event

        # Find handler
        for _name, method in controller.__class__.__dict__.items():
            if hasattr(method, "__socket_handler__"):
                metadata = method.__socket_handler__

                if metadata.get("event") == event:
                    # Validate schema
                    schema = metadata.get("schema")
                    if schema:
                        valid, error = schema.validate(envelope.payload)
                        if not valid:
                            raise WS_MESSAGE_INVALID(error)

                    # Call handler
                    result = await method(controller, conn, envelope.payload)

                    if self._is_stream_result(result):
                        chunk_count = await self._send_stream_result(conn, event, result)
                        ack_data = {"streamed": True, "chunks": chunk_count}
                        handler_wants_ack = metadata.get("ack", False)
                        if handler_wants_ack:
                            await conn.send_json(ack_data)
                        elif envelope.ack:
                            await conn.send_ack(
                                envelope.id,
                                status="ok",
                                data=ack_data,
                            )
                        return

                    # Send ack if handler or client requested it
                    handler_wants_ack = metadata.get("ack", False)
                    if handler_wants_ack or envelope.ack:
                        ack_data = result if isinstance(result, dict) else {}
                        # Use send_json for direct client-friendly response
                        # when the handler produces a result (e.g. @AckEvent)
                        if handler_wants_ack and result is not None:
                            await conn.send_json(ack_data)
                        elif envelope.ack:
                            await conn.send_ack(
                                envelope.id,
                                status="ok",
                                data=ack_data,
                            )

                    return

        # No handler found
        logger.warning(f"No handler for event: {event}")
        raise WS_UNSUPPORTED_EVENT(event)

    @staticmethod
    def _is_stream_result(result: Any) -> bool:
        return isinstance(result, (AsyncIterator, Iterator))

    async def _send_stream_result(self, conn: Connection, event: str, stream: Any) -> int:
        chunk_count = 0

        try:
            if isinstance(stream, AsyncIterator):
                async for chunk in stream:
                    await self._send_stream_chunk(conn, event, chunk)
                    chunk_count += 1
            else:
                for chunk in stream:
                    await self._send_stream_chunk(conn, event, chunk)
                    chunk_count += 1
        finally:
            if hasattr(stream, "aclose"):
                with contextlib.suppress(Exception):
                    await stream.aclose()
            elif hasattr(stream, "close"):
                with contextlib.suppress(Exception):
                    stream.close()

        await conn.send_event(f"{event}.end", {"chunks": chunk_count})
        return chunk_count

    async def _send_stream_chunk(self, conn: Connection, event: str, chunk: Any):
        if isinstance(chunk, MessageEnvelope):
            await conn.send_envelope(chunk)
            return

        if isinstance(chunk, StreamChunk):
            payload = self._normalize_stream_payload(chunk.data)
            payload.update(chunk.meta)
            await conn.send_event(chunk.event or f"{event}.chunk", payload)
            return

        payload = self._normalize_stream_payload(chunk)
        await conn.send_event(f"{event}.chunk", payload)

    @staticmethod
    def _normalize_stream_payload(chunk: dict[str, Any] | str | bytes) -> dict[str, Any]:
        if isinstance(chunk, dict):
            return chunk
        if isinstance(chunk, str):
            return {"text": chunk}
        if isinstance(chunk, bytes):
            import base64

            return {
                "data_b64": base64.b64encode(chunk).decode("ascii"),
                "encoding": "base64",
            }

        raise WS_MESSAGE_INVALID(f"Unsupported stream chunk type: {type(chunk).__name__}")

    async def _disconnect_connection(
        self,
        conn: Connection,
        reason: str,
        *,
        ctx: SocketCtx | None = None,
        stack: SocketMiddlewareStack | None = None,
    ):
        """Disconnect connection and run the teardown fan-out.

        Every close path routes through here — client disconnect, server
        shutdown, and a handler calling ``conn.disconnect()`` — so the middleware
        teardown hooks fire on all three from this one call site.
        """
        if conn.connection_id not in self.connections:
            return

        conn.mark_closing()

        # Call on_disconnect handler
        controller = self.controller_instances.get(conn.namespace)
        if controller:
            try:
                await self._call_on_disconnect(controller, conn, reason)
            except Exception as e:
                logger.error(f"OnDisconnect handler error: {e}", exc_info=True)

        # Middleware teardown, reverse registration order. run_disconnect
        # isolates each hook's failures so one raising cannot strand the rest.
        if stack is None:
            cached = self._chains.get(conn.namespace)
            stack = cached[2] if cached is not None else None
        if stack is not None:
            await stack.run_disconnect(ctx if ctx is not None else SocketCtx(conn), reason)

        # Cleanup
        await conn.leave_all()

        if hasattr(self.adapter, "unregister_send_callback"):
            self.adapter.unregister_send_callback(conn.namespace, conn.connection_id)

        await self.adapter.unregister_connection(conn.namespace, conn.connection_id)

        del self.connections[conn.connection_id]

        conn.mark_closed()

    async def _call_on_disconnect(
        self,
        controller: SocketController,
        conn: Connection,
        reason: str | None,
    ):
        """Call controller's on_disconnect handler."""
        import inspect

        for _name, method in controller.__class__.__dict__.items():
            if hasattr(method, "__socket_handler__"):
                metadata = method.__socket_handler__
                if metadata.get("type") == "on_disconnect":
                    # Inspect signature to determine if handler accepts reason
                    sig = inspect.signature(method)
                    # Parameters: (self, connection, [reason])
                    params = list(sig.parameters.values())
                    if len(params) >= 3:
                        await method(controller, conn, reason)
                    else:
                        await method(controller, conn)
                    return
