import { registerDocEntities } from '../../lib/docPreview/registry'

registerDocEntities([
  // ── AquiliaDatabase ──────────────────────────────────────────────────
  {
    id: 'db.aquilia_database',
    type: 'class',
    title: 'AquiliaDatabase',
    description:
      'Async database engine. Delegates all operations to a backend adapter (SQLite, PostgreSQL, MySQL, Oracle). Uses ? placeholders universally — the adapter translates to the backend native param style. Registered as a DI service with scope="app".',
    signature: 'class AquiliaDatabase:\n    def __init__(self, url: str | None = None, *, config: DatabaseConfig | None = None, **options)',
    language: 'python',
    parameters: [
      { name: 'url', type: 'str | None', optional: true, description: 'Database URL: sqlite:///path, postgresql://..., mysql://..., oracle://...' },
      { name: 'config', type: 'DatabaseConfig | None', optional: true, description: 'Typed config object. Takes precedence over url.' },
      { name: 'connect_retries', type: 'int', optional: true, default: '3', description: 'Number of connection attempts before raising.' },
      { name: 'connect_retry_delay', type: 'float', optional: true, default: '0.5', description: 'Seconds between retry attempts.' },
    ],
    example: {
      code: `from aquilia.db import AquiliaDatabase

# URL-based
db = AquiliaDatabase("postgresql://user:pass@localhost/mydb")
await db.connect()

# Typed config
from aquilia.db.configs import PostgresConfig
db = AquiliaDatabase(config=PostgresConfig(host="localhost", name="mydb", user="admin", password="s3cr3t"))
await db.connect()`,
      language: 'python',
    },
    related: [
      { label: 'configure_database()', id: 'db.configure_database' },
      { label: 'PostgresConfig', id: 'db.postgres_config' },
      { label: 'SqliteConfig', id: 'db.sqlite_config' },
    ],
    status: 'stable',
    version: 'v1.0+',
    docsHref: '/docs/database/engine',
    source: { file: 'aquilia/db/engine.py', line: 89 },
  },

  // ── Core methods ─────────────────────────────────────────────────────
  {
    id: 'db.execute',
    type: 'method',
    title: 'execute()',
    description: 'Execute a single SQL statement. Returns a cursor-like object with lastrowid and rowcount attributes.',
    signature: 'async def execute(self, sql: str, params: list | None = None, model: str = "") -> Any',
    language: 'python',
    parameters: [
      { name: 'sql', type: 'str', description: 'SQL with ? placeholders.' },
      { name: 'params', type: 'list | None', optional: true, description: 'Parameter values.' },
      { name: 'model', type: 'str', optional: true, description: 'Optional model name for query inspector.' },
    ],
    example: { code: `result = await db.execute("INSERT INTO logs (msg) VALUES (?)", ["hello"])\nprint(result.lastrowid)`, language: 'python' },
    related: [{ label: 'fetch_all()', id: 'db.fetch_all' }, { label: 'fetch_one()', id: 'db.fetch_one' }],
    status: 'stable',
    docsHref: '/docs/database/engine',
    source: { file: 'aquilia/db/engine.py', line: 454 },
  },

  {
    id: 'db.fetch_all',
    type: 'method',
    title: 'fetch_all()',
    description: 'Run a SELECT and return all rows as a list of dicts. Uses ? placeholders.',
    signature: 'async def fetch_all(self, sql: str, params: list | None = None, model: str = "") -> list[dict]',
    language: 'python',
    example: { code: `rows = await db.fetch_all("SELECT * FROM users WHERE active = ?", [True])`, language: 'python' },
    related: [{ label: 'fetch_one()', id: 'db.fetch_one' }, { label: 'fetch_val()', id: 'db.fetch_val' }],
    status: 'stable',
    docsHref: '/docs/database/engine',
    source: { file: 'aquilia/db/engine.py', line: 523 },
  },

  {
    id: 'db.fetch_one',
    type: 'method',
    title: 'fetch_one()',
    description: 'Run a SELECT and return the first row as a dict, or None if no rows match.',
    signature: 'async def fetch_one(self, sql: str, params: list | None = None, model: str = "") -> dict | None',
    language: 'python',
    example: { code: `row = await db.fetch_one("SELECT * FROM users WHERE id = ?", [42])`, language: 'python' },
    status: 'stable',
    docsHref: '/docs/database/engine',
    source: { file: 'aquilia/db/engine.py', line: 564 },
  },

  {
    id: 'db.fetch_val',
    type: 'method',
    title: 'fetch_val()',
    description: 'Run a SELECT and return the scalar value from the first row, first column. Returns None if no rows.',
    signature: 'async def fetch_val(self, sql: str, params: list | None = None, model: str = "") -> Any',
    language: 'python',
    example: { code: `count = await db.fetch_val("SELECT COUNT(*) FROM users WHERE active = ?", [True])`, language: 'python' },
    status: 'stable',
    docsHref: '/docs/database/engine',
    source: { file: 'aquilia/db/engine.py', line: 597 },
  },

  {
    id: 'db.execute_many',
    type: 'method',
    title: 'execute_many()',
    description: 'Execute the same SQL with multiple parameter sets. Efficient for bulk inserts.',
    signature: 'async def execute_many(self, sql: str, params_list: list[list]) -> None',
    language: 'python',
    example: {
      code: `await db.execute_many(
    "INSERT INTO tags (name) VALUES (?)",
    [["python"], ["async"], ["orm"]],
)`,
      language: 'python',
    },
    status: 'stable',
    docsHref: '/docs/database/engine',
    source: { file: 'aquilia/db/engine.py', line: 502 },
  },

  // ── Transaction methods ───────────────────────────────────────────────
  {
    id: 'db.transaction',
    type: 'method',
    title: 'transaction()',
    description: 'Async context manager for explicit transactions. Commits on clean exit, rolls back on exception.',
    signature: '@asynccontextmanager\nasync def transaction(self) -> AsyncIterator[None]',
    language: 'python',
    example: {
      code: `async with db.transaction():
    await db.execute("INSERT INTO orders ...")
    await db.execute("UPDATE inventory ...")
# commits if no exception`,
      language: 'python',
    },
    related: [{ label: 'savepoint()', id: 'db.savepoint' }, { label: 'atomic()', id: 'orm.atomic' }],
    status: 'stable',
    docsHref: '/docs/database/engine',
    source: { file: 'aquilia/db/engine.py', line: 290 },
  },

  {
    id: 'db.savepoint',
    type: 'method',
    title: 'savepoint()',
    description: 'Create a named savepoint within an active transaction. Name must be alphanumeric + underscore.',
    signature: 'async def savepoint(self, name: str) -> None',
    language: 'python',
    notes: [{ kind: 'warning', text: 'Must be called inside an active transaction (after begin()). Only alphanumeric + underscore chars are valid in name.' }],
    example: {
      code: `await db.begin()
await db.savepoint("before_risky")
try:
    await db.execute("UPDATE ...")
    await db.release_savepoint("before_risky")
except Exception:
    await db.rollback_to_savepoint("before_risky")
await db.commit()`,
      language: 'python',
    },
    status: 'stable',
    docsHref: '/docs/database/engine',
    source: { file: 'aquilia/db/engine.py', line: 310 },
  },

  // ── Introspection ─────────────────────────────────────────────────────
  {
    id: 'db.table_exists',
    type: 'method',
    title: 'table_exists()',
    description: 'Returns True if the named table exists in the current database.',
    signature: 'async def table_exists(self, table_name: str) -> bool',
    language: 'python',
    example: { code: `if not await db.table_exists("migrations"):\n    await db.execute("CREATE TABLE migrations ...")`, language: 'python' },
    status: 'stable',
    docsHref: '/docs/database/engine',
    source: { file: 'aquilia/db/engine.py', line: 632 },
  },

  {
    id: 'db.get_tables',
    type: 'method',
    title: 'get_tables()',
    description: 'Returns a list of all table names in the connected database.',
    signature: 'async def get_tables(self) -> list[str]',
    language: 'python',
    example: { code: `tables = await db.get_tables()\nprint(tables)  # ["users", "posts", "tags", ...]`, language: 'python' },
    status: 'stable',
    docsHref: '/docs/database/engine',
    source: { file: 'aquilia/db/engine.py', line: 637 },
  },

  {
    id: 'db.get_columns',
    type: 'method',
    title: 'get_columns()',
    description: 'Returns column metadata (ColumnInfo) for a table: name, type, nullable, default, primary_key.',
    signature: 'async def get_columns(self, table_name: str) -> list[ColumnInfo]',
    language: 'python',
    example: { code: `cols = await db.get_columns("users")\nfor col in cols:\n    print(col.name, col.type, col.primary_key)`, language: 'python' },
    status: 'stable',
    docsHref: '/docs/database/engine',
    source: { file: 'aquilia/db/engine.py', line: 642 },
  },

  // ── Module-level functions ────────────────────────────────────────────
  {
    id: 'db.configure_database',
    type: 'function',
    title: 'configure_database()',
    description: 'Configure and store a database instance under an alias. Accepts either a URL string or a typed DatabaseConfig. Alias "default" becomes the primary database.',
    signature: 'def configure_database(url: str | None = None, *, config: DatabaseConfig | None = None, alias: str = "default", **options) -> AquiliaDatabase',
    language: 'python',
    parameters: [
      { name: 'url', type: 'str | None', optional: true, description: 'Database URL (ignored when config provided).' },
      { name: 'config', type: 'DatabaseConfig | None', optional: true, description: 'Typed config object.' },
      { name: 'alias', type: 'str', optional: true, default: '"default"', description: 'Registry alias for multi-DB setups.' },
    ],
    example: {
      code: `from aquilia.db import configure_database
from aquilia.db.configs import PostgresConfig

db = configure_database(config=PostgresConfig(
    host="localhost", name="mydb", user="admin", password="secret"
))

# Multi-database:
configure_database(config=pg_config, alias="primary")
configure_database(config=sqlite_config, alias="cache")`,
      language: 'python',
    },
    related: [{ label: 'get_database()', id: 'db.get_database' }, { label: 'AquiliaDatabase', id: 'db.aquilia_database' }],
    status: 'stable',
    docsHref: '/docs/database/engine',
    source: { file: 'aquilia/db/engine.py', line: 716 },
  },

  {
    id: 'db.get_database',
    type: 'function',
    title: 'get_database()',
    description: 'Retrieve a configured database instance by alias. Pass None or "default" for the primary database.',
    signature: 'def get_database(alias: str | None = None) -> AquiliaDatabase',
    language: 'python',
    example: {
      code: `from aquilia.db import get_database

db = get_database()              # primary
cache_db = get_database("cache") # named alias`,
      language: 'python',
    },
    status: 'stable',
    docsHref: '/docs/database/engine',
    source: { file: 'aquilia/db/engine.py', line: 687 },
  },

  // ── Config classes ────────────────────────────────────────────────────
  {
    id: 'db.sqlite_config',
    type: 'config',
    title: 'SqliteConfig',
    description: 'Typed SQLite configuration dataclass. Supports file-based and :memory: databases, WAL mode, foreign key enforcement, and busy timeout.',
    signature: 'class SqliteConfig(DatabaseConfig):\n    path: str = "db.sqlite3"\n    journal_mode: str = "WAL"\n    foreign_keys: bool = True\n    busy_timeout: int = 5000',
    language: 'python',
    parameters: [
      { name: 'path', type: 'str', optional: true, default: '"db.sqlite3"', description: 'File path or ":memory:" for in-memory.' },
      { name: 'journal_mode', type: 'str', optional: true, default: '"WAL"', description: 'SQLite journal mode: WAL, DELETE, MEMORY, etc.' },
      { name: 'foreign_keys', type: 'bool', optional: true, default: 'True', description: 'Enable PRAGMA foreign_keys.' },
      { name: 'busy_timeout', type: 'int', optional: true, default: '5000', description: 'PRAGMA busy_timeout in milliseconds.' },
    ],
    example: {
      code: `from aquilia.db.configs import SqliteConfig

cfg = SqliteConfig(path="data/app.db", journal_mode="WAL")

# In-memory:
cfg = SqliteConfig(path=":memory:")`,
      language: 'python',
    },
    related: [{ label: 'PostgresConfig', id: 'db.postgres_config' }, { label: 'MysqlConfig', id: 'db.mysql_config' }],
    status: 'stable',
    docsHref: '/docs/database/configs',
    source: { file: 'aquilia/db/configs.py', line: 170 },
  },

  {
    id: 'db.postgres_config',
    type: 'config',
    title: 'PostgresConfig',
    description: 'Typed PostgreSQL configuration via asyncpg. Supports SSL, connection pooling, schema selection. "name" and "database" are interchangeable aliases.',
    signature: 'class PostgresConfig(DatabaseConfig):\n    host: str = "localhost"\n    port: int = 5432\n    name: str = ""\n    user: str = ""\n    password: str = ""\n    sslmode: str = "prefer"',
    language: 'python',
    parameters: [
      { name: 'host', type: 'str', optional: true, default: '"localhost"', description: 'Database server hostname.' },
      { name: 'port', type: 'int', optional: true, default: '5432', description: 'Server port.' },
      { name: 'name / database', type: 'str', description: 'Database name (both aliases work).' },
      { name: 'user', type: 'str', description: 'Database user.' },
      { name: 'password', type: 'str', description: 'Database password.' },
      { name: 'sslmode', type: 'str', optional: true, default: '"prefer"', description: 'SSL mode: disable, allow, prefer, require, verify-full.' },
      { name: 'pool_size', type: 'int', optional: true, default: '5', description: 'Connection pool size.' },
      { name: 'pool_max_size', type: 'int', optional: true, default: '10', description: 'Max connections in pool.' },
    ],
    example: {
      code: `from aquilia.db.configs import PostgresConfig

cfg = PostgresConfig(
    host="db.example.com",
    database="prod_db",
    user="app_user",
    password="s3cr3t",
    sslmode="require",
    pool_size=20,
    pool_max_size=50,
)

# From URL:
cfg = PostgresConfig.from_url("postgresql://admin:secret@localhost:5432/mydb")`,
      language: 'python',
    },
    related: [{ label: 'SqliteConfig', id: 'db.sqlite_config' }, { label: 'MysqlConfig', id: 'db.mysql_config' }],
    status: 'stable',
    docsHref: '/docs/database/configs',
    source: { file: 'aquilia/db/configs.py', line: 226 },
  },

  {
    id: 'db.mysql_config',
    type: 'config',
    title: 'MysqlConfig',
    description: 'Typed MySQL/MariaDB configuration via aiomysql. Supports charset, collation, and connection pooling.',
    signature: 'class MysqlConfig(DatabaseConfig):\n    host: str = "localhost"\n    port: int = 3306\n    name: str = ""\n    user: str = ""\n    password: str = ""\n    charset: str = "utf8mb4"',
    language: 'python',
    example: {
      code: `from aquilia.db.configs import MysqlConfig

cfg = MysqlConfig(
    host="mysql.example.com",
    database="prod_db",
    user="app_user",
    password="secret",
    charset="utf8mb4",
    pool_size=15,
)`,
      language: 'python',
    },
    related: [{ label: 'PostgresConfig', id: 'db.postgres_config' }, { label: 'OracleConfig', id: 'db.oracle_config' }],
    status: 'stable',
    docsHref: '/docs/database/configs',
    source: { file: 'aquilia/db/configs.py', line: 324 },
  },

  {
    id: 'db.oracle_config',
    type: 'config',
    title: 'OracleConfig',
    description: 'Typed Oracle configuration via python-oracledb (thin mode by default — no Oracle Client required). Supports service_name, SID, thick mode.',
    signature: 'class OracleConfig(DatabaseConfig):\n    host: str = "localhost"\n    port: int = 1521\n    service_name: str = "ORCL"\n    thick_mode: bool = False',
    language: 'python',
    example: {
      code: `from aquilia.db.configs import OracleConfig

cfg = OracleConfig(
    host="oracle.example.com",
    database="PROD_SERVICE",
    user="app_user",
    password="tiger",
)`,
      language: 'python',
    },
    status: 'stable',
    docsHref: '/docs/database/configs',
    source: { file: 'aquilia/db/configs.py', line: 414 },
  },
])
