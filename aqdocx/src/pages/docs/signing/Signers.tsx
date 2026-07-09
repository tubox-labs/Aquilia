import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, ShieldCheck } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SigningSigners() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const textMuted = isDark ? 'text-gray-400' : 'text-gray-600'
  const borderMuted = isDark ? 'border-white/5' : 'border-gray-100'

  return (
    <div className="max-w-4xl mx-auto py-6 font-sans">
      {/* Header */}
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-mono mb-4">
          <ShieldCheck className="w-4 h-4" />
          <span>SIGNING SYSTEM / CORE SIGNERS</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Core Signer Classes
        </h1>
        <p className={`text-lg leading-relaxed font-light ${textMuted}`}>
          Discover the primary APIs for cryptographic signing: the stateless Signer class and the time-aware TimestampSigner.
        </p>
      </div>

      {/* Signer API */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Signer API Reference</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            The <DocTerm id="signing.Signer">Signer</DocTerm> class verifies simple string values. The output signature is appended as a Base64 block separated by a specified character (default <code className="text-white">:</code>).
          </p>
        </div>

        <CodeBlock language="python" filename="signer_class.py" compact showLineNumbers={false}>{`class Signer:
    def __init__(self, secret: str | bytes | None = None, *, salt: str = "aquilia.signing", sep: str = ":", algorithm: str = "HS256", backend: SignerBackend | None = None)
    
    def sign(self, value: str) -> str:
        """Sign value and return '<value>:<signature>'."""
        
    def unsign(self, signed_value: str) -> str:
        """Verify signature and return original value. Raises BadSignature on mismatch."""
        
    def sign_bytes(self, data: bytes) -> bytes:
        """Sign binary blobs and return raw data + separator + signature."""
        
    def unsign_bytes(self, signed_data: bytes) -> bytes:
        """Verify binary signature and return original bytes."""
        
    def sign_object(self, obj: Any) -> str:
        """Serialise a JSON-compatible Python object, sign, and encode."""
        
    def unsign_object(self, token: str) -> Any:
        """Verify signature and deserialise the JSON payload."""`}</CodeBlock>
      </section>

      {/* TimestampSigner API */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">TimestampSigner API Reference</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            The <DocTerm id="signing.TimestampSigner">TimestampSigner</DocTerm> class embeds a UTC timestamp in microsecond precision (offset from 2020-01-01) inside the payload before signing. This enables enforcing token lifetimes at verification time.
          </p>
        </div>

        <CodeBlock language="python" filename="timestamp_signer_class.py" compact showLineNumbers={false}>{`class TimestampSigner(Signer):
    def __init__(self, secret: str | bytes | None = None, *, salt: str = "aquilia.signing.ts", sep: str = ":", algorithm: str = "HS256", backend: SignerBackend | None = None)
    
    def sign(self, value: str, *, timestamp: datetime | None = None) -> str:
        """Sign value with an embedded timestamp."""
        
    def unsign(self, signed_value: str, max_age: float | int | timedelta | None = None) -> str:
        """Verify signature and enforce age. Raises SignatureExpired if older than max_age."""
        
    def unsign_with_timestamp(self, signed_value: str, max_age: float | int | timedelta | None = None) -> tuple[str, datetime]:
        """Verify signature and return tuple of (original_value, datetime_when_signed)."""`}</CodeBlock>
      </section>

      {/* Walkthrough Scenarios */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-8">Scenario Walkthroughs</h2>
        
        <div className="space-y-16">
          {/* Scenario 1 */}
          <div>
            <h3 className={`text-lg font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scenario 1: Basic String Verification</h3>
            <p className={`font-light leading-relaxed ${textMuted} mb-6`}>
              Verify stateless data elements passed in query parameters or custom HTTP headers:
            </p>
            <CodeBlock language="python" filename="string_signing.py" highlightLines={[6, 9, 14]}>{`from aquilia.signing import Signer, BadSignature

# 1. Initialize signer with a master key
signer = Signer(secret="my-super-secret-key-32-bytes-minimum")

# 2. Sign a username string
signed_token = signer.sign("john_doe")
print(signed_token)  # e.g. "john_doe:aBcDeFgHiJ..."

# 3. Verify signature on read
try:
    username = signer.unsign(signed_token)
except BadSignature:
    print("Tampered token detected!")`}</CodeBlock>
          </div>

          {/* Scenario 2 */}
          <div>
            <h3 className={`text-lg font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scenario 2: Binary Blob Integrity</h3>
            <p className={`font-light leading-relaxed ${textMuted} mb-6`}>
              Maintain serialization integrity of binary objects, e.g. signed pickle payloads or encrypted files:
            </p>
            <CodeBlock language="python" filename="binary_signing.py" highlightLines={[8, 12]}>{`import pickle
from aquilia.signing import Signer

signer = Signer(secret="my-super-secret-key-32-bytes-minimum")

data = {"file_id": 10842, "checksum": "a90f1"}
pickle_data = pickle.dumps(data)

# Sign binary bytes
signed_payload = signer.sign_bytes(pickle_data)

# Unsign binary bytes and deserialize
original_bytes = signer.unsign_bytes(signed_payload)
restored_data = pickle.loads(original_bytes)`}</CodeBlock>
          </div>

          {/* Scenario 3 */}
          <div>
            <h3 className={`text-lg font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scenario 3: Expirable Tokens</h3>
            <p className={`font-light leading-relaxed ${textMuted} mb-6`}>
              Enforce age validation on cryptographic signatures, automatically discarding tokens older than a set duration:
            </p>
            <CodeBlock language="python" filename="expirable_signing.py" highlightLines={[8, 11, 16]}>{`import time
from aquilia.signing import TimestampSigner, SignatureExpired, BadSignature

ts = TimestampSigner(secret="my-super-secret-key-32-bytes-minimum")

# Sign token (embeds current time)
token = ts.sign("premium_user")

# Sleep to simulate delay
time.sleep(5)

# Verify with max_age restriction (3 seconds)
try:
    user = ts.unsign(token, max_age=3)
except SignatureExpired as exc:
    print(f"Token expired! Signed at: {exc.date_signed}")
except BadSignature:
    print("Invalid signature!")`}</CodeBlock>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/signing/overview" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Overview
        </Link>
        <Link to="/docs/signing/specialized" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Specialized Signers <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
