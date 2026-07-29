import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function ContractsSeals() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const t = (d: string, l: string) => isDark ? d : l

  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm mb-6">
        <Link to="/docs" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Docs</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <Link to="/docs/contracts/overview" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Contracts</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <span className={t('text-gray-300','text-gray-600')}>Seals & Validation</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Seals & Validation</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Sealing is validation. The <DocTerm id="bp.is_sealed">is_sealed()</DocTerm> method runs type checks, constraint enforcement, and custom <DocTerm id="bp.ward">@ward</DocTerm> validators.
        </p>
      </div>

      {/* Validation pipeline */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-6 ${t('text-white','text-gray-900')}`}>Validation Pipeline</h2>
        <div className="space-y-4">
          {[
            { phase: '1. Cast', desc: 'Coerces raw inputs (e.g. string to int) on each Facet. Fails with CastFault.' },
            { phase: '2. Field validation', desc: 'Checks constraints (length, min/max, email patterns) per-facet.' },
            { phase: '3. Nested', desc: 'Each nested Contract runs its own full pipeline, including its wards and validate() hook.' },
            { phase: '4. Wards (@ward)', desc: 'Runs cross-field validators in order, honouring when/groups. Rejects via reject().' },
            { phase: '5. Imprint', desc: 'Writes validated data to database via imprint().' },
          ].map(p => (
            <div key={p.phase} className="flex gap-4 items-start">
              <span className={`font-mono font-bold text-sm shrink-0 w-32 ${t('text-aquilia-400','text-aquilia-600')}`}>{p.phase}</span>
              <p className={`text-sm ${t('text-gray-300','text-gray-600')}`}>{p.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Execution */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Execution</h2>
        <CodeBlock language="python">{`# Instantiate with request body
bp = ProductContract(data=await ctx.json())

# Run validations
if not bp.is_sealed():
    return Response.json(bp.errors, status=422)

# Persist
product = await bp.imprint()`}</CodeBlock>
        <p className={`mt-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Pass <code>raise_fault=True</code> to raise a <code>SealFault</code> instead of returning <code>False</code>. The fault carries the same
          field errors on <code>.field_errors</code>, so a fault handler can render them without re-running validation.
        </p>
      </section>

      {/* Cross-field validation */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Cross-Field Validation</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Use the <DocTerm id="bp.ward">@ward</DocTerm> decorator to enforce dependencies between multiple fields. A ward receives the
          validated data as its second argument, so every field it reads has already been cast and constraint-checked:
        </p>
        <CodeBlock language="python">{`from aquilia.contracts import Contract, ward
from aquilia.contracts.facets import DateFacet

class EventContract(Contract):
    start_date = DateFacet()
    end_date = DateFacet()

    @ward
    def dates_ordered(self, data):
        """Ensure end_date is strictly after start_date."""
        if data["end_date"] <= data["start_date"]:
            self.reject("end_date", "End date must be after start date")`}</CodeBlock>
      </section>

      {/* Accumulating errors */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Accumulating Errors</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          <code>self.reject(field, message)</code> records an error and lets the remaining wards run, so a form reports every problem at once
          rather than one per round trip:
        </p>
        <CodeBlock language="python">{`class SignupContract(Contract):
    password = TextFacet(min_length=8)
    password_confirm = TextFacet()

    @ward
    def passwords_match(self, data):
        if data["password"] != data["password_confirm"]:
            self.reject("password_confirm", "Passwords do not match.")

# {"password_confirm": ["Passwords do not match."]}`}</CodeBlock>
        <p className={`mt-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Set <code>Spec.fail_fast = True</code> to stop at the first ward error instead — useful for pipelines where a later rule&apos;s output
          would be noise once an earlier one has failed. See <Link to="/docs/contracts/validation-control" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Validation Control</Link>.
        </p>
      </section>

      {/* Nested contracts */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Nested Contracts</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          A nested Contract runs its <em>full</em> pipeline, not just its field checks. Its wards and its <code>validate()</code> hook enforce
          rules exactly as they do at the top level, and errors are reported at the failing field&apos;s path:
        </p>
        <CodeBlock language="python">{`class LineItem(Contract):
    qty = IntFacet()

    @ward
    def qty_positive(self, data):
        if data["qty"] < 1:
            self.reject("qty", "Must be at least 1")

class OrderContract(Contract):
    items: list[LineItem] = None

order = OrderContract(data={"items": [{"qty": 5}, {"qty": 0}]})
order.is_sealed()   # False
order.errors        # {"items": {"1": {"qty": ["Must be at least 1"]}}}`}</CodeBlock>
        <div className={`mt-4 p-4 rounded-lg border ${t('bg-amber-500/5 border-amber-500/20','bg-amber-50 border-amber-200')}`}>
          <p className={`text-sm ${t('text-gray-300','text-gray-700')}`}>
            <strong className={t('text-amber-400','text-amber-700')}>Changed in v1.3.5.</strong> Before this release a nested Contract was validated
            structurally only, so its wards and <code>validate()</code> override never ran. Payloads that previously passed may now be rejected —
            correctly. See the <Link to="/releases/1.3.5/contracts_pipeline.md" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>release notes</Link>.
          </p>
        </div>
      </section>

      {/* Async */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Async Validation</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          A ward that needs to await — a uniqueness check, a remote lookup — declares <code>mode=&quot;async&quot;</code> and is run by
          <code> is_sealed_async()</code>:
        </p>
        <CodeBlock language="python">{`class UserContract(Contract):
    email = EmailFacet()

    @ward(mode="async")
    async def email_unique(self, data):
        if await User.objects.filter(email=data["email"]).exists():
            self.reject("email", "Email address is already registered")

if not await contract.is_sealed_async():
    return Response.json(contract.errors, status=422)`}</CodeBlock>
        <p className={`mt-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Calling the synchronous <code>is_sealed()</code> on a Contract with async wards raises <code>ContractAsyncMismatchFault</code> rather
          than skipping them. As of v1.3.5 this detection walks nested Contracts too, so a parent whose child declares an async ward is caught.
          Full details in <Link to="/docs/contracts/async-pipeline" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Async Pipeline</Link>.
        </p>
      </section>

      {/* Malformed input */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Malformed Bodies</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          A body that is not an object is a document-level problem, not a set of missing fields. It is reported under the
          <code> __all__</code> key:
        </p>
        <CodeBlock language="python">{`UserContract(data="not an object").errors
# {"__all__": ["Expected an object, got str"]}`}</CodeBlock>
        <p className={`mt-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Before v1.3.5 this produced a &quot;This field is required&quot; error per field — a misdiagnosis that sent developers hunting the wrong bug.
          Clients that parse a 422 body should render <code>__all__</code> separately from field errors.
        </p>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/contracts/facets" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Facets
        </Link>
        <Link to="/docs/contracts/projections" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Projections <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
