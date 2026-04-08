import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
// import { Link } from 'react-router-dom'
import { Clock } from 'lucide-react'

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
            API Reference
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Complete API documentation for the Tasks module. Every class, function, decorator, and type.
        </p>
      </div>

      {/* @task Decorator */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <code className="text-aquilia-500">@task</code>
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Register an async function as a background task with queue, priority, and retry configuration.
        </p>

        <CodeBlock language="python">{`def task(
    fn=None,
    *,
    name: str | None = None,              # Task name (default: module:qualname)
    queue: str = "default",               # Queue name for routing
    priority: Priority = Priority.NORMAL, # Execution priority
    max_retries: int = 3,                 # Max retry attempts on failure
    retry_delay: float = 1.0,             # Base retry delay in seconds
    retry_backoff: float = 2.0,           # Exponential backoff multiplier
    retry_max_delay: float = 300.0,       # Maximum retry delay cap (5 min)
    timeout: float = 300.0,               # Max execution time (5 min)
    tags: list[str] | None = None,        # Metadata tags for filtering
    schedule: Schedule | None = None,     # Periodic schedule (every/cron)
) -> _TaskDescriptor`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Parameters</h3>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Name</th>
                <th className="text-left py-3 pr-4">Type</th>
                <th className="text-left py-3 pr-4">Default</th>
                <th className="text-left py-3">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4"><code>name</code></td>
                <td className="py-3 pr-4"><code>str | None</code></td>
                <td className="py-3 pr-4"><code>None</code></td>
                <td>Task identifier. Defaults to <code>module:qualname</code>.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>queue</code></td>
                <td className="py-3 pr-4"><code>str</code></td>
                <td className="py-3 pr-4"><code>"default"</code></td>
                <td>Queue name for job routing. Workers poll specific queues.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>priority</code></td>
                <td className="py-3 pr-4"><code>Priority</code></td>
                <td className="py-3 pr-4"><code>NORMAL</code></td>
                <td>Job priority level (CRITICAL=0, HIGH=1, NORMAL=2, LOW=3).</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>max_retries</code></td>
                <td className="py-3 pr-4"><code>int</code></td>
                <td className="py-3 pr-4"><code>3</code></td>
                <td>Maximum number of retry attempts on failure.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>retry_delay</code></td>
                <td className="py-3 pr-4"><code>float</code></td>
                <td className="py-3 pr-4"><code>1.0</code></td>
                <td>Base retry delay in seconds before exponential backoff.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>retry_backoff</code></td>
                <td className="py-3 pr-4"><code>float</code></td>
                <td className="py-3 pr-4"><code>2.0</code></td>
                <td>Multiplier for exponential backoff. Delay = base × backoff^retry_count.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>retry_max_delay</code></td>
                <td className="py-3 pr-4"><code>float</code></td>
                <td className="py-3 pr-4"><code>300.0</code></td>
                <td>Maximum cap on retry delay (5 minutes default).</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>timeout</code></td>
                <td className="py-3 pr-4"><code>float</code></td>
                <td className="py-3 pr-4"><code>300.0</code></td>
                <td>Maximum execution time before the job is terminated.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>tags</code></td>
                <td className="py-3 pr-4"><code>list[str]</code></td>
                <td className="py-3 pr-4"><code>None</code></td>
                <td>Metadata tags for filtering and grouping tasks.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>schedule</code></td>
                <td className="py-3 pr-4"><code>Schedule</code></td>
                <td className="py-3 pr-4"><code>None</code></td>
                <td>Periodic schedule. Use <code>every()</code> or <code>cron()</code>.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Returns</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <code className="text-aquilia-500">_TaskDescriptor</code> — A wrapper object that provides <code>.delay()</code> and <code>.send()</code> methods for enqueueing jobs.
        </p>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Example</h3>
        <CodeBlock language="python">{`from aquilia.tasks import task, Priority, every

# Basic task
@task
async def simple_task():
    return "done"

# Configured task
@task(queue="emails", priority=Priority.HIGH, max_retries=5)
async def send_email(to: str, subject: str, body: str) -> bool:
    # Send email logic
    return True

# Periodic task (runs every hour)
@task(schedule=every(hours=1))
async def hourly_cleanup():
    # Cleanup logic
    pass`}</CodeBlock>
      </section>

      {/* _TaskDescriptor */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <code className="text-aquilia-500">_TaskDescriptor</code>
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Wrapper returned by <code>@task</code> decorator. Provides methods for enqueueing jobs.
        </p>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Methods</h3>

        <div className={`p-4 rounded-xl border mb-4 ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <h4 className={`font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>async delay(*args, **kwargs) → str</code>
          </h4>
          <p className={`text-sm mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Enqueue the task for background execution. Returns the job ID.
          </p>
          <CodeBlock language="python">{`job_id = await send_email.delay(
    to="user@example.com",
    subject="Welcome!",
    body="Hello, world!"
)
print(f"Enqueued job: {job_id}")`}</CodeBlock>
        </div>

        <div className={`p-4 rounded-xl border mb-4 ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <h4 className={`font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>async send(*args, **kwargs) → str</code>
          </h4>
          <p className={`text-sm mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Alias for <code>delay()</code>. Provided for compatibility with Dramatiq/Huey.
          </p>
        </div>

        <div className={`p-4 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <h4 className={`font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>async __call__(*args, **kwargs) → Any</code>
          </h4>
          <p className={`text-sm mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Direct invocation — executes the task immediately without queueing.
          </p>
          <CodeBlock language="python">{`# Execute immediately (bypasses queue)
result = await send_email(to="user@example.com", subject="Hi", body="Test")`}</CodeBlock>
        </div>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Properties</h3>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Property</th>
                <th className="text-left py-3 pr-4">Type</th>
                <th className="text-left py-3">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4"><code>task_name</code></td>
                <td className="py-3 pr-4"><code>str</code></td>
                <td>Unique task identifier.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>queue</code></td>
                <td className="py-3 pr-4"><code>str</code></td>
                <td>Queue name for job routing.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>priority</code></td>
                <td className="py-3 pr-4"><code>Priority</code></td>
                <td>Default priority for jobs.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>is_periodic</code></td>
                <td className="py-3 pr-4"><code>bool</code></td>
                <td><code>True</code> if the task has a schedule.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>func_ref</code></td>
                <td className="py-3 pr-4"><code>str</code></td>
                <td>Full function reference for serialization.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* TaskManager */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <code className="text-aquilia-500">TaskManager</code>
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Central coordinator for task execution. Manages workers, scheduler, and job lifecycle.
        </p>

        <CodeBlock language="python">{`class TaskManager:
    def __init__(
        self,
        backend: TaskBackend | None = None,  # Job storage (default: MemoryBackend)
        num_workers: int = 4,                # Number of worker coroutines
        queues: list[str] | None = None,     # Queues to process (default: ["default"])
        poll_interval: float = 1.0,          # Seconds between polls when idle
    ) -> None`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Methods</h3>

        <div className={`p-4 rounded-xl border mb-4 ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <h4 className={`font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>async start() → None</code>
          </h4>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Start workers and scheduler. Must be called before enqueueing jobs.
          </p>
        </div>

        <div className={`p-4 rounded-xl border mb-4 ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <h4 className={`font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>async shutdown(timeout: float = 10.0) → None</code>
          </h4>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Gracefully stop all workers. Waits for running jobs to complete up to timeout.
          </p>
        </div>

        <div className={`p-4 rounded-xl border mb-4 ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <h4 className={`font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>async enqueue(task, *args, **kwargs) → str</code>
          </h4>
          <p className={`text-sm mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Enqueue a task for background execution. Returns the job ID.
          </p>
          <CodeBlock language="python">{`manager = TaskManager()
await manager.start()

# Enqueue via manager
job_id = await manager.enqueue(send_email, to="user@example.com", subject="Hi")

# Or via task descriptor (preferred)
job_id = await send_email.delay(to="user@example.com", subject="Hi")`}</CodeBlock>
        </div>

        <div className={`p-4 rounded-xl border mb-4 ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <h4 className={`font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>async get_job(job_id: str) → Job | None</code>
          </h4>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Retrieve a job by ID. Returns <code>None</code> if not found.
          </p>
        </div>

        <div className={`p-4 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <h4 className={`font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>async cancel_job(job_id: str) → bool</code>
          </h4>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Cancel a pending job. Returns <code>True</code> if cancelled, <code>False</code> if already running or completed.
          </p>
        </div>
      </section>

      {/* Job */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <code className="text-aquilia-500">Job</code>
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Represents a single execution of a task. Tracks state, timing, retries, and results.
        </p>

        <CodeBlock language="python">{`@dataclass
class Job:
    id: str                         # Unique job ID (UUID hex[:16])
    name: str                       # Human-readable name
    queue: str = "default"          # Queue name
    priority: Priority = NORMAL     # Priority level
    
    func_ref: str = ""              # Task function reference
    args: tuple = ()                # Positional arguments
    kwargs: dict = {}               # Keyword arguments
    
    state: JobState = PENDING       # Current state
    result: JobResult | None = None # Execution result
    
    max_retries: int = 3            # Max retry attempts
    retry_count: int = 0            # Current retry count
    retry_delay: float = 1.0        # Base retry delay
    retry_backoff: float = 2.0      # Backoff multiplier
    retry_max_delay: float = 300.0  # Max delay cap
    
    created_at: datetime            # When created
    started_at: datetime | None     # When execution started
    completed_at: datetime | None   # When execution finished
    scheduled_at: datetime | None   # For delayed/scheduled tasks
    timeout: float = 300.0          # Max execution time
    
    metadata: dict = {}             # Custom metadata
    tags: list[str] = []            # Tags for filtering`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Properties</h3>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Property</th>
                <th className="text-left py-3 pr-4">Type</th>
                <th className="text-left py-3">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4"><code>is_terminal</code></td>
                <td className="py-3 pr-4"><code>bool</code></td>
                <td>True if in COMPLETED, FAILED, CANCELLED, or DEAD state.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>is_runnable</code></td>
                <td className="py-3 pr-4"><code>bool</code></td>
                <td>True if ready to execute (PENDING and past ETA).</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>can_retry</code></td>
                <td className="py-3 pr-4"><code>bool</code></td>
                <td>True if retry_count &lt; max_retries.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>next_retry_delay</code></td>
                <td className="py-3 pr-4"><code>float</code></td>
                <td>Calculated delay with exponential backoff + jitter.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>duration_ms</code></td>
                <td className="py-3 pr-4"><code>float | None</code></td>
                <td>Execution duration in milliseconds (if completed).</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>fingerprint</code></td>
                <td className="py-3 pr-4"><code>str</code></td>
                <td>Stable hash for deduplication (SHA256[:12]).</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Methods</h3>
        <div className={`p-4 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <h4 className={`font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>to_dict() → dict</code>
          </h4>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Serialize job to a dictionary for API/admin consumption.
          </p>
        </div>
      </section>

      {/* JobState */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <code className="text-aquilia-500">JobState</code>
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Enum representing job lifecycle states.
        </p>

        <CodeBlock language="python">{`class JobState(str, Enum):
    PENDING = "pending"       # Waiting in queue
    SCHEDULED = "scheduled"   # Delayed execution (has ETA)
    RUNNING = "running"       # Currently executing
    COMPLETED = "completed"   # Finished successfully
    FAILED = "failed"         # Execution failed (may retry)
    RETRYING = "retrying"     # Scheduled for retry
    CANCELLED = "cancelled"   # Explicitly cancelled
    DEAD = "dead"             # Exhausted all retries`}</CodeBlock>
      </section>

      {/* Priority */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <code className="text-aquilia-500">Priority</code>
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Enum representing job priority levels. Lower value = higher priority.
        </p>

        <CodeBlock language="python">{`class Priority(int, Enum):
    CRITICAL = 0  # Highest priority
    HIGH = 1
    NORMAL = 2    # Default
    LOW = 3       # Lowest priority`}</CodeBlock>
      </section>

      {/* Scheduling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Scheduling Helpers
        </h2>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          <code className="text-aquilia-500">every()</code>
        </h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Create an interval schedule for periodic task execution.
        </p>
        <CodeBlock language="python">{`def every(
    seconds: int = 0,
    minutes: int = 0,
    hours: int = 0,
    days: int = 0,
) -> IntervalSchedule`}</CodeBlock>

        <CodeBlock language="python">{`from aquilia.tasks import task, every

@task(schedule=every(minutes=5))
async def check_health():
    pass

@task(schedule=every(hours=1, minutes=30))
async def report():
    pass`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          <code className="text-aquilia-500">cron()</code>
        </h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Create a cron schedule for precise periodic execution.
        </p>
        <CodeBlock language="python">{`def cron(expression: str) -> CronSchedule`}</CodeBlock>

        <p className={`mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Format: <code>minute hour day_of_month month day_of_week</code>
        </p>
        <CodeBlock language="python">{`from aquilia.tasks import task, cron

@task(schedule=cron("0 9 * * 1-5"))  # 9 AM on weekdays
async def morning_digest():
    pass

@task(schedule=cron("*/15 * * * *"))  # Every 15 minutes
async def frequent_check():
    pass

@task(schedule=cron("0 0 1 * *"))  # Midnight on 1st of month
async def monthly_report():
    pass`}</CodeBlock>
      </section>

      {/* Faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Fault Types
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Structured fault classes for task-related errors.
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
                <td className="py-3 pr-4"><code>TaskFault</code></td>
                <td className="py-3 pr-4"><code>TASK_ERROR</code></td>
                <td>Base class for all task errors.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>TaskNotBoundFault</code></td>
                <td className="py-3 pr-4"><code>TASK_NOT_BOUND</code></td>
                <td>Calling <code>.delay()</code> before TaskManager is started.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>TaskEnqueueFault</code></td>
                <td className="py-3 pr-4"><code>TASK_ENQUEUE_ERROR</code></td>
                <td>Failed to enqueue a job to the backend.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>TaskResolutionFault</code></td>
                <td className="py-3 pr-4"><code>TASK_RESOLUTION_ERROR</code></td>
                <td>Task not found in registry during execution.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>TaskScheduleFault</code></td>
                <td className="py-3 pr-4"><code>TASK_SCHEDULE_ERROR</code></td>
                <td>Invalid schedule configuration.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Example</h3>
        <CodeBlock language="python">{`from aquilia.tasks import TaskNotBoundFault

try:
    await send_email.delay(to="user@example.com", subject="Hi")
except TaskNotBoundFault as e:
    print(f"TaskManager not started: {e.message}")
    # e.code == "TASK_NOT_BOUND"
    # e.metadata["task_name"] contains the task name`}</CodeBlock>
      </section>

      {/* Registry Functions */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Registry Functions
        </h2>

        <div className={`p-4 rounded-xl border mb-4 ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <h4 className={`font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>get_registered_tasks() → dict[str, _TaskDescriptor]</code>
          </h4>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Return all registered task descriptors.
          </p>
        </div>

        <div className={`p-4 rounded-xl border mb-4 ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <h4 className={`font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>get_task(name: str) → _TaskDescriptor | None</code>
          </h4>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Look up a registered task by name.
          </p>
        </div>

        <div className={`p-4 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <h4 className={`font-mono font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
            <code>get_periodic_tasks() → dict[str, _TaskDescriptor]</code>
          </h4>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Return only tasks with a periodic schedule.
          </p>
        </div>
      </section>
    </div>
  )
}
