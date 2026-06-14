# MCP Module

> `aquilia.mcp` — Model Context Protocol server

The MCP module provides a Model Context Protocol (MCP) server implementation for exposing Aquilia application tools, prompts, and context to AI assistants and LLM clients.

## When to Use

Use the MCP module when you need:

- Exposing application tools to AI assistants
- Building MCP-compliant tool servers
- Providing context scanning and indexing
- Installing MCP servers for Claude Desktop or similar clients

## Key Classes

| Class | Purpose |
|---|---|
| `MCPServer` | MCP protocol server |
| Protocol | Transport-agnostic MCP protocol handler |
| Tools | 11 built-in tools for context operations |
| Prompts | Prompt templates for AI interaction |
| Context scanner/indexer | Scans and indexes project context |

## Built-in Tools

The MCP server includes 11 tools for:

- Codebase context scanning and indexing
- Project structure analysis
- Documentation retrieval
- Dependency inspection
- Route inspection
- Configuration analysis

## CLI Usage

```bash
# Start the MCP server
aq mcp

# Install for Claude Desktop
aq mcp install
```

## Import Path

```python
from aquilia.mcp import MCPServer
```

## Related Modules

- [cli](../cli/index.md) — `aq mcp` command
- [discovery](../discovery/index.md) — Context scanning uses discovery engine