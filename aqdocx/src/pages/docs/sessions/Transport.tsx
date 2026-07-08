import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SessionsTransport() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Globe className="w-4 h-4" />
          Sessions / Transport
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Session Transport
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Transport layers manage how session identifiers travel over HTTP requests and responses.
        </p>
      </div>

      {/* Protocol */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>SessionTransport Protocol</h2>
        <CodeBlock language="python" filename="protocol.py">{`from typing import Protocol
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
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>CookieTransport</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Sends the session ID as an HTTP cookie. Best for browser-based client environments where cookies are automatically handled.
        </p>
        <CodeBlock language="python" filename="cookie_transport.py">{`from aquilia.sessions import CookieTransport, TransportPolicy

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

# Factory methods (no parameters accepted, pre-configured defaults):
transport_web = CookieTransport.for_web_browsers()
transport_spa = CookieTransport.for_spa_applications()
transport_mobile = CookieTransport.for_mobile_webviews()
transport_default = CookieTransport.with_aquilia_defaults()`}</CodeBlock>
      </section>

      {/* HeaderTransport */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>HeaderTransport</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Transports the session ID using custom headers. Best for APIs and mobile applications.
        </p>
        <CodeBlock language="python" filename="header_transport.py">{`from aquilia.sessions import HeaderTransport, TransportPolicy

# Constructor accepts a TransportPolicy
policy = TransportPolicy(adapter="header", header_name="X-Session-ID")
transport = HeaderTransport(policy)

# Factory methods:
transport_rest = HeaderTransport.for_rest_apis()
transport_graphql = HeaderTransport.for_graphql_apis()
transport_mobile = HeaderTransport.for_mobile_apis()
transport_service = HeaderTransport.for_microservices()
transport_default = HeaderTransport.with_aquilia_defaults()`}</CodeBlock>
      </section>

      {/* create_transport Factory */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>create_transport() Factory</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Use the factory function to create transport adapters from a `TransportPolicy` object:
        </p>
        <CodeBlock language="python" filename="factory.py">{`from aquilia.sessions import create_transport, TransportPolicy

policy = TransportPolicy(adapter="cookie", cookie_name="my_custom_cookie")
transport = create_transport(policy)`}</CodeBlock>
      </section>

      {/* Custom Transport */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Building a Custom Transport</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Implement the `SessionTransport` protocol using synchronous methods:
        </p>
        <CodeBlock language="python" filename="bearer_transport.py">{`from aquilia.request import Request
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
