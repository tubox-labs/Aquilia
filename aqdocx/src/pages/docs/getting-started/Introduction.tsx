import { useState } from 'react'
import { useVersion } from '../../../hooks/useVersion'
import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { NextSteps } from '../../../components/NextSteps'
import {
  Zap, Layers, Database, Plug, Cpu, Globe,
  Rocket, Box, Terminal, Code2, GitBranch, Copy
} from 'lucide-react'

const RequestLifecycle = () => {
  const steps = [
    { id: 'request', label: 'Request', icon: <Globe className="w-4 h-4" />, color: 'text-blue-400', bg: 'bg-blue-500/10' },
    { id: 'middleware', label: 'Middleware', icon: <Layers className="w-4 h-4" />, color: 'text-purple-400', bg: 'bg-purple-500/10' },
    { id: 'router', label: 'Router', icon: <GitBranch className="w-4 h-4" />, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
    { id: 'controller', label: 'Controller', icon: <Code2 className="w-4 h-4" />, color: 'text-amber-400', bg: 'bg-amber-500/10' },
    { id: 'di', label: 'DI Container', icon: <Plug className="w-4 h-4" />, color: 'text-pink-400', bg: 'bg-pink-500/10' },
    { id: 'response', label: 'Response', icon: <Zap className="w-4 h-4" />, color: 'text-aquilia-400', bg: 'bg-aquilia-500/10' },
  ]

  return (
    <div className="relative py-12">
      {/* Connection Line */}
      <div className="absolute top-1/2 left-0 w-full h-0.5 bg-gradient-to-r from-transparent via-gray-700 to-transparent -translate-y-1/2 opacity-30" />

      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 relative z-10">
        {steps.map((step, i) => (
          <motion.div
            key={step.id}
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: i * 0.1 }}
            className="flex flex-col items-center gap-3"
          >
            <div className={`w-12 h-12 rounded-xl flex items-center justify-center backdrop-blur-sm border border-white/10 ${step.bg} ${step.color} shadow-lg shadow-black/20`}>
              {step.icon}
            </div>
            <div className="text-xs font-mono font-medium opacity-60">{step.label}</div>

            {/* Flow Particles */}
            {i < steps.length - 1 && (
              <div className="hidden lg:block absolute top-1/2 left-[calc(16.66%*${i}+8.33%)] w-[16.66%] h-0.5 -translate-y-1/2 overflow-hidden pointer-events-none">
                <motion.div
                  className={`w-1/2 h-full bg-gradient-to-r from-transparent to-${step.color.split('-')[1]}-500/50`}
                  animate={{ x: ['-100%', '200%'] }}
                  transition={{ duration: 1.5, repeat: Infinity, ease: "linear", delay: i * 0.2 }}
                />
              </div>
            )}
          </motion.div>
        ))}
      </div>
    </div>
  )
}

