# MCP CLI Reference

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
