# aq add

Add new components to an Aquilia workspace. Currently supports adding modules. Future versions will support controllers, services, middleware, tasks, and models directly.

## Usage

```bash
aq add module [NAME] [OPTIONS]
```

## `aq add module`

Add a new module to the current workspace. When run with a TTY and without `--yes`, launches an interactive setup wizard.

### Arguments

| Argument | Required | Description    |
| -------- | -------- | -------------- |
| `NAME`   | No       | Module name    |

### Options

| Option            | Description                                               | Default           |
| ----------------- | --------------------------------------------------------- | ----------------- |
| `--depends-on`    | Module dependencies (repeatable)                          | `()`              |
| `--fault-domain`  | Custom fault domain                                       | `<NAME>.upper()`  |
| `--route-prefix`  | Route prefix                                              | `/<name>`         |
| `--with-tests`    | Generate test routes file                                 | `False`           |
| `--minimal`       | Generate minimal module (controller + manifest only)      | `False`           |
| `--no-docker`     | Skip auto-generating Docker files                         | `False`           |
| `--yes`           | `-y`  Skip interactive prompts and use defaults            | `False`           |

### Interactive Wizard

1. **Module name** — validated against name rules
2. **Route prefix** — default `/<name>`
3. **Module type** — *Full* (controllers, services, faults, models) or *Minimal* (controller + manifest only)
4. **Fault domain** — default `<NAME>.upper()`
5. **Features** — tests, Docker file auto-generation
6. **Dependencies** — select from existing modules
7. **Confirmation** — review before generating

### Generated Structure

#### Full Module

```
modules/<name>/
├── __init__.py
├── manifest.py
├── controllers.py
├── services.py
├── faults.py
└── models/
```

#### Minimal Module (`--minimal`)

```
modules/<name>/
├── __init__.py
├── manifest.py
└── controllers.py
```

#### With Tests (`--with-tests`)

Adds `test_routes.py` to the module directory.

### Manifest Updates

After creating the module, `aq add module` automatically:

1. Updates `workspace.py` with the new `Module()` registration
2. Auto-generates `Dockerfile` and `docker-compose.yml` if they don't exist (unless `--no-docker`)
3. Refreshes the workspace configuration with auto-discovered modules

!!! note "Docker Auto-Generation"
    By default, `aq add module` generates `Dockerfile`, `.dockerignore`, and `docker-compose.yml` if they don't yet exist. Use `--no-docker` to skip this behavior.

## Examples

```bash
# Interactive mode
aq add module

# Interactive with name pre-filled
aq add module users

# Non-interactive with defaults
aq add module users -y

# With dependencies and custom settings
aq add module products --depends-on=users --route-prefix=/api/products

# Minimal module
aq add module health --minimal

# With custom fault domain
aq add module admin --fault-domain=ADMIN --route-prefix=/api/admin

# Skip Docker auto-generation
aq add module internal --no-docker
```

## Name Validation

Module names follow the same rules as workspace names:

- At least 2 characters
- Start with a lowercase letter
- Only `[a-z0-9_-]`
- Max 64 characters

## See Also

- [`aq init`](init.md) — Create a new workspace
- [`aq serve`](serve.md) — Start the production server
- [`aq validate`](validate.md) — Validate manifests