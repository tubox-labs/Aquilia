import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Globe } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function HTTPAPIStreaming() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Globe className="w-4 h-4" />
          HTTP Client / Core API
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            streaming.py
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Async streaming primitives for upload/download pipelines, including progress callbacks, bounded streaming,
          buffered line reads, and HTTP chunked transfer encoding helpers.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Overview</h2>
        <div className={boxClass}>
          <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'} mb-3`}>
            streaming.py is the low-level stream utility module consumed by request bodies, multipart upload paths,
            and response consumers. It standardizes async iteration with optional observability hooks.
          </p>
          <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
            Lifecycle fit: source bytes/file/iterator -&gt; StreamingBody/utility wrappers -&gt; transport writes or response
            consumers decode chunked data and buffered lines.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Architecture and Design</h2>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Primary Building Blocks</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• StreamProgress: immutable transfer telemetry with percentage/rate/ETA derivations.</li>
              <li>• StreamingBody: source adapter for bytes, file handles, paths, and async iterators.</li>
              <li>• Utility coroutines: stream_file, stream_bytes, collect_stream, stream_with_limit.</li>
              <li>• BufferedStream: stateful buffered decoder for read/readline/readlines semantics.</li>
              <li>• ChunkedEncoder/ChunkedDecoder: HTTP/1.1 chunked transfer framing helpers.</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Data Flow</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              All high-volume I/O is chunk-oriented. Blocking file reads are offloaded using run_in_executor. stream_bytes
              yields control with asyncio.sleep(0) for cooperative scheduling in long loops.
            </p>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. API Reference (Exhaustive)</h2>
        <CodeBlock language="python" filename="StreamProgress and callback type">{`@dataclass
class StreamProgress:
    bytes_transferred: int
    total_bytes: int | None
    elapsed: float

    @property def percentage(self) -> float | None
    @property def bytes_per_second(self) -> float
    @property def eta_seconds(self) -> float | None

ProgressCallback = (
    Callable[[StreamProgress], Coroutine[Any, Any, None]]
    | Callable[[StreamProgress], None]
)`}</CodeBlock>

        <CodeBlock language="python" filename="StreamingBody signature">{`class StreamingBody:
    def __init__(
        self,
        source: bytes | AsyncIterator[bytes] | BinaryIO | Path,
        *,
        chunk_size: int = 65536,
        total_size: int | None = None,
        on_progress: ProgressCallback | None = None,
    )
    @property def content_length(self) -> int | None
    async def __aiter__(self) -> AsyncIterator[bytes]
    async def _iter_source(self) -> AsyncIterator[bytes]`}</CodeBlock>

        <CodeBlock language="python" filename="Utility functions">{`async def stream_file(path: Path | str, *, chunk_size: int = 65536) -> AsyncIterator[bytes]
async def stream_bytes(data: bytes, chunk_size: int = 65536) -> AsyncIterator[bytes]
async def collect_stream(stream: AsyncIterator[bytes]) -> bytes
async def stream_with_limit(stream: AsyncIterator[bytes], max_bytes: int) -> AsyncIterator[bytes]
# raises ValueError if max_bytes is exceeded`}</CodeBlock>

        <CodeBlock language="python" filename="Buffered and chunked helpers">{`class BufferedStream:
    def __init__(self, stream: AsyncIterator[bytes], encoding: str = "utf-8")
    async def readline(self) -> str
    async def readlines(self) -> list[str]
    async def read(self, n: int = -1) -> bytes

class ChunkedEncoder:
    def __init__(self, stream: AsyncIterator[bytes])
    async def __aiter__(self) -> AsyncIterator[bytes]

class ChunkedDecoder:
    def __init__(self, stream: AsyncIterator[bytes])
    async def __aiter__(self) -> AsyncIterator[bytes]`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Behavior and Lifecycle</h2>
        <CodeBlock language="python" filename="StreamingBody lifecycle">{`body = StreamingBody(Path("/tmp/big.bin"), chunk_size=1024 * 1024)

async for chunk in body:
    # progress callback invoked after each yielded chunk
    await send(chunk)`}</CodeBlock>

        <CodeBlock language="python" filename="Chunked decode lifecycle">{`decoder = ChunkedDecoder(raw_stream)
async for decoded in decoder:
    consume(decoded)
# returns when terminal 0-size chunk is received`}</CodeBlock>

        <div className={boxClass}>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            Async model: all streaming interfaces are pull-driven by consumer iteration. Backpressure is naturally
            enforced because producers emit only when the consumer awaits the next chunk.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>5. Usage Examples</h2>
        <CodeBlock language="python" filename="Minimal">{`async for chunk in stream_bytes(b"hello world", chunk_size=4):
    print(chunk)`}</CodeBlock>

        <CodeBlock language="python" filename="Progress callback">{`async def on_progress(p: StreamProgress):
    print(p.bytes_transferred, p.percentage, p.bytes_per_second)

body = StreamingBody(Path("/tmp/archive.tar"), on_progress=on_progress)
async for chunk in body:
    await upload_chunk(chunk)`}</CodeBlock>

        <CodeBlock language="python" filename="Bounded stream">{`safe_stream = stream_with_limit(upstream_chunks(), max_bytes=10_000_000)
async for chunk in safe_stream:
    write(chunk)
# ValueError raised immediately when limit is exceeded`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>6. Advanced Topics</h2>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Performance</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• Tune chunk_size based on network and storage characteristics; default 64 KiB is a compromise baseline.</li>
              <li>• collect_stream is convenience-oriented and should be avoided for unbounded or very large streams.</li>
              <li>• stream_file uses executor-backed reads to avoid event-loop stalls from sync file I/O.</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Extensibility</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              ProgressCallback supports sync or async callables, making it easy to push telemetry to metrics pipelines,
              tracing spans, or custom adaptive throttling logic.
            </p>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>7. Integration</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• sessions: streaming itself is session-agnostic; session headers can still be attached at request layer.</li>
            <li>• config/pyconfig: chunk sizing and byte limits should be policy-driven from config profiles.</li>
            <li>• storage: stream_file and StreamingBody(Path/IO) integrate directly with storage upload/download pipelines.</li>
            <li>• tasks: long-running stream operations are natural candidates for task workers with progress reporting.</li>
            <li>• effects/flow: model stream transformations as explicit effect stages for deterministic retry/fallback behavior.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>8. Best Practices</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• Use stream_with_limit defensively on untrusted upstream streams.</li>
            <li>• Prefer async callbacks for progress when callback I/O is non-trivial.</li>
            <li>• Consume ChunkedDecoder output promptly to avoid buffer growth on high-throughput inputs.</li>
            <li>• Use BufferedStream when line semantics are required instead of manual split logic.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>9. Edge Cases and Failure Modes</h2>
        <CodeBlock language="python" filename="Limit exceeded">{`async for _ in stream_with_limit(stream_bytes(b"012345"), max_bytes=3):
    pass
# raises ValueError("Stream exceeded 3 bytes limit")`}</CodeBlock>

        <CodeBlock language="python" filename="Chunk decoder malformed size">{`# invalid hexadecimal chunk size lines are ignored by decoder loop break behavior
# consumers should wrap decoder with protocol validation if strict handling is required`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>10. Internal Notes</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• StreamProgress.eta_seconds returns None when total_bytes is unknown or transfer rate is zero.</li>
            <li>• stream_file defines an internal _read_chunks helper that is currently unused in the live path.</li>
            <li>• ChunkedEncoder emits terminal marker 0\r\n\r\n after source exhaustion.</li>
            <li>• BufferedStream.read(-1) drains the full iterator into memory.</li>
          </ul>
        </div>
      </section>

      <div className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
        Related references: <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/api/response">response.py</Link>,{' '}
        <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/api/multipart">multipart.py</Link>,{' '}
        <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/transport">Transport Layer</Link>.
      </div>

      <NextSteps
        items={[
          { text: 'Return to HTTP API Request', link: '/docs/http/api/request' },
          { text: 'HTTP Transport Internals', link: '/docs/http/transport' },
          { text: 'HTTP Advanced Usage', link: '/docs/http/advanced' },
        ]}
      />
    </div>
  )
}
