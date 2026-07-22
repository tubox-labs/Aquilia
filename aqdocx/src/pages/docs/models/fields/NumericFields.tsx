import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function NumericFields() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const t = (d: string, l: string) => isDark ? d : l

  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm mb-6">
        <Link to="/docs" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Docs</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <Link to="/docs/models/overview" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Models</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <span className={t('text-gray-300','text-gray-600')}>Numeric Fields</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Numeric Fields</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Aquilia provides a set of typed numeric fields representing integer, float, and decimal types. They are strictly typed and reject invalid coercions.
        </p>
      </div>

      {/* Types list */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>IntegerField Types</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          All integer fields map to standard SQL column sizes. Note that booleans are strictly rejected.
        </p>

        <div className={`rounded-xl border overflow-hidden ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Field</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Python Type</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>SQL (Postgres)</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Range</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['IntegerField', 'int', 'INTEGER', '-2,147,483,648 to 2,147,483,647'],
                ['BigIntegerField', 'int', 'BIGINT', '-2^63 to 2^63-1'],
                ['SmallIntegerField', 'int', 'SMALLINT', '-32,768 to 32,767'],
                ['PositiveIntegerField', 'int', 'INTEGER', '0 to 2,147,483,647'],
                ['PositiveBigIntegerField', 'int', 'BIGINT', '0 to 2^63-1'],
                ['PositiveSmallIntegerField', 'int', 'SMALLINT', '0 to 32,767'],
              ].map(([f, type, sql, range]) => (
                <tr key={f}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>{f}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{type}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{sql}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{range}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Floating Point & Decimal */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Float & Decimal Fields</h2>
        <div className="space-y-6">
          <div>
            <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>FloatField</h3>
            <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
              Maps to <code>REAL</code> or <code>DOUBLE PRECISION</code> in database.
            </p>
            <CodeBlock language="python">{`score = FloatField(null=True)`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>DecimalField</h3>
            <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
              Precision decimal fields. Requires <code>max_digits</code> and <code>decimal_places</code>. Maps to <code>DECIMAL(m, d)</code>.
            </p>
            <CodeBlock language="python">{`price = DecimalField(max_digits=10, decimal_places=2)`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>MoneyField</h3>
            <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
              A <code>DecimalField</code> subclass that adds a <code>currency</code> code. Same precision-safe
              storage as <code>DecimalField</code> (stored as <code>str()</code>, never a binary float) — the
              currency is metadata carried on the field, not encoded per-row.
            </p>
            <CodeBlock language="python">{`total = MoneyField(max_digits=12, decimal_places=2, currency="USD")

order = await Order.create(total="149.99")
order.total  # Decimal('149.99')`}</CodeBlock>
            <p className={`text-sm mt-3 ${t('text-gray-300','text-gray-600')}`}>
              <code>currency</code> only validates the 3-uppercase-letter <em>shape</em> (not a full ISO 4217
              lookup table) — a well-formed but unrecognized code is accepted on purpose:
            </p>
            <CodeBlock language="python">{`MoneyField(currency="dollars")  # raises FieldValidationError immediately`}</CodeBlock>
          </div>
        </div>
      </section>

      {/* Primary Key AutoFields */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Auto Incremented Primary Keys</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Use <code>AutoField</code> or <code>BigAutoField</code> for auto-increment keys:
        </p>
        <CodeBlock language="python">{`class User(Model):
    # BigAutoField is default if id is omitted
    id = BigAutoField(primary_key=True)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/models/fields/overview" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Fields Overview
        </Link>
        <Link to="/docs/models/fields/text" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Text Fields <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
