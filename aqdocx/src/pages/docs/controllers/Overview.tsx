import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Layout, Layers, Plug, Settings } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ControllersOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Layout className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Controllers
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.controller — Class-based request handlers</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Controllers are the primary request handling abstraction in Aquilia. Unlike function-based routing, Aquilia controllers are classes that support dependency injection, lifecycle hooks, pipeline execution, rate limiting, and content negotiation.
        </p>
      </div>

      {/* Low-level System Design */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Low-Level System Design</h2>
        <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The following diagram details the low-level execution flow when a request matches a controller endpoint:
        </p>

        <div className="flex justify-center items-center overflow-x-auto py-6">
          <svg viewBox="0 0 800 320" className="w-full max-w-3xl" fill="none" xmlns="http://www.w3.org/2000/svg">
            {/* Step 1: ASGI Router */}
            <rect x="20" y="110" width="120" height="70" rx="10" fill={isDark ? '#18181B' : '#F4F4F5'} stroke="#10B981" strokeWidth="2" />
            <text x="80" y="140" textAnchor="middle" fill={isDark ? '#F3F4F6' : '#111827'} fontSize="11" fontWeight="bold">1. ASGI Router</text>
            <text x="80" y="160" textAnchor="middle" fill={isDark ? '#A1A1AA' : '#71717A'} fontSize="9">Matches CompiledRoute</text>

            <path d="M140 145 H180" stroke="#71717A" strokeWidth="2" markerEnd="url(#arrow)" />

            {/* Step 2: Compiler */}
            <rect x="180" y="20" width="130" height="70" rx="10" fill={isDark ? '#18181B' : '#F4F4F5'} stroke="#F59E0B" strokeWidth="2" />
            <text x="245" y="50" textAnchor="middle" fill={isDark ? '#F3F4F6' : '#111827'} fontSize="11" fontWeight="bold">Route Compiler</text>
            <text x="245" y="70" textAnchor="middle" fill={isDark ? '#A1A1AA' : '#71717A'} fontSize="9">Bakes metadata</text>

            {/* Step 3: Controller Factory */}
            <rect x="180" y="110" width="130" height="70" rx="10" fill={isDark ? '#18181B' : '#F4F4F5'} stroke="#3B82F6" strokeWidth="2" />
            <text x="245" y="140" textAnchor="middle" fill={isDark ? '#F3F4F6' : '#111827'} fontSize="11" fontWeight="bold">2. Factory (DI)</text>
            <text x="245" y="160" textAnchor="middle" fill={isDark ? '#A1A1AA' : '#71717A'} fontSize="9">Instantiates instance</text>

            <path d="M310 145 H350" stroke="#71717A" strokeWidth="2" markerEnd="url(#arrow)" />

            {/* Step 4: Pipeline Execution */}
            <rect x="350" y="110" width="140" height="70" rx="10" fill={isDark ? '#18181B' : '#F4F4F5'} stroke="#8B5CF6" strokeWidth="2" />
            <text x="420" y="140" textAnchor="middle" fill={isDark ? '#F3F4F6' : '#111827'} fontSize="11" fontWeight="bold">3. Pipeline Nodes</text>
            <text x="420" y="160" textAnchor="middle" fill={isDark ? '#A1A1AA' : '#71717A'} fontSize="9">Guards / Interceptors</text>

            <path d="M490 145 H530" stroke="#71717A" strokeWidth="2" markerEnd="url(#arrow)" />

            {/* Step 5: Parameter Binding */}
            <rect x="530" y="110" width="140" height="70" rx="10" fill={isDark ? '#18181B' : '#F4F4F5'} stroke="#EC4899" strokeWidth="2" />
            <text x="600" y="140" textAnchor="middle" fill={isDark ? '#F3F4F6' : '#111827'} fontSize="11" fontWeight="bold">4. Param Binding</text>
            <text x="600" y="160" textAnchor="middle" fill={isDark ? '#A1A1AA' : '#71717A'} fontSize="9">Blueprint casting/seal</text>

            <path d="M670 145 H700 V210 H420 V250" stroke="#71717A" strokeWidth="2" markerEnd="url(#arrow)" fill="none" />

            {/* Step 6: Method Execution */}
            <rect x="350" y="250" width="140" height="60" rx="10" fill={isDark ? '#27272A' : '#EFF6FF'} stroke="#2563EB" strokeWidth="2" />
            <text x="420" y="275" textAnchor="middle" fill={isDark ? '#FFFFFF' : '#1E40AF'} fontSize="11" fontWeight="bold">5. Execute Handler</text>
            <text x="420" y="295" textAnchor="middle" fill={isDark ? '#93C5FD' : '#1E40AF'} fontSize="9">Invokes method</text>

            <defs>
              <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#71717A" />
              </marker>
            </defs>
          </svg>
        </div>
      </section>

      {/* Controller class */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Settings className="w-5 h-5 text-aquilia-400" />
          The Controller Base Class
        </h2>

        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          All controllers extend <DocTerm id="controller.controller">Controller</DocTerm>. The base class provides:
        </p>

        <CodeBlock
          language="python"
          filename="controller_example.py"
          code={`from aquilia import Controller, GET, POST, PUT, DELETE, RequestCtx, Response

class ProductsController(Controller):
    # Class-level configuration
    prefix = "/api/products"
    pipeline = []
    tags = ["Products"]
    instantiation_mode = "per_request" # "per_request" or "singleton"

    # DI dependencies are injected into __init__
    def __init__(self, product_repo: ProductRepository):
        self.repo = product_repo

    # Route handler
    @GET("/")
    async def list_products(self, ctx: RequestCtx) -> Response:
        products = await self.repo.list_all()
        return Response.json({"products": products})`}
        />
      </section>

      {/* Class attributes */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Class Attributes
        </h2>

        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left px-4 py-3 font-semibold">Attribute</th>
                <th className="text-left px-4 py-3 font-semibold">Type</th>
                <th className="text-left px-4 py-3 font-semibold">Default</th>
                <th className="text-left px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                ['prefix', 'str', '""', 'URL prefix for all routes in this controller.'],
                ['pipeline', 'List[FlowNode]', '[]', 'Pipeline nodes applied to all routes in this controller.'],
                ['tags', 'List[str]', '[]', 'OpenAPI tags for routes.'],
                ['instantiation_mode', 'str', '"per_request"', '"per_request" (new instance per request) or "singleton" (shared).'],
                ['version', 'str | None', 'None', 'API version: "v1", "v2", etc.'],
                ['throttle', 'Throttle | None', 'None', 'Throttle instance for controller rate limiting.'],
                ['interceptors', 'List[Interceptor]', '[]', 'Controller interceptors.'],
                ['exception_filters', 'List[ExceptionFilter]', '[]', 'Exception filters.'],
              ].map(([attr, type, def_, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{attr}</td>
                  <td className="px-4 py-2 font-mono text-xs">{type}</td>
                  <td className="px-4 py-2 font-mono text-xs">{def_}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Instantiation modes */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Plug className="w-5 h-5 text-aquilia-400" />
          Instantiation Modes
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <h3 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>per_request (default)</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              A new controller instance is created for each incoming request. It supports the async context manager protocol (<code className="text-aquilia-500">__aenter__</code> / <code className="text-aquilia-500">__aexit__</code>) for request-level resources (e.g. transactions).
            </p>
          </div>
          <div className="space-y-2">
            <h3 className={`font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>singleton</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              A single instance is shared across all requests and lives for the entire server lifespan. Stateful startup and shutdown lifecycle hooks are executed in this mode only.
            </p>
          </div>
        </div>
      </section>

      {/* In This Section */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>In This Section</h2>
        <div className="flex flex-col gap-2">
          <Link to="/docs/controllers/decorators" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → Route Decorators: GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, WS
          </Link>
          <Link to="/docs/controllers/request-ctx" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → RequestCtx: The request context object and its properties
          </Link>
          <Link to="/docs/controllers/factory" className={`text-sm font-medium ${isDark ? 'text-aquilia-400 hover:text-aquilia-300' : 'text-aquilia-600 hover:text-aquilia-500'}`}>
            → ControllerFactory: How controllers are instantiated with DI
          </Link>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}