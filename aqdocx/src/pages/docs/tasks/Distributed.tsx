import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Network, Database, Shield, GitBranch, Fingerprint, AlertTriangle } from 'lucide-react'

export function TasksDistributed() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Network className="w-4 h-4 animate-pulse" />
          Background Tasks / Distributed Execution
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Distributed Execution & Workflows
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Run jobs across many worker processes and machines with durable state, recover work from crashed workers, compose jobs into dependency graphs, and collapse duplicate enqueues.
        </p>
        <p className={`text-sm mt-4 ${subtleText}`}>
          Added in <span className="text-aquilia-500 font-semibold">v1.3.5</span>.
        </p>
      </div>

      {/* Choosing a backend */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Database className="w-5 h-5 text-aquilia-500" />
          Choosing a Backend
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Switching backends is a configuration change, not a rewrite. Task functions, decorators, and <code className="text-aquilia-500">enqueue()</code> calls are identical on every backend.
        </p>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mb-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500 w-32">Backend</th>
                <th className="text-left py-4 px-6">Durable</th>
                <th className="text-left py-4 px-6">Multi-process</th>
                <th className="text-left py-4 px-6">When to use</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['memory', 'No', 'No', 'Development, and applications whose jobs can safely be lost on restart. The default.'],
                ['redis', 'Yes', 'Yes', 'Production. Fastest option — the claim path is one round trip against an in-memory sorted set.'],
                ['sql', 'Yes', 'Yes', 'When you cannot add Redis, or you want jobs to commit in the same transaction as the business data that created them.'],
              ].map(([name, durable, multi, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono font-semibold text-xs text-aquilia-400">{name}</td>
                  <td className="py-3.5 px-6 text-xs">{durable}</td>
                  <td className="py-3.5 px-6 text-xs">{multi}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <CodeBlock language="python">{`# workspace.py
from aquilia.integrations import TasksIntegration

# Development — single process, non-durable (default)
TasksIntegration(num_workers=4)

# Production — distributed workers, durable queue
TasksIntegration(
    backend="redis",
    redis_url="redis://cache:6379/0",
    num_workers=16,
    lease_seconds=120,
)

# Durable without extra infrastructure (requires DatabaseIntegration)
TasksIntegration(backend="sql", sql_table="aquilia_tasks")`}</CodeBlock>
        <p className={`text-sm mt-4 ${subtleText}`}>
          Install the Redis extra with <code className="text-aquilia-500">pip install aquilia[redis]</code>. The SQL backend needs no extra dependency.
        </p>
      </section>

      {/* Leases */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Shield className="w-5 h-5 text-emerald-400" />
          Crash Recovery via Leases
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          A worker claims a job and takes a lease for <code className="text-aquilia-500">lease_seconds</code>. While executing, it renews that lease every <code className="text-aquilia-500">heartbeat_interval</code> seconds. A background loop sweeps every <code className="text-aquilia-500">reclaim_interval</code> seconds and returns jobs whose lease lapsed to the runnable pool.
        </p>
        <p className={`mb-6 ${subtleText}`}>
          If a worker is killed mid-job, its lease expires and a peer picks the job up instead of the job being lost.
        </p>
        <div className="group relative overflow-hidden rounded-xl bg-amber-500/5 border border-amber-500/10 p-4 mb-6">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
            <p className="text-xs leading-relaxed text-amber-400">
              <strong>At-least-once delivery.</strong> A worker that stalls past its lease — a long GC pause, a blocked event loop — can have its job reclaimed and executed a second time. Task functions should be idempotent.
            </p>
          </div>
        </div>
      </section>

      {/* Serialization */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Serialization Rules
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          A job that crosses a process boundary cannot carry a live Python callable or arbitrary objects. Two rules follow.
        </p>
        <p className={`mb-4 ${subtleText}`}>
          <strong>Arguments must be JSON-serializable.</strong> A value JSON cannot represent raises <code className="text-aquilia-500">TaskSerializationFault</code> at <code className="text-aquilia-500">enqueue()</code> — deliberately, since the alternative is a job that enqueues cleanly and then fails unrecoverably on a remote worker, far from the call site.
        </p>
        <CodeBlock language="python">{`# Breaks on a durable backend — an ORM instance is not JSON
await tasks.enqueue(send_welcome, user)

# Correct — pass an identifier, let the worker re-load it
await tasks.enqueue(send_welcome, user.id)`}</CodeBlock>
        <p className={`my-4 ${subtleText}`}>
          <strong>Every worker must import every task module.</strong> Workers resolve jobs by registered name through the <code className="text-aquilia-500">@task</code> registry, so a queue entry can never name a function the application did not register. A worker that has not imported a task's module raises <code className="text-aquilia-500">TaskResolutionFault</code> for that job. Declaring tasks in your module manifests handles this automatically.
        </p>
      </section>

      {/* Workflows */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <GitBranch className="w-5 h-5 text-orange-400" />
          Workflows & DAGs
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Jobs can declare dependencies on other jobs. Every job is created up front with its dependencies recorded, so the graph is durable the moment it is submitted and no orchestrator process is required. Dependent jobs start <code className="text-aquilia-500">WAITING</code> and are released by the backend as their dependencies complete — a waiting step occupies no worker slot.
        </p>
        <CodeBlock language="python">{`from aquilia.tasks.workflow import chain, group, chord, Workflow

# Sequential — each step waits for the previous one
await chain(
    extract.s(source),
    transform.s().with_parent_results(),
    load.s().with_parent_results(),
).run(tasks)

# Parallel fan-out
await group([shard.s(n) for n in range(8)]).run(tasks)

# Parallel then fan-in — merge receives every shard's result
await chord(
    [shard.s(n) for n in range(8)],
    merge.s().with_parent_results(),
).run(tasks)

# Arbitrary DAG (diamond)
wf = Workflow("nightly")
extract_id = wf.add(extract_rows.s(source))
clean_id   = wf.add(clean_rows.s(),  depends_on=[extract_id])
enrich_id  = wf.add(enrich_rows.s(), depends_on=[extract_id])
wf.add(load_rows.s().with_parent_results(), depends_on=[clean_id, enrich_id])

result = await wf.run(tasks)`}</CodeBlock>
        <p className={`my-4 ${subtleText}`}>
          <code className="text-aquilia-500">run()</code> returns a <DocTerm id="tasks.task">WorkflowResult</DocTerm> for polling progress:
        </p>
        <CodeBlock language="python">{`await result.is_complete(tasks)    # every terminal job reached a terminal state
await result.results(tasks)        # terminal jobs' return values, in declaration order
await result.failed_jobs(tasks)    # jobs that ended FAILED or DEAD`}</CodeBlock>
        <p className={`my-4 ${subtleText}`}>
          <code className="text-aquilia-500">is_complete()</code> returns <code className="text-aquilia-500">True</code> for failure as well as success — use <code className="text-aquilia-500">failed_jobs()</code> to distinguish. A step that exhausts its retries leaves everything downstream <code className="text-aquilia-500">WAITING</code> rather than running it on missing input.
        </p>
        <p className={`my-4 ${subtleText}`}>
          Empty workflows, cycles, and unknown dependency indices raise <code className="text-aquilia-500">TaskWorkflowFault</code> before anything is enqueued, so a malformed workflow never partially executes.
        </p>
      </section>

      {/* Deduplication */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Fingerprint className="w-5 h-5 text-rose-400" />
          Idempotent Enqueue
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Every job has a stable fingerprint over its task name, queue, and arguments. The <code className="text-aquilia-500">dedup</code> parameter turns that fingerprint into an enforced reservation — held by the backend, so two racing processes produce one job rather than two.
        </p>
        <CodeBlock language="python">{`# Default — always enqueue (unchanged behavior)
await tasks.enqueue(rebuild_index)

# Collapse a burst of identical requests into one job
job_id = await tasks.enqueue(rebuild_index, dedup="skip")

# Treat a duplicate as a caller error
from aquilia.tasks import TaskDuplicateFault

try:
    await tasks.enqueue(charge_card, order_id, dedup="raise")
except TaskDuplicateFault:
    return Response.json({"status": "already_processing"}, status=409)`}</CodeBlock>
        <p className={`my-4 ${subtleText}`}>
          Enforcement lives in the storage layer: Redis <code className="text-aquilia-500">SET NX</code>, or a primary-key <code className="text-aquilia-500">INSERT</code> into <code className="text-aquilia-500">aquilia_task_locks</code> on SQL. The reservation is released when the job reaches a terminal state, so a failed job can be retried immediately instead of waiting out <code className="text-aquilia-500">dedup_ttl</code>.
        </p>
        <div className="group relative overflow-hidden rounded-xl bg-amber-500/5 border border-amber-500/10 p-4 mb-6">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
            <p className="text-xs leading-relaxed text-amber-400">
              Deduplication suppresses duplicate <strong>enqueues</strong>, not duplicate <strong>execution</strong>. Distributed backends are at-least-once, so task functions should still be idempotent. These are two different guarantees.
            </p>
          </div>
        </div>
      </section>

      {/* Running workers */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Running Dedicated Workers
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          A process that only consumes work is a normal Aquilia application configured with <code className="text-aquilia-500">num_workers</code> and a shared durable backend. There is no separate worker CLI command.
        </p>
        <p className={`mb-4 ${subtleText}`}>
          The queues it polls are derived from the <code className="text-aquilia-500">@task</code> descriptors it has imported, plus any queue it discovers on the shared backend — so a worker does not need to be told in advance which queues its producers use.
        </p>
      </section>

      {/* Degradation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Failure Modes
        </h2>
        <div className="space-y-3">
          {[
            ['Backend unreachable at startup', 'Logs an error naming the durability that was lost and falls back to the in-memory backend rather than aborting startup. The application still serves requests; queued jobs are not durable until the backend recovers and the process restarts.'],
            ['Unknown backend name', 'A typo such as backend="rabbitmq" logs a warning listing the valid values and uses the in-memory backend. A typo does not take production down.'],
            ['Clock skew across machines', 'Leases are absolute timestamps. Significant skew between workers can cause premature reclaim (duplicate execution) or delayed reclaim. Run NTP.'],
          ].map(([title, desc], i) => (
            <div key={i} className="rounded-xl bg-white/5 border border-white/5 p-4">
              <p className={`text-sm font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{title}</p>
              <p className={`text-xs leading-relaxed ${subtleText}`}>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'Configuration — every TasksIntegration parameter', link: '/docs/tasks/configuration' },
          { text: 'Retry Logic — backoff, jitter, and the dead-letter queue', link: '/docs/tasks/retry' },
          { text: 'Scheduling — interval and cron periodic execution', link: '/docs/tasks/scheduling' },
          { text: 'Mail Service — background delivery on distributed tasks', link: '/docs/mail/service' },
        ]}
      />
    </div>
  )
}
