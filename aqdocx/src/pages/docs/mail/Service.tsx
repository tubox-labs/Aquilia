import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Server } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MailService() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderMuted = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto px-4 py-2">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Server className="w-4 h-4" />
          Mail / MailService
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono">MailService API</span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          The <DocTerm id="mail.MailService">MailService</DocTerm> orchestrates email compilation, DKIM signing, rate limiting, and provider dispatch. Learn how to build messages, attach files, set custom headers, and handle errors.
        </p>
      </div>

      {/* Extended Message Compiles Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          EmailMessage API Usages
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          Construct plain-text or HTML-alternative emails using <DocTerm id="mail.EmailMessage">EmailMessage</DocTerm> and <code className="text-aquilia-400">EmailMultiAlternatives</code>:
        </p>

        <CodeBlock
          language="python"
          filename="send_emails.py"
          highlightLines={[7, 18, 25]}
        >{`from aquilia.mail import EmailMessage, EmailMultiAlternatives, Attachment

# 1. Simple Plain Text Email
msg = EmailMessage(
    subject="Invoice #2041",
    body="Your invoice is attached.",
    from_email="billing@myapp.com",
    to=["client@example.com"],
    cc=["accountant@myapp.com"],
    priority=80,  # High priority (default is 50)
    headers={"X-Invoice-ID": "2041"}
)

# Add attachment
msg.attach(Attachment(filename="invoice.pdf", content=b"...pdf_bytes...", content_type="application/pdf"))
await msg.asend()

# 2. HTML Alternative Email
html_msg = EmailMultiAlternatives(
    subject="Monthly Newsletter",
    body="Read the newsletter online at https://myapp.com/newsletter",
    from_email="newsletter@myapp.com",
    to=["user@example.com"]
)
# Attach the HTML body alternative
html_msg.attach_alternative("<h1>Our Monthly Updates</h1><p>Here is the news...</p>", content_type="text/html")
await html_msg.asend()`}</CodeBlock>
      </section>

      {/* MailEnvelope Structure */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          The MailEnvelope Dataclass
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          When messages are processed, they are converted into an immutable <code className="text-aquilia-400">MailEnvelope</code> that represents the delivery unit of work:
        </p>

        <CodeBlock
          language="python"
          filename="envelope_schema.py"
          highlightLines={[7, 10, 16, 21, 25]}
        >{`from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

@dataclass
class MailEnvelope:
    id: str                       # Unique UUID tracking string
    created_at: datetime          # Creation timestamp

    # Queue Priority
    priority: int = 50            # Priority rating (0-100)

    # Addressing
    from_email: str = ""          # Normalized sender address
    to: list[str] = field(default_factory=list)
    cc: list[str] = field(default_factory=list)
    bcc: list[str] = field(default_factory=list)
    reply_to: str | None = None

    # Content
    subject: str = ""             # Pre-interpolated subject line
    body_text: str = ""           # Plain text representation
    body_html: str | None = None  # HTML alternative body
    headers: dict[str, str] = field(default_factory=dict)

    # Attachments
    attachments: list[Attachment] = field(default_factory=list)

    # Idempotency & Verification
    idempotency_key: str | None = None
    digest: str = ""              # SHA-256 checksum hash of the envelope`}</CodeBlock>
      </section>

      {/* Fault Hierarchy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Mail Fault Handling
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          The mail subsystem raises structured exceptions based on the failure domain:
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 text-sm mb-6">
          {[
            { name: 'MailFault', desc: 'Base structured exception class for all mail errors.' },
            { name: 'MailSendFault', desc: 'Raised when mail delivery fails on the network or provider backend.' },
            { name: 'MailTemplateFault', desc: 'Raised when compilation of an ATS template fails due to syntax or file discovery.' },
            { name: 'MailValidationFault', desc: 'Raised early when recipient email syntax, Display Names, or structures fail checks.' },
            { name: 'MailRateLimitFault', desc: 'Raised when message dispatch speeds exceed set global/domain thresholds.' }
          ].map((f, i) => (
            <div key={i} className="pl-4 border-l border-red-500/20 hover:border-red-500/50 transition-colors duration-200">
              <h4 className={`text-xs font-semibold mb-1 font-mono ${isDark ? 'text-red-400' : 'text-red-600'}`}>{f.name}</h4>
              <p className={`text-xs ${textMuted}`}>{f.desc}</p>
            </div>
          ))}
        </div>

        <CodeBlock
          language="python"
          filename="exception_handling.py"
        >{`from aquilia.mail import TemplateMessage
from aquilia.faults import MailSendFault, MailValidationFault

try:
    msg = TemplateMessage(
        template="welcome.aqt",
        subject="Welcome!",
        to=["invalid-email-format"]
    )
    await msg.asend()
except MailValidationFault as e:
    print(f"Validation failed: {e.message}")
except MailSendFault as e:
    print(f"Network delivery failed: {e.message}")`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/mail" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/mail/providers" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Providers <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'Mail Providers (SMTP, SES, SendGrid)', link: '/docs/mail/providers' },
          { text: 'Aquilia Template Syntax (ATS)', link: '/docs/mail/templates' },
          { text: 'Developer Integration Guide', link: '/docs/developer-guide' },
        ]}
      />
    </div>
  )
}