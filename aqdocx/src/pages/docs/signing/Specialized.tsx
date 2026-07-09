import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Link } from 'react-router-dom'
import { ArrowLeft, ArrowRight, ShieldCheck } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function SigningSpecialized() {
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
          <span>SIGNING SYSTEM / SPECIALIZED SIGNERS</span>
        </div>
        <h1 className={`text-4xl font-light tracking-tight mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Specialized Signers &amp; Config
        </h1>
        <p className={`text-lg leading-relaxed font-light ${textMuted}`}>
          Discover the subsystem-isolated signers and how to apply configurations globally at application startup.
        </p>
      </div>

      {/* Subsystem Signers */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">Subsystem-Specific Signers</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            To prevent cross-subsystem token confusion (e.g. using a password reset token as a session cookie), Aquilia provides specialized classes with hardcoded namespace salts:
          </p>
        </div>

        <CodeBlock language="python" filename="specialized_signers.py" compact showLineNumbers={false}>{`class SessionSigner(TimestampSigner):
    # Salt: "aquilia.sessions". Used to secure session identifier cookies.

class CSRFSigner(Signer):
    # Salt: "aquilia.csrf". Used to secure request CSRF tokens. Stateless.

class ActivationLinkSigner(TimestampSigner):
    # Salt: "aquilia.activation". Enforces a default max_age of 24 hours.

class CacheKeySigner(Signer):
    # Salt: "aquilia.cache". Used to sign cached bytes and prevent cache poisoning.

class CookieSigner(TimestampSigner):
    # Salt: "aquilia.cookies". Used for user-space signed HTTP cookies.

class APIKeySigner(TimestampSigner):
    # Salt: "aquilia.apikeys". Used to sign short-lived URL queries and access tokens.`}</CodeBlock>
      </section>

      {/* SigningConfig */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-6">SigningConfig API Reference</h2>
        <div className={`space-y-6 font-light leading-relaxed ${textMuted} mb-8`}>
          <p>
            The <code className="text-white">SigningConfig</code> dataclass defines configuration parameters mapped from the application config registry.
          </p>
        </div>

        <CodeBlock language="python" filename="signing_config.py" compact showLineNumbers={false}>{`@dataclass
class SigningConfig:
    secret: str = ""
    fallback_secrets: list[str] = field(default_factory=list)
    algorithm: str = "HS256"
    salt: str = "aquilia.signing"
    session_salt: str = "aquilia.sessions"
    csrf_salt: str = "aquilia.csrf"
    activation_salt: str = "aquilia.activation"
    cache_salt: str = "aquilia.cache"
    
    def apply(self) -> None:
        """Configures the global secret registry."""
        
    def make_session_signer(self) -> SessionSigner: ...
    def make_csrf_signer(self) -> CSRFSigner: ...
    def make_activation_signer(self) -> ActivationLinkSigner: ...
    def make_cache_signer(self) -> CacheKeySigner: ...
    def make_cookie_signer(self) -> CookieSigner: ...
    def make_api_key_signer(self) -> APIKeySigner: ...`}</CodeBlock>
      </section>

      {/* Scenarios */}
      <section className="mb-16">
        <h2 className="text-xl font-mono text-aquilia-400 uppercase tracking-wider mb-8">Scenario Walkthroughs</h2>
        
        <div className="space-y-16">
          {/* Scenario 1 */}
          <div>
            <h3 className={`text-lg font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scenario 1: Applying Global Configurations</h3>
            <p className={`font-light leading-relaxed ${textMuted} mb-6`}>
              Initialize signing configurations globally at application startup. This is typically invoked from your server entrypoint:
            </p>
            <CodeBlock language="python" filename="server_setup.py" highlightLines={[8, 12]}>{`from aquilia.signing import configure

# 1. Load keys from environment variables or settings
primary_secret = "master-secret-key-32-bytes-minimum"
old_retired_key = "retired-key-32-bytes-minimum"

# 2. Configure global signing registry
configure(
    secret=primary_secret,
    fallback_secrets=[old_retired_key],
    algorithm="HS256"
)`}</CodeBlock>
          </div>

          {/* Scenario 2 */}
          <div>
            <h3 className={`text-lg font-semibold mb-4 ${isDark ? 'text-white' : 'text-gray-900'}`}>Scenario 2: Expirable Activation / Password Reset Links</h3>
            <p className={`font-light leading-relaxed ${textMuted} mb-6`}>
              Generate signed password reset URLs. Verification enforces the default 24-hour limit:
            </p>
            <CodeBlock language="python" filename="controllers/auth.py" highlightLines={[12, 17]}>{`from aquilia.controller import Controller, GET, POST, RequestCtx
from aquilia.signing import ActivationLinkSigner, SignatureExpired, BadSignature

class ResetController(Controller):
    def initialize(self):
        self.signer = ActivationLinkSigner()

    @POST("/auth/reset-password/request")
    async def request_reset(self, ctx: RequestCtx):
        user_id = "user_984"
        # Generate token with activation-specific namespace
        token = self.signer.sign(user_id)
        reset_url = f"https://example.com/reset?token={token}"
        return {"url": reset_url}

    @GET("/auth/reset-password/verify")
    async def verify_reset(self, ctx: RequestCtx):
        token = ctx.query.get("token", "")
        try:
            # Unsigns with default 24h max_age
            user_id = self.signer.unsign(token)
            return {"user_id": user_id, "status": "valid"}
        except SignatureExpired:
            return {"error": "Token has expired"}, 400
        except BadSignature:
            return {"error": "Invalid token"}, 400`}</CodeBlock>
          </div>
        </div>
      </section>

      {/* Navigation */}
      <div className={`flex items-center justify-between pt-8 mt-12 border-t ${borderMuted}`}>
        <Link to="/docs/signing/signers" className="flex items-center gap-2 text-sm text-gray-400 hover:text-white transition-colors">
          <ArrowLeft className="w-4 h-4" /> Core Signers
        </Link>
        <Link to="/docs/signing/advanced" className="flex items-center gap-2 text-sm text-aquilia-500 font-semibold hover:text-aquilia-400 transition-colors">
          Advanced Signing <ArrowRight className="w-4 h-4" />
        </Link>
      </div>

      <NextSteps />
    </div>
  )
}
