import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { BookOpen, AlertTriangle } from 'lucide-react'

export function SqliteAPI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <BookOpen className="w-4 h-4" />
          SQLite › API Reference
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            API Reference
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Complete reference for the SQLite API.
        </p>
      </div>

      {/* create_pool */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          create_pool()
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Create a connection pool.
        </p>

        <CodeBlock language="python">{`async def create_pool(
    database: str,                    # Path to database file or ":memory:"
    max_readers: int = 10,            # Max concurrent readers
    timeout: float = 30.0,            # Connection timeout (seconds)
    check_same_thread: bool = False,  # SQLite thread check
    journal_mode: str = "WAL",        # Journal mode
    synchronous: str = "NORMAL",      # Synchronous mode
    cache_size: int = -64000,         # Cache size (-N = KB, N = pages)
    mmap_size: int = 0,               # Memory-mapped I/O (0 = off)
    statement_cache_size: int = 128,  # Statement cache size
    busy_timeout: int = 5000,         # Busy timeout (milliseconds)
) -> ConnectionPool:`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`from aquilia.sqlite import create_pool

pool = await create_pool(
    database="app.db",
    max_readers=20,
    journal_mode="WAL",
)`}</CodeBlock>
      </section>

      {/* ConnectionPool */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          ConnectionPool
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Manages a pool of reader and writer connections.
        </p>

        <CodeBlock language="python">{`class ConnectionPool:
    async def acquire(self) -> AsyncConnection:
        """Acquire a connection from the pool."""
    
    async def close(self) -> None:
        """Close all connections in the pool."""
    
    async def execute(
        self, sql: str, params: tuple = (), write: bool = False
    ) -> AsyncCursor:
        """Execute SQL directly on the pool."""
    
    async def fetchone(self, sql: str, params: tuple = ()) -> Row | None:
        """Fetch a single row."""
    
    async def fetchall(self, sql: str, params: tuple = ()) -> list[Row]:
        """Fetch all rows."""
    
    async def fetchmany(
        self, sql: str, params: tuple = (), size: int = 100
    ) -> list[Row]:
        """Fetch multiple rows."""`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`# Acquire connection
async with pool.acquire() as conn:
    await conn.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
    await conn.commit()

# Or use pool methods directly
rows = await pool.fetchall("SELECT * FROM users")

# Close pool
await pool.close()`}</CodeBlock>
      </section>

      {/* AsyncConnection */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          AsyncConnection
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Async wrapper around a SQLite connection.
        </p>

        <CodeBlock language="python">{`class AsyncConnection:
    async def execute(
        self, sql: str, params: tuple | dict = ()
    ) -> AsyncCursor:
        """Execute SQL statement."""
    
    async def executemany(
        self, sql: str, params: list[tuple] | list[dict]
    ) -> AsyncCursor:
        """Execute SQL with multiple parameter sets."""
    
    async def fetchone(self, sql: str, params: tuple = ()) -> Row | None:
        """Fetch a single row."""
    
    async def fetchall(self, sql: str, params: tuple = ()) -> list[Row]:
        """Fetch all rows."""
    
    async def fetchmany(
        self, sql: str, params: tuple = (), size: int = 100
    ) -> list[Row]:
        """Fetch multiple rows."""
    
    async def commit(self) -> None:
        """Commit the current transaction."""
    
    async def rollback(self) -> None:
        """Roll back the current transaction."""
    
    def transaction(self) -> TransactionContext:
        """Start a transaction context."""
    
    def savepoint(self, name: str) -> SavepointContext:
        """Create a savepoint context."""
    
    async def close(self) -> None:
        """Close the connection."""`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`async with pool.acquire() as conn:
    # Named parameters
    await conn.execute(
        "INSERT INTO users (name, email) VALUES (:name, :email)",
        {"name": "Bob", "email": "bob@example.com"}
    )
    
    # Positional parameters
    await conn.execute(
        "UPDATE users SET name = ? WHERE id = ?",
        ("Robert", 1)
    )
    
    # Batch insert
    await conn.executemany(
        "INSERT INTO users (name, email) VALUES (?, ?)",
        [("Alice", "alice@example.com"), ("Bob", "bob@example.com")]
    )
    
    await conn.commit()`}</CodeBlock>
      </section>

      {/* Row */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Row
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Dict-like row object with multiple access patterns.
        </p>

        <CodeBlock language="python">{`class Row:
    def __getitem__(self, key: int | str) -> Any:
        """Get value by index or column name."""
    
    def __getattr__(self, name: str) -> Any:
        """Get value by attribute access."""
    
    def __iter__(self) -> Iterator[Any]:
        """Iterate over values."""
    
    def keys(self) -> list[str]:
        """Get column names."""
    
    def values(self) -> list[Any]:
        """Get column values."""
    
    def items(self) -> list[tuple[str, Any]]:
        """Get (name, value) pairs."""`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Example</h4>
        <CodeBlock language="python">{`row = await conn.fetchone("SELECT id, name, email FROM users WHERE id = 1")

# Attribute access
print(row.name)        # "Alice"

# Dict access
print(row["email"])    # "alice@example.com"

# Index access
print(row[0])          # 1

# Dict conversion
user_dict = dict(row)  # {"id": 1, "name": "Alice", "email": "alice@example.com"}

# Keys and values
print(row.keys())      # ["id", "name", "email"]
print(row.values())    # [1, "Alice", "alice@example.com"]`}</CodeBlock>
      </section>

      {/* TransactionContext */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          TransactionContext
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Async context manager for transactions.
        </p>

        <CodeBlock language="python">{`async with conn.transaction():
    await conn.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
    await conn.execute("INSERT INTO posts (user_id, title) VALUES (?, ?)", (1, "Post"))
    # Automatically commits on success
    # Automatically rolls back on exception`}</CodeBlock>
      </section>

      {/* SavepointContext */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          SavepointContext
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Async context manager for savepoints.
        </p>

        <CodeBlock language="python">{`async with conn.transaction():
    await conn.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
    
    async with conn.savepoint("sp1"):
        await conn.execute("INSERT INTO users (name) VALUES (?)", ("Bob",))
        raise Exception("Rollback Bob only")
    
    # Alice is committed, Bob is rolled back`}</CodeBlock>
      </section>

      {/* Errors */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <AlertTriangle className="inline w-6 h-6 mr-2 text-amber-500" />
          Errors
        </h2>

        <div className={`overflow-x-auto rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Exception</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
              <tr>
                <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>SqliteError</code></td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Base class for all SQLite errors</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>SqliteConnectionError</code></td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Cannot connect to database</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>PoolExhaustedError</code></td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>No available connections (timeout)</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>SqliteQueryError</code></td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>SQL syntax error</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>SqliteIntegrityError</code></td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Constraint violation (unique, foreign key, etc.)</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>SqliteSchemaError</code></td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Table or column does not exist</td>
              </tr>
              <tr>
                <td className={`px-4 py-3 ${isDark ? 'text-white' : 'text-gray-900'}`}><code>SqliteTimeoutError</code></td>
                <td className={`px-4 py-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>Database locked (SQLITE_BUSY)</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Error Handling Example</h4>
        <CodeBlock language="python">{`from aquilia.sqlite import (
    create_pool,
    SqliteIntegrityError,
    SqliteQueryError,
    PoolExhaustedError,
)

pool = await create_pool("app.db")

try:
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO users (name, email) VALUES (?, ?)",
            ("Alice", "alice@example.com")
        )
        await conn.commit()
except SqliteIntegrityError as e:
    print(f"Constraint violation: {e}")
except SqliteQueryError as e:
    print(f"SQL error: {e}")
except PoolExhaustedError:
    print("No connections available")`}</CodeBlock>
      </section>
    </div>
  )
}
