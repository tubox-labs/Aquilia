import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import { Link } from 'react-router-dom'
import { Database, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function ModelsOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const t = (d: string, l: string) => isDark ? d : l

  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="flex items-center gap-2 text-sm mb-6">
        <Link to="/docs" className={t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}>Docs</Link>
        <span className={t('text-gray-500','text-gray-400')}>/</span>
        <span className={t('text-gray-300','text-gray-600')}>Models</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Models (ORM)</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Pure Python, async-first ORM. Subclass <DocTerm id="orm.model">Model</DocTerm> and declare fields. A metaclass collects descriptors, assigns PKs, parses <DocTerm id="orm.meta">Meta</DocTerm>, registers globally, and attaches <DocTerm id="orm.manager">Manager</DocTerm>.
        </p>
      </div>

      {/* Architecture callout */}
      <div className={`rounded-xl p-6 mb-10 border ${t('bg-aquilia-500/5 border-aquilia-500/20','bg-blue-50/60 border-blue-200/60')}`}>
        <div className="flex items-start gap-3">
          <Database className={`w-5 h-5 mt-0.5 shrink-0 ${t('text-aquilia-400','text-blue-600')}`} />
          <div>
            <h3 className={`font-semibold mb-2 ${t('text-aquilia-300','text-blue-700')}`}>Architecture</h3>
            <p className={`text-sm leading-relaxed ${t('text-aquilia-200','text-blue-700')}`}>
              Metaclass-driven. All database access methods return an awaitable. A global <DocTerm id="orm.registry">ModelRegistry</DocTerm> maps tables and dependencies.
            </p>
          </div>
        </div>
      </div>

      {/* Quick start */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Quick Start</h2>
        <CodeBlock language="python" filename="models.py">{`from aquilia.models import Model
from aquilia.models.fields_module import CharField, EmailField, BooleanField, DateTimeField

class User(Model):
    table = "users"

    name = CharField(max_length=150)
    email = EmailField(unique=True)
    active = BooleanField(default=True)
    created_at = DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]`}</CodeBlock>
      </section>

      {/* CRUD Operations */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>CRUD Operations</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Mutations use instance methods. Queries are issued through the <DocTerm id="orm.queryset">QuerySet</DocTerm> attached to the <DocTerm id="orm.manager">objects</DocTerm> manager.
        </p>
        <CodeBlock language="python">{`# CREATE
user = User(name="Alice", email="alice@co.com")
await user.save(db)          # INSERT — calls save()

# Eager objects manager creation
user = await User.objects.create(db, name="Bob", email="bob@co.com")

# READ
users = await User.objects.filter(active=True).all()
user  = await User.objects.get(id=1)           # strict one or raise

# UPDATE
user.name = "Alice Smith"
await user.save(db, update_fields=["name"])   # UPDATE with update_fields

# DELETE
await user.delete_instance(db)   # calls delete_instance()`}</CodeBlock>
      </section>

      {/* Instance methods */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Instance Methods</h2>
        <div className={`rounded-xl border overflow-hidden ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Method</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['save(db, update_fields=None)', 'orm.model.save', 'Persist instance. Fires pre_save/post_save signals.'],
                ['delete_instance(db)', 'orm.model.delete_instance', 'DELETE instance row. Fires pre_delete/post_delete signals.'],
                ['full_clean()', 'orm.model.full_clean', 'Runs field-level validators. Raises ValidationError.'],
                ['to_dict(fields=None, exclude=None)', 'orm.model.to_dict', 'Serialize instance attributes to a dict.'],
              ].map(([m, id, d]) => (
                <tr key={m}>
                  <td className="px-4 py-3 font-mono text-xs">
                    <DocTerm id={id}>{m}</DocTerm>
                  </td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Meta class options */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Meta Options</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Configure table properties in <DocTerm id="orm.meta">Meta</DocTerm>:
        </p>
        <div className={`rounded-xl border overflow-hidden ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Option</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Type</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['ordering', 'list[str]', 'Default ORDER BY clause.'],
                ['indexes', 'list[Index]', 'Table-level indexes.'],
                ['constraints', 'list[Constraint]', 'Table constraints (UniqueConstraint, CheckConstraint).'],
                ['abstract', 'bool', 'If True, field schemas are inherited; no table created.'],
                ['db_table', 'str', 'Explicit table name override.'],
              ].map(([opt, type, d]) => (
                <tr key={opt}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>{opt}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{type}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Model Registry */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Model Registry</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Metaclass auto-registers models in <DocTerm id="orm.registry">ModelRegistry</DocTerm> for dependency mapping.
        </p>
        <CodeBlock language="python">{`from aquilia.models.registry import ModelRegistry

# Get model class
UserModel = ModelRegistry.get("User")

# Create all tables (respects FK topology order)
await ModelRegistry.create_tables(db)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-end items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/models/fields" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Fields <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}