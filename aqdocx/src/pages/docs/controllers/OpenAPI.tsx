import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { FileText, Layers, Settings, ArrowRight, ShieldAlert, Cpu } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ControllersOpenAPI() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = "mb-16 scroll-mt-24"
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`
  const listClass = "space-y-4 pl-5 list-decimal"
  const itemClass = `text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`

  return (
    <div className="max-w-4xl mx-auto pb-20">
      {/* Header */}
      <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center">
            <FileText className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                OpenAPI Generation
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.controller.openapi — Production-grade spec extraction from source code</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia features a compiler-integrated <strong>OpenAPI 3.1.0</strong> engine that extracts schemas, parameter bindings, security schemes, and response shapes directly from your <DocTerm id="controllers.controller">Controller</DocTerm> classes and python annotations, serving them via interactive Swagger UI and ReDoc pages.
        </p>
      </div>

      {/* Workspace Integration */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Settings className="w-5 h-5 text-aquilia-400" />
          Workspace-Level Integration
        </h2>
        <p className={pClass}>
          OpenAPI config is integrated into your application at the workspace level inside your <code className="text-aquilia-500 font-mono">workspace.py</code>:
        </p>

        <CodeBlock
          code={`from aquilia.workspace import Workspace
from aquilia.integrations import OpenAPIIntegration

workspace = Workspace("my-app")

# New standard style: Instantiate OpenAPIIntegration directly
workspace.integrate(OpenAPIIntegration(
    title="My Store API",
    version="2.0.0",
    docs_path="/apidocs",
    swagger_ui_theme="dark"
))`}
          language="python"
          filename="workspace.py"
          highlightLines={[2, 7, 8, 9, 10, 11, 12]}
        />

        {/* Configuration Style Note */}
        <div className="pl-4 border-l-2 border-amber-500/80 my-6">
          <h4 className="font-mono font-bold text-xs uppercase tracking-wider text-amber-500 mb-1">Configuration Note</h4>
          <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            The legacy helper method <code className="text-aquilia-500 font-mono">Integration.openapi(**kwargs)</code> is fully supported as an alternative style. However, importing and configuring <code className="text-aquilia-500 font-mono">OpenAPIIntegration</code> directly is preferred as it enables static type checks and parameter autocomplete in IDEs.
          </p>
        </div>
      </section>

      {/* Configuration details */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Settings className="w-5 h-5 text-aquilia-400" />
          OpenAPI Configuration Options
        </h2>
        <p className={pClass}>
          OpenAPI generation is enabled by default and configured using the <DocTerm id="openapi.config">OpenAPIConfig</DocTerm> class. You can tune paths, themes, info metadata, and server endpoints.
        </p>

        <CodeBlock
          code={`from dataclasses import dataclass, field
from typing import Any

