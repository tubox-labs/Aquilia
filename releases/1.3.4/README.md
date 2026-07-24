# Aquilia v1.3.4 Release Notes

Aquilia 1.3.4 is a framework architecture audit and bug fix release focused on stability and performance in the registry, runtime, workspace, config, and CLI subsystems. This release addresses 13 bugs identified across two comprehensive audit rounds and introduces a new CLI validation feature to help developers migrate away from legacy manifest patterns.

## Table of Contents

- [Round 1 Bugfixes](bugfixes_r1.md)
- [Round 2 Bugfixes](bugfixes_r2.md)
- [Performance Improvements](performance.md)
- [Manifest System Changes](manifest_system.md)
- [Workspace Discovery Enhancements](workspace_discovery.md)
- [CLI Updates](cli.md)
- [Migration Guide](migration.md)

## Quick Examples

### Explicit `Secret` API
The `Secret` config class now explicitly distinguishes between literal values and environment variable lookups.

```python
# OLD (broken - ambiguously looked up env var)
db_pass = Secret("MY_DATABASE_PASS")

# NEW (correct)
db_pass = Secret(env="MY_DATABASE_PASS")  # explicit env-var
db_pass = Secret("literal-value")         # literal value, no env lookup
```

### Manifest `imports` Field Support
The `imports` field is now fully integrated into the dependency graph, replacing `depends_on`.

```python
# OLD (broken - imports was ignored by the dependency graph)
manifest = AppManifest(
    name="billing",
    version="1.0.0",
    depends_on=["auth"], 
)

# NEW (correct - correctly drives dependency graph)
manifest = AppManifest(
    name="billing",
    version="1.0.0",
    imports=["auth"], 
)
```

### New CLI Feature: Deprecation Validation
Surface legacy fields in your manifests using the new validation flag.

```bash
# Detect deprecated fields like route_prefix, database, middlewares, depends_on
aq validate --deprecated

# Output as JSON for CI pipelines
aq validate --deprecated --json
```

### Fail-Fast Startup
Make entrypoint errors immediately fatal rather than silently serving 500-error stubs.

```bash
AQUILIA_FAIL_FAST=1 uvicorn entrypoint:app
```

## What Changed

### Files Changed
| File | Subsystem | Description |
|------|-----------|-------------|
| `pyconfig.py` | Config | Explicit `Secret` API, positional value strictness |
| `discovery/engine.py` | Workspace | AST validation for ManifestWriter, mtime/size cache fast-path |
| `aquilary/graph.py` | Registry | Iterative Tarjan implementation, depth-limit removal |
| `aquilary/core.py` | Registry | O(n) manifest lookups, proper exception handling, bidirectional manifest sync |
| `entrypoint.py` | Runtime | `AQUILIA_FAIL_FAST` support |
| `manifest.py` | Registry | Bidirectional sync for `imports` and `depends_on` |
| `runtime.py` | Runtime | Exec-based workspace module discovery |
| `aquilary/loader.py` | Registry | Two-phase static AST manifest extraction |
| `cli.py` | CLI | `--deprecated` flag for `aq validate` |

### New APIs
| Feature | Details |
|---------|---------|
| `Secret(env=...)` | Explicit environment variable resolution. |
| `aq validate --deprecated` | Validation flag for legacy manifest attributes. |
| `AQUILIA_FAIL_FAST=1` | Environment variable to abort startup on initialization errors. |

## Fixes Shipped

| Issue | Root Cause | Fix | File |
|-------|------------|-----|------|
| `Secret` lookup ambiguity | Positional args were treated as env vars by default. | Forced explicit `env=` kwarg, warned on ALL_CAPS pos args. | `pyconfig.py` |
| `ManifestWriter` corruption | Bad AST rewrites were saved directly to disk. | Added `ast.parse()` validation pre-write. | `discovery/engine.py` |
| Max recursion depth in `graph.py` | Recursive Tarjan algorithm failed on 500+ deps. | Converted algorithm to explicit stack iterative approach. | `aquilary/graph.py` |
| Slow manifest lookups (Phase 5) | O(n²) list iteration during resolution. | Pre-built `{m.name: m}` dict for O(n) lookup. | `aquilary/core.py` |
| Silent startup failures | Entrypoint caught and masked critical failures. | Added `AQUILIA_FAIL_FAST=1` bypass. | `entrypoint.py` |
| Slow discovery cache | Files were SHA-256 hashed on every boot. | Added size/mtime fast-path to bypass hashing. | `discovery/engine.py` |
| `imports` ignored in graph | Phase 3 only read `depends_on`. | Updated phase to check both; added bidirectional sync. | `aquilary/core.py`, `manifest.py` |
| Silent discovery failures | Bare `except Exception: pass` swallowed errors. | Added `logger.warning(..., exc_info=True)`. | `aquilary/core.py` |
| Masked surp decode bugs | `except (ImportError, Exception)` grouped severe bugs with missing files. | Split handling: silent `ImportError`, re-raise `Exception`. | `aquilary/core.py` |
| Dead routing code | Leftover commented block for `_build_router`. | Deleted the dead code. | `aquilary/core.py` |
| Regex workspace discovery | Brittle regex missed dynamic modules. | Exec-based discovery fallback to regex. | `runtime.py` |
| Dangerous loader | Executing arbitrary code during manifest parsing. | Added Phase 1 AST extraction with Phase 2 exec fallback. | `aquilary/loader.py` |
