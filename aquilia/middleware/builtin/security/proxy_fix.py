"""Trusted-proxy X-Forwarded-* correction.

Must run before anything that reads the client IP — rate limiting, logging,
access control — or those see the proxy's address instead of the client's.
"""

from __future__ import annotations

import contextlib
import ipaddress
from typing import TYPE_CHECKING

from aquilia.middleware.core.base import Middleware
from aquilia.middleware.core.types import RequestHandler

if TYPE_CHECKING:
    from aquilia.controller.base import RequestCtx
    from aquilia.request import Request
    from aquilia.response import Response

Handler = RequestHandler


class ProxyFixMiddleware(Middleware):
    """
    Fix request attributes when behind a reverse proxy.

    Rewrites request state/headers based on X-Forwarded-* headers from
    **trusted** proxies only.  Uses CIDR-based network matching to validate
    the connecting IP.

    Trusted Headers (RFC 7239 / de-facto):
    - X-Forwarded-For   → client IP
    - X-Forwarded-Proto → scheme (http/https)
    - X-Forwarded-Host  → original Host header
    - X-Forwarded-Port  → original port
    - X-Real-IP         → client IP (nginx)

    Args:
        trusted_proxies: CIDR ranges or IPs of trusted proxies.
        x_for: Number of trusted proxies to unwrap from X-Forwarded-For.
               0 = disabled.
        x_proto: Number of values to trust for X-Forwarded-Proto.
        x_host: Number of values to trust for X-Forwarded-Host.
        x_port: Number of values to trust for X-Forwarded-Port.
    """

    def __init__(
        self,
        trusted_proxies: list[str] | None = None,
        x_for: int = 1,
        x_proto: int = 1,
        x_host: int = 1,
        x_port: int = 0,
    ):
        self._trusted_networks: list[ipaddress.IPv4Network | ipaddress.IPv6Network] = []
        for proxy in trusted_proxies or ["127.0.0.0/8", "::1/128", "10.0.0.0/8", "172.16.0.0/12", "192.168.0.0/16"]:
            with contextlib.suppress(ValueError):
                self._trusted_networks.append(ipaddress.ip_network(proxy, strict=False))

        self._x_for = x_for
        self._x_proto = x_proto
        self._x_host = x_host
        self._x_port = x_port

    async def __call__(self, request: Request, ctx: RequestCtx, next_handler: Handler) -> Response:
        # Determine connecting IP
        remote_addr = self._get_remote_addr(request)
        if remote_addr and not self._is_trusted(remote_addr):
            return await next_handler(request, ctx)

        # X-Forwarded-For → client IP
        if self._x_for:
            forwarded_for = request.header("x-forwarded-for")
            if forwarded_for:
                ips = [ip.strip() for ip in forwarded_for.split(",")]
                # Pick the client IP (n hops from the right)
                idx = max(0, len(ips) - self._x_for)
                client_ip = ips[idx]
                request.state["client_ip"] = client_ip
                request.state["forwarded_for"] = ips

        # X-Real-IP (fallback for nginx)
        if not request.state.get("client_ip"):
            real_ip = request.header("x-real-ip")
            if real_ip:
                request.state["client_ip"] = real_ip.strip()

        # X-Forwarded-Proto → scheme
        if self._x_proto:
            proto = request.header("x-forwarded-proto")
            if proto:
                request.state["forwarded_proto"] = proto.strip().lower()

        # X-Forwarded-Host → original host
        if self._x_host:
            fwd_host = request.header("x-forwarded-host")
            if fwd_host:
                request.state["forwarded_host"] = fwd_host.strip()

        # X-Forwarded-Port → port
        if self._x_port:
            fwd_port = request.header("x-forwarded-port")
            if fwd_port:
                request.state["forwarded_port"] = fwd_port.strip()

        return await next_handler(request, ctx)

    def _get_remote_addr(self, request: Request) -> str | None:
        """Extract connecting IP from ASGI scope."""
        if hasattr(request, "_scope") and isinstance(request._scope, dict):
            client = request._scope.get("client")
            if client and len(client) >= 1:
                return str(client[0])
        return None

    def _is_trusted(self, ip_str: str) -> bool:
        """Check if IP falls within any trusted CIDR range."""
        try:
            addr = ipaddress.ip_address(ip_str)
        except ValueError:
            return False
        return any(addr in net for net in self._trusted_networks)


__all__ = ["ProxyFixMiddleware"]
