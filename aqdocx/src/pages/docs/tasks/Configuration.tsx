import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Settings, ShieldAlert, Info, Terminal } from 'lucide-react'

export function TasksConfiguration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Settings className="w-4 h-4 animate-pulse" />
          Background Tasks / Configuration
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Tasks Configuration
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Complete configuration specifications for background tasks. Learn how to configure workers, retries, periodic intervals, and custom backends at the workspace and module levels.
        </p>
      </div>

      {/* Legacy vs. Modern Integration Configuration Styles */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Integration Configuration Styles
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          Aquilia supports two styles of declaring subsystem integrations within <code className="text-aquilia-500">workspace.py</code>: the legacy builder-class style and the modern typed-dataclass style.
        </p>

        {/* Modern Style */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <Info className="w-5 h-5 text-emerald-400" />
            <h3 className="text-lg font-semibold">Modern Style: Composed Dataclasses (Recommended)</h3>
          </div>
          <p className={`text-sm mb-4 ${subtleText}`}>
            Construct the <DocTerm id="tasks.task">TasksIntegration</DocTerm> class directly. This ensures compile-time validation, IDE type hinting, and strict parameter checking.
          </p>
          <CodeBlock language="python" highlightLines={[8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]}>{`# workspace.py
from aquilia import Workspace, Module
from aquilia.integrations import TasksIntegration

workspace = (
    Workspace("myapp")
    .module(Module("core"))
    .integrate(TasksIntegration(
        backend="memory",
        num_workers=8,
        default_queue="default",
        scheduler_tick=5.0,
        cleanup_interval=60.0,
        cleanup_max_age=600.0,
        max_retries=5,
        retry_delay=1.5,
        retry_backoff=2.0,
        retry_max_delay=120.0,
        default_timeout=180.0,
        dead_letter_max=500,
        auto_start=True
    ))
)`}</CodeBlock>
        </div>

        {/* Legacy Style */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-3">
            <ShieldAlert className="w-5 h-5 text-amber-500" />
            <h3 className="text-lg font-semibold text-amber-500">Legacy Style: Static Integration Builders</h3>
          </div>
          <p className={`text-sm mb-4 ${subtleText}`}>
            The legacy <code className="text-aquilia-500">Integration.tasks()</code> helper delegates to the modern <code className="text-aquilia-500">TasksIntegration</code> under the hood. Avoid this in new projects.
          </p>
          <CodeBlock language="python" highlightLines={[7, 8, 9, 10]}>{`# workspace.py (Legacy)
from aquilia import Workspace
from aquilia.integrations import Integration

workspace = (
    Workspace("myapp")
    .integrate(Integration.tasks(
        num_workers=4,
        scheduler_tick=15.0,
    ))
)`}</CodeBlock>
          <div className="group relative overflow-hidden rounded-xl bg-amber-500/5 border border-amber-500/10 p-4 mt-3">
            <p className="text-xs leading-relaxed text-amber-400">
              <strong>Warning:</strong> The legacy static helper <code className="text-aquilia-500">Integration.tasks()</code> is deprecated and will be removed in a future release. Migrate to direct constructor calls using <code className="text-aquilia-500">TasksIntegration</code>.
            </p>
          </div>
        </div>
      </section>

      {/* Integration Option Table */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          TasksIntegration Parameters
        </h2>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mb-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500 w-44">Parameter</th>
                <th className="text-left py-4 px-6">Type</th>
                <th className="text-left py-4 px-6">Default</th>
                <th className="text-left py-4 px-6">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['backend', 'str', '"memory"', 'Storage backend. "memory" stores job states inside the process memory.'],
                ['num_workers', 'int', '4', 'Number of parallel async worker loop coroutines to run.'],
                ['default_queue', 'str', '"default"', 'Fallback queue name when queue is not explicitly declared.'],
                ['cleanup_interval', 'float', '300.0', 'Frequency (in seconds) of sweeps to purge terminated jobs.'],
                ['cleanup_max_age', 'float', '3600.0', 'Maximum age (in seconds) to retain terminated jobs in history.'],
                ['max_retries', 'int', '3', 'Default maximum retry limit for failed jobs.'],
                ['retry_delay', 'float', '1.0', 'Base backoff cooldown delay in seconds.'],
                ['retry_backoff', 'float', '2.0', 'Multiplier factor for exponential retry backoff.'],
                ['retry_max_delay', 'float', '300.0', 'Maximum cap for backoff delay (in seconds).'],
                ['default_timeout', 'float', '300.0', 'Maximum execution timeout (in seconds) per job.'],
                ['auto_start', 'bool', 'True', 'Whether to boot worker queues during server bootstrap lifecycle.'],
                ['dead_letter_max', 'int', '1000', 'Maximum capacity of the Dead-Letter Queue (DLQ) buffer.'],
                ['scheduler_tick', 'float', '15.0', 'Frequency (in seconds) to check and trigger scheduled tasks.'],
              ].map(([opt, type, defVal, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono font-semibold text-xs text-aquilia-400">{opt}</td>
                  <td className="py-3.5 px-6 font-mono text-xs">{type}</td>
                  <td className="py-3.5 px-6 font-mono text-xs">{defVal}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Module Level Manifest Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Module Manifest & ComponentRef
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Instead of declaring component imports as bare string paths, Aquilia v2 recommends using the <code className="text-aquilia-500">ComponentRef</code> class inside <code className="text-aquilia-500">manifest.py</code>. This offers typed metadata checks during boot scans.
        </p>

        <CodeBlock language="python" highlightLines={[8, 9, 10, 11, 15, 16, 17, 18, 19, 20, 21, 22]}>{`# modules/core/manifest.py
from aquilia import AppManifest, ComponentRef, ComponentKind

manifest = AppManifest(
    name="core",
    controllers=[
        # Controller component references
        ComponentRef(
            class_path="modules.core.controllers:NotificationsController",
            kind=ComponentKind.CONTROLLER
        )
    ],
    tasks=[
        # Task component references
        ComponentRef(
            class_path="modules.core.tasks:send_notification",
            kind=ComponentKind.TASK
        ),
        ComponentRef(
            class_path="modules.core.tasks:cleanup_logs",
            kind=ComponentKind.TASK
        )
    ],
)`}</CodeBlock>
      </section>

      {/* Standalone/Script TaskManager Construction */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Terminal className="w-5 h-5 text-aquilia-500" />
          Direct TaskManager Setup
        </h2>
        <p className={`mb-6 ${subtleText}`}>
          To run task workers in standalone scripts, background processes, or daemon systems, construct the manager manually:
        </p>

        <CodeBlock language="python">{`import asyncio
from aquilia.tasks import TaskManager, MemoryBackend

async def run_worker():
    backend = MemoryBackend()
    manager = TaskManager(
        backend=backend,
        num_workers=4,
        scheduler_tick=1.0
    )
    
    await manager.start()
    try:
        # Keep running
        while True:
            await asyncio.sleep(3600)
    finally:
        await manager.stop()

if __name__ == "__main__":
    asyncio.run(run_worker())`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
