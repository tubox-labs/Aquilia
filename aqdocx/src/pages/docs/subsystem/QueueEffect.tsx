import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Workflow } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function EffectsQueueEffect() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <Workflow className="w-4 h-4" />
          <span>EFFECTS / QUEUE &amp; TASKS</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Queue &amp; Task Effects
        </h1>
        <p className={`text-lg leading-relaxed font-light ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <DocTerm id="effects.QueueEffect">QueueEffect</DocTerm> provides messaging capability inside route handlers. It can pub/sub events to standard brokers via the <DocTerm id="effects.QueueProvider">QueueProvider</DocTerm> or enqueue async background tasks via the <DocTerm id="effects.TaskQueueProvider">TaskQueueProvider</DocTerm>.
        </p>
      </div>

      {/* Message Queue Publishing */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Message Queue Publishing</h2>
        <div className={`space-y-6 font-light leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-8`}>
          <p>
            When wired with the standard <DocTerm id="effects.QueueProvider">QueueProvider</DocTerm>, the effect returns a <DocTerm id="effects.QueueHandle">QueueHandle</DocTerm>. This handle facilitates publishing messages to brokers like Redis Streams or RabbitMQ. During testing, it falls back to collecting messages in an in-memory list.
          </p>
        </div>

        {/* QueueHandle API */}
        <h3 className="text-md font-mono text-aquilia-300 mb-4">QueueHandle API</h3>
        <div className="space-y-6 pl-4 border-l border-aquilia-500/20 text-sm text-gray-400 mb-8">
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.publish(payload: Any, *, headers: dict[str, str] | None = None) -> None`}</CodeBlock>
            <p className="mt-2 font-light">Publishes a single event payload to the configured topic, attaching optional metadata headers.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.publish_batch(payloads: Sequence[Any]) -> None`}</CodeBlock>
            <p className="mt-2 font-light">Publishes a list of payloads sequentially, optimizing connection roundtrips.</p>
          </div>
        </div>

        <CodeBlock language="python" filename="controllers/telemetry.py" highlightLines={[8, 12]}>{`from aquilia.controller import Controller, POST, RequestCtx
from aquilia.flow import requires
from aquilia.effects import QueueEffect

class TelemetryIngestController(Controller):
    # Require Queue capability scoped to the "telemetry" topic
    effects = [QueueEffect("device_metrics")]

    @POST("/ingest/metrics")
    async def ingest_device_data(self, ctx: RequestCtx) -> dict:
        body = await ctx.json()
        queue = ctx.get_effect("Queue")  # QueueHandle instance
        
        # Format payload and headers for real-world RabbitMQ/Redis Broker ingestion
        payload = {
            "device_id": body["device_id"],
            "temperature": float(body["temp"]),
            "humidity": float(body["humidity"]),
            "timestamp": body["timestamp"]
        }
        
        await queue.publish(
            payload,
            headers={
                "schema_version": "1.4.0",
                "environment": "production",
                "tenant_id": ctx.state.get("tenant_id", "default")
            }
        )
        return {"status": "metrics_dispatched_to_broker"}`}</CodeBlock>
      </section>

      {/* Task Queue Bridging */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Background Task Worker Integration</h2>
        <div className={`space-y-6 font-light leading-relaxed ${isDark ? 'text-gray-300' : 'text-gray-700'} mb-8`}>
          <p>
            When registered as a <DocTerm id="effects.TaskQueueProvider">TaskQueueProvider</DocTerm>, the effect hooks directly into Aquilia's background worker system. Rather than executing logic inside the HTTP request loop, it allows handlers to defer complex, resource-heavy operations (e.g. sending transaction emails or running AI inference models) to worker processes.
          </p>
          <p>
            It yields a request-scoped <DocTerm id="effects.TaskQueueHandle">TaskQueueHandle</DocTerm> that exposes the enqueue method.
          </p>
        </div>

        {/* TaskQueueHandle API */}
        <h3 className="text-md font-mono text-aquilia-300 mb-4">TaskQueueHandle API</h3>
        <div className="space-y-6 pl-4 border-l border-blue-500/20 text-sm text-gray-400 mb-8">
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.enqueue(func: Any, *args: Any, **kwargs: Any) -> str`}</CodeBlock>
            <p className="mt-2 font-light">Submits an asynchronous function or task import path to the queue. Returns the unique Job ID.</p>
          </div>
          <div>
            <CodeBlock language="python" compact showLineNumbers={false}>{`await handle.publish(payload: Any, *, headers: dict | None = None) -> None`}</CodeBlock>
            <p className="mt-2 font-light">Compatibility no-op method designed to make the handle interchangeable with <code className="text-aquilia-400">QueueHandle</code>.</p>
          </div>
        </div>

        <CodeBlock language="python" filename="controllers/registrations.py" highlightLines={[12]}>{`from aquilia.controller import Controller, POST, RequestCtx
from aquilia.flow import requires
from aquilia.effects import QueueEffect

class RegistrationController(Controller):
    # Triggers task queue handle acquisition
    effects = [QueueEffect("default")]

    @POST("/register/corporate")
    async def register_company(self, ctx: RequestCtx) -> dict:
        body = await ctx.json()
        task_queue = ctx.get_effect("Queue")  # TaskQueueHandle instance
        
        # Dispatch background worker chain (invoice rendering + email delivery)
        job_id = await task_queue.enqueue(
            "modules.billing.tasks:process_corporate_enrollment",
            company_id=body["company_id"],
            plan_tier=body["plan_tier"],
            billing_email=body["billing_email"]
        )
        return {
            "status": "enrollment_initiated", 
            "job_id": job_id,
            "details": "Invoice generation and welcome email enqueued in background"
        }`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/subsystem/cache" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Cache Effect
        </Link>
        <Link to="/docs/subsystem/http" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          HTTP Effect <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
