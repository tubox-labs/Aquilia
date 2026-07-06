import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Tag, Layers, Zap, Code, ArrowRight, List } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function ControllersDecorators() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-12 pb-16">
      {/* Header */}
      <div>
        <div className="flex items-center gap-3 mb-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <Tag className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Route Decorators
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.controller.decorators — HTTP method decorators</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Route decorators attach metadata to controller methods without import-time side effects.
          The metadata is later extracted by the <code>ControllerCompiler</code> to generate compiled routes.
        </p>
      </div>

      {/* RouteDecorator base class */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Code className="w-5 h-5 text-aquilia-400" />
          RouteDecorator Base
        </h2>

        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          All HTTP method decorators (<code>GET</code>, <code>POST</code>, etc.) inherit from <code>RouteDecorator</code>:
        </p>

        <CodeBlock
          code={`class RouteDecorator:
    def __init__(
        self,
        path: Optional[str] = None,
        *,
        # ── Pipeline & Middleware ─────────────────────────────────
        pipeline: Optional[List[Any]] = None,

        # ── OpenAPI Documentation ─────────────────────────────────
        summary: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        deprecated: bool = False,
        response_model: Optional[type] = None,
        status_code: int = 200,

        # ── Blueprint Casting / Sealing ───────────────────────────
        request_blueprint: Optional[type] = None,
        response_blueprint: Optional[type] = None,

        # ── Filtering, Search, Ordering ───────────────────────────
        filterset_class: Optional[type] = None,
        filterset_fields: Optional[Union[List[str], Any]] = None,
        search_fields: Optional[List[str]] = None,
        ordering_fields: Optional[List[str]] = None,

        # ── Pagination ────────────────────────────────────────────
        pagination_class: Optional[type] = None,

        # ── Content Negotiation ───────────────────────────────────
        renderer_classes: Optional[List[Any]] = None,
    ): ...`}
          language="python"
        />
      </section>

      {/* Full parameter reference */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Parameter Reference
        </h2>

        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left px-4 py-3 font-semibold">Parameter</th>
                <th className="text-left px-4 py-3 font-semibold">Type</th>
                <th className="text-left px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                ['path', 'Optional[str]', 'URL path template. Supports «name:type» params.'],
                ['pipeline', 'Optional[List[Any]]', 'Flow pipeline nodes applied to this route handler.'],
                ['summary', 'Optional[str]', 'OpenAPI summary.'],
                ['description', 'Optional[str]', 'OpenAPI description.'],
                ['tags', 'Optional[List[str]]', 'Route OpenAPI tags.'],
                ['deprecated', 'bool', 'Marks route as deprecated in the OpenAPI spec.'],
                ['response_model', 'Optional[type]', 'Expected response model type.'],
                ['status_code', 'int', 'Default response status code. Defaults to 200.'],
                ['request_blueprint', 'Optional[type]', 'Blueprint class for casting request body.'],
                ['response_blueprint', 'Optional[type]', 'Blueprint class for molding response payload.'],
                ['filterset_class', 'Optional[type]', 'FilterSet subclass for query filtering.'],
                ['filterset_fields', 'Optional[List[str] | Any]', 'List/dict shorthand for filters.'],
                ['search_fields', 'Optional[List[str]]', 'Searchable fields.'],
                ['ordering_fields', 'Optional[List[str]]', 'Sortable fields.'],
                ['pagination_class', 'Optional[type]', 'Pagination handler class.'],
                ['renderer_classes', 'Optional[List[Any]]', 'Content negotiator renderers.']
              ].map(([param, type_, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs whitespace-nowrap text-aquilia-500 font-semibold">{param}</td>
                  <td className="px-4 py-2 font-mono text-xs whitespace-nowrap">{type_}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* HTTP Method Decorators */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Zap className="w-5 h-5 text-aquilia-400" />
          HTTP Method Decorators
        </h2>

        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400">
                <th className="text-left px-4 py-3 font-semibold">Decorator</th>
                <th className="text-left px-4 py-3 font-semibold">Method</th>
                <th className="text-left px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-100 text-gray-700'}`}>
              {[
                ['@GET(path)', 'GET', 'Retrieve resources.'],
                ['@POST(path)', 'POST', 'Create resources.'],
                ['@PUT(path)', 'PUT', 'Full replacement.'],
                ['@PATCH(path)', 'PATCH', 'Partial update.'],
                ['@DELETE(path)', 'DELETE', 'Delete resources.'],
                ['@HEAD(path)', 'HEAD', 'Metadata verification.'],
                ['@OPTIONS(path)', 'OPTIONS', 'CORS / capabilities.'],
                ['@WS(path)', 'WS', 'WebSocket upgrades.']
              ].map(([dec, method, use], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{dec}</td>
                  <td className="px-4 py-2 font-mono text-xs font-bold">{method}</td>
                  <td className="px-4 py-2 text-xs">{use}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Generic route() */}
      <section className="space-y-4">
        <h2 className={`text-2xl font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <List className="w-5 h-5 text-aquilia-400" />
          Generic route() Function
        </h2>

        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          For multi-method routes or dynamic method binding, use the <code>route()</code> function:
        </p>

        <CodeBlock
          code={`from aquilia.controller.decorators import route

class ItemsController(Controller):
    @route(["GET", "POST"], "/bulk")
    async def bulk(self, ctx: RequestCtx) -> Response:
        if ctx.method == "GET":
            return Response.json({"items": []})
        data = await ctx.json()
        return Response.json({"created": len(data)}, status=201)`}
          language="python"
        />
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/controllers/overview" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowRight className="w-4 h-4 rotate-180" />
          <span>Controllers Overview</span>
        </Link>
        <Link to="/docs/controllers/request-ctx" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <span>RequestCtx</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}