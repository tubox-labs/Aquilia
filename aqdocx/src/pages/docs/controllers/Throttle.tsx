import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Layout, Shield, Server, Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function ControllersThrottle() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Shield className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Distributed Throttle Backends
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.controller.throttle — Pluggable rate limiting architecture</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          In Aquilia v1.3.4, rate limiting has been upgraded from in-memory tracking to a pluggable <code className="text-aquilia-500 font-mono">ThrottleBackend</code> system. Supports multi-process cluster deployments with distributed Redis rate limiting and graceful fail-open resilience.
        </p>
      </div>

      {/* Backend Architecture */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Server className="w-5 h-5 text-aquilia-400" />
          Available Backends
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className={`p-5 rounded-2xl border ${isDark ? 'bg-white/5 border-white/10' : 'bg-gray-50 border-gray-200'} space-y-3`}>
            <div className="flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-400" />
              <h3 className="font-bold text-lg text-white">MemoryThrottleBackend</h3>
            </div>
            <p className="text-xs text-gray-400">
              In-memory sliding window algorithm guarded by <code className="text-aquilia-400 font-mono">asyncio.Lock</code>. Built-in LRU eviction and periodic cleanup. Ideal for single-process workers.
            </p>
            <CodeBlock
              language="python"
              code={`throttle = Throttle.with_memory(limit=100, window=60)`}
            />
          </div>

          <div className={`p-5 rounded-2xl border ${isDark ? 'bg-white/5 border-white/10' : 'bg-gray-50 border-gray-200'} space-y-3`}>
            <div className="flex items-center gap-2">
              <Server className="w-5 h-5 text-emerald-400" />
              <h3 className="font-bold text-lg text-white">RedisThrottleBackend</h3>
            </div>
            <p className="text-xs text-gray-400">
              Distributed sliding window using Redis sorted sets (ZADD/ZCARD pipelines). Features lazy connection and <code className="text-aquilia-400 font-mono">fail_open=True</code> fallback when Redis is unreachable.
            </p>
            <CodeBlock
              language="python"
              code={`throttle = Throttle.with_redis("redis://localhost:6379", limit=100, window=60)`}
            />
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layout className="w-5 h-5 text-aquilia-400" />
          Using Throttles in Controllers
        </h2>

        <CodeBlock
          language="python"
          filename="throttle_example.py"
          code={`from aquilia.controller import Controller, route
from aquilia.controller.throttle import Throttle

# Instantiate distributed Redis rate limiter: 10 requests per 60 seconds
redis_throttle = Throttle.with_redis(
    redis_url="redis://localhost:6379/0",
    limit=10,
    window=60,
    fail_open=True
)

class ApiController(Controller):
    prefix = "/api/v1"

    # Route-level override
    @route(["GET"], "/sensitive-data", throttle=redis_throttle)
    async def get_data(self, ctx):
        return {"data": "sensitive"}`}
        />
      </section>

      {/* ThrottleBackend Factory */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>ThrottleBackendFactory</h2>
        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The factory dynamically instantiates the correct backend based on the connection string URL:
        </p>

        <CodeBlock
          language="python"
          filename="factory_example.py"
          code={`from aquilia.controller.throttle import ThrottleBackendFactory

# Memory backend
backend1 = ThrottleBackendFactory.create("memory")

# Redis backend
backend2 = ThrottleBackendFactory.create("redis://redis-cluster.internal:6379")`}
        />
      </section>

      <NextSteps />
    </div>
  )
}
