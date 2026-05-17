# MCP Examples

## Search Runtime APIs

```json
{"query": "AquiliaRuntime bootstrap", "limit": 5}
```

Call `find_api` to locate runtime source, docs, and tests before editing startup behavior.

## Validate A Module Plan

```json
{
  "plan": "Workspace('shop').module(Module('orders').route_prefix('/orders')); AppManifest(name='orders', controllers=[...])"
}
```

Call `validate_manifest_plan` before writing workspace or manifest code. It flags deprecated `Module.register_*`, `AppManifest.route_prefix`, `AppManifest.database`, YAML config, and raw framework-domain exception patterns.

## Generate An Agent Prompt

```json
{"workflow": "aquilia.add_db_models_migrations", "goal": "Add inventory models and migrations"}
```

The prompt includes current Aquilia conventions, anti-pattern guards, expected file shapes, source anchors, and validation steps.

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
