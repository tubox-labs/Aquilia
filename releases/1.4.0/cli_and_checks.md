# Modernized CLI & Unified Health Checks

Aquilia v1.4.0 modernizes the `aq` CLI architecture, introducing structured exception handling, deterministic process exit codes, and an extensible health check framework.

---

## 1. Structured CLI Core (`aquilia.cli.core`)

* **Process Exit Codes (`ExitCode`):**
  Replaces scattered `sys.exit(1)` invocations with a single source of truth:
  * `OK = 0`: Command succeeded or all checks passed.
  * `FAILED = 1`: Operational failure or check errors found.
  * `USAGE = 2`: Invalid command syntax or missing arguments.
  * `CONFIG = 3`: Configuration errors detected.
  * `INTERNAL = 4`: Unexpected internal framework error.
* **Structured CLI Faults (`CliFault`):**
  Extends `aquilia.faults.Fault` into the CLI domain:
  * `WorkspaceNotFoundFault`, `WorkspaceLoadFault`, `ModuleNotFoundFault`, `CheckFailedFault`.
* **Ambient CLI Context (`AqContext`):**
  Thread-safe context management replacing untyped dictionary accesses (`ctx.obj`).

---

## 2. Unified Health Checks Engine (`aquilia.cli.checks`)

Aquilia v1.4.0 unifies `aq doctor` and `aq validate` onto an extensible check engine:

```bash
aq doctor      # Comprehensive workspace & subsystem diagnostics
aq validate    # Strict CI verification with deterministic exit codes
```

### Probed Subsystems:
* **Workspace & Interpreter:** Checks Python compatibility (3.10+), workspace root layout, manifest syntax, and component reference resolution.
* **Routes & Controllers:** Inspects route method/path collisions using `ControllerCompiler`.
* **Database & Migrations:** Tests database reachability, pending migrations, and schema validity.
* **Subsystems (16 Probes):** Automatically probes `vectordb`, `storage`, `cache`, `mail`, `tasks`, `templates`, `i18n`, `otel`, `sse`, `auth`, `sockets`, `contracts`, `mlops`, `admin`, and `versioning`. Probes remain silent when a subsystem is unused.

---

## 3. Accurate Route Introspection (`aq inspect routes`)

* Refactored to compile routes using `ControllerCompiler`.
* Correctly counts individual HTTP endpoint methods rather than controller classes (a controller with 5 methods now accurately reports 5 routes).
* Full support for starter controllers and module route prefixes.
