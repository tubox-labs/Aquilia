import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function HTTPIntegration() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderSubtle = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Globe className="w-4 h-4" />
          HTTP Client / Integration
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Aquilia Integration
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Using the HTTP client within Aquilia: dependency injection, config builders, and integration with other subsystems.
        </p>
      </div>

      {/* Dependency Injection */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Dependency Injection</h2>
        <p className={`mb-4 ${textMuted}`}>
          The <DocTerm id="http.AsyncHTTPClient">AsyncHTTPClient</DocTerm> integrates seamlessly with Aquilia&apos;s DI container:
        </p>
        <CodeBlock language="python" filename="di_basic.py" highlightLines={[8, 13]}>{`from aquilia import Controller, RequestCtx, Response
from aquilia.http import AsyncHTTPClient

class UsersController(Controller):
    prefix = "/users"
    
    def __init__(self, http: AsyncHTTPClient):
        self.http = http
    
    async def get_user_data(self, ctx: RequestCtx):
        response = await self.http.get("https://api.github.com/users/octocat")
        user_data = await response.json()
        return Response.json(user_data)
`}</CodeBlock>
      </section>

      {/* Configuration via Workspace */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Configuration via Workspace</h2>
        <p className={`mb-4 ${textMuted}`}>
          Configure HTTP clients in your <code className="text-aquilia-500">workspace.py</code>:
        </p>
        <CodeBlock language="python" filename="workspace.py" highlightLines={[7, 19, 29]}>{`from aquilia import Workspace, Integration
from aquilia.http import HTTPClientConfig, TimeoutConfig, RetryConfig, PoolConfig

workspace = Workspace(
    integrations=[
        # Configure default HTTP client
        Integration.http_client(
            config=HTTPClientConfig(
                timeout=TimeoutConfig(total=30.0),
                pool=PoolConfig(max_connections=100),
            ),
        ),
        
        # Named HTTP client for specific API
        Integration.http_client(
            name="github_client",
            config=HTTPClientConfig(
                base_url="https://api.github.com",
            ),
        ),
    ],
)
`}</CodeBlock>
      </section>

      {/* Provider Scopes */}
      <section className="mb-16 border-l border-aquilia-500/20 pl-6 py-1">
        <h2 className={`text-xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Provider Scopes</h2>
        <p className={`text-sm mb-4 ${textMuted}`}>
          HTTP clients can be registered with different DI scopes:
        </p>
        <div className="space-y-4">
          <div>
            <strong className={`font-mono text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>Singleton (default)</strong>
            <p className={`text-xs ${textMuted}`}>One client instance shared across the entire app lifecycle. This is highly recommended to benefit from connection pooling reuse.</p>
          </div>
          <div>
            <strong className={`font-mono text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>Request Scope</strong>
            <p className={`text-xs ${textMuted}`}>Creates a new client instance per request. Use with caution as it destroys pooling efficiency.</p>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderSubtle}`}>
        <Link to="/docs/http/faults" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Error Handling
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}
