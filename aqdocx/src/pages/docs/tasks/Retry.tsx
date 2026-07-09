import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Clock, RefreshCw } from 'lucide-react'

export function TasksRetry() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Clock className="w-4 h-4 animate-pulse" />
          Background Tasks / Retry Logic
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Retry Logic & Error Handling
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Understand how Aquilia processes background task failures, computes exponential backoffs with jitter, and routes jobs to the dead-letter queue.
        </p>
      </div>

      {/* How Retry Works */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <RefreshCw className="w-5 h-5 text-aquilia-500" />
          How Retries are Processed
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          When a task handler raises an unhandled exception, the worker catches the error, increments the retry counter, and determines if it can run again based on the task policy:
        </p>

        <div className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 p-6 backdrop-blur-sm shadow-xl mb-8">
          <div className="absolute top-0 bottom-0 left-0 w-1 bg-gradient-to-b from-aquilia-500 to-transparent opacity-50" />
          <ol className={`list-decimal list-inside space-y-3 text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <li><strong>Exception Intercepted:</strong> The worker catches exceptions raised inside the task coroutine.</li>
            <li><strong>Retry Evaluation:</strong> The worker compares <code className="text-aquilia-500">job.retry_count</code> to <code className="text-aquilia-500">job.max_retries</code>.</li>
            <li><strong>Backoff Math:</strong> If retries remain, the next schedule delay is computed with exponential backoff and ±25% random jitter.</li>
            <li><strong>State Transition:</strong> The job state is updated to <DocTerm id="tasks.Job">JobState.RETRYING</DocTerm>.</li>
            <li><strong>Queue Re-push:</strong> The job is pushed back into the heap queue with its <code className="text-aquilia-500">scheduled_at</code> timestamp set to the cooldown expiration.</li>
            <li><strong>Dead-Letter Route:</strong> If all retries are exhausted, the job state transitions to <DocTerm id="tasks.Job">JobState.DEAD</DocTerm> and is sent to the dead-letter queue.</li>
          </ol>
        </div>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          State Transitions
        </h3>
        
        {/* Floating borderless SVG State Transition Diagram */}
        <div className="w-full max-w-2xl mx-auto py-4 flex justify-center overflow-visible">
          <svg viewBox="0 0 600 200" className="w-full h-auto overflow-visible">
            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 1 L 10 5 L 0 9 z" fill="#888" />
              </marker>
              <linearGradient id="glow-running" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#f59e0b" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#f59e0b" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="glow-failed" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#ef4444" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#ef4444" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="glow-retrying" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="glow-pending" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.0" />
              </linearGradient>
              <linearGradient id="glow-dead" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#6b7280" stopOpacity="0.2" />
                <stop offset="100%" stopColor="#6b7280" stopOpacity="0.0" />
              </linearGradient>
              <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* RUNNING Node */}
            <g transform="translate(10, 80)">
              <rect x="0" y="0" width="95" height="42" rx="12" fill="url(#glow-running)" stroke="#f59e0b" strokeWidth="1.5" filter="url(#glow)" />
              <text x="47.5" y="25" textAnchor="middle" fill="#fbbf24" fontSize="10.5" fontWeight="700" fontFamily="monospace">RUNNING</text>
            </g>

            {/* FAILED Node */}
            <g transform="translate(160, 80)">
              <rect x="0" y="0" width="95" height="42" rx="12" fill="url(#glow-failed)" stroke="#ef4444" strokeWidth="1.5" filter="url(#glow)" />
              <text x="47.5" y="25" textAnchor="middle" fill="#f87171" fontSize="10.5" fontWeight="700" fontFamily="monospace">FAILED</text>
            </g>

            {/* RETRYING Node */}
            <g transform="translate(310, 80)">
              <rect x="0" y="0" width="95" height="42" rx="12" fill="url(#glow-retrying)" stroke="#8b5cf6" strokeWidth="1.5" filter="url(#glow)" />
              <text x="47.5" y="25" textAnchor="middle" fill="#c084fc" fontSize="10.5" fontWeight="700" fontFamily="monospace">RETRYING</text>
            </g>

            {/* PENDING Node */}
            <g transform="translate(460, 80)">
              <rect x="0" y="0" width="95" height="42" rx="12" fill="url(#glow-pending)" stroke="#3b82f6" strokeWidth="1.5" filter="url(#glow)" />
              <text x="47.5" y="25" textAnchor="middle" fill="#60a5fa" fontSize="10.5" fontWeight="700" fontFamily="monospace">PENDING</text>
            </g>

            {/* DEAD Node */}
            <g transform="translate(310, 150)">
              <rect x="0" y="0" width="95" height="42" rx="12" fill="url(#glow-dead)" stroke="#6b7280" strokeWidth="1.5" filter="url(#glow)" />
              <text x="47.5" y="25" textAnchor="middle" fill="#9ca3af" fontSize="10.5" fontWeight="700" fontFamily="monospace">DEAD</text>
            </g>

            {/* Arrows */}
            <path d="M 105 101 L 160 101" fill="none" stroke="#e5e7eb" strokeWidth="1.2" opacity="0.6" markerEnd="url(#arrow)" />
            <text x="132" y="94" textAnchor="middle" fill="#ef4444" fontSize="8.5" fontWeight="600">raised error</text>

            <path d="M 255 101 L 310 101" fill="none" stroke="#e5e7eb" strokeWidth="1.2" opacity="0.6" markerEnd="url(#arrow)" />
            <text x="282" y="94" textAnchor="middle" fill="#10b981" fontSize="8.5" fontWeight="600">tries remaining</text>

            <path d="M 405 101 L 460 101" fill="none" stroke="#e5e7eb" strokeWidth="1.2" opacity="0.6" markerEnd="url(#arrow)" />
            <text x="432" y="94" textAnchor="middle" fill="#8b5cf6" fontSize="8.5" fontWeight="600">backoff delay</text>

            <path d="M 207 122 L 207 171 L 310 171" fill="none" stroke="#e5e7eb" strokeWidth="1.2" opacity="0.6" markerEnd="url(#arrow)" />
            <text x="240" y="165" fill="#ef4444" fontSize="8.5" fontWeight="600">limit reached</text>

            {/* Return Arrow from PENDING to RUNNING */}
            <path d="M 507 80 Q 507 40 300 40 Q 57 40 57 80" fill="none" stroke="#3b82f6" strokeWidth="1" strokeDasharray="3 3" opacity="0.6" markerEnd="url(#arrow)" />
            <text x="270" y="34" textAnchor="middle" fill="#3b82f6" fontSize="8.5" fontWeight="600">scheduled worker poll</text>
          </svg>
        </div>
      </section>

      {/* Backoff Calculation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Exponential Backoff & Jitter
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          To prevent the "thundering herd" problem when external services fail, Aquilia adds a ±25% random jitter to the calculated exponential backoff delay.
        </p>

        <CodeBlock language="python" highlightLines={[7, 8, 11, 12]}>{`# Source code from aquilia/tasks/job.py
@property
def next_retry_delay(self) -> float:
    """Calculate next retry delay with exponential backoff + jitter."""
    import random

    delay = self.retry_delay * (self.retry_backoff ** self.retry_count)
    delay = min(delay, self.retry_max_delay)
    
    # Add random jitter (±25%)
    jitter = delay * 0.25 * (2 * random.random() - 1)
    return max(0.1, delay + jitter)`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
          Retry Backoff Intervals (Default Settings)
        </h3>
        <p className={`text-xs mb-4 ${subtleText}`}>
          Formula: <code className="text-aquilia-500">delay = retry_delay * (retry_backoff ^ attempt)</code> capped at <code className="text-aquilia-500">retry_max_delay</code>.
        </p>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500">Attempt</th>
                <th className="text-left py-4 px-6">Formula</th>
                <th className="text-left py-4 px-6">Base Delay</th>
                <th className="text-left py-4 px-6">Actual Interval (with ±25% jitter)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['1', '1.0 × 2⁰', '1.0s', '0.75s – 1.25s'],
                ['2', '1.0 × 2¹', '2.0s', '1.50s – 2.50s'],
                ['3', '1.0 × 2²', '4.0s', '3.00s – 5.00s'],
                ['4', '1.0 × 2³', '8.0s', '6.00s – 10.0s'],
                ['5', '1.0 × 2⁴', '16.0s', '12.0s – 20.0s'],
                ['Max Cap', 'Capped', '300.0s', '225.0s – 375.0s'],
              ].map(([attempt, formula, base, jitter], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3 px-6 font-mono text-xs">{attempt}</td>
                  <td className="py-3 px-6 font-mono text-xs text-aquilia-400">{formula}</td>
                  <td className="py-3 px-6 font-mono text-xs">{base}</td>
                  <td className={`py-3 px-6 text-xs ${subtleText}`}>{jitter}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Configuring Policies */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Configuring Retry Policies
        </h2>

        <div className="space-y-6">
          <div>
            <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
              Aggressive (Short Wait, High Attempts)
            </h3>
            <CodeBlock language="python" highlightLines={[1, 2, 3, 4, 5, 6]}>{`@task(
    max_retries=10,
    retry_delay=0.5,         # Start at 500ms
    retry_backoff=1.5,       # Slower exponential curve
    retry_max_delay=60.0,    # Max cap of 1 minute
)
async def aggressive_retry_task():
    ...`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
              Conservative (Long Wait, Low Attempts)
            </h3>
            <CodeBlock language="python" highlightLines={[1, 2, 3, 4, 5, 6]}>{`@task(
    max_retries=3,
    retry_delay=30.0,        # Start at 30 seconds
    retry_backoff=3.0,       # Slower exponential curve
    retry_max_delay=1800.0,  # Max cap of 30 minutes
)
async def conservative_retry_task():
    ...`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-gray-200' : 'text-gray-800'}`}>
              Disable Retries (One-Shot Task)
            </h3>
            <CodeBlock language="python" highlightLines={[1]}>{`@task(max_retries=0)
async def non_retryable_task():
    # Any failure routes directly to DEAD state
    ...`}</CodeBlock>
          </div>
        </div>
      </section>

      {/* Dead-Letter Queues */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Dead-Letter Queues (DLQ)
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Jobs that exceed `max_retries` transition to the <code className="text-aquilia-500">DEAD</code> state. You can monitor, list, and manually trigger retries for dead jobs.
        </p>

        <CodeBlock language="python" highlightLines={[4, 11]}>{`from aquilia.tasks import JobState

# Query dead jobs from the manager
dead_jobs = await manager.list_jobs(state=JobState.DEAD)

for job in dead_jobs:
    print(f"Dead Job ID: {job.id} | Task: {job.func_ref}")
    print(f"Error: {job.result.error}")
    
    # Manually re-enqueue/retry the job
    await manager.retry_job(job.id)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
