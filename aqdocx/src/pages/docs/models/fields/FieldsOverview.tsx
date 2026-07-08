import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function FieldsOverview() {
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
        <span className={t('text-gray-300','text-gray-600')}>Fields Overview</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Fields: Overview & Core</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          All fields in Aquilia ORM inherit from the base <code>Field[T]</code> class, implementing the Python descriptor protocol. Descriptors ensure type safety, validation, and serialization.
        </p>
      </div>

      {/* Core properties */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Core Field Parameters</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Common options accepted by all field types:
        </p>
        <div className={`rounded-xl border overflow-hidden ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Parameter</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Type</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Default</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['null', 'bool', 'False', 'If True, stores NULL in database for empty values.'],
                ['blank', 'bool', 'False', 'Allows validation to pass on empty strings.'],
                ['default', 'Any', 'UNSET', 'Static value or callable (e.g. uuid.uuid4).'],
                ['unique', 'bool', 'False', 'Enforces unique column constraints.'],
                ['primary_key', 'bool', 'False', 'Marks column as the primary key.'],
                ['db_index', 'bool', 'False', 'Creates a database index on the column.'],
                ['db_column', 'str | None', 'None', 'Override database column name.'],
                ['choices', 'list | None', 'None', 'List of (value, label) tuples.'],
                ['validators', 'list', '[]', 'Callables running custom validation.'],
                ['editable', 'bool', 'True', 'Controls if field is writable in admin panel.'],
              ].map(([p, type, defVal, desc]) => (
                <tr key={p}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>{p}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{type}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{defVal}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Descriptor contract */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Descriptor Contract</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Accessing fields is fully synchronous. Cleaned values are automatically coerced:
        </p>
        <CodeBlock language="python">{`class User(Model):
    name = CharField(max_length=150)

# Class-level access yields the Field instance
reveal_type(User.name)  # -> CharField

# Instance-level access yields the underlying coerced Python type
user = User(name="Alice")
reveal_type(user.name)  # -> str`}</CodeBlock>
      </section>

      {/* Custom fields */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Creating Custom Fields</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          To define a custom field, inherit from <code>Field[T]</code> and implement <code>sql_type()</code>:
        </p>
        <CodeBlock language="python">{`from aquilia.models import Field
from aquilia.models.fields_module import FieldValidationError

class HexColorField(Field[str]):
    _field_type = "COLOR"
    _python_type = str

    def sql_type(self, dialect: str = "sqlite") -> str:
        return "VARCHAR(7)"

    def validate(self, value: Any) -> str:
        value = super().validate(value)
        if value is not None:
            if not isinstance(value, str) or not value.startswith("#") or len(value) != 7:
                raise FieldValidationError(self.name, "Must be a valid hex color string (e.g. #FF00FF)")
        return value`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/models" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/models/fields/numeric" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Numeric Fields <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
