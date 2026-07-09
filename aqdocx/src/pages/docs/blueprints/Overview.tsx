import { useState } from 'react'
import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import { Link } from 'react-router-dom'
import { Binary, ArrowRight, GitBranch, Shield, Layers, Zap, Info } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { motion } from 'framer-motion'

const stages = [
  { step: '1', label: 'Declare', desc: 'Define Facets and Spec on a Blueprint subclass.' },
  { step: '2', label: 'Cast', desc: 'Inbound raw values are coerced by each Facet.' },
  { step: '3', label: 'Seal', desc: 'Facet validators + Ward cross-field checks run.' },
  { step: '4', label: 'Imprint', desc: 'Validated data is written back to the model.' },
  { step: '5', label: 'Mold', desc: 'Model instance is serialized through Facets → dict.' },
]

function BlueprintArchitectureVisualizer({ isDark }: { isDark: boolean }) {
  const [hoveredStep, setHoveredStep] = useState<string | null>(null);

  const stepsData = {
    cast: {
      title: 'Cast Pipeline',
      role: 'Inbound Type Coercion',
      desc: 'Intercepts raw JSON values. Each Facet (e.g. IntFacet, DateFacet) runs coercion rules, parsing strings to target native Python types recursively.',
      file: 'aquilia/blueprints/pipeline.py',
      color: '#10b981'
    },
    seal: {
      title: 'Seal & Wards',
      role: 'Integrity Validation',
      desc: 'Executes individual facet validators (max_length, pattern regex) and gathers all cross-field constraints marked with the @ward decorator in a single pass.',
      file: 'aquilia/blueprints/ward.py',
      color: '#10b981'
    },
    imprint: {
      title: 'Imprint Layer',
      role: 'Database Writer',
      desc: 'Executes database transaction updates. Flushes the validated clean dataset directly into target ORM models as a safe SQL INSERT or UPDATE.',
      file: 'aquilia/blueprints/core.py',
      color: '#059669'
    },
    projection: {
      title: 'Projection Filter',
      role: 'Field Visibility Rules',
      desc: 'Selects the exact list of attributes to expose (e.g. blueprint["public"]). Filters out write-only/sensitive fields automatically from outbound data.',
      file: 'aquilia/blueprints/projections.py',
      color: '#3b82f6'
    },
    lens: {
      title: 'Lens Resolution',
      role: 'Relational Graph Resolver',
      desc: 'Recursively resolves related model fields through nested blueprints. Controls depth limits and runs cyclic loop check guards dynamically.',
      file: 'aquilia/blueprints/lenses.py',
      color: '#3b82f6'
    },
    mold: {
      title: 'Mold Finalization',
      role: 'Outbound Serialization',
      desc: 'Transforms Python model objects back to standard JSON serializable dictionaries, running custom @computed fields and constant conversions.',
      file: 'aquilia/blueprints/facets.py',
      color: '#2563eb'
    }
  };

  const activeStep = hoveredStep ? stepsData[hoveredStep as keyof typeof stepsData] : null;

  return (
    <div className="my-12 w-full font-sans select-none">
      <h2 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>System Architecture</h2>
      <p className={`text-xs ${isDark ? 'text-zinc-500' : 'text-gray-500'} mb-8`}>
        Dual-track request-response lifecycle loops through the central Blueprint contract.
      </p>

      {/* SVG Pipeline Map */}
      <div className="w-full max-w-2xl mx-auto h-[260px] relative overflow-hidden">
        <svg viewBox="0 0 640 260" className="w-full h-full bg-transparent overflow-visible">
          {/* Defs & Patterns */}
          <defs>
            <pattern id="blueprint-grid" width="16" height="16" patternUnits="userSpaceOnUse">
              <circle cx="1" cy="1" r="0.8" fill={isDark ? "#27272a" : "#cbd5e1"} />
            </pattern>
            <linearGradient id="inbound-pulse-grad" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#10b981" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#059669" stopOpacity="0.2" />
            </linearGradient>
            <linearGradient id="outbound-pulse-grad" x1="0%" y1="100%" x2="100%" y2="0%">
              <stop offset="0%" stopColor="#2563eb" stopOpacity="0.2" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.8" />
            </linearGradient>
          </defs>

          {/* Background Grid Pattern */}
          <rect width="100%" height="100%" fill="url(#blueprint-grid)" opacity="0.35" />

          {/* Central Vertical spine axis line */}
          <line 
            x1="320" y1="0" x2="320" y2="260" 
            stroke={isDark ? "#27272a" : "#e4e4e7"} 
            strokeWidth="1" 
            strokeDasharray="4 4" 
          />

          {/* Left Inbound path (Green) */}
          <path
            d="M 60,40 C 180,40 240,70 270,100 C 290,120 250,180 320,210"
            fill="none"
            stroke={isDark ? "#1f1f23" : "#f1f5f9"}
            strokeWidth="1.5"
          />
          <motion.path
            d="M 60,40 C 180,40 240,70 270,100 C 290,120 250,180 320,210"
            fill="none"
            stroke="url(#inbound-pulse-grad)"
            strokeWidth="2"
            strokeDasharray="8 25"
            animate={{ strokeDashoffset: [200, 0] }}
            transition={{ repeat: Infinity, duration: 4, ease: "linear" }}
          />

          {/* Right Outbound path (Blue) */}
          <path
            d="M 320,210 C 390,180 350,120 370,100 C 395,70 460,40 580,40"
            fill="none"
            stroke={isDark ? "#1f1f23" : "#f1f5f9"}
            strokeWidth="1.5"
          />
          <motion.path
            d="M 320,210 C 390,180 350,120 370,100 C 395,70 460,40 580,40"
            fill="none"
            stroke="url(#outbound-pulse-grad)"
            strokeWidth="2"
            strokeDasharray="8 25"
            animate={{ strokeDashoffset: [0, 200] }}
            transition={{ repeat: Infinity, duration: 4, ease: "linear" }}
          />

          {/* Central Blueprint Core Ring */}
          <circle 
            cx="320" cy="100" r="18" 
            fill={isDark ? "#09090b" : "#ffffff"} 
            stroke={hoveredStep ? "#10b981" : (isDark ? "#3f3f46" : "#cbd5e1")} 
            strokeWidth="1.5" 
            className="transition-colors duration-300"
          />
          <text 
            x="320" y="103" textAnchor="middle" 
            fill={isDark ? "#71717a" : "#a1a1aa"} 
            fontSize="7" fontWeight="bold" fontFamily="monospace"
          >
            CONTRACT
          </text>

          {/* Bottom DB Model Ring */}
          <circle 
            cx="320" cy="210" r="16" 
            fill={isDark ? "#09090b" : "#ffffff"} 
            stroke={hoveredStep === 'imprint' ? "#059669" : (isDark ? "#3f3f46" : "#cbd5e1")} 
            strokeWidth="1.5" 
            className="transition-colors duration-300"
          />
          <text 
            x="320" y="213" textAnchor="middle" 
            fill={isDark ? "#52525b" : "#a1a1aa"} 
            fontSize="6" fontWeight="bold" fontFamily="monospace"
          >
            MODEL
          </text>

          {/* Left Endpoint: Request */}
          <circle cx="60" cy="40" r="4" fill="#10b981" />
          <text x="60" y="28" textAnchor="middle" fill="#10b981" fontSize="8" fontWeight="bold" fontFamily="monospace">REQUEST</text>

          {/* Right Endpoint: Response */}
          <circle cx="580" cy="40" r="4" fill="#3b82f6" />
          <text x="580" y="28" textAnchor="middle" fill="#3b82f6" fontSize="8" fontWeight="bold" fontFamily="monospace">RESPONSE</text>

          {/* INBOUND NODES */}
          {/* Node: Cast */}
          <g 
            className="cursor-pointer"
            onMouseEnter={() => setHoveredStep('cast')}
            onMouseLeave={() => setHoveredStep(null)}
          >
            {/* Spinning reticle */}
            <circle 
              cx="160" cy="47" r="8" 
              fill="none" stroke="#10b981" strokeWidth="0.5" strokeDasharray="2 2"
              className={hoveredStep === 'cast' ? 'animate-spin' : ''}
              style={{ transformOrigin: '160px 47px', animationDuration: '3s' }}
            />
            <circle 
              cx="160" cy="47" 
              r="4.5" 
              fill={hoveredStep === 'cast' ? "#10b981" : (isDark ? "#09090b" : "#ffffff")} 
              stroke="#10b981" strokeWidth="1.5"
              className="transition-all duration-200"
            />
            <text x="160" y="67" textAnchor="middle" fill={isDark ? "#a1a1aa" : "#71717a"} fontSize="8" fontFamily="monospace">1. CAST</text>
          </g>

          {/* Node: Seal */}
          <g 
            className="cursor-pointer"
            onMouseEnter={() => setHoveredStep('seal')}
            onMouseLeave={() => setHoveredStep(null)}
          >
            {/* Spinning reticle */}
            <circle 
              cx="251" cy="87" r="8" 
              fill="none" stroke="#10b981" strokeWidth="0.5" strokeDasharray="2 2"
              className={hoveredStep === 'seal' ? 'animate-spin' : ''}
              style={{ transformOrigin: '251px 87px', animationDuration: '3s' }}
            />
            <circle 
              cx="251" cy="87" 
              r="4.5" 
              fill={hoveredStep === 'seal' ? "#10b981" : (isDark ? "#09090b" : "#ffffff")} 
              stroke="#10b981" strokeWidth="1.5"
              className="transition-all duration-200"
            />
            <text x="231" y="107" textAnchor="middle" fill={isDark ? "#a1a1aa" : "#71717a"} fontSize="8" fontFamily="monospace">2. SEAL</text>
          </g>

          {/* Node: Imprint */}
          <g 
            className="cursor-pointer"
            onMouseEnter={() => setHoveredStep('imprint')}
            onMouseLeave={() => setHoveredStep(null)}
          >
            {/* Spinning reticle */}
            <circle 
              cx="278" cy="164" r="8" 
              fill="none" stroke="#059669" strokeWidth="0.5" strokeDasharray="2 2"
              className={hoveredStep === 'imprint' ? 'animate-spin' : ''}
              style={{ transformOrigin: '278px 164px', animationDuration: '3s' }}
            />
            <circle 
              cx="278" cy="164" 
              r="4.5" 
              fill={hoveredStep === 'imprint' ? "#059669" : (isDark ? "#09090b" : "#ffffff")} 
              stroke="#059669" strokeWidth="1.5"
              className="transition-all duration-200"
            />
            <text x="238" y="169" textAnchor="middle" fill={isDark ? "#a1a1aa" : "#71717a"} fontSize="8" fontFamily="monospace">3. IMPRINT</text>
          </g>

          {/* OUTBOUND NODES */}
          {/* Node: Projection */}
          <g 
            className="cursor-pointer"
            onMouseEnter={() => setHoveredStep('projection')}
            onMouseLeave={() => setHoveredStep(null)}
          >
            {/* Spinning reticle */}
            <circle 
              cx="362" cy="164" r="8" 
              fill="none" stroke="#3b82f6" strokeWidth="0.5" strokeDasharray="2 2"
              className={hoveredStep === 'projection' ? 'animate-spin' : ''}
              style={{ transformOrigin: '362px 164px', animationDuration: '3s' }}
            />
            <circle 
              cx="362" cy="164" 
              r="4.5" 
              fill={hoveredStep === 'projection' ? "#3b82f6" : (isDark ? "#09090b" : "#ffffff")} 
              stroke="#3b82f6" strokeWidth="1.5"
              className="transition-all duration-200"
            />
            <text x="402" y="169" textAnchor="middle" fill={isDark ? "#a1a1aa" : "#71717a"} fontSize="8" fontFamily="monospace">1. PROJECT</text>
          </g>

          {/* Node: Lens */}
          <g 
            className="cursor-pointer"
            onMouseEnter={() => setHoveredStep('lens')}
            onMouseLeave={() => setHoveredStep(null)}
          >
            {/* Spinning reticle */}
            <circle 
              cx="384" cy="87" r="8" 
              fill="none" stroke="#3b82f6" strokeWidth="0.5" strokeDasharray="2 2"
              className={hoveredStep === 'lens' ? 'animate-spin' : ''}
              style={{ transformOrigin: '384px 87px', animationDuration: '3s' }}
            />
            <circle 
              cx="384" cy="87" 
              r="4.5" 
              fill={hoveredStep === 'lens' ? "#3b82f6" : (isDark ? "#09090b" : "#ffffff")} 
              stroke="#3b82f6" strokeWidth="1.5"
              className="transition-all duration-200"
            />
            <text x="404" y="107" textAnchor="middle" fill={isDark ? "#a1a1aa" : "#71717a"} fontSize="8" fontFamily="monospace">2. LENS</text>
          </g>

          {/* Node: Mold */}
          <g 
            className="cursor-pointer"
            onMouseEnter={() => setHoveredStep('mold')}
            onMouseLeave={() => setHoveredStep(null)}
          >
            {/* Spinning reticle */}
            <circle 
              cx="489" cy="47" r="8" 
              fill="none" stroke="#2563eb" strokeWidth="0.5" strokeDasharray="2 2"
              className={hoveredStep === 'mold' ? 'animate-spin' : ''}
              style={{ transformOrigin: '489px 47px', animationDuration: '3s' }}
            />
            <circle 
              cx="489" cy="47" 
              r="4.5" 
              fill={hoveredStep === 'mold' ? "#2563eb" : (isDark ? "#09090b" : "#ffffff")} 
              stroke="#2563eb" strokeWidth="1.5"
              className="transition-all duration-200"
            />
            <text x="489" y="67" textAnchor="middle" fill={isDark ? "#a1a1aa" : "#71717a"} fontSize="8" fontFamily="monospace">3. MOLD</text>
          </g>
        </svg>
      </div>

      {/* Coupled Detail Telemetry Info Block (Flat & Open borderless HUD) */}
      <div className="min-h-[110px] mt-4 transition-all duration-300">
        {activeStep ? (
          <div className="flex flex-col gap-2 border-l-2 pl-4 py-1" style={{ borderColor: activeStep.color }}>
            <div className="flex justify-between items-center text-[9px] font-mono">
              <span className="font-bold tracking-widest uppercase" style={{ color: activeStep.color }}>
                {activeStep.role}
              </span>
              <span className={isDark ? 'text-zinc-500' : 'text-gray-400'}>
                {activeStep.file}
              </span>
            </div>
            <h4 className={`text-sm font-mono font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
              {activeStep.title}
            </h4>
            <p className={`text-xs leading-relaxed font-light ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
              {activeStep.desc}
            </p>
          </div>
        ) : (
          <div className="flex items-center gap-2 py-4 justify-center border-l-2 border-zinc-800/20 pl-4">
            <Info className={`w-3.5 h-3.5 ${isDark ? 'text-zinc-650' : 'text-gray-400'}`} />
            <span className={`text-xs font-mono font-light ${isDark ? 'text-zinc-500' : 'text-gray-400'}`}>
              Hover over any numbered node in the pipeline curve to view its execution specifications.
            </span>
          </div>
        )}
      </div>

      {/* Static Typographic Summary Columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-12 gap-y-6 mt-8 pt-6 border-t border-dashed border-zinc-800/30">
        <div>
          <h3 className="text-[10px] font-mono font-bold tracking-wider text-emerald-500 uppercase mb-3">
            Inbound Pipeline (Request Data)
          </h3>
          <ul className="space-y-3.5">
            <li className="flex flex-col gap-0.5">
              <span className={`text-xs font-mono font-semibold ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>1. Cast Phase</span>
              <span className={`text-xs font-light leading-normal ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                Coerces input dictionaries into target Python types via individual Facet casting pipelines.
              </span>
            </li>
            <li className="flex flex-col gap-0.5">
              <span className={`text-xs font-mono font-semibold ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>2. Seal Phase</span>
              <span className={`text-xs font-light leading-normal ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                Runs facet constraint validators and sweeps custom @ward cross-field integrity checks.
              </span>
            </li>
            <li className="flex flex-col gap-0.5">
              <span className={`text-xs font-mono font-semibold ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>3. Imprint Phase</span>
              <span className={`text-xs font-light leading-normal ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                Flushes valid datasets back into the ORM models to trigger SQL inserts or updates.
              </span>
            </li>
          </ul>
        </div>

        <div>
          <h3 className="text-[10px] font-mono font-bold tracking-wider text-blue-500 uppercase mb-3">
            Outbound Pipeline (Response Model)
          </h3>
          <ul className="space-y-3.5">
            <li className="flex flex-col gap-0.5">
              <span className={`text-xs font-mono font-semibold ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>1. Projection Selection</span>
              <span className={`text-xs font-light leading-normal ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                Filters attributes based on named projection limits, respecting write-only properties.
              </span>
            </li>
            <li className="flex flex-col gap-0.5">
              <span className={`text-xs font-mono font-semibold ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>2. Lens Resolution</span>
              <span className={`text-xs font-light leading-normal ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                Fetches related data through nested Lens paths, enforcing recursion and cycle limits.
              </span>
            </li>
            <li className="flex flex-col gap-0.5">
              <span className={`text-xs font-mono font-semibold ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>3. Mold Phase</span>
              <span className={`text-xs font-light leading-normal ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                Serializes model elements to standard native dictionaries for JSON serialization.
              </span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export function BlueprintsOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const t = (d: string, l: string) => isDark ? d : l

  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm mb-6">
        <Link to="/docs" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Docs</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <span className={t('text-gray-300','text-gray-600')}>Blueprints</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Blueprints</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          <DocTerm id="bp.blueprint">Blueprint</DocTerm> is Aquilia's first-class model↔world contract. Not a serializer — a typed framework primitive that handles inbound validation, outbound serialization, and model persistence in one cohesive API.
        </p>
      </div>

      {/* Core concept callout */}
      <div className={`rounded-xl p-6 mb-10 border ${t('bg-aquilia-500/5 border-aquilia-500/20','bg-blue-50/60 border-blue-200/60')}`}>
        <div className="flex items-start gap-3">
          <Binary className={`w-5 h-5 mt-0.5 shrink-0 ${t('text-aquilia-400','text-blue-600')}`} />
          <div>
            <h3 className={`font-semibold mb-2 ${t('text-aquilia-300','text-blue-700')}`}>Blueprint ≠ Serializer</h3>
            <p className={`text-sm leading-relaxed ${t('text-aquilia-200','text-blue-700')}`}>
              A Blueprint declares <strong>what the world sees</strong> (<DocTerm id="bp.facet">Facets</DocTerm>), <strong>named subsets</strong> (<DocTerm id="bp.projection">Projections</DocTerm>), <strong>how data enters</strong> (Casts), <strong>integrity rules</strong> (<DocTerm id="bp.ward">@ward</DocTerm> Seals), and <strong>how data writes back</strong> (<DocTerm id="bp.imprint">imprint()</DocTerm>). A single class covers the full request/response lifecycle.
            </p>
          </div>
        </div>
      </div>

      {/* Blueprint System Architecture */}
      <BlueprintArchitectureVisualizer isDark={isDark} />

      {/* Lifecycle pipeline */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-6 ${t('text-white','text-gray-900')}`}>Lifecycle</h2>
        <div className="flex flex-col sm:flex-row gap-2 sm:items-start">
          {stages.map((s, i) => (
            <div key={s.step} className="flex sm:flex-col flex-row items-center sm:items-center gap-2 sm:gap-1 flex-1">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold shrink-0 ${t('bg-aquilia-500/20 text-aquilia-300','bg-aquilia-100 text-aquilia-700')}`}>
                {s.step}
              </div>
              <div className="text-center sm:px-1">
                <div className={`font-semibold text-sm ${t('text-white','text-gray-900')}`}>{s.label}</div>
                <div className={`text-xs mt-0.5 ${t('text-gray-400','text-gray-500')}`}>{s.desc}</div>
              </div>
              {i < stages.length - 1 && (
                <ArrowRight className={`w-4 h-4 shrink-0 hidden sm:block ${t('text-gray-600','text-gray-300')}`} />
              )}
            </div>
          ))}
        </div>
      </section>

      {/* Quick start */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Quick Start</h2>
        <CodeBlock language="python" filename="blueprints.py">{`from aquilia.blueprints import Blueprint, TextFacet, IntFacet, EmailFacet, DateTimeFacet, Computed
from aquilia.blueprints.annotations import computed

class UserBlueprint(Blueprint):
    # Explicit Facets
    name     = TextFacet(max_length=150, min_length=1)
    email    = EmailFacet()
    bio      = TextFacet(max_length=500, required=False, default="")

    # Computed read-only field
    @computed
    def display_name(self) -> str:
        return self.instance.name.title() if self.instance else ""

    class Spec:
        model = User
        projections = {
            "public":   ["id", "name", "display_name"],
            "profile":  ["id", "name", "email", "bio", "display_name"],
            "admin":    "__all__",
        }
        read_only_fields  = ("id", "display_name")
        write_only_fields = ("password",)
        depth = 2`}</CodeBlock>
      </section>

      {/* Outbound — serialization */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Outbound — Model → Dict</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Pass <code>instance=</code> to serialize. Apply a projection with <code>projection=</code> or the subscript syntax:
        </p>
        <CodeBlock language="python">{`user = await User.objects.get(id=42)

# All fields (or default_projection)
data = UserBlueprint(instance=user).data

# Named projection
data = UserBlueprint(instance=user, projection="public").data

# Subscript syntax (used with route decorators)
data = UserBlueprint["public"](instance=user).data

# List of instances
users = await User.objects.filter(active=True).all()
result = [UserBlueprint(instance=u, projection="public").data for u in users]`}</CodeBlock>
      </section>

      {/* Inbound — validation */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Inbound — Validate + Persist</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Pass <code>data=</code> to validate. Call <DocTerm id="bp.is_sealed">is_sealed()</DocTerm> to run all Facet validators and <DocTerm id="bp.ward">@ward</DocTerm> methods. If valid, call <DocTerm id="bp.imprint">imprint()</DocTerm> to write back.
        </p>
        <CodeBlock language="python">{`bp = UserBlueprint(data=request.json)

if not bp.is_sealed():
    return Response.json({"errors": bp.errors}, status=422)

user = await bp.imprint(db=db)   # INSERT into users table
return Response.json(UserBlueprint(instance=user, projection="profile").data, status=201)`}</CodeBlock>

        <p className={`mt-6 mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Update an existing instance by passing it to <code>imprint()</code>:
        </p>
        <CodeBlock language="python">{`user = await User.objects.get(id=42)
bp = UserBlueprint(data=request.json)

if not bp.is_sealed():
    return Response.json({"errors": bp.errors}, status=422)

user = await bp.imprint(db=db, instance=user)   # UPDATE users SET ...
return Response.json(UserBlueprint(instance=user).data)`}</CodeBlock>
      </section>

      {/* Route integration */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Route Integration</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Blueprints integrate directly with route decorators via <DocTerm id="bp.request_blueprint">request_blueprint</DocTerm> and <DocTerm id="bp.response_blueprint">response_blueprint</DocTerm>:
        </p>
        <CodeBlock language="python">{`from aquilia.controllers import GET, POST, PUT
from aquilia.db import get_database

@GET("/users", response_blueprint=UserBlueprint["public"])
async def list_users(ctx):
    return await User.objects.filter(active=True).all()
    # Aquilia auto-serializes each User via UserBlueprint["public"]

@POST("/users", request_blueprint=UserBlueprint, response_blueprint=UserBlueprint["profile"])
async def create_user(ctx, blueprint: UserBlueprint):
    if not blueprint.is_sealed():
        return Response.json(blueprint.errors, status=422)
    user = await blueprint.imprint(db=get_database())
    return user  # auto-serialized via response_blueprint

@PUT("/users/{id}", request_blueprint=UserBlueprint, response_blueprint=UserBlueprint["profile"])
async def update_user(ctx, blueprint: UserBlueprint, id: int):
    user = await User.objects.get(id=id)
    if not blueprint.is_sealed():
        return Response.json(blueprint.errors, status=422)
    return await blueprint.imprint(db=get_database(), instance=user)`}</CodeBlock>
      </section>

      {/* Annotation-driven declarations */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Annotation-Driven Declarations</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Use Python type annotations with <DocTerm id="bp.spec">Field()</DocTerm> descriptors instead of explicit Facet classes. Aquilia auto-derives the correct Facet from the type:
        </p>
        <CodeBlock language="python">{`from aquilia.blueprints import Blueprint
from aquilia.blueprints.annotations import Field, computed

class ProductBlueprint(Blueprint):
    name:    str   = Field(min_length=1, max_length=200)
    price:   float = Field(ge=0.0)
    sku:     str   = Field(pattern=r"^[A-Z0-9-]+$", max_length=50)
    tags:    list[str] = Field(default_factory=list, max_items=20)
    active:  bool  = Field(default=True)
    notes:   str | None = None    # Optional field, no constraints

    @computed
    def price_display(self) -> str:
        return f"\\\\\${self.instance.price:.2f}" if self.instance else ""

    class Spec:
        model = Product`}</CodeBlock>
      </section>

      {/* What's next */}
      <section className="mb-10">
        <h2 className={`text-2xl font-bold mb-6 ${t('text-white','text-gray-900')}`}>Explore</h2>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {[
            { label: 'Facets', desc: 'Field type catalogue', href: '/docs/blueprints/facets', icon: Layers },
            { label: 'Projections', desc: 'Named field subsets', href: '/docs/blueprints/projections', icon: GitBranch },
            { label: 'Seals', desc: 'Validation rules', href: '/docs/blueprints/seals', icon: Shield },
            { label: 'Lenses', desc: 'Value transformations', href: '/docs/blueprints/lenses', icon: Zap },
            { label: 'Annotations', desc: 'Type-driven fields', href: '/docs/blueprints/annotations', icon: Binary },
            { label: 'Integration', desc: 'Route & response binding', href: '/docs/blueprints/integration', icon: ArrowRight },
          ].map(({ label, desc, href, icon: Icon }) => (
            <Link key={href} to={href} className={`group p-4 rounded-xl border transition-colors ${t('border-gray-700/60 bg-gray-900 hover:border-aquilia-500/40','border-gray-200 bg-white hover:border-aquilia-400')}`}>
              <Icon className={`w-4 h-4 mb-2 ${t('text-aquilia-400','text-aquilia-600')}`} />
              <div className={`font-semibold text-sm ${t('text-white','text-gray-900')}`}>{label}</div>
              <div className={`text-xs mt-0.5 ${t('text-gray-400','text-gray-500')}`}>{desc}</div>
            </Link>
          ))}
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
