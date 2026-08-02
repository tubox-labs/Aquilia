import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { motion } from 'framer-motion'
import { NextSteps } from '../../../components/NextSteps'

export function ADPTransportEnginePage() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl">
      <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.25 }}>
        <h1 className={`text-4xl font-extrabold tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Native Transport Engine
        </h1>
        
        <p className={`text-lg leading-relaxed mb-8 ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
          Unlike traditional development servers that rely on external process wrappers, the Aquilia Development Platform (ADP) 
          features a custom network transport. It runs directly inside your application process, using asyncio socket streams 
          coupled with a strict <code className="text-sm font-mono">h11</code> state machine to achieve high-performance 
          keep-alive HTTP/1.1 parsing and RFC 6455 WebSocket handoffs.
        </p>
      </motion.div>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-white/10 text-white' : 'border-gray-100 text-gray-900'}`}>
          The H11 Connection Pipeline
        </h2>
        <p className={`text-base leading-relaxed mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          At the core of HTTP processing is the <DocTerm id="devplatform.server">H11Connection</DocTerm> class. Instantiated 
          for every accepted socket connection, it encapsulates the StreamReader and StreamWriter. By utilizing Python's 
          asyncio loop, it drives h11's event loop to stream incoming bytes, process pipelined requests, and handle keep-alives 
          without dropping connections.
        </p>

        <CodeBlock 
          language="python" 
          title="aquilia/devplatform/core/h11_transport.py"
          highlightLines={[21, 22, 26, 27]}
          code={`class H11Connection:
    __slots__ = ("reader", "writer", "app", "conn", "_client_addr")

    def __init__(self, reader, writer, app, server_addr):
        self.reader = reader
        self.writer = writer
        self.app = app
        self.conn = h11.Connection(h11.SERVER)
        self._client_addr = writer.get_extra_info("peername")

    async def run(self) -> None:
        try:
            while True:
                # Read next request event from stream
                request = await self._read_request()
                if request is None:
                    break

                # Inspect for WebSocket upgrades
                if _is_websocket_upgrade(request):
                    await self._ws_upgrade_hook(self, request)
                    break  # WebSocket took over socket

                # Dispatch HTTP transaction to ASGI app
                await self._dispatch(request)

                if self.conn.our_state is h11.MUST_CLOSE:
                    break
                self.conn.start_next_cycle()
        finally:
            self.writer.close()`}
        />
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-white/10 text-white' : 'border-gray-100 text-gray-900'}`}>
          WebSocket Upgrades
        </h2>
        <p className={`text-base leading-relaxed mb-6 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          When a request containing <code className="text-sm font-mono">Upgrade: websocket</code> is detected by the transport engine, 
          the connection state machine issues a <code className="text-sm font-mono">SWITCHED_PROTOCOL</code> response. 
          The raw TCP socket ownership is immediately handed off to the devplatform's WebSocket transport layer. 
          This avoids running two separate servers on different ports during development, allowing WebSocket and HTTP traffic 
          to multiplex seamlessly on port 8000.
        </p>
      </section>

      <section className="mt-12">
        <h2 className={`text-2xl font-bold mb-4 pb-2 border-b ${isDark ? 'border-white/10 text-white' : 'border-gray-100 text-gray-900'}`}>
          Under the Hood: Socket Activations & FD Inheritance
        </h2>
        <p className={`text-base leading-relaxed mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          To support integration with advanced system supervisors (like systemd, launchd, or custom process controllers), 
          the transport engine supports inheriting open socket file descriptors (<code className="text-sm font-mono">fd</code>) 
          and Unix Domain Sockets (<code className="text-sm font-mono">uds</code>):
        </p>
        <ul className={`space-y-4 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          <li>
            <strong className={isDark ? 'text-white' : 'text-gray-900'}>Unix Domain Sockets (UDS):</strong> 
            ADP can bind to filesystem paths. When <code className="text-sm font-mono">uds</code> is set in 
            <DocTerm id="devplatform.config">AquiliaDevelopmentConfig</DocTerm>, the server runs <code className="text-sm font-mono">asyncio.start_unix_server</code> 
            and automatically cleans up the socket file on exit.
          </li>
          <li>
            <strong className={isDark ? 'text-white' : 'text-gray-900'}>File Descriptor (FD) Inheritance:</strong> 
            By passing a file descriptor index using the <code className="text-sm font-mono">fd</code> config option, 
            ADP skips binding/listening completely, directly instantiating a Python socket wrapper around the inherited descriptor.
          </li>
        </ul>
      </section>

      <section className="mt-12">
        <NextSteps items={[
          { text: 'Plugins', link: '/docs/devplatform/plugins' },
          { text: 'Faults', link: '/docs/devplatform/faults' },
        ]} />
      </section>
    </div>
  )
}
