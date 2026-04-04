import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function HTTPClient() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Globe className="w-4 h-4" />
          HTTP Client / Basics
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            HTTPClient
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The HTTPClient class provides a high-level async API for making HTTP requests with built-in retry logic, interceptors, and connection pooling.
        </p>
      </div>

      {/* Basic Usage */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Basic Usage</h2>
        <CodeBlock language="python" filename="simple_request.py">{`from aquilia.http import HTTPClient

async def main():
    # Create client
    client = HTTPClient()
    
    try:
        # Make GET request
        response = await client.get("https://api.github.com/users/octocat")
        
        # Check status
        if response.is_success:
            data = await response.json()
            print(f"User: {data['login']}")
        
        # Response provides helpers
        print(f"Status: {response.status_code}")
        print(f"Headers: {response.headers}")
        print(f"Elapsed: {response.elapsed}s")
    
    finally:
        # Always close to release connections
        await client.close()

# Or use context manager
async def with_context():
    async with HTTPClient() as client:
        response = await client.get("https://httpbin.org/get")
        data = await response.json()
        return data`}</CodeBlock>
      </section>

      {/* Configuration */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Configuration</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          HTTPClient supports comprehensive configuration via <code>HTTPClientConfig</code>. All nested configs are also configurable:
        </p>
        <CodeBlock language="python" filename="config.py">{`from aquilia.http import (
    AsyncHTTPClient, HTTPClientConfig, TimeoutConfig, PoolConfig, 
    RetryConfig, ProxyConfig, TLSConfig
)

client = AsyncHTTPClient(HTTPClientConfig(
    # Base URL (prepended to all relative URLs)
    base_url="https://api.example.com",
    
    # Timeout configuration with granular control
    timeout=TimeoutConfig(
        total=30.0,       # Overall request timeout (None = no limit)
        connect=10.0,     # Connection establishment timeout
        read=20.0,        # Read timeout for response data
        write=10.0,       # Write timeout for request data
        pool=5.0,         # Pool acquisition timeout
    ),
    
    # Connection pool configuration
    pool=PoolConfig(
        max_connections=100,             # Global connection limit
        max_connections_per_host=10,     # Per-host connection limit  
        keepalive_expiry=60.0,           # Keep-alive duration (seconds)
    ),
    
    # Retry configuration with exponential backoff
    retry=RetryConfig(
        max_attempts=3,                  # Number of retry attempts
        backoff_base=1.0,                # Base delay for backoff
        backoff_multiplier=2.0,          # Exponential backoff multiplier
        backoff_max=60.0,                # Maximum backoff delay
        backoff_jitter=0.1,              # Add randomness to backoff
        retry_on_status={429, 500, 502, 503, 504},  # Retry on these status codes
        retry_on_methods={"GET", "HEAD", "OPTIONS", "PUT", "DELETE"},  # Retry these methods (idempotent)
    ),
    
    # Proxy configuration (supports environment variables)
    proxy=ProxyConfig(
        http_proxy="http://proxy.corp:8080",
        https_proxy="https://proxy.corp:8080", 
        no_proxy="localhost,127.0.0.1,*.local",
    ),
    
    # TLS/SSL configuration
    tls=TLSConfig(
        verify=True,                     # Verify SSL certificates
        cert_file="/path/to/client.crt", # Client certificate
        key_file="/path/to/client.key",  # Client private key
        ca_bundle="/path/to/ca.pem",     # Custom CA bundle
        ciphers="ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM",  # Cipher suite
    ),
    
    # Default headers for all requests
    default_headers={
        "User-Agent": "MyApp/1.0",
        "Accept": "application/json",
        "X-API-Version": "v1",
    },
    
    # Redirect handling
    follow_redirects=True,               # Follow 3xx redirects
    max_redirects=10,                    # Maximum redirect hops
    
    # Error handling
    raise_for_status=False,              # Raise HTTPStatusFault for 4xx/5xx
    
    # User agent override
    user_agent="Aquilia-HTTP/1.0 MyApp/2.1",
))`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Configuration Presets</h3>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Use factory methods for common scenarios:
        </p>
        <CodeBlock language="python" filename="presets.py">{`# Fast config for internal APIs
config = HTTPClientConfig(
    timeout=TimeoutConfig.fast(),        # total=5.0, connect=2.0
    retry=RetryConfig.no_retry(),        # max_attempts=0
)

# Slow config for external APIs
config = HTTPClientConfig(
    timeout=TimeoutConfig.slow(),        # total=60.0, connect=15.0
    retry=RetryConfig.aggressive(),      # max_attempts=5, backoff_max=30.0
)

# No timeout for long downloads
config = HTTPClientConfig(
    timeout=TimeoutConfig.no_timeout(),  # All timeouts = None
)

# Serialize/deserialize config
config_dict = config.to_dict()
restored = HTTPClientConfig.from_dict(config_dict)`}</CodeBlock>
      </section>

      {/* Request Methods */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Request Methods</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          HTTPClient provides convenience methods for all HTTP verbs:
        </p>
        <CodeBlock language="python" filename="methods.py">{`client = HTTPClient()

# GET request
response = await client.get("/users")

# POST with JSON body
response = await client.post(
    "/users",
    json={"name": "Alice", "email": "alice@example.com"}
)

# PUT with custom headers
response = await client.put(
    "/users/123",
    json={"name": "Bob"},
    headers={"Authorization": "Bearer token123"}
)

# PATCH
response = await client.patch("/users/123", json={"status": "active"})

# DELETE
response = await client.delete("/users/123")

# HEAD (no body)
response = await client.head("/health")

# OPTIONS
response = await client.options("/api")

# Generic request method
response = await client.request(
    "GET",
    "/custom",
    headers={"X-Custom": "value"},
    params={"filter": "active"},
)`}</CodeBlock>
      </section>

      {/* Request Parameters */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Request Parameters</h2>
        <div className={boxClass}>
          <h3 className={`font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>All request methods accept these parameters:</h3>
          <div className={`space-y-3 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <div>
              <code className="text-aquilia-500 font-mono">url: str</code> — Request URL (absolute or relative to base_url)
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">params: dict[str, Any] | None</code> — URL query parameters (supports arrays)
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">headers: dict[str, str] | None</code> — Request headers (merged with defaults, case-insensitive)
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">json: Any</code> — JSON body (auto-serialized with orjson/ujson/stdlib, sets Content-Type)
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">data: dict[str, Any] | str | bytes | None</code> — Form data or raw body
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">files: MultipartFormData | None</code> — Multipart file uploads with progress tracking
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">timeout: float | TimeoutConfig | None</code> — Request timeout override
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">follow_redirects: bool</code> — Follow 3xx redirects (default from config)
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">raise_for_status: bool</code> — Raise HTTPStatusFault for 4xx/5xx
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">cookies: dict[str, str] | None</code> — Request-specific cookies
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">proxy: str | None</code> — Override proxy for this request
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">verify: bool | None</code> — Override SSL verification
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">cert: tuple[str, str] | None</code> — Client cert (cert_file, key_file)
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">stream: bool</code> — Return streaming response for large payloads
            </div>
          </div>
        </div>
      </section>

      {/* Query Parameters */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Query Parameters</h2>
        <CodeBlock language="python" filename="params.py">{`# Query params as dict
response = await client.get(
    "/search",
    params={"q": "python", "page": 1, "limit": 10}
)
# Sends: GET /search?q=python&page=1&limit=10

# URL encoding handled automatically
response = await client.get(
    "/search",
    params={"q": "async programming", "tags": "python,asyncio"}
)
# Sends: GET /search?q=async+programming&tags=python%2Casyncio

# Array-like params
params = {"filter": ["active", "verified"]}
response = await client.get("/users", params=params)
# Sends: GET /users?filter=active&filter=verified`}</CodeBlock>
      </section>

      {/* Headers */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Headers</h2>
        <CodeBlock language="python" filename="headers.py">{`# Per-request headers
response = await client.get(
    "/api/data",
    headers={
        "Authorization": "Bearer token123",
        "X-Request-ID": "abc-123",
        "Accept": "application/json",
    }
)

# Headers are case-insensitive
response = await client.get(
    "/api/data",
    headers={"accept": "application/json"}  # Same as "Accept"
)

# Merge with default headers
client = HTTPClient(HTTPClientConfig(
    default_headers={"User-Agent": "MyApp/1.0"}
))
# Request headers merge with defaults
response = await client.get("/", headers={"X-Custom": "value"})
# Sends: User-Agent: MyApp/1.0, X-Custom: value`}</CodeBlock>
      </section>

      {/* JSON Requests */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>JSON Requests</h2>
        <CodeBlock language="python" filename="json_request.py">{`# JSON is auto-serialized
response = await client.post(
    "/api/users",
    json={
        "name": "Alice",
        "email": "alice@example.com",
        "metadata": {"role": "admin"}
    }
)
# Automatically sets:
# - Content-Type: application/json
# - Serializes dict to JSON string

# Complex data structures
import datetime
data = {
    "created_at": datetime.datetime.now().isoformat(),
    "tags": ["python", "async"],
    "config": {"debug": True},
}
response = await client.post("/api/records", json=data)`}</CodeBlock>
      </section>

      {/* Form Data */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Form Data</h2>
        <CodeBlock language="python" filename="form_data.py">{`# URL-encoded form
response = await client.post(
    "/login",
    data="username=alice&password=secret123",
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

# Or use dict and manual encoding
from urllib.parse import urlencode
form_data = urlencode({"username": "alice", "password": "secret123"})
response = await client.post(
    "/login",
    data=form_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)`}</CodeBlock>
      </section>

      {/* File Uploads and Multipart Forms */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>File Uploads and Multipart Forms</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Comprehensive multipart form support with progress tracking, streaming, and content type detection:
        </p>
        <CodeBlock language="python" filename="multipart.py">{`from aquilia.http import MultipartFormData
from pathlib import Path

# Using MultipartFormData builder
form = (
    MultipartFormData()
    .field("title", "My Document") 
    .field("description", "A sample file upload")
    .file("document", "report.pdf", open("report.pdf", "rb"))
    .file_from_path("image", Path("chart.png"))
    .file_from_bytes("config", "config.json", b'{"debug": true}', "application/json")
)

response = await client.post("/upload", files=form)

# Or use the convenience method for POST
response = await client.post(
    "/upload",
    files=form,
    headers={"Authorization": "Bearer token123"}
)

# Progress tracking with callbacks
async def progress_callback(progress):
    print(f"Uploaded: {progress.bytes_transferred} / {progress.total_bytes} "
          f"({progress.percentage:.1f}%) at {progress.bytes_per_second:.0f} B/s")
    if progress.eta_seconds:
        print(f"ETA: {progress.eta_seconds:.1f}s")

# Streaming upload for large files
from aquilia.http.streaming import StreamingBody
stream = StreamingBody(
    Path("large_file.zip"),
    chunk_size=65536,
    on_progress=progress_callback
)

form = MultipartFormData().file("upload", "large_file.zip", stream)
response = await client.post("/upload", files=form)

# Content-Type auto-detection
form = MultipartFormData()
form.file_from_path("image", "photo.jpg")  # Auto-detects: image/jpeg
form.file_from_path("doc", "report.pdf")   # Auto-detects: application/pdf
form.file("data", "data.json", b'{}')      # Manual: application/json

# Calculate total size if possible
total_size = form.content_length()  # Returns int or None
if total_size:
    print(f"Form size: {total_size} bytes")`}</CodeBlock>
      </section>

      {/* Authentication */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Authentication</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Built-in support for 6 authentication schemes. All auth types are interceptors that automatically add credentials:
        </p>
        
        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Basic Authentication (RFC 7617)</h3>
        <CodeBlock language="python" filename="basic_auth.py">{`from aquilia.http import BasicAuth

auth = BasicAuth("username", "password")
client = AsyncHTTPClient(interceptors=[auth])

# Or per-request
response = await client.get("/protected", auth=("user", "pass"))`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Bearer Token Authentication</h3>
        <CodeBlock language="python" filename="bearer_auth.py">{`from aquilia.http import BearerAuth

# Static token
auth = BearerAuth("your-jwt-token")

# Dynamic token with callback
async def get_token():
    # Fetch fresh token from auth service
    response = await auth_client.post("/oauth/token", ...)
    return (await response.json())["access_token"]

auth = BearerAuth(get_token)  # Calls function for each request
client = AsyncHTTPClient(interceptors=[auth])`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>API Key Authentication</h3>
        <CodeBlock language="python" filename="apikey_auth.py">{`from aquilia.http import APIKeyAuth

# Header-based API key
auth = APIKeyAuth("X-API-Key", "your-api-key", location="header")

# Query parameter API key  
auth = APIKeyAuth("api_key", "your-api-key", location="query")

client = AsyncHTTPClient(interceptors=[auth])`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Digest Authentication (RFC 7616)</h3>
        <CodeBlock language="python" filename="digest_auth.py">{`from aquilia.http import DigestAuth

# Automatic challenge-response flow
auth = DigestAuth("username", "password")
client = AsyncHTTPClient(interceptors=[auth])

# Client handles: 401 challenge → calculate digest → retry with credentials`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>OAuth2 Authentication</h3>
        <CodeBlock language="python" filename="oauth2_auth.py">{`from aquilia.http import OAuth2Auth

auth = OAuth2Auth(
    client_id="your-client-id",
    client_secret="your-client-secret", 
    token_url="https://auth.provider.com/oauth/token",
    initial_token="current-access-token",  # Optional
    scope="read write",                    # Optional
)

# Automatically:
# - Refreshes expired tokens
# - Retries 401 responses with new token
# - Handles token exchange flow
client = AsyncHTTPClient(interceptors=[auth])`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>AWS Signature V4 Authentication</h3>
        <CodeBlock language="python" filename="aws_auth.py">{`from aquilia.http import AWSSignatureV4Auth

auth = AWSSignatureV4Auth(
    access_key="AKIAIOSFODNN7EXAMPLE",
    secret_key="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
    region="us-east-1",
    service="s3"  # s3, lambda, dynamodb, etc.
)

# Signs all requests with AWS Signature Version 4
client = AsyncHTTPClient(interceptors=[auth])
response = await client.get("https://mybucket.s3.amazonaws.com/myfile.txt")`}</CodeBlock>
      </section>

      {/* Streaming */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Streaming Requests and Responses</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Stream large payloads without loading into memory. Supports progress tracking and backpressure handling:
        </p>
        
        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Streaming Response Data</h3>
        <CodeBlock language="python" filename="stream_response.py">{`# Stream response in chunks
response = await client.get("https://example.com/large-file.zip")

async for chunk in response.iter_bytes(chunk_size=8192):
    # Process chunk without loading full response
    process_chunk(chunk)

# Stream response as text lines
response = await client.get("https://api.example.com/logs")
async for line in response.iter_lines():
    parse_log_line(line)

# Stream response as text with encoding
response = await client.get("https://example.com/data.csv")
async for chunk in response.iter_text(chunk_size=4096, encoding="utf-8"):
    parse_csv_chunk(chunk)`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Streaming Request Bodies</h3>
        <CodeBlock language="python" filename="stream_request.py">{`from aquilia.http.streaming import StreamingBody
import asyncio

# Stream file upload
stream = StreamingBody(
    Path("large-video.mp4"),
    chunk_size=65536,
    on_progress=progress_callback
)

response = await client.put("/upload/video", data=stream)

# Stream from async generator
async def generate_data():
    for i in range(1000):
        yield f"chunk-{i}\\n".encode()
        await asyncio.sleep(0.001)  # Simulate processing

stream = StreamingBody(generate_data(), chunk_size=1024)
response = await client.post("/stream-data", data=stream)

# Stream with size limit
from aquilia.http.streaming import stream_with_limit

limited = stream_with_limit(large_stream, max_bytes=10_000_000)  # 10MB limit
response = await client.post("/limited-upload", data=limited)`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Convenience Streaming Method</h3>
        <CodeBlock language="python" filename="stream_method.py">{`# High-level streaming interface
async for chunk in client.stream("GET", "https://example.com/large-data"):
    handle_chunk(chunk)

# Stream with parameters
async for chunk in client.stream(
    "POST", 
    "/api/stream",
    json={"query": "large-dataset"},
    chunk_size=32768
):
    process_stream_chunk(chunk)`}</CodeBlock>
      </section>

      {/* Response Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Response Handling</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          HTTPClientResponse provides comprehensive access to response data, status, headers, and metadata:
        </p>
        
        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Status and Metadata</h3>
        <CodeBlock language="python" filename="response_status.py">{`response = await client.get("/api/users")

# Status code and reason
print(response.status_code)    # 200, 404, 500, etc.
print(response.reason)         # "OK", "Not Found", "Internal Server Error"

# Status check properties
print(response.is_success)      # True for 2xx
print(response.is_error)        # True for 4xx or 5xx  
print(response.is_client_error) # True for 4xx
print(response.is_server_error) # True for 5xx
print(response.is_redirect)     # True for 3xx

# Request metadata
print(response.url)            # Final URL (after redirects)
print(response.method)         # "GET", "POST", etc.
print(response.http_version)   # "1.1"
print(response.elapsed)        # Request duration in seconds

# Redirect history (if any)
if response.history:
    for redirect in response.history:
        print(f"Redirected from: {redirect.url} ({redirect.status_code})")

# Request/response size
print(f"Request size: {response.request_size} bytes")
print(f"Response size: {response.content_length} bytes")`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Headers</h3>
        <CodeBlock language="python" filename="response_headers.py">{`# Headers are case-insensitive MultiDict
headers = response.headers

# Access headers
content_type = headers["Content-Type"]          # Case-insensitive
server = headers.get("Server", "Unknown")       # With default
cache_control = headers.get("cache-control")    # Any case works

# Multiple headers with same name (e.g., Set-Cookie)
cookies = headers.get_all("Set-Cookie")  # Returns list
if cookies:
    for cookie in cookies:
        print(f"Cookie: {cookie}")

# Iterate all headers
for name, value in headers.items():
    print(f"{name}: {value}")

# Common headers
encoding = response.encoding              # Charset from Content-Type
location = response.location              # Redirect location (if 3xx)
content_length = response.content_length  # Content-Length header`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Body Parsing</h3>
        <CodeBlock language="python" filename="response_body.py">{`# JSON parsing (uses orjson > ujson > stdlib)
data = await response.json()

# Text with automatic encoding detection
text = await response.text()                    # Auto-detect charset
text = await response.text(encoding="utf-8")    # Force encoding

# Raw bytes
raw_data = await response.content()

# Check if body is available
if response.has_body:
    data = await response.json()

# Streaming access
async for chunk in response.iter_bytes(chunk_size=8192):
    process_chunk(chunk)

async for line in response.iter_lines():
    process_line(line)

async for text_chunk in response.iter_text(chunk_size=4096):
    process_text(text_chunk)`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Cookie Extraction</h3>
        <CodeBlock language="python" filename="response_cookies.py">{`# Extract cookies from response  
cookies = response.extract_cookies()
for cookie in cookies:
    print(f"Name: {cookie.name}")
    print(f"Value: {cookie.value}")
    print(f"Domain: {cookie.domain}")
    print(f"Path: {cookie.path}")
    print(f"Expires: {cookie.expires}")
    print(f"Secure: {cookie.secure}")
    print(f"HttpOnly: {cookie.http_only}")
    print(f"SameSite: {cookie.same_site}")

# Cookies are automatically stored in session's CookieJar
# and sent with subsequent requests to matching domains/paths`}</CodeBlock>

        <h3 className={`text-lg font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Error Handling</h3>
        <CodeBlock language="python" filename="response_errors.py">{`# Manual status checking
if response.status_code >= 400:
    print(f"HTTP Error: {response.status_code}")
    error_body = await response.text()
    print(f"Error details: {error_body}")

# Automatic raising for error status
response.raise_for_status()  # Raises HTTPStatusFault for 4xx/5xx

# Use config to auto-raise  
client = AsyncHTTPClient(HTTPClientConfig(raise_for_status=True))
# All responses automatically raise for error status

# JSON parsing with error handling
try:
    data = await response.json()
except ValueError as e:
    # Invalid JSON
    print(f"JSON parse error: {e}")
    text = await response.text()
    print(f"Raw response: {text}")`}</CodeBlock>
      </section>

      {/* Error Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Error Handling</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          All HTTP client errors are structured Aquilia faults:
        </p>
        <CodeBlock language="python" filename="error_handling.py">{`from aquilia.http.faults import (
    ConnectionFault,
    TimeoutFault,
    TLSFault,
    HTTPStatusFault,
)

try:
    response = await client.get("https://api.example.com/data")
    response.raise_for_status()
    return await response.json()

except ConnectionFault as e:
    # Network connection failed
    print(f"Connection error: {e.message}")
    print(f"Host: {e.metadata['host']}")
    print(f"Port: {e.metadata['port']}")

except TimeoutFault as e:
    # Request timed out
    print(f"Timeout after {e.metadata['timeout']}s")

except TLSFault as e:
    # SSL/TLS error (cert verification, handshake failure)
    print(f"TLS error: {e.reason}")

except HTTPStatusFault as e:
    # Non-2xx status code
    print(f"HTTP {e.status_code}: {e.message}")
    if e.status_code == 404:
        print("Resource not found")
    elif e.status_code >= 500:
        print("Server error")`}</CodeBlock>
      </section>

      {/* Fault Hierarchy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Hierarchy</h2>
        <div className={boxClass}>
          <div className={`font-mono text-sm space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <p className="text-aquilia-500 font-bold">HTTPClientFault (base)</p>
            <p className="ml-4">├─ <span className="text-aquilia-500">ConnectionFault</span> — Network connection errors</p>
            <p className="ml-4">├─ <span className="text-aquilia-500">TimeoutFault</span> — Request/connection timeouts</p>
            <p className="ml-8">│  ├─ ConnectTimeoutFault — Connection phase timeout</p>
            <p className="ml-8">│  ├─ ReadTimeoutFault — Read phase timeout</p>
            <p className="ml-8">│  └─ WriteTimeoutFault — Write phase timeout</p>
            <p className="ml-4">├─ <span className="text-aquilia-500">TLSFault</span> — SSL/TLS errors</p>
            <p className="ml-8">│  └─ CertificateVerifyFault — Certificate validation failed</p>
            <p className="ml-4">├─ <span className="text-aquilia-500">HTTPStatusFault</span> — Non-2xx status codes</p>
            <p className="ml-8">│  ├─ ClientErrorFault (4xx)</p>
            <p className="ml-8">│  └─ ServerErrorFault (5xx)</p>
            <p className="ml-4">├─ <span className="text-aquilia-500">RetryExhaustedFault</span> — All retries failed</p>
            <p className="ml-4">├─ <span className="text-aquilia-500">RedirectFault</span> — Too many redirects</p>
            <p className="ml-4">└─ <span className="text-aquilia-500">TransportFault</span> — Generic transport error</p>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/http" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/http/sessions" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          Sessions <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}
