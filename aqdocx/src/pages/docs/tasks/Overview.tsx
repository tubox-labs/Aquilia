import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import {
  Zap, Clock, RefreshCw, Layers, Play, CheckCircle, XCircle,
  AlertTriangle, RotateCcw, Timer, ListOrdered, Box, Cpu
} from 'lucide-react'

export function TasksOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  const features = [
    {
      icon: <Zap className="w-5 h-5 text-aquilia-400" />,
      title: 'Async-Native',
      desc: 'Built from the ground up for asyncio. Operates entirely via non-blocking coroutines without thread or process overhead.',
    },
    {
      icon: <ListOrdered className="w-5 h-5 text-blue-400" />,
      title: 'Priority Queues',
      desc: 'Sorts execution using CRITICAL > HIGH > NORMAL > LOW priority constraints. High-priority jobs are executed first.',
    },
    {
      icon: <RefreshCw className="w-5 h-5 text-emerald-400" />,
      title: 'Automatic Retries',
      desc: 'Features exponential backoff with random jitter. Configure delay multipliers and max retry caps per task.',
    },
    {
      icon: <Clock className="w-5 h-5 text-amber-400" />,
      title: 'Periodic Scheduling',
      desc: 'Supports interval-based (every 5 minutes) and cron-style (every Monday at 9 AM) periodic execution.',
    },
    {
      icon: <Layers className="w-5 h-5 text-purple-400" />,
      title: 'Zero Dependencies',
      desc: 'Built entirely on the Python standard library. Employs a heap-based priority queue without Redis or RabbitMQ.',
    },
    {
      icon: <Box className="w-5 h-5 text-pink-400" />,
      title: 'DI Integration',
      desc: 'Seamlessly wires into Aquilia\'s DI system. Inject services and databases directly into task handlers.',
    },
  ]

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Clock className="w-4 h-4 animate-pulse" />
          Background Tasks / Overview
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Background Tasks Module
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Aquilia provides an industry-grade, async-native background task system with priority queues, automatic retries, and scheduled executions. It is a lightweight, integrated replacement for Celery or RQ, running directly inside the asyncio event loop.
        </p>
      </div>

      {/* Quick Start */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Cpu className="w-5 h-5 text-aquilia-500" />
          Quick Start
        </h2>
        
        <div className="space-y-8">
          <div>
            <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
              1. Enable in Workspace
            </h3>
            <p className={`text-sm mb-3 ${subtleText}`}>
              Register the task integration inside your <code className="text-aquilia-500">workspace.py</code> config using <DocTerm id="tasks.task">TasksIntegration</DocTerm>.
            </p>
            <CodeBlock language="python" highlightLines={[9, 10, 11, 12]}>{`# workspace.py
from aquilia import Workspace, Module
from aquilia.integrations import TasksIntegration

workspace = (
    Workspace("myapp", version="1.0.0")
    .runtime(mode="dev", port=8000)
    .module(Module("core"))
    .integrate(TasksIntegration(
        num_workers=4,
        scheduler_tick=15.0,  # Periodic check interval
    ))
)`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
              2. Define a Task
            </h3>
            <p className={`text-sm mb-3 ${subtleText}`}>
              Decorate an async function with <DocTerm id="tasks.task">@task</DocTerm> and configure its queue, priority, and retry policy.
            </p>
            <CodeBlock language="python" highlightLines={[4, 5, 6, 7, 8, 9]}>{`# modules/core/tasks.py
from aquilia.tasks import task, Priority

@task(
    queue="notifications",
    priority=Priority.HIGH,
    max_retries=3,
    timeout=60.0,
)
async def send_notification(user_id: int, message: str) -> bool:
    """Send a notification to a user."""
    # notification logic goes here
    return True`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
              3. Dispatch from a Controller
            </h3>
            <p className={`text-sm mb-3 ${subtleText}`}>
              Call the task asynchronously inside a Controller handler using <code className="text-aquilia-500">.delay()</code>.
            </p>
            <CodeBlock language="python" highlightLines={[13, 14, 15, 16]}>{`# modules/core/controllers.py
from aquilia import Controller, POST, RequestCtx, Response
from .tasks import send_notification

class NotificationsController(Controller):
    prefix = "/notifications"
    
    @POST("/send")
    async def send(self, ctx: RequestCtx) -> Response:
        data = await ctx.json()
        
        # Enqueue task for background execution (returns job ID string)
        job_id = await send_notification.delay(
            user_id=data["user_id"],
            message=data["message"]
        )
        
        return Response.json({
            "job_id": job_id,
            "status": "queued"
        })`}</CodeBlock>
          </div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-500" />
          Key Pillars
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {features.map((feature, i) => (
            <div key={i} className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 hover:border-aquilia-500/20 p-6 backdrop-blur-sm transition-all duration-300 hover:translate-y-[-2px] hover:shadow-lg shadow-black/40">
              <div className="absolute top-0 bottom-0 left-0 w-1 bg-gradient-to-b from-aquilia-500 to-transparent opacity-50 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="flex items-center gap-3 mb-3">
                <div className="text-aquilia-500">{feature.icon}</div>
                <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{feature.title}</h3>
              </div>
              <p className={`text-sm leading-relaxed ${subtleText}`}>{feature.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture Diagram */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Subsystem Architecture</h2>
        <div className="w-full overflow-x-auto py-4">
          <svg viewBox="0 0 740 320" className="w-full h-auto min-w-[650px] overflow-visible">
            {/* Defs for gradients & shadow */}
            <defs>
              <linearGradient id="grad-blue" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#1d4ed8" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="grad-green" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#10b981" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#047857" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="grad-purple" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#6d28d9" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="grad-cyan" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#06b6d4" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#0e7490" stopOpacity="0.0" />
              </linearGradient>
              <marker id="glow-arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#10b981" />
              </marker>
              <filter id="glow-effect" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="4" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Scheduler Node */}
            <g transform="translate(10, 60)">
              <rect x="0" y="0" width="140" height="90" rx="16" fill="url(#grad-purple)" stroke="#8b5cf6" strokeWidth="1.5" filter="url(#glow-effect)" />
              <text x="70" y="32" textAnchor="middle" fill="#c084fc" fontSize="13" fontWeight="700" letterSpacing="0.05em">SCHEDULER</text>
              <text x="70" y="55" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="11" fontFamily="monospace">every() & cron()</text>
              <text x="70" y="70" textAnchor="middle" fill="#a78bfa" fontSize="9">Generates periodic triggers</text>
            </g>

            {/* TaskManager Node */}
            <g transform="translate(195, 60)">
              <rect x="0" y="0" width="160" height="90" rx="16" fill="url(#grad-blue)" stroke="#3b82f6" strokeWidth="1.5" filter="url(#glow-effect)" />
              <text x="80" y="32" textAnchor="middle" fill="#93c5fd" fontSize="13" fontWeight="700" letterSpacing="0.05em">TASK MANAGER</text>
              <text x="80" y="55" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="11" fontFamily="monospace">Registry Lookup</text>
              <text x="80" y="70" textAnchor="middle" fill="#60a5fa" fontSize="9">Orchestrates lifecycles</text>
            </g>

            {/* TaskBackend Node */}
            <g transform="translate(400, 60)">
              <rect x="0" y="0" width="150" height="90" rx="16" fill="url(#grad-green)" stroke="#10b981" strokeWidth="1.5" filter="url(#glow-effect)" />
              <text x="75" y="32" textAnchor="middle" fill="#a7f3d0" fontSize="13" fontWeight="700" letterSpacing="0.05em">QUEUE BACKEND</text>
              <text x="75" y="55" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="11" fontFamily="monospace">Priority Heap</text>
              <text x="75" y="70" textAnchor="middle" fill="#34d399" fontSize="9">Memory Heap queue storage</text>
            </g>

            {/* Workers Node */}
            <g transform="translate(590, 60)">
              <rect x="0" y="0" width="140" height="90" rx="16" fill="url(#grad-cyan)" stroke="#06b6d4" strokeWidth="1.5" filter="url(#glow-effect)" />
              <text x="70" y="32" textAnchor="middle" fill="#81e6d9" fontSize="13" fontWeight="700" letterSpacing="0.05em">WORKER POOL</text>
              <text x="70" y="55" textAnchor="middle" fill={isDark ? '#e5e5e5' : '#374151'} fontSize="11" fontFamily="monospace">Async Coroutines</text>
              <text x="70" y="70" textAnchor="middle" fill="#22d3ee" fontSize="9">Concurrent execution loops</text>
            </g>

            {/* Connectors / Flow Lines */}
            <path d="M 150 105 L 195 105" fill="none" stroke="#8b5cf6" strokeWidth="1.5" strokeDasharray="4 3" markerEnd="url(#glow-arrow)" />
            <path d="M 355 105 L 400 105" fill="none" stroke="#3b82f6" strokeWidth="1.5" strokeDasharray="4 3" markerEnd="url(#glow-arrow)" />
            <path d="M 550 105 L 590 105" fill="none" stroke="#10b981" strokeWidth="1.5" strokeDasharray="4 3" markerEnd="url(#glow-arrow)" />

            {/* Return loop line from workers back to backend / manager for updates */}
            <path d="M 660 60 Q 660 25 365 25 Q 275 25 275 60" fill="none" stroke="#06b6d4" strokeWidth="1.2" strokeDasharray="2 3" opacity="0.6" markerEnd="url(#glow-arrow)" />

            {/* Labels for Flow Steps */}
            <text x="172" y="122" textAnchor="middle" fill="#a78bfa" fontSize="9" fontWeight="600">Tick check</text>
            <text x="378" y="122" textAnchor="middle" fill="#60a5fa" fontSize="9" fontWeight="600">delay()</text>
            <text x="570" y="122" textAnchor="middle" fill="#34d399" fontSize="9" fontWeight="600">poll()</text>

            {/* Job States */}
            <text x="370" y="210" textAnchor="middle" fill={isDark ? '#94a3b8' : '#475569'} fontSize="12" fontWeight="700" letterSpacing="0.1em">JOB LIFECYCLE STATES</text>
            {[
              { x: 30, label: 'PENDING', color: '#3b82f6' },
              { x: 145, label: 'RUNNING', color: '#f59e0b' },
              { x: 265, label: 'COMPLETED', color: '#22c55e' },
              { x: 390, label: 'FAILED', color: '#ef4444' },
              { x: 500, label: 'RETRYING', color: '#8b5cf6' },
              { x: 615, label: 'DEAD', color: '#6b7280' },
            ].map((s, i) => (
              <g key={i}>
                <rect x={s.x} y="235" width="95" height="32" rx="16" fill="transparent" stroke={s.color} strokeWidth="1.2" opacity="0.8" />
                <text x={s.x + 47.5} y="255" textAnchor="middle" fill={s.color} fontSize="9.5" fontWeight="700" fontFamily="monospace">{s.label}</text>
              </g>
            ))}
          </svg>
        </div>
      </section>

      {/* Job Lifecycle Details */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Job Lifecycle States</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {[
            { icon: <Play className="w-5 h-5" />, state: 'PENDING', desc: 'Job is queued in the backend, awaiting worker pickup.', color: 'text-blue-400 bg-blue-500/10' },
            { icon: <Timer className="w-5 h-5" />, state: 'RUNNING', desc: 'Active execution inside an async worker coroutine.', color: 'text-amber-400 bg-amber-500/10' },
            { icon: <CheckCircle className="w-5 h-5" />, state: 'COMPLETED', desc: 'Task executed successfully; results are stored.', color: 'text-green-400 bg-green-500/10' },
            { icon: <XCircle className="w-5 h-5" />, state: 'FAILED', desc: 'Execution raised an error; retries remaining.', color: 'text-red-400 bg-red-500/10' },
            { icon: <RotateCcw className="w-5 h-5" />, state: 'RETRYING', desc: 'Job is waiting for backoff cooldown to elapse.', color: 'text-purple-400 bg-purple-500/10' },
            { icon: <AlertTriangle className="w-5 h-5" />, state: 'DEAD', desc: 'Exhausted all retries; moved to dead-letter queue.', color: 'text-gray-400 bg-gray-500/10' },
          ].map((item, i) => (
            <div key={i} className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 p-5 transition-all duration-300">
              <div className="absolute top-0 bottom-0 left-0 w-1 bg-white/5 group-hover:bg-aquilia-500 transition-colors duration-300" />
              <div className={`w-10 h-10 rounded-lg flex items-center justify-center mb-3 ${item.color}`}>
                {item.icon}
              </div>
              <h3 className={`font-mono font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.state}</h3>
              <p className={`text-xs leading-relaxed ${subtleText}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Priority System */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Priority System</h2>
        <p className={`mb-6 ${subtleText}`}>
          Aquilia background jobs are ordered in the queue using their integer priority. Lower values take absolute precedence.
        </p>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500">Level</th>
                <th className="text-left py-4 px-6">Enum Member</th>
                <th className="text-left py-4 px-6">Value</th>
                <th className="text-left py-4 px-6">Typical Use Case</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                { level: 'CRITICAL', enumVal: 'Priority.CRITICAL', num: 0, color: 'bg-red-500/20 text-red-400', desc: 'Critical alerts, webhooks, security incidents' },
                { level: 'HIGH', enumVal: 'Priority.HIGH', num: 1, color: 'bg-orange-500/20 text-orange-400', desc: 'User-triggered flows like activation emails' },
                { level: 'NORMAL', enumVal: 'Priority.NORMAL', num: 2, color: 'bg-blue-500/20 text-blue-400', desc: 'Standard business tasks (default)' },
                { level: 'LOW', enumVal: 'Priority.LOW', num: 3, color: 'bg-gray-500/20 text-gray-400', desc: 'Cleanup, archiving, report compilation' }
              ].map((row, i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono"><span className={`px-2.5 py-0.5 rounded text-xs ${row.color}`}>{row.level}</span></td>
                  <td className="py-3.5 px-6 font-mono text-xs text-aquilia-400"><DocTerm id="tasks.Priority">{row.enumVal}</DocTerm></td>
                  <td className="py-3.5 px-6 font-mono">{row.num}</td>
                  <td className={`py-3.5 px-6 ${subtleText}`}>{row.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Comparison Section */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Subsystem Comparison</h2>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500">Feature</th>
                <th className="text-left py-4 px-6 font-semibold">Aquilia Tasks</th>
                <th className="text-left py-4 px-6 font-semibold">Celery</th>
                <th className="text-left py-4 px-6 font-semibold">RQ (Redis Queue)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['Async-Native', '✅ Coroutine-based', '❌ Synchronous Worker', '❌ Synchronous Worker'],
                ['Broker Dependency', '✅ Zero (Stdlib Heap)', '❌ Redis or RabbitMQ', '❌ Redis Required'],
                ['Priority Support', '✅ Heap Priority Queue', '✅ Priority Queues', '❌ Lacks Priorities'],
                ['Periodic Schedulers', '✅ Built-in Scheduler Loop', '❌ Celery Beat Service', '❌ Redis Scheduler Ext'],
                ['Memory Backend', '✅ MemoryBackend', '❌ Thread-unsafe / Mock', '❌ Not Available'],
                ['Fault Integration', '✅ Structured Faults', '❌ Custom exception wrappers', '❌ Custom exception wrappers'],
              ].map(([feat, aq, celery, rq], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-semibold">{feat}</td>
                  <td className={`py-3.5 px-6 font-medium text-aquilia-400`}>{aq}</td>
                  <td className={`py-3.5 px-6 ${subtleText}`}>{celery}</td>
                  <td className={`py-3.5 px-6 ${subtleText}`}>{rq}</td>
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