const FEATURE_SPINE_DATA = [
  {
    left: {
      id: 'aquilary',
      title: 'Manifest-Driven Registry',
      pkg: 'aquilia.aquilary',
      file: 'aquilia/aquilary/__init__.py',
      desc: 'Declare application topologies via explicit Python manifests. Compiles into an immutable artifact graph at startup, eliminating import-time discovery magic.',
      color: '#10b981'
    },
    right: {
      id: 'routing',
      title: 'Flow Routing Engine',
      pkg: 'aquilia.controller',
      file: 'aquilia/controller/__init__.py',
      desc: 'Class-based routing and controller architecture. Decoupled request and response contexts, content negotiation, and full middleware pipeline integration.',
      color: '#06b6d4'
    }
  },
  {
    left: {
      id: 'di',
      title: 'Async-First DI Container',
      pkg: 'aquilia.di',
      file: 'aquilia/di/__init__.py',
      desc: 'Six injection scopes (singleton, app, request, transient, pooled, ephemeral) with sub-3µs cached resolutions, cycle detection, and complete graph diagnostics.',
      color: '#3b82f6'
    },
    right: {
      id: 'cache',
      title: 'Multi-Layer Caching',
      pkg: 'aquilia.cache',
      file: 'aquilia/cache/__init__.py',
      desc: 'LRU/LFU memory, Redis, and multi-tier L1+L2 composite backends. Declarative caching using @cached, @cache_aside, and automated cache invalidation.',
      color: '#f59e0b'
    }
  },
  {
    left: {
      id: 'orm',
      title: 'Pure-Python ORM',
      pkg: 'aquilia.models',
      file: 'aquilia/models/__init__.py',
      desc: 'Metaclass-driven ORM with Q-object QuerySets, built-in sqlite integration, automated migrations, model signals, transactions, and aggregations.',
      color: '#a855f7'
    },
    right: {
      id: 'sockets',
      title: 'WebSocket Controllers',
      pkg: 'aquilia.sockets',
      file: 'aquilia/sockets/__init__.py',
      desc: 'Decorator-driven WebSocket event handlers with per-connection dependency injection, connection room management, and pluggable Redis adapter backends.',
      color: '#8b5cf6'
    }
  },
  {
    left: {
      id: 'security',
      title: 'Clearance Security',
      pkg: 'aquilia.auth.clearance',
      file: 'aquilia/auth/clearance.py',
      desc: 'Declarative access control, clearance guards, JWT token authentication, Argon2 password hashing, RBAC/ABAC authorization, and session policy enforcement.',
      color: '#f43f5e'
    },
    right: {
      id: 'faults',
      title: 'Typed Fault System',
      pkg: 'aquilia.faults',
      file: 'aquilia/faults/__init__.py',
      desc: 'Structured exception mapping with severity levels and recovery rules. The central FaultEngine translates raw uncaught exceptions into typed JSON faults.',
      color: '#f97316'
    }
  },
  {
    left: {
      id: 'admin',
      title: 'Admin Dashboard Integration',
      pkg: 'aquilia.admin',
      file: 'aquilia/admin/__init__.py',
      desc: 'Automatic admin module registration, monitoring telemetry, task status overview, user management, and security audit logs.',
      color: '#ec4899'
    },
    right: {
      id: 'db',
      title: 'Database & Migrations',
      pkg: 'aquilia.db',
      file: 'aquilia/db/__init__.py',
      desc: 'Typed DB configurations, SQLite drivers, schema snapshots, migration generation (makemigrations), status checks, and rollbacks.',
      color: '#06b6d4'
    }
  },
  {
    left: {
      id: 'storage',
      title: 'Unified Cloud Storage',
      pkg: 'aquilia.storage',
      file: 'aquilia/storage/__init__.py',
      desc: 'Abstractions for Local, S3, GCS, Azure, and SFTP providers, featuring streaming buffers, registry configurations, and secure write boundaries.',
      color: '#f43f5e'
    },
    right: {
      id: 'tasks',
      title: 'Task Worker & Scheduler',
      pkg: 'aquilia.tasks',
      file: 'aquilia/tasks/__init__.py',
      desc: 'Decorator-driven @task registries, task worker pools, interval loops, cron schedules, memory/Redis queues, and automatic startup initialization.',
      color: '#eab308'
    }
  },
  {
    left: {
      id: 'mcp',
      title: 'Model Context Protocol (MCP)',
      pkg: 'aquilia.mcp',
      file: 'aquilia/mcp/__init__.py',
      desc: 'Native Model Context Protocol (MCP) server sidecar. Exposes codebase tools, structured resources, and api schemas directly to AI agents.',
      color: '#6366f1'
    },
    right: {
      id: 'versioning',
      title: 'API Versioning Engine',
      pkg: 'aquilia.versioning',
      file: 'aquilia/versioning/__init__.py',
      desc: 'Decorator-based route versioning, version negotiation, client cookie/header version targeting, deprecation timelines, and header responders.',
      color: '#14b8a6'
    }
  },
  {
    left: {
      id: 'templates',
      title: 'Sandboxed Templates & Mail',
      pkg: 'aquilia.templates',
      file: 'aquilia/templates/__init__.py',
      desc: 'Sandboxed Jinja template engine loader, secure context isolation, SMTP mail providers, and structured email envelope builders.',
      color: '#a855f7'
    },
    right: {
      id: 'i18n',
      title: 'Internationalization (i18n)',
      pkg: 'aquilia.i18n',
      file: 'aquilia/i18n/__init__.py',
      desc: 'Locale translation extractors, GNU gettext catalog compilation, plural formatting rules, and middleware language negotiaton.',
      color: '#84cc16'
    }
  },
  {
    left: {
      id: 'otel',
      title: 'OpenTelemetry & Observability',
      pkg: 'aquilia.otel',
      file: 'aquilia/otel/__init__.py',
      desc: 'Tracing telemetry middleware, OpenTelemetry exporter integration, request metrics tracking, system CPU/memory timings, and structured logs.',
      color: '#ef4444'
    },
    right: {
      id: 'sse',
      title: 'Server-Sent Events (SSE)',
      pkg: 'aquilia.sse',
      file: 'aquilia/sse/__init__.py',
      desc: 'Async Server-Sent Events stream controller, broadcast event formatting rules, and client stream connectivity state management.',
      color: '#3b82f6'
    }
  },
  {
    left: {
      id: 'testing',
      title: 'Test & Diagnostics SDK',
      pkg: 'aquilia.testing',
      file: 'aquilia/testing/__init__.py',
      desc: 'Diagnostics inspection framework, AquiliaTestCase test suites, async TestClient request adapters, and WebSocketTestClient connections.',
      color: '#10b981'
    },
    right: {
      id: 'filesystem',
      title: 'Secure Filesystem Layer',
      pkg: 'aquilia.filesystem',
      file: 'aquilia/filesystem/__init__.py',
      desc: 'Async filesystem operations, secure path validation against traversal attacks, and sandboxed directory execution contexts.',
      color: '#f97316'
    }
  }
]

