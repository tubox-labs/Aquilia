import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Workflow } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function EffectsHTTPEffect() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Workflow className="w-4 h-4" />
          <span>EFFECTS / OUTBOUND HTTP</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          HTTP Client Effect
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="effects.HTTPEffect">HTTPEffect</DocTerm> provides pre-configured, request-scoped outbound HTTP clients. Backed by the <DocTerm id="effects.HTTPProvider">HTTPProvider</DocTerm> and Aquilia's native HTTP client, it optimizes connection reuse, manages request timeouts, and handles connection pooling.
        </p>
      </div>

      {/* Philosophy */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Unified HTTP Connections</h2>
        <div className={`space-y-6 font-light leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          <p>
            Spawning arbitrary HTTP sessions (e.g. using standard library clients or raw requests libraries) per request degrades server throughput and risks socket exhaustion. The <DocTerm id="effects.HTTPEffect">HTTPEffect</DocTerm> integrates outbound queries into the ASGI lifecycle. Outbound connections share pooled HTTP sessions, enforce unified timeouts, and simplify key management.
          </p>
        </div>
      </section>

      {/* HTTPHandle API */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">HTTPHandle API</h2>
        <p className={`mb-6 font-light ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The acquired handle is an instance of <DocTerm id="effects.HTTPHandle">HTTPHandle</DocTerm>, which automatically parses JSON responses:
        </p>

        <div className="space-y-8 pl-4 border-l border-aquilia-500/20 text-sm text-gray-400">
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.get(url: str, **kwargs) -> Any`}</CodeBlock>
            <p className="mt-2 font-light">Performs an async HTTP GET request. The URL path is appended to the provider's base URL. Returns decoded JSON.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.post(url: str, *, json: Any = None, **kwargs) -> Any`}</CodeBlock>
            <p className="mt-2 font-light">Performs an async HTTP POST request, forwarding the <code className="text-white">json</code> payload. Returns decoded JSON.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.put(url: str, *, json: Any = None, **kwargs) -> Any`}</CodeBlock>
            <p className="mt-2 font-light">Performs an async HTTP PUT request, forwarding the <code className="text-white">json</code> payload. Returns decoded JSON.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.delete(url: str, **kwargs) -> Any`}</CodeBlock>
            <p className="mt-2 font-light">Performs an async HTTP DELETE request. Returns decoded JSON.</p>
          </div>
        </div>
      </section>

      {/* Code Example */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Usage: Stripe Billing Sync</h2>
        <p className={`mb-6 font-light ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          The example below demonstrates querying the Stripe Billing API to check subscription details and issue invoice charge triggers:
        </p>

        <CodeBlock language="python" filename="controllers/stripe_billing.py" highlightLines={[8, 12, 19]}>{`from aquilia.controller import Controller, POST, RequestCtx
from aquilia.flow import requires
from aquilia.effects import HTTPEffect, DBTx

class StripeBillingController(Controller):
    # Require HTTP client capability and database access
    effects = [
        HTTPEffect(service="stripe"),
        DBTx["write"]
    ]

    @POST("/billing/sync-subscription")
    async def sync_stripe_subscription(self, ctx: RequestCtx) -> dict:
        http = ctx.get_effect("HTTP")  # HTTPHandle instance
        db = ctx.get_effect("DBTx")    # DBTxHandle instance
        
        body = await ctx.json()
        
        # 1. Fetch live subscription stats from Stripe API
        stripe_sub = await http.get(
            f"/v1/subscriptions/{body['stripe_sub_id']}", 
            headers={"Authorization": f"Bearer {ctx.secrets.stripe_key}"}
        )
        
        # 2. Check if subscription is unpaid
        if stripe_sub.get("status") == "unpaid":
            # 3. Trigger immediate payment charge retries via POST API
            charge_response = await http.post(
                f"/v1/invoices/{stripe_sub['latest_invoice']}/pay",
                headers={"Authorization": f"Bearer {ctx.secrets.stripe_key}"}
            )
            
            # Update local DB account status to flagged
            await db.execute(
                "UPDATE billing_accounts SET status = ? WHERE stripe_customer_id = ?",
                ("FLAGGED", stripe_sub["customer"])
            )
            return ctx.json({"status": "account_flagged", "stripe_invoice": charge_response["id"]})
            
        return ctx.json({"status": "account_synchronized", "stripe_status": stripe_sub["status"]})`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/subsystem/queue" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Queue Effect
        </Link>
        <Link to="/docs/subsystem/storage" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Storage Effect <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
