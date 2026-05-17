# Sessions Edge Cases And Limitations

## Fault And Error Types

The following error-oriented classes are present in the implementation and should guide defensive usage.

| Type | Source | Meaning |
| --- | --- | --- |
| `SessionRequiredFault` | `aquilia/sessions/decorators.py` | Raised when session is required but missing. |
| `SessionFault` | `aquilia/sessions/faults.py` | Base class for session-related faults. |
| `SessionExpiredFault` | `aquilia/sessions/faults.py` | Session has expired (TTL exceeded). |
| `SessionIdleTimeoutFault` | `aquilia/sessions/faults.py` | Session idle timeout exceeded. |
| `SessionAbsoluteTimeoutFault` | `aquilia/sessions/faults.py` | Session absolute timeout exceeded (OWASP requirement). |
| `SessionInvalidFault` | `aquilia/sessions/faults.py` | Session ID is invalid or malformed. |
| `SessionNotFoundFault` | `aquilia/sessions/faults.py` | Session ID not found in store. |
| `SessionPolicyViolationFault` | `aquilia/sessions/faults.py` | Session violates policy constraints. |
| `SessionConcurrencyViolationFault` | `aquilia/sessions/faults.py` | Too many concurrent sessions for principal. |
| `SessionLockedFault` | `aquilia/sessions/faults.py` | Session is locked by another operation. Retry after lock is released. |
| `SessionStoreUnavailableFault` | `aquilia/sessions/faults.py` | Session store is unavailable. Transient error - retry may succeed. |
| `SessionStoreCorruptedFault` | `aquilia/sessions/faults.py` | Session data in store is corrupted. |
| `SessionRotationFailedFault` | `aquilia/sessions/faults.py` | Session ID rotation failed. Session may be in inconsistent state. |
| `SessionTransportFault` | `aquilia/sessions/faults.py` | Error extracting or injecting session via transport. |
| `SessionForgeryAttemptFault` | `aquilia/sessions/faults.py` | Suspected session forgery or tampering. Security event. |
| `SessionHijackAttemptFault` | `aquilia/sessions/faults.py` | Suspected session hijacking (IP/User-Agent mismatch). |
| `SessionFingerprintMismatchFault` | `aquilia/sessions/faults.py` | Session fingerprint does not match client (OWASP hijack detection). |

## Common Edge Cases

- Optional dependencies may change behavior. Check imports and constructor docs before enabling production features.
- In-memory stores, queues, caches, adapters, and registries are usually process-local. Use durable backends when state must survive restarts or scale across workers.
- Request-scoped data must not be cached globally. Use request state, DI request scopes, or explicit parameters.
- Decorators in Aquilia generally attach metadata at import time. Runtime behavior happens later during compilation, routing, middleware execution, or service startup.
- Many subsystems intentionally convert invalid states into typed faults. Catch the specific fault type when application code can recover.

## Source-Level Limits To Review

Review these files before changing behavior:

- `aquilia/sessions/__init__.py`: AquilaSessions - Production-grade session management for Aquilia.
- `aquilia/sessions/core.py`: AquilaSessions - Core types.
- `aquilia/sessions/decorators.py`: Unique Session Decorators for Aquilia.
- `aquilia/sessions/engine.py`: AquilaSessions - Session Engine.
- `aquilia/sessions/faults.py`: AquilaSessions - Fault definitions.
- `aquilia/sessions/policy.py`: AquilaSessions - Policy types.
- `aquilia/sessions/state.py`: Typed Session State for Aquilia.
- `aquilia/sessions/store.py`: AquilaSessions - Session storage abstraction.
- `aquilia/sessions/transport.py`: AquilaSessions - Transport adapters.
