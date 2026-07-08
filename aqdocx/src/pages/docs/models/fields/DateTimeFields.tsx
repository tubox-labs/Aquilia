import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function DateTimeFields() {
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
        <span className={t('text-gray-300','text-gray-600')}>Date & Time Fields</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Date & Time Fields</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Fields for date, time, timezone-aware datetime instances, and timedeltas.
        </p>
      </div>

      {/* Fields list */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Field Catalogue</h2>
        <div className={`rounded-xl border overflow-hidden ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Field</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Python Type</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>SQL (SQLite / Postgres)</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['DateField', 'datetime.date', 'DATE'],
                ['TimeField', 'datetime.time', 'TIME'],
                ['DateTimeField', 'datetime.datetime', 'TIMESTAMP / TIMESTAMP WITH TIME ZONE'],
                ['DurationField', 'datetime.timedelta', 'BIGINT / INTERVAL'],
              ].map(([f, type, sql]) => (
                <tr key={f}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>{f}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{type}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{sql}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Auto Now Options */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Auto Timestamp Options</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Both <code>DateField</code> and <code>DateTimeField</code> support automatic timestamps:
        </p>
        <CodeBlock language="python">{`created_at = DateTimeField(auto_now_add=True)  # Set once on creation
updated_at = DateTimeField(auto_now=True)      # Set on every save()`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/models/fields/text" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Text Fields
        </Link>
        <Link to="/docs/models/fields/structured" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Structured Fields <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
