# Migration & Upgrade Guide — v1.3.x to v1.4.0

Aquilia v1.4.0 is fully backwards-compatible with v1.3.x applications for standard routing, dependency injection, and ORM usage. This document covers required adjustments when upgrading custom middleware, CLI scripts, and optional dependencies.

---

## Quick Assessment Table

| If your application uses... | Action Required? | Details |
| :--- | :--- | :--- |
| **Controllers, Routes, DI, Models** | ❌ None | Standard application APIs are 100% compatible. |
| **`aquilia.middleware_ext`** | ⚠️ Update Imports | Replaced by `aquilia.middleware.builtin` and `aquilia.middleware.core`. |
| **Custom Middleware `__call__`** | ❌ None | `__call__` remains supported; new `before`/`after` hooks are optional. |
| **`SocketGuard.check_message`** | ⚠️ Update Code | Deprecated; migrate to `SocketMiddleware.on_message`. |
| **CI `aq validate` / `aq doctor`** | ⚠️ Verify Exit Codes | Now exits with non-zero on configuration errors or broken imports. |
| **Vector Search (`aquilia.vectordb`)** | ℹ️ Opt-in | Requires Python 3.11+ and `pip install 'aquilia[vectordb]'`. |

---

## Upgrade Steps

### 1. Upgrade Package
```bash
pip install --upgrade aquilia==1.4.0
```

To install all native acceleration dependencies and optional bundles:
```bash
pip install --upgrade 'aquilia[full]==1.4.0'
```

### 2. Verify Native Extensions
Run the built-in native loader verification:
```bash
python -c "from aquilia._core_loader import NATIVE; from aquilia._dataengine_loader import DATAENGINE_NATIVE; from aquilia.json import native as JSON_NATIVE; print(f'Native status: _core={NATIVE}, _dataengine={DATAENGINE_NATIVE}, _json={JSON_NATIVE}')"
```
On platforms with binary wheels (Linux, macOS, Windows), all three will report `True`. On compiler-free source builds, all three will report `False` and smoothly use pure-Python fallbacks.

### 3. Update Middleware Import Paths (If Applicable)
If you directly imported from the internal `aquilia.middleware_ext` path:
```python
# Before (v1.3.x):
from aquilia.middleware_ext.cors import CORSMiddleware
from aquilia._middleware_base import Middleware

# After (v1.4.0):
from aquilia.middleware import CORSMiddleware, Middleware
# or canonical path:
from aquilia.middleware.builtin import CORSMiddleware
from aquilia.middleware.core import Middleware
```

### 4. Run Health Diagnostics
Execute the unified health checks engine on your workspace:
```bash
aq doctor
```
Verify that all active subsystems report healthy status and no deprecated configuration options are flagged.
