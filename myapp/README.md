# myapp

Aquilia workspace generated with `aq init workspace myapp`.

## Project Structure

```
myapp/
├── workspace.py          # Workspace manifest (modules, integrations)
├── starter.py            # Welcome-page controller
├── requirements.txt      # Python dependencies
├── .env.example          # Environment variable template
├── .editorconfig         # Editor style consistency
├── .gitignore
├── Makefile              # Common dev commands
├── Dockerfile
├── .dockerignore
├── docker-compose.yml
├── config/
│   ├── base.yaml         # Base settings (all environments)
│   ├── dev.yaml          # Development overrides
│   └── prod.yaml         # Production overrides
├── models/
│   └── example.py        # Example model
├── modules/              # Application modules
└── tests/
    ├── conftest.py       # Shared fixtures
    └── test_smoke.py     # Smoke tests
```

## Getting Started

```bash
# 1. Set up environment
cp .env.example .env      # Copy & fill in your values
pip install -r requirements.txt

# 2. Add a module
aq add module users

# 3. Start dev server
make run                  # or: aq run
```

## Configuration

Aquilia separates **structure** from **runtime settings**:

| File              | Purpose                          | Committed? |
|-------------------|----------------------------------|------------|
| `workspace.py`    | Modules, integrations, structure | Yes     |
| `config/*.yaml`   | Host, port, workers, logging     | Yes     |
| `.env`            | Secrets, database URLs           | No      |

Config merge order: `base.yaml` → `<mode>.yaml` → environment variables.

## Useful Commands

```bash
make help             # Show all available make targets
make run              # Start dev server
make test             # Run tests
make lint             # Lint with ruff
make format           # Auto-format with ruff
make docker-build     # Build Docker image
```

| CLI Command            | Description                          |
|------------------------|--------------------------------------|
| `aq add module <name>` | Scaffold a new module                |
| `aq run`               | Start development server             |
| `aq run --mode=prod`   | Start production server              |
| `aq compile`           | Compile workspace artifacts          |
| `aq freeze`            | Freeze artifacts for deployment      |
| `aq validate`          | Validate workspace configuration     |
| `aq doctor`            | Diagnose workspace issues            |
| `aq inspect routes`    | Show compiled route table            |

## Documentation

See Aquilia documentation for complete guides.