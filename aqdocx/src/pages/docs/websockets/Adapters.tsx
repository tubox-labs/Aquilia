import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Layers } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function WebSocketAdapters() {
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
          WebSockets / Adapters
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono">Scaling Adapters</span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Adapters route events, channel subscriptions, room memberships, and messages across your application processes. This pub/sub interface enables AquilaSockets to scale horizontally from a single node to multi-server clusters.
        </p>
      </div>

      {/* Adapter base class */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          The Adapter Base Class
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          To write a custom adapter (e.g. for NATS or RabbitMQ), inherit from the base <code className="text-aquilia-400">Adapter</code> class and implement the following async signature interfaces:
        </p>

        <CodeBlock
          language="python"
          filename="base_adapter.py"
          highlightLines={[7, 11, 15, 23, 27, 31]}
        >{`from aquilia.sockets import Adapter, MessageEnvelope

class CustomAdapter(Adapter):

    async def initialize(self) -> None:
        """Establish client connections to external message brokers."""
        pass

    async def shutdown(self) -> None:
        """Close connections and flush buffers during server teardown."""
        pass

    async def publish(self, namespace: str, room: str, envelope: MessageEnvelope, exclude_connection: str | None = None) -> None:
        """Publish a message to all members subscribing to a room across clusters."""
        pass

    async def broadcast(self, namespace: str, envelope: MessageEnvelope, exclude_connection: str | None = None) -> None:
        """Broadcast a message to all active connections inside a namespace."""
        pass

    async def join_room(self, namespace: str, room: str, connection_id: str) -> None:
        """Register a connection ID as a member of a room."""
        pass

    async def leave_room(self, namespace: str, room: str, connection_id: str) -> None:
        """Unregister a connection ID from a room."""
        pass

    async def get_room_members(self, namespace: str, room: str) -> set[str]:
        """Fetch active connection IDs inside a room across nodes."""
        return set()

    async def get_connection_count(self, namespace: str) -> int:
        """Fetch total client count within the namespace."""
        return 0`}</CodeBlock>
      </section>

      {/* InMemoryAdapter */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          InMemoryAdapter (Default)
        </h2>
        <p className={`text-sm mb-4 ${textMuted}`}>
          The default adapter manages connection states, room memberships, and broadcasts entirely inside the local application memory. It is optimized for single-instance applications, developer environments, and automated testing suites.
        </p>
        <CodeBlock
          language="python"
          filename="in_memory_config.py"
          highlightLines={[3]}
        >{`from aquilia.sockets import AquilaSockets, InMemoryAdapter

sockets = AquilaSockets(
    router=router,
    adapter=InMemoryAdapter()
)`}</CodeBlock>
      </section>

      {/* RedisAdapter */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          RedisAdapter (Production Scaling)
        </h2>
        <p className={`text-sm mb-4 ${textMuted}`}>
          The <DocTerm id="sockets.RedisAdapter">RedisAdapter</DocTerm> uses Redis Pub/Sub channels to sync message delivery between server processes. Connection metadata and room rosters are maintained atomically inside Redis Sets and Sorted Sets:
        </p>
        <CodeBlock
          language="python"
          filename="redis_config.py"
          highlightLines={[3, 4, 5]}
        >{`from aquilia.sockets import AquilaSockets, RedisAdapter

adapter = RedisAdapter(
    url="redis://localhost:6379/0",
    channel_prefix="ws:",
    pool_size=15
)

sockets = AquilaSockets(
    router=router,
    adapter=adapter
)`}</CodeBlock>
      </section>

      {/* Custom Adapter Implementation */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold tracking-tight mb-6 pb-2 border-b ${borderMuted} ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Implementing a Custom Adapter
        </h2>
        <p className={`text-sm mb-6 ${textMuted}`}>
          To integrate with other messaging brokers like NATS or RabbitMQ, inherit from <code className="text-aquilia-400">Adapter</code>:
        </p>
        <CodeBlock
          language="python"
          filename="custom_adapter.py"
          highlightLines={[5, 11]}
        >{`from aquilia.sockets import Adapter, MessageEnvelope

class NatsWebSocketAdapter(Adapter):
    def __init__(self, nats_url: str):
        self.nats_url = nats_url
        self.nc = None

    async def initialize(self):
        import nats
        self.nc = await nats.connect(self.nats_url)

    async def publish(self, namespace: str, room: str, envelope: MessageEnvelope, exclude_connection: str | None = None):
        subject = f"ws.{namespace}.{room}"
        payload = self.codec.encode(envelope)
        await self.nc.publish(subject, payload)

    async def shutdown(self):
        if self.nc:
            await self.nc.close()`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/websockets/runtime" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> WebSocket Runtime
        </Link>
        <Link to="/docs/templates" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Templates <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps
        items={[
          { text: 'Templates Overview', link: '/docs/templates' },
          { text: 'TemplateEngine API', link: '/docs/templates/engine' },
          { text: 'Developer Integration Guide', link: '/docs/developer-guide' },
        ]}
      />
    </div>
  )
}