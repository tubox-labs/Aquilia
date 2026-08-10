import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Search, AlertTriangle } from 'lucide-react'

const methods: [string, string][] = [
  ['filter(*nodes, **lookups)', 'Adds AND-ed conditions. Accepts VF expressions or Django-style keyword lookups.'],
  ['where(...)', 'Alias of filter(), for readers who prefer the SQL word.'],
  ['exclude(...)', 'Adds negated conditions.'],
  ['limit(n) / top(n)', 'Caps result count. top() is the search-side name for the same bound.'],
  ['offset(n)', 'Skips n records. Valid for scans; rejected on a similarity search.'],
  ['min_score(s)', 'Drops hits scoring below s.'],
  ['with_vectors()', 'Includes raw vectors in the result instead of omitting them.'],
  ['ef_search(v)', 'Per-query HNSW recall/latency knob.'],
  ['gpu(enabled=True)', 'Per-query override of the store GPU policy.'],
  ['prompt(template)', 'Wraps the query text in a template before embedding.'],
]

const terminals: [string, string][] = [
  ['await search(text=..., vector=...)', 'Runs similarity search, returning Hit objects ordered by score.'],
  ['await all() / records() / rows()', 'Metadata scan honouring the filters. No similarity involved.'],
  ['await first() / one()', 'Single result; one() faults when the match is not unique.'],
  ['await count()', 'Unfiltered count is a native counter; a filtered count scans.'],
  ['await exists()', 'Cheap existence probe.'],
  ['await delete()', 'Deletes matching records. Refused when the query has no filters.'],
  ['await explain(vector=...)', 'Returns the compiled plan: pushed-down predicate, residuals, index use.'],
]

