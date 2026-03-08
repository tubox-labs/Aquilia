# Session Architecture & Design Analysis

## Module Structure

```
aquilia/sessions/
├── __init__.py        — Public API surface (165 lines)
├── core.py            — Session, SessionID, SessionPrincipal, SessionScope, SessionFlag (~560 lines)
├── policy.py          — SessionPolicy, PersistencePolicy, ConcurrencyPolicy, TransportPolicy (462 lines)
├── store.py           — SessionStore protocol, MemoryStore, FileStore (~530 lines)
├── engine.py          — SessionEngine 7-phase lifecycle orchestrator (~600 lines)
├── transport.py       — CookieTransport, HeaderTransport, create_transport (~400 lines)
├── faults.py          — 16 typed session faults (328 lines)
├── decorators.py      — @session, @authenticated, @stateful, guards (477 lines)
└── state.py           — SessionState, Field, CartState, UserPreferencesState (~300 lines)

aquilia/middleware_ext/
└── session_middleware.py — SessionMiddleware, OptionalSessionMiddleware (210 lines)

aquilia/server.py (lines 1260-1550)
└── Session engine creation, store resolution, transport resolution
```

## Design Principles

### 1. Sessions Are Capabilities
Sessions are explicit state containers that grant scoped access — not implicit
global cookies. This is the foundational architectural insight.

### 2. Policy-Driven Behavior
Every behavioral aspect is governed by `SessionPolicy`:
- **Lifetime**: TTL, idle timeout, absolute timeout
- **Security**: Rotation rules, fingerprint binding
- **Storage**: Persistence strategy, store selection
- **Concurrency**: Max sessions per principal, eviction strategy
- **Transport**: Cookie vs header, security flags

### 3. Transport Agnosticism
Session delivery is abstracted behind `SessionTransport` protocol:
- `CookieTransport` for web browsers (HttpOnly, Secure, SameSite)
- `HeaderTransport` for APIs and mobile apps
- Factory pattern for extensibility

### 4. Lifecycle Engine
`SessionEngine` orchestrates 7 phases per request:
1. **Detection** — Extract session ID from transport
2. **Resolution** — Load from store or create new
3. **Validation** — Check expiry, idle timeout, absolute timeout, fingerprint
4. **Binding** — Bind to request context and DI container
5. **Mutation** — Handler reads/writes session data
6. **Commit** — Persist, rotate, or destroy
7. **Emission** — Transport writes updated reference

### 5. Fault Integration
All session errors use structured `SessionFault` subclasses:
- `SessionExpiredFault`, `SessionIdleTimeoutFault`, `SessionAbsoluteTimeoutFault`
- `SessionInvalidFault`, `SessionNotFoundFault`
- `SessionLockedFault`, `SessionConcurrencyViolationFault`
- `SessionStoreUnavailableFault`, `SessionStoreCorruptedFault`
- `SessionRotationFailedFault`, `SessionTransportFault`
- `SessionForgeryAttemptFault`, `SessionHijackAttemptFault`
- `SessionFingerprintMismatchFault`, `SessionPolicyViolationFault`

## Component Interactions

```
Client → Transport.extract() → Engine.resolve() → Store.load()
                                     ↓
                              Policy.is_valid()
                                     ↓
                           Session (request-scoped)
                                     ↓
                              Handler execution
                                     ↓
Engine.commit() → Policy.should_rotate() → Store.save() → Transport.inject()
```

## Comparison to Standard Frameworks

| Feature | Aquilia | Flask | Django | FastAPI |
|---|---|---|---|---|
| Session ID Entropy | 256-bit | 128-bit | 128-bit | N/A |
| Policy Objects | ✅ | ❌ | ❌ | ❌ |
| Fingerprint Binding | ✅ | ❌ | ❌ | ❌ |
| Absolute Timeout | ✅ | ❌ | ✅ | N/A |
| Rotation on Auth | ✅ | ❌ | ✅ | N/A |
| Typed Faults | ✅ | ❌ | ❌ | ❌ |
| Transport Agnostic | ✅ | ❌ | ❌ | ❌ |
| Concurrency Limits | ✅ | ❌ | ❌ | ❌ |
| Fluent Builders | ✅ | ❌ | ❌ | ❌ |
| Session Guards | ✅ | ❌ | Partial | ❌ |
