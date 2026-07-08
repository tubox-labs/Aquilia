import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { ArrowLeft, ArrowRight, Cpu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function DIDecorators() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Cpu className="w-4 h-4" />
          Dependency Injection / Decorators
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          DI Decorators &amp; Metadata
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Aquilia provides clear annotations under <code className="text-aquilia-500">aquilia/di/decorators.py</code> to configure scopes, inject instances, and define factory dependencies declaratively.
        </p>
      </div>

      {/* Inject Dataclass */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Inject Dataclass</h2>
        <p className={`mb-4 ${subtleText}`}>
          The <code className="text-aquilia-500">Inject</code> dataclass is used within <code className="text-aquilia-500">typing.Annotated</code> hints to instruct providers on how to resolve dependencies:
        </p>
        <CodeBlock language="python" filename="Inject Dataclass">{`from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Inject:
    token: Optional[Any] = None     # Override resolution token
    tag: Optional[str] = None       # Disambiguate between multiple providers
    optional: bool = False          # Resolves to None if unregistered`}</CodeBlock>

        <h3 className={`text-lg font-semibold mb-3 mt-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Usage with Annotated</h3>
        <CodeBlock language="python" filename="Inject in Type Hints">{`from typing import Annotated
from aquilia.di import Inject

class OrderService:
    def __init__(
        self,
        # Resolved by parameter type hint
        repo: OrderRepository,
        
        # Tagged resolution (disambiguate multiple CacheBackends)
        cache: Annotated[CacheBackend, Inject(tag="redis")],
        
        # Optional resolution (defaults to None if missing)
        metrics: Annotated[MetricsClient, Inject(optional=True)],
    ):
        self.repo = repo
        self.cache = cache
        self.metrics = metrics`}</CodeBlock>

        <div className="border-l-4 border-aquilia-500 bg-aquilia-500/5 pl-4 py-3 rounded-r-xl my-6">
          <p className="text-xs text-aquilia-500/90 leading-relaxed">
            <strong>Internal Extraction:</strong> The container uses <code className="text-xs">typing.get_type_hints(cls.__init__)</code> to extract these metadata markers during manifest processing, creating highly optimized static execution plans.
          </p>
        </div>
      </section>

      {/* inject() factory */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>inject()</h2>
        <p className={`mb-4 ${subtleText}`}>
          A shorthand helper that generates <code className="text-aquilia-500">Inject</code> configurations:
        </p>
        <CodeBlock language="python" filename="inject() Shorthand">{`from aquilia.di import inject

class OrderService:
    def __init__(
        self,
        cache: Annotated[CacheBackend, inject(tag="redis")]
    ):
        self.cache = cache`}</CodeBlock>
      </section>

      {/* Dep Descriptor */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Dep (Per-Request Dependency Injection)</h2>
        <div className="border-l-4 border-indigo-500 bg-indigo-500/5 pl-4 py-3 rounded-r-xl my-6">
          <p className="text-xs text-indigo-500/90 leading-relaxed">
            <strong>FastAPI-Style Injection:</strong> <code className="text-xs">Dep</code> is Aquilia's modern approach to inline route injection. It allows you to declare dependencies directly in route signatures, bypassing manifest declarations for route-specific tools.
          </p>
        </div>
        <p className={`mb-4 ${subtleText}`}>
          Dependencies declared in route signatures form a per-request Directed Acyclic Graph (DAG) resolved concurrently:
        </p>
        <CodeBlock language="python" filename="Inline Route Injection">{`from typing import Annotated
from aquilia.di import Dep
from aquilia.controller import Controller, get

async def get_db_session():
    async with db.session() as session:
        yield session

class UserController(Controller):
    prefix = "/users"

    # UserController constructor injection is still used for core services
    def __init__(self, auth: AuthService):
        self.auth = auth

    @get("/{user_id}")
    async def get_user(
        self,
        ctx,
        db_session: Annotated[DbSession, Dep(get_db_session)] # resolved per-request
    ):
        user = await db_session.query(User).filter_by(id=ctx.request.params["user_id"]).first()
        return ctx.json(user)`}</CodeBlock>
      </section>

      {/* Decorators Reference */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Registration Decorators</h2>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Decorator</th>
                <th className="py-4 px-6 text-left font-semibold">Scope</th>
                <th className="py-4 px-6 text-left font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                { d: '@service', s: 'singleton', desc: 'Registers a class as a singleton app-scoped service.' },
                { d: '@service(scope="request")', s: 'request', desc: 'Registers a request-scoped class, created per request.' },
                { d: '@service(scope="transient")', s: 'transient', desc: 'Registers a transient class, created fresh on every lookup.' },
                { d: '@factory', s: 'configurable', desc: 'Registers a function as a custom service factory.' },
                { d: '@provides(Token)', s: 'n/a', desc: 'Exposes a service instance from a custom provider method.' },
                { d: '@auto_inject', s: 'n/a', desc: 'Enables automatic constructor injection on a class without manifests.' },
              ].map((row, i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono text-aquilia-500 text-xs">{row.d}</td>
                  <td className="py-3.5 px-6 font-mono text-xs text-yellow-500">{row.s}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{row.desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className={`mt-16 pt-8 border-t flex justify-between ${isDark ? 'border-white/5' : 'border-gray-200'}`}>
        <Link to="/docs/di/scopes" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> Scopes
        </Link>
        <Link to="/docs/di/lifecycle" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          Lifecycle <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}