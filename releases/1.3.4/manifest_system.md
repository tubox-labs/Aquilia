# Manifest System Enhancements

The `AppManifest` architecture has been significantly overhauled in 1.3.4 for better security, consistency, and alignment with future API directions.

## `imports` vs `depends_on`

In older versions of Aquilia, dependencies between apps were declared using the `depends_on` field. With the introduction of the new modularity specifications, `imports` is the preferred terminology.

**Old API:**
```python
manifest = AppManifest(
    name="analytics",
    depends_on=["database", "auth"]
)
```

**New API (Preferred):**
```python
manifest = AppManifest(
    name="analytics",
    imports=["database", "auth"]
)
```

**When to use which:** Both are fully supported in 1.3.4. We recommend new applications use `imports`. Older applications do not need to migrate immediately, but switching is recommended for clarity.

### Bidirectional Sync
To ensure backward compatibility and prevent bugs where plugins rely on the old `depends_on` field, `AppManifest.__post_init__` now performs bidirectional synchronization. If you specify `imports`, the framework automatically populates `depends_on`, and vice-versa.

## ManifestLoader Two-Phase Loading

Previously, parsing a manifest meant executing the entire Python file. This was inefficient and occasionally dangerous if files contained side-effects at the module level.

**New Behavior:**
1. **Phase 1 (AST Path):** The `ManifestLoader` parses the Python file into an Abstract Syntax Tree (AST) and extracts the `AppManifest` kwargs statically. No code is executed.
2. **Phase 2 (Exec Fallback):** If the AST extraction fails (e.g., due to highly dynamic manifest generation), the loader falls back to executing the module but will emit a runtime warning advising against dynamic manifests.

### Side-by-Side Comparison

| Old Loader | New Loader (1.3.4) |
|------------|--------------------|
| Reads file content | Reads file content |
| `exec()` is called unconditionally | Tries static AST extraction first |
| Side effects trigger immediately | Side effects avoided in 99% of cases |
| Silent execution | Warns if fallback `exec()` is required |

## Migration Guidance

1. Convert `depends_on` to `imports` in your manifests to adopt the v2 standard.
2. Ensure your `AppManifest` declarations are static. Avoid using functions, loops, or complex variables to construct your manifest kwargs, as this forces the loader into the Phase 2 execution fallback path.
