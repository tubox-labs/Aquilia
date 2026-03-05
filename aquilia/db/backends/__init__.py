"""
Aquilia DB Backends Package -- pluggable database adapters.

Provides a common adapter interface and implementations for:
- SQLite (default, via aiosqlite)
- PostgreSQL (via asyncpg)
- MySQL / MariaDB (via aiomysql)
- Oracle (via python-oracledb)
"""

from .base import DatabaseAdapter, AdapterCapabilities, ColumnInfo, TableInfo, IntrospectionResult
from .sqlite import SQLiteAdapter
from .postgres import PostgresAdapter
from .mysql import MySQLAdapter
from .oracle import OracleAdapter

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
