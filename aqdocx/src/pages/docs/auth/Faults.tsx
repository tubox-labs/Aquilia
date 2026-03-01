import { useTheme } from '../../../context/ThemeContext'
import { CodeBlock } from '../../../components/CodeBlock'
import { AlertTriangle, ShieldAlert, Lock, RefreshCw, Globe, Fingerprint, Users } from 'lucide-react'
import { NextSteps } from '../../../components/NextSteps'

export function AuthFaults() {
  const { theme } = useTheme()
  const isDark = theme === 'dark'
  const cellClass = `px-4 py-2 text-sm ${isDark ? 'text-gray-300 border-white/5' : 'text-gray-700 border-gray-100'} border-b`
  const headClass = `px-4 py-2 text-xs font-semibold uppercase tracking-wider ${isDark ? 'text-gray-400 border-white/10' : 'text-gray-500 border-gray-200'} border-b text-left`

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-12">
        <div className="flex items-center gap-2 text-sm text-aquilia-500 font-medium mb-4"><AlertTriangle className="w-4 h-4" />Security &amp; Auth</div>
        <h1 className={`text-4xl ${isDark ? 'text-white' : 'text-gray-900'}`}>
          <span className="font-bold tracking-tighter gradient-text font-mono relative group inline-block">
            Auth Faults Reference
            <span className="absolute -bottom-0.5 left-0 w-0 h-0.5 bg-gradient-to-r from-aquilia-500 to-aquilia-400 group-hover:w-full transition-all duration-300" />
          </span>
        </h1>
        <p className={`text-lg leading-relaxed ${isDark ? 'text-gray-400' : 'text-gray-600'}`}>
          Aquilia auth uses structured <code className="text-aquilia-500">Fault</code> objects for all error conditions. Each fault carries a domain, code, severity, public-safe message, and retryable flag — enabling consistent error handling across your application.
        </p>
      </div>

      {/* Fault Anatomy */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Fault Structure</h2>
        <CodeBlock language="python" filename="Fault Anatomy">{`from aquilia.auth.faults import (
    Fault,               # base class
    raise_auth_fault,    # raise helper
    is_auth_fault,       # type check helper
)

# Every auth fault provides:
class Fault:
    domain: str           # e.g. "auth", "authz"
    code: str             # e.g. "AUTH_001"
    severity: str         # "critical", "error", "warning"
    message: str          # internal message (log-safe)
    public_message: str   # user-facing message (never leaks internals)
    retryable: bool       # can the client retry?
    status_code: int      # HTTP status code (401, 403, etc.)

# Raise a fault with optional context
raise_auth_fault("AUTH_001", context={"identity_id": "user_42"})

# Check if an exception is an auth fault
if is_auth_fault(exc):
    log.warning(f"{exc.code}: {exc.message}")`}</CodeBlock>
      </section>

      {/* Authentication Faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Lock className="w-5 h-5 text-red-500" />Authentication Faults</h2>
        <div className={`rounded-2xl border overflow-x-auto ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full">
            <thead className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
              <tr><th className={headClass}>Code</th><th className={headClass}>Name</th><th className={headClass}>Description</th><th className={headClass}>Status</th><th className={headClass}>Retry</th></tr>
            </thead>
            <tbody>
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
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className={cellClass}><code className="text-red-400 font-mono text-xs">{r[0]}</code></td>
                  <td className={cellClass}><code className="text-aquilia-500 text-xs">{r[1]}</code></td>
                  <td className={cellClass}>{r[2]}</td>
                  <td className={cellClass}><code className="text-xs">{r[3]}</code></td>
                  <td className={cellClass + ' text-center'}>{r[4]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Authorization Faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><ShieldAlert className="w-5 h-5 text-amber-500" />Authorization Faults</h2>
        <div className={`rounded-2xl border overflow-x-auto ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full">
            <thead className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
              <tr><th className={headClass}>Code</th><th className={headClass}>Name</th><th className={headClass}>Description</th><th className={headClass}>Status</th><th className={headClass}>Retry</th></tr>
            </thead>
            <tbody>
              {[
                ['AUTHZ_001', 'InsufficientScope', 'Token lacks the required scope(s)', '403', '✗'],
                ['AUTHZ_002', 'InsufficientRole', 'Identity does not hold the required role(s)', '403', '✗'],
                ['AUTHZ_003', 'PermissionDenied', 'RBAC/ABAC policy denied access', '403', '✗'],
                ['AUTHZ_004', 'TenantMismatch', 'Request targets a resource in a different tenant', '403', '✗'],
                ['AUTHZ_005', 'PolicyEvaluationFailed', 'Policy engine encountered an error during eval', '500', '✓'],
              ].map((r, i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className={cellClass}><code className="text-amber-400 font-mono text-xs">{r[0]}</code></td>
                  <td className={cellClass}><code className="text-aquilia-500 text-xs">{r[1]}</code></td>
                  <td className={cellClass}>{r[2]}</td>
                  <td className={cellClass}><code className="text-xs">{r[3]}</code></td>
                  <td className={cellClass + ' text-center'}>{r[4]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Credential Faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><RefreshCw className="w-5 h-5 text-blue-500" />Credential Faults</h2>
        <div className={`rounded-2xl border overflow-x-auto ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full">
            <thead className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
              <tr><th className={headClass}>Code</th><th className={headClass}>Name</th><th className={headClass}>Description</th><th className={headClass}>Status</th><th className={headClass}>Retry</th></tr>
            </thead>
            <tbody>
              {[
                ['AUTH_101', 'PasswordTooWeak', 'Password fails PasswordPolicy validation', '400', '✓'],
                ['AUTH_102', 'PasswordBreached', 'Password found in HIBP breach database', '400', '✓'],
                ['AUTH_103', 'ApiKeyExpired', 'API key has exceeded its expires_at', '401', '✗'],
                ['AUTH_104', 'ApiKeyRevoked', 'API key has been revoked by owner/admin', '401', '✗'],
                ['AUTH_105', 'ApiKeyInvalidScope', 'API key lacks scopes for this operation', '403', '✗'],
              ].map((r, i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className={cellClass}><code className="text-blue-400 font-mono text-xs">{r[0]}</code></td>
                  <td className={cellClass}><code className="text-aquilia-500 text-xs">{r[1]}</code></td>
                  <td className={cellClass}>{r[2]}</td>
                  <td className={cellClass}><code className="text-xs">{r[3]}</code></td>
                  <td className={cellClass + ' text-center'}>{r[4]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Session Faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Users className="w-5 h-5 text-purple-500" />Session Faults</h2>
        <div className={`rounded-2xl border overflow-x-auto ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full">
            <thead className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
              <tr><th className={headClass}>Code</th><th className={headClass}>Name</th><th className={headClass}>Description</th><th className={headClass}>Status</th><th className={headClass}>Retry</th></tr>
            </thead>
            <tbody>
              {[
                ['AUTH_201', 'SessionNotFound', 'Session ID does not exist in the store', '401', '✗'],
                ['AUTH_202', 'SessionExpired', 'Session has exceeded its TTL', '401', '✓'],
                ['AUTH_203', 'SessionLimitExceeded', 'User has exceeded the max concurrent sessions', '429', '✓'],
              ].map((r, i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className={cellClass}><code className="text-purple-400 font-mono text-xs">{r[0]}</code></td>
                  <td className={cellClass}><code className="text-aquilia-500 text-xs">{r[1]}</code></td>
                  <td className={cellClass}>{r[2]}</td>
                  <td className={cellClass}><code className="text-xs">{r[3]}</code></td>
                  <td className={cellClass + ' text-center'}>{r[4]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* OAuth Faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Globe className="w-5 h-5 text-cyan-500" />OAuth Faults</h2>
        <div className={`rounded-2xl border overflow-x-auto ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full">
            <thead className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
              <tr><th className={headClass}>Code</th><th className={headClass}>Name</th><th className={headClass}>Description</th><th className={headClass}>Status</th><th className={headClass}>Retry</th></tr>
            </thead>
            <tbody>
              {[
                ['AUTH_301', 'OAuthClientNotFound', 'Client ID not registered in the store', '400', '✗'],
                ['AUTH_302', 'OAuthInvalidGrant', 'Auth code is expired, consumed, or invalid', '400', '✗'],
                ['AUTH_303', 'OAuthPKCEFailed', 'PKCE code_verifier does not match code_challenge', '400', '✗'],
                ['AUTH_304', 'OAuthRedirectMismatch', 'redirect_uri does not match registered URIs', '400', '✗'],
              ].map((r, i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className={cellClass}><code className="text-cyan-400 font-mono text-xs">{r[0]}</code></td>
                  <td className={cellClass}><code className="text-aquilia-500 text-xs">{r[1]}</code></td>
                  <td className={cellClass}>{r[2]}</td>
                  <td className={cellClass}><code className="text-xs">{r[3]}</code></td>
                  <td className={cellClass + ' text-center'}>{r[4]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* MFA Faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 flex items-center gap-2 ${isDark ? 'text-white' : 'text-gray-900'}`}><Fingerprint className="w-5 h-5 text-emerald-500" />MFA Faults</h2>
        <div className={`rounded-2xl border overflow-x-auto ${isDark ? 'border-white/10' : 'border-gray-200'}`}>
          <table className="w-full">
            <thead className={isDark ? 'bg-white/5' : 'bg-gray-50'}>
              <tr><th className={headClass}>Code</th><th className={headClass}>Name</th><th className={headClass}>Description</th><th className={headClass}>Status</th><th className={headClass}>Retry</th></tr>
            </thead>
            <tbody>
              {[
                ['AUTH_401', 'MFARequired', 'MFA verification needed to complete auth', '403', '✓'],
                ['AUTH_402', 'MFAInvalidCode', 'TOTP code is incorrect or outside time window', '401', '✓'],
                ['AUTH_403', 'MFANotEnrolled', 'Identity has no MFA credential of this type', '400', '✗'],
                ['AUTH_404', 'MFABackupExhausted', 'All backup codes have been consumed', '401', '✗'],
                ['AUTH_405', 'MFAAlreadyEnrolled', 'Identity already has this MFA type enrolled', '409', '✗'],
              ].map((r, i) => (
                <tr key={i} className={isDark ? 'hover:bg-white/5' : 'hover:bg-gray-50'}>
                  <td className={cellClass}><code className="text-emerald-400 font-mono text-xs">{r[0]}</code></td>
                  <td className={cellClass}><code className="text-aquilia-500 text-xs">{r[1]}</code></td>
                  <td className={cellClass}>{r[2]}</td>
                  <td className={cellClass}><code className="text-xs">{r[3]}</code></td>
                  <td className={cellClass + ' text-center'}>{r[4]}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Handling Faults */}
      <section className="mb-16">
        <h2 className={`text-2xl font-bold mb-6 ${isDark ? 'text-white' : 'text-gray-900'}`}>Handling Auth Faults</h2>
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
        if fault.code == "AUTH_006":
            remaining = rate_limiter.get_remaining_attempts(fault.context.get("identity_id", ""))
            return json({
                "error": fault.public_message,
                "retry_after": 60,
            }, status=fault.status_code)
        # Generic auth fault response — always use public_message
        return json({
            "error": fault.public_message,
            "code": fault.code,
            "retryable": fault.retryable,
        }, status=fault.status_code)

# In middleware — global fault handler
async def auth_fault_middleware(request, handler):
    try:
        return await handler(request)
    except Fault as fault:
        if is_auth_fault(fault):
            logger.warning(f"Auth fault {fault.code}: {fault.message}")
            return json({
                "error": fault.public_message,
                "code": fault.code,
            }, status=fault.status_code)
        raise`}</CodeBlock>
      </section>

      <NextSteps />
    </div>
  )
}
