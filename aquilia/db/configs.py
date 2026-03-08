"""
Aquilia Database Configuration Classes -- Developer-Friendly Typed Configs.

Provides typed, validated configuration dataclasses for each database backend,
with Python-native developer ergonomics using dataclasses and fluent builders.

Supported backends:
    - SqliteConfig     → SQLite via aiosqlite
    - PostgresConfig   → PostgreSQL via asyncpg
    - MysqlConfig      → MySQL/MariaDB via aiomysql
    - OracleConfig     → Oracle via python-oracledb

Usage:
    from aquilia.db.configs import PostgresConfig, SqliteConfig

    # Typed config -- IDE autocompletion, validation, no URL typos:
    db = PostgresConfig(
        host="localhost",
        port=5432,
        database="mydb",       # or name="mydb" -- both work
        user="admin",
        password="secret",
        pool_size=10,
    )

    # Still works with URL:
    db = PostgresConfig.from_url("postgresql://admin:secret@localhost:5432/mydb")

    # Use in workspace:
    .integrate(Integration.database(config=db))

    # Or just a URL (backward compatible):
    .integrate(Integration.database(url="sqlite:///db.sqlite3"))
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional, Union
from urllib.parse import urlparse, quote_plus


__all__ = [
    "DatabaseConfig",
    "SqliteConfig",
    "PostgresConfig",
    "MysqlConfig",
    "OracleConfig",
]


@dataclass
class DatabaseConfig:
    """
    Base database configuration.

    All backend-specific configs inherit from this.
    Provides the common interface for URL generation,
    serialization, and validation.
    """

    # Connection
    engine: str = "sqlite"

    # Pool settings
    pool_size: int = 5
    pool_min_size: int = 2
    pool_max_size: int = 10

    # Behavior
    echo: bool = False
    auto_connect: bool = True
    auto_create: bool = True
    auto_migrate: bool = False
    migrations_dir: str = "migrations"

    # Connection resilience
    connect_retries: int = 3
    connect_retry_delay: float = 0.5
    conn_max_age: int = 0  # 0 = close after each request
    conn_health_checks: bool = False

    # Additional driver-specific options
    options: Dict[str, Any] = field(default_factory=dict)

    def to_url(self) -> str:
        """
        Generate a database connection URL.

        Override in subclasses for backend-specific URL formats.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement to_url()"
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to a flat dictionary for integration with ConfigLoader.
        
        Returns:
            Configuration dictionary with 'url' key and all settings.
        """
        d = {
            "enabled": True,
            "engine": self.engine,
            "url": self.to_url(),
            "auto_connect": self.auto_connect,
            "auto_create": self.auto_create,
            "auto_migrate": self.auto_migrate,
            "migrations_dir": self.migrations_dir,
            "pool_size": self.pool_size,
            "pool_min_size": self.pool_min_size,
            "pool_max_size": self.pool_max_size,
            "echo": self.echo,
            "connect_retries": self.connect_retries,
            "connect_retry_delay": self.connect_retry_delay,
            "conn_max_age": self.conn_max_age,
            "conn_health_checks": self.conn_health_checks,
        }
        if self.options:
            d["options"] = self.options
        return d

    def get_engine_options(self) -> Dict[str, Any]:
        """
        Get kwargs to pass to AquiliaDatabase / adapter.

        Returns:
            Dict of driver-specific connection options.
        """
        opts = {
            "connect_retries": self.connect_retries,
            "connect_retry_delay": self.connect_retry_delay,
        }
        opts.update(self.options)
        return opts

    @classmethod
    def from_url(cls, url: str, **overrides) -> "DatabaseConfig":
        """
        Create a config from a URL string.

        Auto-detects backend from URL scheme and returns the
        appropriate subclass.

        Args:
            url: Database connection URL
            **overrides: Additional config overrides

        Returns:
            Backend-specific DatabaseConfig subclass instance
        """
        if url.startswith("sqlite"):
            return SqliteConfig.from_url(url, **overrides)
        elif url.startswith("postgresql") or url.startswith("postgres"):
            return PostgresConfig.from_url(url, **overrides)
        elif url.startswith("mysql"):
            return MysqlConfig.from_url(url, **overrides)
        elif url.startswith("oracle"):
            return OracleConfig.from_url(url, **overrides)
        else:
            raise ValueError(f"Unsupported database URL scheme: {url}")

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(engine={self.engine!r})"


@dataclass
class SqliteConfig(DatabaseConfig):
    """
    SQLite database configuration.

    Args:
        path: Path to SQLite database file.
               Use ":memory:" for in-memory database.
        journal_mode: WAL (default), DELETE, TRUNCATE, PERSIST, MEMORY, OFF
        foreign_keys: Enable PRAGMA foreign_keys (default True)
        busy_timeout: PRAGMA busy_timeout in ms (default 5000)

    Examples:
        # File-based:
        SqliteConfig(path="db.sqlite3")

        # In-memory:
        SqliteConfig(path=":memory:")

        # Full options:
        SqliteConfig(
            path="data/app.db",
            journal_mode="WAL",
            foreign_keys=True,
            auto_create=True,
            auto_migrate=True,
        )
    """

    engine: str = "sqlite"
    path: str = "db.sqlite3"
    journal_mode: str = "WAL"
    foreign_keys: bool = True
    busy_timeout: int = 5000

    def to_url(self) -> str:
        if self.path == ":memory:":
            return "sqlite:///:memory:"
        return f"sqlite:///{self.path}"

    @classmethod
    def from_url(cls, url: str, **overrides) -> "SqliteConfig":
        """Parse a sqlite:// URL into a SqliteConfig."""
        path = url
        for prefix in ("sqlite:///", "sqlite://"):
            if url.startswith(prefix):
                path = url[len(prefix):]
                break
        if not path:
            path = ":memory:"
        return cls(path=path, **overrides)

    def __repr__(self) -> str:
        return f"SqliteConfig(path={self.path!r})"


