import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Clock, Calendar, Timer, ArrowRight } from 'lucide-react'

export function TasksScheduling() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Clock className="w-4 h-4" />
          Tasks / Scheduling
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Periodic Task Scheduling
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Schedule tasks to run at intervals or on cron schedules. The scheduler loop automatically enqueues tasks at the right time.
        </p>
      </div>

      {/* How It Works */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          How Scheduling Works
        </h2>

        <div className={`p-6 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-gray-50 border-gray-200'}`}>
          <ol className={`list-decimal list-inside space-y-3 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <li><strong>Registration</strong> — Tasks with <code>schedule=</code> are marked as periodic</li>
            <li><strong>Scheduler Loop</strong> — Runs every second when TaskManager is started</li>
            <li><strong>Next Run Check</strong> — Each periodic task's next run time is computed</li>
            <li><strong>Enqueue</strong> — When time arrives, task is enqueued like any other job</li>
            <li><strong>Execution</strong> — Workers process the job normally</li>
          </ol>
        </div>

        <div className="mt-6 overflow-x-auto">
          <svg viewBox="0 0 700 180" className="w-full h-auto">
            <rect width="700" height="180" rx="12" fill="transparent" />
            
            {/* Scheduler box */}
            <rect x="20" y="30" width="180" height="120" rx="10" fill={isDark ? '#1a1a2e' : '#f0fdf4'} stroke="#22c55e" strokeWidth="2" />
            <text x="110" y="55" textAnchor="middle" fill="#22c55e" fontSize="13" fontWeight="700">Scheduler Loop</text>
            <text x="110" y="80" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="10">every 1 second:</text>
            <text x="110" y="100" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="10">check all schedules</text>
            <text x="110" y="120" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="10">enqueue if due</text>
            
            {/* Arrow */}
            <line x1="200" y1="90" x2="260" y2="90" stroke="#22c55e" strokeWidth="2" markerEnd="url(#arrow2)" />
            <text x="230" y="80" textAnchor="middle" fill={isDark ? '#666' : '#9ca3af'} fontSize="9">enqueue()</text>
            
            {/* Queue box */}
            <rect x="260" y="50" width="140" height="80" rx="10" fill={isDark ? '#111' : '#fff'} stroke={isDark ? '#333' : '#d1d5db'} />
            <text x="330" y="80" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="12" fontWeight="600">Task Queue</text>
            <text x="330" y="100" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="10">priority heap</text>
            
            {/* Arrow */}
            <line x1="400" y1="90" x2="460" y2="90" stroke="#22c55e" strokeWidth="2" markerEnd="url(#arrow2)" />
            <text x="430" y="80" textAnchor="middle" fill={isDark ? '#666' : '#9ca3af'} fontSize="9">pop()</text>
            
            {/* Worker box */}
            <rect x="460" y="50" width="140" height="80" rx="10" fill={isDark ? '#111' : '#fff'} stroke={isDark ? '#333' : '#d1d5db'} />
            <text x="530" y="80" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="12" fontWeight="600">Workers</text>
            <text x="530" y="100" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="10">execute task</text>
            
            {/* Schedule examples */}
            <text x="620" y="60" fill={isDark ? '#666' : '#9ca3af'} fontSize="10">every(5m)</text>
            <text x="620" y="80" fill={isDark ? '#666' : '#9ca3af'} fontSize="10">every(1h)</text>
            <text x="620" y="100" fill={isDark ? '#666' : '#9ca3af'} fontSize="10">cron("0 9 * * *")</text>
            
            <defs>
              <marker id="arrow2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto">
                <polygon points="0 0, 10 5, 0 7" fill="#22c55e" />
              </marker>
            </defs>
          </svg>
        </div>
      </section>

      {/* Interval Scheduling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <code className="text-aquilia-500">every()</code> — Interval Scheduling
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Run tasks at fixed intervals. The first execution happens one interval after TaskManager starts.
        </p>

        <CodeBlock language="python">{`from aquilia.tasks import task, every

def every(
    seconds: int = 0,
    minutes: int = 0,
    hours: int = 0,
    days: int = 0,
) -> IntervalSchedule`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Examples
        </h3>
        <CodeBlock language="python">{`# Every 30 seconds
@task(schedule=every(seconds=30))
async def heartbeat():
    await check_system_health()

# Every 5 minutes
@task(schedule=every(minutes=5))
async def check_queue_depth():
    depth = await get_queue_depth()
    if depth > 1000:
        await alert_ops("Queue depth high")

# Every hour
@task(schedule=every(hours=1))
async def hourly_report():
    await generate_and_send_report()

# Every day
@task(schedule=every(days=1))
async def daily_cleanup():
    await cleanup_old_sessions()
    await prune_expired_tokens()

# Combined: every 2 hours and 30 minutes
@task(schedule=every(hours=2, minutes=30))
async def periodic_sync():
    await sync_external_data()`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Interval Behavior
        </h3>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Schedule</th>
                <th className="text-left py-3 pr-4">Total Interval</th>
                <th className="text-left py-3">Runs Per Day</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4"><code>every(seconds=30)</code></td>
                <td className="py-3 pr-4">30 seconds</td>
                <td>2,880</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>every(minutes=5)</code></td>
                <td className="py-3 pr-4">5 minutes</td>
                <td>288</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>every(minutes=15)</code></td>
                <td className="py-3 pr-4">15 minutes</td>
                <td>96</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>every(hours=1)</code></td>
                <td className="py-3 pr-4">1 hour</td>
                <td>24</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>every(hours=6)</code></td>
                <td className="py-3 pr-4">6 hours</td>
                <td>4</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>every(days=1)</code></td>
                <td className="py-3 pr-4">24 hours</td>
                <td>1</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Cron Scheduling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <code className="text-aquilia-500">cron()</code> — Cron Scheduling
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Run tasks on a cron schedule for precise timing control.
        </p>

        <CodeBlock language="python">{`from aquilia.tasks import task, cron

def cron(expression: str) -> CronSchedule

# Format: "minute hour day_of_month month day_of_week"`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Cron Expression Format
        </h3>
        <div className="overflow-x-auto mb-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Field</th>
                <th className="text-left py-3 pr-4">Position</th>
                <th className="text-left py-3 pr-4">Values</th>
                <th className="text-left py-3">Special</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4">Minute</td>
                <td className="py-3 pr-4">1st</td>
                <td className="py-3 pr-4">0-59</td>
                <td><code>* , - /</code></td>
              </tr>
              <tr>
                <td className="py-3 pr-4">Hour</td>
                <td className="py-3 pr-4">2nd</td>
                <td className="py-3 pr-4">0-23</td>
                <td><code>* , - /</code></td>
              </tr>
              <tr>
                <td className="py-3 pr-4">Day of Month</td>
                <td className="py-3 pr-4">3rd</td>
                <td className="py-3 pr-4">1-31</td>
                <td><code>* , - /</code></td>
              </tr>
              <tr>
                <td className="py-3 pr-4">Month</td>
                <td className="py-3 pr-4">4th</td>
                <td className="py-3 pr-4">1-12</td>
                <td><code>* , - /</code></td>
              </tr>
              <tr>
                <td className="py-3 pr-4">Day of Week</td>
                <td className="py-3 pr-4">5th</td>
                <td className="py-3 pr-4">0-6 (Sun=0)</td>
                <td><code>* , - /</code></td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Special Characters
        </h3>
        <div className="overflow-x-auto mb-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Character</th>
                <th className="text-left py-3 pr-4">Meaning</th>
                <th className="text-left py-3">Example</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4"><code>*</code></td>
                <td className="py-3 pr-4">Any value</td>
                <td><code>* * * * *</code> — every minute</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>,</code></td>
                <td className="py-3 pr-4">Value list</td>
                <td><code>0,30 * * * *</code> — :00 and :30</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>-</code></td>
                <td className="py-3 pr-4">Range</td>
                <td><code>0 9-17 * * *</code> — 9 AM to 5 PM</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><code>/</code></td>
                <td className="py-3 pr-4">Step</td>
                <td><code>*/15 * * * *</code> — every 15 min</td>
              </tr>
            </tbody>
          </table>
        </div>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Common Patterns
        </h3>
        <CodeBlock language="python">{`# Every minute
@task(schedule=cron("* * * * *"))
async def every_minute(): pass

# Every 15 minutes
@task(schedule=cron("*/15 * * * *"))
async def every_15_min(): pass

# Every hour at :00
@task(schedule=cron("0 * * * *"))
async def every_hour(): pass

# 9 AM every day
@task(schedule=cron("0 9 * * *"))
async def morning_9am(): pass

# 9 AM on weekdays (Mon-Fri)
@task(schedule=cron("0 9 * * 1-5"))
async def weekday_morning(): pass

# Midnight on first of month
@task(schedule=cron("0 0 1 * *"))
async def monthly_first(): pass

# 3 AM every Sunday
@task(schedule=cron("0 3 * * 0"))
async def weekly_sunday(): pass

# Every 6 hours (midnight, 6am, noon, 6pm)
@task(schedule=cron("0 */6 * * *"))
async def every_6_hours(): pass

# Business hours only (9-17 on weekdays)
@task(schedule=cron("0 9-17 * * 1-5"))
async def business_hours(): pass`}</CodeBlock>
      </section>

      {/* Scheduling Best Practices */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Best Practices
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            {
              icon: <Timer className="w-5 h-5 text-aquilia-400" />,
              title: 'Use Interval for Simple Cases',
              desc: 'For "run every N minutes", every() is clearer than cron. Use cron for complex schedules.',
            },
            {
              icon: <Calendar className="w-5 h-5 text-blue-400" />,
              title: 'Avoid Minute 0',
              desc: 'Many cron jobs run at :00. Offset by a few minutes to reduce load spikes.',
            },
            {
              icon: <Clock className="w-5 h-5 text-amber-400" />,
              title: 'Consider Time Zones',
              desc: 'Scheduler uses server time. Be explicit about UTC vs local for production.',
            },
            {
              icon: <ArrowRight className="w-5 h-5 text-purple-400" />,
              title: 'Idempotent Tasks',
              desc: 'Scheduled tasks may run multiple times if workers restart. Make them idempotent.',
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

      {/* Querying Periodic Tasks */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Querying Periodic Tasks
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Use the registry to inspect registered periodic tasks:
        </p>

        <CodeBlock language="python">{`from aquilia.tasks import get_periodic_tasks, get_registered_tasks

# Get all periodic tasks
periodic = get_periodic_tasks()
for name, descriptor in periodic.items():
    print(f"{name}: {descriptor.schedule}")

# Check if a task is periodic
all_tasks = get_registered_tasks()
task = all_tasks.get("mymodule:hourly_report")
if task and task.is_periodic:
    print(f"Schedule: {task.schedule}")`}</CodeBlock>
      </section>

      {/* Dynamic Scheduling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Dynamic Scheduling
        </h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          For schedules that need to change at runtime, enqueue manually instead of using <code>schedule=</code>:
        </p>

        <CodeBlock language="python">{`from aquilia.tasks import task
from datetime import datetime, timedelta

@task(queue="reports")
async def generate_report(report_type: str):
    # Generate report logic
    pass

# Manual scheduling based on runtime config
async def schedule_reports(manager, config):
    while True:
        # Read schedule from database/config
        schedule = await get_report_schedule()
        
        for report_type, next_run in schedule.items():
            if datetime.now() >= next_run:
                await generate_report.delay(report_type=report_type)
                await update_next_run(report_type)
        
        await asyncio.sleep(60)  # Check every minute`}</CodeBlock>
      </section>
    </div>
  )
}
