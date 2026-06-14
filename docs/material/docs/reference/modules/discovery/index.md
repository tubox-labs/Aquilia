# Discovery Module

> `aquilia.discovery` — Auto-discovery engine for components

The Discovery module provides AST-based and file-based scanning to automatically detect controllers, services, models, middleware, and other framework components — keeping module manifests in sync with the codebase.

## When to Use

Use the Discovery module when:

- Running `aq discover --dry-run` to see what would be detected
- Running `aq discover --sync` to auto-update `manifest.py` files
- Understanding how the framework finds components at startup
- Debugging why a component isn't being registered

## Key Classes

| Class | Purpose |
|---|---|
| `AutoDiscoveryEngine` | Orchestrates the full discovery process |
| `PackageScanner` | Scans Python packages for component files |
| `ASTClassifier` | Parses `.py` files to classify components |
| `FileScanner` | File-system level scanning |
| `ManifestDiffer` | Computes diff between code and manifest |
| `ManifestWriter` | Writes/updates `manifest.py` files |

## Quick Example

```python
from aquilia.discovery import PackageScanner

scanner = PackageScanner("modules/")
results = scanner.scan()

for component in results.controllers:
    print(f"Found controller: {component.class_path}")
for component in results.services:
    print(f"Found service: {component.class_path}")
```

## CLI Usage

```bash
# See what would be discovered (dry run)
aq discover --dry-run

# Auto-update manifests with discovered components
aq discover --sync

# Get JSON output for scripting
aq discover --json
```

## Import Path

```python
from aquilia.discovery import (
    PackageScanner,
    AutoDiscoveryEngine,
    ASTClassifier,
    FileScanner,
)
```

## Related Modules

- [core/manifest](../core/manifest.md) — Manifests updated by discovery
- [aquilary](../aquilary/index.md) — Registry built from discovered components
- [cli](../cli/index.md) — `aq discover` command