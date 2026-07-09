import { useTheme } from '../../../../context/ThemeContext'
import { CodeBlock } from '../../../../components/CodeBlock'
import { DocTerm } from '../../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { Globe } from 'lucide-react'
import { NextSteps } from '../../../../components/NextSteps'

export function HTTPAPICookies() {
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
            cookies.py
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          RFC 6265 compliant Cookie and CookieJar primitives for managing HTTP cookies.
        </p>
      </div>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>1. Overview</h2>
        <div className="border-l-2 border-aquilia-500/20 pl-4 py-1 text-sm text-zinc-500 space-y-2">
          <p>
            <code className="text-aquilia-500 font-mono">cookies.py</code> manages cookie attributes (SameSite, Secure, HttpOnly), domain matching, and path hierarchies.
          </p>
        </div>
      </section>

      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>2. API Reference</h2>
        <CodeBlock language="python" filename="cookies.py classes" highlightLines={[2, 10, 11]}>{`@dataclass
class Cookie:
    name: str
    value: str
    domain: str | None = None
    path: str | None = None
    expires: datetime | None = None
    max_age: int | None = None
    secure: bool = False
    http_only: bool = False
    same_site: str | None = None
`}</CodeBlock>
      </section>

      <NextSteps
        items={[
          { text: 'Request API', link: '/docs/http/api/request' },
          { text: 'Response API', link: '/docs/http/api/response' },
          { text: 'Auth API', link: '/docs/http/api/auth' },
          { text: 'Middleware API', link: '/docs/http/api/middleware' },
        ]}
      />
    </div>
  )
}
