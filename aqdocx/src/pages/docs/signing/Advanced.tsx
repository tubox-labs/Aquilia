import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { DocTerm } from '../../../components/docPreview/DocTerm'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, ShieldCheck } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SigningAdvanced() {
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
          <span>SIGNING SYSTEM / ADVANCED SIGNING</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Advanced Cryptographic Patterns
        </h1>
        <p className={`text-lg leading-relaxed font-light ${textMuted}`}>
          Discover transparent key rotation, compact zlib payload compression, and custom signer backends for asymmetric cryptography.
        </p>
      </div>

      {/* Key Rotation */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Key Rotation</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            When rotation keys in production, old tokens must remain valid until they naturally expire. The <DocTerm id="signing.RotatingSigner">RotatingSigner</DocTerm> class solves this: it always signs using the first secret key in the provided secrets array, but attempts verification against all configured keys in order.
          </p>
        </div>

        <CodeBlock language="python" filename="rotating_signer_class.py" compact showLineNumbers={false}>{`class RotatingSigner:
    def __init__(self, secrets: Sequence[str | bytes], *, salt: str = "aquilia.signing", sep: str = ":", algorithm: str = "HS256", timestamp: bool = False)
    
    def sign(self, value: str) -> str:
        """Signs using the current (first) secret key."""
        
    def unsign(self, signed_value: str, max_age: float | int | timedelta | None = None) -> str:
        """Tries each secret in order. Returns verified value or raises BadSignature."""`}</CodeBlock>
      </section>

      {/* Dumps / Loads */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Structured Serialization (Dumps &amp; Loads)</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            The <code className="text-white">dumps</code> and <code className="text-white">loads</code> helper functions serialize dictionaries and objects to URL-safe strings. If <code className="text-white">compress=True</code> is set, the engine compresses the payload via <code className="text-white">zlib</code> and adds a header byte (<code className="text-white">\x01</code>) to indicate compression.
          </p>
        </div>

        <CodeBlock language="python" filename="dumps_loads.py" compact showLineNumbers={false}>{`def dumps(obj: Any, *, secret: str | bytes | None = None, salt: str = "aquilia.signing.dumps", algorithm: str = "HS256", compress: bool = False, max_age: float | int | timedelta | None = None, timestamp: bool = True) -> str:
    """Serialise a JSON-compatible object to a signed URL-safe string."""

def loads(token: str, *, secret: str | bytes | None = None, salt: str = "aquilia.signing.dumps", algorithm: str = "HS256", max_age: float | int | timedelta | None = None) -> Any:
    """Verify and deserialise a token back to its original object format."""`}</CodeBlock>
      </section>

      {/* Custom Backends */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Custom Backends &amp; Asymmetric Signing</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            You can extend the signature generation mechanism by implementing the abstract <code className="text-white">SignerBackend</code> base class. This enables integration with cloud KMS, hardware security modules (HSM), or asymmetric keys.
          </p>
          <p>
            Aquilia features a built-in <code className="text-white">AsymmetricSignerBackend</code> that supports RS256, ES256, and EdDSA signatures (requires <code className="text-white">pip install cryptography</code>).
          </p>
        </div>

        <CodeBlock language="python" filename="asymmetric_backend.py" compact showLineNumbers={false}>{`class SignerBackend(ABC):
    @abstractmethod
    def sign(self, message: bytes) -> bytes: ...
    @abstractmethod
    def verify(self, message: bytes, signature: bytes) -> bool: ...
    @property
    @abstractmethod
    def algorithm(self) -> str: ...

class AsymmetricSignerBackend(SignerBackend):
    def __init__(self, algorithm: str, *, private_key_pem: str | None = None, public_key_pem: str | None = None)`}</CodeBlock>
      </section>

      {/* Walkthrough Scenarios */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-8">Scenario Walkthroughs</h2>
        
        <div className="space-y-16">
          {/* Scenario 1 */}
          <div>
            <h3 className={`text-lg font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scenario 1: Zero-Downtime Key Rotation</h3>
            <p className={`font-light leading-relaxed ${textMuted} mb-6`}>
              Retire old keys without logging users out or invalidating outstanding links:
            </p>
            <CodeBlock language="python" filename="key_rotation.py" highlightLines={[6, 9, 13]}>{`from aquilia.signing import RotatingSigner

# secrets[0] = active key for new signatures
# secrets[1:] = backup keys used for verifying old tokens
keys = ["new_master_key_2026_32_bytes_min", "old_retired_key_2025_32_bytes_min"]

signer = RotatingSigner(secrets=keys)

# New signatures use the active key
new_token = signer.sign("hello")

# Verification succeeds on old tokens signed with the old key
old_token = "hello:oldSignatureHexOrB64"
value = signer.unsign(old_token)  # returns "hello"`}</CodeBlock>
          </div>

          {/* Scenario 2 */}
          <div>
            <h3 className={`text-lg font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scenario 2: Signed Payload Serialization with Compression</h3>
            <p className={`font-light leading-relaxed ${textMuted} mb-6`}>
              Serialize complex nested lists or dictionaries, compressing them with zlib to keep cookies or URLs compact:
            </p>
            <CodeBlock language="python" filename="compressed_serialization.py" highlightLines={[12, 16]}>{`from aquilia.signing import dumps, loads

session_data = {
    "user_id": 90812,
    "roles": ["admin", "billing"],
    "permissions": ["read:all", "write:billing", "delete:logs"]
}

# Serialize, compress payload, and generate signature
token = dumps(
    session_data,
    secret="my-super-secret-key-32-bytes-minimum",
    compress=True
)

# Decode, verify, and decompress payload
data = loads(
    token,
    secret="my-super-secret-key-32-bytes-minimum",
    max_age=3600
)`}</CodeBlock>
          </div>

          {/* Scenario 3 */}
          <div>
            <h3 className={`text-lg font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scenario 3: Asymmetric Signature Verification</h3>
            <p className={`font-light leading-relaxed ${textMuted} mb-6`}>
              Utilize ES256 (ECDSA P-256) asymmetric signatures for verification, where the public key is distributed but private key is held securely on the auth server:
            </p>
            <CodeBlock language="python" filename="asymmetric_signing.py" highlightLines={[14, 18]}>{`from aquilia.signing import Signer, AsymmetricSignerBackend

private_pem = """-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQg...
-----END PRIVATE KEY-----"""

public_pem = """-----BEGIN PUBLIC KEY-----
MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAE...
-----END PUBLIC KEY-----"""

# 1. Create a backend with the ES256 algorithm
backend = AsymmetricSignerBackend(
    algorithm="ES256",
    private_key_pem=private_pem,
    public_key_pem=public_pem
)

# 2. Attach backend to the Signer
signer = Signer(backend=backend)
token = signer.sign("asymmetric_payload")`}</CodeBlock>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/signing/specialized" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Specialized Signers
        </Link>
        <Link to="/docs/faults" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Fault System <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
