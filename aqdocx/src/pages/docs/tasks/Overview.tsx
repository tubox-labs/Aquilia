import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
// import { Link } from 'react-router-dom'
import {
  Zap, Clock, RefreshCw, Layers, Play, CheckCircle, XCircle,
  AlertTriangle, RotateCcw, Timer, ListOrdered, Box
} from 'lucide-react'

export function TasksOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const features = [
    {
      icon: <Zap className="w-5 h-5 text-aquilia-400" />,
      title: 'Async-Native',
      desc: 'Built from the ground up for asyncio. No thread pools or process spawning — just pure async coroutines.',
    },
    {
      icon: <ListOrdered className="w-5 h-5 text-blue-400" />,
      title: 'Priority Queues',
      desc: 'CRITICAL > HIGH > NORMAL > LOW ordering. Higher priority jobs are always processed first.',
    },
    {
      icon: <RefreshCw className="w-5 h-5 text-emerald-400" />,
      title: 'Automatic Retries',
      desc: 'Exponential backoff with jitter. Configure max retries, delays, and backoff multipliers per task.',
    },
    {
      icon: <Clock className="w-5 h-5 text-amber-400" />,
      title: 'Scheduling',
      desc: 'Interval-based (every(minutes=5)) and cron-style (cron("0 9 * * 1-5")) periodic task execution.',
    },
    {
      icon: <Layers className="w-5 h-5 text-purple-400" />,
      title: 'Zero Dependencies',
      desc: 'Uses only Python stdlib. Heap-based priority queue, no Redis or RabbitMQ required.',
    },
    {
      icon: <Box className="w-5 h-5 text-pink-400" />,
      title: 'DI Integration',
      desc: 'Works seamlessly with Aquilia\'s dependency injection. Inject services into task handlers.',
    },
  ]

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Clock className="w-4 h-4" />
          Background Tasks
        </div>
        <h1 className={`text-4xl mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono">
            Tasks Module
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Industry-grade async background task system with priority queues, retry logic, and scheduling.
          A lightweight, integrated replacement for Celery or RQ.
        </p>
      </div>

      {/* Quick Start */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Quick Start</h2>
        
        <div className="space-y-6">
          <div>
            <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
              1. Define a Task
            </h3>
            <CodeBlock language="python">{`from aquilia.tasks import task, Priority

@task(
    queue="notifications",
    priority=Priority.HIGH,
    max_retries=3,
)
async def send_notification(user_id: int, message: str) -> bool:
    """Send a notification to a user."""
    # Your notification logic here
    return True`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
              2. Enqueue a Job
            </h3>
            <CodeBlock language="python">{`# Enqueue immediately
job_id = await send_notification.delay(user_id=123, message="Hello!")

# Or use .send() (alias for .delay())
job_id = await send_notification.send(user_id=123, message="Hello!")`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
              3. Run Workers
            </h3>
            <CodeBlock language="python">{`from aquilia.tasks import TaskManager

async def main():
    manager = TaskManager()
    await manager.start()
    
    # Enqueue some work
    await send_notification.delay(user_id=1, message="Test")
    
    # Wait for completion
    await manager.wait_for_shutdown()`}</CodeBlock>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Key Features</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {features.map((feature, i) => (
            <div key={i} className={`p-5 rounded-xl border ${isDark ? 'bg-[#111] border-white/10' : 'bg-white border-gray-200'}`}>
              <div className="flex items-center gap-3 mb-3">
                {feature.icon}
                <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{feature.title}</h3>
              </div>
              <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture Diagram */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Architecture</h2>
        <div className="w-full overflow-x-auto">
          <svg viewBox="0 0 720 320" className="w-full h-auto min-w-[600px]">
            <rect width="720" height="320" rx="16" fill="transparent" />

            {/* TaskManager Box */}
            <rect x="20" y="20" width="680" height="180" rx="12" fill={isDark ? '#1a1a2e' : '#f0fdf4'} stroke="#22c55e" strokeWidth="2" />
            <text x="360" y="45" textAnchor="middle" fill="#22c55e" fontSize="14" fontWeight="700">TaskManager</text>

            {/* Workers */}
            <rect x="40" y="60" width="140" height="80" rx="8" fill={isDark ? '#111' : '#fff'} stroke={isDark ? '#333' : '#d1d5db'} />
            <text x="110" y="85" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="12" fontWeight="600">Workers</text>
            <text x="110" y="105" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="10">Worker 1</text>
            <text x="110" y="120" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="10">Worker 2</text>
            <text x="110" y="135" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="10">Worker N</text>

            {/* Scheduler */}
            <rect x="200" y="60" width="140" height="80" rx="8" fill={isDark ? '#111' : '#fff'} stroke={isDark ? '#333' : '#d1d5db'} />
            <text x="270" y="85" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="12" fontWeight="600">Scheduler</text>
            <text x="270" y="105" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="10">every()</text>
            <text x="270" y="120" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="10">cron()</text>

            {/* Backend */}
            <rect x="360" y="60" width="160" height="80" rx="8" fill={isDark ? '#111' : '#fff'} stroke={isDark ? '#333' : '#d1d5db'} />
            <text x="440" y="85" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="12" fontWeight="600">TaskBackend</text>
            <text x="440" y="105" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="10">(MemoryBackend)</text>
            <text x="440" y="125" textAnchor="middle" fill="#22c55e" fontSize="10">Priority Heap Queue</text>

            {/* Registry */}
            <rect x="540" y="60" width="140" height="80" rx="8" fill={isDark ? '#111' : '#fff'} stroke={isDark ? '#333' : '#d1d5db'} />
            <text x="610" y="85" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="12" fontWeight="600">Task Registry</text>
            <text x="610" y="105" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="10">@task decorators</text>
            <text x="610" y="120" textAnchor="middle" fill={isDark ? '#888' : '#6b7280'} fontSize="10">name → fn mapping</text>

            {/* Arrows */}
            <line x1="180" y1="100" x2="200" y2="100" stroke="#22c55e" strokeWidth="2" markerEnd="url(#arrow)" />
            <line x1="340" y1="100" x2="360" y2="100" stroke="#22c55e" strokeWidth="2" markerEnd="url(#arrow)" />
            <line x1="520" y1="100" x2="540" y2="100" stroke="#22c55e" strokeWidth="2" markerEnd="url(#arrow)" />

            {/* Bottom section - Flow */}
            <text x="60" y="175" fill={isDark ? '#666' : '#9ca3af'} fontSize="10">poll()</text>
            <text x="250" y="175" fill={isDark ? '#666' : '#9ca3af'} fontSize="10">enqueue()</text>
            <text x="420" y="175" fill={isDark ? '#666' : '#9ca3af'} fontSize="10">push/pop</text>
            <text x="590" y="175" fill={isDark ? '#666' : '#9ca3af'} fontSize="10">resolve()</text>

            {/* Job States */}
            <text x="360" y="230" textAnchor="middle" fill={isDark ? '#555' : '#94a3b8'} fontSize="12" fontWeight="600">JOB STATES</text>
            {[
              { x: 40, label: 'PENDING', color: '#3b82f6' },
              { x: 140, label: 'RUNNING', color: '#f59e0b' },
              { x: 250, label: 'COMPLETED', color: '#22c55e' },
              { x: 370, label: 'FAILED', color: '#ef4444' },
              { x: 470, label: 'RETRYING', color: '#8b5cf6' },
              { x: 580, label: 'DEAD', color: '#6b7280' },
            ].map((s, i) => (
              <g key={i}>
                <rect x={s.x} y="245" width="90" height="28" rx="14" fill={s.color + '22'} stroke={s.color} strokeWidth="1.5" />
                <text x={s.x + 45} y="264" textAnchor="middle" fill={s.color} fontSize="10" fontWeight="600">{s.label}</text>
              </g>
            ))}

            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#22c55e" />
              </marker>
            </defs>
          </svg>
        </div>
      </section>

      {/* Job Lifecycle */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Job Lifecycle</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: <Play className="w-5 h-5" />, state: 'PENDING', desc: 'Job is queued, waiting for a worker', color: 'text-blue-400 bg-blue-500/10' },
            { icon: <Timer className="w-5 h-5" />, state: 'RUNNING', desc: 'Worker is executing the task', color: 'text-amber-400 bg-amber-500/10' },
            { icon: <CheckCircle className="w-5 h-5" />, state: 'COMPLETED', desc: 'Task finished successfully', color: 'text-green-400 bg-green-500/10' },
            { icon: <XCircle className="w-5 h-5" />, state: 'FAILED', desc: 'Task threw an exception', color: 'text-red-400 bg-red-500/10' },
            { icon: <RotateCcw className="w-5 h-5" />, state: 'RETRYING', desc: 'Scheduled for retry after backoff', color: 'text-purple-400 bg-purple-500/10' },
            { icon: <AlertTriangle className="w-5 h-5" />, state: 'DEAD', desc: 'Exhausted all retry attempts', color: 'text-gray-400 bg-gray-500/10' },
          ].map((item, i) => (
            <div key={i} className={`p-4 rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${item.color}`}>
                {item.icon}
              </div>
              <h3 className={`font-mono font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.state}</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Priority System */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Priority System</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Jobs are executed in priority order. Lower integer value = higher priority.
        </p>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Level</th>
                <th className="text-left py-3 pr-4">Enum Value</th>
                <th className="text-left py-3 pr-4">Integer</th>
                <th className="text-left py-3">Use Case</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              <tr>
                <td className="py-3 pr-4"><span className="px-2 py-1 rounded bg-red-500/20 text-red-400 text-xs font-mono">CRITICAL</span></td>
                <td className="py-3 pr-4"><code className="text-aquilia-500">Priority.CRITICAL</code></td>
                <td className="py-3 pr-4">0</td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>System alerts, security events</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><span className="px-2 py-1 rounded bg-orange-500/20 text-orange-400 text-xs font-mono">HIGH</span></td>
                <td className="py-3 pr-4"><code className="text-aquilia-500">Priority.HIGH</code></td>
                <td className="py-3 pr-4">1</td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>User-facing operations</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><span className="px-2 py-1 rounded bg-blue-500/20 text-blue-400 text-xs font-mono">NORMAL</span></td>
                <td className="py-3 pr-4"><code className="text-aquilia-500">Priority.NORMAL</code></td>
                <td className="py-3 pr-4">2</td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Standard background work (default)</td>
              </tr>
              <tr>
                <td className="py-3 pr-4"><span className="px-2 py-1 rounded bg-gray-500/20 text-gray-400 text-xs font-mono">LOW</span></td>
                <td className="py-3 pr-4"><code className="text-aquilia-500">Priority.LOW</code></td>
                <td className="py-3 pr-4">3</td>
                <td className={isDark ? 'text-gray-400' : 'text-gray-600'}>Maintenance, cleanup, analytics</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Comparison</h2>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-3 pr-4 text-aquilia-500">Feature</th>
                <th className="text-left py-3 pr-4">Aquilia Tasks</th>
                <th className="text-left py-3 pr-4">Celery</th>
                <th className="text-left py-3">RQ</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              {[
                ['Async-native', '✅', '❌ (sync)', '❌ (sync)'],
                ['Zero dependencies', '✅', '❌ (Redis/RabbitMQ)', '❌ (Redis)'],
                ['Priority queues', '✅', '✅', '❌'],
                ['Cron scheduling', '✅', '✅ (celery-beat)', '❌'],
                ['Memory backend', '✅', '❌', '❌'],
                ['Structured faults', '✅', '❌', '❌'],
              ].map(([feature, aquilia, celery, rq], i) => (
                <tr key={i}>
                  <td className="py-3 pr-4 font-medium">{feature}</td>
                  <td className="py-3 pr-4">{aquilia}</td>
                  <td className="py-3 pr-4">{celery}</td>
                  <td className="py-3">{rq}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Next Steps */}
    </div>
  )
}
