import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { FileJson } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function BlueprintsSchemas() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <FileJson className="w-4 h-4" />
          Blueprints / OpenAPI Schemas
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            OpenAPI Schemas
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Blueprints auto-generate JSON Schema and OpenAPI component schemas. Every Facet contributes its schema fragment, and Projections produce per-view schemas — all without manual schema writing.
        </p>
      </div>

      {/* generate_schema */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Generating JSON Schema</h2>
        <CodeBlock language="python" filename="schema_gen.py">{`from aquilia.blueprints.schema import generate_schema


# Generate JSON Schema for a Blueprint
schema = generate_schema(ProductBlueprint)
print(schema)
# {
#   "type": "object",
#   "properties": {
#     "id": {"type": "integer", "readOnly": true},
#     "name": {"type": "string", "maxLength": 200},
#     "price": {"type": "number", "minimum": 0},
#     "sku": {"type": "string", "maxLength": 50, "pattern": "^[A-Z0-9-]+$"},
#     "category": {"type": "string", "enum": ["electronics", "clothing", "food"]},
#     "is_active": {"type": "boolean", "default": true},
#     "tags": {"type": "array", "items": {"type": "string", "maxLength": 50}},
#   },
#   "required": ["name", "price", "sku"]
# }


# Schema for a specific projection
schema = ProductBlueprint.to_schema(projection="__minimal__")
# Only includes: id, name, price, slug

# Schema for input mode (excludes read_only fields)
schema = ProductBlueprint.to_schema(mode="input")

# Schema for output mode (excludes write_only fields)
schema = ProductBlueprint.to_schema(mode="output")`}</CodeBlock>
      </section>

      {/* generate_component_schemas */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>OpenAPI Component Schemas</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Generate OpenAPI <code className="text-aquilia-500">components.schemas</code> for multiple Blueprints at once, with per-projection variants:
        </p>
        <CodeBlock language="python" filename="component_schemas.py">{`from aquilia.blueprints.schema import generate_component_schemas


# Generate component schemas for all Blueprints
components = generate_component_schemas([
    ProductBlueprint,
    UserBlueprint,
    OrderBlueprint,
])

print(components)
# {
#   "ProductBlueprint": { ... default projection schema ... },
#   "ProductBlueprint_minimal": { ... minimal projection schema ... },
#   "ProductBlueprint_detail": { ... detail projection schema ... },
#   "UserBlueprint": { ... },
#   "OrderBlueprint": { ... },
# }

# This output slots directly into your OpenAPI spec:
# openapi_spec["components"]["schemas"] = components`}</CodeBlock>
      </section>

      {/* Per-Facet Schema */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Per-Facet Schema Output</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Each Facet type generates appropriate JSON Schema fragments:
        </p>
        <div className={`overflow-hidden rounded-xl border ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-zinc-900' : 'bg-gray-50'}>
                <th className={`text-left py-3 px-4 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Facet</th>
                <th className={`text-left py-3 px-4 font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>JSON Schema Output</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'divide-y divide-white/5' : 'divide-y divide-gray-100'}>
              {[
                { f: 'TextFacet', s: '{"type": "string", "maxLength": N, "minLength": N, "pattern": "..."}' },
                { f: 'EmailFacet', s: '{"type": "string", "format": "email"}' },
                { f: 'URLFacet', s: '{"type": "string", "format": "uri"}' },
                { f: 'IntFacet', s: '{"type": "integer", "minimum": N, "maximum": N}' },
                { f: 'FloatFacet', s: '{"type": "number", "minimum": N, "maximum": N}' },
                { f: 'DecimalFacet', s: '{"type": "string", "format": "decimal"}' },
                { f: 'BoolFacet', s: '{"type": "boolean"}' },
                { f: 'DateFacet', s: '{"type": "string", "format": "date"}' },
                { f: 'DateTimeFacet', s: '{"type": "string", "format": "date-time"}' },
                { f: 'UUIDFacet', s: '{"type": "string", "format": "uuid"}' },
                { f: 'ListFacet', s: '{"type": "array", "items": {...}, "minItems": N, "maxItems": N}' },
                { f: 'DictFacet', s: '{"type": "object", "additionalProperties": {...}}' },
                { f: 'ChoiceFacet', s: '{"type": "string", "enum": [...]}' },
                { f: 'Computed', s: '{"readOnly": true, ...}' },
              ].map((row, i) => (
                <tr key={i} className={isDark ? 'bg-[#0A0A0A]' : 'bg-white'}>
                  <td className="py-2 px-4"><code className="text-aquilia-500 font-mono text-xs">{row.f}</code></td>
                  <td className={`py-2 px-4 font-mono text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{row.s}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Integration with OpenAPI endpoint */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Integration with OpenAPI Endpoint</h2>
        <CodeBlock language="python" filename="openapi_endpoint.py">{`from aquilia import Controller, Get
from aquilia.blueprints.schema import generate_component_schemas
from myapp.blueprints import ProductBlueprint, UserBlueprint, OrderBlueprint


class OpenAPIController(Controller):
    prefix = "/api"

    @Get("/openapi.json")
    async def openapi_spec(self, ctx):
        schemas = generate_component_schemas([
            ProductBlueprint,
            UserBlueprint,
            OrderBlueprint,
        ])

        spec = {
            "openapi": "3.1.0",
            "info": {"title": "My API", "version": "1.0.0"},
            "components": {"schemas": schemas},
            "paths": { ... }  # Your route definitions
        }

        return ctx.json(spec)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
