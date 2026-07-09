import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function WebSocketControllers() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderMuted = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto px-4 py-2">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Globe className="w-4 h-4" />
          WebSockets / Socket Controllers
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono">Socket Controllers</span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          WebSocket handlers in Aquilia are declared inside classes inheriting from <DocTerm id="sockets.SocketController">SocketController</DocTerm>. Every incoming client connection gets a stateless controller instance bound to its own request-scoped DI container, letting you inject services, handle connection events, validate schemas, and stream responses.
        </p>
      </div>

      {/* Unified Extended Code Example */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Extended Implementation Example
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          The following controller demonstrates connection handshakes, pub/sub room subscriptions, validation schema boundaries, rate-limiting guards, and message acknowledgments in a single production-ready class:
        </p>
        <CodeBlock
          language="python"
          filename="chat_room_controller.py"
          highlightLines={[7, 10, 16, 23, 31, 38, 43]}
        >{`from aquilia.sockets import (
    SocketController, Socket, OnConnect, OnDisconnect,
    Event, AckEvent, Subscribe, Unsubscribe, Guard,
    Connection, Schema
)
from aquilia.di import Inject
from typing import Annotated

@Socket(
    path="/rooms/:room_id",
    allowed_origins=["https://myapp.com"],
    max_message_size=1024 * 1024,  # 1MB
    compression=True
)
class ChatRoomController(SocketController):

    def __init__(self, chat_service: Annotated[ChatService, Inject()]):
        self.chat = chat_service

    @OnConnect
    async def on_connect(self, conn: Connection):
        # Path parameter extraction
        room_id = conn.scope.path_params.get("room_id")
        
        # 1. Join connection to room
        await conn.join(room_id)
        
        # 2. Retrieve identity properties
        user = conn.identity
        username = user.username if user else "Anonymous"
        
        await conn.send_event("presence.join", {
            "user_id": conn.id,
            "username": username
        })

    @Subscribe("chat.history")
    async def on_subscribe(self, conn: Connection):
        room_id = conn.scope.path_params["room_id"]
        history = await self.chat.get_history(room_id)
        await conn.send_event("chat.history_dump", {"messages": history})

    @Event("message.send", schema=Schema({"text": str}))
    async def on_new_message(self, conn: Connection, payload: dict):
        room_id = conn.scope.path_params["room_id"]
        # Save through dependency-injected service
        msg = await self.chat.save_message(room_id, conn.id, payload["text"])
        
        # Broadcast to all connections in the room
        await conn.broadcast(room_id, "message.receive", msg.to_dict())

    @AckEvent("typing.state")
    async def on_typing(self, conn: Connection, payload: dict):
        room_id = conn.scope.path_params["room_id"]
        # Broadcast to room excluding the current sender
        await conn.broadcast(
            room_id, 
            "typing.state", 
            {"user_id": conn.id, "is_typing": payload.get("typing", False)},
            exclude_connection=conn.id
        )
        # Return ACK status back to the sender client
        return {"status": "ok"}

    @Unsubscribe("chat.history")
    async def on_unsubscribe(self, conn: Connection):
        pass

    @OnDisconnect
    async def on_disconnect(self, conn: Connection, reason: str | None = None):
        room_id = conn.scope.path_params.get("room_id")
        await conn.leave(room_id)
        await conn.broadcast(room_id, "presence.leave", {"user_id": conn.id})`}</CodeBlock>
      </section>

      {/* Decorator Details */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Decorator Reference
        </h2>
        <div className="space-y-8">
          {[
            {
              name: '@Socket(path, *, allowed_origins=None, max_connections=None, message_rate_limit=None, max_message_size=65536, compression=True, subprotocols=None)',
              desc: 'Decorates the SocketController class. Configures routing paths (with param matchers), CORS origin constraints, rate limit gates, compression, and subprotocols.',
              code: `from aquilia.sockets import SocketController, Socket

@Socket(
    path="/ws/live/:channel_name",
    allowed_origins=["https://myapp.com", "https://admin.myapp.com"],
    max_connections=5000,          # Limit concurrent connections on this handler
    message_rate_limit=30,          # Allow max 30 incoming messages per connection/sec
    max_message_size=128 * 1024,    # Set maximum frame payload limit to 128KB
    compression=True,               # Enable WebSocket permessage-deflate compression
    subprotocols=["mqtt", "wamp"]   # Define supported application subprotocols
)
class LiveChannelController(SocketController):
    """
    Handles live channel connections. Evaluates path params, limits access
    origins, and monitors frames sizes and compression ratios.
    """
    pass`
            },
            {
              name: '@OnConnect',
              desc: 'Invoked when a client establishes a connection. You can authorize the handshake or raise a SocketFault to disconnect immediately.',
              code: `from aquilia.sockets import OnConnect, Connection
from aquilia.faults import WS_UNAUTHORIZED_FAULT

class ConnectionHandlerController(SocketController):

    @OnConnect
    async def handle_connect(self, conn: Connection):
        # 1. Parse token parameters from query string
        token = conn.scope.query_params.get("token")
        if not token:
            raise WS_UNAUTHORIZED_FAULT("Authorization query token is missing.")
            
        # 2. Extract identity characteristics
        user = conn.identity
        if not user or not user.is_active:
            raise WS_UNAUTHORIZED_FAULT("Active user session required to connect.")
            
        # 3. Associate attributes to the connection context
        conn.state.custom_attrs["connected_at"] = datetime.utcnow()
        await conn.send_event("handshake.success", {"status": "authorized"})`
            },
            {
              name: '@OnDisconnect',
              desc: 'Invoked when a client disconnects. Signature can optionally accept a reason string describing the socket close event.',
              code: `from aquilia.sockets import OnDisconnect, Connection
import logging

logger = logging.getLogger(__name__)

class DisconnectHandlerController(SocketController):

    @OnDisconnect
    async def handle_disconnect(self, conn: Connection, reason: str | None = None):
        # 1. Extract session statistics
        connected_at = conn.state.custom_attrs.get("connected_at")
        session_duration = (datetime.utcnow() - connected_at).total_seconds() if connected_at else 0
        
        # 2. Log close events
        logger.warning(
            f"Client {conn.id} closed connection. "
            f"Reason: {reason or 'Clean Close'}. "
            f"Duration: {session_duration}s"
        )
        
        # 3. Clean up cluster states
        await conn.leave("broadcast_lobby")`
            },
            {
              name: '@Event(name, *, schema=None, ack=False)',
              desc: 'Binds a handler method to an incoming client event. Can validate payloads against a Schema and auto-send back an ACK envelope upon completion.',
              code: `from aquilia.sockets import Event, Connection, Schema

class MessageController(SocketController):

    @Event(
        name="feed.comment",
        schema=Schema({
            "post_id": int,
            "comment": str,
            "tags": list
        }),
        ack=False
    )
    async def on_new_comment(self, conn: Connection, payload: dict):
        post_id = payload["post_id"]
        comment_text = payload["comment"]
        
        # Save payload to database...
        await self.save_comment(conn.identity.id, post_id, comment_text)
        
        # Broadcast updates to the room
        await conn.broadcast(f"post_{post_id}", "comment.added", {
            "author": conn.identity.username,
            "text": comment_text
        })`
            },
            {
              name: '@AckEvent(name, *, schema=None)',
              desc: 'Shorthand for @Event(ack=True). Automatically serializes and sends the returned dictionary from the method back to the client as an ACK payload.',
              code: `from aquilia.sockets import AckEvent, Connection, Schema

class TransactionController(SocketController):

    @AckEvent(
        name="order.checkout",
        schema=Schema({
            "cart_id": str,
            "payment_method": str
        })
    )
    async def on_checkout(self, conn: Connection, payload: dict) -> dict:
        cart_id = payload["cart_id"]
        
        # Process order workflow...
        success, transaction_id = await self.order_service.checkout(cart_id)
        if not success:
            # Returned dict is automatically packed into ACK payload back to sender
            return {"success": False, "error": "Insufficient funds"}
            
        return {
            "success": True, 
            "transaction_id": transaction_id, 
            "timestamp": time.time()
        }`
            },
            {
              name: '@Subscribe(event, *, schema=None)',
              desc: 'Binds a method to run when a client requests a subscription. Use to register connection room presence.',
              code: `from aquilia.sockets import Subscribe, Connection

class SubscriptionController(SocketController):

    @Subscribe("channels.billing")
    async def subscribe_billing(self, conn: Connection):
        # Assert authorization policies
        if not conn.identity or not conn.identity.is_billing_admin:
            await conn.send_event("subscribe.error", {"channel": "billing", "reason": "unauthorized"})
            return
            
        # Join billing events channel room
        await conn.join("room:billing_alerts")
        await conn.send_event("subscribe.success", {"channel": "billing"})`
            },
            {
              name: '@Unsubscribe(event, *, schema=None)',
              desc: 'Binds a method to run when a client requests to unsubscribe from a channel/room.',
              code: `from aquilia.sockets import Unsubscribe, Connection

class UnsubscribeController(SocketController):

    @Unsubscribe("channels.billing")
    async def unsubscribe_billing(self, conn: Connection):
        # Clean up billing subscription rooms
        await conn.leave("room:billing_alerts")
        
        # Log event or trigger accounting hooks...
        await self.audit_log(user=conn.identity.id, action="unsubscribed_billing")
        await conn.send_event("unsubscribe.success", {"channel": "billing"})`
            },
            {
              name: '@Guard(*, priority=50)',
              desc: 'Applies a SocketGuard gate to a specific handler method or the entire controller class. Priority controls evaluation order (lower runs first).',
              code: `from aquilia.sockets import Guard, Event, Connection
              
# Apply guard at class level to authorize handshakes
@Guard(HandshakeAuthGuard(), priority=10)
class SecureAdminController(SocketController):

    # Apply method-level guard for granular permission checks
    @Event("system.config_write")
    @Guard(WritePermissionGuard(), priority=20)
    async def write_config(self, conn: Connection, payload: dict):
        # Executed only if HandshakeAuthGuard and WritePermissionGuard both pass
        await self.config.update(payload)
        await conn.send_event("config.updated", {"status": "success"})`
            }
          ].map((item, i) => (
            <div key={i} className="py-4 border-b border-white/5 last:border-0">
              <h3 className={`font-semibold text-sm mb-2 ${isDark ? 'text-white' : 'text-gray-900'} font-mono`}>
                {item.name}
              </h3>
              <p className={`text-sm mb-3 ${textMuted}`}>{item.desc}</p>
              <CodeBlock language="python">{item.code}</CodeBlock>
            </div>
          ))}
        </div>
      </section>

      {/* Connection Object */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Connection Object API
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          Every controller method receives a <DocTerm id="sockets.Connection">Connection</DocTerm> instance representing the active client session:
        </p>
        <div className="space-y-8">
          {[
            { 
              name: 'conn.id', 
              type: 'str (Property)', 
              desc: 'Unique connection UUID alias.',
              code: `@Event("whoami")
async def handle_whoami(self, conn: Connection, payload: dict):
    # Returns the unique connection ID generated for this socket lifecycle
    connection_uuid = conn.id
    await conn.send_event("whoami.reply", {"connection_id": connection_uuid})`
            },
            { 
              name: 'conn.state', 
              type: 'ConnectionState (Property)', 
              desc: 'Current connection state: connecting, connected, closing, or closed.',
              code: `@Event("ping.state")
async def check_connection_state(self, conn: Connection, payload: dict):
    state = conn.state
    logger.info(f"Checking state. Open: {state.is_connected}, Closing: {state.is_closing}")
    
    # Set and read arbitrary thread-safe connection local attributes
    state.custom_attrs["last_ping_at"] = datetime.utcnow()
    await conn.send_event("pong.state", {"state": str(state.value)})`
            },
            { 
              name: 'conn.scope', 
              type: 'ConnectionScope (Property)', 
              desc: 'Wrapper containing the ASGI route parameters, headers, query arguments, and path.',
              code: `@OnConnect
async def inspect_scope(self, conn: Connection):
    scope = conn.scope
    
    # 1. Access request headers (lowercase keys)
    user_agent = scope.headers.get("user-agent")
    
    # 2. Access query parameters
    api_key = scope.query_params.get("api_key")
    
    # 3. Access path parameters from routes
    room_id = scope.path_params.get("room_id")
    
    # 4. Access Client IP details
    client_ip = scope.client[0] if scope.client else "unknown"`
            },
            { 
              name: 'conn.identity', 
              type: 'Identity | None (Property)', 
              desc: 'The authenticated user identity resolved during handshake.',
              code: `@Event("user.profile_get")
async def get_user_profile(self, conn: Connection, payload: dict):
    # Access the active user identity loaded by auth guards
    user = conn.identity
    if not user:
        await conn.send_event("profile.error", {"reason": "anonymous"})
        return
        
    await conn.send_event("profile.data", {
        "username": user.username,
        "email": user.email,
        "roles": user.roles
    })`
            },
            { 
              name: 'conn.session', 
              type: 'Session | None (Property)', 
              desc: 'The active session object (if SessionMiddleware is active).',
              code: `@Event("session.increment")
async def increment_counter(self, conn: Connection, payload: dict):
    session = conn.session
    if not session:
        await conn.send_event("session.error", {"reason": "sessions_disabled"})
        return
        
    # Read/Write directly to the ASGI Session transport
    counter = session.get("counter", 0) + 1
    session["counter"] = counter
    
    await conn.send_event("session.count", {"counter": counter})`
            },
            { 
              name: 'conn.rooms', 
              type: 'set[str] (Property)', 
              desc: 'A copy of the rooms this connection currently belongs to.',
              code: `@Event("rooms.list")
async def list_joined_rooms(self, conn: Connection, payload: dict):
    # Retrieve all room keys this connection is registered in
    joined_rooms_set = conn.rooms
    await conn.send_event("rooms.reply", {
        "rooms": list(joined_rooms_set),
        "count": len(joined_rooms_set)
    })`
            },
            { 
              name: 'conn.send_event(event, payload, ack=False)', 
              type: 'async method', 
              desc: 'Sends a structured event envelope. Returns a message ID if ack requested.',
              code: `@Event("action.request")
async def trigger_event(self, conn: Connection, payload: dict):
    # Send event to the client. Requesting an ACK returns a UUID
    msg_id = await conn.send_event(
        event="action.confirm",
        payload={"status": "processing", "item_id": 402},
        ack=True
    )
    # Log msg_id to map incoming user acknowledgments later
    logger.info(f"Dispatched message with tracking ID: {msg_id}")`
            },
            { 
              name: 'conn.send_json(data)', 
              type: 'async method', 
              desc: 'Sends raw JSON data directly to the socket, bypassing the standard envelope.',
              code: `@Event("raw.query")
async def send_raw_payload(self, conn: Connection, payload: dict):
    # Bypasses the standard {"event": "name", "payload": {...}} envelope
    # Sends a raw JSON array or dictionary directly down the socket
    await conn.send_json([
        {"id": 1, "value": "A"},
        {"id": 2, "value": "B"}
    ])`
            },
            { 
              name: 'conn.send_raw(data: bytes)', 
              type: 'async method', 
              desc: 'Sends raw binary bytes to the socket.',
              code: `@Event("image.request")
async def stream_raw_image(self, conn: Connection, payload: dict):
    image_bytes = await self.image_service.get_raw_thumbnail(payload["id"])
    
    # Sends raw binary frames down the WebSocket connection (WS OPCODE 2)
    await conn.send_raw(image_bytes)`
            },
            { 
              name: 'conn.join(room) / join_room(room)', 
              type: 'async method', 
              desc: 'Subscribes the connection to a room. Synchronized across nodes via adapters.',
              code: `@Event("room.enter")
async def enter_room_channel(self, conn: Connection, payload: dict):
    room_name = f"chat_{payload['room_id']}"
    
    # Join connection to the channel
    await conn.join(room_name)
    
    # Broadcast join event to all other members in the room
    await conn.broadcast(
        room=room_name,
        event="user.joined",
        payload={"user_id": conn.id},
        exclude_connection=conn.id
    )`
            },
            { 
              name: 'conn.leave(room) / leave_room(room)', 
              type: 'async method', 
              desc: 'Unsubscribes the connection from a room.',
              code: `@Event("room.exit")
async def exit_room_channel(self, conn: Connection, payload: dict):
    room_name = f"chat_{payload['room_id']}"
    
    # Leave room channel
    await conn.leave(room_name)
    
    # Broadcast leave notification to remaining members
    await conn.broadcast(
        room=room_name,
        event="user.left",
        payload={"user_id": conn.id}
    )`
            },
            { 
              name: 'conn.disconnect(reason=None, code=1000)', 
              type: 'async method', 
              desc: 'Closes the WebSocket connection with close codes.',
              code: `@Event("session.terminate")
async def force_disconnect(self, conn: Connection, payload: dict):
    # Close socket connection immediately
    await conn.send_event("session.terminated", {"reason": "forced"})
    
    # Triggers WS 1008 Policy Violation close event
    await conn.disconnect(reason="forced_termination", code=1008)`
            },
            { 
              name: 'conn.resolve(name, optional=False)', 
              type: 'async method', 
              desc: 'Resolves a dependency asynchronously from the connection container scope.',
              code: `@Event("payment.process")
async def process_payment(self, conn: Connection, payload: dict):
    # Retrieve a scoped repository service directly from the DI container
    payment_gateway = await conn.resolve(PaymentGatewayService)
    
    result = await payment_gateway.charge(payload["amount"], token=payload["token"])
    await conn.send_event("payment.result", result.to_dict())`
            }
          ].map((item, i) => (
            <div key={i} className="py-4 border-b border-white/5 last:border-0">
              <div className="flex items-center justify-between gap-4 mb-2">
                <h3 className={`font-semibold text-sm ${isDark ? 'text-white' : 'text-gray-900'} font-mono`}>
                  {item.name}
                </h3>
                <span className={`text-[10px] uppercase tracking-wider ${isDark ? 'text-gray-500' : 'text-gray-400'} font-mono`}>
                  {item.type}
                </span>
              </div>
              <p className={`text-sm mb-3 ${textMuted}`}>{item.desc}</p>
              <CodeBlock language="python">{item.code}</CodeBlock>
            </div>
          ))}
        </div>
      </section>

      {/* Streaming Section */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          WebSocket Chunked Streaming
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          AquilaSockets supports first-class streaming. If a handler returns an <code className="text-aquilia-400">AsyncIterator</code> or <code className="text-aquilia-400">Iterator</code>, the runtime will automatically consume it and stream chunks to the client:
        </p>
        <CodeBlock
          language="python"
          filename="streaming.py"
          highlightLines={[5, 6, 7]}
        >{`@Event("logs.stream")
async def handle_logs_stream(self, conn: Connection, payload: dict) -> AsyncIterator[dict]:
    # Generator yielding chunks back to the client
    for i in range(10):
        await asyncio.sleep(0.5)
        yield {"index": i, "data": f"Log line {i}"}

# Handled by runtime:
# Sends 'logs.stream.chunk' events carrying each dictionary.
# Ends the stream by dispatching 'logs.stream.end'.`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/websockets" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/websockets/runtime" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          WebSocket Runtime <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'WebSocket Runtime Details', link: '/docs/websockets/runtime' },
          { text: 'Scaling Adapters', link: '/docs/websockets/adapters' },
          { text: 'CLI and Macro Tools', link: '/docs/cli' },
        ]}
      />
    </div>
  )
}