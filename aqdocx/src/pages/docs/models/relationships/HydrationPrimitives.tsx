import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function HydrationPrimitives() {
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
        <span className={t('text-gray-300','text-gray-600')}>Hydration Primitives</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">Hydration Primitives</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Aquilia's database driver is 100% async. Python descriptors are synchronous, meaning transparent lazy loading of relations on attribute access is impossible. Relationships must be explicitly hydrated.
        </p>
      </div>

      {/* RelatedNotLoaded Sentinel */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>The RelatedNotLoaded Sentinel</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Accessing a relationship attribute that has not been hydrated returns a <code>RelatedNotLoaded[TModel]</code> instance. This wraps the raw foreign key value and supports no-query operations:
        </p>
        <CodeBlock language="python">{`post = await Post.objects.get(id=42)

# Checking truthiness (is FK set?) — works without query
if post.author:
    print("FK is not null")

# Reading the raw PK value — works without query
print(post.author.pk)  # e.g., 9
print(post.author.id)  # e.g., 9

# Comparing by PK — works without query
if post.author == existing_user:
    print("Same user!")

# Any other attribute access raises RelatedNotLoadedFault!
try:
    print(post.author.name)
except RelatedNotLoadedFault as e:
    print("Relation not loaded yet!")`}</CodeBlock>
      </section>

      {/* Hydration Methods */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>How to Hydrate Relations</h2>
        <div className="space-y-6">
          <div>
            <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>1. Eager JOIN (select_related)</h3>
            <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
              Hydrates single relations (ForeignKey, OneToOneField) inside a single SQL query via a <code>JOIN</code> statement:
            </p>
            <CodeBlock language="python">{`# Single SQL JOIN query
posts = await Post.objects.select_related("author").all()
for post in posts:
    print(post.author.name)  # No extra query!`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>2. Eager Batch (prefetch_related)</h3>
            <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
              Hydrates relations (including ManyToMany or reverse ForeignKey) using a separate query per relation, mapping results in Python:
            </p>
            <CodeBlock language="python">{`# Multi-query batching
posts = await Post.objects.prefetch_related("tags").all()
for post in posts:
    for tag in post.tags:
        print(tag.name)`}</CodeBlock>
          </div>

          <div>
            <h3 className={`text-lg font-semibold mb-2 ${t('text-white','text-gray-900')}`}>3. Explicit Fetch (related)</h3>
            <p className={`text-sm mb-3 ${t('text-gray-300','text-gray-600')}`}>
              Loads and caches a relation on a specific instance explicitly:
            </p>
            <CodeBlock language="python">{`# Fetch and cache relation instance-level
author = await post.related("author")
print(author.name)`}</CodeBlock>
          </div>
        </div>
      </section>

      {/* Typing */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Static Typing Contract</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Relational attributes resolve to a union type alias: <code>Related[UserModel]</code>, which translates to:
        </p>
        <CodeBlock language="python">{`Union[UserModel, RelatedNotLoaded[UserModel], None]`}</CodeBlock>
        <p className={`mt-4 mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Annotate string-referenced relation attributes to restore strict IDE autocompletion:
        </p>
        <CodeBlock language="python">{`class Post(Model):
    # Required for string references
    author: ForeignKey[User] = ForeignKey("User", on_delete="CASCADE")`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/models/relationships/defining" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Defining Relations
        </Link>
        <Link to="/docs/models/relationships/m2m" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Many-to-Many Operations <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
