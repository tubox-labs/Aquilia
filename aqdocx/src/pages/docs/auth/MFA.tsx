import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Fingerprint, KeyRound, Smartphone, ShieldCheck, QrCode } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function AuthMFA() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const boxClass = `p-6 rounded-2xl border ${isDark ? 'bg-[#0A0A0A] border-white/10' : 'bg-white border-gray-200'}`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4"><Fingerprint className="w-4 h-4" />Security &amp; Auth</div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Multi-Factor Authentication
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          AquilAuth provides a complete MFA system with <code className="text-aquilia-500">TOTPProvider</code> (Google Authenticator compatible), <code className="text-aquilia-500">WebAuthnProvider</code> (FIDO2 / passkeys), backup recovery codes, and a unified <code className="text-aquilia-500">MFAManager</code>.
        </p>
      </div>

      {/* MFA Types */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Supported Methods</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {[
            { icon: <Smartphone className="w-5 h-5" />, title: 'TOTP', desc: 'Time-based One-Time Passwords (RFC 6238). Compatible with Google Authenticator, Authy, 1Password. 6-digit codes, 30-second period.', color: '#3b82f6' },
            { icon: <KeyRound className="w-5 h-5" />, title: 'WebAuthn / FIDO2', desc: 'Hardware security keys, biometrics, and passkeys. Cross-platform authenticator support. ES256 and RS256 public keys.', color: '#22c55e' },
            { icon: <ShieldCheck className="w-5 h-5" />, title: 'Backup Codes', desc: 'One-time recovery codes (format: XXXX-XXXX-XXXX). SHA-256 hashed before storage. 10 codes generated per enrollment.', color: '#f59e0b' },
            { icon: <QrCode className="w-5 h-5" />, title: 'SMS / Email OTP', desc: 'MFACredential supports sms and email types via phone_number and email fields. Requires external delivery provider.', color: '#8b5cf6' },
          ].map((m, i) => (
            <div key={i} className={boxClass}>
              <div className="flex items-center gap-2 mb-2" style={{ color: m.color }}>{m.icon}<span className="font-semibold">{m.title}</span></div>
              <p className={`text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{m.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* MFACredential */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>MFACredential Model</h2>
        <CodeBlock language="python" filename="MFACredential">{`from aquilia.auth.core import MFACredential, CredentialStatus

cred = MFACredential(
    identity_id="user_42",
    mfa_type="totp",                   # totp | webauthn | sms | email
    mfa_secret="JBSWY3DPEHPK3PXP",    # Base32 TOTP secret
    backup_codes=["hash1", "hash2"],   # SHA-256 hashed backup codes
    webauthn_credentials=[],           # FIDO2 public key objects
    phone_number=None,                 # For SMS OTP
    email=None,                        # For email OTP
    status=CredentialStatus.ACTIVE,
)

# Helpers
cred.is_verified()            # True if verified_at is set
cred.touch()                  # Update last_used_at

# Generate secrets
MFACredential.generate_totp_secret()    # 20-byte base32 string
MFACredential.generate_backup_codes(10) # ["A1B2-C3D4", ...]`}</CodeBlock>
      </section>

      {/* TOTP Provider */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Smartphone className="w-5 h-5 text-aquilia-500" />TOTP Provider</h2>
        <CodeBlock language="python" filename="TOTPProvider">{`from aquilia.auth.mfa import TOTPProvider

totp = TOTPProvider(
    issuer="Aquilia",     # Shown in authenticator app
    digits=6,             # Code length (default 6)
    period=30,            # Seconds per code (default 30)
    algorithm="SHA1",     # SHA1 | SHA256 | SHA512
)

# 1. Generate secret for user enrollment
secret = totp.generate_secret()
# "JBSWY3DPEHPK3PXP..." (base32, 20-byte random)

# 2. Generate QR code URI
uri = totp.generate_provisioning_uri(
    secret=secret,
    account_name="alice@example.com",
)
# "otpauth://totp/Aquilia:alice@example.com?secret=...&issuer=Aquilia&algorithm=SHA1&digits=6&period=30"
# → Render as QR code for the user to scan

# 3. Generate code (for testing)
code = totp.generate_code(secret)
# "482917" (6-digit code valid for 30 seconds)

# 4. Verify user-submitted code
is_valid = totp.verify_code(
    secret=secret,
    code="482917",
    window=1,          # ±1 period tolerance (clock drift)
)
# True — constant-time comparison via secrets.compare_digest`}</CodeBlock>
      </section>

      {/* Backup Codes */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Backup Recovery Codes</h2>
        <CodeBlock language="python" filename="Backup Codes">{`# Generate 10 backup codes (format: XXXX-XXXX-XXXX)
codes = totp.generate_backup_codes(count=10)
# ["A1B2-C3D4-E5F6", "1234-ABCD-5678", ...]

# Hash for storage (never store plain codes)
hashes = [TOTPProvider.hash_backup_code(c) for c in codes]
# SHA-256 hashes

# Verify a backup code
is_valid = TOTPProvider.verify_backup_code(
    code="A1B2-C3D4-E5F6",
    code_hash=hashes[0],
)
# True — constant-time comparison

# Show codes ONCE to user, store only hashes
# When used, remove the hash from the list`}</CodeBlock>
      </section>

      {/* WebAuthn */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><KeyRound className="w-5 h-5 text-aquilia-500" />WebAuthn / FIDO2</h2>
        <CodeBlock language="python" filename="WebAuthnProvider">{`from aquilia.auth.mfa import WebAuthnProvider

webauthn = WebAuthnProvider(
    rp_id="myapp.com",                  # Relying Party ID (domain)
    rp_name="My Application",           # Display name
    origin="https://myapp.com",         # Expected origin
)

# Registration Flow
# 1. Generate registration options (send to browser)
options = webauthn.generate_registration_options(
    user_id="user_42",
    user_name="alice@example.com",
    user_display_name="Alice",
)
# Returns publicKey options for navigator.credentials.create()
# Includes challenge, rp info, user info, supported algorithms (ES256, RS256)

# 2. Verify registration response (from browser)
credential_data = webauthn.verify_registration_response(
    response=browser_response,
    expected_challenge=options["_challenge"],
)
# Returns: {"credential_id": "...", "public_key": "...", "sign_count": 0}
# → Store in MFACredential.webauthn_credentials

# Authentication Flow
# 1. Generate authentication options
auth_options = webauthn.generate_authentication_options(
    credential_ids=["stored_credential_id"],  # optional allowList
)

# 2. Verify authentication response
is_valid = webauthn.verify_authentication_response(
    response=browser_response,
    expected_challenge=auth_options["_challenge"],
    stored_credential=credential_data,
)
# Checks: credential_id match, sign_count increment (anti-cloning)`}</CodeBlock>
      </section>

      {/* MFA Manager */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>MFAManager</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500">MFAManager</code> coordinates all MFA providers and handles the enrollment/verification workflow.
        </p>
        <CodeBlock language="python" filename="MFAManager">{`from aquilia.auth.mfa import MFAManager, TOTPProvider, WebAuthnProvider

mfa = MFAManager(
    totp_provider=TOTPProvider(issuer="MyApp"),
    webauthn_provider=WebAuthnProvider(
        rp_id="myapp.com",
        rp_name="My App",
        origin="https://myapp.com",
    ),
)

# Enroll user in TOTP
enrollment = await mfa.enroll_totp(
    user_id="user_42",
    account_name="alice@example.com",
)
# {
#   "secret": "JBSWY3DPEHPK3PXP...",
#   "provisioning_uri": "otpauth://totp/...",
#   "backup_codes": ["A1B2-C3D4-E5F6", ...],    # Show ONCE
#   "backup_code_hashes": ["sha256...", ...],     # Store these
# }

# Verify TOTP code
is_valid = await mfa.verify_totp(
    secret=enrollment["secret"],
    code="482917",
)

# Verify and consume backup code
is_valid, remaining_hashes = await mfa.verify_backup_code(
    code="A1B2-C3D4-E5F6",
    backup_code_hashes=enrollment["backup_code_hashes"],
)
# If valid, used hash is removed from remaining_hashes
# → Update stored backup_code_hashes with remaining_hashes`}</CodeBlock>
      </section>

      {/* MFA + Auth Flow */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>MFA + Password Authentication</h2>
        <p className={`mb-4 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          When MFA is enrolled, <code className="text-aquilia-500">AuthManager.authenticate_password()</code> raises <code className="text-red-400">AUTH_MFA_REQUIRED</code> instead of returning tokens. Your application handles the two-step flow:
        </p>
        <CodeBlock language="python" filename="Two-Step Login">{`from aquilia.auth import AuthManager, AUTH_MFA_REQUIRED

try:
    result = await auth.authenticate_password(
        username="alice@example.com",
        password="SuperSecret!23",
    )
    # If no MFA enrolled → tokens returned directly
except AUTH_MFA_REQUIRED as e:
    # MFA enrolled — need second factor
    identity_id = e.metadata["identity_id"]
    methods = e.metadata["available_methods"]  # ["totp", "webauthn"]
    
    # Client submits MFA code
    mfa_valid = await mfa.verify_totp(secret=stored_secret, code=user_code)
    
    if mfa_valid:
        # Issue tokens manually after MFA verification
        access_token = await token_manager.issue_access_token(
            identity_id=identity_id,
            scopes=["profile"],
            roles=["admin"],
        )
        refresh_token = await token_manager.issue_refresh_token(
            identity_id=identity_id,
            scopes=["profile"],
        )
        
        # Mark session as MFA-verified
        from aquilia.auth.integration.aquila_sessions import set_mfa_verified
        set_mfa_verified(session)`}</CodeBlock>
      </section>

      {/* MFA Faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>MFA Faults</h2>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead><tr className={`border-b ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
              <th className="text-left py-3 pr-4 text-aquilia-500">Fault</th>
              <th className="text-left py-3 pr-4 text-aquilia-500">Code</th>
              <th className="text-left py-3 text-aquilia-500">Description</th>
            </tr></thead>
            <tbody className="divide-y divide-white/5">
              {[
                ['AUTH_MFA_REQUIRED', 'AUTH_005', 'MFA enrolled — second factor needed (retryable)'],
                ['AUTH_MFA_INVALID', 'AUTH_006', 'Invalid TOTP code or WebAuthn assertion (retryable)'],
                ['AUTH_MFA_NOT_ENROLLED', 'AUTH_401', 'No MFA method set up for identity'],
                ['AUTH_MFA_ALREADY_ENROLLED', 'AUTH_402', 'MFA type already enrolled'],
                ['AUTH_WEBAUTHN_INVALID', 'AUTH_403', 'WebAuthn credential verification failed (retryable)'],
                ['AUTH_BACKUP_CODE_INVALID', 'AUTH_404', 'Invalid backup recovery code (retryable)'],
                ['AUTH_BACKUP_CODE_EXHAUSTED', 'AUTH_405', 'All backup codes consumed'],
              ].map(([f, c, d], i) => (
                <tr key={i}>
                  <td className="py-2 pr-4 font-mono text-xs text-red-400">{f}</td>
                  <td className="py-2 pr-4 font-mono text-xs text-gray-500">{c}</td>
                  <td className={`py-2 ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <NextSteps />
    </div>
  )
}
