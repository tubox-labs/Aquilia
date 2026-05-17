---
name: aquilia-fault-middleware-builder
description: "Build and debug Aquilia structured faults and middleware. Use for Fault subclasses, FaultDomain, FaultEngine, default handlers, Exception/Fault middleware, request IDs, CORS/CSP/CSRF/rate-limit/static middleware, and middleware chain ordering."
---

# Aquilia Fault Middleware Builder

## Purpose
Represent errors as Aquilia faults and wire middleware in the order the server actually uses.

## Trigger Conditions
Use for custom fault classes, error responses, middleware stack changes, request IDs, debug pages, security middleware, static middleware, rate limiting, or exception-to-response behavior.

## Inputs
- Fault domain/code/message/severity/public metadata.
- Middleware callable/class, scope, priority, and config.
- Expected JSON or HTML response behavior.

## Execution Flow
1. Define faults by subclassing `Fault` or using domain-specific fault modules.
2. Set stable `code`, `message`, `domain`, and safe `public` exposure.
3. Register fault behavior through `FaultHandlingConfig` or server fault engine paths.
4. Add middleware with `MiddlewareStack.add(middleware, scope="global", priority=...)` or config-driven `middleware_chain`.
5. For security middleware, use implemented middleware in `aquilia/middleware_ext/` rather than inventing wrappers.

## Constraints
- Faults require code, message, and domain; missing values raise `TypeError`.
- Middleware order is scope rank then priority, wrapped in reverse when building handlers.
- Internal `FaultMiddleware` and request scope middleware are framework plumbing and should remain present.

## Implementation Anchors
`aquilia/faults/core.py`, `aquilia/faults/engine.py`, `aquilia/faults/domains.py`, `aquilia/middleware.py`, `aquilia/middleware_ext/*.py`, `aquilia/server.py`.

## Examples
- Add a module fault domain with `FaultHandlingConfig(default_domain="ORDERS")`.
- Configure CORS, CSP, HSTS, CSRF, rate limit, and static middleware using implemented middleware classes.
- Return debug HTML for browser `Accept: text/html` in development.

## Failure Handling
If clients see raw exceptions, verify `FaultMiddleware` and `ExceptionMiddleware` order. If sensitive metadata leaks, set `public=False` and sanitize metadata. If middleware does not run, inspect scope, priority, and `middleware_chain` config.