@dataclass
class OpenAPIConfig:
    # Metadata info
    title: str = "Aquilia API"
    version: str = "1.0.0"
    description: str = ""
    terms_of_service: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_url: str = ""
    license_name: str = ""
    license_url: str = ""

    # Target routes
    docs_path: str = "/docs"              # Swagger UI HTML path
    openapi_json_path: str = "/openapi.json"  # Raw JSON specification path
    redoc_path: str = "/redoc"            # ReDoc HTML path

    # Servers list (defaults to [{"url": "/", "description": "Current server"}])
    servers: list[dict[str, str]] = field(default_factory=list)

    # Feature flags
    include_internal: bool = False        # Whether to include /_internal routes
    group_by_module: bool = True          # Group endpoint tags by manifest module
    infer_request_body: bool = True       # Scan handlers for body details
    infer_responses: bool = True          # Inspect return types and response methods
    detect_security: bool = True          # Scan pipeline guards for security schemes

    # Custom UI options
    swagger_ui_theme: str = ""            # Theme style: "dark" or empty (light)
    swagger_ui_config: dict[str, Any] = field(default_factory=field)
    enabled: bool = True                  # Master toggle for OpenAPI endpoints`}
          language="python"
          filename="openapi_config.py"
          highlightLines={[7, 8, 18, 19, 20, 29, 30, 31, 34, 36]}
        />
      </section>

      {/* Type Mapping */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Python to JSON Schema Mapping
        </h2>
        <p className={pClass}>
          The generator introspects type hints on routing arguments, request models, and return annotations, casting standard Python types to their JSON Schema equivalents.
        </p>

        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 text-left">
                <th className="px-4 py-3 font-semibold">Python Type Annotation</th>
                <th className="px-4 py-3 font-semibold">JSON Schema Equivalent</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-150 text-gray-700'}`}>
              {[
                ['str', '{"type": "string"}'],
                ['int', '{"type": "integer"}'],
                ['float', '{"type": "number", "format": "double"}'],
                ['bool', '{"type": "boolean"}'],
                ['bytes', '{"type": "string", "format": "binary"}'],
                ['None', '{"type": "null"}'],
                ['Union[X, None] / Optional[X]', '{"type": X_type, "nullable": true}'],
                ['list[X] / List[X]', '{"type": "array", "items": {X_schema}}'],
                ['dict[str, X] / Dict[str, X]', '{"type": "object", "additionalProperties": {X_schema}}'],
                ['tuple[X, Y]', '{"type": "array", "prefixItems": [{X_schema}, {Y_schema}], "minItems": 2, "maxItems": 2}'],
                ['set[X]', '{"type": "array", "items": {X_schema}, "uniqueItems": true}'],
                ['dataclass / class (with fields)', '{"$ref": "#/components/schemas/ClassName"}']
              ].map(([python, json], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{python}</td>
                  <td className="px-4 py-2 font-mono text-xs">{json}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Inference Logic */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Cpu className="w-5 h-5 text-aquilia-400" />
          Spec Inference Strategies
        </h2>
        <p className={pClass}>
          To provide complete specifications with minimal boilerplates, the <DocTerm id="openapi.generator">OpenAPIGenerator</DocTerm> performs multi-layered static analysis on route handler functions:
        </p>

        <h3 className={h3Class}>1. Parameter Extraction</h3>
        <p className={pClass}>
          Path variables declared in route patterns (e.g., <code className="text-aquilia-500">/users/&lt;id:int&gt;</code>) are auto-converted to OpenAPI path parameters. Query parameters and headers are inferred from handler metadata annotations and parameters:
        </p>
        <CodeBlock
          code={`# Inferred as: path param 'id' (integer), query param 'q' (optional string), header 'X-Token' (string)
@GET("/users/<id:int>")
async def get_user(self, id: int, q: str | None = None, x_token: Annotated[str, Header()] = ""):
    ...`}
          language="python"
          highlightLines={[2, 3]}
        />

        <h3 className={h3Class}>2. Request Body Inference</h3>
        <p className={pClass}>
          For write requests (<code className="text-aquilia-500">POST</code>, <code className="text-aquilia-500">PUT</code>, <code className="text-aquilia-500">PATCH</code>), the generator scans parameters using a 4-tier strategy:
        </p>
        <ol className={listClass}>
          <li className={itemClass}>
            <strong>Parameter Metadata:</strong> Inspects route annotations where the parameter source is explicitly marked as <code className="text-aquilia-500">body</code>.
          </li>
          <li className={itemClass}>
            <strong>Annotated Param:</strong> Checks for parameters declared as <code className="text-aquilia-500">Annotated[MyBlueprint, Body()]</code>.
          </li>
          <li className={itemClass}>
            <strong>Docstring Schema:</strong> Parses the handler docstring for a JSON example block, e.g. <code className="text-aquilia-500">{"Body: {\"username\": \"admin\", \"age\": 30}"}</code>. Types are statically inferred from values.
          </li>
          <li className={itemClass}>
            <strong>Code Introspection:</strong> Checks source code lines for calls to <code className="text-aquilia-500">await ctx.json()</code> (yielding a generic JSON object body) or <code className="text-aquilia-500">await ctx.form()</code> (yielding an urlencoded form body).
          </li>
        </ol>

        <h3 className={h3Class}>3. Response Resolution</h3>
        <p className={pClass}>
          Success status codes and response schemas are generated based on route metadata:
        </p>
        <CodeBlock
          code={`# Will generate a 201 response containing UserBlueprint schema in components/schemas
@POST("/users", response_model=UserBlueprint, status_code=201)
async def create_user(self, ctx: RequestCtx):
    ...`}
          language="python"
          highlightLines={[2]}
        />
        <p className={pClass}>
          If no <code className="text-aquilia-500">response_model</code> is defined, the generator analyzes the handler's python code:
        </p>
        <ul className="list-disc pl-5 space-y-2 text-sm text-gray-500 dark:text-gray-400">
          <li>Detecting <code className="text-aquilia-500">Response.json(...)</code> infers <code className="text-aquilia-500">application/json</code> response.</li>
          <li>Detecting <code className="text-aquilia-500">Response.html(...)</code> or template render calls infers <code className="text-aquilia-500">text/html</code> response.</li>
          <li>Detecting <code className="text-aquilia-500">Response.text(...)</code> infers <code className="text-aquilia-500">text/plain</code> response.</li>
        </ul>
      </section>

      {/* Security Schemes */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <ShieldAlert className="w-5 h-5 text-aquilia-400" />
          Security Schemes Detection
        </h2>
        <p className={pClass}>
          If <code className="text-aquilia-500">detect_security</code> is enabled, the generator scans the pipeline guards registered on your controllers or routes:
        </p>
        <div className="overflow-x-auto py-2 mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 text-left">
                <th className="px-4 py-3 font-semibold">Guard Class Name</th>
                <th className="px-4 py-3 font-semibold">Inferred Security Scheme</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-150 text-gray-700'}`}>
              {[
                ['AuthGuard / Auth', 'HTTP Bearer (JWT) Authentication'],
                ['ApiKeyGuard / ApiKey', 'X-API-Key Header Authorization'],
                ['OAuth2Guard / OAuth2', 'OAuth2 Authorization Code flow'],
                ['RoleGuard / ScopeGuard', 'Attaches required roles/scopes to the Bearer scheme']
              ].map(([guard, scheme], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{guard}</td>
                  <td className="px-4 py-2 text-xs">{scheme}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <CodeBlock
          code={`# Automatically configures BearerAuth requirements for all routes in this controller
class ProfileController(Controller):
    pipeline = [AuthGuard()]

    @GET("/profile")
    async def get_profile(self, ctx: RequestCtx):
        ...`}
          language="python"
          highlightLines={[3, 5]}
        />
      </section>

      {/* HTML UIs */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          Swagger UI & ReDoc
        </h2>
        <p className={pClass}>
          The generated specification is served at custom paths, rendering responsive documentation playgrounds:
        </p>
        <ul className="list-disc pl-5 space-y-4 text-sm text-gray-500 dark:text-gray-400">
          <li>
            <strong>Swagger UI (<code className="text-aquilia-500">/docs</code>):</strong>
            <br />
            Enables developers to inspect schema properties and test endpoints interactively by submitting API requests directly from their browser. In dark mode, it automatically applies color filters to avoid light-flash discomfort. See <DocTerm id="openapi.swagger_html">generate_swagger_html</DocTerm>.
          </li>
          <li>
            <strong>ReDoc (<code className="text-aquilia-500">/redoc</code>):</strong>
            <br />
            Provides a beautiful, structured 3-pane layout optimized for reference manuals and large API catalogs. See <DocTerm id="openapi.redoc_html">generate_redoc_html</DocTerm>.
          </li>
        </ul>
      </section>

      {/* Manual Generation */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Cpu className="w-5 h-5 text-aquilia-400" />
          Manual Spec Generation
        </h2>
        <p className={pClass}>
          You can generate the OpenAPI specification dictionary manually from your compiled <DocTerm id="routing.router">ControllerRouter</DocTerm>:
        </p>
        <CodeBlock
          code={`from aquilia.controller.openapi import OpenAPIGenerator, OpenAPIConfig
from aquilia.controller.router import ControllerRouter

# Setup router
router = ControllerRouter()
# ... register controllers

# Generate spec dict
config = OpenAPIConfig(
    title="Custom API",
    version="2.1.0",
    swagger_ui_theme="dark"
)
generator = OpenAPIGenerator(config=config)
spec_dict = generator.generate(router)`}
          language="python"
          filename="manual_spec.py"
          highlightLines={[9, 10, 11, 12, 13, 14, 15]}
        />
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
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