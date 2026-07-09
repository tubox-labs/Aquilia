import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Clock, Calendar, Timer, ArrowRight, Cpu } from 'lucide-react'

export function TasksScheduling() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Clock className="w-4 h-4 animate-pulse" />
          Background Tasks / Scheduling
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Periodic Task Scheduling
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Schedule tasks to run at fixed intervals or precise calendar times. The scheduler loop automatically detects due tasks and enqueues them into the priority queue.
        </p>
      </div>

      {/* How Scheduling Works */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Cpu className="w-5 h-5 text-aquilia-500" />
          How Scheduling Works
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Aquilia handles scheduling without external services. When <code className="text-aquilia-500">TaskManager.start()</code> runs, a dedicated scheduler loop evaluates periodic registrations on every clock tick (determined by <code className="text-aquilia-500">scheduler_tick</code>).
        </p>

        <div className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 p-6 backdrop-blur-sm shadow-xl mb-8">
          <div className="absolute top-0 bottom-0 left-0 w-1 bg-gradient-to-b from-aquilia-500 to-transparent opacity-50" />
          <ol className={`list-decimal list-inside space-y-3 text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <li><strong>Task Registration:</strong> Tasks decorated with <code className="text-aquilia-500">schedule=</code> are registered with the task manager.</li>
            <li><strong>Tick Loop:</strong> The scheduler coroutine wakes up every tick interval (default: 15s) to check due tasks.</li>
            <li><strong>Due Calculation:</strong> The next execution timestamp is calculated based on the interval or cron specification.</li>
            <li><strong>Job Enqueue:</strong> When due, a new <DocTerm id="tasks.Job">Job</DocTerm> instance is pushed onto the priority queue.</li>
            <li><strong>Execution:</strong> Available workers pop and execute the task concurrently.</li>
          </ol>
        </div>

        {/* Floating borderless scheduling SVG flow */}
        <div className="w-full mx-auto py-4 flex justify-center overflow-visible">
          <svg viewBox="0 0 660 160" className="w-full h-auto overflow-visible">
            <defs>
              <linearGradient id="grad-green-sched" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#047857" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="grad-blue-sched" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#1d4ed8" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="grad-cyan-sched" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#0e7490" stopOpacity="0.0" />
              </linearGradient>
              <marker id="sched-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981" />
              </marker>
              <filter id="glow-sched" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Scheduler Box */}
            <g transform="translate(10, 35)">
              <rect x="0" y="0" width="165" height="90" rx="14" fill="url(#grad-green-sched)" stroke="#10b981" strokeWidth="1.5" filter="url(#glow-sched)" />
              <text x="82.5" y="32" textAnchor="middle" fill="#34d399" fontSize="11" fontWeight="700" letterSpacing="0.05em">SCHEDULER LOOP</text>
              <text x="82.5" y="55" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="10.5" fontFamily="monospace">every() / cron()</text>
              <text x="82.5" y="70" textAnchor="middle" fill="#6ee7b7" fontSize="8.5">Wakes up on tick interval</text>
            </g>

            {/* Queue Box */}
            <g transform="translate(235, 35)">
              <rect x="0" y="0" width="150" height="90" rx="14" fill="url(#grad-blue-sched)" stroke="#3b82f6" strokeWidth="1.5" filter="url(#glow-sched)" />
              <text x="75" y="32" textAnchor="middle" fill="#93c5fd" fontSize="11" fontWeight="700" letterSpacing="0.05em">TASK QUEUE</text>
              <text x="75" y="55" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="10.5" fontFamily="monospace">Priority Heap</text>
              <text x="75" y="70" textAnchor="middle" fill="#60a5fa" fontSize="8.5">Due jobs ordered by time</text>
            </g>

            {/* Workers Box */}
            <g transform="translate(445, 35)">
              <rect x="0" y="0" width="145" height="90" rx="14" fill="url(#grad-cyan-sched)" stroke="#06b6d4" strokeWidth="1.5" filter="url(#glow-sched)" />
              <text x="72.5" y="32" textAnchor="middle" fill="#81e6d9" fontSize="11" fontWeight="700" letterSpacing="0.05em">WORKER POOL</text>
              <text x="72.5" y="55" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="10.5" fontFamily="monospace">Async Coroutines</text>
              <text x="72.5" y="70" textAnchor="middle" fill="#22d3ee" fontSize="8.5">Execute due jobs</text>
            </g>

            {/* Connectors */}
            <path d="M 175 80 L 235 80" fill="none" stroke="#10b981" strokeWidth="1.5" strokeDasharray="3 3" markerEnd="url(#sched-arrow)" />
            <text x="205" y="72" textAnchor="middle" fill="#10b981" fontSize="8.5" fontWeight="600">enqueue()</text>

            <path d="M 385 80 L 445 80" fill="none" stroke="#3b82f6" strokeWidth="1.5" strokeDasharray="3 3" markerEnd="url(#sched-arrow)" />
            <text x="415" y="72" textAnchor="middle" fill="#3b82f6" fontSize="8.5" fontWeight="600">poll()</text>
          </svg>
        </div>
      </section>

      {/* Interval-based Scheduling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <DocTerm id="tasks.every">every()</DocTerm> — Interval-based Schedules
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Specifies that a task runs at fixed intervals. The scheduler calculates intervals dynamically using floats.
        </p>

        <CodeBlock language="python">{`from aquilia.tasks import task, every

@task(schedule=every(seconds=30))
async def report_heartbeat():
    # Runs every 30 seconds
    ...

@task(schedule=every(minutes=5))
async def prune_temp_files():
    # Runs every 5 minutes
    ...

@task(schedule=every(hours=12))
async def check_database_integrity():
    # Runs every 12 hours
    ...

@task(schedule=every(days=1, hours=6))
async def compile_statistics():
    # Runs every 30 hours
    ...`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Interval Schedule Layout
        </h3>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500">Declaration</th>
                <th className="text-left py-4 px-6 font-semibold">Total Cooldown</th>
                <th className="text-left py-4 px-6 font-semibold">Runs Per Day</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['every(seconds=15)', '15.0 seconds', '5,760'],
                ['every(minutes=5)', '300.0 seconds', '288'],
                ['every(hours=1)', '3,600.0 seconds', '24'],
                ['every(hours=6)', '21,600.0 seconds', '4'],
                ['every(days=1)', '86,400.0 seconds', '1'],
              ].map(([decl, total, runs], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-xs text-aquilia-400">{decl}</td>
                  <td className="py-3.5 px-6 font-mono text-xs">{total}</td>
                  <td className={`py-3.5 px-6 ${subtleText}`}>{runs}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Cron-based Scheduling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <DocTerm id="tasks.cron">cron()</DocTerm> — Calendar-based Schedules
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Specifies that a task runs on a cron schedule. Supports standard 5-field cron strings.
        </p>

        <CodeBlock language="python">{`from aquilia.tasks import task, cron

# Format: "minute hour day_of_month month day_of_week"

@task(schedule=cron("0 9 * * *"))
async def daily_9am_reports():
    # Runs at exactly 9:00 AM every day
    ...

@task(schedule=cron("*/15 * * * *"))
async def sync_external_inventory():
    # Runs at :00, :15, :30, and :45 of every hour
    ...

@task(schedule=cron("0 0 1 * *"))
async def monthly_invoice_run():
    # Runs at midnight on the first day of every month
    ...`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Expression Format Specification
        </h3>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500 w-32">Position</th>
                <th className="text-left py-4 px-6">Field Name</th>
                <th className="text-left py-4 px-6">Valid Values</th>
                <th className="text-left py-4 px-6">Supported Symbols</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['1st', 'Minute', '0 - 59', '* , - /'],
                ['2nd', 'Hour', '0 - 23', '* , - /'],
                ['3rd', 'Day of Month', '1 - 31', '* , - /'],
                ['4th', 'Month', '1 - 12', '* , - /'],
                ['5th', 'Day of Week', '0 - 6 (Sunday = 0)', '* , - /'],
              ].map(([pos, field, val, syms], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-xs">{pos}</td>
                  <td className="py-3.5 px-6 font-semibold text-xs text-aquilia-400">{field}</td>
                  <td className="py-3.5 px-6 font-mono text-xs">{val}</td>
                  <td className="py-3.5 px-6 font-mono text-xs">{syms}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Best Practices */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Scheduling Best Practices
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[
            {
              icon: <Timer className="w-5 h-5 text-aquilia-500" />,
              title: 'Task Idempotency',
              desc: 'Scheduled tasks can overlap or repeat if workers restart or run slow. Design tasks to be fully idempotent.',
            },
            {
              icon: <Calendar className="w-5 h-5 text-blue-500" />,
              title: 'Stagger Cron Times',
              desc: 'Running multiple heavy tasks at exactly midnight can spike server loads. Stagger minute coordinates (e.g., 5 0 * * *).',
            },
            {
              icon: <Clock className="w-5 h-5 text-emerald-500" />,
              title: 'Server Timezone Alignment',
              desc: 'Aquilia\'s scheduler uses server-local time. Ensure your environment timezone is configured correctly.',
            },
            {
              icon: <ArrowRight className="w-5 h-5 text-purple-500" />,
              title: 'Keep Tasks Small',
              desc: 'Break long-running batch jobs into parent/child flows: the scheduled task enqueues individual items as separate tasks.',
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
