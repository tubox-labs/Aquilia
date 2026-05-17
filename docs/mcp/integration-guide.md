# MCP Integration Guide

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
