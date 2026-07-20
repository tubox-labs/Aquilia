import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { ArrowLeft, ArrowRight, Cpu } from 'lucide-react'
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
          Bind incoming HTTP metadata directly to your dependency parameters with the built-in <code className="text-aquilia-500">Header</code>, <code className="text-aquilia-500">Query</code>, <code className="text-aquilia-500">Cookie</code>, <code className="text-aquilia-500">Path</code>, and <code className="text-aquilia-500">Body</code> extractors. Values are cast and validated through the Contract facet pipeline.
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

      {/* Casting note */}
      <section className="mb-16">
        <div className="border-l-4 border-aquilia-500 bg-aquilia-500/5 pl-6 py-4 rounded-r-xl">
          <p className={`text-sm leading-relaxed ${subtleText}`}>
            <strong className="text-aquilia-500">Automatic coercion.</strong> Extracted raw strings are cast to the annotated type through the Contract facet pipeline — <code className="text-aquilia-500">Annotated[int, Query("page")]</code> yields a real <code className="text-aquilia-500">int</code>, not a string. A failed cast returns a structured <code className="text-aquilia-500">BadRequestFault</code> (HTTP 400). All five extractors accept <code className="text-aquilia-500">alias</code> to map a differently-named source key.
          </p>
        </div>
      </section>

      {/* Header */}
      <section className="mb-16 border-l-2 border-aquilia-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Header</h2>
        <p className={`mb-4 ${subtleText}`}>
          Extracts an HTTP header. Lookups are case-insensitive. <code className="text-aquilia-500">required</code> defaults to <strong>True</strong>.
        </p>
        <CodeBlock language="python" filename="Header">{`from aquilia.di import Header

@dataclass(frozen=True)
class Header:
    name: str                    # header name, e.g. "Authorization"
    alias: str | None = None     # alternate lookup key
    required: bool = True        # missing -> BadRequestFault (HTTP 400)
    default: Any = None          # fallback when not required

# Usage
async def auth(token: Annotated[str, Header("Authorization")]) -> str:
    return token.removeprefix("Bearer ")`}</CodeBlock>
      </section>

      {/* Query */}
      <section className="mb-16 border-l-2 border-orange-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Query</h2>
        <p className={`mb-4 ${subtleText}`}>
          Extracts a query-string value (<code>?key=value</code>). <code className="text-aquilia-500">required</code> defaults to <strong>False</strong>.
        </p>
        <CodeBlock language="python" filename="Query">{`from aquilia.di import Query

@dataclass(frozen=True)
class Query:
    name: str | None = None      # query key, e.g. "page"
    default: Any = None          # value when absent
    required: bool = False       # missing + required -> BadRequestFault
    alias: str | None = None     # alternate key

# Usage — cast to int with a default
async def page(n: Annotated[int, Query("page", default=1)]) -> int:
    return n`}</CodeBlock>
      </section>

      {/* Cookie */}
      <section className="mb-16 border-l-2 border-purple-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Cookie</h2>
        <p className={`mb-4 ${subtleText}`}>
          Extracts a cookie value. <code className="text-aquilia-500">required</code> defaults to <strong>False</strong>.
        </p>
        <CodeBlock language="python" filename="Cookie">{`from aquilia.di import Cookie

@dataclass(frozen=True)
class Cookie:
    name: str | None = None
    default: Any = None
    required: bool = False
    alias: str | None = None

# Usage
async def sess(sid: Annotated[str, Cookie("session_id")]) -> str:
    return sid`}</CodeBlock>
      </section>

      {/* Path */}
      <section className="mb-16 border-l-2 border-blue-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Path</h2>
        <p className={`mb-4 ${subtleText}`}>
          Extracts a route/path parameter. <code className="text-aquilia-500">required</code> defaults to <strong>True</strong>.
        </p>
        <CodeBlock language="python" filename="Path">{`from aquilia.di import Path

@dataclass(frozen=True)
class Path:
    name: str | None = None
    default: Any = None
    required: bool = True
    alias: str | None = None

# Usage — matches @get("/users/{user_id}"), cast to int
async def load(user_id: Annotated[int, Path()]) -> int:
    return user_id`}</CodeBlock>
      </section>

      {/* Body */}
      <section className="mb-16 border-l-2 border-green-500/30 pl-6">
        <h2 className={`text-2xl font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Body</h2>
        <p className={`mb-4 ${subtleText}`}>
          Injects the parsed request body. Pair with a Contract type for full validation.
        </p>
        <CodeBlock language="python" filename="Body">{`from aquilia.di import Body

@dataclass(frozen=True)
class Body:
    media_type: str = "application/json"
    embed: bool = False

# Usage
async def create(data: Annotated[dict, Body()]) -> dict:
    return data`}</CodeBlock>
      </section>

      {/* Errors */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Error Handling</h2>
        <div className="border-l-4 border-red-500 bg-red-500/5 pl-4 py-3 rounded-r-xl my-6">
          <p className="text-xs text-red-500/90 leading-relaxed">
            A missing <code className="text-red-500">required</code> value, a null where null is disallowed, or a failed type cast raises <strong>BadRequestFault</strong>. The Fault Engine renders it as a structured HTTP 400 automatically — you never write the 400 yourself.
          </p>
        </div>
      </section>

      {/* Navigation */}
      <div className={`mt-16 pt-8 border-t flex justify-between ${isDark ? 'border-white/5' : 'border-gray-200'}`}>
        <Link to="/docs/di/request-dag" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          <ArrowLeft className="w-4 h-4" /> RequestDAG
        </Link>
        <Link to="/docs/di/patterns" className="flex items-center gap-2 text-aquilia-500 hover:text-aquilia-400 transition font-medium">
          Patterns &amp; Recipes <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
