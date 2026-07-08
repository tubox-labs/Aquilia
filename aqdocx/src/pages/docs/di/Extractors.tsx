import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { ArrowLeft, Cpu } from 'lucide-react'
import { Link } from 'react-router-dom'
import { NextSteps } from '../../../components/NextSteps'

export function DIExtractors() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const subtleText = isDark ? 'text-gray-400' : 'text-gray-600'

  return (
    <div className="max-w-4xl mx-auto animate-fade-in select-none">
      {/* Title Header */}
      <div className="mb-12 relative overflow-hidden rounded-3xl bg-gradient-to-br from-aquilia-500/10 via-transparent to-transparent p-8 border border-white/5 shadow-2xl backdrop-blur-md">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Cpu className="w-4 h-4" />
          Dependency Injection / Extractors
        </div>
        <h1 className={`text-4xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'} mb-4`}>
          HTTP Parameter Extractors
        </h1>
        <p className={`text-lg leading-relaxed ${subtleText}`}>
          Bind incoming HTTP metadata directly to your service parameters using the built-in <code className="text-aquilia-500">Header</code>, <code className="text-aquilia-500">Query</code>, and <code className="text-aquilia-500">Body</code> extractors.
        </p>
      </div>

      {/* Overview */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>How Extractors Work</h2>
        <p className={`mb-4 ${subtleText}`}>
          When the <code className="text-aquilia-500">RequestDAG</code> resolves dependencies, it checks if any parameter is annotated with an extractor dataclass. If it is, the DAG intercepts the resolution and reads the value straight from the request:
        </p>

        <CodeBlock language="python" filename="Extractor Usage">{`from typing import Annotated
from aquilia.di import Header, Query, Dep
from aquilia.controller import Controller, get

async def search_telemetry(
    user_agent: Annotated[str, Header("User-Agent")],
    search_query: Annotated[str, Query("q", default="")]
):
    print(f"Tracking search: {search_query} from {user_agent}")
    return search_query

class SearchController(Controller):
    # Recommended constructor injection for app-wide services
    def __init__(self, telemetry_client: TelemetryClient):
        self.telemetry = telemetry_client

    @get("/search")
    async def search_view(
        self,
        ctx,
        query: Annotated[str, Dep(search_telemetry)]
    ):
        await self.telemetry.track("search_run")
        return {"status": "ok", "q": query}`}</CodeBlock>
      </section>

      {/* Header */}
      <section className="mb-16 border-l-2 border-aquilia-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Header</h2>
        <p className={`mb-4 ${subtleText}`}>
          Extracts a specific HTTP header. Header name lookups are case-insensitive.
        </p>
        <CodeBlock language="python" filename="Header Attributes">{`from aquilia.di import Header

@dataclass
class Header:
    name: str                   # Header name (e.g. "Authorization")
    alias: Optional[str] = None # Alias key mapping
    required: bool = True       # Raises ValidationFault if missing
    default: Any = None         # Fallback value`}</CodeBlock>
      </section>

      {/* Query */}
      <section className="mb-16 border-l-2 border-orange-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Query</h2>
        <p className={`mb-4 ${subtleText}`}>
          Extracts values from the query string (`?key=value`).
        </p>
        <CodeBlock language="python" filename="Query Attributes">{`from aquilia.di import Query

@dataclass
class Query:
    name: str                   # Key key (e.g. "page")
    default: Any = None         # Default value
    required: bool = False      # Raises ValidationFault if missing`}</CodeBlock>
      </section>

      {/* Body */}
      <section className="mb-16 border-l-2 border-green-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Body</h2>
        <p className={`mb-4 ${subtleText}`}>
          Directly injects the parsed request body.
        </p>
        <CodeBlock language="python" filename="Body Attributes">{`from aquilia.di import Body

@dataclass
class Body:
    media_type: str = "application/json"   # Expected content-type`}</CodeBlock>
      </section>

      {/* Errors */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Error Handling</h2>
        <div className="border-l-4 border-red-500 bg-red-500/5 pl-4 py-3 rounded-r-xl my-6">
          <p className="text-xs text-red-500/90 leading-relaxed">
            If an extractor is marked as <code className="text-red-500">required=True</code> and the value doesn't exist in the HTTP request, Aquilia raises a <strong>ValidationFault</strong>. The Fault Engine intercepts this to return a structured HTTP 400 Bad Request to the client automatically.
          </p>
        </div>
      </section>

      {/* Navigation */}
      <div className={`mt-16 pt-8 border-t flex justify-between ${isDark ? 'border-white/5' : 'border-gray-200'}`}>
        <Link to="/docs/di/request-dag" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> RequestDAG
        </Link>
        <span />
      </div>

      <NextSteps />
    </div>
  )
}
