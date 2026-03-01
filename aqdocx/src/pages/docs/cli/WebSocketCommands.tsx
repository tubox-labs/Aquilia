import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Terminal, Wifi } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function CLIWebSocketCommands() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = 'mb-16 scroll-mt-24'
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`
  const codeClass = 'text-xs font-mono bg-black/5 dark:bg-white/10 px-1.5 py-0.5 rounded text-aquilia-600 dark:text-aquilia-400'
  const noteClass = `p-4 rounded-xl border-l-4 ${isDark ? 'bg-blue-500/5 border-blue-500/50 text-gray-300' : 'bg-blue-50 border-blue-500 text-gray-700'}`

  const Table = ({ children }: { children: React.ReactNode }) => (
    <div className={`overflow-hidden border rounded-lg mb-6 ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
      <table className="w-full text-sm text-left">
        <thead className={`text-xs uppercase ${isDark ? 'bg-white/5 text-gray-400' : 'bg-gray-50 text-gray-500'}`}>
          <tr>
            <th className="px-4 py-3 font-medium">Option</th>
            <th className="px-4 py-3 font-medium">Description</th>
            <th className="px-4 py-3 font-medium w-32">Default</th>
          </tr>
        </thead>
        <tbody className={`divide-y ${isDark ? 'divide-white/10' : 'divide-gray-200'}`}>
          {children}
        </tbody>
      </table>
    </div>
  )

  const Row = ({ opt, desc, def: defaultVal }: { opt: string; desc: string; def?: string }) => (
    <tr className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
      <td className="px-4 py-3 font-mono text-aquilia-500">{opt}</td>
      <td className={`px-4 py-3 ${isDark ? 'text-gray-300' : 'text-gray-600'}`}>{desc}</td>
      <td className={`px-4 py-3 font-mono text-xs ${isDark ? 'text-gray-500' : 'text-gray-400'}`}>{defaultVal || '-'}</td>
    </tr>
  )

  return (
    <div className="max-w-4xl mx-auto pb-20">
      {/* Header */}
      <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Wifi className="w-4 h-4" />
          CLI / WebSocket Commands
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            WebSocket Commands
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className={codeClass}>aq ws</code> command group provides admin tools for managing WebSocket namespaces, broadcasting messages, generating client SDKs, purging rooms, and kicking connections.
        </p>
      </div>

      {/* Overview */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Wifi className="w-6 h-6 text-aquilia-500" />
          Command Overview
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {[
            { cmd: 'aq ws inspect', desc: 'Show compiled WebSocket namespaces and controllers from ws.crous artifacts' },
            { cmd: 'aq ws broadcast', desc: 'Broadcast a message to a namespace or room via the adapter' },
            { cmd: 'aq ws gen-client', desc: 'Generate TypeScript client SDK from compiled WebSocket artifacts' },
            { cmd: 'aq ws purge-room', desc: 'Purge a room\'s state from the adapter (disconnect all members)' },
            { cmd: 'aq ws kick', desc: 'Kick (disconnect) a specific WebSocket connection by ID' },
          ].map((item, i) => (
            <div key={i} className={boxClass}>
              <code className={`font-bold text-sm ${isDark ? 'text-aquilia-400' : 'text-aquilia-600'}`}>{item.cmd}</code>
              <p className={`text-xs mt-1 ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>{item.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ws inspect */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq ws inspect
        </h2>
        <p className={pClass}>
          Reads the compiled <code className={codeClass}>ws.crous</code> artifact and displays all WebSocket namespaces, controllers, events, guards, and configuration. Requires running <code className={codeClass}>aq compile</code> first.
        </p>

        <Table>
          <Row opt="--artifacts-dir" desc="Directory containing compiled artifacts" def="artifacts" />
        </Table>

        <CodeBlock language="bash" filename="Terminal">{`# Inspect WebSocket namespaces
aq ws inspect

# Use custom artifacts directory
aq ws inspect --artifacts-dir build/artifacts`}</CodeBlock>

        <h3 className={h3Class}>Output Details</h3>
        <p className={pClass}>
          For each WebSocket controller, the output shows:
        </p>
        <ul className={`list-disc pl-6 mb-4 space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><strong>Namespace</strong> — the Socket.IO-style namespace path (e.g. <code className={codeClass}>/chat</code>)</li>
          <li><strong>Controller</strong> — the Python class handling the namespace</li>
          <li><strong>Module</strong> — the import path of the controller module</li>
          <li><strong>Events</strong> — registered event handlers with ACK and schema flags</li>
          <li><strong>Guards</strong> — authentication/authorization guards applied</li>
          <li><strong>Config</strong> — allowed origins, rate limits, and other namespace settings</li>
        </ul>

        <CodeBlock language="text" filename="Example Output">{`WebSocket Namespaces (2 controllers)

Namespace: /chat
  Controller: ChatController
  Module: modules.chat.socket_controllers
  Path: /ws/chat
  Events: 3
    - message.send → on_message_send [ACK] [SCHEMA]
    - user.typing → on_user_typing
    - room.join → on_room_join [ACK]
  Guards: AuthGuard
  Allowed Origins: ["http://localhost:3000"]
  Rate Limit: 30 msg/sec`}</CodeBlock>
      </section>

      {/* ws broadcast */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq ws broadcast
        </h2>
        <p className={pClass}>
          Send a message to all connections in a namespace, or to a specific room. Uses the configured adapter (in-memory for local dev, Redis for production).
        </p>

        <Table>
          <Row opt="--namespace" desc="Target namespace (required)" def="-" />
          <Row opt="--room" desc="Target room within the namespace (optional)" def="all" />
          <Row opt="--event" desc="Event name to broadcast (required)" def="-" />
          <Row opt="--payload" desc="JSON payload to send" def="{}" />
        </Table>

        <CodeBlock language="bash" filename="Terminal">{`# Broadcast to entire namespace
aq ws broadcast --namespace /chat --event message.receive --payload '{"text":"Hello!"}'

# Broadcast to specific room
aq ws broadcast --namespace /chat --room room1 --event message.receive --payload '{"text":"Hello room!"}'`}</CodeBlock>

        <div className={noteClass}>
          <strong>Note:</strong> When using the in-memory adapter (default for dev), broadcasts only reach the current process. For cross-process broadcasting, configure a Redis adapter.
        </div>
      </section>

      {/* ws gen-client */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq ws gen-client
        </h2>
        <p className={pClass}>
          Generate a fully-typed TypeScript client SDK from the compiled <code className={codeClass}>ws.crous</code> artifact. The generated client includes typed event emitters, connection management, namespace classes, and reconnection logic.
        </p>

        <Table>
          <Row opt="--lang" desc="Target language (currently only 'ts')" def="ts" />
          <Row opt="--out" desc="Output file path (required)" def="-" />
          <Row opt="--artifacts-dir" desc="Directory containing compiled artifacts" def="artifacts" />
        </Table>

        <CodeBlock language="bash" filename="Terminal">{`# Generate TypeScript client
aq ws gen-client --out clients/chat.ts

# From custom artifacts directory
aq ws gen-client --out src/ws-client.ts --artifacts-dir build/artifacts`}</CodeBlock>

        <h3 className={h3Class}>Generated Client Structure</h3>
        <p className={pClass}>
          The TypeScript client includes:
        </p>
        <ul className={`list-disc pl-6 mb-4 space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li><strong>MessageEnvelope</strong> interface — type-safe event/ack/system message wrapper</li>
          <li><strong>Namespace classes</strong> — one per namespace with typed event methods</li>
          <li><strong>Connection management</strong> — connect, disconnect, reconnect with exponential backoff</li>
          <li><strong>Room management</strong> — join, leave, and room-scoped event listeners</li>
          <li><strong>Acknowledgement support</strong> — type-safe ACK callbacks</li>
        </ul>
      </section>

      {/* ws purge-room */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq ws purge-room
        </h2>
        <p className={pClass}>
          Remove all connections from a room and clear its state from the adapter. Useful for cleaning up stale rooms or force-clearing a room during development.
        </p>

        <Table>
          <Row opt="--namespace" desc="Namespace containing the room (required)" def="-" />
          <Row opt="--room" desc="Room to purge (required)" def="-" />
          <Row opt="--redis-url" desc="Redis URL for production adapter (optional)" def="in-memory" />
        </Table>

        <CodeBlock language="bash" filename="Terminal">{`# Purge a room
aq ws purge-room --namespace /chat --room room1

# Purge via Redis adapter
aq ws purge-room --namespace /chat --room room1 --redis-url redis://localhost:6379/0`}</CodeBlock>
      </section>

      {/* ws kick */}
      <section className={sectionClass}>
        <h2 className={h2Class}>
          <Terminal className="w-6 h-6 text-aquilia-500" />
          aq ws kick
        </h2>
        <p className={pClass}>
          Disconnect a specific WebSocket connection by its connection ID. The connection is unregistered from all namespaces it belongs to.
        </p>

        <Table>
          <Row opt="--conn" desc="Connection ID to disconnect (required)" def="-" />
          <Row opt="--reason" desc="Reason for the disconnection" def="kicked by admin" />
          <Row opt="--redis-url" desc="Redis URL for production adapter (optional)" def="in-memory" />
        </Table>

        <CodeBlock language="bash" filename="Terminal">{`# Kick a connection
aq ws kick --conn abc-123

# Kick with custom reason
aq ws kick --conn abc-123 --reason "violated rules"

# Kick via Redis adapter
aq ws kick --conn abc-123 --redis-url redis://localhost:6379/0`}</CodeBlock>
      </section>

      {/* Adapter Architecture */}
      <section className={sectionClass}>
        <h2 className={h2Class}>Adapter Architecture</h2>
        <p className={pClass}>
          All WebSocket CLI commands interact with the underlying adapter layer. By default, the in-memory adapter is used, which only works within a single process. For multi-worker or multi-server setups, provide a <code className={codeClass}>--redis-url</code> to use the Redis adapter.
        </p>
        <CodeBlock language="text" filename="Adapter Selection">{`┌─────────────┐     ┌────────────────┐
│  aq ws ...  │ ──▶ │ InMemoryAdapter │  (default, single-process)
│             │     └────────────────┘
│             │
│  --redis-url│ ──▶ ┌────────────────┐
│             │     │  RedisAdapter   │  (production, multi-worker)
└─────────────┘     └────────────────┘`}</CodeBlock>
      </section>

      <NextSteps
        items={[
          { text: 'WebSocket Controllers', link: '/docs/websockets/controllers' },
          { text: 'WebSocket Runtime', link: '/docs/websockets/runtime' },
          { text: 'WebSocket Adapters', link: '/docs/websockets/adapters' },
          { text: 'Artifact Commands', link: '/docs/cli/artifacts' },
        ]}
      />
    </div>
  )
}
