"""
Aquilia Database -- async-first database layer.

Provides:
- AquiliaDatabase: Connection manager with transaction support
- SQLite driver (default), Postgres/MySQL/Oracle adapters
- Pluggable backend adapters (DatabaseAdapter)
- Typed database config classes (SqliteConfig, PostgresConfig, etc.)
- Module-level accessors for DI integration
- Structured faults via AquilaFaults (DatabaseConnectionFault, QueryFault, SchemaFault)
"""

from .engine import (
    AquiliaDatabase,
    DatabaseError,
    get_database,
    configure_database,
    set_database,
)

# Backend adapters
from .backends import (
    DatabaseAdapter,
    AdapterCapabilities,
    SQLiteAdapter,
    PostgresAdapter,
    MySQLAdapter,
    OracleAdapter,
)

# Typed config classes
from .configs import (
    DatabaseConfig,
    SqliteConfig,
    PostgresConfig,
    MysqlConfig,
    OracleConfig,
)

# Re-export fault types for convenience
from ..faults.domains import (
    DatabaseConnectionFault,
    QueryFault,
    SchemaFault,
)

__all__ = [
    "AquiliaDatabase",
    "DatabaseError",
    "DatabaseConnectionFault",
    "QueryFault",
    "SchemaFault",
    "get_database",
    "configure_database",
    "set_database",
    # Backends
    "DatabaseAdapter",
    "AdapterCapabilities",
    "SQLiteAdapter",
    "PostgresAdapter",
    "MySQLAdapter",
    "OracleAdapter",
    # Config classes
    "DatabaseConfig",
    "SqliteConfig",
    "PostgresConfig",
    "MysqlConfig",
    "OracleConfig",
]
