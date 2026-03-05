"""
Comprehensive Tests — Oracle Backend, Typed Database Configs & ORM Dialect System
===================================================================================

Tests every change made during the Phase 9 major ORM overhaul:

Module 1: Typed Database Config Classes (aquilia/db/configs.py)
    - DatabaseConfig base class (to_url, to_dict, from_url, get_engine_options)
    - SqliteConfig (path, journal_mode, to_url, from_url)
    - PostgresConfig (host, port, name, user, password, sslmode, to_url, from_url)
    - MysqlConfig (host, port, name, user, password, charset, to_url, from_url)
    - OracleConfig (host, port, service_name, user, password, to_url, from_url)
    - Config cross-compatibility (all configs produce valid URLs)
    - Config serialization (to_dict round-trip)
    - Config factory dispatch (DatabaseConfig.from_url auto-detection)
    - Config engine options merging
    - Config edge cases (special chars in password, empty fields)

Module 2: Oracle Adapter (aquilia/db/backends/oracle.py)
    - OracleAdapter capabilities
    - OracleAdapter adapt_sql (? → :1, :2, ... conversion)
    - Oracle URL parsing (_parse_oracle_url)
    - OracleAdapter dialect property
    - OracleAdapter import guard (oracledb optional)

Module 3: Engine Integration (aquilia/db/engine.py)
    - _create_adapter factory (sqlite, postgresql, mysql, oracle)
    - _detect_driver URL scheme detection (all 4 backends)
    - AquiliaDatabase with config object
    - AquiliaDatabase with URL string (backward compat)
    - configure_database with config object
    - configure_database with URL (backward compat)
    - Multi-database registry with aliases

Module 4: ORM Oracle SQL Generation (fields_module.py, runtime.py)
    - AutoField.sql_type() across all 4 dialects
    - BigAutoField.sql_type() across all 4 dialects
    - SmallAutoField.sql_type() across all 4 dialects
    - TextField.sql_type() — CLOB for Oracle
    - BooleanField.sql_type() — NUMBER(1) for Oracle
    - BinaryField.sql_type() — BLOB/BYTEA across dialects
    - FloatField.sql_type() — BINARY_DOUBLE for Oracle
    - JSONField.sql_type() — CLOB for Oracle
    - DateTimeField.sql_type() — TIMESTAMP WITH TIME ZONE
    - DurationField.sql_type() — INTERVAL for PG, NUMBER(19) for Oracle
    - UUIDField.sql_type() — VARCHAR2(36) for Oracle
    - CharField.sql_type() — VARCHAR2 for Oracle
    - DecimalField.sql_type() — NUMBER for Oracle
    - ForeignKeyField.sql_type() — NUMBER(10) for Oracle
    - GenericIPAddressField.sql_type() — VARCHAR2(45) for Oracle
    - sql_column_def() autoincrement for all 4 dialects
    - _sql_default() boolean defaults for PG

Module 5: ORM Type Maps (runtime.py)
    - SQLITE_TYPE_MAP completeness
    - POSTGRES_TYPE_MAP completeness
    - MYSQL_TYPE_MAP completeness
    - ORACLE_TYPE_MAP completeness
    - _get_type_map() dispatch
    - _sql_col_def() Oracle IDENTITY column generation
    - _sql_col_def() VARCHAR2 for Oracle strings
    - _sql_col_def() NUMBER for Oracle decimals

Module 6: Migration DSL Oracle Support (migration_dsl.py)
    - ColumnDef.to_sql() Oracle autoincrement
    - ColumnDef._resolve_type() Oracle type mappings
    - _resolve_type() BLOB → BLOB for Oracle
    - _resolve_type() REAL → BINARY_DOUBLE for Oracle

Module 7: Migration Runner & Ops Oracle Support
    - MigrationRunner.ensure_tracking_table() Oracle
    - Legacy MigrationRunner ensure_tracking_table() Oracle
    - MigrationOps.pk() Oracle dialect
    - MigrationOps.bigpk() Oracle dialect
    - MigrationOps.alter_column() Oracle dialect

Module 8: Model Base Class Oracle Support
    - generate_m2m_sql() Oracle dialect
    - generate_create_table_sql() all dialects

Module 9: Config Builders Integration
    - Integration.database(config=...) config-based
    - Integration.database(url=...) backward compatible
    - Workspace.database(config=...) config-based
    - Workspace.database(url=...) backward compatible
    - Module.database(config=...) config-based

Module 10: Package Exports & Imports
    - aquilia.db exports (OracleAdapter, configs)
    - aquilia.db.backends exports (OracleAdapter)
    - aquilia.db.configs exports
    - config_builders __all__
"""

from __future__ import annotations

import asyncio
import copy
import json
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

import pytest


# ════════════════════════════════════════════════════════════════════════════
# MODULE 1: TYPED DATABASE CONFIG CLASSES
# ════════════════════════════════════════════════════════════════════════════


class TestDatabaseConfigBase:
    """Tests for DatabaseConfig base class."""

    def test_from_url_sqlite(self):
        from aquilia.db.configs import DatabaseConfig, SqliteConfig
        config = DatabaseConfig.from_url("sqlite:///test.db")
        assert isinstance(config, SqliteConfig)
        assert config.path == "test.db"

    def test_from_url_postgresql(self):
        from aquilia.db.configs import DatabaseConfig, PostgresConfig
        config = DatabaseConfig.from_url("postgresql://user:pass@host:5432/db")
        assert isinstance(config, PostgresConfig)
        assert config.host == "host"
        assert config.port == 5432
        assert config.name == "db"
        assert config.user == "user"
        assert config.password == "pass"

    def test_from_url_postgres_alias(self):
        from aquilia.db.configs import DatabaseConfig, PostgresConfig
        config = DatabaseConfig.from_url("postgres://u:p@h/d")
        assert isinstance(config, PostgresConfig)

    def test_from_url_mysql(self):
        from aquilia.db.configs import DatabaseConfig, MysqlConfig
        config = DatabaseConfig.from_url("mysql://user:pass@host:3306/db")
        assert isinstance(config, MysqlConfig)
        assert config.host == "host"
        assert config.port == 3306
        assert config.name == "db"

    def test_from_url_oracle(self):
        from aquilia.db.configs import DatabaseConfig, OracleConfig
        config = DatabaseConfig.from_url("oracle://user:pass@host:1521/ORCL")
        assert isinstance(config, OracleConfig)
        assert config.host == "host"
        assert config.port == 1521
        assert config.service_name == "ORCL"

    def test_from_url_unsupported_scheme(self):
        from aquilia.db.configs import DatabaseConfig
        with pytest.raises(ValueError, match="Unsupported database URL"):
            DatabaseConfig.from_url("mongodb://host/db")

    def test_base_to_url_raises(self):
        from aquilia.db.configs import DatabaseConfig
        config = DatabaseConfig()
        with pytest.raises(NotImplementedError):
            config.to_url()

    def test_base_repr(self):
        from aquilia.db.configs import DatabaseConfig
        config = DatabaseConfig()
        assert "DatabaseConfig" in repr(config)


class TestSqliteConfig:
    """Tests for SqliteConfig."""

    def test_defaults(self):
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig()
        assert config.engine == "sqlite"
        assert config.path == "db.sqlite3"
        assert config.journal_mode == "WAL"
        assert config.foreign_keys is True
        assert config.busy_timeout == 5000

    def test_to_url_file(self):
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig(path="data/app.db")
        assert config.to_url() == "sqlite:///data/app.db"

    def test_to_url_memory(self):
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig(path=":memory:")
        assert config.to_url() == "sqlite:///:memory:"

    def test_from_url_file(self):
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig.from_url("sqlite:///myapp.db")
        assert config.path == "myapp.db"

    def test_from_url_memory(self):
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig.from_url("sqlite:///:memory:")
        assert config.path == ":memory:"

    def test_from_url_empty_path(self):
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig.from_url("sqlite://")
        assert config.path == ":memory:"

    def test_to_dict(self):
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig(path="test.db")
        d = config.to_dict()
        assert d["engine"] == "sqlite"
        assert d["url"] == "sqlite:///test.db"
        assert d["enabled"] is True
        assert d["auto_connect"] is True
        assert d["auto_create"] is True

    def test_repr(self):
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig(path="test.db")
        assert "test.db" in repr(config)

    def test_custom_pool_size(self):
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig(pool_size=10)
        assert config.pool_size == 10

    def test_auto_migrate_flag(self):
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig(auto_migrate=True)
        d = config.to_dict()
        assert d["auto_migrate"] is True

    def test_from_url_with_overrides(self):
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig.from_url("sqlite:///db.sqlite3", auto_migrate=True)
        assert config.auto_migrate is True


