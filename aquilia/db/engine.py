"""
Aquilia Database Engine -- async-first, multi-backend, production-ready.

Provides:
- AquiliaDatabase: async connection manager delegating to backend adapters
- SQLite (native aquilia.sqlite), PostgreSQL (asyncpg), MySQL (aiomysql), Oracle (oracledb) backends
- Typed config classes: SqliteConfig, PostgresConfig, MysqlConfig, OracleConfig
- Full integration with AquilaFaults and DI container
- Lifecycle hooks for startup/shutdown
- Connection health checks and reconnection
- Multi-database routing support
"""

from __future__ import annotations

import asyncio
import logging
import re
import sys
import time
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from typing import Any

from aquilia.db.backends.base import AdapterCapabilities, ColumnInfo, DatabaseAdapter
from aquilia.db.configs import DatabaseConfig
from aquilia.di.decorators import service
from aquilia.faults.domains import DatabaseConnectionFault, QueryFault, SchemaFault

logger = logging.getLogger("aquilia.db")


# ── Backward-compatible alias ────────────────────────────────────────────────
DatabaseError = DatabaseConnectionFault

# Sanitize savepoint names to prevent SQL injection
import re

_SP_NAME_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

from contextvars import ContextVar

current_model_var: ContextVar[str] = ContextVar("current_model", default="")

_inspector_checked = False
_inspector_instance = None

# ---------------------------------------------------------------------------
# Query observability gate
# ---------------------------------------------------------------------------
# A diagnostic must be free when it is disabled.
#
# `_notify_inspector` used to run unconditionally on all four query paths,
# including in `mode="prod"`. It called `traceback.extract_stack()` -- which
# walks every Python frame and resolves source lines through `linecache`,
# stat()ing files -- to build a "source" string for a dev-mode UI. Measured at
# 32us per query, ~26% of total query time, and 160us per `/queries?queries=5`
# request. Nothing read the result in production.
#
# The flag is resolved once at startup by `enable_query_inspection()`, called
# from the inspector integration. When it is False the call site is a single
# global load and a branch, which is what "free" has to mean on a path that
# executes once per query.
_QUERY_INSPECTION: bool = False


def enable_query_inspection(enabled: bool = True) -> None:
    """Turn per-query inspector recording on or off process-wide.

    Called by the inspector/admin integration during startup. Not intended to be
    toggled per request: the point of the flag is that the disabled path costs a
    branch, and re-deciding per query would reintroduce the overhead it removes.

    Args:
        enabled: Whether to record spans and stack sources for each query.
    """
    global _QUERY_INSPECTION
    _QUERY_INSPECTION = enabled


def query_inspection_enabled() -> bool:
    """Whether per-query inspector recording is currently active."""
    return _QUERY_INSPECTION


def _caller_location(max_depth: int = 12) -> tuple[str, str]:
    """Find the nearest non-framework caller as ``(source, summary)``.

    Uses ``sys._getframe`` rather than ``traceback.extract_stack()``: the latter
    builds a ``FrameSummary`` per frame and resolves each one's source line
    through ``linecache``, which stat()s the file. This walks raw frames, reads
    two already-materialised ``str`` attributes, and stops at the first match.

    Args:
        max_depth: Frames to inspect before giving up. Bounded so a deep stack
            cannot make this expensive.

    Returns:
        ``(source, stack_summary)``, both empty when no caller qualifies.
    """
    try:
        frame = sys._getframe(2)
    except ValueError:  # pragma: no cover - stack shallower than expected
        return "", ""
    depth = 0
    while frame is not None and depth < max_depth:
        filename = frame.f_code.co_filename
        if "/aquilia/" not in filename and "site-packages" not in filename:
            lineno = frame.f_lineno
            return f"{filename}:{lineno}", f"{frame.f_code.co_name}() at {filename}:{lineno}"
        frame = frame.f_back
        depth += 1
    return "", ""


