import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import { Link } from 'react-router-dom'
import { Binary, ArrowRight, GitBranch, Shield, Layers, Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

const stages = [
  { step: '1', label: 'Declare', desc: 'Define Facets and Spec on a Blueprint subclass.' },
  { step: '2', label: 'Cast', desc: 'Inbound raw values are coerced by each Facet.' },
  { step: '3', label: 'Seal', desc: 'Facet validators + Ward cross-field checks run.' },
  { step: '4', label: 'Imprint', desc: 'Validated data is written back to the model.' },
  { step: '5', label: 'Mold', desc: 'Model instance is serialized through Facets → dict.' },
]

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
