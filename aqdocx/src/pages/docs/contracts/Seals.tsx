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
            { phase: '3. Wards (@ward)', desc: 'Runs cross-field validators. Rejects by raising SealFault or calling reject().' },
            { phase: '4. Imprint', desc: 'Writes validated data to database via imprint().' },
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
bp = ProductContract(data=request.json)

# Run validations
if not bp.is_sealed():
    return Response.json(bp.errors, status=422)

# Persist
product = await bp.imprint(db=db)`}</CodeBlock>
      </section>

      {/* Cross-field validation */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Cross-Field Validation</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Use the <DocTerm id="bp.ward">@ward</DocTerm> decorator to enforce dependencies between multiple fields:
        </p>
        <CodeBlock language="python">{`from aquilia.contracts import Contract, SealFault
from aquilia.contracts.ward import ward

class EventContract(Contract):
    start_date = DateFacet()
    end_date = DateFacet()

    @ward
    def validate_dates(self):
        """Ensure end_date is strictly after start_date."""
        start = self.validated.get("start_date")
        end = self.validated.get("end_date")
        if start and end and end <= start:
            # Raise SealFault to register field error
            raise SealFault({"end_date": "End date must be after start date"})`}</CodeBlock>
      </section>

      {/* Accumulating errors */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Accumulating Errors</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Accumulate validation errors instead of raising immediately using <code>self.reject()</code>:
        </p>
        <CodeBlock language="python">{`class SignupContract(Contract):
    password = TextFacet(min_length=8)
    password_confirm = TextFacet()

    @ward
    def verify_password_match(self):
        pwd = self.validated.get("password")
        conf = self.validated.get("password_confirm")
        if pwd != conf:
            self.reject("password_confirm", "Passwords do not match.")`}</CodeBlock>
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
