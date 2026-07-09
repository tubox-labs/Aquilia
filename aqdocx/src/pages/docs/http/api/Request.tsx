import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { DocTerm } from '../../../../components/docPreview/DocTerm'
import { Globe } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function HTTPAPIRequest() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Globe className="w-4 h-4" />
          HTTP Client / Core API
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            request.py
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Low-level request construction primitives for AquilaHTTP. This module defines immutable request objects,
          URL/header/body validation, and the request builder used by <DocTerm id="http.AsyncHTTPClient">AsyncHTTPClient</DocTerm> and <DocTerm id="http.HTTPSession">HTTPSession</DocTerm>.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Overview</h2>
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 space-y-2">
          <p>
            <code className="text-aquilia-500 font-mono">request.py</code> is the canonical request-shaping boundary for the HTTP client subsystem. It is split into two layers:
          </p>
          <p>• <strong>HTTPClientRequest</strong>: immutable payload consumed by transport and interception stacks.</p>
          <p>• <strong>RequestBuilder</strong>: mutable fluent DSL that validates and materializes HTTPClientRequest.</p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Architecture and Design</h2>
        <div className="space-y-4 text-sm text-zinc-500 border-l-2 border-aquilia-500/20 pl-4 py-1">
          <p>• RequestBuilder stores mutable assembly state in private slots for low-overhead chaining.</p>
          <p>• build() emits HTTPClientRequest dataclass instances to isolate downstream processing from mutation.</p>
          <p>• Header names/values are validated to prevent malformed request lines and header injection issues.</p>
          <p>• JSON/form serialization occurs at build time, not transport time, so faults are deterministic.</p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. API Reference</h2>
        <CodeBlock language="python" filename="request.py core types" highlightLines={[1, 8]}>{`class HTTPMethod(str, Enum):
    GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS, TRACE, CONNECT

HeadersType = Mapping[str, str] | list[tuple[str, str]] | None
ParamsType = Mapping[str, str | int | float | bool | None] | list[tuple[str, str]] | None
CookiesType = Mapping[str, str] | None
DataType = Mapping[str, Any] | str | bytes | None
JsonType = Any
ContentType = str | bytes | AsyncIterator[bytes] | BinaryIO | None
`}</CodeBlock>

        <CodeBlock language="python" filename="request.py validation helpers" highlightLines={[1, 4]}>{`def _normalize_header_name(name: str) -> str:
    # Title-Case normalization
    return name.title()

def _validate_header_name(name: str) -> None:
    # Raises InvalidHeaderFault on empty or control chars
    pass
`}</CodeBlock>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>4. Hardening and Edge Cases</h2>
        <div className="border-l-2 border-amber-500/20 pl-4 py-1 text-sm text-zinc-500 space-y-2">
          <p>• Dotted keys and complex query structures are fully supported and urlencoded automatically.</p>
          <p>• Request headers are strictly validated to prevent CR-LF injection vectors.</p>
        </div>
      </section>

      <NextSteps
        items={[
          { text: 'Response API', link: '/docs/http/api/response' },
          { text: 'Auth API', link: '/docs/http/api/auth' },
          { text: 'Cookies API', link: '/docs/http/api/cookies' },
          { text: 'Middleware API', link: '/docs/http/api/middleware' },
        ]}
      />
    </div>
  )
}
