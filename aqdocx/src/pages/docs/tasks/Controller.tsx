import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Clock, Layout, Box, Plug, Layers } from 'lucide-react'

export function TasksController() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Clock className="w-4 h-4 animate-pulse" />
          Background Tasks / Controller Guide
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Controller Integration
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Learn how to dispatch background tasks from HTTP Controllers, inject the TaskManager instance, track job states, and test your async logic.
        </p>
      </div>

      {/* DI Setup */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          Dependency Injection Setup
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          You do not need to manually register the <DocTerm id="tasks.TaskManager">TaskManager</DocTerm> class inside your app manifests. When <code className="text-aquilia-500">TasksIntegration</code> is registered in <code className="text-aquilia-500">workspace.py</code>, the dependency injection container automatically binds the active manager as an app-scoped singleton.
        </p>

        <p className={`mb-4 ${subtleText}`}>
          Simply declare <DocTerm id="tasks.TaskManager">TaskManager</DocTerm> as a parameter type in your Controller constructor. Aquilia resolves it automatically using type annotations, without requiring explicit <code className="text-aquilia-500">Inject()</code> defaults:
        </p>
        <CodeBlock language="python" highlightLines={[8, 16, 17, 18, 19, 20, 24]}>{`# modules/core/controllers.py
from aquilia import Controller, POST, GET, RequestCtx, Response
from aquilia.tasks import TaskManager
from .tasks import send_welcome_email

class SignupController(Controller):
    # Auto-wired via DI using type annotations
    def __init__(self, manager: TaskManager):
        self.manager = manager
        
    @POST("/signup")
    async def signup(self, ctx: RequestCtx) -> Response:
        data = await ctx.json()
        
        # Option A: Dispatch via injected manager (allows advanced options)
        job_id = await self.manager.enqueue(
            send_welcome_email,
            email=data["email"],
            priority=Priority.HIGH
        )
        
        # Option B: Dispatch via descriptor delay helper directly
        # (TaskManager is auto-bound to send_welcome_email descriptor)
        job_id = await send_welcome_email.delay(email=data["email"])
        
        return Response.json({"job_id": job_id})`}</CodeBlock>
      </section>

      {/* Task Definition with DI */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Task Dependency Injection
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Aquilia's worker automatically resolves task parameters using the DI container based on type hints. Task functions do not need default <code className="text-aquilia-500">Inject()</code> markers.
        </p>
        <CodeBlock language="python" highlightLines={[7, 8, 9, 10, 11]}>{`# modules/core/tasks.py
from aquilia.tasks import task
from modules.core.services import EmailService
from aquilia.sqlite import SqliteService

@task(queue="emails")
async def send_welcome_email(
    email: str,
    email_service: EmailService,
    db: SqliteService,
):
    # DI resolves EmailService and SqliteService when the worker executes this task
    user = await db.fetch_one("SELECT name FROM users WHERE email = ?", [email])
    name = user["name"] if user else "Valued User"
    
    await email_service.send_welcome(email, name)`}</CodeBlock>
      </section>

      {/* Checking Job Status */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Tracking Job Status
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Provide status endpoints to allow clients to poll for background job outcomes or trace failures.
        </p>
        <CodeBlock language="python" highlightLines={[7, 15]}>{`from aquilia import Controller, GET, RequestCtx, Response
from aquilia.tasks import TaskManager, JobState

class JobStatusController(Controller):
    prefix = "/jobs"
    
    def __init__(self, manager: TaskManager):
        self.manager = manager
        
    @GET("/{job_id}")
    async def status(self, ctx: RequestCtx, job_id: str) -> Response:
        job = await self.manager.get_job(job_id)
        if not job:
            return Response.json({"error": "Job not found"}, status=404)
            
        data = {
            "job_id": job.id,
            "state": job.state.value,
            "created_at": job.created_at.isoformat(),
        }
        
        # Include outcomes if finished
        if job.state == JobState.COMPLETED:
            data["result"] = job.result.value
            data["duration_ms"] = job.result.duration_ms
        elif job.state in (JobState.FAILED, JobState.DEAD):
            data["error"] = job.result.error
            data["error_type"] = job.result.error_type
            data["retry_count"] = job.retry_count
            
        return Response.json(data)`}</CodeBlock>
      </section>

      {/* Testing */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Testing Task Controllers
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          To test controller routing without actually processing jobs asynchronously, mock the <DocTerm id="tasks.TaskManager">TaskManager</DocTerm>. To test the task handler itself, run it synchronously as a standard coroutine.
        </p>
        <CodeBlock language="python">{`# tests/test_tasks.py
import pytest
from unittest.mock import AsyncMock
from aquilia.tasks import TaskManager
from modules.core.tasks import send_welcome_email

@pytest.mark.asyncio
async def test_controller_dispatches(client, mock_container):
    # Mock the TaskManager
    mock_manager = AsyncMock(spec=TaskManager)
    mock_manager.enqueue.return_value = "mock_job_123"
    mock_container.register_instance(TaskManager, mock_manager)
    
    response = client.post("/signup", json={"email": "test@example.com"})
    assert response.status_code == 200
    assert response.json()["job_id"] == "mock_job_123"

@pytest.mark.asyncio
async def test_task_logic_directly():
    # Execute task synchronously by passing mocks directly
    mock_service = AsyncMock()
    mock_db = AsyncMock()
    mock_db.fetch_one.return_value = {"name": "Alice"}
    
    await send_welcome_email(
        email="test@example.com",
        email_service=mock_service,
        db=mock_db
    )
    
    mock_service.send_welcome.assert_called_once_with("test@example.com", "Alice")`}</CodeBlock>
      </section>

      {/* Best Practices */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Best Practices
        </h2>
        <div className="grid grid-cols-1 gap-6">
          {[
            {
              icon: <Layout className="w-5 h-5 text-aquilia-500" />,
              title: 'Pass Serializable Arguments Only',
              desc: 'Never pass active database models or open file descriptors as arguments to background tasks. Instead, pass identifier parameters (like user_id) and fetch fresh data from the database inside the task execution scope.',
            },
            {
              icon: <Plug className="w-5 h-5 text-blue-500" />,
              title: 'Handle TaskManager Absence Gracefully',
              desc: 'If writing code that must run both inside and outside of the server environment, wrap .delay() calls in try/except blocks catching TaskNotBoundFault to fall back to direct synchronous execution.',
            },
            {
              icon: <Box className="w-5 h-5 text-emerald-500" />,
              title: 'Return Job IDs for Polling',
              desc: 'When enqueuing background work from an API endpoint, return the job ID immediately. This enables frontends to poll a status endpoint or subscribe to a WebSocket event to update progress bars.',
            },
          ].map((item, i) => (
            <div key={i} className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 p-5 transition-all duration-300">
              <div className="absolute top-0 bottom-0 left-0 w-1 bg-white/5 group-hover:bg-aquilia-500 transition-colors duration-300" />
              <div className="flex items-center gap-3 mb-3">
                {item.icon}
                <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h3>
              </div>
              <p className={`text-xs leading-relaxed ${subtleText}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
