import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Zap, Rocket, Layers, Plug, Database, Lock, Settings, Terminal, ArrowRight } from 'lucide-react'

export function QuickStartPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Zap className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Quick Start
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>Build a working API in 5 minutes</p>
          </div>
        </div>

        <p className={`text-lg ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          This guide walks you through creating, configuring, and running an Aquilia application from scratch.
          By the end, you'll have a multi-endpoint REST API with dependency injection, validation blueprints, database models, and unit tests.
        </p>
      </div>

      {/* Step 1: Create workspace */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="w-8 h-8 rounded-lg bg-aquilia-500/20 text-aquilia-400 flex items-center justify-center text-sm font-bold">1</span>
          Create a Workspace
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Use the <code>aq init workspace</code> command to scaffold a new workspace directory containing standard project configuration files:
        </p>

        <CodeBlock
          code={`# Create a new workspace
aq init workspace my-api

# Navigate into it
cd my-api`}
          language="bash"
        />

        <p className={`mt-4 mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          This command generates the following project layout:
        </p>

        <CodeBlock
          code={`my-api/
├── workspace.py          # Root configuration (integrations, server options)
├── starter.py            # Welcome-page controller (shown at / when debug=True)
├── modules/              # Sub-modules (initially empty)
├── tests/                # Test suite
│   ├── conftest.py
│   └── test_smoke.py
├── requirements.txt      # Project dependencies
├── .env.example          # Environment variables template
└── Makefile              # Developer shortcuts`}
          language="text"
        />

        <h3 className={`text-lg font-semibold mt-6 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Workspace Configuration</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Open <code>workspace.py</code> to see the Fluent Builder configuration structure. The workspace config manages environment settings, module registrations, and third-party integrations:
        </p>

        <CodeBlock
          code={`# workspace.py
from aquilia import Workspace, Module
from aquilia import AquilaConfig, Secret, Env
from aquilia.integrations import (
    MiddlewareChain,
    DiIntegration,
    RegistryIntegration,
    RoutingIntegration,
    FaultHandlingIntegration,
    PatternsIntegration,
    DatabaseIntegration,
    CacheIntegration,
)

class BaseEnv(AquilaConfig):
    """Shared defaults — every environment inherits these."""
    env = "dev"

    class server(AquilaConfig.Server):
        host = "127.0.0.1"
        port = 8000
        workers = 1
        reload = True

workspace = (
    Workspace("my-api")
    .env_config(BaseEnv)
    .starter("starter")
    .middleware(MiddlewareChain.defaults())
    .integrate(DiIntegration(auto_wire=True))
    .integrate(RegistryIntegration())
    .integrate(RoutingIntegration(strict_matching=True))
    .integrate(FaultHandlingIntegration(default_strategy="propagate"))
    .integrate(PatternsIntegration())
    .integrate(DatabaseIntegration(url="sqlite:///db.sqlite3"))
    .integrate(CacheIntegration(backend="memory"))
)

__all__ = ["workspace"]`}
          language="python"
        />

        <h3 className={`text-lg font-semibold mt-6 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Starter welcome page</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The workspace starts with a welcome controller defined in <code>starter.py</code>:
        </p>

        <CodeBlock
          code={`# starter.py
from aquilia import Controller, GET, RequestCtx, Response

class StarterController(Controller):
    prefix = "/"
    tags = ["starter"]

    @GET("/")
    async def welcome(self, ctx: RequestCtx):
        from aquilia.debug.pages import render_welcome_page
        try:
            from aquilia import __version__
            version = __version__
        except Exception:
            version = ""

        html = render_welcome_page(aquilia_version=version)
        return Response(
            content=html.encode("utf-8"),
            status=200,
            headers={"content-type": "text/html; charset=utf-8"},
        )`}
          language="python"
        />
      </section>

      {/* Step 2: Add a Module */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="w-8 h-8 rounded-lg bg-aquilia-500/20 text-aquilia-400 flex items-center justify-center text-sm font-bold">2</span>
          Add a Module
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          To add a new feature or logical domain to your workspace, run <code>aq add module [NAME]</code>:
        </p>

        <CodeBlock
          code={`# Add a new module named "tasks"
aq add module tasks`}
          language="bash"
        />

        <p className={`mt-4 mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          This scaffolds a new module directory structure under <code>modules/tasks/</code>:
        </p>

        <CodeBlock
          code={`modules/tasks/
├── __init__.py
├── manifest.py       # Module identity, component imports, and error domain settings
├── blueprints.py     # Request data validation classes
├── controllers.py    # Request handlers & HTTP routing
├── services.py       # Core business logic
├── faults.py         # Domain-specific error codes
└── models.py         # ORM database models`}
          language="text"
        />

        <p className={`mt-6 mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Here is the complete, valid, executable example code for each of these files as scaffolded by the CLI generator:
        </p>

        {/* manifest.py */}
        <div className="mb-6">
          <p className={`text-sm font-mono mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>modules/tasks/manifest.py</p>
          <CodeBlock
            code={`from aquilia import AppManifest
from aquilia.manifest import FaultHandlingConfig

manifest = AppManifest(
    name="tasks",
    version="0.1.0",
    description="Tasks module",
    tags=["tasks"],
    controllers=[
        "modules.tasks.controllers:TasksController",
    ],
    services=[
        "modules.tasks.services:TasksService",
    ],
    models=[
        "modules.tasks.models:Task",
    ],
    base_path="modules.tasks",
    imports=[],
    exports=[],
    faults=FaultHandlingConfig(
        default_domain="TASKS",
        strategy="propagate",
    ),
    auto_discover=True,
)

__all__ = ["manifest"]`}
            language="python"
          />
        </div>

        {/* __init__.py */}
        <div className="mb-6">
          <p className={`text-sm font-mono mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>modules/tasks/__init__.py</p>
          <CodeBlock
            code={`from .controllers import *
from .services import *
from .faults import *

__module_name__ = "tasks"
__version__ = "0.1.0"`}
            language="python"
          />
        </div>

        {/* blueprints.py */}
        <div className="mb-6">
          <p className={`text-sm font-mono mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>modules/tasks/blueprints.py</p>
          <CodeBlock
            code={`from aquilia import Blueprint

class TaskBlueprint(Blueprint):
    """Blueprint for Task input validation."""
    name: str
    description: str | None = None
    active: bool = True

    class Spec:
        extra_fields = "reject"`}
            language="python"
          />
        </div>

        {/* controllers.py */}
        <div className="mb-6">
          <p className={`text-sm font-mono mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>modules/tasks/controllers.py</p>
          <CodeBlock
            code={`from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response
from .faults import TasksNotFoundFault
from .services import TasksService
from .blueprints import TaskBlueprint

class TasksController(Controller):
    """Controller for tasks endpoints."""
    prefix = "/"
    tags = ["tasks"]

    def __init__(self, service: TasksService = None):
        # Service is injected via Dependency Injection, fallback to direct initialization
        self.service = service or TasksService()

    @GET("/")
    async def list_tasks(self, ctx: RequestCtx):
        """List all tasks."""
        items = await self.service.get_all()
        return Response.json({
            "items": items,
            "total": len(items)
        })

    @POST("/")
    async def create_task(self, ctx: RequestCtx, data: TaskBlueprint):
        """Create a new task, validating parameters using TaskBlueprint."""
        item = await self.service.create(data.to_dict())
        return Response.json(item, status=201)

    @GET("/<id:int>")
    async def get_task(self, ctx: RequestCtx, id: int):
        """Get a task by ID."""
        item = await self.service.get_by_id(id)
        if not item:
            raise TasksNotFoundFault(item_id=id)
        return Response.json(item)

    @PUT("/<id:int>")
    async def update_task(self, ctx: RequestCtx, id: int, data: TaskBlueprint):
        """Update a task by ID."""
        item = await self.service.update(id, data.to_dict())
        if not item:
            raise TasksNotFoundFault(item_id=id)
        return Response.json(item)

    @DELETE("/<id:int>")
    async def delete_task(self, ctx: RequestCtx, id: int):
        """Delete a task."""
        deleted = await self.service.delete(id)
        if not deleted:
            raise TasksNotFoundFault(item_id=id)
        return Response(status=204)`}
            language="python"
          />
        </div>

        {/* services.py */}
        <div className="mb-6">
          <p className={`text-sm font-mono mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>modules/tasks/services.py</p>
          <CodeBlock
            code={`from typing import Optional, List
from aquilia.di import service

@service(scope="app")
class TasksService:
    """Tasks business logic service."""
    def __init__(self):
        self._storage: List[dict] = []
        self._next_id = 1

    async def get_all(self) -> List[dict]:
        return self._storage

    async def get_by_id(self, item_id: int) -> Optional[dict]:
        for item in self._storage:
            if item["id"] == item_id:
                return item
        return None

    async def create(self, data: dict) -> dict:
        item = {
            "id": self._next_id,
            **data
        }
        self._storage.append(item)
        self._next_id += 1
        return item

    async def update(self, item_id: int, data: dict) -> Optional[dict]:
        item = await self.get_by_id(item_id)
        if item:
            item.update(data)
        return item

    async def delete(self, item_id: int) -> bool:
        for i, item in enumerate(self._storage):
            if item["id"] == item_id:
                self._storage.pop(i)
                return True
        return False`}
            language="python"
          />
        </div>

        {/* faults.py */}
        <div className="mb-6">
          <p className={`text-sm font-mono mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>modules/tasks/faults.py</p>
          <CodeBlock
            code={`from aquilia.faults import Fault, FaultDomain, Severity

TASKS_FAULT_DOMAIN = FaultDomain.custom(
    "tasks",
    "Tasks module faults",
)

class TasksNotFoundFault(Fault):
    """Raised when a task is not found."""
    domain = TASKS_FAULT_DOMAIN
    severity = Severity.INFO
    code = "TASKS_NOT_FOUND"

    def __init__(self, item_id: int):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message=f"Task with id {item_id} not found",
            metadata={"item_id": item_id},
            retryable=False,
        )`}
            language="python"
          />
        </div>

        {/* models.py */}
        <div className="mb-6">
          <p className={`text-sm font-mono mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>modules/tasks/models.py</p>
          <CodeBlock
            code={`from aquilia.models import Model
from aquilia.models.fields import (
    AutoField,
    CharField,
    TextField,
    BooleanField,
    DateTimeField,
)

class Task(Model):
    """Database model for Tasks."""
    table = "tasks"

    id = AutoField(primary_key=True)
    name = CharField(max_length=255)
    description = TextField(blank=True, default="")
    active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __repr__(self):
        return f"<Task id={self.id} name={self.name!r}>"`}
            language="python"
          />
        </div>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The CLI auto-discovery updates <code>workspace.py</code> to register your new module as a pointer, ensuring your routes and metadata are wireable:
        </p>

        <CodeBlock
          code={`workspace = (
    Workspace("my-api")
    .env_config(BaseEnv)
    .starter("starter")
    # ---- Modules -------------------------------------------------------------
    .module(
        Module("tasks", version="0.1.0", description="Tasks module")
        .route_prefix("/tasks")
    )
    # ...
)`}
          language="python"
        />
      </section>

      {/* Step 3: Run */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="w-8 h-8 rounded-lg bg-aquilia-500/20 text-aquilia-400 flex items-center justify-center text-sm font-bold">3</span>
          Run the Development Server
        </h2>

        <CodeBlock
          code={`# Start the dev server (auto-reload is active by default in dev environment)
aq run`}
          language="bash"
        />

        <p className={`mt-4 mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Upon booting, the compiler outputs the route registrations and subsystem configurations:
        </p>

        <CodeBlock
          code={`╔══════════════════════════════════════════╗
║     Aquilia v1.2.3  ✓  Development       ║
╚══════════════════════════════════════════╝

  → Loading workspace.py ...
  ✓ Module "tasks" discovered
    ├─ Controllers: TasksController
    ├─ Services: TasksService
    └─ Models: Task
  ✓ Middleware stack compiled (5 layers)
  ✓ DI container ready (2 providers)
  ✓ Routes compiled:
    GET    /
    GET    /tasks/
    POST   /tasks/
    GET    /tasks/<id:int>
    PUT    /tasks/<id:int>
    DELETE /tasks/<id:int>

  Serving on http://127.0.0.1:8000 (Press Ctrl+C to stop)`}
          language="text"
        />
      </section>

      <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
        Open <a href="http://127.0.0.1:8000" target="_blank" rel="noopener noreferrer" className="text-aquilia-400 hover:underline font-mono">http://127.0.0.1:8000</a> in your browser to inspect the dev console.
      </p>

      <div className="mb-10 rounded-2xl overflow-hidden shadow-2xl">
        <img
          src="/starter.png"
          alt="Aquilia Starter Page"
          className="w-full h-auto"
        />
      </div>

      {/* Step 4: Test with cURL */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="w-8 h-8 rounded-lg bg-aquilia-500/20 text-aquilia-400 flex items-center justify-center text-sm font-bold">4</span>
          Test with cURL
        </h2>

        <CodeBlock
          code={`# Create a task
curl -X POST http://127.0.0.1:8000/tasks/ \\
  -H "Content-Type: application/json" \\
  -d '{"name": "Learn Aquilia", "description": "Build an API"}'
# → {"id": 1, "name": "Learn Aquilia", "description": "Build an API", "active": true}

# List all tasks
curl http://127.0.0.1:8000/tasks/
# → {"items": [{"id": 1, "name": "Learn Aquilia", "description": "Build an API", "active": true}], "total": 1}`}
          language="bash"
        />
      </section>

      {/* Step 5: Write Tests */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="w-8 h-8 rounded-lg bg-aquilia-500/20 text-aquilia-400 flex items-center justify-center text-sm font-bold">5</span>
          Write Tests
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Use the built-in <code>AquiliaTestCase</code> to run integration and endpoint verification tests against the modules. You do not need to construct a test client manually; use the built-in <code>self.client</code> property along with status assertion methods:
        </p>

        <CodeBlock
          code={`# tests/test_tasks.py
from aquilia.testing import AquiliaTestCase
from modules.tasks.manifest import manifest as tasks_manifest

class TestTasks(AquiliaTestCase):
    # Specify the module manifests to load in the test context
    manifests = [tasks_manifest]

    async def test_create_task(self):
        # Built-in self.client handles network requests internally
        response = await self.client.post("/tasks/", json={
            "name": "Write Unit Tests",
            "description": "Test the tasks controller endpoints",
        })
        # Built-in assertion helper validates the response status code
        self.assert_status(response, 201)
        
        data = response.json()
        self.assertEqual(data["name"], "Write Unit Tests")

    async def test_list_tasks(self):
        response = await self.client.get("/tasks/")
        self.assert_status(response, 200)
        data = response.json()
        self.assertIn("items", data)`}
          language="python"
        />

        <p className={`mt-4 mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Run the tests using the CLI wrapper:
        </p>

        <CodeBlock
          code={`# Run test suite
aq test`}
          language="bash"
        />
      </section>

      {/* Next Steps */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-8 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Rocket className="w-5 h-5 text-aquilia-400" />
          Next Steps
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-4">
          {[
            { to: '/docs/controllers/overview', icon: <Layers className="w-4 h-4" />, title: 'Controllers in Depth', desc: 'Lifecycle hooks, pipelines, OpenAPI generation' },
            { to: '/docs/di/container', icon: <Plug className="w-4 h-4" />, title: 'Dependency Injection', desc: 'Scopes, providers, and the Container API' },
            { to: '/docs/models/defining', icon: <Database className="w-4 h-4" />, title: 'ORM & Models', desc: 'Define models, run queries, manage migrations' },
            { to: '/docs/auth/identity', icon: <Lock className="w-4 h-4" />, title: 'Authentication', desc: 'JWT tokens, sessions, RBAC, guards' },
            { to: '/docs/config/workspace', icon: <Settings className="w-4 h-4" />, title: 'Configuration', desc: 'Workspace, Module, and Integration builders' },
            { to: '/docs/cli/commands', icon: <Terminal className="w-4 h-4" />, title: 'CLI Reference', desc: 'All aq commands and their options' },
          ].map((link, i) => (
            <Link
              key={i}
              to={link.to}
              className="group relative flex items-start gap-4 py-3 pl-4 transition-all duration-300"
            >
              {/* Vertical brand-colored accent line that grows on hover */}
              <div className="absolute left-0 top-3 bottom-3 w-0.5 bg-aquilia-500 scale-y-0 group-hover:scale-y-100 transition-transform duration-300 origin-center rounded" />
              
              <div className="relative">
                {/* Soft gradient blur glow behind icon on hover */}
                <div className="absolute inset-0 bg-aquilia-500/20 rounded-full blur-md opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className={`relative flex-shrink-0 w-9 h-9 rounded-lg flex items-center justify-center border transition-all duration-300 ${
                  isDark 
                    ? 'bg-zinc-900 border-white/5 text-aquilia-400 group-hover:text-aquilia-300 group-hover:border-aquilia-500/30' 
                    : 'bg-white border-gray-100 text-aquilia-600 group-hover:text-aquilia-500 group-hover:border-aquilia-500/30'
                }`}>
                  {link.icon}
                </div>
              </div>
              
              <div className="flex-grow min-w-0">
                <div className={`font-semibold text-sm transition-colors duration-300 group-hover:text-aquilia-500 dark:group-hover:text-aquilia-400 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  {link.title}
                </div>
                <div className={`text-xs leading-relaxed mt-1 transition-colors duration-300 ${isDark ? 'text-zinc-400 group-hover:text-zinc-300' : 'text-gray-500 group-hover:text-gray-700'}`}>
                  {link.desc}
                </div>
              </div>
              
              <div className="flex-shrink-0 self-center opacity-0 -translate-x-2 group-hover:opacity-100 group-hover:translate-x-0 transition-all duration-300">
                <ArrowRight className="w-4 h-4 text-aquilia-500 dark:text-aquilia-400" />
              </div>
            </Link>
          ))}
        </div>
      </section>
    </div>
  )
}
