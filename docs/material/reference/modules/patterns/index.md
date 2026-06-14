# Patterns Module

> `aquilia.patterns` — Pattern matching and type registry

The Patterns module provides a pattern compiler and matcher for URL patterns, type registries, and declarative matching rules.

## When to Use

Use the Patterns module when you need:

- Compiling URL patterns into efficient matchers
- Type-based dispatch systems
- Declarative pattern matching logic

## Key Classes

| Class | Purpose |
|---|---|
| `PatternCompiler` | Compiles pattern strings into optimized matchers |
| `PatternMatcher` | Executes compiled patterns against input |
| `CompiledPattern` | Optimized, pre-compiled pattern |
| `TypeRegistry` | Registers and resolves types by pattern |

## Quick Example

```python
from aquilia.patterns import PatternCompiler, PatternMatcher

compiler = PatternCompiler()
compiled = compiler.compile("/users/<user_id:int>/posts/<post_id:str>")

matcher = PatternMatcher(compiled)
result = matcher.match("/users/42/posts/hello-world")
# result.params → {"user_id": 42, "post_id": "hello-world"}
```

## Import Path

```python
from aquilia.patterns import (
    PatternCompiler,
    PatternMatcher,
    CompiledPattern,
    TypeRegistry,
)
```

## Related Modules

- [core/controller](../../api/controllers.md) — Route pattern matching in controllers
- [versioning](../versioning/index.md) — Version URL patterns