# Round 2 Bugfixes

Aquilia v1.3.4 includes 7 major bugfixes from the second architecture audit round.

## 7. `imports` Field Ignored by Dependency Graph
- **Symptom:** Manifests using the newer `imports` API did not have their dependencies resolved correctly; only `depends_on` worked.
- **Root Cause:** Phase 3 of the core resolution and `AppContext` only parsed the legacy `depends_on` property.
  ```python
  # Before
  for dep in manifest.depends_on:
      graph.add_edge(manifest.name, dep)
  ```
- **Fix:** Both Phase 3 and `AppContext` now evaluate `imports OR depends_on`. A bidirectional sync was also added in `AppManifest.__post_init__` to ensure the fields mirror each other internally.
  ```python
  # After
  deps = manifest.imports or manifest.depends_on
  for dep in deps:
      graph.add_edge(manifest.name, dep)
  ```
- **File Changed:** `aquilary/core.py`, `manifest.py`
- **Tests Added:** `test_manifest_imports_resolves_graph`, `test_manifest_bidirectional_sync`

## 8. Silent Discovery Failures
- **Symptom:** When autodiscovery failed due to syntax errors in workspace files, it failed silently, making debugging impossible.
- **Root Cause:** Six separate `except Exception: pass` handlers existed in `perform_autodiscovery()`.
- **Fix:** Replaced all empty exception handlers with `logger.warning(..., exc_info=True)` to surface the failures without crashing the scanner.
- **File Changed:** `aquilary/core.py`
- **Tests Added:** `test_autodiscovery_logs_exceptions`

## 9. Masked `surp` Decode Bugs
- **Symptom:** Internal framework bugs related to decoding `surp` files were being swallowed and treated as a "missing file" scenario.
- **Root Cause:** Broad exception catching grouped `ImportError` and general `Exception` together.
  ```python
  # Before
  except (ImportError, Exception):
      return fallback()
  ```
- **Fix:** Split the exception handlers. `ImportError` retains its silent fallback behavior (expected missing files), while general `Exception` instances are logged and re-raised.
- **File Changed:** `aquilary/core.py`
- **Tests Added:** `test_surp_decode_raises_exception`, `test_surp_decode_ignores_import_error`

## 10. Dead Routing Code
- **Symptom:** Maintenance overhead.
- **Root Cause:** A 30-line commented-out block of an old `_build_router` implementation was left in the codebase.
- **Fix:** Deleted the dead code.
- **File Changed:** `aquilary/core.py`
- **Tests Added:** N/A

## 11. Brittle Workspace Discovery
- **Symptom:** Workspaces that dynamically generated module lists were ignored by the framework's workspace discovery logic.
- **Root Cause:** `runtime.py` parsed workspace configuration by running regex over raw source text.
- **Fix:** Implemented `_load_workspace_from_exec()` as the primary discovery mechanism, which executes the workspace configuration. The regex approach is retained strictly as a logged fallback.
- **File Changed:** `runtime.py`
- **Tests Added:** `test_workspace_discovery_exec`, `test_workspace_discovery_regex_fallback`

## 12. Dangerous Manifest Loader
- **Symptom:** Evaluating a manifest automatically executed its surrounding module code, posing a security and stability risk during simple parsing operations.
- **Root Cause:** `ManifestLoader` directly executed modules to extract the `AppManifest` definitions.
- **Fix:** Implemented a two-phase loading strategy. Phase 1 performs AST-based static extraction without executing code. If extraction fails, Phase 2 executes the module but emits a strong warning.
- **File Changed:** `aquilary/loader.py`
- **Tests Added:** `test_manifest_loader_ast_extraction`, `test_manifest_loader_exec_fallback_warns`
