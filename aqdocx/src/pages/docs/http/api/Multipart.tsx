import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { Globe } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function HTTPAPIMultipart() {
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
            multipart.py
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Multipart/form-data builder with support for textual fields, byte payloads, file-like sources, async stream
          sources, and incremental chunk streaming for large uploads.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Overview</h2>
        <div className={boxClass}>
          <p className={`${isDark ? 'text-gray-400' : 'text-gray-600'} mb-3`}>
            multipart.py encapsulates outbound multipart body construction. It decouples form modeling from transport so
            high-level client APIs can upload files while preserving boundary integrity and optional streaming behavior.
          </p>
          <p className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
            Lifecycle fit: user declares fields/files -&gt; MultipartFormData encodes or streams body -&gt; request headers
            include content_type with generated boundary -&gt; transport sends bytes.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Architecture and Design</h2>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Core Data Model</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• FormField models scalar form entries with optional content type and filename metadata.</li>
              <li>• FormFile models file entries from bytes, BinaryIO, AsyncIterator[bytes], or pathlib.Path.</li>
              <li>• MultipartFormData maintains ordered lists of fields/files with boundary-specific serialization.</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Design Decisions</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• MIME type inference uses mimetypes.guess_type with application/octet-stream fallback.</li>
              <li>• encode() supports asynchronous source reading via run_in_executor for sync files and direct async iteration.</li>
              <li>• stream() yields multipart fragments incrementally to avoid buffering entire payload.</li>
              <li>• content_length() returns None when any file part has unknown length (streaming safety).</li>
            </ul>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. API Reference (Exhaustive)</h2>
        <CodeBlock language="python" filename="Data classes">{`@dataclass
class FormField:
    name: str
    value: str | bytes
    content_type: str | None = None
    filename: str | None = None

@dataclass
class FormFile:
    name: str
    filename: str
    content: bytes | BinaryIO | AsyncIterator[bytes] | Path
    content_type: str | None = None
    content_length: int | None = None

    def __post_init__(self)`}</CodeBlock>

        <CodeBlock language="python" filename="MultipartFormData signature">{`class MultipartFormData:
    def __init__(self, boundary: str | None = None)
    @staticmethod
    def _generate_boundary() -> str
    @property def boundary(self) -> str
    @property def content_type(self) -> str

    def field(self, name: str, value: str | bytes, content_type: str | None = None) -> MultipartFormData
    def file(
        self,
        name: str,
        filename: str,
        content: bytes | BinaryIO | AsyncIterator[bytes],
        content_type: str | None = None,
    ) -> MultipartFormData
    def file_from_path(
        self,
        name: str,
        path: Path | str,
        content_type: str | None = None,
        filename: str | None = None,
    ) -> MultipartFormData
    def file_from_bytes(
        self,
        name: str,
        filename: str,
        data: bytes,
        content_type: str | None = None,
    ) -> MultipartFormData

    def _encode_field(self, f: FormField) -> bytes
    async def _encode_file(self, f: FormFile) -> bytes
    async def _read_file_content(self, f: FormFile) -> bytes

    async def encode(self) -> bytes
    def encode_sync(self) -> bytes

    async def stream(self, chunk_size: int = 65536) -> AsyncIterator[bytes]
    async def _stream_file_content(self, f: FormFile, chunk_size: int) -> AsyncIterator[bytes]

    def content_length(self) -> int | None`}</CodeBlock>

        <div className={boxClass}>
          <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Error Surface</h3>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• encode_sync() raises ValueError when async-only content sources are present.</li>
            <li>• Path-based file reads may propagate OSError/IO errors during encoding/streaming.</li>
            <li>• Module does not directly raise Aquilia faults; upstream request/transport faults apply at send time.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Behavior and Lifecycle</h2>
        <CodeBlock language="python" filename="Multipart assembly flow">{`form = MultipartFormData()
form.field("name", "report")
form.file_from_path("attachment", "/tmp/report.pdf")

body = await form.encode()
content_type = form.content_type
content_length = form.content_length()`}</CodeBlock>

        <CodeBlock language="python" filename="Streaming flow">{`# for large files
async for part in form.stream(chunk_size=1024 * 1024):
    await transport_write(part)`}</CodeBlock>

        <div className={boxClass}>
          <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            State transitions: DECLARED (field/file calls) -&gt; ENCODED (encode/encode_sync) or STREAMED (stream).
            No internal one-shot lock exists, so forms may be re-encoded after declaration if source streams are reusable.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>5. Usage Examples</h2>
        <CodeBlock language="python" filename="Minimal">{`form = MultipartFormData().field("title", "image")
form.file_from_bytes("file", "avatar.png", image_bytes, "image/png")`}</CodeBlock>

        <CodeBlock language="python" filename="Real-world mixed sources">{`from pathlib import Path

form = (
    MultipartFormData()
    .field("tenant", "acme")
    .file_from_path("doc", Path("/tmp/contract.pdf"))
    .file("raw", "payload.bin", b"\x00\x01\x02")
)

response = await client.post("https://api.example.com/upload", files=form)`}</CodeBlock>

        <CodeBlock language="python" filename="Edge case: async source requires encode()">{`async def source():
    yield b"chunk-1"
    yield b"chunk-2"

form = MultipartFormData().file("f", "stream.dat", source())
await form.encode()      # valid
form.encode_sync()       # ValueError`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>6. Advanced Topics</h2>
        <div className="space-y-4">
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Performance and Memory</h3>
            <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              <li>• encode() materializes full payload in memory; use stream() for large or unbounded sources.</li>
              <li>• Path and BinaryIO reading uses executor offload to avoid blocking event loop on synchronous file reads.</li>
              <li>• content_length() enables fixed-length upload optimization when all file lengths are known.</li>
            </ul>
          </div>
          <div className={boxClass}>
            <h3 className={`font-bold mb-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>Extensibility</h3>
            <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
              Provide custom AsyncIterator sources for dynamic generation/encryption pipelines, or override content_type
              per part for strict upstream validation contracts.
            </p>
          </div>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>7. Integration</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• sessions: multipart uploads are transport-level concerns; session context may be propagated via headers.</li>
            <li>• config/pyconfig: chunk sizes and upload limits should be centralized in config and passed into stream() callers.</li>
            <li>• storage: direct bridge from storage readers (Path/file handles/async streams) into multipart file parts.</li>
            <li>• tasks: background upload tasks can serialize form metadata and reconstruct forms at worker runtime.</li>
            <li>• effects/flow: compose upload effects where multipart construction is isolated from business node logic.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>8. Best Practices</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• Prefer file_from_path for local files so content_length can often be inferred automatically.</li>
            <li>• Use explicit per-part content_type for APIs with strict MIME validation.</li>
            <li>• For large files, pair stream() with transport backpressure and timeout-aware retry policy.</li>
            <li>• Avoid reusing one-shot async iterators across multiple encode/stream invocations.</li>
          </ul>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>9. Edge Cases and Failure Modes</h2>
        <CodeBlock language="python" filename="Unknown content length">{`async def source():
    yield b"x"

form = MultipartFormData().file("f", "x.bin", source())
assert form.content_length() is None`}</CodeBlock>

        <CodeBlock language="python" filename="Filename escaping">{`form = MultipartFormData().file_from_bytes("f", 'x"y.txt', b"hello")
# quote characters are escaped in Content-Disposition filename field`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>10. Internal Notes</h2>
        <div className={boxClass}>
          <ul className={`space-y-2 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• Boundary format: ----AquilaHTTP&lt;uuid4hex&gt;.</li>
            <li>• encode() always emits CRLF separators and trailing final boundary CRLF.</li>
            <li>• file_from_bytes is a convenience wrapper over file().</li>
            <li>• RequestBuilder.multipart() currently stores multipart file data in request.extensions for later handling.</li>
          </ul>
        </div>
      </section>

      <div className={`text-sm ${isDark ? 'text-gray-500' : 'text-gray-500'}`}>
        Related references: <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/api/request">request.py</Link>,{' '}
        <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/api/streaming">streaming.py</Link>,{' '}
        <Link className="text-aquilia-500 hover:text-aquilia-400" to="/docs/http/client">HTTPClient</Link>.
      </div>

      <NextSteps
        items={[
          { text: 'streaming.py Reference', link: '/docs/http/api/streaming' },
          { text: 'HTTP Advanced Guide', link: '/docs/http/advanced' },
          { text: 'HTTP Transport Layer', link: '/docs/http/transport' },
        ]}
      />
    </div>
  )
}
