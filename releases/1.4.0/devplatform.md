# Native Development Platform (`aquilia.devplatform` / ADP)

Aquilia v1.4.0 rebuilds the local development experience with a high-performance native ASGI development server, deprecating toy parsers in favor of an `h11`-based HTTP engine, a dependency-free RFC 6455 WebSocket engine, and AST-based hot-reloading.

---

## Native ASGI Transports

1. **`h11`-Powered HTTP/1.1 Engine (`aquilia.devplatform.core.h11_transport`):**
   * Driven by the robust `h11` state machine.
   * Full native support for HTTP keep-alive, pipelining, and chunked transfer encoding.
   * Activated by default in development mode (`--http h11`).

2. **RFC 6455 WebSocket Engine (`aquilia.devplatform.core.websocket_transport`):**
   * Zero external dependencies (stdlib-only implementation).
   * Supports text/binary frames, ping/pong heartbeats, protocol subprotocols, and clean disconnects.
   * Security guarded with `_MAX_FRAME_SIZE` (16 MiB) frame-size DoS protection.

3. **UNIX Domain Sockets & File Descriptors:**
   * `--uds PATH`: Bind development servers directly to a UNIX domain socket.
   * `--fd N`: Bind development servers to an inherited file descriptor.

---

## AST-Based Dependency Hot Reloading

Previous reload implementations used naive prefix matching that triggered false-positive full reloads. v1.4.0 introduces an AST-driven reverse dependency analyzer (`aquilia.devplatform.reload.analyzer`):
* Statically parses Python module imports using `ast.parse`.
* Correctly resolves relative imports to exact fully-qualified module paths.
* Integrates with `AutoDiscoveryEngine` to report human-readable discovery diffs on reload (e.g. `Discovery diff: 1 controller added, 2 services updated`).
* Executes bounded graceful server shutdown (`AquiliaServer.graceful_shutdown()`) before triggering `os.execv()`, allowing in-flight requests and database pools to close cleanly.

---

## Per-Request CPU Profiling

cProfile CPU capture is now wired directly into the ASGI request pipeline:
* Enable globally via `profiler_enabled=True` or on a per-request basis using the `X-Aquilia-Profile: true` HTTP header.
* Captured profiles are viewable directly in Aquilia Inspector via Flamegraph (Speedscope format) or tree view:
  ```
  GET /__aquilia__/inspector/devplatform/profile/{request_id}/?format=flamegraph
  ```

---

## DevPlatform Fault Domain Integration

The devplatform is fully integrated with Aquilia's unified fault system:
* `FaultDomain.DEVPLATFORM` with structured faults: `StartupFault`, `ReloadFault`, `InspectorFault`, `WorkerFault`, and `ConfigurationFault`.
* All faults automatically surface in the Aquilia Inspector exception lane.
