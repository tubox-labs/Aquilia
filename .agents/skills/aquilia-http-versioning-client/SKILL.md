---
name: aquilia-http-versioning-client
description: "Build Aquilia outbound HTTP client and API versioning workflows. Use for aquilia.http client/session/request/response/auth/cookies/multipart/streaming/retry/interceptors/pool/middleware and versioning strategies, decorators, negotiation, middleware, resolvers, graph, and sunset behavior."
---

# Aquilia Http Versioning Client

## Purpose
Implement outbound HTTP calls and versioned inbound APIs with the actual Aquilia HTTP and versioning subsystems.

## Trigger Conditions
Use for HTTP client sessions, retries, interceptors, streaming, multipart, cookies/auth, API version decorators, URL/header/media-type negotiation, sunset headers, or route version debugging.

## Inputs
- Base URL, method, headers, auth, retry policy, timeout, stream/multipart payload.
- Versioning strategy, default version, supported versions, route version metadata, deprecation/sunset rules.

## Execution Flow
1. Use `aquilia.http` client/session/request/response primitives for outbound calls instead of ad hoc libraries when framework integration matters.
2. Configure versioning through `VersioningIntegration` or `Integration.versioning(...)`.
3. Decorate controllers/routes with version metadata or route decorator `version=` args.
4. Let `ASGIAdapter._resolve_route_inputs()` pre-resolve versioning before route matching.
5. Use version middleware/negotiation for request state and error responses.

## Constraints
- Do not claim every versioning strategy exists without checking `strategy.py` and integration config.
- Route version matching happens after path/method match; neutral routes remain matchable.
- Preserve streaming semantics and avoid buffering large bodies unless required.

## Implementation Anchors
`aquilia/http/`, `aquilia/versioning/`, `aquilia/integrations/versioning_cfg.py`, `aquilia/asgi.py`, `aquilia/controller/decorators.py`, `tests/test_http_client.py`, `tests/test_versioning.py`, `examples/versioned_public_api_app/`.

## Examples
- Configure default version `1.0` with versions `["1.0", "2.0"]`.
- Add `@GET("/items", version="2.0")` to a controller method.
- Use HTTP retry/interceptor config for an external API client service.

## Failure Handling
If a versioned route 404s, check stripped path and resolved version. If negotiation fails, inspect version parser/resolver errors. If outbound retries hide errors, log final failure with request metadata but not secrets.
