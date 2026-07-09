import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { FlaskConical, Layers, Globe, Radio } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function TestingClient() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = "mb-16 scroll-mt-24"
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`

  return (
    <div className="max-w-4xl mx-auto pb-20">
      <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <FlaskConical className="w-4 h-4" />
          Testing / TestClient
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            TestClient & WebSockets
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <DocTerm id="testing.test_client">TestClient</DocTerm> provides an in-process ASGI runner that executes mock HTTP requests and streams, recording responses without binding to a network port. The <DocTerm id="testing.websocket_client">WebSocketTestClient</DocTerm> lets you test real-time event subscriptions and back-channel messages.
        </p>
      </div>

      {/* HTTP Client Usage */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Globe className="w-5 h-5 text-aquilia-400" />
          HTTP Client API
        </h2>
        <p className={pClass}>
          The client supports cookie persistence across redirects, customizable request headers, query encoding, and file uploads:
        </p>
        <CodeBlock language="python" filename="test_http.py" highlightLines={[6, 9, 16, 17, 18]}>{`from aquilia.testing import TestClient

async def test_auth_and_uploads():
    async with TestClient(app) as client:
        # Set authorization header for subsequent requests
        client.set_bearer_token("my-jwt-token")
        
        # Perform standard POST with JSON
        resp = await client.post("/api/posts", json={"title": "Hello"})
        assert resp.status_code == 201
        
        # Perform file upload (multipart/form-data)
        file_data = b"image bytes data here"
        resp = await client.post(
            "/api/avatars",
            files={"avatar": ("profile.png", file_data, "image/png")},
            data={"caption": "New Profile"}
        )
        assert resp.status_code == 200`}</CodeBlock>

        <h3 className={h3Class}>HTTP Methods</h3>
        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 text-left">
                <th className="px-4 py-3 font-semibold">Method</th>
                <th className="px-4 py-3 font-semibold">Call Signature</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-150 text-gray-700'}`}>
              {[
                ['GET', 'client.get(path, headers=None, query_string="", follow_redirects=None)'],
                ['POST', 'client.post(path, json=None, data=None, body=b"", files=None, headers=None)'],
                ['PUT', 'client.put(path, json=None, body=b"", files=None, headers=None)'],
                ['PATCH', 'client.patch(path, json=None, body=b"", files=None, headers=None)'],
                ['DELETE', 'client.delete(path, headers=None)'],
                ['HEAD', 'client.head(path, headers=None)'],
                ['OPTIONS', 'client.options(path, headers=None)']
              ].map(([method, signature], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{method}</td>
                  <td className="px-4 py-2 font-mono text-xs">{signature}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Response Object */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Layers className="w-5 h-5 text-aquilia-400" />
          TestResponse API
        </h2>
        <p className={pClass}>
          HTTP requests return a <code className="text-aquilia-500">TestResponse</code> wrapper instance that packs response statistics, headers, and bodies:
        </p>
        <CodeBlock language="python" filename="test_response.py" highlightLines={[4, 11, 16]}>{`resp = await client.get("/api/users/1")

# Status codes
resp.status_code        # e.g., 200
resp.is_success         # True if 2xx
resp.is_redirect        # True if 3xx
resp.is_client_error    # True if 4xx
resp.is_server_error    # True if 5xx

# Content readers
resp.json()             # Parsed JSON object (memoized)
resp.text               # Body string decoded as utf-8 or specified charset
resp.body               # Raw bytes content

# Metadata
resp.headers            # dict of lowercase headers
resp.content_type       # Content type string (e.g. "application/json")
resp.location           # Location redirect header value
resp.elapsed            # Time taken in milliseconds`}</CodeBlock>
      </section>

      {/* WebSockets */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Radio className="w-5 h-5 text-aquilia-400" />
          WebSocket Testing
        </h2>
        <p className={pClass}>
          Test WebSocket interactions using <DocTerm id="testing.websocket_client">WebSocketTestClient</DocTerm>, which mirrors connection states and message channels asynchronously:
        </p>
        <CodeBlock language="python" filename="test_ws.py" highlightLines={[5, 7, 11, 14, 18]}>{`from aquilia.testing import WebSocketTestClient

async def test_websocket_messaging():
    # Instantiate client over your ASGI server
    async with WebSocketTestClient(app) as ws:
        # Initiate connection handshake
        await ws.connect("/ws/events")
        assert ws.is_connected
        
        # Send text or JSON events
        await ws.send_json({"event": "ping", "data": "hello"})
        
        # Receive text or JSON
        data = await ws.receive_json(timeout=2.0)
        assert data["event"] == "pong"
        
        # Terminate connection
        await ws.close(code=1000)`}</CodeBlock>


        <h3 className={h3Class}>WebSocket Methods</h3>
        <div className="overflow-x-auto py-2">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 text-left">
                <th className="px-4 py-3 font-semibold">Method / Attribute</th>
                <th className="px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-150 text-gray-700'}`}>
              {[
                ['connect(path, headers=None, subprotocols=None)', 'Initiate connection handshake.'],
                ['send_text(text)', 'Send text payload.'],
                ['send_json(data)', 'Send serialized JSON payload.'],
                ['send_bytes(data)', 'Send binary bytes payload.'],
                ['receive(timeout=5.0)', 'Awaits raw ASGI receive event dictionary.'],
                ['receive_text(timeout=5.0)', 'Awaits string packet.'],
                ['receive_json(timeout=5.0)', 'Awaits parsed JSON structure.'],
                ['receive_bytes(timeout=5.0)', 'Awaits binary bytes payload.'],
                ['close(code=1000)', 'Sends disconnect event and tears down uvicorn loops.'],
                ['is_connected', 'Boolean property check.']
              ].map(([meth, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{meth}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}