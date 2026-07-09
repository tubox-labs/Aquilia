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

function BlueprintArchitectureVisualizer({ isDark }: { isDark: boolean }) {
  return (
    <div className="my-12 w-full font-sans select-none">
      <h2 className={`text-2xl font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>System Architecture</h2>
      <p className={`text-xs ${isDark ? 'text-zinc-500' : 'text-gray-500'} mb-8`}>
        Pipeline network tracing raw request payloads through type casting, validation guards, and relational molding.
      </p>

      {/* SVG Pipeline Map */}
      <div className="w-full max-w-2xl mx-auto h-[320px] relative border border-dashed border-zinc-850 rounded-lg overflow-hidden">
        <svg viewBox="0 0 640 320" className="w-full h-full bg-transparent overflow-visible">
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

          {/* Context Boundaries */}
          {/* Inbound Context */}
          <rect x="130" y="110" width="150" height="170" rx="6" fill="none" stroke="#10b981" strokeWidth="1" strokeDasharray="3 3" opacity="0.35" />
          <text x="140" y="125" fill="#10b981" fontSize="7" opacity="0.6" fontFamily="monospace" fontWeight="bold">INBOUND CONTRACT</text>

          {/* Outbound Context */}
          <rect x="360" y="110" width="150" height="170" rx="6" fill="none" stroke="#3b82f6" strokeWidth="1" strokeDasharray="3 3" opacity="0.35" />
          <text x="370" y="125" fill="#3b82f6" fontSize="7" opacity="0.6" fontFamily="monospace" fontWeight="bold">OUTBOUND CONTRACT</text>

          {/* SYSTEM WIRING CONNECTIONS */}
          {/* 1. Request -> Guard */}
          <path d="M 70,70 V 160" fill="none" stroke={isDark ? "#1f1f23" : "#f1f5f9"} strokeWidth="1.5" />
          <motion.path
            d="M 70,70 V 160" fill="none" stroke="#10b981" strokeWidth="2" strokeDasharray="4 12"
            animate={{ strokeDashoffset: [100, 0] }}
            transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
          />

          {/* 2. Guard -> Cast */}
          <path d="M 70,160 H 200" fill="none" stroke={isDark ? "#1f1f23" : "#f1f5f9"} strokeWidth="1.5" />
          <motion.path
            d="M 70,160 H 200" fill="none" stroke="#10b981" strokeWidth="2" strokeDasharray="4 12"
            animate={{ strokeDashoffset: [100, 0] }}
            transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
          />

          {/* 3. Cast -> Ward */}
          <path d="M 200,160 V 240" fill="none" stroke={isDark ? "#1f1f23" : "#f1f5f9"} strokeWidth="1.5" />
          <motion.path
            d="M 200,160 V 240" fill="none" stroke="#10b981" strokeWidth="2" strokeDasharray="4 12"
            animate={{ strokeDashoffset: [100, 0] }}
            transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
          />

          {/* 4. Ward -> Imprint Model */}
          <path d="M 200,240 H 320" fill="none" stroke={isDark ? "#1f1f23" : "#f1f5f9"} strokeWidth="1.5" />
          <motion.path
            d="M 200,240 H 320" fill="none" stroke="#059669" strokeWidth="2" strokeDasharray="4 12"
            animate={{ strokeDashoffset: [100, 0] }}
            transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
          />

          {/* 5. Imprint Model -> Projection */}
          <path d="M 320,240 H 440" fill="none" stroke={isDark ? "#1f1f23" : "#f1f5f9"} strokeWidth="1.5" />
          <motion.path
            d="M 320,240 H 440" fill="none" stroke="#3b82f6" strokeWidth="2" strokeDasharray="4 12"
            animate={{ strokeDashoffset: [0, 100] }}
            transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
          />

          {/* 6. Projection -> Lens */}
          <path d="M 440,240 V 160" fill="none" stroke={isDark ? "#1f1f23" : "#f1f5f9"} strokeWidth="1.5" />
          <motion.path
            d="M 440,240 V 160" fill="none" stroke="#3b82f6" strokeWidth="2" strokeDasharray="4 12"
            animate={{ strokeDashoffset: [0, 100] }}
            transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
          />

          {/* 7. Lens -> Mold */}
          <path d="M 440,160 H 570" fill="none" stroke={isDark ? "#1f1f23" : "#f1f5f9"} strokeWidth="1.5" />
          <motion.path
            d="M 440,160 H 570" fill="none" stroke="#2563eb" strokeWidth="2" strokeDasharray="4 12"
            animate={{ strokeDashoffset: [0, 100] }}
            transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
          />

          {/* 8. Mold -> Response */}
          <path d="M 570,160 V 70" fill="none" stroke={isDark ? "#1f1f23" : "#f1f5f9"} strokeWidth="1.5" />
          <motion.path
            d="M 570,160 V 70" fill="none" stroke="#2563eb" strokeWidth="2" strokeDasharray="4 12"
            animate={{ strokeDashoffset: [0, 100] }}
            transition={{ repeat: Infinity, duration: 3, ease: "linear" }}
          />

          {/* ARCHITECTURE SYSTEM NODES */}
          {/* Node 1: Request Payload */}
          <circle cx="70" cy="70" r="4" fill="#10b981" />
          <text x="82" y="73" fill="#10b981" fontSize="8" fontWeight="bold" fontFamily="monospace">REQUEST PAYLOAD</text>

          {/* Node 2: Controller Guard */}
          <circle cx="70" cy="160" r="4" fill="#10b981" />
          <text x="82" y="163" fill="#10b981" fontSize="8" fontWeight="bold" fontFamily="monospace">CONTROLLER GUARD</text>

          {/* Node 3: Facet Cast */}
          <circle cx="200" cy="160" r="4" fill="#10b981" />
          <text x="212" y="163" fill="#10b981" fontSize="8" fontWeight="bold" fontFamily="monospace">FACET CAST</text>

          {/* Node 4: Ward Validator */}
          <circle cx="200" cy="240" r="4" fill="#10b981" />
          <text x="212" y="243" fill="#10b981" fontSize="8" fontWeight="bold" fontFamily="monospace">WARD VALIDATOR</text>

          {/* Node 5: DB Model Core (Imprint) */}
          <circle cx="320" cy="240" r="6" fill="#059669" />
          <text x="320" y="226" textAnchor="middle" fill="#059669" fontSize="8" fontWeight="bold" fontFamily="monospace">ORM IMPRINT MODEL</text>

          {/* Node 6: Projection Filter */}
          <circle cx="440" cy="240" r="4" fill="#3b82f6" />
          <text x="428" y="226" textAnchor="middle" fill="#3b82f6" fontSize="8" fontWeight="bold" fontFamily="monospace">PROJECTION FILTER</text>

          {/* Node 7: Lens Resolver */}
          <circle cx="440" cy="160" r="4" fill="#3b82f6" />
          <text x="428" y="146" textAnchor="middle" fill="#3b82f6" fontSize="8" fontWeight="bold" fontFamily="monospace">LENS RESOLVER</text>

          {/* Node 8: Facet Mold */}
          <circle cx="570" cy="160" r="4" fill="#2563eb" />
          <text x="558" y="163" textAnchor="end" fill="#2563eb" fontSize="8" fontWeight="bold" fontFamily="monospace">FACET MOLD</text>

          {/* Node 9: Response JSON */}
          <circle cx="570" cy="70" r="4" fill="#2563eb" />
          <text x="558" y="73" textAnchor="end" fill="#2563eb" fontSize="8" fontWeight="bold" fontFamily="monospace">JSON RESPONSE</text>

        </svg>
      </div>

      {/* Static Typographic Summary Columns */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-x-16 gap-y-10 mt-12 pt-8 border-t border-dashed border-zinc-800/30">
        <div>
          <h3 className="text-[10px] font-mono font-bold tracking-wider text-emerald-500 uppercase mb-4">
            Inbound Request Pipeline
          </h3>
          <ul className="space-y-4">
            <li className="flex flex-col gap-1">
              <span className={`text-xs font-mono font-semibold ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>
                1. Request Payload & Controller Guard
              </span>
              <span className={`text-xs font-light leading-normal ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                Raw HTTP payloads are bound to Controller routes via decorators (e.g. <code>request_blueprint=UserBlueprint</code>), intercepting incoming streams.
              </span>
            </li>
            <li className="flex flex-col gap-1">
              <span className={`text-xs font-mono font-semibold ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>
                2. Facet Cast
              </span>
              <span className={`text-xs font-light leading-normal ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                Coerces raw data types into their target Python-native counterparts recursively (e.g., matching string timestamps into <code>datetime</code> formats).
              </span>
            </li>
            <li className="flex flex-col gap-1">
              <span className={`text-xs font-mono font-semibold ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>
                3. Ward Validator
              </span>
              <span className={`text-xs font-light leading-normal ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                Triggers facet rules and resolves custom <code>@ward</code> methods to check cross-field business constraints.
              </span>
            </li>
            <li className="flex flex-col gap-1">
              <span className={`text-xs font-mono font-semibold ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>
                4. ORM Imprint
              </span>
              <span className={`text-xs font-light leading-normal ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                Flushes the validated dataset back into the target database ORM model as a transaction-safe SQL <code>INSERT</code> or <code>UPDATE</code>.
              </span>
            </li>
          </ul>
        </div>

        <div>
          <h3 className="text-[10px] font-mono font-bold tracking-wider text-blue-500 uppercase mb-4">
            Outbound Response Pipeline
          </h3>
          <ul className="space-y-4">
            <li className="flex flex-col gap-1">
              <span className={`text-xs font-mono font-semibold ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>
                1. Projection Filter
              </span>
              <span className={`text-xs font-light leading-normal ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                Filters attributes based on named projection limits (e.g. <code>UserBlueprint["public"]</code>), automatically stripping write-only credentials.
              </span>
            </li>
            <li className="flex flex-col gap-1">
              <span className={`text-xs font-mono font-semibold ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>
                2. Lens Resolver
              </span>
              <span className={`text-xs font-light leading-normal ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                Recursively resolves model relationships through nested blueprints, enforcing graph depth limits and preventing cyclic infinity loops.
              </span>
            </li>
            <li className="flex flex-col gap-1">
              <span className={`text-xs font-mono font-semibold ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>
                3. Facet Mold
              </span>
              <span className={`text-xs font-light leading-normal ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                Serializes elements back to clean serializable dictionaries, executing custom read-only <code>@computed</code> annotations.
              </span>
            </li>
            <li className="flex flex-col gap-1">
              <span className={`text-xs font-mono font-semibold ${isDark ? 'text-zinc-300' : 'text-gray-800'}`}>
                4. JSON Response
              </span>
              <span className={`text-xs font-light leading-normal ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                Returns structured serialized responses directly back to the HTTP client as a final JSON payload.
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
