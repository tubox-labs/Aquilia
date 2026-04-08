import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Clock, RefreshCw, AlertTriangle } from 'lucide-react'

export function TasksRetry() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Clock className="w-4 h-4" />
          Tasks / Retry Logic
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Retry Logic & Error Handling
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          How failed tasks are retried with exponential backoff, jitter, and configurable retry policies.
        </p>
      </div>

      {/* How Retry Works */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          How Retry Works
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          When a task raises an exception, the worker checks if the job can be retried:
        </p>

        <div className={`p-6 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <ol className={`list-decimal list-inside space-y-3 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <li><strong>Exception caught</strong> — Worker catches the exception from task execution</li>
            <li><strong>Retry check</strong> — If <code>retry_count &lt; max_retries</code>, the job can retry</li>
            <li><strong>Calculate delay</strong> — Exponential backoff with jitter is computed</li>
            <li><strong>State update</strong> — Job state becomes <code>RETRYING</code></li>
            <li><strong>Re-enqueue</strong> — Job is pushed back with <code>scheduled_at = now + delay</code></li>
            <li><strong>Wait</strong> — Workers skip jobs with future <code>scheduled_at</code></li>
            <li><strong>Execute</strong> — Job runs again when <code>scheduled_at</code> passes</li>
          </ol>
        </div>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          State Transitions
        </h3>
        <div className="overflow-x-auto">
          <svg viewBox="0 0 600 180" className="w-full max-w-2xl h-auto">
            <defs>
              <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
                <polygon points="0 0, 10 3.5, 0 7" fill="#22c55e" />
              </marker>
            </defs>
            
            {/* Nodes */}
            <rect x="20" y="70" width="90" height="40" rx="8" fill={isDark ? '#1a1a2e' : '#dbeafe'} stroke="#3b82f6" strokeWidth="2" />
            <text x="65" y="95" textAnchor="middle" fill="#3b82f6" fontSize="12" fontWeight="600">RUNNING</text>
            
            <rect x="160" y="70" width="90" height="40" rx="8" fill={isDark ? '#1a1a2e' : '#fee2e2'} stroke="#ef4444" strokeWidth="2" />
            <text x="205" y="95" textAnchor="middle" fill="#ef4444" fontSize="12" fontWeight="600">FAILED</text>
            
            <rect x="300" y="70" width="90" height="40" rx="8" fill={isDark ? '#1a1a2e' : '#f3e8ff'} stroke="#8b5cf6" strokeWidth="2" />
            <text x="345" y="95" textAnchor="middle" fill="#8b5cf6" fontSize="12" fontWeight="600">RETRYING</text>
            
            <rect x="440" y="70" width="90" height="40" rx="8" fill={isDark ? '#1a1a2e' : '#dbeafe'} stroke="#3b82f6" strokeWidth="2" />
            <text x="485" y="95" textAnchor="middle" fill="#3b82f6" fontSize="12" fontWeight="600">PENDING</text>
            
            <rect x="300" y="140" width="90" height="40" rx="8" fill={isDark ? '#1a1a2e' : '#f3f4f6'} stroke="#6b7280" strokeWidth="2" />
            <text x="345" y="165" textAnchor="middle" fill="#6b7280" fontSize="12" fontWeight="600">DEAD</text>
            
            {/* Arrows */}
            <line x1="110" y1="90" x2="155" y2="90" stroke="#22c55e" strokeWidth="2" markerEnd="url(#arrowhead)" />
            <text x="132" y="82" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="9">exception</text>
            
            <line x1="250" y1="90" x2="295" y2="90" stroke="#22c55e" strokeWidth="2" markerEnd="url(#arrowhead)" />
            <text x="272" y="82" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="9">can_retry</text>
            
            <line x1="390" y1="90" x2="435" y2="90" stroke="#22c55e" strokeWidth="2" markerEnd="url(#arrowhead)" />
            <text x="412" y="82" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="9">backoff</text>
            
            <line x1="345" y1="115" x2="345" y2="135" stroke="#ef4444" strokeWidth="2" markerEnd="url(#arrowhead)" />
            <text x="380" y="128" fill={isDark ? '#888' : '#6b7280'} fontSize="9">exhausted</text>
          </svg>
        </div>
      </section>

      {/* Backoff Calculation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Backoff Calculation
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The retry delay uses exponential backoff with jitter to prevent thundering herd:
        </p>

        <CodeBlock language="python">{`# From aquilia/tasks/job.py
@property
def next_retry_delay(self) -> float:
    """Calculate next retry delay with exponential backoff + jitter."""
    import random
    
    # Exponential backoff
    delay = self.retry_delay * (self.retry_backoff ** self.retry_count)
    
    # Cap at maximum
    delay = min(delay, self.retry_max_delay)
    
    # Add jitter (±25%)
    jitter = delay * 0.25 * (2 * random.random() - 1)
    
    return max(0.1, delay + jitter)`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Example: Default Parameters
        </h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          With <code>retry_delay=1.0</code>, <code>retry_backoff=2.0</code>, <code>retry_max_delay=300.0</code>:
        </p>

        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Retry</th>
                <th className="text-left py-3 pr-4">Formula</th>
                <th className="text-left py-3 pr-4">Base</th>
                <th className="text-left py-3">With Jitter</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4">1</td>
                <td className="py-3 pr-4"><code>1 × 2⁰</code></td>
                <td className="py-3 pr-4">1s</td>
                <td>0.75 – 1.25s</td>
              </tr>
              <tr>
                <td className="py-3 pr-4">2</td>
                <td className="py-3 pr-4"><code>1 × 2¹</code></td>
                <td className="py-3 pr-4">2s</td>
                <td>1.5 – 2.5s</td>
              </tr>
              <tr>
                <td className="py-3 pr-4">3</td>
                <td className="py-3 pr-4"><code>1 × 2²</code></td>
                <td className="py-3 pr-4">4s</td>
                <td>3 – 5s</td>
              </tr>
              <tr>
                <td className="py-3 pr-4">4</td>
                <td className="py-3 pr-4"><code>1 × 2³</code></td>
                <td className="py-3 pr-4">8s</td>
                <td>6 – 10s</td>
              </tr>
              <tr>
                <td className="py-3 pr-4">5</td>
                <td className="py-3 pr-4"><code>1 × 2⁴</code></td>
                <td className="py-3 pr-4">16s</td>
                <td>12 – 20s</td>
              </tr>
              <tr>
                <td className="py-3 pr-4">10</td>
                <td className="py-3 pr-4"><code>1 × 2⁹</code></td>
                <td className="py-3 pr-4">512s → 300s (capped)</td>
                <td>225 – 375s</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Configuring Retry Behavior
        </h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Aggressive Retries (Fast Recovery)
        </h3>
        <CodeBlock language="python">{`@task(
    max_retries=10,          # More attempts
    retry_delay=0.5,         # Start faster
    retry_backoff=1.5,       # Slower growth
    retry_max_delay=60.0,    # Cap at 1 minute
)
async def fast_recovery_task():
    # Retries: 0.5s, 0.75s, 1.1s, 1.7s, 2.5s, 3.8s, 5.7s, 8.5s, 12.8s, 19.2s
    pass`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Conservative Retries (Slow Recovery)
        </h3>
        <CodeBlock language="python">{`@task(
    max_retries=3,           # Few attempts
    retry_delay=30.0,        # Start slow
    retry_backoff=3.0,       # Aggressive growth
    retry_max_delay=3600.0,  # Cap at 1 hour
)
async def slow_recovery_task():
    # Retries: 30s, 90s, 270s
    pass`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          No Retries
        </h3>
        <CodeBlock language="python">{`@task(max_retries=0)
async def one_shot_task():
    # Never retried — goes straight to DEAD on failure
    pass`}</CodeBlock>
      </section>

      {/* Error Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Error Handling in Tasks
        </h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          All Exceptions Trigger Retry
        </h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          By default, any exception causes the job to be retried (if retries remain):
        </p>
        <CodeBlock language="python">{`@task(max_retries=3)
async def risky_task():
    if random.random() < 0.5:
        raise ValueError("Random failure")
    return "success"
    
# ValueError will trigger retry, job state → RETRYING`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Permanent Failures (Skip Retry)
        </h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Raise <code>TaskPermanentFailure</code> to skip retries and go straight to DEAD:
        </p>
        <CodeBlock language="python">{`from aquilia.tasks import task
from aquilia.tasks.faults import TaskPermanentFailure

@task(max_retries=5)
async def validate_and_process(data: dict):
    if "user_id" not in data:
        # Retrying won't help — data is invalid
        raise TaskPermanentFailure("Missing required field: user_id")
    
    # This might work on retry
    result = await external_api.call(data)
    return result`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Manual Retry Control
        </h3>
        <CodeBlock language="python">{`@task(max_retries=5)
async def smart_task():
    try:
        result = await flaky_operation()
        return result
    except TransientError:
        # Let the framework handle retry
        raise
    except PermanentError as e:
        # Don't retry — mark as permanently failed
        raise TaskPermanentFailure(str(e)) from e
    except Exception as e:
        # Log unexpected errors, still retry
        logger.exception("Unexpected error in smart_task")
        raise`}</CodeBlock>
      </section>

      {/* JobResult */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Job Results
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          After execution, the job's <code>result</code> field contains a <code>JobResult</code>:
        </p>

        <CodeBlock language="python">{`@dataclass
class JobResult:
    success: bool              # True if completed without exception
    value: Any = None          # Return value (on success)
    error: str | None = None   # Error message (on failure)
    error_type: str | None     # Exception class name
    traceback: str | None      # Full traceback string
    duration_ms: float = 0.0   # Execution time`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Accessing Results
        </h3>
        <CodeBlock language="python">{`job_id = await send_email.delay(to="user@example.com", subject="Hi")

# Later...
job = await manager.get_job(job_id)

if job.state == JobState.COMPLETED:
    print(f"Success! Result: {job.result.value}")
    print(f"Duration: {job.result.duration_ms}ms")
elif job.state == JobState.DEAD:
    print(f"Failed permanently: {job.result.error}")
    print(f"Exception: {job.result.error_type}")
    print(f"Traceback:\\n{job.result.traceback}")`}</CodeBlock>
      </section>

      {/* Dead Letter Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Dead Letter Handling
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Jobs that exhaust all retries enter the <code>DEAD</code> state. Handle dead jobs:
        </p>

        <CodeBlock language="python">{`# Query dead jobs
from aquilia.tasks import JobState

dead_jobs = await manager.get_jobs_by_state(JobState.DEAD)

for job in dead_jobs:
    print(f"Dead job: {job.id}")
    print(f"  Task: {job.func_ref}")
    print(f"  Error: {job.result.error}")
    print(f"  Retries: {job.retry_count}/{job.max_retries}")
    
    # Option 1: Manually re-enqueue
    if should_retry(job):
        job.retry_count = 0
        job.state = JobState.PENDING
        await manager.backend.push(job)
    
    # Option 2: Archive to dead letter storage
    await dead_letter_store.save(job.to_dict())
    await manager.backend.delete(job.id)
    
    # Option 3: Alert operations team
    await alert_ops(f"Dead job: {job.id} - {job.result.error}")`}</CodeBlock>
      </section>

      {/* Best Practices */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Best Practices
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            {
              icon: <RefreshCw className="w-5 h-5 text-aquilia-400" />,
              title: 'Idempotent Tasks',
              desc: 'Tasks should be safe to run multiple times. Use idempotency keys for external operations.',
            },
            {
              icon: <AlertTriangle className="w-5 h-5 text-amber-400" />,
              title: 'Distinguish Failure Types',
              desc: 'Use TaskPermanentFailure for validation errors. Let transient errors retry naturally.',
            },
            {
              icon: <Clock className="w-5 h-5 text-blue-400" />,
              title: 'Set Reasonable Timeouts',
              desc: 'Configure timeout per task. Long-running tasks should be broken into smaller steps.',
            },
            {
              icon: <RefreshCw className="w-5 h-5 text-purple-400" />,
              title: 'Monitor Dead Jobs',
              desc: 'Set up alerts for jobs entering DEAD state. Review and fix root causes.',
            },
          ].map((item, i) => (
            <div key={i} className={`p-5 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-white border-gray-200'}`}>
              <div className="flex items-center gap-3 mb-3">
                {item.icon}
                <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h3>
              </div>
              <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>
    </div>
  )
}
