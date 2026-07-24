# Round 1 Bugfixes

Aquilia v1.3.4 includes 6 major bugfixes from the first architecture audit round.

## 1. `Secret` Positional-Value Ambiguity
- **Symptom:** Passing a string like `Secret("MY_VAR")` silently treated the string as an environment variable to look up rather than a literal value. 
- **Root Cause:** The `Secret` constructor mapped the first positional argument to the `env` parameter under the hood.
  ```python
  # Before
  def __init__(self, value_or_env: str):
      if value_or_env.isupper():
          self.env = value_or_env
      # ...
  ```
- **Fix:** Positional arguments are now strictly treated as literal values. To look up an environment variable, you must explicitly use the `env` kwarg. A `DeprecationWarning` is emitted if an ALL_CAPS string is passed positionally.
  ```python
  # After
  def __init__(self, value: Optional[str] = None, *, env: Optional[str] = None):
      # ...
  ```
- **File Changed:** `pyconfig.py`
- **Tests Added:** `test_secret_literal_value`, `test_secret_env_kwarg`, `test_secret_deprecation_warning`

## 2. ManifestWriter Corruption
- **Symptom:** Modifying manifests dynamically could result in syntax errors and corrupted Python files written to disk if the rewrite failed.
- **Root Cause:** There was no post-write abstract syntax tree (AST) validation. The writer blindly flushed AST alterations to the file.
- **Fix:** The source code is rewritten in-memory and validated via `ast.parse()` before the disk write is authorized. If validation fails, the write is aborted, and the original file is preserved.
- **File Changed:** `discovery/engine.py`
- **Tests Added:** `test_manifest_writer_ast_validation_success`, `test_manifest_writer_ast_validation_failure_reverts`

## 3. Recursive Tarjan Depth Limit Exceeded
- **Symptom:** Projects with extremely deep dependency chains (e.g., > 500 apps) crashed during startup with `RecursionError`.
- **Root Cause:** `get_transitive_dependencies` and the underlying Tarjan's strongly connected components algorithm used Python's native call stack.
- **Fix:** Both algorithms were rewritten to use an explicit iterative stack approach. 500+ deep chains now resolve effortlessly without hitting Python's recursion limits.
- **File Changed:** `aquilary/graph.py`
- **Tests Added:** `test_tarjan_iterative_deep_graph`, `test_transitive_deps_deep_chain`

## 4. O(n²) Manifest Lookup
- **Symptom:** Startup times scaled poorly for projects with a large number of manifests.
- **Root Cause:** Phase 5 of the boot sequence performed a linear scan `[m for m in manifests if m.name == target]` for every single resolution.
- **Fix:** Implemented a pre-built dictionary mapping `{m.name: m}`, changing the lookup operation to O(n) overall.
- **File Changed:** `aquilary/core.py`
- **Tests Added:** `test_manifest_resolution_performance`

## 5. Silent Startup Failures
- **Symptom:** Boot errors (like missing dependencies or broken configurations) were silently caught, and the server started with 500-error stubs. 
- **Root Cause:** The `entrypoint.py` module wrapped startup in a broad `try-except` block designed to keep the server alive in development.
- **Fix:** Added the `AQUILIA_FAIL_FAST=1` environment variable to allow the entrypoint to re-raise critical exceptions and abort startup.
- **File Changed:** `entrypoint.py`
- **Tests Added:** `test_entrypoint_fail_fast_aborts`, `test_entrypoint_default_swallows_errors`

## 6. Expensive Discovery Cache
- **Symptom:** High CPU utilization and slow boot times during local development reloading.
- **Root Cause:** The discovery cache eagerly generated SHA-256 hashes for every file in the workspace to detect changes.
- **Fix:** Introduced a fast-path cache that checks file size and modification time (`mtime`) first. If both are unchanged, the SHA-256 hash calculation is skipped.
- **File Changed:** `discovery/engine.py`
- **Tests Added:** `test_discovery_cache_mtime_fast_path`, `test_discovery_cache_hash_fallback_on_mtime_change`
