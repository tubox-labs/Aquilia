# Session Fault Integration Audit

## Fault Architecture

All session errors flow through the `aquilia.faults` system. The base class
`SessionFault` extends `Fault` with `FaultDomain.SECURITY`.

## Complete Fault Catalog

| Fault Class | Code | Severity | Public | Retryable | Context Fields |
|---|---|---|---|---|---|
| `SessionExpiredFault` | SESSION_EXPIRED | WARN | ✅ | ❌ | session_id_hash, expires_at |
| `SessionIdleTimeoutFault` | SESSION_IDLE_TIMEOUT | WARN | ✅ | ❌ | — |
| `SessionAbsoluteTimeoutFault` | SESSION_ABSOLUTE_TIMEOUT | WARN | ✅ | ❌ | — |
| `SessionInvalidFault` | SESSION_INVALID | ERROR | ✅ | ❌ | — |
| `SessionNotFoundFault` | SESSION_NOT_FOUND | WARN | ✅ | ❌ | — |
| `SessionPolicyViolationFault` | SESSION_POLICY_VIOLATION | ERROR | ❌ | ❌ | violation, policy_name |
| `SessionConcurrencyViolationFault` | SESSION_CONCURRENCY_VIOLATION | ERROR | ✅ | ❌ | principal_id, active_count, max_allowed |
| `SessionLockedFault` | SESSION_LOCKED | WARN | ❌ | ✅ | — |
| `SessionStoreUnavailableFault` | SESSION_STORE_UNAVAILABLE | ERROR | ❌ | ✅ | store_name, cause |
| `SessionStoreCorruptedFault` | SESSION_STORE_CORRUPTED | ERROR | ❌ | ❌ | session_id_hash |
| `SessionRotationFailedFault` | SESSION_ROTATION_FAILED | ERROR | ❌ | ✅ | old_id_hash, new_id_hash, cause |
| `SessionTransportFault` | SESSION_TRANSPORT_ERROR | WARN | ❌ | ❌ | transport_type, cause |
| `SessionForgeryAttemptFault` | SESSION_FORGERY_ATTEMPT | ERROR | ❌ | ❌ | reason |
| `SessionHijackAttemptFault` | SESSION_HIJACK_ATTEMPT | ERROR | ❌ | ❌ | reason |
| `SessionFingerprintMismatchFault` | SESSION_FINGERPRINT_MISMATCH | ERROR | ❌ | ❌ | session_id_hash |
| `SessionRequiredFault` | SESSION_REQUIRED | — | — | — | — |
| `AuthenticationRequiredFault` | AUTHENTICATION_REQUIRED | — | — | — | — |

## Privacy Protection

All faults that reference session IDs use `_hash_session_id()`:
```python
@staticmethod
def _hash_session_id(session_id: str) -> str:
    return f"sha256:{hashlib.sha256(session_id.encode()).hexdigest()[:16]}"
```

This ensures session IDs never appear in logs, error messages, or API responses.

## Fault Flow Diagram

```
SessionID.from_string()     → SessionInvalidFault
SessionID.__init__()        → SessionInvalidFault
Session.__setitem__()       → SessionLockedFault / SessionPolicyViolationFault
Session.from_dict()         → SessionStoreCorruptedFault
FileStore._get_path()       → SessionForgeryAttemptFault
Engine.resolve()            → SessionExpiredFault / SessionIdleTimeoutFault /
                              SessionAbsoluteTimeoutFault / SessionFingerprintMismatchFault
Engine.commit()             → SessionRotationFailedFault
Engine.check_concurrency()  → SessionConcurrencyViolationFault
create_transport()          → SessionTransportFault
@session.require()          → SessionRequiredFault
@authenticated              → AuthenticationRequiredFault
SessionGuard.check()        → AuthorizationFault
```

## Raw Exception Elimination

### Before Phase 11
| Location | Exception | Count |
|---|---|---|
| `SessionID.__init__` | `ValueError` | 1 |
| `SessionID.from_string` | `ValueError` | 3 |
| `Session.__setitem__` | `RuntimeError` | 1 |
| `Session.__delitem__` | `RuntimeError` | 1 |
| `Session.set` | `RuntimeError` | 1 |
| `Session.delete` | `RuntimeError` | 1 |
| `Session.clear_data` | `RuntimeError` | 1 |
| `create_transport` | `ValueError` | 1 |
| `create_transport` | `NotImplementedError` | 1 |
| **Total** | | **11** |

### After Phase 11
**0 raw exceptions remain** in the session module. All error paths use
structured `SessionFault` subclasses.
