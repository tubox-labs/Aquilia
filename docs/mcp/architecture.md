# MCP Architecture

The server has four layers:

1. `aquilia.mcp.context` scans and indexes `aquilia/**/*.py`, `docs/**/*.md`, `examples/**/*`, and `tests/**/test_*.py`.
2. `aquilia.mcp.registry` exposes deterministic tools and prompts with strict schemas.
3. `aquilia.mcp.server.AquiliaMCPServer` maps MCP JSON-RPC methods to registry calls and resource/prompt access.
4. `aquilia.mcp.transport.stdio` provides bounded newline-delimited JSON-RPC over stdin/stdout.

The index extracts symbols, anchors, imports, sections, summaries, deprecations, CLI metadata, example mappings, and source-backed architecture facts. It stores a deterministic content fingerprint and a lightweight tree fingerprint so unchanged repositories can reuse the persisted index.

The runtime flow described by the tools follows the actual source path:

`aquilia.entrypoint` -> `AquiliaRuntime.configure()` -> `discover()` -> `bootstrap()` -> `AquiliaServer` -> `Aquilary` / `RuntimeRegistry` -> `ASGIAdapter`.

## Protocol

The stdio server supports `initialize`, `ping`, `tools/list`, `tools/call`, `resources/list`, `resources/read`, `prompts/list`, and `prompts/get`. JSON-RPC parsing preserves request IDs, ignores notifications that do not require replies, maps unknown methods to `-32601`, and maps Aquilia/MCP faults into structured error data.

## Security

The MCP layer is read-only by default. It does not expose shell execution or file mutation tools. Resource reads are limited to the configured root, reject absolute paths and traversal, redact secret-like lines in indexed text, and cap read sizes.
