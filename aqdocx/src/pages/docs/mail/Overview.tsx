import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Mail } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MailOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderMuted = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto px-4 py-2">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Mail className="w-4 h-4" />
          Advanced / Mail
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono">Mail System Overview</span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          AquilaMail is a production-ready mail dispatching subsystem featuring pluggable providers (SMTP, AWS SES, SendGrid), DKIM signing, automatic rate limiting, retry backoffs, and an integrated testing outbox.
        </p>
      </div>

      {/* Integration Guide */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          System Integration & Registration
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          To enable email operations, declare the Mail integration at the workspace level, configure templates, and inject the service into your module endpoints.
        </p>

        {/* Workspace Level */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Workspace Integration</h3>
          <p className={`text-sm mb-4 ${textMuted}`}>
            Register Mail in <code className="text-aquilia-400">workspace.py</code> using <DocTerm id="mail.MailIntegration">MailIntegration</DocTerm>:
          </p>
          <CodeBlock
            language="python"
            filename="workspace.py"
            highlightLines={[6, 7]}
          >{`from aquilia.workspace import Workspace
from aquilia.integrations import MailIntegration, SmtpProvider, MailAuth

workspace = (
    Workspace("myapp")
    .integrate(MailIntegration(
        default_from="noreply@myapp.com",
        subject_prefix="[MyApp] ",
        auth=MailAuth.plain("smtp_user", password_env="SMTP_PASSWORD"),
        providers=[
            SmtpProvider(host="smtp.sendgrid.net", port=587, use_tls=True)
        ],
        rate_limit_global=1000,
        dkim_enabled=False
    ))
)`}</CodeBlock>
        </div>

        {/* Injection Level */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Injecting Mail Service in Modules</h3>
          <p className={`text-sm mb-4 ${textMuted}`}>
            Inject <DocTerm id="mail.MailService">MailService</DocTerm> directly into controllers or services to access the sending APIs:
          </p>
          <CodeBlock
            language="python"
            filename="modules/auth/controllers.py"
            highlightLines={[8]}
          >{`from aquilia import Controller, Post, Inject
from aquilia.mail import MailService, TemplateMessage

class AuthController(Controller):
    prefix = "/auth"

    @Inject()
    def __init__(self, mail: MailService):
        self.mail = mail

    @Post("/notify")
    async def notify(self, ctx):
        msg = TemplateMessage(
            template="alert.aqt",
            context={"user": ctx.identity},
            subject="Security Alert",
            to=[ctx.identity.email]
        )
        await msg.asend()
        return ctx.json({"sent": True})`}</CodeBlock>
        </div>
      </section>

      {/* Subsystem Components */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Core Mail Architectures
        </h2>
        <div className="space-y-8">
          {[
            {
              name: 'MailService',
              id: 'mail.MailService',
              desc: 'Orchestrates the delivery pipeline. Receives built envelopes, verifies DKIM keys, applies rate limit locks, and routes payloads to active providers.'
            },
            {
              name: 'EmailMessage',
              id: 'mail.EmailMessage',
              desc: 'Standard envelope wrapper. Supports multiple recipients (to, cc, bcc), priority flags, attachments, and headers.'
            },
            {
              name: 'TemplateMessage',
              id: 'mail.TemplateMessage',
              desc: 'Subclass of EmailMessage. Compiles HTML or plain text bodies dynamically from templates using Aquilia Template Syntax (ATS).'
            },
            {
              name: 'SMTPProvider',
              id: 'mail.MailIntegration',
              desc: 'Async SMTP sender supporting SSL/TLS, username/password authentications, and aiosmtplib connections.'
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

      {/* Testing Section */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Testing Outbox Assertions
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          During testing, the mail system captures outbound emails into an in-memory outbox list rather than dispatching them to external SMTP servers:
        </p>
        <CodeBlock
          language="python"
          filename="test_mail_flow.py"
          highlightLines={[7, 10, 11]}
        >{`from aquilia.testing import AquiliaTestCase, MailTestMixin

class RegistrationTestCase(AquiliaTestCase, MailTestMixin):

    async def test_registration_welcomes(self):
        await self.client.post("/auth/register")
        
        # Verify that exactly one email was sent
        self.assert_mail_sent(count=1)
        
        # Pull the message from outbox and assert properties
        sent_msg = self.get_sent_mail()[0]
        assert sent_msg.to == "user@example.com"
        assert "Welcome!" in sent_msg.subject`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/templates/security" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Security
        </Link>
        <Link to="/docs/mail/service" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          MailService <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'MailService & Envelope Options', link: '/docs/mail/service' },
          { text: 'Provider Backends (SMTP, SES)', link: '/docs/mail/providers' },
          { text: 'Jinja ATS Template Compiles', link: '/docs/mail/templates' },
        ]}
      />
    </div>
  )
}