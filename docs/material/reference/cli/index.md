# CLI Reference

`aq` is the Aquilia command-line interface, implemented with **Click**. It provides manifest-first project orchestration from scaffolding to production deployment.

## Global Options

These flags are available on **every** `aq` command:

| Flag              | Alias | Description                                      |
| ----------------- | ----- | ------------------------------------------------ |
| `--verbose`       | `-v`  | Verbose output (show debug details, tracebacks)   |
| `--quiet`         | `-q`  | Minimal output (suppress banners & decorations)   |
| `--debug`         |       | Enable debug mode (full stack traces on errors)   |
| `--no-color`      |       | Disable coloured output                           |
| `--version`       |       | Show Aquilia version and release name             |

## Environment Variables

The CLI respects these environment variables at runtime:

| Variable             | Description                                | Values             | Default    |
| -------------------- | ------------------------------------------ | ------------------ | ---------- |
| `AQUILIA_WORKSPACE`  | Workspace root path                        | Any path           | `/app`     |
| `AQUILIA_ENV`        | Runtime mode                               | `dev`, `test`, `prod` | `prod` |

## Workspace Requirement

Most commands require a `workspace.py` file in the current directory. The following commands are **exempt** and work without a workspace:

- `aq init`
- `aq doctor`
- `aq mcp`
- `aq --version` / `aq --help`

If a required workspace is missing, the CLI will abort with:

```
✗ No workspace.py found in the current directory.
  Run 'aq init workspace <name>' to create a new Aquilia workspace first.
```

## Command Categories

### Scaffold

| Command                                                       | Description                           |
| ------------------------------------------------------------- | ------------------------------------- |
| [`aq init`](init.md)                                          | Initialize a new workspace or module  |
| [`aq add`](add.md)                                            | Add components to the workspace       |

### Develop

| Command                                                       | Description                           |
| ------------------------------------------------------------- | ------------------------------------- |
| [`aq run`](run.md)                                            | Start development server (hot-reload) |
| [`aq validate`](validate.md)                                  | Validate workspace manifests          |
| [`aq compile`](compile.md)                                    | Compile manifests to artifacts        |
| [`aq test`](test.md)                                          | Run the test suite                    |
| [`aq discover`](discover.md)                                  | Auto-discover components              |
| `aq doctor`                                                   | Diagnose workspace issues             |

### Production

| Command                                                       | Description                           |
| ------------------------------------------------------------- | ------------------------------------- |
| [`aq serve`](serve.md)                                        | Start production server               |
| [`aq freeze`](freeze.md)                                      | Freeze artifacts for deploy           |

### Inspect

| Command                                                       | Description                           |
| ------------------------------------------------------------- | ------------------------------------- |
| [`aq inspect`](inspect.md)                                    | Inspect routes, DI graph, faults      |
| [`aq manifest`](manifest.md)                                  | Manage module manifests               |
| [`aq analytics`](analytics.md)                                | Discovery analytics and health reports|

### Database

| Command                                                       | Description                           |
| ------------------------------------------------------------- | ------------------------------------- |
| [`aq db`](migrate.md)                                         | ORM migrations, schema, shell         |

### Deploy

| Command                                                       | Description                           |
| ------------------------------------------------------------- | ------------------------------------- |
| [`aq deploy`](deploy.md)                                      | Generate deployment files             |
| [`aq provider`](provider.md)                                  | Cloud provider management             |

### Subsystems

| Command                                                       | Description                           |
| ------------------------------------------------------------- | ------------------------------------- |
| [`aq cache`](cache.md)                                        | Cache management                      |
| [`aq mail`](mail.md)                                          | Mail testing and inspection           |
| [`aq i18n`](i18n.md)                                          | Internationalization operations       |
| [`aq ws`](ws.md)                                              | WebSocket operations                  |
| [`aq mcp`](mcp.md)                                            | MCP server management                 |

### Admin

| Command                                                       | Description                           |
| ------------------------------------------------------------- | ------------------------------------- |
| [`aq admin`](admin.md)                                        | Admin dashboard management            |

### Other

| Command                                                       | Description                           |
| ------------------------------------------------------------- | ------------------------------------- |
| [`aq migrate`](migrate.md)                                    | Legacy project migration              |
| [`aq artifacts`](artifacts.md)                                | Artifact operations                   |
| [`aq model`](model.md)                                        | Model shell                           |

## Quick Start

```bash
# Create a new workspace
aq init workspace my-api

# Add a module
aq add module users

# Validate configuration
aq validate

# Start the development server
aq run

# Inspect registered routes
aq inspect routes

# Run tests
aq test

# Generate deployment files
aq deploy all
```