import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Brain } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MLOpsPlugins() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Brain className="w-4 h-4" />
          MLOps / Plugins
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Plugin System
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Extend Aquilia MLOps with a first-class plugin system. The <code className="text-aquilia-500">PluginHost</code> discovers
          and manages plugin lifecycles via Python entry points, while <code className="text-aquilia-500">PluginMarketplace</code> provides
          remote plugin discovery and installation.
        </p>
      </div>

      {/* PluginHost */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>PluginHost</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The plugin host manages the full plugin lifecycle: discovery, loading, activation, hook registration,
          and deactivation. Plugins are discovered via Python <code className="text-aquilia-500">entry_points</code> under
          the <code className="text-aquilia-500">aquilia.mlops.plugins</code> group.
        </p>

        <h3 className={`text-lg font-semibold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Plugin States</h3>
        <div className="flex flex-wrap gap-2 mb-6">
          {['DISCOVERED', 'LOADED', 'ACTIVATED', 'DEACTIVATED', 'ERROR'].map((state) => (
            <span key={state} className={`px-3 py-1 rounded-full text-xs font-mono ${isDark ? 'bg-white/10 text-gray-300' : 'bg-gray-100 text-gray-700'}`}>
              {state}
            </span>
          ))}
        </div>

        <CodeBlock language="python" code={`from aquilia.mlops.plugins.host import PluginHost, PluginDescriptor

host = PluginHost()

# Auto-discover plugins via entry points
# Scans: importlib.metadata.entry_points(group="aquilia.mlops.plugins")
await host.discover()

# Register a plugin manually
host.register(my_plugin_instance)

# Load all discovered plugins
await host.load_all()

# Activate all loaded plugins
await host.activate_all()

# List plugins with state
for desc in host.plugins():
    print(f"{desc.name} v{desc.version} → {desc.state}")
    # PluginDescriptor(
    #   name="health-check",
    #   version="1.0.0",
    #   author="Aquilia Team",
    #   state=PluginState.ACTIVATED,
    #   hooks=["on_health_check", "on_model_loaded"],
    # )

# Hook system: register + emit
host.on("on_model_loaded", callback)

# Emit event to all registered hooks
await host.emit("on_model_loaded", model_name="sentiment", version="2.1.0")

# Deactivate and unload
await host.deactivate_all()
await host.unload_all()`} />
      </section>

      {/* Writing a Plugin */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Writing a Plugin</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Plugins implement the <code className="text-aquilia-500">PluginHook</code> protocol. The minimal interface
          requires <code className="text-aquilia-500">name</code>, <code className="text-aquilia-500">version</code>,
          <code className="text-aquilia-500"> activate()</code>, and <code className="text-aquilia-500">deactivate()</code>.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops._types import PluginHook

class HealthCheckPlugin:
    """Example plugin that adds custom health checks."""

    name = "health-check"
    version = "1.0.0"
    author = "Aquilia Team"

    def __init__(self):
        self._checks: list = []

    async def activate(self, host):
        """Called when the plugin is activated."""
        # Register hooks
        host.on("on_health_check", self.run_checks)
        host.on("on_model_loaded", self.on_model_loaded)

    async def deactivate(self, host):
        """Called when the plugin is deactivated."""
        self._checks.clear()

    async def run_checks(self, **kwargs):
        """Custom health check logic."""
        results = {}
        for check in self._checks:
            results[check["name"]] = await check["fn"]()
        return results

    async def on_model_loaded(self, model_name: str, version: str, **kwargs):
        """React to model load events."""
        print(f"Plugin: Model {model_name} v{version} loaded")`} />

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${isDark ? 'text-white' : 'text-gray-900'}`}>Entry Point Registration</h3>
        <CodeBlock language="toml" code={`# pyproject.toml
[project.entry-points."aquilia.mlops.plugins"]
health-check = "my_package.plugins:HealthCheckPlugin"

# Or in setup.py
entry_points={
    "aquilia.mlops.plugins": [
        "health-check = my_package.plugins:HealthCheckPlugin",
    ],
}`} />
      </section>

      {/* PluginMarketplace */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>PluginMarketplace</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Discover and install community plugins from a remote JSON index.
        </p>
        <CodeBlock language="python" code={`from aquilia.mlops.plugins.marketplace import PluginMarketplace

marketplace = PluginMarketplace(
    index_url="https://plugins.aquilia.dev/mlops/index.json",
)

# Fetch the plugin index
await marketplace.fetch_index()

# Search for plugins
results = marketplace.search("monitoring")
# [
#   {"name": "prometheus-exporter", "version": "2.0.0", "description": "..."},
#   {"name": "datadog-integration", "version": "1.3.0", "description": "..."},
# ]

# Install a plugin (pip install under the hood)
await marketplace.install("prometheus-exporter")
# Runs: pip install aquilia-mlops-prometheus-exporter

# Uninstall
await marketplace.uninstall("prometheus-exporter")
# Runs: pip uninstall aquilia-mlops-prometheus-exporter

# Index JSON format:
# {
#   "plugins": [
#     {
#       "name": "prometheus-exporter",
#       "version": "2.0.0",
#       "description": "Export MLOps metrics to Prometheus",
#       "package": "aquilia-mlops-prometheus-exporter",
#       "author": "community",
#       "tags": ["monitoring", "prometheus"]
#     }
#   ]
# }`} />
      </section>

      {/* Hook Events */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Available Hook Events</h2>
        <div className={boxClass}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className={`text-left ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  <th className="pb-2 pr-4">Event</th>
                  <th className="pb-2 pr-4">Trigger</th>
                  <th className="pb-2">Kwargs</th>
                </tr>
              </thead>
              <tbody className={isDark ? 'text-gray-300' : 'text-gray-700'}>
                {[
                  ['on_model_loaded', 'After model.load()', 'model_name, version'],
                  ['on_model_unloaded', 'After model.unload()', 'model_name'],
                  ['on_inference', 'After each prediction', 'model_name, latency_ms, batch_size'],
                  ['on_error', 'On inference error', 'model_name, error, request_id'],
                  ['on_drift_detected', 'When drift exceeds threshold', 'model_name, drift_report'],
                  ['on_rollout_started', 'Canary rollout begins', 'model_name, canary_version, weight'],
                  ['on_rollout_completed', 'Rollout finishes', 'model_name, version'],
                  ['on_rollback', 'Rollback triggered', 'model_name, from_version, to_version'],
                  ['on_health_check', 'Health endpoint called', 'model_name'],
                  ['on_circuit_open', 'Circuit breaker opens', 'model_name, failure_count'],
                ].map(([event, trigger, kwargs], i) => (
                  <tr key={i} className={`border-t ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                    <td className="py-1.5 pr-4 font-mono text-xs text-aquilia-500">{event}</td>
                    <td className={`py-1.5 pr-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{trigger}</td>
                    <td className={`py-1.5 font-mono text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{kwargs}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'Release & Rollouts', link: '/docs/mlops/release' },
          { text: 'Security', link: '/docs/mlops/security' },
          { text: 'Explainability', link: '/docs/mlops/explain' },
          { text: 'MLOps Tutorial', link: '/docs/mlops/tutorial' },
        ]}
      />
    </div>
  )
}
