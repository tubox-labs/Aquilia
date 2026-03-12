"""
Aquilia DB Backends Package -- pluggable database adapters.

Provides a common adapter interface and implementations for:
- SQLite (default, via native aquilia.sqlite)
- PostgreSQL (via asyncpg)
- MySQL / MariaDB (via aiomysql)
- Oracle (via python-oracledb)
"""

from .base import AdapterCapabilities, ColumnInfo, DatabaseAdapter, IntrospectionResult, TableInfo
from .mysql import MySQLAdapter
from .oracle import OracleAdapter
from .postgres import PostgresAdapter
from .sqlite import SQLiteAdapter

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
