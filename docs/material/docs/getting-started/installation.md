# Installation

Aquilia is distributed via PyPI. The core package includes the framework runtime, CLI, controllers, DI, ORM, templates, filesystem, and native SQLite support. Optional extras add auth, PostgreSQL, Redis, OpenTelemetry, mail providers, and production server tooling.

---

## System Requirements

| Requirement | Minimum |
|---|---|
| **Python** | 3.10, 3.11, 3.12, or 3.13 |
| **OS** | Linux, macOS, Windows |
| **Package manager** | pip 23.0+ or uv |
| **Virtual environment** | Recommended |

Python 3.9 and earlier are **not supported**. Aquilia uses `|` union type syntax, `match`/`case` statements, and `asyncio` features available only in 3.10+.

---

## Core Installation

=== "pip"
    ```bash
    pip install aquilia
    ```

=== "uv"
    ```bash
    uv pip install aquilia
    ```

The core install includes:

- `click` — CLI framework
- `uvicorn` — ASGI server (development)
- `jinja2` — template engine
- `markupsafe` — template security
- `surp` — serializer for manifest compilation

This is enough to create a workspace, define controllers, use the ORM with SQLite, serve templates, and run background tasks.

---

## Optional Extras

Aquilia uses pip's extras mechanism to keep the core lean while making powerful subsystems available on demand.

### Authentication and Security

=== "Auth (all)"
    ```bash
    pip install aquilia[auth]
    ```
    Adds `cryptography` and `argon2-cffi` for JWT signing, password hashing, OAuth, and MFA.

=== "Multipart"
    ```bash
    pip install aquilia[multipart]
    ```
    Adds `python-multipart` for form and file upload parsing.

### Databases

=== "PostgreSQL"
    ```bash
    pip install aquilia[postgres]
    ```
    Adds `asyncpg` for async PostgreSQL connectivity.

=== "Redis"
    ```bash
    pip install aquilia[redis]
    ```
    Adds `redis[asyncio]` for cache backends, WebSocket pub/sub, and session stores.

### Email Providers

=== "SMTP"
    ```bash
    pip install aquilia[mail]
    ```
    Adds `aiosmtplib` for SMTP email delivery.

=== "AWS SES"
    ```bash
    pip install aquilia[mail-ses]
    ```
    Adds `aiobotocore` for SES email delivery.

=== "SendGrid"
    ```bash
    pip install aquilia[mail-sendgrid]
    ```
    Adds `httpx` for SendGrid API email delivery.

### Observability

=== "OpenTelemetry"
    ```bash
    pip install aquilia[otel]
    ```
    Adds OpenTelemetry API, SDK, OTLP gRPC exporter, and ASGI instrumentation.

### Production

=== "Server"
    ```bash
    pip install aquilia[server]
    ```
    Adds `gunicorn` and `uvicorn[standard]` for production deployment with worker management.

---

## Bundle Extras

=== "Full"
    ```bash
    pip install aquilia[full]
    ```
    Installs: `auth`, `multipart`, `redis`, `mail`, `mail-ses`, `mail-sendgrid`, `server`, `postgres`, `otel`.

=== "All"
    ```bash
    pip install aquilia[all]
    ```
    Alias for `full`. Everything in one install.

---

## Development Installation

=== "Development dependencies"
    ```bash
    pip install aquilia[dev]
    ```
    Installs: testing tools (`pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`), `ruff`, `mypy`, and `pre-commit`.

=== "Testing only"
    ```bash
    pip install aquilia[testing]
    ```
    Installs: `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx`.

=== "From source (dev)"
    ```bash
    git clone https://github.com/anomalyco/Aquilia
    cd Aquilia
    pip install -e ".[dev]"
    ```

---

## Verify the Installation

After installing, verify that the `aq` CLI is available and the framework version is correct:

```bash
$ aq --version
⚓ Aquilia 1.1.2 "Crimson Gale"
```

Check that the core imports work:

```python
$ python -c "from aquilia import Controller, GET, POST, RequestCtx, Response; print('OK')"
OK
```

Check available CLI commands:

```bash
$ aq --help
Usage: aq [OPTIONS] COMMAND [ARGS]...

  Aquilia — async-native Python web framework

Options:
  --version          Show the version and exit.
  --verbose, -v      Verbose output
  --quiet, -q        Minimal output
  --debug            Enable debug mode
  --no-color         Disable coloured output

Commands:
  init        Scaffold a new workspace
  add         Add a module to the workspace
  serve       Start development server
  validate    Validate workspace manifests
  inspect     Inspect routes, providers, and compiled data
  compile     Freeze manifests into a deployment artifact
  test        Run the project test suite
  migrate     Run database migrations
  generate    Generate controllers, services, models
  deploy      Generate Docker, K8s, and infrastructure files
  ...
```

---

## Environment Variables

Aquilia uses these environment variables for runtime configuration:

| Variable | Purpose | Values | Default |
|---|---|---|---|
| `AQUILIA_ENV` | Runtime mode | `dev`, `test`, `prod` | `prod` |
| `AQUILIA_WORKSPACE` | Workspace root directory | Any path | `/app` |
| `SECRET_KEY` | Signing secret for sessions, CSRF, cache | Any string | Auto-generated in dev |
| `AQ_SECRET_KEY` | Alternative signing secret key | Any string | — |

Environment variables prefixed with `AQ_` are parsed by the `ConfigLoader` and merged into the runtime configuration. Double underscores become nested keys — for example, `AQ_DATABASE__URL` becomes `config["database"]["url"]`.

---

## Platform Notes

### macOS

No special configuration needed. If using `pip install aquilia[postgres]`, ensure `libpq` is available:

```bash
brew install postgresql
```

### Linux

For production deployments with Gunicorn, ensure the `server` extra is installed:

```bash
pip install aquilia[full]
```

### Windows

Windows is fully supported. For PostgreSQL, install `asyncpg` which includes precompiled wheels for Windows. For file path operations, Aquilia's `filesystem` module normalizes platform separators automatically.

---

## Next Steps

<div class="grid cards" markdown>

-   :material-rocket-launch:{ .lg .middle } **Quickstart**

    ---

    Create your first workspace and serve a controller in under 5 minutes.

    [:octicons-arrow-right-24: Quickstart](quickstart.md)

-   :material-school:{ .lg .middle } **First Project**

    ---

    Build a complete CRUD API with workspace, module, controller, service, blueprint, and DI.

    [:octicons-arrow-right-24: First project](first-project.md)

-   :material-book:{ .lg .middle } **Configuration**

    ---

    Learn about `Workspace`, `Module`, `Integration`, environment variables, and Python-native config.

    [:octicons-arrow-right-24: Configuration](../guides/configuration.md)

</div>