def _sanitize_savepoint(name: str) -> str:
    """Validate savepoint names -- only alphanumeric + underscore allowed."""
    if not _SP_NAME_RE.match(name):
        raise QueryFault(
            model="<transaction>",
            operation="savepoint",
            reason=f"Invalid savepoint name: {name!r}. Use alphanumeric + underscore only.",
        )
    return name


def _create_adapter(driver: str) -> DatabaseAdapter:
    """Factory -- instantiate the correct backend adapter."""
    if driver == "sqlite":
        from aquilia.db.backends.sqlite import SQLiteAdapter

        return SQLiteAdapter()
    elif driver == "postgresql":
        from aquilia.db.backends.postgres import PostgresAdapter

        return PostgresAdapter()
    elif driver == "mysql":
        from aquilia.db.backends.mysql import MySQLAdapter

        return MySQLAdapter()
    elif driver == "oracle":
        from aquilia.db.backends.oracle import OracleAdapter

        return OracleAdapter()
    else:
        raise DatabaseConnectionFault(
            url=f"<{driver}>",
            reason=f"No adapter registered for driver: {driver}",
        )


@service(scope="app", name="AquiliaDatabase")
class AquiliaDatabase:
    """
    Async database engine for Aquilia.

    Delegates all operations to the appropriate backend adapter
    (SQLite, PostgreSQL, or MySQL). All operations are async and
    use parameterized queries with ``?`` placeholders -- the adapter
    translates to the backend's native param style automatically.

    Integrates with:
    - **AquilaFaults**: raises ``DatabaseConnectionFault``, ``QueryFault``,
      ``SchemaFault`` instead of bare exceptions.
    - **DI**: decorated with ``@service(scope="app")``; resolvable from
      Aquilia's dependency-injection container.
    - **Lifecycle**: exposes ``on_startup`` / ``on_shutdown`` hooks for the
      ``LifecycleCoordinator``.

    Usage:
        db = AquiliaDatabase("sqlite:///app.db")
        await db.connect()
        rows = await db.fetch_all("SELECT * FROM users WHERE active = ?", [True])
        await db.disconnect()

        # PostgreSQL:
        db = AquiliaDatabase("postgresql://user:pass@localhost/mydb")
        await db.connect()

        # MySQL:
        db = AquiliaDatabase("mysql://user:pass@localhost/mydb")
        await db.connect()
    """

    __slots__ = (
        "_url",
        "_driver",
        "_adapter",
        "_connected",
        "_lock",
        "_options",
        "_in_transaction",
        "_last_activity",
        "_connect_retries",
        "_connect_retry_delay",
        "_config",
    )

    def __init__(
        self,
        url: str | None = None,
        *,
        config: DatabaseConfig | None = None,
        **options: Any,
    ):
        """
        Initialize database engine.

        Accepts either a URL string or a typed DatabaseConfig object.
        Config objects take precedence over URL if both are provided.

        Args:
            url: Database URL. Supported schemes:
                 - sqlite:///path/to/db.sqlite3
                 - sqlite:///:memory:
                 - postgresql://user:pass@host/db
                 - mysql://user:pass@host/db
                 - oracle://user:pass@host:port/service
            config: Typed DatabaseConfig (SqliteConfig, PostgresConfig,
                    MysqlConfig, OracleConfig). If provided, url is ignored.
            **options: Driver-specific options passed to the backend adapter.
                connect_retries (int): Number of connection retries (default 3).
                connect_retry_delay (float): Seconds between retries (default 0.5).
        """
        self._config: DatabaseConfig | None = config

        if config is not None:
            self._url = config.to_url()
            # Merge config engine options with explicit overrides
            cfg_opts = config.get_engine_options()
            cfg_opts.update(options)
            options = cfg_opts
        else:
            self._url = url or "sqlite:///db.sqlite3"

        self._driver = self._detect_driver(self._url)
        self._adapter: DatabaseAdapter = _create_adapter(self._driver)
        self._connected = False
        self._lock = asyncio.Lock()
        self._options = options
        self._in_transaction = False
        self._last_activity: float = 0.0
        self._connect_retries = int(options.pop("connect_retries", 3))
        self._connect_retry_delay = float(options.pop("connect_retry_delay", 0.5))

    @staticmethod
    def _detect_driver(url: str) -> str:
        """Detect database driver from URL scheme."""
        if url.startswith("sqlite"):
            return "sqlite"
        elif url.startswith("postgresql") or url.startswith("postgres"):
            return "postgresql"
        elif url.startswith("mysql"):
            return "mysql"
        elif url.startswith("oracle"):
            return "oracle"
        else:
            raise DatabaseConnectionFault(
                url=url,
                reason=f"Unsupported database URL scheme: {url}",
            )

    # ── Lifecycle hooks ──────────────────────────────────────────────

    async def on_startup(self) -> None:
        """Lifecycle hook -- called by ``LifecycleCoordinator`` at app start."""
        await self.connect()

    async def on_shutdown(self) -> None:
        """Lifecycle hook -- called by ``LifecycleCoordinator`` at app stop."""
        await self.disconnect()

    # ── Connection management ────────────────────────────────────────

    async def connect(self) -> None:
        """Open database connection with retry logic."""
        if self._connected:
            return

        async with self._lock:
            if self._connected:
                return

            last_exc: Exception | None = None
            for attempt in range(1, self._connect_retries + 1):
                try:
                    await self._adapter.connect(self._url, **self._options)
                    self._connected = True
                    self._last_activity = time.monotonic()
                    return
                except (DatabaseConnectionFault, ImportError):
                    raise
                except Exception as exc:
                    last_exc = exc
                    if attempt < self._connect_retries:
                        logger.warning(
                            f"Connection attempt {attempt} failed: {exc}, retrying in {self._connect_retry_delay}s..."
                        )
                        await asyncio.sleep(self._connect_retry_delay)

            raise DatabaseConnectionFault(
                url=self._url,
                reason=f"Failed after {self._connect_retries} attempts: {last_exc}",
            )

    async def disconnect(self) -> None:
        """Close database connection."""
        if not self._connected:
            return
        async with self._lock:
            if not self._connected:
                return
            try:
                await self._adapter.disconnect()
                self._connected = False
            except Exception as exc:
                self._connected = False
                raise DatabaseConnectionFault(
                    url=self._url,
                    reason=f"Disconnect failed: {exc}",
                ) from exc

    async def ensure_connected(self) -> None:
        """Ensure a live connection exists, reconnecting if needed."""
        if not self._connected:
            await self.connect()
        elif not self._adapter.is_connected:
            self._connected = False
            await self.connect()

    async def begin(self, isolation: str | None = None, readonly: bool = False) -> None:
        """
        Start a transaction on the backend adapter directly.

        This pins a dedicated connection (the writer, for SQLite, unless
        ``readonly=True``) and disables per-statement auto-commit on it --
        unlike sending literal ``"BEGIN"`` text through ``execute()``, which
        the adapter treats as an ordinary auto-committed statement.
        """
        await self.ensure_connected()
        await self._adapter.begin(isolation=isolation, readonly=readonly)
        self._in_transaction = True

    async def commit(self) -> None:
        """Commit the transaction started by :meth:`begin` and release its connection."""
        await self._adapter.commit()
        self._in_transaction = False

    async def rollback(self) -> None:
        """Roll back the transaction started by :meth:`begin` and release its connection."""
        await self._adapter.rollback()
        self._in_transaction = False

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[None]:
        """
        Async context manager for transactions.

        Delegates to the backend adapter's transaction management.

        Usage:
            async with db.transaction():
                await db.execute("INSERT INTO ...")
                await db.execute("UPDATE ...")
        """
        await self.begin()
        try:
            yield
            await self.commit()
        except Exception:
            await self.rollback()
            raise

    async def savepoint(self, name: str) -> None:
        """Create a named savepoint within a transaction."""
        name = _sanitize_savepoint(name)
        await self.ensure_connected()
        await self._adapter.savepoint(name)

    async def release_savepoint(self, name: str) -> None:
        """Release (commit) a named savepoint."""
        name = _sanitize_savepoint(name)
        await self.ensure_connected()
        await self._adapter.release_savepoint(name)

    async def rollback_to_savepoint(self, name: str) -> None:
        """Roll back to a named savepoint."""
        name = _sanitize_savepoint(name)
        await self.ensure_connected()
        await self._adapter.rollback_to_savepoint(name)

    # ── Query Inspector integration ──────────────────────────────────

    @staticmethod
    def _notify_inspector(
        sql: str,
        params: Any,
        duration_ms: float,
        rows_affected: int = 0,
        model: str = "",
        db: AquiliaDatabase | None = None,
    ) -> None:
        """Record a query span in the active trace, or fall back to QueryInspector.

        Callers must gate this on ``_QUERY_INSPECTION``; it is never free enough
        to call unconditionally on a query path.
        """
        try:
            from aquilia.inspector.trace import Lane, SpanStatus, current_trace

            trace = current_trace()
            if trace is not None:
                if not model:
                    model = current_model_var.get()

                source, stack_summary = _caller_location()

                # Get collector config for param redaction
                from aquilia.inspector.collector import _COLLECTOR
                from aquilia.inspector.config import InspectorConfig
                from aquilia.inspector.redaction import redact_body_keys_recursive

                config = _COLLECTOR._config if _COLLECTOR is not None else InspectorConfig()
                redacted_params = redact_body_keys_recursive(params, config.redact_body_keys) if params else None

                now_offset = (time.monotonic() - trace.started_monotonic) * 1000.0
                span = trace.add_span(
                    lane=Lane.DATABASE,
                    label=sql,
                    start_offset_ms=max(0.0, now_offset - duration_ms),
                    duration_ms=duration_ms,
                    status=SpanStatus.OK,
                    detail={
                        "model": model or "",
                        "rows": rows_affected,
                        "params": redacted_params,
                        "stack_summary": stack_summary,
                        "explain_plan": "",
                    },
                    source=source,
                )

                # Run EXPLAIN in background if slow
                if sql.strip().upper().startswith("SELECT"):
                    slow_threshold = (
                        config.slow_request_threshold_ms / 10.0
                        if hasattr(config, "slow_request_threshold_ms")
                        else 50.0
                    )
                    is_slow = duration_ms >= slow_threshold
                    if is_slow and db is not None:
                        import asyncio

                        asyncio.create_task(db._run_explain_plan(sql, params, span))
                return
        except Exception:
            pass

        # Fallback to direct QueryInspector recording when out of request trace
        global _inspector_checked, _inspector_instance
        if not _inspector_checked:
            try:
                from aquilia.admin.query_inspector import get_query_inspector

                _inspector_instance = get_query_inspector()
            except Exception:
                _inspector_instance = None
            _inspector_checked = True

        if _inspector_instance is not None:
            try:
                if not model:
                    model = current_model_var.get()
                _inspector_instance.record(
                    sql=sql,
                    params=params,
                    duration_ms=duration_ms,
                    rows_affected=rows_affected,
                    model=model,
                )
            except Exception:
                pass

    async def _run_explain_plan(self, sql: str, params: Any, span: Any) -> None:
        try:
            dialect = self.dialect
            if dialect == "sqlite":
                explain_sql = f"EXPLAIN QUERY PLAN {sql}"
            elif dialect == "postgresql":
                explain_sql = f"EXPLAIN (FORMAT TEXT) {sql}"
            elif dialect == "mysql":
                explain_sql = f"EXPLAIN {sql}"
            else:
                explain_sql = f"EXPLAIN {sql}"

            rows = await self._adapter.fetch_all(explain_sql, params)
            plan = "\n".join(str(row) for row in rows)
            span.detail["explain_plan"] = plan
        except Exception:
            pass

    # ── Query execution ──────────────────────────────────────────────

    async def execute(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
        model: str = "",
    ) -> Any:
        """
        Execute a SQL statement.

        Args:
            sql: SQL query with ? placeholders (auto-adapted per backend)
            params: Parameter values
            model: Optional ORM model name

        Returns:
            Cursor-like object (exposes lastrowid, rowcount)

        Raises:
            QueryFault: When query execution fails
        """
        await self.ensure_connected()

        if params is None:
            params = []
        try:
            self._last_activity = time.monotonic()
            _t0 = time.perf_counter() if _QUERY_INSPECTION else 0.0
            result = await self._adapter.execute(sql, params)
            if _QUERY_INSPECTION:
                _dur = (time.perf_counter() - _t0) * 1000
                self._notify_inspector(
                    sql,
                    params,
                    _dur,
                    rows_affected=getattr(result, "rowcount", 0),
                    model=model,
                    db=self,
                )
            return result
        except (DatabaseConnectionFault, QueryFault, SchemaFault):
            raise
        except Exception as exc:
            raise QueryFault(
                model="<raw>",
                operation="execute",
                reason=str(exc),
                metadata={"sql": sql[:200]},
            ) from exc

    async def execute_many(
        self,
        sql: str,
        params_list: Sequence[Sequence[Any]],
        model: str = "",
    ) -> None:
        """Execute a SQL statement with multiple parameter sets."""
        await self.ensure_connected()
        try:
            self._last_activity = time.monotonic()
            await self._adapter.execute_many(sql, params_list)
        except (DatabaseConnectionFault, QueryFault, SchemaFault):
            raise
        except Exception as exc:
            raise QueryFault(
                model="<raw>",
                operation="execute_many",
                reason=str(exc),
                metadata={"sql": sql[:200]},
            ) from exc

    async def fetch_all(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
        model: str = "",
    ) -> list[dict[str, Any]]:
        """
        Execute query and return all rows as dicts.

        Args:
            sql: SELECT query with ? placeholders
            params: Parameter values
            model: Optional ORM model name

        Returns:
            List of row dicts

        Raises:
            QueryFault: When query execution fails
        """
        await self.ensure_connected()

        if params is None:
            params = []
        try:
            self._last_activity = time.monotonic()
            _t0 = time.perf_counter() if _QUERY_INSPECTION else 0.0
            rows = await self._adapter.fetch_all(sql, params)
            if _QUERY_INSPECTION:
                _dur = (time.perf_counter() - _t0) * 1000
                self._notify_inspector(sql, params, _dur, rows_affected=len(rows), model=model, db=self)
            return rows
        except (DatabaseConnectionFault, QueryFault, SchemaFault):
            raise
        except Exception as exc:
            raise QueryFault(
                model="<raw>",
                operation="fetch_all",
                reason=str(exc),
                metadata={"sql": sql[:200]},
            ) from exc

    async def fetch_one(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
        model: str = "",
    ) -> dict[str, Any] | None:
        """
        Execute query and return first row as dict, or None.

        Raises:
            QueryFault: When query execution fails
        """
        await self.ensure_connected()

        if params is None:
            params = []
        try:
            self._last_activity = time.monotonic()
            _t0 = time.perf_counter() if _QUERY_INSPECTION else 0.0
            row = await self._adapter.fetch_one(sql, params)
            if _QUERY_INSPECTION:
                _dur = (time.perf_counter() - _t0) * 1000
                self._notify_inspector(sql, params, _dur, rows_affected=1 if row else 0, model=model, db=self)
            return row
        except (DatabaseConnectionFault, QueryFault, SchemaFault):
            raise
        except Exception as exc:
            raise QueryFault(
                model="<raw>",
                operation="fetch_one",
                reason=str(exc),
                metadata={"sql": sql[:200]},
            ) from exc

    async def fetch_val(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
        model: str = "",
    ) -> Any:
        """
        Execute query and return scalar value from first row, first column.

        Raises:
            QueryFault: When query execution fails
        """
        await self.ensure_connected()

        if params is None:
            params = []
        try:
            self._last_activity = time.monotonic()
            _t0 = time.perf_counter() if _QUERY_INSPECTION else 0.0
            val = await self._adapter.fetch_val(sql, params)
            if _QUERY_INSPECTION:
                _dur = (time.perf_counter() - _t0) * 1000
                self._notify_inspector(
                    sql, params, _dur, rows_affected=1 if val is not None else 0, model=model, db=self
                )
            return val
        except (DatabaseConnectionFault, QueryFault, SchemaFault):
            raise
        except Exception as exc:
            raise QueryFault(
                model="<raw>",
                operation="fetch_val",
                reason=str(exc),
                metadata={"sql": sql[:200]},
            ) from exc

    # ── Introspection (delegated to adapter) ─────────────────────────

    async def table_exists(self, table_name: str) -> bool:
        """Check if a table exists in the database."""
        await self.ensure_connected()
        return await self._adapter.table_exists(table_name)

    async def get_tables(self) -> list[str]:
        """List all table names in the database."""
        await self.ensure_connected()
        return await self._adapter.get_tables()

    async def get_columns(self, table_name: str) -> list[ColumnInfo]:
        """Get column metadata for a table."""
        await self.ensure_connected()
        return await self._adapter.get_columns(table_name)

    # ── Properties ───────────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return self._connected and self._adapter.is_connected

    @property
    def url(self) -> str:
        return self._url

    @property
    def driver(self) -> str:
        return self._driver

    @property
    def dialect(self) -> str:
        """Return the SQL dialect name (sqlite, postgresql, mysql)."""
        return self._adapter.dialect

    @property
    def capabilities(self) -> AdapterCapabilities:
        """Return backend capabilities."""
        return self._adapter.capabilities

    @property
    def adapter(self) -> DatabaseAdapter:
        """Direct access to the underlying adapter (advanced use)."""
        return self._adapter

    @property
    def in_transaction(self) -> bool:
        return self._in_transaction


