import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { useVersion } from '../../../hooks/useVersion'
import { ArrowLeft, ArrowRight, Settings } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function TemplatesEngine() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const version = useVersion()
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderMuted = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto px-4 py-2">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Settings className="w-4 h-4" />
          Templates / TemplateEngine
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono">TemplateEngine API</span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          The <DocTerm id="templates.TemplateEngine">TemplateEngine</DocTerm> class governs Jinja2 parsing environments, resolves namespaced sources, loads precompiled bytecode caches, and applies sandboxing rules.
        </p>
      </div>

      {/* Methods Table */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Method API Reference
        </h2>
        <div className="space-y-8">
          {[
            {
              name: 'async def render(self, template_name: str, context: dict | None = None, request_ctx: RequestCtx | None = None) -> str',
              desc: 'Renders the template asynchronously to a string. Populates request context if request_ctx is supplied.',
              code: `async def get_profile_html(self, ctx: RequestCtx, user_id: int) -> str:
    # Fetch data asynchronously
    profile_data = await self.user_service.get_profile(user_id)
    
    # Render template asynchronously to a plain HTML string
    html_content = await self.templates.render(
        template_name="users/profile.html",
        context={"profile": profile_data},
        request_ctx=ctx
    )
    return html_content`
            },
            {
              name: 'def render_sync(self, template_name: str, context: dict | None = None, request_ctx: RequestCtx | None = None) -> str',
              desc: 'Synchronous counterpart for rendering templates, useful inside sync context execution blocks.',
              code: `def render_invoice_pdf_markup(self, invoice_id: int) -> str:
    # Synchronously resolve and render templates for reporting backends
    invoice = self.db.query_sync(Invoice).get(invoice_id)
    
    markup = self.templates.render_sync(
        template_name="reports/invoice.html",
        context={"invoice": invoice}
    )
    return markup`
            },
            {
              name: 'async def stream(self, template_name: str, context: dict | None = None, request_ctx: RequestCtx | None = None) -> AsyncIterator[bytes]',
              desc: 'Returns an async generator yielding chunked HTML bytes. Enables incremental client-side rendering.',
              code: `async def stream_large_dashboard(self, ctx: RequestCtx) -> AsyncIterator[bytes]:
    stats_cursor = await self.analytics.get_live_cursor()
    
    # Stream template chunks back to client incrementally
    async for chunk in self.templates.stream(
        template_name="admin/dashboard.html",
        context={"stats_stream": stats_cursor},
        request_ctx=ctx
    ):
        yield chunk`
            },
            {
              name: 'async def render_to_response(self, template_name: str, context: dict | None = None, *, status: int = 200, headers: dict | None = None, request_ctx: RequestCtx | None = None) -> Response',
              desc: 'Renders the template and wraps the output in an HTTP HTML Response object.',
              code: `@Get("/welcome")
async def welcome(self, ctx: RequestCtx):
    # Renders template and packages it into an HTTP HTML Response wrapper
    return await self.templates.render_to_response(
        template_name="marketing/welcome.html",
        context={"promo": "SUMMER50"},
        status=200,
        headers={"Cache-Control": "public, max-age=3600"},
        request_ctx=ctx
    )`
            },
            {
              name: 'async def template_stream_response(self, template_name: str, context: dict | None = None, *, status: int = 200, headers: dict | None = None, request_ctx: RequestCtx | None = None) -> Response',
              desc: 'Returns a streaming response containing the incremental HTML chunks yielded by stream().',
              code: `@Get("/stream-reports")
async def report_stream(self, ctx: RequestCtx):
    # Generates a Streaming Response immediately, yielding HTML chunks
    return await self.templates.template_stream_response(
        template_name="reports/heavy_audit.html",
        context={"logs": await self.audit.fetch_large_logs()},
        status=200,
        headers={"Content-Type": "text/html; charset=utf-8"},
        request_ctx=ctx
    )`
            },
            {
              name: 'def get_template(self, name: str) -> jinja2.Template',
              desc: 'Loads a template object from the filesystem or bytecode cache for low-level manipulation.',
              code: `def inspect_template_blocks(self):
    # Load low-level template objects to inspect block names or macros
    template = self.templates.get_template("base.html")
    logger.info(f"Loaded blocks: {template.blocks.keys()}")`
            },
            {
              name: 'def invalidate_cache(self, template_name: str | None = None) -> None',
              desc: 'Clears compilation cache. Invalidate specific templates, or clear the entire cache if template_name is None.',
              code: `def on_theme_updated(self, theme_file: str):
    # Clear specific template cache from environment compilation caches
    self.templates.invalidate_cache(f"themes/{theme_file}.html")`
            },
            {
              name: 'def register_filter(self, name: str, func: Callable) -> None',
              desc: 'Registers a custom filter function (e.g. {{ val | my_filter }}).',
              code: `def register_formatting_filters(self):
    # Register custom filters dynamically into the template environment
    self.templates.register_filter(
        name="obfuscate_email",
        func=lambda val: val.split("@")[0][:3] + "***@" + val.split("@")[1]
    )`
            },
            {
              name: 'def register_global(self, name: str, value: Any) -> None',
              desc: 'Registers a global variable or helper function available in all templates.',
              code: `def register_application_globals(self):
    # Register global functions / values available inside all rendering contexts
    self.templates.register_global("api_version", "v${version}")
    self.templates.register_global("check_feature_flag", lambda flag: self.flags.enabled(flag))`
            }
          ].map((item, i) => (
            <div key={i} className="py-4 border-b border-white/5 last:border-0">
              <h3 className={`font-semibold text-sm mb-2 ${isDark ? 'text-white' : 'text-gray-900'} font-mono`}>
                {item.name}
              </h3>
              <p className={`text-sm mb-3 ${textMuted}`}>{item.desc}</p>
              <CodeBlock language="python">{item.code}</CodeBlock>
            </div>
          ))}
        </div>
      </section>

      {/* Built-in Custom Filters */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Built-in Filters
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          AquilaTemplates extends Jinja2 with a set of default data formatters. Here is how they are used inside templates:
        </p>
        <div className="space-y-6">
          {[
            { 
              filter: 'format_date', 
              desc: 'Converts datetime objects or Unix timestamps to formatted strings.',
              code: `<!-- Input: datetime.utcnow() -->
<p>Joined on: {{ user.created_at | format_date("%B %d, %Y") }}</p>
<!-- Output: <p>Joined on: July 09, 2026</p> -->`
            },
            { 
              filter: 'format_currency', 
              desc: 'Formats floating point values to currency strings.',
              code: `<!-- Input: 1240.5 -->
<p>Total: {{ order.total | format_currency("USD") }}</p>
<!-- Output: <p>Total: $1,240.50</p> -->`
            },
            { 
              filter: 'pluralize', 
              desc: 'Returns singular or plural text based on count values.',
              code: `<!-- Input: [1, 2, 3] -->
<p>You have {{ items | length }} {{ items | length | pluralize("item", "items") }}</p>
<!-- Output: <p>You have 3 items</p> -->`
            },
            { 
              filter: 'sanitize_html', 
              desc: 'Safely strips unsafe script elements while preserving basic markup to mitigate XSS.',
              code: `<!-- Input: "Hello <script>alert('xss')</script> <b>World</b>" -->
<div>{{ comment.body | sanitize_html | safe }}</div>
<!-- Output: <div>Hello  <b>World</b></div> -->`
            },
            { 
              filter: 'tojson', 
              desc: 'Converts dictionary structures and list inputs to serialized JSON strings.',
              code: `<!-- Input: {"name": "Asha", "role": "admin"} -->
<script>
  const user = {{ user.profile | tojson | safe }};
</script>
<!-- Output: const user = {"name": "Asha", "role": "admin"}; -->`
            }
          ].map((item, i) => (
            <div key={i} className="py-4 border-b border-white/5 last:border-0">
              <h3 className={`font-semibold text-sm mb-1 ${isDark ? 'text-white' : 'text-gray-900'} font-mono`}>
                {item.filter}
              </h3>
              <p className={`text-sm mb-3 ${textMuted}`}>{item.desc}</p>
              <CodeBlock language="html">{item.code}</CodeBlock>
            </div>
          ))}
        </div>
      </section>

      {/* Bytecode Cache Implementations */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Bytecode Caching
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          Templates are compiled into python bytecode. Choose from two distinct caching behaviors:
        </p>
        <div className="space-y-6">
          <div className="pl-4 border-l-2 border-aquilia-500/20">
            <h4 className={`text-sm font-semibold mb-1 font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
              MemoryBytecodeCache
            </h4>
            <p className={`text-xs ${textMuted}`}>
              Stores compiled abstract syntax tree nodes entirely inside RAM. Fast execution speeds, ideal for ephemeral container dynos and cloud functions.
            </p>
          </div>
          <div className="pl-4 border-l-2 border-aquilia-500/20">
            <h4 className={`text-sm font-semibold mb-1 font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>
              SurpBytecodeCache
            </h4>
            <p className={`text-xs ${textMuted}`}>
              Compiles templates into a single compressed `.surp` archive. HMAC signatures verify the bytecode integrity on startup to prevent local file tampering.
            </p>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/templates" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/templates/loaders" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Loaders <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'Template Loaders & Namespaces', link: '/docs/templates/loaders' },
          { text: 'Sandboxed Security Policy', link: '/docs/templates/security' },
          { text: 'Developer Integration Guide', link: '/docs/developer-guide' },
        ]}
      />
    </div>
  )
}