# MCP CLI Reference

All commands are mounted under `aq mcp` from `aquilia/cli/commands/mcp.py` and use the canonical server package `aquilia.aquilia_mcp`.

## Serve

```bash
aq mcp serve --workspace . --stdio --index .aquilia/mcp/index.json
```

Starts the local MCP server over stdio. `--workspace` points at the repository or workspace root. `--index` selects a persisted index file.

## Build Index

```bash
aq mcp build-index --workspace . --force
```

Builds or refreshes the persistent source index. Without `--force`, unchanged trees reuse the existing index.

## Doctor

```bash
aq mcp doctor --json
```

Checks that the index can be loaded, tools/prompts are registered, and the server can be constructed.

## Install

```bash
aq mcp install --agent claude --dry-run
aq mcp install --agent codex --verify
aq mcp install --agent gemini
```

Patches the local agent config idempotently, preserving a backup when an existing file is changed. `--verify` constructs the server and confirms that a non-empty tool list is reachable.

## Discovery

```bash
aq mcp list-tools
aq mcp list-prompts
aq mcp query "runtime bootstrap"
```

These commands expose the same registry and search behavior available through MCP clients.

```bash
aq mcp serve [--workspace PATH] [--stdio] [--index PATH]
aq mcp build-index [--force] [--workspace PATH]
aq mcp doctor [--json]
aq mcp install --agent claude|codex|gemini [--dry-run] [--verify]
aq mcp list-tools
aq mcp list-prompts
aq mcp query "runtime bootstrap"
```

`serve` uses stdio and is intended for local agent configs.

`build-index` writes `.aquilia/mcp/index.json` by default.

`install` patches the selected agent config idempotently and backs up existing config before writing.
