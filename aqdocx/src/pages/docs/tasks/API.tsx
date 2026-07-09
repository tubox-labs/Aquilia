import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Code2, BookOpen, Layers, Terminal } from 'lucide-react'

export function TasksAPI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <BookOpen className="w-4 h-4 animate-pulse" />
          Background Tasks / API Reference
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Tasks API Reference
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Complete interface specifications for background task decorators, coordinates, workers, and schedulers, compiled from the actual implementation in <code className="text-aquilia-500">aquilia/tasks/</code>.
        </p>
      </div>

      {/* Table of Contents */}
      <section className="mb-16">
        <div className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 p-6 backdrop-blur-sm shadow-xl">
          <div className="absolute top-0 bottom-0 left-0 w-1 bg-gradient-to-b from-aquilia-500 to-transparent opacity-50" />
          <h3 className={`font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Table of Contents</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-sm">
            {[
              { name: '@task Decorator', hash: 'task-decorator' },
              { name: 'TaskManager Class', hash: 'taskmanager-class' },
              { name: 'Job Dataclass', hash: 'job-dataclass' },
              { name: 'JobResult Dataclass', hash: 'jobresult-dataclass' },
              { name: 'Priority Enum', hash: 'priority-enum' },
              { name: 'JobState Enum', hash: 'jobstate-enum' },
              { name: 'Schedule Helpers', hash: 'schedule-helpers' },
              { name: 'Task Registry Queries', hash: 'registry-queries' },
              { name: 'Integration Builder', hash: 'integration-builder' },
              { name: 'Structured Faults', hash: 'structured-faults' },
            ].map((item, i) => (
              <a key={i} href={`#${item.hash}`} className="text-aquilia-500 hover:text-aquilia-400 font-medium hover:underline flex items-center gap-1.5">
                <span className="text-aquilia-500/50">•</span> {item.name}
              </a>
            ))}
          </div>
        </div>
      </section>

      {/* @task Decorator */}
      <section id="task-decorator" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Code2 className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="tasks.task">@task</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Decorator to register an async function as a background task. Can be used with or without parentheses.
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
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500 w-32">Parameter</th>
                <th className="text-left py-4 px-6">Type</th>
                <th className="text-left py-4 px-6">Default</th>
                <th className="text-left py-4 px-6">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['name', 'str | None', 'None', 'Unique name for task. Auto-generated as module:qualname if None.'],
                ['queue', 'str', '"default"', 'Queue name for job routing.'],
                ['priority', 'Priority', 'Priority.NORMAL', 'Priority level.'],
                ['max_retries', 'int', '3', 'Maximum retries before marking task as DEAD.'],
                ['retry_delay', 'float', '1.0', 'Base delay in seconds between retries.'],
                ['retry_backoff', 'float', '2.0', 'Exponential backoff multiplier.'],
                ['retry_max_delay', 'float', '300.0', 'Maximum retry delay ceiling (5 minutes).'],
                ['timeout', 'float', '300.0', 'Maximum execution time in seconds.'],
                ['tags', 'list[str] | None', 'None', 'Metadata tags for query filtering.'],
                ['schedule', 'Schedule | None', 'None', 'Periodic schedule config (every or cron).'],
              ].map(([param, type, defVal, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono font-semibold text-xs text-aquilia-400">{param}</td>
                  <td className="py-3.5 px-6 font-mono text-xs">{type}</td>
                  <td className="py-3.5 px-6 font-mono text-xs">{defVal}</td>
                  <td className={`py-3.5 px-6 ${subtleText}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* TaskManager */}
      <section id="taskmanager-class" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="tasks.TaskManager">TaskManager</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Central coordinator for creating, routing, enqueuing, and querying background tasks.
        </p>

        <CodeBlock language="python">{`class TaskManager:
    def __init__(
        self,
        *,
        backend: TaskBackend | None = None,   # MemoryBackend() by default
        num_workers: int = 4,
        default_queue: str = "default",
        cleanup_interval: float = 300.0,      # Seconds between cleanup runs
        cleanup_max_age: float = 3600.0,      # Job TTL after termination
        scheduler_tick: float = 15.0,         # Scheduler tick frequency
    ) -> None

    async def start(self) -> None:
        """Start worker threads, cleanup loops, and scheduled task loops."""

    async def stop(self, timeout: float = 10.0) -> None:
        """Gracefully stop all worker tasks and loops, waiting up to timeout."""

    async def enqueue(
        self,
        func: Callable | _TaskDescriptor,
        *args: Any,
        queue: str | None = None,
        priority: Priority | None = None,
        delay: float | None = None,            # Delay execution in seconds
        max_retries: int | None = None,
        timeout: float | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> str:
        """Enqueue task and return job ID string."""

    async def get_job(self, job_id: str) -> Job | None:
        """Retrieve job dataclass by ID."""

    async def list_jobs(
        self,
        *,
        queue: str | None = None,
        state: JobState | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs matching filters, ordered created_at DESC."""

    async def cancel(self, job_id: str) -> bool:
        """Cancel a pending/running job. Returns True if successful."""

    async def retry_job(self, job_id: str) -> bool:
        """Manually force-retry a failed/dead/cancelled job."""

    async def flush(self, queue: str | None = None) -> int:
        """Clear all tasks (or filtered by queue). Returns number of cleared jobs."""

    async def get_stats(self) -> dict[str, Any]:
        """Return comprehensive TaskManager metrics, uptime, and Chart.js datasets."""`}</CodeBlock>
      </section>

      {/* Job Dataclass */}
      <section id="job-dataclass" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="tasks.Job">Job</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Dataclass representing the immutable job configuration and mutable execution state.
        </p>

        <CodeBlock language="python">{`@dataclass
class Job:
    id: str                                  # Hexadecimal UUID prefix (16 chars)
    name: str                                # Human readable task name
    queue: str = "default"
    priority: Priority = Priority.NORMAL
    func_ref: str = ""                       # module:qualname path
    args: tuple[Any, ...] = ()
    kwargs: dict[str, Any] = field(default_factory=dict)
    state: JobState = JobState.PENDING
    result: JobResult | None = None
    max_retries: int = 3
    retry_count: int = 0
    created_at: datetime = datetime.now(timezone.utc)
    started_at: datetime | None = None
    completed_at: datetime | None = None
    scheduled_at: datetime | None = None    # Set when executing with delay
    timeout: float = 300.0
    metadata: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)

    @property
    def is_terminal(self) -> bool:
        """Returns True if state is COMPLETED, FAILED, CANCELLED, or DEAD."""

    @property
    def is_runnable(self) -> bool:
        """Returns True if job is pending/scheduled and scheduled_at has passed."""

    @property
    def next_retry_delay(self) -> float:
        """Computes next backoff delay with exponential backoff and random jitter."""

    @property
    def can_retry(self) -> bool:
        """Returns True if retry_count < max_retries."""

    @property
    def duration_ms(self) -> float | None:
        """Duration of job execution in milliseconds."""

    @property
    def fingerprint(self) -> str:
        """SHA-256 fingerprint for enqueued parameter deduplication."""`}</CodeBlock>
      </section>

      {/* JobResult Dataclass */}
      <section id="jobresult-dataclass" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          JobResult
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Container representing task execution outcomes, exceptions, and execution metrics.
        </p>

        <CodeBlock language="python">{`@dataclass
class JobResult:
    success: bool
    value: Any = None                        # Return value (converted to repr() string on dict serialization)
    error: str | None = None                 # Exception message
    error_type: str | None = None           # Name of Exception class
    traceback: str | None = None            # Formatted traceback string
    duration_ms: float = 0.0                 # Millisecond execution time`}</CodeBlock>
      </section>

      {/* Priority Enum */}
      <section id="priority-enum" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          <DocTerm id="tasks.Priority">Priority</DocTerm>
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Integer enumeration specifying job urgency. Lower values represent higher priority.
        </p>
        <CodeBlock language="python">{`class Priority(int, Enum):
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3`}</CodeBlock>
      </section>

      {/* JobState Enum */}
      <section id="jobstate-enum" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          JobState
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Lifecycle states for a task job.
        </p>
        <CodeBlock language="python">{`class JobState(str, Enum):
    PENDING = "pending"          # Waiting in queue
    SCHEDULED = "scheduled"      # Waiting for delayed timestamp
    RUNNING = "running"          # Undergoing worker processing
    COMPLETED = "completed"      # Executed successfully
    FAILED = "failed"            # Failed, pending retry
    RETRYING = "retrying"        # Rescheduled for retry
    CANCELLED = "cancelled"      # Terminated by admin action
    DEAD = "dead"                # Exhausted all retries (sent to dead letter)`}</CodeBlock>
      </section>

      {/* Schedule Helpers */}
      <section id="schedule-helpers" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          Schedule Helpers
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Helper methods to generate periodic task schedules for the scheduler loop.
        </p>

        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-semibold mb-2"><DocTerm id="tasks.every">every()</DocTerm></h3>
            <CodeBlock language="python">{`def every(
    *,
    seconds: float = 0,
    minutes: float = 0,
    hours: float = 0,
    days: float = 0,
) -> IntervalSchedule`}</CodeBlock>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-2"><DocTerm id="tasks.cron">cron()</DocTerm></h3>
            <CodeBlock language="python">{`def cron(expression: str) -> CronSchedule`}</CodeBlock>
            <p className={`text-xs mt-2 ${subtleText}`}>
              Accepts standard 5-field cron syntax: <code className="text-aquilia-500">"minute hour dom month dow"</code>.
            </p>
          </div>
        </div>
      </section>

      {/* Task Registry Queries */}
      <section id="registry-queries" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          Registry Queries
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Access internally mapped tasks registered via decorators.
        </p>
        <CodeBlock language="python">{`def get_registered_tasks() -> dict[str, _TaskDescriptor]:
    """Retrieve mapping of all task names to their descriptors."""

def get_periodic_tasks() -> dict[str, _TaskDescriptor]:
    """Retrieve mapping of only scheduled/periodic tasks."""

def get_task(name: str) -> _TaskDescriptor | None:
    """Look up a task descriptor by its registered name."""`}</CodeBlock>
      </section>

      {/* Integration Builder */}
      <section id="integration-builder" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          Integration Builder Option
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Configures background tasks at the workspace level.
        </p>
        <CodeBlock language="python">{`# from aquilia.integrations import Integration
@staticmethod
def tasks(
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
    scheduler_tick: float = 15.0,
    enabled: bool = True,
) -> dict[str, Any]`}</CodeBlock>
      </section>

      {/* Structured Faults */}
      <section id="structured-faults" className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Terminal className="w-5 h-5 text-aquilia-500" />
          Structured Faults
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Specific errors raised by the tasks subsystem under the <code className="text-aquilia-500">"tasks"</code> fault domain.
        </p>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500">Fault</th>
                <th className="text-left py-4 px-6">Triggers</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['TaskFault', 'Base class for all background task failures.'],
                ['TaskScheduleFault', 'Raised when interval <= 0 or cron expression lacks exactly 5 fields.'],
                ['TaskNotBoundFault', 'Raised when calling .delay() before a TaskManager is bound (startup lifecycle not run).'],
                ['TaskEnqueueFault', 'Raised when trying to enqueue a non-callable object.'],
                ['TaskResolutionFault', 'Raised when workers cannot find task in registry (e.g., deleted code/import issues).'],
              ].map(([fault, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-xs font-semibold text-aquilia-400">{fault}</td>
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
