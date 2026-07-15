import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { motion } from 'framer-motion'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ADPPluginsPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Plugins
        </h1>
        <p className={`text-lg leading-relaxed mb-6 ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          ADP exposes an extensible plugin API. By hooking into request lifecycles and exception streams, custom plugins can record 
          metrics, audit requests, or wire up third-party logging engines.
        </p>
      </motion.div>

      <section className="mt-10">
        <h2 className={`text-2xl font-bold mb-6 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Hook API Reference
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Plugins register hooks through the <DocTerm id="devplatform.platform">AquiliaDevelopmentPlatform</DocTerm> manager:
        </p>
        <div className="space-y-6">
          <div className="py-2">
            <div className="flex items-baseline gap-2 mb-1 flex-wrap">
              <code className={`text-sm font-mono font-bold ${isDark ? 'text-aquilia-300' : 'text-aquilia-600'}`}>on_request_start(hook)</code>
              <span className={`text-xs font-mono ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>(scope: dict) {"-> None"}</span>
            </div>
            <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              Invoked at the beginning of each HTTP connection, receiving the raw ASGI scope parameters.
            </p>
          </div>
          <div className="py-2">
            <div className="flex items-baseline gap-2 mb-1 flex-wrap">
              <code className={`text-sm font-mono font-bold ${isDark ? 'text-aquilia-300' : 'text-aquilia-600'}`}>on_request_end(hook)</code>
              <span className={`text-xs font-mono ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>(record: RequestRecord) {"-> None"}</span>
            </div>
            <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              Invoked after a request finishes, receiving the compiled <DocTerm id="devplatform.request_record">RequestRecord</DocTerm> containing telemetry and diagnostics.
            </p>
          </div>
          <div className="py-2">
            <div className="flex items-baseline gap-2 mb-1 flex-wrap">
              <code className={`text-sm font-mono font-bold ${isDark ? 'text-aquilia-300' : 'text-aquilia-600'}`}>on_exception(hook)</code>
              <span className={`text-xs font-mono ${isDark ? 'text-zinc-500' : 'text-zinc-400'}`}>(exc: Exception, context: Any) {"-> None"}</span>
            </div>
            <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
              Invoked whenever an unhandled exception propagates through request paths, passing the exception instance.
            </p>
          </div>
        </div>
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Implementing a Plugin
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          A plugin is a Python class with an <code className="font-mono text-sm">initialize(adp)</code> method. 
          Use Python entry points to register it under the <code className="font-mono text-sm">aquilia.devplatform.plugins</code> group:
        </p>
        <CodeBlock 
          language="python" 
          highlightLines={[12, 14, 15]}
          code={`# myplugin/plugin.py
from aquilia.devplatform import AquiliaDevelopmentPlatform
from aquilia.devplatform.core.state import RequestRecord

class RequestLogPlugin:
    name = "request-log"
    version = "1.0.0"

    def __init__(self):
        self._fh = None

    def initialize(self, adp: AquiliaDevelopmentPlatform) -> None:
        self._fh = open("requests.log", "a")
        adp.on_request_end(self._log_request)
        adp.on_exception(self._log_exception)

    def _log_request(self, record: RequestRecord) -> None:
        self._fh.write(f"{record.trace_id} {record.path} {record.status_code}\\n")
        self._fh.flush()

    def _log_exception(self, exc: Exception, context) -> None:
        self._fh.write(f"ERROR: {exc}\\n")

    def shutdown(self) -> None:
        if self._fh:
            self._fh.close()`} 
        />
        <p className={`text-sm mt-6 mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          Register the entry point in your plugin's package configurations:
        </p>
        <CodeBlock 
          language="toml" 
          highlightLines={[2]}
          code={`# pyproject.toml
[project.entry-points."aquilia.devplatform.plugins"]
request-log = "myplugin.plugin:RequestLogPlugin"`} 
        />
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Programmatic Registration
        </h2>
        <p className={`text-sm mb-4 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          For testing or internal hooks, register instances directly:
        </p>
        <CodeBlock 
          language="python" 
          highlightLines={[4]}
          code={`server = AquiliaDevelopmentServer(config)
platform = server.get_platform()

platform.register_plugin_direct(RequestLogPlugin())`} 
        />
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-zinc-800/60 text-white' : 'border-gray-100 text-gray-900'}`}>
          Hook Isolation & Safety
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`}>
          To ensure one misbehaving plugin cannot break request cycles or crash the server, ADP executes all callbacks 
          inside exception blocks. If a hook raises an exception, the error is isolated, encapsulated as a 
          <DocTerm id="devplatform.fault.worker">WorkerFault</DocTerm>, and reported to the fault engine.
        </p>
      </section>

      <section className="mt-16">
        <NextSteps items={[
          { text: 'Faults', link: '/docs/devplatform/faults' },
          { text: 'Architecture', link: '/docs/devplatform/architecture' },
        ]} />
      </section>
    </div>
  )
}
