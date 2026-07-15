import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Sliders, Cpu, Shield, BookOpen, Terminal, AlertCircle, ArrowRight, XCircle, CheckCircle2, AlertTriangle } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function ControllersAttributes() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="relative max-w-4xl mx-auto space-y-16 pb-16">
      {/* Decorative Gradient Glows for Premium Vibe (No Box Layout) */}
      <div className="absolute top-0 -left-20 w-72 h-72 bg-aquilia-500/10 dark:bg-aquilia-500/5 rounded-full blur-3xl -z-10 pointer-events-none" />
      <div className="absolute top-1/3 -right-20 w-80 h-80 bg-aquilia-500/10 dark:bg-aquilia-500/5 rounded-full blur-3xl -z-10 pointer-events-none" />

      {/* Header Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-aquilia-500/30 to-aquilia-500/10 flex items-center justify-center border border-aquilia-500/20">
            <Sliders className="w-5 h-5 text-aquilia-400" />
          </div>
          <div>
            <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
              <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
                Controller Attributes
                <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
              </span>
            </h1>
            <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>aquilia.controller.attrs — Declarative class-level metadata builder</p>
          </div>
        </div>

        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The <DocTerm id="controller.attributes">Attributes</DocTerm> class is a fluent, chainable builder used to configure class-level metadata on <DocTerm id="controller.controller">Controller</DocTerm> subclasses. By leveraging Python's descriptor protocol, it guarantees compile-time validation and applies configurations dynamically at class-definition time with zero request-time runtime overhead.
        </p>
      </div>

      {/* Old Style vs New Style (Deprecation Warning) */}
      <section className="space-y-6">
        <div className="flex items-center gap-2">
          <AlertCircle className="w-5 h-5 text-amber-500 animate-pulse" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Old Style vs. New Style</h2>
        </div>

        <div className={`p-5 rounded-xl border-l-4 border-amber-500 ${isDark ? 'bg-amber-950/20 text-gray-300' : 'bg-amber-50 text-gray-700'}`}>
          <div className="flex items-start gap-3">
            <div>
              <h5 className="font-semibold text-sm text-amber-600 dark:text-amber-400 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-amber-500" />
                Deprecation Warning
              </h5>
              <p className="text-xs mt-1 leading-relaxed">
                Directly overriding class attributes (e.g. <code className="text-aquilia-500 font-mono">prefix = "/users"</code>, <code className="text-aquilia-500 font-mono">pipeline = [...]</code>) is now <strong>deprecated</strong> and scheduled for removal in future releases. All new controller definitions should use the modern <DocTerm id="controller.attributes">Attributes</DocTerm> builder assigned to the <code className="text-aquilia-500 font-mono">attr</code> variable.
              </p>
            </div>
          </div>
        </div>

        <div className="space-y-6 pt-2">
          <div className="space-y-2">
            <h4 className={`text-sm font-semibold text-red-500 flex items-center gap-1.5`}>
              <XCircle className="w-4 h-4" />
              <span>Old Style (Deprecated)</span>
            </h4>
            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Overriding class-level variables directly:
            </p>
            <CodeBlock
              language="python"
              filename="old_style.py"
              code={`class ProductsController(Controller):
    prefix = "/api/products"
    tags = ["Products"]
    instantiation_mode = "singleton"
    timeout = 30.0`}
            />
          </div>

          <div className="space-y-2">
            <h4 className={`text-sm font-semibold text-emerald-500 flex items-center gap-1.5`}>
              <CheckCircle2 className="w-4 h-4" />
              <span>New Style (Recommended)</span>
            </h4>
            <p className={`text-xs ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Using the chainable <code className="text-aquilia-500 font-mono">Attributes</code> descriptor:
            </p>
            <CodeBlock
              language="python"
              filename="new_style.py"
              code={`class ProductsController(Controller):
    attr = (
        Attributes()
        .prefix("/api/products")
        .tags("Products")
        .instantiation_mode("singleton")
        .timeout(30.0)
    )`}
            />
          </div>
        </div>

        <div className="space-y-3 pt-2">
          <h4 className={`text-sm font-bold ${isDark ? 'text-white' : 'text-gray-800'}`}>Why is the old style deprecated?</h4>
          <ul className={`list-disc list-inside text-xs space-y-2 pl-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
            <li>
              <strong className={isDark ? 'text-gray-300' : 'text-gray-700'}>Deferred Validation:</strong> Direct properties are not validated when the class is defined. Any misspelled attribute names or bad types will fail silently or crash later at runtime.
            </li>
            <li>
              <strong className={isDark ? 'text-gray-300' : 'text-gray-700'}>Mutable State Leakage:</strong> Setting lists (like <code className="text-aquilia-500 font-mono">pipeline</code> or <code className="text-aquilia-500 font-mono">tags</code>) directly exposes them to default mutable value issues where subclasses might share or leak states.
            </li>
            <li>
              <strong className={isDark ? 'text-gray-300' : 'text-gray-700'}>Poor Autocomplete Support:</strong> IDEs and linters cannot suggest options or provide typings for direct class variables. The fluent builder provides full IDE autocomplete.
            </li>
          </ul>
        </div>
      </section>

      {/* Design Philosophy & Performance */}
      <section className="space-y-6">
        <div className="flex items-center gap-2">
          <Cpu className="w-5 h-5 text-aquilia-400" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Design Philosophy & Performance</h2>
        </div>
        
        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia prioritizes performance, ensuring that request routing and context setup are as optimized as possible. The <DocTerm id="controller.attributes">Attributes</DocTerm> builder achieves this through three key architectural decisions:
        </p>

        {/* Timeline-style Flow Track (Non-Boxed Layout) */}
        <div className="relative border-l border-gray-200 dark:border-white/10 pl-6 ml-3 space-y-8 py-2">
          <div className="relative">
            <span className="absolute -left-[30px] top-1 w-4.5 h-4.5 rounded-full bg-aquilia-500/20 border border-aquilia-500 flex items-center justify-center text-[10px] text-aquilia-400 font-bold">1</span>
            <h4 className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>__slots__ Optimization</h4>
            <p className={`text-xs mt-1 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Using <code className="text-aquilia-500">__slots__</code> eliminates the per-instance dictionary (<code className="text-aquilia-500">__dict__</code>). This reduces the memory footprint and speeds up attribute access in the method chain by approximately 40%.
            </p>
          </div>

          <div className="relative">
            <span className="absolute -left-[30px] top-1 w-4.5 h-4.5 rounded-full bg-aquilia-500/20 border border-aquilia-500 flex items-center justify-center text-[10px] text-aquilia-400 font-bold">2</span>
            <h4 className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>__set_name__ Descriptor Protocol</h4>
            <p className={`text-xs mt-1 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Rather than analyzing metadata on every request, the builder implements Python's <code className="text-aquilia-500">__set_name__(self, owner, name)</code>. This executes exactly once when Python loads the controller class, applying the compiled metadata directly onto the controller type.
            </p>
          </div>

          <div className="relative">
            <span className="absolute -left-[30px] top-1 w-4.5 h-4.5 rounded-full bg-aquilia-500/20 border border-aquilia-500 flex items-center justify-center text-[10px] text-aquilia-400 font-bold">3</span>
            <h4 className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>O(1) Chaining & Zero Allocations</h4>
            <p className={`text-xs mt-1 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              Each fluent method call does not clone or instantiate a new builder. Instead, it mutates the existing builder's slot field in O(1) time and returns <code className="text-aquilia-500">self</code>, generating zero trash collector allocations beyond list conversions for variadic args.
            </p>
          </div>
        </div>
      </section>

      {/* Code Examples Section */}
      <section className="space-y-6">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-aquilia-400" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Usage & Examples</h2>
        </div>

        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Assign the builder chain to a class-level variable named <code className="text-aquilia-500 font-semibold font-mono">attr</code> in any controller subclass.
        </p>

        <div className="space-y-8">
          <div className="space-y-2">
            <h3 className={`text-lg font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-800'}`}>
              <span className="w-1.5 h-1.5 rounded-full bg-aquilia-500" />
              1. Basic REST Configuration
            </h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Configuring basic route grouping and OpenAPI tag classifications:
            </p>
            <CodeBlock
              language="python"
              filename="basic_attributes.py"
              code={`from aquilia import Controller, GET, Attributes, RequestCtx, Response

class UsersController(Controller):
    # Configure path prefix and OpenAPI tags for all routes in this controller
    attr = (
        Attributes()
        .prefix("/api/users")
        .tags("Users", "Management")
    )

    @GET("/")
    async def get_all(self, ctx: RequestCtx) -> Response:
        return Response.json({"users": []})`}
            />
          </div>

          <div className="space-y-2">
            <h3 className={`text-lg font-bold flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-800'}`}>
              <span className="w-1.5 h-1.5 rounded-full bg-aquilia-500" />
              2. Advanced Enterprise Configuration
            </h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Enforcing API versions, pipeline guards, rate limits, timeouts, and structured exception handlers at the class level:
            </p>
            <CodeBlock
              language="python"
              filename="advanced_attributes.py"
              code={`from aquilia import Controller, GET, Attributes, RequestCtx, Response
from aquilia.controller import Throttle, Interceptor, ExceptionFilter
from myapp.guards import JWTGuard
from myapp.filters import DatabaseExceptionFilter

class TransactionLogger(Interceptor):
    async def before(self, ctx: RequestCtx) -> Response | None:
        ctx.state["logger_time"] = ctx.request_id
        return None

    async def after(self, ctx: RequestCtx, result: Response) -> Response:
        # Custom log post-processing
        return result

class BillingController(Controller):
    attr = (
        Attributes()
        .prefix("/api/billing")
        .tags("Finance", "Billing")
        .version(["v1", "v2"])
        .instantiation_mode("singleton")
        .pipeline(JWTGuard) # Run auth guard for all routes
        .throttle(Throttle(limit=60, window=60)) # Rate limit: 60 req/min
        .interceptors(TransactionLogger()) # Attach request interceptor
        .exception_filters(DatabaseExceptionFilter()) # Catch DB exceptions
        .timeout(10.0) # Terminate route if execution > 10s
        .max_body_size(1024 * 1024) # Cap request payloads to 1MB
    )

    @GET("/history")
    async def billing_history(self, ctx: RequestCtx) -> Response:
        return Response.json({"invoices": []})`}
            />
          </div>
        </div>
      </section>

      {/* Builder API Reference */}
      <section className="space-y-6">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-aquilia-400" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Fluent Builder API Reference</h2>
        </div>
        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          The following list describes each chainable method exposed by the <DocTerm id="controller.attributes">Attributes</DocTerm> class:
        </p>

        {/* Modern clean API list without box layout, using left vertical line accent */}
        <div className="space-y-8 pl-4 border-l-2 border-aquilia-500/10">
          <div className="space-y-1">
            <h4 className="font-mono text-sm text-aquilia-500 font-semibold">.prefix(value: str) -&gt; Attributes</h4>
            <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              Configures the base URL path prefix for all endpoints in the controller.
            </p>
            <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              <strong>Validation:</strong> The value must be a string and start with <code className="text-aquilia-500">/</code> or be empty (<code className="text-aquilia-500">""</code>).
            </p>
          </div>

          <div className="space-y-1">
            <h4 className="font-mono text-sm text-aquilia-500 font-semibold">.pipeline(*nodes: Any) -&gt; Attributes</h4>
            <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              Accepts variadic positional arguments of guards, hooks, or middleware. They execute sequentially before the request hits the handler method.
            </p>
            <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              <strong>Validation:</strong> The arguments are collected as an iterable sequence.
            </p>
          </div>

          <div className="space-y-1">
            <h4 className="font-mono text-sm text-aquilia-500 font-semibold">.tags(*tag_values: str) -&gt; Attributes</h4>
            <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              Specifies the OpenAPI documentation categories. All endpoints within the controller inherit these tags.
            </p>
            <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              <strong>Validation:</strong> Each tag item must be a valid string.
            </p>
          </div>

          <div className="space-y-1">
            <h4 className="font-mono text-sm text-aquilia-500 font-semibold">.instantiation_mode(mode: Literal["per_request", "singleton"]) -&gt; Attributes</h4>
            <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              Controls the controller's lifecycle scope managed by the DI container.
            </p>
            <ul className={`list-disc list-inside text-xs space-y-1 pl-2 ${isDark ? 'text-gray-400' : 'text-gray-500'}`}>
              <li><code className="text-aquilia-500">per_request</code>: (Default) Instantiates a new controller instance per HTTP request. Supports request-scoped resources.</li>
              <li><code className="text-aquilia-500">singleton</code>: Shares a single instance across all requests for the application's entire lifespans. Required for startup/shutdown hooks.</li>
            </ul>
          </div>

          <div className="space-y-1">
            <h4 className="font-mono text-sm text-aquilia-500 font-semibold">.version(v: str | list[str]) -&gt; Attributes</h4>
            <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              Binds the controller endpoints to specific API versions (e.g. <code className="text-aquilia-500">"v1"</code>).
            </p>
            <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              <strong>Validation:</strong> Must be a string or a list of strings representing version names.
            </p>
          </div>

          <div className="space-y-1">
            <h4 className="font-mono text-sm text-aquilia-500 font-semibold">.throttle(t: Throttle) -&gt; Attributes</h4>
            <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              Applies rate-limiting metrics at the class level via a <DocTerm id="controller.throttle">Throttle</DocTerm> instance.
            </p>
          </div>

          <div className="space-y-1">
            <h4 className="font-mono text-sm text-aquilia-500 font-semibold">.interceptors(*items: Interceptor) -&gt; Attributes</h4>
            <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              Registers class-wide <DocTerm id="controller.interceptor">Interceptor</DocTerm> hooks that intercept controller route processing before and after methods run.
            </p>
          </div>

          <div className="space-y-1">
            <h4 className="font-mono text-sm text-aquilia-500 font-semibold">.exception_filters(*items: ExceptionFilter) -&gt; Attributes</h4>
            <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              Registers class-wide <DocTerm id="controller.exceptionfilter">ExceptionFilter</DocTerm> instances to convert raised exceptions to clean JSON payloads.
            </p>
          </div>

          <div className="space-y-1">
            <h4 className="font-mono text-sm text-aquilia-500 font-semibold">.timeout(seconds: float) -&gt; Attributes</h4>
            <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              Sets the handler timeout in seconds. Requests running longer than this will yield a timeout fault.
            </p>
            <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              <strong>Validation:</strong> Must be a non-negative integer or float (<code className="text-aquilia-500">&gt;= 0</code>).
            </p>
          </div>

          <div className="space-y-1">
            <h4 className="font-mono text-sm text-aquilia-500 font-semibold">.max_body_size(bytes_size: int) -&gt; Attributes</h4>
            <p className={`text-sm ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
              Restricts request body payload sizes (in bytes) to prevent Denial of Service (DoS) attacks.
            </p>
            <p className={`text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>
              <strong>Validation:</strong> Must be a non-negative integer (<code className="text-aquilia-500">&gt;= 0</code>).
            </p>
          </div>
        </div>
      </section>

      {/* Validation & Error Handling (Descriptors) */}
      <section className="space-y-6">
        <div className="flex items-center gap-2">
          <Shield className="w-5 h-5 text-aquilia-400" />
          <h2 className={`text-2xl font-bold ${isDark ? 'text-white' : 'text-gray-900'}`}>Compile-Time Validation</h2>
        </div>
        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          Aquilia prevents configuration errors from going unnoticed until runtime. The <code className="text-aquilia-500">_validate</code> engine is executed immediately during class evaluation (via <code className="text-aquilia-500">__set_name__</code>).
        </p>
        <p className={`${isDark ? 'text-gray-300' : 'text-gray-600'}`}>
          If any parameters violate validation limits, Aquilia raises a <code className="text-red-500 font-semibold font-mono">ConfigInvalidFault</code> during application startup.
        </p>

        {/* Clean Callout without heavy box border */}
        <div className={`p-5 rounded-xl border-l-4 border-amber-500 ${isDark ? 'bg-amber-950/20 text-gray-300' : 'bg-amber-50 text-gray-700'}`}>
          <div className="flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-amber-500 flex-shrink-0 mt-0.5" />
            <div>
              <h5 className="font-semibold text-sm">Definition-Time Error Surfacing</h5>
              <p className="text-xs mt-1 leading-relaxed">
                By throwing during definition time, the server will refuse to start if paths are formatted incorrectly (e.g. prefix without <code className="text-aquilia-500">/</code>), or if limits are set below zero. This guarantees that route integrity does not depend on request test cases.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className="flex justify-between items-center pt-8 border-t border-gray-200 dark:border-white/10">
        <Link to="/docs/controllers/overview" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors text-sm font-medium">
          <ArrowRight className="w-4 h-4 rotate-180" />
          <span>Overview</span>
        </Link>
        <Link to="/docs/controllers/request-ctx" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition-colors text-sm font-medium">
          <span>RequestCtx</span>
          <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
