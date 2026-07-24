import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Archive, ArrowLeft, ArrowRight } from 'lucide-react'

import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function AquilaryManifest() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Archive className="w-4 h-4" />
          <span>AQUILARY / MANIFEST SYSTEM</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Manifest Loading &amp; Validation
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The manifest system provides safe, import-free module discovery. By loading declarations lazily, Aquilia compiles dependency layouts without executing user module imports.
        </p>
      </div>

      {/* ManifestLoader API */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>ManifestLoader</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The <code className="text-aquilia-500">ManifestLoader</code> class parses manifest specifications from multiple sources. It accepts a list of sources—which can be direct Python manifest classes, absolute/relative paths to Python manifest files, or DSL (YAML/JSON) files:
        </p>

        <CodeBlock language="python" filename="manifest_load.py" highlightLines={[6, 9]}>{`from aquilia.aquilary import ManifestLoader

loader = ManifestLoader()

# Load multiple modules from mixed sources (safe, no import side effects)
manifests = loader.load_manifests(
    sources=[
        "modules/auth/manifest.py",
        "modules/users/manifest.yaml", # DSL config support
    ],
    allow_fs_autodiscovery=True # Scan standard directories
)

for m in manifests:
    print(f"Loaded: {m.name} v{m.version} [Origin: {m.__source__}]")`}</CodeBlock>
      </section>

      {/* RegistryValidator */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Registry Validation</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Once loaded, the <code className="text-aquilia-500">RegistryValidator</code> inspects the manifest declarations. It compiles a validation report covering schema compatibility, route collisions, and duplicate app declarations:
        </p>

        <CodeBlock language="python" filename="validate_registry.py" highlightLines={[6]}>{`from aquilia.aquilary import RegistryValidator, RegistryMode

validator = RegistryValidator(mode=RegistryMode.PROD)

# Run validations on manifests
report = validator.validate_manifests(
    manifests,
    config,
    workspace_modules=workspace_modules_config
)

if report.has_errors():
    raise Exception(report.to_exception())`}</CodeBlock>
      </section>

      {/* Validation Checks Table */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Core Validation Rules</h2>
        <div className="w-full overflow-x-auto font-sans">
          <table className="w-full text-sm text-left border-collapse">
            <thead>
              <tr className="border-b border-white/10 text-aquilia-400 font-mono text-xs uppercase tracking-wider">
                <th className="py-3 px-4">Validation Code</th>
                <th className="py-3 px-4">Focus</th>
                <th className="py-3 px-4">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5 text-gray-400 text-xs">
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3.5 px-4 font-mono text-aquilia-300">DuplicateAppError</td>
                <td className="py-3.5 px-4">Uniqueness</td>
                <td className="py-3.5 px-4">Triggers if two modules declare the exact same name.</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3.5 px-4 font-mono text-aquilia-300">RouteConflictError</td>
                <td className="py-3.5 px-4">Routing</td>
                <td className="py-3.5 px-4">Flags overlapping paths or colliding HTTP endpoint route templates.</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3.5 px-4 font-mono text-aquilia-300">DependencyCycleError</td>
                <td className="py-3.5 px-4">Topology</td>
                <td className="py-3.5 px-4">Raised when circular dependencies exist between module imports.</td>
              </tr>
              <tr className="hover:bg-white/2 transition-colors">
                <td className="py-3.5 px-4 font-mono text-aquilia-300">DeprecationWarning</td>
                <td className="py-3.5 px-4">Legacy</td>
                <td className="py-3.5 px-4">Emitted when using the deprecated <code>depends_on</code> argument instead of <code>imports</code>.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      {/* Bidirectional Sync */}
      <section className="mb-16" id="imports-sync">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6 flex items-center gap-2`}>
          Bidirectional Sync — imports ↔ depends_on <span className="bg-aquilia-500/20 text-aquilia-300 text-xs px-2 py-1 rounded">v1.3.4</span>
        </h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The <code>AppManifest.__post_init__</code> hook now keeps <code>imports</code> and <code>depends_on</code> in sync automatically.
        </p>
        <ul className={`list-disc list-inside mb-6 space-y-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <li>Using <code>imports=[...]</code> is preferred, and auto-populates <code>depends_on</code>.</li>
          <li>Using <code>depends_on=[...]</code> auto-populates <code>imports</code> but emits a <code>DeprecationWarning</code>.</li>
        </ul>
        <CodeBlock language="python" filename="manifest_sync.py">{`from aquilia import AppManifest

# Preferred
manifest1 = AppManifest(
    name="users",
    imports=["auth"] # depends_on automatically set to ["auth"]
)

# Deprecated (emits warning)
manifest2 = AppManifest(
    name="billing",
    depends_on=["users"] # imports automatically set to ["users"]
)`}</CodeBlock>
      </section>

      {/* Two-Phase Manifest Loading */}
      <section className="mb-16" id="two-phase-loading">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6 flex items-center gap-2`}>
          Two-Phase Manifest Loading <span className="bg-aquilia-500/20 text-aquilia-300 text-xs px-2 py-1 rounded">v1.3.4</span>
        </h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The <code>ManifestLoader</code> now uses a two-phase loading strategy: an AST-based primary path and an exec fallback.
        </p>
        <ul className={`list-disc list-inside mb-6 space-y-2 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <li><strong>Phase 1: AST path</strong> — Handles simple manifests with zero side effects, fast and safe.</li>
          <li><strong>Phase 2: exec fallback</strong> — Handles complex manifests (e.g., dynamic imports). Emits a logged warning.</li>
        </ul>
        <CodeBlock language="python" filename="two_phase_loading.py">{`# Phase 1: Resolved via AST (Fast, safe)
manifest = AppManifest(
    name="auth",
    version="1.0.0"
)

# Phase 2: Falls back to exec (Logs warning about side effects)
DYNAMIC_VERSION = os.getenv("VERSION", "1.0.0")
manifest = AppManifest(
    name="billing",
    version=DYNAMIC_VERSION
)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/aquilary/overview" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/aquilary/runtime" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Runtime Registry <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}