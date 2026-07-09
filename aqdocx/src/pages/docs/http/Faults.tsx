import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, Globe } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function HTTPFaults() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderSubtle = isDark ? 'border-white/5' : 'border-gray-100'

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
        <p className={`text-lg leading-relaxed ${textMuted}`}>
          Structured error handling with typed faults, metadata, and domain-specific error codes.
        </p>
      </div>

      {/* Why Faults? */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Why Faults?</h2>
        <p className={`mb-6 ${textMuted}`}>
          Aquilia uses structured faults instead of raw exceptions for better error handling:
        </p>
        <div className="space-y-4">
          {[
            ['Typed errors', 'Each fault type represents a specific failure mode.'],
            ['Stable codes', 'Machine-readable error codes that do not change.'],
            ['Rich metadata', 'Context about what went wrong (host, port, timeout value, etc.).'],
            ['Severity levels', 'Classification into Error, Warning, and Critical levels.'],
          ].map(([title, desc], i) => (
            <div key={i} className="border-l-2 border-aquilia-500/20 pl-4 py-1">
              <strong className={`font-mono text-sm ${isDark ? 'text-white' : 'text-gray-900'}`}>{title}</strong>
              <p className={`text-sm ${textMuted}`}>{desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Fault Hierarchy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Hierarchy</h2>
        <div className="border-l border-aquilia-500/20 pl-6 py-1">
          <div className={`font-mono text-sm space-y-2 ${textMuted}`}>
            <p className="text-aquilia-500 font-bold">Fault (base class for all Aquilia errors)</p>
            <p className="ml-4">└─ <span className="text-aquilia-500 font-bold">HTTPClientFault</span> (domain: HTTP_CLIENT)</p>
            <p className="ml-8">├─ <span className="text-aquilia-400">ConnectionFault</span> (CONNECTION_FAILED)</p>
            <p className="ml-8">├─ <span className="text-aquilia-400">TimeoutFault</span> (TIMEOUT)</p>
            <p className="ml-12">│  ├─ ConnectTimeoutFault (CONNECT_TIMEOUT)</p>
            <p className="ml-12">│  ├─ ReadTimeoutFault (READ_TIMEOUT)</p>
            <p className="ml-12">│  └─ WriteTimeoutFault (WRITE_TIMEOUT)</p>
            <p className="ml-8">├─ <span className="text-aquilia-400">TLSFault</span> (TLS_ERROR)</p>
            <p className="ml-12">│  └─ CertificateVerifyFault (CERT_VERIFY_FAILED)</p>
            <p className="ml-8">├─ <span className="text-aquilia-400">HTTPStatusFault</span> (HTTP_STATUS_ERROR)</p>
            <p className="ml-12">│  ├─ ClientErrorFault (4xx)</p>
            <p className="ml-12">│  └─ ServerErrorFault (5xx)</p>
            <p className="ml-8">├─ <span className="text-aquilia-400">RetryExhaustedFault</span> (RETRY_EXHAUSTED)</p>
            <p className="ml-8">├─ <span className="text-aquilia-400">RedirectFault</span> (TOO_MANY_REDIRECTS)</p>
            <p className="ml-8">└─ <span className="text-aquilia-400">TransportFault</span> (TRANSPORT_ERROR)</p>
          </div>
        </div>
      </section>

      {/* ConnectionFault */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>ConnectionFault</h2>
        <p className={`mb-4 ${textMuted}`}>
          Raised when a TCP socket connection fails:
        </p>
        <CodeBlock language="python" filename="connection_fault.py" highlightLines={[6, 11]}>{`from aquilia.http.faults import ConnectionFault

try:
    response = await client.get("https://nonexistent-host.invalid")
except ConnectionFault as e:
    print(f"Code: {e.code}")           # CONNECTION_FAILED
    print(f"Message: {e.message}")     # "Connection failed: ..."
    print(f"Domain: {e.domain}")       # HTTP_CLIENT
    
    # Metadata
    print(f"Host: {e.metadata['host']}")
    print(f"Port: {e.metadata['port']}")
`}</CodeBlock>
      </section>

      {/* TimeoutFault */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>TimeoutFault</h2>
        <p className={`mb-4 ${textMuted}`}>
          Raised when a network operation exceeds a defined timeout limit:
        </p>
        <CodeBlock language="python" filename="timeout_fault.py" highlightLines={[8, 14, 20]}>{`from aquilia.http.faults import (
    TimeoutFault,
    ConnectTimeoutFault,
    ReadTimeoutFault,
)

try:
    response = await client.get("https://slow-api.com")
except TimeoutFault as e:
    print(f"Timeout: {e.metadata['timeout']}s")
    print(f"Phase: {e.metadata.get('phase')}")  # connect/read/write

try:
    response = await client.get("https://slow-connect.com")
except ConnectTimeoutFault:
    print("Connection timed out")
`}</CodeBlock>
      </section>

      {/* TLSFault */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>TLSFault</h2>
        <p className={`mb-4 ${textMuted}`}>
          Raised for SSL/TLS handshaking or validation errors:
        </p>
        <CodeBlock language="python" filename="tls_fault.py" highlightLines={[4, 10]}>{`from aquilia.http.faults import TLSFault, CertificateVerifyFault

try:
    response = await client.get("https://expired-cert.badssl.com")
except TLSFault as e:
    print(f"TLS error: {e.message}")

try:
    response = await client.get("https://self-signed.badssl.com")
except CertificateVerifyFault as e:
    print("Certificate verification failed")
`}</CodeBlock>
      </section>

      {/* HTTPStatusFault */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>HTTPStatusFault</h2>
        <p className={`mb-4 ${textMuted}`}>
          Raised for non-2xx status codes when using <code className="text-aquilia-500">raise_for_status()</code>:
        </p>
        <CodeBlock language="python" filename="status_fault.py" highlightLines={[5, 13]}>{`from aquilia.http.faults import HTTPStatusFault, ClientErrorFault, ServerErrorFault

response = await client.get("/api/users/9999")
try:
    response.raise_for_status()
except HTTPStatusFault as e:
    print(f"Status: {e.status_code}")         # 404
    print(f"Message: {e.message}")            # "HTTP 404: Not Found"

try:
    response = await client.get("/api/protected")
    response.raise_for_status()
except ClientErrorFault as e:
    if e.status_code == 401:
        print("Unauthorized")
`}</CodeBlock>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderSubtle}`}>
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
