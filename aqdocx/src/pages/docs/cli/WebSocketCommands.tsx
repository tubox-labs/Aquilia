import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { NextSteps } from '../../../components/NextSteps'
import { Radio } from 'lucide-react'
import { DocTerm } from '../../../components/docPreview/DocTerm'

export function CLIWebSocketCommands() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  const sectionClass = "mb-16 scroll-mt-24"
  const h2Class = `text-2xl font-bold mb-6 flex items-center gap-3 ${isDark ? 'text-white' : 'text-gray-900'}`
  const h3Class = `text-lg font-semibold mt-8 mb-3 ${isDark ? 'text-gray-200' : 'text-gray-800'}`
  const pClass = `mb-4 leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`

  return (
    <div className="max-w-4xl mx-auto pb-20">
      {/* Header */}
      <div className="mb-12 border-b border-gray-200 dark:border-white/10 pb-8">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Radio className="w-4 h-4" />
          CLI / WebSocket Commands
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            WebSocket Commands
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed mt-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500 font-mono font-bold">aq ws</code> command group provides administrative tools to inspect active WebSocket controllers, broadcast realtime events, compile client SDK code, purge rooms, and disconnect clients.
        </p>
      </div>

      {/* aq ws inspect */}
      <section id="ws-inspect" className={sectionClass}>
        <h2 className={h2Class}><DocTerm id="cli.ws_inspect">aq ws inspect</DocTerm></h2>
        <p className={pClass}>
          Dumps the compiled SocketController routing table and message channels compiled within your <code className="text-aquilia-500 font-mono">ws.surp</code> artifacts bundle.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq ws inspect --artifacts-dir=artifacts</CodeBlock>
      </section>

      {/* aq ws broadcast */}
      <section id="ws-broadcast" className={sectionClass}>
        <h2 className={h2Class}><DocTerm id="cli.ws_broadcast">aq ws broadcast</DocTerm></h2>
        <p className={pClass}>
          Sends a payload event message to a namespace, room, or specific connection ID using the registered WebSocket adapter backend (e.g. Redis).
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# Broadcast chat event to general room
aq ws broadcast --namespace=/chat --room=general --event=new_message --payload='{"msg":"hello"}'`}</CodeBlock>

        <h3 className={h3Class}>Options</h3>
        <div className="overflow-x-auto py-2 mb-6">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 dark:border-white/10 text-gray-500 dark:text-gray-400 text-left">
                <th className="px-4 py-3 font-semibold">Option</th>
                <th className="px-4 py-3 font-semibold">Description</th>
              </tr>
            </thead>
            <tbody className={`divide-y ${isDark ? 'divide-white/5 text-gray-300' : 'divide-gray-150 text-gray-700'}`}>
              {[
                ['--namespace', 'Target namespace path (defaults to root namespace "/").'],
                ['--room', 'Limit broadcast to connections matching the named room.'],
                ['--event', 'Name of the event message to emit.'],
                ['--payload', 'JSON string body content containing message payloads.']
              ].map(([opt, desc], i) => (
                <tr key={i} className="hover:bg-aquilia-500/5 transition-colors">
                  <td className="px-4 py-2 font-mono text-xs text-aquilia-500 font-semibold">{opt}</td>
                  <td className="px-4 py-2 text-xs">{desc}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* aq ws gen-client */}
      <section id="ws-gen-client" className={sectionClass}>
        <h2 className={h2Class}><DocTerm id="cli.ws_gen_client">aq ws gen-client</DocTerm></h2>
        <p className={pClass}>
          Compiles compiled WebSocket SocketControllers and generates a fully typed TypeScript client SDK.
        </p>
        <CodeBlock language="bash" filename="Terminal">{`# Compile TypeScript websocket client SDK
aq ws gen-client --out=frontend/src/sdk --lang=ts`}</CodeBlock>
      </section>

      {/* aq ws purge-room */}
      <section id="ws-purge-room" className={sectionClass}>
        <h2 className={h2Class}><DocTerm id="cli.ws_purge_room">aq ws purge-room</DocTerm></h2>
        <p className={pClass}>
          Purges a room state from the adapter, forcing all currently connected client members of that room to disconnect.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq ws purge-room --namespace=/chat --room=general</CodeBlock>
      </section>

      {/* aq ws kick */}
      <section id="ws-kick" className={sectionClass}>
        <h2 className={h2Class}><DocTerm id="cli.ws_kick">aq ws kick</DocTerm></h2>
        <p className={pClass}>
          Forces the disconnection of a specific connection ID by submitting a kick command to the WebSocket adapter.
        </p>
        <CodeBlock language="bash" filename="Terminal">aq ws kick --conn=client-connection-id-123 --reason="Admin maintenance"</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
