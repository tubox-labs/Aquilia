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
        <CodeBlock language="python" filename="config.py">{`from aquilia.http import HTTPClient, HTTPClientConfig, TimeoutConfig, PoolConfig

client = HTTPClient(HTTPClientConfig(
    # Base URL (optional)
    base_url="https://api.example.com",
    
    # Timeout configuration
    timeout=TimeoutConfig(
        total=30.0,       # Overall request timeout
        connect=10.0,     # Connection timeout
        read=20.0,        # Read timeout
        write=10.0,       # Write timeout
    ),
    
    # Connection pool
    pool=PoolConfig(
        max_connections=100,             # Total connections
        max_connections_per_host=10,     # Per-host limit
        keepalive_expiry=60.0,           # Keep-alive duration (seconds)
    ),
    
    # Default headers
    default_headers={
        "User-Agent": "MyApp/1.0",
        "Accept": "application/json",
    },
    
    # Follow redirects (default: True, max 10)
    follow_redirects=True,
    max_redirects=10,
))`}</CodeBlock>
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
          <h3 className={`font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>All request methods accept:</h3>
          <div className={`space-y-3 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <div>
              <code className="text-aquilia-500 font-mono">url: str</code> — The request URL (absolute or relative to base_url)
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">headers: dict[str, str]</code> — Request headers (merged with defaults)
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">params: dict[str, str]</code> — URL query parameters
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">json: Any</code> — JSON body (auto-serialized, sets Content-Type)
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">data: bytes | str</code> — Raw request body
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">files: dict</code> — Multipart file uploads
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">auth: tuple[str, str]</code> — Basic auth (username, password)
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">timeout: TimeoutConfig</code> — Override default timeout
            </div>
            <div>
              <code className="text-aquilia-500 font-mono">follow_redirects: bool</code> — Follow 3xx redirects
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

      {/* File Uploads */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>File Uploads</h2>
        <CodeBlock language="python" filename="uploads.py">{`# Single file upload
with open("photo.jpg", "rb") as f:
    response = await client.post(
        "/upload",
        files={"photo": f}
    )

# Multiple files
files = {
    "photo1": open("img1.jpg", "rb"),
    "photo2": open("img2.jpg", "rb"),
}
response = await client.post("/upload", files=files)

# File with custom filename and content-type
response = await client.post(
    "/upload",
    files={
        "file": ("custom_name.pdf", open("doc.pdf", "rb"), "application/pdf")
    }
)

# Mixed multipart: files + form fields
response = await client.post(
    "/submit",
    files={"document": open("report.pdf", "rb")},
    data={"title": "Q4 Report", "author": "Alice"}
)`}</CodeBlock>
      </section>

      {/* Response Handling */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Response Handling</h2>
        <CodeBlock language="python" filename="response.py">{`response = await client.get("/api/users")

# Status checks
if response.is_success:  # 2xx
    print("Success!")
if response.is_error:    # 4xx or 5xx
    print("Error!")
if response.is_client_error:  # 4xx
    print("Client error")
if response.is_server_error:  # 5xx
    print("Server error")

# Status code
print(response.status_code)  # 200, 404, etc.

# Headers (case-insensitive)
content_type = response.headers["Content-Type"]
server = response.headers.get("Server", "Unknown")

# Parse response body
json_data = await response.json()           # Parse JSON
text = await response.text()                # Decode as UTF-8 text
raw_bytes = await response.read()          # Raw bytes
stream = response.stream()                  # Async iterator

# Metadata
print(f"Request took {response.elapsed}s")
print(f"Final URL: {response.url}")  # After redirects
print(f"HTTP version: {response.http_version}")  # "1.1"

# Auto-raise for errors
response.raise_for_status()  # Raises HTTPStatusFault if 4xx/5xx`}</CodeBlock>
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
