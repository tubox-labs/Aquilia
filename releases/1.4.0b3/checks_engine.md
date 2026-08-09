# Unified Health Checks Engine — v1.4.0b3

## Overview & Architecture

Aquilia v1.4.0b3 introduces a unified health checks engine (`aquilia.cli.checks`). It replaces the legacy, separate implementations in `doctor.py` (597 lines) and `validate.py` (372 lines) with a single registry of extensible, tagged check functions.

```
aquilia/cli/checks/
├── __init__.py        # Re-exports check protocol & runner
├── base.py            # Finding, Check, CheckResult, @register_check decorator
├── report.py          # Human and JSON report formatters
├── workspace.py       # Core workspace health checks (modules, manifests, routes, DI, DB)
└── subsystems.py      # Subsystem-specific probes (tasks, templates, storage, etc.)
```

---

## 1. The Check Protocol (`base.py`)

Checks never print directly to `stdout` or `stderr`. Instead, a check receives an `AqContext` instance and yields structured `Finding` objects.

```python
from aquilia.cli.checks.base import Finding, register_check
from aquilia.cli.core.context import AqContext
from aquilia.faults.core import Severity

@register_check(
    name="db.reachable",
    summary="Database configuration is valid and reachable",
    tags=["db", "deep"],
    subsystem="db",
)
def check_db_reachable(ctx: AqContext):
    ws = ctx.workspace
    db_cfg = ws.workspace_obj.database
    if db_cfg is None:
        yield Finding(
            code="AQ_DB_NOT_CONFIGURED",
            message="No database integration configured in workspace",
            severity=Severity.WARN,
            remedy="Add DatabaseIntegration to workspace.py if persistence is required",
        )
```

### Finding Dataclass

```python
@dataclass
class Finding:
    code: str                  # Stable identifier (e.g. "AQ_DB_MISSING")
    message: str               # Human-readable summary
    severity: Severity = Severity.ERROR # Severity level (INFO, WARN, ERROR, FATAL)
    remedy: str | None = None  # Actionable remediation guidance
    location: str | None = None# File path or module location
    detail: str | None = None  # Detailed error or stack trace (shown in -v mode)
```

---

## 2. Core Workspace Checks (`workspace.py`)

| Check Name | Summary | Severity Range | Tags |
|---|---|---|---|
| `env.python` | Interpreter version >= 3.10 | `FATAL` | `env`, `quick` |
| `workspace.present` | `workspace.py` exists and imports cleanly | `ERROR`, `WARN` | `workspace`, `quick` |
| `workspace.modules` | Declared modules exist on disk | `ERROR`, `WARN` | `workspace`, `modules` |
| `manifest.loadable` | Every declared module has an importable `manifest.py` | `ERROR` | `manifest`, `quick` |
| `manifest.references` | Component references (`module.path:Class`) resolve | `ERROR` | `manifest`, `deep` |
| `routes.parsable` | Controller route metadata extracts cleanly | `ERROR` | `routes`, `deep` |
| `routes.conflicts` | No overlapping HTTP method + path collisions | `ERROR` | `routes`, `deep` |
| `di.providers` | DI service providers resolve and import | `ERROR`, `INFO` | `di`, `deep` |
| `db.reachable` | Database backend configured and reachable | `ERROR`, `WARN` | `db`, `deep` |

---

## 3. Config-Driven Subsystem Checks (`subsystems.py`)

Subsystem checks inspect the integrations declared on `workspace.py` and stay silent when a subsystem is unused. This closes the monitoring gap for 13 subsystems:

- **`tasks.registry`**: Validates background task references (`module:task_name`) and confirms functions carry the `@task` decorator.
- **`templates.dirs`**: Verifies that configured Jinja template search directories exist on disk.
- **`subsystems.available`**: Confirms that packages for configured integrations (`storage`, `cache`, `mail`, `i18n`, `otel`, `sse`, `versioning`, `http`, `auth`, `sockets`, `contracts`, `mlops`, `admin`) are installed.

---

## 4. Route Introspection Engine (`aquilia.cli.introspect.routes`)

Legacy CLI route inspection relied on checking non-existent attributes like `__controller_routes__`. v1.4.0b3 uses `ControllerCompiler` — the exact same compiler called by `AquiliaServer` at boot.

```python
from aquilia.cli.introspect.routes import collect_routes, count_routes

# Collect all routes across workspace modules and starter controllers
routes = collect_routes(ws)
for controller in routes:
    print(f"Controller: {controller.controller} (Prefix: {controller.prefix})")
    for r in controller.routes:
        print(f"  {r.http_method:<6} {r.full_path:<30} -> {r.handler}")
```

### Accurate Route Counting

`count_routes()` counts individual HTTP endpoints rather than controller classes. A controller exposing 5 endpoint methods now correctly reports `5 routes` instead of `1`.

---

## 5. Report Formatters (`report.py`)

### Human Output (`render_human`)

```
  x  [AQ_DB_MISSING] Database file does not exist: /app/db.sqlite3
        at: /app/db.sqlite3
        fix: Run migrations to create the DB, or check the configured path
  !  [AQ_TASK_NOT_DECORATED] users: 'sync_user' is listed as a task but has no @task decorator
        at: modules/users/tasks.py
        fix: Decorate it with @task so the registry can schedule it

  12 checks run: 1 error, 1 warning
  Result: FAILED
```

### JSON Output (`render_json`) for CI Pipelines

```json
{
  "summary": {
    "checks_run": 12,
    "checks_skipped": 0,
    "checks_errored": 0,
    "findings": {
      "info": 0,
      "warn": 1,
      "error": 1,
      "fatal": 0
    },
    "total_findings": 2,
    "passed": false
  },
  "exit_code": 1,
  "checks": [
    {
      "name": "db.reachable",
      "summary": "Database configuration is valid and reachable",
      "subsystem": "db",
      "tags": ["db", "deep"],
      "skipped": false,
      "findings": [
        {
          "code": "AQ_DB_MISSING",
          "message": "Database file does not exist: /app/db.sqlite3",
          "severity": "error",
          "remedy": "Run migrations to create the DB, or check the configured path",
          "location": "/app/db.sqlite3",
          "detail": null
        }
      ]
    }
  ]
}
```
