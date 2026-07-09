import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { Globe } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function HTTPAPIResponse() {
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
            response.py
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Immutable response envelope with lazy body consumption, streaming iterators, text/JSON decoding helpers,
          status classification, and fault-aware status escalation.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Overview</h2>
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 space-y-2">
          <p>
            <code className="text-aquilia-500 font-mono">response.py</code> is the terminal read model for outbound HTTP execution. It provides a single object that supports both buffered and streaming usage patterns.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. Architecture and Design</h2>
        <div className="space-y-4 text-sm text-zinc-500 border-l-2 border-aquilia-500/20 pl-4 py-1">
          <p>• Headers are stored as dictionaries supporting case-insensitive lookups.</p>
          <p>• Body can be pre-buffered or lazy-streamed with one-time consumption semantics.</p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>3. API Reference</h2>
        <CodeBlock language="python" filename="response.py signature" highlightLines={[2, 3, 10, 11]}>{`@dataclass
class HTTPClientResponse:
    status_code: int
    headers: dict[str, str]
    url: str
    http_version: str = "1.1"
    elapsed: float = 0.0
    history: list[HTTPClientResponse] = field(default_factory=list)

    _body: bytes | None = None
    _stream: AsyncIterator[bytes] | None = None

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300
`}</CodeBlock>
      </section>

      <NextSteps
        items={[
          { text: 'Request API', link: '/docs/http/api/request' },
          { text: 'Auth API', link: '/docs/http/api/auth' },
          { text: 'Cookies API', link: '/docs/http/api/cookies' },
          { text: 'Middleware API', link: '/docs/http/api/middleware' },
        ]}
      />
    </div>
  )
}
