import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function DefiningRelationships() {
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
        <span className={t('text-gray-300','text-gray-600')}>Defining Relationships</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Defining Relationships</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Aquilia ORM supports first-class relational fields including Many-to-One, One-to-One, and Many-to-Many configurations.
        </p>
      </div>

      {/* ForeignKey */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>ForeignKey (Many-to-One)</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Declares a many-to-one relationship. Requires the target model (either class reference or forward reference string) and <code>on_delete</code> behavior:
        </p>
        <CodeBlock language="python">{`from aquilia.models.fields_module import ForeignKey

class Post(Model):
    # Class reference
    author = ForeignKey(User, on_delete="CASCADE", related_name="posts")
    
    # Or string reference (prevents circular imports)
    category = ForeignKey("Category", on_delete="SET_NULL", null=True)`}</CodeBlock>

        <h3 className={`text-lg font-semibold mt-6 mb-3 ${t('text-white','text-gray-900')}`}>On-Delete Actions</h3>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Supported database-level delete cascades:
        </p>
        <ul className={`list-disc list-inside space-y-2 text-sm ${t('text-gray-300','text-gray-600')}`}>
          <li><code>"CASCADE"</code>: Cascades the deletion of the referenced row to this row.</li>
          <li><code>"SET_NULL"</code>: Sets the foreign key column to NULL (requires <code>null=True</code>).</li>
          <li><code>"RESTRICT"</code>: Rejects parent deletion if dependent children rows exist.</li>
          <li><code>"SET_DEFAULT"</code>: Sets the column to its configured default value.</li>
          <li><code>"DO_NOTHING"</code>: No database-level action is taken (raw foreign key remains unchanged).</li>
        </ul>
      </section>

      {/* OneToOneField */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>OneToOneField</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Similar to <code>ForeignKey</code>, but enforces a UNIQUE constraint on the foreign key column, establishing a strict 1-to-1 link:
        </p>
        <CodeBlock language="python">{`from aquilia.models.fields_module import OneToOneField

class Profile(Model):
    user = OneToOneField(User, on_delete="CASCADE", related_name="profile")`}</CodeBlock>
      </section>

      {/* ManyToManyField */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>ManyToManyField</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Configures a many-to-many relationship. Automatically generates an intermediary junction table:
        </p>
        <CodeBlock language="python">{`from aquilia.models.fields_module import ManyToManyField

class Article(Model):
    tags = ManyToManyField("Tag", related_name="articles")`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/models/queryset" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> QuerySet API
        </Link>
        <Link to="/docs/models/relationships/hydration" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Hydration Primitives <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
