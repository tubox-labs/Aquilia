---
name: aquilia-testing-debug-toolkit
description: "Use Aquilia testing and debugging utilities. Use for TestServer, TestClient, WebSocketTestClient, AquiliaTestCase, fixtures, mocks, aq test, debug pages, diagnostics, health, and framework regression tests."
---

# Aquilia Testing Debug Toolkit

## Purpose
Test Aquilia apps in-process and debug framework behavior with real testing utilities.

## Trigger Conditions
Use for writing tests, running `aq test`, in-process HTTP/WebSocket tests, fixtures, mock DI/cache/effects/fault/mail, debug pages, health checks, and regression coverage.

## Inputs
- Manifests, config overrides, enabled subsystems, request paths, expected responses.
- Pytest/unittest preference.
- Optional live server requirement.

## Execution Flow
1. For in-process API tests, use `TestServer` and `TestClient`; no network socket is needed.
2. For unittest-style tests, subclass `AquiliaTestCase`; set `manifests`, `settings`, and subsystem enable flags.
3. For pytest, import fixtures from `aquilia.testing.fixtures`.
4. Use `TestResponse` helpers for JSON, headers, status, redirects, and cookies.
5. Run `aq test` or `python -m pytest tests/` depending on scope.

## Constraints
- Prefer in-process tests unless real TCP behavior is required.
- Enable subsystems explicitly in test cases to avoid hidden dependencies.
- Keep workspace mutation out of tests unless testing generators/discovery.

## Implementation Anchors
`aquilia/testing/`, `aquilia/debug/pages.py`, `aquilia/cli/commands/test.py`, `tests/`, `examples/*/tests/`.

## Examples
- `async with TestServer(manifests=[manifest]) as srv: resp = await TestClient(srv).get("/")`.
- Subclass `AquiliaTestCase` with `enable_sessions=True`.
- Use `mail_outbox`, `di_container`, or `effect_registry` fixtures.

## Failure Handling
If server exceptions should be captured rather than raised, configure `TestClient(raise_server_exceptions=False)`. If async fixtures fail, confirm pytest-asyncio is installed and `asyncio_mode=auto` from pyproject is active.
