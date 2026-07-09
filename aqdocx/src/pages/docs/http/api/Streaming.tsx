import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { DocTerm } from '../../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { Globe } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function HTTPAPIStreaming() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderSubtle = isDark ? 'border-white/5' : 'border-gray-100'

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
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Asynchronous request-body and response-body streaming primitives for AquilaHTTP.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Overview</h2>
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 space-y-2">
          <p>
            <code className="text-aquilia-500 font-mono">streaming.py</code> defines progress callbacks, backpressure mechanisms, and streaming helpers.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. API Reference</h2>
        <CodeBlock language="python" filename="streaming.py classes" highlightLines={[1, 6]}>{`class StreamingBody:
    def __init__(
        self,
        generator: AsyncIterator[bytes] | BinaryIO,
        chunk_size: int = 8192,
        on_progress: Callable[[UploadProgress], None] | None = None,
    )
`}</CodeBlock>
      </section>

      <NextSteps
        items={[
          { text: 'Request API', link: '/docs/http/api/request' },
          { text: 'Response API', link: '/docs/http/api/response' },
          { text: 'Auth API', link: '/docs/http/api/auth' },
          { text: 'Cookies API', link: '/docs/http/api/cookies' },
        ]}
      />
    </div>
  )
}
