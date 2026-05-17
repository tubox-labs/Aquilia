# Core Edge Cases And Limitations

Root framework runtime files: ASGI adapter, server, runtime bootstrap, config, pyconfig, request/response, middleware, lifecycle, signing, effects, dotenv, uploads, and data structures.

## Source-Backed Limits

- YAML config loading is removed and raises `ConfigInvalidFault`.
- `AquiliaRuntime.app` and `.server` are guarded until `READY`/`RUNNING`.
- `/_health` bypasses normal routing and supports only GET/HEAD.
- HEAD can fall back to GET and strip the body.
- `aquilia.entrypoint` returns stub 503/500 ASGI apps for missing workspace/startup failure.

## Fault And Error Classes Detected

`ConfigError`, `FlowError`, `LifecycleError`, `FaultHandlerConfig`, `FaultHandlingConfig`, `RequestFault`, `MultipartParseError`, `ResponseStreamError`, `TemplateRenderError`, `InvalidHeaderError`, `ClientDisconnectError`, `RangeNotSatisfiableError`, `HLSManifestError`

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
