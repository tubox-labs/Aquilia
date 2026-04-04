import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function HTTPAdvanced() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

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
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Advanced HTTP client features: streaming, retry strategies, interceptors, and middleware.
        </p>
      </div>

      {/* Streaming Responses */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Streaming Responses</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Process large responses without loading the entire body into memory:
        </p>
        <CodeBlock language="python" filename="streaming.py">{`client = HTTPClient()

# Stream response body
response = await client.get("https://example.com/large-file.csv")

async for chunk in response.stream():
    # Process chunk (bytes)
    process_data(chunk)
    # chunk is ~8KB by default

# Stream to file
response = await client.get("https://example.com/video.mp4")
with open("video.mp4", "wb") as f:
    async for chunk in response.stream():
        f.write(chunk)

# Stream with progress tracking
total_size = int(response.headers.get("Content-Length", 0))
downloaded = 0

async for chunk in response.stream(chunk_size=1024 * 64):  # 64KB chunks
    downloaded += len(chunk)
    progress = (downloaded / total_size) * 100
    print(f"Progress: {progress:.1f}%")
    write_to_disk(chunk)

# Stream lines (text)
response = await client.get("https://example.com/logs.txt")
async for line in response.stream_lines():
    # Each line is decoded as UTF-8
    print(f"Log: {line}")

# Stream JSON lines (JSONL/NDJSON)
response = await client.get("https://api.example.com/stream")
async for line in response.stream_lines():
    if line.strip():
        record = json.loads(line)
        process_record(record)`}</CodeBlock>
      </section>

      {/* Streaming Requests */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Streaming Requests</h2>
        <CodeBlock language="python" filename="streaming_request.py">{`# Stream file upload without loading into memory
async def file_stream():
    with open("large-file.bin", "rb") as f:
        while chunk := f.read(1024 * 64):  # 64KB chunks
            yield chunk

response = await client.post(
    "/upload",
    data=file_stream(),
    headers={"Content-Type": "application/octet-stream"},
)

# Stream generated data
async def data_generator():
    for i in range(1000):
        yield f"Line {i}\n".encode()
        await asyncio.sleep(0.01)  # Simulate slow generation

response = await client.post("/stream-upload", data=data_generator())

# Multipart streaming upload
from aquilia.http import MultipartEncoder

encoder = MultipartEncoder(fields={
    "file1": ("data.csv", open("data.csv", "rb"), "text/csv"),
    "file2": ("image.jpg", open("image.jpg", "rb"), "image/jpeg"),
})

response = await client.post(
    "/upload-multiple",
    data=encoder.stream(),
    headers={"Content-Type": encoder.content_type},
)`}</CodeBlock>
      </section>

      {/* Retry Strategies */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Retry Strategies</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Automatic retries with exponential backoff for transient failures:
        </p>
        <CodeBlock language="python" filename="retry.py">{`from aquilia.http import HTTPClient, RetryConfig

client = HTTPClient(HTTPClientConfig(
    retry=RetryConfig(
        max_attempts=3,          # Retry up to 3 times
        backoff_factor=2.0,      # Exponential backoff: 1s, 2s, 4s
        backoff_max=30.0,        # Cap backoff at 30s
        retry_on_status={408, 429, 500, 502, 503, 504},  # Which status codes
        retry_on_faults={
            "CONNECTION_FAILED",
            "READ_TIMEOUT",
            "WRITE_TIMEOUT",
        },
    ),
))

# Retries happen automatically
response = await client.get("https://unreliable-api.com/data")
# If it fails with 503, waits 1s and retries
# If it fails again, waits 2s and retries
# If it fails a third time, raises RetryExhaustedFault

# Custom retry logic
from aquilia.http.retry import RetryStrategy

class CustomRetry(RetryStrategy):
    async def should_retry(
        self,
        attempt: int,
        fault: HTTPClientFault | None,
        response: HTTPResponse | None,
    ) -> bool:
        # Custom logic for when to retry
        if attempt >= self.max_attempts:
            return False
        
        if response and response.status_code == 429:
            # Always retry rate limits
            return True
        
        if isinstance(fault, ConnectionFault):
            # Retry connection errors
            return True
        
        return False
    
    async def get_backoff_delay(self, attempt: int) -> float:
        # Custom backoff: 0.5s, 1s, 2s, 4s...
        return 0.5 * (2 ** attempt)

client = HTTPClient(retry_strategy=CustomRetry(max_attempts=5))`}</CodeBlock>
      </section>

      {/* Interceptors */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Interceptors</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Hooks that execute before requests and after responses:
        </p>
        <CodeBlock language="python" filename="interceptors.py">{`from aquilia.http import HTTPInterceptor, HTTPRequest, HTTPResponse

# Logging interceptor
class LoggingInterceptor(HTTPInterceptor):
    async def before_request(self, request: HTTPRequest) -> HTTPRequest:
        print(f"→ {request.method} {request.url}")
        return request
    
    async def after_response(self, response: HTTPResponse) -> HTTPResponse:
        print(f"← {response.status_code} {response.url}")
        return response

# Authentication interceptor
class BearerAuthInterceptor(HTTPInterceptor):
    def __init__(self, token: str):
        self.token = token
    
    async def before_request(self, request: HTTPRequest) -> HTTPRequest:
        request.headers["Authorization"] = f"Bearer {self.token}"
        return request

# Rate limiting interceptor
class RateLimitInterceptor(HTTPInterceptor):
    def __init__(self, requests_per_second: float):
        self.rate = requests_per_second
        self.last_request = 0.0
    
    async def before_request(self, request: HTTPRequest) -> HTTPRequest:
        now = time.time()
        elapsed = now - self.last_request
        min_interval = 1.0 / self.rate
        
        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)
        
        self.last_request = time.time()
        return request

# Add interceptors to client
client = HTTPClient(interceptors=[
    LoggingInterceptor(),
    BearerAuthInterceptor("your-token"),
    RateLimitInterceptor(10.0),  # 10 req/s
])

# All requests go through interceptors
response = await client.get("/api/data")`}</CodeBlock>
      </section>

      {/* Request/Response Modification */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Request/Response Modification</h2>
        <CodeBlock language="python" filename="modification.py">{`# Add custom headers
class HeaderInterceptor(HTTPInterceptor):
    async def before_request(self, request: HTTPRequest) -> HTTPRequest:
        request.headers["X-Request-ID"] = str(uuid.uuid4())
        request.headers["X-Client-Version"] = "1.0.0"
        return request

# Modify request body
class EncryptionInterceptor(HTTPInterceptor):
    async def before_request(self, request: HTTPRequest) -> HTTPRequest:
        if request.body:
            encrypted = encrypt(request.body)
            request.body = encrypted
            request.headers["X-Encrypted"] = "true"
        return request

# Transform response
class JSONWrapperInterceptor(HTTPInterceptor):
    async def after_response(self, response: HTTPResponse) -> HTTPResponse:
        # Wrap all JSON responses in {"data": ...}
        if "application/json" in response.headers.get("Content-Type", ""):
            original = await response.json()
            response._json_data = {"data": original, "meta": {"version": "1.0"}}
        return response

# Cache responses
class CacheInterceptor(HTTPInterceptor):
    def __init__(self):
        self.cache = {}
    
    async def before_request(self, request: HTTPRequest) -> HTTPRequest:
        cache_key = f"{request.method}:{request.url}"
        if cache_key in self.cache:
            # Return cached response (implementation detail)
            raise CacheHitException(self.cache[cache_key])
        return request
    
    async def after_response(self, response: HTTPResponse) -> HTTPResponse:
        if response.status_code == 200:
            cache_key = f"{response.request.method}:{response.url}"
            self.cache[cache_key] = response
        return response`}</CodeBlock>
      </section>

      {/* Middleware */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Middleware</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Middleware wraps the entire request/response cycle:
        </p>
        <CodeBlock language="python" filename="middleware.py">{`from aquilia.http import HTTPMiddleware, HTTPRequest, HTTPResponse
from typing import Callable, Awaitable

# Timing middleware
class TimingMiddleware(HTTPMiddleware):
    async def __call__(
        self,
        request: HTTPRequest,
        next: Callable[[HTTPRequest], Awaitable[HTTPResponse]],
    ) -> HTTPResponse:
        start = time.time()
        
        try:
            response = await next(request)
            elapsed = time.time() - start
            response.elapsed = elapsed
            print(f"Request took {elapsed:.3f}s")
            return response
        
        except Exception as e:
            elapsed = time.time() - start
            print(f"Request failed after {elapsed:.3f}s: {e}")
            raise

# Error handling middleware
class ErrorHandlerMiddleware(HTTPMiddleware):
    async def __call__(self, request, next):
        try:
            return await next(request)
        
        except HTTPStatusFault as e:
            if e.status_code == 401:
                # Refresh token and retry
                await self.refresh_auth_token()
                request.headers["Authorization"] = f"Bearer {self.token}"
                return await next(request)
            raise
        
        except ConnectionFault:
            # Log and re-raise
            logger.error(f"Connection failed for {request.url}")
            raise

# Circuit breaker middleware
class CircuitBreakerMiddleware(HTTPMiddleware):
    def __init__(self, failure_threshold: int = 5):
        self.failures = 0
        self.threshold = failure_threshold
        self.state = "closed"  # closed | open | half-open
        self.last_failure_time = 0
    
    async def __call__(self, request, next):
        if self.state == "open":
            # Check if we should try again
            if time.time() - self.last_failure_time > 60:
                self.state = "half-open"
            else:
                raise CircuitOpenFault("Circuit breaker is open")
        
        try:
            response = await next(request)
            
            if self.state == "half-open":
                # Success, close the circuit
                self.state = "closed"
                self.failures = 0
            
            return response
        
        except HTTPClientFault:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.threshold:
                self.state = "open"
            
            raise

# Add middleware
client = HTTPClient(middleware=[
    TimingMiddleware(),
    ErrorHandlerMiddleware(),
    CircuitBreakerMiddleware(),
])`}</CodeBlock>
      </section>

      {/* Concurrency */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Concurrent Requests</h2>
        <CodeBlock language="python" filename="concurrency.py">{`import asyncio

client = HTTPClient()

# Parallel requests with asyncio.gather
urls = [
    "https://api.example.com/users/1",
    "https://api.example.com/users/2",
    "https://api.example.com/users/3",
]

responses = await asyncio.gather(*[
    client.get(url) for url in urls
])

# Process responses
for response in responses:
    data = await response.json()
    print(data)

# Limit concurrency with semaphore
semaphore = asyncio.Semaphore(5)  # Max 5 concurrent

async def fetch(url: str):
    async with semaphore:
        return await client.get(url)

tasks = [fetch(url) for url in range(100)]
responses = await asyncio.gather(*tasks)

# TaskGroup (Python 3.11+)
async with asyncio.TaskGroup() as group:
    tasks = [
        group.create_task(client.get(f"/api/data/{i}"))
        for i in range(10)
    ]

# All tasks complete or all fail

# Sequential requests with results
results = []
for i in range(10):
    response = await client.get(f"/api/item/{i}")
    data = await response.json()
    results.append(data)
    
    # Process incrementally
    process_data(data)

# Timeout for group of requests
try:
    responses = await asyncio.wait_for(
        asyncio.gather(*[client.get(url) for url in urls]),
        timeout=10.0,
    )
except asyncio.TimeoutError:
    print("Batch request timed out")`}</CodeBlock>
      </section>

      {/* Custom Headers & User-Agent */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Custom Headers & User-Agent</h2>
        <CodeBlock language="python" filename="custom_headers.py">{`# Set default User-Agent
client = HTTPClient(HTTPClientConfig(
    default_headers={
        "User-Agent": "MyApp/1.0 (https://example.com)",
    }
))

# Override per request
response = await client.get(
    "/api/data",
    headers={"User-Agent": "CustomBot/2.0"},
)

# Common header patterns
headers = {
    # Authentication
    "Authorization": "Bearer token123",
    "X-API-Key": "secret-key",
    
    # Content negotiation
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    
    # CORS
    "Origin": "https://example.com",
    "Referer": "https://example.com/page",
    
    # Custom
    "X-Request-ID": str(uuid.uuid4()),
    "X-Correlation-ID": "abc-123",
    "X-Client-Version": "1.2.3",
}

response = await client.get("/api/data", headers=headers)`}</CodeBlock>
      </section>

      {/* Redirects */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Redirect Handling</h2>
        <CodeBlock language="python" filename="redirects.py">{`# Follow redirects automatically (default)
client = HTTPClient(HTTPClientConfig(
    follow_redirects=True,
    max_redirects=10,
))

response = await client.get("https://example.com/redirect")
# Follows 301, 302, 303, 307, 308 redirects
print(response.url)  # Final URL after redirects

# Disable redirects
client = HTTPClient(HTTPClientConfig(follow_redirects=False))

response = await client.get("https://example.com/redirect")
print(response.status_code)  # 301 or 302
print(response.headers["Location"])  # Redirect target

# Manual redirect handling
response = await client.get("/api/resource", follow_redirects=False)
if response.status_code in (301, 302, 303, 307, 308):
    redirect_url = response.headers["Location"]
    response = await client.get(redirect_url)

# Too many redirects
try:
    response = await client.get("/infinite-redirect")
except RedirectFault as e:
    print(f"Too many redirects: {e.redirect_count}")`}</CodeBlock>
      </section>

      {/* Proxy Support */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Proxy Support</h2>
        <CodeBlock language="python" filename="proxy.py">{`# HTTP proxy
client = HTTPClient(HTTPClientConfig(
    proxy="http://proxy.example.com:8080",
))

# Authenticated proxy
client = HTTPClient(HTTPClientConfig(
    proxy="http://user:pass@proxy.example.com:8080",
))

# SOCKS proxy (requires socks library)
client = HTTPClient(HTTPClientConfig(
    proxy="socks5://proxy.example.com:1080",
))

# Per-request proxy
response = await client.get(
    "https://api.example.com/data",
    proxy="http://other-proxy.com:3128",
)

# Environment variable
import os
os.environ["HTTP_PROXY"] = "http://proxy.example.com:8080"
os.environ["HTTPS_PROXY"] = "http://proxy.example.com:8080"

# Client respects environment variables
client = HTTPClient()  # Uses HTTP_PROXY/HTTPS_PROXY`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
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
