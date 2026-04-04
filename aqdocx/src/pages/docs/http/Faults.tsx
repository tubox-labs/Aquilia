import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function HTTPFaults() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4">
          <Globe className="w-4 h-4" />
          HTTP Client / Error Handling
        </div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Fault System
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Structured error handling with typed faults, metadata, and domain-specific error codes.
        </p>
      </div>

      {/* Fault Philosophy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Why Faults?</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia uses structured faults instead of raw exceptions for better error handling:
        </p>
        <div className={boxClass}>
          <ul className={`space-y-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Typed errors</strong> — Each fault type represents a specific failure mode</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Stable codes</strong> — Machine-readable error codes that don't change</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Rich metadata</strong> — Context about what went wrong (host, port, timeout, etc.)</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Severity levels</strong> — Error, Warning, Critical classification</li>
            <li>• <strong className={isDark ? 'text-white' : 'text-gray-900'}>Domain isolation</strong> — HTTP faults are separate from auth, storage, etc.</li>
          </ul>
        </div>
      </section>

      {/* Fault Hierarchy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Hierarchy</h2>
        <div className={boxClass}>
          <div className={`font-mono text-sm space-y-1 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <p className="text-aquilia-500 font-bold">Fault (base class for all Aquilia errors)</p>
            <p className="ml-4">└─ <span className="text-aquilia-500 font-bold">HTTPClientFault</span> (domain: HTTP_CLIENT)</p>
            <p className="ml-8">├─ <span className="text-red-500">ConnectionFault</span></p>
            <p className="ml-12">│  └─ code: CONNECTION_FAILED</p>
            <p className="ml-8">├─ <span className="text-red-500">TimeoutFault</span></p>
            <p className="ml-12">│  ├─ code: TIMEOUT</p>
            <p className="ml-12">│  ├─ ConnectTimeoutFault (CONNECT_TIMEOUT)</p>
            <p className="ml-12">│  ├─ ReadTimeoutFault (READ_TIMEOUT)</p>
            <p className="ml-12">│  └─ WriteTimeoutFault (WRITE_TIMEOUT)</p>
            <p className="ml-8">├─ <span className="text-red-500">TLSFault</span></p>
            <p className="ml-12">│  ├─ code: TLS_ERROR</p>
            <p className="ml-12">│  └─ CertificateVerifyFault (CERT_VERIFY_FAILED)</p>
            <p className="ml-8">├─ <span className="text-red-500">HTTPStatusFault</span></p>
            <p className="ml-12">│  ├─ code: HTTP_STATUS_ERROR</p>
            <p className="ml-12">│  ├─ ClientErrorFault (HTTP_CLIENT_ERROR, 4xx)</p>
            <p className="ml-12">│  └─ ServerErrorFault (HTTP_SERVER_ERROR, 5xx)</p>
            <p className="ml-8">├─ <span className="text-red-500">RetryExhaustedFault</span></p>
            <p className="ml-12">│  └─ code: RETRY_EXHAUSTED</p>
            <p className="ml-8">├─ <span className="text-red-500">RedirectFault</span></p>
            <p className="ml-12">│  └─ code: TOO_MANY_REDIRECTS</p>
            <p className="ml-8">└─ <span className="text-red-500">TransportFault</span></p>
            <p className="ml-12">   └─ code: TRANSPORT_ERROR</p>
          </div>
        </div>
      </section>

      {/* ConnectionFault */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>ConnectionFault</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Raised when TCP connection fails:
        </p>
        <CodeBlock language="python" filename="connection_fault.py">{`from aquilia.http.faults import ConnectionFault

try:
    response = await client.get("https://nonexistent-host.invalid")

except ConnectionFault as e:
    print(f"Code: {e.code}")           # CONNECTION_FAILED
    print(f"Message: {e.message}")     # "Connection failed: ..."
    print(f"Domain: {e.domain}")       # HTTP_CLIENT
    print(f"Severity: {e.severity}")   # ERROR
    
    # Metadata
    print(f"Host: {e.metadata['host']}")
    print(f"Port: {e.metadata['port']}")
    print(f"Reason: {e.metadata.get('reason')}")

# Common causes:
# - DNS resolution failed
# - Host unreachable
# - Connection refused
# - Network interface down
# - Firewall blocking connection

# Retry logic
from aquilia.http.faults import ConnectionFault

max_retries = 3
for attempt in range(max_retries):
    try:
        response = await client.get(url)
        break
    except ConnectionFault:
        if attempt == max_retries - 1:
            raise
        await asyncio.sleep(2 ** attempt)  # Exponential backoff`}</CodeBlock>
      </section>

      {/* TimeoutFault */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>TimeoutFault</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Raised when request times out:
        </p>
        <CodeBlock language="python" filename="timeout_fault.py">{`from aquilia.http.faults import (
    TimeoutFault,
    ConnectTimeoutFault,
    ReadTimeoutFault,
    WriteTimeoutFault,
)

# Generic timeout
try:
    response = await client.get("https://slow-api.com/data")
except TimeoutFault as e:
    print(f"Timeout: {e.metadata['timeout']}s")
    print(f"Phase: {e.metadata.get('phase')}")  # connect/read/write

# Specific timeout types
try:
    response = await client.get("https://slow-connect.com")
except ConnectTimeoutFault as e:
    # TCP connection took too long
    print("Connection timeout")

try:
    response = await client.get("https://slow-response.com")
except ReadTimeoutFault as e:
    # Server didn't send response in time
    print("Read timeout")

try:
    response = await client.post("https://slow-upload.com", data=large_file)
except WriteTimeoutFault as e:
    # Couldn't write request body in time
    print("Write timeout")

# Increase timeout for specific request
try:
    response = await client.get(
        "/slow-endpoint",
        timeout=TimeoutConfig(total=120.0),  # 2 minutes
    )
except TimeoutFault:
    print("Still too slow!")`}</CodeBlock>
      </section>

      {/* TLSFault */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>TLSFault</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Raised for SSL/TLS errors:
        </p>
        <CodeBlock language="python" filename="tls_fault.py">{`from aquilia.http.faults import TLSFault, CertificateVerifyFault

# General TLS error
try:
    response = await client.get("https://expired-cert.badssl.com")
except TLSFault as e:
    print(f"TLS error: {e.message}")
    print(f"Reason: {e.metadata.get('reason')}")

# Certificate verification failed
try:
    response = await client.get("https://self-signed.badssl.com")
except CertificateVerifyFault as e:
    print("Certificate verification failed")
    print(f"Reason: {e.metadata['reason']}")

# Common TLS errors:
# - Expired certificate
# - Self-signed certificate
# - Certificate hostname mismatch
# - Untrusted certificate authority
# - TLS version mismatch
# - Cipher suite mismatch

# Disable SSL verification (not recommended for production)
client = HTTPClient(HTTPClientConfig(
    verify_ssl=False,  # Skip certificate verification
))

response = await client.get("https://self-signed.badssl.com")
# No TLSFault raised (but insecure!)

# Use custom CA certificate
client = HTTPClient(HTTPClientConfig(
    ca_cert_path="/path/to/ca-cert.pem",
))`}</CodeBlock>
      </section>

      {/* HTTPStatusFault */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>HTTPStatusFault</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Raised for non-2xx status codes when using <code className="text-aquilia-500">raise_for_status()</code>:
        </p>
        <CodeBlock language="python" filename="status_fault.py">{`from aquilia.http.faults import HTTPStatusFault, ClientErrorFault, ServerErrorFault

# Raise for any error status
response = await client.get("/api/users/9999")
try:
    response.raise_for_status()
except HTTPStatusFault as e:
    print(f"Status: {e.status_code}")         # 404
    print(f"Message: {e.message}")            # "HTTP 404: Not Found"
    print(f"URL: {e.metadata['url']}")
    print(f"Method: {e.metadata['method']}")

# 4xx errors (client errors)
try:
    response = await client.get("/api/protected")
    response.raise_for_status()
except ClientErrorFault as e:
    if e.status_code == 401:
        print("Unauthorized - need to log in")
    elif e.status_code == 403:
        print("Forbidden - insufficient permissions")
    elif e.status_code == 404:
        print("Not found")
    elif e.status_code == 429:
        print("Rate limited")

# 5xx errors (server errors)
try:
    response = await client.post("/api/create")
    response.raise_for_status()
except ServerErrorFault as e:
    if e.status_code == 500:
        print("Internal server error")
    elif e.status_code == 502:
        print("Bad gateway")
    elif e.status_code == 503:
        print("Service unavailable")
    elif e.status_code == 504:
        print("Gateway timeout")

# Check status without raising
response = await client.get("/api/data")
if response.is_client_error:
    print(f"Client error: {response.status_code}")
elif response.is_server_error:
    print(f"Server error: {response.status_code}")
elif response.is_success:
    data = await response.json()`}</CodeBlock>
      </section>

      {/* RetryExhaustedFault */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>RetryExhaustedFault</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Raised when all retry attempts fail:
        </p>
        <CodeBlock language="python" filename="retry_fault.py">{`from aquilia.http.faults import RetryExhaustedFault

client = HTTPClient(HTTPClientConfig(
    retry=RetryConfig(max_attempts=3),
))

try:
    response = await client.get("https://always-fails.com/api")
except RetryExhaustedFault as e:
    print(f"Failed after {e.metadata['attempts']} attempts")
    print(f"Last error: {e.metadata['last_error']}")
    
    # Get all attempt details
    for i, attempt in enumerate(e.metadata['history']):
        print(f"Attempt {i + 1}: {attempt['error']}")
        print(f"  Backoff: {attempt['backoff']}s")

# Metadata structure:
{
    "attempts": 3,
    "last_error": "ConnectionFault: Connection failed",
    "history": [
        {"attempt": 1, "error": "...", "backoff": 1.0},
        {"attempt": 2, "error": "...", "backoff": 2.0},
        {"attempt": 3, "error": "...", "backoff": 4.0},
    ]
}`}</CodeBlock>
      </section>

      {/* RedirectFault */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>RedirectFault</h2>
        <CodeBlock language="python" filename="redirect_fault.py">{`from aquilia.http.faults import RedirectFault

try:
    response = await client.get("https://infinite-redirect.com")
except RedirectFault as e:
    print(f"Too many redirects: {e.metadata['redirect_count']}")
    print(f"Max allowed: {e.metadata['max_redirects']}")
    
    # Redirect chain
    for i, url in enumerate(e.metadata['redirect_chain']):
        print(f"{i + 1}. {url}")

# Increase redirect limit
client = HTTPClient(HTTPClientConfig(max_redirects=20))

# Or disable redirects entirely
client = HTTPClient(HTTPClientConfig(follow_redirects=False))`}</CodeBlock>
      </section>

      {/* Catching Multiple Faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Catching Multiple Faults</h2>
        <CodeBlock language="python" filename="multiple_faults.py">{`from aquilia.http.faults import (
    HTTPClientFault,
    ConnectionFault,
    TimeoutFault,
    TLSFault,
    HTTPStatusFault,
)

# Catch all HTTP client faults
try:
    response = await client.get(url)
    response.raise_for_status()
    return await response.json()

except HTTPClientFault as e:
    # Catches any HTTP client error
    print(f"HTTP error: {e.code} - {e.message}")

# Catch specific faults
try:
    response = await client.get(url)

except ConnectionFault:
    print("Network connection failed")
    # Maybe retry with different network

except TimeoutFault:
    print("Request timed out")
    # Maybe increase timeout and retry

except TLSFault:
    print("TLS/SSL error")
    # Maybe check certificate configuration

except HTTPStatusFault as e:
    if e.status_code == 429:
        # Rate limited
        retry_after = int(e.response.headers.get("Retry-After", 60))
        await asyncio.sleep(retry_after)
        # Retry request
    else:
        raise

# Catch multiple specific types
try:
    response = await client.get(url)

except (ConnectionFault, TimeoutFault) as e:
    # Network-related errors
    print(f"Network error: {e}")
    await notify_network_team(e)

except (TLSFault, HTTPStatusFault) as e:
    # Security or HTTP errors
    print(f"Application error: {e}")
    await log_to_monitoring(e)`}</CodeBlock>
      </section>

      {/* Fault Metadata */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Metadata</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          All faults include structured metadata:
        </p>
        <CodeBlock language="python" filename="metadata.py">{`from aquilia.http.faults import HTTPClientFault

try:
    response = await client.get("https://example.com/api")

except HTTPClientFault as e:
    # Standard fields
    print(f"Code: {e.code}")         # Stable error code
    print(f"Message: {e.message}")   # Human-readable description
    print(f"Domain: {e.domain}")     # HTTP_CLIENT
    print(f"Severity: {e.severity}") # ERROR, WARNING, CRITICAL
    
    # Metadata dict (varies by fault type)
    print(f"Metadata: {e.metadata}")
    
    # Common metadata fields:
    # - host: str
    # - port: int
    # - url: str
    # - method: str
    # - timeout: float
    # - reason: str
    # - status_code: int
    # - attempts: int
    
    # Original exception (if any)
    if hasattr(e, '__cause__'):
        print(f"Caused by: {e.__cause__}")

# Custom fault handling based on metadata
except ConnectionFault as e:
    host = e.metadata.get('host')
    port = e.metadata.get('port')
    
    if port == 443:
        print(f"HTTPS connection to {host} failed")
        # Try HTTP fallback?
    else:
        print(f"HTTP connection to {host}:{port} failed")

except TimeoutFault as e:
    timeout = e.metadata.get('timeout')
    print(f"Request timed out after {timeout}s")
    
    # Increase timeout for next attempt
    new_timeout = timeout * 2
    response = await client.get(url, timeout=TimeoutConfig(total=new_timeout))`}</CodeBlock>
      </section>

      {/* Logging Faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Logging & Monitoring</h2>
        <CodeBlock language="python" filename="logging.py">{`import logging
from aquilia.http.faults import HTTPClientFault

logger = logging.getLogger(__name__)

# Log all HTTP faults
try:
    response = await client.get(url)
except HTTPClientFault as e:
    logger.error(
        "HTTP request failed",
        extra={
            "fault_code": e.code,
            "fault_domain": e.domain,
            "fault_severity": e.severity.value,
            "fault_metadata": e.metadata,
            "url": url,
        },
        exc_info=True,
    )
    raise

# Structured logging
from aquilia.http.faults import HTTPClientFault
import structlog

log = structlog.get_logger()

try:
    response = await client.get(url)
except HTTPClientFault as e:
    log.error(
        "http_request_failed",
        fault_code=e.code,
        fault_message=e.message,
        fault_metadata=e.metadata,
        url=url,
    )

# Metrics/monitoring
from prometheus_client import Counter

http_errors = Counter(
    'http_client_errors_total',
    'Total HTTP client errors',
    ['fault_code', 'fault_domain'],
)

try:
    response = await client.get(url)
except HTTPClientFault as e:
    http_errors.labels(
        fault_code=e.code,
        fault_domain=e.domain,
    ).inc()
    raise`}</CodeBlock>
      </section>

      {/* Best Practices */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Best Practices</h2>
        <div className={boxClass}>
          <h3 className={`font-bold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Error Handling Guidelines:</h3>
          <ul className={`space-y-3 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
            <li>
              <strong className={isDark ? 'text-white' : 'text-gray-900'}>Catch specific faults</strong> — Handle expected errors explicitly
              <CodeBlock language="python">{`except TimeoutFault:
    # Increase timeout and retry
except ConnectionFault:
    # Check network connectivity`}</CodeBlock>
            </li>
            <li>
              <strong className={isDark ? 'text-white' : 'text-gray-900'}>Use fault metadata</strong> — Access structured error context
              <CodeBlock language="python">{`except HTTPClientFault as e:
    print(f"{e.code}: {e.message}")
    print(f"Details: {e.metadata}")`}</CodeBlock>
            </li>
            <li>
              <strong className={isDark ? 'text-white' : 'text-gray-900'}>Log before re-raising</strong> — Preserve error context
              <CodeBlock language="python">{`except HTTPClientFault as e:
    logger.error(f"Request failed: {e.code}")
    raise  # Re-raise for caller to handle`}</CodeBlock>
            </li>
            <li>
              <strong className={isDark ? 'text-white' : 'text-gray-900'}>Don't catch Fault base class</strong> — Too broad, catches all Aquilia errors
            </li>
            <li>
              <strong className={isDark ? 'text-white' : 'text-gray-900'}>Use raise_for_status() wisely</strong> — Only when you want to treat 4xx/5xx as exceptions
            </li>
          </ul>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
        <Link to="/docs/http/advanced" className={`flex items-center gap-2 text-sm ${isDark ? 'text-gray-400 hover:text-white' : 'text-gray-500 hover:text-gray-900'}`}>
          <ArrowLeft className="w-4 h-4" /> Advanced Usage
        </Link>
        <Link to="/docs/http/integration" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400">
          DI Integration <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    
      <NextSteps />
    </div>
  )
}
