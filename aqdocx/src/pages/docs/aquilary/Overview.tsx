import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Archive, ArrowLeft, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function AquilaryOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Archive className="w-4 h-4" />
          <span>ADVANCED / AQUILARY REGISTRY</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Aquilary Registry
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The Aquilary is Aquilia's manifest-driven module registry. It manages module declaration, resolves dependencies topologically, indexes route structures, and generates secure cryptographic fingerprints to enable deterministic hot-reloads.
        </p>
      </div>

      {/* Core Architectural Division */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Two-Phase Registry Lifecycle</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          To prevent import-time side effects and keep development tooling fast, Aquilia separates registry instantiation into two distinct phases:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <div className="border-l-2 border-aquilia-500/20 pl-6 py-2">
            <span className="font-mono text-xs text-white font-bold uppercase tracking-wider">1. Static Validation Phase</span>
            <p className="text-sm text-gray-400 mt-2 leading-relaxed">
              Executed by <DocTerm id="aquilary.AquilaryRegistry">AquilaryRegistry</DocTerm>. Reads manifest files without importing controllers or services. It checks route conflicts, resolves dependency cycles, and computes the load order topologically.
            </p>
          </div>
          <div className="border-l-2 border-aquilia-500/20 pl-6 py-2">
            <span className="font-mono text-xs text-white font-bold uppercase tracking-wider">2. Lazy Compilation Phase</span>
            <p className="text-sm text-gray-400 mt-2 leading-relaxed">
              Managed by <DocTerm id="aquilary.RuntimeRegistry">RuntimeRegistry</DocTerm>. Active only when bootstrapping the live ASGI server. Performs runtime package scans, imports user code, compiles route trees, and builds DI containers.
            </p>
          </div>
        </div>
      </section>

      {/* How it Works code */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Workspace Integration</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Your workspace structure declares the relationships between modules. Here's a clean workspace instantiation:
        </p>

        <CodeBlock language="python" filename="workspace.py" highlightLines={[6, 9, 10]}>{`from aquilia import Workspace, Module
from modules.users import UserController, UserService
from modules.products import ProductController, ProductService

workspace = Workspace(
    modules=[
        Module("users", controllers=[UserController], providers=[UserService]),
        Module("products", controllers=[ProductController], providers=[ProductService]),
        Module("orders",
            controllers=["modules.orders.controllers:OrderController"],
            providers=["modules.orders.services:OrderService"],
            imports=["users", "products"], # Declares load dependency
        ),
    ],
)`}</CodeBlock>
      </section>

      {/* Registry Verification */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>CLI Validation Tooling</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The CLI operates directly on the static metadata phase, inspecting the registry without importing user classes:
        </p>

        <CodeBlock language="shell" filename="Terminal">{`# 1. Validate manifest structure and dependency safety
aq validate

# 2. Inspect route structures
aq inspect routes

# 3. View module dependencies
aq inspect modules`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/middleware" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Middleware
        </Link>
        <Link to="/docs/aquilary/manifest" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Manifest System <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
