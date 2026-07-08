import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function ModelsQuerySet() {
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
        <span className={t('text-gray-300','text-gray-600')}>QuerySet API</span>
      </div>

      {/* Header */}
      <div className="mb-10">
        <h1 className={`text-4xl font-bold tracking-tighter mb-4 ${t('text-white','text-gray-900')}`}>
          <span className="gradient-text font-mono">QuerySet API</span>
        </h1>
        <p className={`text-xl leading-relaxed ${t('text-gray-300','text-gray-600')}`}>
          Immutable, clone-on-write async query builder. Chains return new <DocTerm id="orm.queryset">QuerySet</DocTerm> clones; terminal methods (all, first, get, count) execute SQL.
        </p>
      </div>

      {/* Obtaining a QuerySet */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Obtaining a QuerySet</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Access the model <DocTerm id="orm.manager">objects</DocTerm> manager to start a chain:
        </p>
        <CodeBlock language="python">{`# Fresh QuerySet clone
qs = User.objects.filter(active=True)

# QuerySet is immutable: every chain returns a new clone
q1 = User.objects.filter(active=True)
q2 = q1.filter(age__gt=18)          # q1 is unaffected
q3 = q2.order("-created_at")        # q2 is unaffected`}</CodeBlock>
      </section>

      {/* Chain methods */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Chain Methods</h2>
        <div className={`rounded-xl border overflow-hidden mb-6 ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Method</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['filter(**kwargs)', 'orm.queryset.filter', 'AND filter conditions in WHERE.'],
                ['exclude(**kwargs)', 'orm.queryset.exclude', 'AND NOT filter conditions in WHERE.'],
                ['order(*fields)', '', 'ORDER BY. Prefix "-" for DESC.'],
                ['limit(n)', '', 'LIMIT clause.'],
                ['offset(n)', '', 'OFFSET clause.'],
                ['only(*fields)', '', 'SELECT only specified columns.'],
                ['defer(*fields)', '', 'Exclude columns from SELECT.'],
                ['select_related(*fields)', 'orm.queryset.select_related', 'JOIN related models (FK/O2O).'],
                ['prefetch_related(*lookups)', 'orm.queryset.prefetch_related', 'Separate queries for related models (M2M/FK).'],
                ['annotate(**expressions)', 'orm.queryset.annotate', 'Add computed columns to each row.'],
              ].map(([m, id, d]) => (
                <tr key={m}>
                  <td className="px-4 py-3 font-mono text-xs">
                    {id ? <DocTerm id={id}>{m}</DocTerm> : m}
                  </td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Terminal methods */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Terminal Methods (async)</h2>
        <div className={`rounded-xl border overflow-hidden mb-6 ${t('border-gray-700','border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800','bg-gray-50')}>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Method</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Returns</th>
                <th className={`px-4 py-2.5 text-left font-semibold ${t('text-gray-300','text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700','divide-gray-200')}`}>
              {[
                ['all()', 'list[Model]', 'Execute query and return model instances.'],
                ['first()', 'Model | None', 'First matching row or None.'],
                ['get(**kwargs)', 'Model', 'Exactly one row or raises ModelNotFoundFault.'],
                ['count()', 'int', 'SELECT COUNT(*) scalar.'],
                ['exists()', 'bool', 'Check if matching rows exist.'],
                ['update(**kwargs)', 'int', 'Bulk UPDATE. Returns affected rows count.'],
                ['delete()', 'int', 'Bulk DELETE. Returns affected rows count.'],
              ].map(([m, r, d]) => (
                <tr key={m}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400','text-aquilia-600')}`}>{m}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400','text-gray-500')}`}>{r}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-300','text-gray-600')}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Double underscore lookups */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Lookups</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Filter using Django-style double-underscore suffixes:
        </p>
        <CodeBlock language="python">{`# Exact & Case-insensitive exact
User.objects.filter(name__exact="Alice")
User.objects.filter(name__iexact="alice")

# Contained text
User.objects.filter(email__icontains="co.com")

# Range & IN checks
User.objects.filter(age__range=(18, 30))
User.objects.filter(id__in=[1, 2, 3])

# Null check
User.objects.filter(active__isnull=False)`}</CodeBlock>
      </section>

      {/* Complex logic with Q */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Q Node Composition</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Combine conditions using <DocTerm id="orm.q">Q</DocTerm> nodes and logical operators <code>&amp;</code> (AND), <code>|</code> (OR), and <code>~</code> (NOT):
        </p>
        <CodeBlock language="python">{`from aquilia.models import Q

# (active=True AND role="admin") OR email ends with @co.com
qs = User.objects.filter(
    (Q(active=True) & Q(role="admin")) | Q(email__endswith="@co.com")
)

# NOT suspended
qs = User.objects.filter(~Q(suspended=True))`}</CodeBlock>
      </section>

      {/* F Expressions */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>F Expressions</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Reference columns directly in SQL comparison or updates via <DocTerm id="orm.f">F</DocTerm>:
        </p>
        <CodeBlock language="python">{`from aquilia.models import F

# Compare field values
await User.objects.filter(login_count__gt=F("post_count")).all()

# Atomic database increments
await Product.objects.filter(id=42).update(stock=F("stock") - 1)`}</CodeBlock>
      </section>

      {/* Custom Managers & QuerySets */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white','text-gray-900')}`}>Custom QuerySets</h2>
        <p className={`mb-4 text-sm ${t('text-gray-300','text-gray-600')}`}>
          Extend <DocTerm id="orm.queryset">QuerySet</DocTerm> to reuse domain queries:
        </p>
        <CodeBlock language="python">{`from aquilia.models import QuerySet, Manager

class ArticleQuerySet(QuerySet):
    def published(self):
        return self.filter(status="published")

    def recent(self):
        return self.order("-published_at")

class Article(Model):
    table = "articles"
    # Attach to objects descriptor
    objects = Manager.from_queryset(ArticleQuerySet)()

# Usage
posts = await Article.objects.published().recent().all()`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700','border-gray-200')}`}>
        <Link to="/docs/models/fields" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          <ArrowLeft className="w-4 h-4" /> Fields
        </Link>
        <Link to="/docs/models/relationships" className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300','text-aquilia-600 hover:text-aquilia-500')}`}>
          Relationships <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}