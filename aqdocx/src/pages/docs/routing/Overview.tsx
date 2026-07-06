import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowRight, GitBranch, Shield, Zap, Layers, AlertCircle } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function RoutingOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <GitBranch className="w-4 h-4" />
          Core / Routing
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Routing
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia features a highly optimized, compile-time routing engine. By declaring route patterns directly on controller methods via decorators, routes are parsed, analyzed, and compiled at application startup to provide near-zero matching overhead.
        </p>
      </div>

      {/* Warning Banner: Legacy Syntax Removal */}
      <div className="p-4 border-l-4 border-red-500 bg-red-500/5 rounded-r-xl space-y-2">
        <h4 className="font-bold text-sm text-red-500 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          Syntax Deprecation & Removal Warning
        </h4>
        <p className={`text-xs ${isDark ? 'text-red-200/80' : 'text-red-800'}`}>
          The legacy angle bracket parameter syntax (e.g. <code className="text-red-500 font-semibold">&lt;id:int&gt;</code> or <code className="text-red-500 font-semibold">«id:int»</code>) has been <strong>completely removed</strong> from the framework. Using it will result in compilation and runtime matching failures. You must use the modern curly brace format (e.g. <code className="text-red-500 font-semibold">{"{id:int}"}</code>) for all parameterized paths.
        </p>
      </div>

      {/* Route Declaration */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Shield className="w-5 h-5 text-aquilia-400" />
          Route Declaration & Nesting
        </h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          In Aquilia, controllers act as routing namespaces. The class-level <code className="text-aquilia-500">prefix</code> is automatically merged with method-level path templates during compilation:
        </p>

        <CodeBlock
          language="python"
          filename="controller_routing.py"
          code={`from aquilia import Controller, GET, POST, RequestCtx, Response

class ArticleController(Controller):
    prefix = "/api/articles"

    @GET("/")
    async def list_articles(self, ctx: RequestCtx) -> Response:
        # Resolves to: GET /api/articles
        return Response.json({"articles": []})

    @GET("/{id:int}")
    async def get_article(self, ctx: RequestCtx, id: int) -> Response:
        # Resolves to: GET /api/articles/42
        return Response.json({"id": id})`}
        />
      </section>

      {/* Specificity */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          Route Specificity Scoring
        </h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia avoids matching order bugs by sorting routes mathematically based on segment specificity. When matching a path, the router evaluates routes from the highest specificity score to the lowest:
        </p>
        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="px-4 py-3 font-semibold">Route Pattern</th>
                <th className="px-4 py-3 font-semibold">Match Target</th>
                <th className="px-4 py-3 font-semibold">Specificity Score</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                ['/users/active', '/users/active (Exact match)', '200 (Static segments +100 each)'],
                ['/users/{id:int}', '/users/42 (Integer segment match)', '150 (Static + Typed parameter +50)'],
                ['/users/{slug:str}', '/users/john (Generic string match)', '125 (Static + Untyped parameter +25)'],
                ['/users/*path', '/users/profile/settings (Wildcard catch-all)', '101 (Static + Splat segment +1)']
              ].map(([pattern, target, score], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{pattern}</td>
                  <td className="px-4 py-2 text-xs">{target}</td>
                  <td className="px-4 py-2 font-mono text-xs">{score}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Guides */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Guides & Reference
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-2">
          <Link to="/docs/routing/patterns" className="group block space-y-1 hover:text-aquilia-500 transition-colors">
            <h3 className={`font-semibold text-sm flex items-center gap-2 ${isDark ? 'text-white group-hover:text-aquilia-400' : 'text-gray-900 group-hover:text-aquilia-600'}`}>
              <span>Pattern Syntax & constraints</span>
              <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
            </h3>
            <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>Curly brace pattern grammar, types, constraints, and validation.</p>
          </Link>
          <Link to="/docs/routing/urls" className="group block space-y-1 hover:text-aquilia-500 transition-colors">
            <h3 className={`font-semibold text-sm flex items-center gap-2 ${isDark ? 'text-white group-hover:text-aquilia-400' : 'text-gray-900 group-hover:text-aquilia-600'}`}>
              <span>URL Generation</span>
              <ArrowRight className="w-4 h-4 opacity-0 group-hover:opacity-100 transition-opacity" />
            </h3>
            <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>Reverse path routing using url_for and query parameters.</p>
          </Link>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}