import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function SessionsTransport() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionHeaderClass = `text-2xl font-mono font-bold tracking-tight mb-6 flex items-center gap-3 ${
    isDark ? 'text-white' : 'text-gray-900'
  }`
  const textClass = `text-sm leading-relaxed mb-6 ${isDark ? 'text-zinc-400' : 'text-zinc-600'}`

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-12 border-b border-zinc-200 dark:border-zinc-800 pb-8">
        <div className="flex items-center gap-2 text-xs font-mono uppercase tracking-widest text-aquilia-500 mb-4">
          <Globe className="w-4 h-4" />
          Sessions / Transport
        </div>
        <h1 className={`text-4xl font-mono ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          <span className="font-bold tracking-tighter gradient-text relative group inline-block">
            Session Transport
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-zinc-300' : 'text-zinc-700'}`}>
          Transport layers manage how session identifiers travel over HTTP requests and responses. They isolate network details from session state using the <DocTerm id="sessions.transport">SessionTransport</DocTerm> protocol.
        </p>
      </div>

      {/* Protocol */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>SessionTransport Protocol</h2>
        <p className={textClass}>
          All transport adapters implement the synchronous <code className="text-aquilia-500">SessionTransport</code> protocol:
        </p>
        <CodeBlock language="python" filename="protocol.py" highlightLines={[8, 12, 16]}>{`from typing import Protocol
from aquilia.request import Request
from aquilia.response import Response
from aquilia.sessions import Session

class SessionTransport(Protocol):
    """Protocol for session ID transport mechanisms (synchronous methods)."""

    def extract(self, request: Request) -> str | None:
        """Extract a session ID string from the incoming request."""
        ...

    def inject(self, response: Response, session: Session) -> None:
        """Inject the session ID into the outgoing response."""
        ...

    def clear(self, response: Response) -> None:
        """Remove the session ID from the outgoing response (on logout/destroy)."""
        ...`}</CodeBlock>
      </section>

      {/* CookieTransport */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>CookieTransport (HTTP Cookies)</h2>
        <p className={textClass}>
          Sends the session ID as an HTTP cookie. Highly recommended for web browsers as it provides HttpOnly (XSS block), Secure (HTTPS enforce), and SameSite (CSRF block) security parameters via <DocTerm id="sessions.cookie_transport">CookieTransport</DocTerm>.
        </p>
        <CodeBlock language="python" filename="cookie_transport.py" highlightLines={[4, 15, 16, 17, 18]}>{`from aquilia.sessions import CookieTransport, TransportPolicy

# Constructor accepts a TransportPolicy
policy = TransportPolicy(
    adapter="cookie",
    cookie_name="aquilia_web_session",
    cookie_httponly=True,
    cookie_secure=True,
    cookie_samesite="strict",
    cookie_path="/",
)
transport = CookieTransport(policy)

# Factory methods for pre-configured defaults:
transport_web = CookieTransport.for_web_browsers()
transport_spa = CookieTransport.for_spa_applications()
transport_mobile = CookieTransport.for_mobile_webviews()
transport_default = CookieTransport.with_aquilia_defaults()`}</CodeBlock>
      </section>

      {/* HeaderTransport */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>HeaderTransport (Custom Headers)</h2>
        <p className={textClass}>
          Transports the session ID using custom headers. Best suited for stateless REST APIs, mobile apps, or inter-service communications where cookies are difficult to handle, implemented via <DocTerm id="sessions.header_transport">HeaderTransport</DocTerm>.
        </p>
        <CodeBlock language="python" filename="header_transport.py" highlightLines={[4, 10, 11, 12, 13]}>{`from aquilia.sessions import HeaderTransport, TransportPolicy

# Constructor accepts a TransportPolicy
policy = TransportPolicy(adapter="header", header_name="X-Session-ID")
transport = HeaderTransport(policy)

# Factory methods for pre-configured defaults:
transport_rest = HeaderTransport.for_rest_apis()
transport_graphql = HeaderTransport.for_graphql_apis()
transport_mobile = HeaderTransport.for_mobile_apis()
transport_service = HeaderTransport.for_microservices()
transport_default = HeaderTransport.with_aquilia_defaults()`}</CodeBlock>
      </section>

      {/* create_transport Factory */}
      <section className="mb-16">
        <h2 className={sectionHeaderClass}>create_transport() Factory</h2>
        <p className={textClass}>
          Helper utility function to initialize transport adapters directly from policy configurations:
        </p>
        <CodeBlock language="python" filename="factory.py" highlightLines={[4]}>{`from aquilia.sessions import create_transport, TransportPolicy

policy = TransportPolicy(adapter="cookie", cookie_name="my_custom_cookie")
transport = create_transport(policy)`}</CodeBlock>
      </section>

      {/* Custom Transport */}
      <section className="mb-16 border-t border-zinc-200 dark:border-zinc-800 pt-12">
        <h2 className={sectionHeaderClass}>Building a Custom Transport</h2>
        <p className={textClass}>
          Create custom transport layers (for example, reading token properties from custom JSON payloads or Authorization headers) by matching the protocol:
        </p>
        <CodeBlock language="python" filename="bearer_transport.py" highlightLines={[9, 15, 18]}>{`from aquilia.request import Request
from aquilia.response import Response
from aquilia.sessions import Session

class BearerTokenTransport:
    """Custom transport for extracting session IDs from the Authorization Bearer header."""

    def extract(self, request: Request) -> str | None:
        auth = request.header("authorization") or ""
        if auth.startswith("Bearer "):
            return auth[7:]
        return None

    def inject(self, response: Response, session: Session) -> None:
        response.headers["Authorization"] = f"Bearer {str(session.id)}"

    def clear(self, response: Response) -> None:
        if "Authorization" in response.headers:
            del response.headers["Authorization"]`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
