"""
SQLite Service — DI-integrated pool lifecycle management.

Provides a ``SqliteService`` class decorated with ``@service(scope="app")``
for automatic startup/shutdown of the connection pool within the Aquilia
DI container.
"""

from __future__ import annotations

import logging

from aquilia.di.decorators import service

from ._config import SqlitePoolConfig
from ._metrics import SqliteMetrics
from ._pool import ConnectionPool

logger = logging.getLogger("aquilia.sqlite.service")

__all__ = ["SqliteService"]


@service(scope="app", name="SqliteService")
class SqliteService:
    """
    DI-managed SQLite connection pool.

    Register this service to have the pool automatically created at
    server startup and closed at shutdown.

    Usage in workspace config::

        from aquilia.sqlite import SqliteService, SqlitePoolConfig

        config = SqlitePoolConfig(path="db.sqlite3")
        svc = SqliteService(config)
        # The lifecycle coordinator calls svc.startup() / svc.shutdown()

    From a controller::

        from aquilia.di import Inject
        from aquilia.sqlite import SqliteService

        class UserController:
            db: SqliteService = Inject()

            async def list_users(self):
                rows = await self.db.pool.fetch_all("SELECT * FROM users")
                return rows
    """

    __slots__ = ("_config", "_pool", "_metrics")

    def __init__(
        self,
        config: SqlitePoolConfig | None = None,
    ) -> None:
        self._config = config or SqlitePoolConfig()
        self._pool: ConnectionPool | None = None
        self._metrics = SqliteMetrics()

    async def startup(self) -> None:
        """
        Open the connection pool.

        Called by the lifecycle coordinator during server startup.
        """
        if self._pool is not None:
            return

        self._pool = ConnectionPool(self._config, metrics=self._metrics)
        await self._pool.open()
        logger.info("SqliteService started (path=%s)", self._config.path)

    async def shutdown(self) -> None:
        """
        Close the connection pool.

        Called by the lifecycle coordinator during server shutdown.
        """
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            logger.info("SqliteService stopped")

    @property
    def pool(self) -> ConnectionPool:
        """
        The underlying connection pool.

        Raises:
            RuntimeError: If the service has not been started.
        """
        if self._pool is None:
            from aquilia.faults.domains import DatabaseConnectionFault

            raise DatabaseConnectionFault(
                backend="sqlite",
                reason=("SqliteService not started. Call startup() first or register with the lifecycle coordinator."),
            )
        return self._pool

    @property
    def metrics(self) -> SqliteMetrics:
        """Pool metrics."""
        return self._metrics

    @property
    def is_running(self) -> bool:
        """Whether the service is running."""
        return self._pool is not None and self._pool.is_open
