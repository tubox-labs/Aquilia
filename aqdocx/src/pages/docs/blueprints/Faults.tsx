import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { AlertTriangle } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function BlueprintsFaults() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <AlertTriangle className="w-4 h-4" />
          Blueprints / Faults
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Blueprint Faults
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Blueprints use structured fault types instead of bare exceptions. All Blueprint errors are part of the <code className="text-aquilia-500">BLUEPRINT</code> fault domain and integrate seamlessly with the AquilaFaults error handling system.
        </p>
      </div>

      {/* Fault Taxonomy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Taxonomy</h2>
        <div className="space-y-3">
          {[
            { code: 'BP100', name: 'CastFault', desc: 'Type coercion failed — raw value could not be converted to expected Python type', severity: 'ERROR' },
            { code: 'BP200', name: 'SealFault', desc: 'Validation failed — one or more fields did not pass seal constraints', severity: 'WARN' },
            { code: 'BP210', name: 'MissingSealFault', desc: 'Required field was missing from input data', severity: 'WARN' },
            { code: 'BP300', name: 'ImprintFault', desc: 'Failed to write validated data to Model instance', severity: 'ERROR' },
            { code: 'BP400', name: 'LensCycleFault', desc: 'Circular reference detected in Blueprint Lens chain', severity: 'ERROR' },
            { code: 'BP500', name: 'SchemaFault', desc: 'Error generating JSON Schema for this Blueprint', severity: 'WARN' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <div className="flex items-center gap-3">
                <code className="text-aquilia-500 font-mono font-bold text-sm">{item.code}</code>
                <code className={`font-bold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.name}</code>
                <span className={`text-xs px-2 py-0.5 rounded-full ${
                  item.severity === 'ERROR'
                    ? 'bg-red-500/10 text-red-400'
                    : 'bg-yellow-500/10 text-yellow-400'
                }`}>{item.severity}</span>
              </div>
              <p className={`text-sm mt-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CastFault */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>CastFault</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Raised when a Facet cannot coerce a raw value to the expected Python type:
        </p>
        <CodeBlock language="python" filename="cast_fault.py">{`from aquilia.blueprints.exceptions import CastFault

# CastFault is raised internally during Phase 1 (Cast)
# Typically caught by the Blueprint and added to errors dict

# Example triggers:
# IntFacet receives "not a number"
# DateTimeFacet receives "invalid date"
# BoolFacet receives [1, 2, 3]
# EmailFacet receives "not@an@email"

try:
    facet = IntFacet()
    facet.cast("hello")
except CastFault as e:
    print(e.field)     # "quantity"
    print(e.message)   # "Expected integer, got str"
    print(e.code)      # "BP100"`}</CodeBlock>
      </section>

      {/* SealFault */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>SealFault</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Raised when validation fails — either from Facet constraints or from custom seal methods:
        </p>
        <CodeBlock language="python" filename="seal_fault.py">{`from aquilia.blueprints.exceptions import SealFault

bp = ProductBlueprint(data={"name": "", "price": -10})

# SealFault accumulates all errors
bp.is_sealed()
print(bp.errors)
# {"name": ["This field is required."], "price": ["Must be >= 0."]}

# With raise_fault=True:
try:
    bp.is_sealed(raise_fault=True)
except SealFault as e:
    print(e.field_errors)    # dict of field → error messages
    print(e.error_count)     # Total number of errors
    print(e.as_response_body())
    # {
    #   "fault_code": "BP200",
    #   "fault_domain": "BLUEPRINT",
    #   "message": "Validation failed",
    #   "field_errors": {
    #     "name": ["This field is required."],
    #     "price": ["Must be >= 0."]
    #   }
    # }`}</CodeBlock>
      </section>

      {/* Handling Faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Handling Blueprint Faults</h2>
        <CodeBlock language="python" filename="handling.py">{`from aquilia import Controller, Post
from aquilia.faults import fault_handler
from aquilia.blueprints.exceptions import SealFault


class ProductController(Controller):
    prefix = "/api/products"

    @Post("/", status_code=201)
    async def create(self, ctx, payload: ProductBlueprint):
        # Pattern 1: Check and return errors
        if not payload.is_sealed():
            return ctx.json(payload.errors, status=422)

        product = payload.imprint()
        await product.save()
        return ctx.json(ProductBlueprint(instance=product).data, status=201)


# Pattern 2: Global fault handler for SealFault
@fault_handler(SealFault)
async def handle_seal_fault(ctx, fault):
    """Auto-converts SealFault to 422 response."""
    return ctx.json(fault.as_response_body(), status=422)

# Register in workspace:
# workspace = Workspace(fault_handlers=[handle_seal_fault])


# Pattern 3: raise_fault=True for exception-based flow
class StrictProductController(Controller):
    prefix = "/api/strict/products"

    @Post("/")
    async def create(self, ctx, payload: ProductBlueprint):
        # This raises SealFault if validation fails
        # The global fault handler catches it automatically
        payload.is_sealed(raise_fault=True)
        
        product = payload.imprint()
        await product.save()
        return ctx.json(ProductBlueprint(instance=product).data, status=201)`}</CodeBlock>
      </section>

      {/* Faults Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Integration with AquilaFaults</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          All Blueprint faults inherit from <code className="text-aquilia-500">Fault</code> and integrate with Aquilia's fault engine:
        </p>
        <CodeBlock language="python" filename="integration.py">{`from aquilia.faults.core import Fault, Severity, FaultDomain
from aquilia.blueprints.exceptions import SealFault, CastFault

# All Blueprint faults have:
fault = SealFault(field="email", message="Invalid email")
fault.code        # "BP200"
fault.severity    # Severity.WARN
fault.domain      # FaultDomain.BLUEPRINT (or VALIDATION)
fault.public      # True (safe to show to user)
fault.retryable   # False (fix the input, don't retry)

# They appear in the FaultEngine's error log
# They are caught by global fault handlers
# They integrate with the trace/observability system`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
