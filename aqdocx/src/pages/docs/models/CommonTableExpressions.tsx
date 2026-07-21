import { useTheme } from '../../../context/ThemeContext';
import { CodeBlock } from '../../../components/CodeBlock';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { NextSteps } from '../../../components/NextSteps';

export function CommonTableExpressions() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const t = (dark: string, light: string) => isDark ? dark : light;

  return (
    <div className="max-w-4xl mx-auto">
      {/* Breadcrumb */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm mb-4">
          <Link to="/docs" className={t('text-aquilia-400 hover:text-aquilia-300', 'text-aquilia-600 hover:text-aquilia-500')}>Docs</Link>
          <span className={t('text-gray-500', 'text-gray-400')}>/</span>
          <Link to="/docs/models/overview" className={t('text-aquilia-400 hover:text-aquilia-300', 'text-aquilia-600 hover:text-aquilia-500')}>Models</Link>
          <span className={t('text-gray-500', 'text-gray-400')}>/</span>
          <span className={t('text-gray-300', 'text-gray-600')}>Common Table Expressions</span>
        </div>
        <h1 className={`text-4xl ${t('text-white', 'text-gray-900')}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Common Table Expressions
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-xl mt-2 ${t('text-gray-300', 'text-gray-600')}`}>
          Named subqueries defined at the start of a statement — compose readable, reusable query fragments.
        </p>
        <div className={`mt-3 inline-flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-full border ${t('border-aquilia-500/30 bg-aquilia-500/10 text-aquilia-400', 'border-aquilia-500/40 bg-aquilia-50 text-aquilia-600')}`}>
          v1.3.3+
        </div>
      </div>

      {/* Concept */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Concept</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          A <strong>Common Table Expression (CTE)</strong> is a named, temporary result set defined with a <code>WITH name AS (SELECT ...)</code>
          clause that precedes the main query. The main query can then reference the CTE by name as if it were a table.
        </p>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          CTEs excel at:
        </p>
        <ul className={`list-disc ml-6 mb-4 space-y-1 ${t('text-gray-300', 'text-gray-600')}`}>
          <li><strong>Breaking complex queries into readable steps</strong> — each CTE is a named, focused subquery</li>
          <li><strong>Reusing subquery results</strong> — reference the same CTE multiple times in the main query</li>
          <li><strong>Post-processing window function results</strong> — filter on a windowed annotation (impossible in a single SELECT)</li>
          <li><strong>Analytics pipelines</strong> — chain filtering, ranking, and aggregation as separate named stages</li>
        </ul>
        <div className={`rounded-lg border p-4 text-sm ${t('border-blue-500/20 bg-blue-500/5 text-blue-300', 'border-blue-300 bg-blue-50 text-blue-800')}`}>
          <strong>Performance note:</strong> Most databases materialise CTEs once (PostgreSQL &lt; 12 always; PostgreSQL 12+ optimises unless <code>MATERIALIZED</code> is specified).
          On SQLite and MySQL 8.0+, the optimiser may inline CTEs. Measure with <code>.explain()</code> if performance matters.
        </div>
      </section>

      {/* Imports */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Imports</h2>
        <CodeBlock language="python">
{`from aquilia.models import CTE, CTEReference, CTECol
# CTE objects are also created via the QuerySet .cte() method — no direct instantiation needed`}
        </CodeBlock>
      </section>

      {/* Basic CTE */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Basic Non-Recursive CTE</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Call <code>.cte(name)</code> on any QuerySet to create a named CTE, then pass it to <code>.with_cte()</code> on the
          outer query. The outer query can then reference the CTE name as a table.
        </p>
        <CodeBlock language="python">
{`from aquilia.models import F

# Step 1: Define the CTE queryset
active_users_qs = User.objects.filter(is_active=True, verified=True)

# Step 2: Name it as a CTE
active_users = active_users_qs.cte('active_users')

# Step 3: Use it in an outer query
# Note: the outer query selects FROM the CTE name as a table
result = await (
    User.objects
    .with_cte(active_users)
    .filter(role='admin')
    .order('-created_at')
    .all()
)

# Generates:
# WITH "active_users" AS (
#     SELECT * FROM "users" WHERE "is_active" = ? AND "verified" = ?
# )
# SELECT * FROM "users" WHERE "role" = ? ORDER BY "created_at" DESC`}
        </CodeBlock>
      </section>

      {/* Multiple CTEs */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Multiple CTEs</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Pass multiple CTEs to <code>.with_cte()</code> in a single call, or chain calls additively.
          CTEs are rendered in registration order.
        </p>
        <CodeBlock language="python">
{`# Analytics pipeline: filter → annotate → join via CTEs

# CTE 1: active users with post count
active_qs = User.objects.filter(is_active=True)
active = active_qs.cte('active_users')

# CTE 2: top posts (last 30 days)
from datetime import datetime, timedelta
cutoff = datetime.utcnow() - timedelta(days=30)
top_posts_qs = Post.objects.filter(created_at__gte=cutoff).order('-likes')
top_posts = top_posts_qs.cte('recent_top_posts')

# Main query referencing both
result = await (
    User.objects
    .with_cte(active, top_posts)   # both CTEs in one call
    .filter(is_active=True)
    .all()
)

# Generates:
# WITH "active_users" AS (...),
#      "recent_top_posts" AS (...)
# SELECT ...`}
        </CodeBlock>
      </section>

      {/* CTECol */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Referencing CTE Columns</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Use <code>cte.col("column_name")</code> to get a <code>CTECol</code> expression that renders as
          <code>"cte_name"."column"</code>. Use this in filter expressions or annotations that reference the CTE.
        </p>
        <CodeBlock language="python">
{`from aquilia.models import CTE, F

ranked_qs = Post.objects.annotate(
    rn=Window(RowNumber(), partition_by=['author_id'], order_by='-likes')
)
ranked = ranked_qs.cte('ranked_posts')

# Reference CTE column in outer query filter
top3_col = ranked.col('rn')    # → CTECol("ranked_posts", "rn")

# Use in annotation or raw filter
result = await (
    Post.objects
    .with_cte(ranked)
    .filter(**{'rn__lte': 3})   # Filter on annotated window rank from CTE
    .all()
)`}
        </CodeBlock>
      </section>

      {/* Rank + Filter Pattern */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Production Pattern: Rank + Filter</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          The most common CTE pattern is computing a window function annotation in a CTE and then filtering on it
          in the outer query — bypassing the SQL restriction that window functions cannot appear in WHERE.
        </p>
        <CodeBlock language="python">
{`from aquilia.models import Window, RowNumber, F

# TOP-3 POSTS PER AUTHOR — using CTE to filter on window annotation

# Inner queryset: annotate with row number within each author's partition
ranked_qs = Post.objects.annotate(
    rn=Window(
        RowNumber(),
        partition_by=['author_id'],
        order_by='-likes',
    )
)
ranked = ranked_qs.cte('ranked_posts')

# Outer query: select from the CTE, filter on rn
top3 = await (
    Post.objects
    .with_cte(ranked)
    .filter(rn__lte=3)          # Now valid — rn is a column in the CTE
    .order('author_id', 'rn')
    .all()
)
# → Up to 3 most-liked posts per author`}
        </CodeBlock>
      </section>

      {/* Parameter ordering */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Parameter Ordering</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Aquilia guarantees correct parameter ordering: CTE bind values are prepended before the main query's
          annotation params and WHERE params. You should not need to manage this manually.
        </p>
        <CodeBlock language="python">
{`# The generated parameterized query:
# WITH "active_users" AS (SELECT ... WHERE "is_active" = ?)   ← CTE param: True
# SELECT * FROM "users" WHERE "role" = ?                       ← WHERE param: 'admin'
# Final params: [True, 'admin']   (CTE params first, always)`}
        </CodeBlock>
      </section>

      {/* Backend Compat */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Backend Compatibility</h2>
        <div className={`rounded-lg border overflow-hidden ${t('border-gray-700', 'border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800', 'bg-gray-50')}>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Backend</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Min Version</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Notes</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700', 'divide-gray-200')}`}>
              {[
                ['SQLite', '3.8.3+', 'Non-recursive CTEs. Recursive requires 3.8.3+.'],
                ['PostgreSQL', '8.4+', 'Full CTE and recursive CTE support.'],
                ['MySQL', '8.0+', 'CTEs supported. Earlier versions have no CTE support.'],
              ].map(([b, v, n]) => (
                <tr key={b as string}>
                  <td className={`px-4 py-3 font-semibold ${t('text-gray-200', 'text-gray-800')}`}>{b}</td>
                  <td className={`px-4 py-3 font-mono ${t('text-gray-400', 'text-gray-500')}`}>{v}</td>
                  <td className={`px-4 py-3 ${t('text-gray-300', 'text-gray-700')}`}>{n}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700', 'border-gray-200')}`}>
        <Link
          to="/docs/models/window-functions"
          className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300', 'text-aquilia-600 hover:text-aquilia-500')}`}
        >
          <ArrowLeft className="w-4 h-4" /> Window Functions
        </Link>
        <Link
          to="/docs/models/recursive-cte"
          className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300', 'text-aquilia-600 hover:text-aquilia-500')}`}
        >
          Recursive CTEs <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  );
}