@dataclass
class PostgresConfig(DatabaseConfig):
    """
    PostgreSQL database configuration.

    Args:
        host: Database server hostname
        port: Database server port (default 5432)
        name: Database name (or use ``database`` as an alias)
        database: Alias for ``name`` -- use whichever feels natural
        user: Database user
        password: Database password
        schema: Default schema (default "public")
        sslmode: SSL mode (disable, allow, prefer, require, verify-ca, verify-full)

    Examples:
        # Simple:
        PostgresConfig(
            host="localhost",
            database="mydb",
            user="admin",
            password="secret",
        )

        # Also works with 'name':
        PostgresConfig(
            host="localhost",
            name="mydb",
            user="admin",
            password="secret",
        )

        # Production with SSL:
        PostgresConfig(
            host="db.example.com",
            port=5432,
            database="prod_db",
            user="app_user",
            password="strong_password",
            sslmode="require",
            pool_size=20,
            pool_max_size=50,
            conn_health_checks=True,
        )
    """

    engine: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    name: str = ""
    database: str = ""  # Alias for 'name' -- use whichever feels natural
    user: str = ""
    password: str = ""
    schema: str = "public"
    sslmode: str = "prefer"

    def __post_init__(self):
        # Resolve 'database' → 'name' alias.  'database' wins if 'name' is empty.
        if self.database and not self.name:
            self.name = self.database
        # Always clear the alias so to_dict() / to_url() use 'name'
        object.__setattr__(self, "database", "")

    def to_url(self) -> str:
        auth = ""
        if self.user:
            auth = quote_plus(self.user)
            if self.password:
                auth += f":{quote_plus(self.password)}"
            auth += "@"
        port_part = f":{self.port}" if self.port != 5432 else ":5432"
        return f"postgresql://{auth}{self.host}{port_part}/{self.name}"

    def get_engine_options(self) -> Dict[str, Any]:
        opts = super().get_engine_options()
        opts["pool_min_size"] = self.pool_min_size
        opts["pool_max_size"] = self.pool_max_size
        if self.sslmode and self.sslmode != "prefer":
            opts["ssl"] = self.sslmode
        return opts

    @classmethod
    def from_url(cls, url: str, **overrides) -> "PostgresConfig":
        """Parse a postgresql:// URL into a PostgresConfig."""
        parsed = urlparse(url)
        return cls(
            host=parsed.hostname or "localhost",
            port=parsed.port or 5432,
            name=(parsed.path or "/").lstrip("/") or "",
            user=parsed.username or "",
            password=parsed.password or "",
            **overrides,
        )

    def __repr__(self) -> str:
        return (
            f"PostgresConfig(host={self.host!r}, port={self.port}, "
            f"database={self.name!r}, user={self.user!r})"
        )


