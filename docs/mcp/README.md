# Aquilia MCP

Aquilia MCP is a local, read-only Model Context Protocol server for coding agents working on Aquilia projects.

It indexes the repository source, docs, examples, and tests, then exposes tools and prompts for Aquilia-aware generation, validation, discovery, and debugging.

## Quick Start

```bash
aq mcp build-index --workspace .
aq mcp doctor --json
aq mcp list-tools
python -m aquilia.mcp --stdio --workspace .
```

The package lives at `aquilia/mcp`. The server identity remains `aquilia-mcp`.

## Design Rules

- Source code is the source of truth.
- `workspace.py` handles workspace orchestration.
- `modules/<name>/manifest.py` handles module internals.
- `Module.register_*`, `AppManifest.database`, and `AppManifest.route_prefix` are treated as deprecated.
- MCP tools are read-only and do not expose arbitrary shell execution.
