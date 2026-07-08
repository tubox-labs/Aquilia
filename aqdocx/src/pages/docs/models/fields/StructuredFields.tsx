import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function StructuredFields() {
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
        <span className={t('text-gray-300','text-gray-600')}>Structured Fields</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Structured & JSON Fields</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          JSON storage, native array lists, range bounds, and key-value mapping (HStore) fields.
        </p>
      </div>

      {/* JSONField */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>JSONField</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Supported across all database backends (SQLite, PostgreSQL, MySQL). Handles serialization and deserialization of nested Python structures (lists, dicts) automatically.
        </p>
        <CodeBlock language="python">{`from aquilia.models.fields_module import JSONField

class Product(Model):
    metadata = JSONField(default_factory=dict)`}</CodeBlock>
      </section>

      {/* PostgreSQL Native Fields */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>PostgreSQL Native Fields</h2>
        <div className="space-y-6">
          <div>
            <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>ArrayField</h3>
            <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
              Declared with a child field type. Compiles to native SQL array.
            </p>
            <CodeBlock language="python">{`from aquilia.models.fields_module import ArrayField, CharField

tags = ArrayField(CharField(max_length=50), default_factory=list)`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>HStoreField</h3>
            <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
              Stores key-value pairs where both keys and values are strings.
            </p>
            <CodeBlock language="python">{`from aquilia.models.fields_module import HStoreField

attributes = HStoreField(default_factory=dict)`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>RangeField</h3>
            <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
              Represents numeric or temporal intervals. Supported variants: <code>IntegerRangeField</code>, <code>BigIntegerRangeField</code>, <code>DecimalRangeField</code>, <code>DateRangeField</code>, <code>DateTimeRangeField</code>.
            </p>
            <CodeBlock language="python">{`from aquilia.models.fields_module import IntegerRangeField

age_range = IntegerRangeField()`}</CodeBlock>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/models/fields/datetime" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Date & Time Fields
        </Link>
        <Link to="/docs/models/queryset" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          QuerySet API <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
