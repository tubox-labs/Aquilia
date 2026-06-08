# MCP Integration Guide

## Local Server Command

Use this command in local agents:

```json
{
  "command": "python",
  "args": ["-m", "aquilia.mcp", "--stdio", "--workspace", "/path/to/Aquilia"]
}
```

`aq mcp install` writes this command for Claude, Codex, and Gemini CLI configs. The installer is idempotent and supports `--dry-run` and `--verify`.

## Agent Use

Ask agents to call MCP tools before generating Aquilia code. The most useful first calls are:

- `explain_bootstrap` for runtime and request lifecycle.
- `find_api` for source symbols and docs.
- `validate_manifest_plan` before writing workspace or manifest code.
- `deprecation_guard` when adapting older snippets.
- `find_examples` to locate runnable reference applications.

## Compatibility

`aquilia.mcp` remains importable for older local configs, but new configs should use `aquilia.mcp`.

## Claude Desktop

```bash
aq mcp install --agent claude --dry-run
aq mcp install --agent claude --verify
```

## Codex

```bash
aq mcp install --agent codex --dry-run
aq mcp install --agent codex --verify
```

## Gemini CLI

```bash
aq mcp install --agent gemini --dry-run
aq mcp install --agent gemini --verify
```

Each adapter registers:

```json
{
  "command": "python",
  "args": ["-m", "aquilia.mcp", "--stdio", "--workspace", "<repo>"]
}
```