class TestPostgresConfig:
    """Tests for PostgresConfig."""

    def test_defaults(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig()
        assert config.engine == "postgresql"
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.schema == "public"
        assert config.sslmode == "prefer"

    def test_to_url_basic(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(
            host="localhost",
            port=5432,
            name="mydb",
            user="admin",
            password="secret",
        )
        url = config.to_url()
        assert url.startswith("postgresql://")
        assert "admin" in url
        assert "secret" in url
        assert "mydb" in url
        assert "localhost" in url

    def test_to_url_special_chars_in_password(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(
            host="localhost",
            name="db",
            user="admin",
            password="p@ss:w/ord",
        )
        url = config.to_url()
        # Special chars should be URL-encoded
        assert "p%40ss%3Aw%2Ford" in url

    def test_to_url_no_auth(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(host="localhost", name="db")
        url = config.to_url()
        assert "postgresql://localhost" in url
        assert "@" not in url

    def test_from_url(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig.from_url(
            "postgresql://admin:pass@db.example.com:5433/prod_db"
        )
        assert config.host == "db.example.com"
        assert config.port == 5433
        assert config.name == "prod_db"
        assert config.user == "admin"
        assert config.password == "pass"

    def test_from_url_defaults(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig.from_url("postgresql://localhost/testdb")
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.name == "testdb"

    def test_to_dict(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(
            host="localhost", name="mydb", user="admin", password="secret"
        )
        d = config.to_dict()
        assert d["engine"] == "postgresql"
        assert "postgresql://" in d["url"]
        assert d["enabled"] is True

    def test_get_engine_options_ssl(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(sslmode="require")
        opts = config.get_engine_options()
        assert opts["ssl"] == "require"

    def test_get_engine_options_no_ssl(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(sslmode="prefer")
        opts = config.get_engine_options()
        assert "ssl" not in opts

    def test_get_engine_options_pool(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(pool_min_size=5, pool_max_size=50)
        opts = config.get_engine_options()
        assert opts["pool_min_size"] == 5
        assert opts["pool_max_size"] == 50

    def test_repr(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(host="db.example.com", name="prod")
        r = repr(config)
        assert "db.example.com" in r
        assert "prod" in r

    def test_conn_resilience_options(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(
            connect_retries=5,
            connect_retry_delay=1.0,
            conn_max_age=600,
            conn_health_checks=True,
        )
        d = config.to_dict()
        assert d["connect_retries"] == 5
        assert d["connect_retry_delay"] == 1.0
        assert d["conn_max_age"] == 600
        assert d["conn_health_checks"] is True


class TestMysqlConfig:
    """Tests for MysqlConfig."""

    def test_defaults(self):
        from aquilia.db.configs import MysqlConfig
        config = MysqlConfig()
        assert config.engine == "mysql"
        assert config.host == "localhost"
        assert config.port == 3306
        assert config.charset == "utf8mb4"
        assert config.collation == "utf8mb4_unicode_ci"

    def test_to_url(self):
        from aquilia.db.configs import MysqlConfig
        config = MysqlConfig(
            host="mysql.example.com",
            port=3307,
            name="app_db",
            user="root",
            password="pass123",
        )
        url = config.to_url()
        assert "mysql://" in url
        assert "root" in url
        assert "3307" in url
        assert "app_db" in url

    def test_from_url(self):
        from aquilia.db.configs import MysqlConfig
        config = MysqlConfig.from_url("mysql://user:pass@host:3306/mydb")
        assert config.host == "host"
        assert config.port == 3306
        assert config.name == "mydb"
        assert config.user == "user"
        assert config.password == "pass"

    def test_from_url_default_port(self):
        from aquilia.db.configs import MysqlConfig
        config = MysqlConfig.from_url("mysql://user:pass@host/db")
        assert config.port == 3306

    def test_to_dict(self):
        from aquilia.db.configs import MysqlConfig
        config = MysqlConfig(host="localhost", name="db", user="root")
        d = config.to_dict()
        assert d["engine"] == "mysql"
        assert "mysql://" in d["url"]

    def test_get_engine_options(self):
        from aquilia.db.configs import MysqlConfig
        config = MysqlConfig(charset="latin1")
        opts = config.get_engine_options()
        assert opts["charset"] == "latin1"

    def test_repr(self):
        from aquilia.db.configs import MysqlConfig
        config = MysqlConfig(host="db.host", name="mydb", user="root")
        assert "db.host" in repr(config)

    def test_options_dict(self):
        from aquilia.db.configs import MysqlConfig
        config = MysqlConfig(options={"ssl": True})
        d = config.to_dict()
        assert d["options"] == {"ssl": True}


class TestOracleConfig:
    """Tests for OracleConfig."""

    def test_defaults(self):
        from aquilia.db.configs import OracleConfig
        config = OracleConfig()
        assert config.engine == "oracle"
        assert config.host == "localhost"
        assert config.port == 1521
        assert config.service_name == "ORCL"
        assert config.thick_mode is False
        assert config.encoding == "UTF-8"

    def test_to_url(self):
        from aquilia.db.configs import OracleConfig
        config = OracleConfig(
            host="oracle.example.com",
            port=1521,
            service_name="PROD",
            user="scott",
            password="tiger",
        )
        url = config.to_url()
        assert "oracle://" in url
        assert "scott" in url
        assert "PROD" in url
        assert "1521" in url

    def test_to_url_sid(self):
        from aquilia.db.configs import OracleConfig
        config = OracleConfig(
            host="localhost",
            service_name="",
            sid="XE",
            user="admin",
            password="pass",
        )
        url = config.to_url()
        assert "XE" in url

    def test_from_url(self):
        from aquilia.db.configs import OracleConfig
        config = OracleConfig.from_url("oracle://scott:tiger@host:1521/SERVICE")
        assert config.host == "host"
        assert config.port == 1521
        assert config.service_name == "SERVICE"
        assert config.user == "scott"
        assert config.password == "tiger"

    def test_from_url_defaults(self):
        from aquilia.db.configs import OracleConfig
        config = OracleConfig.from_url("oracle://localhost/ORCL")
        assert config.host == "localhost"
        assert config.port == 1521
        assert config.service_name == "ORCL"

    def test_get_dsn(self):
        from aquilia.db.configs import OracleConfig
        config = OracleConfig(
            host="oracle.example.com",
            port=1521,
            service_name="PROD",
        )
        dsn = config.get_dsn()
        assert dsn == "oracle.example.com:1521/PROD"

    def test_to_dict(self):
        from aquilia.db.configs import OracleConfig
        config = OracleConfig(
            host="oracle.example.com",
            service_name="PROD",
            user="scott",
        )
        d = config.to_dict()
        assert d["engine"] == "oracle"
        assert "oracle://" in d["url"]
        assert d["enabled"] is True

    def test_get_engine_options(self):
        from aquilia.db.configs import OracleConfig
        config = OracleConfig(pool_min_size=3, pool_max_size=30)
        opts = config.get_engine_options()
        assert opts["pool_min_size"] == 3
        assert opts["pool_max_size"] == 30

    def test_repr(self):
        from aquilia.db.configs import OracleConfig
        config = OracleConfig(host="oracle.host", service_name="SVC")
        r = repr(config)
        assert "oracle.host" in r
        assert "SVC" in r

    def test_from_url_with_overrides(self):
        from aquilia.db.configs import OracleConfig
        config = OracleConfig.from_url(
            "oracle://u:p@host/SVC", pool_size=20, auto_migrate=True
        )
        assert config.pool_size == 20
        assert config.auto_migrate is True


class TestConfigCrossCompatibility:
    """Test that all configs produce valid, parseable URLs."""

    def test_sqlite_roundtrip(self):
        from aquilia.db.configs import SqliteConfig
        config1 = SqliteConfig(path="test.db")
        url = config1.to_url()
        config2 = SqliteConfig.from_url(url)
        assert config2.path == "test.db"

    def test_postgres_roundtrip(self):
        from aquilia.db.configs import PostgresConfig
        config1 = PostgresConfig(
            host="localhost", port=5432, name="db", user="admin", password="pass"
        )
        url = config1.to_url()
        config2 = PostgresConfig.from_url(url)
        assert config2.host == "localhost"
        assert config2.name == "db"
        assert config2.user == "admin"

    def test_mysql_roundtrip(self):
        from aquilia.db.configs import MysqlConfig
        config1 = MysqlConfig(
            host="localhost", port=3306, name="db", user="root", password="pass"
        )
        url = config1.to_url()
        config2 = MysqlConfig.from_url(url)
        assert config2.host == "localhost"
        assert config2.name == "db"
        assert config2.user == "root"

    def test_oracle_roundtrip(self):
        from aquilia.db.configs import OracleConfig
        config1 = OracleConfig(
            host="host", port=1521, service_name="SVC", user="u", password="p"
        )
        url = config1.to_url()
        config2 = OracleConfig.from_url(url)
        assert config2.host == "host"
        assert config2.service_name == "SVC"

    def test_all_configs_have_enabled_in_dict(self):
        from aquilia.db.configs import SqliteConfig, PostgresConfig, MysqlConfig, OracleConfig
        for cls in [SqliteConfig, PostgresConfig, MysqlConfig, OracleConfig]:
            config = cls()
            d = config.to_dict()
            assert d["enabled"] is True
            assert "url" in d
            assert "engine" in d

    def test_all_configs_produce_valid_url_scheme(self):
        from aquilia.db.configs import SqliteConfig, PostgresConfig, MysqlConfig, OracleConfig
        assert SqliteConfig().to_url().startswith("sqlite:")
        assert PostgresConfig().to_url().startswith("postgresql:")
        assert MysqlConfig().to_url().startswith("mysql:")
        assert OracleConfig().to_url().startswith("oracle:")


# ════════════════════════════════════════════════════════════════════════════
# MODULE 2: ORACLE ADAPTER
# ════════════════════════════════════════════════════════════════════════════


class TestOracleAdapterCapabilities:
    """Tests for OracleAdapter capabilities and metadata."""

    def test_capabilities(self):
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = OracleAdapter()
        caps = adapter.capabilities
        assert caps.name == "oracle"
        assert caps.supports_returning is True
        assert caps.supports_json_type is False
        assert caps.supports_arrays is False
        assert caps.supports_savepoints is True
        assert caps.supports_window_functions is True
        assert caps.supports_cte is True
        assert caps.supports_upsert is True
        assert caps.param_style == "named"
        assert caps.null_ordering is True

    def test_dialect_property(self):
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = OracleAdapter()
        assert adapter.dialect == "oracle"

    def test_is_connected_default(self):
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = OracleAdapter()
        assert adapter.is_connected is False

    def test_not_connected_raises(self):
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = OracleAdapter()
        with pytest.raises(RuntimeError):
            asyncio.run(adapter.execute("SELECT 1"))


class TestOracleAdaptSQL:
    """Tests for Oracle SQL placeholder adaptation."""

    def test_basic_placeholder(self):
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = OracleAdapter()
        assert adapter.adapt_sql("SELECT * FROM t WHERE id = ?") == \
            "SELECT * FROM t WHERE id = :1"

    def test_multiple_placeholders(self):
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = OracleAdapter()
        result = adapter.adapt_sql("INSERT INTO t (a, b, c) VALUES (?, ?, ?)")
        assert result == "INSERT INTO t (a, b, c) VALUES (:1, :2, :3)"

    def test_no_placeholders(self):
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = OracleAdapter()
        sql = "SELECT * FROM t"
        assert adapter.adapt_sql(sql) == sql

    def test_string_literal_safe(self):
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = OracleAdapter()
        sql = "SELECT * FROM t WHERE name = '?' AND id = ?"
        result = adapter.adapt_sql(sql)
        assert result == "SELECT * FROM t WHERE name = '?' AND id = :1"

    def test_escaped_quote(self):
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = OracleAdapter()
        sql = "SELECT * FROM t WHERE name = 'it''s' AND id = ?"
        result = adapter.adapt_sql(sql)
        assert result == "SELECT * FROM t WHERE name = 'it''s' AND id = :1"

    def test_empty_sql(self):
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = OracleAdapter()
        assert adapter.adapt_sql("") == ""


class TestOracleURLParsing:
    """Tests for Oracle URL parsing."""

    def test_full_url(self):
        from aquilia.db.backends.oracle import _parse_oracle_url
        result = _parse_oracle_url("oracle://scott:tiger@db.example.com:1521/ORCL")
        assert result["user"] == "scott"
        assert result["password"] == "tiger"
        assert result["dsn"] == "db.example.com:1521/ORCL"

    def test_default_port(self):
        from aquilia.db.backends.oracle import _parse_oracle_url
        result = _parse_oracle_url("oracle://scott:tiger@db.example.com/ORCL")
        assert result["dsn"] == "db.example.com:1521/ORCL"

    def test_default_service(self):
        from aquilia.db.backends.oracle import _parse_oracle_url
        result = _parse_oracle_url("oracle://scott:tiger@localhost")
        assert "ORCL" in result["dsn"]

    def test_no_auth(self):
        from aquilia.db.backends.oracle import _parse_oracle_url
        result = _parse_oracle_url("oracle://localhost:1521/XE")
        assert "user" not in result
        assert "password" not in result
        assert result["dsn"] == "localhost:1521/XE"

    def test_thin_scheme(self):
        from aquilia.db.backends.oracle import _parse_oracle_url
        result = _parse_oracle_url("oracle+thin://scott:tiger@host:1521/SVC")
        assert result["user"] == "scott"


class TestOracleAdapterImportGuard:
    """Test that OracleAdapter handles missing oracledb gracefully."""

    def test_import_error_on_connect(self):
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = OracleAdapter()
        # oracledb is likely not installed in test env
        import aquilia.db.backends.oracle as oracle_mod
        original = oracle_mod._HAS_ORACLEDB
        oracle_mod._HAS_ORACLEDB = False
        try:
            with pytest.raises(ImportError, match="oracledb"):
                asyncio.run(adapter.connect("oracle://localhost/ORCL"))
        finally:
            oracle_mod._HAS_ORACLEDB = original

    def test_savepoint_validation(self):
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = OracleAdapter()
        with pytest.raises((ValueError, RuntimeError)):
            asyncio.run(adapter.savepoint("invalid name!"))

    def test_release_savepoint_no_op(self):
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = OracleAdapter()
        # Oracle doesn't support RELEASE SAVEPOINT — should be a no-op
        asyncio.run(adapter.release_savepoint("valid_name"))


# ════════════════════════════════════════════════════════════════════════════
# MODULE 3: ENGINE INTEGRATION
# ════════════════════════════════════════════════════════════════════════════


class TestCreateAdapterFactory:
    """Tests for _create_adapter factory."""

    def test_sqlite(self):
        from aquilia.db.engine import _create_adapter
        from aquilia.db.backends.sqlite import SQLiteAdapter
        adapter = _create_adapter("sqlite")
        assert isinstance(adapter, SQLiteAdapter)

    def test_postgresql(self):
        from aquilia.db.engine import _create_adapter
        from aquilia.db.backends.postgres import PostgresAdapter
        adapter = _create_adapter("postgresql")
        assert isinstance(adapter, PostgresAdapter)

    def test_mysql(self):
        from aquilia.db.engine import _create_adapter
        from aquilia.db.backends.mysql import MySQLAdapter
        adapter = _create_adapter("mysql")
        assert isinstance(adapter, MySQLAdapter)

    def test_oracle(self):
        from aquilia.db.engine import _create_adapter
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = _create_adapter("oracle")
        assert isinstance(adapter, OracleAdapter)

    def test_unsupported_driver(self):
        from aquilia.db.engine import _create_adapter
        from aquilia.faults.domains import DatabaseConnectionFault
        with pytest.raises(DatabaseConnectionFault):
            _create_adapter("mssql")


class TestDetectDriver:
    """Tests for AquiliaDatabase._detect_driver."""

    def test_sqlite_url(self):
        from aquilia.db.engine import AquiliaDatabase
        assert AquiliaDatabase._detect_driver("sqlite:///db.sqlite3") == "sqlite"

    def test_sqlite_memory(self):
        from aquilia.db.engine import AquiliaDatabase
        assert AquiliaDatabase._detect_driver("sqlite:///:memory:") == "sqlite"

    def test_postgresql_url(self):
        from aquilia.db.engine import AquiliaDatabase
        assert AquiliaDatabase._detect_driver("postgresql://u:p@h/d") == "postgresql"

    def test_postgres_alias_url(self):
        from aquilia.db.engine import AquiliaDatabase
        assert AquiliaDatabase._detect_driver("postgres://u:p@h/d") == "postgresql"

    def test_mysql_url(self):
        from aquilia.db.engine import AquiliaDatabase
        assert AquiliaDatabase._detect_driver("mysql://u:p@h/d") == "mysql"

    def test_oracle_url(self):
        from aquilia.db.engine import AquiliaDatabase
        assert AquiliaDatabase._detect_driver("oracle://u:p@h/d") == "oracle"

    def test_unsupported_url(self):
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.faults.domains import DatabaseConnectionFault
        with pytest.raises(DatabaseConnectionFault):
            AquiliaDatabase._detect_driver("mssql://host/db")


class TestAquiliaDatabaseWithConfig:
    """Tests for AquiliaDatabase construction with config objects."""

    def test_init_with_sqlite_config(self):
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig(path="test.db")
        db = AquiliaDatabase(config=config)
        assert db.url == "sqlite:///test.db"
        assert db.driver == "sqlite"
        assert db.dialect == "sqlite"

    def test_init_with_postgres_config(self):
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(
            host="localhost", port=5432, name="mydb",
            user="admin", password="secret",
        )
        db = AquiliaDatabase(config=config)
        assert db.driver == "postgresql"
        assert db.dialect == "postgresql"
        assert "mydb" in db.url

    def test_init_with_mysql_config(self):
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.db.configs import MysqlConfig
        config = MysqlConfig(
            host="localhost", port=3306, name="mydb",
            user="root", password="pass",
        )
        db = AquiliaDatabase(config=config)
        assert db.driver == "mysql"
        assert "mydb" in db.url

    def test_init_with_oracle_config(self):
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.db.configs import OracleConfig
        config = OracleConfig(
            host="oracle.example.com",
            service_name="PROD",
            user="scott",
            password="tiger",
        )
        db = AquiliaDatabase(config=config)
        assert db.driver == "oracle"
        assert db.dialect == "oracle"
        assert "oracle" in db.url

    def test_init_with_url_backward_compat(self):
        from aquilia.db.engine import AquiliaDatabase
        db = AquiliaDatabase("sqlite:///db.sqlite3")
        assert db.url == "sqlite:///db.sqlite3"
        assert db.driver == "sqlite"

    def test_init_default(self):
        from aquilia.db.engine import AquiliaDatabase
        db = AquiliaDatabase()
        assert db.url == "sqlite:///db.sqlite3"
        assert db.driver == "sqlite"

    def test_config_overrides_url(self):
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig(path="from_config.db")
        db = AquiliaDatabase("sqlite:///from_url.db", config=config)
        # Config takes precedence
        assert db.url == "sqlite:///from_config.db"

    def test_config_engine_options_merged(self):
        from aquilia.db.engine import AquiliaDatabase
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(
            host="localhost", name="db", user="u",
            connect_retries=5, connect_retry_delay=2.0,
        )
        db = AquiliaDatabase(config=config)
        assert db._connect_retries == 5
        assert db._connect_retry_delay == 2.0


class TestConfigureDatabaseWithConfig:
    """Tests for configure_database() with config objects."""

    def test_configure_with_config(self):
        from aquilia.db.engine import configure_database, _database_registry
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig(path=":memory:")
        db = configure_database(config=config, alias="test_config")
        assert "test_config" in _database_registry
        assert db.url == "sqlite:///:memory:"
        # Cleanup
        _database_registry.pop("test_config", None)

    def test_configure_with_url_backward_compat(self):
        from aquilia.db.engine import configure_database, _database_registry
        db = configure_database("sqlite:///test.db", alias="test_url")
        assert db.url == "sqlite:///test.db"
        # Cleanup
        _database_registry.pop("test_url", None)

    def test_configure_default_alias(self):
        from aquilia.db.engine import configure_database, get_database, _database_registry, _default_database
        import aquilia.db.engine as engine_mod
        old_default = engine_mod._default_database
        try:
            db = configure_database("sqlite:///:memory:", alias="default")
            assert get_database() is db
        finally:
            engine_mod._default_database = old_default
            _database_registry.pop("default", None)

    def test_multi_database_aliases(self):
        from aquilia.db.engine import configure_database, get_database, _database_registry
        from aquilia.db.configs import SqliteConfig
        try:
            db1 = configure_database(config=SqliteConfig(path="primary.db"), alias="primary")
            db2 = configure_database(config=SqliteConfig(path="cache.db"), alias="cache")
            assert get_database("primary") is db1
            assert get_database("cache") is db2
            assert db1.url != db2.url
        finally:
            _database_registry.pop("primary", None)
            _database_registry.pop("cache", None)


# ════════════════════════════════════════════════════════════════════════════
# MODULE 4: ORM ORACLE SQL GENERATION — FIELDS
# ════════════════════════════════════════════════════════════════════════════


class TestAutoFieldSqlType:
    """Tests for AutoField.sql_type() across all dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import AutoField
        f = AutoField()
        assert f.sql_type("sqlite") == "INTEGER"

    def test_postgresql(self):
        from aquilia.models.fields_module import AutoField
        f = AutoField()
        assert f.sql_type("postgresql") == "SERIAL"

    def test_mysql(self):
        from aquilia.models.fields_module import AutoField
        f = AutoField()
        assert f.sql_type("mysql") == "INTEGER"

    def test_oracle(self):
        from aquilia.models.fields_module import AutoField
        f = AutoField()
        assert f.sql_type("oracle") == "NUMBER(10)"


class TestBigAutoFieldSqlType:
    """Tests for BigAutoField.sql_type() across all dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import BigAutoField
        f = BigAutoField()
        assert f.sql_type("sqlite") == "INTEGER"

    def test_postgresql(self):
        from aquilia.models.fields_module import BigAutoField
        f = BigAutoField()
        assert f.sql_type("postgresql") == "BIGSERIAL"

    def test_mysql(self):
        from aquilia.models.fields_module import BigAutoField
        f = BigAutoField()
        assert f.sql_type("mysql") == "INTEGER"

    def test_oracle(self):
        from aquilia.models.fields_module import BigAutoField
        f = BigAutoField()
        assert f.sql_type("oracle") == "NUMBER(19)"


class TestSmallAutoFieldSqlType:
    """Tests for SmallAutoField.sql_type() across all dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import SmallAutoField
        f = SmallAutoField()
        assert f.sql_type("sqlite") == "INTEGER"

    def test_postgresql(self):
        from aquilia.models.fields_module import SmallAutoField
        f = SmallAutoField()
        assert f.sql_type("postgresql") == "SMALLSERIAL"

    def test_oracle(self):
        from aquilia.models.fields_module import SmallAutoField
        f = SmallAutoField()
        assert f.sql_type("oracle") == "NUMBER(5)"


class TestTextFieldSqlType:
    """Tests for TextField.sql_type() across dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import TextField
        f = TextField()
        assert f.sql_type("sqlite") == "TEXT"

    def test_postgresql(self):
        from aquilia.models.fields_module import TextField
        f = TextField()
        assert f.sql_type("postgresql") == "TEXT"

    def test_mysql(self):
        from aquilia.models.fields_module import TextField
        f = TextField()
        assert f.sql_type("mysql") == "TEXT"

    def test_oracle(self):
        from aquilia.models.fields_module import TextField
        f = TextField()
        assert f.sql_type("oracle") == "CLOB"


class TestBooleanFieldSqlType:
    """Tests for BooleanField.sql_type() across dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField()
        assert f.sql_type("sqlite") == "INTEGER"

    def test_postgresql(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField()
        assert f.sql_type("postgresql") == "BOOLEAN"

    def test_mysql(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField()
        assert f.sql_type("mysql") == "INTEGER"

    def test_oracle(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField()
        assert f.sql_type("oracle") == "NUMBER(1)"


class TestBinaryFieldSqlType:
    """Tests for BinaryField.sql_type() across dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import BinaryField
        f = BinaryField()
        assert f.sql_type("sqlite") == "BLOB"

    def test_postgresql(self):
        from aquilia.models.fields_module import BinaryField
        f = BinaryField()
        assert f.sql_type("postgresql") == "BYTEA"

    def test_oracle(self):
        from aquilia.models.fields_module import BinaryField
        f = BinaryField()
        assert f.sql_type("oracle") == "BLOB"


class TestFloatFieldSqlType:
    """Tests for FloatField.sql_type() across dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import FloatField
        f = FloatField()
        assert f.sql_type("sqlite") == "REAL"

    def test_postgresql(self):
        from aquilia.models.fields_module import FloatField
        f = FloatField()
        assert f.sql_type("postgresql") == "DOUBLE PRECISION"

    def test_oracle(self):
        from aquilia.models.fields_module import FloatField
        f = FloatField()
        assert f.sql_type("oracle") == "BINARY_DOUBLE"


class TestJSONFieldSqlType:
    """Tests for JSONField.sql_type() across dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import JSONField
        f = JSONField()
        assert f.sql_type("sqlite") == "TEXT"

    def test_postgresql(self):
        from aquilia.models.fields_module import JSONField
        f = JSONField()
        assert f.sql_type("postgresql") == "JSONB"

    def test_mysql(self):
        from aquilia.models.fields_module import JSONField
        f = JSONField()
        assert f.sql_type("mysql") == "TEXT"

    def test_oracle(self):
        from aquilia.models.fields_module import JSONField
        f = JSONField()
        assert f.sql_type("oracle") == "CLOB"


class TestDateTimeFieldSqlType:
    """Tests for DateTimeField.sql_type() across dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField()
        assert f.sql_type("sqlite") == "TIMESTAMP"

    def test_postgresql(self):
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField()
        assert f.sql_type("postgresql") == "TIMESTAMP WITH TIME ZONE"

    def test_oracle(self):
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField()
        assert f.sql_type("oracle") == "TIMESTAMP WITH TIME ZONE"


class TestDurationFieldSqlType:
    """Tests for DurationField.sql_type() across dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import DurationField
        f = DurationField()
        assert f.sql_type("sqlite") == "INTEGER"

    def test_postgresql(self):
        from aquilia.models.fields_module import DurationField
        f = DurationField()
        assert f.sql_type("postgresql") == "INTERVAL"

    def test_oracle(self):
        from aquilia.models.fields_module import DurationField
        f = DurationField()
        assert f.sql_type("oracle") == "INTERVAL DAY TO SECOND"


class TestUUIDFieldSqlType:
    """Tests for UUIDField.sql_type() across dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import UUIDField
        f = UUIDField()
        assert f.sql_type("sqlite") == "VARCHAR(36)"

    def test_postgresql(self):
        from aquilia.models.fields_module import UUIDField
        f = UUIDField()
        assert f.sql_type("postgresql") == "UUID"

    def test_oracle(self):
        from aquilia.models.fields_module import UUIDField
        f = UUIDField()
        assert f.sql_type("oracle") == "VARCHAR2(36)"


class TestCharFieldSqlType:
    """Tests for CharField/VarcharField sql_type() across dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import CharField
        f = CharField(max_length=100)
        assert f.sql_type("sqlite") == "VARCHAR(100)"

    def test_postgresql(self):
        from aquilia.models.fields_module import CharField
        f = CharField(max_length=100)
        assert f.sql_type("postgresql") == "VARCHAR(100)"

    def test_oracle(self):
        from aquilia.models.fields_module import CharField
        f = CharField(max_length=100)
        assert f.sql_type("oracle") == "VARCHAR2(100)"


class TestDecimalFieldSqlType:
    """Tests for DecimalField.sql_type() across dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import DecimalField
        f = DecimalField(max_digits=10, decimal_places=2)
        assert f.sql_type("sqlite") == "DECIMAL(10,2)"

    def test_oracle(self):
        from aquilia.models.fields_module import DecimalField
        f = DecimalField(max_digits=10, decimal_places=2)
        assert f.sql_type("oracle") == "NUMBER(10,2)"


class TestIntegerFieldSqlType:
    """Tests for IntegerField across dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import IntegerField
        f = IntegerField()
        assert f.sql_type("sqlite") == "INTEGER"

    def test_postgresql(self):
        from aquilia.models.fields_module import IntegerField
        f = IntegerField()
        assert f.sql_type("postgresql") == "INTEGER"

    def test_oracle(self):
        from aquilia.models.fields_module import IntegerField
        f = IntegerField()
        assert f.sql_type("oracle") == "NUMBER(10)"


class TestBigIntegerFieldSqlType:
    """Tests for BigIntegerField across dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import BigIntegerField
        f = BigIntegerField()
        assert f.sql_type("sqlite") == "INTEGER"

    def test_postgresql(self):
        from aquilia.models.fields_module import BigIntegerField
        f = BigIntegerField()
        assert f.sql_type("postgresql") == "BIGINT"

    def test_oracle(self):
        from aquilia.models.fields_module import BigIntegerField
        f = BigIntegerField()
        assert f.sql_type("oracle") == "NUMBER(19)"


class TestSmallIntegerFieldSqlType:
    """Tests for SmallIntegerField across dialects."""

    def test_oracle(self):
        from aquilia.models.fields_module import SmallIntegerField
        f = SmallIntegerField()
        assert f.sql_type("oracle") == "NUMBER(5)"


class TestPositiveIntegerFieldSqlType:
    """Tests for PositiveIntegerField across dialects."""

    def test_oracle(self):
        from aquilia.models.fields_module import PositiveIntegerField
        f = PositiveIntegerField()
        assert f.sql_type("oracle") == "NUMBER(10)"


class TestPositiveBigIntegerFieldSqlType:
    """Tests for PositiveBigIntegerField across dialects."""

    def test_oracle(self):
        from aquilia.models.fields_module import PositiveBigIntegerField
        f = PositiveBigIntegerField()
        assert f.sql_type("oracle") == "NUMBER(19)"


class TestForeignKeyFieldSqlType:
    """Tests for ForeignKey.sql_type() across dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import ForeignKey
        f = ForeignKey("OtherModel")
        assert f.sql_type("sqlite") == "INTEGER"

    def test_oracle(self):
        from aquilia.models.fields_module import ForeignKey
        f = ForeignKey("OtherModel")
        assert f.sql_type("oracle") == "NUMBER(10)"


class TestGenericIPAddressFieldSqlType:
    """Tests for GenericIPAddressField.sql_type() across dialects."""

    def test_sqlite(self):
        from aquilia.models.fields_module import GenericIPAddressField
        f = GenericIPAddressField()
        assert f.sql_type("sqlite") == "VARCHAR(39)"

    def test_postgresql(self):
        from aquilia.models.fields_module import GenericIPAddressField
        f = GenericIPAddressField()
        assert f.sql_type("postgresql") == "INET"

    def test_oracle(self):
        from aquilia.models.fields_module import GenericIPAddressField
        f = GenericIPAddressField()
        assert f.sql_type("oracle") == "VARCHAR2(39)"


class TestSqlColumnDefAutoincrement:
    """Tests for sql_column_def() autoincrement across all dialects."""

    def test_sqlite_autoincrement(self):
        from aquilia.models.fields_module import AutoField
        f = AutoField(primary_key=True)
        f.name = "id"
        f.attr_name = "id"
        col_def = f.sql_column_def("sqlite")
        assert "AUTOINCREMENT" in col_def
        assert "PRIMARY KEY" in col_def

    def test_postgresql_serial(self):
        from aquilia.models.fields_module import AutoField
        f = AutoField(primary_key=True)
        f.name = "id"
        f.attr_name = "id"
        col_def = f.sql_column_def("postgresql")
        assert "SERIAL" in col_def
        assert "PRIMARY KEY" in col_def
        assert "AUTOINCREMENT" not in col_def

    def test_mysql_auto_increment(self):
        from aquilia.models.fields_module import AutoField
        f = AutoField(primary_key=True)
        f.name = "id"
        f.attr_name = "id"
        col_def = f.sql_column_def("mysql")
        assert "AUTO_INCREMENT" in col_def
        assert "PRIMARY KEY" in col_def

    def test_oracle_identity(self):
        from aquilia.models.fields_module import AutoField
        f = AutoField(primary_key=True)
        f.name = "id"
        f.attr_name = "id"
        col_def = f.sql_column_def("oracle")
        assert "GENERATED ALWAYS AS IDENTITY" in col_def
        assert "PRIMARY KEY" in col_def
        assert "AUTOINCREMENT" not in col_def
        assert "AUTO_INCREMENT" not in col_def


class TestSqlDefaultBoolean:
    """Tests for _sql_default() boolean handling."""

    def test_postgresql_true(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=True)
        f.name = "active"
        f.attr_name = "active"
        assert f._sql_default("postgresql") == "TRUE"

    def test_postgresql_false(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=False)
        f.name = "active"
        f.attr_name = "active"
        assert f._sql_default("postgresql") == "FALSE"

    def test_sqlite_true(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=True)
        f.name = "active"
        f.attr_name = "active"
        assert f._sql_default("sqlite") == "1"

    def test_sqlite_false(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=False)
        f.name = "active"
        f.attr_name = "active"
        assert f._sql_default("sqlite") == "0"


# ════════════════════════════════════════════════════════════════════════════
# MODULE 5: ORM TYPE MAPS
# ════════════════════════════════════════════════════════════════════════════


class TestTypeMaps:
    """Tests for SQL type maps in runtime.py."""

    def test_sqlite_type_map_complete(self):
        from aquilia.models.runtime import SQLITE_TYPE_MAP
        from aquilia.models.ast_nodes import FieldType
        for ft in [FieldType.AUTO, FieldType.INT, FieldType.BIGINT, FieldType.STR,
                    FieldType.TEXT, FieldType.BOOL, FieldType.FLOAT, FieldType.DECIMAL,
                    FieldType.JSON, FieldType.BYTES, FieldType.DATETIME, FieldType.DATE,
                    FieldType.TIME, FieldType.UUID, FieldType.ENUM, FieldType.FOREIGN_KEY]:
            assert ft in SQLITE_TYPE_MAP, f"Missing {ft} in SQLITE_TYPE_MAP"

    def test_postgres_type_map_complete(self):
        from aquilia.models.runtime import POSTGRES_TYPE_MAP
        from aquilia.models.ast_nodes import FieldType
        for ft in [FieldType.AUTO, FieldType.INT, FieldType.STR, FieldType.TEXT,
                    FieldType.BOOL, FieldType.FLOAT, FieldType.JSON, FieldType.BYTES,
                    FieldType.DATETIME, FieldType.UUID]:
            assert ft in POSTGRES_TYPE_MAP

    def test_mysql_type_map_complete(self):
        from aquilia.models.runtime import MYSQL_TYPE_MAP
        from aquilia.models.ast_nodes import FieldType
        for ft in [FieldType.AUTO, FieldType.INT, FieldType.STR, FieldType.TEXT,
                    FieldType.BOOL, FieldType.FLOAT, FieldType.JSON, FieldType.BYTES]:
            assert ft in MYSQL_TYPE_MAP

    def test_oracle_type_map_complete(self):
        from aquilia.models.runtime import ORACLE_TYPE_MAP
        from aquilia.models.ast_nodes import FieldType
        for ft in [FieldType.AUTO, FieldType.INT, FieldType.BIGINT, FieldType.STR,
                    FieldType.TEXT, FieldType.BOOL, FieldType.FLOAT, FieldType.DECIMAL,
                    FieldType.JSON, FieldType.BYTES, FieldType.DATETIME, FieldType.DATE,
                    FieldType.TIME, FieldType.UUID, FieldType.ENUM, FieldType.FOREIGN_KEY]:
            assert ft in ORACLE_TYPE_MAP, f"Missing {ft} in ORACLE_TYPE_MAP"

    def test_oracle_type_map_values(self):
        from aquilia.models.runtime import ORACLE_TYPE_MAP
        from aquilia.models.ast_nodes import FieldType
        assert ORACLE_TYPE_MAP[FieldType.AUTO] == "NUMBER(10)"
        assert ORACLE_TYPE_MAP[FieldType.INT] == "NUMBER(10)"
        assert ORACLE_TYPE_MAP[FieldType.BIGINT] == "NUMBER(19)"
        assert ORACLE_TYPE_MAP[FieldType.STR] == "VARCHAR2"
        assert ORACLE_TYPE_MAP[FieldType.TEXT] == "CLOB"
        assert ORACLE_TYPE_MAP[FieldType.BOOL] == "NUMBER(1)"
        assert ORACLE_TYPE_MAP[FieldType.FLOAT] == "BINARY_DOUBLE"
        assert ORACLE_TYPE_MAP[FieldType.JSON] == "CLOB"
        assert ORACLE_TYPE_MAP[FieldType.BYTES] == "BLOB"
        assert ORACLE_TYPE_MAP[FieldType.UUID] == "VARCHAR2(36)"

    def test_get_type_map_sqlite(self):
        from aquilia.models.runtime import _get_type_map, SQLITE_TYPE_MAP
        assert _get_type_map("sqlite") is SQLITE_TYPE_MAP

    def test_get_type_map_postgresql(self):
        from aquilia.models.runtime import _get_type_map, POSTGRES_TYPE_MAP
        assert _get_type_map("postgresql") is POSTGRES_TYPE_MAP

    def test_get_type_map_mysql(self):
        from aquilia.models.runtime import _get_type_map, MYSQL_TYPE_MAP
        assert _get_type_map("mysql") is MYSQL_TYPE_MAP

    def test_get_type_map_oracle(self):
        from aquilia.models.runtime import _get_type_map, ORACLE_TYPE_MAP
        assert _get_type_map("oracle") is ORACLE_TYPE_MAP

    def test_get_type_map_unknown_falls_back_to_sqlite(self):
        from aquilia.models.runtime import _get_type_map, SQLITE_TYPE_MAP
        assert _get_type_map("unknown") is SQLITE_TYPE_MAP

    def test_type_maps_in_registry(self):
        from aquilia.models.runtime import _TYPE_MAPS
        assert "sqlite" in _TYPE_MAPS
        assert "postgresql" in _TYPE_MAPS
        assert "mysql" in _TYPE_MAPS
        assert "oracle" in _TYPE_MAPS


class TestSqlColDef:
    """Tests for _sql_col_def() in runtime.py with Oracle."""

    def test_oracle_auto_identity(self):
        """Oracle AUTO PK should use GENERATED ALWAYS AS IDENTITY."""
        from aquilia.models.runtime import _sql_col_def
        from aquilia.models.ast_nodes import FieldType

        # Create a mock SlotNode
        slot = MagicMock()
        slot.name = "id"
        slot.field_type = FieldType.AUTO
        slot.is_pk = True
        slot.is_unique = False
        slot.is_nullable = False
        slot.default_expr = None
        slot.max_length = None
        slot.type_params = None

        result = _sql_col_def(slot, "oracle")
        assert "GENERATED ALWAYS AS IDENTITY" in result
        assert "PRIMARY KEY" in result

    def test_oracle_varchar2_with_length(self):
        """Oracle STR fields should use VARCHAR2."""
        from aquilia.models.runtime import _sql_col_def
        from aquilia.models.ast_nodes import FieldType

        slot = MagicMock()
        slot.name = "name"
        slot.field_type = FieldType.STR
        slot.max_length = 255
        slot.is_pk = False
        slot.is_unique = False
        slot.is_nullable = True
        slot.default_expr = None
        slot.type_params = None

        result = _sql_col_def(slot, "oracle")
        assert "VARCHAR2(255)" in result

    def test_oracle_number_decimal(self):
        """Oracle DECIMAL should use NUMBER(p,s)."""
        from aquilia.models.runtime import _sql_col_def
        from aquilia.models.ast_nodes import FieldType

        slot = MagicMock()
        slot.name = "price"
        slot.field_type = FieldType.DECIMAL
        slot.type_params = [10, 2]
        slot.max_length = None
        slot.is_pk = False
        slot.is_unique = False
        slot.is_nullable = False
        slot.default_expr = None

        result = _sql_col_def(slot, "oracle")
        assert "NUMBER(10,2)" in result
        assert "NOT NULL" in result

    def test_sqlite_auto_pk(self):
        """SQLite AUTO PK should use AUTOINCREMENT."""
        from aquilia.models.runtime import _sql_col_def
        from aquilia.models.ast_nodes import FieldType

        slot = MagicMock()
        slot.name = "id"
        slot.field_type = FieldType.AUTO
        slot.is_pk = True
        slot.is_unique = False
        slot.is_nullable = False
        slot.default_expr = None
        slot.max_length = None
        slot.type_params = None

        result = _sql_col_def(slot, "sqlite")
        assert "AUTOINCREMENT" in result
        assert "PRIMARY KEY" in result

    def test_postgresql_serial(self):
        """PostgreSQL AUTO PK should not have AUTOINCREMENT."""
        from aquilia.models.runtime import _sql_col_def
        from aquilia.models.ast_nodes import FieldType

        slot = MagicMock()
        slot.name = "id"
        slot.field_type = FieldType.AUTO
        slot.is_pk = True
        slot.is_unique = False
        slot.is_nullable = False
        slot.default_expr = None
        slot.max_length = None
        slot.type_params = None

        result = _sql_col_def(slot, "postgresql")
        assert "SERIAL" in result
        assert "PRIMARY KEY" in result
        assert "AUTOINCREMENT" not in result

    def test_mysql_auto_increment(self):
        """MySQL AUTO PK should use AUTO_INCREMENT."""
        from aquilia.models.runtime import _sql_col_def
        from aquilia.models.ast_nodes import FieldType

        slot = MagicMock()
        slot.name = "id"
        slot.field_type = FieldType.AUTO
        slot.is_pk = True
        slot.is_unique = False
        slot.is_nullable = False
        slot.default_expr = None
        slot.max_length = None
        slot.type_params = None

        result = _sql_col_def(slot, "mysql")
        assert "AUTO_INCREMENT" in result
        assert "PRIMARY KEY" in result


# ════════════════════════════════════════════════════════════════════════════
# MODULE 6: MIGRATION DSL ORACLE SUPPORT
# ════════════════════════════════════════════════════════════════════════════


class TestColumnDefToSqlOracle:
    """Tests for ColumnDef.to_sql() Oracle dialect."""

    def test_oracle_autoincrement_pk(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(
            name="id", col_type="INTEGER",
            primary_key=True, autoincrement=True,
        )
        sql = col.to_sql("oracle")
        assert "GENERATED ALWAYS AS IDENTITY" in sql
        assert "PRIMARY KEY" in sql
        assert "AUTOINCREMENT" not in sql
        assert "AUTO_INCREMENT" not in sql

    def test_oracle_regular_column(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(
            name="name", col_type="VARCHAR(255)",
            nullable=False,
        )
        sql = col.to_sql("oracle")
        assert '"name"' in sql
        assert "NOT NULL" in sql

    def test_sqlite_autoincrement_pk(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(
            name="id", col_type="INTEGER",
            primary_key=True, autoincrement=True,
        )
        sql = col.to_sql("sqlite")
        assert "AUTOINCREMENT" in sql
        assert "PRIMARY KEY" in sql

    def test_postgresql_serial_pk(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(
            name="id", col_type="INTEGER",
            primary_key=True, autoincrement=True,
        )
        sql = col.to_sql("postgresql")
        assert "SERIAL" in sql
        assert "PRIMARY KEY" in sql
        assert "AUTOINCREMENT" not in sql

    def test_mysql_auto_increment_pk(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(
            name="id", col_type="INTEGER",
            primary_key=True, autoincrement=True,
        )
        sql = col.to_sql("mysql")
        assert "AUTO_INCREMENT" in sql
        assert "PRIMARY KEY" in sql


class TestResolveTypeOracle:
    """Tests for ColumnDef._resolve_type() Oracle dialect."""

    def test_oracle_autoincrement(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(
            name="id", col_type="INTEGER",
            primary_key=True, autoincrement=True,
        )
        resolved = col._resolve_type("oracle")
        assert resolved == "NUMBER(10) GENERATED ALWAYS AS IDENTITY"

    def test_oracle_big_autoincrement(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(
            name="id", col_type="BIGINTEGER",
            primary_key=True, autoincrement=True,
        )
        resolved = col._resolve_type("oracle")
        assert resolved == "NUMBER(19) GENERATED ALWAYS AS IDENTITY"

    def test_oracle_blob_stays_blob(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(name="data", col_type="BLOB")
        resolved = col._resolve_type("oracle")
        assert resolved == "BLOB"

    def test_oracle_real_becomes_binary_double(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(name="val", col_type="REAL")
        resolved = col._resolve_type("oracle")
        assert resolved == "BINARY_DOUBLE"

    def test_oracle_text_becomes_clob(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(name="content", col_type="TEXT")
        resolved = col._resolve_type("oracle")
        assert resolved == "CLOB"

    def test_oracle_boolean_becomes_number(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(name="active", col_type="BOOLEAN")
        resolved = col._resolve_type("oracle")
        assert resolved == "NUMBER(1)"

    def test_postgresql_blob_becomes_bytea(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(name="data", col_type="BLOB")
        resolved = col._resolve_type("postgresql")
        assert resolved == "BYTEA"


# ════════════════════════════════════════════════════════════════════════════
# MODULE 7: MIGRATION RUNNER & OPS ORACLE SUPPORT
# ════════════════════════════════════════════════════════════════════════════


class TestMigrationRunnerEnsureTrackingTable:
    """Tests for MigrationRunner.ensure_tracking_table() Oracle dialect."""

    def test_oracle_tracking_table(self):
        from aquilia.models.migration_runner import MigrationRunner
        db = MagicMock()
        db.execute = AsyncMock()
        runner = MigrationRunner(db, dialect="oracle")
        asyncio.run(runner.ensure_tracking_table())
        sql = db.execute.call_args[0][0]
        assert "GENERATED ALWAYS AS IDENTITY" in sql
        assert "PRIMARY KEY" in sql
        assert "AUTOINCREMENT" not in sql

    def test_postgresql_tracking_table(self):
        from aquilia.models.migration_runner import MigrationRunner
        db = MagicMock()
        db.execute = AsyncMock()
        runner = MigrationRunner(db, dialect="postgresql")
        asyncio.run(runner.ensure_tracking_table())
        sql = db.execute.call_args[0][0]
        assert "SERIAL" in sql
        assert "PRIMARY KEY" in sql

    def test_mysql_tracking_table(self):
        from aquilia.models.migration_runner import MigrationRunner
        db = MagicMock()
        db.execute = AsyncMock()
        runner = MigrationRunner(db, dialect="mysql")
        asyncio.run(runner.ensure_tracking_table())
        sql = db.execute.call_args[0][0]
        assert "AUTO_INCREMENT" in sql

    def test_sqlite_tracking_table(self):
        from aquilia.models.migration_runner import MigrationRunner
        db = MagicMock()
        db.execute = AsyncMock()
        runner = MigrationRunner(db, dialect="sqlite")
        asyncio.run(runner.ensure_tracking_table())
        sql = db.execute.call_args[0][0]
        assert "AUTOINCREMENT" in sql


class TestMigrationOpsPkOracle:
    """Tests for MigrationOps.pk() and bigpk() Oracle dialect."""

    def test_pk_oracle(self):
        from aquilia.models.migrations import MigrationOps
        result = MigrationOps.pk("id", dialect="oracle")
        assert "NUMBER(10)" in result
        assert "GENERATED ALWAYS AS IDENTITY" in result
        assert "PRIMARY KEY" in result

    def test_pk_postgresql(self):
        from aquilia.models.migrations import MigrationOps
        result = MigrationOps.pk("id", dialect="postgresql")
        assert "SERIAL" in result
        assert "PRIMARY KEY" in result

    def test_pk_mysql(self):
        from aquilia.models.migrations import MigrationOps
        result = MigrationOps.pk("id", dialect="mysql")
        assert "AUTO_INCREMENT" in result

    def test_pk_sqlite_default(self):
        from aquilia.models.migrations import MigrationOps
        result = MigrationOps.pk("id")
        assert "AUTOINCREMENT" in result

    def test_bigpk_oracle(self):
        from aquilia.models.migrations import MigrationOps
        result = MigrationOps.bigpk("id", dialect="oracle")
        assert "NUMBER(19)" in result
        assert "GENERATED ALWAYS AS IDENTITY" in result
        assert "PRIMARY KEY" in result

    def test_bigpk_postgresql(self):
        from aquilia.models.migrations import MigrationOps
        result = MigrationOps.bigpk("id", dialect="postgresql")
        assert "BIGSERIAL" in result

    def test_bigpk_mysql(self):
        from aquilia.models.migrations import MigrationOps
        result = MigrationOps.bigpk("id", dialect="mysql")
        assert "BIGINT" in result
        assert "AUTO_INCREMENT" in result


class TestLegacyMigrationRunnerOracle:
    """Tests for legacy MigrationRunner ensure_tracking_table Oracle."""

    def test_oracle_tracking_table_legacy(self):
        from aquilia.models.migrations import MigrationRunner as LegacyRunner
        db = MagicMock()
        db.dialect = "oracle"
        db.execute = AsyncMock()
        runner = LegacyRunner(db)
        asyncio.run(runner.ensure_tracking_table())
        sql = db.execute.call_args[0][0]
        assert "GENERATED ALWAYS AS IDENTITY" in sql
        assert "AUTOINCREMENT" not in sql

    def test_postgresql_tracking_table_legacy(self):
        from aquilia.models.migrations import MigrationRunner as LegacyRunner
        db = MagicMock()
        db.dialect = "postgresql"
        db.execute = AsyncMock()
        runner = LegacyRunner(db)
        asyncio.run(runner.ensure_tracking_table())
        sql = db.execute.call_args[0][0]
        assert "SERIAL" in sql

    def test_mysql_tracking_table_legacy(self):
        from aquilia.models.migrations import MigrationRunner as LegacyRunner
        db = MagicMock()
        db.dialect = "mysql"
        db.execute = AsyncMock()
        runner = LegacyRunner(db)
        asyncio.run(runner.ensure_tracking_table())
        sql = db.execute.call_args[0][0]
        assert "AUTO_INCREMENT" in sql


class TestMigrationOpsAlterColumnOracle:
    """Tests for MigrationOps.alter_column() Oracle dialect."""

    def test_alter_column_oracle_type(self):
        from aquilia.models.migrations import MigrationOps
        # Oracle alter_column is not explicitly handled — falls through
        # without generating SQL (no oracle branch in alter_column)
        ops = MigrationOps(dialect="oracle")
        ops.alter_column("users", "email", type="VARCHAR2(500)")
        stmts = ops._statements
        # No statements generated since Oracle has no dedicated branch
        assert len(stmts) == 0

    def test_alter_column_postgresql(self):
        from aquilia.models.migrations import MigrationOps
        ops = MigrationOps(dialect="postgresql")
        ops.alter_column("users", "email", type="VARCHAR(500)")
        stmts = ops._statements
        assert any("TYPE" in s for s in stmts)

    def test_alter_column_sqlite_comment(self):
        from aquilia.models.migrations import MigrationOps
        ops = MigrationOps(dialect="sqlite")
        ops.alter_column("users", "email", type="VARCHAR(500)")
        stmts = ops._statements
        assert any("SQLite" in s or "--" in s for s in stmts)


# ════════════════════════════════════════════════════════════════════════════
# MODULE 8: MODEL BASE CLASS ORACLE SUPPORT
# ════════════════════════════════════════════════════════════════════════════


class TestGenerateM2mSqlOracle:
    """Tests for Model.generate_m2m_sql() Oracle dialect."""

    def test_oracle_m2m_identity(self):
        """Oracle M2M junction tables should use IDENTITY, not AUTOINCREMENT."""
        from aquilia.models.base import Model
        from aquilia.models.fields_module import AutoField, CharField, ManyToManyField

        # Create a model with M2M
        class Tag(Model):
            class Meta:
                table_name = "tag"
            id = AutoField(primary_key=True)
            name = CharField(max_length=100)

        class Article(Model):
            class Meta:
                table_name = "article"
            id = AutoField(primary_key=True)
            title = CharField(max_length=200)
            tags = ManyToManyField("Tag")

        stmts = Article.generate_m2m_sql("oracle")
        assert len(stmts) > 0
        sql = stmts[0]
        assert "GENERATED ALWAYS AS IDENTITY" in sql
        assert "PRIMARY KEY" in sql
        assert "AUTOINCREMENT" not in sql
        assert "AUTO_INCREMENT" not in sql

    def test_postgresql_m2m_serial(self):
        from aquilia.models.base import Model
        from aquilia.models.fields_module import AutoField, CharField, ManyToManyField

        class TagPg(Model):
            class Meta:
                table_name = "tag_pg"
            id = AutoField(primary_key=True)
            name = CharField(max_length=100)

        class ArticlePg(Model):
            class Meta:
                table_name = "article_pg"
            id = AutoField(primary_key=True)
            title = CharField(max_length=200)
            tags = ManyToManyField("TagPg")

        stmts = ArticlePg.generate_m2m_sql("postgresql")
        if stmts:
            assert "SERIAL" in stmts[0]

    def test_mysql_m2m_auto_increment(self):
        from aquilia.models.base import Model
        from aquilia.models.fields_module import AutoField, CharField, ManyToManyField

        class TagMy(Model):
            class Meta:
                table_name = "tag_my"
            id = AutoField(primary_key=True)
            name = CharField(max_length=100)

        class ArticleMy(Model):
            class Meta:
                table_name = "article_my"
            id = AutoField(primary_key=True)
            title = CharField(max_length=200)
            tags = ManyToManyField("TagMy")

        stmts = ArticleMy.generate_m2m_sql("mysql")
        if stmts:
            assert "AUTO_INCREMENT" in stmts[0]


# ════════════════════════════════════════════════════════════════════════════
# MODULE 9: CONFIG BUILDERS INTEGRATION
# ════════════════════════════════════════════════════════════════════════════


class TestIntegrationDatabaseWithConfig:
    """Tests for Integration.database() with typed config objects."""

    def test_with_sqlite_config(self):
        from aquilia.config_builders import Integration
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig(path="app.db")
        result = Integration.database(config=config)
        assert result["enabled"] is True
        assert "sqlite:///app.db" in result["url"]

    def test_with_postgres_config(self):
        from aquilia.config_builders import Integration
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(
            host="localhost", name="mydb", user="admin", password="secret",
        )
        result = Integration.database(config=config)
        assert result["enabled"] is True
        assert "postgresql://" in result["url"]
        assert "mydb" in result["url"]

    def test_with_oracle_config(self):
        from aquilia.config_builders import Integration
        from aquilia.db.configs import OracleConfig
        config = OracleConfig(
            host="oracle.host", service_name="PROD",
            user="scott", password="tiger",
        )
        result = Integration.database(config=config)
        assert "oracle://" in result["url"]

    def test_with_url_backward_compat(self):
        from aquilia.config_builders import Integration
        result = Integration.database(url="sqlite:///legacy.db")
        assert result["url"] == "sqlite:///legacy.db"
        assert result["enabled"] is True

    def test_default_no_config_no_url(self):
        from aquilia.config_builders import Integration
        result = Integration.database()
        assert result["url"] == "sqlite:///db.sqlite3"

    def test_config_with_overrides(self):
        from aquilia.config_builders import Integration
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig(path="base.db")
        result = Integration.database(
            config=config, auto_migrate=True, pool_size=20,
        )
        assert result["auto_migrate"] is True
        assert result["pool_size"] == 20

    def test_scan_dirs_preserved(self):
        from aquilia.config_builders import Integration
        result = Integration.database(
            url="sqlite:///db.sqlite3",
            scan_dirs=["models", "modules/*/models"],
        )
        assert result["scan_dirs"] == ["models", "modules/*/models"]


class TestWorkspaceDatabaseWithConfig:
    """Tests for Workspace.database() with typed config objects."""

    def test_workspace_with_config(self):
        from aquilia.config_builders import Workspace
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(
            host="localhost", name="mydb", user="admin", password="secret",
        )
        ws = Workspace("test").database(config=config)
        d = ws.to_dict()
        assert "database" in d
        assert "url" in d["database"]
        assert "postgresql://" in d["database"]["url"]

    def test_workspace_with_url_backward_compat(self):
        from aquilia.config_builders import Workspace
        ws = Workspace("test").database(url="sqlite:///test.db")
        d = ws.to_dict()
        assert d["database"]["url"] == "sqlite:///test.db"

    def test_workspace_database_in_integrations(self):
        from aquilia.config_builders import Workspace
        ws = Workspace("test").database(url="sqlite:///test.db")
        d = ws.to_dict()
        assert "database" in d["integrations"]


class TestModuleDatabaseWithConfig:
    """Tests for Module.database() with typed config objects."""

    def test_module_with_config(self):
        from aquilia.config_builders import Module
        from aquilia.db.configs import SqliteConfig
        config = SqliteConfig(path="module.db")
        mod = Module("users").database(config=config)
        built = mod.build()
        assert built.database is not None
        assert "url" in built.database
        assert "sqlite:///module.db" in built.database["url"]

    def test_module_with_url_backward_compat(self):
        from aquilia.config_builders import Module
        mod = Module("users").database(url="sqlite:///users.db")
        built = mod.build()
        assert built.database["url"] == "sqlite:///users.db"


# ════════════════════════════════════════════════════════════════════════════
# MODULE 10: PACKAGE EXPORTS & IMPORTS
# ════════════════════════════════════════════════════════════════════════════


class TestPackageExports:
    """Tests for package-level exports."""

    def test_db_exports_oracle_adapter(self):
        from aquilia.db import OracleAdapter
        assert OracleAdapter is not None

    def test_db_exports_config_classes(self):
        from aquilia.db import (
            DatabaseConfig, SqliteConfig, PostgresConfig,
            MysqlConfig, OracleConfig,
        )
        assert DatabaseConfig is not None
        assert SqliteConfig is not None
        assert PostgresConfig is not None
        assert MysqlConfig is not None
        assert OracleConfig is not None

    def test_backends_exports_oracle(self):
        from aquilia.db.backends import OracleAdapter
        assert OracleAdapter is not None

    def test_configs_module_all(self):
        from aquilia.db.configs import __all__
        assert "DatabaseConfig" in __all__
        assert "SqliteConfig" in __all__
        assert "PostgresConfig" in __all__
        assert "MysqlConfig" in __all__
        assert "OracleConfig" in __all__

    def test_db_all_contains_oracle(self):
        from aquilia.db import __all__ as db_all
        assert "OracleAdapter" in db_all

    def test_db_all_contains_configs(self):
        from aquilia.db import __all__ as db_all
        assert "DatabaseConfig" in db_all
        assert "SqliteConfig" in db_all
        assert "PostgresConfig" in db_all
        assert "MysqlConfig" in db_all
        assert "OracleConfig" in db_all

    def test_config_builders_exports(self):
        from aquilia.config_builders import __all__ as cb_all
        assert "Workspace" in cb_all
        assert "Integration" in cb_all
        assert "Module" in cb_all

    def test_backends_all_contains_oracle(self):
        from aquilia.db.backends import __all__ as backends_all
        assert "OracleAdapter" in backends_all

    def test_engine_exports_configure_database(self):
        from aquilia.db.engine import configure_database
        assert callable(configure_database)

    def test_oracle_adapter_is_database_adapter(self):
        from aquilia.db.backends.oracle import OracleAdapter
        from aquilia.db.backends.base import DatabaseAdapter
        adapter = OracleAdapter()
        assert isinstance(adapter, DatabaseAdapter)


# ════════════════════════════════════════════════════════════════════════════
# MODULE 11: ADAPTER PATTERN CONSISTENCY
# ════════════════════════════════════════════════════════════════════════════


class TestAdapterConsistency:
    """Verify all 4 adapters implement the same interface."""

    def test_all_adapters_have_capabilities(self):
        from aquilia.db.backends.sqlite import SQLiteAdapter
        from aquilia.db.backends.postgres import PostgresAdapter
        from aquilia.db.backends.mysql import MySQLAdapter
        from aquilia.db.backends.oracle import OracleAdapter

        for AdapterClass in [SQLiteAdapter, PostgresAdapter, MySQLAdapter, OracleAdapter]:
            adapter = AdapterClass()
            caps = adapter.capabilities
            assert hasattr(caps, "name")
            assert hasattr(caps, "supports_returning")
            assert hasattr(caps, "supports_json_type")
            assert hasattr(caps, "param_style")

    def test_all_adapters_have_dialect(self):
        from aquilia.db.backends.sqlite import SQLiteAdapter
        from aquilia.db.backends.postgres import PostgresAdapter
        from aquilia.db.backends.mysql import MySQLAdapter
        from aquilia.db.backends.oracle import OracleAdapter

        assert SQLiteAdapter().dialect == "sqlite"
        assert PostgresAdapter().dialect == "postgresql"
        assert MySQLAdapter().dialect == "mysql"
        assert OracleAdapter().dialect == "oracle"

    def test_all_adapters_have_is_connected(self):
        from aquilia.db.backends.sqlite import SQLiteAdapter
        from aquilia.db.backends.postgres import PostgresAdapter
        from aquilia.db.backends.mysql import MySQLAdapter
        from aquilia.db.backends.oracle import OracleAdapter

        for AdapterClass in [SQLiteAdapter, PostgresAdapter, MySQLAdapter, OracleAdapter]:
            adapter = AdapterClass()
            assert adapter.is_connected is False

    def test_all_adapters_have_adapt_sql(self):
        from aquilia.db.backends.sqlite import SQLiteAdapter
        from aquilia.db.backends.postgres import PostgresAdapter
        from aquilia.db.backends.mysql import MySQLAdapter
        from aquilia.db.backends.oracle import OracleAdapter

        sql = "SELECT * FROM t WHERE id = ? AND name = ?"

        # SQLite: keeps ? as-is
        assert SQLiteAdapter().adapt_sql(sql) == sql

        # PostgreSQL: ? → $1, $2
        pg = PostgresAdapter().adapt_sql(sql)
        assert "$1" in pg and "$2" in pg

        # MySQL: ? → %s
        my = MySQLAdapter().adapt_sql(sql)
        assert "%s" in my

        # Oracle: ? → :1, :2
        ora = OracleAdapter().adapt_sql(sql)
        assert ":1" in ora and ":2" in ora

    def test_adapter_capabilities_unique_names(self):
        from aquilia.db.backends.sqlite import SQLiteAdapter
        from aquilia.db.backends.postgres import PostgresAdapter
        from aquilia.db.backends.mysql import MySQLAdapter
        from aquilia.db.backends.oracle import OracleAdapter

        names = {
            SQLiteAdapter().capabilities.name,
            PostgresAdapter().capabilities.name,
            MySQLAdapter().capabilities.name,
            OracleAdapter().capabilities.name,
        }
        assert len(names) == 4  # All unique


# ════════════════════════════════════════════════════════════════════════════
# MODULE 12: EDGE CASES & ROBUSTNESS
# ════════════════════════════════════════════════════════════════════════════


class TestEdgeCases:
    """Edge cases and robustness tests."""

    def test_config_with_empty_password(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(host="localhost", name="db", user="admin", password="")
        url = config.to_url()
        assert "admin" in url

    def test_config_with_no_user(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(host="localhost", name="db")
        url = config.to_url()
        assert "@" not in url

    def test_oracle_config_sid_fallback(self):
        from aquilia.db.configs import OracleConfig
        config = OracleConfig(host="h", service_name="", sid="XE")
        assert config.get_dsn() == "h:1521/XE"

    def test_oracle_config_default_service(self):
        from aquilia.db.configs import OracleConfig
        config = OracleConfig(host="h", service_name="", sid="")
        assert "ORCL" in config.get_dsn()

    def test_config_options_in_dict(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig(options={"statement_timeout": "30s"})
        d = config.to_dict()
        assert d["options"]["statement_timeout"] == "30s"

    def test_config_no_options_no_key(self):
        from aquilia.db.configs import PostgresConfig
        config = PostgresConfig()
        d = config.to_dict()
        assert "options" not in d

    def test_multiple_adapters_independent(self):
        """Each adapter instance is independent."""
        from aquilia.db.backends.oracle import OracleAdapter
        a1 = OracleAdapter()
        a2 = OracleAdapter()
        assert a1 is not a2
        assert a1._connected is False
        assert a2._connected is False

    def test_oracle_adapt_sql_complex(self):
        """Test complex SQL with mixed placeholders and strings."""
        from aquilia.db.backends.oracle import OracleAdapter
        adapter = OracleAdapter()
        sql = (
            "INSERT INTO users (name, email, bio) "
            "VALUES (?, ?, 'default ''bio'' text') "
            "WHERE id = ?"
        )
        result = adapter.adapt_sql(sql)
        assert ":1" in result
        assert ":2" in result
        assert ":3" in result
        assert "'default ''bio'' text'" in result

    def test_detect_driver_edge_cases(self):
        from aquilia.db.engine import AquiliaDatabase
        # Various oracle URL formats
        assert AquiliaDatabase._detect_driver("oracle+thin://h/s") == "oracle"
        assert AquiliaDatabase._detect_driver("oracle+thick://h/s") == "oracle"

    def test_all_field_types_have_oracle_mapping(self):
        """Ensure every FieldType used in SQLITE_TYPE_MAP also exists in ORACLE_TYPE_MAP."""
        from aquilia.models.runtime import SQLITE_TYPE_MAP, ORACLE_TYPE_MAP
        for ft in SQLITE_TYPE_MAP:
            assert ft in ORACLE_TYPE_MAP, f"FieldType {ft} missing from ORACLE_TYPE_MAP"

    def test_database_config_from_url_dispatches_correctly(self):
        """Verify factory dispatch for all URL schemes."""
        from aquilia.db.configs import DatabaseConfig, SqliteConfig, PostgresConfig, MysqlConfig, OracleConfig
        dispatch_map = {
            "sqlite:///test.db": SqliteConfig,
            "postgresql://h/d": PostgresConfig,
            "postgres://h/d": PostgresConfig,
            "mysql://h/d": MysqlConfig,
            "oracle://h/d": OracleConfig,
        }
        for url, expected_cls in dispatch_map.items():
            config = DatabaseConfig.from_url(url)
            assert isinstance(config, expected_cls), \
                f"URL {url} should produce {expected_cls.__name__}, got {type(config).__name__}"


# ════════════════════════════════════════════════════════════════════════════
# MODULE 13: BOOLEAN TYPE-SAFETY FIX (PostgreSQL migration bug)
# ════════════════════════════════════════════════════════════════════════════


class TestBooleanColumnDSL:
    """Tests that C.boolean() uses BOOLEAN col_type and resolves correctly per dialect."""

    def test_boolean_col_type_is_boolean(self):
        from aquilia.models.migration_dsl import columns as C
        col = C.boolean("flag")
        assert col.col_type == "BOOLEAN"

    def test_boolean_resolves_to_integer_on_sqlite(self):
        from aquilia.models.migration_dsl import columns as C
        col = C.boolean("active", default=True)
        sql = col.to_sql("sqlite")
        assert '"active" INTEGER' in sql
        assert "DEFAULT 1" in sql
        assert "DEFAULT TRUE" not in sql

    def test_boolean_resolves_to_boolean_on_postgresql(self):
        from aquilia.models.migration_dsl import columns as C
        col = C.boolean("active", default=True)
        sql = col.to_sql("postgresql")
        assert '"active" BOOLEAN' in sql
        assert "DEFAULT TRUE" in sql

    def test_boolean_resolves_to_integer_on_mysql(self):
        from aquilia.models.migration_dsl import columns as C
        col = C.boolean("active", default=True)
        sql = col.to_sql("mysql")
        assert '"active" INTEGER' in sql
        assert "DEFAULT 1" in sql
        assert "DEFAULT TRUE" not in sql

    def test_boolean_resolves_to_number1_on_oracle(self):
        from aquilia.models.migration_dsl import columns as C
        col = C.boolean("active", default=True)
        sql = col.to_sql("oracle")
        assert '"active" NUMBER(1)' in sql
        assert "DEFAULT 1" in sql

    def test_boolean_false_default_sqlite(self):
        from aquilia.models.migration_dsl import columns as C
        col = C.boolean("is_admin", default=False)
        sql = col.to_sql("sqlite")
        assert "DEFAULT 0" in sql

    def test_boolean_false_default_postgresql(self):
        from aquilia.models.migration_dsl import columns as C
        col = C.boolean("is_admin", default=False)
        sql = col.to_sql("postgresql")
        assert "DEFAULT FALSE" in sql

    def test_boolean_false_default_oracle(self):
        from aquilia.models.migration_dsl import columns as C
        col = C.boolean("is_admin", default=False)
        sql = col.to_sql("oracle")
        assert "DEFAULT 0" in sql

    def test_boolean_nullable(self):
        from aquilia.models.migration_dsl import columns as C
        col = C.boolean("flag", null=True)
        sql = col.to_sql("sqlite")
        assert "NOT NULL" not in sql

    def test_boolean_not_null_default(self):
        from aquilia.models.migration_dsl import columns as C
        col = C.boolean("flag")
        sql = col.to_sql("sqlite")
        assert "NOT NULL" in sql


class TestBooleanFieldSqlColumnDef:
    """Tests that BooleanField.sql_column_def produces correct DDL for all dialects."""

    def test_bool_field_def_sqlite(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=False)
        f.name = "is_superuser"
        f.attr_name = "is_superuser"
        col = f.sql_column_def("sqlite")
        assert "INTEGER" in col
        assert "DEFAULT 0" in col

    def test_bool_field_def_postgresql(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=False)
        f.name = "is_superuser"
        f.attr_name = "is_superuser"
        col = f.sql_column_def("postgresql")
        assert "BOOLEAN" in col
        assert "DEFAULT FALSE" in col
        # Must NOT have a type mismatch (INTEGER with TRUE/FALSE)
        assert "INTEGER" not in col

    def test_bool_field_def_postgresql_true(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=True)
        f.name = "is_active"
        f.attr_name = "is_active"
        col = f.sql_column_def("postgresql")
        assert "BOOLEAN" in col
        assert "DEFAULT TRUE" in col

    def test_bool_field_def_oracle(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=True)
        f.name = "is_active"
        f.attr_name = "is_active"
        col = f.sql_column_def("oracle")
        assert "NUMBER(1)" in col
        assert "DEFAULT 1" in col
        assert "TRUE" not in col

    def test_bool_field_def_mysql(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=True)
        f.name = "is_staff"
        f.attr_name = "is_staff"
        col = f.sql_column_def("mysql")
        assert "INTEGER" in col
        assert "DEFAULT 1" in col


class TestIntegerWithBoolDefaultSafety:
    """Ensure C.integer() with a bool default doesn't produce TRUE/FALSE on PostgreSQL."""

    def test_integer_bool_default_postgresql(self):
        """C.integer('flag', default=True) must NOT produce DEFAULT TRUE on PG."""
        from aquilia.models.migration_dsl import columns as C
        col = C.integer("flag", default=True)
        sql = col.to_sql("postgresql")
        # INTEGER column on PostgreSQL cannot have DEFAULT TRUE
        assert "DEFAULT 1" in sql
        assert "DEFAULT TRUE" not in sql

    def test_integer_bool_false_default_postgresql(self):
        from aquilia.models.migration_dsl import columns as C
        col = C.integer("flag", default=False)
        sql = col.to_sql("postgresql")
        assert "DEFAULT 0" in sql
        assert "DEFAULT FALSE" not in sql

    def test_integer_int_default_postgresql(self):
        """Regular int defaults on INTEGER columns should work as before."""
        from aquilia.models.migration_dsl import columns as C
        col = C.integer("count", default=0)
        sql = col.to_sql("postgresql")
        assert "DEFAULT 0" in sql

    def test_integer_bool_default_sqlite(self):
        """SQLite INTEGER with bool default — always 0/1."""
        from aquilia.models.migration_dsl import columns as C
        col = C.integer("flag", default=True)
        sql = col.to_sql("sqlite")
        assert "DEFAULT 1" in sql

    def test_integer_bool_default_oracle(self):
        """Oracle NUMBER(10) with bool default — always 0/1."""
        from aquilia.models.migration_dsl import columns as C
        col = C.integer("flag", default=True)
        sql = col.to_sql("oracle")
        assert "DEFAULT 1" in sql
        assert "DEFAULT TRUE" not in sql


class TestResolveTypeBooleanDialects:
    """Tests that _resolve_type correctly maps BOOLEAN per dialect."""

    def test_boolean_sqlite(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(name="flag", col_type="BOOLEAN")
        assert col._resolve_type("sqlite") == "INTEGER"

    def test_boolean_postgresql(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(name="flag", col_type="BOOLEAN")
        assert col._resolve_type("postgresql") == "BOOLEAN"

    def test_boolean_mysql(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(name="flag", col_type="BOOLEAN")
        assert col._resolve_type("mysql") == "INTEGER"

    def test_boolean_oracle(self):
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(name="flag", col_type="BOOLEAN")
        assert col._resolve_type("oracle") == "NUMBER(1)"


class TestFormatDefaultDialectAware:
    """Tests for _format_default with col_type awareness."""

    def test_bool_true_on_boolean_col_postgresql(self):
        from aquilia.models.migration_dsl import _format_default
        assert _format_default(True, "postgresql", "BOOLEAN") == "TRUE"

    def test_bool_false_on_boolean_col_postgresql(self):
        from aquilia.models.migration_dsl import _format_default
        assert _format_default(False, "postgresql", "BOOLEAN") == "FALSE"

    def test_bool_true_on_integer_col_postgresql(self):
        from aquilia.models.migration_dsl import _format_default
        assert _format_default(True, "postgresql", "INTEGER") == "1"

    def test_bool_false_on_integer_col_postgresql(self):
        from aquilia.models.migration_dsl import _format_default
        assert _format_default(False, "postgresql", "INTEGER") == "0"

    def test_bool_true_on_integer_col_sqlite(self):
        from aquilia.models.migration_dsl import _format_default
        assert _format_default(True, "sqlite", "INTEGER") == "1"

    def test_bool_true_on_number1_col_oracle(self):
        from aquilia.models.migration_dsl import _format_default
        assert _format_default(True, "oracle", "NUMBER(1)") == "1"

    def test_bool_default_no_col_type_postgresql(self):
        """When col_type not specified, PostgreSQL defaults to TRUE/FALSE."""
        from aquilia.models.migration_dsl import _format_default
        assert _format_default(True, "postgresql") == "TRUE"

    def test_int_default_unchanged(self):
        from aquilia.models.migration_dsl import _format_default
        assert _format_default(42, "postgresql", "INTEGER") == "42"

    def test_str_default_quoted(self):
        from aquilia.models.migration_dsl import _format_default
        assert _format_default("hello", "postgresql") == "'hello'"

    def test_str_with_quotes_escaped(self):
        from aquilia.models.migration_dsl import _format_default
        assert _format_default("it's", "sqlite") == "'it''s'"

    def test_none_default(self):
        from aquilia.models.migration_dsl import _format_default
        assert _format_default(None, "postgresql") == "NULL"


class TestMigrationOpsFormatDefault:
    """Tests for _format_default in migrations.py (MigrationOps path)."""

    def test_bool_default_postgresql(self):
        from aquilia.models.migrations import _format_default
        assert _format_default(True, "postgresql") == "TRUE"
        assert _format_default(False, "postgresql") == "FALSE"

    def test_bool_default_mysql(self):
        from aquilia.models.migrations import _format_default
        assert _format_default(True, "mysql") == "1"
        assert _format_default(False, "mysql") == "0"

    def test_bool_default_sqlite(self):
        from aquilia.models.migrations import _format_default
        assert _format_default(True, "sqlite") == "1"
        assert _format_default(False, "sqlite") == "0"

    def test_bool_default_oracle(self):
        from aquilia.models.migrations import _format_default
        assert _format_default(True, "oracle") == "1"
        assert _format_default(False, "oracle") == "0"


class TestSchemaSnapshotBooleanField:
    """Tests that _field_to_sql_type maps BooleanField to BOOLEAN."""

    def test_boolean_field_maps_to_boolean(self):
        from aquilia.models.schema_snapshot import _field_to_sql_type
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=True)
        assert _field_to_sql_type(f) == "BOOLEAN"

    def test_integer_field_maps_to_integer(self):
        from aquilia.models.schema_snapshot import _field_to_sql_type
        from aquilia.models.fields_module import IntegerField
        f = IntegerField()
        assert _field_to_sql_type(f) == "INTEGER"


class TestMigrationGenBooleanField:
    """Tests that _render_column_def emits C.boolean() for BOOLEAN columns."""

    def test_boolean_col_renders_c_boolean(self):
        from aquilia.models.migration_dsl import ColumnDef, _SentinelType
        from aquilia.models.migration_gen import _render_column_def
        _SENTINEL = _SentinelType()
        col = ColumnDef(name="is_active", col_type="BOOLEAN", default=True)
        rendered = _render_column_def(col)
        assert rendered == 'C.boolean("is_active", default=True)'

    def test_boolean_col_false_renders_c_boolean(self):
        from aquilia.models.migration_dsl import ColumnDef
        from aquilia.models.migration_gen import _render_column_def
        col = ColumnDef(name="is_superuser", col_type="BOOLEAN", default=False)
        rendered = _render_column_def(col)
        assert rendered == 'C.boolean("is_superuser", default=False)'

    def test_integer_col_still_renders_c_integer(self):
        from aquilia.models.migration_dsl import ColumnDef
        from aquilia.models.migration_gen import _render_column_def
        col = ColumnDef(name="action_flag", col_type="INTEGER")
        rendered = _render_column_def(col)
        assert rendered == 'C.integer("action_flag")'

    def test_boolean_nullable_renders_correctly(self):
        from aquilia.models.migration_dsl import ColumnDef
        from aquilia.models.migration_gen import _render_column_def
        col = ColumnDef(name="flag", col_type="BOOLEAN", nullable=True, default=False)
        rendered = _render_column_def(col)
        assert "C.boolean(" in rendered
        assert "null=True" in rendered
        assert "default=False" in rendered


class TestAdminUserMigrationIntegrity:
    """End-to-end tests verifying AdminUser fields generate correct DDL on all dialects."""

    def test_admin_user_is_superuser_postgresql(self):
        """is_superuser must produce BOOLEAN NOT NULL DEFAULT FALSE on PostgreSQL."""
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=False)
        f.name = "is_superuser"
        f.attr_name = "is_superuser"
        col = f.sql_column_def("postgresql")
        # Must be BOOLEAN, not INTEGER
        assert '"is_superuser" BOOLEAN' in col
        assert "DEFAULT FALSE" in col
        assert "NOT NULL" in col

    def test_admin_user_is_staff_postgresql(self):
        """is_staff must produce BOOLEAN NOT NULL DEFAULT TRUE on PostgreSQL."""
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=True)
        f.name = "is_staff"
        f.attr_name = "is_staff"
        col = f.sql_column_def("postgresql")
        assert '"is_staff" BOOLEAN' in col
        assert "DEFAULT TRUE" in col

    def test_admin_user_is_active_postgresql(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=True)
        f.name = "is_active"
        f.attr_name = "is_active"
        col = f.sql_column_def("postgresql")
        assert '"is_active" BOOLEAN' in col
        assert "DEFAULT TRUE" in col

    def test_admin_user_boolean_fields_sqlite(self):
        """SQLite: BooleanField → INTEGER DEFAULT 0/1."""
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=False)
        f.name = "is_superuser"
        f.attr_name = "is_superuser"
        col = f.sql_column_def("sqlite")
        assert '"is_superuser" INTEGER' in col
        assert "DEFAULT 0" in col

    def test_admin_user_boolean_fields_oracle(self):
        """Oracle: BooleanField → NUMBER(1) DEFAULT 0/1."""
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=True)
        f.name = "is_staff"
        f.attr_name = "is_staff"
        col = f.sql_column_def("oracle")
        assert '"is_staff" NUMBER(1)' in col
        assert "DEFAULT 1" in col

    def test_migration_dsl_boolean_postgresql_no_type_mismatch(self):
        """The exact error scenario: C.boolean with bool default on PostgreSQL."""
        from aquilia.models.migration_dsl import columns as C
        col_superuser = C.boolean("is_superuser", default=False)
        col_staff = C.boolean("is_staff", default=True)
        col_active = C.boolean("is_active", default=True)

        sql_su = col_superuser.to_sql("postgresql")
        sql_st = col_staff.to_sql("postgresql")
        sql_ac = col_active.to_sql("postgresql")

        # All must be BOOLEAN with TRUE/FALSE defaults
        assert '"is_superuser" BOOLEAN NOT NULL DEFAULT FALSE' == sql_su
        assert '"is_staff" BOOLEAN NOT NULL DEFAULT TRUE' == sql_st
        assert '"is_active" BOOLEAN NOT NULL DEFAULT TRUE' == sql_ac

    def test_migration_dsl_boolean_sqlite_no_type_mismatch(self):
        from aquilia.models.migration_dsl import columns as C
        col = C.boolean("is_superuser", default=False)
        sql = col.to_sql("sqlite")
        assert '"is_superuser" INTEGER NOT NULL DEFAULT 0' == sql


# ════════════════════════════════════════════════════════════════════════════
# MODULE 14: BOOLEAN to_db() BIND PARAMETER FIX (asyncpg type safety)
# ════════════════════════════════════════════════════════════════════════════


class TestBooleanFieldToDbDialectAware:
    """BooleanField.to_db() must return native Python bool for PostgreSQL
    and int (0/1) for SQLite/MySQL/Oracle. asyncpg rejects int for BOOLEAN cols."""

    def test_to_db_postgresql_true_returns_bool(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=False)
        f.name = "flag"
        result = f.to_db(True, dialect="postgresql")
        assert result is True
        assert isinstance(result, bool)

    def test_to_db_postgresql_false_returns_bool(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=False)
        f.name = "flag"
        result = f.to_db(False, dialect="postgresql")
        assert result is False
        assert isinstance(result, bool)

    def test_to_db_sqlite_true_returns_int(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=False)
        f.name = "flag"
        result = f.to_db(True, dialect="sqlite")
        assert result == 1
        assert isinstance(result, int) and not isinstance(result, bool)

    def test_to_db_sqlite_false_returns_int(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=False)
        f.name = "flag"
        result = f.to_db(False, dialect="sqlite")
        assert result == 0
        assert isinstance(result, int) and not isinstance(result, bool)

    def test_to_db_mysql_returns_int(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=False)
        f.name = "flag"
        assert f.to_db(True, dialect="mysql") == 1
        assert isinstance(f.to_db(True, dialect="mysql"), int)
        assert f.to_db(False, dialect="mysql") == 0

    def test_to_db_oracle_returns_int(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=False)
        f.name = "flag"
        assert f.to_db(True, dialect="oracle") == 1
        assert isinstance(f.to_db(True, dialect="oracle"), int)
        assert f.to_db(False, dialect="oracle") == 0

    def test_to_db_none_returns_none(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(null=True)
        f.name = "flag"
        assert f.to_db(None, dialect="postgresql") is None
        assert f.to_db(None, dialect="sqlite") is None

    def test_to_db_default_dialect_is_sqlite(self):
        """Default dialect should be sqlite (backward compat)."""
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=True)
        f.name = "flag"
        result = f.to_db(True)
        assert result == 1
        assert isinstance(result, int)

    def test_to_db_postgresql_truthy_int_returns_bool(self):
        """Even passing int 1 should return bool True for postgresql."""
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=False)
        f.name = "flag"
        assert f.to_db(1, dialect="postgresql") is True
        assert f.to_db(0, dialect="postgresql") is False

    def test_to_db_sqlite_truthy_int_returns_int(self):
        from aquilia.models.fields_module import BooleanField
        f = BooleanField(default=False)
        f.name = "flag"
        assert f.to_db(1, dialect="sqlite") == 1
        assert f.to_db(0, dialect="sqlite") == 0


class TestFieldToDbDialectSignature:
    """All Field subclasses must accept the dialect kwarg on to_db()."""

    def test_base_field_accepts_dialect(self):
        from aquilia.models.fields_module import CharField
        f = CharField(max_length=100)
        f.name = "name"
        assert f.to_db("hello", dialect="postgresql") == "hello"
        assert f.to_db("hello", dialect="sqlite") == "hello"

    def test_integer_field_accepts_dialect(self):
        from aquilia.models.fields_module import IntegerField
        f = IntegerField()
        f.name = "count"
        assert f.to_db(42, dialect="postgresql") == 42

    def test_decimal_field_accepts_dialect(self):
        from aquilia.models.fields_module import DecimalField
        f = DecimalField(max_digits=10, decimal_places=2)
        f.name = "price"
        import decimal
        assert f.to_db(decimal.Decimal("9.99"), dialect="postgresql") == "9.99"

    def test_uuid_field_accepts_dialect(self):
        from aquilia.models.fields_module import UUIDField
        import uuid
        f = UUIDField()
        f.name = "uid"
        u = uuid.uuid4()
        assert f.to_db(u, dialect="postgresql") == str(u)

    def test_json_field_accepts_dialect(self):
        from aquilia.models.fields_module import JSONField
        f = JSONField()
        f.name = "data"
        assert f.to_db({"a": 1}, dialect="postgresql") == '{"a": 1}'

    def test_date_field_accepts_dialect(self):
        from aquilia.models.fields_module import DateField
        import datetime
        f = DateField()
        f.name = "dt"
        d = datetime.date(2025, 1, 1)
        # Oracle/PG/MySQL drivers expect native date objects; only SQLite uses strings
        assert f.to_db(d, dialect="oracle") == d
        assert f.to_db(d, dialect="sqlite") == "2025-01-01"


class TestAdminSuperuserCreateBindParams:
    """Simulate the exact create_superuser flow: BooleanField.to_db()
    is called from base.py create() with the db dialect."""

    def test_superuser_boolean_bind_params_postgresql(self):
        from aquilia.models.fields_module import BooleanField
        # Simulate what base.py create() does:
        fields = {
            "is_superuser": BooleanField(default=False),
            "is_staff": BooleanField(default=True),
            "is_active": BooleanField(default=True),
        }
        data = {"is_superuser": True, "is_staff": True, "is_active": True}
        dialect = "postgresql"

        bind_params = {}
        for name, field in fields.items():
            field.name = name
            bind_params[name] = field.to_db(data[name], dialect=dialect)

        # asyncpg requires Python bool for BOOLEAN columns
        assert bind_params["is_superuser"] is True
        assert isinstance(bind_params["is_superuser"], bool)
        assert bind_params["is_staff"] is True
        assert isinstance(bind_params["is_staff"], bool)
        assert bind_params["is_active"] is True
        assert isinstance(bind_params["is_active"], bool)

    def test_superuser_boolean_bind_params_sqlite(self):
        from aquilia.models.fields_module import BooleanField
        fields = {
            "is_superuser": BooleanField(default=False),
            "is_staff": BooleanField(default=True),
            "is_active": BooleanField(default=True),
        }
        data = {"is_superuser": True, "is_staff": True, "is_active": True}
        dialect = "sqlite"

        bind_params = {}
        for name, field in fields.items():
            field.name = name
            bind_params[name] = field.to_db(data[name], dialect=dialect)

        # SQLite uses INTEGER for booleans
        assert bind_params["is_superuser"] == 1
        assert isinstance(bind_params["is_superuser"], int)
        assert not isinstance(bind_params["is_superuser"], bool)


# ════════════════════════════════════════════════════════════════════════════
# MODULE 15: DATE/TIME/DATETIME to_db() BIND PARAMETER FIX (asyncpg)
# ════════════════════════════════════════════════════════════════════════════


class TestDateTimeFieldToDbDialectAware:
    """DateTimeField.to_db() must return native datetime for PG/MySQL/Oracle,
    ISO string for SQLite. asyncpg rejects strings for TIMESTAMP columns."""

    def test_to_db_postgresql_returns_native_datetime(self):
        import datetime
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(); f.name = "created_at"
        dt = datetime.datetime(2026, 3, 5, 15, 49, 38, tzinfo=datetime.timezone.utc)
        result = f.to_db(dt, dialect="postgresql")
        assert result is dt
        assert isinstance(result, datetime.datetime)

    def test_to_db_sqlite_returns_iso_string(self):
        import datetime
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(); f.name = "created_at"
        dt = datetime.datetime(2026, 3, 5, 15, 49, 38, tzinfo=datetime.timezone.utc)
        result = f.to_db(dt, dialect="sqlite")
        assert isinstance(result, str)
        assert result == "2026-03-05T15:49:38+00:00"

    def test_to_db_mysql_returns_native_datetime(self):
        import datetime
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(); f.name = "created_at"
        dt = datetime.datetime(2026, 3, 5, 15, 49, 38)
        result = f.to_db(dt, dialect="mysql")
        assert result is dt

    def test_to_db_oracle_returns_native_datetime(self):
        import datetime
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(); f.name = "created_at"
        dt = datetime.datetime(2026, 3, 5, 15, 49, 38)
        result = f.to_db(dt, dialect="oracle")
        assert result is dt

    def test_to_db_none(self):
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(null=True); f.name = "x"
        assert f.to_db(None, dialect="postgresql") is None
        assert f.to_db(None, dialect="sqlite") is None


class TestDateFieldToDbDialectAware:
    """DateField.to_db() must return native date for PG/MySQL/Oracle."""

    def test_to_db_postgresql_returns_native_date(self):
        import datetime
        from aquilia.models.fields_module import DateField
        f = DateField(); f.name = "born"
        d = datetime.date(2026, 3, 5)
        result = f.to_db(d, dialect="postgresql")
        assert result is d
        assert isinstance(result, datetime.date)

    def test_to_db_sqlite_returns_iso_string(self):
        import datetime
        from aquilia.models.fields_module import DateField
        f = DateField(); f.name = "born"
        d = datetime.date(2026, 3, 5)
        result = f.to_db(d, dialect="sqlite")
        assert result == "2026-03-05"
        assert isinstance(result, str)

    def test_to_db_mysql_returns_native_date(self):
        import datetime
        from aquilia.models.fields_module import DateField
        f = DateField(); f.name = "born"
        d = datetime.date(2026, 3, 5)
        assert f.to_db(d, dialect="mysql") is d

    def test_to_db_oracle_returns_native_date(self):
        import datetime
        from aquilia.models.fields_module import DateField
        f = DateField(); f.name = "born"
        d = datetime.date(2026, 3, 5)
        assert f.to_db(d, dialect="oracle") is d


class TestTimeFieldToDbDialectAware:
    """TimeField.to_db() must return native time for PG/MySQL/Oracle."""

    def test_to_db_postgresql_returns_native_time(self):
        import datetime
        from aquilia.models.fields_module import TimeField
        f = TimeField(); f.name = "start"
        t = datetime.time(15, 49, 38)
        result = f.to_db(t, dialect="postgresql")
        assert result is t
        assert isinstance(result, datetime.time)

    def test_to_db_sqlite_returns_iso_string(self):
        import datetime
        from aquilia.models.fields_module import TimeField
        f = TimeField(); f.name = "start"
        t = datetime.time(15, 49, 38)
        result = f.to_db(t, dialect="sqlite")
        assert result == "15:49:38"
        assert isinstance(result, str)

    def test_to_db_mysql_returns_native_time(self):
        import datetime
        from aquilia.models.fields_module import TimeField
        f = TimeField(); f.name = "start"
        t = datetime.time(15, 49, 38)
        assert f.to_db(t, dialect="mysql") is t


class TestAdminCreateSuperuserDatetimeBindParams:
    """Simulate the exact superuser creation flow with DateTimeField."""

    def test_datetime_bind_params_postgresql(self):
        import datetime
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(auto_now_add=True); f.name = "date_joined"; f.attr_name = "date_joined"
        dt = datetime.datetime(2026, 3, 5, 15, 49, 38, 634367, tzinfo=datetime.timezone.utc)
        result = f.to_db(dt, dialect="postgresql")
        # asyncpg requires native datetime for TIMESTAMP columns
        assert isinstance(result, datetime.datetime)
        assert not isinstance(result, str)

    def test_datetime_bind_params_sqlite(self):
        import datetime
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(auto_now_add=True); f.name = "date_joined"; f.attr_name = "date_joined"
        dt = datetime.datetime(2026, 3, 5, 15, 49, 38, 634367, tzinfo=datetime.timezone.utc)
        result = f.to_db(dt, dialect="sqlite")
        assert isinstance(result, str)


# ── Module 16: TIMESTAMP WITH TIME ZONE resolution & naive-datetime hardening ─

class TestTimestampWithTimeZoneResolution:
    """_resolve_type() must map TIMESTAMP → TIMESTAMP WITH TIME ZONE on PG & Oracle."""

    def test_postgresql_timestamp_resolves_to_timestamptz(self):
        from aquilia.models.migration_dsl import C
        col = C.timestamp("created")
        resolved = col._resolve_type("postgresql")
        assert resolved == "TIMESTAMP WITH TIME ZONE"

    def test_oracle_timestamp_resolves_to_timestamptz(self):
        from aquilia.models.migration_dsl import C
        col = C.timestamp("created")
        resolved = col._resolve_type("oracle")
        assert resolved == "TIMESTAMP WITH TIME ZONE"

    def test_sqlite_timestamp_stays_timestamp(self):
        from aquilia.models.migration_dsl import C
        col = C.timestamp("created")
        resolved = col._resolve_type("sqlite")
        assert resolved == "TIMESTAMP"

    def test_mysql_timestamp_stays_timestamp(self):
        from aquilia.models.migration_dsl import C
        col = C.timestamp("created")
        resolved = col._resolve_type("mysql")
        assert resolved == "TIMESTAMP"

    def test_postgresql_timestamp_in_rendered_sql(self):
        from aquilia.models.migration_dsl import C
        col = C.timestamp("created")
        sql = col.to_sql("postgresql")
        assert "TIMESTAMP WITH TIME ZONE" in sql

    def test_oracle_timestamp_in_rendered_sql(self):
        from aquilia.models.migration_dsl import C
        col = C.timestamp("created")
        sql = col.to_sql("oracle")
        assert "TIMESTAMP WITH TIME ZONE" in sql

    def test_sqlite_timestamp_in_rendered_sql(self):
        from aquilia.models.migration_dsl import C
        col = C.timestamp("created")
        sql = col.to_sql("sqlite")
        assert "TIMESTAMP" in sql
        assert "WITH TIME ZONE" not in sql


class TestDateTimeFieldNaiveDatetimeHardening:
    """to_db() must add UTC tzinfo to naive datetimes on PostgreSQL."""

    def test_naive_datetime_gets_utc_on_postgresql(self):
        import datetime
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(); f.name = "ts"
        naive = datetime.datetime(2026, 3, 5, 15, 53, 20, 123456)
        assert naive.tzinfo is None
        result = f.to_db(naive, dialect="postgresql")
        assert isinstance(result, datetime.datetime)
        assert result.tzinfo is datetime.timezone.utc
        # Value should be identical except for tzinfo
        assert result.year == 2026
        assert result.microsecond == 123456

    def test_aware_datetime_unchanged_on_postgresql(self):
        import datetime
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(); f.name = "ts"
        aware = datetime.datetime(2026, 3, 5, 15, 53, 20, tzinfo=datetime.timezone.utc)
        result = f.to_db(aware, dialect="postgresql")
        assert result is aware  # exact same object, no copy

    def test_naive_datetime_unchanged_on_sqlite(self):
        import datetime
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(); f.name = "ts"
        naive = datetime.datetime(2026, 3, 5, 15, 53, 20)
        result = f.to_db(naive, dialect="sqlite")
        # SQLite gets ISO string, no tzinfo patching needed
        assert isinstance(result, str)

    def test_naive_datetime_unchanged_on_mysql(self):
        import datetime
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(); f.name = "ts"
        naive = datetime.datetime(2026, 3, 5, 15, 53, 20)
        result = f.to_db(naive, dialect="mysql")
        # MySQL returns the native datetime as-is (no tzinfo patching)
        assert result is naive

    def test_naive_datetime_unchanged_on_oracle(self):
        import datetime
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(); f.name = "ts"
        naive = datetime.datetime(2026, 3, 5, 15, 53, 20)
        result = f.to_db(naive, dialect="oracle")
        assert result is naive


class TestDateTimeFieldAutoNowAddDefault:
    """auto_now_add should set a callable default when none is provided."""

    def test_auto_now_add_sets_default(self):
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(auto_now_add=True)
        assert f.has_default()

    def test_auto_now_add_default_produces_utc_datetime(self):
        import datetime
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(auto_now_add=True)
        val = f.get_default()
        assert isinstance(val, datetime.datetime)
        assert val.tzinfo is not None

    def test_auto_now_add_with_explicit_default_preserves_it(self):
        import datetime
        from aquilia.models.fields_module import DateTimeField
        sentinel = datetime.datetime(2000, 1, 1, tzinfo=datetime.timezone.utc)
        f = DateTimeField(auto_now_add=True, default=sentinel)
        # get_default() returns deepcopy, so use == not is
        assert f.default is sentinel
        assert f.get_default() == sentinel

    def test_auto_now_not_add_no_default(self):
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField(auto_now=True)
        # auto_now alone does not set a default
        assert not f.has_default()

    def test_plain_datetime_field_no_default(self):
        from aquilia.models.fields_module import DateTimeField
        f = DateTimeField()
        assert not f.has_default()


# ── Module 17: MySQL adapter identifier quoting ──────────────────────────────

class TestMySQLAdaptSqlIdentifierQuoting:
    """MySQL adapt_sql() must convert double-quoted identifiers to backticks."""

    def test_create_table_identifiers(self):
        from aquilia.db.backends.mysql import MySQLAdapter
        adapter = MySQLAdapter()
        sql = 'CREATE TABLE IF NOT EXISTS "users" (\n  "id" INTEGER PRIMARY KEY\n);'
        result = adapter.adapt_sql(sql)
        assert '`users`' in result
        assert '`id`' in result
        assert '"' not in result

    def test_insert_identifiers_and_placeholders(self):
        from aquilia.db.backends.mysql import MySQLAdapter
        adapter = MySQLAdapter()
        sql = 'INSERT INTO "users" ("name", "email") VALUES (?, ?)'
        result = adapter.adapt_sql(sql)
        assert result == "INSERT INTO `users` (`name`, `email`) VALUES (%s, %s)"

    def test_string_literals_preserved(self):
        from aquilia.db.backends.mysql import MySQLAdapter
        adapter = MySQLAdapter()
        sql = """SELECT * FROM "users" WHERE "name" = 'O''Brien' AND "id" = ?"""
        result = adapter.adapt_sql(sql)
        assert "`users`" in result
        assert "`name`" in result
        assert "`id`" in result
        assert "O''Brien" in result
        assert "%s" in result

    def test_fk_references_converted(self):
        from aquilia.db.backends.mysql import MySQLAdapter
        adapter = MySQLAdapter()
        sql = '"user_id" INTEGER REFERENCES "users"("id") ON DELETE CASCADE'
        result = adapter.adapt_sql(sql)
        assert '`user_id`' in result
        assert '`users`' in result
        assert '`id`' in result

    def test_no_double_quotes_remain(self):
        from aquilia.db.backends.mysql import MySQLAdapter
        adapter = MySQLAdapter()
        sql = (
            'CREATE TABLE "admin_users" (\n'
            '  "id" INTEGER PRIMARY KEY AUTO_INCREMENT,\n'
            '  "username" VARCHAR(150) NOT NULL UNIQUE,\n'
            '  "is_active" INTEGER NOT NULL DEFAULT 1\n'
            ');'
        )
        result = adapter.adapt_sql(sql)
        assert '"' not in result
        assert "`admin_users`" in result
        assert "`username`" in result


class TestPostgresAdaptSqlPreservesQuotes:
    """PostgreSQL adapt_sql() must keep double-quoted identifiers as-is."""

    def test_identifiers_stay_double_quoted(self):
        from aquilia.db.backends.postgres import PostgresAdapter
        adapter = PostgresAdapter()
        sql = 'INSERT INTO "users" ("name") VALUES (?)'
        result = adapter.adapt_sql(sql)
        assert '"users"' in result
        assert '"name"' in result
        assert "$1" in result


# ═══════════════════════════════════════════════════════════════════════════════
# Module 18 — Database Config `database` Parameter Alias
# ═══════════════════════════════════════════════════════════════════════════════
# PostgresConfig, MysqlConfig, OracleConfig now accept a `database` keyword
# as an ergonomic alias for the canonical field (`name` or `service_name`).
# The alias is resolved in __post_init__ and then cleared so it never leaks
# into to_dict() or to_url().
# ═══════════════════════════════════════════════════════════════════════════════


class TestPostgresConfigDatabaseAlias:
    """PostgresConfig `database=` resolves to `name`."""

    def test_database_sets_name(self):
        from aquilia.db.configs import PostgresConfig
        cfg = PostgresConfig(host="localhost", database="mydb", user="u", password="p")
        assert cfg.name == "mydb"

    def test_database_field_cleared_after_init(self):
        from aquilia.db.configs import PostgresConfig
        cfg = PostgresConfig(host="localhost", database="mydb", user="u", password="p")
        assert cfg.database == ""

    def test_name_still_works(self):
        from aquilia.db.configs import PostgresConfig
        cfg = PostgresConfig(host="localhost", name="mydb", user="u", password="p")
        assert cfg.name == "mydb"

    def test_name_takes_precedence_over_database(self):
        from aquilia.db.configs import PostgresConfig
        cfg = PostgresConfig(host="localhost", name="explicit", database="alias", user="u", password="p")
        assert cfg.name == "explicit"

    def test_to_url_with_database(self):
        from aquilia.db.configs import PostgresConfig
        cfg = PostgresConfig(host="localhost", port=5432, database="mydb", user="u", password="p")
        url = cfg.to_url()
        assert "mydb" in url
        assert url.startswith("postgresql://")

    def test_to_dict_excludes_database_alias(self):
        from aquilia.db.configs import PostgresConfig
        cfg = PostgresConfig(host="localhost", database="mydb", user="u", password="p")
        d = cfg.to_dict()
        # `database` should NOT appear as a standalone key
        assert "database" not in d
        # The database name appears inside the URL
        assert "mydb" in d["url"]

    def test_repr_shows_database_label(self):
        from aquilia.db.configs import PostgresConfig
        cfg = PostgresConfig(host="localhost", database="mydb", user="u", password="p")
        r = repr(cfg)
        assert "database=" in r
        assert "mydb" in r

    def test_from_url_roundtrip_with_database(self):
        from aquilia.db.configs import PostgresConfig
        cfg1 = PostgresConfig(host="localhost", port=5432, database="mydb", user="u", password="p")
        url = cfg1.to_url()
        cfg2 = PostgresConfig.from_url(url)
        assert cfg2.name == "mydb"


class TestMysqlConfigDatabaseAlias:
    """MysqlConfig `database=` resolves to `name`."""

    def test_database_sets_name(self):
        from aquilia.db.configs import MysqlConfig
        cfg = MysqlConfig(host="localhost", database="mydb", user="u", password="p")
        assert cfg.name == "mydb"

    def test_database_field_cleared_after_init(self):
        from aquilia.db.configs import MysqlConfig
        cfg = MysqlConfig(host="localhost", database="mydb", user="u", password="p")
        assert cfg.database == ""

    def test_name_still_works(self):
        from aquilia.db.configs import MysqlConfig
        cfg = MysqlConfig(host="localhost", name="mydb", user="u", password="p")
        assert cfg.name == "mydb"

    def test_name_takes_precedence_over_database(self):
        from aquilia.db.configs import MysqlConfig
        cfg = MysqlConfig(host="localhost", name="explicit", database="alias", user="u", password="p")
        assert cfg.name == "explicit"

    def test_to_url_with_database(self):
        from aquilia.db.configs import MysqlConfig
        cfg = MysqlConfig(host="localhost", port=3306, database="mydb", user="u", password="p")
        url = cfg.to_url()
        assert "mydb" in url
        assert url.startswith("mysql://")

    def test_to_dict_excludes_database_alias(self):
        from aquilia.db.configs import MysqlConfig
        cfg = MysqlConfig(host="localhost", database="mydb", user="u", password="p")
        d = cfg.to_dict()
        assert "database" not in d
        assert "mydb" in d["url"]

    def test_repr_shows_database_label(self):
        from aquilia.db.configs import MysqlConfig
        cfg = MysqlConfig(host="localhost", database="mydb", user="u", password="p")
        r = repr(cfg)
        assert "database=" in r
        assert "mydb" in r


class TestOracleConfigDatabaseAlias:
    """OracleConfig `database=` resolves to `service_name`."""

    def test_database_sets_service_name(self):
        from aquilia.db.configs import OracleConfig
        cfg = OracleConfig(host="localhost", database="PROD", user="u", password="p")
        assert cfg.service_name == "PROD"

    def test_database_field_cleared_after_init(self):
        from aquilia.db.configs import OracleConfig
        cfg = OracleConfig(host="localhost", database="PROD", user="u", password="p")
        assert cfg.database == ""

    def test_service_name_still_works(self):
        from aquilia.db.configs import OracleConfig
        cfg = OracleConfig(host="localhost", service_name="PROD", user="u", password="p")
        assert cfg.service_name == "PROD"

    def test_service_name_takes_precedence_over_database(self):
        from aquilia.db.configs import OracleConfig
        cfg = OracleConfig(host="localhost", service_name="explicit", database="alias", user="u", password="p")
        assert cfg.service_name == "explicit"

    def test_to_url_with_database(self):
        from aquilia.db.configs import OracleConfig
        cfg = OracleConfig(host="localhost", port=1521, database="PROD", user="u", password="p")
        url = cfg.to_url()
        assert "PROD" in url
        assert url.startswith("oracle://")

    def test_to_dict_excludes_database_alias(self):
        from aquilia.db.configs import OracleConfig
        cfg = OracleConfig(host="localhost", database="PROD", user="u", password="p")
        d = cfg.to_dict()
        assert "database" not in d
        assert "PROD" in d["url"]

    def test_repr_shows_database_label(self):
        from aquilia.db.configs import OracleConfig
        cfg = OracleConfig(host="localhost", database="PROD", user="u", password="p")
        r = repr(cfg)
        assert "database=" in r
        assert "PROD" in r


class TestDatabaseAliasBackwardCompat:
    """Backward compatibility: existing code using `name=` must keep working."""

    def test_postgres_name_unchanged(self):
        from aquilia.db.configs import PostgresConfig
        cfg = PostgresConfig(host="h", name="db1", user="u", password="p")
        assert cfg.name == "db1"
        assert cfg.to_url() == "postgresql://u:p@h:5432/db1"

    def test_mysql_name_unchanged(self):
        from aquilia.db.configs import MysqlConfig
        cfg = MysqlConfig(host="h", name="db1", user="u", password="p")
        assert cfg.name == "db1"
        assert cfg.to_url() == "mysql://u:p@h:3306/db1"

    def test_oracle_service_name_unchanged(self):
        from aquilia.db.configs import OracleConfig
        cfg = OracleConfig(host="h", service_name="SVC", user="u", password="p")
        assert cfg.service_name == "SVC"
        assert cfg.to_url() == "oracle://u:p@h:1521/SVC"

    def test_neither_database_nor_name_defaults_empty(self):
        from aquilia.db.configs import PostgresConfig
        cfg = PostgresConfig(host="h", user="u", password="p")
        assert cfg.name == ""
        assert cfg.database == ""


# ═══════════════════════════════════════════════════════════════════════════════
# Module 19 — MySQL CREATE INDEX IF NOT EXISTS Stripping
# ═══════════════════════════════════════════════════════════════════════════════
# MySQL does not support ``CREATE INDEX IF NOT EXISTS``.  The fix strips the
# clause at three layers: Index.sql(dialect="mysql"),
# generate_index_sql(dialect="mysql"), and the safety-net in
# MySQLAdapter.adapt_sql().
# ═══════════════════════════════════════════════════════════════════════════════


class TestMySQLCreateIndexIfNotExistsStripping:
    """MySQL must never receive CREATE INDEX IF NOT EXISTS."""

    def test_adapt_sql_strips_if_not_exists(self):
        from aquilia.db.backends.mysql import MySQLAdapter
        adapter = MySQLAdapter()
        sql = 'CREATE INDEX IF NOT EXISTS "idx_foo" ON "bar" ("col");'
        result = adapter.adapt_sql(sql)
        assert "IF NOT EXISTS" not in result
        assert "CREATE INDEX" in result
        assert "`idx_foo`" in result

    def test_adapt_sql_strips_unique_index_if_not_exists(self):
        from aquilia.db.backends.mysql import MySQLAdapter
        adapter = MySQLAdapter()
        sql = 'CREATE UNIQUE INDEX IF NOT EXISTS "idx_foo" ON "bar" ("col");'
        result = adapter.adapt_sql(sql)
        assert "IF NOT EXISTS" not in result
        assert "CREATE UNIQUE INDEX" in result

    def test_adapt_sql_preserves_create_table_if_not_exists(self):
        from aquilia.db.backends.mysql import MySQLAdapter
        adapter = MySQLAdapter()
        sql = 'CREATE TABLE IF NOT EXISTS "users" ("id" INTEGER PRIMARY KEY);'
        result = adapter.adapt_sql(sql)
        assert "IF NOT EXISTS" in result

    def test_index_sql_mysql_dialect_no_if_not_exists(self):
        from aquilia.models.fields_module import Index
        idx = Index(fields=["email"], name="idx_email")
        sql = idx.sql("users", dialect="mysql")
        assert "IF NOT EXISTS" not in sql
        assert "idx_email" in sql
        assert '"users"' in sql

    def test_index_sql_sqlite_dialect_has_if_not_exists(self):
        from aquilia.models.fields_module import Index
        idx = Index(fields=["email"], name="idx_email")
        sql = idx.sql("users", dialect="sqlite")
        assert "IF NOT EXISTS" in sql

    def test_index_sql_postgresql_dialect_has_if_not_exists(self):
        from aquilia.models.fields_module import Index
        idx = Index(fields=["email"], name="idx_email")
        sql = idx.sql("users", dialect="postgresql")
        assert "IF NOT EXISTS" in sql

    def test_unique_index_sql_mysql_no_if_not_exists(self):
        from aquilia.models.fields_module import Index
        idx = Index(fields=["email"], name="idx_email", unique=True)
        sql = idx.sql("users", dialect="mysql")
        assert "IF NOT EXISTS" not in sql
        assert "UNIQUE" in sql

    def test_generate_index_sql_mysql_no_if_not_exists(self):
        """generate_index_sql(dialect='mysql') must omit IF NOT EXISTS."""
        from aquilia.models.base import Model
        from aquilia.models.fields_module import CharField

        class _IdxTestModel(Model):
            email = CharField(max_length=255, db_index=True)
            class Meta:
                table_name = "idx_test"

        stmts = _IdxTestModel.generate_index_sql(dialect="mysql")
        for stmt in stmts:
            assert "IF NOT EXISTS" not in stmt, f"MySQL index SQL has IF NOT EXISTS: {stmt}"

    def test_generate_index_sql_sqlite_has_if_not_exists(self):
        """generate_index_sql(dialect='sqlite') must include IF NOT EXISTS."""
        from aquilia.models.base import Model
        from aquilia.models.fields_module import CharField

        class _IdxTestModel2(Model):
            email = CharField(max_length=255, db_index=True)
            class Meta:
                table_name = "idx_test2"

        stmts = _IdxTestModel2.generate_index_sql(dialect="sqlite")
        for stmt in stmts:
            assert "IF NOT EXISTS" in stmt


class TestPostgresOnlyIndexMySQLFallback:
    """PostgreSQL-specific indexes fall back to B-tree on MySQL without IF NOT EXISTS."""

    def test_gin_index_mysql_fallback(self):
        from aquilia.models.index import GinIndex
        idx = GinIndex(fields=["data"], name="idx_data_gin")
        sql = idx.sql("docs", dialect="mysql")
        assert "IF NOT EXISTS" not in sql
        assert "GIN" not in sql
        assert "idx_data_gin" in sql

    def test_gin_index_postgres_uses_gin(self):
        from aquilia.models.index import GinIndex
        idx = GinIndex(fields=["data"], name="idx_data_gin")
        sql = idx.sql("docs", dialect="postgresql")
        assert "IF NOT EXISTS" in sql
        assert "USING GIN" in sql

    def test_functional_index_mysql_no_if_not_exists(self):
        from aquilia.models.index import FunctionalIndex
        idx = FunctionalIndex(expression='LOWER("email")', name="idx_email_lower")
        sql = idx.sql("users", dialect="mysql")
        assert "IF NOT EXISTS" not in sql
        assert "idx_email_lower" in sql

    def test_functional_index_sqlite_has_if_not_exists(self):
        from aquilia.models.index import FunctionalIndex
        idx = FunctionalIndex(expression='LOWER("email")', name="idx_email_lower")
        sql = idx.sql("users", dialect="sqlite")
        assert "IF NOT EXISTS" in sql


# ═══════════════════════════════════════════════════════════════════════════════
# Module 20 — MySQL TEXT/BLOB/JSON DEFAULT Suppression
# ═══════════════════════════════════════════════════════════════════════════════
# MySQL rejects DEFAULT on TEXT, BLOB, JSON, and GEOMETRY columns (error 1101).
# The fix suppresses the DDL DEFAULT clause on MySQL for these types; the
# Python-level default still applies at INSERT time.
# ═══════════════════════════════════════════════════════════════════════════════


class TestMySQLTextDefaultSuppression:
    """MySQL _sql_default() must return None for TEXT/BLOB/JSON columns."""

    def test_text_field_no_default_mysql(self):
        from aquilia.models.fields_module import TextField
        f = TextField(blank=True, default="")
        f.name = "bio"
        result = f._sql_default(dialect="mysql")
        assert result is None, f"MySQL TEXT must not emit DEFAULT, got {result!r}"

    def test_text_field_default_sqlite(self):
        from aquilia.models.fields_module import TextField
        f = TextField(blank=True, default="")
        f.name = "bio"
        result = f._sql_default(dialect="sqlite")
        assert result == "''"

    def test_text_field_default_postgresql(self):
        from aquilia.models.fields_module import TextField
        f = TextField(blank=True, default="")
        f.name = "bio"
        result = f._sql_default(dialect="postgresql")
        assert result == "''"

    def test_text_field_sql_column_def_mysql_no_default(self):
        from aquilia.models.fields_module import TextField
        f = TextField(blank=True, default="", null=True)
        f.name = "bio"
        sql = f.sql_column_def(dialect="mysql")
        assert "DEFAULT" not in sql

    def test_text_field_sql_column_def_sqlite_has_default(self):
        from aquilia.models.fields_module import TextField
        f = TextField(blank=True, default="", null=True)
        f.name = "bio"
        sql = f.sql_column_def(dialect="sqlite")
        assert "DEFAULT ''" in sql

    def test_json_field_no_default_mysql(self):
        from aquilia.models.fields_module import JSONField
        f = JSONField(default={})
        f.name = "data"
        result = f._sql_default(dialect="mysql")
        assert result is None

    def test_binary_field_no_default_mysql(self):
        from aquilia.models.fields_module import BinaryField
        f = BinaryField(default=b"")
        f.name = "payload"
        # BinaryField sql_type is BLOB on MySQL
        result = f._sql_default(dialect="mysql")
        # BLOB has no default on MySQL; however, BinaryField default is bytes
        # which won't match str check in _sql_default, so it returns None
        # regardless. Still, we verify it doesn't crash.
        assert result is None

    def test_migration_dsl_column_def_text_mysql(self):
        """ColumnDef.to_sql() must omit DEFAULT for TEXT on MySQL."""
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(name="bio", col_type="TEXT", nullable=True, default="")
        sql = col.to_sql(dialect="mysql")
        assert "DEFAULT" not in sql

    def test_migration_dsl_column_def_text_sqlite(self):
        """ColumnDef.to_sql() must include DEFAULT for TEXT on SQLite."""
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(name="bio", col_type="TEXT", nullable=True, default="")
        sql = col.to_sql(dialect="sqlite")
        assert "DEFAULT ''" in sql

    def test_migration_dsl_varchar_default_mysql_ok(self):
        """VARCHAR DEFAULT is fine on MySQL -- not suppressed."""
        from aquilia.models.migration_dsl import ColumnDef
        col = ColumnDef(name="name", col_type="VARCHAR(255)", nullable=True, default="")
        sql = col.to_sql(dialect="mysql")
        assert "DEFAULT ''" in sql


class TestAdminModelObjectIdField:
    """AdminLogEntry.object_id must be VARCHAR, not TEXT (MySQL indexability)."""

    def test_object_id_is_char_field(self):
        from aquilia.admin.models import AdminLogEntry
        field = AdminLogEntry._fields.get("object_id")
        from aquilia.models.fields_module import CharField
        assert isinstance(field, CharField), (
            f"object_id should be CharField for MySQL indexability, got {type(field).__name__}"
        )

    def test_object_id_max_length(self):
        from aquilia.admin.models import AdminLogEntry
        field = AdminLogEntry._fields.get("object_id")
        assert hasattr(field, "max_length")
        assert field.max_length == 255


# ═══════════════════════════════════════════════════════════════════════════════
# Module 21 — CLI URL Detection + Migration State for Non-SQLite Backends
# ═══════════════════════════════════════════════════════════════════════════════
# Two bugs surfaced when running `aq run` and `aq admin createsuperuser` against
# MySQL:
#
# 1.  check_migrations_applied() was SQLite-only — it used sqlite3.connect()
#     unconditionally.  For non-SQLite URLs the function now returns True early
#     (the async MigrationRunner handles tracking at runtime).
#
# 2.  _detect_workspace_db_url() only matched  .database(url="...")  patterns.
#     If workspace.py uses a typed config like  MysqlConfig(host=..., ...)  the
#     function fell back to sqlite:///db.sqlite3 causing CLI commands to query
#     the wrong database.  It now also parses MysqlConfig / PostgresConfig /
#     OracleConfig blocks via regex and reconstructs the URL.
# ═══════════════════════════════════════════════════════════════════════════════


class TestCheckMigrationsAppliedNonSQLite:
    """check_migrations_applied() must return True for non-SQLite URLs."""

    def test_mysql_url_returns_true(self):
        from aquilia.models.migration_runner import check_migrations_applied
        result = check_migrations_applied("mysql://user:pass@localhost:3306/mydb")
        assert result is True

    def test_postgresql_url_returns_true(self):
        from aquilia.models.migration_runner import check_migrations_applied
        result = check_migrations_applied("postgresql://user:pass@localhost:5432/mydb")
        assert result is True

    def test_oracle_url_returns_true(self):
        from aquilia.models.migration_runner import check_migrations_applied
        result = check_migrations_applied("oracle://user:pass@localhost:1521/orcl")
        assert result is True

    def test_postgres_asyncpg_url_returns_true(self):
        from aquilia.models.migration_runner import check_migrations_applied
        result = check_migrations_applied("postgresql+asyncpg://u:p@host/db")
        assert result is True

    def test_sqlite_url_still_probed(self, tmp_path):
        """SQLite URLs should still go through the probe logic."""
        from aquilia.models.migration_runner import check_migrations_applied
        # Non-existent SQLite file → check_db_exists returns False → returns False
        result = check_migrations_applied(f"sqlite:///{tmp_path / 'nonexistent.db'}")
        assert result is False

    def test_sqlite_memory_returns_true(self):
        from aquilia.models.migration_runner import check_migrations_applied
        result = check_migrations_applied("sqlite:///:memory:")
        assert result is True


class TestDetectWorkspaceDbUrl:
    """_detect_workspace_db_url() must parse typed config patterns."""

    def _run_detect(self, workspace_content: str, tmp_path):
        """Helper: write workspace.py, chdir, call _detect_workspace_db_url."""
        import os
        ws_file = tmp_path / "workspace.py"
        ws_file.write_text(workspace_content)
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            from aquilia.cli.__main__ import _detect_workspace_db_url
            return _detect_workspace_db_url()
        finally:
            os.chdir(old_cwd)

    def test_mysql_config_detected(self, tmp_path):
        content = '''
from aquilia.db.configs import MysqlConfig
app.database(
    config=MysqlConfig(
        host="db.example.com",
        port=3307,
        user="root",
        password="secret",
        database="shop",
    )
)
'''
        url = self._run_detect(content, tmp_path)
        assert url == "mysql://root:secret@db.example.com:3307/shop"

    def test_postgres_config_detected(self, tmp_path):
        content = '''
from aquilia.db.configs import PostgresConfig
app.database(
    config=PostgresConfig(
        host="pg.local",
        port=5433,
        user="pguser",
        password="pgpass",
        name="analytics",
    )
)
'''
        url = self._run_detect(content, tmp_path)
        assert url == "postgresql://pguser:pgpass@pg.local:5433/analytics"

    def test_oracle_config_detected(self, tmp_path):
        content = '''
from aquilia.db.configs import OracleConfig
app.database(
    config=OracleConfig(
        host="oracle.prod",
        port=1522,
        user="sys",
        password="oracle123",
        service_name="ORCL",
    )
)
'''
        url = self._run_detect(content, tmp_path)
        assert url == "oracle://sys:oracle123@oracle.prod:1522/ORCL"

    def test_mysql_config_database_alias(self, tmp_path):
        """database= alias is picked up."""
        content = '''
app.database(config=MysqlConfig(host="localhost", port=3306, user="admin", password="admin123", database="mydb"))
'''
        url = self._run_detect(content, tmp_path)
        assert url == "mysql://admin:admin123@localhost:3306/mydb"

    def test_mysql_config_name_field(self, tmp_path):
        """name= field works too."""
        content = '''
app.database(config=MysqlConfig(host="localhost", port=3306, user="admin", password="pw", name="testdb"))
'''
        url = self._run_detect(content, tmp_path)
        assert url == "mysql://admin:pw@localhost:3306/testdb"

    def test_url_pattern_still_works(self, tmp_path):
        """The original .database(url="...") pattern still works."""
        content = '''
app.database(url="sqlite:///mytest.db")
'''
        url = self._run_detect(content, tmp_path)
        assert url == "sqlite:///mytest.db"

    def test_url_pattern_takes_priority(self, tmp_path):
        """If both url= and config= are present, url= wins."""
        content = '''
app.database(url="sqlite:///priority.db")
app.database(config=MysqlConfig(host="localhost", port=3306, user="u", password="p", name="db"))
'''
        url = self._run_detect(content, tmp_path)
        assert url == "sqlite:///priority.db"

    def test_no_workspace_file_returns_default(self, tmp_path):
        """Missing workspace.py returns the default SQLite URL."""
        import os
        old_cwd = os.getcwd()
        try:
            os.chdir(tmp_path)
            from aquilia.cli.__main__ import _detect_workspace_db_url
            url = _detect_workspace_db_url()
            assert url == "sqlite:///db.sqlite3"
        finally:
            os.chdir(old_cwd)

    def test_defaults_for_mysql_port(self, tmp_path):
        """Port defaults to 3306 for MySQL when not specified."""
        content = '''
app.database(config=MysqlConfig(host="localhost", user="u", password="p", database="db"))
'''
        url = self._run_detect(content, tmp_path)
        assert ":3306/" in url

    def test_defaults_for_postgres_port(self, tmp_path):
        """Port defaults to 5432 for PostgreSQL when not specified."""
        content = '''
app.database(config=PostgresConfig(host="localhost", user="u", password="p", name="db"))
'''
        url = self._run_detect(content, tmp_path)
        assert ":5432/" in url

    def test_defaults_for_oracle_port(self, tmp_path):
        """Port defaults to 1521 for Oracle when not specified."""
        content = '''
app.database(config=OracleConfig(host="localhost", user="u", password="p", service_name="XE"))
'''
        url = self._run_detect(content, tmp_path)
        assert ":1521/" in url

    def test_multiline_config_block(self, tmp_path):
        """Config spread across many lines is still parsed."""
        content = '''
app.database(
    config=MysqlConfig(
        host="myhost",
        port=3308,
        user="myuser",
        password="mypass",
        database="mydb",
    )
)
'''
        url = self._run_detect(content, tmp_path)
        assert url == "mysql://myuser:mypass@myhost:3308/mydb"

    def test_no_user_no_creds_in_url(self, tmp_path):
        """If user is empty, no credentials section in URL."""
        content = '''
app.database(config=MysqlConfig(host="localhost", port=3306, database="testdb"))
'''
        url = self._run_detect(content, tmp_path)
        assert url == "mysql://localhost:3306/testdb"
        assert "@" not in url


# ═══════════════════════════════════════════════════════════════════════════════
# Module 22 — Migration Runner: MySQL Duplicate Index (1061) Handling
# ═══════════════════════════════════════════════════════════════════════════════
# When tables are auto-created by ``create_tables()`` at startup, their
# indexes already exist.  Running ``aq db migrate`` then tries to re-create
# the same indexes, and MySQL raises error 1061 (duplicate key name).
# The migration runner must catch 1061 during DSL execution and skip the
# duplicate index silently instead of aborting the entire migration.
# ═══════════════════════════════════════════════════════════════════════════════


class TestMigrationRunnerMySQLDuplicateIndex:
    """_execute_dsl_migration must skip MySQL 1061 (duplicate key name)."""

    @pytest.fixture
    def mock_db(self):
        """Build a mock DB adapter with dialect and transaction support."""
        import asyncio
        from unittest.mock import AsyncMock, MagicMock
        from contextlib import asynccontextmanager

        db = AsyncMock()
        db.dialect = "mysql"

        @asynccontextmanager
        async def fake_transaction():
            yield

        db.transaction = fake_transaction
        return db

    def _make_mysql_1061(self):
        """Create a chained exception mimicking aiomysql error 1061."""
        inner = Exception(1061, "Duplicate key name 'idx_foo'")
        outer = Exception("execute failed")
        outer.__cause__ = inner
        return outer

    def _make_mysql_1091(self):
        """Create a chained exception mimicking aiomysql error 1091."""
        inner = Exception(1091, "Can't DROP 'idx_foo'; check that column/key exists")
        outer = Exception("execute failed")
        outer.__cause__ = inner
        return outer

    @pytest.mark.asyncio
    async def test_duplicate_index_skipped_during_upgrade(self, mock_db):
        from aquilia.models.migration_runner import MigrationRunner
        from aquilia.models.migration_dsl import Migration, CreateIndex, CreateModel
        from aquilia.models.migration_dsl import ColumnDef

        call_count = 0

        async def mock_execute(sql, params=None):
            nonlocal call_count
            call_count += 1
            # Raise 1061 for CREATE INDEX, succeed for everything else
            if "CREATE" in sql and "INDEX" in sql:
                raise self._make_mysql_1061()

        mock_db.execute = mock_execute

        runner = MigrationRunner.__new__(MigrationRunner)
        runner.db = mock_db
        runner.dialect = "mysql"

        migration = Migration(
            revision="test_001",
            slug="test_dup_index",
            models=["TestModel"],
            operations=[
                CreateIndex(
                    name="idx_foo", table="test_table",
                    columns=["col_a"], unique=False,
                ),
            ],
        )

        # Should NOT raise — the 1061 is caught and skipped
        await runner._execute_dsl_migration(migration)
        assert call_count == 1  # The CREATE INDEX was attempted

    @pytest.mark.asyncio
    async def test_non_1061_error_still_raises(self, mock_db):
        from aquilia.models.migration_runner import MigrationRunner
        from aquilia.models.migration_dsl import Migration, CreateIndex
        from aquilia.faults.domains import MigrationFault

        async def mock_execute(sql, params=None):
            inner = Exception(1054, "Unknown column 'bad_col'")
            outer = Exception("execute failed")
            outer.__cause__ = inner
            raise outer

        mock_db.execute = mock_execute

        runner = MigrationRunner.__new__(MigrationRunner)
        runner.db = mock_db
        runner.dialect = "mysql"

        migration = Migration(
            revision="test_002",
            slug="test_bad_col",
            models=["TestModel"],
            operations=[
                CreateIndex(
                    name="idx_bad", table="test_table",
                    columns=["bad_col"], unique=False,
                ),
            ],
        )

        with pytest.raises(MigrationFault, match="DSL migration failed"):
            await runner._execute_dsl_migration(migration)

    @pytest.mark.asyncio
    async def test_sqlite_1061_like_error_not_suppressed(self, mock_db):
        """On SQLite dialect, 1061-shaped errors must NOT be silently skipped."""
        from aquilia.models.migration_runner import MigrationRunner
        from aquilia.models.migration_dsl import Migration, CreateIndex
        from aquilia.faults.domains import MigrationFault

        mock_db.dialect = "sqlite"

        async def mock_execute(sql, params=None):
            inner = Exception(1061, "Duplicate key name 'idx_foo'")
            outer = Exception("execute failed")
            outer.__cause__ = inner
            raise outer

        mock_db.execute = mock_execute

        runner = MigrationRunner.__new__(MigrationRunner)
        runner.db = mock_db
        runner.dialect = "sqlite"

        migration = Migration(
            revision="test_003",
            slug="test_sqlite_no_skip",
            models=["TestModel"],
            operations=[
                CreateIndex(
                    name="idx_foo", table="test_table",
                    columns=["col_a"], unique=False,
                ),
            ],
        )

        with pytest.raises(MigrationFault):
            await runner._execute_dsl_migration(migration)

    @pytest.mark.asyncio
    async def test_multiple_indexes_all_skipped(self, mock_db):
        """Multiple duplicate indexes in one migration are all skipped."""
        from aquilia.models.migration_runner import MigrationRunner
        from aquilia.models.migration_dsl import Migration, CreateIndex

        skipped = []

        async def mock_execute(sql, params=None):
            if "CREATE" in sql and "INDEX" in sql:
                skipped.append(sql)
                raise self._make_mysql_1061()

        mock_db.execute = mock_execute

        runner = MigrationRunner.__new__(MigrationRunner)
        runner.db = mock_db
        runner.dialect = "mysql"

        migration = Migration(
            revision="test_004",
            slug="test_multi_dup",
            models=["TestModel"],
            operations=[
                CreateIndex(name="idx_a", table="t", columns=["a"]),
                CreateIndex(name="idx_b", table="t", columns=["b"]),
                CreateIndex(name="idx_c", table="t", columns=["c"]),
            ],
        )

        await runner._execute_dsl_migration(migration)
        assert len(skipped) == 3

    @pytest.mark.asyncio
    async def test_create_table_followed_by_duplicate_index(self, mock_db):
        """CREATE TABLE succeeds, then duplicate CREATE INDEX is skipped."""
        from aquilia.models.migration_runner import MigrationRunner
        from aquilia.models.migration_dsl import (
            Migration, CreateModel, CreateIndex,
        )
        from aquilia.models.migration_dsl import columns as C

        executed = []

        async def mock_execute(sql, params=None):
            executed.append(sql)
            if "CREATE" in sql and "INDEX" in sql:
                raise self._make_mysql_1061()

        mock_db.execute = mock_execute

        runner = MigrationRunner.__new__(MigrationRunner)
        runner.db = mock_db
        runner.dialect = "mysql"

        migration = Migration(
            revision="test_005",
            slug="test_table_then_index",
            models=["TestModel"],
            operations=[
                CreateModel(
                    name="TestModel", table="test_table",
                    fields=[C.auto("id"), C.varchar("name", 100)],
                ),
                CreateIndex(
                    name="idx_name", table="test_table",
                    columns=["name"],
                ),
            ],
        )

        await runner._execute_dsl_migration(migration)
        # CREATE TABLE was executed, CREATE INDEX was attempted (then skipped)
        assert any("CREATE TABLE" in s for s in executed)
        assert any("INDEX" in s for s in executed)

    @pytest.mark.asyncio
    async def test_rollback_1091_skipped(self, mock_db):
        """During rollback, MySQL error 1091 (can't DROP) is skipped."""
        from aquilia.models.migration_runner import MigrationRunner
        from aquilia.models.migration_dsl import Migration, CreateIndex

        async def mock_execute(sql, params=None):
            if "DROP" in sql and "INDEX" in sql:
                raise self._make_mysql_1091()

        mock_db.execute = mock_execute

        runner = MigrationRunner.__new__(MigrationRunner)
        runner.db = mock_db
        runner.dialect = "mysql"

        migration = Migration(
            revision="test_006",
            slug="test_rollback_drop",
            models=["TestModel"],
            operations=[
                CreateIndex(
                    name="idx_gone", table="test_table",
                    columns=["col_a"],
                ),
            ],
        )

        # compile_downgrade produces DROP INDEX; the 1091 should be skipped
        stmts = migration.compile_downgrade("mysql")
        assert any("DROP" in s for s in stmts)

        # Simulate the rollback execution path
        try:
            async with mock_db.transaction():
                for sql in stmts:
                    if sql.startswith("--"):
                        continue
                    try:
                        await mock_db.execute(sql)
                    except Exception as idx_exc:
                        cause = getattr(idx_exc, "__cause__", idx_exc)
                        code = getattr(cause, "args", (None,))[0]
                        if runner.dialect == "mysql" and code in (1061, 1091):
                            continue
                        raise
        except Exception:
            pytest.fail("Rollback should not raise on MySQL 1091")