@dataclass
class MysqlConfig(DatabaseConfig):
    """
    MySQL / MariaDB database configuration.

    Args:
        host: Database server hostname
        port: Database server port (default 3306)
        name: Database name (or use ``database`` as an alias)
        database: Alias for ``name`` -- use whichever feels natural
        user: Database user
        password: Database password
        charset: Character set (default "utf8mb4")
        collation: Collation (default "utf8mb4_unicode_ci")

    Examples:
        # Simple:
        MysqlConfig(
            host="localhost",
            database="mydb",
            user="root",
            password="secret",
        )

        # Also works with 'name':
        MysqlConfig(
            host="localhost",
            name="mydb",
            user="root",
            password="secret",
        )

        # Production:
        MysqlConfig(
            host="mysql.example.com",
            port=3306,
            database="prod_db",
            user="app_user",
            password="strong_password",
            charset="utf8mb4",
            pool_size=15,
        )
    """

    engine: str = "mysql"
    host: str = "localhost"
    port: int = 3306
    name: str = ""
    database: str = ""  # Alias for 'name' -- use whichever feels natural
    user: str = ""
    password: str = ""
    charset: str = "utf8mb4"
    collation: str = "utf8mb4_unicode_ci"

    def __post_init__(self):
        if self.database and not self.name:
            self.name = self.database
        object.__setattr__(self, "database", "")

    def to_url(self) -> str:
        auth = ""
        if self.user:
            auth = quote_plus(self.user)
            if self.password:
                auth += f":{quote_plus(self.password)}"
            auth += "@"
        return f"mysql://{auth}{self.host}:{self.port}/{self.name}"

    def get_engine_options(self) -> Dict[str, Any]:
        opts = super().get_engine_options()
        opts["charset"] = self.charset
        return opts

    @classmethod
    def from_url(cls, url: str, **overrides) -> "MysqlConfig":
        """Parse a mysql:// URL into a MysqlConfig."""
        parsed = urlparse(url)
        return cls(
            host=parsed.hostname or "localhost",
            port=parsed.port or 3306,
            name=(parsed.path or "/").lstrip("/") or "",
            user=parsed.username or "",
            password=parsed.password or "",
            **overrides,
        )

    def __repr__(self) -> str:
        return (
            f"MysqlConfig(host={self.host!r}, port={self.port}, "
            f"database={self.name!r}, user={self.user!r})"
        )


@dataclass
class OracleConfig(DatabaseConfig):
    """
    Oracle database configuration.

    Uses python-oracledb (thin mode by default -- no Oracle Client required).

    Args:
        host: Database server hostname
        port: Database server port (default 1521)
        service_name: Oracle service name
        database: Alias for ``service_name`` -- use whichever feels natural
        user: Database user
        password: Database password
        sid: Oracle SID (alternative to service_name)
        thick_mode: Use thick mode requiring Oracle Client (default False)
        encoding: NLS encoding (default "UTF-8")

    Examples:
        # Simple:
        OracleConfig(
            host="localhost",
            database="ORCL",
            user="scott",
            password="tiger",
        )

        # Also works with 'service_name':
        OracleConfig(
            host="localhost",
            service_name="ORCL",
            user="scott",
            password="tiger",
        )

        # Production with service name:
        OracleConfig(
            host="oracle.example.com",
            port=1521,
            database="PROD_SERVICE",
            user="app_user",
            password="strong_password",
            pool_size=20,
        )

        # Using SID:
        OracleConfig(
            host="oracle.example.com",
            sid="ORCL",
            user="scott",
            password="tiger",
        )
    """

    engine: str = "oracle"
    host: str = "localhost"
    port: int = 1521
    service_name: str = "ORCL"
    database: str = ""  # Alias for 'service_name' -- use whichever feels natural
    user: str = ""
    password: str = ""
    sid: str = ""
    thick_mode: bool = False
    encoding: str = "UTF-8"

    def __post_init__(self):
        if self.database and self.service_name == "ORCL":
            self.service_name = self.database
        object.__setattr__(self, "database", "")

    def to_url(self) -> str:
        auth = ""
        if self.user:
            auth = quote_plus(self.user)
            if self.password:
                auth += f":{quote_plus(self.password)}"
            auth += "@"
        db_name = self.service_name or self.sid or "ORCL"
        return f"oracle://{auth}{self.host}:{self.port}/{db_name}"

    def get_dsn(self) -> str:
        """Get Oracle DSN in Easy Connect format."""
        db_name = self.service_name or self.sid or "ORCL"
        return f"{self.host}:{self.port}/{db_name}"

    def get_engine_options(self) -> Dict[str, Any]:
        opts = super().get_engine_options()
        opts["pool_min_size"] = self.pool_min_size
        opts["pool_max_size"] = self.pool_max_size
        return opts

    @classmethod
    def from_url(cls, url: str, **overrides) -> "OracleConfig":
        """Parse an oracle:// URL into an OracleConfig."""
        parsed = urlparse(url)
        return cls(
            host=parsed.hostname or "localhost",
            port=parsed.port or 1521,
            service_name=(parsed.path or "/").lstrip("/") or "ORCL",
            user=parsed.username or "",
            password=parsed.password or "",
            **overrides,
        )

    def __repr__(self) -> str:
        return (
            f"OracleConfig(host={self.host!r}, port={self.port}, "
            f"database={self.service_name!r}, user={self.user!r})"
        )
