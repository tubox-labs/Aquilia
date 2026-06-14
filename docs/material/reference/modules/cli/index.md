# CLI Module

> `aquilia.cli` — The `aq` command-line interface

The CLI module implements the `aq` command-line tool with over 25 commands for scaffolding, development, production deployment, inspection, database operations, and subsystem management.

## When to Use

Use the CLI module when you need to:

- Scaffold new workspaces and modules (`aq init`, `aq add`)
- Run the development server (`aq run`)
- Serve production traffic (`aq serve`)
- Validate manifests and routes (`aq validate`)
- Inspect registered routes, DI graph, and faults (`aq inspect`)
- Manage database migrations (`aq db`)
- Generate deployment artifacts (`aq deploy`)
- Freeze artifacts for production (`aq freeze`)
- Test your application (`aq test`)

## Command Categories

| Category | Commands |
|---|---|
| **Scaffold** | `init`, `add` |
| **Develop** | `run`, `validate`, `compile`, `test`, `discover` |
| **Production** | `serve`, `freeze` |
| **Inspect** | `inspect`, `manifest`, `analytics` |
| **Database** | `db` (migrations, schema, shell) |
| **Deploy** | `deploy`, `provider` |
| **Subsystems** | `cache`, `mail`, `i18n`, `ws`, `mcp` |
| **Admin** | `admin` |
| **Other** | `migrate`, `artifacts`, `model` |

## Quick Example

```bash
# Initialize a new workspace
aq init workspace my-api

# Add a module
aq add module users

# Validate configuration
aq validate

# Start the dev server
aq run

# Inspect registered routes
aq inspect routes

# Run tests
aq test

# Generate deployment files
aq deploy dockerfile
```

## Import Path

```python
# CLI is invoked via the `aq` command, not imported directly
# Entry point: aquilia/cli/__init__.py → main()
```

## Related Modules

- [core/server](../core/server.md) — Server started by `aq serve`
- [core/entrypoint](../core/entrypoint.md) — The entrypoint used by `aq run` / `aq serve`
- [discovery](../discovery/index.md) — Component discovery used by `aq discover`