# aq mcp

Run and manage a local Aquilia MCP (Model Context Protocol) server. Provides AI coding assistants with workspace-aware tools, prompts, and source indexing.

## Usage

```bash
aq mcp <SUBCOMMAND> [OPTIONS]
```

## Subcommands

### aq mcp serve

Start the MCP server over stdio.

```bash
aq mcp serve [OPTIONS]
```

| Option        | Description                    | Default |
| ------------- | ------------------------------ | ------- |
| `--workspace` | Repository/workspace root      | `.`     |
| `--stdio`     | Serve over stdio               | `True`  |
| `--index`     | Index file path                | auto    |

### aq mcp build-index

Build the persistent local source index.

```bash
aq mcp build-index [OPTIONS]
```

| Option        | Description                                    | Default |
| ------------- | ---------------------------------------------- | ------- |
| `--workspace` | Repository/workspace root                      | `.`     |
| `--force`     | Rebuild even if an existing index exists       | `False` |
| `--index`     | Index file path                                | auto    |

Output:

```json
{"path": "/path/to/index.surp", "fingerprint": "sha256:...", "sources": 42}
```

### aq mcp doctor

Check MCP server health.

```bash
aq mcp doctor [OPTIONS]
```

| Option        | Description          | Default |
| ------------- | -------------------- | ------- |
| `--workspace` | Workspace root       | `.`     |
| `--json`      | Output as JSON       | `False` |

### aq mcp install

Install Aquilia MCP into a local agent configuration file.

```bash
aq mcp install [OPTIONS]
```

| Option        | Description                                           | Default |
| ------------- | ----------------------------------------------------- | ------- |
| `--agent`     | Target agent: `claude`, `codex`, or `gemini`         | Required|
| `--workspace` | Repository/workspace root                             | `.`     |
| `--dry-run`   | Preview config changes without writing                | `False` |
| `--verify`    | Verify server tool list after patching                | `False` |

```bash
aq mcp install --agent claude
aq mcp install --agent codex
aq mcp install --agent gemini --dry-run
aq mcp install --agent claude --verify
```

### aq mcp list-tools

List available MCP tools as JSON.

```bash
aq mcp list-tools [OPTIONS]
```

| Option        | Description       | Default |
| ------------- | ----------------- | ------- |
| `--workspace` | Workspace root    | `.`     |

### aq mcp list-prompts

List available MCP prompts as JSON.

```bash
aq mcp list-prompts [OPTIONS]
```

| Option        | Description       | Default |
| ------------- | ----------------- | ------- |
| `--workspace` | Workspace root    | `.`     |

### aq mcp query

Search the local Aquilia MCP index.

```bash
aq mcp query <QUERY> [OPTIONS]
```

| Option        | Description       | Default |
| ------------- | ----------------- | ------- |
| `--workspace` | Workspace root    | `.`     |

```bash
aq mcp query "find all controllers"
aq mcp query "database migrations"
```

## Workspace-Free Operation

`aq mcp` does **not** require a `workspace.py` file. It can be used in any repository root to provide codebase-aware AI assistance.

## Examples

```bash
# Start the MCP server
aq mcp serve

# Build a fresh index
aq mcp build-index --force

# Check health
aq mcp doctor
aq mcp doctor --json

# Install into Claude
aq mcp install --agent claude

# List available capabilities
aq mcp list-tools
aq mcp list-prompts

# Search the index
aq mcp query "user authentication"
```

## See Also

- [MCP Module](/reference/modules/mcp/index/) — MCP server API reference