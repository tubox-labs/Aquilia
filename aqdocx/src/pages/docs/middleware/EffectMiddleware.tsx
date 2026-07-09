import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MiddlewareEffect() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Layers className="w-4 h-4" />
          <span>MIDDLEWARE / EFFECTS ACQUISITION</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          EffectMiddleware &amp; FlowContextMiddleware
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          These middlewares integrate the Effects capability-resolution system with the ASGI HTTP pipeline, enabling automatic acquisition and releasing of transactional resources.
        </p>
      </div>

      {/* EffectMiddleware */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>1. EffectMiddleware</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The <code className="text-aquilia-500">EffectMiddleware</code> inspects handler route declarations (like <code className="text-aquilia-400">@requires()</code>) at request start, calls the active providers to acquire the resources, and cleans them up after the handler finishes executing.
        </p>

        <div className="space-y-4 mb-8 text-sm text-gray-400 font-sans">
          <div className="border-b border-white/5 pb-2">
            <code className="text-white text-xs font-mono">effect_registry: EffectRegistry | None = None</code> — The registry carrying registered side-effect providers.
          </div>
          <div className="pb-2">
            <code className="text-white text-xs font-mono">auto_detect: bool = True</code> — Enables automatic inspection of <code className="text-white">__flow_effects__</code> on route handlers.
          </div>
        </div>
      </section>

      {/* FlowContextMiddleware */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>2. FlowContextMiddleware</h2>
        <p className={`mb-6 leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The <code className="text-aquilia-500">FlowContextMiddleware</code> sets up a thread-safe context object carrying request and capability states, exposing them to sub-guards or nested call pipelines.
        </p>
      </section>

      {/* Usage Example */}
      <section className="mb-16">
        <h2 className={`text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6`}>Usage Example</h2>
        <CodeBlock language="python" filename="effects_middleware_setup.py" highlightLines={[6, 9]}>{`from aquilia.middleware_ext import EffectMiddleware, FlowContextMiddleware
from aquilia.workspace import Workspace
from aquilia.integrations import MiddlewareChain

workspace = Workspace("myapp").middleware(
    MiddlewareChain()
    .use("aquilia.middleware_ext.effect_middleware:FlowContextMiddleware", priority=15)
    .use("aquilia.middleware_ext.effect_middleware:EffectMiddleware", priority=16)
)`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/middleware/overview" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <span />
      </div>

      <NextSteps />
    </div>
  )
}
