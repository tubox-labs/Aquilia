import { useTheme } from '../../../context/ThemeContext'
import { motion } from 'framer-motion'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { ADPArchitectureDiagram } from '../../../components/ADPArchitectureDiagram'
import { ADPComponentInteractionDiagram } from '../../../components/ADPComponentInteractionDiagram'
import { ADPIntegrationPointsDiagram } from '../../../components/ADPIntegrationPointsDiagram'
import { ADPStartupSequenceSVG } from '../../../components/ADPStartupSequenceSVG'
import { ADPRequestFlowSVG } from '../../../components/ADPRequestFlowSVG'

export function ADPArchitecturePage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Architecture
        </h1>
        <p className={`text-lg leading-relaxed mb-6 ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          The Aquilia Development Platform (ADP) operates as an in-process network layer wrapping your Aquilia application. 
          By intercepting lifecycle hooks and request scopes at the protocol boundaries, it gathers rich instrumentation 
          telemetry without modifying your application logic.
        </p>
      </motion.div>

      {/* Premium Interactive Architecture SVG Diagram */}
      <section className="mt-8">
        <h2 className={`text-xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>System Layout</h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          A high-level view of how file watchers, protocol streams, and background diagnostics orchestrate the development context:
        </p>
        <ADPArchitectureDiagram isDark={isDark} />
      </section>

      {/* Component Interaction Diagram */}
      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-2 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Component Interaction Diagram
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          This model illustrates the communication lines between the client connection, the hot-reload watcher system, 
          the diagnostic sensors, and the Inspector bridge:
        </p>
        <ADPComponentInteractionDiagram isDark={isDark} />
      </section>

      {/* Framework Integration Points */}
      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Framework Integration Points
        </h2>
        <p className={`text-sm leading-relaxed mb-6 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          The ADP is a first-class Aquilia subsystem, wired into the same core machinery every other subsystem uses 
          rather than a parallel architecture.
        </p>

        <div className="space-y-6 text-sm leading-relaxed">
          <div>
            <h3 className={`font-bold text-base mb-1 ${isDark ? 'text-zinc-200' : 'text-zinc-800'}`}>Fault System Integration</h3>
            <p className={isDark ? 'text-zinc-400' : 'text-zinc-600'}>
              <code className="text-xs font-mono">aquilia/devplatform/faults.py</code> defines <code className="text-xs font-mono">DEVPLATFORM_DOMAIN</code> 
              (registered in <code className="text-xs font-mono">aquilia/faults/core.py</code>) and the <DocTerm id="devplatform.fault.base">DevPlatformFault</DocTerm> hierarchy 
              comprising <DocTerm id="devplatform.fault.startup">StartupFault</DocTerm>, <DocTerm id="devplatform.fault.reload">ReloadFault</DocTerm>, 
              <DocTerm id="devplatform.fault.inspector">InspectorFault</DocTerm>, and others. Non-fatal failures propagate through the wrapped app's 
              central <code className="text-xs font-mono">FaultEngine</code>. Because the Inspector's fault bridge is registered directly on the engine, 
              devplatform faults automatically surface in the Inspector's <code className="text-xs font-mono">Lane.EXCEPTION</code> without external hooks.
            </p>
          </div>

          <div>
            <h3 className={`font-bold text-base mb-1 ${isDark ? 'text-zinc-200' : 'text-zinc-800'}`}>Unified Configuration</h3>
            <p className={isDark ? 'text-zinc-400' : 'text-zinc-600'}>
              The <DocTerm id="devplatform.config">AquiliaDevelopmentConfig</DocTerm> resolves each environment key through 
              <code className="text-xs font-mono">aquilia.pyconfig.Env</code> during validation inside <code className="text-xs font-mono">__post_init__</code>. 
              Its serialized dictionary output acts as the single source of truth for generating the wrapped boot script wrapper at 
              <code className="text-xs font-mono">runtime/_adp_app.py</code>.
            </p>
          </div>

          <div>
            <h3 className={`font-bold text-base mb-1 ${isDark ? 'text-zinc-200' : 'text-zinc-800'}`}>Subsystem Typing & Cache</h3>
            <p className={isDark ? 'text-zinc-400' : 'text-zinc-600'}>
              Types reside in <code className="text-xs font-mono">aquilia/typing/devplatform.py</code>. State engines share a base 
              singleton mixin, while import resolution paths are optimized using a bounded cache.
            </p>
          </div>

          <div>
            <h3 className={`font-bold text-base mb-1 ${isDark ? 'text-zinc-200' : 'text-zinc-800'}`}>Diagnostic Telemetry Serving</h3>
            <p className={isDark ? 'text-zinc-400' : 'text-zinc-600'}>
              Database diagnostics read <code className="text-xs font-mono">Lane.DATABASE</code> spans off the request trace. A custom 
              <code className="text-xs font-mono">Lane.DEVPLATFORM</code> records hot-reload cycles and serves performance flamegraphs at 
              <code className="text-xs font-mono">/__aquilia__/inspector/devplatform/profile/&#123;request_id&#125;/</code>.
            </p>
          </div>
        </div>

        <ADPIntegrationPointsDiagram isDark={isDark} />
      </section>

      {/* Startup Sequence */}
      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-2 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Startup Sequence
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          The detailed sequence representing thread bootstrap, terminal listener hooks, watcher instantiation, and socket binding:
        </p>
        <ADPStartupSequenceSVG isDark={isDark} />
      </section>

      {/* Per-Request Transaction Flow */}
      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-2 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Per-Request Transaction Flow
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          The flow mapping client TCP frames to ASGI boundaries, Trace spans registration, and metrics logs:
        </p>
        <ADPRequestFlowSVG isDark={isDark} />
      </section>

      {/* Teardown & Shutdown */}
      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-6 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Teardown & Shutdown
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          On receiving a termination signal (SIGINT/SIGTERM or keyboard Q), ADP executes a clean teardown loop:
        </p>
        <ul className={`text-sm space-y-3 pl-5 list-disc ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          <li>Closes server ports and stops accepting new connections immediately.</li>
          <li>Waits for active in-flight HTTP requests to complete, up to the configured grace duration.</li>
          <li>Cancels the central lifespan coroutine, which triggers shutdown hooks inside the user's application modules.</li>
          <li>Shuts down file watchers, diagnostics threads, and runs <code className="text-xs font-mono">plugin.shutdown()</code> on loaded plugins.</li>
        </ul>
      </section>

      <section className="mt-16">
        <NextSteps items={[
          { text: 'Configuration', link: '/docs/devplatform/configuration' },
          { text: 'Hot Reload', link: '/docs/devplatform/hot-reload' },
        ]} />
      </section>
    </div>
  )
}
