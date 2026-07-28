import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { NextSteps } from '../../../components/NextSteps'
import { Send, Database, ShieldAlert, Webhook, Ban, AlertTriangle } from 'lucide-react'

export function MailDelivery() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Send className="w-4 h-4 animate-pulse" />
          Mail / Delivery Queue &amp; Bounces
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          Delivery Queue, Bounces &amp; Suppression
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Move mail off the request path onto background workers, then process provider webhooks so bounced and complaining recipients are suppressed automatically.
        </p>
        <p className={`text-sm mt-4 ${subtleText}`}>
          Added in <span className="text-aquilia-500 font-semibold">v1.3.5</span>.
        </p>
      </div>

      {/* Why */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Why Queue Mail
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Sending inside a request handler ties the response time of a user-facing endpoint to a third party's SMTP latency. A slow provider makes signup slow; an unreachable provider makes signup fail.
        </p>
        <p className={`mb-4 ${subtleText}`}>
          With the queue enabled, <code className="text-aquilia-500">send_message()</code> persists an envelope, schedules a delivery job, and returns. The SMTP conversation happens on a worker, with retries and backoff managed by the task scheduler — Aquilia reuses the existing task system rather than introducing a second queue.
        </p>
      </section>

      {/* Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Database className="w-5 h-5 text-aquilia-500" />
          Enabling Background Delivery
        </h2>
        <CodeBlock language="python">{`# workspace.py
from aquilia.integrations import Integration

# Inline delivery (default, unchanged)
Integration.mail(default_from="noreply@example.com", providers=[...])

# Background delivery
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
)

# Durable envelopes and suppression, delivered by distributed workers
Integration.tasks(backend="redis", redis_url="redis://cache:6379/0")
Integration.mail(
    default_from="noreply@example.com",
    providers=[...],
    queue_enabled=True,
    queue_persistent=True,
)`}</CodeBlock>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl my-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500 w-64">Option</th>
                <th className="text-left py-4 px-6">Default</th>
                <th className="text-left py-4 px-6">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['queue_enabled', 'False', 'Deliver via background tasks instead of inside the request. Requires a running TaskManager.'],
                ['queue_persistent', 'False', 'Keep envelopes and suppression records in the application database. Requires DatabaseIntegration.'],
                ['queue_dedupe_window_seconds', '3600', 'Window in which an identical send is collapsed rather than sent twice.'],
                ['queue_retention_days', '30', 'How long delivered envelopes are retained.'],
              ].map(([opt, defVal, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono font-semibold text-xs text-aquilia-400">{opt}</td>
                  <td className="py-3.5 px-6 font-mono text-xs">{defVal}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className={`text-sm ${subtleText}`}>
          Call sites do not change. <code className="text-aquilia-500">asend()</code> still returns an envelope ID — it now returns before delivery completes.
        </p>
      </section>

      {/* Checking status */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Tracking an Envelope
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          With the queue enabled, a returned envelope ID means <strong>accepted</strong>, not <strong>delivered</strong>. Poll the store where that distinction matters.
        </p>
        <CodeBlock language="python">{`from aquilia.mail import EmailMessage

envelope_id = await EmailMessage(
    subject="Welcome",
    body="Thanks for signing up",
    to=user.email,
).asend()

envelope = await mail.store.get(envelope_id)
envelope.status     # QUEUED -> SENDING -> SENT / FAILED / BOUNCED / CANCELLED
envelope.attempts`}</CodeBlock>
        <p className={`my-4 ${subtleText}`}>
          The <DocTerm id="mail.MailService">EnvelopeStore</DocTerm> is the durable record of accepted mail. <code className="text-aquilia-500">MemoryEnvelopeStore</code> is the default and is bounded; <code className="text-aquilia-500">SQLEnvelopeStore</code> (table <code className="text-aquilia-500">aquilia_mail_envelopes</code>) is selected by <code className="text-aquilia-500">queue_persistent=True</code>.
        </p>
        <div className="group relative overflow-hidden rounded-xl bg-amber-500/5 border border-amber-500/10 p-4">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5 shrink-0" />
            <p className="text-xs leading-relaxed text-amber-400">
              The delivery job carries an envelope <strong>ID</strong>, not a live envelope object — a job must be JSON-serializable to reach a distributed backend. The worker reloads the envelope from the shared store, which is what lets delivery run on another machine with no API change.
            </p>
          </div>
        </div>
      </section>

      {/* Webhooks */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Webhook className="w-5 h-5 text-emerald-400" />
          Processing Provider Webhooks
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Three parsers normalize each provider's format into a shared vocabulary, and <code className="text-aquilia-500">process_webhook</code> applies the result — suppressing bad addresses and updating envelope status.
        </p>
        <CodeBlock language="python">{`from aquilia import Controller, POST, RequestCtx, Response
from aquilia.mail import parse_ses, process_webhook

class MailWebhookController(Controller):
    prefix = "/webhooks/mail"

    @POST("/ses")
    async def ses(self, ctx: RequestCtx):
        events = parse_ses(await ctx.body(), verify_topic_arn=SES_TOPIC_ARN)
        summary = await process_webhook(
            events,
            suppression=self.mail.suppression,
            store=self.mail.store,
        )
        return Response.json(summary)   # {"suppressed": 2, "delivered": 5, "ignored": 1}`}</CodeBlock>
        <p className={`my-4 ${subtleText}`}>
          Aquilia does not register the route for you — the path, authentication, and CSRF policy belong to the application. Exempt the webhook path from CSRF; providers do not carry your CSRF token.
        </p>
        <CodeBlock language="python">{`parse_ses(payload, *, verify_topic_arn=None)
parse_sendgrid(payload, *, headers=None, public_key=None, max_age_seconds=600.0)
parse_mailgun(payload, *, signing_key=None, max_age_seconds=600.0)`}</CodeBlock>
        <div className="group relative overflow-hidden rounded-xl bg-red-500/5 border border-red-500/10 p-4 mt-6">
          <div className="flex items-start gap-2">
            <ShieldAlert className="w-4 h-4 text-red-400 mt-0.5 shrink-0" />
            <p className="text-xs leading-relaxed text-red-400">
              <strong>Verify signatures in production.</strong> An unverified endpoint lets anyone POST a forged bounce and suppress an arbitrary address — a trivial denial of service against your own users. Pass <code>verify_topic_arn</code> (SES), <code>public_key</code> (SendGrid), or <code>signing_key</code> (Mailgun). Omitting them parses without verification and logs a warning.
            </p>
          </div>
        </div>
      </section>

      {/* Suppression */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Ban className="w-5 h-5 text-rose-400" />
          Suppression Lists
        </h2>
        <p className={`mb-4 ${subtleText}`}>
          Deliverability is reputation, and reputation is destroyed by continuing to mail addresses that bounce. A hard bounce or complaint removes the address from every future send.
        </p>
        <div className="overflow-x-auto rounded-2xl border border-white/5 bg-white/5 backdrop-blur-sm shadow-xl mb-6">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className="border-b border-white/5 bg-white/5">
                <th className="text-left py-4 px-6 font-semibold text-aquilia-500 w-44">Reason</th>
                <th className="text-left py-4 px-6">Permanence</th>
                <th className="text-left py-4 px-6">Meaning</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['HARD_BOUNCE', 'Permanent', 'The address does not exist.'],
                ['SOFT_BOUNCE', 'Expires (24h default)', 'Temporary failure — mailbox full, server down.'],
                ['COMPLAINT', 'Permanent', 'Marked as spam. The most reputation-damaging signal a provider tracks.'],
                ['UNSUBSCRIBE', 'Permanent', 'The recipient opted out.'],
                ['MANUAL', 'Permanent', 'Operator-added.'],
              ].map(([reason, perm, desc], i) => (
                <tr key={i} className="hover:bg-white/5 transition-colors duration-150">
                  <td className="py-3.5 px-6 font-mono font-semibold text-xs text-aquilia-400">{reason}</td>
                  <td className="py-3.5 px-6 text-xs">{perm}</td>
                  <td className={`py-3.5 px-6 text-xs ${subtleText}`}>{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <CodeBlock language="python">{`from aquilia.mail import SuppressionReason

await mail.suppression.suppress(
    "bounced@example.com",
    reason=SuppressionReason.HARD_BOUNCE,
    expires_in=None,          # seconds; ignored for permanent reasons
    provider="ses",
    detail="550 5.1.1 user unknown",
)

await mail.suppression.is_suppressed("Bounced@Example.COM")   # True — normalized
await mail.suppression.unsuppress("bounced@example.com")
await mail.suppression.filter_recipients(emails)              # (allowed, blocked)
await mail.suppression.cleanup()                              # drop expired entries`}</CodeBlock>
        <p className={`my-4 ${subtleText}`}>
          Addresses are lowercased and trimmed before storage and lookup. Suppressed recipients are removed while preparing every envelope; an envelope whose recipients are <em>all</em> suppressed is marked <code className="text-aquilia-500">CANCELLED</code> and never dispatched. An envelope with three recipients where one is suppressed still sends to the other two.
        </p>
      </section>

      {/* Failure modes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Failure Modes
        </h2>
        <div className="space-y-3">
          {[
            ['No task manager, queue enabled', 'Delivery falls back to inline sending. Recording an envelope as queued when nothing can deliver it would silently drop mail. The same applies when a manager exists but has not been started.'],
            ['queue_persistent without a database', 'Logs an error naming the durability that was lost and falls back to in-memory stores rather than aborting startup.'],
            ['Missing envelope at delivery time', 'A delivery job whose envelope was cleaned up or cancelled logs a warning and is treated as success — no amount of retrying will bring it back.'],
            ['MemoryEnvelopeStore eviction', 'The in-memory store evicts oldest-first past max_envelopes; an evicted envelope\'s delivery job finds nothing and gives up. Use queue_persistent=True where that matters.'],
          ].map(([title, desc], i) => (
            <div key={i} className="rounded-xl bg-white/5 border border-white/5 p-4">
              <p className={`text-sm font-semibold mb-1 ${isDark ? 'text-white' : 'text-gray-900'}`}>{title}</p>
              <p className={`text-xs leading-relaxed ${subtleText}`}>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'MailService — building and dispatching messages', link: '/docs/mail/service' },
          { text: 'Providers — SMTP, SES, SendGrid configuration', link: '/docs/mail/providers' },
          { text: 'Distributed & Workflows — the task backend behind the queue', link: '/docs/tasks/distributed' },
          { text: 'Templates — ATS rendering and autoescaping', link: '/docs/mail/templates' },
        ]}
      />
    </div>
  )
}
