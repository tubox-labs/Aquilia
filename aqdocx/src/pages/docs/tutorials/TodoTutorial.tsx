import { useState } from 'react'
import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { CheckCircle } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { NextSteps } from '../../../components/NextSteps'

export function TodoTutorialPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [activeStep, setActiveStep] = useState(1)

  const steps = [
    { id: 1, label: '1. Scaffolding', desc: 'Generate the todos module structure' },
    { id: 2, label: '2. DB Model', desc: 'Define the Todo database schema' },
    { id: 3, label: '3. Blueprints', desc: 'Create validation and serialization contracts' },
    { id: 4, label: '4. Faults', desc: 'Define domain-specific errors' },
    { id: 5, label: '5. DI Service', desc: 'Implement queries and business logic' },
    { id: 6, label: '6. Controller', desc: 'Write REST endpoints' },
    { id: 7, label: '7. Wire Up', desc: 'Register the module and run migrations' },
    { id: 8, label: '8. Testing', desc: 'Write end-to-end integration tests' },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-10">
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <CheckCircle className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Todo Application
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>End-to-End Beginner-Level Tutorial with Code Examples</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          In this tutorial, you will build a complete, database-backed REST API for a Todo application.
          You'll learn how to define database models using the Aquilia ORM, create request/response contracts using validation blueprints, write business logic inside dependency-injected services, handle client errors using custom faults, and test your work using the built-in test client.
        </p>
      </div>

      {/* Interactive Step Navigator */}
      <section className="mb-14 mt-6">
        <div className="relative flex items-center justify-between mb-16 max-w-3xl mx-auto px-4">
          {/* Connecting line */}
          <div className={`absolute top-1/2 left-0 right-0 h-[2px] -translate-y-1/2 ${isDark ? 'bg-white/5' : 'bg-gray-200'}`} />
          {/* Active filling line */}
          <div
            className="absolute top-1/2 left-0 h-[2px] -translate-y-1/2 bg-gradient-to-r from-aquilia-500 to-blue-500 transition-all duration-300"
            style={{ width: `${((activeStep - 1) / (steps.length - 1)) * 100}%` }}
          />
          {steps.map((step) => {
            const isActive = activeStep === step.id
            const isCompleted = activeStep > step.id
            return (
              <button
                key={step.id}
                onClick={() => setActiveStep(step.id)}
                className="relative flex flex-col items-center group cursor-pointer z-10 focus:outline-none"
              >
                <div
                  className={`w-9 h-9 rounded-full flex items-center justify-center font-mono text-xs font-bold transition-all duration-300 ${
                    isActive
                      ? 'bg-gradient-to-r from-aquilia-500 to-blue-500 text-white ring-4 ring-aquilia-500/20 scale-110 shadow-lg shadow-aquilia-500/25'
                      : isCompleted
                        ? 'bg-aquilia-500 text-white'
                        : isDark
                          ? 'bg-zinc-900 text-gray-500 border border-white/10 hover:border-white/20'
                          : 'bg-white text-gray-400 border border-zinc-200 hover:border-zinc-300'
                  }`}
                >
                  {step.id}
                </div>
                <span
                  className={`absolute top-11 text-[9px] font-mono tracking-tighter transition-colors duration-200 hidden md:block whitespace-nowrap ${
                    isActive
                      ? isDark ? 'text-white font-bold' : 'text-gray-900 font-bold'
                      : 'text-gray-500 hover:text-gray-400'
                  }`}
                >
                  {step.label.split('. ')[1]}
                </span>
              </button>
            )
          })}
        </div>
      </section>

      {/* Step Content */}
      <div className="min-h-[400px]">
        <AnimatePresence mode="wait">
          {activeStep === 1 && (
            <motion.div
              key="step-1"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 1: Scaffolding the Module</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                First, let's create a new, self-contained application module named <code className="text-aquilia-400">todos</code>.
                In your workspace directory, run the <DocTerm id="cli.add_module">aq add module</DocTerm> command:
              </p>

              <CodeBlock
                code={`# Generate the module structure inside modules/todos/
aq add module todos`}
                language="bash"
              />

              <p className={`mt-6 mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                This creates a new folder <code className="text-aquilia-400">modules/todos/</code> containing a complete scaffold.
                Let's look at the generated files:
              </p>

              <div className="space-y-6 my-8 pl-4 border-l border-aquilia-500/10">
                {[
                  { file: 'manifest.py', desc: 'The single source of truth for the module. Registers controllers, services, models, and dependencies.' },
                  { file: 'models.py', desc: 'Define your database tables here using the Aquilia ORM Model classes.' },
                  { file: 'blueprints.py', desc: 'Declare request body and response schemas to control casting and validation.' },
                  { file: 'services.py', desc: 'Houses business logic, database queries, and is wired using dependency injection.' },
                  { file: 'controllers.py', desc: 'Contains route handlers decorated with HTTP methods like GET, POST, and PUT.' },
                  { file: 'faults.py', desc: 'Declare custom domain exceptions (e.g. TodoItemNotFound) for structured error reporting.' },
                ].map((item) => (
                  <div key={item.file} className="flex flex-col md:flex-row md:items-start gap-1 md:gap-4 relative">
                    <div className="font-mono text-sm text-aquilia-400 font-bold w-36 shrink-0 flex items-center gap-2">
                      <span className="w-1.5 h-1.5 rounded-full bg-aquilia-500" />
                      {item.file}
                    </div>
                    <div className={`text-xs leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</div>
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {activeStep === 2 && (
            <motion.div
              key="step-2"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 2: Defining the Database Model</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                Open <code className="text-aquilia-400">modules/todos/models.py</code>. We will declare our <DocTerm id="orm.model">Model</DocTerm> class representing a row in our database.
                We'll use columns to store the todo title, completed state, and creation timestamps:
              </p>

              <CodeBlock
                code={`# modules/todos/models.py
from aquilia.models import Model
from aquilia.models.fields import (
    AutoField,
    CharField,
    BooleanField,
    DateTimeField,
)


class TodoItem(Model):
    """
    TodoItem database model.
    Maps to the "todos" database table.
    """
    table = "todos"

    id = AutoField(primary_key=True)
    title = CharField(max_length=255)
    completed = BooleanField(default=False)
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __repr__(self):
        return f"<TodoItem id={self.id} title={self.title!r} completed={self.completed}>"
`}
                language="python"
                filename="models.py"
                highlightLines={[9, 15, 17, 18, 19, 20, 21, 23, 24]}
              />

              <h4 className={`text-md font-bold mt-6 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>ORM Concept Explanations:</h4>
              <ul className={`space-y-3.5 text-sm leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>Model:</strong> The base class representing an ORM model. Metaclasses scan this subclass, build column registries, and attach a default <DocTerm id="orm.manager">objects Manager</DocTerm>.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>AutoField:</strong> Creates an autoincrementing integer primary key column.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>BooleanField:</strong> A boolean field in SQL. Note that the blueprint validation counterpart is named <DocTerm id="bp.facet">BoolFacet</DocTerm>, which handles type casting from JSON payloads.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>class Meta:</strong> Metaclass metadata containing table settings, ordering rules (here we sort records in descending order of creation time), indexes, or custom database constraints.</span>
                </li>
              </ul>
            </motion.div>
          )}

          {activeStep === 3 && (
            <motion.div
              key="step-3"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 3: Creating Validation Blueprints</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                Open <code className="text-aquilia-400">modules/todos/blueprints.py</code>. We will create schemas to validate request payloads (inbound) and serialize models (outbound).
                Aquilia supports two styles of declaring blueprints: the <strong className="text-aquilia-400">Explicit Facet style</strong> (descriptors) and the <strong className="text-aquilia-400">Type-Annotated style</strong> (Pydantic-like).
              </p>

              {/* Option A: Explicit Facet Style */}
              <div className="mb-6">
                <h4 className={`text-md font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Option A: Explicit Facet Descriptor Style</h4>
                <p className={`text-sm mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  Declares fields by directly instantiating class descriptors (Facets). This offers explicit type safety and constructor configuration.
                </p>
                <CodeBlock
                  code={`# modules/todos/blueprints.py (Explicit Facet Style)
from aquilia import Blueprint
from aquilia.blueprints import (
    IntFacet,
    TextFacet,
    BoolFacet,
    DateTimeFacet,
)
from .models import TodoItem


class TodoBlueprint(Blueprint):
    """
    Blueprint using explicit Facet descriptors.
    """
    id = IntFacet(read_only=True)
    title = TextFacet(max_length=255, required=True, min_length=1)
    completed = BoolFacet(required=False, default=False)
    created_at = DateTimeFacet(read_only=True)

    class Spec:
        model = TodoItem
        extra_fields = "reject"  # Fail if client sends unregistered fields
        projections = {
            "summary": ["id", "title", "completed"],
            "detail": "__all__"
        }
`}
                  language="python"
                  filename="blueprints.py"
                  highlightLines={[12, 16, 17, 18, 23, 24]}
                />
              </div>

              {/* Option B: Annotated Style */}
              <div className="mb-8">
                <h4 className={`text-md font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Option B: Modern Type-Annotated Style</h4>
                <p className={`text-sm mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  Declares fields using standard Python type hints. Constraints are declared using the <code className="text-aquilia-400">Field</code> descriptor, and computed properties can be decorated with <code className="text-aquilia-400">@computed</code>.
                </p>
                <CodeBlock
                  code={`# modules/todos/blueprints.py (Type-Annotated Style)
from datetime import datetime
from aquilia import Blueprint, Field, computed
from .models import TodoItem


class TodoBlueprint(Blueprint):
    """
    Blueprint using Python type hints and Field descriptors.
    """
    id: int = Field(read_only=True)
    title: str = Field(min_length=1, max_length=255)
    completed: bool = Field(default=False)
    created_at: datetime = Field(read_only=True)

    @computed
    def is_fresh(self, instance) -> bool:
        """Computed field dynamically resolved during serialization."""
        delta = datetime.utcnow() - instance.created_at
        return delta.total_seconds() < 3600

    class Spec:
        model = TodoItem
        extra_fields = "reject"  # Rejects inputs with extra attributes
        projections = {
            "summary": ["id", "title", "completed"],
            "detail": "__all__"
        }
`}
                  language="python"
                  filename="blueprints.py"
                  highlightLines={[7, 12, 13, 14, 15, 17, 18, 24, 25]}
                />
              </div>

              <h4 className={`text-md font-bold mt-6 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Blueprint Configuration Options (class Spec):</h4>
              <ul className={`space-y-3.5 text-sm leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>model:</strong> Binds the blueprint schema to an ORM Model class (e.g. <code className="text-aquilia-400">TodoItem</code>).</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>extra_fields:</strong> Controls how the validator handles undeclared payload fields. Set to <code className="text-aquilia-400">"reject"</code> to fail validation immediately, <code className="text-aquilia-400">"ignore"</code> (default) to strip them out, or <code className="text-aquilia-400">"allow"</code> to preserve them in raw data.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>fields / exclude:</strong> Specifying <code className="text-aquilia-400">fields = "__all__"</code> inherits all fields from the ORM model, while <code className="text-aquilia-400">exclude = ["created_at"]</code> explicitly ignores columns.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>read_only_fields / write_only_fields:</strong> Tuples designating columns that are output-only (like DB autoincrement keys) or input-only (like password secrets).</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>Projections:</strong> Subsets of fields (e.g. <code className="text-aquilia-400">TodoBlueprint["summary"]</code>) returned to callers based on serialization context, preventing unnecessary query overhead.</span>
                </li>
              </ul>
            </motion.div>
          )}

          {activeStep === 4 && (
            <motion.div
              key="step-4"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 4: Creating Custom Faults</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                Open <code className="text-aquilia-400">modules/todos/faults.py</code>. We will define structured domain exceptions.
                Unlike standard Python exceptions, <strong className="text-aquilia-400">Faults</strong> provide structured, machine-readable validation contexts.
              </p>

              <CodeBlock
                code={`# modules/todos/faults.py
from aquilia.faults import Fault, FaultDomain, Severity

# Define a domain classifier namespace for this module
TODOS_DOMAIN = FaultDomain.custom(
    "TODOS",
    "Todo application domain faults",
)


class TodoNotFoundFault(Fault):
    """
    Raised when a requested Todo item is missing from the database.
    Mapped automatically to a 404 response.
    """
    domain = TODOS_DOMAIN
    severity = Severity.INFO
    code = "TODO_NOT_FOUND"

    def __init__(self, todo_id: int):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message=f"Todo item with id {todo_id} not found",
            metadata={"todo_id": todo_id},
            retryable=False,
            public=True,  # Safe to expose error code to client
        )


class TodoAlreadyExistsFault(Fault):
    """
    Raised when trying to create a todo with a duplicate title.
    Mapped automatically to a 409 Conflict response.
    """
    domain = TODOS_DOMAIN
    severity = Severity.WARN
    code = "TODO_ALREADY_EXISTS"

    def __init__(self, title: str):
        super().__init__(
            code=self.code,
            domain=self.domain,
            message=f"Todo item with title '{title}' already exists",
            metadata={"title": title},
            retryable=False,
            public=True,
        )
`}
                language="python"
                filename="faults.py"
                highlightLines={[11, 20, 24, 33, 42]}
              />

              <h4 className={`text-md font-bold mt-6 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Why are Faults superior to Standard Exceptions?</h4>
              <ul className={`space-y-3.5 text-sm leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>Public vs Private Safety:</strong> When standard exceptions leak, they expose Python stack tracebacks (introducing severe security vulnerabilities). By setting <code className="text-aquilia-400">public=False</code>, Aquilia intercepts operational faults, logging details internally while masking client-side output with a generic 500 status code. Setting <code className="text-aquilia-400">public=True</code> safely streams the metadata to the frontend.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>Stable Error Codes:</strong> Clients should parse machine-readable IDs (e.g. <code className="text-aquilia-400">"TODO_NOT_FOUND"</code>) instead of trying to parse volatile string trace messages.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>Structured Context (Metadata):</strong> Allows developers to attach JSON payloads (e.g. mapping key identifiers) to help clients decode why operations failed.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>Retry Semantics:</strong> A fault specifies a <code className="text-aquilia-400">retryable: bool</code> flag. Transient network or concurrency glitches marked <code className="text-aquilia-400">retryable=True</code> inform middleware layers that it is safe to automatically replay the transaction.</span>
                </li>
              </ul>
            </motion.div>
          )}

          {activeStep === 5 && (
            <motion.div
              key="step-5"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 5: Implementing the DI Service</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                Open <code className="text-aquilia-400">modules/todos/services.py</code>. We will write the business logic layer.
                Annotating the class with <DocTerm id="di.service">@service</DocTerm> makes it available for injection into controllers:
              </p>

              <CodeBlock
                code={`# modules/todos/services.py
from typing import Optional, List
from aquilia.di import service
from .models import TodoItem


@service(scope="app")
class TodoService:
    """
    TodoService handles database operations.
    Wired into controllers via constructor injection.
    """

    async def get_all(self) -> List[TodoItem]:
        """Fetch all todo items."""
        return await TodoItem.objects.all()

    async def get_by_id(self, todo_id: int) -> Optional[TodoItem]:
        """Fetch a specific todo item by ID."""
        try:
            return await TodoItem.objects.get(id=todo_id)
        except Exception:
            return None

    async def create(self, data: dict) -> TodoItem:
        """Create a new todo item, raising TodoAlreadyExistsFault if title is duplicated."""
        exists = await TodoItem.objects.filter(title=data["title"]).exists()
        if exists:
            from .faults import TodoAlreadyExistsFault
            raise TodoAlreadyExistsFault(title=data["title"])

        return await TodoItem.objects.create(
            title=data["title"],
            completed=data.get("completed", False)
        )

    async def update(self, todo_id: int, data: dict) -> Optional[TodoItem]:
        """Update an existing todo item."""
        todo = await self.get_by_id(todo_id)
        if not todo:
            return None

        if "title" in data:
            # Check for title clash on update
            exists = await TodoItem.objects.filter(title=data["title"]).exclude(id=todo_id).exists()
            if exists:
                from .faults import TodoAlreadyExistsFault
                raise TodoAlreadyExistsFault(title=data["title"])
            todo.title = data["title"]
            
        if "completed" in data:
            todo.completed = data["completed"]

        await todo.save()
        return todo

    async def delete(self, todo_id: int) -> bool:
        """Delete a todo item by ID."""
        todo = await self.get_by_id(todo_id)
        if not todo:
            return False

        await todo.delete_instance()
        return True
`}
                language="python"
                filename="services.py"
                highlightLines={[7, 8, 15, 20, 25, 27, 28, 29, 30, 42, 45, 52]}
              />

              <h4 className={`text-md font-bold mt-6 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>DI and Query Concepts:</h4>
              <ul className={`space-y-3.5 text-sm leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>@service(scope="app"):</strong> Registers this service in the dependency injection container. <code className="text-aquilia-400">"app"</code> scope is initialized once and cached across requests.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>TodoItem.objects:</strong> The QuerySet manager. We invoke <code className="text-aquilia-400">all()</code> to load all items, <code className="text-aquilia-400">get(id=...)</code> for single items, and <code className="text-aquilia-400">create(**kwargs)</code> to insert a new row in one command.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>save():</strong> An instance method on the model that compiles changed columns and executes an UPDATE SQL statement in the database.</span>
                </li>
              </ul>
            </motion.div>
          )}

          {activeStep === 6 && (
            <motion.div
              key="step-6"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 6: Writing the Controller Routes</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                Open <code className="text-aquilia-400">modules/todos/controllers.py</code>. We'll use decorators to declare our endpoints.
                Constructor parameters automatically inject our <code className="text-aquilia-400">TodoService</code>, and endpoint arguments automatically validate and serialize using blueprints:
              </p>

              <CodeBlock
                code={`# modules/todos/controllers.py
from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response
from .services import TodoService
from .blueprints import TodoBlueprint
from .faults import TodoNotFoundFault


class TodoController(Controller):
    """
    Controller handling HTTP endpoints for Todo CRUD operations.
    """
    prefix = "/"
    tags = ["todos"]

    def __init__(self, service: TodoService = None):
        # Service is automatically injected by the DI container
        self.service = service or TodoService()

    @GET("/", response_blueprint=TodoBlueprint["summary"])
    async def list_todos(self, ctx: RequestCtx):
        """List all todo items, returning only basic summary fields."""
        todos = await self.service.get_all()
        return Response.json(todos)

    @POST("/", request_blueprint=TodoBlueprint, response_blueprint=TodoBlueprint["detail"])
    async def create_todo(self, ctx: RequestCtx, blueprint: TodoBlueprint):
        """Create a new todo, validating input and returning full details."""
        todo = await self.service.create(blueprint.validated_data)
        return Response.json(todo, status=201)

    @GET("/<id:int>", response_blueprint=TodoBlueprint["detail"])
    async def get_todo(self, ctx: RequestCtx, id: int):
        """Get a single todo by integer ID, raising TodoNotFoundFault if missing."""
        todo = await self.service.get_by_id(id)
        if not todo:
            raise TodoNotFoundFault(todo_id=id)
        return Response.json(todo)

    @PUT("/<id:int>", request_blueprint=TodoBlueprint, response_blueprint=TodoBlueprint["detail"])
    async def update_todo(self, ctx: RequestCtx, id: int, blueprint: TodoBlueprint):
        """Update an existing todo, merging payload, and returning detail fields."""
        todo = await self.service.update(id, blueprint.validated_data)
        if not todo:
            raise TodoNotFoundFault(todo_id=id)
        return Response.json(todo)

    @DELETE("/<id:int>")
    async def delete_todo(self, ctx: RequestCtx, id: int):
        """Delete a todo by ID, returning 204 No Content on success."""
        deleted = await self.service.delete(id)
        if not deleted:
            raise TodoNotFoundFault(todo_id=id)
        return Response(status=204)
`}
                language="python"
                filename="controllers.py"
                highlightLines={[8, 16, 20, 25, 27, 32, 38, 43, 49]}
              />

              <h4 className={`text-md font-bold mt-6 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Controller Route Concepts:</h4>
              <ul className={`space-y-3.5 text-sm leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>HTTP Verb Decorators:</strong> <DocTerm id="controller.get">@GET</DocTerm>, <DocTerm id="controller.post">@POST</DocTerm>, etc. bind route patterns to asynchronous handler methods.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>request_blueprint:</strong> Enables automatic parsing of request bodies, casting inputs, and raising a <DocTerm id="bp.seal_fault">SealFault</DocTerm> if validation fails. The verified parameters are accessible via <code className="text-aquilia-400">blueprint.validated_data</code>.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>response_blueprint:</strong> Filters and serializes model return values. We specify projections, e.g., <code className="text-aquilia-400">TodoBlueprint["summary"]</code>, to select which columns to output.</span>
                </li>
                <li className="flex gap-2.5">
                  <span className="text-aquilia-500 font-bold">•</span>
                  <span><strong className={isDark ? 'text-white' : 'text-gray-900'}>Path Parameters:</strong> Binds variables from URL paths (e.g. <code className="text-aquilia-400">&lt;id:int&gt;</code>) directly as type-coerced arguments in handler signatures.</span>
                </li>
              </ul>
            </motion.div>
          )}

          {activeStep === 7 && (
            <motion.div
              key="step-7"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 7: Wiring Up and Running Migrations</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                To activate our new module, we must register it inside the workspace configuration.
                Aquilia supports both <strong className="text-aquilia-400">Explicit Manual Wiring</strong> and <strong className="text-aquilia-400">Auto-Discovery Wiring</strong>.
              </p>

              {/* Way A: Manual Wiring */}
              <div className="mb-8">
                <h4 className={`text-md font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Way A: Explicit Manual Wiring</h4>
                <p className={`text-sm mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  Manual wiring is used when you want absolute control over which modules are imported, and exactly which classes are mapped to which paths.
                </p>

                {/* manual manifest */}
                <CodeBlock
                  code={`# modules/todos/manifest.py (Explicit Manual wiring)
from aquilia import AppManifest

manifest = AppManifest(
    name="todos",
    version="0.1.0",
    description="Todos CRUD API",
    controllers=["modules.todos.controllers:TodoController"],
    services=["modules.todos.services:TodoService"],
    models=["modules.todos.models:TodoItem"],
    auto_discover=False,  # Skip automatic directory scanning
)
`}
                  language="python"
                  filename="manifest.py"
                  highlightLines={[8, 9, 10, 11]}
                />

                {/* manual workspace */}
                <p className={`text-sm my-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  Then register it inside <code className="text-aquilia-400">workspace.py</code>:
                </p>
                <CodeBlock
                  code={`# workspace.py (Explicit Manual wiring)
workspace = (
    Workspace(name="my_server")
    .env_config(BaseEnv)
    
    # Register manually (overriding auto-discovery presets)
    .module(Module("todos", version="0.1.0")
        .route_prefix("/")
        .register_controllers("modules.todos.controllers:TodoController")
        .register_services("modules.todos.services:TodoService")
    )
    .integrate(DiIntegration(auto_wire=True))
)`}
                  language="python"
                  filename="workspace.py"
                  highlightLines={[7, 8, 9, 10]}
                />
              </div>

              {/* Way B: Auto-Discovery */}
              <div className="mb-8">
                <h4 className={`text-md font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Way B: Automatic Auto-Discovery (Recommended)</h4>
                <p className={`text-sm mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  Auto-discovery instructs the workspace scanner to automatically locate files.
                  Classes inheriting from <code className="text-aquilia-400">Controller</code>, annotated with <code className="text-aquilia-400">@service</code>, or extending <code className="text-aquilia-400">Model</code> are registered automatically.
                </p>
                
                {/* auto manifest */}
                <CodeBlock
                  code={`# modules/todos/manifest.py (Auto-discovery)
from aquilia import AppManifest

manifest = AppManifest(
    name="todos",
    version="0.1.0",
    auto_discover=True,  # Automatically scans controllers, services, models files
)
`}
                  language="python"
                  filename="manifest.py"
                  highlightLines={[6]}
                />

                {/* auto workspace */}
                <p className={`text-sm my-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  Your <code className="text-aquilia-400">workspace.py</code> simplifies down to:
                </p>
                <CodeBlock
                  code={`# workspace.py (Auto-discovery)
workspace = (
    Workspace(name="my_server")
    .env_config(BaseEnv)
    
    # Simply load the module -- auto-discovery resolves routing, services, and models
    .module(Module("todos", version="0.1.0").route_prefix("/"))
    
    .integrate(DiIntegration(auto_wire=True))  # Wires services and controller dependencies automatically
)`}
                  language="python"
                  filename="workspace.py"
                  highlightLines={[7, 9]}
                />
              </div>

              {/* CLI Actions */}
              <h4 className={`text-md font-bold mt-6 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Pre-verify and Run the Server</h4>
              <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Run migrations to construct the tables, and then test the workspace integrity before booting up:
              </p>

              <CodeBlock
                code={`# 1. ALWAYS run makemigrations first to scan models and output scripts
aq db makemigrations

# 2. Then run migrate to execute DDL statements on the database
aq db migrate

# 3. Statically validate configurations, imports, and DI trees before starting
aq validate

# 4. Start the server in hot-reload mode
aq run`}
                language="bash"
              />

              <h4 className={`text-md font-bold mt-6 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. Test the Endpoints</h4>
              <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Once the server starts at <code className="text-aquilia-400">http://127.0.0.1:8000</code>, try sending CRUD requests:
              </p>
              <CodeBlock
                code={`# Create a new Todo item (throws TodoAlreadyExistsFault if title is duplicated)
curl -X POST http://127.0.0.1:8000/ \\
  -H "Content-Type: application/json" \\
  -d '{"title": "Buy groceries"}'

# Response:
# {"id":1,"title":"Buy groceries","completed":false,"created_at":"2026-07-10T13:30:00","updated_at":"2026-07-10T13:30:00"}`}
                language="bash"
              />
            </motion.div>
          )}

          {activeStep === 8 && (
            <motion.div
              key="step-8"
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.2 }}
            >
              <h3 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Step 8: Writing Integration Tests</h3>
              <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
                To ensure code reliability, write integration tests in <code className="text-aquilia-400">tests/test_todos.py</code>.
                We'll use Aquilia's built-in <code className="text-aquilia-400">AquiliaTestCase</code> and the async <code className="text-aquilia-400">TestClient</code>:
              </p>

              <CodeBlock
                code={`# tests/test_todos.py
from aquilia.testing import AquiliaTestCase, TestClient
from workspace import workspace


class TodoIntegrationTests(AquiliaTestCase):
    """
    Test suite for Todo CRUD routes.
    """
    # Instructs test runner to boot this workspace instance
    workspace = workspace

    async def asyncSetUp(self):
        # Get an async test client connected to the ASGI app
        self.client = TestClient(self.app)

    async def test_create_and_list_todos(self):
        # 1. Create a todo item
        res = await self.client.post("/", json={"title": "Test Todo"})
        self.assertEqual(res.status_code, 201)
        data = res.json()
        self.assertEqual(data["title"], "Test Todo")
        self.assertFalse(data["completed"])
        todo_id = data["id"]

        # 2. Get the todo by ID
        res = await self.client.get(f"/{todo_id}")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["title"], "Test Todo")

        # 3. List all todos (verifies list returned)
        res = await self.client.get("/")
        self.assertEqual(res.status_code, 200)
        items = res.json()
        self.assertTrue(len(items) >= 1)
        self.assertEqual(items[0]["id"], todo_id)

    async def test_todo_not_found_raises_404(self):
        # Querying an ID that does not exist should raise 404
        res = await self.client.get("/99999")
        self.assertEqual(res.status_code, 404)
        data = res.json()
        self.assertEqual(data["error"]["code"], "TODO_NOT_FOUND")
`}
                language="python"
                filename="test_todos.py"
                highlightLines={[5, 11, 15, 18, 26, 32]}
              />

              <h4 className={`text-md font-bold mt-6 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Running the Test Suite:</h4>
              <p className={`text-sm mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Execute the tests using the <DocTerm id="cli.test">aq test</DocTerm> command:
              </p>

              <CodeBlock
                code={`# Execute all tests in the workspace and output coverage metrics
aq test --coverage`}
                language="bash"
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Navigation Buttons */}
      <div className="flex justify-between items-center mt-12 pt-6 border-t border-white/5">
        <button
          onClick={() => setActiveStep((prev) => Math.max(1, prev - 1))}
          disabled={activeStep === 1}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition cursor-pointer border ${
            activeStep === 1
              ? 'opacity-40 cursor-not-allowed border-transparent'
              : isDark
                ? 'text-gray-300 hover:text-white border-white/10 hover:bg-white/5'
                : 'text-gray-700 hover:text-gray-900 border-zinc-200 hover:bg-zinc-50'
          }`}
        >
          Previous Step
        </button>

        <button
          onClick={() => setActiveStep((prev) => Math.min(steps.length, prev + 1))}
          disabled={activeStep === steps.length}
          className={`flex items-center gap-1.5 px-4 py-2 rounded-xl text-sm font-medium transition cursor-pointer border ${
            activeStep === steps.length
              ? 'opacity-40 cursor-not-allowed border-transparent'
              : isDark
                ? 'text-aquilia-400 border-aquilia-500/20 hover:border-aquilia-500/40 hover:bg-aquilia-500/10'
                : 'text-aquilia-600 border-aquilia-200 hover:border-aquilia-400 hover:bg-aquilia-50'
          }`}
        >
          Next Step
        </button>
      </div>

      {/* Next Steps Footer link */}
      <section className="mt-14">
        <NextSteps />
      </section>
    </div>
  )
}
