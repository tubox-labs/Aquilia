import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, Workflow } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function EffectsCustomEffects() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Workflow className="w-4 h-4" />
          <span>EFFECTS / CUSTOM EFFECTS</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Custom Effects &amp; Providers
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia's Effect system is open and fully extensible. By subclassing <DocTerm id="effects.Effect">Effect</DocTerm> and <DocTerm id="effects.EffectProvider">EffectProvider</DocTerm>, you can declare custom infrastructural integrations (e.g. SMTP clients, payment gateways, or AI models) and inject them safely into request contexts.
        </p>
      </div>

      {/* Building Custom Effects */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Step-by-Step Implementation</h2>
        <div className={`space-y-6 font-light leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-8`}>
          <p>
            To extend the capability system, you must define three items:
          </p>
          <ol className="list-decimal list-inside space-y-3 pl-2">
            <li>
              <strong>Effect Token:</strong> A subclass of <DocTerm id="effects.Effect">Effect</DocTerm> representing the typed capability tag.
            </li>
            <li>
              <strong>Resource Handle:</strong> A class wrapping the provider client. Handlers interact with this handle inside the request context.
            </li>
            <li>
              <strong>Effect Provider:</strong> A subclass of <DocTerm id="effects.EffectProvider">EffectProvider</DocTerm> managing the connection, setup, and cleanup lifecycle.
            </li>
          </ol>
        </div>
      </section>

      {/* Step 1: Subclassing and Definition */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Code Implementation (Slack Dispatcher)</h2>
        <p className={`mb-6 font-light ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Here is how to create a custom <code className="text-aquilia-400">SlackEffect</code> that pools HTTPS webhook client sessions, formats slack block payloads, and manages channel routing:
        </p>

        <CodeBlock language="python" filename="extensions/slack_effect.py" highlightLines={[6, 17, 25]}>{`import aiohttp
from typing import Any, dict
from aquilia.effects import Effect, EffectProvider, EffectKind

# 1. Define the Effect Token
class SlackEffect(Effect[str]):
    def __init__(self, channel: str = "general"):
        super().__init__("Slack", mode=channel, kind=EffectKind.CUSTOM)

# 2. Define the user-facing resource handle
class SlackHandle:
    def __init__(self, session: aiohttp.ClientSession, webhook_url: str, channel: str):
        self.session = session
        self.webhook_url = webhook_url
        self.channel = channel

    async def send_message(self, text: str, blocks: list[dict] | None = None) -> None:
        payload = {
            "channel": f"#{self.channel}",
            "text": text,
            "blocks": blocks or []
        }
        async with self.session.post(self.webhook_url, json=payload) as resp:
            resp.raise_for_status()

# 3. Define the Lifecycle Provider
class SlackProvider(EffectProvider):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
        self.session = None

    async def initialize(self) -> None:
        # Invoked once at server startup: initialize shared async HTTP session
        self.session = aiohttp.ClientSession()

    async def acquire(self, mode: str | None = None) -> SlackHandle:
        # Invoked per-request: return a handle scoped to the requested channel mode
        channel = mode or "general"
        return SlackHandle(self.session, self.webhook_url, channel)

    async def release(self, resource: SlackHandle, success: bool = True) -> None:
        # Invoked per-request end: nothing to tear down since session is pooled
        pass

    async def finalize(self) -> None:
        # Invoked once at server shutdown: safely close async HTTP session
        if self.session:
            await self.session.close()

    async def health_check(self) -> dict[str, Any]:
        if not self.session or self.session.closed:
            return {"healthy": False, "reason": "HTTP session is closed"}
        return {"healthy": True}`}</CodeBlock>
      </section>

      {/* Step 2: Registering Providers */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Provider Registration</h2>
        <div className={`space-y-6 font-light leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-8`}>
          <p>
            You can register your custom provider with the <DocTerm id="effects.EffectRegistry">EffectRegistry</DocTerm> during application startup:
          </p>
        </div>

        <CodeBlock language="python" filename="bootstrap.py" highlightLines={[6]}>{`from aquilia.effects import EffectRegistry
from extensions.slack_effect import SlackProvider

# Create or fetch registry
registry = EffectRegistry()

# Register custom provider with Slack webhook URL configuration
registry.register("Slack", SlackProvider(webhook_url="https://hooks.slack.com/services/T00/B00/X00"))`}</CodeBlock>
      </section>

      {/* Step 3: Usage in Handler */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Using in Controllers</h2>
        <p className={`mb-6 font-light ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Once registered, require the capability by name. The handle will be automatically acquired and injected into the context:
        </p>

        <CodeBlock language="python" filename="controllers/notifications.py" highlightLines={[6, 11]}>{`from aquilia.controller import Controller, POST, RequestCtx
from aquilia.flow import requires
from extensions.slack_effect import SlackEffect

class SlackNotificationController(Controller):
    # Require Slack capability scoped to the "incidents" channel
    effects = [SlackEffect("incidents")]

    @POST("/notify/incident")
    async def dispatch_incident(self, ctx: RequestCtx) -> dict:
        slack = ctx.get_effect("Slack")  # SlackHandle instance
        
        # Dispatch formatted alert block
        await slack.send_message(
            text="ALERT: Incident detected in server-prod-04",
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*ALERT:* Critical incident detected on *server-prod-04*. CPU utilization > 98%."
                    }
                }
            ]
        )
        return {"status": "slack_notification_dispatched"}`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/effects/storage" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Storage Effect
        </Link>
        <span />
      </div>

      <NextSteps />
    </div>
  )
}
