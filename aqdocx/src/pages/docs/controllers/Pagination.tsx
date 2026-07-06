import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Layers, ArrowLeft } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function ControllersPagination() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Layers className="w-4 h-4" />
          Controllers
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Pagination
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia provides standard pagination strategies out of the box to paginate list responses.
        </p>
      </div>

      {/* Strategies */}
      <section className="space-y-6">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Supported Strategies</h2>
        
        <div className="space-y-4">
          <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>1. PageNumberPagination</h3>
          <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Standard page-based pagination using <code className="text-aquilia-500">?page=2&page_size=20</code>. Works with both database QuerySets and in-memory lists.
          </p>
          <CodeBlock
            language="python"
            filename="pagenumber_pagination.py"
            code={`from aquilia import Controller, GET
from aquilia.controller.pagination import PageNumberPagination

class ProductsController(Controller):
    @GET("/", pagination_class=PageNumberPagination)
    async def list_products(self, ctx):
        # The routing engine automatically applies the paginator
        return await Product.objects.all()`}
          />
        </div>

        <div className="space-y-4">
          <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>2. LimitOffsetPagination</h3>
          <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Offset-based pagination using <code className="text-aquilia-500">?limit=20&offset=40</code>.
          </p>
        </div>

        <div className="space-y-4">
          <h3 className={`text-lg font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>3. CursorPagination</h3>
          <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
             Opaque cursor-based keyset pagination using <code className="text-aquilia-500">?cursor=...</code>. Designed for large, frequently changing datasets where page skips are expensive or lead to duplicate elements.
          </p>
        </div>
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
