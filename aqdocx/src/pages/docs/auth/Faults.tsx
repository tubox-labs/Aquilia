import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { AlertTriangle, ShieldAlert, Lock, RefreshCw, Globe, Fingerprint, Users } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function AuthFaults() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="max-w-4xl mx-auto space-y-16">
      {/* Header Section */}
      <div className="space-y-4">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium tracking-wide">
          <AlertTriangle className="w-4 h-4" />
          <span>Security &amp; Auth</span>
        </div>
        <h1 className={`text-4xl font-extrabold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="gradient-text font-mono relative group inline-block">
            Auth Faults Reference
            <span className="absolute -bottom-1 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia auth uses structured <code className="text-aquilia-500 font-mono text-sm">Fault</code> objects for all error conditions. Each fault carries a domain, code, severity, public-safe message, and retryable flag — enabling consistent error handling across your application.
        </p>
      </div>

      {/* Fault Anatomy */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Fault Structure
        </h2>
        <CodeBlock language="python" filename="Fault Anatomy">{`from aquilia.auth.faults import (
    Fault,               # base class
    raise_auth_fault,    # raise helper
    is_auth_fault,       # type check helper
)

# Every auth fault provides:
class Fault:
    domain: str           # e.g. "auth"
    code: str             # e.g. "AUTH_001"
    severity: str         # "critical" | "error" | "warning"
    message: str          # internal message (log-safe)
    public_message: str   # user-facing message
    retryable: bool       # can the client retry?
    status_code: int      # HTTP status code (401, 403, etc.)
`}</CodeBlock>
      </section>

      {/* Authentication Faults */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Lock className="w-6 h-6 text-red-500" />
          <span>Authentication Faults</span>
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className={`border-b ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/6">Code</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/4">Name</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-2/5">Description</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/12">Status</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-1/12 text-center">Retry</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/10 dark:divide-zinc-800/50">
              {[
                ['AUTH_001', 'InvalidCredentials', 'Password or API key verification failed', '401', '✓'],
                ['AUTH_002', 'IdentityNotFound', 'No identity matches the provided identifier', '401', '✗'],
                ['AUTH_003', 'IdentitySuspended', 'Account has been suspended by an administrator', '403', '✗'],
                ['AUTH_004', 'IdentityDeleted', 'Account has been soft-deleted', '403', '✗'],
                ['AUTH_005', 'IdentityPending', 'Account has not yet been activated', '403', '✗'],
                ['AUTH_006', 'AccountLocked', 'Too many failed attempts — rate limiter lockout', '429', '✓'],
                ['AUTH_007', 'TokenExpired', 'Access or refresh token has expired', '401', '✓'],
                ['AUTH_008', 'TokenInvalid', 'Token signature verification or decode failed', '401', '✗'],
                ['AUTH_009', 'TokenRevoked', 'Token has been explicitly revoked', '401', '✗'],
                ['AUTH_010', 'RefreshTokenRequired', 'Refresh token missing from request', '400', '✗'],
                ['AUTH_011', 'RefreshTokenExpired', 'Refresh token past its TTL', '401', '✓'],
                ['AUTH_012', 'RefreshTokenReuse', 'Refresh token reuse detected — possible theft', '401', '✗'],
                ['AUTH_013', 'AuthenticationRequired', 'No credentials provided for protected route', '401', '✗'],
                ['AUTH_014', 'UnsupportedAuthMethod', 'Auth method not configured or not supported', '400', '✗'],
                ['AUTH_015', 'PasswordRotationRequired', 'Password hash needs rehashing with new params', '403', '✓'],
              ].map((r, i) => (
                <tr key={i} className="hover:bg-aquilia-500/2 transition-colors duration-200">
                  <td className="py-3 font-mono text-xs font-bold text-red-500/90">{r[0]}</td>
                  <td className="py-3 font-mono text-xs font-semibold text-aquilia-500">{r[1]}</td>
                  <td className={`py-3 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{r[2]}</td>
                  <td className="py-3 font-mono text-xs text-zinc-400">{r[3]}</td>
                  <td className={`py-3 text-xs font-bold text-center ${r[4] === '✓' ? 'text-green-500' : 'text-zinc-500/40'}`}>{r[4]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Authorization Faults */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <ShieldAlert className="w-6 h-6 text-amber-500" />
          <span>Authorization Faults</span>
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className={`border-b ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/6">Code</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/4">Name</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-2/5">Description</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/12">Status</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-1/12 text-center">Retry</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/10 dark:divide-zinc-800/50">
              {[
                ['AUTHZ_001', 'InsufficientScope', 'Token lacks the required scope(s)', '403', '✗'],
                ['AUTHZ_002', 'InsufficientRole', 'Identity does not hold the required role(s)', '403', '✗'],
                ['AUTHZ_003', 'PermissionDenied', 'RBAC/ABAC policy denied access', '403', '✗'],
                ['AUTHZ_004', 'TenantMismatch', 'Request targets a resource in a different tenant', '403', '✗'],
                ['AUTHZ_005', 'PolicyEvaluationFailed', 'Policy engine encountered an error during eval', '500', '✓'],
              ].map((r, i) => (
                <tr key={i} className="hover:bg-aquilia-500/2 transition-colors duration-200">
                  <td className="py-3 font-mono text-xs font-bold text-amber-500/90">{r[0]}</td>
                  <td className="py-3 font-mono text-xs font-semibold text-aquilia-500">{r[1]}</td>
                  <td className={`py-3 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{r[2]}</td>
                  <td className={`py-3 font-mono text-xs ${r[3] === '500' ? 'text-red-500 font-bold' : 'text-zinc-400'}`}>{r[3]}</td>
                  <td className={`py-3 text-xs font-bold text-center ${r[4] === '✓' ? 'text-green-500' : 'text-zinc-500/40'}`}>{r[4]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Credential Faults */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <RefreshCw className="w-6 h-6 text-blue-500" />
          <span>Credential Faults</span>
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className={`border-b ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/6">Code</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/4">Name</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-2/5">Description</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/12">Status</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-1/12 text-center">Retry</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/10 dark:divide-zinc-800/50">
              {[
                ['AUTH_101', 'PasswordTooWeak', 'Password fails PasswordPolicy validation', '400', '✓'],
                ['AUTH_102', 'PasswordBreached', 'Password found in HIBP breach database', '400', '✓'],
                ['AUTH_103', 'ApiKeyExpired', 'API key has exceeded its expires_at', '401', '✗'],
                ['AUTH_104', 'ApiKeyRevoked', 'API key has been revoked by owner/admin', '401', '✗'],
                ['AUTH_105', 'ApiKeyInvalidScope', 'API key lacks scopes for this operation', '403', '✗'],
              ].map((r, i) => (
                <tr key={i} className="hover:bg-aquilia-500/2 transition-colors duration-200">
                  <td className="py-3 font-mono text-xs font-bold text-blue-500/90">{r[0]}</td>
                  <td className="py-3 font-mono text-xs font-semibold text-aquilia-500">{r[1]}</td>
                  <td className={`py-3 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{r[2]}</td>
                  <td className="py-3 font-mono text-xs text-zinc-400">{r[3]}</td>
                  <td className={`py-3 text-xs font-bold text-center ${r[4] === '✓' ? 'text-green-500' : 'text-zinc-500/40'}`}>{r[4]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Session Faults */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Users className="w-6 h-6 text-purple-500" />
          <span>Session Faults</span>
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className={`border-b ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/6">Code</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/4">Name</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-2/5">Description</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/12">Status</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-1/12 text-center">Retry</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/10 dark:divide-zinc-800/50">
              {[
                ['AUTH_201', 'SessionNotFound', 'Session ID does not exist in the store', '401', '✗'],
                ['AUTH_202', 'SessionExpired', 'Session has exceeded its TTL', '401', '✓'],
                ['AUTH_203', 'SessionLimitExceeded', 'User has exceeded the max concurrent sessions', '429', '✓'],
              ].map((r, i) => (
                <tr key={i} className="hover:bg-aquilia-500/2 transition-colors duration-200">
                  <td className="py-3 font-mono text-xs font-bold text-purple-500/90">{r[0]}</td>
                  <td className="py-3 font-mono text-xs font-semibold text-aquilia-500">{r[1]}</td>
                  <td className={`py-3 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{r[2]}</td>
                  <td className="py-3 font-mono text-xs text-zinc-400">{r[3]}</td>
                  <td className={`py-3 text-xs font-bold text-center ${r[4] === '✓' ? 'text-green-500' : 'text-zinc-500/40'}`}>{r[4]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* OAuth Faults */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Globe className="w-6 h-6 text-cyan-500" />
          <span>OAuth Faults</span>
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className={`border-b ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/6">Code</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/4">Name</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-2/5">Description</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/12">Status</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-1/12 text-center">Retry</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/10 dark:divide-zinc-800/50">
              {[
                ['AUTH_301', 'OAuthClientNotFound', 'Client ID not registered in the store', '400', '✗'],
                ['AUTH_302', 'OAuthTargetInvalid', 'Auth code is expired, consumed, or invalid', '400', '✗'],
                ['AUTH_303', 'OAuthPKCEFailed', 'PKCE code_verifier does not match code_challenge', '400', '✗'],
                ['AUTH_304', 'OAuthRedirectMismatch', 'redirect_uri does not match registered URIs', '400', '✗'],
              ].map((r, i) => (
                <tr key={i} className="hover:bg-aquilia-500/2 transition-colors duration-200">
                  <td className="py-3 font-mono text-xs font-bold text-cyan-500/90">{r[0]}</td>
                  <td className="py-3 font-mono text-xs font-semibold text-aquilia-500">{r[1]}</td>
                  <td className={`py-3 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{r[2]}</td>
                  <td className="py-3 font-mono text-xs text-zinc-400">{r[3]}</td>
                  <td className={`py-3 text-xs font-bold text-center ${r[4] === '✓' ? 'text-green-500' : 'text-zinc-500/40'}`}>{r[4]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* MFA Faults */}
      <section className="space-y-6">
        <h2 className={`text-2.5xl font-bold tracking-tight flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <Fingerprint className="w-6 h-6 text-emerald-500" />
          <span>MFA Faults</span>
        </h2>
        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className={`border-b ${isDark ? 'border-zinc-800' : 'border-zinc-200'}`}>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/6">Code</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/4">Name</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-2/5">Description</th>
                <th className="py-3 font-semibold text-aquilia-500 font-mono text-xs w-1/12">Status</th>
                <th className="py-3 font-semibold text-aquilia-500 text-xs w-1/12 text-center">Retry</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/10 dark:divide-zinc-800/50">
              {[
                ['AUTH_401', 'MFARequired', 'MFA verification needed to complete auth', '403', '✓'],
                ['AUTH_402', 'MFAInvalidCode', 'TOTP code is incorrect or outside time window', '401', '✓'],
                ['AUTH_403', 'MFANotEnrolled', 'Identity has no MFA credential of this type', '400', '✗'],
                ['AUTH_404', 'MFABackupExhausted', 'All backup codes have been consumed', '401', '✗'],
                ['AUTH_405', 'MFAAlreadyEnrolled', 'Identity already has this MFA type enrolled', '409', '✗'],
              ].map((r, i) => (
                <tr key={i} className="hover:bg-aquilia-500/2 transition-colors duration-200">
                  <td className="py-3 font-mono text-xs font-bold text-emerald-500/90">{r[0]}</td>
                  <td className="py-3 font-mono text-xs font-semibold text-aquilia-500">{r[1]}</td>
                  <td className={`py-3 text-xs ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>{r[2]}</td>
                  <td className="py-3 font-mono text-xs text-zinc-400">{r[3]}</td>
                  <td className={`py-3 text-xs font-bold text-center ${r[4] === '✓' ? 'text-green-500' : 'text-zinc-500/40'}`}>{r[4]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Handling Faults */}
      <section className="space-y-4">
        <h2 className={`text-2.5xl font-bold tracking-tight ${isDark ? 'text-white' : 'text-gray-900'}`}>
          Handling Auth Faults
        </h2>
        <CodeBlock language="python" filename="Error Handling">{`from aquilia.auth.faults import is_auth_fault, Fault

# In your route handler
async def login(request):
    try:
        result = await auth_manager.authenticate_password(
            identifier="alice@example.com",
            password=request.body["password"],
        )
        return json({"token": result.tokens["access_token"]})
    except Fault as fault:
        # Generic auth fault response — always use public_message
        return json({
            "error": fault.public_message,
            "code": fault.code,
            "retryable": fault.retryable,
        }, status=fault.status_code)
`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
