import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function MailProviders() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderMuted = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto px-4 py-2">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Layers className="w-4 h-4" />
          Mail / Providers
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono">Mail Providers & Backends</span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          All email backends implement the standard <DocTerm id="mail.MailIntegration">IMailProvider</DocTerm> protocol, allowing you to swap backends between local files, stdout consoles, and cloud providers (SMTP, SES, SendGrid) without changing your application code.
        </p>
      </div>

      {/* Provider Types */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Pluggable Backends Comparison
        </h2>
        <div className="space-y-6 text-sm font-sans">
          {[
            { name: 'SMTPProvider', deps: 'aiosmtplib', desc: 'Standard SMTP relay client. Supports SSL/TLS encryption, credentials, and connection pools.' },
            { name: 'SESProvider', deps: 'aiobotocore', desc: 'AWS Simple Email Service integration. Interacts asynchronously via AWS IAM credentials.' },
            { name: 'SendGridProvider', deps: 'httpx', desc: 'SendGrid Web API v3 client. Optimizes transmission speeds using HTTP request batching.' },
            { name: 'ConsoleProvider', deps: 'None', desc: 'Development fallback. Prints raw mail payloads to standard output stream (stdout).' },
            { name: 'FileProvider', deps: 'None', desc: 'Test and audit utility. Writes raw .eml envelopes to a local workspace folder.' }
          ].map((item, i) => (
            <div key={i} className="py-4 border-b border-white/5 last:border-0">
              <div className="flex items-center justify-between gap-4 mb-2">
                <span className="text-aquilia-400 font-mono text-sm font-semibold">{item.name}</span>
                <span className={`flex-shrink-0 text-[10px] uppercase tracking-wider ${isDark ? 'text-gray-500' : 'text-gray-400'} font-mono`}>
                  deps: {item.deps}
                </span>
              </div>
              <p className={`text-sm ${textMuted}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* IMailProvider Protocol API */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          IMailProvider Custom Implementation
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          To write a custom provider (e.g., Postmark API), implement the <DocTerm id="mail.MailIntegration">IMailProvider</DocTerm> interface using `httpx` async clients, error handling structures, and status code maps:
        </p>
        <CodeBlock
          language="python"
          filename="custom_postmark_provider.py"
          highlightLines={[7, 10, 20, 27, 34, 40]}
        >{`import httpx
from aquilia.mail.providers import IMailProvider, ProviderResult, ProviderResultStatus
from aquilia.mail import MailEnvelope

class PostmarkMailProvider(IMailProvider):
    name = "postmark"
    supports_batching = False
    max_batch_size = 1

    def __init__(self, api_token: str):
        self.api_token = api_token
        self.client = None

    async def initialize(self) -> None:
        # Open a persistent connection pool with server credentials
        self.client = httpx.AsyncClient(
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Postmark-Server-Token": self.api_token
            },
            timeout=10.0
        )

    async def send(self, envelope: MailEnvelope) -> ProviderResult:
        payload = {
            "From": envelope.from_email,
            "To": ",".join(envelope.to),
            "Subject": envelope.subject,
            "HtmlBody": envelope.body_html,
            "TextBody": envelope.body_text
        }
        try:
            response = await self.client.post("https://api.postmarkapp.com/email", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                return ProviderResult(
                    status=ProviderResultStatus.SUCCESS,
                    provider_message_id=data.get("MessageID")
                )
            elif response.status_code == 422:
                # Permanent failure (e.g. invalid recipient address format)
                return ProviderResult(
                    status=ProviderResultStatus.PERMANENT_FAILURE,
                    error_message=response.text
                )
            elif response.status_code == 429:
                # Rate limited, request retry backoff duration
                return ProviderResult(
                    status=ProviderResultStatus.RATE_LIMITED,
                    retry_after=float(response.headers.get("Retry-After", 60))
                )
            else:
                return ProviderResult(
                    status=ProviderResultStatus.TRANSIENT_FAILURE,
                    error_message=f"HTTP Error {response.status_code}: {response.text}"
                )
        except Exception as e:
            # Handle socket/timeout exceptions as transient retry attempts
            return ProviderResult(
                status=ProviderResultStatus.TRANSIENT_FAILURE, 
                error_message=str(e)
            )

    async def health_check(self) -> bool:
        try:
            res = await self.client.get("https://status.postmarkapp.com/api/v2/status.json")
            return res.status_code == 200
        except Exception:
            return False

    async def shutdown(self) -> None:
        if self.client:
            await self.client.aclose()`}</CodeBlock>
      </section>

      {/* Provider Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Provider Configurations
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          Configure individual providers as list parameters inside the typed <DocTerm id="mail.MailIntegration">MailIntegration</DocTerm>:
        </p>
        <CodeBlock
          language="python"
          filename="providers_list.py"
          highlightLines={[8, 14, 18]}
        >{`from aquilia.integrations import (
    MailIntegration, SmtpProvider, SesProvider, SendGridProvider
)

workspace.integrate(MailIntegration(
    providers=[
        # 1. Standard SMTP Server
        SmtpProvider(
            host="smtp.gmail.com", port=587, 
            use_tls=True, timeout=15
        ),
        # 2. Amazon SES
        SesProvider(
            region="us-east-1",
            aws_access_key_id="AKIA...",
            aws_secret_access_key="secret"
        ),
        # 3. SendGrid
        SendGridProvider(
            api_key="SG.xxx"
        )
    ]
))`}</CodeBlock>
      </section>

      {/* MailProviderRegistry */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          MailProviderRegistry & Auto-Discovery
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          The mail subsystem leverages Aquilia's <code className="text-aquilia-400">PackageScanner</code> to auto-discover provider classes. Register custom provider packages to make them auto-wireable:
        </p>
        <CodeBlock
          language="python"
          filename="discover_providers.py"
          highlightLines={[5, 8]}
        >{`from aquilia.mail.di_providers import MailProviderRegistry

registry = MailProviderRegistry()

# 1. Register custom package to scan for IMailProvider classes
registry.add_scan_package("myapp.mail_providers")

# 2. Discover classes and get custom mapping
discovered_types = registry.discover()
# Result: {"smtp": SMTPProvider, "ses": SESProvider, "custom_http": CustomHttpProvider}`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/mail/service" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> MailService
        </Link>
        <Link to="/docs/mail/templates" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Mail Templates <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'Aquilia Template Syntax (ATS)', link: '/docs/mail/templates' },
          { text: 'Developer Integration Guide', link: '/docs/developer-guide' },
        ]}
      />
    </div>
  )
}