function FeatureArchitectureVisualizer({ isDark }: { isDark: boolean }) {
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  return (
    <div className="my-12 flex flex-col items-center w-full font-sans select-none">
      {/* Central spine header */}
      <div className="hidden md:flex flex-col items-center mb-2">
        <span className={`text-[8px] font-mono tracking-widest px-2 py-0.5 rounded border ${
          isDark ? 'border-zinc-800 bg-zinc-900/60 text-zinc-500' : 'border-gray-200 bg-gray-50 text-gray-500'
        }`}>
          AQUILIA CORE ENGINE
        </span>
        <div className={`w-[1px] h-10 ${isDark ? 'bg-zinc-800' : 'bg-gray-200'}`} />
      </div>

      <div className="w-full space-y-8 md:space-y-0">
        {FEATURE_SPINE_DATA.map((row, idx) => {
          const isLeftHovered = hoveredId === row.left.id;
          const isRightHovered = hoveredId === row.right.id;
          const anyHovered = hoveredId !== null;

          return (
            <div key={idx} className="flex flex-col md:grid md:grid-cols-[1fr_100px_1fr] items-center gap-4 md:gap-0">
              
              {/* Left Subsystem */}
              <div 
                onMouseEnter={() => setHoveredId(row.left.id)}
                onMouseLeave={() => setHoveredId(null)}
                className={`text-left md:text-right pr-0 md:pr-6 cursor-default transition-all duration-300 transform ${
                  isLeftHovered 
                    ? 'scale-[1.02] md:-translate-x-1' 
                    : anyHovered 
                      ? 'opacity-25 scale-[0.98]' 
                      : ''
                }`}
              >
                <div className="flex flex-col gap-1 md:items-end">
                  <span className={`text-[9px] font-mono font-semibold`} style={{ color: row.left.color }}>
                    {row.left.pkg}
                  </span>
                  <h4 className={`text-sm font-mono font-bold transition-colors ${
                    isLeftHovered 
                      ? (isDark ? 'text-white' : 'text-gray-900') 
                      : (isDark ? 'text-zinc-300' : 'text-gray-800')
                  }`}>
                    {row.left.title}
                  </h4>
                  <p className={`text-xs leading-relaxed font-light mt-1 max-w-sm ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
                    {row.left.desc}
                  </p>
                  <a
                    href={`file:///Users/kuroyami/TuboxLabProject/Aquilia/${row.left.file}`}
                    className={`font-mono text-[9px] font-medium hover:underline transition-colors mt-2 ${
                      isLeftHovered 
                        ? 'text-emerald-400' 
                        : (isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-gray-400 hover:text-gray-600')
                    }`}
                  >
                    • {row.left.file}
                  </a>
                </div>
              </div>

              {/* Middle Connection SVG (Visible on Desktop only) */}
              <div className="hidden md:block w-[100px] h-[140px] relative">
                <svg viewBox="0 0 100 140" className="w-full h-full bg-transparent overflow-visible">
                  <defs>
                    <linearGradient id={`left-grad-${idx}`} x1="100%" y1="0%" x2="0%" y2="0%">
                      <stop offset="0%" stopColor={isDark ? "#121214" : "#f3f4f6"} stopOpacity="0.2" />
                      <stop offset="100%" stopColor={row.left.color} />
                    </linearGradient>
                    <linearGradient id={`right-grad-${idx}`} x1="0%" y1="0%" x2="100%" y2="0%">
                      <stop offset="0%" stopColor={isDark ? "#121214" : "#f3f4f6"} stopOpacity="0.2" />
                      <stop offset="100%" stopColor={row.right.color} />
                    </linearGradient>
                  </defs>

                  {/* Vertical Spine segment */}
                  <line 
                    x1="50" y1="0" x2="50" y2="140" 
                    stroke={isDark ? "#18181b" : "#f3f4f6"} 
                    strokeWidth="1.5" 
                  />

                  {/* Central Spine timeline micro-particles (Always flowing downwards) */}
                  <motion.circle
                    cx="50"
                    r="1.2"
                    fill={isDark ? "#3f3f46" : "#cbd5e1"}
                    animate={{ cy: [0, 140] }}
                    transition={{ repeat: Infinity, duration: 3, ease: "linear", delay: idx * 0.5 }}
                  />

                  {/* LEFT BRANCH (Y-Curve) */}
                  {/* Glowing aura if hovered */}
                  {isLeftHovered && (
                    <path 
                      d="M 50,55 C 35,55 30,75 15,75" 
                      fill="none" 
                      stroke={row.left.color} 
                      strokeWidth="5" 
                      opacity="0.25"
                      className="blur-[2px]"
                    />
                  )}
                  <path 
                    d="M 50,55 C 35,55 30,75 15,75" 
                    fill="none" 
                    stroke={isLeftHovered ? row.left.color : `url(#left-grad-${idx})`} 
                    strokeWidth={isLeftHovered ? "1.8" : "1.2"} 
                    opacity={isLeftHovered ? "1" : anyHovered ? "0.15" : "0.7"}
                    className="transition-all duration-300"
                  />
                  {/* Left flowing pulse */}
                  <motion.circle
                    r={isLeftHovered ? "2.5" : "1.8"}
                    fill={row.left.color}
                    animate={{ cx: [50, 15] }}
                    transition={{ 
                      repeat: Infinity, 
                      duration: isLeftHovered ? 1.0 : 2.2, 
                      ease: "easeInOut", 
                      delay: idx * 0.2 
                    }}
                    opacity={anyHovered && !isLeftHovered ? "0.1" : "0.8"}
                    cy="75"
                  />
                  {/* Left Tip dot */}
                  <circle 
                    cx="15" cy="75" 
                    r={isLeftHovered ? "4" : "2.5"} 
                    fill={row.left.color} 
                    opacity={anyHovered && !isLeftHovered ? "0.15" : "1"}
                    className="transition-all duration-300"
                  />

                  {/* RIGHT BRANCH (Y-Curve) */}
                  {/* Glowing aura if hovered */}
                  {isRightHovered && (
                    <path 
                      d="M 50,55 C 65,55 70,75 85,75" 
                      fill="none" 
                      stroke={row.right.color} 
                      strokeWidth="5" 
                      opacity="0.25"
                      className="blur-[2px]"
                    />
                  )}
                  <path 
                    d="M 50,55 C 65,55 70,75 85,75" 
                    fill="none" 
                    stroke={isRightHovered ? row.right.color : `url(#right-grad-${idx})`} 
                    strokeWidth={isRightHovered ? "1.8" : "1.2"} 
                    opacity={isRightHovered ? "1" : anyHovered ? "0.15" : "0.7"}
                    className="transition-all duration-300"
                  />
                  {/* Right flowing pulse */}
                  <motion.circle
                    r={isRightHovered ? "2.5" : "1.8"}
                    fill={row.right.color}
                    animate={{ cx: [50, 85] }}
                    transition={{ 
                      repeat: Infinity, 
                      duration: isRightHovered ? 1.0 : 2.2, 
                      ease: "easeInOut", 
                      delay: idx * 0.2 + 0.4 
                    }}
                    opacity={anyHovered && !isRightHovered ? "0.1" : "0.8"}
                    cy="75"
                  />
                  {/* Right Tip dot */}
                  <circle 
                    cx="85" cy="75" 
                    r={isRightHovered ? "4" : "2.5"} 
                    fill={row.right.color} 
                    opacity={anyHovered && !isRightHovered ? "0.15" : "1"}
                    className="transition-all duration-300"
                  />

                  {/* Central Hub Junction dot */}
                  <circle 
                    cx="50" cy="55" 
                    r={isLeftHovered || isRightHovered ? "5" : "3.5"} 
                    fill={isDark ? "#000000" : "#ffffff"} 
                    stroke={isLeftHovered ? row.left.color : isRightHovered ? row.right.color : (isDark ? "#3f3f46" : "#cbd5e1")} 
                    strokeWidth="2" 
                    className="transition-all duration-300"
                  />
                </svg>
              </div>

              {/* Right Subsystem */}
              <div 
                onMouseEnter={() => setHoveredId(row.right.id)}
                onMouseLeave={() => setHoveredId(null)}
                className={`text-left pl-0 md:pl-6 cursor-default transition-all duration-300 transform ${
                  isRightHovered 
                    ? 'scale-[1.02] md:translate-x-1' 
                    : anyHovered 
                      ? 'opacity-25 scale-[0.98]' 
                      : ''
                }`}
              >
                <div className="flex flex-col gap-1 items-start">
                  <span className={`text-[9px] font-mono font-semibold`} style={{ color: row.right.color }}>
                    {row.right.pkg}
                  </span>
                  <h4 className={`text-sm font-mono font-bold transition-colors ${
                    isRightHovered 
                      ? (isDark ? 'text-white' : 'text-gray-900') 
                      : (isDark ? 'text-zinc-300' : 'text-gray-800')
                  }`}>
                    {row.right.title}
                  </h4>
                  <p className={`text-xs leading-relaxed font-light mt-1 max-w-sm ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
                    {row.right.desc}
                  </p>
                  <a
                    href={`file:///Users/kuroyami/TuboxLabProject/Aquilia/${row.right.file}`}
                    className={`font-mono text-[9px] font-medium hover:underline transition-colors mt-2 ${
                      isRightHovered 
                        ? 'text-emerald-400' 
                        : (isDark ? 'text-zinc-500 hover:text-zinc-300' : 'text-gray-400 hover:text-gray-600')
                    }`}
                  >
                    • {row.right.file}
                  </a>
                </div>
              </div>

            </div>
          );
        })}
      </div>

      {/* Central spine footer */}
      <div className="hidden md:flex flex-col items-center mt-2">
        <div className={`w-[1px] h-10 bg-gradient-to-b ${isDark ? 'from-zinc-800 to-transparent' : 'from-gray-200 to-transparent'}`} />
      </div>
    </div>
  );
}

export function IntroductionPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const version = useVersion()
  const codename = version.startsWith('1.3') ? "Poseidon's Trident" : version.startsWith('1.2') ? "Kraken's Wake" : "Genesis"

  return (
    <div className="max-w-4xl mx-auto">
      {/* Hero */}
      <div className="relative mb-12">
        <div className="absolute -inset-4 bg-gradient-to-r from-aquilia-500/10 via-blue-500/5 to-purple-500/10 rounded-3xl blur-2xl print:hidden" />
        <div className="relative">
          <div className="flex items-center gap-3 mb-4">
            <img src="/logo.png" alt="Aquilia" className="w-12 h-12 rounded-2xl shadow-lg shadow-aquilia-500/20" />
            <div>
              <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
                <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                  Aquilia Framework
                  <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
                </span>
              </h1>
              <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>v{version} ("{codename}") · Production-ready async Python web framework</p>
            </div>
          </div>

          <p className={`text-lg leading-relaxed mb-6 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
            <strong>Stop writing routing, config, and deployment boilerplate. Focus only on business logic.</strong>
          </p>

          <div className="flex flex-col items-start gap-6 mb-12">
            <div className="flex flex-wrap gap-4">
              <Link
                to="/docs/quickstart"
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-aquilia-600 hover:bg-aquilia-500 text-white font-semibold shadow-lg shadow-aquilia-500/20 transition-all hover:scale-105 active:scale-95"
              >
                <Rocket className="w-5 h-5" />
                Quick Start
              </Link>
              <Link
                to="/docs/architecture"
                className={`flex items-center gap-2 px-6 py-3 rounded-xl border font-semibold transition-all hover:scale-105 active:scale-95 ${isDark ? 'border-white/10 hover:bg-white/5 text-gray-300 hover:text-white' : 'border-gray-200 hover:bg-gray-50 text-gray-700'}`}
              >
                <Cpu className="w-5 h-5" />
                Architecture
              </Link>
            </div>

            {/* Quick Install */}
            <div className="flex flex-col sm:flex-row gap-3">
              <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border font-mono text-sm ${isDark ? 'bg-black/40 border-white/10 text-gray-400' : 'bg-gray-50 border-gray-200 text-gray-600'}`}>
                <span className="text-aquilia-500">$</span>
                <span>pip install aquilia</span>
                <button
                  onClick={() => navigator.clipboard.writeText('pip install aquilia')}
                  className="ml-4 p-1.5 rounded-lg hover:bg-white/10 transition-colors text-gray-500 hover:text-aquilia-400"
                  title="Copy to clipboard"
                >
                  <Copy className="w-3.5 h-3.5" />
                </button>
              </div>
              <div className={`flex items-center gap-3 px-4 py-3 rounded-xl border font-mono text-sm ${isDark ? 'bg-black/40 border-white/10 text-gray-400' : 'bg-gray-50 border-gray-200 text-gray-600'}`}>
                <span className="text-aquilia-500">$</span>
                <span>uv pip install aquilia</span>
                <button
                  onClick={() => navigator.clipboard.writeText('uv pip install aquilia')}
                  className="ml-4 p-1.5 rounded-lg hover:bg-white/10 transition-colors text-gray-500 hover:text-aquilia-400"
                  title="Copy to clipboard"
                >
                  <Copy className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          </div>

          <div className={`grid grid-cols-1 md:grid-cols-2 gap-6 mt-8`}>
            <div>
              <h3 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>What is Aquilia?</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Aquilia is an async-first Python framework built on an <strong>auto-discovery architecture</strong>. It features a built-in ORM, production-ready infrastructure generation, and ML deployment built-in. It removes the friction of wiring components together manually.
              </p>
            </div>
            <div>
              <h3 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Who is it for?</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                Teams building production APIs who want clean architecture, auto-discovery, and built-in deployment tooling without the wiring boilerplate of microframeworks or the bloat of legacy monoliths.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Core Philosophy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Core Philosophy
        </h2>
        <p className={`text-xs ${isDark ? 'text-zinc-500' : 'text-gray-500'} mb-10`}>
          Aquilia shifts framework architecture from manual configuration boilerplate to declarative autodiscovery.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-x-16 gap-y-10">
          
          {/* Row 1 */}
          <div>
            <span className="text-[10px] font-mono font-bold tracking-widest text-rose-500/80 uppercase">
              ✕ Legacy Wiring
            </span>
            <p className={`text-xs mt-2 font-light leading-relaxed ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
              Manual configuration of components, services, and routing topologies. Wiring boilerplate accumulates as the codebase grows.
            </p>
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold tracking-widest text-emerald-500 uppercase">
              ✓ Auto-Discovery
            </span>
            <p className={`text-xs mt-2 font-light leading-relaxed ${isDark ? 'text-zinc-200' : 'text-gray-800'}`}>
              Programmatic registry structures the module and DI graph automatically. Sensible defaults eliminate setup overhead.
            </p>
          </div>

          {/* Row 2 */}
          <div>
            <span className="text-[10px] font-mono font-bold tracking-widest text-rose-500/80 uppercase">
              ✕ Manual Infra
            </span>
            <p className={`text-xs mt-2 font-light leading-relaxed ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
              Deployment infrastructure, Dockerfiles, and container charts are treated as an afterthought left to separate operations.
            </p>
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold tracking-widest text-emerald-500 uppercase">
              ✓ Infra Generation
            </span>
            <p className={`text-xs mt-2 font-light leading-relaxed ${isDark ? 'text-zinc-200' : 'text-gray-800'}`}>
              First-class generators build production Render, Docker, and Kubernetes configurations natively from the code topology.
            </p>
          </div>

          {/* Row 3 */}
          <div>
            <span className="text-[10px] font-mono font-bold tracking-widest text-rose-500/80 uppercase">
              ✕ Fragile MLOps
            </span>
            <p className={`text-xs mt-2 font-light leading-relaxed ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
              Machine Learning serving, metrics, and experimental tracking require building a separate, disjointed middleware stack.
            </p>
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold tracking-widest text-emerald-500 uppercase">
              ✓ Integrated ML
            </span>
            <p className={`text-xs mt-2 font-light leading-relaxed ${isDark ? 'text-zinc-200' : 'text-gray-800'}`}>
              Integrated MLOps serving, experimental tracking, and pipeline plugins are supported out of the box by the runtime.
            </p>
          </div>

          {/* Row 4 */}
          <div>
            <span className="text-[10px] font-mono font-bold tracking-widest text-rose-500/80 uppercase">
              ✕ Boilerplate Overhead
            </span>
            <p className={`text-xs mt-2 font-light leading-relaxed ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
              Writing repetitive boilerplate code for session storage, clearance guards, cache invalidation, and task queue workers.
            </p>
          </div>
          <div>
            <span className="text-[10px] font-mono font-bold tracking-widest text-emerald-500 uppercase">
              ✓ Unified Modules
            </span>
            <p className={`text-xs mt-2 font-light leading-relaxed ${isDark ? 'text-zinc-200' : 'text-gray-800'}`}>
              Unified batteries-included modules cover clearance access levels, multi-layer caching, mail, and worker pools.
            </p>
          </div>

        </div>
      </section>

      {/* Feature Architecture Overview */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-2 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          Feature Architecture
        </h2>
        <p className={`text-xs ${isDark ? 'text-zinc-500' : 'text-gray-500'} mb-6`}>
          Click on any node in the tactical radar engine schema to inspect its subsystem mapping, declarative syntax, and source code files.
        </p>

        <FeatureArchitectureVisualizer isDark={isDark} />
      </section>

      {/* Pipeline overview */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Cpu className="w-5 h-5 text-aquilia-400" />
          Architecture at a Glance
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia boots using a programmatic entrypoint that loads the workspace, resolves integrations, auto-discovers manifests, and instantiates the ASGI application:
        </p>

        <div className="mb-6">
          <p className={`text-sm font-mono mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>app.py</p>
          <CodeBlock
            code={`from pathlib import Path
from aquilia.runtime import AquiliaRuntime

_WORKSPACE_ROOT = Path(__file__).resolve().parent.parent

# Boots the entire workspace: configures config loader, auto-discovers manifests, and constructs the DI containers
runtime = AquiliaRuntime.from_workspace(
    workspace_root=_WORKSPACE_ROOT,
    mode="prod",
)
app = runtime.app`}
            language="python"
          />
        </div>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Once booted, inbound requests flow through a deterministic pipeline:
        </p>

        <div className={`rounded-3xl overflow-hidden relative`}>
          <div className="absolute inset-0 opacity-20" style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, rgba(255,255,255,0.1) 1px, transparent 0)', backgroundSize: '20px 20px' }}></div>
          <RequestLifecycle />
        </div>
      </section>

      {/* Minimal Example */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Rocket className="w-5 h-5 text-aquilia-400" />
          Minimal Example
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          A complete Aquilia application with a modern manifest-driven structure, typed database integration, pure-Python ORM model, validation blueprint, service, and controller:
        </p>

        <div className="space-y-4">
          <div>
            <p className={`text-sm font-mono mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>workspace.py</p>
            <CodeBlock
              code={`from aquilia import Workspace, Module
from aquilia.integrations import DatabaseIntegration

workspace = (
    Workspace("my-api")
    .module(
        Module("core")
        .route_prefix("/core")
        .auto_discover(True)
    )
    .integrate(
        DatabaseIntegration(url="sqlite:///db.sqlite3")
    )
)`}
              language="python"
            />
          </div>

          <div>
            <p className={`text-sm font-mono mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>modules/core/manifest.py</p>
            <CodeBlock
              code={`from aquilia import AppManifest

manifest = AppManifest(
    name="core",
    version="1.0.0",
    description="Core module",
    controllers=["modules.core.controllers:UsersController"],
    services=["modules.core.services:UserService"],
    models=["modules.core.models:User"],
    base_path="modules.core",
)

__all__ = ["manifest"]`}
              language="python"
            />
          </div>

          <div>
            <p className={`text-sm font-mono mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>modules/core/blueprints.py</p>
            <CodeBlock
              code={`from aquilia import Blueprint

class UserCreateBlueprint(Blueprint):
    name: str
    email: str

    class Spec:
        extra_fields = "reject"

    def seal_email(self, data):
        email = data.get("email", "").strip()
        if "@" not in email:
            self.reject("email", "Invalid email address format")
        data["email"] = email`}
              language="python"
            />
          </div>

          <div>
            <p className={`text-sm font-mono mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>modules/core/controllers.py</p>
            <CodeBlock
              code={`from aquilia import Controller, GET, POST, RequestCtx, Response
from .blueprints import UserCreateBlueprint
from .services import UserService

class UsersController(Controller):
    prefix = "/users"
    tags = ["users"]

    def __init__(self, user_service: UserService):
        self.user_service = user_service

    @GET("/")
    async def list_users(self, ctx: RequestCtx) -> Response:
        users = await self.user_service.list_users()
        return Response.json({"users": [user.to_dict() for user in users]})

    @POST("/")
    async def create_user(self, ctx: RequestCtx) -> Response:
        blueprint = UserCreateBlueprint(data=await ctx.json())
        await blueprint.is_sealed_async(raise_fault=True)
        user = await self.user_service.create_user(blueprint.validated_data)
        return Response.json(user.to_dict(), status=201)`}
              language="python"
            />
          </div>

          <div>
            <p className={`text-sm font-mono mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>modules/core/services.py</p>
            <CodeBlock
              code={`from aquilia import service
from .models import User

@service(scope="app")
class UserService:
    async def list_users(self) -> list[User]:
        return await User.objects.all()

    async def create_user(self, data: dict) -> User:
        return await User.objects.create(
            name=data["name"],
            email=data["email"],
        )`}
              language="python"
            />
          </div>

          <div>
            <p className={`text-sm font-mono mb-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>modules/core/models.py</p>
            <CodeBlock
              code={`from aquilia.models import Model, CharField

class User(Model):
    table = "users"

    name = CharField(max_length=150)
    email = CharField(max_length=255, unique=True)`}
              language="python"
            />
          </div>
        </div>

        <div className={`mt-4 rounded-lg border p-4 ${isDark ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-emerald-50 border-emerald-200'}`}>
          <p className={`text-sm ${isDark ? 'text-emerald-300' : 'text-emerald-700'}`}>
            <strong>Run it:</strong> <code className="font-mono">aq run</code> or <code className="font-mono">python -m aquilia.cli run</code> — starts the development server with auto-reload on port 8000.
          </p>
        </div>
      </section>

      {/* Subsystem Map */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Box className="w-5 h-5 text-aquilia-400" />
          Subsystem Map
        </h2>

        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia is organized into cohesive subsystems, each covered in depth by this documentation:
        </p>

        <div className={`rounded-xl border overflow-hidden ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-zinc-800/80' : 'bg-gray-50'}>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Subsystem</th>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Package</th>
                <th className={`text-left px-4 py-3 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Key Classes</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5' : 'divide-gray-100'}`}>
              {[
                ['Server', 'aquilia.server', 'AquiliaServer'],
                ['Config', 'aquilia.config, aquilia.workspace, aquilia.integrations', 'ConfigLoader, Workspace, Module, Integration'],
                ['Controllers', 'aquilia.controller', 'Controller, GET/POST/PUT/PATCH/DELETE/WS'],
                ['DI', 'aquilia.di', 'Container, Provider, Inject, @service, @factory'],
                ['Models', 'aquilia.models', 'Model, Field types, Manager, QuerySet, Q'],
                ['Sessions', 'aquilia.sessions', 'SessionEngine, SessionPolicy, SessionState'],
                ['Auth', 'aquilia.auth', 'AuthManager, TokenManager, PasswordHasher, AuthzEngine'],
                ['Middleware', 'aquilia.middleware', 'MiddlewareStack, CORS, CSP, CSRF, RateLimit'],
                ['Serializers', 'aquilia.serializers', 'Serializer, ModelSerializer, ListSerializer'],
                ['Blueprints', 'aquilia.blueprints', 'Blueprint, Facet, Projection, Cast, Seal'],
                ['Cache', 'aquilia.cache', 'CacheService, MemoryBackend, RedisBackend'],
                ['Mail', 'aquilia.mail', 'MailService, asend_mail, EmailMessage'],
                ['WebSockets', 'aquilia.sockets', 'AquilaSockets, SocketController, @Event'],
                ['Templates', 'aquilia.templates', 'TemplateEngine, TemplateLoader'],
                ['Faults', 'aquilia.faults', 'Fault, FaultEngine, FaultDomain, Severity'],
                ['Effects', 'aquilia.effects', 'Effect, EffectProvider, EffectRegistry'],
                ['CLI', 'aquilia.cli', 'aq init/add/generate/validate/run/serve'],
                ['Testing', 'aquilia.testing', 'TestClient, AquiliaTestCase'],
              ].map(([name, pkg, classes], i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className={`px-4 py-2 font-medium ${isDark ? 'text-white' : 'text-gray-900'}`}>{name}</td>
                  <td className={`px-4 py-2 font-mono text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{pkg}</td>
                  <td className={`px-4 py-2 font-mono text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{classes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Quick Navigation */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Terminal className="w-5 h-5 text-aquilia-400" />
          Where to Go Next
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {[
            { to: '/docs/installation', icon: <Rocket className="w-4 h-4" />, title: 'Installation', desc: 'Install Aquilia and set up your environment' },
            { to: '/docs/quickstart', icon: <Zap className="w-4 h-4" />, title: 'Quick Start', desc: 'Build your first API in 5 minutes' },
            { to: '/docs/architecture', icon: <Cpu className="w-4 h-4" />, title: 'Architecture', desc: 'Understand the manifest-driven pipeline' },
            { to: '/docs/controllers/overview', icon: <Layers className="w-4 h-4" />, title: 'Controllers', desc: 'Class-based request handlers with DI' },
            { to: '/docs/di/container', icon: <Plug className="w-4 h-4" />, title: 'Dependency Injection', desc: 'Six-scope DI container with async support' },
            { to: '/docs/models/defining', icon: <Database className="w-4 h-4" />, title: 'Models & ORM', desc: 'Metaclass-driven ORM with migrations' },
          ].map((link, i) => (
            <Link
              key={i}
              to={link.to}
              className={`flex items-start gap-3 p-4 rounded-xl border transition-all hover:scale-[1.01] ${isDark ? 'bg-zinc-900/50 border-white/10 hover:border-aquilia-500/30' : 'bg-white border-gray-200 hover:border-aquilia-300'}`}
            >
              <div className="mt-0.5 text-aquilia-400">{link.icon}</div>
              <div>
                <div className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>{link.title}</div>
                <div className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{link.desc}</div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      <NextSteps />
    </div>
  )
}