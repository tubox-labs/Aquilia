import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { BookOpen, Database, Layers, Terminal } from 'lucide-react'

export function SqliteAPI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <BookOpen className="w-4 h-4 animate-pulse" />
          SQLite / API Reference
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          SQLite API Reference
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Detailed interface specifications for SQLite pools, connections, row objects, prepared statement caches, and query methods.
        </p>
      </div>

      {/* Table of Contents */}
      <section className="mb-16">
        <div className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 p-6 backdrop-blur-sm shadow-xl">
          <div className="absolute top-0 bottom-0 left-0 w-1 bg-gradient-to-b from-aquilia-500 to-transparent opacity-50" />
          <h3 className={`font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Table of Contents</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            {[
              { name: 'create_pool() Function', hash: 'create-pool' },
              { name: 'ConnectionPool Class', hash: 'connection-pool' },
              { name: 'AsyncConnection Class', hash: 'async-connection' },
              { name: 'Row Object', hash: 'row-object' },
              { name: 'SqlitePoolConfig Class', hash: 'pool-config' },
              { name: 'SQLite Error Hierarchy', hash: 'sqlite-errors' },
            ].map((item, i) => (
              <a key={i} href={`#${item.hash}`} className="text-aquilia-500 hover:text-aquilia-400 font-medium hover:underline flex items-center gap-1.5">
                <span className="text-aquilia-500/50">•</span> {item.name}
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* create_pool() */}
      <section id="create-pool" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Database className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="sqlite.create_pool">create_pool()</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Initialize a connection pool for the SQLite database.
        </p>
        <CodeBlock language="python">{`from aquilia.sqlite import create_pool, SqlitePoolConfig

async def create_pool(
    config: SqlitePoolConfig | str,
    metrics: SqliteMetrics | None = None,
) -> ConnectionPool`}</CodeBlock>
      </section>

      {/* ConnectionPool */}
      <section id="connection-pool" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="sqlite.ConnectionPool">ConnectionPool</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Manages reader and writer connections, exposing shortcuts for query execution.
        </p>
        <CodeBlock language="python">{`class ConnectionPool:
    def acquire(self, *, readonly: bool = False) -> _AcquireContext:
        """Acquire a connection from the pool.
        
        Returns a context manager yielding AsyncConnection.
        """

    async def close(self) -> None:
        """Close all connections inside the pool."""

    async def execute(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
    ) -> AsyncCursor:
        """Helper to acquire writer connection and execute SQL statement."""

    async def execute_many(
        self,
        sql: str,
        params_seq: Sequence[Sequence[Any]],
    ) -> int:
        """Helper to execute SQL across multiple parameter sets. Returns affected rowcount."""

    async def fetch_all(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
    ) -> list[Row]:
        """Helper to acquire reader connection and fetch all rows."""

    async def fetch_one(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
    ) -> Row | None:
        """Helper to acquire reader connection and fetch a single row."""

    async def fetch_val(
        self,
        sql: str,
        params: Sequence[Any] | None = None,
        *,
        column: int = 0,
    ) -> Any:
        """Helper to fetch a single scalar value from the first row."""`}</CodeBlock>
      </section>

      {/* AsyncConnection */}
      <section id="async-connection" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="sqlite.AsyncConnection">AsyncConnection</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Wraps a single connection, mapping query and transaction calls to thread pool execution.
        </p>
        <CodeBlock language="python">{`class AsyncConnection:
    @property
    def readonly(self) -> bool:
        """Returns True if this is a read-only reader connection."""

    @property
    def in_transaction(self) -> bool:
        """Returns True if a transaction is currently active."""

    async def execute(self, sql: str, params: Sequence[Any] | None = None) -> AsyncCursor:
        """Execute a single SQL statement."""

    async def execute_many(self, sql: str, params_seq: Sequence[Sequence[Any]]) -> int:
        """Execute SQL with multiple parameter sets."""

    async def fetch_all(self, sql: str, params: Sequence[Any] | None = None) -> list[Row]:
        """Fetch all rows."""

    async def fetch_one(self, sql: str, params: Sequence[Any] | None = None) -> Row | None:
        """Fetch a single row or None."""

    async def fetch_val(self, sql: str, params: Sequence[Any] | None = None, *, column: int = 0) -> Any:
        """Fetch a single scalar value."""

    def transaction(self, *, mode: str = "DEFERRED") -> TransactionContext:
        """Returns a transaction context manager (DEFERRED, IMMEDIATE, EXCLUSIVE)."""

    def savepoint_ctx(self, name: str) -> SavepointContext:
        """Returns a savepoint context manager."""

    async def table_exists(self, name: str) -> bool:
        """Returns True if the table exists."""

    async def get_tables(self) -> list[str]:
        """List all user-defined table names."""

    async def backup(self, target: str | AsyncConnection, *, pages: int = -1) -> None:
        """Perform an online backup to another file or connection."""`}</CodeBlock>
      </section>

      {/* Row */}
      <section id="row-object" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="sqlite.Row">Row</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          High-performance, dict-like object wrapping SQLite rows.
        </p>
        <CodeBlock language="python">{`class Row:
    def keys(self) -> list[str]:
        """Get list of column names."""

    def values(self) -> list[Any]:
        """Get list of column values."""

    def items(self) -> list[tuple[str, Any]]:
        """Get list of (column, value) tuples."""

    def __getitem__(self, key: int | str) -> Any:
        """Get column value by integer index or name string."""

    def __getattr__(self, name: str) -> Any:
        """Access column value via attribute name."""`}</CodeBlock>
      </section>

      {/* SqlitePoolConfig */}
      <section id="pool-config" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="sqlite.SqlitePoolConfig">SqlitePoolConfig</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Configuration dataclass for native SQLite connection pools.
        </p>
        <CodeBlock language="python">{`@dataclass
class SqlitePoolConfig:
    path: str = "db.sqlite3"
    journal_mode: str = "WAL"
    foreign_keys: bool = True
    busy_timeout: int = 5000            # milliseconds
    synchronous: str = "NORMAL"
    cache_size: int = -8000             # negative = KiB
    mmap_size: int = 268435456          # bytes (256 MB)
    temp_store: str = "MEMORY"
    pool_size: int = 5                  # reader connections count
    pool_min_size: int = 2
    statement_cache_size: int = 256
    query_timeout: float = 30.0         # seconds
    echo: bool = False
    auto_commit: bool = True`}</CodeBlock>
      </section>

      {/* Errors */}
      <section id="sqlite-errors" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Terminal className="w-5 h-5 text-aquilia-500" />
          SQLite Error Hierarchy
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Custom exceptions raised by the native wrapper.
        </p>

        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500 w-52">Exception Class</th>
                <th className="text-left py-4 px-6 font-semibold">Base Class</th>
                <th className="text-left py-4 px-6">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['SqliteError', 'Exception', 'Base class for all module exceptions.'],
                ['SqliteConnectionError', 'SqliteError', 'Raised when connecting or closing fails.'],
                ['PoolExhaustedError', 'SqliteError', 'Raised when a connection acquisition request times out.'],
                ['SqliteQueryError', 'SqliteError', 'Raised on standard SQL syntax or runtime failures.'],
                ['SqliteIntegrityError', 'SqliteQueryError', 'Constraint violation (UNIQUE, FOREIGN KEY, NOT NULL).'],
                ['SqliteSchemaError', 'SqliteError', 'Raised when columns or tables do not exist.'],
                ['SqliteTimeoutError', 'SqliteError', 'Raised when database lock waits time out.'],
                ['SqliteSecurityError', 'SqliteError', 'Raised when queries attempt to escape sandbox limits.'],
              ].map(([exc, base, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-xs font-semibold text-aquilia-400">{exc}</td>
                  <td className="py-3.5 px-6 font-mono text-xs text-aquilia-500">{base}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
