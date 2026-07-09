import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Archive, ArrowLeft, ArrowRight } from 'lucide-react'

import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function AquilaryFingerprint() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Archive className="w-4 h-4" />
          <span>AQUILARY / FINGERPRINTING</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Registry Fingerprinting
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia uses content-addressable fingerprinting to verify application configuration state, detect hot-reload requirements, and guarantee reproducible production deployments.
        </p>
      </div>

      {/* How Fingerprints are Computed */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Deterministic SHA-256 Generation</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The <code className="text-aquilia-500">FingerprintGenerator</code> compiles a canonical dictionary representation of the application state, serializes it to sorted JSON, and computes a SHA-256 hash. To ensure reproducibility across local machines, Docker images, and cloud providers, it filters out environment variations:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8 text-sm">
          <div className="border-l-2 border-green-500/20 pl-6 py-2">
            <span className="font-mono text-xs text-green-400 font-bold uppercase tracking-wider">Included in Hash</span>
            <ul className="list-disc list-inside text-gray-400 mt-2 space-y-1">
              <li>App manifest names and versions</li>
              <li>Dependency relationships between modules</li>
              <li>Route paths, parameters, and HTTP methods</li>
              <li>Config keys and schemas (structure only)</li>
            </ul>
          </div>
          <div className="border-l-2 border-red-500/20 pl-6 py-2">
            <span className="font-mono text-xs text-red-400 font-bold uppercase tracking-wider">Excluded from Hash</span>
            <ul className="list-disc list-inside text-gray-400 mt-2 space-y-1">
              <li>Environment variable values</li>
              <li>Absolute path structures</li>
              <li>Build or compilation timestamps</li>
              <li>Active runtime container references</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Verifying Fingerprints</h2>
        <CodeBlock language="python" filename="verify_fingerprint.py" highlightLines={[6, 9]}>{`from aquilia.aquilary import FingerprintGenerator

# Compute the fingerprint of the live registry
generator = FingerprintGenerator()
fingerprint = generator.generate(app_contexts, config, mode)

print(f"Active Fingerprint: {fingerprint}")
# -> "8f9e1a2b3c4d5e6f..."

# If deployment fingerprint differs from frozen disk configuration:
# 1. Hot reload module registry
# 2. Re-compile route endpoints`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/aquilary/runtime" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Runtime Registry
        </Link>
        <Link to="/docs/effects" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Effects System <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
