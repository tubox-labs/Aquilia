import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowRight, GitBranch, Link2, Zap, Settings, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function RoutingUrls() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <GitBranch className="w-4 h-4" />
          Routing
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            URL Generation
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia handles reverse URL resolution by looking up registered controller method names and filling in path templates at runtime.
        </p>
      </div>

      {/* url_for API */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Link2 className="w-5 h-5 text-aquilia-400" />
          Reverse Routing via url_for()
        </h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The router exposes a <code className="text-aquilia-500">url_for()</code> method that builds routes from target method names and arguments. Route name queries support absolute names (<code className="text-aquilia-500">ControllerClass.method_name</code>) or shorthand relative method names:
        </p>

        <CodeBlock
          language="python"
          code={`# Syntax: url_for("ControllerClass.method_name", **params)
url = router.url_for("ArticleController.get_article", id=42)
# → "/api/articles/42"

# Shorthand usage:
url = router.url_for("get_article", id=42)
# → "/api/articles/42"`}
        />
      </section>

      {/* Prefix Nesting */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Globe className="w-5 h-5 text-aquilia-400" />
          Prefix Nesting Resolution
        </h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Prefixes are merged compile-time to maintain path structure. For example, if you register a controller inside a module that has its own sub-prefix, <code className="text-aquilia-500">url_for</code> handles the combined path automatically:
        </p>
        <CodeBlock
          language="python"
          code={`# Module Prefix: "/v1"
# Controller Prefix: "/users"
# Route Template: "/{id:int}"
# Resolved URL: "/v1/users/42"`}
        />
      </section>

      {/* Query Parameters */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          Query Parameter Appends
        </h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Arguments that are not defined in the route parameter template are automatically appended to the path as query variables:
        </p>

        <CodeBlock
          language="python"
          code={`url = router.url_for("ArticleController.get_article", id=42, refresh=True, format="html")
# → "/api/articles/42?refresh=True&format=html"`}
        />
      </section>

      {/* Failures */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Settings className="w-5 h-5 text-aquilia-400" />
          Exception Handling
        </h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          If no controller matches the name query, the router raises a structured <code className="text-aquilia-500">RouteNotFoundFault</code>:
        </p>
        <CodeBlock
          language="python"
          code={`try:
    url = router.url_for("NonExistentController.get")
except RouteNotFoundFault as e:
    # Handle missing route
    pass`}
        />
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/routing/patterns" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowRight className="w-4 h-4 rotate-180" />
          <span>Pattern Matching</span>
        </Link>
        <Link to="/docs/di/overview" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <span>Dependency Injection</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
