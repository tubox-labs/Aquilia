import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Server } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function WebSocketRuntime() {
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
          WebSockets / Runtime
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono">WebSocket Runtime</span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          The AquilaSockets runtime manages connection lifecycles, upgrades ASGI HTTP connections to WebSockets, decodes incoming messages, runs auth guards, and coordinates pub/sub scaling.
        </p>
      </div>

      {/* Lifespan timeline */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Handshake & Lifespan Cycle
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          When a client connects to a SocketController route, the runtime coordinates the lifecycle through these phases:
        </p>
        <div className="space-y-6">
          {[
            { step: '1. Handshake Auth Upgrade', desc: 'The server receives the HTTP GET request containing upgrade headers. It runs the class-level @Guard check_handshake routines to authenticate early.' },
            { step: '2. Connection Establish', desc: 'Once upgraded, the socket transitions to the open state. The runtime instantiates a connection-scoped container and invokes the @OnConnect event.' },
            { step: '3. Message Processing Loop', desc: 'An ASGI listen loop receives frames, decodes them to MessageEnvelope dicts, validates schemas, executes method-level @Guard check_message routines, and dispatches events.' },
            { step: '4. Teardown & Disconnection', desc: 'Upon socket close (cleanly or via heartbeat drops), the runtime triggers @OnDisconnect, exits rooms, and disposes the request-scoped dependency container.' }
          ].map((item, i) => (
            <div key={i} className="pl-4 border-l border-white/10 hover:border-aquilia-500/50 transition-colors duration-200">
              <h4 className={`text-sm font-semibold mb-1 font-mono ${isDark ? 'text-white' : 'text-gray-900'}`}>{item.step}</h4>
              <p className={`text-xs ${textMuted}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Built-in Guards */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Built-in Security Guards
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          Guards inherit from the base <code className="text-aquilia-400">SocketGuard</code> protocol class and are applied via <code className="text-aquilia-400">@Guard</code> decorators. They can intercept either the initial HTTP handshake or individual incoming client messages.
        </p>

        <div className="space-y-8 text-sm">
          <div>
            <h3 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'} font-mono`}>
              1. HandshakeAuthGuard
            </h3>
            <p className={`mb-3 ${textMuted}`}>
              Authenticates and authorizes connections during the initial HTTP upgrade handshake phase. If the check fails, the connection is aborted immediately.
            </p>
            <CodeBlock language="python">{`from aquilia.sockets import Guard, HandshakeAuthGuard

# Require a valid user identity that is flagged as an admin
@Guard(HandshakeAuthGuard(
    require_identity=True, 
    require_session=True, 
    allowed_identity_types=["admin"]
))
class AdminSocketController(SocketController):
    pass`}</CodeBlock>
          </div>

          <div>
            <h3 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'} font-mono`}>
              2. OriginGuard
            </h3>
            <p className={`mb-3 ${textMuted}`}>
              Validates the upgrade request's origin header against a list of allowed endpoints to prevent Cross-Site WebSocket Hijacking (CSWSH) attacks.
            </p>
            <CodeBlock language="python">{`from aquilia.sockets import Guard, OriginGuard

# Reject any requests originating from unrecognized domains
@Guard(OriginGuard(allowed_origins=["https://myapp.com", "https://*.myapp.com"]))
class SecureController(SocketController):
    pass`}</CodeBlock>
          </div>

          <div>
            <h3 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'} font-mono`}>
              3. MessageAuthGuard
            </h3>
            <p className={`mb-3 ${textMuted}`}>
              Periodically re-authenticates the user token during the lifespan of the WebSocket connection, ensuring revoked tokens disconnect active users within the set interval.
            </p>
            <CodeBlock language="python">{`from aquilia.sockets import Guard, MessageAuthGuard

# Re-authenticate the active token every 5 minutes (300 seconds)
@Guard(MessageAuthGuard(check_interval=300))
class LongLivedController(SocketController):
    pass`}</CodeBlock>
          </div>

          <div>
            <h3 className={`font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'} font-mono`}>
              4. RateLimitGuard
            </h3>
            <p className={`mb-3 ${textMuted}`}>
              Applies rate limit controls on a per-connection basis to prevent clients from flooding handlers with excessive message frequencies.
            </p>
            <CodeBlock language="python">{`from aquilia.sockets import Guard, RateLimitGuard, Event

class MessageRateController(SocketController):

    # Limit message.send events to a maximum of 5 payloads per second
    @Event("message.send")
    @Guard(RateLimitGuard(messages_per_second=5))
    async def on_send(self, conn, payload):
        pass`}</CodeBlock>
          </div>
        </div>
      </section>

      {/* Custom Guards */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Writing Custom Socket Guards
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          To write a custom guard, subclass <code className="text-aquilia-400">SocketGuard</code> and implement <code className="text-aquilia-400">check_handshake</code> (ran once at upgrade) or <code className="text-aquilia-400">check_message</code> (ran on every incoming message event):
        </p>
        <CodeBlock
          language="python"
          filename="custom_guard.py"
          highlightLines={[7, 13]}
        >{`from aquilia.sockets import SocketGuard, Connection, ConnectionScope, MessageEnvelope
from aquilia.faults import WS_FORBIDDEN  # Socket fault status code

class RoomAccessGuard(SocketGuard):
    def __init__(self, role: str):
        self.role = role

    async def check_handshake(self, scope: ConnectionScope) -> None:
        # Check permissions early from request headers or path parameters
        room_id = scope.path_params.get("room_id")
        user = scope.identity
        if not user or not user.has_room_role(room_id, self.role):
            # Abort the upgrade phase immediately
            raise WS_FORBIDDEN("You do not have access to this room.")

    async def check_message(self, conn: Connection, envelope: MessageEnvelope) -> None:
        # Check permissions on specific incoming messages
        if envelope.event == "room.admin_action" and not conn.identity.is_staff:
            raise WS_FORBIDDEN("Staff only action.")`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/websockets/controllers" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Socket Controllers
        </Link>
        <Link to="/docs/websockets/adapters" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Adapters <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'WebSocket Adapters', link: '/docs/websockets/adapters' },
          { text: 'Templates Overview', link: '/docs/templates' },
          { text: 'Developer Integration Guide', link: '/docs/developer-guide' },
        ]}
      />
    </div>
  )
}