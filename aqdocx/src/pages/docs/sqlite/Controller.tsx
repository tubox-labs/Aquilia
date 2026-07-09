import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Code, Layers, Terminal } from 'lucide-react'

export function SqliteController() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Code className="w-4 h-4 animate-pulse" />
          SQLite / Controller Guide
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Controller Integration
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Learn how to execute queries, manage transaction scopes, handle constraint exceptions, and paginate records inside your HTTP Controllers using the SqliteService.
        </p>
      </div>

      {/* Dependency Injection */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          Injecting the SqliteService
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          The <DocTerm id="sqlite.SqliteService">SqliteService</DocTerm> manages the connection pool lifecycle (opening on startup, closing on shutdown) and is registered in the DI container automatically.
        </p>

        <p className={`mb-4 ${subtleText}`}>
          Simply declare <DocTerm id="sqlite.SqliteService">SqliteService</DocTerm> as a parameter type in your Controller constructor. Aquilia resolves it automatically using type annotations, without requiring explicit <code className="text-aquilia-500">Inject()</code> defaults:
        </p>
        <CodeBlock language="python" highlightLines={[9, 15, 29, 30, 32, 33, 34, 35]}>{`# modules/users/controllers.py
from aquilia import Controller, GET, POST, RequestCtx, Response
from aquilia.sqlite import SqliteService, SqliteIntegrityError

class UsersController(Controller):
    prefix = "/users"

    # Auto-wired via DI using type annotations
    def __init__(self, db: SqliteService):
        self.db = db

    @GET("/")
    async def list_users(self, ctx: RequestCtx) -> Response:
        # Access the ConnectionPool via self.db.pool
        rows = await self.db.pool.fetch_all("SELECT id, name, email FROM users")
        
        # Rows behave like dictionaries:
        users = [
            {"id": row.id, "name": row["name"], "email": row.email}
            for row in rows
        ]
        return Response.json(users)

    @POST("/")
    async def create_user(self, ctx: RequestCtx) -> Response:
        data = await ctx.json()
        
        try:
            async with self.db.pool.acquire(readonly=False) as conn:
                async with conn.transaction():
                    # execute returns AsyncCursor, allowing us to read lastrowid
                    cursor = await conn.execute(
                        "INSERT INTO users (name, email) VALUES (?, ?)",
                        [data["name"], data["email"]]
                    )
                    user_id = cursor.lastrowid
                    
            return Response.json({"id": user_id}, status=201)
        except SqliteIntegrityError:
            return Response.json({"error": "Email address already registered"}, status=400)`}</CodeBlock>
      </section>

      {/* CRUD Controller Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4`}>
          Complete CRUD Operations
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          A complete controller implementing standard CRUD logic, checking cursor results to return proper HTTP responses:
        </p>
        <CodeBlock language="python" highlightLines={[7, 12, 23, 24, 36]}>{`from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response
from aquilia.sqlite import SqliteService, SqliteIntegrityError

class ItemsController(Controller):
    prefix = "/items"
    
    def __init__(self, db: SqliteService):
        self.db = db
        
    @GET("/{item_id:int}")
    async def get_item(self, ctx: RequestCtx, item_id: int) -> Response:
        row = await self.db.pool.fetch_one(
            "SELECT id, title, description FROM items WHERE id = ?", [item_id]
        )
        if not row:
            return Response.json({"error": "Item not found"}, status=404)
        return Response.json(dict(row))
        
    @PUT("/{item_id:int}")
    async def update_item(self, ctx: RequestCtx, item_id: int) -> Response:
        data = await ctx.json()
        
        async with self.db.pool.acquire(readonly=False) as conn:
            async with conn.transaction():
                cursor = await conn.execute(
                    "UPDATE items SET title = ?, description = ? WHERE id = ?",
                    [data["title"], data["description"], item_id]
                )
                if cursor.rowcount == 0:
                    return Response.json({"error": "Item not found"}, status=404)
                    
        return Response.json({"id": item_id, "updated": True})
        
    @DELETE("/{item_id:int}")
    async def delete_item(self, ctx: RequestCtx, item_id: int) -> Response:
        async with self.db.pool.acquire(readonly=False) as conn:
            async with conn.transaction():
                cursor = await conn.execute("DELETE FROM items WHERE id = ?", [item_id])
                if cursor.rowcount == 0:
                    return Response.json({"error": "Item not found"}, status=404)
                    
        return Response.json({"deleted": True})`}</CodeBlock>
      </section>

      {/* Pagination */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4`}>
          Query Pagination
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Paginate large SQL results by compiling count queries and using OFFSET parameters.
        </p>
        <CodeBlock language="python">{`@GET("/search")
async def search_items(self, ctx: RequestCtx) -> Response:
    page = int(ctx.request.query.get("page", 1))
    per_page = int(ctx.request.query.get("per_page", 10))
    offset = (page - 1) * per_page
    
    # Run total count query
    count_val = await self.db.pool.fetch_val("SELECT COUNT(*) FROM items")
    total = count_val or 0
    
    # Fetch paginated rows
    rows = await self.db.pool.fetch_all(
        "SELECT id, title FROM items LIMIT ? OFFSET ?", [per_page, offset]
    )
    
    return Response.json({
        "items": [dict(row) for row in rows],
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": (total + per_page - 1) // per_page,
    })`}</CodeBlock>
      </section>

      {/* Error Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Terminal className="w-5 h-5 text-aquilia-500" />
          Handling SQLite Exceptions
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Catch custom SQLite exceptions to return specific, actionable API error responses.
        </p>
        <CodeBlock language="python">{`from aquilia.sqlite import (
    SqliteIntegrityError,
    SqliteQueryError,
    PoolExhaustedError
)

@POST("/safe-action")
async def safe_action(self, ctx: RequestCtx) -> Response:
    try:
        await self.db.pool.execute("INSERT INTO audit_logs DEFAULT VALUES")
        return Response.json({"logged": True})
    except SqliteIntegrityError as e:
        return Response.json({"error": f"Constraint failed: {e}"}, status=400)
    except SqliteQueryError as e:
        return Response.json({"error": "Bad database request"}, status=500)
    except PoolExhaustedError:
        return Response.json({"error": "Database connection timeout"}, status=503)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
