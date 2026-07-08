import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { GitBranch, ArrowLeft, ArrowRight, Zap, RefreshCw, Layers, Cpu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function DIRequestDAG() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Cpu className="w-4 h-4" />
          Dependency Injection / RequestDAG
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          RequestDAG &amp; Inline Injection
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          The <code className="text-aquilia-500">RequestDAG</code> resolves dependencies declared inline via <code className="text-aquilia-500">Dep()</code> in route signatures. It compiles a deduplicated, concurrent execution graph per request.
        </p>
      </div>

      {/* Core Concepts */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Execution Mechanics</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[
            { icon: <Layers className="w-5 h-5" />, title: 'Graph Deduplication', desc: 'If multiple dependencies inside your handler require the same sub-dependency (like a DB connection), the RequestDAG calculates a deduplicated graph. The shared sub-dependency executes exactly once.' },
            { icon: <Zap className="w-5 h-5" />, title: 'Parallel Resolution', desc: 'Independent branches of the dependency graph are resolved concurrently using asyncio.gather. The engine maximizes throughput for async I/O bounded dependencies.' },
            { icon: <RefreshCw className="w-5 h-5" />, title: 'LIFO Generator Teardown', desc: 'If a dependency yields a value, execution pauses. After the HTTP response is sent, the code following the yield block executes in strict Last-In-First-Out (LIFO) order to guarantee safe resource release.' },
            { icon: <GitBranch className="w-5 h-5" />, title: 'Container Fallback', desc: 'If a Dep() annotation targets an interface or type natively bound in the application Container (via @service), the RequestDAG seamlessly falls back to container.resolve_async().' },
          ].map((card, i) => (
            <div key={i} className="group relative overflow-hidden rounded-2xl bg-white/5 border border-white/5 hover:border-aquilia-500/20 p-6 backdrop-blur-sm transition-all duration-300 hover:translate-y-[-2px] hover:shadow-lg shadow-black/40">
              <div className="absolute top-0 bottom-0 left-0 w-1 bg-gradient-to-b from-aquilia-500 to-transparent opacity-50 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="flex items-center gap-3 mb-3">
                <div className="text-aquilia-500">{card.icon}</div>
                <h3 className={`font-semibold ${isDark ? 'text-white' : 'text-gray-900'}`}>{card.title}</h3>
              </div>
              <p className={`text-sm leading-relaxed ${subtleText}`}>{card.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Resolution Flow Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Resolution Flow</h2>
        <p className={`mb-4 ${subtleText}`}>
          Consider a route handler with deeply nested dependencies:
        </p>

        <CodeBlock language="python" filename="Nested Dependencies">{`from typing import Annotated
from aquilia.di import Dep

async def get_db():
    print("Opening DB")
    yield "DB_SESSION"
    print("Closing DB")

async def get_user_repo(db: Annotated[str, Dep(get_db)]):
    print("Creating UserRepo")
    return {"name": "UserRepository", "db": db}

async def get_auth_service(db: Annotated[str, Dep(get_db)]):
    print("Creating AuthService")
    return {"name": "AuthService", "db": db}

# In your controller class:
class MyController(Controller):
    @get("/dashboard")
    async def dashboard_view(
        self,
        ctx,
        repo: Annotated[dict, Dep(get_user_repo)],
        auth: Annotated[dict, Dep(get_auth_service)],
    ):
        return {"repo": repo, "auth": auth}`}</CodeBlock>

        <div className="border-l-4 border-aquilia-500 bg-aquilia-500/5 pl-6 py-4 rounded-r-xl my-6">
          <h4 className={`font-mono text-sm mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Execution Output Trace:</h4>
          <ol className={`space-y-2 list-decimal list-inside font-mono text-xs ${isDark ? 'text-green-400' : 'text-green-700'}`}>
            <li><span className={isDark ? 'text-gray-300' : 'text-gray-800'}>Opening DB</span> <span className="text-gray-500 text-xs italic">// Executed only once due to deduplication!</span></li>
            <li><span className={isDark ? 'text-gray-300' : 'text-gray-800'}>Creating UserRepo</span> <span className="text-gray-500 text-xs italic">// Resolved concurrently</span></li>
            <li><span className={isDark ? 'text-gray-300' : 'text-gray-800'}>Creating AuthService</span></li>
            <li><span className="text-blue-400">HTTP Response sent to client</span></li>
            <li><span className={isDark ? 'text-gray-300' : 'text-gray-800'}>Closing DB</span> <span className="text-gray-500 text-xs italic">// Teardown executed in LIFO order after response</span></li>
          </ol>
        </div>
      </section>

      {/* Navigation */}
      <div className={`mt-16 pt-8 border-t flex justify-between ${isDark ? 'border-white/5' : 'border-gray-200'}`}>
        <Link to="/docs/di/decorators" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> Decorators
        </Link>
        <Link to="/docs/di/extractors" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          Extractors <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}
