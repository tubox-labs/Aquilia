import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { ArrowLeft, ArrowRight, Cpu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function DIProviders() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Cpu className="w-4 h-4" />
          Dependency Injection / Providers
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          DI Providers
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Providers encapsulate instantiation logic. Each provider represents a blueprint for creating concrete services.
        </p>
      </div>

      {/* ClassProvider */}
      <section className="mb-16 border-l-2 border-aquilia-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>ClassProvider</h2>
        <p className={`mb-4 ${subtleText}`}>
          The default provider type. Instantiates a class by auto-resolving constructor dependencies via <code className="text-aquilia-500">inspect.signature()</code> and type hints. Supports <code className="text-aquilia-500">Annotated[Type, Inject(...)]</code> for tagged dependencies and the <code className="text-aquilia-500">async_init()</code> convention for post-construction async initialization.
        </p>

        <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Dependency Extraction</h3>
        <p className={`mb-4 text-sm ${subtleText}`}>
          The container analyzes constructor signatures at manifest loading time to construct O(1) resolution plans:
        </p>
        <div className="space-y-3 mb-6 text-sm text-gray-400">
          {[
            'Inspects __init__ signatures via inspect.signature()',
            'Bypasses self and wildcard parameters (*args, **kwargs)',
            'Checks for Annotated[Type, Inject(tag="...")] for disambiguation',
            'Resolves matching types automatically'
          ].map((item, idx) => (
            <div key={idx} className="flex items-center gap-3">
              <span className="w-1.5 h-1.5 rounded-full bg-aquilia-500" />
              <span>{item}</span>
            </div>
          ))}
        </div>

        <CodeBlock language="python" filename="ClassProvider Usage">{`from aquilia.di.providers import ClassProvider
from aquilia.di import Inject
from typing import Annotated

class OrderService:
    def __init__(
        self,
        repo: OrderRepository,                              # Untagged dep
        cache: Annotated[CacheBackend, Inject(tag="redis")], # Tagged dep
        logger: Annotated[Logger, Inject(optional=True)],    # Optional dep
    ):
        self.repo = repo
        self.cache = cache
        self.logger = logger
    
    async def async_init(self):
        """Called after __init__ if present. Perfect for async setup."""
        await self.cache.ping()

# Registers in container
provider = ClassProvider(OrderService, scope="request")`}</CodeBlock>
      </section>

      {/* FactoryProvider */}
      <section className="mb-16 border-l-2 border-orange-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>FactoryProvider</h2>
        <p className={`mb-4 ${subtleText}`}>
          Calls a sync or async factory function to create instances. Dependencies are auto-resolved from the factory function's parameter signature.
        </p>
        <CodeBlock language="python" filename="FactoryProvider Usage">{`from aquilia.di.providers import FactoryProvider

async def create_database_pool(config: AppConfig) -> DatabasePool:
    pool = await asyncpg.create_pool(dsn=config.database_url)
    return pool

provider = FactoryProvider(
    token=DatabasePool,
    factory_fn=create_database_pool,
    scope="app",
)`}</CodeBlock>
      </section>

      {/* ValueProvider */}
      <section className="mb-16 border-l-2 border-yellow-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>ValueProvider</h2>
        <p className={`mb-4 ${subtleText}`}>
          Returns a pre-existing object instance. Useful for configurations or external clients initialized outside the DI framework.
        </p>
        <CodeBlock language="python" filename="ValueProvider Usage">{`from aquilia.di.providers import ValueProvider

config = AppConfig(debug=True)
provider = ValueProvider(token=AppConfig, value=config)`}</CodeBlock>
      </section>

      {/* PoolProvider */}
      <section className="mb-16 border-l-2 border-green-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>PoolProvider</h2>
        <p className={`mb-4 ${subtleText}`}>
          Maintains an internal `asyncio.Queue` pool of instances for concurrent reuse. Resolving acquires an instance, and releasing returns it.
        </p>
        <CodeBlock language="python" filename="PoolProvider Usage">{`from aquilia.di.providers import PoolProvider

# Pool manages 10 instances of heavy clients
provider = PoolProvider(
    HeavyClient,
    max_size=10,
    scope="pooled",
)`}</CodeBlock>
      </section>

      {/* BlueprintProvider */}
      <section className="mb-16 border-l-2 border-pink-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>BlueprintProvider</h2>
        <p className={`mb-4 ${subtleText}`}>
          Specially designed for request validation. Instantiates a <code className="text-aquilia-500">Blueprint</code> validation schema by parsing and binding the incoming request payload with strict casting rules.
        </p>
        <CodeBlock language="python" filename="BlueprintProvider Usage">{`from aquilia.di.providers import BlueprintProvider

# Registers in container
container.register(BlueprintProvider(UserBlueprint, scope="request"))`}</CodeBlock>
      </section>

      {/* Selection Logic */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Automatic Provider Selection</h2>
        <p className={`mb-4 ${subtleText}`}>
          When the Registry processes a manifest service entry, it selects the appropriate provider type automatically:
        </p>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="py-4 px-6 text-left font-semibold text-aquilia-500">Condition</th>
                <th className="py-4 px-6 text-left font-semibold">Provider Created</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['Entry is a class with __di_factory__ attribute', 'FactoryProvider'],
                ['Entry is a callable (function)', 'FactoryProvider'],
                ['Entry is a class (standard)', 'ClassProvider'],
                ['Entry has "allow_lazy": True and is in a cycle', 'LazyProxyProvider wrapping ClassProvider'],
                ['Entry has "scope" override', 'ScopedProvider wrapping the inner provider'],
                ['Entry is a pre-built value', 'ValueProvider'],
                ['Entry is a Blueprint subclass', 'BlueprintProvider'],
              ].map(([condition, provider], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className={`py-3.5 px-6 ${subtleText}`}>{condition}</td>
                  <td className="py-3.5 px-6"><code className="text-aquilia-500 text-xs">{provider}</code></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Navigation */}
      <div className={`mt-16 pt-8 border-t flex justify-between ${isDark ? 'border-white/5' : 'border-gray-200'}`}>
        <Link to="/docs/di/container" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> Container
        </Link>
        <Link to="/docs/di/scopes" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          Scopes <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}