export function VectorDBQueries() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  const table = (title: string, rows: [string, string][]) => (
    <div className="mb-8">
      <h3 className={`text-sm font-bold mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>{title}</h3>
      <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
        <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <tbody className="divide-y divide-white/5">
            {rows.map(([name, desc], i) => (
              <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                <td className="py-3.5 px-6 font-mono text-xs text-aquilia-400 w-72 align-top">{name}</td>
                <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{desc}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Search className="w-4 h-4 animate-pulse" />
          Vector Database / Queries
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Querying Vectors
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          <code className="text-aquilia-500">VectorQuery</code> is lazy and cloning: each builder
          method returns a new query, so a base query can be shared and specialised without one
          caller corrupting another. Nothing touches the store until you await a terminal.
        </p>
      </div>

      {/* Basic */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Basic search
        </h2>
        <CodeBlock language="python" highlightLines={[2, 8, 9, 10, 11]}>{`# Text search — embedded by the store
hits = await Article.vectors.search("how do migrations work", limit=5)

# Explicit vector, no embedder needed
hits = await Article.vectors.search(vector=my_embedding, limit=5)

# Filters and a score floor, composed
hits = await (
    Article.vectors.query()
    .filter(kind="doc")
    .min_score(0.75)
    .top(10)
    .search("how do migrations work")
)

for hit in hits:
    print(hit.score, hit.key, hit.title)`}</CodeBlock>
        <p className={`mt-4 text-sm ${subtleText}`}>
          A <code className="text-aquilia-500">Hit</code> proxies attribute access to the underlying
          record, so <code className="text-aquilia-500">hit.title</code> works while{' '}
          <code className="text-aquilia-500">hit.score</code>,{' '}
          <code className="text-aquilia-500">hit.distance</code>,{' '}
          <code className="text-aquilia-500">hit.approximate</code> and{' '}
          <code className="text-aquilia-500">hit.codec</code> stay query-level facts.{' '}
          <code className="text-aquilia-500">score</code> is normalised so higher always means more
          similar; <code className="text-aquilia-500">distance</code> is the raw value the index
          reported, where lower is closer.
        </p>
      </section>

      {/* Filters */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Filter expressions
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Two equivalent styles. Keyword lookups read shortest; <code className="text-aquilia-500">VF</code>{' '}
          expressions compose with <code className="text-aquilia-500">&amp;</code>,{' '}
          <code className="text-aquilia-500">|</code> and <code className="text-aquilia-500">~</code>{' '}
          when the logic needs OR.
        </p>
        <CodeBlock language="python" highlightLines={[4, 9, 10]}>{`from aquilia.vectordb import VF

# Keyword lookups: field__op=value, AND-ed together
q = Article.vectors.query().filter(kind="doc", views__gte=100, title__icontains="migration")

# VF nodes take the same lookups, and compose with & | ~
q = Article.vectors.query().filter(
    (VF(kind="doc") | VF(kind="faq")) & VF(views__gte=10),
    ~VF(archived=True),
)

# Inspect what will be pushed down versus resolved in Python
print(await q.explain())`}</CodeBlock>
        <p className={`mt-4 text-sm ${subtleText}`}>
          Supported suffixes are <code className="text-aquilia-500">exact</code>/
          <code className="text-aquilia-500">eq</code>, <code className="text-aquilia-500">ne</code>,{' '}
          <code className="text-aquilia-500">gt</code>,{' '}
          <code className="text-aquilia-500">gte</code>/<code className="text-aquilia-500">ge</code>,{' '}
          <code className="text-aquilia-500">lt</code>,{' '}
          <code className="text-aquilia-500">lte</code>/<code className="text-aquilia-500">le</code>,{' '}
          <code className="text-aquilia-500">in</code>,{' '}
          <code className="text-aquilia-500">contains</code>,{' '}
          <code className="text-aquilia-500">icontains</code>,{' '}
          <code className="text-aquilia-500">startswith</code>,{' '}
          <code className="text-aquilia-500">endswith</code> and{' '}
          <code className="text-aquilia-500">range</code>. Anything else is treated as a typo rather
          than a payload key, so a misspelled lookup fails loudly. What the native layer cannot
          express becomes a residual predicate applied in Python after the scan —{' '}
          <code className="text-aquilia-500">explain()</code> tells you which.
        </p>
        <div className={`mt-6 rounded-xl border p-5 ${isDark ? 'border-white/10 bg-white/5' : 'border-gray-200 bg-gray-50'}`}>
          <h3 className={`text-sm font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Two lookups that raise on purpose</h3>
          <p className={`text-sm mb-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <code className="text-aquilia-500">__isnull</code> raises{' '}
            <code className="text-aquilia-500">VectorLookupFault</code>. elips metadata has no null
            concept — an absent key does not match any predicate, so the lookup has no honest
            answer. Model absence explicitly with a sentinel value or a{' '}
            <code className="text-aquilia-500">has_x</code> boolean and filter on that.
          </p>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Range lookups on a field whose codec is not order-preserving raise too. A{' '}
            <code className="text-aquilia-500">Decimal</code> or{' '}
            <code className="text-aquilia-500">UUID</code> encodes to a string where ordering is
            lexicographic (<code className="text-aquilia-500">&apos;9&apos; &gt; &apos;10&apos;</code>), so a range would
            return the wrong records. Use <code className="text-aquilia-500">exact</code> or{' '}
            <code className="text-aquilia-500">__in</code>.
          </p>
        </div>
      </section>

      {/* API tables */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Method reference
        </h2>
        {table('Builders (return a new query)', methods)}
        {table('Terminals (hit the store)', terminals)}
      </section>

      {/* Pitfalls */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <AlertTriangle className="w-5 h-5 text-amber-500" />
          Edge cases
        </h2>
        <div className="space-y-4">
          {[
            [
              'offset() plus search() is rejected',
              'An approximate index has no stable global ordering to skip into, so a paged similarity search would silently drop or repeat results. Raise the top() bound and slice, or page a metadata scan instead.',
            ],
            [
              'Scores are estimates on a compressed store',
              'After aq vectordb compress, distances are computed from quantized vectors. hit.approximate marks those results; do not hard-threshold on score without accounting for the error.',
            ],
            [
              'An unfiltered delete() faults',
              'VectorQueryFault rather than emptying the collection. Add a filter that names what you meant to remove.',
            ],
            [
              'one() faults on a non-unique match',
              'Same contract as the SQL ORM. Use first() when more than one match is acceptable.',
            ],
          ].map(([title, body], i) => (
            <div key={i} className={`rounded-xl border p-5 ${isDark ? 'border-white/10 bg-white/5' : 'border-gray-200 bg-gray-50'}`}>
              <h3 className={`text-sm font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>{title}</h3>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{body}</p>
            </div>
          ))}
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
