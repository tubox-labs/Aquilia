import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function HTTPAdvanced() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderSubtle = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Globe className="w-4 h-4" />
          HTTP Client / Advanced
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Advanced Usage
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Advanced HTTP client features: streaming, retry strategies, interceptors, and middleware.
        </p>
      </div>

      {/* Streaming Responses */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Streaming Responses</h2>
        <p className={`mb-4 ${textMuted}`}>
          Process large response payloads without loading the entire body into memory:
        </p>
        <CodeBlock language="python" filename="streaming.py" highlightLines={[8, 13, 28, 34]}>{`client = AsyncHTTPClient()

# Stream response body bytes
response = await client.get("https://example.com/large-file.csv")

async for chunk in response.iter_bytes(chunk_size=8192):
    # Process chunk (bytes)
    process_data(chunk)

# Stream to file
response = await client.get("https://example.com/video.mp4")
with open("video.mp4", "wb") as f:
    async for chunk in response.iter_bytes():
        f.write(chunk)

# Stream lines (text)
response = await client.get("https://example.com/logs.txt")
async for line in response.iter_lines():
    # Each line is decoded as UTF-8
    print(f"Log: {line}")

# Stream JSON lines (JSONL/NDJSON)
response = await client.get("https://api.example.com/stream")
async for line in response.iter_lines():
    if line.strip():
        record = json.loads(line)
        process_record(record)`}</CodeBlock>
      </section>

      {/* Streaming Requests */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Streaming Requests</h2>
        <p className={`mb-4 ${textMuted}`}>
          Stream large file uploads or generators to minimize memory footprint:
        </p>
        <CodeBlock language="python" filename="streaming_request.py" highlightLines={[8, 17]}>{`# Stream file upload without loading into memory
async def file_stream():
    with open("large-file.bin", "rb") as f:
        while chunk := f.read(1024 * 64):
            yield chunk

response = await client.post(
    "/upload",
    data=file_stream(),
    headers={"Content-Type": "application/octet-stream"},
)

# Stream generated data
async def data_generator():
    for i in range(100):
        yield f"Line {i}\n".encode()

response = await client.post("/stream-upload", data=data_generator())
`}</CodeBlock>
      </section>

      {/* Retry Strategies */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Retry Strategies</h2>
        <p className={`mb-4 ${textMuted}`}>
          Configure automatic retries with exponential backoff for transient failures using <DocTerm id="http.RetryConfig">RetryConfig</DocTerm>:
        </p>
        <CodeBlock language="python" filename="retry.py" highlightLines={[4, 5, 8]}>{`from aquilia.http import AsyncHTTPClient, RetryConfig

client = AsyncHTTPClient(HTTPClientConfig(
    retry=RetryConfig(
        max_attempts=3,          # Retry up to 3 times
        backoff_base=1.0,        # Exponential backoff base delay (seconds)
        backoff_max=30.0,        # Cap backoff delay
        retry_on_status={408, 429, 500, 502, 503, 504},
    ),
))`}</CodeBlock>
      </section>

      {/* Interceptors */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Interceptors</h2>
        <p className={`mb-4 ${textMuted}`}>
          Hook actions that execute before a request is sent, or after a response is received:
        </p>
        <CodeBlock language="python" filename="interceptors.py" highlightLines={[3, 7, 21]}>{`from aquilia.http.interceptors import HTTPInterceptor

# Logging interceptor
class LoggingInterceptor(HTTPInterceptor):
    async def intercept(self, request, handler):
        print(f"→ {request.method} {request.url}")
        response = await handler(request)
        print(f"← {response.status_code} {response.url}")
        return response

client = AsyncHTTPClient(interceptors=[
    LoggingInterceptor(),
])
`}</CodeBlock>
      </section>

      {/* Concurrency */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Concurrent Requests</h2>
        <CodeBlock language="python" filename="concurrency.py" highlightLines={[8, 18]}>{`import asyncio

client = AsyncHTTPClient()

urls = [
    "https://api.example.com/users/1",
    "https://api.example.com/users/2",
]

responses = await asyncio.gather(*[
    client.get(url) for url in urls
])

# Limit concurrency with semaphore
semaphore = asyncio.Semaphore(5)

async def fetch(url: str):
    async with semaphore:
        return await client.get(url)
`}</CodeBlock>
      </section>

      {/* Proxy Support */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Proxy Support</h2>
        <CodeBlock language="python" filename="proxy.py" highlightLines={[3, 8]}>{`# HTTP proxy
client = AsyncHTTPClient(HTTPClientConfig(
    proxy=ProxyConfig(http_proxy="http://proxy.example.com:8080"),
))

# Environment variable fallback
import os
os.environ["HTTP_PROXY"] = "http://proxy.example.com:8080"
client = AsyncHTTPClient()
`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderSubtle}`}>
        <Link to="/docs/http/transport" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Transport Layer
        </Link>
        <Link to="/docs/http/faults" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Error Handling <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}
