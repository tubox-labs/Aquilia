# Sessions Architecture

Session IDs, policies, stores, transports, engine, decorators, typed session state, and session faults.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/sessions/__init__.py` | 144 | 0 | 0 | AquilaSessions - Production-grade session management for Aquilia. |
| `aquilia/sessions/core.py` | 602 | 5 | 0 | AquilaSessions - Core types. |
| `aquilia/sessions/decorators.py` | 442 | 4 | 2 | Unique Session Decorators for Aquilia. |
| `aquilia/sessions/engine.py` | 407 | 1 | 0 | AquilaSessions - Session Engine. |
| `aquilia/sessions/faults.py` | 320 | 16 | 0 | AquilaSessions - Fault definitions. |
| `aquilia/sessions/policy.py` | 456 | 5 | 0 | AquilaSessions - Policy types. |
| `aquilia/sessions/state.py` | 189 | 4 | 0 | Typed Session State for Aquilia. |
| `aquilia/sessions/store.py` | 309 | 3 | 0 | AquilaSessions - Session storage abstraction. |
| `aquilia/sessions/transport.py` | 290 | 3 | 1 | AquilaSessions - Transport adapters. |

## Internal Shape

`sessions` has 9 Python files, 41 public classes, 3 public module-level functions, and 9 constants or module flags detected by AST.

## Runtime Responsibilities

- No mounted `aq` command group maps directly to this module; it is used through Python APIs, manifests, workspace integrations, or server startup wiring.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.core` | 4 |
| `.faults` | 3 |
| `.decorators` | 1 |
| `.engine` | 1 |
| `.policy` | 1 |
| `.state` | 1 |
| `.store` | 1 |
| `.transport` | 1 |
| `aquilia._version` | 1 |
| `aquilia.faults` | 1 |
| `aquilia.faults.core` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `typing` | 7 |
| `__future__` | 5 |
| `datetime` | 5 |
| `dataclasses` | 4 |
| `collections` | 2 |
| `contextlib` | 2 |
| `hashlib` | 2 |
| `asyncio` | 1 |
| `base64` | 1 |
| `enum` | 1 |
| `functools` | 1 |
| `inspect` | 1 |
| `json` | 1 |
| `logging` | 1 |
| `pathlib` | 1 |
| `re` | 1 |
| `secrets` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `SessionContextManager` | `aquilia/sessions/decorators.py` | Context manager for scoped session access. |
| `SessionGuard` | `aquilia/sessions/decorators.py` | Advanced session guards for complex authorization logic. |
| `SessionEngine` | `aquilia/sessions/engine.py` | Session lifecycle orchestrator. |
| `SessionPolicyViolationFault` | `aquilia/sessions/faults.py` | Session violates policy constraints. |
| `SessionStoreUnavailableFault` | `aquilia/sessions/faults.py` | Session store is unavailable. Transient error - retry may succeed. |
| `SessionStoreCorruptedFault` | `aquilia/sessions/faults.py` | Session data in store is corrupted. |
| `SessionTransportFault` | `aquilia/sessions/faults.py` | Error extracting or injecting session via transport. |
| `PersistencePolicy` | `aquilia/sessions/policy.py` | Controls how sessions persist to storage. |
| `ConcurrencyPolicy` | `aquilia/sessions/policy.py` | Controls concurrent session limits per principal. |
| `TransportPolicy` | `aquilia/sessions/policy.py` | Controls how sessions travel across network. |
| `SessionPolicy` | `aquilia/sessions/policy.py` | Master policy that defines how sessions behave. |
| `SessionPolicyBuilder` | `aquilia/sessions/policy.py` | Fluent builder for SessionPolicy with unique Aquilia syntax. |
| `SessionStore` | `aquilia/sessions/store.py` | Abstract session storage interface. |
| `MemoryStore` | `aquilia/sessions/store.py` | In-memory session storage for development and testing. |
| `FileStore` | `aquilia/sessions/store.py` | File-based session storage for debugging and development. NOT suitable for production. |
| `SessionTransport` | `aquilia/sessions/transport.py` | Abstract transport interface for session ID delivery. |
| `CookieTransport` | `aquilia/sessions/transport.py` | Cookie-based session transport. |
| `HeaderTransport` | `aquilia/sessions/transport.py` | Header-based session transport for APIs and mobile apps. |

## Error Handling

Fault/error classes defined here:

`SessionRequiredFault`, `SessionFault`, `SessionExpiredFault`, `SessionIdleTimeoutFault`, `SessionAbsoluteTimeoutFault`, `SessionInvalidFault`, `SessionNotFoundFault`, `SessionPolicyViolationFault`, `SessionConcurrencyViolationFault`, `SessionLockedFault`, `SessionStoreUnavailableFault`, `SessionStoreCorruptedFault`, `SessionRotationFailedFault`, `SessionTransportFault`, `SessionForgeryAttemptFault`, `SessionHijackAttemptFault`, `SessionFingerprintMismatchFault`
