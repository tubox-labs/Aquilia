import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function BlueprintsFacets() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const t = (d: string, l: string) => isDark ? d : l

  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm mb-6">
        <Link to="/docs" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Docs</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <Link to="/docs/blueprints/overview" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Blueprints</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <span className={t('text-gray-300','text-gray-600')}>Facets</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Facets</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Atomic field-level primitives of a Blueprint contract. Each <DocTerm id="bp.facet">Facet</DocTerm> manages type coercion (cast), validation (seal), and output representation (mold).
        </p>
      </div>

      {/* Base Facet Options */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Base Facet Options</h2>
        <CodeBlock language="python">{`from aquilia.blueprints import Facet

field = Facet(
    source="model_field",     # read from distinct model attribute
    required=True,            # fail CastFault if missing on inbound
    read_only=False,          # exclude from inbound cast
    write_only=False,         # exclude from outbound serialization
    default=None,             # fallback value
    allow_null=False,         # accept None
    allow_blank=False,        # accept empty string (TextFacet only)
    validators=[],            # additional validator callables
)`}</CodeBlock>
      </section>

      {/* Common Facets */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-6 ${t('text-white','text-gray-900')}`}>Built-in Facets</h2>

        {/* Text */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>
            <DocTerm id="bp.text_facet">TextFacet</DocTerm>
          </h3>
          <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
            Handles string properties with length boundaries and pattern matching.
          </p>
          <CodeBlock language="python">{`sku = TextFacet(max_length=50, pattern=r"^[A-Z0-9-]+$")`}</CodeBlock>
        </div>

        {/* Numeric */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>
            <DocTerm id="bp.int_facet">IntFacet</DocTerm>
          </h3>
          <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
            Coerces numeric strings/floats to integers. Validates min_value and max_value. Rejects booleans.
          </p>
          <CodeBlock language="python">{`quantity = IntFacet(min_value=1, max_value=99)`}</CodeBlock>
        </div>

        {/* Special */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>
            <DocTerm id="bp.computed_facet">Computed</DocTerm>
          </h3>
          <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
            Derived read-only fields computed via a function or method. Can also use the <DocTerm id="bp.computed_decorator">@computed</DocTerm> decorator.
          </p>
          <CodeBlock language="python">{`# Inline lambda computed facet
full_name = Computed(lambda bp: f"{bp.instance.first_name} {bp.instance.last_name}")

# Method decorator pattern
@computed
def display_title(self) -> str:
    return self.instance.title.upper()`}</CodeBlock>
        </div>
      </section>

      {/* Choice Facet */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Choice Constraint</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Restricts values to a specific set. Supports lists, dicts, or tuples:
        </p>
        <CodeBlock language="python">{`from aquilia.blueprints import ChoiceFacet

# List choices
status = ChoiceFacet(choices=["draft", "published"])

# Dict choices (value -> description)
priority = ChoiceFacet(choices={"L": "Low", "H": "High"})`}</CodeBlock>
      </section>

      {/* Complete Reference */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-6 ${t('text-white','text-gray-900')}`}>Facet Registry Reference</h2>
        <div className={`rounded-xl border overflow-hidden ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Facet</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Python Target</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['TextFacet', 'str', 'String fields with length & regex.'],
                ['IntFacet', 'int', 'Integer values.'],
                ['FloatFacet', 'float', 'Floating point values.'],
                ['DecimalFacet', 'Decimal', 'Precision decimal values serialized as string.'],
                ['BoolFacet', 'bool', 'Truthiness/falsiness checks.'],
                ['DateTimeFacet', 'datetime', 'ISO 8601 timestamps.'],
                ['Computed', 'Any', 'Eagerly evaluated derived fields.'],
                ['ChoiceFacet', 'Any', 'Enumerated values.'],
              ].map(([m, r, d]) => (
                <tr key={m}>
                  <td className="px-4 py-3 font-mono text-xs text-aquilia-400">
                    <DocTerm id={m === 'TextFacet' ? 'bp.text_facet' : m === 'IntFacet' ? 'bp.int_facet' : m === 'Computed' ? 'bp.computed_facet' : 'bp.facet'}>
                      {m}
                    </DocTerm>
                  </td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{r}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/blueprints" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/blueprints/projections" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Projections <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
