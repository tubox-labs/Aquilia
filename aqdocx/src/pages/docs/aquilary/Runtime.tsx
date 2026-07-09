import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Archive, ArrowLeft, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function AquilaryRuntime() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Archive className="w-4 h-4" />
          <span>AQUILARY / RUNTIME REGISTRY</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Runtime Registry &amp; Discovery
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="aquilary.RuntimeRegistry">RuntimeRegistry</DocTerm> class compiles the static module graph metadata into a live application server state, performing package discovery, lazily importing controllers, and building DI containers.
        </p>
      </div>

      {/* Autodiscovery Flow */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Auto-Discovery Phases</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          When calling <code className="text-aquilia-500">perform_autodiscovery()</code>, the registry scans <code className="text-white">modules.{"{module_name}"}</code> recursively up to a depth of 5, identifying and importing classes matching predicate rules:
        </p>

        <div className="space-y-6 mb-8">
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">1. Controller Scanning</span>
            <p className="text-sm text-gray-400 mt-1">Discovers classes whose names end with <code className="text-aquilia-400">"Controller"</code> or that directly inherit from <DocTerm id="controller.controller">Controller</DocTerm>.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">2. Service Scanning</span>
            <p className="text-sm text-gray-400 mt-1">Discovers dependency injection services whose names end with <code className="text-aquilia-400">"Service"</code> or declare the <code className="text-aquilia-400">__di_scope__</code> attribute.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">3. Socket Controllers</span>
            <p className="text-sm text-gray-400 mt-1">Scans for classes decorated with <code className="text-aquilia-400">@Socket</code> or whose names end with <code className="text-aquilia-400">"SocketController"</code>.</p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-4 py-1">
            <span className="font-mono text-xs text-white font-bold">4. Tasks and Models</span>
            <p className="text-sm text-gray-400 mt-1">Imports <code className="text-aquilia-400">tasks.py</code> to trigger background task registrations, and scans database models to catalog schemas.</p>
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Bootstrapping</h2>
        <CodeBlock language="python" filename="bootstrap.py" highlightLines={[6, 9]}>{`from aquilia.aquilary import RuntimeRegistry

# 1. Instantiate runtime registry from compiled metadata
runtime = RuntimeRegistry.from_metadata(registry_meta, config)

# 2. Perform autodiscovery package scan (depth=5)
runtime.perform_autodiscovery()

# 3. Import controllers and build the ASGI route tables
runtime.compile_routes()`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/aquilary/manifest" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Manifest System
        </Link>
        <Link to="/docs/aquilary/fingerprint" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Fingerprinting <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
