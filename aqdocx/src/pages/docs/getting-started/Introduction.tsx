import { useState } from 'react'
import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { NextSteps } from '../../../components/NextSteps'
import {
  Zap, Shield, Layers, Database, Plug, Cpu, Globe, AlertCircle, Gauge,
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

const SUBSYSTEMS_DATA = [
  {
    id: 'aquilary',
    title: 'Manifest-Driven Architecture',
    shortDesc: 'Declare application topology through Python manifests. Compiles into an immutable artifact graph.',
    desc: 'Declare your application topology through Python manifests. The framework compiles them into an immutable artifact graph — no magic, no discovery at import time.',
    pkg: 'aquilia.aquilary, aquilia.manifest, aquilia.workspace',
    files: ['aquilia/aquilary/__init__.py', 'aquilia/manifest.py', 'aquilia/workspace.py'],
    icon: <Layers className="w-4 h-4 text-emerald-400" />,
    color: '#10b981',
    code: `# workspace.py
workspace = (
    Workspace("api")
    .module(Module("core").auto_discover(True))
)`
  },
  {
    id: 'di',
    title: 'Async-First DI Container',
    shortDesc: 'Six scopes, <3 µs cached lookups, cycle detection, and full graph diagnostics.',
    desc: 'Six scopes (singleton, app, request, transient, pooled, ephemeral), <3 µs cached lookups, cycle detection, and full graph diagnostics — all without annotations or XML.',
    pkg: 'aquilia.di, aquilia.providers',
    files: ['aquilia/di/__init__.py', 'aquilia/providers/__init__.py'],
    icon: <Plug className="w-4 h-4 text-blue-400" />,
    color: '#3b82f6',
    code: `# service definition
@service(scope="request")
class InvoiceService:
    def __init__(self, db: Database):
        self.db = db`
  },
  {
    id: 'orm',
    title: 'Pure-Python ORM',
    shortDesc: 'Metaclass-driven ORM with migrations, signals, transactions, and aggregation.',
    desc: 'Metaclass-driven ORM with 30+ field types, Q-object query builder, Manager/QuerySet, migrations, signals, transactions, and aggregation.',
    pkg: 'aquilia.models, aquilia.sqlite',
    files: ['aquilia/models/__init__.py', 'aquilia/sqlite/__init__.py'],
    icon: <Database className="w-4 h-4 text-purple-400" />,
    color: '#a855f7',
    code: `# models.py
class User(Model):
    name = CharField(max_length=150)
    email = CharField(max_length=255, unique=True)`
  },
  {
    id: 'security',
    title: 'Batteries-Included Security',
    shortDesc: 'Declarative access control, clearance guards, JWT, MFA, and RBAC/ABAC authz.',
    desc: 'Identity model, JWT/RS256 token management, Argon2 password hashing, RBAC/ABAC authorization, OAuth2/OIDC, MFA, and session-based auth with policy enforcement.',
    pkg: 'aquilia.auth, aquilia.auth.clearance, aquilia.auth.authz',
    files: ['aquilia/auth/clearance.py', 'aquilia/auth/core.py', 'aquilia/auth/authz.py'],
    icon: <Shield className="w-4 h-4 text-rose-400" />,
    color: '#f43f5e',
    code: `# clearance authorization
@exempt
@grant(AccessLevel.READ)
class PublicController(Controller):
    ...`
  },
  {
    id: 'routing',
    title: 'Flow Routing Engine',
    shortDesc: 'Class-based HTTP controllers and async request/response pipelines.',
    desc: 'Class-based routing and controller architecture. Decoupled request and response contexts, content negotiation, stream adapters, and full middleware integration.',
    pkg: 'aquilia.controller, aquilia.http',
    files: ['aquilia/controller/__init__.py', 'aquilia/request.py', 'aquilia/response.py'],
    icon: <Globe className="w-4 h-4 text-cyan-400" />,
    color: '#06b6d4',
    code: `# controllers.py
class UsersController(Controller):
    prefix = "/users"

    @GET("/")
    async def list(self, ctx: RequestCtx):
        return Response.json({"users": []})`
  },
  {
    id: 'cache',
    title: 'Multi-Layer Caching',
    shortDesc: 'LRU/LFU memory, Redis, and L1+L2 caching with async decorators.',
    desc: 'Memory (LRU/LFU/TTL), Redis, and Composite (L1+L2) backends. Decorator-driven caching with @cached, @cache_aside, and @invalidate.',
    pkg: 'aquilia.cache',
    files: ['aquilia/cache/__init__.py'],
    icon: <Gauge className="w-4 h-4 text-amber-400" />,
    color: '#f59e0b',
    code: `# caching
@cached(ttl=300, key="users:{user_id}")
async def get_user(user_id: int):
    ...`
  },
  {
    id: 'sockets',
    title: 'WebSocket Controllers',
    shortDesc: 'Decorator WebSocket handlers with per-connection DI and namespace rooms.',
    desc: 'Decorator-based WebSocket handlers with per-connection DI, room management, namespace support, guards, and pluggable adapters (in-memory, Redis).',
    pkg: 'aquilia.sockets',
    files: ['aquilia/sockets/__init__.py'],
    icon: <Zap className="w-4 h-4 text-violet-400" />,
    color: '#8b5cf6',
    code: `# socket handler
@Socket("/chat")
class ChatSocket(SocketController):
    async def on_connect(self):
        await self.join("lobby")`
  },
  {
    id: 'faults',
    title: 'Typed Fault System',
    shortDesc: 'Domain-specific fault taxonomy, recovery plans, and exception mapping.',
    desc: 'Domain-specific fault taxonomy with severity levels, recovery strategies, and a FaultEngine that transforms unhandled exceptions into structured fault signals.',
    pkg: 'aquilia.faults',
    files: ['aquilia/faults/__init__.py', 'aquilia/middleware.py'],
    icon: <AlertCircle className="w-4 h-4 text-orange-400" />,
    color: '#f97316',
    code: `# fault raising
if not user:
    raise EntityNotFoundError("User", id)`
  }
];

function FeatureArchitectureVisualizer({ isDark }: { isDark: boolean }) {
  const [selectedId, setSelectedId] = useState('aquilary');

  const activeItem = SUBSYSTEMS_DATA.find(s => s.id === selectedId) || SUBSYSTEMS_DATA[0];

  const getCoordinates = (index: number) => {
    const angle = (index * 45 - 90) * Math.PI / 180;
    const x = 320 + 120 * Math.cos(angle);
    const y = 180 + 120 * Math.sin(angle);
    return { x, y };
  };

  const getLabelAnchor = (index: number) => {
    if (index === 0 || index === 4) return 'middle';
    if (index > 0 && index < 4) return 'start';
    return 'end';
  };

  const getLabelOffset = (index: number, x: number, y: number) => {
    if (index === 0) return { lx: x, ly: y - 13 };
    if (index === 4) return { lx: x, ly: y + 20 };
    if (index > 0 && index < 4) return { lx: x + 13, ly: y + 3 };
    return { lx: x - 13, ly: y + 3 };
  };

  return (
    <div className="my-10 flex flex-col md:flex-row items-center md:items-start justify-center gap-10 w-full font-sans">
      {/* SVG Diagram */}
      <div className="relative w-full max-w-[340px] aspect-square flex-shrink-0">
        <svg viewBox="0 0 640 360" className="w-full h-full bg-transparent overflow-visible">
          <defs>
            <linearGradient id="intro-sweep-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#10b981" stopOpacity="0" />
            </linearGradient>
          </defs>

          <style>{`
            @keyframes intro-sweep {
              from { transform: rotate(0deg); }
              to { transform: rotate(360deg); }
            }
            .intro-radar-sweep {
              animation: intro-sweep 16s linear infinite;
              transform-origin: 320px 180px;
            }
          `}</style>

          {/* Radar Grid Crosshairs */}
          <line x1="320" y1="20" x2="320" y2="340" stroke={isDark ? "#27272a" : "#cbd5e1"} strokeWidth="0.5" strokeDasharray="3 3" opacity="0.3" />
          <line x1="160" y1="180" x2="480" y2="180" stroke={isDark ? "#27272a" : "#cbd5e1"} strokeWidth="0.5" strokeDasharray="3 3" opacity="0.3" />

          {/* Concentric rings */}
          <circle cx="320" cy="180" r="120" fill="none" stroke={isDark ? "#27272a" : "#e4e4e7"} strokeWidth="1" strokeDasharray="4,4" opacity="0.5" />
          <circle cx="320" cy="180" r="60" fill="none" stroke={isDark ? "#27272a" : "#e4e4e7"} strokeWidth="1" strokeDasharray="4,4" opacity="0.5" />

          {/* Rotating radar sweep */}
          <g className="intro-radar-sweep">
            <path
              d="M 320,180 L 320,50 A 130,130 0 0,1 412,88 Z"
              fill="url(#intro-sweep-grad)"
              className="pointer-events-none"
            />
          </g>

          {/* Core (Runtime Engine) */}
          <circle cx="320" cy="180" r="22" fill={isDark ? "#064e3b" : "#d1fae5"} stroke="#10b981" strokeWidth="2" className="animate-pulse" />
          <text x="320" y="183" textAnchor="middle" fill="#10b981" fontSize="7" fontWeight="bold" fontFamily="monospace">ENGINE</text>

          {/* Render Orbiting Subsystem Nodes */}
          {SUBSYSTEMS_DATA.map((sub, i) => {
            const { x, y } = getCoordinates(i);
            const isSelected = sub.id === selectedId;
            const anchor = getLabelAnchor(i);
            const { lx, ly } = getLabelOffset(i, x, y);

            return (
              <g key={sub.id} className="cursor-pointer" onClick={() => setSelectedId(sub.id)}>
                {isSelected && (
                  <>
                    {/* Pulsing target reticle */}
                    <circle
                      cx={x}
                      cy={y}
                      r="12"
                      fill="none"
                      stroke={sub.color}
                      strokeWidth="1.2"
                      strokeDasharray="3 2"
                      className="animate-spin"
                      style={{ transformOrigin: `${x}px ${y}px`, animationDuration: '6s' }}
                    />
                    <circle cx={x} cy={y} r="8" fill="none" stroke={sub.color} strokeWidth="1" opacity="0.4" className="animate-ping" />
                    {/* Laser connection beam to core */}
                    <line x1="320" y1="180" x2={x} y2={y} stroke={sub.color} strokeWidth="1" strokeDasharray="2 3" opacity="0.5" />
                    <motion.line
                      x1="320" y1="180" x2={x} y2={y}
                      stroke={sub.color}
                      strokeWidth="1.5"
                      strokeDasharray="4 4"
                      animate={{ strokeDashoffset: [0, -12] }}
                      transition={{ repeat: Infinity, ease: "linear", duration: 0.8 }}
                      opacity="0.8"
                    />
                  </>
                )}
                {/* Node Dot */}
                <circle
                  cx={x}
                  cy={y}
                  r={isSelected ? "5.5" : "4"}
                  fill={isSelected ? sub.color : (isDark ? "#000000" : "#ffffff")}
                  stroke={sub.color}
                  strokeWidth={isSelected ? "2.5" : "1.5"}
                />
                {/* Node text label */}
                <text
                  x={lx}
                  y={ly}
                  textAnchor={anchor}
                  fill={isSelected ? (isDark ? "#ffffff" : "#000000") : (isDark ? "#a1a1aa" : "#71717a")}
                  fontSize="7.5"
                  fontWeight={isSelected ? "bold" : "normal"}
                  fontFamily="monospace"
                  className="pointer-events-none"
                >
                  {sub.title.split(' ')[0]} {/* first word only to keep it clean */}
                </text>
              </g>
            );
          })}
        </svg>
      </div>

      {/* Subsystem Telemetry Details (No boxes, pure typographic) */}
      <div className="w-full max-w-xl md:mt-2">
        <div className="flex justify-between items-center mb-4 pb-2 border-b border-dashed border-zinc-800/35">
          <span className={`text-[9px] font-mono px-2 py-0.5 rounded border font-semibold`} style={{ color: activeItem.color, borderColor: `${activeItem.color}30` }}>
            {activeItem.pkg.toUpperCase()}
          </span>
          <span className={`text-[10px] font-mono ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
            SUBSYSTEM INTEGRITY
          </span>
        </div>

        <h4 className={`text-md font-mono font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`} style={{ color: activeItem.color }}>
          {activeItem.title}
        </h4>

        <p className={`text-xs leading-relaxed mb-6 font-light ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
          {activeItem.desc}
        </p>

        <div className="border-t border-dashed border-zinc-850 pt-4 mb-4">
          <span className={`text-[9px] font-mono block mb-1.5 ${isDark ? 'text-zinc-500' : 'text-gray-400'}`}>
            CODEBASE FILES (READ FROM REPOSITORY SOURCE)
          </span>
          <div className="flex flex-col gap-1.5">
            {activeItem.files.map((file) => (
              <a
                key={file}
                href={`file:///Users/kuroyami/TuboxLabProject/Aquilia/${file}`}
                className={`font-mono text-[9.5px] font-medium hover:underline transition-colors ${
                  isDark ? 'text-zinc-400 hover:text-emerald-400' : 'text-gray-600 hover:text-emerald-600'
                }`}
              >
                • {file}
              </a>
            ))}
          </div>
        </div>

        <div className="space-y-2">
          <span className={`text-[9px] font-mono block ${isDark ? 'text-zinc-500' : 'text-gray-400'}`}>
            DECLARATIVE SYNTAX
          </span>
          <div className="font-mono text-[9px]">
            <CodeBlock language="python" filename="" showLineNumbers={false}>
              {activeItem.code}
            </CodeBlock>
          </div>
        </div>
      </div>
    </div>
  );
}

export function IntroductionPage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

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
              <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>v1.2.3 ("Kraken's Wake") · Production-ready async Python web framework</p>
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
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Core Philosophy
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* The Problem */}
          <div className={`rounded-xl border p-6 ${isDark ? 'bg-red-500/5 border-red-500/10' : 'bg-red-50 border-red-100'}`}>
            <h3 className={`font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-red-400' : 'text-red-700'}`}>
              The Problem With Modern Frameworks
            </h3>
            <ul className={`space-y-3 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              <li className="flex items-start gap-3">
                <span className="text-red-400 mt-1">✕</span>
                <div>Too much configuration wiring components together</div>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-red-400 mt-1">✕</span>
                <div>Deployment infrastructure is an afterthought</div>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-red-400 mt-1">✕</span>
                <div>ML integration is painful and disjointed</div>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-red-400 mt-1">✕</span>
                <div>Boilerplate everywhere for basic features</div>
              </li>
            </ul>
          </div>

          {/* Aquilia's Approach */}
          <div className={`rounded-xl border p-6 ${isDark ? 'bg-emerald-500/5 border-emerald-500/10' : 'bg-emerald-50 border-emerald-100'}`}>
            <h3 className={`font-bold mb-4 flex items-center gap-2 ${isDark ? 'text-emerald-400' : 'text-emerald-700'}`}>
              Aquilia's Approach
            </h3>
            <ul className={`space-y-3 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              <li className="flex items-start gap-3">
                <span className="text-emerald-400 mt-1">✓</span>
                <div><strong>Auto-discovery</strong> eliminates wiring boilerplate</div>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-emerald-400 mt-1">✓</span>
                <div><strong>Convention over configuration</strong> — sensible defaults</div>
              </li>
              <li className="flex items-start gap-3">
                <span className="text-emerald-400 mt-1">✓</span>
                <div><strong>Infrastructure generation</strong> built-in</div>
              </li>
            </ul>
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