# Strict Discovery Mode

Aquilia includes a powerful module discovery system that automatically registers models, controllers, services, and tasks. By default, this discovery engine uses **AST (Abstract Syntax Tree) parsing**.

While AST parsing is incredibly fast (because it doesn't actually execute or import the Python code), it has limitations. **Strict Discovery Mode** exists to bridge that gap by using real runtime imports when accuracy is more important than raw speed.

## The Limitation of AST Mode

AST mode reads the textual syntax of your Python files. It looks for class definitions that inherit from known bases (like `class MyController(Controller):`).

Because it doesn't execute the code, it cannot resolve:

1. **Transitive Inheritance**: If you have `class BaseUserCtrl(Controller):` in one file, and `class AdminUserCtrl(BaseUserCtrl):` in another, the AST mode won't know that `AdminUserCtrl` is a `Controller`.
2. **Aliased Imports**: If you do `from aquilia.controller import Controller as BaseCtrl`, AST mode might miss `class MyCtrl(BaseCtrl):`.
3. **Dynamic `__all__` Exports**: If you dynamically build module exports.

## When to use Strict Mode

You should use strict mode when:
- You rely heavily on deep, multi-file class hierarchies for your controllers or models.
- You rename framework base classes via import aliases.
- You are debugging missing components that aren't showing up in `aq inspect routes` or `aq discover`.
- You are running a CI pipeline to freeze routing manifests for production.

## CLI Usage

You can trigger strict discovery from the command line using the `--strict` flag:

```bash
aq discover --strict
```

If you are updating your manifest file, use it in conjunction with other commands if they support it, or validate your workspace with:

```bash
aq validate --strict
```

## Programmatic API

If you are invoking the discovery engine manually in a script or custom command, pass `strict=True` to the discover method:

```python
from aquilia.discovery import AutoDiscoveryEngine

engine = AutoDiscoveryEngine(workspace_path=".")
# Uses StrictDiscoveryEngine under the hood
manifest = engine.discover(strict=True) 
```

Or you can import the engine directly:

```python
from aquilia.discovery import StrictDiscoveryEngine

engine = StrictDiscoveryEngine(workspace_path=".")
manifest = engine.discover()
```

## What gets detected in Strict Mode?

Because strict mode imports the modules and uses Python's `issubclass()` and Method Resolution Order (MRO), it successfully detects:

- **Aliased bases**: `class MyCtrl(BaseCtrl):` where `BaseCtrl` is an alias of `Controller`.
- **Transitive chains**: Subclasses of subclasses of `Controller` or `Model`.
- **`__all__` re-exports**: Correctly traverses package boundaries defined by `__all__`.

## Performance Implications

Strict discovery is significantly slower than AST discovery because it must evaluate module-level code, resolve imports, and interact with the Python runtime.

In a large codebase, AST discovery might take 50ms, while strict discovery could take 500ms to 1s.

## Best Practices

- **Development**: Rely on AST mode (the default). It's fast enough to run on every hot-reload when you save a file. Keep your controller/model inheritance flat enough that AST mode works.
- **CI/CD**: Use `--strict` during your CI/CD pipeline (e.g., when compiling production routes or running `aq validate --strict`) to ensure 100% accuracy before deployment.
