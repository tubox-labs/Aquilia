# sessions Module

## Purpose

Session policies, stores, transports, and guards. Use this module for session creation, cookie and header transport, persistence policy, state objects, guards, decorators, and session fault handling.

## Source Coverage

- Python files: 9
- Public classes: 41
- Dataclasses: 6
- Enums: 2
- Public functions: 3

## How It Fits In Aquilia

1. Define SessionPolicy objects and choose store plus transport policy.
2. Session middleware resolves session data and places it on RequestCtx.
3. Decorators and guards enforce required session state.

## Practical Guidance

- Cookie security defaults are strict. For local HTTP development, intentionally configure secure flags through environment config.
- Session state should be small and serializable. Use storage or cache for larger data.

## Public Classes

| Name | Source | Role |
| --- | --- | --- |
| `SessionID` | `aquilia/sessions/core.py` | Opaque session identifier with cryptographic randomness. |
| `SessionScope` | `aquilia/sessions/core.py` | Public class. |
| `SessionFlag` | `aquilia/sessions/core.py` | Public class. |
| `SessionPrincipal` | `aquilia/sessions/core.py` | Represents who the session belongs to. |
| `Session` | `aquilia/sessions/core.py` | Core session object - explicit state container with lifecycle. |
| `SessionRequiredFault` | `aquilia/sessions/decorators.py` | Raised when session is required but missing. |
| `SessionDecorators` | `aquilia/sessions/decorators.py` | Namespace for session decorators. |
| `SessionContextManager` | `aquilia/sessions/decorators.py` | Context manager for scoped session access. |
| `SessionGuard` | `aquilia/sessions/decorators.py` | Advanced session guards for complex authorization logic. |
| `SessionEngine` | `aquilia/sessions/engine.py` | Session lifecycle orchestrator. |
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
| `PersistencePolicy` | `aquilia/sessions/policy.py` | Controls how sessions persist to storage. |
| `ConcurrencyPolicy` | `aquilia/sessions/policy.py` | Controls concurrent session limits per principal. |
| `TransportPolicy` | `aquilia/sessions/policy.py` | Controls how sessions travel across network. |
| `SessionPolicy` | `aquilia/sessions/policy.py` | Master policy that defines how sessions behave. |
| `SessionPolicyBuilder` | `aquilia/sessions/policy.py` | Fluent builder for SessionPolicy with unique Aquilia syntax. |
| `Field` | `aquilia/sessions/state.py` | Field descriptor for SessionState. |
| `SessionState` | `aquilia/sessions/state.py` | Base class for typed session state. |
| `CartState` | `aquilia/sessions/state.py` | Shopping cart session state. |
| `UserPreferencesState` | `aquilia/sessions/state.py` | User preferences session state. |
| `SessionStore` | `aquilia/sessions/store.py` | Abstract session storage interface. |
| `MemoryStore` | `aquilia/sessions/store.py` | In-memory session storage for development and testing. |
| `FileStore` | `aquilia/sessions/store.py` | File-based session storage for debugging and development. |
| `SessionTransport` | `aquilia/sessions/transport.py` | Abstract transport interface for session ID delivery. |
| `CookieTransport` | `aquilia/sessions/transport.py` | Cookie-based session transport. |
| `HeaderTransport` | `aquilia/sessions/transport.py` | Header-based session transport for APIs and mobile apps. |

## Public Functions

| Name | Source | Role |
| --- | --- | --- |
| `stateful` | `aquilia/sessions/decorators.py` | Shorthand decorator for stateful sessions. |
| `requires` | `aquilia/sessions/decorators.py` | Decorator to require multiple session guards. |
| `create_transport` | `aquilia/sessions/transport.py` | Create transport adapter from policy. |

## Implementation Map

| File | What To Look For |
| --- | --- |
| `aquilia/sessions/__init__.py` | AquilaSessions - Production-grade session management for Aquilia. |
| `aquilia/sessions/core.py` | AquilaSessions - Core types. |
| `aquilia/sessions/decorators.py` | Unique Session Decorators for Aquilia. |
| `aquilia/sessions/engine.py` | AquilaSessions - Session Engine. |
| `aquilia/sessions/faults.py` | AquilaSessions - Fault definitions. |
| `aquilia/sessions/policy.py` | AquilaSessions - Policy types. |
| `aquilia/sessions/state.py` | Typed Session State for Aquilia. |
| `aquilia/sessions/store.py` | AquilaSessions - Session storage abstraction. |
| `aquilia/sessions/transport.py` | AquilaSessions - Transport adapters. |

## Testing Pointers

Search `tests/` for `sessions` to find behavior-level examples. The test suite is especially useful for edge cases because many modules expose lightweight public APIs but enforce important security and lifecycle behavior internally.
