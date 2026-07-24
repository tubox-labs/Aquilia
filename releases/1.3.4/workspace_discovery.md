# Workspace Discovery Enhancements

Aquilia 1.3.4 fundamentally improves how the framework detects and registers workspaces.

## Old Behavior: Regex Source Scanning

Previously, workspace module discovery was performed by reading the raw source code of workspace configuration files and applying regular expressions to find registered modules.

**What it missed:**
If your workspace configuration generated modules dynamically or used list comprehensions, the regex would fail to capture them, silently omitting critical parts of your application.

## New Behavior: Exec-Based Discovery

The framework now uses `_load_workspace_from_exec()` as the primary discovery mechanism. This function safely executes the workspace configuration in an isolated namespace and extracts the actual Python lists/objects.

### Example: The Dynamic Workspace

The following `workspace.py` would have been completely missed by the 1.3.3 regex engine, but works perfectly in 1.3.4:

```python
# workspace.py
base_modules = ["auth", "users", "billing"]
feature_flags = get_active_features()

# 1.3.3 Regex missed this completely!
# 1.3.4 Exec path correctly evaluates it.
REGISTERED_MODULES = base_modules + [f"features.{f}" for f in feature_flags]
```

### Fallback Behavior
If the execution fails (for example, if the workspace imports a heavy dependency that isn't available during the early discovery phase), the system falls back to the old regex method and logs a warning.

### Diagnostics and Logs
Before 1.3.4, workspace discovery failures were entirely silent. Now, you will receive explicit logging:
- `DEBUG: Workspace executed successfully. Found X modules.`
- `WARNING: Workspace exec failed (reason...). Falling back to regex.`
- `ERROR: Workspace parsing failed completely. No modules discovered.`
