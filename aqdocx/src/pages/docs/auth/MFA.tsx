import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { Fingerprint, KeyRound, Smartphone, ShieldCheck, QrCode } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'


export function AuthMFA() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-16">
      {/* Header Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium tracking-wide">
          <Fingerprint className="w-4 h-4" />
          <span>Security &amp; Auth</span>
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono relative group inline-block">
            Multi-Factor Authentication
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          AquilAuth provides a complete MFA system with <code className="text-aquilia-500 font-mono text-sm">TOTPProvider</code> (Google Authenticator compatible), <code className="text-aquilia-500 font-mono text-sm">WebAuthnProvider</code> (FIDO2 / passkeys), backup recovery codes, and a unified <code className="text-aquilia-500 font-mono text-sm">MFAManager</code>.
        </p>
      </div>

      {/* MFA Types */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Supported Methods
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
          {[
            { icon: <Smartphone className="w-5 h-5" />, title: 'TOTP', desc: 'Time-based One-Time Passwords (RFC 6238). Compatible with Google Authenticator, Authy, 1Password. 6-digit codes, 30-second period.', color: '#3b82f6' },
            { icon: <KeyRound className="w-5 h-5" />, title: 'WebAuthn / FIDO2', desc: 'Hardware security keys, biometrics, and passkeys. Cross-platform authenticator support. ES256 and RS256 public keys.', color: '#22c55e' },
            { icon: <ShieldCheck className="w-5 h-5" />, title: 'Backup Codes', desc: 'One-time recovery codes (format: XXXX-XXXX-XXXX). SHA-256 hashed before storage. 10 codes generated per enrollment.', color: '#f59e0b' },
            { icon: <QrCode className="w-5 h-5" />, title: 'SMS / Email OTP', desc: 'MFACredential supports sms and email types via phone_number and email fields. Requires external delivery provider.', color: '#8b5cf6' },
          ].map((m, i) => (
            <div key={i} className="flex gap-4 p-4 rounded-xl hover:bg-aquilia-500/5 transition-all duration-300 group">
              <div className="mt-1 p-2 rounded-lg bg-aquilia-500/10 group-hover:scale-105 transition-all" style={{ color: m.color }}>
                {m.icon}
              </div>
              <div className="space-y-1">
                <span className="font-bold text-sm font-mono block" style={{ color: m.color }}>
                  {m.title}
                </span>
                <p className={`text-xs leading-normal ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
                  {m.desc}
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* MFACredential */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          MFACredential Model
        </h2>
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
`}</CodeBlock>
      </section>

      {/* TOTP Provider */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Smartphone className="w-6 h-6 text-aquilia-500" />
          <span>TOTP Provider</span>
        </h2>
        <CodeBlock language="python" filename="TOTPProvider">{`from aquilia.auth.mfa import TOTPProvider

totp = TOTPProvider(
    issuer="Aquilia",     # Shown in authenticator app
    digits=6,             # Code length (default 6)
    period=30,            # Seconds per code (default 30)
    algorithm="SHA1",     # SHA1 | SHA256 | SHA512
)
`}</CodeBlock>
      </section>

      {/* Backup Codes */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Backup Recovery Codes
        </h2>
        <CodeBlock language="python" filename="Backup Codes">{`# Generate 10 backup codes (format: XXXX-XXXX-XXXX)
codes = totp.generate_backup_codes(count=10)
`}</CodeBlock>
      </section>

      {/* WebAuthn */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <KeyRound className="w-6 h-6 text-aquilia-500" />
          <span>WebAuthn / FIDO2</span>
        </h2>
        <CodeBlock language="python" filename="WebAuthnProvider">{`from aquilia.auth.mfa import WebAuthnProvider

webauthn = WebAuthnProvider(
    rp_id="myapp.com",                  # Relying Party ID (domain)
    rp_name="My Application",           # Display name
    origin="https://myapp.com",         # Expected origin
)
`}</CodeBlock>
      </section>

      {/* MFA Manager */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          MFAManager
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          The <code className="text-aquilia-500 font-mono text-sm">MFAManager</code> coordinates all MFA providers and handles enrollment and verification workflows.
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
`}</CodeBlock>
      </section>

      {/* MFA + Auth Flow */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          MFA + Password Authentication
        </h2>
        <p className={`text-sm leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          When MFA is enrolled, <code className="text-aquilia-500 font-mono text-xs">AuthManager.authenticate_password()</code> raises <code className="text-red-400 font-mono text-xs">AUTH_MFA_REQUIRED</code> instead of returning tokens.
        </p>
        <CodeBlock language="python" filename="Two-Step Login">{`from aquilia.auth import AuthManager, AUTH_MFA_REQUIRED

try:
    result = await auth.authenticate_password(
        username="alice@example.com",
        password="SuperSecret!23",
    )
except AUTH_MFA_REQUIRED as e:
    # MFA enrolled — verify code separately
    pass
`}</CodeBlock>
      </section>

      {/* MFA Faults */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          MFA Faults
        </h2>
        <div className="overflow-x-auto">
          <table className={`w-full text-sm text-left ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>
            <thead>
              <tr className={`border-b ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/3">Fault</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/6">Code</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-1/2">Description</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/10 dark:divide-zinc-800/50">
              {[
                ['AUTH_MFA_REQUIRED', 'AUTH_005', 'MFA enrolled — second factor needed (retryable).'],
                ['AUTH_MFA_INVALID', 'AUTH_006', 'Invalid TOTP code or WebAuthn assertion (retryable).'],
                ['AUTH_MFA_NOT_ENROLLED', 'AUTH_401', 'No MFA method set up for identity.'],
                ['AUTH_MFA_ALREADY_ENROLLED', 'AUTH_402', 'MFA type already enrolled.'],
                ['AUTH_WEBAUTHN_INVALID', 'AUTH_403', 'WebAuthn credential verification failed (retryable).'],
                ['AUTH_BACKUP_CODE_INVALID', 'AUTH_404', 'Invalid backup recovery code (retryable).'],
                ['AUTH_BACKUP_CODE_EXHAUSTED', 'AUTH_405', 'All backup codes consumed.'],
              ].map(([f, c, d], i) => (
                <tr key={i} className="hover:bg-aquilia-500/2 transition-colors duration-200">
                  <td className="py-3 font-mono text-xs text-red-500/90 font-bold">{f}</td>
                  <td className="py-3 font-mono text-xs text-gray-500">{c}</td>
                  <td className={`py-3 text-sm ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{d}</td>
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