# ── Module-level singleton accessor ─────────────────────────────────────────

_default_database: AquiliaDatabase | None = None
_database_registry: dict[str, AquiliaDatabase] = {}


def get_database(alias: str | None = None) -> AquiliaDatabase:
    """
    Get a database instance by alias, or the default.

    Args:
        alias: Optional database alias for multi-database setups.
               Use "default" or None for the primary database.

    Raises:
        DatabaseConnectionFault: If no database is configured.
    """
    if alias and alias != "default":
        db = _database_registry.get(alias)
        if db is None:
            raise DatabaseConnectionFault(
                url=f"<alias:{alias}>",
                reason=f"No database configured with alias '{alias}'. Available: {list(_database_registry.keys())}",
            )
        return db

    global _default_database
    if _default_database is None:
        raise DatabaseConnectionFault(
            url="<not configured>",
            reason=("No database configured. Call configure_database() first or set database URL in aquilia config."),
        )
    return _default_database


def configure_database(
    url: str | None = None,
    *,
    config: DatabaseConfig | None = None,
    alias: str = "default",
    **options: Any,
) -> AquiliaDatabase:
    """
    Configure and return a database instance.

    Accepts either a URL string or a typed DatabaseConfig object.

    Args:
        url: Database connection URL (ignored if config is provided)
        config: Typed DatabaseConfig (SqliteConfig, PostgresConfig,
                MysqlConfig, OracleConfig)
        alias: Database alias for multi-database setups (default "default")
        **options: Driver-specific options

    Returns:
        AquiliaDatabase instance

    Examples:
        # URL-based (backward compatible):
        db = configure_database("sqlite:///db.sqlite3")

        # Config-based:
        db = configure_database(config=PostgresConfig(
            host="localhost",
            name="mydb",
            user="admin",
            password="secret",
        ))

        # Multi-database:
        configure_database(config=pg_config, alias="primary")
        configure_database(config=sqlite_config, alias="cache")
    """
    if config is not None:
        db = AquiliaDatabase(config=config, **options)
    else:
        db = AquiliaDatabase(url or "sqlite:///db.sqlite3", **options)

    _database_registry[alias] = db

    if alias == "default":
        global _default_database
        _default_database = db

    return db


def set_database(db: AquiliaDatabase, *, alias: str = "default") -> None:
    """Set an externally-created database as the default or by alias."""
    _database_registry[alias] = db
    if alias == "default":
        global _default_database
        _default_database = db


def get_all_databases() -> dict[str, AquiliaDatabase]:
    """Return all configured database instances."""
    return dict(_database_registry)
