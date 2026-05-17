# Aquilia MCP Bootstrap Example

This example shows local agent configuration snippets for running Aquilia MCP.

Build the index:

```bash
aq mcp build-index --workspace ../..
```

Start the server:

```bash
python -m aquilia.aquilia_mcp --stdio --workspace ../..
```

See `mcp_config/` for Claude, Codex, and Gemini example config snippets.
