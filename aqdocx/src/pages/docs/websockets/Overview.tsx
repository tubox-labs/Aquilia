import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Radio, Shield, Network, Zap } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function WebSocketsOverview() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderMuted = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto px-4 py-2">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Radio className="w-4 h-4 animate-pulse" />
          Advanced / WebSockets
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono">WebSockets Overview</span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          AquilaSockets provides production-grade WebSocket support featuring a declarative, decorator-driven syntax. Every connection is backed by its own request-scoped DI container, auth-first upgrade guards, structured message envelopes, event streaming, and horizontal scaling via message broker adapters.
        </p>
      </div>

      {/* Integration Guide */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          System Integration & Registration
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          To activate WebSocket routing, a controller must be mounted in your module's manifest, which is in turn loaded by the workspace configuration.
        </p>

        {/* Workspace Level */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Workspace Registration</h3>
          <p className={`text-sm mb-4 ${textMuted}`}>
            Register your module within the workspace builder in <code className="text-aquilia-400">workspace.py</code>:
          </p>
          <CodeBlock
            language="python"
            filename="workspace.py"
            highlightLines={[8]}
          >{`from aquilia.workspace import Workspace, Module

workspace = (
    Workspace("myapp")
    .runtime(port=8000)
    .module(
        Module("chat")
        .route_prefix("/chat")
    )
)`}</CodeBlock>
        </div>

        {/* Manifest Level */}
        <div className="mb-8">
          <h3 className={`text-lg font-semibold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Manifest Mounting</h3>
          <p className={`text-sm mb-4 ${textMuted}`}>
            Mount the socket controller class inside your module's manifest file in the <code className="text-aquilia-400">socket_controllers</code> parameter:
          </p>
          <CodeBlock
            language="python"
            filename="modules/chat/manifest.py"
            highlightLines={[7]}
          >{`from aquilia.manifest import AppManifest

manifest = AppManifest(
    name="chat",
    version="1.0.0",
    controllers=[],
    socket_controllers=[
        "modules.chat.controllers:RoomChatController",
    ],
    services=[
        "modules.chat.services:ChatService"
    ]
)`}</CodeBlock>
        </div>
      </section>

      {/* Architecture Section */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Subsystem Architecture
        </h2>
        <p className={`text-sm mb-8 ${textMuted}`}>
          The WebSocket module separates connection lifecycle, message codec parsing, security validation, and pub/sub distribution into distinct components:
        </p>
        <div className="space-y-8">
          {[
            {
              name: 'SocketController',
              id: 'sockets.SocketController',
              desc: 'Class-based message handler compiled at build-time. It maps incoming events to async methods, instantiated inside a request-scoped DI container.'
            },
            {
              name: 'Connection',
              id: 'sockets.Connection',
              desc: 'Active connection handle wrapping the underlying transport. Manages state dictionaries, room subscriptions, connection statistics, and async sending.'
            },
            {
              name: 'MessageEnvelope',
              id: 'sockets.MessageEnvelope',
              desc: 'Typed message protocol mapping fields like event name, client-supplied payload, message ID (for acks), and timestamp.'
            },
            {
              name: 'InMemoryAdapter',
              id: 'sockets.InMemoryAdapter',
              desc: 'Default single-process scaling adapter. Routes room subscribes and broadcasts internally without broker dependencies.'
            },
            {
              name: 'RedisAdapter',
              id: 'sockets.RedisAdapter',
              desc: 'Production-ready scaling adapter using Redis Pub/Sub channels to sync events and rooms across multiple ASGI worker processes.'
            },
            {
              name: 'HandshakeAuthGuard',
              id: 'sockets.HandshakeAuthGuard',
              desc: 'Handshake security gate. Rejects connections early (during HTTP-upgrade phase) if authorization criteria are not met.'
            }
          ].map((item, i) => (
            <div key={i} className={`group pl-5 border-l-2 ${isDark ? 'border-aquilia-500/20 hover:border-aquilia-400' : 'border-aquilia-500/10 hover:border-aquilia-600'} transition-all duration-300`}>
              <div className="flex items-center gap-2 mb-1.5">
                <DocTerm id={item.id} className="text-aquilia-500 font-mono text-sm font-semibold border-b-0 hover:underline">
                  {item.name}
                </DocTerm>
              </div>
              <p className={`text-sm leading-relaxed ${textMuted}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Code Walkthrough */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Extended Controller Implementation
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          WebSocket controllers are defined by inheriting from <DocTerm id="sockets.SocketController">SocketController</DocTerm> and decorating with <DocTerm id="controllers.GET">@Socket</DocTerm>:
        </p>

        <CodeBlock
          language="python"
          filename="chat_controller.py"
          highlightLines={[7, 12, 17, 23, 29]}
        >{`from aquilia.sockets import (
    SocketController, Socket, OnConnect, OnDisconnect,
    Event, AckEvent, Subscribe, Connection, Schema
)
from aquilia import Inject

@Socket("/ws/chat/:room")
class RoomChatController(SocketController):

    @Inject()
    def __init__(self, chat_service: ChatService):
        self.chat = chat_service

    @OnConnect
    async def handle_connect(self, conn: Connection):
        # Read parameters from ASGI path patterns
        room = conn.scope.path_params.get("room")
        await conn.join(room)
        
        # Inject user identity resolved from handshake auth
        user = conn.identity
        await conn.send_event("welcome", {
            "msg": f"Hello {user.username if user else 'Guest'}!"
        })

    @Event("chat.message", schema=Schema({"text": str}))
    async def on_message(self, conn: Connection, payload: dict):
        room = conn.scope.path_params["room"]
        # Broadcast to all connections in the room
        await conn.broadcast(room, "chat.message", {
            "sender": conn.id,
            "text": payload["text"]
        })

    @AckEvent("user.typing")
    async def on_typing(self, conn: Connection, payload: dict):
        room = conn.scope.path_params["room"]
        await conn.broadcast(room, "user.typing", {"user": conn.id})
        return {"delivered": True}  # Returned directly to the sender as an ACK`}</CodeBlock>
      </section>

      {/* Features Showcase */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Core Capabilities
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Zap className="w-4 h-4 text-aquilia-500" />
              <h3 className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>DI-Scoped Handlers</h3>
            </div>
            <p className={`text-xs leading-relaxed ${textMuted}`}>
              Every connection creates its own request-scoped dependency injection container. Scoped objects are automatically created, injected, and cleaned up when the client disconnects.
            </p>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Shield className="w-4 h-4 text-aquilia-500" />
              <h3 className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>Robust Handshake Security</h3>
            </div>
            <p className={`text-xs leading-relaxed ${textMuted}`}>
              Authenticates connections via Authorization Bearer headers, query string tokens, or cookies, using HTTP guard logic before upgrading the connection to a WebSocket.
            </p>
          </div>
          <div>
            <div className="flex items-center gap-2 mb-2">
              <Network className="w-4 h-4 text-aquilia-500" />
              <h3 className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>Horizontal Scaling</h3>
            </div>
            <p className={`text-xs leading-relaxed ${textMuted}`}>
              Pluggable broker adapters (such as <DocTerm id="sockets.RedisAdapter">RedisAdapter</DocTerm>) forward broadcast and room events across multiple servers seamlessly, ensuring instant pub/sub delivery.
            </p>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/cache" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Cache
        </Link>
        <Link to="/docs/websockets/controllers" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Socket Controllers <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'WebSocket Controllers', link: '/docs/websockets/controllers' },
          { text: 'WebSocket Runtime Details', link: '/docs/websockets/runtime' },
          { text: 'Scaling Adapters', link: '/docs/websockets/adapters' },
        ]}
      />
    </div>
  )
}