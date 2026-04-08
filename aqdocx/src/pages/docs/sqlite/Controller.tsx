import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Code } from 'lucide-react'

export function SqliteController() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Code className="w-4 h-4" />
          SQLite › Controller Guide
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Controller Integration
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Using SQLite in Aquilia controllers.
        </p>
      </div>

      {/* Dependency Injection */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Dependency Injection
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Register the pool in the DI container.
        </p>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Setup in workspace</h4>
        <CodeBlock language="python">{`# workspace.py
from aquilia import Workspace, Module
from aquilia.sqlite import create_pool, ConnectionPool

workspace = Workspace(
    name="myapp",
    modules=[
        Module(name="api", path="modules/api"),
    ],
)

# Create pool on startup
async def setup_db():
    pool = await create_pool(
        database="app.db",
        max_readers=20,
        journal_mode="WAL",
    )
    return pool

# Register in DI container
pool = await setup_db()
workspace.container.register_singleton(ConnectionPool, lambda: pool)`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Inject in controller</h4>
        <CodeBlock language="python">{`from aquilia import Controller, GET, POST, RequestCtx, Response
from aquilia.sqlite import ConnectionPool

class UsersController(Controller):
    prefix = "/users"
    
    def __init__(self, db: ConnectionPool):
        self.db = db
    
    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        rows = await self.db.fetchall("SELECT * FROM users")
        users = [dict(row) for row in rows]
        return Response.json(users)
    
    @POST("/")
    async def create_user(self, ctx: RequestCtx):
        data = await ctx.request.json()
        
        async with self.db.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "INSERT INTO users (name, email) VALUES (?, ?)",
                    (data["name"], data["email"])
                )
                user_id = conn.last_insert_rowid
        
        return Response.json({"id": user_id}, status=201)`}</CodeBlock>
      </section>

      {/* CRUD Operations */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          CRUD Controller
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Complete CRUD example.
        </p>

        <CodeBlock language="python">{`from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response
from aquilia.sqlite import ConnectionPool, SqliteIntegrityError

class UsersController(Controller):
    prefix = "/users"
    
    def __init__(self, db: ConnectionPool):
        self.db = db
    
    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        """List all users."""
        rows = await self.db.fetchall("SELECT id, name, email FROM users")
        return Response.json([dict(row) for row in rows])
    
    @GET("/{id}")
    async def get_user(self, ctx: RequestCtx):
        """Get user by ID."""
        user_id = int(ctx.params["id"])
        row = await self.db.fetchone(
            "SELECT id, name, email FROM users WHERE id = ?",
            (user_id,)
        )
        if not row:
            return Response.json({"error": "User not found"}, status=404)
        return Response.json(dict(row))
    
    @POST("/")
    async def create_user(self, ctx: RequestCtx):
        """Create a new user."""
        data = await ctx.request.json()
        
        try:
            async with self.db.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        "INSERT INTO users (name, email) VALUES (?, ?)",
                        (data["name"], data["email"])
                    )
                    user_id = conn.last_insert_rowid
            
            return Response.json({"id": user_id}, status=201)
        except SqliteIntegrityError:
            return Response.json({"error": "Email already exists"}, status=400)
    
    @PUT("/{id}")
    async def update_user(self, ctx: RequestCtx):
        """Update user."""
        user_id = int(ctx.params["id"])
        data = await ctx.request.json()
        
        async with self.db.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE users SET name = ?, email = ? WHERE id = ?",
                    (data["name"], data["email"], user_id)
                )
                if conn.rowcount == 0:
                    return Response.json({"error": "User not found"}, status=404)
        
        return Response.json({"id": user_id})
    
    @DELETE("/{id}")
    async def delete_user(self, ctx: RequestCtx):
        """Delete user."""
        user_id = int(ctx.params["id"])
        
        async with self.db.acquire() as conn:
            async with conn.transaction():
                await conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
                if conn.rowcount == 0:
                    return Response.json({"error": "User not found"}, status=404)
        
        return Response.json({"deleted": True})`}</CodeBlock>
      </section>

      {/* Repository Pattern */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Repository Pattern
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Separate database logic from controllers.
        </p>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Create repository</h4>
        <CodeBlock language="python">{`# repositories/users.py
from aquilia.sqlite import ConnectionPool
from dataclasses import dataclass

@dataclass
class User:
    id: int
    name: str
    email: str

class UserRepository:
    def __init__(self, db: ConnectionPool):
        self.db = db
    
    async def find_all(self) -> list[User]:
        rows = await self.db.fetchall("SELECT id, name, email FROM users")
        return [User(**row) for row in rows]
    
    async def find_by_id(self, user_id: int) -> User | None:
        row = await self.db.fetchone(
            "SELECT id, name, email FROM users WHERE id = ?",
            (user_id,)
        )
        return User(**row) if row else None
    
    async def create(self, name: str, email: str) -> int:
        async with self.db.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "INSERT INTO users (name, email) VALUES (?, ?)",
                    (name, email)
                )
                return conn.last_insert_rowid
    
    async def update(self, user_id: int, name: str, email: str) -> bool:
        async with self.db.acquire() as conn:
            async with conn.transaction():
                await conn.execute(
                    "UPDATE users SET name = ?, email = ? WHERE id = ?",
                    (name, email, user_id)
                )
                return conn.rowcount > 0
    
    async def delete(self, user_id: int) -> bool:
        async with self.db.acquire() as conn:
            async with conn.transaction():
                await conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
                return conn.rowcount > 0`}</CodeBlock>

        <h4 className={`font-semibold mt-6 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Use in controller</h4>
        <CodeBlock language="python">{`from aquilia import Controller, GET, POST, RequestCtx, Response
from repositories.users import UserRepository

class UsersController(Controller):
    prefix = "/users"
    
    def __init__(self, users: UserRepository):
        self.users = users
    
    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        users = await self.users.find_all()
        return Response.json([{"id": u.id, "name": u.name, "email": u.email} for u in users])
    
    @GET("/{id}")
    async def get_user(self, ctx: RequestCtx):
        user_id = int(ctx.params["id"])
        user = await self.users.find_by_id(user_id)
        if not user:
            return Response.json({"error": "User not found"}, status=404)
        return Response.json({"id": user.id, "name": user.name, "email": user.email})
    
    @POST("/")
    async def create_user(self, ctx: RequestCtx):
        data = await ctx.request.json()
        user_id = await self.users.create(data["name"], data["email"])
        return Response.json({"id": user_id}, status=201)`}</CodeBlock>
      </section>

      {/* Pagination */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Pagination
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Paginate large result sets.
        </p>

        <CodeBlock language="python">{`from aquilia import Controller, GET, RequestCtx, Response
from aquilia.sqlite import ConnectionPool

class UsersController(Controller):
    prefix = "/users"
    
    def __init__(self, db: ConnectionPool):
        self.db = db
    
    @GET("/")
    async def list_users(self, ctx: RequestCtx):
        # Get pagination params
        page = int(ctx.request.query.get("page", 1))
        per_page = int(ctx.request.query.get("per_page", 20))
        offset = (page - 1) * per_page
        
        # Get total count
        count_row = await self.db.fetchone("SELECT COUNT(*) as count FROM users")
        total = count_row.count
        
        # Get paginated results
        rows = await self.db.fetchall(
            "SELECT id, name, email FROM users LIMIT ? OFFSET ?",
            (per_page, offset)
        )
        
        return Response.json({
            "data": [dict(row) for row in rows],
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page,
        })`}</CodeBlock>
      </section>

      {/* Error Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Error Handling
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Handle database errors gracefully.
        </p>

        <CodeBlock language="python">{`from aquilia import Controller, POST, RequestCtx, Response
from aquilia.sqlite import (
    ConnectionPool,
    SqliteIntegrityError,
    SqliteQueryError,
    PoolExhaustedError,
)

class UsersController(Controller):
    prefix = "/users"
    
    def __init__(self, db: ConnectionPool):
        self.db = db
    
    @POST("/")
    async def create_user(self, ctx: RequestCtx):
        data = await ctx.request.json()
        
        try:
            async with self.db.acquire() as conn:
                async with conn.transaction():
                    await conn.execute(
                        "INSERT INTO users (name, email) VALUES (?, ?)",
                        (data["name"], data["email"])
                    )
                    user_id = conn.last_insert_rowid
            
            return Response.json({"id": user_id}, status=201)
            
        except SqliteIntegrityError as e:
            # Constraint violation (e.g., duplicate email)
            return Response.json({"error": "Email already exists"}, status=400)
            
        except SqliteQueryError as e:
            # SQL syntax error
            return Response.json({"error": "Invalid query"}, status=500)
            
        except PoolExhaustedError:
            # No connections available
            return Response.json({"error": "Database busy"}, status=503)`}</CodeBlock>
      </section>

      {/* Next Steps */}
    </div>
  )
}
