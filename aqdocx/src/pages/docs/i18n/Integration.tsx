import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Puzzle } from 'lucide-react'

export function I18nIntegration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const box = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const subtle = isDark ? 'text-gray-400' : 'text-gray-600'

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
        <p className={`text-lg leading-relaxed ${subtle}`}>
          i18n is integrated at server startup, then exposed through middleware state, template helpers,
          and DI providers. This page covers default wiring and manual integration patterns.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Server-Level Wiring</h2>
        <CodeBlock language="python" filename="aquilia/server.py::_setup_i18n">{`cfg = I18nConfig.from_dict(config_loader.get_i18n_config())
service = create_i18n_service(cfg)
register_i18n_providers(container, service, cfg)
resolver = build_resolver(cfg)
middleware_stack.add(I18nMiddleware(service, resolver), priority=24)
register_i18n_template_globals(template_env, service)
`}</CodeBlock>
        <div className={box}>
          <p className={`text-sm ${subtle}`}>
            With enabled=False, setup is skipped entirely. With enabled=True, locale and i18n service become available
            in request state for all downstream middleware and handlers.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Middleware Order and State Contract</h2>
        <CodeBlock language="python" filename="middleware behavior">{`# I18nMiddleware at priority 24
# request.state after middleware:
request.state["locale"]      # str
request.state["locale_obj"]  # Locale
request.state["i18n"]        # I18nService
`}</CodeBlock>
        <CodeBlock language="python" filename="controller.py">{`from aquilia import Controller, GET, RequestCtx

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

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Template Integration</h2>
        <CodeBlock language="jinja" filename="template.jinja2">{`<h1>{{ _("messages.welcome", name=user_name) }}</h1>
<p>{{ _n("messages.items", count=item_count) }}</p>
<p>{{ "messages.greeting" | translate(name=user_name) }}</p>
<p>{{ total | format_currency("USD") }}</p>
<p>{{ created_at | format_date }}</p>
`}</CodeBlock>
        <div className={box}>
          <p className={`text-sm ${subtle}`}>
            Template globals include _, _n, _p, gettext, ngettext, and i18n_service. Filters include translate,
            t, format_number, format_currency, format_date, format_time, and format_percent.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>DI Integration</h2>
        <CodeBlock language="python" filename="aquilia/i18n/di_integration.py">{`# App-scope registration
register_i18n_providers(container, service, config)

# Optional request-scope locale registration
register_i18n_request_providers(request_container, locale, service)
`}</CodeBlock>
        <div className={box}>
          <ul className={`list-disc pl-6 space-y-2 text-sm ${subtle}`}>
            <li>register_i18n_providers attempts multiple container APIs and registers I18nService and I18nConfig.</li>
            <li>register_i18n_request_providers exists for request-scope locale tokens but is not auto-called by server wiring.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Session and Auth Interplay</h2>
        <CodeBlock language="python" filename="workspace.py">{`Integration.i18n(
    enabled=True,
    available_locales=["en", "fr"],
    resolver_order=["session", "query", "cookie", "header"],
)

# expected request state shape from session subsystem
request.state["session"] = {"locale": "fr"}
`}</CodeBlock>
        <div className={box}>
          <p className={`text-sm ${subtle}`}>
            i18n does not authenticate identities. SessionLocaleResolver simply reads a locale hint from session state
            when that resolver is enabled.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Manual Integration Pattern</h2>
        <CodeBlock language="python" filename="manual_boot.py">{`from aquilia.i18n.service import I18nConfig, create_i18n_service
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
