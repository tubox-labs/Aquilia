import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SessionsTransport() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

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
          Transport layers control how session identifiers travel between client and server. Aquilia provides <code className="text-aquilia-500">CookieTransport</code> for browser-based apps and <code className="text-aquilia-500">HeaderTransport</code> for APIs, both implementing the <code className="text-aquilia-500">SessionTransport</code> protocol.
        </p>
      </div>

      {/* Protocol */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>SessionTransport Protocol</h2>
        <CodeBlock language="python" filename="protocol.py">{`from typing import Protocol, Optional
from aquilia.sessions import SessionID


class SessionTransport(Protocol):
    """Protocol for session ID transport mechanisms."""

    async def extract(self, request) -> Optional[SessionID]:
        """Extract a session ID from the incoming request.
        Returns None if no session ID is present."""
        ...

    async def inject(self, response, session_id: SessionID) -> None:
        """Inject a session ID into the outgoing response."""
        ...

    async def clear(self, response) -> None:
        """Remove the session ID from the outgoing response.
        Used when destroying a session."""
        ...`}</CodeBlock>
      </section>

      {/* CookieTransport */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>CookieTransport</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Sends the session ID as an HTTP cookie. Ideal for traditional web applications and SPAs where the browser automatically includes the cookie with every request.
        </p>
        <CodeBlock language="python" filename="cookie_transport.py">{`from aquilia.sessions import CookieTransport

# Direct construction with full control
transport = CookieTransport(
    cookie_name="aq_session",
    path="/",
    domain="example.com",
    httponly=True,          # Not accessible via JavaScript
    secure=True,            # HTTPS only
    samesite="lax",         # CSRF protection: "strict" | "lax" | "none"
    max_age=7200,           # Cookie lifetime in seconds
)

# Factory methods for common configurations:

# Standard web browsers (SSR apps, traditional web)
transport = CookieTransport.for_web_browsers(
    domain="example.com",
    cookie_name="aq_session",    # optional
)
# → HttpOnly=True, Secure=True, SameSite=Lax

# Single-Page Applications (SPA with separate API)
transport = CookieTransport.for_spa_applications(
    domain=".example.com",       # dot-prefix for subdomains
    samesite="none",             # Cross-origin requests
)
# → HttpOnly=True, Secure=True, SameSite=None

# Mobile WebViews
transport = CookieTransport.for_mobile_webviews()
# → HttpOnly=True, Secure=True, SameSite=Lax, no domain restriction`}</CodeBlock>

        <h3 className={`text-xl font-semibold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>How It Works</h3>
        <CodeBlock language="python" filename="cookie_flow.py">{`# Phase 1 — Detection: Extract from Cookie header
session_id = await transport.extract(request)
# Reads: Cookie: aq_session=sess_A1b2C3d4E5f6...
# Returns: SessionID("sess_A1b2C3d4E5f6...")

# Phase 7 — Emission: Inject into Set-Cookie header
await transport.inject(response, session.id)
# Sets: Set-Cookie: aq_session=sess_A1b2C3d4E5f6...; 
#        Path=/; Domain=example.com; HttpOnly; Secure; SameSite=Lax; Max-Age=7200

# On destroy: Clear the cookie
await transport.clear(response)
# Sets: Set-Cookie: aq_session=; Max-Age=0; Path=/; ...`}</CodeBlock>
      </section>

      {/* HeaderTransport */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>HeaderTransport</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Sends the session ID in a custom HTTP header. Ideal for REST APIs, GraphQL endpoints, mobile apps, and microservice-to-microservice communication.
        </p>
        <CodeBlock language="python" filename="header_transport.py">{`from aquilia.sessions import HeaderTransport

# Direct construction
transport = HeaderTransport(
    request_header="X-Session-ID",     # Header name for incoming requests
    response_header="X-Session-ID",    # Header name for outgoing responses
)

# Factory methods:

# REST APIs
transport = HeaderTransport.for_rest_apis(
    header_name="X-Session-ID",        # optional, this is the default
)

# GraphQL APIs (uses Authorization-style header)
transport = HeaderTransport.for_graphql_apis(
    header_name="X-Session-Token",
)

# Mobile native apps
transport = HeaderTransport.for_mobile_apis(
    header_name="X-Device-Session",
)

# Microservices (internal service mesh)
transport = HeaderTransport.for_microservices(
    header_name="X-Internal-Session",
)`}</CodeBlock>

        <h3 className={`text-xl font-semibold mt-8 mb-3 ${isDark ? 'text-white' : 'text-gray-900'}`}>How It Works</h3>
        <CodeBlock language="python" filename="header_flow.py">{`# Phase 1 — Detection: Extract from request header
session_id = await transport.extract(request)
# Reads: X-Session-ID: sess_A1b2C3d4E5f6...
# Returns: SessionID("sess_A1b2C3d4E5f6...")

# Phase 7 — Emission: Inject into response header
await transport.inject(response, session.id)
# Sets: X-Session-ID: sess_A1b2C3d4E5f6...

# Client usage:
# fetch("/api/data", {
#   headers: { "X-Session-ID": "sess_A1b2C3d4E5f6..." }
# })`}</CodeBlock>
      </section>

      {/* create_transport Factory */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>create_transport() Factory</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">create_transport()</code> factory auto-selects the appropriate transport based on a string key:
        </p>
        <CodeBlock language="python" filename="factory.py">{`from aquilia.sessions import create_transport

# Create by name
cookie_transport = create_transport("cookie", domain="example.com")
header_transport = create_transport("header", header_name="X-Session-ID")

# Used internally by SessionPolicyBuilder:
policy = (
    SessionPolicyBuilder("web")
    .web_defaults()   # calls create_transport("cookie", ...)
    .build()
)

policy = (
    SessionPolicyBuilder("api")
    .api_defaults()   # calls create_transport("header", ...)
    .build()
)`}</CodeBlock>
      </section>

      {/* Comparison */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Transport Comparison</h2>
        <div className={`overflow-x-auto ${boxClass}`}>
          <table className="w-full text-sm">
            <thead>
              <tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
                <th className="text-left py-2 pr-4 font-semibold">Feature</th>
                <th className="text-left py-2 pr-4 font-semibold">CookieTransport</th>
                <th className="text-left py-2 font-semibold">HeaderTransport</th>
              </tr>
            </thead>
            <tbody className={isDark ? 'text-gray-400' : 'text-gray-600'}>
              {[
                ['Auto-sent by browser', '✅ Yes', '❌ No (manual)'],
                ['CSRF protection', '✅ SameSite attribute', '✅ Inherent (CORS)'],
                ['HttpOnly protection', '✅ JS cannot read', 'N/A'],
                ['Cross-origin', '⚠️ SameSite=None', '✅ Via CORS headers'],
                ['Mobile native', '⚠️ WebView only', '✅ Full control'],
                ['Microservices', '❌ Not practical', '✅ Standard approach'],
                ['Token storage', 'Browser cookie jar', 'Client-side (localStorage/memory)'],
              ].map(([feature, cookie, header], i) => (
                <tr key={i} className={`border-b ${isDark ? 'border-white/5' : 'border-gray-100'}`}>
                  <td className="py-2 pr-4 font-semibold text-xs">{feature}</td>
                  <td className="py-2 pr-4 text-xs">{cookie}</td>
                  <td className="py-2 text-xs">{header}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Custom Transport */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Building a Custom Transport</h2>
        <CodeBlock language="python" filename="jwt_transport.py">{`from typing import Optional
from aquilia.sessions import SessionID


class BearerTokenTransport:
    """Extract session ID from Authorization: Bearer header."""

    async def extract(self, request) -> Optional[SessionID]:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer sess_"):
            return SessionID(auth[len("Bearer "):])
        return None

    async def inject(self, response, session_id: SessionID) -> None:
        response.headers["Authorization"] = f"Bearer {session_id.value}"

    async def clear(self, response) -> None:
        response.headers.pop("Authorization", None)


# Register:
engine = SessionEngine(
    transports={
        "bearer": BearerTokenTransport(),
        "cookie": CookieTransport.for_web_browsers(domain="example.com"),
    },
    # ...
)`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
