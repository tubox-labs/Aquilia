import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Clock } from 'lucide-react'

export function TasksConfiguration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Clock className="w-4 h-4" />
          Tasks / Configuration
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Configuration
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Complete configuration reference for the Tasks module. Every setting, default, and environment variable.
        </p>
      </div>

      {/* TaskManager Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          TaskManager Configuration
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Configuration is passed to the <code className="text-aquilia-500">TaskManager</code> constructor.
        </p>

        <div className="overflow-x-auto mb-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Parameter</th>
                <th className="text-left py-3 pr-4">Type</th>
                <th className="text-left py-3 pr-4">Default</th>
                <th className="text-left py-3">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4"><code>backend</code></td>
                <td className="py-3 pr-4"><code>TaskBackend</code></td>
                <td className="py-3 pr-4"><code>MemoryBackend()</code></td>
                <td>Job storage backend. Default is in-memory heap-based queue.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>num_workers</code></td>
                <td className="py-3 pr-4"><code>int</code></td>
                <td className="py-3 pr-4"><code>4</code></td>
                <td>Number of worker coroutines to spawn.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>queues</code></td>
                <td className="py-3 pr-4"><code>list[str]</code></td>
                <td className="py-3 pr-4"><code>["default"]</code></td>
                <td>List of queue names to process.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>poll_interval</code></td>
                <td className="py-3 pr-4"><code>float</code></td>
                <td className="py-3 pr-4"><code>1.0</code></td>
                <td>Seconds between polls when queues are empty.</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Minimal Configuration</h3>
        <CodeBlock language="python">{`from aquilia.tasks import TaskManager

# Uses all defaults
manager = TaskManager()
await manager.start()`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Full Configuration</h3>
        <CodeBlock language="python">{`from aquilia.tasks import TaskManager, MemoryBackend

manager = TaskManager(
    backend=MemoryBackend(),
    num_workers=8,
    queues=["default", "emails", "notifications", "analytics"],
    poll_interval=0.5,
)
await manager.start()`}</CodeBlock>
      </section>

      {/* Task Decorator Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Task Decorator Configuration
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Per-task configuration via the <code className="text-aquilia-500">@task</code> decorator.
        </p>

        <div className="overflow-x-auto mb-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Parameter</th>
                <th className="text-left py-3 pr-4">Type</th>
                <th className="text-left py-3 pr-4">Default</th>
                <th className="text-left py-3">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4"><code>name</code></td>
                <td className="py-3 pr-4"><code>str | None</code></td>
                <td className="py-3 pr-4"><code>module:qualname</code></td>
                <td>Task identifier. Auto-generated from function name if not provided.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>queue</code></td>
                <td className="py-3 pr-4"><code>str</code></td>
                <td className="py-3 pr-4"><code>"default"</code></td>
                <td>Queue name for job routing.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>priority</code></td>
                <td className="py-3 pr-4"><code>Priority</code></td>
                <td className="py-3 pr-4"><code>NORMAL</code></td>
                <td>Job priority (CRITICAL=0, HIGH=1, NORMAL=2, LOW=3).</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>max_retries</code></td>
                <td className="py-3 pr-4"><code>int</code></td>
                <td className="py-3 pr-4"><code>3</code></td>
                <td>Maximum retry attempts on failure.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>retry_delay</code></td>
                <td className="py-3 pr-4"><code>float</code></td>
                <td className="py-3 pr-4"><code>1.0</code></td>
                <td>Base retry delay in seconds.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>retry_backoff</code></td>
                <td className="py-3 pr-4"><code>float</code></td>
                <td className="py-3 pr-4"><code>2.0</code></td>
                <td>Exponential backoff multiplier.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>retry_max_delay</code></td>
                <td className="py-3 pr-4"><code>float</code></td>
                <td className="py-3 pr-4"><code>300.0</code></td>
                <td>Maximum retry delay cap (5 minutes).</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>timeout</code></td>
                <td className="py-3 pr-4"><code>float</code></td>
                <td className="py-3 pr-4"><code>300.0</code></td>
                <td>Maximum execution time in seconds.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>tags</code></td>
                <td className="py-3 pr-4"><code>list[str]</code></td>
                <td className="py-3 pr-4"><code>[]</code></td>
                <td>Metadata tags for filtering.</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>schedule</code></td>
                <td className="py-3 pr-4"><code>Schedule</code></td>
                <td className="py-3 pr-4"><code>None</code></td>
                <td>Periodic schedule (every() or cron()).</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>Example: High-Reliability Email Task</h3>
        <CodeBlock language="python">{`from aquilia.tasks import task, Priority

@task(
    name="email.send",           # Explicit name
    queue="emails",              # Dedicated queue
    priority=Priority.HIGH,      # Higher priority
    max_retries=5,               # More retries
    retry_delay=2.0,             # Longer initial delay
    retry_backoff=3.0,           # More aggressive backoff
    retry_max_delay=600.0,       # 10 minute cap
    timeout=120.0,               # 2 minute timeout
    tags=["email", "critical"],  # Metadata
)
async def send_email(to: str, subject: str, body: str) -> bool:
    # Email sending logic
    return True`}</CodeBlock>
      </section>

      {/* Retry Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Retry Behavior
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The retry delay is calculated using exponential backoff with jitter:
        </p>

        <CodeBlock language="python">{`# Backoff formula
delay = min(retry_delay * (retry_backoff ** retry_count), retry_max_delay)
delay = delay * (1.0 + random.uniform(-0.25, 0.25))  # ±25% jitter`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Example: Default Settings
        </h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          With <code>retry_delay=1.0</code>, <code>retry_backoff=2.0</code>, <code>retry_max_delay=300.0</code>:
        </p>

        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Retry #</th>
                <th className="text-left py-3 pr-4">Base Delay</th>
                <th className="text-left py-3">With Jitter (±25%)</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4">1</td>
                <td className="py-3 pr-4">1 second</td>
                <td>0.75 – 1.25 seconds</td>
              </tr>
              <tr>
                <td className="py-3 pr-4">2</td>
                <td className="py-3 pr-4">2 seconds</td>
                <td>1.5 – 2.5 seconds</td>
              </tr>
              <tr>
                <td className="py-3 pr-4">3</td>
                <td className="py-3 pr-4">4 seconds</td>
                <td>3.0 – 5.0 seconds</td>
              </tr>
              <tr>
                <td className="py-3 pr-4">4</td>
                <td className="py-3 pr-4">8 seconds</td>
                <td>6.0 – 10.0 seconds</td>
              </tr>
              <tr>
                <td className="py-3 pr-4">5</td>
                <td className="py-3 pr-4">16 seconds</td>
                <td>12.0 – 20.0 seconds</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Queue Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Queue Configuration
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Queues are logical partitions for organizing tasks. Workers process specific queues.
        </p>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Multiple Queue Workers
        </h3>
        <CodeBlock language="python">{`# Process all queues
manager = TaskManager(
    num_workers=8,
    queues=["default", "emails", "notifications"],
)

# Or run dedicated workers per queue
email_manager = TaskManager(num_workers=4, queues=["emails"])
notification_manager = TaskManager(num_workers=2, queues=["notifications"])`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Recommended Queue Structure
        </h3>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Queue</th>
                <th className="text-left py-3 pr-4">Workers</th>
                <th className="text-left py-3">Use Case</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4"><code>default</code></td>
                <td className="py-3 pr-4">2-4</td>
                <td>General-purpose background work</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>emails</code></td>
                <td className="py-3 pr-4">2-4</td>
                <td>Email delivery (may have latency)</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>notifications</code></td>
                <td className="py-3 pr-4">4-8</td>
                <td>Push notifications, SMS (high volume)</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>analytics</code></td>
                <td className="py-3 pr-4">1-2</td>
                <td>Tracking, metrics (low priority)</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>critical</code></td>
                <td className="py-3 pr-4">2-4</td>
                <td>Security alerts, billing (high priority)</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Schedule Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Schedule Configuration
        </h2>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Interval Schedule
        </h3>
        <CodeBlock language="python">{`from aquilia.tasks import task, every

@task(schedule=every(seconds=30))   # Every 30 seconds
async def heartbeat(): pass

@task(schedule=every(minutes=5))    # Every 5 minutes
async def check_health(): pass

@task(schedule=every(hours=1))      # Every hour
async def hourly_report(): pass

@task(schedule=every(days=1))       # Daily
async def daily_cleanup(): pass

# Combined
@task(schedule=every(hours=2, minutes=30))  # Every 2.5 hours
async def periodic_task(): pass`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Cron Schedule
        </h3>
        <p className={`mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Format: <code>minute hour day_of_month month day_of_week</code>
        </p>
        <CodeBlock language="python">{`from aquilia.tasks import task, cron

@task(schedule=cron("*/5 * * * *"))     # Every 5 minutes
async def frequent(): pass

@task(schedule=cron("0 * * * *"))       # Every hour at :00
async def hourly(): pass

@task(schedule=cron("0 9 * * 1-5"))     # 9 AM weekdays
async def morning_digest(): pass

@task(schedule=cron("0 0 1 * *"))       # Midnight on 1st
async def monthly_report(): pass

@task(schedule=cron("0 3 * * 0"))       # 3 AM Sunday
async def weekly_maintenance(): pass`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Cron Expression Reference
        </h3>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Field</th>
                <th className="text-left py-3 pr-4">Values</th>
                <th className="text-left py-3">Special Characters</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4">Minute</td>
                <td className="py-3 pr-4">0-59</td>
                <td><code>* , - /</code></td>
              </tr>
              <tr>
                <td className="py-3 pr-4">Hour</td>
                <td className="py-3 pr-4">0-23</td>
                <td><code>* , - /</code></td>
              </tr>
              <tr>
                <td className="py-3 pr-4">Day of Month</td>
                <td className="py-3 pr-4">1-31</td>
                <td><code>* , - /</code></td>
              </tr>
              <tr>
                <td className="py-3 pr-4">Month</td>
                <td className="py-3 pr-4">1-12</td>
                <td><code>* , - /</code></td>
              </tr>
              <tr>
                <td className="py-3 pr-4">Day of Week</td>
                <td className="py-3 pr-4">0-6 (Sun=0)</td>
                <td><code>* , - /</code></td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Behavior */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Missing Configuration Behavior
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          What happens when configuration is omitted:
        </p>

        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Missing</th>
                <th className="text-left py-3">Behavior</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4"><code>backend</code></td>
                <td>Uses <code>MemoryBackend()</code> — in-memory, lost on restart</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>num_workers</code></td>
                <td>Defaults to 4 worker coroutines</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>queues</code></td>
                <td>Only processes <code>"default"</code> queue</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>poll_interval</code></td>
                <td>1 second between polls when queues are empty</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>name</code> (task)</td>
                <td>Auto-generated from <code>module:qualname</code></td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>schedule</code> (task)</td>
                <td>Task is on-demand only, not periodic</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>
    </div>
  )
}
