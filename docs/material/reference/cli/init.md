# aq init

Initialize a new Aquilia workspace. Supports interactive wizard mode and non-interactive CLI flags.

## Usage

```bash
aq init workspace [NAME] [OPTIONS]
```

## Arguments

| Argument | Required | Description                        |
| -------- | -------- | ---------------------------------- |
| `NAME`   | No       | Workspace/project name             |

## Options

| Option        | Alias | Description                                          | Default |
| ------------- | ----- | ---------------------------------------------------- | ------- |
| `--minimal`   |       | Minimal setup (no examples, no Docker, no Makefile)  | `False` |
| `--template`  |       | Use template: `api`, `service`, or `monolith`        | `none`  |
| `--yes`       | `-y`  | Skip interactive prompts and use defaults            | `False` |

## Interactive Mode

When run without `--yes` and with a TTY, `aq init` launches an interactive setup wizard:

1. **Project name** — default: `my-api`
2. **Template** — choose from:
   - *Blank workspace* — start from scratch
   - *REST API* — routes, JSON responses, CORS
   - *Microservice* — lightweight, single-purpose
   - *Monolith* — full-featured, batteries included
3. **Full vs minimal** — prompt to include full project structure
4. **Features to include** — multi-select:
   - Dockerfile
   - docker-compose
   - Makefile
   - README
   - .gitignore
   - tests/
5. **License** — choose from `MIT`, `Apache-2.0`, `BSD-3`, or none
6. **Confirmation** — review and confirm before scaffolding

## Generated Structure

### Full Mode (default)

```
my-api/
├── workspace.py
├── starter.py
├── .env.example
├── .editorconfig
├── .gitignore
├── requirements.txt
├── Makefile
├── Dockerfile
├── docker-compose.yml
├── modules/
├── tests/
│   ├── conftest.py
│   └── test_smoke.py
└── artifacts/
```

### Minimal Mode (`--minimal`)

```
my-api/
├── workspace.py
├── starter.py
├── .env.example
├── .editorconfig
├── .gitignore
├── requirements.txt
├── modules/
└── tests/
    ├── conftest.py
    └── test_smoke.py
```

## Templates

### `--template=api`

Pre-configures a REST API workspace with CORS middleware, JSON response helpers, and API-focused starter controllers.

### `--template=service`

Configures a lightweight microservice workspace with minimal dependencies and a single-purpose structure.

### `--template=monolith`

Full-featured workspace with authentication, sessions, admin dashboard, templates, static files, and database integration pre-configured.

## Name Validation

Workspace names must:

- Be at least 2 characters
- Start with a **lowercase** letter
- Contain only `[a-z0-9_-]`
- Be at most 64 characters

!!! failure "Invalid Names"
    - `MyApp` — starts with uppercase
    - `my app` — contains spaces
    - `a` — too short

## Examples

```bash
# Interactive mode with name pre-filled
aq init workspace my-api

# Non-interactive with defaults
aq init workspace my-api -y

# Minimal setup
aq init workspace my-api --minimal

# Use a template
aq init workspace api-service --template=api

# Interactive mode, pick name during wizard
aq init workspace
```

## Environment Variables

| Variable | Effect                                |
| -------- | ------------------------------------- |
| None     | `aq init` does not use env variables  |

## See Also

- [`aq add module`](add.md) — Add modules to an existing workspace
- [`aq run`](run.md) — Start the development server