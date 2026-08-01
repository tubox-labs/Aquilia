"""
Aquilia DB Backends Package -- pluggable database adapters.

Provides a common adapter interface and implementations for:
- SQLite (default, via native aquilia.sqlite)
- PostgreSQL (via asyncpg)
- MySQL / MariaDB (via aiomysql)
- Oracle (via python-oracledb)
"""

from aquilia.db.backends.base import AdapterCapabilities, ColumnInfo, DatabaseAdapter, IntrospectionResult, TableInfo
from aquilia.db.backends.mysql import MySQLAdapter
from aquilia.db.backends.oracle import OracleAdapter
from aquilia.db.backends.postgres import PostgresAdapter
from aquilia.db.backends.sqlite import SQLiteAdapter

__all__ = [
    "DatabaseAdapter",
    "AdapterCapabilities",
    "ColumnInfo",
    "TableInfo",
    "IntrospectionResult",
    "SQLiteAdapter",
    "PostgresAdapter",
    "MySQLAdapter",
    "OracleAdapter",
]
