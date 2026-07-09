import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, FileText } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function TemplatesOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderMuted = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto px-4 py-2">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <FileText className="w-4 h-4" />
          Advanced / Templates
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono">Template Engine Overview</span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          AquilaTemplates is an async-native rendering engine built on top of Jinja2. It features sandboxed script execution, module-aware namespace loaders, precompiled bytecode caching, and auto-populated request/session contexts.
        </p>
      </div>

      {/* Configuration & Setup */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          System Integration & Registration
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          Configure templates at the workspace level and organize directories within module structures.
        </p>

        {/* Workspace Level */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Workspace Integration</h3>
          <p className={`text-sm mb-4 ${textMuted}`}>
            Register templates inside <code className="text-aquilia-400">workspace.py</code> using <DocTerm id="templates.TemplateLoader">TemplatesIntegration</DocTerm>:
          </p>
          <CodeBlock
            language="python"
            filename="workspace.py"
            highlightLines={[6, 7]}
          >{`from aquilia.workspace import Workspace
from aquilia.integrations import TemplatesIntegration

workspace = (
    Workspace("myapp")
    .integrate(TemplatesIntegration(
        search_paths=["templates", "shared_templates"],
        cache="memory",
        sandbox=True,
        sandbox_policy="strict"
    ))
)`}</CodeBlock>
        </div>

        {/* Manifest Level */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Manifest Auto-Discovery & Layout</h3>
          <p className={`text-sm mb-4 ${textMuted}`}>
            By default, templates placed inside modules under the <code className="text-aquilia-400">templates/</code> folder are auto-discovered. You can also customize search paths inside <code className="text-aquilia-400">module.aq</code>:
          </p>
          <CodeBlock
            language="json"
            filename="modules/auth/module.aq"
          >{`{
  "templates": {
    "enabled": true,
    "search_paths": [
      "./templates",
      "./custom_themes"
    ],
    "precompile": true,
    "cache": "surp"
  }
}`}</CodeBlock>
        </div>
      </section>

      {/* Subsystem Components */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Engine Architecture
        </h2>
        <div className="space-y-8">
          {[
            {
              name: 'TemplateEngine',
              id: 'templates.TemplateEngine',
              desc: 'Core coordinator managing environment states, rendering engines, and Response construction helpers.'
            },
            {
              name: 'TemplateLoader',
              id: 'templates.TemplateLoader',
              desc: 'Namespace-aware loader. Supports relative paths, package resources, and cross-module referencing formats (@module/path).'
            },
            {
              name: 'SurpBytecodeCache',
              id: 'templates.SurpBytecodeCache',
              desc: 'Production-ready cache compiled into frozen .surp bytecode artifacts. Utilizes HMAC hashes for tampering detection.'
            },
            {
              name: 'TemplateSandbox',
              id: 'templates.TemplateSandbox',
              desc: 'Execution gate enforcing a whitelist of filters, functions, globals, and operators. Disallows arbitrary Python execution.'
            }
          ].map((item, i) => (
            <div key={i} className="pl-4 border-l-2 border-aquilia-500/20 hover:border-aquilia-400 transition-colors duration-200">
              <DocTerm id={item.id} className="text-aquilia-500 font-mono text-sm font-semibold border-b-0 hover:underline">
                {item.name}
              </DocTerm>
              <p className={`text-sm mt-1 leading-relaxed ${textMuted}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Rendering in Controllers */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Rendering in Controllers
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          Access the template system either through controller helper methods or by direct invocation of the injected <DocTerm id="templates.TemplateEngine">TemplateEngine</DocTerm>:
        </p>
        <CodeBlock
          language="python"
          filename="controllers.py"
          highlightLines={[12, 17, 24]}
        >{`from aquilia import Controller, Get, Inject
from aquilia.templates import TemplateEngine

class WebController(Controller):

    @Inject()
    def __init__(self, templates: TemplateEngine):
        self.templates = templates

    @Get("/")
    async def index(self, ctx):
        # 1. Convenient controller render helper (returns Response)
        return await self.render("index.html", {"title": "Home"}, request_ctx=ctx)

    @Get("/profile")
    async def profile(self, ctx):
        # 2. Render directly to string via TemplateEngine
        html = await self.templates.render(
            "profile.html", 
            {"user": ctx.identity}, 
            request_ctx=ctx
        )
        return ctx.html(html)

    @Get("/dashboard")
    async def dashboard(self, ctx):
        # 3. Direct response generation via TemplateEngine
        return await self.templates.render_to_response(
            "dashboard.html",
            {"stats": await get_stats()},
            status=200,
            request_ctx=ctx
        )`}</CodeBlock>
      </section>

      {/* Auto-injected Context */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Auto-Injected Context Variables
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          When rendering templates with <code className="text-aquilia-400">request_ctx</code> provided, the environment automatically attaches standard context helpers and objects:
        </p>
        <div className="space-y-4 font-sans text-sm">
          {[
            { variable: 'request', desc: 'The active AquiliaRequest object containing cookies, headers, query parameters, and method state.' },
            { variable: 'identity', desc: 'The authenticated user identity resolved by guards, or None.' },
            { variable: 'session', desc: 'Direct access to the session storage dictionary.' },
            { variable: 'csrf_token', desc: 'A string representing the active CSRF verification token.' },
            { variable: 'get_flashed_messages()', desc: 'Loads and flushes temporary notification messages from session state.' },
            { variable: 'url_for(handler, **params)', desc: 'Generates URLs from controller endpoints dynamically.' },
            { variable: 'static(path)', desc: 'Generates relative path bindings for assets, static files, and media.' }
          ].map((item, i) => (
            <div key={i} className="flex justify-between py-3 border-b border-white/5 last:border-0 gap-4">
              <code className="text-aquilia-500 font-mono text-xs font-semibold flex-shrink-0">{item.variable}</code>
              <span className={`text-right ${textMuted}`}>{item.desc}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/websockets/adapters" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Adapters
        </Link>
        <Link to="/docs/templates/engine" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          TemplateEngine <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'TemplateEngine API', link: '/docs/templates/engine' },
          { text: 'Template Loaders & Namespaces', link: '/docs/templates/loaders' },
          { text: 'Sandboxed Security Policy', link: '/docs/templates/security' },
        ]}
      />
    </div>
  )
}