"""
SQLite Configuration — Extended pool and PRAGMA config for native SQLite.

Extends the framework's ``SqliteConfig`` with pool-specific and PRAGMA
knobs that the native module exposes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aquilia.db.configs import SqliteConfig

__all__ = [
    "SqlitePoolConfig",
    "JOURNAL_MODES",
    "SYNC_MODES",
    "TEMP_STORE_MODES",
]

# ── Valid PRAGMA values (allowlists) ─────────────────────────────────────

JOURNAL_MODES = frozenset({"DELETE", "TRUNCATE", "PERSIST", "MEMORY", "WAL", "OFF"})
SYNC_MODES = frozenset({"OFF", "NORMAL", "FULL", "EXTRA"})
TEMP_STORE_MODES = frozenset({"DEFAULT", "FILE", "MEMORY"})


@dataclass
class SqlitePoolConfig:
    """
    Comprehensive SQLite configuration for the native pool.

    Provides all PRAGMA knobs, pool sizing, statement cache capacity,
    query timeout, and security settings.

    Can be constructed from an existing ``SqliteConfig`` via
    :meth:`from_sqlite_config`.
    """

    # ── Database path ────────────────────────────────────────────────
    path: str = "db.sqlite3"

    # ── PRAGMAs ──────────────────────────────────────────────────────
    journal_mode: str = "WAL"
    foreign_keys: bool = True
    busy_timeout: int = 5000  # milliseconds
    synchronous: str = "NORMAL"  # NORMAL is safe under WAL
    cache_size: int = -8000  # negative = KiB (8 MiB)
    mmap_size: int = 268435456  # bytes (256 MiB)
    temp_store: str = "MEMORY"
    wal_autocheckpoint: int = 1000  # pages

    # ── Pool ─────────────────────────────────────────────────────────
    pool_size: int = 5  # reader connections
    pool_min_size: int = 2  # pre-opened readers
    pool_max_idle_time: float = 300.0  # seconds before idle eviction
    pool_timeout: float = 30.0  # seconds to wait for a connection

    # ── Statement cache ──────────────────────────────────────────────
    statement_cache_size: int = 256  # per connection

    # ── Query timeout ────────────────────────────────────────────────
    query_timeout: float = 30.0  # seconds, 0 = no timeout

    # ── Behaviour ────────────────────────────────────────────────────
    echo: bool = False  # log all SQL when True
    auto_commit: bool = True  # auto-commit outside transactions

    # ── Security ─────────────────────────────────────────────────────
    enforce_path_security: bool = True
    sandbox_root: str | None = None

    # ── Extra driver options ─────────────────────────────────────────
    options: dict[str, Any] = field(default_factory=dict)

    # ── Retry ────────────────────────────────────────────────────────
    connect_retries: int = 3
    connect_retry_delay: float = 0.5

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values."""
        from aquilia.faults.domains import ConfigInvalidFault

        jm = self.journal_mode.upper()
        if jm not in JOURNAL_MODES:
            raise ConfigInvalidFault(
                key="sqlite.journal_mode",
                reason=(
                    f"Invalid journal_mode {self.journal_mode!r}. Must be one of: {', '.join(sorted(JOURNAL_MODES))}"
                ),
            )
        self.journal_mode = jm

        sm = self.synchronous.upper()
        if sm not in SYNC_MODES:
            raise ConfigInvalidFault(
                key="sqlite.synchronous",
                reason=(f"Invalid synchronous {self.synchronous!r}. Must be one of: {', '.join(sorted(SYNC_MODES))}"),
            )
        self.synchronous = sm

        ts = self.temp_store.upper()
        if ts not in TEMP_STORE_MODES:
            raise ConfigInvalidFault(
                key="sqlite.temp_store",
                reason=(
                    f"Invalid temp_store {self.temp_store!r}. Must be one of: {', '.join(sorted(TEMP_STORE_MODES))}"
                ),
            )
        self.temp_store = ts

        if self.busy_timeout < 0:
            raise ConfigInvalidFault(
                key="sqlite.busy_timeout",
                reason=f"busy_timeout must be >= 0, got {self.busy_timeout}",
            )

        if self.pool_size < 1:
            raise ConfigInvalidFault(
                key="sqlite.pool_size",
                reason=f"pool_size must be >= 1, got {self.pool_size}",
            )

        if self.pool_min_size < 0:
            raise ConfigInvalidFault(
                key="sqlite.pool_min_size",
                reason=f"pool_min_size must be >= 0, got {self.pool_min_size}",
            )

        if self.pool_min_size > self.pool_size:
            raise ConfigInvalidFault(
                key="sqlite.pool_min_size",
                reason=(f"pool_min_size ({self.pool_min_size}) must be <= pool_size ({self.pool_size})"),
            )

        if self.statement_cache_size < 0:
            raise ConfigInvalidFault(
                key="sqlite.statement_cache_size",
                reason=f"statement_cache_size must be >= 0, got {self.statement_cache_size}",
            )

    @classmethod
    def from_sqlite_config(cls, cfg: SqliteConfig, **overrides: Any) -> SqlitePoolConfig:
        """
        Create a ``SqlitePoolConfig`` from an existing ``SqliteConfig``.

        Transfers all compatible fields and applies overrides.

        Args:
            cfg: An existing ``SqliteConfig`` from ``aquilia.db.configs``.
            **overrides: Additional fields to override.

        Returns:
            A new ``SqlitePoolConfig`` with fields populated from *cfg*.
        """
        kwargs: dict[str, Any] = {
            "path": cfg.path,
            "journal_mode": cfg.journal_mode,
            "foreign_keys": cfg.foreign_keys,
            "busy_timeout": cfg.busy_timeout,
            "pool_size": cfg.pool_size,
            "pool_min_size": cfg.pool_min_size,
            "echo": cfg.echo,
            "connect_retries": cfg.connect_retries,
            "connect_retry_delay": cfg.connect_retry_delay,
        }
        if cfg.options:
            kwargs["options"] = dict(cfg.options)
        kwargs.update(overrides)
        return cls(**kwargs)

    @classmethod
    def from_url(cls, url: str, **overrides: Any) -> SqlitePoolConfig:
        """
        Create from a ``sqlite:///`` URL string.

        Args:
            url: SQLite URL (e.g. ``sqlite:///db.sqlite3``).
            **overrides: Additional config overrides.

        Returns:
            A new ``SqlitePoolConfig``.
        """
        path = url
        for prefix in ("sqlite:///", "sqlite://"):
            if url.startswith(prefix):
                path = url[len(prefix) :]
                break
        if not path:
            path = ":memory:"
        return cls(path=path, **overrides)

    def to_url(self) -> str:
        """Generate a ``sqlite:///`` URL from this config."""
        if self.path == ":memory:":
            return "sqlite:///:memory:"
        return f"sqlite:///{self.path}"

    @property
    def is_memory(self) -> bool:
        """True if this is an in-memory database."""
        return self.path == ":memory:" or ":memory:" in self.path
