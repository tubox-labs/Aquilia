"""
ASGI adapter -- Bridges the ASGI protocol to Aquilia's request / response system.
Supports HTTP, WebSocket, and Lifespan events.

Performance (v2):
- Middleware chain is built ONCE after startup and cached.
- Route matching uses sync O(1)/O(k) hot path.
- Per-request allocations minimized.
- Query string parsed once (lazy, inside Request).
- DI container lookup uses cached app container reference.

Hardening (v2.1):
- In-flight request tracking via ``EngineMetrics``.
- Built-in ``/_health`` endpoint returns liveness + metrics JSON.
- Graceful error recovery with structured logging.
- Lifespan guards for ``DatabaseNotReadyError``.
"""

from __future__ import annotations

import logging
import time
from typing import Any, cast

from .controller.base import _ctx_pool
from .controller.router import ControllerRouter
from .engine import get_engine_metrics
from .middleware import Handler, MiddlewareStack
from .request import Request
from .response import Response
from .typing import ASGIReceive, ASGIScope, ASGISend
from .typing.controller import ControllerRouteMatchLike


class ASGIAdapter:
    """
    ASGI application adapter.
    Converts ASGI events to Aquilia Request/Response.
    Uses controller-based routing exclusively.
    """

    __slots__ = (
        "controller_router",
        "controller_engine",
        "middleware_stack",
        "server",
        "socket_runtime",
        "logger",
        "_cached_middleware_chain",
        "_default_container",
        "_debug",
        "_has_routes_cache",
        "_server_runtime",
    )

    def __init__(
        self,
        controller_router: ControllerRouter,
        controller_engine: Any,
        middleware_stack: MiddlewareStack,
        server: Any | None = None,
        socket_runtime: Any | None = None,
    ):
        self.controller_router = controller_router
        self.controller_engine = controller_engine
        self.middleware_stack = middleware_stack
        self.server = server
        self.socket_runtime = socket_runtime
        self.logger = logging.getLogger("aquilia.asgi")
        self._cached_middleware_chain: Handler | None = None
        self._default_container = None
        self._debug: bool | None = None
        self._has_routes_cache: bool | None = None
        self._server_runtime: Any | None = None  # Cached after startup

        if self.socket_runtime and self.server:
            self._setup_socket_di()

    def _setup_socket_di(self):
        """Setup DI container factory for WebSockets."""
        server = self.server

        async def container_factory(request=None):
            if not server or not hasattr(server, "runtime"):
                from .di import Container

                return Container(scope="request")
            if server.runtime.di_containers:
                app_container = next(iter(server.runtime.di_containers.values()))
                return app_container.create_request_scope()
            from .di import Container

            return Container(scope="request")

        self.socket_runtime.container_factory = container_factory

    # ------------------------------------------------------------------
    # Cached helpers
    # ------------------------------------------------------------------

    def _is_debug(self) -> bool:
        if self._debug is None:
            if self.server and hasattr(self.server, "_is_debug"):
                self._debug = self.server._is_debug()
            else:
                self._debug = False
        return self._debug

    def _get_default_container(self):
        """Get or create the default app container (cached)."""
        if self._default_container is None:
            if self.server and hasattr(self.server, "runtime") and self.server.runtime.di_containers:
                self._default_container = next(iter(self.server.runtime.di_containers.values()))
            else:
                from .di import Container

                self._default_container = Container(scope="app")
        return self._default_container

    def _has_routes(self) -> bool:
        if self._has_routes_cache is None:
            try:
                if hasattr(self.controller_router, "routes_by_method"):
                    self._has_routes_cache = any(
                        len(routes) > 0 for routes in self.controller_router.routes_by_method.values()
                    )
                else:
                    self._has_routes_cache = True
            except Exception:
                self._has_routes_cache = True
        return self._has_routes_cache

    # ------------------------------------------------------------------
    # Middleware chain building (cached)
    # ------------------------------------------------------------------

    def _build_cached_chain(self):
        """Build the middleware chain once. The final handler dispatches
        to the matched controller stored in request.state."""
        if self._cached_middleware_chain is not None:
            return

        async def _final_handler(request: Request, ctx) -> Response:
            """Final handler that dispatches to matched controller."""
            controller_match = cast(ControllerRouteMatchLike | None, request.state.get("_controller_match"))

            if controller_match:
                response = await self.controller_engine.execute(
                    controller_match.route,
                    request,
                    controller_match.params,
                    ctx.container,
                )
                return cast(Response, response)

            # No controller matched -- 404
            accept = self._get_accept_from_request(request)
            if "text/html" in accept:
                from .debug.pages import render_http_error_page, render_welcome_page

                version = self._get_version()
                path = request.path
                method = request.method
                if self._is_debug() and path == "/" and not self._has_routes():
                    # Welcome page only in debug mode
                    system_info = {
                        "debug": True,
                    }

                    html_body = render_welcome_page(aquilia_version=version, system_info=system_info)
                    return Response(
                        content=html_body.encode("utf-8"),
                        status=200,
                        headers={"content-type": "text/html; charset=utf-8"},
                    )
                html_body = render_http_error_page(
                    404,
                    "Not Found",
                    f"No route matches {method} {path}",
                    request,
                    aquilia_version=version,
                )
                return Response(
                    content=html_body.encode("utf-8"),
                    status=404,
                    headers={"content-type": "text/html; charset=utf-8"},
                )

            from .faults.domains import NotFoundFault

            raise NotFoundFault(
                detail=f"No route matches {request.method} {request.path}",
            )

        self._cached_middleware_chain = self.middleware_stack.build_handler(_final_handler)

    @staticmethod
    def _get_accept_from_request(request: Request) -> str:
        try:
            return request.header("accept") or ""
        except Exception:
            return ""

    def _get_version(self) -> str:
        try:
            from aquilia import __version__

            return __version__
        except Exception:
            return ""

    # ------------------------------------------------------------------
    # ASGI entry point
    # ------------------------------------------------------------------

    async def __call__(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        scope_type = scope["type"]
        if scope_type == "http":
            await self.handle_http(scope, receive, send)
        elif scope_type == "websocket":
            await self.handle_websocket(scope, receive, send)
        elif scope_type == "lifespan":
            await self.handle_lifespan(scope, receive, send)
        else:
            self.logger.warning(
                "Unrecognized ASGI scope type '%s' — ignoring",
                scope_type,
            )

    async def handle_http(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        """Handle HTTP request with optimized hot path.

        Performance (v3 — scalability):
        - Uses RequestCtx object pool to avoid per-request allocation.
        - Single metrics.request_started() call (no double-counting).
        - Returns ctx to pool after response is sent.
        """

        # ── Build middleware chain once (idempotent) ──
        if self._cached_middleware_chain is None:
            self._build_cached_chain()
        handler = self._cached_middleware_chain
        if handler is None:
            raise RuntimeError("Middleware chain was not initialized")

        path = scope.get("path", "/")
        method = scope.get("method", "GET")

        # ── Fast-path: built-in health endpoint ──
        if path == "/_health":
            if method not in ("GET", "HEAD"):
                await self._send_method_not_allowed(send, ["GET", "HEAD"], scope)
                return
            await self._serve_health(send, head_only=(method == "HEAD"))
            return

        # ── Create lean Request object ──
        request = Request(scope, receive)

        # ── Sync route matching (O(1) for static, O(k) for dynamic) ──
        # If versioning middleware ran, it stored the resolved ApiVersion
        # in request.state["api_version"].  Pass it to the router so
        # version-filtered matching can discriminate versioned routes.
        _api_version = request.state.get("api_version") if isinstance(request.state, dict) else None
        controller_match = self.controller_router.match_sync(
            path,
            method,
            api_version=_api_version,
        )

        # ── ARCH-01: 405 Method Not Allowed + ARCH-05: HEAD auto-support ──
        is_head_fallback = False
        if controller_match is None:
            if method == "HEAD":
                # HTTP/1.1 §9.4: HEAD must be supported wherever GET is.
                controller_match = self.controller_router.match_sync(
                    path,
                    "GET",
                    api_version=_api_version,
                )
                if controller_match is not None:
                    is_head_fallback = True

            if controller_match is None:
                allowed = self.controller_router.get_allowed_methods(path)
                if allowed:
                    # Path exists but method is not allowed → 405
                    if "GET" in allowed and "HEAD" not in allowed:
                        allowed.append("HEAD")
                    await self._send_method_not_allowed(send, sorted(allowed), scope)
                    return

        # ── Resolve DI container ──
        app_container = None
        runtime = self._server_runtime
        if runtime is None and self.server and hasattr(self.server, "runtime"):
            runtime = self.server.runtime
            self._server_runtime = runtime

        if controller_match and runtime:
            app_name = getattr(controller_match.route, "app_name", None)
            if app_name:
                app_container = runtime.di_containers.get(app_name)
            if app_container is None and runtime.di_containers:
                app_container = self._get_default_container()
        else:
            app_container = self._get_default_container()

        di_container = app_container.create_request_scope() if app_container else None
        if di_container is None:
            from .di import Container

            di_container = Container(scope="request")

        # ── Acquire RequestCtx from pool (zero-alloc hot path) ──
        ctx = _ctx_pool.acquire(
            request=request,
            identity=None,
            session=None,
            container=di_container,
        )

        # Store controller match in request state for the final handler
        if controller_match:
            request.state["_controller_match"] = controller_match
            request.state["app_name"] = getattr(controller_match.route, "app_name", None)
            request.state["route_pattern"] = getattr(controller_match.route, "full_path", None)
            request.state["path_params"] = controller_match.params
        else:
            request.state["app_name"] = None
            request.state["route_pattern"] = None
            request.state["path_params"] = {}

        # ── Execute cached middleware chain ──
        metrics = get_engine_metrics()
        metrics.request_started()

        # ── ARCH-09: Wire server._inflight_requests to real counter ──
        if self.server:
            self.server._inflight_requests = metrics.inflight

        t0 = time.monotonic()
        try:
            response = await handler(request, ctx)
        except Exception as e:
            metrics.request_errored()
            self.logger.error(f"Critical error in request pipeline: {e}", exc_info=True)
            accept = self._get_accept_from_request(request)
            if "text/html" in accept:
                try:
                    if self._is_debug():
                        from .debug.pages import render_debug_exception_page

                        html_body = render_debug_exception_page(
                            e,
                            request,
                            aquilia_version=self._get_version(),
                        )
                    else:
                        from .debug.pages import render_http_error_page

                        html_body = render_http_error_page(
                            500,
                            "Internal Server Error",
                            "An unexpected error occurred processing your request.",
                            request,
                            aquilia_version=self._get_version(),
                        )
                except Exception as render_exc:
                    self.logger.error(
                        f"Error page renderer crashed: {render_exc}",
                        exc_info=True,
                    )
                    html_body = (
                        '<!DOCTYPE html><html><head><meta charset="utf-8">'
                        '<title>500</title></head><body style="font-family:'
                        "system-ui;background:#000;color:#eee;display:flex;"
                        "justify-content:center;align-items:center;height:"
                        '100vh;margin:0;"><div style="text-align:center;">'
                        '<h1 style="color:#ef4444;">500</h1>'
                        "<p>Internal Server Error</p></div></body></html>"
                    )
                response = Response(
                    content=html_body.encode("utf-8"),
                    status=500,
                    headers={"content-type": "text/html; charset=utf-8"},
                )
                await response.send_asgi(send)
                return
            response = Response.json(
                {"error": "Internal server error"},
                status=500,
            )
        finally:
            latency_ms = (time.monotonic() - t0) * 1000.0
            metrics.request_finished(latency_ms)

            # ── ARCH-09: Keep server counter in sync ──
            if self.server:
                self.server._inflight_requests = metrics.inflight

            # ── ARCH-02: DI container cleanup is handled by request_scope_mw
            # (priority 5) in server._setup_middleware().  That middleware's
            # finally block always runs because FaultMiddleware (priority 2)
            # wraps the entire chain and catches exceptions.
            # Container.shutdown() IS idempotent (_shutdown_called guard),
            # but removing the redundant call here avoids ~1µs of overhead
            # per request.  If request_scope_mw is ever removed, re-enable
            # the shutdown call below as a safety net.
            # ──────────────────────────────────────────────────────────────

            # ── Return ctx to pool for reuse ──
            _ctx_pool.release(ctx)

        # ── ARCH-05: Strip body for HEAD requests ──
        if is_head_fallback and response is not None:
            response = Response(
                content=b"",
                status=response.status,
                headers=dict(response.headers) if hasattr(response, "headers") else {},
            )

        await response.send_asgi(send)

    # ------------------------------------------------------------------
    # 405 Method Not Allowed response (ARCH-01)
    # ------------------------------------------------------------------

    async def _send_method_not_allowed(self, send: ASGISend, allowed: list[str], scope: ASGIScope | None = None) -> None:
        """Send a ``405 Method Not Allowed`` response with an ``Allow`` header.

        Renders the styled Tubox error page for browser clients and
        returns structured JSON for API clients.
        """
        allow_value = ", ".join(sorted(allowed))
        method = (scope or {}).get("method", "?")
        path = (scope or {}).get("path", "?")
        detail = f"Method {method} is not allowed for {path}. Allowed: {allow_value}"

        # Check Accept header from raw ASGI scope
        accept = ""
        for hdr_name, hdr_val in (scope or {}).get("headers", []):
            if hdr_name == b"accept":
                accept = hdr_val.decode("latin-1", errors="replace")
                break

        if "text/html" in accept:
            from .debug.pages import render_http_error_page

            html_body = render_http_error_page(
                405,
                "Method Not Allowed",
                detail,
                aquilia_version=self._get_version(),
            )
            body = html_body.encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": 405,
                    "headers": [
                        (b"content-type", b"text/html; charset=utf-8"),
                        (b"allow", allow_value.encode("utf-8")),
                        (b"content-length", str(len(body)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})
        else:
            import json as _json

            body = _json.dumps(
                {
                    "error": {
                        "code": "HTTP_405",
                        "message": "Method Not Allowed",
                        "status": 405,
                        "detail": detail,
                        "allowed_methods": sorted(allowed),
                    },
                }
            ).encode("utf-8")
            await send(
                {
                    "type": "http.response.start",
                    "status": 405,
                    "headers": [
                        (b"content-type", b"application/json"),
                        (b"allow", allow_value.encode("utf-8")),
                        (b"content-length", str(len(body)).encode()),
                    ],
                }
            )
            await send({"type": "http.response.body", "body": body})

    # ------------------------------------------------------------------
    # Built-in health endpoint (ARCH-03: method-restricted + optional auth)
    # ------------------------------------------------------------------

    async def _serve_health(self, send: ASGISend, *, head_only: bool = False) -> None:
        """Serve ``GET /_health`` -- liveness probe + engine metrics.

        Returns JSON with:
        - ``status``: ``"healthy"`` / ``"degraded"``
        - ``metrics``: in-flight, total requests, mean latency
        - ``subsystems``: per-subsystem health (if HealthRegistry is available)

        Security (ARCH-03 / ARCH-07):
        - Restricted to GET and HEAD only (405 for others).
        - Minimal security headers applied (no-store, no-sniff, deny framing).
        """
        import json as _json

        metrics = get_engine_metrics()
        body: dict[str, Any] = {
            "status": "healthy",
            "metrics": metrics.snapshot(),
        }

        # Optionally include subsystem health from HealthRegistry (v2)
        try:
            # Access registry from server reference if available
            registry = getattr(self.server, "health_registry", None) if self.server else None
            if registry is not None:
                health_report = registry.to_dict()
                body["subsystems"] = health_report.get("subsystems", {})
                # Degrade overall status if any subsystem is unhealthy
                overall_status = health_report.get("status", "healthy")
                if overall_status != "healthy":
                    body["status"] = overall_status
        except Exception:
            pass

        payload = _json.dumps(body).encode("utf-8")

        # ARCH-07: Apply minimal security headers even though middleware is bypassed
        headers = [
            (b"content-type", b"application/json"),
            (b"cache-control", b"no-store"),
            (b"content-length", str(len(payload)).encode()),
            (b"x-content-type-options", b"nosniff"),
            (b"x-frame-options", b"DENY"),
        ]

        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": headers,
            }
        )
        await send(
            {
                "type": "http.response.body",
                # ARCH-05: HEAD support -- send empty body for HEAD requests
                "body": b"" if head_only else payload,
            }
        )

    async def handle_websocket(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        """Handle WebSocket connection."""
        if self.socket_runtime:
            await self.socket_runtime.handle_websocket(scope, receive, send)
        else:
            self.logger.warning("WebSocket connection attempt but sockets are disabled")
            await send({"type": "websocket.close", "code": 1003})

    async def handle_lifespan(self, scope: ASGIScope, receive: ASGIReceive, send: ASGISend) -> None:
        """Handle ASGI lifespan events."""
        while True:
            message = await receive()

            if message["type"] == "lifespan.startup":
                try:
                    if self.server:
                        await self.server.startup()
                        # Invalidate caches after startup
                        self._cached_middleware_chain = None
                        self._default_container = None
                        self._has_routes_cache = None
                        self._debug = None
                        self._server_runtime = None
                    else:
                        self.logger.warning("No server instance - controllers may not be loaded")
                    await send({"type": "lifespan.startup.complete"})
                except SystemExit as e:
                    # DatabaseNotReadyError is a SystemExit subclass.
                    # Log the message but complete the lifespan handshake so
                    # uvicorn doesn't fall back to "lifespan unsupported".
                    self.logger.warning(f"Startup guard warning (non-fatal): {e}")
                    await send({"type": "lifespan.startup.complete"})
                except Exception as e:
                    self.logger.error(f"Startup error: {e}", exc_info=True)
                    # Sanitize error message to prevent internal details leakage (OWASP)
                    await send({"type": "lifespan.startup.failed", "message": "Server startup failed"})
                    raise

            elif message["type"] == "lifespan.shutdown":
                try:
                    if self.server:
                        await self.server.shutdown()
                    await send({"type": "lifespan.shutdown.complete"})
                except Exception as e:
                    self.logger.error(f"Shutdown error: {e}", exc_info=True)
                    await send({"type": "lifespan.shutdown.complete"})
                break
