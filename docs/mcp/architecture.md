# MCP Architecture

The server has four layers:

1. `aquilia.mcp.context` scans and indexes `aquilia/**/*.py`, `docs/**/*.md`, `examples/**/*`, and `tests/test_*.py`.
2. `aquilia.mcp.registry` exposes deterministic tools and prompts.
3. `aquilia.mcp.server.AquiliaMCPServer` maps MCP JSON-RPC methods to registry calls.
4. `aquilia.mcp.transport.stdio` provides newline-delimited JSON-RPC over stdin/stdout.

The index extracts symbols, anchors, summaries, deprecations, CLI metadata, example mappings, and source-backed architecture facts.

The runtime flow described by the tools follows the actual source path:

`aquilia.entrypoint` -> `AquiliaRuntime.configure()` -> `discover()` -> `bootstrap()` -> `AquiliaServer` -> `Aquilary` / `RuntimeRegistry` -> `ASGIAdapter`.
