import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Puzzle } from 'lucide-react'

export function I18nIntegration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderSubtle = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Puzzle className="w-4 h-4" />
          i18n / Integration
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            i18n Integration Guide
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          i18n is integrated at server startup, then exposed through middleware state, template helpers,
          and DI providers. This page covers default wiring and manual integration patterns.
        </p>
      </div>

      {/* Server-Level Wiring */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Server-Level Wiring</h2>
        <CodeBlock language="python" filename="aquilia/server.py::_setup_i18n" highlightLines={[2, 3, 5]}>{`cfg = I18nConfig.from_dict(config_loader.get_i18n_config())
service = create_i18n_service(cfg)
register_i18n_providers(container, service, cfg)
resolver = build_resolver(cfg)
middleware_stack.add(I18nMiddleware(service, resolver), priority=24)
register_i18n_template_globals(template_env, service)
`}</CodeBlock>
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 mt-4">
          <p>
            When <code className="text-aquilia-500">enabled=True</code>, the resolved locale and <DocTerm id="i18n.I18nService">I18nService</DocTerm> context become available in the request state dict for all downstream handlers.
          </p>
        </div>
      </section>

      {/* Middleware Order and State Contract */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Middleware Order and State Contract</h2>
        <CodeBlock language="python" filename="middleware behavior" highlightLines={[2, 4]}>{`# I18nMiddleware at priority 24
# request.state after middleware:
request.state["locale"]      # str
request.state["locale_obj"]  # Locale
request.state["i18n"]        # I18nService
`}</CodeBlock>
        <CodeBlock language="python" filename="controller.py" highlightLines={[6, 7]}>{`from aquilia import Controller, GET, RequestCtx

class WelcomeController(Controller):
    @GET("/welcome")
    async def welcome(self, ctx: RequestCtx):
        i18n = ctx.request.state["i18n"]
        locale = ctx.request.state.get("locale", "en")
        return {
            "message": i18n.t("messages.welcome", locale=locale, name="World"),
            "count": i18n.tn("messages.items", 3, locale=locale),
        }
`}</CodeBlock>
      </section>

      {/* Template Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Template Integration</h2>
        <CodeBlock language="jinja" filename="template.jinja2" highlightLines={[1, 2]}>{`<h1>{{ _("messages.welcome", name=user_name) }}</h1>
<p>{{ _n("messages.items", count=item_count) }}</p>
<p>{{ "messages.greeting" | translate(name=user_name) }}</p>
<p>{{ total | format_currency("USD") }}</p>
<p>{{ created_at | format_date }}</p>
`}</CodeBlock>
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 mt-4">
          <p>
            Template globals automatically bound to the Jinja sandbox environment include <code className="text-aquilia-500">_</code>, <code className="text-aquilia-500">_n</code>, <code className="text-aquilia-500">_p</code>, and filters include <code className="text-aquilia-500">translate</code>, <code className="text-aquilia-500">format_number</code>, <code className="text-aquilia-500">format_currency</code>, and <code className="text-aquilia-500">format_date</code>.
          </p>
        </div>
      </section>

      {/* DI Integration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>DI Integration</h2>
        <CodeBlock language="python" filename="aquilia/i18n/di_integration.py" highlightLines={[2, 5]}>{`# App-scope registration
register_i18n_providers(container, service, config)

# Request-scope locale registration
register_i18n_request_providers(request_container, locale, service)
`}</CodeBlock>
      </section>

      {/* Manual Integration Pattern */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Manual Integration Pattern</h2>
        <CodeBlock language="python" filename="manual_boot.py" highlightLines={[7, 10]}>{`from aquilia.i18n.service import I18nConfig, create_i18n_service
from aquilia.i18n.middleware import I18nMiddleware, build_resolver
from aquilia.i18n.di_integration import register_i18n_providers
from aquilia.i18n.template_integration import register_i18n_template_globals

cfg = I18nConfig(default_locale="en", available_locales=["en", "fr"], catalog_dirs=["locales"])
svc = create_i18n_service(cfg)
register_i18n_providers(app_container, svc, cfg)
resolver = build_resolver(cfg)

middleware_stack.add(I18nMiddleware(svc, resolver), scope="global", priority=24, name="i18n")
register_i18n_template_globals(template_env, svc)
`}</CodeBlock>
      </section>

      <NextSteps
        items={[
          { text: 'i18n API Reference', link: '/docs/i18n/api-reference' },
          { text: 'i18n CLI Reference', link: '/docs/i18n/cli' },
          { text: 'i18n Edge Cases', link: '/docs/i18n/edge-cases' },
          { text: 'i18n Troubleshooting', link: '/docs/i18n/troubleshooting' },
        ]}
      />
    </div>
  )
}
