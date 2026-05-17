# Testing Architecture

Test client/server, test cases, fixtures, auth/cache/mail/fault/effect/DI test helpers, config overrides, and request factory utilities.

## Source Boundaries

| File | Lines | Classes | Functions | Purpose |
| --- | ---: | ---: | ---: | --- |
| `aquilia/testing/__init__.py` | 117 | 0 | 0 | Aquilia Testing Framework. |
| `aquilia/testing/assertions.py` | 442 | 1 | 0 | Aquilia Testing - Custom Assertion Helpers. |
| `aquilia/testing/auth.py` | 290 | 3 | 0 | Aquilia Testing - Auth & Identity Helpers. |
| `aquilia/testing/cache.py` | 221 | 2 | 0 | Aquilia Testing - Cache Testing Utilities. |
| `aquilia/testing/cases.py` | 274 | 4 | 0 | Aquilia Testing - Test Case Base Classes. |
| `aquilia/testing/client.py` | 606 | 3 | 0 | Aquilia Testing - HTTP & WebSocket Test Client. |
| `aquilia/testing/config.py` | 299 | 2 | 2 | Aquilia Testing - Config Override Utilities. |
| `aquilia/testing/di.py` | 290 | 1 | 4 | Aquilia Testing - DI Container Testing Utilities. |
| `aquilia/testing/effects.py` | 258 | 4 | 0 | Aquilia Testing - Effect System Testing Utilities. |
| `aquilia/testing/faults.py` | 167 | 2 | 0 | Aquilia Testing - Fault Testing Utilities. |
| `aquilia/testing/fixtures.py` | 212 | 0 | 14 | Aquilia Testing - Pytest Fixtures. |
| `aquilia/testing/mail.py` | 168 | 2 | 3 | Aquilia Testing - Mail Testing Utilities. |
| `aquilia/testing/server.py` | 267 | 1 | 1 | Aquilia Testing - TestServer Factory. |
| `aquilia/testing/utils.py` | 263 | 0 | 6 | Aquilia Testing - Request/Response Utility Factories. |

## Internal Shape

`testing` has 14 Python files, 25 public classes, 30 public module-level functions, and 3 constants or module flags detected by AST.

## Runtime Responsibilities

- This module has `aq` command coverage documented in `cli-reference.md`; 1 commands map to this subsystem.

## Internal Imports

| Import | Count |
| --- | ---: |
| `.client` | 3 |
| `.config` | 3 |
| `.server` | 3 |
| `.utils` | 3 |
| `.assertions` | 2 |
| `.auth` | 2 |
| `.cache` | 2 |
| `.di` | 2 |
| `.effects` | 2 |
| `.faults` | 2 |
| `.mail` | 2 |
| `aquilia.config` | 2 |
| `aquilia.manifest` | 2 |
| `.cases` | 1 |
| `.fixtures` | 1 |
| `aquilia._version` | 1 |
| `aquilia.aquilary.core` | 1 |
| `aquilia.auth.core` | 1 |
| `aquilia.di.core` | 1 |
| `aquilia.effects` | 1 |
| `aquilia.faults.core` | 1 |
| `aquilia.request` | 1 |
| `aquilia.response` | 1 |
| `aquilia.server` | 1 |

## External And Stdlib Imports

| Import root | Count |
| --- | ---: |
| `__future__` | 13 |
| `typing` | 12 |
| `collections` | 4 |
| `dataclasses` | 3 |
| `time` | 3 |
| `asyncio` | 2 |
| `contextlib` | 2 |
| `json` | 2 |
| `logging` | 2 |
| `copy` | 1 |
| `functools` | 1 |
| `pytest` | 1 |
| `unittest` | 1 |

## Lifecycle And Extension Points

| Extension Type | Source | Role |
| --- | --- | --- |
| `MockCacheBackend` | `aquilia/testing/cache.py` | In-memory cache backend for testing with TTL tracking. |
| `TestConfig` | `aquilia/testing/config.py` | Lightweight config wrapper for test overrides. |
| `MockEffectProvider` | `aquilia/testing/effects.py` | Stub provider that returns configurable values. |
| `MockEffectRegistry` | `aquilia/testing/effects.py` | Test-friendly :class:`EffectRegistry` that auto-stubs missing effects. |
| `MockFaultEngine` | `aquilia/testing/faults.py` | Drop-in replacement for :class:`~aquilia.faults.engine.FaultEngine` that captures faults instead of dispatching them. |

## Error Handling

Fault/error classes defined here:

`CapturedFault`, `MockFaultEngine`
