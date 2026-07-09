import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import { Link } from 'react-router-dom'
import { Binary, ArrowRight, GitBranch, Shield, Layers, Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { motion } from 'framer-motion'

const stages = [
  { step: '1', label: 'Declare', desc: 'Define Facets and Spec on a Blueprint subclass.' },
  { step: '2', label: 'Cast', desc: 'Inbound raw values are coerced by each Facet.' },
  { step: '3', label: 'Seal', desc: 'Facet validators + Ward cross-field checks run.' },
  { step: '4', label: 'Imprint', desc: 'Validated data is written back to the model.' },
  { step: '5', label: 'Mold', desc: 'Model instance is serialized through Facets → dict.' },
]

const BLUEPRINT_FLOW_DATA = [
  {
    left: {
      title: '1. Cast Pipeline',
      pkg: 'aquilia.blueprints.pipeline',
      file: 'aquilia/blueprints/pipeline.py',
      desc: 'Coerces raw payload inputs into target Python types via facet coercion (e.g. parsing strings to datetime objects recursively).',
      color: '#10b981'
    },
    right: {
      title: '1. Projection Selection',
      pkg: 'aquilia.blueprints.projections',
      file: 'aquilia/blueprints/projections.py',
      desc: 'Selects fields to expose (e.g. blueprint["public"]). Filters out write-only/sensitive fields automatically from outbound data.',
      color: '#3b82f6'
    }
  },
  {
    left: {
      title: '2. Seal & Wards',
      pkg: 'aquilia.blueprints.ward',
      file: 'aquilia/blueprints/ward.py',
      desc: 'Executes individual facet validators (max_length, pattern regex) and gathers @ward cross-field integrity checks in a single pass.',
      color: '#10b981'
    },
    right: {
      title: '2. Lens Resolution',
      pkg: 'aquilia.blueprints.lenses',
      file: 'aquilia/blueprints/lenses.py',
      desc: 'Recursively resolves related model fields through nested blueprints, enforcing depth limits and cycle check guards dynamically.',
      color: '#3b82f6'
    }
  },
  {
    left: {
      title: '3. Imprint Layer',
      pkg: 'aquilia.blueprints.core',
      file: 'aquilia/blueprints/core.py',
      desc: 'Writes validated datasets back into the target database models safely via transactional INSERT or UPDATE operations.',
      color: '#059669'
    },
    right: {
      title: '3. Mold Finalization',
      pkg: 'aquilia.blueprints.facets',
      file: 'aquilia/blueprints/facets.py',
      desc: 'Transforms Python model objects back to standard JSON serializable dictionaries, running @computed fields and constant conversions.',
      color: '#2563eb'
    }
  }
]

function BlueprintArchitectureVisualizer({ isDark }: { isDark: boolean }) {
  return (
    <div className="my-12 flex flex-col items-center w-full font-sans select-none">
      {/* Central spine header */}
      <div className="hidden md:flex flex-col items-center mb-2">
        <span className={`text-[8px] font-mono tracking-widest px-2 py-0.5 rounded border ${
          isDark ? 'border-zinc-800 bg-zinc-900/60 text-zinc-500' : 'border-gray-200 bg-gray-50 text-gray-500'
        }`}>
          BLUEPRINT CONTRACT CORE
        </span>
        <div className={`w-[1px] h-10 ${isDark ? 'bg-zinc-800' : 'bg-gray-200'}`} />
      </div>

      <div className="w-full space-y-8 md:space-y-0">
        {BLUEPRINT_FLOW_DATA.map((row, idx) => (
          <div key={idx} className="flex flex-col md:grid md:grid-cols-[1fr_100px_1fr] items-center gap-4 md:gap-0">
            
            {/* Left Inbound Step */}
            <div className="text-left md:text-right pr-0 md:pr-6">
              <div className="flex flex-col gap-1 md:items-end">
                <span className={`text-[9px] font-mono font-semibold`} style={{ color: row.left.color }}>
                  {row.left.pkg}
                </span>
                <h4 className={`text-sm font-mono font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  {row.left.title}
                </h4>
                <p className={`text-xs leading-relaxed font-light mt-1 max-w-sm ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
                  {row.left.desc}
                </p>
                <a
                  href={`file:///Users/kuroyami/TuboxLabProject/Aquilia/${row.left.file}`}
                  className={`font-mono text-[9px] font-medium hover:underline transition-colors mt-2 ${
                    isDark ? 'text-zinc-500 hover:text-emerald-400' : 'text-gray-400 hover:text-emerald-600'
                  }`}
                >
                  • {row.left.file}
                </a>
              </div>
            </div>

            {/* Middle Connection SVG (Visible on Desktop only) */}
            <div className="hidden md:block w-[100px] h-[140px] relative">
              <svg viewBox="0 0 100 140" className="w-full h-full bg-transparent overflow-visible">
                {/* Vertical Spine segment */}
                <line 
                  x1="50" y1="0" x2="50" y2="140" 
                  stroke={isDark ? "#18181b" : "#f3f4f6"} 
                  strokeWidth="1.5" 
                />

                {/* Spine timeline particles flowing down */}
                <motion.circle
                  cx="50"
                  r="1.2"
                  fill={isDark ? "#3f3f46" : "#cbd5e1"}
                  animate={{ cy: [0, 140] }}
                  transition={{ repeat: Infinity, duration: 3, ease: "linear", delay: idx * 0.5 }}
                />

                {/* Left Branch (Inbound Request - flows INWARD to spine) */}
                <path 
                  d="M 50,70 H 15" 
                  fill="none" 
                  stroke={isDark ? "#27272a" : "#cbd5e1"} 
                  strokeWidth="1.2" 
                />
                {/* Flow inward: from 15 to 50 */}
                <motion.circle
                  r="2"
                  fill={row.left.color}
                  animate={{ cx: [15, 50] }}
                  transition={{ repeat: Infinity, duration: 2.2, ease: "easeInOut", delay: idx * 0.3 }}
                  cy="70"
                />
                {/* Left Tip */}
                <circle cx="15" cy="70" r="3" fill={row.left.color} />

                {/* Right Branch (Outbound Response - flows OUTWARD from spine) */}
                <path 
                  d="M 50,70 H 85" 
                  fill="none" 
                  stroke={isDark ? "#27272a" : "#cbd5e1"} 
                  strokeWidth="1.2" 
                />
                {/* Flow outward: from 50 to 85 */}
                <motion.circle
                  r="2"
                  fill={row.right.color}
                  animate={{ cx: [50, 85] }}
                  transition={{ repeat: Infinity, duration: 2.2, ease: "easeInOut", delay: idx * 0.3 + 0.5 }}
                  cy="70"
                />
                {/* Right Tip */}
                <circle cx="85" cy="70" r="3" fill={row.right.color} />

                {/* Central Hub Junction dot */}
                <circle 
                  cx="50" cy="70" r="4.5" 
                  fill={isDark ? "#000000" : "#ffffff"} 
                  stroke={isDark ? "#3f3f46" : "#a1a1aa"} 
                  strokeWidth="2" 
                />
              </svg>
            </div>

            {/* Right Outbound Step */}
            <div className="text-left pl-0 md:pl-6">
              <div className="flex flex-col gap-1 items-start">
                <span className={`text-[9px] font-mono font-semibold`} style={{ color: row.right.color }}>
                  {row.right.pkg}
                </span>
                <h4 className={`text-sm font-mono font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                  {row.right.title}
                </h4>
                <p className={`text-xs leading-relaxed font-light mt-1 max-w-sm ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
                  {row.right.desc}
                </p>
                <a
                  href={`file:///Users/kuroyami/TuboxLabProject/Aquilia/${row.right.file}`}
                  className={`font-mono text-[9px] font-medium hover:underline transition-colors mt-2 ${
                    isDark ? 'text-zinc-500 hover:text-emerald-400' : 'text-gray-400 hover:text-emerald-600'
                  }`}
                >
                  • {row.right.file}
                </a>
              </div>
            </div>

          </div>
        ))}
      </div>

      {/* Central spine footer */}
      <div className="hidden md:flex flex-col items-center mt-2">
        <div className={`w-[1px] h-10 bg-gradient-to-b ${isDark ? 'from-zinc-800 to-transparent' : 'from-gray-200 to-transparent'}`} />
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
