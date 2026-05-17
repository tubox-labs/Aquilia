# Aquilia MCP

Aquilia MCP is a local, read-only Model Context Protocol server for coding agents working on Aquilia projects.

It indexes the actual repository source, docs, examples, and tests, then exposes source-backed tools and prompts for Aquilia-aware generation, validation, discovery, and debugging. The canonical package is `aquilia.aquilia_mcp`; `aquilia.mcp` remains as a compatibility import path.

## Quick Start

```bash
aq mcp build-index --workspace .
aq mcp doctor --json
aq mcp list-tools
python -m aquilia.aquilia_mcp --stdio --workspace .
```

The server identity remains `aquilia-mcp`.

## Tools

- `find_api`: search symbols, docs, examples, and tests.
- `explain_bootstrap`: explain runtime/server/ASGI flow from source anchors.
- `suggest_architecture`: propose manifest-first workspace/module structure.
- `scaffold_workspace`: return a read-only workspace scaffold plan.
- `scaffold_module`: return a read-only module scaffold plan.
- `validate_manifest_plan`: catch deprecated or incorrect Aquilia patterns.
- `recommend_integrations`: map feature goals to current Integration/Workspace APIs.
- `deprecation_guard`: flag deprecated APIs in snippets or plans.
- `list_cli_commands`: list the mounted Click command tree.
- `find_examples`: find runnable examples by feature.
- `generate_agent_prompt`: render source-backed workflow prompts.

## Design Rules

- Source code is the source of truth.
- `workspace.py` handles workspace orchestration.
- `modules/<name>/manifest.py` handles module internals.
- `Module.register_*`, `AppManifest.database`, and `AppManifest.route_prefix` are treated as deprecated.
- MCP tools are read-only and do not expose arbitrary shell execution.
- Resource reads reject path traversal, null bytes, missing files, directories, and binary files.
