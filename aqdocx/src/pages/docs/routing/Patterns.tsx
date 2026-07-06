import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowRight, GitBranch, Shield, Zap, Layers, AlertCircle, Sparkles } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function RoutingPatterns() {
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
            Pattern Matching Syntax
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia employs a formal parameter parser that validates and casts incoming path and query parameter tokens. 
        </p>
      </div>

      {/* Syntax Notice */}
      <div className="p-4 border-l-4 border-red-500 bg-red-500/5 rounded-r-xl space-y-2">
        <h4 className="font-bold text-sm text-red-500 flex items-center gap-2">
          <AlertCircle className="w-4 h-4" />
          Legacy Syntax Removed
        </h4>
        <p className={`text-xs ${isDark ? 'text-red-200/80' : 'text-red-800'}`}>
          Angle brackets/chevrons (e.g. <code className="text-red-500 font-semibold">&lt;id:int&gt;</code>) are <strong>no longer supported</strong> and have been completely removed. You must use curly braces <code className="text-red-500 font-semibold">{"{id:int}"}</code> for all routing parameters.
        </p>
      </div>

      {/* EBNF Parameter Grammar */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Parameter Grammar Definition
        </h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          A parameter token follows this EBNF grammar structure:
        </p>
        <CodeBlock
          language="ebnf"
          code={`token = "{" ident [ ":" type ] [ "|" constraint_list ] [ "=" default ] [ "@" transform ] "}"`}
        />
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          This design allows you to enforce validation constraints, type-casting rules, and string transformations directly within the route template.
        </p>
      </section>

      {/* Built-in Types */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Shield className="w-5 h-5 text-aquilia-400" />
          Segment Type Reference
        </h2>
        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm text-left">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="px-4 py-3 font-semibold">Type Name</th>
                <th className="px-4 py-3 font-semibold">Internal Regex Matcher</th>
                <th className="px-4 py-3 font-semibold">Casting Result</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                ['str', '[^/]+', 'str (default if type is omitted)'],
                ['int', '\\d+', 'int'],
                ['float', '\\d+\\.\\d+', 'float'],
                ['uuid', '[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-4[a-fA-F0-9]{3}-[89abAB][a-fA-F0-9]{3}-[a-fA-F0-9]{12}', 'str (validated UUID v4)'],
                ['slug', '[a-z0-9-]+', 'str'],
                ['bool', '(true|false|1|0|yes|no)', 'bool'],
                ['json', '[^/]+', 'Parsed JSON object/list']
              ].map(([type_, regex, casting], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{"{"}name:{type_}{"}"}</td>
                  <td className="px-4 py-2 font-mono text-xs">{regex}</td>
                  <td className="px-4 py-2 text-xs">{casting}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Constraints and ReDoS safety */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          Constraints & ReDoS Prevention
        </h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Constraints are defined by appending pipeline operators (<code className="text-aquilia-500">|</code>) to parameter declarations:
        </p>
        <ul className={`list-disc pl-6 space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><code className="text-aquilia-500">min=value / max=value</code>: Restricts numeric limits or character lengths.</li>
          <li><code className="text-aquilia-500">in=(value1,value2)</code>: Limits choices to a static set (enum validation).</li>
          <li><code className="text-aquilia-500">re="pattern"</code>: Matches a custom regular expression constraint.</li>
        </ul>
        
        <div className="p-4 border-l-4 border-amber-500 bg-amber-500/5 rounded-r-xl">
          <p className={`text-xs ${isDark ? 'text-amber-300' : 'text-amber-700'}`}>
            <strong>ReDoS Security Guard:</strong> Custom regular expression constraints are automatically analyzed for vulnerability before compile time. Patterns exceeding 256 characters or patterns using unsafe nested quantifiers (like <code className="text-rose-500">(a+)+</code>) are rejected immediately to protect against Denial of Service.
          </p>
        </div>
      </section>

      {/* Catch-all Splats & Optional segments */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Sparkles className="w-5 h-5 text-aquilia-400" />
          Splats & Optional Groups
        </h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Splats capture all remaining segments. Optional groups allow nested, optional sub-segments:
        </p>
        <CodeBlock
          language="python"
          code={`# Splats:
@GET("/files/*path")            # path captures remaining segments as list ['a', 'b']
@GET("/download/*path:path")    # path captures segments as slash-joined string "a/b"

# Optional segments:
@GET("/posts[/{year:int}[/{month:int}]]")
# Matches: /posts, /posts/2024, /posts/2024/12`}
        />
      </section>

      {/* Query parameters & Transforms */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Query Parameters & Transforms</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Declare query variables directly at the end of templates. Use transforms (prefixed by <code className="text-aquilia-500">@</code>) to modify parameters on-the-fly:
        </p>
        <CodeBlock
          language="python"
          code={`# Query parameters mapping (?q=term&limit=10):
@GET("/search?q:str|min=1&limit:int=10")

# Parameter Transforms:
@GET("/users/{username:str@lower}")  # Casts parameter to lowercase before route handling
@GET("/articles/{title:str@strip}")  # Strips trailing and leading whitespace`}
        />
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/routing" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowRight className="w-4 h-4 rotate-180" />
          <span>Routing Overview</span>
        </Link>
        <Link to="/docs/routing/urls" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <span>URL Generation</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
