import { useState } from 'react'
import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import {
  Eye,
  Settings,
  ArrowRight,
  ShieldAlert,
  Cpu,
  Download,
  Zap,
  Lock,
  Play
} from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ControllersOpenAPI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const [activeConfigTab, setActiveConfigTab] = useState<'basic' | 'paths' | 'features' | 'mock' | 'security'>('basic')

  const sectionClass = "mb-20 scroll-mt-24"
  const h2Class = `text-3xl font-bold tracking-tight mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const pClass = `mb-6 text-base leading-relaxed ${isDark ? 'text-zinc-400' : 'text-gray-600'}`

  return (
    <div className="max-w-5xl mx-auto pb-24 px-4 sm:px-6">
      {/* Premium Header */}
      <div className="relative mb-16 pt-8 pb-12 overflow-hidden border-b border-zinc-200/80 dark:border-zinc-800/80">
        <div className="absolute top-0 right-0 -w-96 -h-96 bg-aquilia-500/5 rounded-full blur-3xl -z-10 animate-pulse duration-[8000ms]" />

        <div className="flex items-center gap-4 mb-6">
          <div className="w-12 h-12 rounded-2xl bg-aquilia-500 flex items-center justify-center shadow-lg shadow-aquilia-500/20">
            <Eye className="w-6 h-6 text-white" />
          </div>
          <div>
            <h1 className={`text-5xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
              Specula API Observatory
            </h1>
          </div>
        </div>

        <p className={`text-xl leading-relaxed max-w-4xl font-light ${isDark ? 'text-zinc-300' : 'text-gray-700'}`}>
          Specula is Aquilia's compiler-integrated API Observatory and schema compilation engine. It replaces legacy, static OpenAPI wrappers with a dynamic, metadata-enriched, introspective ASGI dashboard that exposes versions, routes, schemas, and live updates.
        </p>
      </div>

      {/* Clean Showcase Image */}
      <div className="relative mb-20 overflow-hidden rounded-2xl shadow-xl border border-zinc-200 dark:border-zinc-800">
        <img
          src="/specula_showcase.png"
          alt="Specular Observatory Dashboard Showcase"
          className="w-full h-auto object-cover"
          loading="eager"
        />
      </div>

      {/* Overview - Premium Left-Accent Layout */}
      <section className={sectionClass}>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="flex flex-col gap-3 py-4 border-l-2 border-aquilia-500/30 pl-6">
            <div className="w-10 h-10 rounded-xl bg-aquilia-500/10 flex items-center justify-center text-aquilia-400">
              <Cpu className="w-5 h-5" />
            </div>
            <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Spec Compilation</h3>
            <p className={`text-sm ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
              Processes compiled routing topologies, type annotations, and clearance constraints directly from memory without code scanners.
            </p>
          </div>
          <div className="flex flex-col gap-3 py-4 border-l-2 border-blue-500/30 pl-6">
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 flex items-center justify-center text-blue-400">
              <Zap className="w-5 h-5" />
            </div>
            <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Hot-Reload Streams</h3>
            <p className={`text-sm ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
              Uses built-in Server-Sent Events (SSE) to push instant route updates to the Observatory UI during local development.
            </p>
          </div>
          <div className="flex flex-col gap-3 py-4 border-l-2 border-purple-500/30 pl-6">
            <div className="w-10 h-10 rounded-xl bg-purple-500/10 flex items-center justify-center text-purple-400">
              <Play className="w-5 h-5" />
            </div>
            <h3 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Mocking & Exports</h3>
            <p className={`text-sm ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
              Serves simulated payloads automatically from JSON schemas and exports clean Postman v2.1/Insomnia v4 catalogs.
            </p>
          </div>
        </div>
      </section>

      {/* Integration */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Settings className="w-6 h-6 text-aquilia-400" />
          Workspace Integration
        </h2>
        <p className={pClass}>
          Specula is registered as a typed integration in your application's <code className="font-mono text-aquilia-400">workspace.py</code>. By declaring it, the compilation phase automatically hooks routing and validation events.
        </p>

        <CodeBlock
          code={`from aquilia.workspace import Workspace
from aquilia.integrations import Integration

workspace = Workspace("payment-gateway")

# Register Specula Observatory Integration
workspace.integrate(Integration.specula(
    title="Payment Gateway API",
    version="2.1.0",
    ui_theme="dark",
    mock_server_enabled=True,
    spec_cache_ttl=120,
))`}
          language="python"
          filename="workspace.py"
        />

        <div className="my-8 border-l-4 border-amber-500 pl-6 py-2 flex items-start gap-4">
          <ShieldAlert className="w-5 h-5 text-amber-500 shrink-0 mt-0.5" />
          <div>
            <h4 className="text-sm font-bold text-amber-500 uppercase tracking-wider font-mono">Removal of Legacy OpenAPI</h4>
            <p className={`text-sm mt-1 leading-relaxed ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
              The legacy <code className="font-mono text-amber-500">OpenAPIIntegration</code> and its helper method <code className="font-mono text-amber-500">Integration.openapi(...)</code> have been completely removed. Change your configuration to use <code className="font-mono text-aquilia-400">Integration.specula(...)</code> instead.
            </p>
          </div>
        </div>
      </section>

      {/* Interactive Config tabs */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Settings className="w-6 h-6 text-aquilia-400" />
          Interactive Configuration Reference
        </h2>
        <p className={pClass}>
          Specula offers high-fidelity configuration. Select a category below to view the available attributes on <DocTerm id="specula.config">SpeculaConfig</DocTerm> / <DocTerm id="specula.integration">SpeculaIntegration</DocTerm>.
        </p>

        {/* Tab Controls */}
        <div className="flex flex-wrap gap-2 mb-6 border-b border-zinc-200 dark:border-zinc-800 pb-px">
          {[
            { id: 'basic', label: 'Info & Metadata' },
            { id: 'paths', label: 'URL Mapping' },
            { id: 'features', label: 'Feature Flags' },
            { id: 'mock', label: 'Mock Engine' },
            { id: 'security', label: 'Observatory Security' }
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveConfigTab(tab.id as any)}
              className={`px-4 py-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeConfigTab === tab.id
                  ? 'border-aquilia-500 text-aquilia-400 font-semibold'
                  : 'border-transparent text-zinc-500 hover:text-zinc-700 dark:hover:text-zinc-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content - Clean Borderless Spacing */}
        <div className="pt-6">
          {activeConfigTab === 'basic' && (
            <div>
              <h3 className="text-lg font-bold mb-4 text-zinc-800 dark:text-zinc-200">Info & Branding Configuration</h3>
              <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-6">
                Customize metadata variables visible on generated schemas, exports, and headers.
              </p>
              <div className="space-y-4">
                {[
                  { field: 'title', type: 'str', default: '"Aquilia API"', desc: 'The display title of your API catalog.' },
                  { field: 'version', type: 'str', default: '"1.0.0"', desc: 'Semantic version tag representing the current deployment.' },
                  { field: 'description', type: 'str', default: '""', desc: 'Markdown or plaintext description of the API endpoints.' },
                  { field: 'ui_theme', type: '"auto" | "light" | "dark"', default: '"auto"', desc: 'Specifies the default dashboard styling theme.' },
                  { field: 'ui_primary_color', type: 'str', default: '"#22c55e"', desc: 'Hex color value used as the Observatory UI accent color.' }
                ].map((item, idx) => (
                  <div key={idx} className="flex flex-col sm:flex-row sm:items-baseline gap-2 border-b border-zinc-150 dark:border-zinc-800/30 pb-3 last:border-0 last:pb-0">
                    <span className="font-mono text-xs font-bold text-aquilia-400 sm:w-44 shrink-0">{item.field}</span>
                    <span className="font-mono text-xs text-zinc-500 dark:text-zinc-500 w-36 shrink-0">Type: {item.type}</span>
                    <div className="flex-grow">
                      <p className="text-sm text-zinc-700 dark:text-zinc-350">{item.desc}</p>
                      <p className="text-xs font-mono text-zinc-500 mt-1">Default: {item.default}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeConfigTab === 'paths' && (
            <div>
              <h3 className="text-lg font-bold mb-4 text-zinc-800 dark:text-zinc-200">Endpoint Path Mappings</h3>
              <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-6">
                Change the default ASGI paths mapped by Specula. Avoid trailing slashes; parameters are registered dynamically.
              </p>
              <div className="space-y-4">
                {[
                  { field: 'ui_path', default: '"/specula"', desc: 'The HTML browser console path for developers.' },
                  { field: 'json_path', default: '"/specula/spec.json"', desc: 'Raw OpenAPI 3.1.0 JSON schema endpoint.' },
                  { field: 'yaml_path', default: '"/specula/spec.yaml"', desc: 'Raw OpenAPI 3.1.0 YAML spec endpoint.' },
                  { field: 'stream_path', default: '"/specula/stream"', desc: 'Server-Sent Events endpoint pushing real-time routes.' },
                  { field: 'mock_path', default: '"/specula/mock"', desc: 'Mock server mount path.' },
                  { field: 'versions_path', default: '"/specula/versions"', desc: 'Version index and spec router.' }
                ].map((item, idx) => (
                  <div key={idx} className="flex flex-col sm:flex-row sm:items-baseline gap-2 border-b border-zinc-150 dark:border-zinc-800/30 pb-3 last:border-0 last:pb-0">
                    <span className="font-mono text-xs font-bold text-aquilia-400 sm:w-44 shrink-0">{item.field}</span>
                    <div className="flex-grow">
                      <p className="text-sm text-zinc-700 dark:text-zinc-350">{item.desc}</p>
                      <p className="text-xs font-mono text-zinc-500 mt-1">Default: {item.default}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeConfigTab === 'features' && (
            <div>
              <h3 className="text-lg font-bold mb-4 text-zinc-800 dark:text-zinc-200">Feature Toggle Flags</h3>
              <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-6">
                Control which attributes are extracted, generated, and rendered in the specification.
              </p>
              <div className="space-y-4">
                {[
                  { field: 'include_internal', default: 'False', desc: 'Include routes prefix-matched with "/_" in the API spec.' },
                  { field: 'detect_security', default: 'True', desc: 'Scan pipeline guards and decorators for security schemes (bearer, oauth2).' },
                  { field: 'infer_request_body', default: 'True', desc: 'Analyze contracts and parameter type hints to generate body schemas.' },
                  { field: 'infer_responses', default: 'True', desc: 'Examine return types and response methods to determine output models.' },
                  { field: 'include_effect_annotations', default: 'True', desc: 'Include x-specula-effects vendor extensions on operations.' },
                  { field: 'include_pipeline_annotations', default: 'True', desc: 'Include x-specula-pipeline guards sequence on operations.' }
                ].map((item, idx) => (
                  <div key={idx} className="flex flex-col sm:flex-row sm:items-baseline gap-2 border-b border-zinc-150 dark:border-zinc-800/30 pb-3 last:border-0 last:pb-0">
                    <span className="font-mono text-xs font-bold text-aquilia-400 sm:w-44 shrink-0">{item.field}</span>
                    <span className="font-mono text-xs text-zinc-500 dark:text-zinc-500 w-24 shrink-0">Type: bool</span>
                    <div className="flex-grow">
                      <p className="text-sm text-zinc-700 dark:text-zinc-350">{item.desc}</p>
                      <p className="text-xs font-mono text-zinc-500 mt-1">Default: {item.default}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeConfigTab === 'mock' && (
            <div>
              <h3 className="text-lg font-bold mb-4 text-zinc-800 dark:text-zinc-200">Mock Server Engine</h3>
              <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-6">
                Specula runs an interactive mock server. Connect clients directly to develop frontends before writing controller logic.
              </p>
              <div className="space-y-4">
                {[
                  { field: 'mock_server_enabled', type: 'bool', default: 'False', desc: 'Master toggle to enable the /specula/mock endpoint.' },
                  { field: 'mock_max_depth', type: 'int', default: '4', desc: 'Maximum JSON Schema recursion depth for synthesizing mock data objects.' }
                ].map((item, idx) => (
                  <div key={idx} className="flex flex-col sm:flex-row sm:items-baseline gap-2 border-b border-zinc-150 dark:border-zinc-800/30 pb-3 last:border-0 last:pb-0">
                    <span className="font-mono text-xs font-bold text-aquilia-400 sm:w-44 shrink-0">{item.field}</span>
                    <span className="font-mono text-xs text-zinc-500 dark:text-zinc-500 w-24 shrink-0">Type: {item.type}</span>
                    <div className="flex-grow">
                      <p className="text-sm text-zinc-700 dark:text-zinc-350">{item.desc}</p>
                      <p className="text-xs font-mono text-zinc-500 mt-1">Default: {item.default}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeConfigTab === 'security' && (
            <div>
              <h3 className="text-lg font-bold mb-4 text-zinc-800 dark:text-zinc-200">Observatory Access Security</h3>
              <p className="text-sm text-zinc-500 dark:text-zinc-400 mb-6">
                Lock down the Specula UI console on production environments using RBAC roles.
              </p>
              <div className="space-y-4">
                {[
                  { field: 'docs_auth_required', type: 'bool', default: 'False', desc: 'If True, visiting /specula requires credentials verification.' },
                  { field: 'docs_roles', type: 'list[str]', default: 'field(default_factory=list)', desc: 'List of clearance roles allowed to inspect the observatory. e.g., ["admin", "developer"].' }
                ].map((item, idx) => (
                  <div key={idx} className="flex flex-col sm:flex-row sm:items-baseline gap-2 border-b border-zinc-150 dark:border-zinc-800/30 pb-3 last:border-0 last:pb-0">
                    <span className="font-mono text-xs font-bold text-aquilia-400 sm:w-44 shrink-0">{item.field}</span>
                    <span className="font-mono text-xs text-zinc-500 dark:text-zinc-500 w-36 shrink-0">Type: {item.type}</span>
                    <div className="flex-grow">
                      <p className="text-sm text-zinc-700 dark:text-zinc-350">{item.desc}</p>
                      <p className="text-xs font-mono text-zinc-500 mt-1">Default: {item.default}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </section>

      {/* Schema Introspection Engine */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Cpu className="w-6 h-6 text-aquilia-400" />
          Spec Inference & Introspection
        </h2>
        <p className={pClass}>
          The <DocTerm id="specula.builder">SpeculaBuilder</DocTerm> compiles dynamic endpoints at startup through multiple layers of static and runtime analysis:
        </p>

        <div className="space-y-16">
          {/* Parameter parsing - Stacked Vertically */}
          <div className="flex flex-col gap-4">
            <div>
              <h3 className="text-lg font-bold flex items-center gap-2 mb-2 text-zinc-800 dark:text-zinc-200">
                <span className="w-6 h-6 rounded bg-aquilia-500/10 text-aquilia-400 flex items-center justify-center text-xs font-bold font-mono">1</span>
                Parameter Extraction
              </h3>
              <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
                URL path variables parsed by the router pattern (e.g. <code className="font-mono text-aquilia-400">/users/&lt;id:int&gt;</code>) are mapped directly to OpenAPI path parameters. Query parameters and custom headers are extracted from type hints and Annotated metadata.
              </p>
            </div>
            <div>
              <CodeBlock
                code={`# Extracted parameters:
# - id: integer (path, required)
# - active: boolean (query, optional, default: True)
# - x_client: string (header, required)
@GET("/users/<id:int>")
async def get_user(
    self,
    id: int,
    active: bool = True,
    x_client: Annotated[str, Header()] = ""
): ...`}
                language="python"
              />
            </div>
          </div>

          {/* Request body inference - Stacked Vertically */}
          <div className="flex flex-col gap-4">
            <div>
              <h3 className="text-lg font-bold flex items-center gap-2 mb-2 text-zinc-800 dark:text-zinc-200">
                <span className="w-6 h-6 rounded bg-aquilia-500/10 text-aquilia-400 flex items-center justify-center text-xs font-bold font-mono">2</span>
                Request Body Extraction
              </h3>
              <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
                Specula resolves request payloads through a 4-tier strategy:
              </p>
              <ul className="list-disc pl-5 mt-2 space-y-1.5 text-xs text-zinc-500 dark:text-zinc-400">
                <li><code className="font-mono text-aquilia-400">request_contract</code> argument on decorators.</li>
                <li>Method arguments annotated with a <code className="font-mono text-aquilia-400">Contract</code> type.</li>
                <li>Google-style docstring blocks: <code className="font-mono">Body: {"{...}"}</code></li>
                <li>Static code analysis searching for <code className="font-mono">await ctx.json()</code> or <code className="font-mono">await ctx.form()</code> calls.</li>
              </ul>
            </div>
            <div>
              <CodeBlock
                code={`# Inferred as application/json request body containing ProductCreate schema
@POST("/products")
async def create_product(
    self,
    ctx: RequestCtx,
    data: ProductCreateContract
): ...`}
                language="python"
              />
            </div>
          </div>

          {/* Response Resolution - Stacked Vertically */}
          <div className="flex flex-col gap-4">
            <div>
              <h3 className="text-lg font-bold flex items-center gap-2 mb-2 text-zinc-800 dark:text-zinc-200">
                <span className="w-6 h-6 rounded bg-aquilia-500/10 text-aquilia-400 flex items-center justify-center text-xs font-bold font-mono">3</span>
                Response Shapes Resolution
              </h3>
              <p className={`text-sm leading-relaxed ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
                Success status codes, content-types, and body structures are mapped from the decorator's <code className="font-mono text-aquilia-400">response_model</code> or <code className="font-mono text-aquilia-400">response_contract</code> parameters.
              </p>
              <p className={`text-xs mt-2 leading-relaxed ${isDark ? 'text-zinc-500' : 'text-gray-500'}`}>
                If omitted, the engine scans the handler source code for <code className="font-mono">Response.json()</code> (JSON content), <code className="font-mono">Response.html()</code> / renderers (HTML content), and <code className="font-mono">SSEResponse</code> (text/event-stream content).
              </p>
            </div>
            <div>
              <CodeBlock
                code={`# Inferred as 201 response containing product payload
@POST(
    "/products",
    response_model=ProductContract,
    status_code=201
)
async def create_product(self, ctx: RequestCtx):
    ...`}
                language="python"
              />
            </div>
          </div>
        </div>
      </section>

      {/* Security and clearance - Premium Borderless Left-Accent Column */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <ShieldAlert className="w-6 h-6 text-aquilia-400" />
          Security Schemes & Clearance Detection
        </h2>
        <p className={pClass}>
          Specula automatically detects security schemas from authentication decorators, custom pipeline guards, and role clearances:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-8">
          <div className="py-4 border-l-2 border-aquilia-500/30 pl-6">
            <h4 className={`text-base font-bold flex items-center gap-2 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <Lock className="w-4 h-4 text-aquilia-400" />
              Auth Guards & Decorators
            </h4>
            <p className={`text-sm leading-relaxed mb-4 ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
              Methods decorated with <code className="font-mono text-aquilia-400">@authenticated</code> or carrying auth-related guards in their pipeline (e.g. <code className="font-mono">ApiKeyGuard</code>, <code className="font-mono">SessionGuard</code>) are mapped with appropriate security schemes.
            </p>
            <CodeBlock
              code={`# Auto-registers bearerAuth security requirement
@GET("/profile")
@authenticated
async def get_profile(self, ctx: RequestCtx):
    ...`}
              language="python"
            />
          </div>

          <div className="py-4 border-l-2 border-blue-500/30 pl-6">
            <h4 className={`text-base font-bold flex items-center gap-2 mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <Zap className="w-4 h-4 text-blue-400" />
              Clearance System Mapping
            </h4>
            <p className={`text-sm leading-relaxed mb-4 ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
              Specula detects controller-level and route-level clearances. It exposes AccessLevel values and entitlements inside custom vendor extension tags (<code className="font-mono text-aquilia-400">x-specula-security</code>).
            </p>
            <CodeBlock
              code={`# Exposes clearance hierarchy inside spec metadata
class AdminController(Controller):
    clearance = Clearance(level=AccessLevel.INTERNAL)

    @GET("/reports")
    async def get_reports(self, ctx):
        ...`}
              language="python"
            />
          </div>
        </div>
      </section>

      {/* Mocking and exports */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Download className="w-6 h-6 text-aquilia-400" />
          Mocking, SSE, & Integration Exports
        </h2>
        <p className={pClass}>
          Specula is designed to make frontend integration quick and reliable. It goes beyond serving JSON to provide operational utility.
        </p>

        <div className="space-y-8">
          <div className="flex items-start gap-4">
            <div className="w-8 h-8 rounded-lg bg-aquilia-500/10 text-aquilia-400 flex items-center justify-center shrink-0 mt-1 font-bold font-mono text-xs">
              M
            </div>
            <div>
              <h4 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                Mock Server (<code className="font-mono">/specula/mock</code>)
              </h4>
              <p className={`text-sm leading-relaxed mt-1 ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
                When <code className="font-mono text-aquilia-400">mock_server_enabled</code> is active, Specula hosts a dynamic mocking endpoint. Calling it with any documented path returns synthesized mock responses matching the JSON Schema definitions, complete with mock values resolved up to <code className="font-mono">mock_max_depth</code>.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="w-8 h-8 rounded-lg bg-blue-500/10 text-blue-400 flex items-center justify-center shrink-0 mt-1 font-bold font-mono text-xs">
              S
            </div>
            <div>
              <h4 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                Live Refresh SSE Stream (<code className="font-mono">/specula/stream</code>)
              </h4>
              <p className={`text-sm leading-relaxed mt-1 ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
                Specula handles hot reloading. It maintains an active Server-Sent Events channel. When modules reload, a spec invalidation event is pushed to the client browser, forcing the Observatory dashboard to rebuild dynamically without hard refreshes.
              </p>
            </div>
          </div>

          <div className="flex items-start gap-4">
            <div className="w-8 h-8 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center shrink-0 mt-1 font-bold font-mono text-xs">
              E
            </div>
            <div>
              <h4 className={`text-lg font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>
                Postman & Insomnia Exports
              </h4>
              <p className={`text-sm leading-relaxed mt-1 ${isDark ? 'text-zinc-400' : 'text-gray-600'}`}>
                Download configured collection assets directly.
              </p>
              <ul className="list-disc pl-5 mt-2 space-y-1 text-xs text-zinc-500 dark:text-zinc-400">
                <li><code className="font-mono text-aquilia-400">/specula/export/postman</code> yields a complete Postman Collection v2.1.</li>
                <li><code className="font-mono text-aquilia-400">/specula/export/insomnia</code> yields a clean Insomnia v4 export file.</li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-zinc-200 dark:border-zinc-800">
        <Link to="/docs/controllers/router" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <ArrowRight className="w-4 h-4 rotate-180" />
          <span>ControllerRouter</span>
        </Link>
        <Link to="/docs/config/overview" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors">
          <span>Configuration Overview</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}