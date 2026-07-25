# Strict Resolved-Import Discovery Mode

Aquilia v1.3.4 introduces a robust new mechanism for workspace discovery: **Strict Resolved-Import Mode**. 

## Motivation

By default, Aquilia uses an Abstract Syntax Tree (AST) scanner to discover controllers, services, and models. This AST mode is incredibly fast because it does not execute any application code. However, it is fundamentally limited:
- It cannot resolve complex, multi-file inheritance chains (transitive inheritance).
- It cannot reliably detect classes imported via aliases (`from lib import BaseController as MyBase`).
- It cannot discover components re-exported through `__all__` in `__init__.py` files.

To support complex application architectures and advanced modular patterns, we've built the `StrictDiscoveryEngine`.

## How It Works Internally

The `StrictDiscoveryEngine` (a subclass of `AutoDiscoveryEngine`) bypasses the AST parser and safely utilizes Python's module loading system (`importlib.util.spec_from_file_location`). 

By performing actual runtime imports, it gains access to the true `inspect.getmro()` Method Resolution Order (MRO) chain for every class. 

- **Deduplication:** It tracks `import_path` identifiers to ensure re-exported classes are only registered once, enforcing a strict `__module__` guard.
- **Resilience:** If a file contains a syntax error or an unresolvable import, the engine catches the `ImportError`, emits a targeted warning log, and gracefully continues scanning the rest of the workspace.

## Usage Guide

You can enable strict mode programmatically when invoking the discovery engine:

```python
from aquilia.discovery.engine import AutoDiscoveryEngine

engine = AutoDiscoveryEngine()
# Enable strict import-based discovery
manifest = engine.discover(strict=True)

# Also works for sync_manifest
engine.sync_manifest(strict=True)
```

### CLI Integration

When using the Aquilia CLI, simply pass the `--strict` flag:

```bash
aq discover --strict
```

## AST Mode vs Strict Mode

| Scenario | AST Mode (Default) | Strict Mode |
|---|---|---|
| Speed | **Very Fast** (~O(1) per file) | Slower (executes module init code) |
| Direct Inheritance (`class MyCtrl(Controller):`) | Discovered | Discovered |
| Transitive Inheritance (`class MyCtrl(BaseCtrl):`) | ❌ Missed | ✅ Discovered |
| Aliased Imports (`class MyCtrl(Alias):`) | ❌ Missed | ✅ Discovered |
| Re-exports (`__all__ = ["MyCtrl"]`) | ❌ Missed | ✅ Discovered |

## Best Practices & Limitations

- **Performance:** Strict mode imports your modules. Any expensive side-effects at the module level (e.g., establishing database connections, long computations) will execute during discovery. It is highly recommended to keep module-level code pure and side-effect free.
- **Default Behavior:** The default AST mode remains unchanged in behavior and performance. Use strict mode only if your project structure relies on aliasing, deep inheritance, or re-exports.
