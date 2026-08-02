import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { motion } from 'framer-motion'
import {
  RefreshCw, Activity, Terminal, Layers,
  Database, Eye, Shield, GitBranch
} from 'lucide-react'

function FeatureItem({ icon, title, desc, isDark }: { icon: React.ReactNode; title: string; desc: string; isDark: boolean }) {
  return (
    <div className="py-6 border-b last:border-b-0 border-zinc-100 dark:border-zinc-800/60">
      <div className="flex items-center gap-3 mb-2">
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${isDark ? 'bg-aquilia-500/10 text-aquilia-400' : 'bg-aquilia-50 text-aquilia-600'}`}>
          {icon}
        </div>
        <h3 className={`font-bold text-base ${isDark ? 'text-zinc-100' : 'text-zinc-900'}`}>{title}</h3>
      </div>
      <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{desc}</p>
    </div>
  )
}

function LayerRow({ label, pkg, desc, color, isDark }: { label: React.ReactNode; pkg: string; desc: string; color: string; isDark: boolean }) {
  return (
    <div className="flex items-start gap-4 py-4 border-b last:border-b-0 border-zinc-100 dark:border-zinc-800/60">
      <div className="flex-shrink-0 mt-1">
        <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
      </div>
      <div className="flex-1">
        <div className="flex items-baseline gap-2 mb-1 flex-wrap">
          <span className={`font-bold text-sm ${isDark ? 'text-zinc-100' : 'text-zinc-900'}`}>{label}</span>
          <code className={`text-xs px-2 py-0.5 rounded font-mono ${isDark ? 'bg-zinc-800 text-zinc-400' : 'bg-zinc-100 text-zinc-600'}`}>{pkg}</code>
        </div>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>{desc}</p>
      </div>
    </div>
  )
}

export function ADPOverviewPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const features = [
    { icon: <Terminal className="w-4 h-4" />, title: 'Interactive Terminal UI', desc: 'A keyboard-driven command center right in your shell. Inspect diagnostics, trigger reloads, and check status with simple hotkeys like R, P, or M — removing browser dependency.' },
    { icon: <RefreshCw className="w-4 h-4" />, title: 'Intelligent Hot-Reload', desc: 'Computes dependency changes using static AST imports. Only modifies modules that actually changed, preserving connection pools, caches, and global states safely.' },
    { icon: <Eye className="w-4 h-4" />, title: 'Per-Request Tracing', desc: 'Every HTTP transaction generates a unique trace ID and logs precise timing durations. Data is stored inside RuntimeStateStore and automatically bridged into Aquilia\'s Inspector.' },
    { icon: <Database className="w-4 h-4" />, title: 'SQL Diagnostics', desc: 'Identifies slow queries, duplicate transactions, and potential N+1 query patterns dynamically during local requests, suggesting optimizations in real time.' },
    { icon: <Activity className="w-4 h-4" />, title: 'Telemetry Monitors', desc: 'Includes active monitoring for event-loop latency (blocking calls) and automated memory snapshots powered by Python\'s tracemalloc module.' },
    { icon: <Shield className="w-4 h-4" />, title: 'Structured Fault Reporting', desc: 'Standardizes errors as typed DevPlatformFault classes that report directly through the central application engine to avoid messy tracebacks.' },
    { icon: <GitBranch className="w-4 h-4" />, title: 'Platform Plugins', desc: 'Supports custom plugin registration allowing tools to hook into request startup, completion, shutdown, and unhandled exception loops.' },
    { icon: <Layers className="w-4 h-4" />, title: 'Native TCP Transport', desc: 'Powered by an h11 state machine transport written on top of asyncio stream sockets, resolving standard dev requirements without external dependencies.' },
  ]

  return (
    <div className="max-w-4xl">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Overview
        </h1>
        
        <p className={`text-lg leading-relaxed mb-6 ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          The <strong>Aquilia Development Platform (ADP)</strong> is the default framework-native ASGI development environment 
          shipped with Aquilia. It replaces third-party servers like Uvicorn in local workflows, injecting native observers 
          for AST-based hot-reloads, DB diagnostics, request tracing, and keyboard controls.
        </p>

        <div className={`text-sm px-4 py-3 rounded-xl border ${isDark ? 'border-amber-500/15 bg-amber-500/5 text-amber-300' : 'border-amber-200 bg-amber-50 text-amber-800'}`}>
          <strong>Note:</strong> ADP is designed exclusively for the inner loop development process. The CLI runner{' '}
          <code className="font-mono text-xs">aq run</code> automatically falls back to hardened production servers in prod environments.
        </div>
      </motion.div>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Quick Start
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          To spin up a development workspace using ADP, execute the standard dev command:
        </p>
        <CodeBlock language="bash" code={`# Run using ADP with default settings
aq dev

# Explicitly start dev mode
aq run --mode dev

# Fall back to raw Uvicorn server instead of ADP
aq run --no-adp`} />
        
        <p className={`text-sm mt-6 mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          You can also initialize the development server programmatically within your entrypoint script:
        </p>
        <CodeBlock 
          language="python" 
          highlightLines={[4, 7, 8]}
          code={`import asyncio
from aquilia.devplatform import AquiliaDevelopmentServer, AquiliaDevelopmentConfig

config = AquiliaDevelopmentConfig(host="127.0.0.1", port=8000, reload=True)

async def main():
    server = AquiliaDevelopmentServer(config)
    await server.start(app)  # Blocks until SIGINT/SIGTERM

asyncio.run(main())`} 
        />
      </section>

      <section className="mt-16">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Platform Features
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8">
          {features.map(f => <FeatureItem key={f.title} {...f} isDark={isDark} />)}
        </div>
      </section>

      <section className="mt-16">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Core Subsystems
        </h2>
        <div className="divide-y divide-zinc-100 dark:divide-zinc-800/60">
          <LayerRow label={<DocTerm id="devplatform.server">ADPProtocolHandler</DocTerm>} pkg="core.protocol" desc="The central dispatcher mapping raw ASGI protocols. Inspects connection states and logs HTTP metadata." color="#3b82f6" isDark={isDark} />
          <LayerRow label="ASGILifespanManager" pkg="core.lifespan" desc="Intercepts ASGI lifespan events to safely wire background diagnostic workers around your server hooks." color="#10b981" isDark={isDark} />
          <LayerRow label={<DocTerm id="devplatform.platform">AquiliaDevelopmentPlatform</DocTerm>} pkg="platform" desc="Exposes the safe hook registry allowing first- and third-party extensions to hook into request and exception states." color="#8b5cf6" isDark={isDark} />
          <LayerRow label={<DocTerm id="devplatform.runtime_state_store">RuntimeStateStore</DocTerm>} pkg="core.runtime" desc="Holds live metrics, rolling transaction history logs, and database status in a thread-safe singleton." color="#f59e0b" isDark={isDark} />
        </div>
      </section>

      <section className="mt-16">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Opting Out
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          If you prefer to disable ADP globally in your workspace configuration and bypass it entirely in favor of plain ASGI runs:
        </p>
        <CodeBlock 
          language="python" 
          highlightLines={[3]}
          code={`# workspace.py
class MyServer(AquilaConfig.Server):
    use_adp = False  # Bypasses ADP for all dev runs
    host = "0.0.0.0"
    port = 8000`} 
        />
      </section>

      <section className="mt-16">
        <NextSteps items={[
          { text: 'Getting Started', link: '/docs/devplatform/getting-started' },
          { text: 'Architecture', link: '/docs/devplatform/architecture' },
          { text: 'Configuration', link: '/docs/devplatform/configuration' },
        ]} />
      </section>
    </div>
  )
}
