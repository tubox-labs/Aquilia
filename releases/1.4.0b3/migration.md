# Migration Guide — 1.4.0b2 → 1.4.0b3

Aquilia v1.4.0b3 is backward-compatible for standard applications, but introduces breaking changes for internal CLI tools, custom health scripts, and CI/CD pipelines expecting legacy exit code behavior.

---

## 1. Exit Code Contract Changes

In v1.4.0b2 and earlier, `aq doctor` and `aq validate` returned exit code `0` even when findings contained errors. In v1.4.0b3, exit codes are strictly enforced:

- `ExitCode.OK` (`0`): Command succeeded without errors.
- `ExitCode.FAILED` (`1`): At least one `ERROR` or `FATAL` finding was discovered.
- `ExitCode.CONFIG` (`3`): Workspace file missing or unloadable.

### CI/CD Pipeline Migration

If your CI pipeline relies on `aq validate` or `aq doctor`, update scripts to handle non-zero exit codes:

```bash
# BEFORE (in CI pipeline)
aq validate
# Always returned 0, even on broken manifests

# AFTER (in CI pipeline)
aq validate
# Returns exit code 1 if manifest has errors, failing the build as intended.
```

---

## 2. Removed Legacy Parser Modules

The following internal CLI parser modules were removed:
- `aquilia/cli/discovery_cli.py`
- `aquilia/cli/parsers/__init__.py`
- `aquilia/cli/parsers/module.py`
- `aquilia/cli/parsers/workspace.py`

### Replacement

If you had custom scripts importing from `aquilia.cli.parsers`, migrate to `aquilia.cli.core.workspace`:

```python
# BEFORE
from aquilia.cli.parsers.workspace import WorkspaceManifest
manifest = WorkspaceManifest.from_file(Path("workspace.py"))

# AFTER
from aquilia.cli.core.workspace import load_workspace
ws = load_workspace(Path.cwd())
print(ws.module_names)
```

---

## 3. Router Teardown API

If you maintain custom test fixtures that manually instantiate `ControllerRouter` or `AquiliaServer`, invoke `.clear()` or `.shutdown()` during teardown:

```python
# BEFORE
router = ControllerRouter()
router.initialize()
# ... test logic ...
# router left in memory

# AFTER
router = ControllerRouter()
router.initialize()
try:
    # ... test logic ...
finally:
    router.clear()
```

---

## Upgrade Checklist

- [ ] Upgrade `aquilia` to `1.4.0b3` in `pyproject.toml` or `requirements.txt`.
- [ ] Run `aq doctor` to perform a full health audit of your workspace.
- [ ] Remove any imports from `aquilia.cli.parsers`.
- [ ] Verify that CI/CD workflows handle non-zero exit codes from `aq validate`.
- [ ] Ensure test fixtures call `server.shutdown()` or `router.clear()` to prevent nanobind leak warnings.

---

## Compatibility Matrix

| Component | Minimum | Recommended |
|---|---|---|
| Python | 3.10 | 3.12+ |
| OS | Linux, macOS 11+, Windows 10+ | Ubuntu 22.04 / macOS 14 |
| SQLite | 3.35.0 | 3.42.0+ |
