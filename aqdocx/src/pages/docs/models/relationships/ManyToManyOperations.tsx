import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function ManyToManyOperations() {
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
        <span className={t('text-gray-300','text-gray-600')}>ManyToMany Operations</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">ManyToMany Operations</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Working with junction tables, attaching and detaching relations, and defining custom through models.
        </p>
      </div>

      {/* attaching & detaching */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Attaching and Detaching</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Manage relations on a saved model instance using the <code>attach()</code> and <code>detach()</code> methods:
        </p>
        <CodeBlock language="python">{`# Add a tag (ID 3) to an article instance
await article.attach(db, "tags", [3])

# Remove tag (ID 3) from the article
await article.detach(db, "tags", [3])

# Clear all tags
await article.detach(db, "tags")`}</CodeBlock>
      </section>

      {/* custom through models */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Custom through Models</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          When you need additional metadata columns on the junction table, declare a custom model class and pass it to the <code>through</code> argument:
        </p>
        <CodeBlock language="python">{`class User(Model):
    table = "users"
    groups = ManyToManyField("Group", through="Membership")

class Group(Model):
    table = "groups"

class Membership(Model):
    table = "memberships"
    user = ForeignKey(User, on_delete="CASCADE")
    group = ForeignKey(Group, on_delete="CASCADE")
    role = CharField(max_length=50)
    joined_at = DateTimeField(auto_now_add=True)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/models/relationships/hydration" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Hydration Primitives
        </Link>
        <Link to="/docs/models/transactions" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Transactions <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
