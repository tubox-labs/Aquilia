import { useTheme } from '../../../context/ThemeContext';
import { CodeBlock } from '../../../components/CodeBlock';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { NextSteps } from '../../../components/NextSteps';

export function ModelsAggregation() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-2 text-sm mb-4">
          <Link to="/docs" className={isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}>Docs</Link>
          <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>/</span>
          <Link to="/docs/models/overview" className={isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}>Models</Link>
          <span className={isDark ? 'text-gray-500' : 'text-gray-400'}>/</span>
          <span className={isDark ? 'text-gray-300' : 'text-gray-600'}>Aggregation</span>
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Aggregation
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-xl ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Computing database summary values using Sum, Avg, Count, Max, Min, and database group-by operations.
        </p>
      </div>

      {/* Aggregation */}
      <section className="mb-12">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Database Aggregates</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aggregate functions compute summary values. Use <code>.aggregate()</code> for whole-table aggregates or <code>.annotate()</code> with <code>.group_by()</code> for per-group.
        </p>
        <div className={`rounded-lg border ${isDark ? 'border-gray-700' : 'border-gray-200'} overflow-hidden mb-4`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={isDark ? 'bg-gray-800' : 'bg-gray-50'}>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Function</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>SQL</th>
                <th className={`px-4 py-3 text-left font-semibold ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>Notes</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-gray-700' : 'divide-gray-200'}`}>
              {[
                ['Sum("field")', 'SUM(field)', 'Numeric sum'],
                ['Avg("field")', 'AVG(field)', 'Average'],
                ['Count("field")', 'COUNT(field)', 'Count. distinct=True for COUNT(DISTINCT)'],
                ['Max("field")', 'MAX(field)', 'Maximum value'],
                ['Min("field")', 'MIN(field)', 'Minimum value'],
                ['StdDev("field")', 'STDDEV(field)', 'Standard deviation. sample=True for STDDEV_SAMP'],
                ['Variance("field")', 'VARIANCE(field)', 'Variance. sample=True for VAR_SAMP'],
              ].map(([func, sql, notes]) => (
                <tr key={func}>
                  <td className={`px-4 py-3 font-mono ${isDark ? 'text-aquilia-400' : 'text-blue-600'}`}>{func}</td>
                  <td className={`px-4 py-3 font-mono ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>{sql}</td>
                  <td className={`px-4 py-3 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{notes}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <CodeBlock language="python">
{`from aquilia.models.aggregate import Sum, Avg, Count, Max, Min

# Whole-table aggregate
stats = await Order.objects.aggregate(
    total=Sum("amount"),
    avg_amount=Avg("amount"),
    order_count=Count("id"),
    max_amount=Max("amount"),
)
# → {"total": 50000, "avg_amount": 250.0, "order_count": 200, "max_amount": 999}

# Per-group annotation
by_category = await (
    Product.objects
    .annotate(total_sales=Sum("sales"))
    .group_by("category")
    .order("-total_sales")
    .values("category", "total_sales")
    .all()
)
# → [{"category": "Electronics", "total_sales": 50000}, ...]

# PostgreSQL-specific aggregates
from aquilia.models.aggregate import ArrayAgg, StringAgg

grouped = await (
    Tag.objects
    .annotate(
        names=ArrayAgg("name"),
        csv=StringAgg("name", delimiter=", "),
    )
    .group_by("category")
    .values("category", "names", "csv")
    .all()
)`}
        </CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex justify-between items-center pt-8 mt-8 border-t ${isDark ? 'border-gray-700' : 'border-gray-200'}`}>
        <Link
          to="/docs/models/transactions"
          className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}
        >
          <ArrowLeft className="w-4 h-4" /> Transactions
        </Link>
        <Link
          to="/docs/models/advanced"
          className={`flex items-center gap-2 text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}
        >
          Advanced <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  );
}
