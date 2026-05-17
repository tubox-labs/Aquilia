# MCP Examples

## Find Aquilia APIs

```bash
aq mcp query "AppManifest route_prefix"
```

## List Agent-Facing Tools

```bash
aq mcp list-tools
```

## Build A Prompt

Use the `generate_agent_prompt` tool with:

```json
{
  "workflow": "aquilia.add_module",
  "goal": "Add an orders module with REST endpoints and background tasks"
}
```

The generated prompt includes source-backed anchors, anti-pattern guards, expected file shape, and validation steps.
