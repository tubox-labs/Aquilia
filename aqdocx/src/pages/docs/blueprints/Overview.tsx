import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowRight, Layers, Database, Shield, Sparkles, GitBranch, Eye, FileCheck } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function BlueprintsOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Layers className="w-4 h-4" />
          Data Layer / Blueprints
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Blueprints
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Blueprints are Aquilia's first-class data contract system. They declare the exact shape of data flowing between your Models and the outside world — handling inbound validation, outbound serialization, relational views, projections, OpenAPI schema generation, and deep integration with DI, auth, and sessions.
        </p>
      </div>

      {/* Philosophy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Philosophy</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Unlike traditional serializers that treat validation and serialization as separate concerns, Blueprints unify the entire data lifecycle into a single, declarative contract. Every Blueprint defines:
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { icon: <Shield className="w-5 h-5" />, title: 'Cast', desc: 'Inbound type coercion — raw JSON values become typed Python objects' },
            { icon: <FileCheck className="w-5 h-5" />, title: 'Seal', desc: 'Validation pipeline — field-level, cross-field, and async validation' },
            { icon: <Database className="w-5 h-5" />, title: 'Imprint', desc: 'Write-back — validated data writes directly to Model instances' },
            { icon: <Eye className="w-5 h-5" />, title: 'Mold', desc: 'Outbound shaping — Model data transforms for API responses' },
            { icon: <GitBranch className="w-5 h-5" />, title: 'Lens', desc: 'Relational views — depth-controlled nested relationship rendering' },
            { icon: <Sparkles className="w-5 h-5" />, title: 'Projection', desc: 'Named field subsets — different views of the same data' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <div className="text-aquilia-500 mb-2">{item.icon}</div>
              <h3 className={`font-bold text-sm mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.title}</h3>
              <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Terminology */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Terminology</h2>
        <div className={`overflow-hidden rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-zinc-900' : 'bg-gray-50'}>
                <th className={`text-left py-3 px-4 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Term</th>
                <th className={`text-left py-3 px-4 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Description</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'divide-y divide-white/5' : 'divide-y divide-gray-100'}>
              {[
                { term: 'Blueprint', desc: 'A declarative data contract bound to a Model (or standalone)' },
                { term: 'Facet', desc: 'A field-level primitive — the atomic unit of a Blueprint (like TextFacet, IntFacet)' },
                { term: 'Cast', desc: 'Inbound type coercion (str → int, ISO string → datetime, etc.)' },
                { term: 'Seal', desc: 'Validation — field-level constraints, cross-field rules, async checks' },
                { term: 'Imprint', desc: 'Write validated data onto a Model instance (create or update)' },
                { term: 'Mold', desc: 'Outbound transformation — shape data for API response' },
                { term: 'Lens', desc: 'A Facet that renders a related object through another Blueprint' },
                { term: 'Projection', desc: 'A named subset of fields — different views of the same Blueprint' },
                { term: 'Spec', desc: 'Inner class (like Meta) that configures model binding, field selection, projections' },
              ].map((row, i) => (
                <tr key={i} className={isDark ? 'bg-[#0A0A0A]' : 'bg-white'}>
                  <td className="py-2 px-4"><code className="text-aquilia-500 font-mono text-xs">{row.term}</code></td>
                  <td className={`py-2 px-4 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{row.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Quick Start */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Quick Start</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Define a Blueprint with explicit Facet declarations or use type annotations with the <code className="text-aquilia-500">Field</code> descriptor.
        </p>

        <h3 className={`text-lg font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Style 1: Explicit Facets</h3>
        <CodeBlock language="python" filename="blueprints.py">{`from aquilia.blueprints import (
    Blueprint, TextFacet, IntFacet, FloatFacet,
    EmailFacet, BoolFacet, ChoiceFacet, ListFacet,
)
from myapp.models import Product


class ProductBlueprint(Blueprint):
    """Declares the data contract for Product."""

    name = TextFacet(max_length=200, required=True, help_text="Product name")
    price = FloatFacet(min_value=0, required=True)
    sku = TextFacet(max_length=50, required=True, pattern=r"^[A-Z0-9-]+$")
    description = TextFacet(max_length=2000, required=False, default="")
    category = ChoiceFacet(choices=["electronics", "clothing", "food"])
    is_active = BoolFacet(default=True)
    tags = ListFacet(child=TextFacet(max_length=50), required=False)

    class Spec:
        model = Product
        fields = ["name", "price", "sku", "description", "category", "is_active", "tags"]
        read_only_fields = ["id"]`}</CodeBlock>

        <h3 className={`text-lg font-bold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>Style 2: Type Annotations</h3>
        <CodeBlock language="python" filename="blueprints.py">{`from aquilia.blueprints import Blueprint, Field
from myapp.models import Product


class ProductBlueprint(Blueprint):
    """Same contract using Python type annotations."""

    name: str = Field(max_length=200, required=True)
    price: float = Field(ge=0, required=True)
    sku: str = Field(max_length=50, pattern=r"^[A-Z0-9-]+$")
    description: str = Field(max_length=2000, default="")
    category: str = Field(choices=["electronics", "clothing", "food"])
    is_active: bool = Field(default=True)
    tags: list[str] = Field(required=False)

    class Spec:
        model = Product
        fields = "__all__"
        read_only_fields = ["id"]`}</CodeBlock>
      </section>

      {/* Lifecycle Flow */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Lifecycle Flow</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Every Blueprint follows a strict lifecycle depending on the direction of data flow:
        </p>

        <div className={`p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`}>
          <h3 className={`font-bold text-sm mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Inbound (Request → Model)</h3>
          <div className={`font-mono text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-aquilia-500 font-bold">1.</span> Raw JSON payload arrives
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-aquilia-500 font-bold">2.</span> <code>Cast</code> — each Facet coerces its value to the correct type
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-aquilia-500 font-bold">3.</span> <code>Seal</code> — field-level validation (min/max, patterns, etc.)
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-aquilia-500 font-bold">4.</span> <code>seal_*</code> — cross-field validators (e.g., seal_password_match)
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-aquilia-500 font-bold">5.</span> <code>validate()</code> — final object-level validation hook
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-aquilia-500 font-bold">6.</span> <code>async_seal_*</code> — async validators (DB uniqueness checks, etc.)
            </div>
            <div className="flex items-center gap-2">
              <span className="text-aquilia-500 font-bold">7.</span> <code>Imprint</code> — write validated data to Model instance
            </div>
          </div>
        </div>

        <div className={`p-6 rounded-2xl border mt-4 ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`}>
          <h3 className={`font-bold text-sm mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Outbound (Model → Response)</h3>
          <div className={`font-mono text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-aquilia-500 font-bold">1.</span> Model instance passed to Blueprint
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-aquilia-500 font-bold">2.</span> <code>Mold</code> — each Facet transforms the value for JSON output
            </div>
            <div className="flex items-center gap-2 mb-2">
              <span className="text-aquilia-500 font-bold">3.</span> <code>Lens</code> — related objects rendered through nested Blueprints
            </div>
            <div className="flex items-center gap-2">
              <span className="text-aquilia-500 font-bold">4.</span> <code>Projection</code> — only selected fields are included in output
            </div>
          </div>
        </div>
      </section>

      {/* Using with Controllers */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Using with Controllers</h2>
        <CodeBlock language="python" filename="controller.py">{`from aquilia import Controller, Post, Put, Get
from myapp.blueprints import ProductBlueprint


class ProductController(Controller):
    prefix = "/api/products"

    @Post("/", status_code=201)
    async def create(self, ctx, payload: ProductBlueprint):
        # payload is auto-parsed and validated via Blueprint
        if not payload.is_sealed():
            return ctx.json(payload.errors, status=422)
        
        product = payload.imprint()  # Creates Model instance
        await product.save()
        
        # Render response through same Blueprint
        output = ProductBlueprint(instance=product)
        return ctx.json(output.data)

    @Put("/{id:int}")
    async def update(self, ctx, id: int, payload: ProductBlueprint):
        product = await Product.objects.get(id=id)
        
        if not payload.is_sealed():
            return ctx.json(payload.errors, status=422)
        
        payload.imprint(instance=product, partial=True)
        await product.save()
        
        return ctx.json(ProductBlueprint(instance=product).data)

    @Get("/{id:int}")
    async def detail(self, ctx, id: int):
        product = await Product.objects.get(id=id)
        # Use a projection for minimal response
        return ctx.json(ProductBlueprint(instance=product, projection="summary").data)`}</CodeBlock>
      </section>

      {/* Auto-derivation from Models */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Auto-Derivation from Models</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          When a <code className="text-aquilia-500">Spec.model</code> is provided, Blueprint auto-derives Facets from Model fields. You only need to declare fields that require customization.
        </p>
        <CodeBlock language="python" filename="auto_derive.py">{`class ProductBlueprint(Blueprint):
    """Auto-derives Facets from Product model fields."""
    
    class Spec:
        model = Product
        fields = "__all__"                       # All model fields
        exclude = ["internal_notes"]              # Skip these
        read_only_fields = ["id", "created_at"]   # Can't be written
        write_only_fields = ["password"]          # Never in output

    # Override auto-derived field with custom settings
    sku = TextFacet(max_length=50, pattern=r"^[A-Z0-9-]+$")


# Field mapping: Model field → Facet
# CharField        → TextFacet
# IntegerField     → IntFacet
# FloatField       → FloatFacet
# BooleanField     → BoolFacet
# DateField        → DateFacet
# DateTimeField    → DateTimeFacet
# EmailField       → EmailFacet
# URLField         → URLFacet
# UUIDField        → UUIDFacet
# DecimalField     → DecimalFacet
# SlugField        → SlugFacet
# ForeignKey       → IntFacet (PK) or Lens
# ManyToManyField  → ListFacet(IntFacet) or Lens`}</CodeBlock>
      </section>

      {/* Validation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Validation (Sealing)</h2>
        <CodeBlock language="python" filename="validation.py">{`from aquilia.blueprints import Blueprint, TextFacet, EmailFacet, IntFacet
from aquilia.blueprints.exceptions import SealFault


class RegisterBlueprint(Blueprint):
    username = TextFacet(min_length=3, max_length=30)
    email = EmailFacet(required=True)
    password = TextFacet(min_length=8)
    password_confirm = TextFacet(min_length=8)
    age = IntFacet(min_value=13)

    class Spec:
        model = User
        fields = ["username", "email", "password", "age"]

    # ── Cross-field validator ──
    def seal_password_match(self, data):
        """Cross-field seal — called after field-level validation."""
        if data.get("password") != data.get("password_confirm"):
            self.reject("password_confirm", "Passwords do not match.")

    # ── Field-level validator ──
    def seal_username(self, value):
        """Per-field seal — called for 'username' specifically."""
        if value.lower() in ["admin", "root", "system"]:
            self.reject("username", "This username is reserved.")
        return value.lower()

    # ── Async validator ──
    async def async_seal_email_unique(self, data):
        """Async seal — runs database checks."""
        exists = await User.objects.filter(email=data["email"]).exists()
        if exists:
            self.reject("email", "Email already registered.")

    # ── Final validation hook ──
    def validate(self, data):
        """Object-level validator — last sync check."""
        data.pop("password_confirm", None)
        return data


# Usage
bp = RegisterBlueprint(data={"username": "john", "email": "john@example.com", ...})

# Sync validation
if bp.is_sealed():
    user = bp.imprint()
else:
    print(bp.errors)  # {"password_confirm": ["Passwords do not match."]}

# Async validation (includes async_seal_* methods)
if await bp.is_sealed_async():
    user = bp.imprint()
else:
    print(bp.errors)`}</CodeBlock>
      </section>

      {/* Sub-Pages */}
      <section>
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Deep Dives</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { title: 'Facets', desc: 'Complete reference for all field-level Facet types', to: '/docs/blueprints/facets' },
            { title: 'Projections', desc: 'Named field subsets and multiple views', to: '/docs/blueprints/projections' },
            { title: 'Lenses', desc: 'Depth-controlled relational rendering', to: '/docs/blueprints/lenses' },
            { title: 'Seals & Validation', desc: 'Field, cross-field, and async validation patterns', to: '/docs/blueprints/seals' },
            { title: 'Annotations & Field()', desc: 'Type-annotation-driven Blueprint declarations', to: '/docs/blueprints/annotations' },
            { title: 'Controller Integration', desc: 'Blueprints with DI, auth, sessions, and controllers', to: '/docs/blueprints/integration' },
            { title: 'OpenAPI Schemas', desc: 'Auto-generated JSON Schema and OpenAPI specs', to: '/docs/blueprints/schemas' },
            { title: 'Faults', desc: 'Blueprint-specific error types and handling', to: '/docs/blueprints/faults' },
          ].map((item, i) => (
            <Link key={i} to={item.to} className={`group p-5 rounded-xl border transition-all hover:-translate-y-0.5 ${isDark ? 'bg-[#0A0A0A] border-white/10 hover:border-aquilia-500/30' : 'bg-white border-gray-200 hover:border-aquilia-500/30'}`}>
              <h3 className={`font-bold text-sm mb-1 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
                {item.title}
                <ArrowRight className="w-3 h-3 text-aquilia-500 opacity-0 group-hover:opacity-100 transition" />
              </h3>
              <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{item.desc}</p>
            </Link>
          ))}
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
