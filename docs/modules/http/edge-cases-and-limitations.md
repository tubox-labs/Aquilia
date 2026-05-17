# Http Edge Cases And Limitations

Native async HTTP client, request/response builders, sessions, retry policies, auth interceptors, cookies, middleware, streaming, and transport.

## Source-Backed Limits

- No module-specific edge branch was detected beyond optional imports, validation, and dependency availability.

## Fault And Error Classes Detected

`HTTPClientFault`, `ConnectionFault`, `ConnectionPoolExhaustedFault`, `ConnectionClosedFault`, `TimeoutFault`, `ConnectTimeoutFault`, `ReadTimeoutFault`, `WriteTimeoutFault`, `RequestTimeoutFault`, `TLSFault`, `CertificateVerifyFault`, `ResponseFault`, `InvalidResponseFault`, `DecodingFault`, `HTTPStatusFault`, `ClientErrorFault`, `ServerErrorFault`, `TooManyRedirectsFault`, `RequestBuildFault`, `InvalidURLFault`, `InvalidHeaderFault`, `TransportFault`, `ProxyFault`, `RetryExhaustedFault`, `ConfigurationFault`, `ErrorHandlingMiddleware`

## Operational Boundaries

- Optional external libraries are only required when the corresponding provider/backend/runtime is configured.
- Deprecated APIs generally warn when retained for migration rather than disappearing silently.
- Server startup intentionally degrades non-critical optional subsystems where source catches and logs exceptions.
- Use `api-reference.md` to check exact constructor defaults and method signatures before depending on behavior.

## Verification

- `aq doctor` for workspace/integration issues.
- `aq validate` for manifest issues.
- `aq inspect config` for merged configuration.
- `GET /_health` for live subsystem status once the app is running.
