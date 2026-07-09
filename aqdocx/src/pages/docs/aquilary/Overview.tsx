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

        {/* Premium SVG Flow-Based Architecture Diagram */}
        <div className="w-full flex justify-center py-6 bg-transparent">
          <svg viewBox="0 0 900 340" className="w-full h-auto drop-shadow-2xl font-mono select-none">
            <defs>
              <linearGradient id="waveGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#22c55e" stopOpacity="0.9" />
                <stop offset="50%" stopColor="#3b82f6" stopOpacity="0.9" />
                <stop offset="100%" stopColor="#a855f7" stopOpacity="0.9" />
              </linearGradient>
              <radialGradient id="glowGreen" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#22c55e" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#22c55e" stopOpacity="0" />
              </radialGradient>
              <radialGradient id="glowBlue" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#3b82f6" stopOpacity="0" />
              </radialGradient>
              <radialGradient id="glowPurple" cx="50%" cy="50%" r="50%">
                <stop offset="0%" stopColor="#a855f7" stopOpacity="0.15" />
                <stop offset="100%" stopColor="#a855f7" stopOpacity="0" />
              </radialGradient>
              <filter id="glowFilter" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Glowing Halos Behind Nodes */}
            <circle cx="80" cy="170" r="50" fill="url(#glowGreen)" />
            <circle cx="240" cy="110" r="50" fill="url(#glowGreen)" />
            <circle cx="400" cy="90" r="50" fill="url(#glowBlue)" />
            <circle cx="560" cy="230" r="50" fill="url(#glowBlue)" />
            <circle cx="720" cy="190" r="50" fill="url(#glowPurple)" />
            <circle cx="840" cy="170" r="50" fill="url(#glowGreen)" />

            {/* Connecting Wave Lines (Bundle of Light Fibers) */}
            <path d="M 80 170 C 160 170, 160 110, 240 110 C 320 110, 320 90, 400 90 C 480 90, 480 230, 560 230 C 640 230, 640 190, 720 190 C 800 190, 800 170, 840 170" fill="none" stroke="url(#waveGrad)" strokeWidth="4.5" strokeLinecap="round" />
            <path d="M 80 170 C 160 170, 160 110, 240 110 C 320 110, 320 90, 400 90 C 480 90, 480 230, 560 230 C 640 230, 640 190, 720 190 C 800 190, 800 170, 840 170" fill="none" stroke="#ffffff" strokeWidth="1" strokeOpacity="0.25" strokeDasharray="4 8" strokeLinecap="round" />

            {/* Node 1: App Manifests */}
            <g transform="translate(80, 170)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#22c55e" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">APPMANIFESTS</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Declarative inputs</text>
            </g>

            {/* Node 2: Manifest Loading */}
            <g transform="translate(240, 110)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#22c55e" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">MANIFESTLOADER</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Safe loading (no imports)</text>
            </g>

            {/* Node 3: Validation */}
            <g transform="translate(400, 90)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#3b82f6" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#3b82f6" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">VALIDATION &amp; GRAPH</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Cycles &amp; Route conflicts</text>
            </g>

            {/* Node 4: Fingerprinted Metadata */}
            <g transform="translate(560, 230)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#3b82f6" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#3b82f6" />
              <text x="0" y="-24" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">AQUILARYREGISTRY</text>
              <text x="0" y="-12" textAnchor="middle" fontSize="8" fill="#71717a">Fingerprinted static state</text>
            </g>

            {/* Node 5: Lazy Auto-Discovery */}
            <g transform="translate(720, 190)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#a855f7" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#a855f7" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">AUTO-DISCOVERY</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">Lazy class load &amp; scan</text>
            </g>

            {/* Node 6: Runtime Registry */}
            <g transform="translate(840, 170)">
              <circle cx="0" cy="0" r="10" fill={isDark ? "#02040a" : "#ffffff"} stroke="#22c55e" strokeWidth="2.5" filter="url(#glowFilter)" />
              <circle cx="0" cy="0" r="4" fill="#22c55e" />
              <text x="0" y="32" textAnchor="middle" fontSize="10" fill={isDark ? "#e4e4e7" : "#1f2937"} fontWeight="bold">RUNTIMEREGISTRY</text>
              <text x="0" y="44" textAnchor="middle" fontSize="8" fill="#71717a">ASGI server compilation</text>
            </g>
          </svg>
        </div>

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
