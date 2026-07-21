import { useTheme } from '../../../context/ThemeContext';
import { CodeBlock } from '../../../components/CodeBlock';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { NextSteps } from '../../../components/NextSteps';

export function WindowFunctions() {
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
          <span className={t('text-gray-300', 'text-gray-600')}>Window Functions</span>
        </div>
        <h1 className={`text-4xl ${t('text-white', 'text-gray-900')}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Window Functions
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-xl mt-2 ${t('text-gray-300', 'text-gray-600')}`}>
          Compute values across related rows without collapsing them — rankings, running totals, moving averages, and more.
        </p>
        <div className={`mt-3 inline-flex items-center gap-2 text-xs font-mono px-3 py-1.5 rounded-full border ${t('border-aquilia-500/30 bg-aquilia-500/10 text-aquilia-400', 'border-aquilia-500/40 bg-aquilia-50 text-aquilia-600')}`}>
          v1.3.3+
        </div>
      </div>

      {/* Concept */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Concept</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          A <strong>window function</strong> operates on a set of rows related to the current row — defined by an OVER clause —
          and returns a value for each row individually. Unlike aggregate functions used with <code>GROUP BY</code>, window functions
          do not collapse rows. Every input row receives its own output row, with the window function result added as an annotation.
        </p>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          The canonical use cases are:
        </p>
        <ul className={`list-disc ml-6 mb-4 space-y-1 ${t('text-gray-300', 'text-gray-600')}`}>
          <li><strong>Ranking</strong> — RANK(), DENSE_RANK(), ROW_NUMBER() per partition</li>
          <li><strong>Running totals</strong> — SUM() OVER ordered window</li>
          <li><strong>Moving averages</strong> — AVG() OVER frame clause</li>
          <li><strong>Lead/lag comparisons</strong> — LAG() and LEAD() for period-over-period</li>
          <li><strong>Top-N per group</strong> — rank within partition, then filter in Python or subquery</li>
        </ul>
        <div className={`rounded-lg border p-4 text-sm ${t('border-amber-500/20 bg-amber-500/5 text-amber-300', 'border-amber-300 bg-amber-50 text-amber-800')}`}>
          <strong>Key difference from GROUP BY:</strong> <code>GROUP BY</code> collapses many rows into one aggregate row.
          Window functions keep all rows and add a computed column. Use GROUP BY when you want one row per group; use window functions when you want all rows with per-row context.
        </div>
      </section>

      {/* Import */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Imports</h2>
        <CodeBlock language="python">
{`# Top-level import — everything exported from aquilia.models
from aquilia.models import (
    Window,
    Rank, DenseRank, RowNumber, Ntile,
    Lag, Lead, FirstValue, LastValue, NthValue,
    FrameType, FrameBound, WindowFrame,
    Sum, Avg, Count,   # aggregates work as window functions too
    F, OrderBy,
)

# Or import from the window module directly
from aquilia.models.window import Window, Rank, FrameBound, WindowFrame`}
        </CodeBlock>
      </section>

      {/* Window() API */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>The <code>Window()</code> Wrapper</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          <code>Window</code> wraps any window function or aggregate expression with an OVER clause. It is used inside
          <code>.annotate()</code> just like any other expression.
        </p>
        <div className={`rounded-lg border overflow-hidden mb-4 ${t('border-gray-700', 'border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800', 'bg-gray-50')}>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Parameter</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Type</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700', 'divide-gray-200')}`}>
              {[
                ['expression', 'Expression', 'Window function or aggregate (Rank(), Sum("amount"), ...)'],
                ['partition_by', 'str | list[str | F] | None', 'PARTITION BY columns. Strings converted to F() automatically.'],
                ['order_by', 'str | list[str] | OrderBy | list[OrderBy] | None', 'ORDER BY inside the window. Prefix "-" for DESC.'],
                ['frame', 'WindowFrame | None', 'Optional ROWS/RANGE/GROUPS frame clause.'],
              ].map(([p, type, desc]) => (
                <tr key={p}>
                  <td className={`px-4 py-3 font-mono ${t('text-aquilia-400', 'text-blue-600')}`}>{p}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400', 'text-gray-500')}`}>{type}</td>
                  <td className={`px-4 py-3 ${t('text-gray-300', 'text-gray-700')}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <CodeBlock language="python">
{`# Window generates: RANK() OVER (PARTITION BY "country" ORDER BY "score" DESC)
result = await User.objects.annotate(
    rank=Window(Rank(), partition_by=['country'], order_by='-score')
).all()

# Access annotation on each row:
for user in result:
    print(user.rank, user.name)  # 1 Alice, 2 Bob, ...`}
        </CodeBlock>
      </section>

      {/* Ranking Functions */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Ranking Functions</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Ranking functions assign a position to each row within its partition. They require an ORDER BY clause in the window
          to be meaningful; without it, all rows receive the same rank.
        </p>
        <div className={`rounded-lg border overflow-hidden mb-6 ${t('border-gray-700', 'border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800', 'bg-gray-50')}>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Class</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>SQL</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Tie Handling</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700', 'divide-gray-200')}`}>
              {[
                ['Rank()', 'RANK()', 'Tied rows get same rank; next rank skips (1, 1, 3)'],
                ['DenseRank()', 'DENSE_RANK()', 'Tied rows get same rank; no skips (1, 1, 2)'],
                ['RowNumber()', 'ROW_NUMBER()', 'Unique sequential number per row regardless of ties'],
                ['Ntile(n)', 'NTILE(n)', 'Distributes rows into n ranked buckets (1..n)'],
              ].map(([cls, sql, note]) => (
                <tr key={cls as string}>
                  <td className={`px-4 py-3 font-mono ${t('text-aquilia-400', 'text-blue-600')}`}>{cls}</td>
                  <td className={`px-4 py-3 font-mono ${t('text-gray-400', 'text-gray-500')}`}>{sql}</td>
                  <td className={`px-4 py-3 ${t('text-gray-300', 'text-gray-700')}`}>{note}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <CodeBlock language="python">
{`from aquilia.models import Rank, DenseRank, RowNumber, Ntile, Window

# Leaderboard: rank players per game, ordered by score DESC
leaderboard = await PlayerScore.objects.annotate(
    rank=Window(Rank(), partition_by=['game_id'], order_by='-score'),
    dense_rank=Window(DenseRank(), partition_by=['game_id'], order_by='-score'),
    row_num=Window(RowNumber(), partition_by=['game_id'], order_by='-score'),
).order('game_id', 'rank').all()

# Percentile buckets: split each department into 4 salary quartiles
quartiles = await Employee.objects.annotate(
    quartile=Window(Ntile(4), partition_by=['department_id'], order_by='salary')
).all()
# quartile=1 → lowest 25%, quartile=4 → top 25%`}
        </CodeBlock>
      </section>

      {/* Value Functions */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Value Functions: Lag, Lead, First/Last/Nth</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Value functions look at other rows in the window relative to the current row or access boundary values.
        </p>
        <div className={`rounded-lg border overflow-hidden mb-6 ${t('border-gray-700', 'border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800', 'bg-gray-50')}>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Class</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>SQL</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700', 'divide-gray-200')}`}>
              {[
                ['Lag(expr, offset=1, default=None)', 'LAG(expr, n, default)', 'Value from n rows before current row'],
                ['Lead(expr, offset=1, default=None)', 'LEAD(expr, n, default)', 'Value from n rows after current row'],
                ['FirstValue(expr)', 'FIRST_VALUE(expr)', 'First value in the window frame'],
                ['LastValue(expr)', 'LAST_VALUE(expr)', 'Last value in the window frame'],
                ['NthValue(expr, n)', 'NTH_VALUE(expr, n)', 'Value at position n within the frame (PG 11+, MySQL 8.0.2+, SQLite 3.25+)'],
              ].map(([cls, sql, desc]) => (
                <tr key={cls as string}>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-aquilia-400', 'text-blue-600')}`}>{cls}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400', 'text-gray-500')}`}>{sql}</td>
                  <td className={`px-4 py-3 ${t('text-gray-300', 'text-gray-700')}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <CodeBlock language="python">
{`from aquilia.models import Lag, Lead, FirstValue, LastValue, NthValue, Window, F

# Month-over-month revenue change
monthly = await MonthlySales.objects.annotate(
    prev_month_revenue=Window(
        Lag(F('revenue'), offset=1, default=0),
        partition_by=['product_id'],
        order_by='month',
    )
).all()

# pct_change computed in Python after fetching:
for row in monthly:
    if row.prev_month_revenue:
        row.pct_change = (row.revenue - row.prev_month_revenue) / row.prev_month_revenue

# Rolling 3-day lookahead
orders = await DailyOrder.objects.annotate(
    next_3_days=Window(
        Lead(F('order_count'), offset=3, default=0),
        partition_by=['region'],
        order_by='date',
    )
).all()

# Cheapest item in department (frame: all rows in partition)
products = await Product.objects.annotate(
    cheapest_in_dept=Window(
        FirstValue(F('price')),
        partition_by=['department_id'],
        order_by='price',
    )
).all()`}
        </CodeBlock>
      </section>

      {/* Aggregates as Window Functions */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Aggregates as Window Functions</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Any aggregate expression (Sum, Avg, Count, Max, Min) can be placed inside <code>Window()</code>.
          The aggregate then computes over the rows in the window frame instead of the whole group.
        </p>
        <CodeBlock language="python">
{`from aquilia.models import Sum, Avg, Count, Window, F

# Running total of sales per region, ordered by date
sales = await Sale.objects.annotate(
    running_total=Window(
        Sum(F('amount')),
        partition_by=['region'],
        order_by='sale_date',
    )
).order('region', 'sale_date').all()

# 7-day moving average of page views
from aquilia.models import WindowFrame, FrameType, FrameBound

seven_day_avg = await PageView.objects.annotate(
    moving_avg=Window(
        Avg(F('views')),
        partition_by=['page_id'],
        order_by='date',
        frame=WindowFrame(
            FrameType.ROWS,
            start=FrameBound.preceding(6),
            end=FrameBound.current_row(),
        )
    )
).all()

# Cumulative count of orders per customer up to current order
orders = await Order.objects.annotate(
    cumulative_orders=Window(
        Count(F('id')),
        partition_by=['customer_id'],
        order_by='created_at',
    )
).all()`}
        </CodeBlock>
      </section>

      {/* PARTITION BY & ORDER BY */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>PARTITION BY & ORDER BY</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          <code>partition_by</code> divides rows into independent groups; the window function resets at each group boundary.
          <code>order_by</code> within the window controls how rows are sequenced inside each partition.
        </p>
        <CodeBlock language="python">
{`from aquilia.models import Window, Rank, F, OrderBy

# Single partition column (string shorthand)
Window(Rank(), partition_by='department_id', order_by='-salary')

# Multiple partition columns
Window(Rank(), partition_by=['country', 'city'], order_by='-score')

# F() objects instead of strings
Window(Rank(), partition_by=[F('country'), F('city')], order_by='-score')

# Mixed ascending/descending with explicit OrderBy
Window(
    Rank(),
    partition_by=['department_id'],
    order_by=[OrderBy(F('salary'), descending=True), 'name'],
)

# No partition — window spans entire result set
Window(Rank(), order_by='-score')  # Global rank across all rows`}
        </CodeBlock>
      </section>

      {/* Frame Clauses */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Frame Clauses</h2>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          Frame clauses restrict which rows within the ordered window participate in the aggregate. They only apply
          to aggregate-style window functions (Sum, Avg, etc.) — pure ranking functions ignore frames.
        </p>
        <div className={`rounded-lg border overflow-hidden mb-4 ${t('border-gray-700', 'border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800', 'bg-gray-50')}>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>FrameType</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Meaning</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Support</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700', 'divide-gray-200')}`}>
              {[
                ['FrameType.ROWS', 'Physical row offset from current row', 'All backends'],
                ['FrameType.RANGE', 'Logical value range relative to current row value', 'All backends'],
                ['FrameType.GROUPS', 'Peer group offset', 'PostgreSQL 11+, SQLite 3.28+'],
              ].map(([ft, m, s]) => (
                <tr key={ft as string}>
                  <td className={`px-4 py-3 font-mono ${t('text-aquilia-400', 'text-blue-600')}`}>{ft}</td>
                  <td className={`px-4 py-3 ${t('text-gray-300', 'text-gray-700')}`}>{m}</td>
                  <td className={`px-4 py-3 text-xs ${t('text-gray-400', 'text-gray-500')}`}>{s}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <CodeBlock language="python">
{`from aquilia.models import WindowFrame, FrameType, FrameBound, Window, Avg, F

# Unbounded running total (from first row to current row)
WindowFrame(
    FrameType.ROWS,
    start=FrameBound.unbounded_preceding(),
    end=FrameBound.current_row(),
)

# 7-row sliding window (3 before, current, 3 after)
WindowFrame(
    FrameType.ROWS,
    start=FrameBound.preceding(3),
    end=FrameBound.following(3),
)

# Entire partition
WindowFrame(
    FrameType.ROWS,
    start=FrameBound.unbounded_preceding(),
    end=FrameBound.unbounded_following(),
)

# Example: 30-day moving average
thirty_day_ma = await DailyStat.objects.annotate(
    ma_30=Window(
        Avg(F('value')),
        order_by='date',
        frame=WindowFrame(
            FrameType.ROWS,
            start=FrameBound.preceding(29),
            end=FrameBound.current_row(),
        )
    )
).all()`}
        </CodeBlock>
      </section>

      {/* Production Scenarios */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Production Scenarios</h2>

        <h3 className={`text-lg font-semibold mb-3 ${t('text-gray-200', 'text-gray-800')}`}>Top-N Per Group</h3>
        <p className={`mb-4 ${t('text-gray-300', 'text-gray-600')}`}>
          SQL does not allow filtering on window annotation aliases directly in WHERE (SQL engine restriction —
          window functions execute after WHERE). Fetch via a CTE or subquery, then filter in Python or wrap in a CTE:
        </p>
        <CodeBlock language="python">
{`from aquilia.models import Window, RowNumber, F

# Fetch top-3 posts per author (filter in Python after fetch)
posts = await Post.objects.annotate(
    rn=Window(RowNumber(), partition_by=['author_id'], order_by='-likes')
).all()

top3 = [p for p in posts if p.rn <= 3]

# Alternative: use a CTE to filter at the database level (v1.3.3+)
ranked = Post.objects.annotate(
    rn=Window(RowNumber(), partition_by=['author_id'], order_by='-likes')
).cte('ranked_posts')

top3_qs = await (
    Post.objects
    .with_cte(ranked)
    # SELECT * FROM "ranked_posts" WHERE rn <= 3
    # Achieved by selecting from the CTE directly — see CTE docs
).all()`}
        </CodeBlock>

        <h3 className={`text-lg font-semibold mb-3 mt-8 ${t('text-gray-200', 'text-gray-800')}`}>Year-over-Year Comparison</h3>
        <CodeBlock language="python">
{`from aquilia.models import Window, Lag, F

# Revenue vs same month last year
revenue = await MonthlyRevenue.objects.annotate(
    prev_year=Window(
        Lag(F('revenue'), offset=12, default=0),
        partition_by=['product_id'],
        order_by='period',
    )
).all()

for r in revenue:
    if r.prev_year:
        r.yoy_pct = (r.revenue - r.prev_year) / r.prev_year * 100`}
        </CodeBlock>
      </section>

      {/* Backend Compatibility */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Backend Compatibility</h2>
        <div className={`rounded-lg border overflow-hidden ${t('border-gray-700', 'border-gray-200')}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={t('bg-gray-800', 'bg-gray-50')}>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>Feature</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>SQLite</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>PostgreSQL</th>
                <th className={`px-4 py-3 text-left font-semibold ${t('text-gray-300', 'text-gray-700')}`}>MySQL</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${t('divide-gray-700', 'divide-gray-200')}`}>
              {[
                ['Window functions', '3.25+', '8.4+', '8.0+'],
                ['ROWS/RANGE frames', '3.25+', '8.4+', '8.0+'],
                ['GROUPS frame', '3.28+', '11+', 'Not supported'],
                ['NTH_VALUE', '3.25+', '11+', '8.0.2+'],
                ['IGNORE NULLS (Lag/Lead)', 'Not supported', '11+', '8.0+'],
              ].map(([feat, s, p, m]) => (
                <tr key={feat as string}>
                  <td className={`px-4 py-3 ${t('text-gray-300', 'text-gray-700')}`}>{feat}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400', 'text-gray-500')}`}>{s}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400', 'text-gray-500')}`}>{p}</td>
                  <td className={`px-4 py-3 font-mono text-xs ${t('text-gray-400', 'text-gray-500')}`}>{m}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Limitations */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${t('text-white', 'text-gray-900')}`}>Limitations & Gotchas</h2>
        <ul className={`space-y-3 ${t('text-gray-300', 'text-gray-600')}`}>
          <li className="flex gap-3">
            <span className="text-amber-400 mt-0.5">⚠</span>
            <span><strong>Cannot filter on window annotations in WHERE</strong> — SQL evaluates window functions after WHERE and GROUP BY. Use a CTE or subquery to filter on window results.</span>
          </li>
          <li className="flex gap-3">
            <span className="text-amber-400 mt-0.5">⚠</span>
            <span><strong>Cannot use window annotations in GROUP BY</strong> — Window expressions may not appear in GROUP BY columns.</span>
          </li>
          <li className="flex gap-3">
            <span className="text-amber-400 mt-0.5">⚠</span>
            <span><strong>Ntile parameter is a bind value</strong> — <code>Ntile(n)</code> passes <code>n</code> as a parameter, not inlined SQL. This is correct and safe.</span>
          </li>
          <li className="flex gap-3">
            <span className="text-green-400 mt-0.5">✓</span>
            <span><strong>Placeholders use <code>?</code></strong> — All Aquilia backends use positional <code>?</code> placeholders. The backend layer translates as needed.</span>
          </li>
        </ul>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${t('border-gray-700', 'border-gray-200')}`}>
        <Link
          to="/docs/models/aggregation"
          className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300', 'text-aquilia-600 hover:text-aquilia-500')}`}
        >
          <ArrowLeft className="w-4 h-4" /> Aggregation
        </Link>
        <Link
          to="/docs/models/cte"
          className={`flex items-center gap-2 text-sm font-medium ${t('text-aquilia-400 hover:text-aquilia-300', 'text-aquilia-600 hover:text-aquilia-500')}`}
        >
          Common Table Expressions <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  );
}
