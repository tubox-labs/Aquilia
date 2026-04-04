"""
AquilaHTTP — Connection Pool.

Async connection pool with per-host limits, keepalive management,
and health tracking.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

from .config import PoolConfig
from .faults import ConnectionClosedFault, ConnectionPoolExhaustedFault

logger = logging.getLogger("aquilia.http.pool")


@dataclass
class ConnectionStats:
    """Connection pool statistics."""

    total_created: int = 0
    total_closed: int = 0
    total_reused: int = 0
    active_connections: int = 0
    idle_connections: int = 0
    failed_acquisitions: int = 0
    pool_exhausted_count: int = 0

    def to_dict(self) -> dict[str, int]:
        return {
            "total_created": self.total_created,
            "total_closed": self.total_closed,
            "total_reused": self.total_reused,
            "active_connections": self.active_connections,
            "idle_connections": self.idle_connections,
            "failed_acquisitions": self.failed_acquisitions,
            "pool_exhausted_count": self.pool_exhausted_count,
        }


@dataclass
class PooledConnection:
    """
    Wrapper for a pooled connection.

    Tracks connection state, age, and usage.
    """

    host: str
    port: int
    scheme: str
    connection: Any  # Underlying transport connection
    created_at: float = field(default_factory=time.monotonic)
    last_used_at: float = field(default_factory=time.monotonic)
    requests_count: int = 0
    is_available: bool = True
    is_http2: bool = False

    @property
    def age(self) -> float:
        """Seconds since connection was created."""
        return time.monotonic() - self.created_at

    @property
    def idle_time(self) -> float:
        """Seconds since connection was last used."""
        return time.monotonic() - self.last_used_at

    @property
    def key(self) -> str:
        """Connection pool key."""
        return f"{self.scheme}://{self.host}:{self.port}"

    def mark_used(self) -> None:
        """Mark connection as in use."""
        self.is_available = False
        self.last_used_at = time.monotonic()
        self.requests_count += 1

    def mark_available(self) -> None:
        """Mark connection as available for reuse."""
        self.is_available = True
        self.last_used_at = time.monotonic()

    def is_expired(self, max_age: float) -> bool:
        """Check if connection has exceeded keepalive timeout."""
        return self.idle_time > max_age


class ConnectionPool:
    """
    Async connection pool.

    Manages connection lifecycle, reuse, and cleanup.

    Features:
    - Per-host connection limits
    - Global connection limit
    - Keepalive expiry
    - Automatic cleanup
    - Health tracking
    """

    __slots__ = (
        "_config",
        "_connections",
        "_locks",
        "_global_lock",
        "_stats",
        "_closed",
        "_cleanup_task",
    )

    def __init__(self, config: PoolConfig | None = None):
        """
        Initialize connection pool.

        Args:
            config: Pool configuration (uses defaults if None).
        """
        self._config = config or PoolConfig()
        self._connections: dict[str, list[PooledConnection]] = defaultdict(list)
        self._locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)
        self._global_lock = asyncio.Lock()
        self._stats = ConnectionStats()
        self._closed = False
        self._cleanup_task: asyncio.Task[None] | None = None

    @property
    def stats(self) -> ConnectionStats:
        """Get pool statistics."""
        return self._stats

    @property
    def config(self) -> PoolConfig:
        """Get pool configuration."""
        return self._config

    def _host_key(self, url: str) -> str:
        """Extract host key from URL."""
        parsed = urlparse(url)
        port = parsed.port or (443 if parsed.scheme == "https" else 80)
        return f"{parsed.scheme}://{parsed.hostname}:{port}"

    def _count_active(self) -> int:
        """Count total active connections."""
        count = 0
        for conns in self._connections.values():
            count += sum(1 for c in conns if not c.is_available)
        return count

    def _count_idle(self) -> int:
        """Count total idle connections."""
        count = 0
        for conns in self._connections.values():
            count += sum(1 for c in conns if c.is_available)
        return count

    async def acquire(
        self,
        url: str,
        *,
        timeout: float | None = None,
    ) -> PooledConnection | None:
        """
        Acquire a connection from the pool.

        Args:
            url: Target URL.
            timeout: Maximum time to wait for a connection.

        Returns:
            PooledConnection if available, None if new connection needed.

        Raises:
            ConnectionPoolExhaustedFault: If pool is exhausted and timeout expired.
        """
        if self._closed:
            raise ConnectionClosedFault("Connection pool is closed")

        key = self._host_key(url)
        lock = self._locks[key]

        start_time = time.monotonic()
        timeout = timeout if timeout is not None else 5.0

        while True:
            async with lock:
                # Try to reuse an existing connection
                connections = self._connections[key]

                for conn in connections:
                    if conn.is_available and not conn.is_expired(self._config.keepalive_expiry):
                        conn.mark_used()
                        self._stats.total_reused += 1
                        self._stats.active_connections = self._count_active()
                        self._stats.idle_connections = self._count_idle()
                        logger.debug(f"Reused connection for {key}")
                        return conn

                # Check if we can create a new connection
                host_count = len(connections)
                total_count = sum(len(c) for c in self._connections.values())

                can_create_for_host = host_count < self._config.max_connections_per_host
                can_create_global = total_count < self._config.max_connections

                if can_create_for_host and can_create_global:
                    # Return None to signal caller should create new connection
                    return None

            # Pool exhausted - wait and retry
            elapsed = time.monotonic() - start_time
            if elapsed >= timeout:
                self._stats.pool_exhausted_count += 1
                self._stats.failed_acquisitions += 1
                raise ConnectionPoolExhaustedFault(
                    f"Connection pool exhausted for {key}",
                    pool_size=self._config.max_connections,
                    active_connections=self._count_active(),
                )

            # Wait briefly before retrying
            await asyncio.sleep(0.1)

    async def add(
        self,
        url: str,
        connection: Any,
        *,
        is_http2: bool = False,
    ) -> PooledConnection:
        """
        Add a new connection to the pool.

        Args:
            url: Target URL.
            connection: Underlying transport connection.
            is_http2: Whether connection uses HTTP/2.

        Returns:
            PooledConnection wrapper.
        """
        parsed = urlparse(url)
        key = self._host_key(url)

        pooled = PooledConnection(
            host=parsed.hostname or "",
            port=parsed.port or (443 if parsed.scheme == "https" else 80),
            scheme=parsed.scheme,
            connection=connection,
            is_http2=is_http2,
        )
        pooled.mark_used()

        async with self._locks[key]:
            self._connections[key].append(pooled)
            self._stats.total_created += 1
            self._stats.active_connections = self._count_active()
            self._stats.idle_connections = self._count_idle()

        logger.debug(f"Added new connection for {key}")
        return pooled

    async def release(
        self,
        conn: PooledConnection,
        *,
        reusable: bool = True,
    ) -> None:
        """
        Release a connection back to the pool.

        Args:
            conn: Connection to release.
            reusable: Whether connection can be reused.
        """
        key = conn.key

        async with self._locks[key]:
            if reusable:
                conn.mark_available()
                self._stats.idle_connections = self._count_idle()
                logger.debug(f"Released connection for {key}")
            else:
                # Remove and close
                connections = self._connections[key]
                if conn in connections:
                    connections.remove(conn)
                    self._stats.total_closed += 1
                    await self._close_connection(conn)
                    logger.debug(f"Closed connection for {key}")

        self._stats.active_connections = self._count_active()

    async def remove(self, conn: PooledConnection) -> None:
        """Remove and close a connection."""
        await self.release(conn, reusable=False)

    async def _close_connection(self, conn: PooledConnection) -> None:
        """Close the underlying connection."""
        if conn.connection is None:
            return

        try:
            if hasattr(conn.connection, "close"):
                result = conn.connection.close()
                if asyncio.iscoroutine(result):
                    await result
        except Exception as e:
            logger.warning(f"Error closing connection: {e}")

    async def cleanup(self) -> int:
        """
        Clean up expired connections.

        Returns:
            Number of connections cleaned up.
        """
        cleaned = 0

        async with self._global_lock:
            for key in list(self._connections.keys()):
                async with self._locks[key]:
                    connections = self._connections[key]
                    expired = [c for c in connections if c.is_available and c.is_expired(self._config.keepalive_expiry)]

                    for conn in expired:
                        connections.remove(conn)
                        self._stats.total_closed += 1
                        await self._close_connection(conn)
                        cleaned += 1

                    # Remove empty keys
                    if not connections:
                        del self._connections[key]

        if cleaned:
            logger.debug(f"Cleaned up {cleaned} expired connections")
            self._stats.active_connections = self._count_active()
            self._stats.idle_connections = self._count_idle()

        return cleaned

    async def _cleanup_loop(self) -> None:
        """Background cleanup task."""
        while not self._closed:
            try:
                await asyncio.sleep(30)  # Cleanup every 30 seconds
                await self.cleanup()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup error: {e}")

    def start_cleanup_task(self) -> None:
        """Start background cleanup task."""
        if self._cleanup_task is None:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())

    async def close(self) -> None:
        """Close all connections and shutdown pool."""
        self._closed = True

        # Cancel cleanup task
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

        # Close all connections
        async with self._global_lock:
            for key in list(self._connections.keys()):
                async with self._locks[key]:
                    for conn in self._connections[key]:
                        await self._close_connection(conn)
                        self._stats.total_closed += 1
                    self._connections[key].clear()

        self._connections.clear()
        logger.info("Connection pool closed")

    async def __aenter__(self) -> ConnectionPool:
        """Async context manager entry."""
        self.start_cleanup_task()
        return self

    async def __aexit__(self, *exc: Any) -> None:
        """Async context manager exit."""
        await self.close()

    def __repr__(self) -> str:
        active = self._count_active()
        idle = self._count_idle()
        return f"<ConnectionPool active={active} idle={idle}>"


class ConnectionPoolManager:
    """
    Manager for multiple connection pools.

    Provides separate pools for different configurations or isolation.
    """

    __slots__ = ("_pools", "_default_config", "_lock")

    def __init__(self, default_config: PoolConfig | None = None):
        self._pools: dict[str, ConnectionPool] = {}
        self._default_config = default_config or PoolConfig()
        self._lock = asyncio.Lock()

    async def get_pool(
        self,
        name: str = "default",
        config: PoolConfig | None = None,
    ) -> ConnectionPool:
        """Get or create a named pool."""
        async with self._lock:
            if name not in self._pools:
                self._pools[name] = ConnectionPool(config or self._default_config)
                self._pools[name].start_cleanup_task()
            return self._pools[name]

    async def close_all(self) -> None:
        """Close all managed pools."""
        async with self._lock:
            for pool in self._pools.values():
                await pool.close()
            self._pools.clear()

    async def __aenter__(self) -> ConnectionPoolManager:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close_all()
