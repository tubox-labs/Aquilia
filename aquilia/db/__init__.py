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

# Re-export fault types for convenience
# Backend adapters
from aquilia.db.backends import (
    AdapterCapabilities,
    DatabaseAdapter,
    MySQLAdapter,
    OracleAdapter,
    PostgresAdapter,
    SQLiteAdapter,
)

# Typed config classes
from aquilia.db.configs import DatabaseConfig, MysqlConfig, OracleConfig, PostgresConfig, SqliteConfig
from aquilia.db.engine import AquiliaDatabase, DatabaseError, configure_database, get_database, set_database
from aquilia.faults.domains import DatabaseConnectionFault, QueryFault, SchemaFault

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
