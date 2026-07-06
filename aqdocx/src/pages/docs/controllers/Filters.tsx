import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Shield, ArrowLeft } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function ControllersFilters() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Shield className="w-4 h-4" />
          Controllers
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Filtering, Searching & Ordering
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia supports declarative query parameter filters, searching, and field ordering directly on route decorators.
        </p>
      </div>

      {/* FilterSet */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>FilterSet</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">FilterSet</code> class defines field matches, ranges, case-insensitive checks, null validation, or custom query overrides:
        </p>

        <CodeBlock
          language="python"
          filename="filters_example.py"
          code={`from aquilia import Controller, GET
from aquilia.controller.filters import FilterSet

class ProductFilter(FilterSet):
    class Meta:
        fields = {
            "category": ["exact"],
            "price": ["gte", "lte", "range"],
            "is_active": ["exact"],
            "name": ["icontains"],
        }

class ProductsController(Controller):
    prefix = "/products"

    @GET("/", filterset_class=ProductFilter,
         search_fields=["name", "description"],
         ordering_fields=["price", "created_at"])
    async def list_products(self, ctx):
        # Auto-filters category, price ranges, handles ?search=term and ?ordering=price
        return await Product.objects.all()`}
        />
      </section>

      {/* ReDoS Prevention */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold text-rose-500`}>ReDoS Security Guards</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          To protect endpoints from Regular Expression Denial of Service (ReDoS) attacks, Aquilia enforces strict validation when compiling user-provided filter patterns:
        </p>
        <ul className={`list-disc pl-6 space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><strong>Pattern Length Limits:</strong> Rejects any pattern exceeding 256 characters.</li>
          <li><strong>Dangerous Alterations:</strong> Rejects nested alternations and quantifier repetitions like <code className="text-rose-500">(a+)+</code> or <code className="text-rose-500">(a|a)+</code>.</li>
        </ul>
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/controllers/overview" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowLeft className="w-4 h-4" />
          <span>Controllers Overview</span>
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
