"""
aquilia.devplatform.portmanager — Deterministic dev-server port resolution.

Port recovery belongs to the development platform, not the CLI. This module
replaces the old ``aquilia.cli.commands.run._find_available_port`` helper,
which probed a bind **without** ``SO_REUSEADDR`` while the real dev server
binds **with** ``reuse_address=True`` (see
``aquilia.devplatform.devserver.AquiliaDevelopmentServer.start``). The mismatch
made a just-terminated server's ``TIME_WAIT`` socket look occupied, so the CLI
kept hopping 8000 -> 8001 -> 8002 even though the real bind would have
succeeded.

``PortManager.resolve`` probes with the *same* socket options the server uses,
so its verdict matches what the server will actually do:

  * bind succeeds (free, or ``TIME_WAIT`` reclaimed by ``SO_REUSEADDR``)
        -> keep the port.
  * bind fails ``EADDRINUSE`` and a ``connect()`` to the port succeeds
        -> a live listener genuinely owns it -> switch to the next port.
  * bind fails ``EADDRINUSE`` but ``connect()`` is refused (transient race)
        -> retry the reuse-address bind once before switching.

No process is killed. The decision is deterministic and carries a
human-readable ``reason``.
"""

from __future__ import annotations

import errno
import socket
from dataclasses import dataclass

_MAX_PORT = 65535


@dataclass(slots=True)
class PortDecision:
    """Outcome of :meth:`PortManager.resolve`."""

    port: int
    reclaimed: bool  # kept the requested port (free or TIME_WAIT reclaimed)
    switched: bool  # a live listener forced a move to a different port
    reason: str


class PortManager:
    """Resolve the port the dev server should bind, matching its bind semantics."""

    def __init__(self, *, max_attempts: int = 100) -> None:
        self._max_attempts = max_attempts

    @staticmethod
    def _supports_reuse_port() -> bool:
        return hasattr(socket, "SO_REUSEPORT")

    @classmethod
    def _try_bind(cls, host: str, port: int) -> bool:
        """Return True if a socket with the server's options can bind ``port``.

        Mirrors ``AquiliaDevelopmentServer.start``: ``SO_REUSEADDR`` (and
        ``SO_REUSEPORT`` where available). This is what makes ``TIME_WAIT``
        ports reclaimable instead of false-positive "occupied".
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if cls._supports_reuse_port():
                try:
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except OSError:
                    pass
            try:
                s.bind((host, port))
                return True
            except OSError as exc:
                if exc.errno in (errno.EADDRINUSE, errno.EADDRNOTAVAIL):
                    return False
                raise

    @staticmethod
    def _has_live_listener(host: str, port: int) -> bool:
        """Return True if something is actively accepting connections on ``port``.

        Distinguishes a genuine live listener from a lingering ``TIME_WAIT``
        socket: only a real listener answers ``connect()``.
        """
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            try:
                s.connect((host, port))
                return True
            except OSError:
                return False

    def resolve(self, host: str, port: int) -> PortDecision:
        """Decide which port to bind, recovering from transient states first."""
        check_host = "127.0.0.1" if host in ("0.0.0.0", "") else host
        requested = port

        current = port
        for _ in range(self._max_attempts):
            if self._try_bind(check_host, current):
                if current == requested:
                    return PortDecision(
                        port=current,
                        reclaimed=True,
                        switched=False,
                        reason=f"Port {current} is available — binding.",
                    )
                return PortDecision(
                    port=current,
                    reclaimed=False,
                    switched=True,
                    reason=(f"Port {requested} is actively in use by another process. Switching to {current}."),
                )

            # Bind refused. Only a live listener justifies switching; a transient
            # EADDRINUSE without an accepting listener is retried once via reuse.
            if not self._has_live_listener(check_host, current):
                if self._try_bind(check_host, current):
                    if current == requested:
                        return PortDecision(
                            port=current,
                            reclaimed=True,
                            switched=False,
                            reason=f"Port {current} was recently released — reclaimed.",
                        )
                    return PortDecision(
                        port=current,
                        reclaimed=False,
                        switched=True,
                        reason=(f"Port {requested} is actively in use by another process. Switching to {current}."),
                    )

            current += 1
            if current > _MAX_PORT:
                break

        # Exhausted attempts — fall back to the requested port and let the
        # server surface the real bind error (StartupFault EADDRINUSE).
        return PortDecision(
            port=requested,
            reclaimed=False,
            switched=False,
            reason=f"No free port found near {requested} — deferring to server bind.",
        )
