import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Clock, Code2, Box, Zap, Database } from 'lucide-react'

export function TasksAPI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Clock className="w-4 h-4" />
          Tasks / API Reference
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Complete API Reference
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Full API documentation based on the actual implementation in <code>aquilia/tasks/</code>.
        </p>
      </div>

      {/* Table of Contents */}
      <section className="mb-16">
        <div className={`p-6 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <h3 className={`font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Table of Contents</h3>
          <div className="grid grid-cols-2 gap-3 text-sm">
            {[
              '@task Decorator',
              'TaskManager Class',
              'Priority Enum',
              'JobState Enum',
              'Job & JobResult',
              'Schedule Helpers (every, cron)',
              'get_registered_tasks()',
              'get_periodic_tasks()',
              'Integration.tasks()',
              'Faults',
            ].map((item, i) => (
              <a key={i} href={`#${item.toLowerCase().replace(/[()@\s]/g, '-')}`} className="text-aquilia-500 hover:underline">
                {item}
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* @task Decorator */}
      <section id="task-decorator" className="mb-16">
        <div className="flex items-center gap-2 mb-4">
          <Code2 className="w-5 h-5 text-aquilia-500" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code className="text-aquilia-500">@task</code>
          </h2>
        </div>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Decorator to register an async function as a background task.
        </p>

        <CodeBlock language="python">{`from aquilia.tasks import task, Priority, every, cron

def task(
    fn=None,
    *,
    name: str | None = None,
    queue: str = "default",
    priority: Priority = Priority.NORMAL,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    retry_backoff: float = 2.0,
    retry_max_delay: float = 300.0,
    timeout: float = 300.0,
    tags: list[str] | None = None,
    schedule: Schedule | None = None,
) -> _TaskDescriptor`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Parameters</h3>
        <div className="overflow-x-auto mb-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500 w-32">Parameter</th>
                <th className="text-left py-3 pr-4">Type</th>
                <th className="text-left py-3 pr-4">Default</th>
                <th className="text-left py-3">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4"><code className="text-xs">name</code></td>
                <td className="py-3 pr-4"><code className="text-xs">str | None</code></td>
                <td className="py-3 pr-4"><code className="text-xs">None</code></td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Task identifier. Auto-generated as <code>module:qualname</code> if omitted.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code className="text-xs">queue</code></td>
                <td className="py-3 pr-4"><code className="text-xs">str</code></td>
                <td className="py-3 pr-4"><code className="text-xs">"default"</code></td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Queue name for job routing.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code className="text-xs">priority</code></td>
                <td className="py-3 pr-4"><code className="text-xs">Priority</code></td>
                <td className="py-3 pr-4"><code className="text-xs">NORMAL</code></td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Priority level (CRITICAL=0, HIGH=1, NORMAL=2, LOW=3).</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code className="text-xs">max_retries</code></td>
                <td className="py-3 pr-4"><code className="text-xs">int</code></td>
                <td className="py-3 pr-4"><code className="text-xs">3</code></td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Maximum retry attempts on failure.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code className="text-xs">retry_delay</code></td>
                <td className="py-3 pr-4"><code className="text-xs">float</code></td>
                <td className="py-3 pr-4"><code className="text-xs">1.0</code></td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Base retry delay in seconds.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code className="text-xs">retry_backoff</code></td>
                <td className="py-3 pr-4"><code className="text-xs">float</code></td>
                <td className="py-3 pr-4"><code className="text-xs">2.0</code></td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Exponential backoff multiplier.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code className="text-xs">retry_max_delay</code></td>
                <td className="py-3 pr-4"><code className="text-xs">float</code></td>
                <td className="py-3 pr-4"><code className="text-xs">300.0</code></td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Maximum retry delay cap (5 minutes).</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code className="text-xs">timeout</code></td>
                <td className="py-3 pr-4"><code className="text-xs">float</code></td>
                <td className="py-3 pr-4"><code className="text-xs">300.0</code></td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Maximum execution time (5 minutes).</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code className="text-xs">tags</code></td>
                <td className="py-3 pr-4"><code className="text-xs">list[str]</code></td>
                <td className="py-3 pr-4"><code className="text-xs">[]</code></td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Metadata tags for filtering.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code className="text-xs">schedule</code></td>
                <td className="py-3 pr-4"><code className="text-xs">Schedule</code></td>
                <td className="py-3 pr-4"><code className="text-xs">None</code></td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Periodic schedule (<code>every()</code> or <code>cron()</code>). If set, scheduler auto-enqueues.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Returns</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">_TaskDescriptor</code> — A descriptor object with these methods:
        </p>
        <ul className={`list-disc list-inside space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><code>async delay(*args, **kwargs) → str</code> — Enqueue task, return job ID</li>
          <li><code>async send(*args, **kwargs) → str</code> — Alias for <code>delay()</code></li>
          <li><code>async __call__(*args, **kwargs)</code> — Direct execution (bypass queue)</li>
          <li><code>bind(manager: TaskManager)</code> — Bind a TaskManager (auto-called at server start)</li>
        </ul>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Examples</h3>
        <CodeBlock language="python">{`# Simple task
@task
async def simple_task():
    print("Hello from task")

# Fully configured
@task(
    name="email.send",
    queue="emails",
    priority=Priority.HIGH,
    max_retries=5,
    timeout=120.0,
    tags=["email", "critical"],
)
async def send_email(to: str, subject: str, body: str) -> dict:
    # Email logic
    return {"sent": True}

# Periodic task
@task(schedule=every(minutes=5))
async def cleanup():
    # Runs every 5 minutes
    pass

# Cron task
@task(schedule=cron("0 9 * * 1-5"))
async def weekday_morning():
    # Runs at 9 AM on weekdays
    pass`}</CodeBlock>
      </section>

      {/* TaskManager */}
      <section id="taskmanager-class" className="mb-16">
        <div className="flex items-center gap-2 mb-4">
          <Box className="w-5 h-5 text-aquilia-500" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code className="text-aquilia-500">TaskManager</code>
          </h2>
        </div>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Central coordinator for background task execution. Manages workers, scheduler, and job lifecycle.
        </p>

        <CodeBlock language="python">{`from aquilia.tasks import TaskManager, MemoryBackend

class TaskManager:
    def __init__(
        self,
        *,
        backend: TaskBackend | None = None,
        num_workers: int = 4,
        default_queue: str = "default",
        cleanup_interval: float = 300.0,   # 5 minutes
        cleanup_max_age: float = 3600.0,   # 1 hour
        scheduler_tick: float = 15.0,      # Periodic check interval
    )`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Lifecycle Methods</h3>
        <div className="space-y-4">
          <div>
            <code className="text-aquilia-500">async start() → None</code>
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Start workers, scheduler, and cleanup loop. Binds all <code>@task</code> decorators to this manager.
            </p>
          </div>
          <div>
            <code className="text-aquilia-500">async stop(timeout: float = 10.0) → None</code>
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Gracefully stop all workers, cancel background loops, wait up to <code>timeout</code> seconds.
            </p>
          </div>
          <div>
            <code className="text-aquilia-500">is_running: bool</code>
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Property indicating if the manager is currently running.
            </p>
          </div>
        </div>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Enqueue API</h3>
        <CodeBlock language="python">{`async def enqueue(
    self,
    func,  # Task descriptor or plain async callable
    *args,
    queue: str | None = None,
    priority: Priority | None = None,
    delay: float | None = None,
    max_retries: int | None = None,
    timeout: float | None = None,
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
    **kwargs,
) -> str  # Returns job ID`}</CodeBlock>
        <p className={`text-sm mt-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Enqueue a task for background execution. Parameters override <code>@task</code> decorator defaults.
        </p>
        <CodeBlock language="python">{`# Using a task descriptor
job_id = await manager.enqueue(send_email, to="user@example.com", subject="Hi")

# Override queue and priority
job_id = await manager.enqueue(
    send_email,
    to="user@example.com",
    subject="Urgent",
    queue="critical",
    priority=Priority.CRITICAL,
)

# Delayed execution
job_id = await manager.enqueue(
    send_email,
    to="user@example.com",
    subject="Reminder",
    delay=3600.0,  # Run in 1 hour
)`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Job Query API</h3>
        <div className="space-y-4">
          <div>
            <code className="text-aquilia-500">async get_job(job_id: str) → Job | None</code>
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Retrieve job by ID. Returns <code>None</code> if not found.
            </p>
          </div>
          <div>
            <code className="text-aquilia-500">async list_jobs(queue: str | None, state: JobState | None, limit: int = 100, offset: int = 0) → list[Job]</code>
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              List jobs with optional filters.
            </p>
          </div>
          <div>
            <code className="text-aquilia-500">async cancel(job_id: str) → bool</code>
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Cancel a pending/running job. Returns <code>True</code> if cancelled.
            </p>
          </div>
          <div>
            <code className="text-aquilia-500">async retry_job(job_id: str) → bool</code>
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Manually retry a failed/dead job. Returns <code>True</code> if re-queued.
            </p>
          </div>
          <div>
            <code className="text-aquilia-500">async flush(queue: str | None = None) → int</code>
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Remove all jobs from a queue (or all queues). Returns count removed.
            </p>
          </div>
        </div>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Monitoring API</h3>
        <div className="space-y-4">
          <div>
            <code className="text-aquilia-500">async get_stats() → dict[str, Any]</code>
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Comprehensive statistics: total jobs, states, uptime, queue count, etc.
            </p>
          </div>
          <div>
            <code className="text-aquilia-500">async get_queue_stats() → dict[str, dict[str, int]]</code>
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Per-queue breakdown of job counts by state.
            </p>
          </div>
        </div>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Event Hooks</h3>
        <CodeBlock language="python">{`def on_complete(self, callback: Callable) → None
def on_failure(self, callback: Callable) → None
def on_dead_letter(self, callback: Callable) → None

# Example
def log_completion(job: Job):
    print(f"Job {job.id} completed: {job.result}")

manager.on_complete(log_completion)`}</CodeBlock>
      </section>

      {/* Priority Enum */}
      <section id="priority-enum" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <code className="text-aquilia-500">Priority</code> Enum
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Task priority levels. Lower integer value = higher priority.
        </p>
        <CodeBlock language="python">{`from enum import Enum

class Priority(int, Enum):
    CRITICAL = 0  # System alerts, security events
    HIGH = 1      # User-facing operations
    NORMAL = 2    # Standard background work (default)
    LOW = 3       # Maintenance, analytics, cleanup`}</CodeBlock>
      </section>

      {/* JobState Enum */}
      <section id="jobstate-enum" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <code className="text-aquilia-500">JobState</code> Enum
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Job lifecycle states.
        </p>
        <CodeBlock language="python">{`from enum import Enum

class JobState(str, Enum):
    PENDING = "pending"       # Queued, waiting for worker
    SCHEDULED = "scheduled"   # Delayed, waiting for scheduled_at
    RUNNING = "running"       # Currently executing
    COMPLETED = "completed"   # Finished successfully
    FAILED = "failed"         # Threw exception (may retry)
    RETRYING = "retrying"     # Scheduled for retry after backoff
    CANCELLED = "cancelled"   # Manually cancelled
    DEAD = "dead"             # Permanently failed (exhausted retries)`}</CodeBlock>
      </section>

      {/* Job & JobResult */}
      <section id="job---jobresult" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <code className="text-aquilia-500">Job</code> & <code className="text-aquilia-500">JobResult</code>
        </h2>
        
        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Job Dataclass</h3>
        <CodeBlock language="python">{`@dataclass
class Job:
    # Identity
    id: str
    name: str
    queue: str
    priority: Priority
    
    # Callable
    func_ref: str
    args: tuple
    kwargs: dict
    
    # State
    state: JobState
    result: JobResult | None
    
    # Retry policy
    max_retries: int
    retry_count: int
    retry_delay: float
    retry_backoff: float
    retry_max_delay: float
    
    # Timing
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    scheduled_at: datetime | None
    timeout: float
    
    # Metadata
    metadata: dict
    tags: list[str]
    
    # Properties
    @property
    def is_terminal(self) -> bool
    @property
    def can_retry(self) -> bool
    @property
    def next_retry_delay(self) -> float
    @property
    def duration_ms(self) -> float | None
    @property
    def fingerprint(self) -> str  # For deduplication`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>JobResult Dataclass</h3>
        <CodeBlock language="python">{`@dataclass
class JobResult:
    success: bool
    value: Any = None           # Return value if success
    error: str | None = None    # Error message if failure
    error_type: str | None = None
    traceback: str | None = None
    duration_ms: float = 0.0`}</CodeBlock>
      </section>

      {/* Schedule Helpers */}
      <section id="schedule-helpers--every--cron-" className="mb-16">
        <div className="flex items-center gap-2 mb-4">
          <Zap className="w-5 h-5 text-aquilia-500" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
            Schedule Helpers: <code className="text-aquilia-500">every()</code> & <code className="text-aquilia-500">cron()</code>
          </h2>
        </div>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>every()</h3>
        <CodeBlock language="python">{`def every(
    *,
    seconds: float = 0,
    minutes: float = 0,
    hours: float = 0,
    days: float = 0,
) -> IntervalSchedule

# Examples
every(seconds=30)
every(minutes=5)
every(hours=1)
every(hours=2, minutes=30)  # 2.5 hours`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>cron()</h3>
        <CodeBlock language="python">{`def cron(expression: str) -> CronSchedule

# Format: "minute hour day_of_month month day_of_week"
cron("*/5 * * * *")     # Every 5 minutes
cron("0 * * * *")       # Every hour at :00
cron("0 9 * * 1-5")     # 9 AM on weekdays
cron("0 0 1 * *")       # Midnight on 1st of month
cron("0 3 * * 0")       # 3 AM every Sunday`}</CodeBlock>
      </section>

      {/* Helper Functions */}
      <section id="get_registered_tasks--" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Helper Functions
        </h2>

        <div className="space-y-4">
          <div>
            <code className="text-aquilia-500">get_registered_tasks() → dict[str, _TaskDescriptor]</code>
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Returns all registered task descriptors (task_name → descriptor).
            </p>
          </div>
          <div>
            <code className="text-aquilia-500">get_task(name: str) → _TaskDescriptor | None</code>
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Look up a specific task by name.
            </p>
          </div>
          <div>
            <code className="text-aquilia-500">get_periodic_tasks() → dict[str, _TaskDescriptor]</code>
            <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Returns only tasks with a <code>schedule</code> set.
            </p>
          </div>
        </div>

        <CodeBlock language="python">{`from aquilia.tasks import get_registered_tasks, get_task, get_periodic_tasks

# List all tasks
all_tasks = get_registered_tasks()
for name, descriptor in all_tasks.items():
    print(f"{name}: queue={descriptor.queue}, priority={descriptor.priority}")

# Find a specific task
task = get_task("mymodule:send_email")
if task:
    print(f"Found: {task.task_name}")

# List periodic tasks
periodic = get_periodic_tasks()
for name, descriptor in periodic.items():
    print(f"{name}: {descriptor.schedule.human_readable}")`}</CodeBlock>
      </section>

      {/* Integration.tasks() */}
      <section id="integration-tasks--" className="mb-16">
        <div className="flex items-center gap-2 mb-4">
          <Database className="w-5 h-5 text-aquilia-500" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code className="text-aquilia-500">Integration.tasks()</code>
          </h2>
        </div>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Workspace configuration builder for the task subsystem.
        </p>

        <CodeBlock language="python">{`from aquilia.config_builders import Integration

Integration.tasks(
    backend: str = "memory",
    num_workers: int = 4,
    default_queue: str = "default",
    cleanup_interval: float = 300.0,
    cleanup_max_age: float = 3600.0,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    retry_backoff: float = 2.0,
    retry_max_delay: float = 300.0,
    default_timeout: float = 300.0,
    auto_start: bool = True,
    dead_letter_max: int = 1000,
    scheduler_tick: float = 15.0,  # Periodic check interval
) -> dict`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Usage in Workspace</h3>
        <CodeBlock language="python">{`# workspace.py
from aquilia import Workspace, Module
from aquilia.config_builders import Integration

workspace = (
    Workspace("myapp", version="1.0.0")
    .runtime(mode="dev", port=8000)
    .module(Module("core"))
    .integrate(Integration.tasks(
        num_workers=8,
        scheduler_tick=10.0,
        cleanup_interval=600.0,
    ))
)`}</CodeBlock>
      </section>

      {/* Faults */}
      <section id="faults" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Structured Faults
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          All task system errors use structured <code>Fault</code> classes from <code>aquilia.tasks.faults</code>.
        </p>

        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Fault</th>
                <th className="text-left py-3 pr-4">Code</th>
                <th className="text-left py-3">When Raised</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4"><code className="text-xs">TaskScheduleFault</code></td>
                <td className="py-3 pr-4"><code className="text-xs">TASK_SCHEDULE_INVALID</code></td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Invalid <code>every()</code> or <code>cron()</code> parameters</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code className="text-xs">TaskNotBoundFault</code></td>
                <td className="py-3 pr-4"><code className="text-xs">TASK_NOT_BOUND</code></td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}><code>.delay()</code> called before server started</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code className="text-xs">TaskEnqueueFault</code></td>
                <td className="py-3 pr-4"><code className="text-xs">TASK_ENQUEUE_INVALID</code></td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Invalid callable passed to <code>enqueue()</code></td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code className="text-xs">TaskResolutionFault</code></td>
                <td className="py-3 pr-4"><code className="text-xs">TASK_RESOLUTION_FAILED</code></td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Worker cannot resolve task from <code>func_ref</code></td>
              </tr>
            </tbody>
          </table>
        </div>

        <CodeBlock language="python">{`from aquilia.tasks.faults import TaskNotBoundFault

try:
    await my_task.delay()
except TaskNotBoundFault as e:
    print(f"Error: {e.message}")
    print(f"Code: {e.code}")
    print(f"Domain: {e.domain}")`}</CodeBlock>
      </section>

      {/* Complete Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Complete Example
        </h2>
        <CodeBlock language="python">{`# workspace.py
from aquilia import Workspace, Module
from aquilia.config_builders import Integration

workspace = (
    Workspace("myapp", version="1.0.0")
    .runtime(mode="dev", port=8000)
    .module(Module("core"))
    .integrate(Integration.tasks(num_workers=4, scheduler_tick=15.0))
)

# modules/core/tasks.py
from aquilia.tasks import task, Priority, every

@task(queue="emails", priority=Priority.HIGH, max_retries=5)
async def send_email(to: str, subject: str, body: str) -> dict:
    # Email logic
    return {"sent": True}

@task(schedule=every(minutes=5))
async def cleanup_sessions():
    # Runs every 5 minutes
    pass

# modules/core/controllers.py
from aquilia import Controller, POST, RequestCtx, Response
from .tasks import send_email

class EmailController(Controller):
    prefix = "/emails"
    
    @POST("/send")
    async def send(self, ctx: RequestCtx) -> Response:
        data = await ctx.json()
        
        # Enqueue task
        job_id = await send_email.delay(
            to=data["to"],
            subject=data["subject"],
            body=data["body"]
        )
        
        return Response.json({"job_id": job_id, "status": "queued"})`}</CodeBlock>
      </section>
    </div>
  )
}
